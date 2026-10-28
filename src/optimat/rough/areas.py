"""Công tác theo diện tích của một mặt bằng: sàn, cán nền, nền tầng trệt, chống thấm (đặc tả mục 3.6, 3.8–3.10).

Hình học lấy từ tường đã chốt (khe cửa đã được nối khi nhận dạng): tô các tường lên lưới ô CELL_MM, lấp kín phần
bên trong đường bao (khe tới 2 × CLOSE_GAP_MM ở chỗ cột, đầu tường hụt được coi là liền; vẫn hở thì lấy bao lồi của
tường bao, cảnh báo để kiểm tra, 28/10/2026) rồi đo:
    diện tích trong tim tường bao = diện tích trong mép ngoài tường bao - Σ dài tường bao × dày / 2
    diện tích sử dụng (cán nền)    = phần trong đường bao không phải tường
    phòng                          = từng vùng trống khép kín; tên phòng đọc từ chữ trên bản vẽ theo data/rules/room_rules.csv
    sàn (m³)        = (diện tích trong tim tường bao - ô trống) × dày sàn; không tính cho tầng trệt
    cốp pha sàn (m²)= diện tích sàn (đáy), chưa trừ phần đáy dầm
    cán nền (m²)    = diện tích sử dụng
    nền trệt (m³)   = diện tích sử dụng × dày từng lớp (đệm cát, bê tông lót)
    chống thấm (m²) = Σ phòng vệ sinh (diện tích + cao cổ tường × chu vi) + ban công (nhập tay)
Sai số của lưới: chiều dày tường lệch tới một ô (ô 10 mm: khoảng 0,3% diện tích với nhà 100 m²).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import ndimage
from scipy.spatial import ConvexHull, QhullError

from .. import config
from ..db.session import read_rule_table
from ..drawing.encoding import normalize
from .materials import _fmt
from .models import ProjectParams, WorkItem
from .walls import _work

CELL_MM = 10.0
ROOM_RULES_PATH = config.DATA_DIR / "rules" / "room_rules.csv"
MIN_ROOM_M2 = 0.5
CLOSE_GAP_MM = 400.0      # khe giữa hai đầu tường tới 800 mm (cột, đầu tường hụt) được coi là liền khi tìm đường bao


class PlanParams(BaseModel):
    """Thông số riêng của một mặt bằng, người dùng nhập hoặc xác nhận."""
    name: str
    is_ground: bool = False                         # tầng trệt: tính nền, không tính sàn
    void_area_m2: Optional[float] = None            # ô trống trên sàn (lỗ cầu thang, giếng trời)
    balcony_area_m2: Optional[float] = None         # ban công, lô gia cần chống thấm (nằm ngoài tường bao)
    outline_area_m2: Optional[float] = None         # nhập tay: diện tích trong tim tường bao (dùng thay số đo từ tường)
    usable_area_m2: Optional[float] = None          # nhập tay: diện tích sử dụng


@dataclass
class Room:
    kind: str                     # WET | BALCONY | "" (không có tên khớp quy tắc)
    label: str
    area_m2: float
    perimeter_m: float


@dataclass
class PlanGeometry:
    closed: bool
    outline_area_m2: float = 0.0          # trong tim tường bao
    usable_area_m2: float = 0.0
    wall_area_m2: float = 0.0
    rooms: list[Room] = field(default_factory=list)
    labels_outside: list[str] = field(default_factory=list)   # tên phòng khớp quy tắc nhưng không nằm trong vùng khép kín nào
    hull: bool = False                    # tường bao hở, đường bao lấy theo bao lồi của tường bao (người dùng kiểm tra)


@lru_cache(maxsize=4)
def load_room_rules(path: str | None = None) -> tuple[tuple[str, re.Pattern, str], ...]:
    df = read_rule_table("room_rules", path, ROOM_RULES_PATH)
    return tuple((r["rule_id"], re.compile(r["pattern"]), r["kind"]) for r in df.to_dict("records"))


def room_kind(text: str, rules=None) -> str | None:
    norm = normalize(text)
    for _, pattern, kind in rules or load_room_rules():
        if pattern.search(norm):
            return kind
    return None


def room_labels(drawing) -> list[tuple[str, str, float, float]]:
    """Chữ trên bản vẽ là tên phòng cần cho phần thô: (loại, chữ, x, y)."""
    out = []
    for t in drawing.texts:
        kind = room_kind(t.text)
        if kind:
            out.append((kind, t.text.strip(), t.x, t.y))
    return out


def _rasterize(walls, cell: float):
    xs = [c for w in walls for c in (w.x1, w.x2)]
    ys = [c for w in walls for c in (w.y1, w.y2)]
    pad = 1000.0
    x0, y0 = min(xs) - pad, min(ys) - pad
    nx, ny = int((max(xs) + pad - x0) / cell) + 1, int((max(ys) + pad - y0) / cell) + 1
    grid = np.zeros((ny, nx), dtype=bool)
    for w in walls:
        half = float(w.cls) / 2
        L = math.hypot(w.x2 - w.x1, w.y2 - w.y1)
        if L == 0:
            continue
        ux, uy = (w.x2 - w.x1) / L, (w.y2 - w.y1) / L
        i0 = max(0, int((min(w.x1, w.x2) - half - x0) / cell) - 1)
        i1 = min(nx, int((max(w.x1, w.x2) + half - x0) / cell) + 2)
        j0 = max(0, int((min(w.y1, w.y2) - half - y0) / cell) - 1)
        j1 = min(ny, int((max(w.y1, w.y2) + half - y0) / cell) + 2)
        cx = x0 + (np.arange(i0, i1) + 0.5) * cell
        cy = y0 + (np.arange(j0, j1) + 0.5) * cell
        X, Y = np.meshgrid(cx, cy)
        along = (X - w.x1) * ux + (Y - w.y1) * uy
        perp = np.abs(-(X - w.x1) * uy + (Y - w.y1) * ux)
        grid[j0:j1, i0:i1] |= (along >= -half) & (along <= L + half) & (perp <= half)
    return grid, x0, y0


def plan_geometry(walls, labels: list[tuple[str, str, float, float]] | None = None, cell: float = CELL_MM) -> PlanGeometry:
    """walls: tường đang giữ (ReviewWall: cls, role, x1..y2)."""
    walls = [w for w in walls if getattr(w, "keep", True)]
    if not walls:
        return PlanGeometry(closed=False)
    grid, x0, y0 = _rasterize(walls, cell)
    a = cell * cell / 1e6
    # đóng khe nhỏ (chỗ cột, đầu tường hụt) trước khi lấp: khe hẹp hơn 2 × CLOSE_GAP_MM coi như liền
    r = CLOSE_GAP_MM / cell
    closed_walls = ndimage.distance_transform_edt(ndimage.distance_transform_edt(~grid) <= r) > r   # nở r rồi co r
    filled = ndimage.binary_fill_holes(closed_walls)
    inside = filled & ~grid
    wall_area = grid.sum() * a
    hull = False
    if inside.sum() * a < wall_area:
        # nhà ống: mặt tiền, mặt sau toàn cửa / lan can giữa hai cột góc, không đoạn tường nào để khép
        filled = _hull_mask([w for w in walls if w.role == "envelope"] or walls, grid.shape, x0, y0, cell)
        if filled is None or (filled & ~grid).sum() * a < wall_area:
            return PlanGeometry(closed=False, wall_area_m2=round(wall_area, 2))
        inside, hull = filled & ~grid, True
    envelope_strip = sum(math.hypot(w.x2 - w.x1, w.y2 - w.y1) * float(w.cls) / 2 for w in walls if w.role == "envelope") / 1e6
    comp, n = ndimage.label(filled & ~closed_walls)
    sizes = ndimage.sum(inside, comp, range(1, n + 1)) * a
    names: dict[int, list[tuple[str, str]]] = {}
    outside = []
    for kind, text, x, y in labels or []:
        i, j = int((x - x0) / cell), int((y - y0) / cell)
        k = int(comp[j, i]) if 0 <= j < comp.shape[0] and 0 <= i < comp.shape[1] else 0
        if k and sizes[k - 1] >= MIN_ROOM_M2:
            names.setdefault(k, []).append((kind, text))
        else:
            outside.append(text)
    rooms = []
    for k in range(1, n + 1):
        if sizes[k - 1] < MIN_ROOM_M2:
            continue
        mask = comp == k
        edges = (np.count_nonzero(mask[:, 1:] != mask[:, :-1]) + np.count_nonzero(mask[1:, :] != mask[:-1, :])) * cell / 1000
        tags = names.get(k, [])
        kind = "WET" if any(t[0] == "WET" for t in tags) else (tags[0][0] if tags else "")
        rooms.append(Room(kind=kind, label=", ".join(t[1] for t in tags), area_m2=round(sizes[k - 1], 2),
                          perimeter_m=round(edges, 2)))
    return PlanGeometry(closed=True, outline_area_m2=round(filled.sum() * a - envelope_strip, 2),
                        usable_area_m2=round(inside.sum() * a, 2), wall_area_m2=round(wall_area, 2),
                        rooms=rooms, labels_outside=outside, hull=hull)


def _hull_mask(walls, shape, x0: float, y0: float, cell: float):
    """Ô lưới nằm trong bao lồi của mép ngoài các tường (4 góc mỗi tường). None khi tường thẳng hàng (không có bao)."""
    pts = []
    for w in walls:
        L = math.hypot(w.x2 - w.x1, w.y2 - w.y1)
        if L == 0:
            continue
        half = float(w.cls) / 2
        nx, ny = -(w.y2 - w.y1) / L * half, (w.x2 - w.x1) / L * half
        ex, ey = (w.x2 - w.x1) / L * half, (w.y2 - w.y1) / L * half
        pts += [(w.x1 - ex + sx * nx, w.y1 - ey + sx * ny) for sx in (-1, 1)]
        pts += [(w.x2 + ex + sx * nx, w.y2 + ey + sx * ny) for sx in (-1, 1)]
    try:
        hull = ConvexHull(np.array(pts))
    except (QhullError, ValueError):
        return None
    cy, cx = np.mgrid[0:shape[0], 0:shape[1]]
    X, Y = x0 + (cx + 0.5) * cell, y0 + (cy + 0.5) * cell
    mask = np.ones(shape, dtype=bool)
    for nxe, nye, off in hull.equations:          # mặt phẳng: n·p + off ≤ 0 là bên trong
        mask &= nxe * X + nye * Y + off <= 1e-6
    return mask


def area_works(geom: PlanGeometry, params: ProjectParams, plan: PlanParams) -> tuple[list[WorkItem], list[str]]:
    """Diện tích nhập tay trong PlanParams thắng số đo từ tường (dùng khi tường bao trên bản vẽ chưa khép kín)."""
    name = plan.name
    warnings: list[str] = []
    outline = plan.outline_area_m2 if plan.outline_area_m2 is not None else (geom.outline_area_m2 if geom.closed else None)
    usable = plan.usable_area_m2 if plan.usable_area_m2 is not None else (geom.usable_area_m2 if geom.closed else None)
    if outline is None and usable is None:
        warnings.append(f"{name}: tường bao chưa khép kín, chưa tính được diện tích sàn, nền, chống thấm. "
                        "Vẽ thêm đoạn tường còn thiếu trên trang kiểm tra hoặc nhập tay diện tích.")
        return [], warnings
    if geom.hull and (plan.outline_area_m2 is None or plan.usable_area_m2 is None):
        warnings.append(f"{name}: tường bao chưa khép kín, đã khép theo bao lồi của tường bao "
                        f"({_fmt(geom.outline_area_m2)} m² trong tim tường bao): kiểm tra; nhà không phải hình chữ nhật "
                        "(chữ L, có hốc) thì vẽ thêm tường hoặc nhập tay diện tích.")
    src_outline = "manual" if plan.outline_area_m2 is not None else "auto"
    src_usable = "manual" if plan.usable_area_m2 is not None else "auto"
    no_outline = [] if outline is not None else ["diện tích trong tim tường bao (tường bao chưa khép kín)"]
    no_usable = [] if usable is not None else ["diện tích sử dụng (tường bao chưa khép kín)"]
    works: list[WorkItem] = []
    if not plan.is_ground:
        void = plan.void_area_m2
        if void is None:
            warnings.append(f"{name}: chưa nhập diện tích ô trống (lỗ cầu thang, giếng trời), sàn chưa trừ ô trống.")
        t = params.slab_thickness_mm
        area = None if outline is None else max(0.0, outline - (void or 0.0))
        works.append(_work("SAN", area * t / 1000 if t and area is not None else None, plan=name, element="sàn",
                           source=src_outline,
                           formula=f"({_fmt(outline) if outline is not None else '?'} m² trong tim tường bao − "
                                   f"{_fmt(void or 0)} m² ô trống) × " + (f"{_fmt(t / 1000)} m" if t else "dày sàn"),
                           missing=no_outline + ([] if t else ["chiều dày sàn"])))
        # cốp pha đáy sàn = diện tích sàn; chưa trừ phần đáy dầm (đặc tả 3.6 còn để ngỏ)
        works.append(_work("COP_PHA", area, plan=name, element="cốp pha đáy sàn", source=src_outline, formwork_of="SAN",
                           formula=f"{_fmt(area) if area is not None else '?'} m² sàn (chưa trừ đáy dầm)", missing=no_outline))
    u = _fmt(usable) if usable is not None else "?"
    works.append(_work("CAN_NEN", usable, plan=name, element="nền các phòng", source=src_usable,
                       variant=None if params.screed_thickness_mm is None else f"{params.screed_thickness_mm:g}",
                       formula=f"{u} m² diện tích sử dụng",
                       missing=no_usable + ([] if params.screed_thickness_mm is not None else ["chiều dày cán nền"])))
    if plan.is_ground:
        if not params.ground_layers:
            for code in ("NEN_DEM_CAT", "BE_TONG_LOT"):
                works.append(_work(code, None, plan=name, element="nền tầng trệt", missing=["cấu tạo nền (lớp và chiều dày)"]))
        for layer in params.ground_layers:
            works.append(_work(layer.kind, usable * layer.thickness_mm / 1000 if usable is not None else None, plan=name,
                               element="nền tầng trệt", source=src_usable, missing=no_usable,
                               formula=f"{u} m² × {_fmt(layer.thickness_mm / 1000)} m"))
    wet = [r for r in geom.rooms if r.kind == "WET"]
    up = params.waterproof_upturn_mm
    variant = params.waterproof_material_id
    for r in wet:
        q = r.area_m2 + (up / 1000 * r.perimeter_m if up is not None else 0.0)
        works.append(_work("CHONG_THAM", q if up is not None else None, plan=name, element=f"phòng {r.label}", variant=variant,
                           formula=f"{_fmt(r.area_m2)} m² + " + (f"{_fmt(up / 1000)} m" if up is not None else "cao cổ tường")
                                   + f" × {_fmt(r.perimeter_m)} m chu vi",
                           missing=[] if up is not None else ["chiều cao cổ tường chống thấm"]))
    if plan.balcony_area_m2:
        works.append(_work("CHONG_THAM", plan.balcony_area_m2, plan=name, element="ban công", variant=variant, source="manual",
                           formula=f"{_fmt(plan.balcony_area_m2)} m² nhập tay"))
    elif any(room_kind(t) == "BALCONY" for t in geom.labels_outside) or any(r.kind == "BALCONY" for r in geom.rooms):
        warnings.append(f"{name}: bản vẽ có ban công/lô gia nhưng chưa nhập diện tích, chưa tính chống thấm ban công.")
    wet_outside = [t for t in geom.labels_outside if room_kind(t) == "WET"]
    if wet_outside:
        warnings.append(f"{name}: tên phòng {', '.join(wet_outside)} không nằm trong phòng khép kín nào, chưa tính chống thấm.")
    return works, warnings
