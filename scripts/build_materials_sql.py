"""Sinh sql/03_materials.sql từ data/catalog/materials_master.xlsx.

    python scripts/build_materials_sql.py

File SQL sinh ra chạy được nhiều lần: thêm cột và bảng nếu chưa có, rồi chèn hoặc cập nhật 75 vật liệu,
các phương án tường, quan hệ vật liệu và tên gọi khác. Sửa số liệu trong file Excel rồi chạy lại script này.
Script cũng ghi data/catalog/materials.csv, wall_systems.csv, material_aliases.csv (cùng số liệu, cho chế độ CSV),
để mã vật liệu khi nhận diện bản vẽ, tối ưu và tra giá luôn là mã của danh mục thật (GN01, AAC01...).
"""
import re
import sys
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.db.models import Base  # noqa: E402

XLSX = ROOT / "data/catalog/materials_master.xlsx"
OUT = ROOT / "sql/03_materials.sql"
CSV_DIR = ROOT / "data/catalog"
GROUP_IDS = {1: "be_tong_cot_thep", 2: "phan_tho", 3: "hoan_thien", 4: "khac_phap_ly", 5: "ket_cau_thep_bao_che"}
GROUPS = [("be_tong_cot_thep", 1, "Vật liệu bê tông cốt thép", "Xi măng, cốt liệu, nước, phụ gia, bê tông, cốt thép"),
          ("phan_tho", 2, "Vật liệu thi công phần thô", "Gạch xây, vữa, khối xây, chống thấm, giàn giáo, cốp pha"),
          ("hoan_thien", 3, "Vật liệu hoàn thiện", "Ốp lát, sơn, kính, thạch cao, gỗ, cửa, vật liệu hoàn thiện"),
          ("khac_phap_ly", 4, "Vật liệu khác và khung pháp lý", "Quy chuẩn, an toàn cháy, cách nhiệt, vật liệu xanh, bitum, composite, hợp quy"),
          ("ket_cau_thep_bao_che", 5, "Vật liệu kết cấu thép và bao che", "Thép hình, thép tấm, thép ống, liên kết, chống ăn mòn, tôn, panel, xà gồ")]
# Cột trong sheet "Vat lieu" (dòng 2 là tên cột cơ sở dữ liệu) -> cột của bảng materials
RENAME = {"group_id": "group", "lambda_design": "lambda_w_mk"}
MATERIAL_COLS = ["material_id", "group_id", "subgroup", "name", "family", "usage_text", "usage_role", "tier", "unit", "purchase_unit",
                 "unit_conversion", "length_mm", "width_mm", "height_mm", "price_priority", "needs_lambda", "lambda_design",
                 "lambda_source", "unit_weight_kg", "weight_source", "transport_volume_m3", "waste_pct", "waste_source",
                 "standards_text", "reference_brands", "tech_notes", "data_note"]
WALL_COLS = ["wall_system_id", "material_id", "wall_thickness_mm", "detect_class", "role", "masonry_thickness_mm", "norm_code",
             "units_per_m3", "mortar_m3_per_m3", "labor_day_per_m3", "unit_factor", "mortar_material_id", "mortar_density",
             "r0_reference", "norm_source", "note"]
REL_COLS = ["material_id", "relation_type", "related_material_id", "quantity", "quantity_unit", "source", "note"]


def lit(v) -> str:
    if v is None or v == "":
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(int(v)) if float(v).is_integer() else repr(round(float(v), 6))
    return "'" + str(v).strip().replace("'", "''") + "'"


def sheet_rows(wb, name: str) -> list[dict]:
    ws = wb[name]
    keys = [c.value for c in ws[2]]
    out = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] is None:
            continue
        out.append({k: v for k, v in zip(keys, row) if k and k != "—"})
    return out


def source_labels(wb) -> dict[str, str]:
    """S1 -> 'tên tài liệu [hạng]' để cột nguồn trong cơ sở dữ liệu đọc được mà không cần mở file Excel."""
    return {r["source_id"]: f"{r['document']} [{r['grade']}]" for r in sheet_rows(wb, "Nguon")}


def expand(text, labels: dict[str, str]):
    if not text:
        return None
    codes = re.findall(r"\b(S\d+|C)\s*\(", text)
    return "; ".join(labels.get(c, c) for c in codes)[:255] or None


