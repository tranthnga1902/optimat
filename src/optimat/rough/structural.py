"""Đọc mặt bằng kết cấu ra cấu kiện phần thô: móng (đếm theo ký hiệu), dầm và đà kiềng (đo theo cặp nét).

Loại hình vẽ nhận theo tiêu đề (drawing/sheets.py, data/rules/loai_ban_ve.csv). Ký hiệu cấu kiện (C1, D7, ĐK1, M2) nhận
theo data/rules/ky_hieu_cau_kien.csv: chữ đã bỏ dấu khớp trọn một mẫu. Trên mặt bằng móng, mặt bằng dầm:
    móng       = số ký hiệu M… trên mặt bằng móng, theo từng loại
    dầm        = mỗi ký hiệu D…/ĐK… ứng với cặp nét song song gần nhất (cách nhau BEAM_WIDTH_MM) chạy qua chỗ ký hiệu;
                 nhiều ký hiệu trên cùng cặp nét thì cắt ở trung điểm giữa hai ký hiệu kề nhau
    rộng dầm   = khoảng cách cặp nét; tiết diện ghi chữ ("ĐÀ KIỀNG ĐK2 300X500") thắng, rồi tới mặt cắt dầm
    cột        = số ký hiệu C… (chỉ báo, cột vẫn bóc trên mặt bằng kiến trúc để không đếm hai lần)
    bảng thống kê cột ("THỐNG KÊ CỘT": mã cột + SL, hàng "Từ … Đến …", ô có mặt cắt) thì bê tông, cốp pha cột lấy từ bảng,
                 cột trên mặt bằng kiến trúc chỉ dùng trừ khối xây (read_column_schedule)
Tỷ lệ mỗi hình vẽ = số hiển thị / số đo của đường kích thước trong hình (drawing/dimensions.py): mặt bằng vẽ TL 1/50 trên
khung 1/100 có tỷ lệ 0,5. Không có đường kích thước thì coi là 1 và cảnh báo.
Hình chi tiết (đọc số hiển thị của đường kích thước):
    mặt cắt    = chữ "MC 1-1"…; thuộc tiêu đề chi tiết (MÓNG M1, DẦM D1) gần nhất nằm phía trên nó; vùng của mặt cắt
                 là phía trên chữ, chia đôi khoảng cách tới mặt cắt cùng hàng, dừng ở mặt cắt hàng trên hoặc tiêu đề
    móng       = dài × rộng: số ngang, số đứng lớn nhất trên hình MÓNG Mx; cao: số đứng lớn nhất trong FOOTING_H_MM
                 trên các mặt cắt của nó; lót: số đứng hay gặp nhất trong LEAN_MM. Móng coi là khối hộp dài × rộng × cao
    dầm        = mỗi mặt cắt: rộng = số ngang trong BEAM_WIDTH_MM, cao (gồm sàn) = số đứng lớn nhất trên rộng, đến
                 BEAM_DEPTH_MAX_MM; lấy cặp hay gặp nhất của mọi mặt cắt thuộc dầm đó
Số đọc từ chi tiết luôn kèm cảnh báo để người dùng kiểm tra; không đọc được thì để trống (Quy ước B7).
"""
from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from .. import config
from ..drawing.dimensions import Dim, inside, read_dimensions, view_scale
from ..drawing.encoding import normalize
from ..drawing.layer_classifier import LayerClass
from ..drawing.plans import FRAME_LAYER_WORDS
from ..drawing.sheets import View, find_views, sheet_inventory
from .beams import Beam
from .foundations import SAME_SPOT_MM
from .models import FoundationItem

ELEMENT_FILE = config.DATA_DIR / "rules" / "ky_hieu_cau_kien.csv"
PLAN_TYPES = ("BV04", "BV06", "BV08")       # mặt bằng móng, cột, dầm
BEAM_WIDTH_MM = (100.0, 700.0)
LABEL_REACH_MM = 1500.0                      # ký hiệu cách trục dầm không quá khoảng này
SECTION_HALF_MM = 10000.0                    # nửa bề rộng vùng mặt cắt khi không có mặt cắt cùng hàng (mm bản vẽ)
SECTION_REACH_MM = 40000.0                   # mặt cắt cách tiêu đề chi tiết không quá khoảng này
FOOTING_H_MM = (200.0, 2000.0)
LEAN_MM = (80.0, 200.0)               # 50 thường là lớp bê tông bảo vệ, không phải lót
BEAM_DEPTH_MAX_MM = 1500.0
SIZE_RE = re.compile(r"(\d{2,4})\s*[x×*]\s*(\d{2,4})", re.I)


