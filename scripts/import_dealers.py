"""Nạp danh bạ đại lý thật (thu thập ở thư mục ngoài, vd. D:\\daily) vào data/catalog/suppliers.csv và bảng suppliers.

    python scripts/import_dealers.py --src D:\\daily [--no-db]

Thư mục nguồn có gop_dai_ly.py (gộp Trang Vàng, Hòa Phát, OpenStreetMap, Google; loại trùng) và, nếu đã chạy
geocode_dai_ly.py, geocode_cache.csv (tọa độ tra từ địa chỉ). Chưa có tọa độ / thời gian cung ứng thì để trống.
Đại lý đã có trong database không bị ghi đè (giữ sửa đổi và ghi chép trên trang Đại lý), chỉ bổ sung tọa độ còn trống.
"""
import argparse
import csv
import datetime as dt
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build(src: Path) -> pd.DataFrame:
    sys.path.insert(0, str(src))
    cwd = os.getcwd()
    os.chdir(src)                                    # gop_dai_ly đọc file theo đường dẫn tương đối
    try:
        import gop_dai_ly
        _, merged = gop_dai_ly.merge()
    finally:
        os.chdir(cwd)
    geo = {}
    if (src / "geocode_cache.csv").exists():
        with open(src / "geocode_cache.csv", encoding="utf-8-sig") as f:
            geo = {r["dia_chi"]: r for r in csv.DictReader(f) if r["lat"]}
    rows = []
    for r in merged:
        g = geo.get(r["dia_chi"]) if not r["lat"] else None
        lat, lon = (_num(g["lat"]), _num(g["lng"])) if g else (_num(r["lat"]), _num(r["lng"]))
        files = [f for f in ("dai_ly_yp.csv", "dai_ly_hoaphat.csv", "dai_ly_osm.csv", "dai_ly.csv") if (src / f).exists()]
        collected = max(dt.date.fromtimestamp((src / f).stat().st_mtime) for f in files)
        source = "; ".join(x for x in (r["nguon"], r["link"]) if x)
        if g:
            source += f"; tọa độ Nominatim theo địa chỉ ({'đúng địa chỉ' if g['bo_phan'] == '0' else 'gần đúng'})"
        rows.append({
            "supplier_id": r["ma"], "name": r["ten"][:255], "province": r["tinh"], "lat": lat, "lon": lon,
            "lead_time_days": None, "data_kind": "ACTUAL", "address": r["dia_chi"][:512] or None,
            "phone": r["dien_thoai"][:64] or None, "website": r["website"][:1024] or None,
            "maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat is not None else None,
            "verified": False, "collected_at": collected, "collected_by": "thu thập tự động", "source": source[:1024],
            "note": f"Nhóm vật liệu: {r['nhom']}" if r["nhom"] else None,
        })
    return pd.DataFrame(rows)


def to_db(df: pd.DataFrame) -> tuple[int, int]:
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert

    from optimat.db.models import Base
    from optimat.db.session import get_engine
    t = Base.metadata.tables["suppliers"]
    recs = [{k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in r.items()} for r in df.to_dict("records")]
    with get_engine().begin() as conn:
        before = conn.execute(text("SELECT count(*) FROM suppliers")).scalar()
        for i in range(0, len(recs), 500):
            stmt = insert(t).values(recs[i:i + 500])
            conn.execute(stmt.on_conflict_do_update(index_elements=["supplier_id"], set_={
                c: text(f"COALESCE(suppliers.{c}, excluded.{c})") for c in ("lat", "lon", "maps_url")}))
        after = conn.execute(text("SELECT count(*) FROM suppliers")).scalar()
    return after - before, after


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="thư mục có gop_dai_ly.py và các file dai_ly_*.csv")
    ap.add_argument("--no-db", action="store_true", help="chỉ ghi data/catalog/suppliers.csv")
    args = ap.parse_args()
    df = build(Path(args.src))
    assert df.supplier_id.is_unique, "mã đại lý trùng"
    df.to_csv(ROOT / "data/catalog/suppliers.csv", index=False, encoding="utf-8")
    print(f"data/catalog/suppliers.csv: {len(df)} đại lý, {df.lat.notna().sum()} có tọa độ.")
    from optimat.db.session import get_database_url
    if not args.no_db and get_database_url():
        added, total = to_db(df)
        print(f"Bảng suppliers: thêm {added}, tổng {total}.")


if __name__ == "__main__":
    main()
