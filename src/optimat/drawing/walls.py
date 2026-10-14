"""Nhận diện tường từ các cặp nét song song.

Các bước (mỗi bước đều xem được trên trang xem bóc tách):
1. Chọn layer tường: layer có tên tường (TUONG, WALL...) cộng với layer tự nhận bằng hình học, tức layer có
   nhiều cặp nét song song cách nhau đúng một lớp chiều dày. Cần bước này vì bản vẽ thật hay đặt tường
   trên layer theo nét bút (NET_MANH, 1, LAYER1...). Người dùng chỉ định layer tường thì không tự nhận.
2. Ghép cặp: hai nét song song, khoảng cách thuộc một lớp chiều dày, chồng nhau đủ dài -> một đoạn tường
   theo trục tim. Nét của hatch bị phá và cạnh hình kín nhỏ (cột) không tham gia.
3. Góc chữ L: kéo hai đầu tường tới giao điểm trục tim (đo theo tim như dự toán). Ngã ba giữ nguyên:
   tường nhánh đo tới mặt tường chính.
4. Khe cửa: hai đoạn thẳng hàng cùng lớp, giữa có cánh cửa (cung tròn), block cửa hoặc nét kính cửa sổ,
   được nối thành một đoạn và ghi lại lỗ mở để trừ diện tích. Khe không có dấu hiệu cửa thì để hở.

Giới hạn: tường cong chưa xử lý; tường vẽ bằng một nét hoặc chỉ bằng hatch không nhận được.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from .. import config
from ..schemas import WallSegment
from .dxf_reader import Drawing, Segment
from .layer_classifier import LayerClass

ANGLE_BUCKET_DEG = 0.5


def _unit(seg: Segment):
    dx, dy = seg.x2 - seg.x1, seg.y2 - seg.y1
    length = math.hypot(dx, dy)
    return (dx / length, dy / length, length) if length > 1e-6 else (0.0, 0.0, 0.0)


def classify_thickness(dist: float) -> str | None:
    for name, (lo, hi) in config.WALL_THICKNESS_CLASSES.items():
        if lo <= dist <= hi:
            return name
    return None


def _pairs(segs: list[Segment]):
    """Các cặp nét song song có khoảng cách thuộc lớp chiều dày. Gom theo hướng để không so mọi cặp."""
    units = [_unit(s) for s in segs]
    cos_tol = math.cos(math.radians(config.PARALLEL_ANGLE_TOL_DEG))
    buckets: dict[int, list[int]] = defaultdict(list)
    for i, (ux, uy, la) in enumerate(units):
        if la >= config.MIN_WALL_OVERLAP_MM:
            buckets[int((math.degrees(math.atan2(uy, ux)) % 180) / ANGLE_BUCKET_DEG)].append(i)
    n_buckets = int(180 / ANGLE_BUCKET_DEG)
    max_dist = max(hi for lo, hi in config.WALL_THICKNESS_CLASSES.values())
    seen = set()
    for key, members in buckets.items():
        near = members + buckets.get((key + 1) % n_buckets, []) + buckets.get((key - 1) % n_buckets, [])
        for i in members:
            a = segs[i]
            ux, uy, la = units[i]
            for j in near:
                if j <= i or (i, j) in seen:
                    continue
                seen.add((i, j))
                b = segs[j]
                vx, vy, lb = units[j]
                if abs(ux * vx + uy * vy) < cos_tol:
                    continue
                dist = abs((b.x1 - a.x1) * (-uy) + (b.y1 - a.y1) * ux)
                if dist > max_dist:
                    continue
                cls = classify_thickness(dist)
                if cls is None:
                    continue
                t1 = (b.x1 - a.x1) * ux + (b.y1 - a.y1) * uy
                t2 = (b.x2 - a.x1) * ux + (b.y2 - a.y1) * uy
                lo, hi = max(0.0, min(t1, t2)), min(la, max(t1, t2))
                if hi - lo < config.MIN_WALL_OVERLAP_MM:
                    continue
                yield hi - lo, i, j, lo, hi, cls, dist


def _usable(s: Segment) -> bool:
    """Nét được dùng để tìm tường: nét thường nằm trong model hoặc trong block vô danh (*U, *X do phần mềm sinh ra).
    Nét trong block có tên (bàn ghế, thiết bị, ký hiệu) không bao giờ là tường."""
    if s.kind != "line":
        return False
    if not s.source:
        return True
    return all(part.startswith("*") for part in s.source.split("/"))


HATCH_CELL_MM = 500.0


def _hatch_index(drawing: Drawing):
    """Lưới các nét hatch ngắn, để hỏi nhanh: giữa hai nét tường có hatch tô không."""
    grid: dict[tuple[int, int], list[tuple[float, float, float, float]]] = defaultdict(list)
    for s in drawing.segments:
        if s.kind == "hatch" and math.hypot(s.x2 - s.x1, s.y2 - s.y1) <= 800:
            # chỉ nét xiên (hatch gạch chéo kiểu ANSI31); bậc thang, sàn có nét vuông góc hoặc song song
            mx, my = (s.x1 + s.x2) / 2, (s.y1 + s.y2) / 2
            grid[(int(mx // HATCH_CELL_MM), int(my // HATCH_CELL_MM))].append((s.x1, s.y1, s.x2, s.y2))
    return grid


def _strip_has_hatch(grid, a: Segment, ux: float, uy: float, lo: float, hi: float, side: float) -> bool:
    if not grid:
        return False
    x1, y1 = a.x1 + ux * lo, a.y1 + uy * lo
    x2, y2 = a.x1 + ux * hi, a.y1 + uy * hi
    ox, oy = -uy * side, ux * side
    xs = (x1, x2, x1 + ox, x2 + ox)
    ys = (y1, y2, y1 + oy, y2 + oy)
    for cx in range(int(min(xs) // HATCH_CELL_MM), int(max(xs) // HATCH_CELL_MM) + 1):
        for cy in range(int(min(ys) // HATCH_CELL_MM), int(max(ys) // HATCH_CELL_MM) + 1):
            for hx1, hy1, hx2, hy2 in grid.get((cx, cy), ()):
                lh = math.hypot(hx2 - hx1, hy2 - hy1) or 1.0
                if abs(((hx2 - hx1) * ux + (hy2 - hy1) * uy) / lh) > math.cos(math.radians(20)) or \
                        abs(((hx2 - hx1) * ux + (hy2 - hy1) * uy) / lh) < math.cos(math.radians(70)):
                    continue
                # cả hai đầu nét hatch nằm trong dải giữa hai nét tường: hatch tô tường (bậc thang, sàn thì tràn ra ngoài)
                ok = True
                for px, py in ((hx1, hy1), (hx2, hy2)):
                    t = (px - a.x1) * ux + (py - a.y1) * uy
                    d = (px - a.x1) * (-uy) + (py - a.y1) * ux
                    if not (lo - 5 <= t <= hi + 5 and min(0, side) - 5 <= d <= max(0, side) + 5):
                        ok = False
                        break
                if ok:
                    return True
    return False


def _tread_index(drawing: Drawing):
    """Lưới nét hatch theo mọi ô chúng đi qua, để hỏi: cặp nét có bị các bậc thang cắt ngang không."""
    grid: dict[tuple[int, int], list[Segment]] = defaultdict(list)
    for s in drawing.segments:
        if s.kind != "hatch":
            continue
        L = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
        steps = max(1, int(L / HATCH_CELL_MM))
        cells = {(int((s.x1 + (s.x2 - s.x1) * k / steps) // HATCH_CELL_MM),
                  int((s.y1 + (s.y2 - s.y1) * k / steps) // HATCH_CELL_MM)) for k in range(steps + 1)}
        for c in cells:
            grid[c].append(s)
    return grid


def _is_stringer(treads, a: Segment, ux: float, uy: float, lo: float, hi: float, side: float) -> bool:
    """Cặp nét bị từ 2 nét hatch gần vuông góc cắt ngang qua cả hai nét: thành cầu thang, không phải tường."""
    if not treads:
        return False
    x1, y1 = a.x1 + ux * lo, a.y1 + uy * lo
    x2, y2 = a.x1 + ux * hi, a.y1 + uy * hi
    xs = (x1, x2, x1 - uy * side, x2 - uy * side)
    ys = (y1, y2, y1 + ux * side, y2 + ux * side)
    seen, crossing = set(), 0
    for cx in range(int(min(xs) // HATCH_CELL_MM), int(max(xs) // HATCH_CELL_MM) + 1):
        for cy in range(int(min(ys) // HATCH_CELL_MM), int(max(ys) // HATCH_CELL_MM) + 1):
            for h in treads.get((cx, cy), ()):
                if id(h) in seen:
                    continue
                seen.add(id(h))
                lh = math.hypot(h.x2 - h.x1, h.y2 - h.y1) or 1.0
                if abs(((h.x2 - h.x1) * ux + (h.y2 - h.y1) * uy) / lh) > 0.5:   # không gần vuông góc
                    continue
                d1 = (h.x1 - a.x1) * (-uy) + (h.y1 - a.y1) * ux
                d2 = (h.x2 - a.x1) * (-uy) + (h.y2 - a.y1) * ux
                t = (h.x1 - a.x1) * ux + (h.y1 - a.y1) * uy
                lo_d, hi_d = min(d1, d2), max(d1, d2)
                if lo <= t <= hi and lo_d <= min(0, side) + 5 and hi_d >= max(0, side) - 5:
                    crossing += 1
                    if crossing >= 2:
                        return True
    return False


PAR_CELL_MM = 600.0


def _line_index(drawing: Drawing):
    """Lưới mọi nét thẳng (mọi layer, kể cả trong block) để hỏi nhanh các nét song song quanh một cặp nét."""
    lines = [x for x in drawing.segments if x.kind != "hatch"]
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for k, x in enumerate(lines):
        L = math.hypot(x.x2 - x.x1, x.y2 - x.y1)
        n = max(1, int(L // PAR_CELL_MM) + 1)
        seen = set()
        for t in range(n + 1):
            px, py = x.x1 + (x.x2 - x.x1) * t / n, x.y1 + (x.y2 - x.y1) * t / n
            c = (int(px // PAR_CELL_MM), int(py // PAR_CELL_MM))
            if c not in seen:
                seen.add(c)
                grid[c].append(k)
    return lines, grid


def _parallels(index, a: Segment, ux: float, uy: float, lo: float, hi: float, reach: float, skip=()):
    """Các nét song song với a trong dải [lo, hi] dọc trục a, cách a không quá reach.
    Trả về (khoảng cách có dấu tới a, tỉ lệ chồng lên đoạn [lo, hi], chiều dài nét)."""
    lines, grid = index
    nx, ny = -uy, ux
    cells = set()
    steps = max(1, int((hi - lo) // PAR_CELL_MM) + 1)
    for t in range(steps + 1):
        d = lo + (hi - lo) * t / steps
        for off in (-reach, 0.0, reach):
            px, py = a.x1 + ux * d + nx * off, a.y1 + uy * d + ny * off
            cx, cy = int(px // PAR_CELL_MM), int(py // PAR_CELL_MM)
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    cells.add((cx + i, cy + j))
    out, seen = [], set()
    for c in cells:
        for k in grid.get(c, ()):
            if k in seen:
                continue
            seen.add(k)
            x = lines[k]
            if x is a or id(x) in skip:
                continue
            L = math.hypot(x.x2 - x.x1, x.y2 - x.y1)
            if L < 1 or abs((x.x2 - x.x1) / L * ux + (x.y2 - x.y1) / L * uy) < 0.995:
                continue
            o1 = (x.x1 - a.x1) * nx + (x.y1 - a.y1) * ny
            o2 = (x.x2 - a.x1) * nx + (x.y2 - a.y1) * ny
            if abs(o1 - o2) > 5 or abs(o1) > reach:
                continue
            p1 = (x.x1 - a.x1) * ux + (x.y1 - a.y1) * uy
            p2 = (x.x2 - a.x1) * ux + (x.y2 - a.y1) * uy
            ov = min(hi, max(p1, p2)) - max(lo, min(p1, p2))
            if ov > 0:
                out.append(((o1 + o2) / 2, ov / (hi - lo), L))
    return out


def _ladder_or_frame(index, a: Segment, b: Segment, ux: float, uy: float, lo: float, hi: float, side: float) -> str | None:
    """Cặp nét không phải tường:
    - "bậc thang / lan can": có nét thứ ba song song cách đều (cùng khoảng cách) phía ngoài cặp, kiểu bậc thang,
      thanh lan can, sọc lát;
    - "khung cửa sổ": giữa hai nét có từ hai nét song song ngắn (kính, khung), dài xấp xỉ đoạn cặp nét.
      Tường thật giữa hai mặt chỉ có hatch chéo hoặc nét trát sát mặt; trục định vị đi qua tường thì dài hơn nhiều."""
    dist = abs(side)
    sgn = 1.0 if side >= 0 else -1.0
    near = _parallels(index, a, ux, uy, lo, hi, 2.2 * dist, skip=(id(b),))
    for off, frac, _ in near:
        beyond_b = sgn * off - dist
        before_a = -sgn * off
        if frac >= 0.5 and (abs(beyond_b - dist) < 0.15 * dist or abs(before_a - dist) < 0.15 * dist):
            return "bậc thang / lan can"
    inner = [1 for off, frac, L in near
             if 0.2 * dist < sgn * off < 0.8 * dist and frac >= 0.6 and L <= 1.3 * (hi - lo)]
    if len(inner) >= 2:
        return "khung cửa sổ"
    return None


def wall_layer_scores(drawing: Drawing) -> tuple[dict[str, float], dict[str, float]]:
    """Theo từng layer: (tổng mm cặp nét song song đúng chiều dày, phần trong đó có hatch nằm giữa hai nét)."""
    by_layer: dict[str, list[Segment]] = defaultdict(list)
    for s in drawing.segments:
        if _usable(s) and drawing.layer_classes.get(s.layer) not in (LayerClass.IGNORE, LayerClass.OPENING):
            by_layer[s.layer].append(s)
    grid = _hatch_index(drawing)
    treads = _tread_index(drawing)
    scores, hatched = {}, {}
    for layer, segs in by_layer.items():
        total = filled = 0.0
        for overlap, i, j, lo, hi, cls, dist in _pairs(segs):
            a, b = segs[i], segs[j]
            L = math.hypot(a.x2 - a.x1, a.y2 - a.y1)
            ux, uy = (a.x2 - a.x1) / L, (a.y2 - a.y1) / L
            side = (b.x1 - a.x1) * (-uy) + (b.y1 - a.y1) * ux
            if _is_stringer(treads, a, ux, uy, lo, hi, side):
                continue
            total += overlap
            if _strip_has_hatch(grid, a, ux, uy, lo, hi, side):
                filled += overlap
        if total > 0:
            scores[layer] = round(total, 0)
            hatched[layer] = round(filled, 0)
    return scores, hatched


def choose_wall_layers(drawing: Drawing) -> tuple[set[str], dict[str, float], list[str]]:
    """(layer dùng làm tường, điểm từng layer, các layer được tự nhận thêm).

    Bản vẽ có tô hatch trong tường thì chấm điểm theo phần cặp nét có hatch ở giữa (phân biệt tường
    với bậc thang, lan can, đồ đạc); không có thì chấm theo tổng chiều dài cặp nét.
    """
    named = {n for n, c in drawing.layer_classes.items() if c == LayerClass.WALL}
    if drawing.user_wall_layers:
        return named, {}, []
    raw, hatched = wall_layer_scores(drawing)
    best_raw, best_hatched = max(raw.values(), default=0), max(hatched.values(), default=0)
    use_hatched = best_hatched >= config.WALL_LAYER_MIN_SCORE_MM and best_hatched >= 0.25 * best_raw
    scores = hatched if use_hatched else raw
    scores = {k: v for k, v in scores.items() if v > 0}
    best = max(scores.values(), default=0.0)
    chosen = {n for n in named if scores.get(n, 0) > 0}
    auto = []
    for layer, score in sorted(scores.items(), key=lambda kv: -kv[1]):
        if layer in chosen or score < config.WALL_LAYER_MIN_SCORE_MM:
            continue
        rel = score / best if best else 0
        # layer có tên chú thích (CHU_KT, TEXT...) chỉ được nhận khi chính nó là layer điểm cao nhất
        if drawing.layer_classes.get(layer) == LayerClass.ANNOTATION and score < best:
            continue
        if rel >= config.WALL_LAYER_REL_SCORE:
            chosen.add(layer)
            auto.append(layer)
    if not chosen and named:
        chosen = named
    return chosen, scores, auto


def _hatched_pairs_elsewhere(drawing: Drawing, wall_layers: set[str]):
    """Cặp nét trên layer khác có hatch gạch chéo tô kín ở giữa: vẫn là tường dù layer không được chọn."""
    grid = _hatch_index(drawing)
    if not grid:
        return []
    by_layer: dict[str, list[Segment]] = defaultdict(list)
    for s in drawing.segments:
        if s.layer not in wall_layers and _usable(s) and \
                drawing.layer_classes.get(s.layer) not in (LayerClass.IGNORE, LayerClass.OPENING):
            by_layer[s.layer].append(s)
    out = []
    for segs in by_layer.values():
        for overlap, i, j, lo, hi, cls, dist in _pairs(segs):
            a, b = segs[i], segs[j]
            L = math.hypot(a.x2 - a.x1, a.y2 - a.y1)
            ux, uy = (a.x2 - a.x1) / L, (a.y2 - a.y1) / L
            side = (b.x1 - a.x1) * (-uy) + (b.y1 - a.y1) * ux
            if _strip_has_hatch(grid, a, ux, uy, lo, hi, side):
                out.extend([a, b])
    return out


def detect_walls(drawing: Drawing, wall_layers: set[str] | None = None) -> list[WallSegment]:
    if wall_layers is None:
        wall_layers = {n for n, c in drawing.layer_classes.items() if c == LayerClass.WALL}
    segs = [s for s in drawing.segments if s.layer in wall_layers and _usable(s)]
    extra: set[int] = set()
    if not drawing.user_wall_layers:
        extra = {id(s) for s in _hatched_pairs_elsewhere(drawing, wall_layers)}
        segs += [s for s in drawing.segments if id(s) in extra]
    units = [_unit(s) for s in segs]
    candidates = sorted(_pairs(segs), reverse=True)
    treads = _tread_index(drawing)
    index = _line_index(drawing)
    used: dict[int, list[tuple[float, float]]] = {}
    walls: list[WallSegment] = []
    drawing.rejected_pairs = []                      # cặp nét đã loại và lý do, để xem trên trang kiểm tra

    def covered(intervals, lo, hi):
        total = sum(max(0.0, min(hi, b) - max(lo, a)) for a, b in intervals)
        return total / (hi - lo) if hi > lo else 1.0

    for overlap, i, j, lo, hi, cls, dist in candidates:
        a, b = segs[i], segs[j]
        ux, uy, _ = units[i]
        vx, vy, _ = units[j]
        s1 = (a.x1 + ux * lo - b.x1) * vx + (a.y1 + uy * lo - b.y1) * vy
        s2 = (a.x1 + ux * hi - b.x1) * vx + (a.y1 + uy * hi - b.y1) * vy
        blo, bhi = min(s1, s2), max(s1, s2)
        if covered(used.get(i, []), lo, hi) > 0.5 or covered(used.get(j, []), blo, bhi) > 0.5:
            continue
        if _is_stringer(treads, a, ux, uy, lo, hi, (b.x1 - a.x1) * (-uy) + (b.y1 - a.y1) * ux):
            continue
        side0 = (b.x1 - a.x1) * (-uy) + (b.y1 - a.y1) * ux
        reason = _ladder_or_frame(index, a, b, ux, uy, lo, hi, side0)
        if reason:
            off0 = side0 / 2.0
            drawing.rejected_pairs.append((reason, a.x1 + ux * lo - uy * off0, a.y1 + uy * lo + ux * off0,
                                           a.x1 + ux * hi - uy * off0, a.y1 + uy * hi + ux * off0, cls))
            continue
        used.setdefault(i, []).append((lo, hi))
        used.setdefault(j, []).append((blo, bhi))
        side = (b.x1 - a.x1) * (-uy) + (b.y1 - a.y1) * ux
        off = dist / 2.0 * (1 if side >= 0 else -1)
        ox, oy = -uy * off, ux * off
        lo_c, hi_c = config.WALL_THICKNESS_CLASSES[cls]
        nominal = (lo_c + hi_c) / 2.0
        confidence = round(max(0.5, 1.0 - abs(dist - nominal) / nominal), 2)
        if id(a) in extra or id(b) in extra:      # tường nhận nhờ hatch trên layer khác: có thể là bồn hoa, quầy xây
            confidence = 0.5
        walls.append(WallSegment(
            wall_id=f"W{len(walls) + 1}", layer=a.layer, thickness_class=cls, length_mm=round(overlap, 1),
            x1=a.x1 + ux * lo + ox, y1=a.y1 + uy * lo + oy, x2=a.x1 + ux * hi + ox, y2=a.y1 + uy * hi + oy,
            confidence=confidence, thickness_mm=round(dist, 1),
        ))
    return walls


def dedupe_walls(walls: list[WallSegment]) -> list[WallSegment]:
    """Bỏ tường trùng: bản vẽ có nét vẽ chồng hai lần hoặc tường vẽ bằng ba, bốn nét (mặt gạch và mặt trát)
    sinh ra nhiều đoạn tường song song nằm đè lên nhau. Giữ đoạn dài hơn, nới nó ra phủ cả đoạn bị bỏ."""
    walls = sorted(walls, key=lambda w: -w.length_mm)
    kept: list[WallSegment] = []
    for w in walls:
        merged = False
        for k in kept:
            L = k.length_mm or 1.0
            ux, uy = (k.x2 - k.x1) / L, (k.y2 - k.y1) / L
            lw = w.length_mm or 1.0
            if abs(ux * (w.x2 - w.x1) / lw + uy * (w.y2 - w.y1) / lw) < 0.999:
                continue
            tk = k.thickness_mm or float(k.thickness_class)
            tw = w.thickness_mm or float(w.thickness_class)
            d1 = abs((w.x1 - k.x1) * (-uy) + (w.y1 - k.y1) * ux)
            d2 = abs((w.x2 - k.x1) * (-uy) + (w.y2 - k.y1) * ux)
            if max(d1, d2) > (tk + tw) / 2 - 10:
                continue
            p1 = (w.x1 - k.x1) * ux + (w.y1 - k.y1) * uy
            p2 = (w.x2 - k.x1) * ux + (w.y2 - k.y1) * uy
            lo, hi = min(p1, p2), max(p1, p2)
            if min(hi, L) - max(lo, 0.0) < 0.5 * lw:
                continue
            nlo, nhi = min(0.0, lo), max(L, hi)
            k.x1, k.y1, k.x2, k.y2 = k.x1 + ux * nlo, k.y1 + uy * nlo, k.x1 + ux * nhi, k.y1 + uy * nhi
            k.length_mm = round(nhi - nlo, 1)
            merged = True
            break
        if not merged:
            kept.append(w)
    for i, w in enumerate(kept, start=1):
        w.wall_id = f"W{i}"
    return kept


# ---------------------------------------------------------------- góc chữ L

def _intersect(a: WallSegment, b: WallSegment):
    d1x, d1y = a.x2 - a.x1, a.y2 - a.y1
    d2x, d2y = b.x2 - b.x1, b.y2 - b.y1
    den = d1x * d2y - d1y * d2x
    if abs(den) < 1e-9:
        return None
    t = ((b.x1 - a.x1) * d2y - (b.y1 - a.y1) * d2x) / den
    return a.x1 + t * d1x, a.y1 + t * d1y


def _set_length(w: WallSegment) -> None:
    w.length_mm = round(math.hypot(w.x2 - w.x1, w.y2 - w.y1), 1)


def extend_corners(walls: list[WallSegment]) -> int:
    """Góc chữ L: hai tường cùng dừng trước giao điểm trục tim thì kéo cả hai tới giao điểm. Trả về số góc đã nối."""
    joined = 0
    for i, a in enumerate(walls):
        for b in walls[i + 1:]:
            la, lb = a.length_mm, b.length_mm
            if la <= 0 or lb <= 0:
                continue
            cos = abs(((a.x2 - a.x1) * (b.x2 - b.x1) + (a.y2 - a.y1) * (b.y2 - b.y1)) / (la * lb))
            if cos > 0.9:
                continue
            p = _intersect(a, b)
            if p is None:
                continue
            ta, tb = (a.thickness_mm or float(a.thickness_class)), (b.thickness_mm or float(b.thickness_class))
            ea = min(((a.x1, a.y1), (a.x2, a.y2)), key=lambda e: math.dist(e, p))
            eb = min(((b.x1, b.y1), (b.x2, b.y2)), key=lambda e: math.dist(e, p))
            if math.dist(ea, p) <= tb / 2 + 80 and math.dist(eb, p) <= ta / 2 + 80:
                for w, e in ((a, ea), (b, eb)):
                    if (w.x1, w.y1) == e:
                        w.x1, w.y1 = p
                    else:
                        w.x2, w.y2 = p
                    _set_length(w)
                joined += 1
    return joined


# ---------------------------------------------------------------- khe cửa

@dataclass
class GapOpening:
    kind: str          # door | window | block
    x: float
    y: float
    width_mm: float
    height_mm: float
    wall_id: str
    evidence: str      # cung cửa, nét kính, block ...


def _project(w: WallSegment, x: float, y: float):
    """(vị trí dọc trục tim tính từ đầu 1, khoảng cách tới trục tim)."""
    L = math.hypot(w.x2 - w.x1, w.y2 - w.y1) or 1.0
    ux, uy = (w.x2 - w.x1) / L, (w.y2 - w.y1) / L
    return (x - w.x1) * ux + (y - w.y1) * uy, abs((x - w.x1) * (-uy) + (y - w.y1) * ux)


def bridge_openings(walls: list[WallSegment], drawing: Drawing, wall_layers: set[str],
                    opening_blocks: list) -> tuple[list[WallSegment], list[GapOpening], list]:
    """Nối các đoạn tường thẳng hàng bị ngắt tại cửa. Trả về (tường, lỗ mở từ khe, block cửa đã dùng)."""
    openings: list[GapOpening] = []
    used_blocks: list = []
    lo_r, hi_r = config.DOOR_ARC_RADIUS_MM
    door_arcs = [a for a in drawing.arcs if lo_r <= a.r <= hi_r and 60 <= a.sweep <= 120]
    glass = [s for s in drawing.segments if s.kind == "line" and s.layer not in wall_layers]
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(walls):
            for j, b in enumerate(walls):
                if j <= i or a.thickness_class != b.thickness_class:
                    continue
                L = a.length_mm
                if L <= 0:
                    continue
                ux, uy = (a.x2 - a.x1) / L, (a.y2 - a.y1) / L
                lb = math.hypot(b.x2 - b.x1, b.y2 - b.y1) or 1.0
                if abs(ux * (b.x2 - b.x1) / lb + uy * (b.y2 - b.y1) / lb) < 0.9995:
                    continue
                tb1, d1 = _project(a, b.x1, b.y1)
                tb2, d2 = _project(a, b.x2, b.y2)
                if max(d1, d2) > 40:
                    continue
                blo, bhi = min(tb1, tb2), max(tb1, tb2)
                if blo >= L:
                    g0, g1 = L, blo
                elif bhi <= 0:
                    g0, g1 = bhi, 0.0
                else:
                    continue
                gap = g1 - g0
                if not (0 < gap <= config.MAX_OPENING_GAP_MM):
                    continue
                t = a.thickness_mm or float(a.thickness_class)
                mid = g0 + gap / 2
                cx, cy = a.x1 + ux * mid, a.y1 + uy * mid
                found = None
                silent = gap <= 400   # khe nhỏ: nét bị ngắt tại chỗ giao tường khác, nối liền không có lỗ mở
                for arc in ([] if silent else door_arcs):
                    p, d = _project(a, arc.cx, arc.cy)
                    if d <= t / 2 + 250 and g0 - 250 <= p <= g1 + 250:
                        found = GapOpening("door", cx, cy, gap, config.DEFAULT_OPENINGS_MM["D"][1], "", "cung cánh cửa")
                        break
                if found is None and not silent:
                    for blk in opening_blocks:
                        p, d = _project(a, blk.x, blk.y)
                        if d <= t / 2 + 600 and g0 - 300 <= p <= g1 + 300:
                            kind = "window" if blk.name.upper().startswith(("S", "CS", "W")) else "door"
                            h = config.DEFAULT_OPENINGS_MM["S" if kind == "window" else "D"][1]
                            found = GapOpening(kind, cx, cy, gap, h, "", f"block {blk.name}")
                            used_blocks.append(blk)
                            break
                if found is None and not silent:
                    cover = 0.0
                    for s in glass:
                        ls = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
                        if ls < 100 or abs(ux * (s.x2 - s.x1) / ls + uy * (s.y2 - s.y1) / ls) < 0.999:
                            continue
                        p1, e1 = _project(a, s.x1, s.y1)
                        p2, e2 = _project(a, s.x2, s.y2)
                        if max(e1, e2) <= t / 2 + 30:
                            cover = max(cover, min(g1, max(p1, p2)) - max(g0, min(p1, p2)))
                    if cover >= 0.6 * gap:
                        found = GapOpening("window", cx, cy, gap, config.DEFAULT_OPENINGS_MM["S"][1], "", "nét kính")
                if found is None and not silent:
                    continue
                # nối: đoạn mới đi từ đầu xa của a tới đầu xa của b
                ends = [(a.x1, a.y1), (a.x2, a.y2), (b.x1, b.y1), (b.x2, b.y2)]
                proj = [(_project(a, *e)[0], e) for e in ends]
                (_, e0), (_, e1) = min(proj), max(proj)
                a.x1, a.y1 = e0
                a.x2, a.y2 = e1
                _set_length(a)
                a.confidence = min(a.confidence, b.confidence)
                for o in openings:
                    if o.wall_id == b.wall_id:
                        o.wall_id = a.wall_id
                if found is not None:
                    found.wall_id = a.wall_id
                    openings.append(found)
                walls.pop(j)
                changed = True
                break
            if changed:
                break
    return walls, openings, used_blocks


# ------------------------------------------------------------------ tường vẽ bằng một nét + hatch
STRIP_MIN_HATCH_PER_M = 2.0      # số nét hatch tối thiểu mỗi mét chạm mặt tường
STRIP_MAX_SPREAD_MM = 25.0       # độ lệch cho phép của đầu nét hatch phía mặt kia (mặt kia phải thẳng)
STRIP_CONFIDENCE = 0.6


def hatch_strip_walls(drawing: Drawing, existing: list[WallSegment], wall_layers: set[str] | None = None) -> list[WallSegment]:
    """Tường chỉ có một nét mặt (mặt kia không vẽ hoặc nằm trên layer khác, bị cắt vụn) nhưng có hatch gạch chéo:
    các nét hatch chạy từ mặt này sang mặt kia, nên đầu bên kia của chúng thẳng hàng ở khoảng cách bằng chiều dày.
    Nhận thành tường khi khoảng cách đó thuộc một lớp chiều dày. Độ tin cậy thấp để người dùng duyệt."""
    hatch = [s for s in drawing.segments if s.kind == "hatch"]
    if not hatch or drawing.user_wall_layers:
        return []
    wall_layers = wall_layers or set()
    ok_class = (LayerClass.WALL, LayerClass.UNKNOWN)

    def face_layer_ok(name: str) -> bool:   # mặt tường không nằm trên layer trục, kích thước, chữ, nội thất, cửa
        return name in wall_layers or drawing.layer_classes.get(name, LayerClass.UNKNOWN) in ok_class
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for k, h in enumerate(hatch):
        for x, y in ((h.x1, h.y1), (h.x2, h.y2)):
            grid[(int(x // HATCH_CELL_MM), int(y // HATCH_CELL_MM))].append(k)
    faces = [s for s in drawing.segments if _usable(s) and face_layer_ok(s.layer) and math.hypot(s.x2 - s.x1, s.y2 - s.y1) >= 400]
    out: list[WallSegment] = []
    taken = list(existing)

    def overlaps_existing(x1, y1, x2, y2) -> bool:
        L = math.hypot(x2 - x1, y2 - y1)
        for w in taken:
            wl = math.hypot(w.x2 - w.x1, w.y2 - w.y1) or 1.0
            ux, uy = (w.x2 - w.x1) / wl, (w.y2 - w.y1) / wl
            if abs(ux * (x2 - x1) / L + uy * (y2 - y1) / L) < 0.995:
                continue
            if max(abs((x1 - w.x1) * -uy + (y1 - w.y1) * ux), abs((x2 - w.x1) * -uy + (y2 - w.y1) * ux)) > 200:
                continue
            p1, p2 = (x1 - w.x1) * ux + (y1 - w.y1) * uy, (x2 - w.x1) * ux + (y2 - w.y1) * uy
            if min(max(p1, p2), wl) - max(min(p1, p2), 0.0) > 0.5 * L:
                return True
        return False

    for a in faces:
        ux, uy, L = _unit(a)
        nx, ny = -uy, ux
        cells = set()
        n = max(1, int(L // HATCH_CELL_MM) + 1)
        for t in range(n + 1):
            px, py = a.x1 + ux * L * t / n, a.y1 + uy * L * t / n
            cx, cy = int(px // HATCH_CELL_MM), int(py // HATCH_CELL_MM)
            cells.update((cx + i, cy + j) for i in (-1, 0, 1) for j in (-1, 0, 1))
        seen, sides = set(), {1: [], -1: []}
        for c in cells:
            for k in grid.get(c, ()):
                if k in seen:
                    continue
                seen.add(k)
                h = hatch[k]
                ends = [((h.x1 - a.x1) * nx + (h.y1 - a.y1) * ny, (h.x1 - a.x1) * ux + (h.y1 - a.y1) * uy),
                        ((h.x2 - a.x1) * nx + (h.y2 - a.y1) * ny, (h.x2 - a.x1) * ux + (h.y2 - a.y1) * uy)]
                for e_on, e_off in (ends, ends[::-1]):
                    if abs(e_on[0]) <= 15 and -20 <= e_on[1] <= L + 20 and abs(e_off[0]) > 60:
                        sides[1 if e_off[0] > 0 else -1].append((abs(e_off[0]), e_on[1]))
                        break
        for sgn, pts in sides.items():
            if len(pts) < 3:
                continue
            offs = sorted(p[0] for p in pts)
            med = offs[len(offs) // 2]
            good = [p for p in pts if abs(p[0] - med) <= STRIP_MAX_SPREAD_MM]
            lo, hi = min(p[1] for p in good), max(p[1] for p in good)
            span = max(hi - lo, 1.0)
            cls = classify_thickness(med)
            if cls is None or span < 400 or len(good) / (span / 1000) < STRIP_MIN_HATCH_PER_M or len(good) < 0.7 * len(pts):
                continue
            lo, hi = max(0.0, lo - 50), min(L, hi + 50)
            off = sgn * med / 2
            x1, y1 = a.x1 + ux * lo + nx * off, a.y1 + uy * lo + ny * off
            x2, y2 = a.x1 + ux * hi + nx * off, a.y1 + uy * hi + ny * off
            if overlaps_existing(x1, y1, x2, y2):
                continue
            w = WallSegment(wall_id=f"H{len(out) + 1}", layer=a.layer, thickness_class=cls, length_mm=round(hi - lo, 1),
                            x1=x1, y1=y1, x2=x2, y2=y2, confidence=STRIP_CONFIDENCE, thickness_mm=round(med, 1))
            out.append(w)
            taken.append(w)
    return out