@lru_cache(maxsize=4)
def load_element_rules(path: str | None = None) -> tuple[tuple[re.Pattern, str, str], ...]:
    # shortcut: đọc CSV, chưa có bảng PostgreSQL riêng (thêm bảng là đổi lược đồ, cần duyệt)
    rows = pd.read_csv(Path(path or ELEMENT_FILE), dtype=str, keep_default_na=False).to_dict("records")
    return tuple((re.compile(r["mau"]), r["vai_tro"], r["ten"]) for r in rows)


def element_of(text: str) -> tuple[str, str, str] | None:
    """Ký hiệu cấu kiện -> (vai trò, tên loại, khóa chữ thường bỏ dấu). Chữ phải khớp trọn mẫu."""
    key = re.sub(r"\s+", "", normalize(text))
    key = re.sub(r"(?<=[a-z])[-–](?=\d)", "", key)
    for pat, role, name in load_element_rules():
        if pat.fullmatch(key):
            return role, name, key
    return None


def written_sections(drawing) -> dict[str, tuple[float, float]]:
    """Tiết diện ghi bằng chữ cạnh ký hiệu ("ĐÀ KIỀNG ĐK2 300X500", "D1 (220x400)") -> {khóa ký hiệu: (rộng, cao)}."""
    out = {}
    for t in drawing.texts:
        m = SIZE_RE.search(t.text)
        if not m:
            continue
        for word in re.split(r"[\s(),:]+", t.text[:m.start()]):
            if word and (e := element_of(word)) and e[0] in ("BEAM", "COLUMN"):
                out[e[2]] = (float(m.group(1)), float(m.group(2)))
    return out


def floor_count(title: str) -> int:
    """Số tầng một mặt bằng kết cấu dùng chung, đọc từ tiêu đề: "LẦU 2-3-4-SÂN THƯỢNG" -> 4, "LẦU 2-LẦU 5" -> 4."""
    m = re.search(r"\b(lau|tang)\s+(.+)$", normalize(title))
    parts = [p.strip() for p in re.split(r"\s*-\s*", m.group(2))] if m else []
    if len(parts) < 2:
        return 1
    nums = [re.fullmatch(r"(?:(?:lau|tang)\s+)?(\d+)", p) for p in parts]
    if len(parts) == 2 and all(nums) and int(nums[1].group(1)) > int(nums[0].group(1)):
        return int(nums[1].group(1)) - int(nums[0].group(1)) + 1
    return len(parts)


def _title_key(title: str):
    """Ký hiệu cấu kiện trong tiêu đề chi tiết: "MÓNG M1" -> ("FOUNDATION", "m1"), "DẦM D7a" -> ("BEAM", "d7a")."""
    for w in reversed(re.split(r"[\s(),:]+", title)):
        if w and (e := element_of(w)) and e[0] in ("BEAM", "FOUNDATION"):
            return e[0], e[2]
    return None


def detail_sections(drawing, views: list[View], dims: list[Dim]) -> dict[tuple, list[list[Dim]]]:
    """Đường kích thước của từng mặt cắt, gom theo cấu kiện của tiêu đề chi tiết: {(vai trò, khóa): [[Dim...]...]}."""
    labels = [t for t in drawing.texts if (e := element_of(t.text)) and e[0] == "SECTION"]
    owners = [(v, k) for v in views if v.ma in ("BV05", "BV09") and (k := _title_key(v.title))]
    out: dict[tuple, list[list[Dim]]] = {}
    for t in labels:
        above = [(math.hypot(v.x - t.x, v.y - t.y), v, k) for v, k in owners if v.y > t.y]
        if not above:
            continue
        dist, v, k = min(above, key=lambda a: a[0])
        if dist > SECTION_REACH_MM:
            continue
        left, right, top = t.x - SECTION_HALF_MM, t.x + SECTION_HALF_MM, v.y
        for o in labels:
            if o is not t and abs(o.y - t.y) < 1000:
                if o.x < t.x:
                    left = max(left, (o.x + t.x) / 2)
                elif o.x > t.x:
                    right = min(right, (o.x + t.x) / 2)
        for o in labels:
            if o.y > t.y + 1000 and left <= o.x <= right:
                top = min(top, o.y)
        out.setdefault(k, []).append(inside(dims, (left, t.y, right, top)))
    return out


def beam_detail_sizes(sections: dict) -> dict[str, tuple[float, float]]:
    """Tiết diện dầm từ mặt cắt: {khóa dầm: (rộng, cao gồm sàn)}, cặp hay gặp nhất."""
    out = {}
    for (role, key), secs in sections.items():
        if role != "BEAM":
            continue
        pairs = Counter()
        for ds in secs:
            widths = [d.value for d in ds if not d.vertical and BEAM_WIDTH_MM[0] <= d.value <= BEAM_WIDTH_MM[1]]
            if not widths:
                continue
            b = Counter(widths).most_common(1)[0][0]
            depths = [d.value for d in ds if d.vertical and b < d.value <= BEAM_DEPTH_MAX_MM]
            if depths:
                pairs[(b, max(depths))] += 1
        if pairs:
            out[key] = pairs.most_common(1)[0][0]
    return out


