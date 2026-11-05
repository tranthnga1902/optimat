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
from dataclasses import dataclass, replace

import numpy as np

from .. import config
from .dxf_reader import Drawing
from .encoding import normalize

PLAN_WORDS = ("mat bang",)
EXCLUDE_WORDS = ("ket cau", "da kieng", "giang", "mong cot", "co cot", "cot ", "bo tri thep", "tran", "mong", "mai", "dinh vi", "tong the", "dien", "nuoc", "cap ", "thoat",
                 "lat ", "bo tri", "coc", "dam", "thep", "san ", "chieu sang", "chong set", "phoi canh", "cau thang",
                 "chi tiet", "trich doan", "khai trien", "tu hoai", " thang ")
DETAIL_SCALE_MAX = config.threshold("NG01")     # tỷ lệ 1:n, n ≤ này là hình chi tiết (data/rules/nguong_nhan_dien.csv)
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


ABBREV = {"mb": "mat bang", "md": "mat dung", "mc": "mat cat"}


def _title(text: str) -> str:
    """Chữ thường bỏ dấu, viết đầy đủ chữ tắt đầu tiêu đề ("MB TRỆT" = mặt bằng trệt, "MĐ", "MC")."""
    t = normalize(text).strip()
    m = re.match(r"(mb|md|mc)\b", t)
    return ABBREV[m.group(1)] + t[2:] if m else t


def _is_plan_title(text: str) -> bool:
    # "sân thượng" bỏ dấu thành "san thuong", trùng từ loại "san " (mặt bằng sàn kết cấu)
    t = " " + _title(text).replace("san thuong", "san-thuong") + " "
    scale = re.search(r"\btl\s*:?\s*1\s*[:/]\s*(\d+)", t)
    return (any(w in t for w in PLAN_WORDS) and not any(w in t for w in EXCLUDE_WORDS)
            and not (scale and int(scale.group(1)) <= DETAIL_SCALE_MAX))


def _level(text: str) -> float | None:
    m = LEVEL_RE.search(text)
    if not m:
        return None
    value = float(m.group(2).replace(",", "."))
    return -value if m.group(1) == "-" else value


def _clusters(drawing: Drawing, window: tuple[float, float, float, float], max_line: float = MAX_CLUSTER_LINE_MM):
    """Cụm nét trong khung: ô lưới 1 m có nét, nối các ô kề nhau. Bỏ nét hatch, khung, trục, nét quá dài."""
    wx0, wy0, wx1, wy1 = window
    cells: dict[tuple[int, int], int] = defaultdict(int)
    for s in drawing.segments:
        if s.kind == "hatch" or any(w in normalize(s.layer) for w in FRAME_LAYER_WORDS):
            continue
        if not (wx0 <= s.x1 <= wx1 and wy0 <= s.y1 <= wy1 and wx0 <= s.x2 <= wx1 and wy0 <= s.y2 <= wy1):
            continue
        length = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
        if length > max_line:
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
FLOOR_MIN_M = config.threshold("NG03") / 1000      # hai tầng liền kề cách nhau trong khoảng này
FLOOR_MAX_M = config.threshold("NG04") / 1000
FRAME_PARTNER_SHARE = config.threshold("NG02")  # nét song song phủ từ tỷ lệ này chiều dài: là tường, không phải khung


def _frame_lines(drawing: Drawing):
    """Nét thẳng đứng hoặc nằm ngang rất dài, không có nét song song đi kèm ở khoảng cách chiều dày tường:
    viền khung bản vẽ, viền khung tên. Dùng làm giới hạn khung tìm mặt bằng.
    Nét đi kèm tính cả các đoạn ngắn: mặt tường dài 22 m có mặt kia bị cửa cắt thành nhiều đoạn vẫn là tường
    (trước đây chỉ so với nét dài khác, mặt bằng nhà ống bị cắt cụt ở chính bức tường dọc nhà)."""
    axis = {"h": [], "v": []}            # (tọa độ ngang trục, đầu, cuối) của mọi đoạn thẳng đứng / nằm ngang
    longs = []
    for s in drawing.segments:
        if s.kind != "line":
            continue
        dx, dy = s.x2 - s.x1, s.y2 - s.y1
        if abs(dx) < 1 or abs(dy) < 1:
            vertical = abs(dx) < 1
            axis["v" if vertical else "h"].append((s.x1, min(s.y1, s.y2), max(s.y1, s.y2)) if vertical
                                                  else (s.y1, min(s.x1, s.x2), max(s.x1, s.x2)))
            if math.hypot(dx, dy) >= FRAME_MIN_MM:
                longs.append(("v" if vertical else "h", *axis["v" if vertical else "h"][-1]))
    arr = {k: np.array(v, dtype=float).reshape(-1, 3) for k, v in axis.items()}
    out = []
    for kind, c, a, b in longs:
        o = arr[kind]
        gap = np.abs(o[:, 0] - c)
        overlap = np.clip(np.minimum(o[:, 2], b) - np.maximum(o[:, 1], a), 0, None)
        if overlap[(gap > 40) & (gap < 400)].sum() < FRAME_PARTNER_SHARE * (b - a):
            out.append((kind, c, a, b))
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


