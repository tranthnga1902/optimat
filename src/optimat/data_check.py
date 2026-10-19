"""Kiểm soát dữ liệu: kiểm tra danh mục vật liệu, phương án tường, tên gọi khác, bộ quy tắc bóc tách, nhà cung cấp, giá
và đáp án đo tay trước khi dùng cho bóc tách, tối ưu hay báo cáo.

    python scripts/check_data.py            # in báo cáo, ghi reports/data_check.md; có lỗi thì thoát mã 1
    GET /api/data/check                     # cùng nội dung cho trang Quản trị

Mức độ:
    error   : dữ liệu sai cấu trúc hoặc tham chiếu hỏng; phải sửa trước khi chạy (bóc tách ra mã không tra được giá...)
    warning : còn trống số liệu, dữ liệu mẫu hoặc giá cũ; hệ thống vẫn chạy nhưng kết quả bị giới hạn
    info    : thống kê
Hàm chỉ đọc, không sửa dữ liệu và không điền số thay người dùng.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date

import pandas as pd

from . import config
from .catalog.repository import Catalog
from .db.session import get_database_url, get_engine
from .drawing.encoding import normalize
from .drawing.material_rules import load_rules

PRICE_MAX_AGE_DAYS = 90          # giá cũ hơn số ngày này bị cảnh báo
DATA_KINDS = ("ACTUAL", "SAMPLE", "SYNTHETIC")


@dataclass
class Finding:
    level: str          # error | warning | info
    area: str           # vat_lieu | phuong_an_tuong | ten_goi_khac | quy_tac | dinh_muc_phan_tho | nguon_cung | gia | dap_an
    item: str
    message: str


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip())


def _check_materials(cat: Catalog, out: list[Finding]) -> None:
    m = cat.materials
    for mid, n in Counter(m.material_id).items():
        if n > 1:
            out.append(Finding("error", "vat_lieu", mid, f"Mã vật liệu lặp {n} lần."))
    walls = m[m.get("family").notna()] if "family" in m else m.iloc[0:0]
    for r in walls.itertuples():
        if r.family not in cat.wall_families():
            out.append(Finding("error", "vat_lieu", r.material_id, f"Họ vật liệu {r.family} không có trong danh sách họ tường."))
        miss = [label for col, label in (("unit_weight_kg", "khối lượng / đơn vị"), ("lambda_w_mk", "hệ số dẫn nhiệt λ"),
                                         ("waste_pct", "hao hụt thi công (%)")) if _blank(getattr(r, col, None))]
        if miss:
            out.append(Finding("warning", "vat_lieu", r.material_id, "Vật liệu tường còn trống: " + ", ".join(miss) + "."))


def _check_wall_systems(cat: Catalog, out: list[Finding]) -> dict:
    ids = set(cat.materials.material_id)
    ws = cat.wall_systems
    for r in ws.itertuples():
        if r.material_id not in ids:
            out.append(Finding("error", "phuong_an_tuong", r.wall_system_id, f"Mã vật liệu {r.material_id} không có trong danh mục."))
        mortar = getattr(r, "mortar_material_id", None)
        if not _blank(mortar) and mortar not in ids:
            out.append(Finding("error", "phuong_an_tuong", r.wall_system_id, f"Mã vữa {mortar} không có trong danh mục."))
    view = cat.wall_view()
    for r in view.itertuples():
        if _blank(r.detect_class):
            out.append(Finding("warning", "phuong_an_tuong", r.wall_system_id,
                               "Chưa có lớp nhận diện bản vẽ (chiều dày): bóc tách không quy về được phương án này."))
        elif r.detect_class not in config.WALL_THICKNESS_CLASSES:
            out.append(Finding("error", "phuong_an_tuong", r.wall_system_id, f"Lớp nhận diện {r.detect_class} không hợp lệ."))
        elif not r.ready:
            out.append(Finding("warning", "phuong_an_tuong", r.wall_system_id,
                               "Chưa đủ số liệu để tối ưu, thiếu: " + ", ".join(r.missing) + "."))
        if bool(r.ready) and r.data_kind == "SAMPLE":
            out.append(Finding("warning", "phuong_an_tuong", r.wall_system_id, "Đang dùng SỐ MẪU, không dùng để báo cáo."))
    ready = view[view.ready.astype(bool)] if len(view) else view
    by_class = {}
    for cls in config.WALL_THICKNESS_CLASSES:
        n_all = int((view.detect_class == cls).sum()) if len(view) else 0
        n_ready = int((ready.detect_class == cls).sum()) if len(ready) else 0
        by_class[cls] = {"phuong_an": n_all, "du_so_lieu": n_ready}
        if n_all == 0:
            out.append(Finding("warning", "phuong_an_tuong", f"lớp {cls}",
                               f"Chưa có phương án tường nào cho lớp {cls}: tường {cls} nhận diện được nhưng không gán được vật liệu."))
        elif n_ready == 0:
            out.append(Finding("warning", "phuong_an_tuong", f"lớp {cls}", f"Lớp {cls} chưa có phương án nào đủ số liệu để tối ưu."))
    return by_class


def _check_aliases(cat: Catalog, out: list[Finding]) -> None:
    ids = set(cat.materials.material_id)
    fam = cat.materials.set_index("material_id").get("family", pd.Series(dtype=object))
    owners: dict[str, set[str]] = defaultdict(set)
    for a in cat.aliases.itertuples():
        if a.material_id not in ids:
            out.append(Finding("error", "ten_goi_khac", str(a.alias), f"Trỏ tới mã {a.material_id} không có trong danh mục."))
            continue
        if fam.get(a.material_id) in cat.wall_families():
            owners[normalize(str(a.alias)).strip()].add(a.material_id)
    for alias, mats in sorted(owners.items()):
        if len(mats) > 1:
            out.append(Finding("warning", "ten_goi_khac", alias,
                               f"Một tên gọi trỏ tới {len(mats)} vật liệu ({', '.join(sorted(mats))}): ghi chú bản vẽ khớp tên này sẽ mơ hồ."))


def _check_rules(cat: Catalog, out: list[Finding]) -> None:
    rules = load_rules()
    known = set(cat.wall_families()) | set(cat.materials.material_id)
    for rid, n in Counter(r.rule_id for r in rules).items():
        if n > 1:
            out.append(Finding("error", "quy_tac", rid, f"Mã quy tắc lặp {n} lần."))
    for r in rules:
        bad = [t for t in r.target if t not in known]
        if bad:
            out.append(Finding("error", "quy_tac", r.rule_id, f"Họ hoặc mã vật liệu không có trong danh mục: {', '.join(bad)}."))
        if r.signal == "block":
            try:
                re.compile(r.pattern)
            except re.error as exc:
                out.append(Finding("error", "quy_tac", r.rule_id, f"Biểu thức chính quy lỗi: {exc}."))


def _check_rough_norms(cat: Catalog, out: list[Finding]) -> dict:
    """data/rules/dinh_muc_phan_tho.csv: mã công tác, mã vật liệu, đơn vị đổi được, số có kèm số hiệu bảng TT 38."""
    from .rough.norms import MORTAR, load_norms, unit_factor
    try:
        norms = load_norms()
    except (ValueError, KeyError) as exc:
        out.append(Finding("error", "dinh_muc_phan_tho", "dinh_muc_phan_tho.csv", str(exc)))
        return {"dong": 0, "con_trong": 0}
    units = cat.materials.set_index("material_id").unit if not cat.materials.empty else pd.Series(dtype=object)
    for n in norms:
        item = f"{n.work_code} {n.variant} {n.material_id or n.material_name}".replace("  ", " ")
        if n.material_id not in (None, MORTAR) and n.material_id not in units.index:
            out.append(Finding("error", "dinh_muc_phan_tho", item, f"Mã vật liệu {n.material_id} không có trong danh mục."))
        elif n.material_id not in (None, MORTAR) and unit_factor(n.numerator_unit, str(units[n.material_id])) is None:
            out.append(Finding("warning", "dinh_muc_phan_tho", item,
                               f"Không đổi được {n.qty_unit} sang đơn vị {units[n.material_id]} của vật liệu."))
        if n.qty is not None and not n.norm_code:
            out.append(Finding("error", "dinh_muc_phan_tho", item, "Có số định mức mà chưa ghi số hiệu bảng TT 38/2026 (Quy ước B7)."))
    blank = [n for n in norms if n.qty is None]
    if blank:
        out.append(Finding("warning", "dinh_muc_phan_tho", "dinh_muc_phan_tho.csv",
                           f"{len(blank)}/{len(norms)} dòng định mức còn trống, chờ tra TT 38/2026: công tác dùng các dòng này "
                           "chưa ra vật liệu mua về."))
    return {"dong": len(norms), "con_trong": len(blank)}


def _check_material_notes(cat: Catalog, out: list[Finding]) -> None:
    """data/rules/material_notes.csv (bảng material_notes): mã vật liệu phải có trong danh mục, mã quy tắc không lặp."""
    from collections import Counter

    from .drawing.material_notes import load_note_rules
    try:
        rules = load_note_rules()
    except (ValueError, KeyError) as exc:
        out.append(Finding("error", "quy_tac", "material_notes.csv", str(exc)))
        return
    known = set(cat.materials.material_id)
    for rid, n in Counter(r.rule_id for r in rules).items():
        if n > 1:
            out.append(Finding("error", "quy_tac", rid, f"Mã quy tắc ghi chú lặp {n} lần."))
    for r in rules:
        if r.material_id not in known:
            out.append(Finding("error", "quy_tac", r.rule_id, f"Ghi chú \"{r.pattern}\" trỏ tới mã {r.material_id} không có trong danh mục."))


def _check_supply(cat: Catalog, out: list[Finding], today: date) -> dict:
    sm, sup = cat.supplier_materials, cat.suppliers
    sup_ids, mat_ids = set(sup.supplier_id), set(cat.materials.material_id)
    for r in sm.itertuples():
        key = f"{r.supplier_id} / {r.material_id}"
        if r.supplier_id not in sup_ids:
            out.append(Finding("error", "nguon_cung", key, "Nhà cung cấp không có trong bảng suppliers."))
        if r.material_id not in mat_ids:
            out.append(Finding("error", "nguon_cung", key, "Mã vật liệu không có trong danh mục (mã cũ MAT_...?)."))
        price = getattr(r, "base_price", None)
        if not _blank(price):
            if _blank(getattr(r, "price_level", None)) or _blank(getattr(r, "price_date", None)):
                out.append(Finding("error", "nguon_cung", key, "Có giá nhưng thiếu mức giá hoặc ngày của giá."))
            else:
                age = (today - pd.to_datetime(r.price_date).date()).days
                if age > PRICE_MAX_AGE_DAYS:
                    out.append(Finding("warning", "gia", key, f"Giá đã {age} ngày (quá {PRICE_MAX_AGE_DAYS} ngày)."))
    for r in sup.itertuples():
        if all(_blank(getattr(r, c, None)) for c in ("maps_url", "website", "facebook", "price_page_url")):
            out.append(Finding("warning", "nguon_cung", r.supplier_id, "Chưa có liên kết (Google Maps, website): kết quả tối ưu không dẫn link được."))
    fam = cat.materials.set_index("material_id").get("family", pd.Series(dtype=object))
    wall_mats = sorted(m for m in mat_ids if fam.get(m) in cat.wall_families())
    priced = set(sm[sm.base_price.notna()].material_id) if "base_price" in sm else set()
    no_price = [m for m in wall_mats if m not in priced]
    if no_price:
        out.append(Finding("warning", "gia", f"{len(no_price)} vật liệu tường",
                           "Chưa có giá đại lý nào: " + ", ".join(no_price) + "."))
    kinds = Counter(sm.get("data_kind", pd.Series(dtype=object)).fillna("?"))
    if kinds.get("SAMPLE") or kinds.get("SYNTHETIC"):
        out.append(Finding("warning", "nguon_cung", "supplier_materials",
                           f"Có {kinds.get('SAMPLE', 0) + kinds.get('SYNTHETIC', 0)} dòng giá MẪU hoặc MÔ PHỎNG: không dùng để báo cáo."))
    return {"nha_cung_cap": len(sup), "dong_gia_dai_ly": len(sm), "co_gia": int(sm.base_price.notna().sum()) if "base_price" in sm else 0,
            "theo_loai": dict(kinds), "vat_lieu_tuong_co_gia": len(wall_mats) - len(no_price), "vat_lieu_tuong": len(wall_mats)}


def _price_records_summary(out: list[Finding]) -> dict:
    """Lịch sử giá: bảng price_records khi có PostgreSQL, không thì file mô phỏng đi kèm."""
    if get_database_url():
        with get_engine().connect() as conn:
            df = pd.read_sql_query("SELECT data_kind, price_level, count(*) AS n, max(date) AS last FROM price_records "
                                   "GROUP BY 1, 2 ORDER BY 1, 2", conn)
        source = "price_records"
    else:
        path = config.DATA_DIR / "sample" / "prices_sample.csv"
        raw = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["data_kind", "date"])
        raw["price_level"] = raw.get("price_level", "DEALER")
        df = raw.groupby(["data_kind", "price_level"]).agg(n=("date", "size"), last=("date", "max")).reset_index()
        source = "data/sample/prices_sample.csv"
    actual = int(df[df.data_kind == "ACTUAL"].n.sum()) if len(df) else 0
    if actual == 0:
        out.append(Finding("warning", "gia", source, "Chưa có dòng giá THẬT (ACTUAL): mô hình giá chỉ học trên dữ liệu mô phỏng, "
                                                     "chưa dùng được để báo cáo độ chính xác."))
    return {"nguon": source, "dong": int(df.n.sum()) if len(df) else 0, "that": actual,
            "chi_tiet": [{"loai": r.data_kind, "muc_gia": r.price_level, "dong": int(r.n), "moi_nhat": str(r.last)[:10]}
                         for r in df.itertuples()]}


def _check_ground_truth(cat: Catalog, out: list[Finding]) -> dict:
    gt = config.DATA_DIR / "ground_truth"
    index = pd.read_csv(gt / "index.csv") if (gt / "index.csv").exists() else pd.DataFrame(columns=["drawing_file", "split"])
    walls = pd.read_csv(gt / "walls.csv", dtype={"wall_type": str}) if (gt / "walls.csv").exists() else pd.DataFrame()
    splits = Counter(index.get("split", pd.Series(dtype=object)))
    if not splits.get("test"):
        out.append(Finding("warning", "dap_an", "data/ground_truth", "Chưa có bản vẽ nhóm test có đáp án đo tay: chưa có số sai số để báo cáo."))
    ids = set(cat.materials.material_id)
    for r in walls.itertuples():
        if not _blank(getattr(r, "material_id", None)) and r.material_id not in ids:
            out.append(Finding("error", "dap_an", f"{r.drawing_file} / {r.wall_type}", f"Vật liệu {r.material_id} không có trong danh mục."))
        if str(r.drawing_file).startswith("data/sample/"):
            out.append(Finding("info", "dap_an", r.drawing_file, "Bản vẽ mẫu tự tạo, chỉ để kiểm thử mã."))
    return {"ban_ve": len(index), "theo_nhom": dict(splits), "dong_dap_an": len(walls)}


def run_checks(catalog: Catalog | None = None, today: date | None = None) -> dict:
    cat = catalog or Catalog.load()
    today = today or date.today()
    out: list[Finding] = []
    _check_materials(cat, out)
    classes = _check_wall_systems(cat, out)
    _check_aliases(cat, out)
    _check_rules(cat, out)
    rough = _check_rough_norms(cat, out)
    _check_material_notes(cat, out)
    supply = _check_supply(cat, out, today)
    prices = _price_records_summary(out)
    truth = _check_ground_truth(cat, out)
    fam = cat.materials.get("family", pd.Series(dtype=object))
    view = cat.wall_view()
    summary = {
        "nguon_du_lieu": "postgresql" if get_database_url() else "csv",
        "ngay_kiem_tra": today.isoformat(),
        "vat_lieu": len(cat.materials), "vat_lieu_tuong": int(fam.isin(list(cat.wall_families())).sum()),
        "phuong_an_tuong": len(view), "phuong_an_du_so_lieu": int(view.ready.sum()) if len(view) else 0,
        "theo_lop_tuong": classes, "ten_goi_khac": len(cat.aliases), "quy_tac": len(load_rules()),
        "nguon_cung": supply, "lich_su_gia": prices, "dap_an_do_tay": truth, "dinh_muc_phan_tho": rough,
    }
    levels = Counter(f.level for f in out)
    return {"ok": levels.get("error", 0) == 0, "counts": {k: levels.get(k, 0) for k in ("error", "warning", "info")},
            "summary": summary, "findings": [asdict(f) for f in sorted(out, key=lambda f: (("error", "warning", "info").index(f.level), f.area, f.item))]}


def to_markdown(report: dict) -> str:
    s, c = report["summary"], report["counts"]
    lines = [f"# Kiểm soát dữ liệu OptiMat AI ({s['ngay_kiem_tra']}, nguồn {s['nguon_du_lieu']})", "",
             f"Kết quả: **{'ĐẠT' if report['ok'] else 'CÓ LỖI'}** · {c['error']} lỗi · {c['warning']} cảnh báo · {c['info']} ghi chú", "",
             "| Hạng mục | Số liệu |", "|---|---|",
             f"| Vật liệu (vật liệu tường) | {s['vat_lieu']} ({s['vat_lieu_tuong']}) |",
             f"| Phương án tường (đủ số liệu tối ưu) | {s['phuong_an_tuong']} ({s['phuong_an_du_so_lieu']}) |",
             "| Theo lớp tường: phương án / đủ số liệu | " + ", ".join(f"{k}: {v['phuong_an']}/{v['du_so_lieu']}" for k, v in s["theo_lop_tuong"].items()) + " |",
             f"| Tên gọi khác, quy tắc bóc tách | {s['ten_goi_khac']}, {s['quy_tac']} |",
             f"| Nhà cung cấp, dòng giá đại lý (có giá) | {s['nguon_cung']['nha_cung_cap']}, {s['nguon_cung']['dong_gia_dai_ly']} ({s['nguon_cung']['co_gia']}) |",
             f"| Vật liệu tường đã có giá | {s['nguon_cung']['vat_lieu_tuong_co_gia']}/{s['nguon_cung']['vat_lieu_tuong']} |",
             f"| Lịch sử giá ({s['lich_su_gia']['nguon']}): tổng / thật | {s['lich_su_gia']['dong']} / {s['lich_su_gia']['that']} |",
             f"| Đáp án đo tay: bản vẽ, theo nhóm | {s['dap_an_do_tay']['ban_ve']}, {s['dap_an_do_tay']['theo_nhom']} |", ""]
    names = {"error": "Lỗi (phải sửa)", "warning": "Cảnh báo", "info": "Ghi chú"}
    for level in ("error", "warning", "info"):
        items = [f for f in report["findings"] if f["level"] == level]
        if items:
            lines += [f"## {names[level]} ({len(items)})", "", "| Khu vực | Mục | Nội dung |", "|---|---|---|"]
            lines += [f"| {f['area']} | {f['item']} | {f['message'].replace('|', '/')} |" for f in items] + [""]
    return "\n".join(lines)
