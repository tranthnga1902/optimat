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

import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

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
    area: str           # vat_lieu | phuong_an_tuong | ten_goi_khac | quy_tac | dinh_muc_phan_tho | nguon_cung | gia | dap_an | ho_so | dap_an_d02
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
    from .drawing import concepts
    signals = concepts.load_signals()
    for ma, n in Counter(s.ma for s in signals).items():
        if n > 1:
            out.append(Finding("error", "ky_hieu", ma, f"Mã ký hiệu lặp {n} lần."))
    for ma, msg in concepts.conflicts(signals).items():
        out.append(Finding("error", "ky_hieu", ma, f"Ký hiệu {msg}."))


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
        if n.value is not None and not n.norm_code:
            # đặc tả 30/10/2026 mục 1A, 3B: hệ số tham khảo ngoài TT 38 được dùng (trạng thái C) nếu ghi đủ mức xác nhận,
            # nguồn và ngày tra; thiếu một trong ba thì là số không có căn cứ (Quy ước B7)
            lack = [k for k, v in (("mức xác nhận (muc_xac_nhan)", n.confirmation), ("nguồn (source)", n.source),
                                   ("ngày tra (ngay_tra)", n.checked_on)) if not v]
            if lack:
                out.append(Finding("error", "dinh_muc_phan_tho", item,
                                   "Có số mà chưa ghi số hiệu bảng TT 38/2026 và thiếu " + ", ".join(lack) + " (Quy ước B7)."))
            else:
                out.append(Finding("warning", "dinh_muc_phan_tho", item,
                                   f"Hệ số tham khảo ({n.confirmation}, {n.source}), chưa có số hiệu bảng TT 38/2026: vật liệu tính từ dòng này là tạm tính (C)."))
        if n.qty_min is not None and n.qty_max is not None and n.qty_min > n.qty_max:
            out.append(Finding("error", "dinh_muc_phan_tho", item, "Khoảng hệ số: qty_min lớn hơn qty_max."))
    blank = [n for n in norms if n.value is None]
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


def _check_abbreviations(out: list[Finding]) -> None:
    """data/rules/viet_tat.csv: mã không lặp, viết tắt và chữ đầy đủ không trống, viết tắt không trùng nhau,
    chữ đầy đủ không chứa lại chính viết tắt (giãn vô hạn / lặp)."""
    import csv
    path = config.DATA_DIR / "rules" / "viet_tat.csv"
    if not path.exists():
        out.append(Finding("warning", "quy_tac", "viet_tat.csv", "Chưa có file từ viết tắt: ghi chú viết tắt không được giãn."))
        return
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for ma, n in Counter(r["ma"] for r in rows).items():
        if n > 1:
            out.append(Finding("error", "quy_tac", ma, f"Mã viết tắt lặp {n} lần."))
    seen: dict[str, str] = {}
    for r in rows:
        short, full = normalize(r["viet_tat"]).strip(), normalize(r["day_du"]).strip()
        if not short or not full:
            out.append(Finding("error", "quy_tac", r["ma"], "Thiếu viết tắt hoặc chữ đầy đủ."))
            continue
        if short in seen:
            out.append(Finding("error", "quy_tac", r["ma"], f"Viết tắt \"{short}\" trùng với {seen[short]}."))
        seen[short] = r["ma"]
        if re.search(rf"(?<![a-z0-9]){re.escape(short)}(?![a-z0-9])", full):
            out.append(Finding("error", "quy_tac", r["ma"], f"Chữ đầy đủ \"{full}\" chứa lại viết tắt \"{short}\"."))
        if not r.get("nguon", "").strip():
            out.append(Finding("warning", "quy_tac", r["ma"], "Chưa ghi nguồn của cách viết tắt (Quy ước B7)."))


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
    """Lịch sử giá chỉ đọc từ PostgreSQL."""
    if not get_database_url():
        return {"nguon": "price_records", "dong": 0, "that": 0, "chi_tiet": []}
    with get_engine().connect() as conn:
        df = pd.read_sql_query("SELECT data_kind, price_level, count(*) AS n, max(date) AS last FROM price_records "
                               "GROUP BY 1, 2 ORDER BY 1, 2", conn)
    source = "price_records"
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


# Manifest hồ sơ đánh giá phần thô (D01): data/ground_truth/du_toan/cases.csv, mô tả trong README cùng thư mục
CASES_FILE = config.DATA_DIR / "ground_truth" / "du_toan" / "cases.csv"
CASE_REQUIRED = ("ten", "cong_trinh_id", "data_kind", "split", "du_toan")
CASE_COLUMNS = CASE_REQUIRED + ("phien_ban", "kien_truc", "ket_cau", "thong_so", "nguon", "quyen_dung",
                                "dap_an_trang_thai", "nguoi_kiem")
CASE_SPLITS = ("build", "test")
CASE_RIGHTS = ("duoc_phep", "noi_bo", "chua_ro")          # được phép phân phối | chỉ dùng nội bộ | chưa rõ
CASE_KEYS = ("chua_kiem", "da_kiem")                       # đáp án đã được người kiểm xác nhận hay chưa
CASE_PURPOSES = ("phat_trien", "bao_cao")


