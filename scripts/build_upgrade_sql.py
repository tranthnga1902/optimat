"""Sinh sql/04_upgrade.sql: nâng cấp một database optimat đã có (đang thiếu bảng, cột, ràng buộc) lên đúng
lược đồ trong src/optimat/db/models.py mà không xóa dữ liệu.

    python scripts/build_upgrade_sql.py

Script SQL sinh ra chạy lại nhiều lần được: chỉ thêm cái còn thiếu, không xóa bảng, không xóa dòng.
Ràng buộc nào bị dữ liệu cũ vi phạm thì bỏ qua và in cảnh báo (WARNING) để sửa dữ liệu rồi chạy lại.
Cuối script có truy vấn kiểm tra: liệt kê bảng, cột, ràng buộc còn thiếu hoặc sai kiểu; kết quả rỗng là đủ.
"""
import re
import sys
from pathlib import Path

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import AddConstraint, CreateIndex, CreateTable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.db.models import Base  # noqa: E402

DIALECT = postgresql.dialect()
UDT = {"VARCHAR": "varchar", "FLOAT": "float8", "INTEGER": "int4", "BIGINT": "int8", "BOOLEAN": "bool",
       "DATE": "date", "TEXT": "text", "TIMESTAMP WITH TIME ZONE": "timestamptz", "JSONB": "jsonb"}

VIEWS = '''
-- View đặc trưng cho huấn luyện mô hình giá: chỉ lấy dữ liệu thật (ACTUAL), nối thông tin vật liệu và đại lý.
-- Công cụ Price đọc dữ liệu huấn luyện từ một chỗ duy nhất này.
DROP VIEW IF EXISTS v_price_training;
CREATE VIEW v_price_training AS
SELECT p.id, p.date, p.material_id, p.supplier_id, p.province, p.quantity, p.unit, p.unit_price,
       p.vat_included, p.transport_included, p.price_level, p.source,
       m.name AS material_name, m."group" AS material_group, m.family, m.tier, m.unit AS material_unit,
       s.district AS supplier_district, s.dealer_type, s.lat AS supplier_lat, s.lon AS supplier_lon
FROM price_records p
JOIN materials m ON m.material_id = p.material_id
LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id
WHERE p.data_kind = 'ACTUAL';
'''

BACKFILL = '''
-- Giá đã có trong supplier_materials trước khi có cột mức giá: coi là giá đại lý, ngày của giá = ngày thu thập.
UPDATE supplier_materials SET price_level = 'DEALER' WHERE base_price IS NOT NULL AND price_level IS NULL;
UPDATE supplier_materials SET price_date = collected_at WHERE base_price IS NOT NULL AND price_date IS NULL;
-- Chuẩn hóa giá trị cờ thuế, vận chuyển về YES / NO / UNKNOWN.
UPDATE supplier_materials SET vat_included = 'UNKNOWN' WHERE vat_included IS NULL OR vat_included NOT IN ('YES', 'NO', 'UNKNOWN');
UPDATE supplier_materials SET transport_included = 'UNKNOWN' WHERE transport_included IS NULL OR transport_included NOT IN ('YES', 'NO', 'UNKNOWN');
UPDATE price_records SET vat_included = 'UNKNOWN' WHERE vat_included IS NULL OR vat_included NOT IN ('YES', 'NO', 'UNKNOWN');
UPDATE price_records SET transport_included = 'UNKNOWN' WHERE transport_included IS NULL OR transport_included NOT IN ('YES', 'NO', 'UNKNOWN');
'''

OPTIONAL = '''
-- ===================== Khi có cảnh báo "Chưa thêm được ..." =====================
-- uq_price_records_dedup: tìm dòng giá trùng, xóa bớt rồi chạy lại file này.
-- SELECT material_id, supplier_id, date, quantity, source, count(*) FROM price_records
--   GROUP BY 1, 2, 3, 4, 5 HAVING count(*) > 1;
-- ck_supplier_materials_price_complete: dòng có giá nhưng thiếu mức giá hoặc ngày của giá.
-- SELECT * FROM supplier_materials WHERE base_price IS NOT NULL AND (price_level IS NULL OR price_date IS NULL);
-- ===================== TÙY CHỌN: dọn dữ liệu mẫu (bỏ dấu -- để chạy) =====================
-- Chỉ chạy khi đã có dữ liệu thật. Xóa vật liệu mẫu MAT_..., đại lý mẫu và toàn bộ dòng SAMPLE / SYNTHETIC.
-- DELETE FROM price_records WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM supplier_materials WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM suppliers WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM vehicles WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM materials WHERE material_id LIKE 'MAT\\_%' AND data_kind = 'SAMPLE';
'''


def column_spec(table, col) -> str:
    spec = DIALECT.ddl_compiler(DIALECT, CreateTable(table)).get_column_specification(col)
    if col.server_default is None:
        spec = spec.replace(" NOT NULL", "")   # bảng đã có dòng thì không thêm được cột NOT NULL không có mặc định
    for fk in col.foreign_keys:
        target = fk.column
        spec += f" REFERENCES {target.table.name} ({target.name})"
        if fk.ondelete:
            spec += f" ON DELETE {fk.ondelete}"
    return spec


def guarded(sql: str, label: str, errors: str) -> str:
    sql = sql.replace("'", "''")
    return (f"DO $$ BEGIN\n  EXECUTE '{sql}';\n"
            f"EXCEPTION\n  WHEN duplicate_object OR duplicate_table THEN NULL;\n"
            f"  WHEN {errors} THEN RAISE WARNING 'Chưa thêm được {label}: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';\n"
            f"END $$;")


