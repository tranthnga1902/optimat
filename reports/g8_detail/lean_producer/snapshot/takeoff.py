"""Gộp phần thô của mọi mặt bằng thành một bảng: công tác theo tầng, tổng theo công tác, vật liệu mua về.

    compute_rough(RoughRequest)      công thức chốt duy nhất (trang kiểm tra gửi lên dữ liệu đã sửa)
    rough_from_drawing(drawing, ...) dựng RoughRequest từ nhận dạng tự động (tường, cửa, cột, tên phòng, dầm suy)
"""
from __future__ import annotations

import math
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .. import config
from ..catalog.repository import Catalog, default_catalog
from ..drawing.concepts import layer_role, match_block_signal
from ..drawing.encoding import normalize
from ..drawing.review import ReviewOpening, ReviewWall
from ..drawing.registry import floors_of
from .areas import PlanParams, area_works, plan_geometry, room_labels
from .beams import Beam, beam_joints, beam_works, infer_beams, is_tie_beam
from .checks import cross_checks, envelope_by_orientation, floor_area_checks
from .columns import Column, column_overlaps, column_works, detect_columns, schedule_column_works
from .materials import materials_for_works
from .models import RAW_CLASSES, WORKS, MaterialLine, ProjectParams, RoughBill, WorkItem, worst_status
from .stairs import Stair, building_stairs, stair_works
from .status import assign_status
from .foundations import _neg, foundation_works, footing_rects
from .rebar import (RebarRow, RebarScopeAssignment, RebarSourceRef, RebarTableManifest,
                    read_rebar_schedules)
from .secondary import (LinearMember, deduct_ties, drop_slab_under_roof, lintel_under_beam, linear_works,
                        normalize_ties, read_secondary, roof_works)
from .steel import steel_works
from .structural import ColumnSpan, floor_count, read_structural
from ..schemas import WallGroup
from .wall_groups import final_wall_groups
from .walls import review_input_from_takeoff, wall_works


class RoomLabel(BaseModel):
    kind: str
    text: str
    x: float
    y: float


def _beam_floor(value: str) -> str:
    if not re.fullmatch(r"T[1-9]\d*|MONG|MAI|ST", value):
        raise ValueError("Khóa tầng dầm phải là T1, T2… hoặc MONG/MAI/ST.")
    return value


class BeamViewScope(BaseModel):
    floors: list[str] = Field(min_length=1)
    evidence: str = Field(min_length=1)

    @field_validator("floors")
    @classmethod
    def _floors(cls, values):
        if len(set(values)) != len(values):
            raise ValueError("Phạm vi dầm có tầng lặp.")
        return [_beam_floor(v) for v in values]

    @field_validator("evidence")
    @classmethod
    def _evidence(cls, value):
        if not value.strip():
            raise ValueError("Cần căn cứ xác nhận phạm vi dầm.")
        return value


class BeamFloorSource(BaseModel):
    source: Literal["structural", "manual"]
    ref: str = Field(min_length=1)
    evidence: str = Field(min_length=1)

    @field_validator("ref", "evidence")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Nguồn dầm và căn cứ chọn không được để trắng.")
        return value


