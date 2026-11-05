"""Kiểm tra sai lệch một dự toán: khối lượng so với hệ thống, đơn giá so với giá tham chiếu, vật tư so với định mức,
lỗi số học (khối lượng × đơn giá ≠ thành tiền).

Đầu vào là bảng chuẩn (CSV hoặc sheet Excel, dòng đầu là tiêu đề), cùng cột với data/ground_truth/du_toan/*.csv:
- bảng công tác: ten_cong_tac, don_vi, khoi_luong; tùy chọn ma_dinh_muc, ma_cong_tac, cau_kien, don_gia, thanh_tien;
- bảng vật tư: ten_vat_tu, don_vi, khoi_luong; tùy chọn material_id, don_gia[_goc|_thuc_te], thanh_tien[_goc|_thuc_te].
Tiêu đề viết có dấu ("Tên công tác", "Khối lượng"...) cũng nhận. Dòng chưa có ma_cong_tac / material_id được gắn theo tên
và đánh dấu "tự gắn" để người dùng xem lại. Không quy đổi đơn vị khi chưa có căn cứ (chỉ kg↔tấn, m3↔m³).
"""
from __future__ import annotations

import io
import re
import statistics
import unicodedata

import pandas as pd

from ..catalog.pricing import normalize_unit, price_offers, select_best_offer
from ..drawing.encoding import normalize
from ..catalog.repository import Catalog
from .estimate_reader import read_estimate_book
from .materials import materials_for_works
from .models import WORKS, ProjectParams, WorkItem, worst_status
from .norms import unit_factor

THRESHOLD_PCT = 10.0

PRICE_PAIRS = [("don_gia", "thanh_tien"), ("don_gia_thuc_te", "thanh_tien_thuc_te"), ("don_gia_goc", "thanh_tien_goc")]
CONCRETE_CODES = {"MONG", "DAM", "COT", "CAU_THANG", "LANH_TO", "GIANG_TUONG", "SE_NO", "MAI", "SAN"}


def _norm(text) -> str:
    return re.sub(r"\s+", " ", normalize(str(text or ""))).strip()


def classify(name: str) -> tuple[str, str]:
    """Tên công tác -> (mã công tác phần thô, cấu kiện) theo data/rules/cong_tac_du_toan.csv (cùng quy tắc KD07);
    ("", "") = ngoài phần thô hoặc chưa nhận ra. Cốp pha, cốt thép: cấu kiện là mã bê tông khớp với phần tên còn lại
    ("ván khuôn xà dầm" -> "be tong xa dam" -> DAM), không giữ danh sách cấu kiện riêng trong mã."""
    from ..facts.estimate import OUT, load_rules
    text, rules = _norm(name), load_rules()
    hit = next(((pat, code) for _, pat, code in rules if pat.search(text)), None)
    if hit is None or hit[1] == OUT:
        return "", ""
    pat, code = hit
    if code not in ("COP_PHA", "COT_THEP"):
        return code, ""
    rest = "be tong " + pat.sub(" ", text)
    return code, next((c for _, p, c in rules if c in CONCRETE_CODES and p.search(rest)), "")