def footing_detail_sizes(views: list[View], sections: dict, dims: list[Dim]) -> dict[str, dict]:
    """Kích thước móng từ chi tiết: {khóa móng: {length_mm, width_mm, height_mm, lean_thickness_mm, nguon}}."""
    out = {}
    details = [v for v in views if v.ma == "BV05" and v.bbox]
    for v in details:
        k = _title_key(v.title)
        if not k or k[0] != "FOUNDATION":
            continue
        if k[1].startswith("bm"):
            # Hình cắt ngang móng băng không cho chiều dài chạy dọc băng.
            continue
        # khung hình nới xuống tới dưới tiêu đề (đường kích thước tổng hay nằm sát tiêu đề), mỗi bên không quá nửa
        # khoảng cách tới chi tiết móng gần nhất cùng hàng (khung tự tìm có thể lấn sang hình bên cạnh)
        x0, y0, x1, y1 = _grown(v.bbox)
        gaps = [abs(o.x - v.x) for o in details if o is not v and abs(o.y - v.y) < 5000]
        if gaps:
            x0, x1 = max(x0, v.x - min(gaps) / 2), min(x1, v.x + min(gaps) / 2)
        ds = inside(dims, (x0, min(y0, v.y - 1000), x1, y1))
        horiz = [d.value for d in ds if not d.vertical]
        vert = [d.value for d in ds if d.vertical]
        secs = [d for s in sections.get(k, []) for d in s if d.vertical]
        heights = [d.value for d in secs if FOOTING_H_MM[0] <= d.value <= FOOTING_H_MM[1]]
        leans = [d.value for d in secs if LEAN_MM[0] <= d.value <= LEAN_MM[1]]
        size = {"length_mm": max(horiz) if horiz else None, "width_mm": max(vert) if vert else None,
                     "height_mm": max(heights) if heights else None,
                     "lean_thickness_mm": max(Counter(leans).items(), key=lambda kv: (kv[1], kv[0]))[0] if leans else None,
                     "nguon": f"{v.title} tại ({v.x:g}, {v.y:g}), {len(sections.get(k, []))} mặt cắt"}
        previous = out.get(k[1])
        if previous and (previous.get("conflict") or any(size[d] != previous[d] for d in size if d != "nguon")):
            def describe(s):
                return " × ".join("?" if s[d] is None else f"{s[d]:g}" for d in ("length_mm", "width_mm", "height_mm"))
            earlier = previous["nguon"] if previous.get("conflict") else f"{previous['nguon']} ({describe(previous)} mm)"
            size = {d: None for d in size if d != "nguon"} | {
                "conflict": True, "nguon": f"{earlier} / {size['nguon']} ({describe(size)} mm)"}
        out[k[1]] = size
    return out


@dataclass
class StructuralTakeoff:
    views: list[View]
    sheets: list[dict]
    beams: dict[str, list[Beam]] = field(default_factory=dict)          # theo tiêu đề mặt bằng
    foundations: list[FoundationItem] = field(default_factory=list)
    columns: dict[str, dict[str, int]] = field(default_factory=dict)    # mặt bằng -> {C1: số lượng}
    column_sections: dict[str, tuple[float, float]] = field(default_factory=dict)   # tiết diện cột ghi chữ: {c1: (b, h)}
    column_schedule: list[ColumnSpan] = field(default_factory=list)     # bảng thống kê cột (read_column_schedule)
    structural_columns: list = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ColumnSpan(BaseModel):
    """Một ô của bảng thống kê cột: cột `code` (số lượng `count`) đoạn từ cao độ z_from đến z_to, tiết diện b × h."""
    code: str
    count: int
    z_from_mm: float
    z_to_mm: float
    b_mm: float
    h_mm: float
    floor_key: str | None = None


_LEVEL = re.compile(r"([+\-±]?)\s*(\d+[.,]\d+)")


def _z(text: str) -> float | None:
    m = _LEVEL.search(text)
    return None if m is None else (-1 if m.group(1) == "-" else 1) * float(m.group(2).replace(",", ".")) * 1000