def main() -> None:
    tables = list(Base.metadata.sorted_tables)
    out = [f"-- Nâng cấp database optimat lên lược đồ hiện tại ({len(tables)} bảng). Sinh tự động bởi scripts/build_upgrade_sql.py,",
           "-- không sửa tay. Không xóa bảng hay dữ liệu; chạy lại nhiều lần được.",
           "-- DBeaver: kết nối database optimat, mở file này, chạy cả script bằng Alt+X.",
           "-- Sau file này chạy sql/03_materials.sql (danh mục 93 vật liệu, họ vật liệu) rồi sql/05_rules.sql (bộ quy tắc).", "",
           "SET client_encoding = 'UTF8';",
           "SET client_min_messages = warning;   -- ẩn thông báo 'đã có, bỏ qua'; chỉ hiện cảnh báo cần xử lý", "",
           "-- ===================== 1. Bảng còn thiếu =====================", ""]
    for t in tables:
        out.append(str(CreateTable(t, if_not_exists=True).compile(dialect=DIALECT)).strip() + ";\n")

    out += ["-- ===================== 2. Cột còn thiếu =====================", ""]
    for t in tables:
        out.append(f"-- {t.name}")
        for c in t.columns:
            if not c.primary_key:
                out.append(f"ALTER TABLE {t.name} ADD COLUMN IF NOT EXISTS {column_spec(t, c)};")
        out.append("")

    out += ["-- ===================== 3. Cột được phép để trống =====================", ""]
    for t in tables:
        for c in t.columns:
            if c.nullable and not c.primary_key:
                out.append(f"ALTER TABLE {t.name} ALTER COLUMN {c.name} DROP NOT NULL;")
    out.append("")

    out += ["-- ===================== 4. Bổ sung giá trị cho dữ liệu cũ =====================", BACKFILL]

    out += ["-- ===================== 5. Ràng buộc =====================", ""]
    expected_constraints = []
    for t in tables:
        for con in sorted(t.constraints, key=lambda c: str(c.name)):
            if isinstance(con, (CheckConstraint, UniqueConstraint)):
                sql = str(AddConstraint(con).compile(dialect=DIALECT)).strip()
                name = re.search(r"ADD CONSTRAINT (\S+)", sql).group(1)
                expected_constraints.append((t.name, name))
                errors = "check_violation" if isinstance(con, CheckConstraint) else "unique_violation"
                out.append(guarded(sql, f"ràng buộc {name}", errors))
            elif isinstance(con, ForeignKeyConstraint):
                pass   # khóa ngoại tạo cùng bảng hoặc cùng cột ở mục 1, 2
    out.append("")

    out += ["-- ===================== 6. Chỉ mục =====================", ""]
    for t in tables:
        for idx in sorted(t.indexes, key=lambda i: i.name):
            sql = str(CreateIndex(idx, if_not_exists=True).compile(dialect=DIALECT)).strip()
            out.append(guarded(sql, f"chỉ mục {idx.name}", "unique_violation") if idx.unique else sql + ";")
            expected_constraints.append((t.name, idx.name))
    out.append("")

    out += ["-- ===================== 7. View =====================", VIEWS, OPTIONAL]

    cols = []
    for t in tables:
        for c in t.columns:
            udt = UDT[re.sub(r"\(.*\)", "", str(c.type.compile(dialect=DIALECT)))]
            cols.append(f"('{t.name}', '{c.name}', '{udt}')")
    cons = ", ".join(f"('{t}', '{n}')" for t, n in expected_constraints)
    out += ["-- ===================== 8. Kiểm tra: kết quả rỗng nghĩa là database đã đủ =====================",
            "WITH expected(table_name, column_name, udt_name) AS (VALUES",
            "  " + ",\n  ".join(cols) + "),",
            f"expected_con(table_name, con_name) AS (VALUES {cons})",
            "SELECT 'THIEU COT' AS van_de, e.table_name, e.column_name AS ten, e.udt_name AS can_co, NULL AS dang_co",
            "FROM expected e LEFT JOIN information_schema.columns c",
            "  ON c.table_schema = 'public' AND c.table_name = e.table_name AND c.column_name = e.column_name",
            "WHERE c.column_name IS NULL",
            "UNION ALL",
            "SELECT 'SAI KIEU', e.table_name, e.column_name, e.udt_name, c.udt_name",
            "FROM expected e JOIN information_schema.columns c",
            "  ON c.table_schema = 'public' AND c.table_name = e.table_name AND c.column_name = e.column_name",
            "WHERE c.udt_name <> e.udt_name",
            "UNION ALL",
            "SELECT 'THIEU RANG BUOC', x.table_name, x.con_name, NULL, NULL FROM expected_con x",
            "WHERE NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = x.con_name)",
            "  AND NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = x.con_name)",
            "ORDER BY 1, 2, 3;", "",
            "-- Số dòng của từng bảng",
            "SELECT table_name AS bang,",
            "       (xpath('/row/n/text()', query_to_xml(format('SELECT count(*) AS n FROM %I', table_name), false, true, '')))[1]::text::int AS so_dong",
            "FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1;", ""]
    path = ROOT / "sql/04_upgrade.sql"
    path.write_text("\n".join(out), encoding="utf8")
    print(f"Đã ghi {path.relative_to(ROOT)}: {len(tables)} bảng, {len(cols)} cột, {len(expected_constraints)} ràng buộc và chỉ mục")


if __name__ == "__main__":
    main()
