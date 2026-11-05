"""Đọc thẳng file dự toán (.xls/.xlsx) của phần mềm dự toán ra bảng công tác và bảng vật tư chuẩn của estimate_check.

Không cố định vị trí cột: mỗi sheet tìm dòng tiêu đề (một hoặc hai dòng) có cột tên + đơn vị + khối lượng, nhận cột theo
từ khóa ("Tên công tác", "Diễn giải công việc", "Đơn vị", "Khối lượng"/"Tổng cộng", "Đơn giá", "Thành tiền"...). Dòng
công tác/vật tư là dòng có số thứ tự; dòng không số thứ tự ngay dưới công tác là diễn giải. Nhiều sheet cùng loại
(bảng khối lượng chi tiết và bảng dự toán) thì chọn sheet có nhiều dòng có giá nhất. Chữ VNI/TCVN3 đổi sang Unicode.
"""
from __future__ import annotations

import io
import re

import pandas as pd

from ..drawing.encoding import _UNICODE_VI, normalize, to_unicode, vni_to_unicode

# Dấu hiệu chắc chắn của chữ VNI trong một từ (Unicode tiếng Việt không có các cặp này)
_VNI_STRONG = re.compile(r"[AEIOUYaeiouy][ùøûõïöäëåæÙØÛÕÏÖÄËÅÆ]|[AEOaeo][Ââ]|[Aa][ÊêÉéÈèËë]|[EAea][ÁáÀàÃã]|[Ññ]")
UNITS = {"100m2": ("m²", 100), "100m3": ("m³", 100), "100m": ("m", 100), "m3": ("m³", 1), "m2": ("m²", 1)}
_SKIP_SECTION = re.compile(r"nhan cong|may thi cong|thiet bi")