def read_column_schedule(drawing, dims: list[Dim]) -> tuple[list[ColumnSpan], list[str]]:
    """Bảng "THỐNG KÊ CỘT" dạng lưới: hàng tiêu đề có mã cột (C1…) kèm "SL: n"; mỗi hàng là một đoạn cao độ ghi
    "Từ +a" / "Đến +b"; ô giao vẽ mặt cắt cột: rộng = số ngang lớn nhất, cao = số đứng lớn nhất của đường kích thước trong
    ô (số nhỏ hơn là lớp bảo vệ, khoảng thép). Ô không đọc được tiết diện thì bỏ và cảnh báo (B7)."""
    spans, warnings = [], []
    for title in (t for t in drawing.texts if "thong ke cot" in normalize(t.text)):
        heads = [(t, e) for t in drawing.texts if (e := element_of(t.text)) and e[0] == "COLUMN"
                 and abs(t.x - title.x) < 40000 and 0 <= t.y - title.y <= 3000]
        if not heads:
            continue
        hy = statistics.median(t.y for t, _ in heads)
        heads = sorted(((t, e) for t, e in heads if abs(t.y - hy) < 300), key=lambda h: h[0].x)
        xs = [t.x for t, _ in heads]
        step = statistics.median(b - a for a, b in zip(xs, xs[1:])) if len(xs) > 1 else 5000.0
        counts = {}
        for t in drawing.texts:
            if (m := re.match(r"\s*sl\s*:\s*(\d+)", normalize(t.text))) and abs(t.y - hy) < 1000:
                near = min(heads, key=lambda h: abs(h[0].x - t.x))
                if abs(near[0].x - t.x) < step / 2:
                    counts[near[0].text.strip().upper()] = int(m.group(1))
        froms = [t for t in drawing.texts if normalize(t.text).startswith("tu") and _z(t.text) is not None
                 and t.y > hy and abs(t.x - title.x) < 40000 and t.x < xs[0]]
        tos = [t for t in drawing.texts if normalize(t.text).startswith("den") and _z(t.text) is not None
               and t.y > hy and abs(t.x - title.x) < 40000 and t.x < xs[0]]
        rows = []
        for f in froms:
            below = [t for t in tos if 0 < f.y - t.y < 3000 and abs(t.x - f.x) < 3000]
            if below:
                to = min(below, key=lambda t: f.y - t.y)
                rows.append(((f.y + to.y) / 2, _z(f.text), _z(to.text)))
        rows.sort()
        ys = [r[0] for r in rows]
        for i, (y, z0, z1) in enumerate(rows):
            lo = (ys[i - 1] + y) / 2 if i else y - (ys[1] - y if len(ys) > 1 else 3000) / 2
            hi = (ys[i + 1] + y) / 2 if i + 1 < len(ys) else y + (y - ys[i - 1] if i else 3000) / 2
            for t, e in heads:
                code = t.text.strip().upper()
                cell = [d for d in dims if abs(d.x - t.x) < step / 2 and lo <= d.y <= hi]
                b = max((d.value for d in cell if not d.vertical), default=None)
                h = max((d.value for d in cell if d.vertical), default=None)
                if b and h and code in counts:
                    spans.append(ColumnSpan(code=code, count=counts[code], z_from_mm=z0, z_to_mm=z1, b_mm=b, h_mm=h))
                else:
                    warnings.append(f"Bảng thống kê cột: {code} đoạn {z0 / 1000:+.3f} → {z1 / 1000:+.3f} chưa đọc được "
                                    + ("số lượng" if code not in counts else "tiết diện") + ", chưa tính.")
    if spans:
        warnings.append(f"Bê tông cột lấy từ bảng thống kê cột ({len({s.code for s in spans})} loại cột, {len(spans)} đoạn "
                        "cao độ; tiết diện đọc từ đường kích thước trong bảng): kiểm tra.")
    return spans, warnings


def _lines(drawing, bbox):
    """Nét thẳng ngang / đứng trong khung, bỏ nét hatch, chú thích, khung, trục: ('h'|'v', tọa độ, đầu, cuối)."""
    x0, y0, x1, y1 = bbox
    out = []
    for s in drawing.segments:
        if s.kind != "line" or drawing.layer_classes.get(s.layer) == LayerClass.ANNOTATION:
            continue
        if any(w in normalize(s.layer + " " + s.source) for w in FRAME_LAYER_WORDS):
            continue
        if not (x0 <= min(s.x1, s.x2) and max(s.x1, s.x2) <= x1 and y0 <= min(s.y1, s.y2) and max(s.y1, s.y2) <= y1):
            continue
        if abs(s.y2 - s.y1) < 1 and abs(s.x2 - s.x1) >= 300:
            out.append(("h", (s.y1 + s.y2) / 2, min(s.x1, s.x2), max(s.x1, s.x2)))
        elif abs(s.x2 - s.x1) < 1 and abs(s.y2 - s.y1) >= 300:
            out.append(("v", (s.x1 + s.x2) / 2, min(s.y1, s.y2), max(s.y1, s.y2)))
    return out


