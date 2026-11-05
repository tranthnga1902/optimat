"""Tạo bảng trong PostgreSQL và nạp dữ liệu từ các file CSV.

    $env:DATABASE_URL = "postgresql+psycopg://optimat:matkhau@localhost:5432/optimat"
    python scripts/init_db.py                  # tạo bảng, nạp danh mục
    python scripts/init_db.py --prices data/sample/prices_sample.csv   # nạp thêm lịch sử giá
    python scripts/init_db.py --standards data/catalog/standards.csv   # nạp tiêu chuẩn (cột: code,title,kind,status,valid_from,valid_to,source_url)
                                                                       # và material_standards.csv cùng thư mục (material_id,code,note)
    python scripts/init_db.py --reload-rules   # nạp lại 6 bảng quy tắc từ data/rules sau khi sửa CSV bằng Excel
    python scripts/init_db.py --reset          # xóa toàn bộ bảng rồi tạo lại (mất dữ liệu)

Script chỉ nạp vào bảng đang trống, nên chạy lại nhiều lần không tạo dòng trùng.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sqlalchemy import String  # noqa: E402

from optimat.db.models import Base  # noqa: E402
from optimat.db.session import get_engine  # noqa: E402
from optimat.db.compat20 import initialize_database  # noqa: E402
from optimat.db.schema20 import NAMES  # noqa: E402

CATALOG_TABLES = ["material_groups", "material_families", "materials", "wall_systems", "material_aliases", "material_relations", "suppliers",
                  "supplier_materials", "vehicles", "labor_rates"]   # theo thứ tự khóa ngoại
RULE_TABLES = {"material_rules": "material_rules.csv", "room_rules": "room_rules.csv", "rough_norms": "dinh_muc_phan_tho.csv",
               "material_notes": "material_notes.csv", "drawing_concepts": "concepts.csv", "convention_clauses": "quy_uoc.csv"}


def load_table(engine, table: str, csv_path: Path, date_cols=()) -> int:
    with engine.connect() as conn:
        existing = pd.read_sql_query(f'SELECT COUNT(*) AS n FROM "{table}"', conn).n[0]
    if existing:
        print(f"  {table}: đã có {existing} dòng, bỏ qua")
        return 0
    # cột chữ đọc thành chữ (mã "15", "220" không bị đổi thành số)
    df = pd.read_csv(csv_path, dtype={c.name: str for c in Base.metadata.tables[table].columns if isinstance(c.type, String)})
    # cột chỉ có trong CSV mà chưa có trong lược đồ: bỏ qua khi nạp, báo để biết (mã đọc bảng sẽ không thấy các cột này)
    extra = [c for c in df.columns if c not in Base.metadata.tables[table].columns]
    if extra:
        print(f"  {table}: bỏ qua cột chưa có trong lược đồ: {', '.join(extra)}")
        df = df.drop(columns=extra)
    for col in date_cols:
        df[col] = pd.to_datetime(df[col]).dt.date
    df.to_sql(table, engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  {table}: nạp {len(df)} dòng từ {csv_path.name}")
    return len(df)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="xóa toàn bộ bảng rồi tạo lại")
    parser.add_argument("--prices", help="file CSV lịch sử giá để nạp vào bảng price_records")
    parser.add_argument("--reload-rules", action="store_true", help="xóa rồi nạp lại 6 bảng quy tắc từ data/rules")
    parser.add_argument("--standards", help="file CSV tiêu chuẩn, quy chuẩn để nạp vào bảng standards")
    args = parser.parse_args()
    engine = get_engine()
    initialize_database(engine, reset=args.reset)
    print('Đã có 20 bảng vật lý:', ', '.join(sorted(NAMES)))
    for table in CATALOG_TABLES:
        load_table(engine, table, ROOT / "data/catalog" / f"{table}.csv",
                   date_cols={"suppliers": ("collected_at",), "supplier_materials": ("collected_at", "price_date"), "labor_rates": ("valid_from",)}.get(table, ()))
    if args.reload_rules:
        from sqlalchemy import text
        with engine.begin() as conn:
            for table in RULE_TABLES:
                conn.execute(text(f'DELETE FROM "{table}"'))
    for table, name in RULE_TABLES.items():
        load_table(engine, table, ROOT / "data/rules" / name)
    if args.prices:
        load_table(engine, "price_records", Path(args.prices), date_cols=("date",))
    if args.standards:
        load_table(engine, "standards", Path(args.standards), date_cols=("valid_from", "valid_to"))
        load_material_standards(engine, Path(args.standards).with_name("material_standards.csv"))


def load_material_standards(engine, csv_path: Path) -> int:
    """Liên kết vật liệu - tiêu chuẩn (cột material_id, code, note): code quy về standard_id của bảng standards."""
    if not csv_path.exists():
        return 0
    with engine.connect() as conn:
        if pd.read_sql_query('SELECT COUNT(*) AS n FROM "material_standards"', conn).n[0]:
            print("  material_standards: đã có dữ liệu, bỏ qua")
            return 0
        ids = pd.read_sql_query("SELECT standard_id, code FROM standards", conn)
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False).merge(ids, on="code", how="left")
    missing = df[df.standard_id.isna()].code.unique()
    if len(missing):
        raise SystemExit(f"material_standards: mã tiêu chuẩn chưa có trong bảng standards: {', '.join(missing)}")
    df[["material_id", "standard_id", "note"]].astype({"standard_id": int}).to_sql(
        "material_standards", engine, if_exists="append", index=False, method="multi")
    print(f"  material_standards: nạp {len(df)} dòng từ {csv_path.name}")
    return len(df)


if __name__ == "__main__":
    main()
