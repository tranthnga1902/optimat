"""Tìm các mặt bằng tầng trong một file bản vẽ và cao độ sàn của từng tầng.

Một file kiến trúc thường chứa nhiều mặt bằng, mặt đứng, mặt cắt và khung tên. Cách tìm:
1. Lấy các dòng chữ là tiêu đề mặt bằng tầng ("MẶT BẰNG TẦNG 1", "mặt bằng trệt"...), bỏ mặt bằng kết cấu,
   trần, mái, móng, điện nước, và bỏ chữ nhỏ trong khung tên.
2. Khung tìm của mỗi tiêu đề: phía trên tiêu đề, chia đôi khoảng cách với tiêu đề cùng hàng, dừng ở tiêu đề
   hàng trên (mọi tiêu đề cỡ lớn đều dùng để giới hạn, kể cả mặt đứng, mặt cắt).
3. Trong khung, gom nét thành cụm (ô lưới 1 m, nối ô kề nhau; bỏ hatch, khung, trục, kích thước) và lấy cụm lớn nhất.
4. Cao độ sàn lấy từ tiêu đề "(+3.30)" hoặc ký hiệu cao độ trong mặt bằng ("±0.000", "+2.800").
   Chiều cao tầng = cao độ tầng trên liền kề - cao độ tầng này.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from .dxf_reader import Drawing
from .encoding import normalize

PLAN_WORDS = ("mat bang",)
EXCLUDE_WORDS = ("ket cau", "da kieng", "giang", "mong cot", "co cot", "cot ", "bo tri thep", "tran", "mong", "mai", "dinh vi", "tong the", "dien", "nuoc", "cap ", "thoat",
                 "lat ", "bo tri", "coc", "dam", "thep", "san ", "chieu sang", "chong set", "phoi canh")
HEADING_WORDS = ("mat bang", "mat cat", "mat dung", "mat tien", "mat ben", "chi tiet", "phoi canh", "so do", "trich")
FRAME_LAYER_WORDS = ("khung", "frame", "title", "border", "truc", "grid", "axis", "dim", "kich thuoc", "defpoints")
CELL_MM = 1000.0
MAX_CLUSTER_LINE_MM = 20000.0
LEVEL_RE = re.compile(r"([±+\-])\s*(\d{1,2}[.,]\d{2,3})")


@dataclass
class PlanRegion:
    name: str
    title_x: float
    title_y: float
    bbox: tuple[float, float, float, float]
    level_m: float | None
    level_source: str
    n_segments: int
    title: str = ""          # tiêu đề gốc khi tên đã được đánh số thêm vì trùng (QU-05)


def _is_plan_title(text: str) -> bool:
    t = " " + normalize(text) + " "
    return any(w in t for w in PLAN_WORDS) and not any(w in t for w in EXCLUDE_WORDS)


def _level(text: str) -> float | None:
    m = LEVEL_RE.search(text)
    if not m:
        return None
    value = float(m.group(2).replace(",", "."))
    return -value if m.group(1) == "-" else value


def _clusters(drawing: Drawing, window: tuple[float, float, float, float]):
    """Cụm nét trong khung: ô lưới 1 m có nét, nối các ô kề nhau. Bỏ nét hatch, khung, trục, nét quá dài."""
    wx0, wy0, wx1, wy1 = window
    cells: dict[tuple[int, int], int] = defaultdict(int)
    for s in drawing.segments:
        if s.kind == "hatch" or any(w in normalize(s.layer) for w in FRAME_LAYER_WORDS):
            continue
        if not (wx0 <= s.x1 <= wx1 and wy0 <= s.y1 <= wy1 and wx0 <= s.x2 <= wx1 and wy0 <= s.y2 <= wy1):
            continue
        length = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
        if length > MAX_CLUSTER_LINE_MM:
            continue
        steps = max(1, int(length / CELL_MM))
        for k in range(steps + 1):
            x = s.x1 + (s.x2 - s.x1) * k / steps
            y = s.y1 + (s.y2 - s.y1) * k / steps
            cells[(int(math.floor(x / CELL_MM)), int(math.floor(y / CELL_MM)))] += 1
    seen, clusters = set(), []
    for start in cells:
        if start in seen:
            continue
        stack, comp = [start], []
        seen.add(start)
        while stack:
            cx, cy = stack.pop()
            comp.append((cx, cy))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (cx + dx, cy + dy)
                    if n in cells and n not in seen:
                        seen.add(n)
                        stack.append(n)
        xs = [c[0] for c in comp]
        ys = [c[1] for c in comp]
        clusters.append(((min(xs) * CELL_MM, min(ys) * CELL_MM, (max(xs) + 1) * CELL_MM, (max(ys) + 1) * CELL_MM),
                         sum(cells[c] for c in comp)))
    return clusters


def _window(t, others) -> tuple[float, float, float, float]:
    """Khung tìm mặt bằng của tiêu đề t: phía trên t, giới hạn bởi các tiêu đề lớn khác ở bên cạnh và phía trên."""
    left, right, top = t.x - 25000, t.x + 25000, t.y + 30000
    for o in others:
        if o is t:
            continue
        if abs(o.y - t.y) < 5000:                      # tiêu đề cùng hàng: chia đôi khoảng cách
            if o.x < t.x:
                left = max(left, (o.x + t.x) / 2)
            elif o.x > t.x:
                right = min(right, (o.x + t.x) / 2)
        elif o.y > t.y + 1000 and abs(o.x - t.x) < 15000:   # tiêu đề hàng trên: mặt bằng của t nằm dưới nó
            top = min(top, o.y - 200)
    return left, t.y - 300, right, top


FRAME_MIN_MM = 20000.0


def _frame_lines(drawing: Drawing):
    """Nét thẳng đứng hoặc nằm ngang rất dài, không có nét song song đi kèm ở khoảng cách chiều dày tường:
    viền khung bản vẽ, viền khung tên. Dùng làm giới hạn khung tìm mặt bằng."""
    longs = []
    for s in drawing.segments:
        if s.kind != "line":
            continue
        dx, dy = s.x2 - s.x1, s.y2 - s.y1
        if math.hypot(dx, dy) >= FRAME_MIN_MM and (abs(dx) < 1 or abs(dy) < 1):
            longs.append(s)
    out = []
    for s in longs:
        vertical = abs(s.x2 - s.x1) < 1
        partner = any(o is not s and (abs(o.x2 - o.x1) < 1) == vertical and
                      40 < (abs(o.x1 - s.x1) if vertical else abs(o.y1 - s.y1)) < 400 for o in longs)
        if not partner:
            out.append(("v", s.x1, min(s.y1, s.y2), max(s.y1, s.y2)) if vertical
                       else ("h", s.y1, min(s.x1, s.x2), max(s.x1, s.x2)))
    return out


def _shrink(window, t, frames):
    left, bottom, right, top = window
    for kind, c, a, b in frames:
        if kind == "v" and a <= t.y <= b + 30000:
            if left < c < t.x:
                left = c
            elif t.x < c < right:
                right = c
        elif kind == "h" and a <= t.x <= b and t.y < c < top:
            top = c
    return left, bottom, right, top


def find_plans(drawing: Drawing) -> list[PlanRegion]:
    titles = [t for t in drawing.texts if _is_plan_title(t.text)]
    if not titles:
        return []
    big = max(t.height for t in titles) or 0
    titles = [t for t in titles if t.height >= 0.6 * big]
    # mọi tiêu đề cỡ lớn (cả mặt đứng, mặt cắt, kết cấu) dùng để giới hạn khung tìm
    # (bỏ chữ ngắn như tên trục "A", "1", ký hiệu cao độ: chúng nằm trong mặt bằng chứ không phải tiêu đề)
    headings = [t for t in drawing.texts if big and t.height >= 0.6 * big
                and any(w in normalize(t.text) for w in HEADING_WORDS)]
    frames = _frame_lines(drawing)
    plans: list[PlanRegion] = []
    for t in sorted(titles, key=lambda t: (-t.y, t.x)):
        window = _shrink(_window(t, headings), t, frames)
        clusters = [c for c in _clusters(drawing, window) if c[0][1] <= t.y + 8000]
        if not clusters:
            continue
        bbox, weight = max(clusters, key=lambda c: c[1])
        level, source = _level(t.text), "tiêu đề"
        if level is None:
            inside = [_level(x.text) for x in drawing.texts
                      if bbox[0] <= x.x <= bbox[2] and bbox[1] <= x.y <= bbox[3] and LEVEL_RE.search(x.text)]
            inside = [v for v in inside if v is not None]
            ground = bool(re.search(r"\b(tang 1|tret)\b", normalize(t.text)))
            if ground and 0.0 in inside:
                level, source = 0.0, "ký hiệu ±0.000 trong mặt bằng"
            elif inside:
                level, source = Counter(inside).most_common(1)[0][0], "ký hiệu cao độ trong mặt bằng"
            elif ground:
                level, source = 0.0, "tầng 1 coi là ±0.000"
        name = re.sub(r"\s+", " ", t.text).strip()
        plans.append(PlanRegion(name, t.x, t.y, bbox, level, source if level is not None else "", weight))
    # QU-05: tên mặt bằng là khóa ở trang kiểm tra, /app, file đáp án, phần thô; hai tiêu đề trùng thì đánh số thêm
    seen: dict[str, int] = {}
    for p in plans:
        seen[p.name] = seen.get(p.name, 0) + 1
        if seen[p.name] > 1:
            p.title, p.name = p.name, f"{p.name} ({seen[p.name]})"
    return plans


def floor_heights(plans: list[PlanRegion]) -> dict[int, float]:
    """Chiều cao tầng (mm) theo chỉ số mặt bằng: hiệu cao độ với tầng trên liền kề, nếu hợp lý (2,4–6 m)."""
    levels = sorted({p.level_m for p in plans if p.level_m is not None})
    out = {}
    for i, p in enumerate(plans):
        if p.level_m is None:
            continue
        higher = [v for v in levels if v > p.level_m + 1e-6]
        if higher:
            h = (higher[0] - p.level_m) * 1000
            if 2400 <= h <= 6000:
                out[i] = round(h)
    return out


def has_only_other_plans(drawing: Drawing) -> bool:
    """File có tiêu đề "mặt bằng" nhưng toàn là mặt bằng kết cấu, móng, điện nước...: không có mặt bằng kiến trúc."""
    return any("mat bang" in normalize(t.text) for t in drawing.texts) and not any(
        _is_plan_title(t.text) for t in drawing.texts)