class PlanInput(PlanParams):
    """Một mặt bằng đã (hoặc chưa) qua trang kiểm tra."""
    height_mm: Optional[float] = None           # trống: chưa có chiều cao tầng, mặt bằng chưa tính
    height_source: Optional[str] = None         # truy vết trạng thái A/B/C/D: "cao độ tầng trên" (B) | "nhập tay" (C) | "chưa có" (D)
    walls: list[ReviewWall]
    openings: list[ReviewOpening] = Field(default_factory=list)
    columns: list[Column] = Field(default_factory=list)
    beams: Optional[list[Beam]] = None          # None: suy từ tường và cột
    beam_floor_key: Optional[str] = None
    beam_floor_evidence: Optional[str] = None
    stairs: list[Stair] = Field(default_factory=list)
    labels: list[RoomLabel] = Field(default_factory=list)
    wall_systems: dict[str, Optional[str]] = Field(default_factory=dict)   # tường -> phương án tường đã quy đổi
    found: dict[str, list[str]] = Field(default_factory=dict)   # vai trò phần thô (ngoài cột) -> layer/block thấy trên mặt bằng
    members: list[LinearMember] = Field(default_factory=list)   # giằng tường, sê nô trên mặt bằng này (giằng trừ khỏi xây)

    @model_validator(mode="after")
    def _beam_floor_pair(self):
        if (self.beam_floor_key is None) != (self.beam_floor_evidence is None):
            raise ValueError("Khóa tầng dầm và căn cứ tầng phải đi cùng nhau.")
        if self.beam_floor_key is not None:
            _beam_floor(self.beam_floor_key)
            if not self.beam_floor_evidence.strip():
                raise ValueError("Cần căn cứ xác nhận tầng của mặt bằng.")
        return self


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
    plan_scope_confirmed: bool = False
    structural_beams: dict[str, list[Beam]] = Field(default_factory=dict)   # dầm đọc từ mặt bằng kết cấu, theo tiêu đề
    structural_floors: dict[str, int] = Field(default_factory=dict)        # đối chiếu số tầng với scope; không dùng làm số nhân
    beam_view_scopes: dict[str, BeamViewScope] = Field(default_factory=dict)
    beam_floor_sources: dict[str, BeamFloorSource] = Field(default_factory=dict)
    column_sections: dict[str, tuple[float, float]] = Field(default_factory=dict)   # tiết diện cột ghi chữ trên bản vẽ kết cấu
    sheets: list[dict] = Field(default_factory=list)       # 14 loại bản vẽ: có / chưa có trong file (drawing/sheets.py)
    notes: list[str] = Field(default_factory=list)         # cảnh báo khi đọc bản vẽ kết cấu
    rebar: list[RebarRow] = Field(default_factory=list)    # dòng bảng thống kê thép đọc từ bản vẽ (rough/rebar.py)
    rebar_sources: list[RebarSourceRef] = Field(default_factory=list)
    rebar_table_manifest: list[RebarTableManifest] = Field(default_factory=list)
    rebar_scope_assignments: list[RebarScopeAssignment] = Field(default_factory=list)  # chỉ lưu vết; áp mới phải reupload
    rebar_conversion: dict[str, dict] = Field(default_factory=dict)  # source_id -> log chuyển DWG gốc
    members: list[LinearMember] = Field(default_factory=list)   # giằng tường, sê nô đọc từ mặt bằng kết cấu
    column_schedule: list[ColumnSpan] = Field(default_factory=list)   # bảng thống kê cột: có thì bê tông, cốp pha cột lấy từ đây

    @model_validator(mode="after")
    def _unique_plan_names(self):
        for view in self.beam_view_scopes:
            if view not in self.structural_beams:
                raise ValueError(f"Phạm vi dầm tham chiếu view không có: {view}.")
        for floor, choice in self.beam_floor_sources.items():
            _beam_floor(floor)
            if choice.source == "structural":
                if choice.ref not in self.structural_beams:
                    raise ValueError(f"Nguồn dầm không có view {choice.ref}.")
                scope = self.beam_view_scopes.get(choice.ref)
                if floor not in (scope.floors if scope else floors_of(choice.ref)):
                    raise ValueError(f"View {choice.ref} không phủ tầng {floor}.")
            else:
                plans = [p for p in self.plans if p.name == choice.ref]
                if len(plans) != 1:
                    raise ValueError(f"Nguồn dầm nhập tay không xác định duy nhất: {choice.ref}.")
                p = plans[0]
                scope = [p.beam_floor_key] if p.beam_floor_key else floors_of(p.name)
                if (scope != [floor] or not p.beams or not any(b.keep for b in p.beams)
                        or any(b.source != "manual" for b in p.beams if b.keep)):
                    raise ValueError(f"Nguồn nhập tay {choice.ref} cần dầm manual và đúng một tầng {floor}.")
        # tên mặt bằng là khóa (dầm, thép, chi tiết theo tầng): bản vẽ có hai tiêu đề trùng thì đánh số thêm
        seen: dict[str, int] = {}
        for p in self.plans:
            seen[p.name] = seen.get(p.name, 0) + 1
            if seen[p.name] > 1:
                p.name = f"{p.name} ({seen[p.name]})"
        if self.rebar_scope_assignments:
            note = ("Mapping phạm vi thép trong JSON chỉ lưu vết, không áp mới hoặc khử trùng lại; "
                    "muốn áp/thay mapping cần gửi lại đúng file qua /api/takeoff/structural.")
            if note not in self.notes:
                self.notes.append(note)
        return self


class WorkTotal(BaseModel):
    code: str
    name: str
    unit: str
    quantity: Optional[float] = None    # tổng phần đã tính được
    complete: bool = True
    items: int = 0
    status: Optional[str] = None        # xấu nhất trong các dòng góp vào (D, C, B, A)


class GroupTotal(BaseModel):
    """Một trong 5 nhóm vật liệu của đề cương (đặc tả 1A): nhóm ngoài phạm vi phần thô vẫn liệt kê, ghi rõ."""
    group_id: str
    name: str
    in_scope: bool = True               # False: nhóm hoàn thiện, kết cấu thép bao che, khác: ngoài phạm vi phần thô
    materials: list[str] = Field(default_factory=list)   # mã (hoặc tên) vật liệu thuộc nhóm trong bảng vật liệu
    weight_kg: Optional[float] = None   # tổng kg của các dòng có khối lượng riêng
    weight_complete: bool = True        # False: có lượng nguồn chưa đủ hoặc chưa đủ dữ liệu quy đổi sang kg
    status: Optional[str] = None