def check_cases(path=None, root=None) -> tuple[list[Finding], dict[str, list[str]]]:
    """Kiểm manifest hồ sơ đánh giá. Trả (phát hiện, {tên hồ sơ: lý do không chạy được}).
    Lỗi cấu trúc/định danh/tham chiếu và file CAD khai báo nhưng thiếu trên máy đều chặn hồ sơ đó; quyền dùng chưa rõ
    chỉ cảnh báo. Không sửa, không điền giá trị thay người dùng."""
    import csv
    path, root = Path(path or CASES_FILE), Path(root or config.ROOT)
    out: list[Finding] = []
    blocked: dict[str, list[str]] = defaultdict(list)
    if not path.exists():
        out.append(Finding("error", "ho_so", path.name, "Chưa có manifest hồ sơ đánh giá."))
        return out, dict(blocked)
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = reader.fieldnames or []
    missing_cols = [c for c in CASE_COLUMNS if c not in cols]
    if missing_cols:
        out.append(Finding("error", "ho_so", path.name, f"Thiếu cột: {', '.join(missing_cols)}."))
    seen: dict[str, int] = {}
    by_project: dict[str, list[tuple[str, str]]] = defaultdict(list)
    by_file: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def bad(level: str, line: int, ten: str, msg: str) -> None:
        out.append(Finding(level, "ho_so", f"{path.name} dòng {line} ({ten or 'không tên'})", msg))
        if level == "error":
            blocked[ten or f"dòng {line}"].append(msg)

    for i, r in enumerate(rows, start=2):                  # dòng 1 là tiêu đề
        r = {k: (v or "").strip() for k, v in r.items() if k}
        ten = r.get("ten", "")
        for c in CASE_REQUIRED:
            if c in cols and not r.get(c):
                bad("error", i, ten, f"Thiếu {c} (bắt buộc).")
        if ten:
            if ten in seen:
                bad("error", i, ten, f"Tên hồ sơ trùng dòng {seen[ten]}.")
            seen.setdefault(ten, i)
        for c, allowed in (("split", CASE_SPLITS), ("data_kind", DATA_KINDS), ("quyen_dung", CASE_RIGHTS),
                           ("dap_an_trang_thai", CASE_KEYS)):
            if r.get(c) and r[c] not in allowed:
                bad("error", i, ten, f"{c} = \"{r[c]}\" không hợp lệ (chọn: {', '.join(allowed)}).")
        if r.get("quyen_dung") in ("", "chua_ro") and "quyen_dung" in cols:
            bad("warning", i, ten, "Quyền dùng chưa rõ: chỉ dùng nội bộ để đánh giá, không phân phối lại hồ sơ.")
        if r.get("dap_an_trang_thai") == "da_kiem" and not r.get("nguoi_kiem"):
            bad("error", i, ten, "Đáp án ghi đã kiểm nhưng chưa có người kiểm.")
        if r.get("cong_trinh_id") and r.get("split") in CASE_SPLITS:
            by_project[r["cong_trinh_id"]].append((ten, r["split"]))
        for c in ("du_toan", "thong_so", "kien_truc", "ket_cau"):
            if not r.get(c):
                continue
            p = (root / r[c]).resolve()
            if c != "thong_so" and r.get("split") in CASE_SPLITS:      # cùng file đáp án/bản vẽ = cùng nguồn
                by_file[str(p).lower()].append((ten, r["split"]))
            if p.is_file():
                continue
            if p.exists():                             # có đường dẫn nhưng là thư mục: không đọc được như file
                bad("error", i, ten, f"{c}: {r[c]} không phải file.")
            elif c in ("du_toan", "thong_so"):         # đáp án, thông số nằm trong kho: thiếu là tham chiếu hỏng
                bad("error", i, ten, f"{c}: không có file {r[c]}.")
            else:                                      # bản vẽ không vào Git: thiếu trên máy này thì chưa chạy được
                bad("warning", i, ten, f"{c}: thiếu file cục bộ {r[c]} (bản vẽ không phân phối cùng kho).")
                blocked[ten].append(f"thiếu file cục bộ {r[c]}")
    # cùng công trình (kể cả khác phiên bản, tên) hoặc cùng file nguồn ở cả build và test: chặn cả hai phía
    groups = [(f"Công trình {k}", v) for k, v in by_project.items()] + \
             [(f"File {Path(k).name}", v) for k, v in by_file.items()]
    for label, items in groups:
        if len({s for _, s in items}) > 1:
            names = sorted({t for t, _ in items})
            msg = f"{label} nằm ở cả build và test ({', '.join(names)})."
            out.append(Finding("error", "ho_so", ", ".join(names), msg))
            for t in names:
                blocked[t].append(msg)
    return out, dict(blocked)


