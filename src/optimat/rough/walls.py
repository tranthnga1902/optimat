"""Công tác từ tường đã chốt trên trang Kiểm tra bóc tách: xây, trát, lanh tô (Quy ước B3, đặc tả mục 3.1–3.3).

Kích thước theo trục tim tường, H là chiều cao tầng.
    cao xây      = H - cao dầm (chưa nhập cao dầm thì không trừ, có cảnh báo)
    xây (m³)     = Σ dài × cao xây × dày - Σ lỗ cửa × dày - thể tích lanh tô - thể tích cột nằm trong tường
    lỗ cửa (m²)  = rộng × min(cao cửa, cao xây)
    lanh tô (m³) = Σ (rộng lỗ + 2 × gối) × dày tường × cao lanh tô, mỗi lỗ một lanh tô
    trát (m²)    = 2 mặt × (dài × cao xây - lỗ cửa); tường bao tách mặt trong và mặt ngoài
    cốp pha lanh tô (m²) = Σ rộng lỗ × dày tường (đáy) + 2 × (rộng lỗ + 2 × gối) × cao lanh tô (hai thành)
Dày khối xây lấy theo phương án tường (masonry_thickness_mm); chưa có phương án thì lấy dày danh nghĩa của lớp tường.
"""
from __future__ import annotations

import math
from typing import Optional

import pandas as pd

from ..catalog.repository import Catalog
from ..drawing.review import ReviewOpening, ReviewWall
from .materials import _fmt
from .models import WORKS, ProjectParams, WorkItem

ROLE_VI = {"envelope": "bao che", "partition": "ngăn"}


def _work(code: str, quantity: Optional[float], **kw) -> WorkItem:
    name, unit = WORKS[code]
    return WorkItem(code=code, name=name, unit=unit,
                    quantity=None if quantity is None else round(max(0.0, quantity), 3), **kw)


def _thickness_m(system_id: Optional[str], cls: str, view: pd.DataFrame) -> tuple[float, str]:
    if system_id and system_id in view.index:
        t = pd.to_numeric(view.loc[system_id].get("masonry_thickness_mm"), errors="coerce")
        if pd.notna(t):
            return float(t) / 1000, f"dày khối xây {system_id}"
    return float(cls) / 1000, f"dày danh nghĩa lớp {cls}"