def _key(text) -> str:
    """'Tên công tác' -> 'ten_cong_tac' (bỏ dấu, chữ thường, khoảng trắng -> _)."""
    s = unicodedata.normalize("NFKD", str(text).replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(f) else f


def _pct(value: float | None, ref: float | None) -> float | None:
    return round((value - ref) / ref * 100, 1) if value is not None and ref else None


def _flag(pct: float | None, threshold: float) -> str:
    return "chưa so được" if pct is None else "lệch" if abs(pct) > threshold else "khớp"


def read_tables(files: list[tuple[str, bytes]]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """(bảng công tác, bảng vật tư, ghi chú) từ các file CSV/XLSX/XLS. Bảng chuẩn nhận theo cột tên (ten_cong_tac |
    ten_vat_tu); file Excel không có bảng chuẩn thì đọc như file dự toán gốc (estimate_reader)."""
    works, mats, notes = [], [], []
    for name, data in files:
        low = name.lower()
        try:
            if low.endswith(".csv"):
                frames = [pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")]
            elif low.endswith((".xlsx", ".xls")):
                frames = list(pd.read_excel(io.BytesIO(data), sheet_name=None).values())
            else:
                raise ValueError(f"{name}: chỉ nhận CSV, XLSX hoặc XLS")
        except ValueError:
            raise
        except Exception as exc:                      # file hỏng / sai định dạng: báo người dùng, không 500
            raise ValueError(f"{name}: không đọc được file ({exc})") from exc
        if low.endswith((".xlsx", ".xls")):
            # Excel: đọc như file dự toán gốc trước (bỏ mục nhân công/máy, gộp diễn giải); không nhận ra thì xem là bảng chuẩn
            w, m, n = read_estimate_book(name, data)
            if not (w.empty and m.empty):
                works += [w] if not w.empty else []
                mats += [m] if not m.empty else []
                notes += n
                continue
        for df in frames:
            df = df.rename(columns=_key)
            if "ten_cong_tac" in df:
                works.append(df)
            elif "ten_vat_tu" in df:
                mats.append(df)
    if not works and not mats:
        raise ValueError("Không nhận ra bảng công tác hay bảng vật tư nào: " + ("; ".join(notes) or
                         "cần cột 'ten_cong_tac' hoặc 'ten_vat_tu' (bảng chuẩn), hoặc file dự toán có cột tên, đơn vị, khối lượng"))
    return (pd.concat(works, ignore_index=True) if works else pd.DataFrame(),
            pd.concat(mats, ignore_index=True) if mats else pd.DataFrame(), notes)


def tag_works(df: pd.DataFrame) -> pd.DataFrame:
    """Gắn ma_cong_tac, cau_kien theo tên cho dòng còn trống; cột tu_gan đánh dấu dòng tự gắn."""
    df = df.copy()
    for col in ("ma_cong_tac", "cau_kien"):
        df[col] = df[col].fillna("").astype(str).str.strip() if col in df else ""
    blank = df.ma_cong_tac == ""
    guessed = df.loc[blank, "ten_cong_tac"].fillna("").astype(str).map(classify)
    df.loc[blank, "ma_cong_tac"] = [g[0] for g in guessed]
    df.loc[blank, "cau_kien"] = [g[1] for g in guessed]
    df["tu_gan"] = blank & (df.ma_cong_tac != "")
    return df


def tag_materials(df: pd.DataFrame, catalog: Catalog) -> pd.DataFrame:
    """Gắn material_id theo tên trùng tên gọi khác (material_aliases) hoặc tên danh mục; trùng nhiều mã thì để trống."""
    df = df.copy()
    df["material_id"] = df["material_id"].fillna("").astype(str).str.strip() if "material_id" in df else ""
    def key(s) -> str:                                 # "Gạch ống ( 8 x 8 x 19 )" -> "gachong8x8x19"
        return re.sub(r"[^a-z0-9]", "", normalize(str(s)).replace("×", "x"))
    names: dict[str, set[str]] = {}
    for alias, mid in list(zip(catalog.aliases.alias, catalog.aliases.material_id)) + list(
            zip(catalog.materials.name, catalog.materials.index if "material_id" not in catalog.materials else catalog.materials.material_id)):
        names.setdefault(key(alias), set()).add(str(mid))

    def lookup(n) -> set[str]:
        k = key(n)
        if k in names:
            return names[k]
        # tên dự toán dài hơn tên gọi khác ("Gạch chỉ thẻ 4x8x19" ⊃ "gạch chỉ thẻ"): lấy tên gọi dài nhất là tiền tố
        # chỉ khi phần dư là kích thước hoặc chữ không đổi loại ("Cát vàng hạt nhỏ" không được thành cát vàng hạt to)
        prefixes = sorted((a for a in names if len(a) >= 4 and k.startswith(a)
                           and re.fullmatch(r"[0-9x]*(mm|cm)?|vn|cacloai", k[len(a):])), key=len, reverse=True)
        return names[prefixes[0]] if prefixes else set()
    blank = df.material_id == ""
    found = df.loc[blank, "ten_vat_tu"].map(lookup)
    df.loc[blank, "material_id"] = [next(iter(s)) if len(s) == 1 else "" for s in found]
    df["tu_gan"] = blank & (df.material_id != "")
    return df


def check_quantities(est: pd.DataFrame, works: list[WorkItem], threshold: float = THRESHOLD_PCT) -> list[dict]:
    """Khối lượng dự toán so với công tác hệ thống, gom theo mã công tác (cốp pha, cốt thép thêm cấu kiện)."""
    est = est[(est.ma_cong_tac != "") & est.ma_cong_tac.isin(WORKS)]
    got: dict[tuple, list] = {}
    for w in works:
        elem = w.formwork_of if w.code == "COP_PHA" else w.steel_element if w.code == "COT_THEP" else ""
        got.setdefault((w.code, elem or ""), []).append(w)
    rows = []
    for (code, elem), g in est.groupby(["ma_cong_tac", "cau_kien"], sort=False):
        q = got.get((code, elem), [])
        known = [w.quantity for w in q if w.quantity is not None]
        sys_q = round(sum(known), 3) if known else None
        complete = bool(q) and len(known) == len(q)
        ref = round(sum(_num(v) or 0 for v in g.khoi_luong), 3)
        pct = _pct(sys_q, ref) if complete else None
        rows.append({"ma_cong_tac": code, "cau_kien": elem, "ten": WORKS[code][0], "don_vi": WORKS[code][1],
                     "du_toan": ref, "he_thong": sys_q,
                     "trang_thai_he_thong": "không có" if not q else "đủ" if complete else "thiếu",
                     "status": worst_status(*[w.status for w in q]), "lech_pct": pct, "ket_luan": _flag(pct, threshold),
                     "tu_gan": bool(g.tu_gan.any()) if "tu_gan" in g else False})
    return rows


def _unit_ok(est_unit: str, sys_unit: str) -> bool:
    return unit_factor(normalize_unit(est_unit), sys_unit) == 1.0


def estimate_works(est: pd.DataFrame) -> tuple[list[WorkItem], list[str]]:
    """Dòng dự toán thuộc phần thô -> WorkItem (source=estimate) để tính vật tư theo định mức."""
    out, notes = [], []
    for r in est[(est.ma_cong_tac != "") & est.ma_cong_tac.isin(WORKS)].to_dict("records"):
        code, elem, unit = r["ma_cong_tac"], r.get("cau_kien") or None, WORKS[r["ma_cong_tac"]][1]
        if not _unit_ok(str(r.get("don_vi", "")), unit):
            notes.append(f"{r['ten_cong_tac']}: đơn vị {r.get('don_vi')} khác {unit}, chưa quy đổi nên bỏ qua")
            continue
        out.append(WorkItem(code=code, name=str(r["ten_cong_tac"]), unit=unit, quantity=_num(r.get("khoi_luong")),
                            formwork_of=elem if code == "COP_PHA" else None,
                            steel_element=elem if code == "COT_THEP" else None, source="estimate"))
    return out, notes


def check_norms(est: pd.DataFrame, mats: pd.DataFrame, params: ProjectParams, catalog: Catalog,
                threshold: float = THRESHOLD_PCT) -> tuple[list[dict], list[str]]:
    """Vật tư tính từ khối lượng dự toán × định mức so với bảng vật tư của dự toán, theo material_id."""
    works, notes = estimate_works(est)
    bill = materials_for_works(works, params, catalog)
    rows = []
    for m in bill.materials:
        if not m.material_id:
            notes.append(f"{m.name}: chưa tính được vật tư theo định mức ({'; '.join(m.missing) or 'thiếu thông tin'})")
            continue
        given = mats[mats.material_id == m.material_id] if not mats.empty else mats
        qty = None
        for r in given.to_dict("records"):
            f = unit_factor(normalize_unit(str(r.get("don_vi", ""))), m.unit)
            if f is None or _num(r.get("khoi_luong")) is None:
                notes.append(f"{r['ten_vat_tu']}: đơn vị {r.get('don_vi')} khác {m.unit}, chưa quy đổi")
                continue
            qty = (qty or 0) + _num(r["khoi_luong"]) * f
        pct = _pct(qty, m.quantity) if m.complete else None
        rows.append({"material_id": m.material_id, "ten": m.name, "don_vi": m.unit,
                     "dinh_muc": None if m.quantity is None else round(m.quantity, 3),
                     "du_toan": None if qty is None else round(qty, 3), "lech_pct": pct, "ket_luan": _flag(pct, threshold),
                     "day_du": m.complete, "thieu": m.missing, "status": m.status})
    if rows:
        notes.append("Định mức chỉ tính phần thô; bảng vật tư dự toán có thể gồm cả công tác hoàn thiện nên thường lớn hơn.")
    return rows, notes


def check_prices(mats: pd.DataFrame, catalog: Catalog, threshold: float = THRESHOLD_PCT) -> list[dict]:
    """Đơn giá vật tư dự toán so với trung vị các giá hợp lệ trong danh mục (cùng đơn vị sau khi đổi kg↔tấn)."""
    if mats.empty:
        return []
    col = next((c for c in ("don_gia_thuc_te", "don_gia", "don_gia_goc") if c in mats), None)
    if col is None:
        return []
    ids = sorted({m for m in mats.material_id if m})
    offers = price_offers(catalog, ids)
    mat = catalog.materials.set_index("material_id") if "material_id" in catalog.materials else catalog.materials
    rows = []
    for r in mats[mats.material_id != ""].to_dict("records"):
        mid, price = r["material_id"], _num(r.get(col))
        unit = str(mat.at[mid, "unit"]) if mid in mat.index else ""
        f = unit_factor(normalize_unit(str(r.get("don_vi", ""))), unit) if unit else None
        _, checked = select_best_offer(offers.get(mid, []), unit, None, actual_only=False)
        ok = [o for o in checked if o.eligible]
        ref = statistics.median(o.price for o in ok) if ok else None
        mine = price / f if price is not None and f else None      # đơn giá dự toán quy về đơn vị danh mục
        pct = _pct(mine, ref)
        rows.append({"material_id": mid, "ten_vat_tu": r["ten_vat_tu"], "don_vi_du_toan": r.get("don_vi"),
                     "don_gia_du_toan": price, "don_vi": unit, "don_gia_quy_doi": None if mine is None else round(mine, 2),
                     "gia_tham_chieu": ref, "gia_min": min((o.price for o in ok), default=None),
                     "gia_max": max((o.price for o in ok), default=None), "so_nguon": len(ok),
                     "loai_nguon": sorted({f"{o.price_level}/{o.data_kind}" for o in ok}),
                     "lech_pct": pct, "ket_luan": "chưa có giá" if not ok else "khác đơn vị" if f is None else _flag(pct, threshold),
                     "tu_gan": bool(r.get("tu_gan"))})
    return rows


def check_arithmetic(tables: dict[str, pd.DataFrame]) -> list[dict]:
    """Dòng có khối lượng × đơn giá lệch thành tiền quá max(1 đồng, 0,1 %)."""
    rows = []
    for table, df in tables.items():
        name_col = "ten_cong_tac" if table == "cong_tac" else "ten_vat_tu"
        for price_col, total_col in PRICE_PAIRS:
            if df.empty or price_col not in df or total_col not in df:
                continue
            for i, r in enumerate(df.to_dict("records")):
                # đơn giá dự toán tính theo đơn vị gốc (100 m³...), nên nhân với khối lượng gốc khi có
                q = _num(r.get("khoi_luong_goc")) if _num(r.get("khoi_luong_goc")) is not None else _num(r.get("khoi_luong"))
                p, t = _num(r.get(price_col)), _num(r.get(total_col))
                if None in (q, p, t):
                    continue
                expect = q * p
                if abs(expect - t) > max(1.0, abs(expect) * 0.001):
                    rows.append({"bang": table, "dong": r.get("dong_excel") or i + 2, "ten": r.get(name_col), "khoi_luong": q, "don_gia": p,
                                 "cot": total_col, "thanh_tien": t, "tinh_lai": round(expect, 2), "chenh": round(t - expect, 2)})
    return rows


def check_estimate(files: list[tuple[str, bytes]], works: list[WorkItem] | None, params: ProjectParams,
                   catalog: Catalog, threshold: float = THRESHOLD_PCT) -> dict:
    """Chạy cả bốn kiểm tra; phần nào thiếu đầu vào thì trả danh sách trống kèm ghi chú."""
    est, mats, notes = read_tables(files)
    if not est.empty:
        est = tag_works(est)
    if not mats.empty:
        mats = tag_materials(mats, catalog)
    if est.empty:
        notes.append("Không có bảng công tác: bỏ qua kiểm khối lượng và định mức.")
    if mats.empty:
        notes.append("Không có bảng vật tư: bỏ qua kiểm đơn giá và so định mức.")
    if works is None:
        notes.append("Chưa có kết quả phần thô của hệ thống: bỏ qua so khối lượng.")
    quantities = check_quantities(est, works, threshold) if works is not None and not est.empty else []
    norms, norm_notes = check_norms(est, mats, params, catalog, threshold) if not est.empty else ([], [])
    result = {"nguong_pct": threshold, "khoi_luong": quantities, "dinh_muc": norms,
              "don_gia": check_prices(mats, catalog, threshold),
              "so_hoc": check_arithmetic({"cong_tac": est, "vat_tu": mats}), "ghi_chu": notes + norm_notes}
    result["tom_tat"] = {
        "khoi_luong_lech": sum(r["ket_luan"] == "lệch" for r in quantities),
        "dinh_muc_lech": sum(r["ket_luan"] == "lệch" for r in norms),
        "don_gia_lech": sum(r["ket_luan"] == "lệch" for r in result["don_gia"]),
        "so_hoc_loi": len(result["so_hoc"]),
        "cong_tac": len(est), "vat_tu": len(mats)}
    return result


SHEETS = [("khoi_luong", "Khối lượng"), ("dinh_muc", "Vật tư - định mức"), ("don_gia", "Đơn giá"), ("so_hoc", "Lỗi số học")]


def check_workbook(result: dict) -> bytes:
    """Kết quả kiểm tra ra Excel: một sheet mỗi loại kiểm tra và sheet ghi chú."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for key, title in SHEETS:
            df = pd.DataFrame(result[key])
            for c in df.columns:
                if df[c].map(lambda v: isinstance(v, list)).any():
                    df[c] = df[c].map(lambda v: "; ".join(map(str, v)) if isinstance(v, list) else v)
            (df if not df.empty else pd.DataFrame({"": ["Không có dòng"]})).to_excel(xw, sheet_name=title, index=False)
        pd.DataFrame({"Ghi chú": result["ghi_chu"] or ["—"]}).to_excel(xw, sheet_name="Ghi chú", index=False)
    return buf.getvalue()
