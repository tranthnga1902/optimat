"""Gộp phần thô của mọi mặt bằng thành một bảng: công tác theo tầng, tổng theo công tác, vật liệu mua về.

    compute_rough(RoughRequest)      công thức chốt duy nhất (trang kiểm tra gửi lên dữ liệu đã sửa)
    rough_from_drawing(drawing, ...) dựng RoughRequest từ nhận dạng tự động (tường, cửa, cột, tên phòng, dầm suy)
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from .. import config
from ..catalog.repository import Catalog, default_catalog
from ..drawing.concepts import layer_role, match_block_signal
from ..drawing.encoding import normalize
from ..drawing.review import ReviewOpening, ReviewWall
from .areas import PlanParams, area_works, plan_geometry, room_labels
from .beams import Beam, beam_joints, beam_works, infer_beams, is_tie_beam
from .columns import Column, column_overlaps, column_works, detect_columns
from .materials import materials_for_works
from .models import WORKS, ProjectParams, RoughBill, WorkItem
from .stairs import Stair, stair_works
from .foundations import _neg, foundation_works, footing_rects
from .rebar import RebarRow, read_rebar_schedules
from .secondary import (LinearMember, deduct_ties, drop_slab_under_roof, lintel_under_beam, linear_works,
                        read_secondary, roof_works)
from .steel import steel_works
from .structural import floor_count, read_structural
from .walls import review_input_from_takeoff, wall_works


class RoomLabel(BaseModel):
    kind: str
    text: str
    x: float
    y: float


class PlanInput(PlanParams):
    """Một mặt bằng đã (hoặc chưa) qua trang kiểm tra."""
    height_mm: Optional[float] = None           # trống: chưa có chiều cao tầng, mặt bằng chưa tính
    walls: list[ReviewWall]
    openings: list[ReviewOpening] = Field(default_factory=list)
    columns: list[Column] = Field(default_factory=list)
    beams: Optional[list[Beam]] = None          # None: suy từ tường và cột
    stairs: list[Stair] = Field(default_factory=list)
    labels: list[RoomLabel] = Field(default_factory=list)
    wall_systems: dict[str, Optional[str]] = Field(default_factory=dict)   # tường -> phương án tường đã quy đổi
    found: dict[str, list[str]] = Field(default_factory=dict)   # vai trò phần thô (ngoài cột) -> layer/block thấy trên mặt bằng
    members: list[LinearMember] = Field(default_factory=list)   # giằng tường, sê nô trên mặt bằng này (giằng trừ khỏi xây)


# bộ phận phần thô thấy theo ký hiệu nhưng chưa bóc tự động: nhắc người dùng nhập
FOUND_HINT = {"BEAM": ("dầm", "đang suy dầm từ tường và cột, kiểm tra hoặc nhập dầm"),
              "STAIR": ("cầu thang", "nhập thông số cầu thang để bóc"),
              "SLAB": ("sàn", "kiểm tra dày sàn trong thông số công trình"),
              "LINTEL": ("lanh tô", "kiểm tra thông số lanh tô"),
              "FOUNDATION": ("móng", "nhập móng trong thông số công trình")}


def rough_parts(drawing) -> dict[str, list[str]]:
    """Bộ phận phần thô (trừ cột, đã nhận hình) có trên bản vẽ theo ký hiệu layer/block (data/rules/concepts.csv)."""
    found: dict[str, list[str]] = {}
    used = {s.layer for s in drawing.segments} | {h.layer for h in drawing.hatches} | {b.layer for b in drawing.blocks}
    for n in sorted(used):
        if (r := layer_role(n)) in FOUND_HINT:
            found.setdefault(r, []).append(f"layer {n}")
    for n in sorted({b.name for b in drawing.blocks}):
        if (s := match_block_signal(n)) and s.vai_tro in FOUND_HINT:
            found.setdefault(s.vai_tro, []).append(f"block {n}")
    return found


class RoughRequest(BaseModel):
    project_id: Optional[int] = None
    file: str = ""
    params: ProjectParams = Field(default_factory=ProjectParams)
    plans: list[PlanInput]
    structural_beams: dict[str, list[Beam]] = Field(default_factory=dict)   # dầm đọc từ mặt bằng kết cấu, theo tiêu đề
    structural_floors: dict[str, int] = Field(default_factory=dict)        # số tầng dùng chung mặt bằng kết cấu (mặc định 1)
    column_sections: dict[str, tuple[float, float]] = Field(default_factory=dict)   # tiết diện cột ghi chữ trên bản vẽ kết cấu
    sheets: list[dict] = Field(default_factory=list)       # 14 loại bản vẽ: có / chưa có trong file (drawing/sheets.py)
    notes: list[str] = Field(default_factory=list)         # cảnh báo khi đọc bản vẽ kết cấu
    rebar: list[RebarRow] = Field(default_factory=list)    # dòng bảng thống kê thép đọc từ bản vẽ (rough/rebar.py)
    members: list[LinearMember] = Field(default_factory=list)   # giằng tường, sê nô đọc từ mặt bằng kết cấu

    @model_validator(mode="after")
    def _unique_plan_names(self):
        # tên mặt bằng là khóa (dầm, thép, chi tiết theo tầng): bản vẽ có hai tiêu đề trùng thì đánh số thêm
        seen: dict[str, int] = {}
        for p in self.plans:
            seen[p.name] = seen.get(p.name, 0) + 1
            if seen[p.name] > 1:
                p.name = f"{p.name} ({seen[p.name]})"
        return self


class WorkTotal(BaseModel):
    code: str
    name: str
    unit: str
    quantity: Optional[float] = None    # tổng phần đã tính được
    complete: bool = True
    items: int = 0


class RoughResult(RoughBill):
    totals: list[WorkTotal] = Field(default_factory=list)
    beams: dict[str, list[Beam]] = Field(default_factory=dict)       # dầm đã dùng theo mặt bằng (kể cả dầm suy)
    takeoff_id: Optional[int] = None                                   # dòng đã lưu trong takeoff_results (nếu có)
    formwork: list[WorkTotal] = Field(default_factory=list)            # cốp pha cộng theo cấu kiện (mỗi cấu kiện một dòng)


def compute_rough(req: RoughRequest, catalog: Catalog | None = None) -> RoughResult:
    catalog = catalog or default_catalog()
    params = req.params
    works: list[WorkItem] = []
    warnings: list[str] = []
    used_beams: dict[str, list[Beam]] = {}
    warnings += req.notes
    missing = [s for s in req.sheets if not s["co"]]
    if req.sheets and missing:
        warnings.append("Chưa có loại bản vẽ: " + "; ".join(f"{s['loai_ban_ve']} ({s['vat_lieu']})" for s in missing)
                        + ". Bộ phận lấy từ các loại này phải nhập tay hoặc tải thêm bản vẽ.")
    if not req.plans:
        warnings.append("Không tìm thấy mặt bằng tầng kiến trúc trong bản vẽ: chưa tính xây, trát, sàn, cột"
                        + (" (dầm, móng lấy từ bản vẽ kết cấu)." if req.structural_beams or params.foundations else "."))
    elif not any(p.is_ground for p in req.plans):
        warnings.append("Chưa xác định tầng trệt: chưa tính nền tầng trệt (đệm cát, bê tông lót).")
    for p in req.plans:
        for role, names in p.found.items():
            label, hint = FOUND_HINT.get(role, (role, "kiểm tra"))
            if (role == "STAIR" and p.stairs) or (role == "BEAM" and (p.beams is not None or req.structural_beams)):
                continue
            warnings.append(f"{p.name}: bản vẽ có {label} ({', '.join(names[:3])}): {hint}.")
        if not p.height_mm:
            warnings.append(f"{p.name}: chưa có chiều cao tầng, chưa tính phần thô của mặt bằng này.")
            continue
        overlaps = column_overlaps(p.columns, [w for w in p.walls if w.masonry])
        known = set(catalog.materials.material_id)
        # phương án tường quy đổi lại từ mã vật liệu (người dùng có thể đã đổi vật liệu, lớp tường, vẽ thêm tường)
        systems = {w.id: catalog.resolve_wall([w.mat], w.cls).wall_system_id if w.mat in known else p.wall_systems.get(w.id)
                   for w in p.walls}
        # có dầm từ bản vẽ kết cấu thì không suy dầm trên mặt bằng kiến trúc (tránh đếm hai lần)
        beams = p.beams if p.beams is not None else [] if req.structural_beams else infer_beams(p.columns, p.walls)
        beams, warn = beam_joints(beams, p.columns, params)
        warnings += warn
        warnings += _section_checks(p, beams, params, req.column_sections)
        wall_params = params
        depths = sorted({b.d_mm for b in beams or [b for bs in req.structural_beams.values() for b in bs] if b.keep and b.d_mm})
        if params.beam_depth_mm is None and len(depths) == 1:     # dầm nhập tay có cao dầm: dùng để trừ khỏi tường
            wall_params = params.model_copy(update={"beam_depth_mm": depths[0]})
        for fn in (lambda: wall_works(p.name, p.height_mm, p.walls, p.openings, wall_params, catalog, systems, overlaps),
                   lambda: column_works(p.name, p.columns, p.height_mm, params, beams),
                   lambda: stair_works(p.name, p.stairs, p.height_mm, params)):
            w, warn = fn()
            works += w
            warnings += warn
        # S08-04: không cộng trùng lanh tô – dầm, giằng – tường
        warnings += lintel_under_beam(works, p.name, p.height_mm, p.walls, p.openings, systems, wall_params, catalog)
        warnings += deduct_ties(works, p.name, p.walls, systems, p.members, catalog)
        w, warn = linear_works(p.name, p.members)
        works += w
        warnings += warn
        used_beams[p.name] = beams
        w, warn = beam_works(p.name, beams, params)
        works += w
        warnings += warn
        geom = plan_geometry([w for w in p.walls if w.masonry], [(l.kind, l.text, l.x, l.y) for l in p.labels])
        w, warn = area_works(geom, params, p)
        works += w
        warnings += warn
        works += _slab_form_deduction(p.name, beams, p.columns, params)
    for view, beams in req.structural_beams.items():
        beams, warn = beam_joints(beams, [], params, footing_rects(params.foundations, view))
        warnings += warn
        used_beams[view] = beams
        w, warn = beam_works(view, beams, params)
        w += _slab_form_deduction(view, beams, [], params)
        n = req.structural_floors.get(view, 1)
        if n > 1:       # một mặt bằng dầm dùng cho nhiều tầng: nhân khối lượng
            w = [x.model_copy(update={"quantity": None if x.quantity is None else round(x.quantity * n, 3),
                                      "formula": f"{n} tầng × ({x.formula})"}) for x in w]
        works += w
        warnings += warn
    for fn in (lambda: linear_works("bản vẽ kết cấu", req.members), lambda: roof_works(params)):
        w, warn = fn()
        works += w
        warnings += warn
    works, warn = drop_slab_under_roof(works, params)
    warnings += warn
    for fn in (lambda: foundation_works(params), lambda: steel_works(works, params, req.rebar)):
        w, warn = fn()
        works += w
        warnings += warn
    if not any(w.code == "COP_PHA" and w.formwork_of == "SAN" and (w.quantity or 0) > 0 for w in works):
        works = [w for w in works if not (w.formwork_of == "SAN" and (w.quantity or 0) < 0)]   # không có sàn thì không trừ
    warnings.append("Ca máy chưa tính: chưa có định mức hao phí máy theo TT 38/2026/TT-BXD.")
    order = list(WORKS)
    plan_order = {p.name: i for i, p in enumerate(req.plans)}
    works.sort(key=lambda w: (order.index(w.code), plan_order.get(w.plan, len(plan_order))))
    bill = materials_for_works(works, params, catalog)
    totals = []
    for code in order:
        items = [w for w in works if w.code == code]
        if not items:
            continue
        known_q = [w.quantity for w in items if w.quantity is not None]
        totals.append(WorkTotal(code=code, name=WORKS[code][0], unit=WORKS[code][1], items=len(items),
                                quantity=round(sum(known_q), 3) if known_q else None,
                                complete=len(known_q) == len(items)))
    formwork = []
    for code in ("LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "GIANG_TUONG", "SE_NO", "MAI", "MONG"):
        items = [w for w in works if w.code == "COP_PHA" and w.formwork_of == code]
        if items:
            known_q = [w.quantity for w in items if w.quantity is not None]
            formwork.append(WorkTotal(code=code, name="Cốp pha " + WORKS[code][0].replace("Bê tông ", ""), unit="m²",
                                      items=len(items), quantity=round(sum(known_q), 3) if known_q else None,
                                      complete=len(known_q) == len(items)))
    return RoughResult(works=works, intermediates=bill.intermediates, materials=bill.materials,
                       warnings=warnings + bill.warnings, totals=totals, beams=used_beams, formwork=formwork)


def _section_checks(p: PlanInput, beams: list[Beam], params, column_sections: dict) -> list[str]:
    """S06-06: xung đột cao độ dầm / tầng; cột kiến trúc không khớp tiết diện cột kết cấu nào (chỉ báo, không tự loại)."""
    out = []
    for b in beams:
        d = b.d_mm or params.beam_depth_mm
        if b.keep and d and p.height_mm and d >= p.height_mm:
            out.append(f"{p.name}: xung đột cao độ: dầm {b.id} cao {d:.0f} mm không nhỏ hơn chiều cao tầng {p.height_mm:.0f} mm.")
    if column_sections:
        sizes = {tuple(sorted(v)) for v in column_sections.values()}
        odd = [c.id for c in p.columns if c.keep and c.role is None and tuple(sorted((c.b_mm, c.h_mm))) not in sizes]
        if odd:
            out.append(f"{p.name}: cột {', '.join(odd[:8])} không khớp tiết diện cột kết cấu nào "
                       f"({', '.join(f'{k.upper()} {a:.0f}×{b:.0f}' for k, (a, b) in sorted(column_sections.items()))}): "
                       "kiểm tra, cột kiến trúc thì đánh dấu để không tính bê tông.")
    return out


def _slab_form_deduction(plan: str, beams: list[Beam], columns, params) -> list[WorkItem]:
    """Đáy sàn nằm trên mặt dầm, đỉnh cột không ghép ván: trừ khỏi cốp pha sàn (sàn phía trên các dầm, cột này).
    shortcut: gán vào mặt bằng của dầm, cột (không dò sàn tầng trên); khi ghép tầng theo cao độ thì trừ đúng ô sàn."""
    dam = sum((b.b_mm or params.beam_width_mm) * b.length_mm / 1e6 for b in beams
              if b.keep and not is_tie_beam(b) and (b.b_mm or params.beam_width_mm))
    cot = sum(c.b_mm * c.h_mm / 1e6 for c in columns if c.keep and c.role != "kien_truc")
    if dam + cot <= 0:
        return []
    return [_neg("COP_PHA", dam + cot, plan=plan, element="trừ đáy sàn trên mặt dầm, đỉnh cột", formwork_of="SAN",
                 formula=f"−({dam:.3f} m² mặt dầm + {cot:.3f} m² đỉnh cột)")]


def ground_index(names: list[str], levels: list[Optional[float]]) -> Optional[int]:
    """Tầng trệt: mặt bằng có cao độ thấp nhất; không có cao độ thì theo tên (config.GROUND_PLAN_PATTERNS)."""
    known = [(lv, i) for i, lv in enumerate(levels) if lv is not None]
    if known and len(known) == len(levels):
        return min(known)[1]
    for i, n in enumerate(names):
        if any(re.search(p, normalize(n)) for p in config.GROUND_PLAN_PATTERNS):
            return i
    return None


def rough_from_drawing(drawing, params: ProjectParams | None = None, floor_height_mm: float | None = None,
                       catalog: Catalog | None = None, file: str = "", openings=None, structural=None,
                       structural_scale: float | None = None) -> RoughRequest:
    """Dựng đầu vào phần thô từ nhận dạng tự động, để trang kiểm tra hiển thị và người dùng sửa.
    structural: bản vẽ kết cấu tải riêng (một hoặc danh sách nhiều file); hình vẽ kết cấu nằm chung file kiến trúc cũng
    được đọc. Bảng thống kê thép (rebar.py), giằng tường, sê nô, mái (secondary.py) đọc trên mọi file.
    structural_scale: hệ số đổi số đo trên mặt bằng kết cấu ra mm thật (mặt bằng vẽ phóng to 2 lần: 0,5); trống: tự suy
    từ đường kích thước của từng mặt bằng. Kích thước móng, tiết diện dầm đọc từ hình chi tiết (rough/structural.py)."""
    from ..drawing.dxf_reader import crop
    from ..drawing.takeoff import takeoff_plans
    plans = takeoff_plans(drawing, floor_height_mm, catalog, openings)
    g = ground_index([p.name for p in plans], [p.level_m for p in plans])
    out = []
    for i, p in enumerate(plans):
        sub = crop(drawing, p.bbox) if p.name != "Toàn bộ bản vẽ" else drawing
        walls, openings, systems = review_input_from_takeoff(p.result)
        out.append(PlanInput(name=p.name, is_ground=(i == g), height_mm=p.height_mm, walls=walls, openings=openings,
                             wall_systems=systems, columns=detect_columns(sub), found=rough_parts(sub),
                             labels=[RoomLabel(kind=k, text=t, x=x, y=y) for k, t, x, y in room_labels(sub)]))
    params = (params or ProjectParams()).model_copy()
    beams, notes, sheets, col_sections, rebar, members = {}, [], [], {}, [], []
    extra = structural if isinstance(structural, list) else [structural] if structural is not None else []
    for d in [drawing] + extra:
        rows, warn = read_rebar_schedules(d)
        rebar += rows
        notes += warn
        m, lintel_h, warn = read_secondary(d, structural_scale)
        members += m
        notes += warn
        if params.lintel_height_mm is None and len(set(lintel_h.values())) == 1:
            params.lintel_height_mm = next(iter(lintel_h.values()))
            notes.append(f"Cao lanh tô {params.lintel_height_mm:.0f} mm lấy từ tiết diện ghi chữ "
                         f"{', '.join(k.upper() for k in lintel_h)} trên bản vẽ kết cấu: kiểm tra.")
        st = read_structural(d, structural_scale)
        beams.update(st.beams)
        col_sections.update(st.column_sections)
        notes += st.warnings
        sheets = [dict(a, co=a["co"] or b["co"], tieu_de=a["tieu_de"] + b["tieu_de"]) for a, b in zip(sheets, st.sheets)] or st.sheets
        if not params.foundations:
            params.foundations = st.foundations
    return RoughRequest(file=file, params=params, plans=out, structural_beams=beams, sheets=sheets, notes=notes,
                        structural_floors={v: floor_count(v) for v in beams}, column_sections=col_sections,
                        rebar=rebar, members=members)


def save_rough(result: RoughResult, req: RoughRequest) -> Optional[int]:
    """Lưu bảng phần thô đã chốt vào takeoff_results (cột JSON result, khóa "kind" = "rough"; không đổi lược đồ).
    Không có PostgreSQL hoặc không gắn dự án thì không lưu. Dự án không tồn tại thì báo lỗi."""
    from ..db.session import get_database_url, get_engine
    if req.project_id is None or not get_database_url():
        return None
    from datetime import datetime, timezone

    from sqlalchemy.orm import Session

    from ..db.models import Project, TakeoffResultRow
    with Session(get_engine()) as session:
        if session.get(Project, req.project_id) is None:
            raise LookupError(f"Không có dự án {req.project_id}.")
        row = TakeoffResultRow(project_id=req.project_id, confirmed_at=datetime.now(timezone.utc),
                               result={"kind": "rough", **result.model_dump(mode="json"), "input": req.model_dump(mode="json")})
        session.add(row)
        session.commit()
        return row.takeoff_id