def upsert(table: str, cols: list[str], values: list[str], key: str) -> str:
    quoted = ", ".join(f'"{c}"' for c in cols)
    sets = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in cols if c not in key.split(", "))
    conflict = ", ".join(f'"{k}"' for k in key.split(", "))
    return f'INSERT INTO "{table}" ({quoted}) VALUES ({", ".join(values)})\n  ON CONFLICT ({conflict}) DO UPDATE SET {sets};'


def export_csv(materials: list[dict], walls: list[dict], aliases: list[tuple[str, str]]) -> None:
    """Cùng dữ liệu với file SQL, ghi ra CSV cho chế độ không có PostgreSQL (data/catalog). Một nguồn: file Excel."""
    import pandas as pd
    mats = pd.DataFrame([{RENAME.get(c, c): m.get(c) for c in MATERIAL_COLS} for m in materials])
    mats["data_kind"] = "ACTUAL"
    mats.to_csv(CSV_DIR / "materials.csv", index=False)
    ws = pd.DataFrame([{c: w.get(c) for c in WALL_COLS} for w in walls])
    ws["detect_class"] = ws.detect_class.map(lambda v: None if v is None or v != v else str(int(float(v))))
    ws["data_kind"] = "ACTUAL"
    ws.to_csv(CSV_DIR / "wall_systems.csv", index=False)
    pd.DataFrame([{"alias": a, "material_id": m, "source": "tu khoa de xuat"} for a, m in aliases]).to_csv(
        CSV_DIR / "material_aliases.csv", index=False)
    print(f"Đã ghi data/catalog/materials.csv, wall_systems.csv, material_aliases.csv")


