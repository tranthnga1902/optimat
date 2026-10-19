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
from .beams import Beam, beam_works, infer_beams
from .columns import Column, column_overlaps, column_works, detect_columns
from .materials import materials_for_works
from .models import WORKS, ProjectParams, RoughBill, WorkItem
from .stairs import Stair, stair_works
from .steel import foundation_works, steel_works
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
    if not req.plans:
        warnings.append("Không tìm thấy mặt bằng tầng nào trong bản vẽ (bản vẽ kết cấu hoặc thiếu tiêu đề mặt bằng): "
                        "chưa tính được công tác nào.")
    elif not any(p.is_ground for p in req.plans):
        warnings.append("Chưa xác định tầng trệt: chưa tính nền tầng trệt (đệm cát, bê tông lót).")
    for p in req.plans:
        for role, names in p.found.items():
            label, hint = FOUND_HINT.get(role, (role, "kiểm tra"))
            if (role == "STAIR" and p.stairs) or (role == "BEAM" and p.beams is not None):
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
        beams = p.beams if p.beams is not None else infer_beams(p.columns, p.walls)
        wall_params = params
        depths = sorted({b.d_mm for b in beams if b.keep and b.d_mm})
        if params.beam_depth_mm is None and len(depths) == 1:     # dầm nhập tay có cao dầm: dùng để trừ khỏi tường
            wall_params = params.model_copy(update={"beam_depth_mm": depths[0]})
        for fn in (lambda: wall_works(p.name, p.height_mm, p.walls, p.openings, wall_params, catalog, systems, overlaps),
                   lambda: column_works(p.name, p.columns, p.height_mm, params),
                   lambda: stair_works(p.name, p.stairs, p.height_mm, params)):
            w, warn = fn()
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
    for fn in (lambda: foundation_works(params), lambda: steel_works(works, params)):
        w, warn = fn()
        works += w
        warnings += warn
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
    for code in ("LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "MONG"):
        items = [w for w in works if w.code == "COP_PHA" and w.formwork_of == code]
        if items:
            known_q = [w.quantity for w in items if w.quantity is not None]
            formwork.append(WorkTotal(code=code, name="Cốp pha " + WORKS[code][0].replace("Bê tông ", ""), unit="m²",
                                      items=len(items), quantity=round(sum(known_q), 3) if known_q else None,
                                      complete=len(known_q) == len(items)))
    return RoughResult(works=works, intermediates=bill.intermediates, materials=bill.materials,
                       warnings=warnings + bill.warnings, totals=totals, beams=used_beams, formwork=formwork)


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
                       catalog: Catalog | None = None, file: str = "", openings=None) -> RoughRequest:
    """Dựng đầu vào phần thô từ nhận dạng tự động, để trang kiểm tra hiển thị và người dùng sửa."""
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
    return RoughRequest(file=file, params=params or ProjectParams(), plans=out)


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
