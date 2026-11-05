"""Cột bê tông cốt thép trên mặt bằng kiến trúc (đặc tả mục 3.4).

Nhận cột: vùng tô đặc (hatch SOLID; bản vẽ xuất qua phần mềm xem nhanh tách hatch thành nhiều tam giác) được tô lên
lưới, gộp các mảnh liền nhau, giữ vùng gần chữ nhật có hai cạnh trong config.COLUMN_SIDE_MM; hatch mọi mẫu trên layer
có ký hiệu vai trò COLUMN cũng được tô. Thêm cột theo ký hiệu (data/rules/concepts.csv, vai trò COLUMN): nét trên layer cột
hoặc trong block cột, các nét nối đầu nhau thành một hình. Người dùng thêm, bớt cột trên trang kiểm tra.
    chiều cao cột (m)   = H - dày sàn (chưa nhập dày sàn thì lấy H, có cảnh báo)
    bê tông cột (m³)    = Σ rộng × dài tiết diện × chiều cao cột
    cốp pha cột (m²)    = Σ 2 × (rộng + dài) × chiều cao cột − Σ rộng dầm × (cao dầm − dày sàn) mỗi đầu dầm gác vào cột
Cột kiến trúc (role = "kien_truc", cột trang trí, ốp): không tính bê tông, cốp pha.
Phần trục tim tường đi qua cột được trừ khỏi khối xây (column_overlaps).
"""
from __future__ import annotations

from typing import Literal, Optional

import numpy as np
from pydantic import BaseModel
from scipy import ndimage

from .. import config
from ..drawing.concepts import layer_role, match_block_signal
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
    source: str = "hatch"        # hatch | signal (ký hiệu layer/block cột) | manual
    keep: bool = True
    role: Optional[Literal["ket_cau", "kien_truc"]] = None    # trống: chưa phân biệt, tính như cột kết cấu

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


def _column_layers(drawing) -> set[str]:
    return {n for n in drawing.layers if layer_role(n) == "COLUMN"}


def signal_columns(drawing) -> list[Column]:
    """Cột theo ký hiệu: nét (không tính nét hatch bị phá) trên layer cột hoặc trong block cột; nét nối đầu nhau gộp
    thành một hình, giữ hình có hai cạnh khung bao trong config.COLUMN_SIDE_MM."""
    lo, hi = config.COLUMN_SIDE_MM
    layers, blocks = _column_layers(drawing), {}
    def is_col(seg) -> bool:
        if seg.layer in layers:
            return True
        if seg.source and seg.source not in blocks:     # block lồng: "ngoài/trong", xét block trong cùng
            sig = match_block_signal(seg.source.rsplit("/", 1)[-1])
            blocks[seg.source] = bool(sig and sig.vai_tro == "COLUMN")
        return bool(seg.source) and blocks[seg.source]
    segs = [s for s in drawing.segments if s.kind != "hatch" and is_col(s)]
    parent: dict = {}
    def find(k):
        while parent.setdefault(k, k) != k:
            parent[k] = k = parent[parent[k]]
        return k
    key = lambda x, y: (round(x), round(y))
    for s in segs:
        parent[find(key(s.x1, s.y1))] = find(key(s.x2, s.y2))
    boxes: dict = {}
    for s in segs:
        b = boxes.setdefault(find(key(s.x1, s.y1)), [s.x1, s.y1, s.x1, s.y1])
        b[:] = [min(b[0], s.x1, s.x2), min(b[1], s.y1, s.y2), max(b[2], s.x1, s.x2), max(b[3], s.y1, s.y2)]
    out = []
    for x0, y0, x1, y1 in boxes.values():
        if lo <= min(x1 - x0, y1 - y0) and max(x1 - x0, y1 - y0) <= hi:
            out.append(Column(id="", x=round((x0 + x1) / 2, 1), y=round((y0 + y1) / 2, 1),
                              b_mm=round((x1 - x0) / 10) * 10, h_mm=round((y1 - y0) / 10) * 10, source="signal"))
    return out


def detect_columns(drawing, cell: float = CELL_MM) -> list[Column]:
    """Cột từ vùng tô đặc, cộng cột theo ký hiệu không trùng cột đã có."""
    out = _fill_columns(drawing, cell)
    for c in signal_columns(drawing):
        if not any(abs(c.x - o.x) < (c.b_mm + o.b_mm) / 2 and abs(c.y - o.y) < (c.h_mm + o.h_mm) / 2 for o in out):
            out.append(c.model_copy(update={"id": f"C{len(out) + 1}"}))
    return out


