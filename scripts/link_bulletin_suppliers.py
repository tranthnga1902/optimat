"""Ghép nhà cung cấp trong công bố giá (suppliers CBG-...) với đại lý thật cùng công ty (suppliers.linked_supplier_id).

Cùng công ty = trùng mã số thuế, hoặc trùng tên sau khi bỏ dấu, bỏ loại hình (công ty, cổ phần, TNHH, chi nhánh...) và
bỏ tiền tố thương hiệu kiểu Trang Vàng ("Sài Sơn - Công Ty ..."). Chỉ ghi khi có đúng một đại lý khớp; nhiều đại lý khớp
thì in ra để chọn tay ở trang /dai-ly. Không ghi đè cặp đã ghép.

    python scripts/link_bulletin_suppliers.py            # chỉ in đề xuất
    python scripts/link_bulletin_suppliers.py --apply    # ghi các cặp khớp duy nhất vào PostgreSQL
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

_FORMS = r"\b(cong ty|cty|co phan|cp|tnhh|mtv|tap doan|chi nhanh|vpdd|van phong dai dien|group|jsc|viet nam)\b"


def company_key(name: str | None) -> str:
    s = unicodedata.normalize("NFD", (name or "").lower().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"^[^-–]{1,40}\s[-–]\s(?=.*\bcong ty\b)", "", s)   # "Sài Sơn - Công Ty ...": bỏ tên thương hiệu đứng trước
    s = re.sub(_FORMS, " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def match(bulletin: list[dict], dealers: list[dict]) -> dict[str, list[dict]]:
    """Mã CBG -> các đại lý cùng công ty (mã số thuế trước, tên sau)."""
    out = {}
    for b in bulletin:
        tax = (b.get("tax_code") or "").strip()
        hits = [d for d in dealers if tax and (d.get("tax_code") or "").strip() == tax]
        if not hits and company_key(b["name"]):
            hits = [d for d in dealers if company_key(d["name"]) == company_key(b["name"])]
        out[b["supplier_id"]] = hits
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    from sqlalchemy import text

    from optimat.db.session import get_database_url, get_engine
    if not get_database_url():
        raise SystemExit("Cần DATABASE_URL (PostgreSQL).")
    with get_engine().begin() as conn:
        rows = [dict(r) for r in conn.execute(text(
            "SELECT supplier_id, name, tax_code, lat, lon, lead_time_days, linked_supplier_id FROM suppliers "
            "WHERE data_kind = 'ACTUAL'")).mappings()]
        bulletin = [r for r in rows if r["supplier_id"].startswith("CBG-") and not r["linked_supplier_id"]]
        dealers = [r for r in rows if not r["supplier_id"].startswith("CBG-")]
        linked = 0
        for b in bulletin:
            hits = match([b], dealers)[b["supplier_id"]]
            info = "; ".join(f"{d['supplier_id']} {d['name']} (tọa độ: {'có' if d['lat'] is not None else 'chưa'}, "
                             f"cung ứng: {d['lead_time_days'] if d['lead_time_days'] is not None else 'chưa'})" for d in hits)
            print(f"{b['supplier_id']} {b['name']}: " + (info or "không có đại lý khớp")
                  + (" -> nhiều đại lý, chọn tay ở /dai-ly" if len(hits) > 1 else ""))
            if args.apply and len(hits) == 1:
                conn.execute(text("UPDATE suppliers SET linked_supplier_id = :d WHERE supplier_id = :b"),
                             {"d": hits[0]["supplier_id"], "b": b["supplier_id"]})
                linked += 1
        print(f"Đã ghép {linked} nhà cung cấp công bố giá." if args.apply else "Chưa ghi (thêm --apply để ghi).")
    if args.apply and linked:
        from optimat.catalog.repository import default_catalog
        default_catalog.cache_clear()


if __name__ == "__main__":
    main()
