"""Sinh sql/01_schema.sql, sql/02_seed_sample.sql và sql/05_rules.sql từ db/models.py và các file CSV.

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
from optimat.db.compat20 import schema_sql  # noqa: E402

RULE_TABLES = {"material_rules": "material_rules.csv", "room_rules": "room_rules.csv", "rough_norms": "dinh_muc_phan_tho.csv",
               "material_notes": "material_notes.csv", "drawing_concepts": "concepts.csv", "convention_clauses": "quy_uoc.csv"}
SEED_TABLES = ["material_groups", "material_families", "materials", "suppliers", "supplier_materials", "vehicles", "labor_rates"]


def literal(value) -> str:
    if pd.isna(value):
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return repr(float(value)) if isinstance(value, float) and not float(value).is_integer() else str(int(value))
    return "'" + str(value).replace("'", "''") + "'"


def main() -> None:
    (ROOT / "sql/01_schema.sql").write_text(schema_sql(), encoding="utf8")

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

    rules = ["-- Bộ quy tắc bóc tách và định mức phần thô, sinh từ data/rules/*.csv bằng scripts/export_sql.py. Không sửa tay.",
             "-- Chạy sau 01_schema.sql (hoặc 04_upgrade.sql). Chạy lại được: xóa rồi nạp lại toàn bộ 3 bảng.",
             "-- Sửa CSV bằng Excel rồi sinh lại file này (hoặc chạy scripts/init_db.py --reload-rules).", "",
             "SET client_encoding = 'UTF8';", "BEGIN;"]
    for name, csv in RULE_TABLES.items():
        df = pd.read_csv(ROOT / "data/rules" / csv, dtype=str)
        # cột chỉ có trong CSV (chưa đổi lược đồ) thì không đưa vào SQL
        df = df[[c for c in df.columns if c in Base.metadata.tables[name].columns]]
        cols = ", ".join(f'"{c}"' for c in df.columns)
        rules += ["", f"-- {name}: {len(df)} dòng từ {csv}", f'DELETE FROM "{name}";']
        for row in df.itertuples(index=False):
            rules.append(f'INSERT INTO "{name}" ({cols}) VALUES ({", ".join(literal(v) for v in row)});')
    rules += ["", "COMMIT;", ""]
    (ROOT / "sql/05_rules.sql").write_text("\n".join(rules), encoding="utf8")
    parts=['01_schema.sql','02_seed_sample.sql','03_materials.sql','04_upgrade.sql','05_rules.sql','06_demo_actual.sql','07_cement_historical_actual.sql']
    bundle=['-- OptiMat AI: khởi tạo 20 bảng vật lý và dữ liệu nguồn. Không phải backup dữ liệu người dùng.\n-- Database đã có dữ liệu: dùng migrate_schema20.py --apply, không chạy lại gói khởi tạo.']
    for name in parts:
        path=ROOT/'sql'/name
        if path.exists():
            bundle.append('-- Nguồn: '+name+'\n'+path.read_text(encoding='utf-8'))
    (ROOT/'sql/optimat_day_du.sql').write_text('\n\n'.join(bundle),encoding='utf-8')
    print('Đã ghi sql/01_schema.sql (20 bảng vật lý và view tương thích), sql/02_seed_sample.sql và sql/05_rules.sql')


if __name__ == "__main__":
    main()
