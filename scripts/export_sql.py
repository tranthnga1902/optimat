"""Sinh sql/01_schema.sql và sql/02_seed_sample.sql từ db/models.py và các file CSV.

    python scripts/export_sql.py

Dùng khi muốn tạo bảng bằng cách chạy SQL trực tiếp trong DBeaver thay vì chạy scripts/init_db.py.
Sau khi sửa db/models.py, chạy lại script này để hai file SQL khớp với mã.
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.db.models import Base  # noqa: E402

SEED_TABLES = ["material_groups", "materials", "suppliers", "supplier_materials", "vehicles"]


def literal(value) -> str:
    if pd.isna(value):
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return repr(float(value)) if isinstance(value, float) and not float(value).is_integer() else str(int(value))
    return "'" + str(value).replace("'", "''") + "'"


def main() -> None:
    dialect = postgresql.dialect()
    lines = ["-- Lược đồ OptiMat AI (19 bảng). Sinh tự động từ src/optimat/db/models.py, không sửa tay.",
             "-- Chạy trong DBeaver khi đang kết nối tới database optimat bằng tài khoản optimat.", ""]
    for table in Base.metadata.sorted_tables:
        lines.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";\n")
        for index in sorted(table.indexes, key=lambda i: i.name):
            lines.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";\n")
    (ROOT / "sql/01_schema.sql").write_text("\n".join(lines), encoding="utf8")

    seed = ["-- Dữ liệu khởi tạo: 5 nhóm vật liệu (thật) và danh mục MẪU (data_kind = SAMPLE).",
            "-- Chạy sau 01_schema.sql. Thay dữ liệu SAMPLE bằng dữ liệu thật trước khi báo cáo kết quả.", ""]
    for name in SEED_TABLES:
        df = pd.read_csv(ROOT / "data/catalog" / f"{name}.csv")
        cols = ", ".join(f'"{c}"' for c in df.columns)
        seed.append(f"-- {name}: {len(df)} dòng")
        for row in df.itertuples(index=False):
            seed.append(f'INSERT INTO "{name}" ({cols}) VALUES ({", ".join(literal(v) for v in row)});')
        seed.append("")
    (ROOT / "sql/02_seed_sample.sql").write_text("\n".join(seed), encoding="utf8")
    print(f"Đã ghi sql/01_schema.sql ({len(Base.metadata.tables)} bảng) và sql/02_seed_sample.sql")


if __name__ == "__main__":
    main()
