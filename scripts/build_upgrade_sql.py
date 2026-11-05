"""Sinh kiểm tra schema 20; chuyển dữ liệu bằng migrate_schema20.py có backup."""
import sys
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from optimat.db.schema20 import NAMES, metadata
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, CreateColumn, CreateIndex, AddConstraint

VIEWS='''
CREATE OR REPLACE VIEW v_price_training AS
SELECT p.id,p.date,p.material_id,p.supplier_id,p.province,p.quantity,p.unit,p.unit_price,
       p.vat_included,p.transport_included,p.price_level,p.source,
       m.name AS material_name,m."group" AS material_group,m.family,m.tier,m.unit AS material_unit,
       s.district AS supplier_district,s.dealer_type,s.lat AS supplier_lat,s.lon AS supplier_lon
FROM price_records p JOIN materials m ON m.material_id=p.material_id
LEFT JOIN suppliers s ON s.supplier_id=p.supplier_id WHERE p.data_kind='ACTUAL';
'''

def main():
    names=','.join("'"+n+"'" for n in sorted(NAMES))
    dialect=postgresql.dialect()
    repairs=[]
    for table in metadata.sorted_tables:
        repairs.append(str(CreateTable(table,if_not_exists=True).compile(dialect=dialect))+';')
        for c in table.columns:
            repairs.append(f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS '+str(CreateColumn(c).compile(dialect=dialect))+';')
        for k in table.constraints:
            if isinstance(k,(CheckConstraint,UniqueConstraint)) and k.name:
                ddl=str(AddConstraint(k).compile(dialect=dialect))
                sql_name=re.search(r'ADD CONSTRAINT "?([A-Za-z0-9_]+)',ddl).group(1)
                repairs.append(f"DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='{table.name}'::regclass AND conname='{sql_name}') THEN {ddl}; END IF; END $$;")
        repairs.extend(str(CreateIndex(i,if_not_exists=True).compile(dialect=dialect))+';' for i in sorted(table.indexes,key=lambda i:i.name))
    sql=f'''-- Sinh từ scripts/build_upgrade_sql.py. Không tạo lại 28 bảng cũ.
-- Database cũ: python scripts/migrate_schema20.py --apply (backup bắt buộc).
BEGIN;
DO $$
DECLARE actual text[];
BEGIN
  SELECT array_agg(table_name::text ORDER BY table_name) INTO actual FROM information_schema.tables
  WHERE table_schema='public' AND table_type='BASE TABLE';
  IF actual IS NULL OR NOT actual <@ ARRAY[{names}]::text[] THEN
    RAISE EXCEPTION 'Database chưa đúng 20 bảng. Chạy scripts/migrate_schema20.py --apply trước.';
  END IF;
END $$;
{chr(10).join(repairs)}
{VIEWS}
COMMIT;
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;
'''
    (ROOT/'sql/04_upgrade.sql').write_text(sql,encoding='utf-8')
    print('Đã sinh sql/04_upgrade.sql: kiểm tra đúng 20 bảng và cập nhật view huấn luyện.')

if __name__=='__main__':main()