def text(v) -> str:
    """Ô Excel -> chữ Unicode. Ô có dấu hiệu VNI: đổi các từ chưa phải Unicode tiếng Việt (ô trộn hai bảng mã)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    out, enc = to_unicode(s)
    if enc != "unicode":
        return out.strip()
    if not _VNI_STRONG.search(s):
        return s
    return re.sub(r"[^\s,;:()/]+", lambda m: m[0] if _UNICODE_VI.search(m[0]) else vni_to_unicode(m[0]), s)


def _num(v) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(f) else f


def _labels(df: pd.DataFrame, i: int) -> list[tuple[str, str]]:
    """Nhãn cột từ dòng i và i+1 (tiêu đề gộp ô: dòng trên trống thì lấy nhãn ô trái gần nhất), cả bản ép VNI."""
    top = [text(v) for v in df.iloc[i]]
    sub = [text(v) for v in df.iloc[i + 1]] if i + 1 < len(df) else [""] * len(top)
    raw_top = ["" if pd.isna(v) else str(v) for v in df.iloc[i]]
    raw_sub = ["" if pd.isna(v) else str(v) for v in df.iloc[i + 1]] if i + 1 < len(df) else [""] * len(top)
    out, last, last_raw = [], "", ""
    for t, s, rt, rs in zip(top, sub, raw_top, raw_sub):
        if t:
            last, last_raw = t, rt
        elif not s:
            last = last_raw = ""
        a = normalize(f"{t or last} {s}")
        b = normalize(f"{vni_to_unicode(rt or last_raw)} {vni_to_unicode(rs)}")
        out.append((" ".join(re.sub(r"[^a-z0-9 ]", " ", a).split()), " ".join(re.sub(r"[^a-z0-9 ]", " ", b).split())))
    return out


def _find(labels, pattern: str, exclude: str | None = None) -> list[int]:
    p, x = re.compile(pattern), re.compile(exclude) if exclude else None
    return [j for j, ab in enumerate(labels) if any(p.search(s) and not (x and x.search(s)) for s in ab)]


def _best_numeric(df, rows, cols) -> int | None:
    counts = {c: sum(_num(df.iat[r, c]) is not None for r in rows) for c in cols}
    best = max(counts, key=lambda c: (counts[c], -c), default=None)
    return best if best is not None and counts[best] else None


def _table(df: pd.DataFrame, sheet: str) -> tuple[str, pd.DataFrame, str] | None:
    """(loại 'cong_tac' | 'vat_tu', bảng chuẩn, mô tả) của một sheet; None khi không nhận ra bảng."""
    for i in range(min(20, len(df) - 1)):
        lab = _labels(df, i)
        names = _find(lab, r"\bten\b|dien giai cong viec|noi dung cong viec", r"loai may|nhan cong$|thiet bi")
        units = _find(lab, r"\bdon v[io]\b|\bdvt\b")
        stts = _find(lab, r"^(stt|so tt|tt)\b")
        if not names or not units:
            continue
        name = names[0]
        kind = "vat_tu" if any(re.search(r"vat tu|vat lieu", s) and not re.search(r"cong tac|cong viec", s)
                               for s in lab[name]) else "cong_tac"
        stt = stts[0] if stts else None
        if stt is None:
            continue
        body = range(i + 2, len(df))
        items = [r for r in body if _num(df.iat[r, stt]) is not None and text(df.iat[r, name])]
        qty = _best_numeric(df, items, _find(lab, r"khoi luong|tong cong|tong so|^so luong",
                                             r"hao phi|chi tiet|dinh muc|\bk l\b|tung phan"))
        if qty is None:
            continue
        codes = [c for c in _find(lab, r"ma hieu|ma so|dinh muc|ma vat tu") if c not in (name, stt)]
        prices = [c for c in _find(lab, r"don gia|\bd gia\b|gia goc|gia thuc te|gia t b|gia thang", r"cuoc|ca may|thanh tien|chenh lech")
                  if c != qty and any(_num(df.iat[r, c]) is not None for r in items)]
        totals = [c for c in _find(lab, r"thanh tien|th tien", r"cuoc") if any(_num(df.iat[r, c]) is not None for r in items)]
        rows, skip, last = [], False, None
        for r in body:
            n, s = text(df.iat[r, name]), df.iat[r, stt]
            if _num(s) is None:
                if n and kind == "vat_tu":
                    skip = bool(_SKIP_SECTION.search(normalize(n))) or (bool(text(s)) and skip)
                elif n and last is not None and kind == "cong_tac":
                    last["dien_giai"].append(n)
                if text(s):                       # dòng mục (I.), II.)...) đổi phần
                    skip = bool(_SKIP_SECTION.search(normalize(n)))
                    last = None
                continue
            q = _num(df.iat[r, qty])
            if not n or q is None or skip:
                last = None
                continue
            unit_raw = text(df.iat[r, units[0]])
            unit, k = UNITS.get(unit_raw.lower().replace(" ", ""), (unit_raw, 1))
            row = {"stt": int(_num(s)), "ma": text(df.iat[r, codes[0]]) if codes else "", "ten": n.lstrip("+ ").strip(),
                   "don_vi_goc": unit_raw, "khoi_luong_goc": q, "don_vi": unit, "khoi_luong": round(q * k, 6),
                   "sheet": sheet, "dong_excel": r + 1, "dien_giai": []}
            _prices(row, df, r, lab, kind, prices, totals)
            rows.append(row)
            last = row
        if not rows:
            continue
        out = pd.DataFrame(rows)
        out["dien_giai"] = out.dien_giai.map(" | ".join)
        out = out.rename(columns={"ma": "ma_dinh_muc" if kind == "cong_tac" else "ma_vat_tu_du_toan",
                                  "ten": "ten_cong_tac" if kind == "cong_tac" else "ten_vat_tu"})
        return kind, out, f"sheet '{sheet}', tiêu đề dòng {i + 1}: {len(out)} dòng {'công tác' if kind == 'cong_tac' else 'vật tư'}"
    return None


def _prices(row: dict, df, r: int, lab, kind: str, prices: list[int], totals: list[int]) -> None:
    """Đơn giá, thành tiền của dòng. Công tác: cộng các phần (vật liệu, nhân công, máy). Vật tư: giá gốc và giá áp dụng."""
    def v(c):
        return _num(df.iat[r, c])
    if kind == "cong_tac":
        ps, ts = [v(c) for c in prices], [v(c) for c in totals]
        if any(p is not None for p in ps):
            row["don_gia"] = sum(p or 0 for p in ps)
        if any(t is not None for t in ts):
            row["thanh_tien"] = sum(t or 0 for t in ts)
        return
    def total_for(c, suffix):
        same = [t for t in totals if suffix and any(suffix in s for s in lab[t])]
        if same:
            return same[0]
        nxt = [t for t in totals if t > c and not any(c < p < t for p in prices)]
        return nxt[0] if nxt else None
    goc = [c for c in prices if any("goc" in s for s in lab[c])]
    applied = [c for c in prices if c not in goc]
    for key, cols, suffix in (("goc", goc, "goc"), ("", applied[-1:], "thuc te")):
        if not cols:
            continue
        c = cols[0]
        tag = "_goc" if key else ""
        row[f"don_gia{tag}"] = v(c)
        t = total_for(c, suffix)
        if t is not None:
            row[f"thanh_tien{tag}"] = v(t)


def read_estimate_book(name: str, data: bytes) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """(bảng công tác, bảng vật tư, ghi chú) từ file dự toán gốc; mỗi loại lấy một sheet tốt nhất."""
    book = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, dtype=object)
    found: dict[str, list[tuple[int, pd.DataFrame, str]]] = {"cong_tac": [], "vat_tu": []}
    for sheet, df in book.items():
        if df.shape[0] < 3 or df.shape[1] < 3:
            continue
        got = _table(df.reset_index(drop=True), text(sheet))
        if got:
            kind, table, note = got
            priced = sum(table[c].notna().sum() for c in ("don_gia", "don_gia_goc") if c in table)
            found[kind].append(((priced > 0, len(table)), table, note))   # bảng có giá (dự toán) trước bảng đo chi tiết
    notes, picked = [], {}
    for kind, cands in found.items():
        if cands:
            _, table, note = max(cands, key=lambda x: x[0])
            picked[kind] = table
            notes.append(f"{name}: dùng {note}" + (f" (bỏ {len(cands) - 1} sheet cùng loại)" if len(cands) > 1 else ""))
    if not picked:
        notes.append(f"{name}: không nhận ra bảng khối lượng hay bảng vật tư (cần cột tên, đơn vị, khối lượng và số thứ tự)")
    return picked.get("cong_tac", pd.DataFrame()), picked.get("vat_tu", pd.DataFrame()), notes