class RoughResult(RoughBill):
    plan_scope_confirmed: bool = False
    wall_groups: list[WallGroup] = Field(default_factory=list)
    wall_group_issues: list[str] = Field(default_factory=list)
    totals: list[WorkTotal] = Field(default_factory=list)
    beams: dict[str, list[Beam]] = Field(default_factory=dict)       # dầm đã dùng theo mặt bằng (kể cả dầm suy)
    plan_beams: dict[str, list[Beam]] = Field(default_factory=dict)  # nguồn plan/infer local, không trộn geometry KC
    structural_beams: dict[str, list[Beam]] = Field(default_factory=dict)  # geometry view KC gốc, không đổi khóa tầng
    takeoff_id: Optional[int] = None                                   # dòng đã lưu trong takeoff_results (nếu có)
    formwork: list[WorkTotal] = Field(default_factory=list)            # cốp pha cộng theo cấu kiện (mỗi cấu kiện một dòng)
    by_group: list[GroupTotal] = Field(default_factory=list)           # vật liệu gộp theo 5 nhóm (đầu vào bộ tối ưu)
    by_class: list[GroupTotal] = Field(default_factory=list)           # gộp theo loại vật liệu thô (RAW_CLASSES), group_id = mã loại
    status: Optional[str] = None                                       # xấu nhất của toàn bảng (chỉ để hiển thị nhanh)
    # tường bao theo hướng nhà (đặc tả mục 11, vỏ bao che): mặt bằng -> hướng B/Đ/N/T -> gross, cửa, net (m²), dài (m);
    # chỉ có khi ProjectParams.north_deg được nhập
    envelope_by_orientation: dict[str, dict[str, dict[str, float]]] = Field(default_factory=dict)


def _wall_length(p: PlanInput) -> float:
    return sum(math.hypot(w.x2 - w.x1, w.y2 - w.y1) for w in p.walls if w.keep and w.masonry)


def _title_key(name: str) -> str:
    return normalize(re.sub(r"\s*\(\d+\)$", "", name))


def _floor_key(name: str):
    """Mặt bằng kết cấu: cùng tầng (floors_of) là trùng dù khác tên ("MÓNG - ĐÀ KIỀNG" và "ĐÀ KIỀNG" đều là MONG)."""
    from ..drawing.registry import floors_of
    return tuple(floors_of(name)) or _title_key(name)


def duplicate_plans(sizes: dict[str, float], key=_title_key) -> dict[str, str]:
    """Mặt bằng cùng tiêu đề (bỏ số "(2)" đánh thêm khi trùng tên) là một tầng vẽ nhiều lần (bản nội thất + bản kích
    thước) hoặc tiêu đề lặp làm khung tìm tách một mặt bằng thành hai mảnh: chỉ tính bản nhận được nhiều nhất
    (sizes: tên -> tổng chiều dài tường, hoặc dầm với mặt bằng kết cấu).
    Không so hình học được: hai bản của cùng một tầng nhận tường lệch nhau tới 100% (Bietthu7 tầng 2: 0 m và 29 m).
    Trả {tên bản bỏ qua: tên bản được tính}."""
    groups: dict[str, list[str]] = {}
    for name in sizes:
        groups.setdefault(key(name), []).append(name)
    out = {}
    for g in groups.values():
        keep = max(g, key=sizes.get)
        out.update({n: keep for n in g if n != keep})
    return out