def select_cases(purpose: str, path=None, root=None) -> tuple[list[dict], list[tuple[str, str]]]:
    """Lối vào đánh giá: chọn hồ sơ được chạy theo mục đích.
        phat_trien  chỉ split build (mọi data_kind, kết quả ghi nhãn phát triển); không chạy test
        bao_cao     chỉ ACTUAL + test + đáp án đã kiểm có người kiểm (chỉ tiêu chính)
    Hồ sơ có lỗi manifest, chưa khai báo bản vẽ kiến trúc, đường dẫn không phải file hoặc thiếu bản vẽ cục bộ bị loại kèm lý do. Trả (hồ sơ chạy, [(tên, lý do loại)])."""
    import csv
    if purpose not in CASE_PURPOSES:
        raise ValueError(f"Mục đích đánh giá không hợp lệ: {purpose} (chọn: {', '.join(CASE_PURPOSES)}).")
    path = Path(path or CASES_FILE)
    findings, blocked = check_cases(path, root)
    fatal = [f.message for f in findings if f.level == "error" and f.item == path.name]
    if fatal:
        raise ValueError(f"Manifest {path.name} lỗi: {' '.join(fatal)}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [{k: (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]
    run, skipped = [], []
    for i, r in enumerate(rows, start=2):
        ten = r["ten"] or f"dòng {i}"
        if purpose == "phat_trien" and r["split"] != "build":
            why = "không phải split build (phát triển không chạy bộ test)"
        elif purpose == "bao_cao" and r["data_kind"] != "ACTUAL":
            why = f"data_kind {r['data_kind'] or 'trống'}: không vào chỉ tiêu chính"
        elif purpose == "bao_cao" and r["split"] != "test":
            why = f"split {r['split'] or 'trống'}: chỉ tiêu chính chỉ dùng test"
        elif purpose == "bao_cao" and (r["dap_an_trang_thai"] != "da_kiem" or not r["nguoi_kiem"]):
            why = "đáp án chưa được người kiểm xác nhận"
        elif blocked.get(ten):
            why = "; ".join(blocked[ten])
        elif not r["kien_truc"]:                    # manifest cho phép để trống, nhưng evaluator cần bản vẽ kiến trúc
            why = "chưa khai báo bản vẽ kiến trúc (kien_truc): evaluator không chạy được"
        else:
            run.append(r)
            continue
        skipped.append((ten, why))
    return run, skipped


def _check_cases_manifest(out: list[Finding]) -> dict:
    findings, blocked = check_cases()
    out += findings
    n = len(pd.read_csv(CASES_FILE, dtype=str)) if CASES_FILE.exists() else 0
    return {"ho_so": n, "bi_chan": sorted(blocked)}


# Bộ đáp án D02 (mẫu: data/ground_truth/du_toan/d02/_mau, đặc tả docs/D02_DAC_TA_DAP_AN.md): một thư mục mỗi hồ sơ,
# tên thư mục = cases.csv/ten. Kiểm hợp đồng dữ liệu, không tính KPI; không thực thi chuỗi công thức.
D02_DIR = CASES_FILE.parent / "d02"
D02_COLUMNS = {
    "so_hang_muc.csv": ("id", "cong_trinh_id", "vi_tri", "ma_pt", "ton_tai", "nguon_ton_tai", "pham_vi", "ma_qd", "ly_do",
                        "trang_thai_kiem", "nguoi_kiem", "ngay_kiem"),
    "dap_an_cong_tac.csv": ("id", "cong_trinh_id", "dong_goc", "cha_id", "quan_he_cha", "hang_muc_id", "ma_pt", "pham_vi", "ma_qd",
                            "dem_mau_so", "ma_cong_tac_goc", "ma_cong_tac", "cau_kien", "vi_tri", "noi_dung", "so_luong",
                            "kich_thuoc", "cong_thuc", "khoi_luong", "khoi_luong_tinh_lai", "don_vi", "cong_tru", "phu_thuoc",
                            "loai_nguon", "nguon", "trang_thai_kiem", "nguoi_kiem", "ngay_kiem", "can_kiem"),
    "dap_an_vat_tu.csv": ("id", "cong_trinh_id", "cong_tac_id", "dong_vat_tu_goc", "material_id", "ten_vat_tu", "quy_cach",
                          "don_vi_goc", "don_vi", "luong", "co_so_luong", "he_so", "nguon_he_so", "hao_hut", "dung_lam_dap_an",
                          "loai_nguon", "nguon", "trang_thai_kiem", "nguoi_kiem", "ngay_kiem", "thieu"),
    "khoa_nguon.csv": ("duong_dan", "vai_tro", "sha256", "so_byte", "trong_kho", "ngay_khoa", "ghi_chu"),
}
D02_CHECK = ("nhap", "cho_kiem", "da_kiem")
D02_EXISTS = ("co", "khong", "chua_ro")
D02_SCOPE = ("IN", "OUT", "chua_phan_loai", "hon_hop")      # hon_hop: chỉ dòng gốc có dòng con khác phạm vi
D02_COUNT = ("co", "khong", "cho_phan_loai")
D02_SOURCE = ("du_toan", "do_tay", "tai_lieu_khac")
# M01 mục 5A: hạng mục OUT; PT09 vừa IN (vật tư cọc) vừa OUT (dịch vụ ép/khoan/đập đầu cọc)
M01_PT = tuple(f"PT{i:02d}" for i in range(1, 48))
M01_PT_OUT = ("PT22", "PT25", "PT45", "PT46", "PT47")
M01_PT_BOTH = ("PT09",)
M01_QD_OUT = ("QĐ-chung", "QĐ-02", "QĐ-11", "QĐ-12", "QĐ-13", "QĐ-18")     # quyết định có thể đặt OUT
# đổi đơn vị chính xác (nhân lũy thừa 10 hoặc viết lại ký hiệu): không cần nguồn; (gốc, mới) -> hệ số nhân giá trị
EXACT_UNITS = {("tấn", "kg"): 1000.0, ("m3", "m³"): 1.0, ("m2", "m²"): 1.0, ("100m2", "m²"): 100.0, ("100m3", "m³"): 100.0,
               ("100m", "m"): 100.0}
D02_ADD = ("", "cong", "tru")      # cong_tru: phần con trừ (giao nhau, lỗ mở) ghi số âm kèm cong_tru = tru


def _num_or_none(v: str):
    """Số hữu hạn hoặc None (chuỗi trống, chữ, NaN, ±Infinity đều không phải số dùng để tính)."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _same(a: float, b: float) -> bool:
    """Bằng nhau trong sai số làm tròn số thực."""
    return abs(a - b) <= max(1e-9, 1e-9 * max(abs(a), abs(b)))


def _rows(path: Path) -> tuple[list[str], list[dict]]:
    import csv
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), [{k: (v or "").strip() for k, v in r.items() if k} for r in reader]


def denominator_ids(works: list[dict]) -> list[str]:
    """Dòng đáp án công tác vào mẫu số: dem_mau_so = co (một dòng mỗi dòng gốc; dòng con không bao giờ đếm)."""
    return [r["id"] for r in works if r.get("dem_mau_so") == "co"]


def material_totals(materials: list[dict]) -> dict[tuple[str, str, str], float]:
    """Cộng vật tư theo (quy cách, đơn vị, cơ sở lượng): lượng lắp đặt và lượng mua không bao giờ gộp chung."""
    out: dict[tuple[str, str, str], float] = defaultdict(float)
    for r in materials:
        q = _num_or_none(r.get("luong"))
        if q is not None:
            out[(r["quy_cach"], r["don_vi"], r["co_so_luong"])] += q
    return dict(out)


def check_answer_set(folder, cases_path=None, root=None) -> list[Finding]:
    """Kiểm một bộ đáp án D02. Lỗi: cấu trúc, liên kết, phạm vi trái M01, đã kiểm thiếu bằng chứng, số 0 thay số trống,
    tổng con lệch cha chưa ghi nhận, trộn lượng lắp đặt/mua, đổi đơn vị thiếu căn cứ. Cảnh báo: dòng chưa phân loại, phần chưa
    tách đủ số, lệch đã ghi nhận, nguồn ngoài kho thiếu trên máy."""
    import hashlib
    from .rough.models import WORKS
    folder, root = Path(folder), Path(root or config.ROOT)
    tag = f"d02/{folder.name}"
    out: list[Finding] = []

    def f(level: str, item: str, msg: str) -> None:
        out.append(Finding(level, "dap_an_d02", f"{tag}/{item}", msg))

    data: dict[str, list[dict]] = {}
    for name, cols in D02_COLUMNS.items():
        p = folder / name
        if not p.is_file():
            f("error", name, "Thiếu file.")
            data[name] = []
            continue
        have, rows = _rows(p)
        miss = [c for c in cols if c not in have]
        if miss:
            f("error", name, f"Thiếu cột: {', '.join(miss)}.")
            return out
        data[name] = rows
    hm, works, mats, lock = (data[n] for n in D02_COLUMNS)

    # liên kết với manifest D01
    case = None
    if (Path(cases_path) if cases_path else CASES_FILE).is_file():
        _, cases = _rows(Path(cases_path) if cases_path else CASES_FILE)
        case = next((c for c in cases if c.get("ten") == folder.name), None)
    if case is None:
        f("error", folder.name, "Tên thư mục không khớp hồ sơ nào trong cases.csv.")
    ct = case.get("cong_trinh_id") if case else None
    for name in ("so_hang_muc.csv", "dap_an_cong_tac.csv", "dap_an_vat_tu.csv"):
        bad = sorted({r["cong_trinh_id"] for r in data[name]} - {ct}) if ct else []
        if bad:
            f("error", name, f"cong_trinh_id {', '.join(bad)} khác manifest ({ct}).")

    def unique(rows: list[dict], name: str) -> dict[str, dict]:
        seen: dict[str, dict] = {}
        for i, r in enumerate(rows, start=2):
            if not r["id"]:
                f("error", f"{name} dòng {i}", "Thiếu id.")
            elif r["id"] in seen:
                f("error", f"{name} dòng {i}", f"id {r['id']} trùng.")
            seen.setdefault(r["id"], r)
        return seen

    def checked(r: dict, name: str, src_field: str) -> None:
        if r["trang_thai_kiem"] not in D02_CHECK:
            f("error", f"{name} {r['id']}", f"trang_thai_kiem \"{r['trang_thai_kiem']}\" không hợp lệ.")
        if r["trang_thai_kiem"] == "da_kiem":
            miss = [c for c in ("nguoi_kiem", "ngay_kiem", src_field) if not r.get(c)]
            if miss:
                f("error", f"{name} {r['id']}", f"Ghi đã kiểm nhưng thiếu {', '.join(miss)}.")

    def scope(r: dict, name: str) -> None:
        pt, pv, qd = r.get("ma_pt", ""), r["pham_vi"], r["ma_qd"]
        if pv not in D02_SCOPE or (pv == "hon_hop" and name != "dap_an_cong_tac.csv"):
            f("error", f"{name} {r['id']}", f"pham_vi \"{pv}\" không hợp lệ.")
        if pt and pt not in M01_PT:
            f("error", f"{name} {r['id']}", f"ma_pt {pt} không có trong M01.")
        if pv == "OUT":
            if not qd:
                f("error", f"{name} {r['id']}", "Dòng OUT thiếu mã quyết định M01.")
            elif not any(q in M01_QD_OUT for q in qd.split("/")):
                f("error", f"{name} {r['id']}", f"{qd} không phải quyết định đặt ngoài phạm vi (M01 5A).")
            if pt and pt not in M01_PT_OUT + M01_PT_BOTH:
                f("error", f"{name} {r['id']}", f"{pt} là IN theo M01, không được đặt OUT.")
        elif pv == "IN" and pt in M01_PT_OUT:
            f("error", f"{name} {r['id']}", f"{pt} là OUT theo M01 (H5), không được đặt IN.")

    # sổ hạng mục
    hm_by = unique(hm, "so_hang_muc.csv")
    for r in hm:
        scope(r, "so_hang_muc.csv")
        checked(r, "so_hang_muc.csv", "nguon_ton_tai")
        if r["ton_tai"] not in D02_EXISTS:
            f("error", f"so_hang_muc.csv {r['id']}", f"ton_tai \"{r['ton_tai']}\" không hợp lệ.")
        if r["ton_tai"] == "chua_ro" and not r["ly_do"]:
            f("error", f"so_hang_muc.csv {r['id']}", "Chưa rõ có/không nhưng không ghi lý do.")
    missing_pt = [p for p in M01_PT if p not in {r["ma_pt"] for r in hm}]
    if hm and missing_pt:
        f("error", "so_hang_muc.csv", f"Thiếu hạng mục M01: {', '.join(missing_pt)} (không phát hiện ≠ không có; ghi chua_ro).")

    # nguồn đã khóa: bắt buộc đúng một nguồn công tác (trùng manifest); thiếu thì không được bỏ qua đối chiếu số gốc
    src_rows: list[dict] = []
    vt_rows: list[dict] = []
    src_ok = vt_ok = False
    roles = Counter(r["vai_tro"] for r in lock)
    if roles["du_toan_cong_tac"] != 1:
        f("error", "khoa_nguon.csv", f"Phải có đúng một nguồn vai_tro = du_toan_cong_tac (đang có {roles['du_toan_cong_tac']}): "
                                     "không đối chiếu được số gốc và kiểm kê dòng dự toán.")
    if roles["du_toan_vat_tu"] > 1:
        f("error", "khoa_nguon.csv", f"Có {roles['du_toan_vat_tu']} nguồn du_toan_vat_tu, chỉ được một.")
    for r in lock:
        p = root / r["duong_dan"]
        if not p.is_file():
            f("error" if r["trong_kho"] == "co" else "warning", f"khoa_nguon.csv {r['duong_dan']}",
              "Không có file" + ("." if r["trong_kho"] == "co" else " trên máy này (ngoài kho)."))
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
            f("error", f"khoa_nguon.csv {r['duong_dan']}", "Nội dung file đã đổi sau khi khóa (sha256 khác).")
        if r["vai_tro"] == "du_toan_cong_tac":
            src_rows, src_ok = _rows(p)[1], roles["du_toan_cong_tac"] == 1
            if case and case.get("du_toan") != r["duong_dan"]:
                f("error", f"khoa_nguon.csv {r['duong_dan']}", f"Khác file đáp án của manifest ({case.get('du_toan')}).")
        elif r["vai_tro"] == "du_toan_vat_tu":
            vt_rows, vt_ok = _rows(p)[1], roles["du_toan_vat_tu"] == 1
    if roles["du_toan_cong_tac"] == 1 and not src_ok:
        f("error", "khoa_nguon.csv", "Không đọc được nguồn du_toan_cong_tac: không đối chiếu được số gốc.")
    if any(r["dong_vat_tu_goc"] for r in mats) and not vt_ok:
        f("error", "khoa_nguon.csv", "Đáp án vật tư tham chiếu dong_vat_tu_goc nhưng không có nguồn du_toan_vat_tu đọc được.")

    # đáp án công tác
    w_by = unique(works, "dap_an_cong_tac.csv")
    kids: dict[str, list[dict]] = defaultdict(list)
    for r in works:
        if r["cha_id"]:
            kids[r["cha_id"]].append(r)
    src_by = {s["stt"]: s for s in src_rows}
    roots_by_line: dict[str, list[str]] = defaultdict(list)
    pending = []
    for r in works:
        item = f"dap_an_cong_tac.csv {r['id']}"
        scope(r, "dap_an_cong_tac.csv")
        checked(r, "dap_an_cong_tac.csv", "nguon")
        if r["loai_nguon"] not in D02_SOURCE:
            f("error", item, f"loai_nguon \"{r['loai_nguon']}\" không hợp lệ.")
        if r["hang_muc_id"] and r["hang_muc_id"] not in hm_by:
            f("error", item, f"hang_muc_id {r['hang_muc_id']} không có trong sổ hạng mục.")
        for dep in filter(None, r["phu_thuoc"].split(";")):
            if dep not in w_by:
                f("error", item, f"phu_thuoc {dep} không có.")
        if r["ma_cong_tac"]:
            if r["ma_cong_tac"] not in WORKS:
                f("error", item, f"ma_cong_tac {r['ma_cong_tac']} không có trong WORKS.")
            elif r["don_vi"] != WORKS[r["ma_cong_tac"]][1]:
                f("error", item, f"Đơn vị {r['don_vi'] or 'trống'} khác đơn vị của {r['ma_cong_tac']} ({WORKS[r['ma_cong_tac']][1]}).")
        q = _num_or_none(r["khoi_luong"])
        if r["khoi_luong"] and q is None:
            f("error", item, f"khoi_luong \"{r['khoi_luong']}\" không phải số hữu hạn.")
        elif q == 0:
            f("error", item, "khoi_luong = 0: chưa có số thì để trống và ghi lý do.")
        elif not r["khoi_luong"] and not r["can_kiem"]:
            f("error", item, "Chưa có khối lượng nhưng không ghi lý do (can_kiem).")
        if r["khoi_luong_tinh_lai"] and _num_or_none(r["khoi_luong_tinh_lai"]) is None:
            f("error", item, f"khoi_luong_tinh_lai \"{r['khoi_luong_tinh_lai']}\" không phải số hữu hạn.")
        if r["cong_tru"] not in D02_ADD:
            f("error", item, f"cong_tru \"{r['cong_tru']}\" không hợp lệ (trống, cong, tru).")
        elif q is not None and q < 0 and not (r["cha_id"] and r["quan_he_cha"] == "phan" and r["cong_tru"] == "tru"):
            f("error", item, "Số âm chỉ dùng cho dòng con phần trừ (quan_he_cha = phan, cong_tru = tru).")
        elif q is not None and q > 0 and r["cong_tru"] == "tru":
            f("error", item, "Phần trừ phải ghi số âm.")
        if not r["don_vi"] and r["pham_vi"] != "OUT":
            f("error", item, "Thiếu đơn vị.")
        if r["pham_vi"] == "chua_phan_loai":
            pending.append(r["id"])
        if r["cha_id"]:
            parent = w_by.get(r["cha_id"])
            if parent is None:
                f("error", item, f"cha_id {r['cha_id']} không có.")
            elif parent["cha_id"]:
                f("error", item, "Chỉ cho phép một cấp cha–con.")
            elif parent["dong_goc"] != r["dong_goc"]:
                f("error", item, "Dòng con khác dong_goc của dòng cha.")
            if r["quan_he_cha"] not in ("phan", "khia_canh"):
                f("error", item, "quan_he_cha phải là phan hoặc khia_canh.")
            if r["dem_mau_so"] != "khong":
                f("error", item, "Dòng con không được tính mẫu số (dem_mau_so = khong).")
            if r["pham_vi"] == "hon_hop":
                f("error", item, "hon_hop chỉ dùng cho dòng gốc.")
            continue
        roots_by_line[r["dong_goc"]].append(r["id"])
        ks = kids.get(r["id"], [])
        if r["pham_vi"] == "hon_hop" and not ks:
            f("error", item, "hon_hop phải có dòng con.")
        pv = {k["pham_vi"] for k in ks} if r["pham_vi"] == "hon_hop" else {r["pham_vi"]}
        expect = "co" if "IN" in pv else "cho_phan_loai" if "chua_phan_loai" in pv else "khong"
        if r["dem_mau_so"] != expect:
            f("error", item, f"dem_mau_so = {r['dem_mau_so'] or 'trống'}, theo phạm vi phải là {expect}.")
        s = src_by.get(r["dong_goc"])
        if src_ok and s is None:
            f("error", item, f"dong_goc {r['dong_goc']} không có trong dự toán gốc.")
        elif s is not None:
            sq = _num_or_none(s["khoi_luong"])
            if sq is None or q is None or not _same(sq, q):
                f("error", item, f"khoi_luong {r['khoi_luong']} khác số gốc {s['khoi_luong']} (không sửa số gốc; ghi số tính lại riêng).")
            if (s["don_vi"] if s["don_vi"] != "nan" else "") != r["don_vi"]:
                f("error", item, f"Đơn vị {r['don_vi'] or 'trống'} khác đơn vị gốc {s['don_vi']}.")
        parts = [k for k in ks if k["quan_he_cha"] == "phan"]
        if parts and q is not None:
            if any(k["don_vi"] != r["don_vi"] for k in parts):
                f("error", item, "Dòng con khác đơn vị dòng cha.")
            vals = [_num_or_none(k["khoi_luong"]) for k in parts]
            if None in vals:
                f("warning", item, "Còn phần con chưa có số: chưa kiểm được tổng.")
            else:
                total, tol = sum(vals), max(1e-3, abs(q) * 1e-6)
                if abs(total - q) > tol:
                    noted = _num_or_none(r["khoi_luong_tinh_lai"])
                    if noted is not None and abs(noted - total) <= tol:
                        f("warning", item, f"Tổng phần con {total:g} lệch số gốc {q:g} (đã ghi khoi_luong_tinh_lai): người kiểm xác nhận.")
                    else:
                        f("error", item, f"Tổng phần con {total:g} lệch số gốc {q:g} mà chưa ghi khoi_luong_tinh_lai.")
    for line, ids in roots_by_line.items():
        if len(ids) > 1:
            f("error", f"dap_an_cong_tac.csv dòng gốc {line}", f"Nhiều dòng gốc cho cùng dòng dự toán: {', '.join(ids)}.")
    not_covered = [s["stt"] for s in src_rows if s["stt"] not in roots_by_line]
    if not_covered:
        f("error", "dap_an_cong_tac.csv", f"Chưa kiểm kê dòng dự toán gốc: {', '.join(not_covered)}.")
    if pending:
        f("warning", "dap_an_cong_tac.csv", f"{len(pending)} dòng chưa phân loại IN/OUT (giữ trong bộ, không coi là OUT): "
                                             f"{', '.join(pending[:10])}{' …' if len(pending) > 10 else ''}.")

    # đáp án vật tư
    unique(mats, "dap_an_vat_tu.csv")
    vt_by_line = {str(i): v for i, v in enumerate(vt_rows, start=2)}
    for r in mats:
        item = f"dap_an_vat_tu.csv {r['id']}"
        checked(r, "dap_an_vat_tu.csv", "nguon")
        for c in filter(None, r["cong_tac_id"].split(";")):
            if c not in w_by:
                f("error", item, f"cong_tac_id {c} không có trong đáp án công tác.")
        if not r["quy_cach"]:
            f("error", item, "Thiếu quy cách (giữ quy cách dù chưa có mã danh mục).")
        if r["co_so_luong"] not in ("lap_dat", "mua"):
            f("error", item, "co_so_luong phải là lap_dat hoặc mua.")
        if r["hao_hut"] not in ("da_gom", "chua_gom", "chua_ro"):
            f("error", item, f"hao_hut \"{r['hao_hut']}\" không hợp lệ.")
        if r["co_so_luong"] == "lap_dat" and r["hao_hut"] == "da_gom":
            f("error", item, "Lượng lắp đặt không được gồm hao hụt: trộn cơ sở lắp đặt và mua.")
        if r["dung_lam_dap_an"] not in ("co", "khong", "cho_kiem"):
            f("error", item, f"dung_lam_dap_an \"{r['dung_lam_dap_an']}\" không hợp lệ.")
        if r["dung_lam_dap_an"] == "khong" and r["trang_thai_kiem"] == "da_kiem":
            f("error", item, "Dòng không dùng làm đáp án không được ghi đã kiểm.")
        if r["loai_nguon"] not in D02_SOURCE:
            f("error", item, f"loai_nguon \"{r['loai_nguon']}\" không hợp lệ.")
        if r["he_so"]:
            hs = _num_or_none(r["he_so"])
            if hs is None or hs <= 0:
                f("error", item, f"he_so \"{r['he_so']}\" phải là số hữu hạn dương.")
            if not r["nguon_he_so"]:
                f("error", item, "Có hệ số nhưng thiếu nguồn hệ số.")
        factor = 1.0 if r["don_vi"] == r["don_vi_goc"] else EXACT_UNITS.get((r["don_vi_goc"], r["don_vi"]))
        if r["don_vi_goc"] and factor is None:
            f("error", item, f"Đổi {r['don_vi_goc']} → {r['don_vi']} thiếu căn cứ (chỉ đổi đơn vị chính xác).")
        q = _num_or_none(r["luong"])
        if r["luong"] and q is None:
            f("error", item, f"luong \"{r['luong']}\" không phải số hữu hạn.")
        elif q is not None and q < 0:
            f("error", item, "luong âm: lượng vật tư không được âm.")
        elif q == 0:
            f("error", item, "luong = 0: chưa có số thì để trống và ghi lý do.")
        elif not r["luong"] and not r["thieu"]:
            f("error", item, "Chưa có lượng nhưng không ghi dữ liệu thiếu.")
        if r["dong_vat_tu_goc"]:
            v = vt_by_line.get(r["dong_vat_tu_goc"])
            if vt_ok and v is None:
                f("error", item, f"dong_vat_tu_goc {r['dong_vat_tu_goc']} không có trong tổng hợp vật tư.")
            elif v is not None:
                if r["don_vi_goc"] != v["don_vi"]:
                    f("error", item, f"don_vi_goc {r['don_vi_goc'] or 'trống'} khác đơn vị nguồn {v['don_vi']}.")
                sq = _num_or_none(v["khoi_luong"])
                if factor is not None and (sq is None or q is None or not _same(sq * factor, q)):
                    f("error", item, f"luong {r['luong']} {r['don_vi']} khác số gốc {v['khoi_luong']} {v['don_vi']} sau quy đổi.")
    return out


def _check_answer_sets(out: list[Finding]) -> dict:
    sets = sorted(p for p in D02_DIR.glob("*") if p.is_dir() and not p.name.startswith("_")) if D02_DIR.is_dir() else []
    summary = {}
    for p in sets:
        out += check_answer_set(p)
        _, works = _rows(p / "dap_an_cong_tac.csv") if (p / "dap_an_cong_tac.csv").is_file() else ([], [])
        roots = [r for r in works if not r.get("cha_id")]
        summary[p.name] = {"dong_goc": len(roots), "dong_con": len(works) - len(roots), "mau_so": len(denominator_ids(works)),
                           "cho_phan_loai": sum(r.get("dem_mau_so") == "cho_phan_loai" for r in roots),
                           "da_kiem": sum(r.get("trang_thai_kiem") == "da_kiem" for r in works)}
    return summary


def run_checks(catalog: Catalog | None = None, today: date | None = None) -> dict:
    if catalog is None and not get_database_url():
        raise RuntimeError("Kiểm soát dữ liệu cần kết nối PostgreSQL (DATABASE_URL).")
    cat = catalog or Catalog.load()
    today = today or date.today()
    out: list[Finding] = []
    _check_materials(cat, out)
    classes = _check_wall_systems(cat, out)
    _check_aliases(cat, out)
    _check_rules(cat, out)
    rough = _check_rough_norms(cat, out)
    _check_material_notes(cat, out)
    _check_abbreviations(out)
    supply = _check_supply(cat, out, today)
    prices = _price_records_summary(out)
    truth = _check_ground_truth(cat, out)
    cases = _check_cases_manifest(out)
    answers = _check_answer_sets(out)
    fam = cat.materials.get("family", pd.Series(dtype=object))
    view = cat.wall_view()
    summary = {
        "nguon_du_lieu": "postgresql" if get_database_url() else "csv",
        "ngay_kiem_tra": today.isoformat(),
        "vat_lieu": len(cat.materials), "vat_lieu_tuong": int(fam.isin(list(cat.wall_families())).sum()),
        "phuong_an_tuong": len(view), "phuong_an_du_so_lieu": int(view.ready.sum()) if len(view) else 0,
        "theo_lop_tuong": classes, "ten_goi_khac": len(cat.aliases), "quy_tac": len(load_rules()),
        "nguon_cung": supply, "lich_su_gia": prices, "dap_an_do_tay": truth, "dinh_muc_phan_tho": rough,
        "ho_so_danh_gia": cases, "dap_an_d02": answers,
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
             f"| Đáp án đo tay: bản vẽ, theo nhóm | {s['dap_an_do_tay']['ban_ve']}, {s['dap_an_do_tay']['theo_nhom']} |",
             f"| Hồ sơ đánh giá phần thô (cases.csv): tổng, bị chặn | {s['ho_so_danh_gia']['ho_so']}, {len(s['ho_so_danh_gia']['bi_chan'])} |",
             "| Bộ đáp án D02: dòng gốc / mẫu số / chờ phân loại / đã kiểm | " + "; ".join(
                 f"{k}: {v['dong_goc']} / {v['mau_so']} / {v['cho_phan_loai']} / {v['da_kiem']}" for k, v in s.get("dap_an_d02", {}).items()) + " |", ""]
    names = {"error": "Lỗi (phải sửa)", "warning": "Cảnh báo", "info": "Ghi chú"}
    for level in ("error", "warning", "info"):
        items = [f for f in report["findings"] if f["level"] == level]
        if items:
            lines += [f"## {names[level]} ({len(items)})", "", "| Khu vực | Mục | Nội dung |", "|---|---|---|"]
            lines += [f"| {f['area']} | {f['item']} | {f['message'].replace('|', '/')} |" for f in items] + [""]
    return "\n".join(lines)