def wall_works(plan: str, height_mm: float, walls: list[ReviewWall], openings: list[ReviewOpening],
               params: ProjectParams, catalog: Catalog, system_of: dict[str, Optional[str]] | None = None,
               column_len_in_walls: dict[str, float] | None = None) -> tuple[list[WorkItem], list[str]]:
    """Trả (công tác, cảnh báo) của một mặt bằng. system_of: tường -> phương án tường (đã quy đổi khi xác nhận);
    trống thì quy đổi lại từ mã vật liệu. column_len_in_walls: chiều dài trục tim tường nằm trong cột (mm), theo id
    tường (columns.column_overlaps); phần đó tính vào cột, trừ khỏi khối xây."""
    warnings: list[str] = []
    kept = [w for w in walls if w.keep and w.masonry]
    ids = {w.id for w in kept}
    view = catalog.wall_view().set_index("wall_system_id") if not catalog.wall_systems.empty else pd.DataFrame()
    if system_of is None:
        system_of = {}
        known = set(catalog.materials.material_id)
        for w in kept:
            if w.mat in known:
                system_of[w.id] = catalog.resolve_wall([w.mat], w.cls).wall_system_id

    beam = params.beam_depth_mm
    h_wall = height_mm - (beam or 0.0)
    if beam is None:
        warnings.append(f"{plan}: chưa nhập cao dầm, chiều cao xây lấy bằng chiều cao tầng {height_mm:.0f} mm (chưa trừ dầm).")
    if h_wall <= 0:
        raise ValueError(f"{plan}: cao dầm {beam:.0f} mm không nhỏ hơn chiều cao tầng {height_mm:.0f} mm.")

    lintel_ok = params.lintel_height_mm is not None and params.lintel_bearing_mm is not None
    lintel_missing = [label for v, label in ((params.lintel_height_mm, "cao lanh tô"),
                                             (params.lintel_bearing_mm, "chiều dài gối lanh tô")) if v is None]
    by_wall: dict[str, list[ReviewOpening]] = {}
    for o in openings:
        if o.keep and o.wall in ids:
            by_wall.setdefault(o.wall, []).append(o)

    works: list[WorkItem] = []
    lintel_total, lintel_form, lintel_count, lintel_parts = 0.0, 0.0, 0, []
    keys = sorted({(w.cls, w.role, system_of.get(w.id)) for w in kept}, key=lambda k: (k[0], k[1], k[2] or ""))
    for cls, role, system in keys:
        members = [w for w in kept if w.cls == cls and w.role == role and system_of.get(w.id) == system]
        t, t_note = _thickness_m(system, cls, view)
        length = sum(math.hypot(w.x2 - w.x1, w.y2 - w.y1) for w in members) / 1000
        ops = [o for w in members for o in by_wall.get(w.id, [])]
        no_h = [o.id for o in ops if o.h is None]
        open_area = sum(o.w * min(o.h, h_wall) for o in ops if o.h is not None) / 1e6
        lintel = sum((o.w + 2 * (params.lintel_bearing_mm or 0)) / 1000 * t * (params.lintel_height_mm or 0) / 1000
                     for o in ops) if lintel_ok else 0.0
        # cốp pha lanh tô: đáy dưới lỗ cửa (rộng lỗ × dày tường) + hai thành suốt chiều dài lanh tô
        form = sum(o.w / 1000 * t + 2 * (o.w + 2 * (params.lintel_bearing_mm or 0)) / 1000 * (params.lintel_height_mm or 0) / 1000
                   for o in ops) if lintel_ok else 0.0
        columns = sum((column_len_in_walls or {}).get(w.id, 0.0) for w in members) / 1000 * t * h_wall / 1000
        gross = length * h_wall / 1000
        net_area = max(0.0, gross - open_area)
        label = f"tường {cls} {ROLE_VI.get(role, role)}"
        volume = gross * t - open_area * t - lintel - columns
        formula = (f"{_fmt(length)} m × {_fmt(h_wall / 1000)} m × {_fmt(t)} m ({t_note}) − {_fmt(open_area)} m² cửa × {_fmt(t)} m"
                   + (f" − {_fmt(lintel)} m³ lanh tô" if lintel else "") + (f" − {_fmt(columns)} m³ cột" if columns else ""))
        missing = [] if system else ["phương án tường (vật liệu xây)"]
        works.append(_work("XAY", volume, plan=plan, element=label, wall_system_id=system, formula=formula, missing=missing))
        if no_h:   # lanh tô chỉ cần rộng lỗ nên vẫn tính; diện tích lỗ cần cao
            warnings.append(f"{plan}, {label}: {len(no_h)} lỗ mở chưa có chiều cao ({', '.join(no_h)}), khối xây và trát chưa trừ các lỗ này.")
        if ops and not lintel_ok:
            warnings.append(f"{plan}, {label}: chưa nhập {', '.join(lintel_missing)}, khối xây chưa trừ lanh tô.")
        faces = [("mặt trong", 1), ("mặt ngoài", 1)] if role == "envelope" else [("hai mặt", 2)]
        for face, n in faces:
            works.append(_work("TRAT", n * net_area, plan=plan, element=f"{label}, {face}",
                               variant=None if params.plaster_thickness_mm is None else f"{params.plaster_thickness_mm:g}",
                               formula=f"{n} × ({_fmt(length)} m × {_fmt(h_wall / 1000)} m − {_fmt(open_area)} m² cửa)",
                               missing=[] if params.plaster_thickness_mm is not None else ["chiều dày trát"]))
        if ops:
            lintel_total += lintel
            lintel_form += form
            lintel_count += len(ops)
            lintel_parts.append(f"{len(ops)} lỗ {label}")
    if lintel_count:
        works.append(_work("LANH_TO", lintel_total if lintel_ok else None, plan=plan, element=f"{lintel_count} lanh tô",
                           formula=("Σ (rộng lỗ + 2 × " + _fmt((params.lintel_bearing_mm or 0) / 1000) + " m) × dày tường × "
                                    + _fmt((params.lintel_height_mm or 0) / 1000) + " m; " + ", ".join(lintel_parts))
                           if lintel_ok else ", ".join(lintel_parts),
                           missing=lintel_missing))
        works.append(_work("COP_PHA", lintel_form if lintel_ok else None, plan=plan, element=f"cốp pha {lintel_count} lanh tô",
                           formwork_of="LANH_TO",
                           formula="Σ rộng lỗ × dày tường + 2 × (rộng lỗ + 2 × gối) × cao lanh tô", missing=lintel_missing))
    return works, warnings


def review_input_from_takeoff(result) -> tuple[list[ReviewWall], list[ReviewOpening], dict[str, Optional[str]]]:
    """Kết quả nhận dạng tự động (TakeoffResult) -> dạng đầu vào của trang kiểm tra, khi chưa có người dùng sửa."""
    walls = [ReviewWall(id=w.wall_id, cls=w.thickness_class, role=w.role or "partition", x1=w.x1, y1=w.y1, x2=w.x2,
                        y2=w.y2, mat=w.material_id, masonry=w.is_masonry) for w in result.walls]
    openings = [ReviewOpening(id=f"O{i}", wall=o.wall_id, kind=o.kind, w=o.width_mm, h=o.height_mm)
                for i, o in enumerate(result.openings, start=1)]
    return walls, openings, {w.wall_id: w.wall_system_id for w in result.walls}