SCALE_SUFFIX_RE = re.compile(r"\s*\btl\b.*$")


def _merge_twin_titles(titles) -> tuple[list, set[int]]:
    """Một hình ghi tiêu đề hai lần cạnh nhau, một dòng thêm tỷ lệ ("MẶT BẰNG LẦU 2" và "MẶT BẰNG LẦU 2 TL 1:50", bộ 46
    cách nhau 19–21 m): gộp thành một tiêu đề ở giữa. Không gộp thì khung tìm chia đôi khoảng cách hai tiêu đề và cắt
    mặt bằng nhà ống dài 25 m làm hai mảnh. Chỉ gộp cặp cùng tên tầng, cùng hàng, một dòng có tỷ lệ một dòng không.
    Trả (tiêu đề sau gộp, id các tiêu đề đã gộp vào bạn để bỏ khỏi danh sách giới hạn khung)."""
    out, absorbed = [], set()
    for t in sorted(titles, key=lambda t: (-t.y, t.x)):
        if id(t) in absorbed:
            continue
        key, scaled = SCALE_SUFFIX_RE.sub("", _title(t.text)).strip(), bool(SCALE_SUFFIX_RE.search(_title(t.text)))
        twin = next((o for o in titles if o is not t and id(o) not in absorbed and abs(o.y - t.y) < 5000
                     and abs(o.x - t.x) < 25000 and SCALE_SUFFIX_RE.sub("", _title(o.text)).strip() == key
                     and bool(SCALE_SUFFIX_RE.search(_title(o.text))) != scaled), None)
        if twin is None:
            out.append(t)
            continue
        absorbed |= {id(t), id(twin)}
        named = t if scaled else twin                     # giữ dòng có tỷ lệ làm tên (đọc được tỷ lệ chi tiết)
        out.append(replace(named, x=(t.x + twin.x) / 2, y=min(t.y, twin.y)))
    return out, absorbed


def find_plans(drawing: Drawing) -> list[PlanRegion]:
    titles = [t for t in drawing.texts if _is_plan_title(t.text)]
    if not titles:
        return []
    big = max(t.height for t in titles) or 0
    titles, twins = _merge_twin_titles([t for t in titles if t.height >= 0.6 * big])
    # mọi tiêu đề cỡ lớn (cả mặt đứng, mặt cắt, kết cấu) dùng để giới hạn khung tìm
    # (bỏ chữ ngắn như tên trục "A", "1", ký hiệu cao độ: chúng nằm trong mặt bằng chứ không phải tiêu đề)
    headings = [t for t in drawing.texts if big and t.height >= 0.6 * big and id(t) not in twins
                and any(w in _title(t.text) for w in HEADING_WORDS)] + [t for t in titles if not any(t is h for h in drawing.texts)]
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
    _levels_from_chain(drawing, plans)
    # QU-05: tên mặt bằng là khóa ở trang kiểm tra, giao diện web, file đáp án, phần thô; hai tiêu đề trùng thì đánh số thêm
    seen: dict[str, int] = {}
    for p in plans:
        seen[p.name] = seen.get(p.name, 0) + 1
        if seen[p.name] > 1:
            p.title, p.name = p.name, f"{p.name} ({seen[p.name]})"
    return plans


def floor_order(title: str) -> int | None:
    """Thứ tự tầng theo tiêu đề: trệt / tầng 1 = 0, lầu n = n, tầng n = n - 1; sân thượng = -2 (tầng trên lầu cao nhất);
    lửng, tầng hầm, không rõ: None."""
    t = normalize(title)
    if re.search(r"\b(lung|ham|ngam)\b", t):
        return None
    if re.search(r"\btret\b", t):
        return 0
    if m := re.search(r"\blau\s*(\d+)\b", t):
        return int(m.group(1))
    if m := re.search(r"\btang\s*(\d+)\b", t):
        return int(m.group(1)) - 1
    if "san thuong" in t:
        return -2
    return None