def _nearest_pair(lines, x: float, y: float):
    """Cặp nét song song gần ký hiệu nhất: (khoảng cách tới trục, hướng, trục, đầu, cuối, rộng, khóa cặp) hoặc None."""
    best = None
    for o in ("h", "v"):
        along, across = (x, y) if o == "h" else (y, x)
        near = [l for l in lines if l[0] == o and l[2] - 200 <= along <= l[3] + 200 and abs(l[1] - across) <= LABEL_REACH_MM]
        for i, a in enumerate(near):
            for b in near[i + 1:]:
                width = abs(a[1] - b[1])
                lo, hi = max(a[2], b[2]), min(a[3], b[3])
                if not (BEAM_WIDTH_MM[0] <= width <= BEAM_WIDTH_MM[1]) or not (lo - 200 <= along <= hi + 200):
                    continue
                axis = (a[1] + b[1]) / 2
                cand = (abs(axis - across), o, axis, lo, hi, width, (o, round(axis), round(lo), round(hi)))
                if best is None or cand[:1] < best[:1]:
                    best = cand
    return best


def _grown(bbox):
    """Khung hình vẽ nới thêm LABEL_REACH_MM: ký hiệu hay đặt sát ngoài nét ngoài cùng."""
    x0, y0, x1, y1 = bbox
    return x0 - LABEL_REACH_MM, y0 - LABEL_REACH_MM, x1 + LABEL_REACH_MM, y1 + LABEL_REACH_MM


def _labels(drawing, bbox):
    x0, y0, x1, y1 = _grown(bbox)
    return [(t, e) for t in drawing.texts if x0 <= t.x <= x1 and y0 <= t.y <= y1 and (e := element_of(t.text))]


def _scale_by_beam_width(drawing, view: View, dims: list[Dim], sections: dict) -> float | None:
    """Khung mặt bằng dầm chứa cả hình chi tiết tỷ lệ khác (dầm mái bộ 46: 82 kích thước 1:20, 7 kích thước của mặt bằng):
    trong các tỷ lệ có ≥ 2 đường kích thước, chọn tỷ lệ làm bề rộng cặp nét dầm gần nhất với bề rộng ghi trên mặt cắt dầm.
    None khi chỉ có một tỷ lệ hoặc không có bề rộng mặt cắt để so."""
    cands = [r for r, n in Counter(round(d.value / d.measured, 3) for d in dims if d.measured).items() if n >= 2]
    widths = {b for b, _ in sections.values() if b}
    if len(cands) < 2 or not widths:
        return None
    best = None
    for s in cands:
        beams, _ = measure_beams(drawing, view, {}, s)
        if beams:
            err = statistics.median(min(abs(b.b_mm - w) for w in widths) for b in beams)
            if best is None or err < best[0]:
                best = (err, s)
    return best[1] if best else None


def measure_beams(drawing, view: View, sections: dict, scale: float = 1.0) -> tuple[list[Beam], list[str]]:
    """scale: hệ số đổi số đo trên bản vẽ ra mm thật (hình vẽ phóng to 2 lần: 0,5)."""
    labels = [(t, e) for t, e in _labels(drawing, view.bbox) if e[0] == "BEAM"]
    lines = _lines(drawing, _grown(view.bbox))
    groups: dict[tuple, list] = {}
    unplaced = []
    for t, e in labels:
        p = _nearest_pair(lines, t.x, t.y)
        if p is None:
            unplaced.append(t.text.strip())
            continue
        groups.setdefault(p[6], []).append((t.x if p[1] == "h" else t.y, t, e, p))
    beams, warnings = [], []
    for members in groups.values():
        members.sort(key=lambda m: m[0])
        _, o, axis, lo, hi, width, _ = members[0][3]
        width *= scale
        cuts = [lo] + [(a[0] + b[0]) / 2 for a, b in zip(members, members[1:])] + [hi]
        for (_, t, e, _), a, b in zip(members, cuts, cuts[1:]):
            sec = sections.get(e[2])
            pts = [(p[0] * scale, p[1] * scale) for p in (((a, axis), (b, axis)) if o == "h" else ((axis, a), (axis, b)))]
            beams.append(Beam(id=t.text.strip().upper(), x1=round(pts[0][0], 1), y1=round(pts[0][1], 1),
                              x2=round(pts[1][0], 1), y2=round(pts[1][1], 1), b_mm=sec[0] if sec else round(width / 10) * 10,
                              d_mm=sec[1] if sec else None, source="structural"))
            if sec and abs(width - sec[0]) > 0.2 * sec[0]:
                warnings.append(f"{view.title}: {t.text.strip()} rộng ghi {sec[0]:.0f} mm, đo trên bản vẽ {width:.0f} mm "
                                f"(tỷ lệ {width / sec[0]:.2f}): kiểm tra tỷ lệ hình vẽ, chiều dài dầm đo theo cùng tỷ lệ.")
    if unplaced:
        warnings.append(f"{view.title}: {len(unplaced)} ký hiệu dầm không tìm thấy cặp nét dầm ({', '.join(sorted(set(unplaced))[:5])}).")
    extra = _unlabeled_beams(lines, [m[0][3] for m in groups.values()], scale)
    if extra:
        beams += extra
        warnings.append(f"{view.title}: {len(extra)} đoạn dầm không ghi ký hiệu "
                        f"({sum(math.hypot(b.x2 - b.x1, b.y2 - b.y1) for b in extra) / 1000:.1f} m), lấy theo cặp nét cùng bề rộng "
                        "với dầm có ký hiệu, mã D?, cao theo cao dầm chung: kiểm tra.")
    no_depth = sorted({b.id for b in beams if b.d_mm is None})
    if no_depth:
        warnings.append(f"{view.title}: chưa có cao dầm {', '.join(no_depth[:8])}{'…' if len(no_depth) > 8 else ''} "
                        "(không có tiết diện ghi chữ hay mặt cắt dầm): nhập cao dầm hoặc cao dầm chung trong thông số công trình.")
    return beams, warnings


