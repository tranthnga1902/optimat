"""Bảng thống kê cốt thép trên bản vẽ (S07-01…04): đọc dòng, tính kg, kiểm sai đơn vị và dòng trùng.

Quy ước bảng đã chuẩn hóa (data/rules/bang_thep.csv):
    tiêu đề    = chữ có "THỐNG KÊ THÉP" / "THỐNG KÊ CỐT THÉP"
    dòng tiêu đề cột = một hàng chữ phía dưới tiêu đề, khớp ít nhất cột đường kính và chiều dài cắt
    dòng dữ liệu     = các hàng chữ bên dưới, mỗi chữ thuộc cột có tọa độ x gần nhất; dừng ở dòng "TỔNG", tiêu đề
                       khác hoặc khoảng trống lớn hơn ROW_GAP_STOP lần khoảng cách dòng đầu
    kg dòng    = tổng số thanh × chiều dài cắt (m) × khối lượng 1 m (data/rules/thep_kg_m.csv, có nguồn)
    tổng thanh = cột tổng số thanh; không có thì số thanh 1 cấu kiện × số cấu kiện
Chiều dài cắt lấy nguyên từ bảng (đã gồm neo, nối, uốn, móc theo chi tiết thiết kế); hệ thống không tự cộng neo, nối.
Thiếu số nào thì dòng đó để trống kèm lý do (Quy ước B7). Thép tính ở đây luôn có basis = "bang_thong_ke",
tách khỏi thép ước theo hàm lượng (steel.py).
Bảng ACAD_TABLE chưa đọc được (dxf_reader bỏ qua): phải phá bảng (EXPLODE) thành TEXT/MTEXT.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field

from .. import config
from ..drawing.encoding import normalize
from .models import ROLE_WORK

RULE_FILE = config.DATA_DIR / "rules" / "bang_thep.csv"
UNIT_MASS_FILE = config.DATA_DIR / "rules" / "thep_kg_m.csv"
TITLE_RE = re.compile(r"\bthong ke (cot )?thep\b")
HEADER_ROWS_MAX = 4          # dòng tiêu đề cột nằm trong chừng này hàng chữ dưới tiêu đề bảng
ROW_GAP_STOP = 3.0
KG_TOL = 0.03                # lệch so với cột khối lượng của bảng quá 3% thì cảnh báo
LENGTH_MM = (100.0, 30000.0)  # chiều dài cắt hợp lý (mm); ngoài khoảng: nghi sai đơn vị


class RebarRow(BaseModel):
    table: str                                   # tiêu đề bảng
    row: int                                     # thứ tự dòng trong bảng (từ 1)
    element: str = ""                            # cấu kiện như ghi trong bảng (C1, DẦM D2, SÀN)
    element_code: Optional[str] = None           # mã công tác (COT, DAM...); trống: chưa có quy ước
    mark: str = ""
    shape: str = ""
    dia_mm: Optional[float] = None
    cut_length_mm: Optional[float] = None
    bars_per_member: Optional[float] = None
    members: Optional[float] = None
    total_bars: Optional[float] = None
    kg_per_m: Optional[float] = None
    kg_per_m_source: str = ""
    kg: Optional[float] = None                   # số hệ thống tính
    schedule_kg: Optional[float] = None          # số ghi trong bảng (chỉ đối chiếu)
    evidence: str = ""
    missing: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def formula(self) -> str:
        n = "?" if self.total_bars is None else f"{self.total_bars:g}"
        L = "?" if self.cut_length_mm is None else f"{self.cut_length_mm / 1000:g}"
        m = "?" if self.kg_per_m is None else f"{self.kg_per_m:g}"
        return f"{n} thanh × {L} m × {m} kg/m (Ø{self.dia_mm:g})" if self.dia_mm else f"{n} thanh × {L} m × {m} kg/m"


@lru_cache(maxsize=2)
def load_rules(path: str | None = None) -> tuple[tuple, tuple]:
    """(cột bảng: ((khóa, mẫu)...), tên cấu kiện: ((mã công tác, mẫu)...))."""
    rows = pd.read_csv(Path(path or RULE_FILE), dtype=str, keep_default_na=False).to_dict("records")
    cols = tuple((r["khoa"], re.compile(r["mau"])) for r in rows if r["nhom"] == "cot_bang")
    words = tuple((r["khoa"], re.compile(r["mau"])) for r in rows if r["nhom"] == "ten_cau_kien")
    return cols, words


@lru_cache(maxsize=2)
def unit_mass(path: str | None = None) -> dict[float, tuple[float, str]]:
    """{đường kính mm: (kg/m, nguồn)}."""
    df = pd.read_csv(Path(path or UNIT_MASS_FILE), dtype={"nguon": str})
    return {float(r.duong_kinh_mm): (float(r.kg_m), str(r.nguon)) for r in df.itertuples()}


def _num(text: str) -> Optional[float]:
    """Số trong ô: "3.200" (dấu chấm ngăn nghìn) = 3200, "1,58" = 1.58, "Ø16" = 16."""
    m = re.search(r"\d[\d.,]*", text or "")
    if not m:
        return None
    s = m.group(0).rstrip(".,")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def element_code(text: str) -> Optional[str]:
    """Cấu kiện ghi trong bảng -> mã công tác: ký hiệu (C1, D2, M1...) theo ky_hieu_cau_kien.csv, rồi tên (CỘT, SÀN)."""
    from .structural import element_of
    words = [w for w in re.split(r"[\s(),:;-]+", text) if w]
    for w in reversed(words):
        if (e := element_of(w)) and e[0] in ROLE_WORK:
            return ROLE_WORK[e[0]]
    plain = re.sub(r"\s+", " ", normalize(" ".join(w for w in words if not element_of(w)))).strip()
    for code, pat in load_rules()[1]:
        if pat.search(plain):
            return code
    return None


def _rows(texts, tol: float) -> list[list]:
    """Gom chữ thành hàng theo y (trên xuống)."""
    out: list[list] = []
    for t in sorted(texts, key=lambda t: -t.y):
        if out and abs(out[-1][0].y - t.y) <= tol:
            out[-1].append(t)
        else:
            out.append([t])
    return out


def _header(row) -> dict[str, tuple[float, str]]:
    cols = {}
    for t in row:
        key = normalize(t.text).strip()
        for name, pat in load_rules()[0]:
            if name not in cols and pat.search(key):
                cols[name] = (t.x, key)
                break
    return cols


def read_table(drawing, title) -> tuple[list[RebarRow], list[str]]:
    """Một bảng thống kê thép có tiêu đề title (TextItem)."""
    below = [t for t in drawing.texts if t.y < title.y and t is not title]
    h = title.height or median([t.height for t in below if t.height] or [0]) or 1.0
    tol = 0.6 * h
    rows = _rows(below, tol)
    header, hy = None, None
    for r in rows[:HEADER_ROWS_MAX * 3]:
        cols = _header(r)
        if "duong_kinh" in cols and "chieu_dai" in cols:
            header, hy = cols, r[0].y
            break
    name = title.text.strip()
    if header is None:
        return [], [f"Bảng '{name}': không thấy dòng tiêu đề cột (cần cột đường kính và chiều dài cắt), bỏ qua bảng."]
    xs = sorted(x for x, _ in header.values())
    gap = median([b - a for a, b in zip(xs, xs[1:])]) if len(xs) > 1 else 10 * h
    lo, hi = xs[0] - gap / 2, xs[-1] + gap / 2
    length_in_m = "(m)" in header["chieu_dai"][1]
    data = _rows([t for t in below if t.y < hy - tol and lo <= t.x <= hi], tol)
    masses = unit_mass()
    out, warnings, last_y, step, element = [], [], hy, None, ""
    for r in data:
        y = r[0].y
        if step is not None and last_y - y > ROW_GAP_STOP * step:
            break
        cells: dict[str, str] = {}
        for t in sorted(r, key=lambda t: t.x):
            k = min(header, key=lambda c: abs(header[c][0] - t.x))
            cells[k] = (cells.get(k, "") + " " + t.text).strip()
        joined = normalize(" ".join(cells.values()))
        if TITLE_RE.search(joined) or re.match(r"\s*tong\b", joined):
            break
        if _num(cells.get("duong_kinh", "")) is None and _num(cells.get("chieu_dai", "")) is None:
            break
        step = step or (last_y - y)
        last_y = y
        element = cells.get("cau_kien") or element
        row = RebarRow(table=name, row=len(out) + 1, element=element, element_code=element_code(element) if element else None,
                       mark=cells.get("so_hieu", ""), shape=cells.get("hinh_dang", ""),
                       dia_mm=_num(cells.get("duong_kinh", "")), schedule_kg=_num(cells.get("khoi_luong", "")),
                       bars_per_member=_num(cells.get("sl_1ck", "")), members=_num(cells.get("so_ck", "")),
                       total_bars=_num(cells.get("tong_thanh", "")),
                       evidence=f"{name}, dòng {len(out) + 1} (x={r[0].x:.0f}, y={y:.0f}, layer {r[0].layer}): "
                                + " | ".join(f"{k}={v}" for k, v in cells.items()))
        L = _num(cells.get("chieu_dai", ""))
        if L is not None and length_in_m:
            L *= 1000
        if L is None:
            row.missing.append("chiều dài cắt (gồm neo, nối, uốn, móc theo chi tiết)")
        elif not LENGTH_MM[0] <= L <= LENGTH_MM[1]:
            row.missing.append(f"chiều dài cắt {L:g} mm ngoài khoảng {LENGTH_MM[0]:g}–{LENGTH_MM[1]:g} mm: nghi sai đơn vị (m/mm)")
        else:
            row.cut_length_mm = L
        product = row.bars_per_member * row.members if None not in (row.bars_per_member, row.members) else None
        if row.total_bars is None:
            row.total_bars = product
        elif product is not None and abs(product - row.total_bars) > 0.5:
            row.notes.append(f"tổng số thanh {row.total_bars:g} ≠ {row.bars_per_member:g} × {row.members:g} = {product:g}: "
                             "kiểm tra đếm trùng; đang dùng cột tổng")
        if row.total_bars is None:
            row.missing.append("số thanh")
        if row.dia_mm is None:
            row.missing.append("đường kính")
        elif row.dia_mm not in masses:
            row.missing.append(f"khối lượng 1 m của Ø{row.dia_mm:g} (chưa có trong thep_kg_m.csv)")
        else:
            row.kg_per_m, row.kg_per_m_source = masses[row.dia_mm]
        if row.element_code is None:
            row.notes.append(f"cấu kiện '{element or '(trống)'}' chưa có quy ước: Not supported, không cộng vào cốt thép")
        if not row.missing:
            row.kg = round(row.total_bars * row.cut_length_mm / 1000 * row.kg_per_m, 2)
            if row.schedule_kg:
                ratio = row.kg / row.schedule_kg
                if abs(ratio - 1) > KG_TOL:
                    unit = " (lệch khoảng 1000 lần: bảng ghi tấn hay chiều dài theo m?)" if 500 < ratio < 2000 or 5e-4 < ratio < 2e-3 else ""
                    row.notes.append(f"kg tính {row.kg:g} ≠ kg ghi trong bảng {row.schedule_kg:g}{unit}: cần review")
        for n in row.notes:
            warnings.append(f"Bảng '{name}' dòng {row.row} ({element} {row.mark}): {n}.")
        out.append(row)
    if not out:
        warnings.append(f"Bảng '{name}': có dòng tiêu đề cột nhưng không đọc được dòng thép nào.")
    return out, warnings


def read_rebar_schedules(drawing) -> tuple[list[RebarRow], list[str]]:
    """Mọi bảng thống kê thép trên bản vẽ. Dòng trùng hệt nhau (bảng vẽ lặp ở hai chỗ) chỉ giữ dòng đầu."""
    rows, warnings, seen = [], [], {}
    for title in [t for t in drawing.texts if TITLE_RE.search(normalize(t.text))]:
        r, w = read_table(drawing, title)
        warnings += w
        for row in r:
            key = (normalize(row.element), normalize(row.mark), row.dia_mm, row.cut_length_mm, row.total_bars)
            if key in seen and row.mark:
                warnings.append(f"Bảng '{row.table}' dòng {row.row} trùng hệt {seen[key]} ({row.element} {row.mark}): "
                                "không cộng lần hai, kiểm tra bảng lặp.")
                continue
            seen[key] = f"bảng '{row.table}' dòng {row.row}"
            rows.append(row)
    if rows:
        warnings.append("Cốt thép theo bảng thống kê: chiều dài cắt lấy nguyên từ bảng (đã gồm neo, nối, uốn, móc theo "
                        "thiết kế), hệ thống không tự cộng neo, nối.")
    return rows, warnings
