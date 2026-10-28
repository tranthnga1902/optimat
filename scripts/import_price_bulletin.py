"""Nạp file PDF công bố giá vật liệu của Sở Xây dựng vào bảng suppliers và price_records (mức giá BULLETIN).

    python scripts/import_price_bulletin.py <file.pdf> [--province "Hà Nội"] [--date 2026-06-20] [--no-db]

Mỗi công ty / bãi trong công bố là một nhà cung cấp (mã CBG-...). Chỉ dòng ghép được mã vật liệu theo
data/rules/cong_bo_gia.csv mới vào database; mỗi (nhà cung cấp, mã) lấy dòng đầu tiên. Toàn bộ dòng đọc được ghi ra
data/cong_bo_gia/<số văn bản>.csv (cột material_id, ly_do) để duyệt và bổ sung quy tắc.
Nạp lại không ghi đè: nhà cung cấp đã có giữ nguyên (sửa đổi trên trang Đại lý), giá trùng nguồn bị bỏ qua.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.catalog.bulletin import load_rules, match, read_pdf, supplier_id, transport_included  # noqa: E402


def frames(rows, doc_no: str, date: str, province: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ok = [r for r in rows if r.material_id]
    date = dt.date.fromisoformat(date)
    source = f"Công bố giá {doc_no} ({province})"
    suppliers = {}
    for r in ok:
        suppliers.setdefault(supplier_id(r.supplier), {
            "supplier_id": supplier_id(r.supplier), "name": r.supplier[:255], "province": province, "data_kind": "ACTUAL",
            "dealer_type": "bãi / mỏ vật liệu" if r.terms.startswith("giá tại bãi") else "nhà sản xuất / cung ứng",
            "price_public": "YES", "verified": False, "collected_at": date, "collected_by": "nạp công bố giá",
            "source": source[:1024], "note": f"Nhà sản xuất: {r.maker}"[:2000] if r.maker else None})
    prices = [{
        "date": date, "material_id": r.material_id, "supplier_id": supplier_id(r.supplier), "province": province,
        "quantity": 1.0, "unit": None, "unit_price": r.catalog_price, "vat_included": "NO",
        "transport_included": transport_included(r.terms), "price_level": "BULLETIN", "data_kind": "ACTUAL",
        "source": f"{source}, tr.{r.page + 1}: {r.name} ({r.unit})"[:1024]} for r in ok]
    return pd.DataFrame(list(suppliers.values())), pd.DataFrame(prices)


def to_db(sup: pd.DataFrame, prices: pd.DataFrame) -> tuple[int, int]:
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert

    from optimat.db.models import Base
    from optimat.db.session import get_engine
    with get_engine().begin() as conn:
        units = dict(conn.execute(text("SELECT material_id, unit FROM materials")).all())
        missing = sorted(set(prices.material_id) - set(units))
        if missing:
            raise SystemExit(f"Mã vật liệu không có trong bảng materials: {missing}")
        prices = prices.assign(unit=prices.material_id.map(units))      # giá đã đổi sang đơn vị tính của danh mục
        count = lambda t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()   # rowcount của INSERT nhiều dòng = -1
        before = count("suppliers"), count("price_records")
        conn.execute(insert(Base.metadata.tables["suppliers"]).values(sup.to_dict("records"))
                     .on_conflict_do_nothing(index_elements=["supplier_id"]))
        conn.execute(insert(Base.metadata.tables["price_records"]).values(prices.to_dict("records")).on_conflict_do_nothing())
        return count("suppliers") - before[0], count("price_records") - before[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--province", default="Hà Nội")
    ap.add_argument("--date", help="ngày của giá (YYYY-MM-DD); mặc định đọc dấu thời gian chữ ký số trong PDF")
    ap.add_argument("--no-db", action="store_true", help="chỉ ghi CSV duyệt")
    args = ap.parse_args()

    print("Đang đọc bảng trong PDF (vài phút với file hàng trăm trang)...")
    b = read_pdf(args.pdf)
    date = args.date or b.date
    if not date:
        raise SystemExit("Không đọc được ngày công bố trong PDF: chạy lại với --date YYYY-MM-DD.")
    rows = match(b.rows, load_rules())

    out = ROOT / "data/cong_bo_gia" / (re.sub(r"[^\w.-]+", "_", b.doc_no) + ".csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"trang": r.page + 1, "nha_cung_cap": r.supplier, "ten": r.name, "don_vi": r.unit, "gia": r.price,
                   "nha_san_xuat": r.maker, "dieu_kien": r.terms, "material_id": r.material_id, "quy_tac": r.rule_id,
                   "gia_theo_dvt_danh_muc": r.catalog_price, "ly_do": r.reason} for r in rows]
                 ).to_csv(out, index=False, encoding="utf-8-sig")
    sup, prices = frames(rows, b.doc_no, date, args.province)
    print(f"{b.doc_no}, ngày {date}: {len(rows)} dòng giá, ghép được {len(prices)} giá / {prices.material_id.nunique()} mã / "
          f"{len(sup)} nhà cung cấp. Bảng duyệt: {out.relative_to(ROOT)}")

    from optimat.db.session import get_database_url
    if not args.no_db and get_database_url() and len(prices):
        n_sup, n_price = to_db(sup, prices)
        print(f"Database: thêm {n_sup} nhà cung cấp, {n_price} giá (bỏ qua dòng đã có).")


if __name__ == "__main__":
    main()
