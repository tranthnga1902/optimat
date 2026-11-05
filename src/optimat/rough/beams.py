"""Dầm (đặc tả mục 3.5). Dầm của một mặt bằng là dầm đỡ sàn phía trên nó, nằm trên đỉnh tường của mặt bằng đó.

Nguồn dầm: người dùng nhập (hoặc đọc từ bản vẽ kết cấu, chưa làm). Không có thì suy: nối hai cột kề nhau cùng hàng
(lệch trục ≤ BEAM_AXIS_TOL_MM, nhịp ≤ BEAM_MAX_SPAN_MM) khi có tường chạy dọc ít nhất BEAM_WALL_COVER nhịp. Dầm suy luôn
kèm cảnh báo để người dùng duyệt.
    dài dầm             = nhịp thông thủy giữa hai mặt cột
    bê tông dầm (m³)    = dài × rộng × (cao − dày sàn)
    cốp pha dầm (m²)    = (2 × (cao − dày sàn) + rộng) × dài − Σ rộng × (cao − dày sàn) của dầm phụ gác vào thành
Nút giao (beam_joints, không đếm trùng): sàn liền qua dầm và cột (dầm tính phần dưới sàn, cột tới đáy sàn); cột liền qua
dầm (dầm cắt ở mặt cột); dầm chính liền qua dầm phụ (dầm phụ cắt ở mặt dầm chính). Dầm chính: cao hơn, rồi rộng hơn, rồi
dài hơn. Hai dầm nằm chồng trên một trục: bỏ đoạn chồng của dầm sau và báo.
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
    cut_mm: float = 0.0                  # beam_joints: phần dài nằm trong cột, móng, dầm chính (không tính lần hai)
    framed: list[tuple[Optional[float], Optional[float]]] = []   # beam_joints: (rộng, cao) dầm phụ gác vào thành dầm này

    @property
    def length_mm(self) -> float:
        return max(0.0, math.hypot(self.x2 - self.x1, self.y2 - self.y1) - self.cut_mm)


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


def _rect(b: Beam, width: float) -> tuple[float, float, float, float]:
    """Khung mặt bằng của dầm (trục ngang hoặc đứng) rộng `width`."""
    h = width / 2
    if abs(b.y2 - b.y1) < abs(b.x2 - b.x1):
        return min(b.x1, b.x2), b.y1 - h, max(b.x1, b.x2), b.y1 + h
    return b.x1 - h, min(b.y1, b.y2), b.x1 + h, max(b.y1, b.y2)


def _horizontal(b: Beam) -> bool:
    return abs(b.y2 - b.y1) < abs(b.x2 - b.x1)


def beam_joints(beams: list[Beam], columns: list[Column], params: ProjectParams,
                rects: list[tuple[str, tuple[float, float, float, float]]] = ()) -> tuple[list[Beam], list[str]]:
    """Tính lại cut_mm, framed của từng dầm từ đầu (gọi nhiều lần cho cùng kết quả). rects: khung khác mà dầm phải
    dừng ở mép (móng trên mặt bằng móng): [(tên, (x0, y0, x1, y1))]."""
    out = [b.model_copy(update={"cut_mm": 0.0, "framed": []}) for b in beams]
    kept = [b for b in out if b.keep]
    warnings = []
    width = {id(b): b.b_mm or params.beam_width_mm for b in kept}
    depth = {id(b): b.d_mm or params.beam_depth_mm for b in kept}
    stops = [(f"cột {c.id}", c.rect()) for c in columns if c.keep] + list(rects)
    for b in kept:
        for name, r in stops:
            b.cut_mm += _clip_length(b.x1, b.y1, b.x2, b.y2, r)
    rank = lambda b: (depth[id(b)] or 0, width[id(b)] or 0, math.hypot(b.x2 - b.x1, b.y2 - b.y1))
    for i, a in enumerate(kept):
        for b in kept[i + 1:]:
            if _horizontal(a) == _horizontal(b):
                # cùng phương, cùng trục: đoạn chồng là vẽ trùng
                if _horizontal(a) and abs(a.y1 - b.y1) < 1 or not _horizontal(a) and abs(a.x1 - b.x1) < 1:
                    lap = _clip_length(b.x1, b.y1, b.x2, b.y2, _rect(a, 2))
                    if lap > 1:
                        b.cut_mm += lap
                        warnings.append(f"Dầm {b.id} chồng lên dầm {a.id} {lap:.0f} mm trên cùng trục: bỏ đoạn chồng (đếm trùng).")
                continue
            main, sec = (a, b) if rank(a) >= rank(b) else (b, a)
            if width[id(main)] is None:
                continue
            inside = _clip_length(sec.x1, sec.y1, sec.x2, sec.y2, _rect(main, width[id(main)]))
            if inside <= 0:
                continue
            sec.cut_mm += inside
            # dầm phụ đi xuyên qua: gác vào hai thành; dừng ở dầm chính: một thành
            grown = _rect(main, width[id(main)] + 2)
            ends_in = any(_inside_rect(x, y, grown) for x, y in ((sec.x1, sec.y1), (sec.x2, sec.y2)))
            main.framed += [(width[id(sec)], depth[id(sec)])] * (1 if ends_in else 2)
    return out, warnings


def _inside_rect(x, y, r) -> bool:
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]


def is_tie_beam(b: Beam) -> bool:
    """Đà kiềng, giằng móng (ký hiệu ĐK…, GM… theo data/rules/ky_hieu_cau_kien.csv): không có sàn bên trên."""
    from .structural import element_of        # structural nhập beams: nhập muộn tránh vòng
    e = element_of(b.id)
    return b.source != "inferred" and e is not None and e[1] == TIE_NAME


TIE_NAME = "đà kiềng, giằng móng"


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
        # dầm đọc từ bản vẽ, nhập tay: gom theo mã cấu kiện (D1, ĐK2) để truy ngược; dầm suy: theo tiết diện
        code = "" if b.source == "inferred" else b.id
        groups.setdefault((code, b.b_mm or params.beam_width_mm, b.d_mm or params.beam_depth_mm), []).append(b)
    works = []
    for (code, width, depth), members in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0, kv[0][2] or 0)):
        length = sum(b.length_mm for b in members) / 1000
        cut = sum(b.cut_mm for b in members) / 1000
        tie = all(is_tie_beam(b) for b in members)
        missing = [label for v, label in ((width, "rộng dầm"), (depth, "cao dầm"), (None if tie else slab, "chiều dày sàn"))
                   if v is None and not (tie and label == "chiều dày sàn")]
        label = (f"{code}: " if code else "") + f"{len(members)} {'giằng' if tie else 'dầm'}" + (f" {width:.0f}×{depth:.0f}" if width and depth else "")
        web = depth / 1000 if tie and depth is not None else (depth - slab) / 1000 if depth is not None and slab is not None else None
        ok = not missing and web is not None and web > 0
        if not missing and not ok:
            warnings.append(f"{plan}: cao dầm {depth:.0f} mm không lớn hơn dày sàn {slab:.0f} mm.")
        sec = f"{_fmt(width / 1000) if width else 'rộng'} m × {_fmt(web) if web is not None else '(cao − dày sàn)'} m"
        note = f" (đã trừ {_fmt(cut)} m trong cột, dầm chính, móng)" if cut > 0 else ""
        dimensions = [dict(label=b.id, count=1, length_m=b.length_mm/1000,
                           gross_length_m=math.hypot(b.x2-b.x1, b.y2-b.y1)/1000, deducted_length_m=b.cut_mm/1000,
                           width_m=width/1000 if width is not None else None,
                           height_m=depth/1000 if depth is not None else None, concrete_height_m=web,
                           source=f"{plan}: {b.id} ({b.source})",
                           field_sources={"length_m": f"Trục {b.id} và khoản trừ giao beam_joints",
                               "width_m": f"Beam.{b.id}.b_mm ({b.source})" if b.b_mm else "ProjectParams.beam_width_mm",
                               "height_m": f"Beam.{b.id}.d_mm ({b.source})" if b.d_mm else "ProjectParams.beam_depth_mm",
                               "concrete_height_m": "Cao toàn tiết diện" if tie else "Cao toàn tiết diện − ProjectParams.slab_thickness_mm"},
                           note=f"Dài net; đã trừ giao {b.cut_mm/1000:g} m. Cao là toàn tiết diện; " +
                                ("giằng không trừ sàn" if tie else "cao tính bê tông là phần dưới sàn") +
                                "; CP còn khoản trừ đầu dầm phụ riêng, không nhân kích thước để thay lượng CP") for b in members]
        works.append(_work("DAM", length * width / 1000 * web if ok else None, dimensions=dimensions, plan=plan, element=label,
                           formula=f"{_fmt(length)} m × {sec}{note}", missing=missing))
        framed = [(bw, bd) for b in members for bw, bd in b.framed]
        hole = sum(bw * (bd - slab) / 1e6 for bw, bd in framed if bw and bd and slab is not None and bd > slab) if ok else 0.0
        bottom = 0.0 if tie else width / 1000 if width else None     # giằng đặt trên lót: không ván đáy
        works.append(_work("COP_PHA", (2 * web + bottom) * length - hole if ok else None, dimensions=dimensions, plan=plan,
                           element=f"cốp pha {label}", formwork_of="DAM",
                           formula=f"(2 × {_fmt(web) if web is not None else '(cao − dày sàn)'} + "
                                   f"{_fmt(bottom) if bottom is not None else 'rộng'}) m × {_fmt(length)} m"
                                   + (f" − {_fmt(hole)} m² chỗ {len(framed)} đầu dầm phụ gác vào" if hole else ""),
                           missing=missing))
    return works, warnings