def _beam_allocation(req: RoughRequest, skipped: set[str]):
    """Một owner mỗi tầng; scope không chứng minh hai bản vẽ cùng hệ tọa độ."""
    scopes, candidates, invalid = {}, {}, {}
    pending = []
    for view in req.structural_beams:
        explicit = req.beam_view_scopes.get(view)
        scope = explicit.floors if explicit else floors_of(view)
        scopes[view] = scope
        if not scope:
            pending.append((view, "chưa xác định phạm vi tầng của view dầm"))
            continue
        if view in req.structural_floors and req.structural_floors[view] != len(scope):
            invalid[view] = "số tầng khai báo không khớp phạm vi tầng của view"
        for floor in scope:
            candidates.setdefault(floor, []).append(view)
    plan_floors = {}
    local = {}
    for p in req.plans:
        if p.name in skipped:
            continue
        scope = [p.beam_floor_key] if p.beam_floor_key else floors_of(p.name)
        floor = scope[0] if len(scope) == 1 else None
        plan_floors[p.name] = floor
        if floor:
            local.setdefault(floor, []).append(p.name)
    owners = {}
    for floor in sorted(set(candidates) | set(local) | set(req.beam_floor_sources)):
        views = candidates.get(floor, [])
        choice = req.beam_floor_sources.get(floor)
        if choice:
            if choice.source == "manual" and choice.ref in skipped:
                pending.append((floor, "mặt bằng dầm nhập tay được chọn đang bị loại do trùng tiêu đề"))
                continue
            if choice.source == "structural" and choice.ref in invalid:
                pending.append((floor, f"{choice.ref}: {invalid[choice.ref]}"))
                continue
            owners[floor] = (choice.source, choice.ref, "C", choice.evidence)
        elif len(views) == 1 and views[0] not in invalid:
            view = views[0]
            explicit = req.beam_view_scopes.get(view)
            owners[floor] = ("structural", view, "C" if explicit else "B",
                             explicit.evidence if explicit else f"phạm vi suy từ tiêu đề {view}")
        elif views:
            reason = "; ".join(f"{v}: {invalid[v]}" for v in views if v in invalid)
            pending.append((floor, reason or f"nhiều view cùng tầng ({', '.join(sorted(views))}); chưa chọn owner"))
        elif len(local.get(floor, [])) == 1:
            name = local[floor][0]
            p = next(p for p in req.plans if p.name == name)
            owners[floor] = ("plan", name, "C" if p.beam_floor_key else "B",
                             p.beam_floor_evidence or f"tầng suy từ tiêu đề {name}")
        else:
            pending.append((floor, "nhiều mặt bằng kiến trúc cùng tầng; chưa chọn nguồn dầm"))
    return owners, pending, plan_floors, scopes


def _beam_trace(items, status, evidence, missing=()):
    for item in items:
        item.status = worst_status(item.status, status)
        if item.quantity is not None and not item.missing:
            item.inputs.append(f"phạm vi/nguồn dầm: {status}")
        item.evidence.append(evidence)
        item.missing = list(dict.fromkeys([*item.missing, *missing]))


def _pending_beams(plan, reason):
    return [WorkItem(code=code, name=WORKS[code][0], unit=WORKS[code][1], plan=plan,
                     element="phạm vi dầm chờ xác nhận", quantity=None, status="D",
                     formwork_of="DAM" if code == "COP_PHA" else None, missing=[reason], evidence=[reason])
            for code in ("DAM", "COP_PHA")]