def level_chain(drawing: Drawing) -> list[float]:
    """Chuỗi cao độ sàn ghi trên bản vẽ (thường ở mặt cắt, mặt đứng): từ ±0.000 đi lên, mỗi bước chọn cao độ ghi nhiều
    lần nhất trong khoảng 2,4–6 m phía trên. Rỗng khi không có ±0.000 hoặc không đi lên được."""
    counts = Counter(v for t in drawing.texts if LEVEL_RE.search(t.text) and (v := _level(t.text)) is not None)
    if not counts.get(0.0):
        return []
    chain = [0.0]
    while True:
        nxt = [(n, v) for v, n in counts.items()
               if chain[-1] + FLOOR_MIN_M <= v <= chain[-1] + FLOOR_MAX_M and n >= config.threshold("NG05")]
        if not nxt:
            return chain if len(chain) > 1 else []
        chain.append(max(nxt)[1])


def _levels_from_chain(drawing: Drawing, plans: list[PlanRegion]) -> None:
    """Mặt bằng chưa có cao độ (tiêu đề không ghi, trong mặt bằng không có ký hiệu): lấy theo thứ tự tầng trong
    chuỗi cao độ của bản vẽ. Chỉ khi quá nửa mặt bằng có cao độ khớp chuỗi (lệch ≤ 0,1 m: cốt hoàn thiện / kết cấu);
    một bản trệt lấy nhầm cốt sân −0.500 không làm hỏng cả bản vẽ."""
    if all(p.level_m is not None for p in plans):
        return
    chain = level_chain(drawing)
    order = {id(p): floor_order(p.title or p.name) for p in plans}
    tops = [o for o in order.values() if o is not None and o >= 0]
    for p in plans:
        if order[id(p)] == -2:
            order[id(p)] = max(tops) + 1 if tops else None
    known = [(order[id(p)], p.level_m) for p in plans if p.level_m is not None and order[id(p)] is not None]
    match = sum(o < len(chain) and abs(chain[o] - v) <= config.threshold("NG06") for o, v in known)
    if not chain or (known and match * 2 <= len(known)):
        return
    for p in plans:
        o = order[id(p)]
        if p.level_m is None and o is not None and o < len(chain):
            p.level_m, p.level_source = chain[o], f"chuỗi cao độ của bản vẽ, tầng thứ {o} (kiểm tra)"


def floor_heights(plans: list[PlanRegion], chain: list[float] = ()) -> dict[int, float]:
    """Chiều cao tầng (mm) theo chỉ số mặt bằng: hiệu cao độ với tầng trên liền kề, nếu hợp lý (2,4–6 m).
    chain (level_chain): tầng cao nhất (sân thượng) không có mặt bằng phía trên thì lấy cao độ kế tiếp trong chuỗi."""
    levels = sorted({p.level_m for p in plans if p.level_m is not None})
    out = {}
    for i, p in enumerate(plans):
        if p.level_m is None:
            continue
        # tầng trên cao hơn ít nhất 2,4 m: bỏ cao độ hoàn thiện / chi tiết sát cao độ tầng này (+3.650 và +3.700)
        higher = [v for v in levels if v >= p.level_m + FLOOR_MIN_M] or [v for v in chain if v >= p.level_m + FLOOR_MIN_M]
        if higher:
            h = (higher[0] - p.level_m) * 1000
            if FLOOR_MIN_M * 1000 <= h <= FLOOR_MAX_M * 1000:
                out[i] = round(h)
    return out


VIEW_START_WORDS = ("mat cat", "mat dung", "mat tien", "mat ben", "chi tiet", "trich doan")


def has_only_views(drawing: Drawing) -> bool:
    """File không có tiêu đề mặt bằng tầng nhưng có tiêu đề mặt cắt, mặt đứng, chi tiết ("MẶT CẮT A-A", "CHI TIẾT
    CẦU THANG"): nét trên đó không phải tường mặt bằng, không đo cả bản vẽ như một mặt bằng."""
    return not any(_is_plan_title(t.text) for t in drawing.texts) and any(
        _title(t.text).startswith(VIEW_START_WORDS) for t in drawing.texts)


def has_only_other_plans(drawing: Drawing) -> bool:
    """File có tiêu đề "mặt bằng" nhưng toàn là mặt bằng kết cấu, móng, điện nước...: không có mặt bằng kiến trúc."""
    return any("mat bang" in normalize(t.text) for t in drawing.texts) and not any(
        _is_plan_title(t.text) for t in drawing.texts)
