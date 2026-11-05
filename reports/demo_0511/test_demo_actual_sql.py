import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("build_demo_actual_sql", Path(__file__).with_name("build_demo_actual_sql.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    row = {"trang": "4", "nha_cung_cap": "Bãi nguồn", "ten": "Cát vàng", "don_vi": "m3", "gia": "600000",
           "material_id": "CA01", "quy_tac": "CBG04", "gia_theo_dvt_danh_muc": "600000", "ly_do": ""}
    materials = {"CA01": {"material_id": "CA01", "data_kind": "ACTUAL", "unit": "m³"}}
    rules = {r.rule_id: r for r in module.load_rules()}
    evidence = [{"material_id": "CA01", "supplier_id": module.supplier_id("Bãi nguồn"), "date": "2026-06-20",
                 "province": "Hà Nội", "unit": "m³", "unit_price": "600000", "quantity": "1", "vat_included": "NO",
                 "transport_included": "NO", "source": "Công bố giá 02.01/2026/CBGVL-SXD (Hà Nội), tr.4: Cát vàng (m3)"}]
    return row, materials, rules, evidence


def test_preserves_recorded_date_unit_source_and_missing_delivery():
    row, materials, rules, evidence = fixture()
    suppliers, prices, skipped = module.prepare([row, {"material_id": "", "ly_do": "chưa khớp"}], materials, rules, evidence)
    assert skipped == 1
    assert prices[0]["date"] == "2026-06-20"  # Không suy02.01 thành tháng01.
    assert prices[0]["source"] == evidence[0]["source"]
    assert prices[0]["price_level"] == "BULLETIN" and prices[0]["unit"] == "m³"
    assert suppliers[0]["lead_time_days"] is None and suppliers[0]["lat"] is None
    assert module.render_sql(suppliers, prices) == module.render_sql(*module.prepare([row], materials, rules, evidence)[:2])
    sql = module.render_sql(suppliers, prices)
    assert sql.count("ON CONFLICT DO NOTHING") == 2
    assert "supplier_materials" not in sql and sql.startswith("-- ACTUAL")


@pytest.mark.parametrize("field,value", [("data_kind", "SAMPLE"), ("gia_theo_dvt_danh_muc", "nan"),
                                          ("gia", "-1"), ("don_vi", "kg"), ("material_id", "UNKNOWN")])
def test_refuses_corrupt_or_unsourced_approved_row(field, value):
    row, materials, rules, evidence = fixture()
    row[field] = value
    with pytest.raises(ValueError):
        module.prepare([row], materials, rules, evidence)


def test_requires_metadata_evidence_and_refuses_duplicate_natural_key():
    row, materials, rules, evidence = fixture()
    with pytest.raises(ValueError, match="biên nhận"):
        module.prepare([row], materials, rules, [])
    with pytest.raises(ValueError, match="lặp khóa"):
        module.prepare([row, row], materials, rules, evidence)
    evidence[0]["unit"] = "tấn"
    with pytest.raises(ValueError, match="đơn vị"):
        module.prepare([row], materials, rules, evidence)


def test_sql_literals_do_not_allow_quotes_to_escape_data():
    assert module.literal("Bãi O'Brien; DROP TABLE suppliers; --") == "'Bãi O''Brien; DROP TABLE suppliers; --'"
    assert module.literal(None) == "NULL"
    with pytest.raises(ValueError):
        module.literal(float("inf"))


def test_read_evidence_only_accepts_actual_bulletin_without_executing_dump(tmp_path):
    path = tmp_path / "evidence.sql"
    path.write_text("DROP TABLE price_records;\n"
                    "INSERT INTO public.price_records (material_id, data_kind, price_level, source) VALUES ('CA01', 'ACTUAL', 'BULLETIN', 'O''Brien');\n"
                    "INSERT INTO public.price_records (material_id, data_kind, price_level, source) VALUES ('CA01', 'SAMPLE', 'DEALER', 'mẫu');\n", encoding="utf-8")
    assert module.read_evidence(path) == [{"material_id": "CA01", "data_kind": "ACTUAL", "price_level": "BULLETIN", "source": "O'Brien"}]
