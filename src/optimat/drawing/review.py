"""Tính lại khối lượng sau khi người dùng sửa và bổ sung kết quả nhận dạng trên trang Kiểm tra bóc tách.

Trang tính tạm ngay trên trình duyệt để người dùng thấy số thay đổi; khi bấm Xác nhận, máy chủ tính lại bằng
hàm này (một nguồn công thức) và kết quả của máy chủ là kết quả chốt:
    diện tích tường = chiều dài x chiều cao tầng - tổng (rộng x min(cao cửa, chiều cao tầng)) các lỗ mở,
chiều dài theo trục tim hoặc thông thủy (length_rule, walls.net_lengths); lỗ mở của một tường không vượt diện tích tường.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .. import config
from ..catalog.pricing import BillLine, bill_of_materials
from ..catalog.repository import Catalog, default_catalog
from ..schemas import WallGroup
from .walls import LENGTH_RULES, net_lengths


class ReviewWall(BaseModel):
    id: str
    cls: str                                  # lớp chiều dày: 110 | 150 | 220 | 330
    role: str = "partition"                   # envelope | partition
    x1: float
    y1: float
    x2: float
    y2: float
    mat: Optional[str] = None                 # mã vật liệu trong danh mục (GN01, AAC01...), dùng để tra giá
    masonry: bool = True
    keep: bool = True                         # False: người dùng loại bỏ (nhận nhầm)
    src: str = "auto"                         # auto | manual (người dùng vẽ thêm)
    edited: bool = False
    rule: Optional[str] = None                # truy vết: mã quy tắc vật liệu đã khớp khi nhận dạng
    msrc: Optional[str] = None                # truy vết: nguồn vật liệu (text | hatch | layer | none)


class ReviewOpening(BaseModel):
    id: str
    wall: Optional[str] = None
    kind: str = "door"                        # door | window | block
    w: float                                  # rộng (mm)
    h: Optional[float] = None                 # cao (mm); trống: chưa trừ lỗ mở (Quy ước B7)
    keep: bool = True
    src: str = "auto"
    ev: Optional[str] = None                  # truy vết: dấu hiệu nhận ra cửa (block D1, cung cánh cửa, nét kính)


class ReviewPlan(BaseModel):
    project_id: Optional[int] = None          # có PostgreSQL và dự án: kết quả chốt được lưu vào bảng takeoff_results
    file: str
    plan: str
    height_mm: float
    length_rule: str = "tim"                  # tim | thong_thuy
    height_source: Optional[str] = None       # truy vết: nhập tay | cao độ tầng trên | chưa có
    unmatched: dict[str, list[str]] = Field(default_factory=dict)   # truy vết: tín hiệu chưa có quy tắc lúc nhận dạng
    walls: list[ReviewWall]
    openings: list[ReviewOpening] = Field(default_factory=list)


class ReviewResult(BaseModel):
    file: str
    plan: str
    height_mm: float
    length_rule: str = "tim"
    groups: list[WallGroup]
    total_net_area_m2: float
    walls_kept: int
    walls_removed: int
    walls_added: int
    walls_edited: int
    openings_kept: int
    openings_added: int
    confirmed_at: str
    warnings: list[str] = Field(default_factory=list)
    bill: list[BillLine] = Field(default_factory=list)        # vật liệu cần mua và giá đang có trong danh mục
    bill_total: Optional[float] = None                        # tổng tiền vật liệu khi mọi dòng đều có giá
    bill_missing: list[str] = Field(default_factory=list)     # dòng nào thiếu số liệu gì
    takeoff_id: Optional[int] = None                          # dòng đã lưu trong takeoff_results (nếu có)


def compute_review(plan: ReviewPlan, catalog: Catalog | None = None) -> ReviewResult:
    catalog = catalog or default_catalog()
    if plan.height_mm <= 0:
        raise ValueError("Chiều cao tầng phải lớn hơn 0.")
    H = plan.height_mm
    unknown = [c for c in {w.cls for w in plan.walls} if c not in config.WALL_THICKNESS_CLASSES]
    if unknown:
        raise ValueError(f"Lớp tường không hợp lệ: {', '.join(unknown)}.")
    if plan.length_rule not in LENGTH_RULES:
        raise ValueError(f"Quy tắc chiều dài không hợp lệ: {plan.length_rule} (chỉ nhận {', '.join(LENGTH_RULES)}).")
    walls = [w for w in plan.walls if w.keep and w.masonry]
    ids = {w.id for w in walls}
    if plan.length_rule == "thong_thuy":
        # tường bê tông giữ lại vẫn là mặt giao: tính thông thủy trên mọi tường đang giữ
        lengths = net_lengths([(w.id, w.x1, w.y1, w.x2, w.y2, float(w.cls)) for w in plan.walls if w.keep])
    else:
        lengths = {w.id: math.hypot(w.x2 - w.x1, w.y2 - w.y1) for w in walls}
    open_area: dict[str, float] = {}
    warnings = []
    for o in plan.openings:
        if not o.keep:
            continue
        if o.wall not in ids:
            warnings.append(f"Lỗ mở {o.id} không gắn với tường nào đang giữ, không trừ.")
            continue
        if o.h is None:
            warnings.append(f"Lỗ mở {o.id} chưa có chiều cao, không trừ.")
            continue
        open_area[o.wall] = open_area.get(o.wall, 0.0) + o.w * min(o.h, H) / 1e6
    for wid, area in open_area.items():
        gross_w = lengths[wid] * H / 1e6
        if area > gross_w + 1e-6:
            warnings.append(f"Tường {wid}: lỗ mở {area:.2f} m² lớn hơn diện tích tường {gross_w:.2f} m², chỉ trừ bằng diện "
                            "tích tường. Kiểm tra cửa gắn nhầm tường hoặc cửa trùng.")
            open_area[wid] = gross_w
    known = set(catalog.materials.material_id)
    system_of: dict[str, Optional[str]] = {}
    for w in walls:
        if w.mat is None:
            continue
        if w.mat not in known:
            warnings.append(f"Tường {w.id}: mã vật liệu {w.mat} không có trong danh mục, không tra giá được.")
            continue
        res = catalog.resolve_wall([w.mat], w.cls)
        system_of[w.id] = res.wall_system_id
        if res.note:
            warnings.append(f"Tường {w.id}: {res.note}")
    groups = []
    # mỗi phương án tường (hay mã vật liệu khi chưa quy đổi được) một nhóm: bảng vật liệu áp đúng định mức từng phương án
    kind = lambda w: system_of.get(w.id) or w.mat or ""  # noqa: E731
    for cls, role, k in sorted({(w.cls, w.role, kind(w)) for w in walls}):
        members = [w for w in walls if w.cls == cls and w.role == role and kind(w) == k]
        length_m = sum(lengths[w.id] for w in members) / 1000
        gross = length_m * H / 1000
        opening = sum(open_area.get(w.id, 0.0) for w in members)
        by_mat: dict[str, float] = {}
        for w in members:
            if w.mat:
                by_mat[w.mat] = by_mat.get(w.mat, 0.0) + lengths[w.id]
        design = max(by_mat, key=by_mat.get) if by_mat else None
        system = next((system_of.get(w.id) for w in members if w.mat == design and system_of.get(w.id)), None)
        groups.append(WallGroup(
            wall_type=cls, role=role, length_m=round(length_m, 2), gross_area_m2=round(gross, 2),
            opening_area_m2=round(opening, 2), net_area_m2=round(max(0.0, gross - opening), 2),
            min_confidence=1.0, design_material_id=design, design_wall_system_id=system,
            design_material_share=round(by_mat[design] / (length_m * 1000), 3) if design and length_m else 0.0))
    if any(w.mat is None for w in walls):
        warnings.append("Còn tường chưa có vật liệu theo thiết kế.")
    bill = bill_of_materials(groups, catalog)
    role_vi = {"envelope": "bao che", "partition": "ngăn"}
    bill_missing = [f"Tường {b.wall_type} {role_vi.get(b.role, b.role)}, {'vữa' if b.kind == 'mortar' else 'vật liệu'}"
                    f"{' ' + b.material_id if b.material_id else ''}: thiếu {', '.join(b.missing)}" for b in bill if b.missing]
    costs = [b.est_cost for b in bill]
    return ReviewResult(
        bill=bill, bill_missing=bill_missing,
        bill_total=round(sum(costs)) if costs and all(c is not None for c in costs) else None,
        file=plan.file, plan=plan.plan, height_mm=H, length_rule=plan.length_rule, groups=groups,
        total_net_area_m2=round(sum(g.net_area_m2 for g in groups), 2),
        walls_kept=len(walls), walls_removed=sum(1 for w in plan.walls if not w.keep),
        walls_added=sum(1 for w in plan.walls if w.src == "manual" and w.keep),
        walls_edited=sum(1 for w in plan.walls if w.edited and w.src != "manual" and w.keep),
        openings_kept=sum(1 for o in plan.openings if o.keep and o.wall in ids),
        openings_added=sum(1 for o in plan.openings if o.src == "manual" and o.keep),
        confirmed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), warnings=warnings)


def save_review(result: ReviewResult, plan: ReviewPlan) -> Optional[int]:
    """Lưu kết quả chốt vào takeoff_results (cột result: kết quả + dữ liệu người dùng đã sửa). Không có
    PostgreSQL hoặc không gắn dự án thì không lưu. Dự án không tồn tại thì báo lỗi."""
    from ..db.session import get_database_url, get_engine
    if plan.project_id is None or not get_database_url():
        return None
    from sqlalchemy.orm import Session

    from ..db.models import Project, TakeoffResultRow
    with Session(get_engine()) as session:
        if session.get(Project, plan.project_id) is None:
            raise LookupError(f"Không có dự án {plan.project_id}.")
        row = TakeoffResultRow(project_id=plan.project_id, confirmed_at=datetime.fromisoformat(result.confirmed_at),
                               result={**result.model_dump(mode="json"), "input": plan.model_dump(mode="json")})
        session.add(row)
        session.commit()
        return row.takeoff_id