def _fill_columns(drawing, cell: float) -> list[Column]:
    lo, hi = config.COLUMN_SIDE_MM
    col_layers = _column_layers(drawing)
    polys = []
    for h in drawing.hatches:
        if h.pattern.upper() != "SOLID" and h.layer not in col_layers:
            continue
        for p in h.polygons:
            xs, ys = [q[0] for q in p], [q[1] for q in p]
            if len(p) >= 3 and max(max(xs) - min(xs), max(ys) - min(ys)) <= hi * 1.5:
                polys.append(p)
    if not polys:
        return []
    # mỗi cụm vùng tô gần nhau dựng lưới riêng: một lưới chung cho cả file nhiều khung vẽ cách nhau hàng km cần hàng trăm GiB
    origin = (min(q[0] for p in polys for q in p) - 2 * cell, min(q[1] for p in polys for q in p) - 2 * cell)
    found = [c for group in _near_groups(polys, 2 * cell) for c in _raster_columns(group, cell, lo, hi, origin)]
    found.sort(key=lambda c: (round(c.y - c.h_mm / 2), round(c.x - c.b_mm / 2)))   # thứ tự quét lưới như trước
    return [c.model_copy(update={"id": f"C{i}"}) for i, c in enumerate(found, start=1)]


def _near_groups(polys, gap: float) -> list[list]:
    """Gom đa giác có hộp bao chạm nhau (nới gap) thành cụm; tra lân cận qua lưới thô ô 1 m."""
    boxes = [(min(q[0] for q in p) - gap, min(q[1] for q in p) - gap, max(q[0] for q in p) + gap, max(q[1] for q in p) + gap)
             for p in polys]
    parent = list(range(len(polys)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    size, buckets = 1000.0, {}
    for i, (ax0, ay0, ax1, ay1) in enumerate(boxes):
        keys = [(gx, gy) for gx in range(int(ax0 // size), int(ax1 // size) + 1) for gy in range(int(ay0 // size), int(ay1 // size) + 1)]
        for k in keys:
            for j in buckets.get(k, ()):
                bx0, by0, bx1, by1 = boxes[j]
                if ax0 <= bx1 and bx0 <= ax1 and ay0 <= by1 and by0 <= ay1:
                    parent[find(i)] = find(j)
            buckets.setdefault(k, []).append(i)
    groups: dict[int, list] = {}
    for i, p in enumerate(polys):
        groups.setdefault(find(i), []).append(p)
    return list(groups.values())


def _raster_columns(polys, cell: float, lo: float, hi: float, origin: tuple[float, float]) -> list[Column]:
    # gốc lưới cụm nằm trên cùng mạng ô với gốc chung: kết quả trùng với một lưới phủ cả bản vẽ
    x0 = origin[0] + ((min(q[0] for p in polys for q in p) - 2 * cell - origin[0]) // cell) * cell
    y0 = origin[1] + ((min(q[1] for p in polys for q in p) - 2 * cell - origin[1]) // cell) * cell
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
        out.append(Column(id="", x=round(cx, 1), y=round(cy, 1), b_mm=round(b / 10) * 10, h_mm=round(h / 10) * 10))
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


def _beam_end_area(c: Column, beams, params: ProjectParams) -> float:
    """m² mặt cột bị đầu dầm che (không ghép cốp pha): đầu dầm nằm trong cột hoặc chạm mặt cột (±2 mm)."""
    slab = params.slab_thickness_mm
    x0, y0, x1, y1 = c.rect()
    area = 0.0
    for b in beams or []:
        w, d = b.b_mm or params.beam_width_mm, b.d_mm or params.beam_depth_mm
        if not b.keep or None in (w, d, slab) or d <= slab:
            continue
        for x, y in ((b.x1, b.y1), (b.x2, b.y2)):
            if x0 - 2 <= x <= x1 + 2 and y0 - 2 <= y <= y1 + 2:
                area += w * (d - slab) / 1e6
    return area


def column_works(plan: str, columns: list[Column], height_mm: float,
                 params: ProjectParams, beams=None) -> tuple[list[WorkItem], list[str]]:
    kept = [c for c in columns if c.keep and c.role != "kien_truc"]
    warnings = []
    arch = [c.id for c in columns if c.keep and c.role == "kien_truc"]
    if arch:
        warnings.append(f"{plan}: {len(arch)} cột kiến trúc ({', '.join(arch[:5])}) không tính bê tông, cốp pha.")
    if not kept:
        return [], warnings
    slab = params.slab_thickness_mm
    if slab is None:
        warnings.append(f"{plan}: chưa nhập dày sàn, chiều cao cột lấy bằng chiều cao tầng {height_mm:.0f} mm.")
    hc = (height_mm - (slab or 0.0)) / 1000
    if hc <= 0:
        warnings.append(f"{plan}: xung đột cao độ: dày sàn {slab:.0f} mm không nhỏ hơn chiều cao tầng {height_mm:.0f} mm, chưa tính cột.")
        return [], warnings
    works = []
    for b, h in sorted({(c.b_mm, c.h_mm) for c in kept}):
        group = [c for c in kept if (c.b_mm, c.h_mm) == (b, h)]
        n = len(group)
        hole = sum(_beam_end_area(c, beams, params) for c in group)
        label = f"{n} cột {b:.0f}×{h:.0f}"
        dimensions = [dict(label=c.id, count=1, length_m=h/1000, width_m=b/1000, height_m=hc,
                           source=f"{plan}: {c.id} ({c.source}); chiều cao tầng và dày sàn",
                           note="Cao tính bê tông = cao tầng − dày sàn" + ("; chưa có dày sàn, đang lấy cao tầng" if slab is None else "")) for c in group]
        works.append(_work("COT", n * b * h / 1e6 * hc, dimensions=dimensions, plan=plan, element=label,
                           formula=f"{n} × {_fmt(b / 1000)} m × {_fmt(h / 1000)} m × {_fmt(hc)} m"))
        works.append(_work("COP_PHA", n * 2 * (b + h) / 1000 * hc - hole, dimensions=dimensions, plan=plan, element=f"cốp pha {label}", formwork_of="COT",
                           formula=f"{n} × 2 × ({_fmt(b / 1000)} + {_fmt(h / 1000)}) m × {_fmt(hc)} m"
                                   + (f" − {_fmt(hole)} m² đầu dầm gác vào" if hole else "")))
    return works, warnings


def schedule_column_works(spans) -> list[WorkItem]:
    """Bê tông, cốp pha cột theo bảng thống kê cột (rough/structural.py read_column_schedule): mỗi ô = count × b × h ×
    (z_to − z_from). Cốp pha chu vi đủ, chưa trừ đầu dầm gác vào (bảng không cho vị trí dầm)."""
    works = []
    for s in spans:
        hc = (s.z_to_mm - s.z_from_mm) / 1000
        label = f"{s.count} cột {s.code} {s.b_mm:.0f}×{s.h_mm:.0f}, {s.z_from_mm / 1000:+.3f} → {s.z_to_mm / 1000:+.3f}"
        dimensions = [dict(label=s.code, count=s.count, length_m=s.h_mm/1000, width_m=s.b_mm/1000, height_m=hc,
                           source=f"Bảng thống kê cột {s.code}: {s.z_from_mm:g} → {s.z_to_mm:g} mm",
                           note="Chiều cao đoạn cột theo hai cao độ; chưa trừ đầu dầm khỏi cốp pha")]
        works.append(_work("COT", s.count * s.b_mm * s.h_mm / 1e6 * hc, dimensions=dimensions, plan="bảng thống kê cột", element=label,
                           formula=f"{s.count} × {_fmt(s.b_mm / 1000)} m × {_fmt(s.h_mm / 1000)} m × {_fmt(hc)} m"))
        works.append(_work("COP_PHA", s.count * 2 * (s.b_mm + s.h_mm) / 1000 * hc, dimensions=dimensions, plan="bảng thống kê cột",
                           element=f"cốp pha {label}", formwork_of="COT",
                           formula=f"{s.count} × 2 × ({_fmt(s.b_mm / 1000)} + {_fmt(s.h_mm / 1000)}) m × {_fmt(hc)} m "
                                   "(chưa trừ đầu dầm)"))
    return works


def columns_from_dicts(rows: Optional[list[dict]]) -> list[Column]:
    return [Column(**r) for r in rows or []]