MIN_UNLABELED_BEAM_MM = config.threshold("NG07")   # đoạn cặp nét ngắn hơn (cạnh cột, đầu dầm) không là dầm không ký hiệu


def _unlabeled_beams(lines, labeled, scale: float) -> list[Beam]:
    """Bản vẽ kết cấu thường ghi ký hiệu một lần cho mỗi loại dầm: cặp nét song song cùng bề rộng (±5%) với dầm đã có ký
    hiệu trong hình là dầm. Gộp các đoạn cùng trục (lệch ≤ 15 mm), bỏ phần đã có dầm ký hiệu (bộ 46 lầu 1: 72 → ~100 m,
    dự toán 95 m). labeled: cặp nét của dầm có ký hiệu (kết quả _nearest_pair)."""
    widths = {p[5] for p in labeled}
    if not widths:
        return []
    tol = config.threshold("NG09") / scale
    spans: dict[str, list[list]] = {"h": [], "v": []}        # [trục, [(đầu, cuối)...], phần đã có ký hiệu]

    def slot(o, axis):
        for s in spans[o]:
            if abs(s[0] - axis) <= tol:
                return s
        spans[o].append(s := [axis, [], []])
        return s
    for p in labeled:
        slot(p[1], p[2])[2].append((p[3], p[4]))
    for o in ("h", "v"):
        ls = sorted((l for l in lines if l[0] == o), key=lambda l: l[1])
        for i, a in enumerate(ls):
            for b in ls[i + 1:]:
                w = b[1] - a[1]
                if w > max(widths) * 1.05:
                    break
                lo, hi = max(a[2], b[2]), min(a[3], b[3])
                if any(abs(w - x) <= config.threshold("NG08") * x for x in widths) and (hi - lo) * scale >= MIN_UNLABELED_BEAM_MM:
                    slot(o, (a[1] + b[1]) / 2)[1].append((lo, hi, w))
    out = []                                                  # (hướng, trục, đầu, cuối, rộng)
    for o in ("h", "v"):
        for axis, ivs, done in spans[o]:
            merged: list[list[float]] = []
            for lo, hi, w in sorted(ivs):
                if merged and lo <= merged[-1][1] + tol:
                    merged[-1][1] = max(merged[-1][1], hi)
                else:
                    merged.append([lo, hi, w])
            for lo, hi, w in merged:
                for dlo, dhi in sorted(done):          # bỏ phần đã có dầm ký hiệu
                    if dhi <= lo or dlo >= hi:
                        continue
                    if (dlo - lo) * scale >= MIN_UNLABELED_BEAM_MM:
                        out.append((o, axis, lo, dlo, w))
                    lo = max(lo, dhi)
                if (hi - lo) * scale >= MIN_UNLABELED_BEAM_MM:
                    out.append((o, axis, lo, hi, w))
    beams = []
    for o, axis, lo, hi, w in out:
        pts = ((lo, axis), (hi, axis)) if o == "h" else ((axis, lo), (axis, hi))
        beams.append(Beam(id="D?", x1=round(pts[0][0] * scale, 1), y1=round(pts[0][1] * scale, 1),
                          x2=round(pts[1][0] * scale, 1), y2=round(pts[1][1] * scale, 1),
                          b_mm=round(w * scale / 10) * 10, source="structural"))
    return beams