def main() -> None:
    wb = load_workbook(XLSX, data_only=True)
    labels = source_labels(wb)
    dialect = postgresql.dialect()
    tables = Base.metadata.tables
    out = ["-- OptiMat AI: danh mục 75 vật liệu, phương án tường, quan hệ vật liệu, tên gọi khác.",
           "-- Sinh tự động bằng scripts/build_materials_sql.py từ data/catalog/materials_master.xlsx. Không sửa tay.",
           "-- Chạy SAU 01_schema.sql (hoặc scripts/init_db.py). Chạy lại nhiều lần được: dòng đã có sẽ được cập nhật.",
           "-- DBeaver: mở file này, bấm Alt+X (Execute SQL Script) để chạy toàn bộ, không bôi đen từng đoạn.",
           "", "SET client_min_messages = warning;", "BEGIN;", "", "-- 1. Bổ sung cột cho bảng materials (bỏ qua nếu đã có)"]
    legacy = {"material_id", "name", "group", "thickness_mm", "unit", "qty_per_m2", "weight_kg_per_m2", "lambda_w_mk",
              "labor_days_per_m2", "data_kind"}
    for col in tables["materials"].columns:
        if col.name not in legacy:
            out.append(f'ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS "{col.name}" {col.type.compile(dialect=dialect)};')
    out += ["", "-- 2. Hai bảng mới (bỏ qua nếu đã có)"]
    for name in ("wall_systems", "material_relations"):
        ddl = str(CreateTable(tables[name]).compile(dialect=dialect)).strip().replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
        out.append(ddl + ";")
        for index in sorted(tables[name].indexes, key=lambda i: i.name):
            cols = ", ".join(f'"{c.name}"' for c in index.columns)
            out.append(f'CREATE INDEX IF NOT EXISTS "{index.name}" ON "{name}" ({cols});')
        out.append("")

    out.append("-- 3. Năm nhóm vật liệu bắt buộc")
    for g in GROUPS:
        out.append(upsert("material_groups", ["group_id", "sort_order", "name", "description"], [lit(v) for v in g], "group_id"))

    materials = sheet_rows(wb, "Vat lieu")
    out += ["", f"-- 4. Vật liệu: {len(materials)} dòng"]
    for m in materials:
        m["group_id"] = GROUP_IDS[int(m["group_id"])]
        m["needs_lambda"] = {"Có": True, "Không": False}.get(m.get("needs_lambda"))
        for k in ("lambda_source", "weight_source", "waste_source"):
            m[k] = expand(m.get(k), labels)
        cols = [RENAME.get(c, c) for c in MATERIAL_COLS] + ["data_kind"]
        out.append(upsert("materials", cols, [lit(m.get(c)) for c in MATERIAL_COLS] + ["'ACTUAL'"], "material_id"))

    walls = [w for w in sheet_rows(wb, "Phuong an tuong")]
    out += ["", f"-- 5. Phương án tường: {len(walls)} dòng (định mức theo 1 m3 khối xây)"]
    for w in walls:
        w["norm_source"] = expand(w.get("norm_source"), labels)
        out.append(upsert("wall_systems", WALL_COLS + ["data_kind"], [lit(w.get(c)) for c in WALL_COLS] + ["'ACTUAL'"], "wall_system_id"))

    rels = sheet_rows(wb, "Quan he")
    out += ["", f"-- 6. Quan hệ vật liệu: {len(rels)} dòng"]
    for r in rels:
        r["source"] = expand(r.get("source"), labels)
        out.append(upsert("material_relations", REL_COLS, [lit(r.get(c)) for c in REL_COLS], "material_id, related_material_id, relation_type"))

    aliases = [(a.strip(), m["material_id"]) for m in materials for a in (m.get("keywords") or "").split(";") if a.strip()]
    out += ["", f"-- 7. Tên gọi khác và từ khóa thu thập giá: {len(aliases)} dòng"]
    for alias, mid in aliases:
        out.append(f'INSERT INTO "material_aliases" ("alias", "material_id", "source") VALUES ({lit(alias)}, {lit(mid)}, \'tu khoa de xuat\')'
                   ' ON CONFLICT ("alias", "material_id") DO NOTHING;')

    out += ["", "-- 8. View tính sẵn định mức theo 1 m2 tường = định mức theo m3 x chiều dày khối xây",
            'CREATE OR REPLACE VIEW "v_wall_systems" AS',
            "SELECT w.wall_system_id, w.material_id, m.name AS material_name, m.unit, w.wall_thickness_mm, w.detect_class, w.role,",
            "       w.units_per_m3 * w.masonry_thickness_mm / 1000 * w.unit_factor AS qty_per_m2,",
            "       w.mortar_material_id, w.mortar_m3_per_m3 * w.masonry_thickness_mm / 1000 AS mortar_m3_per_m2,",
            "       w.labor_day_per_m3 * w.masonry_thickness_mm / 1000 AS labor_day_per_m2,",
            "       w.units_per_m3 * w.masonry_thickness_mm / 1000 * w.unit_factor * m.unit_weight_kg",
            "         + w.mortar_m3_per_m3 * w.masonry_thickness_mm / 1000 * w.mortar_density AS weight_kg_per_m2,",
            "       m.lambda_w_mk, w.r0_reference, w.norm_code, w.norm_source,",
            "       (w.units_per_m3 IS NOT NULL AND w.labor_day_per_m3 IS NOT NULL AND m.unit_weight_kg IS NOT NULL) AS ready_for_optimization",
            'FROM "wall_systems" w JOIN "materials" m ON m.material_id = w.material_id;',
            "", "COMMIT;", "",
            "-- Kiểm tra sau khi chạy:",
            "--   SELECT g.sort_order, g.name, count(*) FROM materials m JOIN material_groups g ON g.group_id = m.\"group\"",
            "--     WHERE m.tier IS NOT NULL GROUP BY 1, 2 ORDER BY 1;          -- 28, 23, 8, 7, 9",
            "--   SELECT * FROM v_wall_systems ORDER BY wall_system_id;",
            "",
            "-- Tùy chọn: xóa 6 vật liệu MẪU cũ (MAT_...) cùng giá và nguồn cung mẫu của chúng. Bỏ dấu -- rồi chạy riêng.",
            "-- DELETE FROM price_records WHERE material_id LIKE 'MAT\\_%';",
            "-- DELETE FROM supplier_materials WHERE material_id LIKE 'MAT\\_%';",
            "-- DELETE FROM materials WHERE material_id LIKE 'MAT\\_%';", ""]
    OUT.write_text("\n".join(out), encoding="utf8")
    export_csv(materials, walls, aliases)
    print(f"Đã ghi {OUT.relative_to(ROOT)}: {len(materials)} vật liệu, {len(walls)} phương án tường, {len(rels)} quan hệ, {len(aliases)} tên gọi khác")


if __name__ == "__main__":
    main()
