"""Dầm (đặc tả mục 3.5). Dầm của một mặt bằng là dầm đỡ sàn phía trên nó, nằm trên đỉnh tường của mặt bằng đó.

Nguồn dầm: người dùng nhập (hoặc đọc từ bản vẽ kết cấu, chưa làm). Không có thì suy: nối hai cột kề nhau cùng hàng
(lệch trục ≤ BEAM_AXIS_TOL_MM, nhịp ≤ BEAM_MAX_SPAN_MM) khi có tường chạy dọc ít nhất BEAM_WALL_COVER nhịp. Dầm suy luôn
kèm cảnh báo để người dùng duyệt.
    dài dầm             = nhịp thông thủy giữa hai mặt cột
    bê tông dầm (m³)    = dài × rộng × (cao − dày sàn)
    cốp pha dầm (m²)    = (2 × (cao − dày sàn) + rộng) × dài
"""
from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel

from .columns import Column, _clip_length
from .materials import _fmt
from .models import ProjectParams, WorkItem
from .walls import _work

BEAM_AXIS_TOL_MM = 150.0
BEAM_MAX_SPAN_MM = 7000.0
BEAM_WALL_COVER = 0.5


class Beam(BaseModel):
    id: str
    x1: float
    y1: float
    x2: float
    y2: float
    b_mm: Optional[float] = None         # trống: lấy rộng dầm chung của công trình
    d_mm: Optional[float] = None         # cao dầm gồm cả phần sàn; trống: lấy cao dầm chung
    source: str = "inferred"             # inferred (suy từ tường, cột) | manual | structural
    keep: bool = True

    @property
    def length_mm(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)


def _wall_cover(x1, y1, x2, y2, walls) -> float:
    """Phần nhịp (0..1) có tường chạy dọc: chiều dài trục tim tường nằm trong dải rộng 2 × BEAM_AXIS_TOL_MM quanh nhịp."""
    span = math.hypot(x2 - x1, y2 - y1)
    if span == 0:
        return 0.0
    horizontal = abs(y2 - y1) < abs(x2 - x1)
    t = BEAM_AXIS_TOL_MM
    rect = (min(x1, x2), min(y1, y2) - t, max(x1, x2), max(y1, y2) + t) if horizontal else \
        (min(x1, x2) - t, min(y1, y2), max(x1, x2) + t, max(y1, y2))
    covered = 0.0
    for w in walls:
        if not getattr(w, "keep", True):
            continue
        wx, wy = w.x2 - w.x1, w.y2 - w.y1
        if (abs(wy) < abs(wx)) != horizontal:
            continue
        covered += _clip_length(w.x1, w.y1, w.x2, w.y2, rect)
    return min(1.0, covered / span)


def infer_beams(columns: list[Column], walls) -> list[Beam]:
    cols = [c for c in columns if c.keep]
    out: list[Beam] = []
    for axis in ("x", "y"):
        for a in cols:
            # cột kề gần nhất về phía dương trên cùng hàng
            same = [c for c in cols if c is not a and (abs(c.y - a.y) if axis == "x" else abs(c.x - a.x)) <= BEAM_AXIS_TOL_MM
                    and ((c.x - a.x) if axis == "x" else (c.y - a.y)) > 0]
            if not same:
                continue
            b = min(same, key=lambda c: (c.x - a.x) if axis == "x" else (c.y - a.y))
            if axis == "x":
                x1, x2, y = a.x + a.b_mm / 2, b.x - b.b_mm / 2, (a.y + b.y) / 2
                p1, p2 = (x1, y), (x2, y)
            else:
                y1, y2, x = a.y + a.h_mm / 2, b.y - b.h_mm / 2, (a.x + b.x) / 2
                p1, p2 = (x, y1), (x, y2)
            span = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if span <= 0 or span > BEAM_MAX_SPAN_MM:
                continue
            if _wall_cover(*p1, *p2, walls) >= BEAM_WALL_COVER:
                out.append(Beam(id=f"D{len(out) + 1}", x1=round(p1[0], 1), y1=round(p1[1], 1),
                                x2=round(p2[0], 1), y2=round(p2[1], 1)))
    return out


def beam_works(plan: str, beams: list[Beam], params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    kept = [b for b in beams if b.keep]
    if not kept:
        return [], []
    warnings = []
    inferred = [b for b in kept if b.source == "inferred"]
    if inferred:
        warnings.append(f"{plan}: {len(inferred)} dầm suy từ tường và cột (chưa có bản vẽ kết cấu), cần kiểm tra trên trang kiểm tra.")
    slab = params.slab_thickness_mm
    groups: dict[tuple, list[Beam]] = {}
    for b in kept:
        groups.setdefault((b.b_mm or params.beam_width_mm, b.d_mm or params.beam_depth_mm), []).append(b)
    works = []
    for (width, depth), members in sorted(groups.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1] or 0)):
        length = sum(b.length_mm for b in members) / 1000
        missing = [label for v, label in ((width, "rộng dầm"), (depth, "cao dầm"), (slab, "chiều dày sàn")) if v is None]
        label = f"{len(members)} dầm" + (f" {width:.0f}×{depth:.0f}" if width and depth else "")
        web = (depth - slab) / 1000 if depth is not None and slab is not None else None
        ok = not missing and web is not None and web > 0
        if not missing and not ok:
            warnings.append(f"{plan}: cao dầm {depth:.0f} mm không lớn hơn dày sàn {slab:.0f} mm.")
        sec = f"{_fmt(width / 1000) if width else 'rộng'} m × {_fmt(web) if web is not None else '(cao − dày sàn)'} m"
        works.append(_work("DAM", length * width / 1000 * web if ok else None, plan=plan, element=label,
                           formula=f"{_fmt(length)} m × {sec}", missing=missing))
        works.append(_work("COP_PHA", (2 * web + width / 1000) * length if ok else None, plan=plan,
                           element=f"cốp pha {label}", formwork_of="DAM",
                           formula=f"(2 × {_fmt(web) if web is not None else '(cao − dày sàn)'} + "
                                   f"{_fmt(width / 1000) if width else 'rộng'}) m × {_fmt(length)} m",
                           missing=missing))
    return works, warnings