def _footing_center(lines, x: float, y: float, a: float, b: float, tol: float = 0.03):
    """Tâm khung chữ nhật a × b (hoặc b × a) gần ký hiệu (x, y) nhất, ghép từ hai nét ngang + hai nét đứng; None nếu không có."""
    best = None
    for la, lb in ((a, b), (b, a)):
        hs = [l for l in lines if l[0] == "h" and abs((l[3] - l[2]) - la) <= tol * la]
        vs = [l for l in lines if l[0] == "v" and abs((l[3] - l[2]) - lb) <= tol * lb]
        for i, h1 in enumerate(hs):
            for h2 in hs[i + 1:]:
                if abs(abs(h1[1] - h2[1]) - lb) > tol * lb or abs(h1[2] - h2[2]) > tol * la:
                    continue
                y0, y1 = sorted((h1[1], h2[1]))
                x0, x1 = h1[2], h1[3]
                if sum(1 for v in vs if min(abs(v[1] - x0), abs(v[1] - x1)) <= tol * la and abs(v[2] - y0) <= tol * lb) < 2:
                    continue
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                gap = max(abs(x - cx) - la / 2, abs(y - cy) - lb / 2, 0)      # 0: ký hiệu nằm trong khung
                if gap <= LABEL_REACH_MM and (best is None or gap < best[0]):
                    best = (gap, cx, cy)
    return None if best is None else best[1:]


