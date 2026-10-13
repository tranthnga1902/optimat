"""Tạo bảng trong PostgreSQL và nạp dữ liệu từ các file CSV.

    $env:DATABASE_URL = "postgresql+psycopg://optimat:matkhau@localhost:5432/optimat"
    python scripts/init_db.py                  # tạo bảng, nạp danh mục
    python scripts/init_db.py --prices data/sample/prices_sample.csv   # nạp thêm lịch sử giá
    python scripts/init_db.py --standards tieu_chuan.csv   # nạp tiêu chuẩn (cột: code,title,kind,status,valid_from,valid_to,source_url)
    python scripts/init_db.py --reset          # xóa toàn bộ bảng rồi tạo lại (mất dữ liệu)

Script chỉ nạp vào bảng đang trống, nên chạy lại nhiều lần không tạo dòng trùng.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.db.models import Base  # noqa: E402
from optimat.db.session import get_engine  # noqa: E402

CATALOG_TABLES = ["material_groups", "materials", "wall_systems", "material_aliases", "suppliers", "supplier_materials", "vehicles"]   # theo thứ tự khóa ngoại


def load_table(engine, table: str, csv_path: Path, date_cols=()) -> int:
    with engine.connect() as conn:
        existing = pd.read_sql_query(f'SELECT COUNT(*) AS n FROM "{table}"', conn).n[0]
    if existing:
        print(f"  {table}: đã có {existing} dòng, bỏ qua")
        return 0
    df = pd.read_csv(csv_path)
    for col in date_cols:
        df[col] = pd.to_datetime(df[col]).dt.date
    df.to_sql(table, engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  {table}: nạp {len(df)} dòng từ {csv_path.name}")
    return len(df)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="xóa toàn bộ bảng rồi tạo lại")
    parser.add_argument("--prices", help="file CSV lịch sử giá để nạp vào bảng price_records")
    parser.add_argument("--standards", help="file CSV tiêu chuẩn, quy chuẩn để nạp vào bảng standards")
    args = parser.parse_args()
    engine = get_engine()
    if args.reset:
        from sqlalchemy import text
        with engine.begin() as conn:      # view do sql/03, sql/04 tạo phụ thuộc vào bảng: bỏ trước khi xóa bảng
            conn.execute(text("DROP VIEW IF EXISTS v_price_training, v_wall_systems CASCADE"))
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print(f"Đã có {len(Base.metadata.tables)} bảng:", ", ".join(t.name for t in Base.metadata.sorted_tables))
    for table in CATALOG_TABLES:
        load_table(engine, table, ROOT / "data/catalog" / f"{table}.csv",
                   date_cols=("collected_at", "price_date") if table == "supplier_materials" else ())
    if args.prices:
        load_table(engine, "price_records", Path(args.prices), date_cols=("date",))
    if args.standards:
        load_table(engine, "standards", Path(args.standards))


if __name__ == "__main__":
    main()