def compute_rough(req: RoughRequest, catalog: Catalog | None = None) -> RoughResult:
    catalog = catalog or default_catalog()
    params = req.params
    works: list[WorkItem] = []
    warnings: list[str] = []
    used_beams: dict[str, list[Beam]] = {}
    plan_beams = {p.name: list(p.beams or []) for p in req.plans}
    envelope: dict[str, dict] = {}
    floor_areas: dict[str, float] = {}         # m² sàn từng tầng (trong tim tường bao) cho kiểm tra KH05
    by_param: set[tuple[str, str]] = set()     # (mặt bằng, phương án tường) lấy từ ProjectParams.wall_systems_by_class
    unknown = set(params.wall_systems_by_class.values()) - set(catalog.wall_systems.wall_system_id)
    unknown_cls = set(params.material_classes) - set(RAW_CLASSES)
    if unknown_cls:
        raise ValueError(f"Loại vật liệu không có: {', '.join(sorted(unknown_cls))}. Chọn trong: {', '.join(RAW_CLASSES)}.")
    if unknown:
        raise ValueError(f"Phương án tường theo lớp không có trong danh mục: {', '.join(sorted(unknown))}.")
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
    by_name = {p.name: p for p in req.plans}
    length = {p.name: _wall_length(p) for p in req.plans}
    dup = {} if req.plan_scope_confirmed else duplicate_plans(length)
    scope_issues = []
    if req.plan_scope_confirmed:
        warnings.append("Phạm vi mặt bằng kiến trúc do người dùng chọn: " + ", ".join(length))
    for name, keep in dup.items():
        warnings.append(f"QU-05: \"{name}\" trùng tiêu đề với \"{keep}\": coi là một tầng, chỉ tính \"{keep}\" "
                        f"(tường {length[keep] / 1000:.1f} m, bản bỏ qua {length[name] / 1000:.1f} m). "
                        "Nếu là hai tầng khác nhau, sửa tiêu đề trên bản vẽ.")
    beam_owners, beam_pending, plan_floors, beam_scopes = _beam_allocation(req, set(dup))
    beam_sources = {}
    for plan, reason in beam_pending:
        works += _pending_beams(plan, reason)
        warnings.append(f"O01: {plan}: {reason}.")
    ground_keep = {keep for name, keep in dup.items() if by_name[name].is_ground}
    for p in req.plans:
        if p.name in dup:
            continue
        if p.name in ground_keep and not p.is_ground:     # bản bỏ qua được chọn làm tầng trệt: bản được tính thay nó
            p = p.model_copy(update={"is_ground": True})
        floor = plan_floors.get(p.name)
        owner = beam_owners.get(floor)
        selected = owner and owner[0] in ("plan", "manual") and owner[1] == p.name
        # Tầng chưa map vẫn giữ phần số plan; không dùng KC tầng khác để tắt suy.
        unresolved = floor is None and bool(req.structural_beams)
        local_allowed = selected or floor is None
        beams = (p.beams if p.beams is not None else infer_beams(p.columns, p.walls)) if local_allowed else []
        beams, warn = beam_joints(beams, p.columns, params)
        warnings += warn
        used_beams[p.name] = beams
        if p.beams is None:
            plan_beams[p.name] = beams
        beam_sources[p.name] = {b.source for b in beams if b.keep}
        w, warn = beam_works(p.name, beams, params)
        status = owner[2] if selected else "B"
        trace = f"{p.name}; tầng {floor or 'chưa xác định'}; " + (owner[3] if selected else "chưa có mapping tầng")
        issue = ["chưa loại trừ chồng phạm vi với view KC chưa ánh xạ tầng"] if unresolved else []
        if any(not s for s in beam_scopes.values()) and selected and floor not in req.beam_floor_sources:
            issue.append("còn view KC chưa xác định phạm vi; chưa loại trừ chồng tầng")
        _beam_trace(w, "D" if issue else status, trace, issue)
        works += w
        warnings += warn
        if p.beams is not None and not selected and floor is not None:
            warnings.append(f"O01: {p.name}: dầm plan chưa được chọn; không cộng thêm vào nguồn tầng {floor}.")
        if local_allowed and p.beams is not None and not any(b.keep for b in p.beams):
            warnings.append(f"O01: {p.name}: beams=[] hoặc toàn bộ keep=False: không suy dầm, chưa xác nhận thiết kế không có dầm.")
            works += _pending_beams(p.name, "dầm plan rỗng hoặc đã loại hết; chưa xác nhận phạm vi dầm đã đủ")
        for role, names in p.found.items():
            label, hint = FOUND_HINT.get(role, (role, "kiểm tra"))
            if (role == "STAIR" and p.stairs) or (role == "BEAM" and (p.beams is not None or owner and owner[0] == "structural")):
                continue
            warnings.append(f"{p.name}: bản vẽ có {label} ({', '.join(names[:3])}): {hint}.")
        if not p.height_mm:
            if length[p.name] > 0:
                scope_issues.append(f"{p.name}: chưa có chiều cao tầng.")
            warnings.append(f"{p.name}: chưa có chiều cao tầng, chưa tính phần thô của mặt bằng này.")
            continue
        kept_ids = {w.id for w in p.walls if w.keep}
        if any(o.keep and o.wall not in kept_ids for o in p.openings):
            scope_issues.append(f"{p.name}: còn lỗ mở chưa gán tường, cần gán hoặc loại khỏi phạm vi.")
        overlaps = column_overlaps(p.columns, [w for w in p.walls if w.masonry])
        known = set(catalog.materials.material_id)
        # phương án tường quy đổi lại từ mã vật liệu (người dùng có thể đã đổi vật liệu, lớp tường, vẽ thêm tường)
        systems = {w.id: catalog.resolve_wall([w.mat], w.cls).wall_system_id if w.mat in known else p.wall_systems.get(w.id)
                   for w in p.walls}
        for w in p.walls:          # tường bản vẽ không ghi vật liệu: phương án người dùng chọn theo lớp (C)
            if w.masonry and systems.get(w.id) is None and (chosen := params.wall_systems_by_class.get(w.cls)):
                systems[w.id] = chosen
                by_param.add((p.name, chosen))
        warnings += _section_checks(p, beams, params, req.column_sections)
        wall_params = params
        depths = sorted({b.d_mm for b in beams if b.keep and b.d_mm})
        if params.beam_depth_mm is None and len(depths) == 1:     # dầm nhập tay có cao dầm: dùng để trừ khỏi tường
            wall_params = params.model_copy(update={"beam_depth_mm": depths[0]})
        for fn in (lambda: wall_works(p.name, p.height_mm, p.walls, p.openings, wall_params, catalog, systems, overlaps),
                   # có bảng thống kê cột thì cột kiến trúc chỉ dùng trừ khối xây (không đếm cột hai lần)
                   lambda: ([], []) if req.column_schedule else column_works(p.name, p.columns, p.height_mm, params, beams),
                   lambda: stair_works(p.name, p.stairs, p.height_mm, params)):
            w, warn = fn()
            if req.structural_beams and wall_params.beam_depth_mm is None:
                for item in w:
                    if item.code in ("XAY", "TRAT"):
                        item.missing.append("chưa có cao dầm riêng mặt bằng để trừ tường; mapping KC không chứng minh căn chỉnh")
                        item.status = "D"
            if wall_params is not params:
                depth_inputs = [(p.name, b) for b in beams if b.keep and b.d_mm == wall_params.beam_depth_mm]
                depth_source = "; ".join(f"{view}: {b.id} ({b.source}), d={b.d_mm:g} mm" for view, b in depth_inputs)
                for item in w:
                    if item.code in ("XAY", "TRAT"):
                        for dimension in item.dimensions:
                            dimension.field_sources["height_m"] = "PlanInput.height_mm − cao dầm lấy từ " + depth_source
                            dimension.source += "; cao dầm: " + depth_source
            works += w
            warnings += warn
        # S08-04: không cộng trùng lanh tô – dầm, giằng – tường
        warnings += lintel_under_beam(works, p.name, p.height_mm, p.walls, p.openings, systems, wall_params, catalog)
        tie_groups = normalize_ties(p.members, plan_context=True)
        warnings += deduct_ties(works, p.name, p.walls, systems, p.members, catalog,
                                tie_groups=tie_groups,
                                wall_height_mm=p.height_mm - (wall_params.beam_depth_mm or 0.0),
                                openings=p.openings, column_len_in_walls=overlaps)
        w, warn = linear_works(p.name, p.members, tie_groups=tie_groups)
        works += w
        warnings += warn
        geom = plan_geometry([w for w in p.walls if w.masonry], [(l.kind, l.text, l.x, l.y) for l in p.labels])
        w, warn = area_works(geom, params, p)
        outline = p.outline_area_m2 if p.outline_area_m2 is not None else geom.outline_area_m2 if geom.closed else None
        if outline:
            floor_areas[p.name] = outline
        works += w
        warnings += warn
        works += _slab_form_deduction(p.name, beams, p.columns, params)
        env = envelope_by_orientation(p.walls, p.openings, p.height_mm, params.north_deg)
        if env:
            envelope[p.name] = env
    # Giữ geometry theo view gốc, kể cả nguồn chưa được chọn; không coi mapping tầng là căn chỉnh XY.
    used_beams.update(req.structural_beams)
    for floor, (kind, view, status, evidence) in sorted(beam_owners.items()):
        if kind != "structural":
            continue
        beams, warn = beam_joints(req.structural_beams[view], [], params, footing_rects(params.foundations, view))
        warnings += warn
        used_beams[view] = beams
        label = f"{view} → {floor}"
        beam_sources[label] = {b.source for b in beams if b.keep}
        w, warn = beam_works(label, beams, params)
        w += _slab_form_deduction(label, beams, [], params)
        trace = f"view {view}; tầng đích {floor}; phạm vi gốc {', '.join(beam_scopes[view])}; {evidence}"
        issue = []
        if any(not s for s in beam_scopes.values()) and floor not in req.beam_floor_sources:
            issue.append("còn view KC chưa xác định phạm vi; chưa loại trừ chồng tầng")
        if not any(b.keep for b in beams):
            w += _pending_beams(label, "view KC rỗng hoặc toàn bộ dầm đã loại; chưa xác nhận đủ phạm vi")
        _beam_trace(w, "D" if issue else status, trace, issue)
        works += w
        warnings += warn
    works += schedule_column_works(req.column_schedule)
    for fn in (lambda: linear_works("bản vẽ kết cấu", req.members,
                                         tie_groups=normalize_ties(req.members, plan_context=False)), lambda: roof_works(params)):
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
    # kiểm tra chéo (đặc tả mục 7): tỷ số trên m² sàn các tầng (sàn = bê tông sàn / dày sàn khi có)
    slab_m2 = None
    if params.slab_thickness_mm:
        san = [w.quantity for w in works if w.code == "SAN" and w.quantity is not None]
        slab_m2 = sum(san) / (params.slab_thickness_mm / 1000) if san else None
    warnings += cross_checks(works, slab_m2)
    warnings += floor_area_checks(floor_areas, params.building_area_m2)
    order = list(WORKS)
    plan_order = {p.name: i for i, p in enumerate(req.plans)}
    works.sort(key=lambda w: (order.index(w.code), plan_order.get(w.plan, len(plan_order))))
    # trạng thái A/B/C/D (đặc tả mục 3): chiều cao tầng nhập tay trên PlanInput mà không ghi nguồn thì coi là nhập tay (C)
    for w in works:
        if w.code in ("XAY", "TRAT") and (w.plan, w.wall_system_id) in by_param:
            w.evidence.append("phương án tường theo thông số công trình (wall_systems_by_class), bản vẽ không ghi vật liệu")
    assign_status(works, params,
                  {p.name: p.height_source or ("nhập tay" if p.height_mm else "chưa có") for p in req.plans},
                  beam_sources)
    for collision in sorted(set(plan_beams) & set(req.structural_beams)):
        used_beams.pop(collision, None)
        warnings.append(f"O01: tên plan/view KC trùng '{collision}': bỏ khóa khỏi beams legacy để tránh ghi đè nguồn; "
                        "xem plan_beams và structural_beams riêng, không coi hai nguồn đã căn chỉnh XY.")
    bill = materials_for_works(works, params, catalog)
    if params.material_classes:            # chỉ xuất loại vật liệu người dùng chọn; công tác vẫn tính đủ
        dropped = [m for m in bill.materials if m.raw_class not in params.material_classes]
        bill.materials = [m for m in bill.materials if m.raw_class in params.material_classes]
        if dropped:
            warnings.append(f"Chỉ bóc loại vật liệu đã chọn ({', '.join(RAW_CLASSES[c] for c in params.material_classes)}); "
                            f"bỏ {len(dropped)} dòng vật liệu loại khác.")
    totals = []
    for code in order:
        items = [w for w in works if w.code == code]
        if not items:
            continue
        known_q = [w.quantity for w in items if w.quantity is not None]
        totals.append(WorkTotal(code=code, name=WORKS[code][0], unit=WORKS[code][1], items=len(items),
                                quantity=round(sum(known_q), 3) if known_q else None,
                                complete=len(known_q) == len(items) and not any(w.missing or w.status == "D" for w in items),
                                status=worst_status(*(w.status for w in items))))
    formwork = []
    for code in ("LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "GIANG_TUONG", "SE_NO", "MAI", "MONG"):
        items = [w for w in works if w.code == "COP_PHA" and w.formwork_of == code]
        if items:
            known_q = [w.quantity for w in items if w.quantity is not None]
            formwork.append(WorkTotal(code=code, name="Cốp pha " + WORKS[code][0].replace("Bê tông ", ""), unit="m²",
                                      items=len(items), quantity=round(sum(known_q), 3) if known_q else None,
                                      complete=len(known_q) == len(items) and not any(w.missing or w.status == "D" for w in items),
                                      status=worst_status(*(w.status for w in items))))
    attach_prices(bill.materials, catalog, actual_only=req.plan_scope_confirmed)
    wall_groups, wall_group_issues = final_wall_groups(works, params, catalog)
    return RoughResult(works=works, intermediates=bill.intermediates, materials=bill.materials,
                       plan_scope_confirmed=req.plan_scope_confirmed,
                       wall_groups=[] if scope_issues or wall_group_issues else wall_groups,
                       wall_group_issues=scope_issues + wall_group_issues,
                       warnings=warnings + bill.warnings, totals=totals, beams=used_beams, formwork=formwork,
                       plan_beams=plan_beams, structural_beams=req.structural_beams,
                       by_group=group_totals(bill.materials, catalog), by_class=class_totals(bill.materials),
                       envelope_by_orientation=envelope,
                       status=worst_status(*(w.status for w in works), *(m.status for m in bill.materials)))


def attach_prices(materials: list[MaterialLine], catalog: Catalog, actual_only: bool = False) -> None:
    """Giá thấp nhất cùng đơn vị cho từng vật liệu có mã (giá đại lý, báo giá, công bố giá). Khác đơn vị thì để trống,
    không tự quy đổi (bao, kg, tấn...)."""
    from ..catalog.pricing import has_price_source, price_offers, select_best_offer
    for m in materials:
        m.best_price = None
        m.price_source = None
        m.est_cost = None
    ids = sorted({m.material_id for m in materials if m.material_id})
    if not ids:
        return
    offers = price_offers(catalog, ids)
    kinds = dict(zip(catalog.materials.material_id, catalog.materials.data_kind))
    for m in materials:
        best, _ = select_best_offer(offers.get(m.material_id or "", []), m.unit, kinds.get(m.material_id), actual_only)
        if best is None:
            continue
        m.best_price = best.price
        level = "BULLETIN (công bố tham khảo)" if best.is_reference else best.price_level
        if best.source == "price_records" and not best.is_reference:
            level = f"{best.price_level} (giá lịch sử tham khảo)"
        terms = {"YES": "đã gồm", "NO": "chưa gồm"}
        vat = terms.get(best.vat_included, "chưa rõ") + " VAT"
        freight = terms.get(best.transport_included, "chưa rõ") + " cước giao hàng"
        page = best.url if has_price_source(price_url=best.url) and best.url != best.source_detail else None
        validity = f"hiệu lực đến {best.valid_until}" if best.valid_until else "chưa rõ hiệu lực"
        basis = (level, best.supplier_name or best.supplier_id, best.price_date, best.data_kind,
                 best.source_detail, page, vat, freight, validity)
        m.price_source = " · ".join(x for x in basis if x)
        qty = m.quantity_with_waste if m.quantity_with_waste is not None else m.quantity
        m.est_cost = round(qty * best.price) if qty is not None and m.complete and m.status != "D" else None


# nhóm vật liệu thuộc phạm vi phần thô (đặc tả 1A: chỉ lấp nhóm 1 và 2; nhóm khác liệt kê "ngoài phạm vi")
ROUGH_GROUPS = ("be_tong_cot_thep", "phan_tho")


def group_totals(materials, catalog: Catalog) -> list[GroupTotal]:
    """Gộp bảng vật liệu theo 5 nhóm của danh mục (material_groups, theo sort_order). Vật liệu chưa có mã (danh mục thiếu)
    xếp vào nhóm "chua_ro"."""
    groups = catalog.material_groups.sort_values("sort_order") if not catalog.material_groups.empty else None
    out: list[GroupTotal] = []
    rows = [(str(r.group_id), str(r.name)) for r in groups.itertuples()] if groups is not None else \
        [(g, g) for g in ROUGH_GROUPS]
    for gid, name in rows + [("chua_ro", "Chưa xếp nhóm (danh mục chưa có mã)")]:
        lines = [m for m in materials if (m.group_id or "chua_ro") == gid]
        if gid == "chua_ro" and not lines:
            continue
        kg = [m.weight_kg for m in lines if m.weight_kg is not None]
        out.append(GroupTotal(group_id=gid, name=name, in_scope=gid in ROUGH_GROUPS or gid == "chua_ro",
                              materials=[m.material_id or m.name for m in lines],
                              weight_kg=round(sum(kg), 1) if kg else None,
                              weight_complete=len(kg) == len(lines) and all(m.complete and m.status != "D" for m in lines),
                              status=worst_status(*(m.status for m in lines))))
    return out


def class_totals(materials) -> list[GroupTotal]:
    """Gộp bảng vật liệu theo loại vật liệu thô (RAW_CLASSES, theo thứ tự khai báo); chỉ liệt kê loại có dòng."""
    out = []
    for code, name in RAW_CLASSES.items():
        lines = [m for m in materials if m.raw_class == code]
        if not lines:
            continue
        kg = [m.weight_kg for m in lines if m.weight_kg is not None]
        out.append(GroupTotal(group_id=code, name=name, in_scope=code != "khac", materials=[m.material_id or m.name for m in lines],
                              weight_kg=round(sum(kg), 1) if kg else None,
                              weight_complete=len(kg) == len(lines) and all(m.complete and m.status != "D" for m in lines),
                              status=worst_status(*(m.status for m in lines))))
    return out


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
    subs = [crop(drawing, p.bbox) if p.name != "Toàn bộ bản vẽ" else drawing for p in plans]
    stairs, stair_notes = building_stairs(subs, [p.name for p in plans])
    for i, (p, sub) in enumerate(zip(plans, subs)):
        walls, openings, systems = review_input_from_takeoff(p.result)
        out.append(PlanInput(name=p.name, is_ground=(i == g), height_mm=p.height_mm, height_source=p.height_source,
                             walls=walls, openings=openings, stairs=stairs[i],
                             wall_systems=systems, columns=detect_columns(sub), found=rough_parts(sub),
                             labels=[RoomLabel(kind=k, text=t, x=x, y=y) for k, t, x, y in room_labels(sub)]))
    extra = structural if isinstance(structural, list) else [structural] if structural is not None else []
    params, parts = structural_parts([drawing] + extra, params, structural_scale)
    parts["notes"] = stair_notes + parts["notes"]
    return RoughRequest(file=file, params=params, plans=out, **parts)


def structural_parts(drawings: list, params: ProjectParams | None = None,
                     structural_scale: float | None = None, *,
                     rebar_reads: list[tuple[list[RebarRow], list[str]]] | None = None
                     ) -> tuple[ProjectParams, dict]:
    """Phần đọc từ bản vẽ kết cấu (dầm, cột, móng, bảng thép, cấu kiện phụ) cho RoughRequest; trang kiểm tra gọi riêng
    khi người dùng mở thêm bản vẽ kết cấu. Trả (thông số đã bổ sung móng / cao lanh tô đọc được, các trường còn lại)."""
    if rebar_reads is not None and len(rebar_reads) != len(drawings):
        raise ValueError("rebar_reads phải có đúng một kết quả cho mỗi Drawing.")
    params = (params or ProjectParams()).model_copy()
    beams, notes, sheets, col_sections, rebar, members, schedule = {}, [], [], {}, [], [], []
    for index, d in enumerate(drawings):
        rows, warn = rebar_reads[index] if rebar_reads is not None else read_rebar_schedules(d)
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
        schedule += st.column_schedule
        notes += st.warnings
        sheets = [dict(a, co=a["co"] or b["co"], tieu_de=a["tieu_de"] + b["tieu_de"]) for a, b in zip(sheets, st.sheets)] or st.sheets
        if not params.foundations:
            params.foundations = st.foundations
    return params, dict(structural_beams=beams, sheets=sheets, notes=notes, structural_floors={v: floor_count(v) for v in beams},
                        column_sections=col_sections, column_schedule=schedule, rebar=rebar, members=members)


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