def read_structural(drawing, scale: float | None = None, dims: list[Dim] | None = None) -> StructuralTakeoff:
    """scale: hệ số đổi số đo trên mặt bằng kết cấu ra mm thật; None: tự suy từ đường kích thước của từng mặt bằng.
    dims: đường kích thước (mặc định đọc từ bản vẽ gốc)."""
    views = find_views(drawing, bbox_for=PLAN_TYPES + ("BV05",))
    out = StructuralTakeoff(views=views, sheets=sheet_inventory(views))
    from .structural_column_instances import read_column_instances
    out.structural_columns = read_column_instances(drawing, views)
    dims = read_dimensions(drawing) if dims is None else dims
    details = detail_sections(drawing, views, dims)
    beam_sizes = beam_detail_sizes(details)
    if beam_sizes:
        out.warnings.append("Tiết diện dầm đọc từ mặt cắt dầm (rộng × cao gồm sàn): "
                            + ", ".join(f"{k.upper()} {b:.0f}×{h:.0f}" for k, (b, h) in sorted(beam_sizes.items()))
                            + "; kiểm tra trên trang kiểm tra.")
    sections = {**beam_sizes, **written_sections(drawing)}      # tiết diện ghi chữ thắng
    spots: dict[str, list] = {}             # móng -> [(mặt bằng, x, y, tỷ lệ)] của từng ký hiệu
    plan_lines: dict[str, list] = {}
    for v in views:
        if v.ma not in PLAN_TYPES or v.bbox is None:
            continue
        s = scale
        if s is None:
            s = view_scale(inside(dims, _grown(v.bbox)))
            if v.ma in ("BV04", "BV08") and (picked := _scale_by_beam_width(drawing, v, inside(dims, _grown(v.bbox)), sections)):
                if s is not None and abs(picked - s) > 0.01:
                    out.warnings.append(f"{v.title}: khung có hình vẽ nhiều tỷ lệ (trung vị {s:.3g}); dùng tỷ lệ {picked:.3g} "
                                        "cho bề rộng dầm đo được khớp bề rộng ghi trên mặt cắt dầm, kiểm tra.")
                s = picked
            if s is None:
                s = 1.0
                if v.ma in ("BV04", "BV08"):
                    out.warnings.append(f"{v.title}: không có đường kích thước để suy tỷ lệ, đang coi số đo là mm thật.")
            elif abs(s - 1) > 0.01 and v.ma in ("BV04", "BV08"):
                out.warnings.append(f"{v.title}: tỷ lệ hình vẽ {s:.3g} (số hiển thị / số đo của đường kích thước), "
                                    "chiều dài, rộng dầm đã đổi theo tỷ lệ này.")
        inside_labels = _labels(drawing, v.bbox)
        cols = Counter(t.text.strip().upper() for t, e in inside_labels if e[0] == "COLUMN")
        if cols:
            out.columns[v.title] = dict(sorted(cols.items()))
        if v.ma == "BV04":
            for t, e in inside_labels:
                if e[0] == "FOUNDATION":
                    spots.setdefault(t.text.strip().upper(), []).append((v.title, t.x, t.y, s))
            plan_lines[v.title] = _lines(drawing, _grown(v.bbox))
        if v.ma in ("BV04", "BV08"):
            beams, warn = measure_beams(drawing, v, sections, s)
            if beams:
                out.beams[v.title] = beams
            out.warnings += warn
    out.column_sections = {k: v for k, v in sections.items() if (e := element_of(k)) and e[0] == "COLUMN"}
    out.column_schedule, warn = read_column_schedule(drawing, dims)
    out.warnings += warn
    sizes = footing_detail_sizes(views, details, dims)
    strip_sections = {_title_key(v.title) for v in views if v.ma == "BV05" and "mong bang" in normalize(v.title)}
    strip_notes: dict[str, set[tuple[float, int | None]]] = {}
    for t in drawing.texts:
        note = re.fullmatch(r"(bm[-–]?\d+[a-z]?)\s*:\s*l\s*=\s*(\d+(?:[.,]\d+)?)\s*mm(?:\s*;\s*sl\s*=\s*(\d+))?",
                            t.text.strip(), re.IGNORECASE)
        if note and (mark := element_of(note[1])) and ("FOUNDATION", mark[2]) in strip_sections:
            length = float(note[2].replace(",", "."))
            if length > 0:
                strip_notes.setdefault(mark[2], set()).add((length, int(note[3]) if note[3] else None))
    for n, pts in sorted(spots.items()):
        mark = element_of(n)[2]
        size = sizes.get(mark, {})
        is_strip = mark.startswith("bm")
        if is_strip:
            lengths = {length for length, _ in strip_notes.get(mark, set())}
            if len(lengths) == 1:
                length = next(iter(lengths))
                size = {"gross_length_mm": length, "nguon": f"ghi chú {n}: L={length:g} mm và mặt cắt móng băng cùng ký hiệu"}
            out.warnings.append(f"{n}: cần kiểm phạm vi băng, phần giao và tiết diện móng trước khi tính thể tích."
                                + (f" Có nhiều chiều dài ghi trên bản vẽ: {sorted(lengths)} mm." if len(lengths) > 1 else ""))
        plans = {p[0] for p in pts}
        uniq = []                                  # ký hiệu vẽ trùng chỗ (copy đè) chỉ đếm một lần
        for p in pts:
            if not any(q[0] == p[0] and math.hypot(q[1] - p[1], q[2] - p[2]) * p[3] < SAME_SPOT_MM for q in uniq):
                uniq.append(p)
        c = len(uniq)
        if len(pts) > c:
            out.warnings.append(f"Móng {n}: {len(pts) - c} ký hiệu trùng vị trí, đếm một lần.")
        centers = []
        if len(plans) == 1 and size.get("length_mm") and size.get("width_mm"):
            for title, x, y, sc in uniq:
                ctr = _footing_center(plan_lines[title], x, y, size["length_mm"] / sc, size["width_mm"] / sc)
                centers.append(None if ctr is None else (round(ctr[0] * sc, 1), round(ctr[1] * sc, 1)))
        found_all = bool(centers) and None not in centers
        if size.get("conflict"):
            out.warnings.append(f"Móng {n}: các chi tiết cùng ký hiệu có kích thước khác nhau; cần xác định chi tiết cho từng vị trí. {size['nguon']}")
        f = FoundationItem(name=n, count=c, kind="bang" if is_strip else None, **{k: v for k, v in size.items() if k.endswith("_mm")},
                           positions=centers if found_all else [], plan=next(iter(plans)) if found_all else None,
                           source=f"{n} trên {', '.join(sorted(plans))}" + (f"; kích thước: {size['nguon']}" if size else ""))
        if centers and not found_all:
            out.warnings.append(f"Móng {n}: không tìm thấy khung móng {size['length_mm']:.0f}×{size['width_mm']:.0f} quanh "
                                f"{centers.count(None)}/{c} ký hiệu: chưa có vị trí để kiểm tra hố đào chồng lấn, giằng qua móng.")
        out.foundations.append(f)
        dims_txt = " × ".join(f"{v:.0f}" if v is not None else "?" for v in (f.length_mm, f.width_mm, f.height_mm))
        out.warnings.append(f"Móng {n}: {c} khối, {dims_txt} mm"
                            + (f", lót {f.lean_thickness_mm:.0f} mm" if f.lean_thickness_mm else "")
                            + (" (móng băng: chờ kiểm tra tiết diện và phần giao)." if is_strip else
                               " (chờ đối chiếu các chi tiết cùng ký hiệu)." if size.get("conflict") else
                               f" (đọc từ chi tiết {size['nguon']}; móng coi là khối hộp, móng có bậc hoặc vát cần sửa)."
                               if size else " (không có chi tiết móng: nhập kích thước trong thông số công trình)."))
    located_marks = {element_of(n)[2] for n in spots}
    for mark, notes in sorted(strip_notes.items()):
        if mark in located_marks:
            continue
        if len(notes) != 1:
            out.warnings.append(f"{mark.upper()}: các ghi chú L/SL khác nhau, cần đối chiếu từng vị trí trên mặt bằng.")
            continue
        length, count = next(iter(notes))
        if not count:
            out.warnings.append(f"{mark.upper()}: đọc được L={length:g} mm, thiếu số lượng và vị trí trên mặt bằng.")
            continue
        name = f"BM-{mark[2:].upper()}"
        source = f"Chi tiết móng băng {name}, L={length:g} mm, SL={count}; chưa nối vị trí trên mặt bằng"
        out.foundations.append(FoundationItem(name=name, kind="bang", count=count, gross_length_mm=length, source=source))
        out.warnings.append(f"{source}. Chưa tính thể tích: thiếu tiết diện và phạm vi giao nhau.")
    return out
