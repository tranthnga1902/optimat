"""Cột bê tông cốt thép trên mặt bằng kiến trúc (đặc tả mục 3.4).

Nhận cột: vùng tô đặc (hatch SOLID; bản vẽ xuất qua phần mềm xem nhanh tách hatch thành nhiều tam giác) được tô lên
lưới, gộp các mảnh liền nhau, giữ vùng gần chữ nhật có hai cạnh trong config.COLUMN_SIDE_MM. Người dùng thêm, bớt cột
trên trang kiểm tra.
    chiều cao cột (m)   = H - dày sàn (chưa nhập dày sàn thì lấy H, có cảnh báo)
    bê tông cột (m³)    = Σ rộng × dài tiết diện × chiều cao cột
    cốp pha cột (m²)    = Σ 2 × (rộng + dài) × chiều cao cột
Phần trục tim tường đi qua cột được trừ khỏi khối xây (column_overlaps).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from pydantic import BaseModel
from scipy import ndimage

from .. import config
from .materials import _fmt
from .models import ProjectParams, WorkItem
from .walls import _work

CELL_MM = 10.0


class Column(BaseModel):
    id: str
    x: float                     # tâm (mm, tọa độ bản vẽ)
    y: float
    b_mm: float                  # cạnh theo phương x
    h_mm: float                  # cạnh theo phương y
    source: str = "hatch"        # hatch | manual
    keep: bool = True

    def rect(self) -> tuple[float, float, float, float]:
        return self.x - self.b_mm / 2, self.y - self.h_mm / 2, self.x + self.b_mm / 2, self.y + self.h_mm / 2


def _inside(poly: list[tuple[float, float]], X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Điểm nằm trong đa giác (quy tắc chẵn lẻ)."""
    out = np.zeros(X.shape, dtype=bool)
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]
        x2, y2 = poly[(k + 1) % n]
        if y1 == y2:
            continue
        cross = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / (y2 - y1) + x1)
        out ^= cross
    return out


def detect_columns(drawing, cell: float = CELL_MM) -> list[Column]:
    lo, hi = config.COLUMN_SIDE_MM
    polys = []
    for h in drawing.hatches:
        if h.pattern.upper() != "SOLID":
            continue
        for p in h.polygons:
            xs, ys = [q[0] for q in p], [q[1] for q in p]
            if len(p) >= 3 and max(max(xs) - min(xs), max(ys) - min(ys)) <= hi * 1.5:
                polys.append(p)
    if not polys:
        return []
    x0 = min(q[0] for p in polys for q in p) - 2 * cell
    y0 = min(q[1] for p in polys for q in p) - 2 * cell
    nx = int((max(q[0] for p in polys for q in p) - x0) / cell) + 3
    ny = int((max(q[1] for p in polys for q in p) - y0) / cell) + 3
    grid = np.zeros((ny, nx), dtype=bool)
    for p in polys:
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        i0, i1 = int((min(xs) - x0) / cell), int((max(xs) - x0) / cell) + 2
        j0, j1 = int((min(ys) - y0) / cell), int((max(ys) - y0) / cell) + 2
        X, Y = np.meshgrid(x0 + (np.arange(i0, i1) + 0.5) * cell, y0 + (np.arange(j0, j1) + 0.5) * cell)
        grid[j0:j1, i0:i1] |= _inside(p, X, Y)
    # các mảnh tam giác cùng một vùng tô có thể hở một ô ở cạnh chung: nở một ô rồi mới gộp
    comp, n = ndimage.label(ndimage.binary_dilation(grid), structure=np.ones((3, 3)))
    out = []
    for k, sl in enumerate(ndimage.find_objects(comp), start=1):
        mask = (comp[sl] == k) & grid[sl]
        if not mask.any():
            continue
        rows, cols = np.nonzero(mask)
        b = (cols.max() - cols.min() + 1) * cell
        h = (rows.max() - rows.min() + 1) * cell
        fill = mask.sum() * cell * cell / (b * h)
        if not (lo <= min(b, h) and max(b, h) <= hi and max(b, h) / min(b, h) <= config.COLUMN_MAX_ASPECT
                and fill >= config.COLUMN_MIN_FILL):
            continue
        cx = x0 + (sl[1].start + (cols.min() + cols.max() + 1) / 2) * cell
        cy = y0 + (sl[0].start + (rows.min() + rows.max() + 1) / 2) * cell
        out.append(Column(id=f"C{len(out) + 1}", x=round(cx, 1), y=round(cy, 1),
                          b_mm=round(b / 10) * 10, h_mm=round(h / 10) * 10))
    return out


def _clip_length(x1, y1, x2, y2, rect) -> float:
    """Chiều dài đoạn thẳng nằm trong hình chữ nhật (Liang–Barsky)."""
    xmin, ymin, xmax, ymax = rect
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - xmin), (dx, xmax - x1), (-dy, y1 - ymin), (dy, ymax - y1)):
        if p == 0:
            if q < 0:
                return 0.0
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return 0.0
    return (t1 - t0) * (dx * dx + dy * dy) ** 0.5


def column_overlaps(columns: list[Column], walls) -> dict[str, float]:
    """Tường -> chiều dài trục tim (mm) nằm trong cột đang giữ."""
    out: dict[str, float] = {}
    for w in walls:
        if not getattr(w, "keep", True):
            continue
        length = sum(_clip_length(w.x1, w.y1, w.x2, w.y2, c.rect()) for c in columns if c.keep)
        if length > 0:
            out[w.id] = length
    return out


def column_works(plan: str, columns: list[Column], height_mm: float,
                 params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    kept = [c for c in columns if c.keep]
    if not kept:
        return [], []
    warnings = []
    slab = params.slab_thickness_mm
    if slab is None:
        warnings.append(f"{plan}: chưa nhập dày sàn, chiều cao cột lấy bằng chiều cao tầng {height_mm:.0f} mm.")
    hc = (height_mm - (slab or 0.0)) / 1000
    works = []
    for b, h in sorted({(c.b_mm, c.h_mm) for c in kept}):
        n = sum(1 for c in kept if (c.b_mm, c.h_mm) == (b, h))
        label = f"{n} cột {b:.0f}×{h:.0f}"
        works.append(_work("COT", n * b * h / 1e6 * hc, plan=plan, element=label,
                           formula=f"{n} × {_fmt(b / 1000)} m × {_fmt(h / 1000)} m × {_fmt(hc)} m"))
        works.append(_work("COP_PHA", n * 2 * (b + h) / 1000 * hc, plan=plan, element=f"cốp pha {label}", formwork_of="COT",
                           formula=f"{n} × 2 × ({_fmt(b / 1000)} + {_fmt(h / 1000)}) m × {_fmt(hc)} m"))
    return works, warnings


def columns_from_dicts(rows: Optional[list[dict]]) -> list[Column]:
    return [Column(**r) for r in rows or []]
