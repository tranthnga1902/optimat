"""Kiểm tra ranh giới phiên bản, quy mô định mức và truy nguồn dữ liệu mới."""
import copy
import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from optimat.rough.quantity_knowledge import DEFAULT_PATH, QuantityKnowledge, resource_consumption


@pytest.fixture(scope="module")
def knowledge():
    return QuantityKnowledge()


def test_candidates_are_never_implicitly_enabled(knowledge):
    assert knowledge.norms_for_code("AK.21120", as_of=date(2026, 11, 4)) == []
    assert knowledge.rules_for_work("XAY", as_of=date(2025, 4, 1), purpose="estimate") == []


def test_real_plaster_table_and_decimal_precision(knowledge):
    rows = knowledge.norms_for_code("AK.21120", as_of=date(2026, 11, 4), include_candidates=True)
    mortar = next(r for r in rows if r["resource_name"] == "Vữa xi măng")
    assert mortar["source_id"] == "TT38_2026_3" and mortar["pdf_page"] == 589
    assert mortar["quantity"] == "0.017"
    assert mortar["conditions_raw"] == ["Chiều dày trát (cm)", "1,5"]
    assert resource_consumption(mortar, "10", "m2", preview=True) == Decimal("0.170")
    with pytest.raises(ValueError, match="chưa được duyệt"):
        resource_consumption(mortar, "10", "m2")


def test_real_mix_code_is_not_structural_concrete_coefficient(knowledge):
    rows = knowledge.norms_for_code("11.11321", as_of=date(2026, 11, 4), include_candidates=True)
    assert {r["resource_name"]: r["quantity"] for r in rows} == {
        "Xi măng": "225", "Cát vàng": "0.520", "Đá dăm": "0.848", "Nước": "191"}
    assert all(r["conditions_raw"]["grade"] == "100" for r in rows)
    assert all(r["basis"]["unit_raw"] == "m3 vữa bê tông" for r in rows)


def test_hundred_unit_basis_divides_instead_of_multiplies(knowledge):
    record = knowledge.norms_for_code("CH.11110", as_of=date(2026, 11, 4), include_candidates=True)[0]
    assert record["basis"]["quantity"] == "100"
    assert resource_consumption(record, "10", "m", preview=True) == Decimal("0.02")
    with pytest.raises(ValueError, match="đơn vị"):
        resource_consumption(record, "10", "m2", preview=True)


@pytest.mark.parametrize("quantity", ["NaN", "Infinity", "-1", "không phải số"])
def test_rejects_nonfinite_or_negative_work_quantity(knowledge, quantity):
    record = knowledge.norms_for_code("AK.21120", as_of=date(2026, 11, 4), include_candidates=True)[0]
    with pytest.raises(ValueError):
        resource_consumption(record, quantity, "m2", preview=True)


def test_percentage_and_unspecified_value_are_not_resource_quantities(knowledge):
    rows = knowledge.norms_for_code("AK.21120", as_of=date(2026, 11, 4), include_candidates=True)
    percentage = next(r for r in rows if r["value_type"] == "percentage")
    with pytest.raises(ValueError, match="phần trăm"):
        resource_consumption(percentage, "10", "m2", preview=True)
    missing = copy.deepcopy(rows[0])
    missing["quantity"] = None
    with pytest.raises(ValueError, match="thiếu số"):
        resource_consumption(missing, "10", "m2", preview=True)


def test_amendment_boundary_and_payment_scope(knowledge):
    def concrete(day, purpose="estimate"):
        return knowledge.rules_for_work("COT", as_of=day, purpose=purpose, include_candidates=True)
    before, after = concrete(date(2025, 3, 7)), concrete(date(2025, 3, 8))
    assert any(r["source_locator"] == "Phụ lục VI, II.5.4 bản gốc" for r in before)
    assert not any(r["source_locator"] == "Phụ lục VI, II.5.4 bản gốc" for r in after)
    assert any(r["source_id"] == "TT01_2025_CONGBAO" for r in after)
    assert not any(r["source_id"] == "TT01_2025_CONGBAO" for r in concrete(date(2025, 4, 1), "payment"))
    assert not any(r["source_id"] == "TT13_2021_1" for r in concrete(date(2026, 7, 1)))
    assert knowledge.norms_for_code("AK.21120", as_of=date(2026, 6, 30), include_candidates=True) == []


def test_outside_rough_work_is_not_returned_as_general_rule(knowledge):
    rules = knowledge.rules_for_work("XAY", as_of=date(2025, 4, 1), purpose="estimate", include_candidates=True)
    assert not any(r["work_group"] in ("duong", "mep", "coc", "go") for r in rules)
    opening = next(r for r in rules if r["work_group"] == "xay" and r["predicate"])
    assert opening["predicate"] == {"field": "opening_area_m2", "operator": "lt", "value": "0.25", "unit": "m2"}


def test_spaced_prefix_does_not_assign_both_columns_to_same_code(knowledge):
    def labor(code):
        rows = knowledge.norms_for_code(code, as_of=date(2026, 11, 4), include_candidates=True)
        return [r["quantity"] for r in rows if r["resource_kind"] == "labor"]
    assert labor("AF.11310") == ["1.19"]
    assert labor("AF.11410") == ["1.81"]


def test_multiline_resource_name_stays_with_its_own_quantity(knowledge):
    rows = knowledge.norms_for_code("BB.91601", as_of=date(2026, 11, 4), include_candidates=True)
    names = {r["resource_name"] for r in rows}
    assert "Thùng đun nước nóng kiểu liên tục" in names
    assert "Vật liệu khác" in names
    assert not any(name.startswith("kiểu liên tục Vật liệu") for name in names)


def test_thousand_separator_preserves_steel_quantity(knowledge):
    rows = knowledge.norms_for_code("AF.61621", as_of=date(2026, 11, 4), include_candidates=True)
    steel = next(r for r in rows if r["resource_name"] == "Thép tròn")
    assert steel["quantity_raw"] == "1.020"
    assert steel["quantity"] == "1020" and steel["number_format"] == "vi_dot_thousands"
    assert resource_consumption(steel, "1", "t", preview=True) == Decimal("1020")


def test_checksum_detects_changed_file(tmp_path):
    payload = "[]"
    (tmp_path / "measurement_rules.json").write_text(payload, encoding="utf-8")
    manifest = {"schema_version": "optimat.quantity-knowledge.v1", "files": {
        "measurement_rules.json": {"sha256": hashlib.sha256(payload.encode()).hexdigest()}}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    k = QuantityKnowledge(tmp_path)
    (tmp_path / "measurement_rules.json").write_text("[{}]", encoding="utf-8")
    with pytest.raises(ValueError, match="đã thay đổi hoặc hỏng"):
        k.rules_for_work("XAY", as_of=date(2026, 11, 4), purpose="estimate")


def test_json_pack_references_and_scalar_values():
    sources = {s["source_id"]: s for s in json.loads((DEFAULT_PATH / "sources.json").read_text(encoding="utf-8"))}
    tables = {}
    with (DEFAULT_PATH / "tables.jsonl").open(encoding="utf-8") as f:
        for line in f:
            t = json.loads(line)
            tables[t["table_id"]] = (t["source_id"], t["pdf_page"])
    seen = set()
    with (DEFAULT_PATH / "norms.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            assert row["record_id"] not in seen
            seen.add(row["record_id"])
            assert tables[row["table_id"]] == (row["source_id"], row["pdf_page"])
            assert row["source_sha256"] == sources[row["source_id"]]["sha256"]
            assert row["enabled"] is False
            if row["quantity"] is not None:
                value = Decimal(row["quantity"])
                assert value.is_finite() and value >= 0
            if row["value_type"] == "percentage":
                assert row["quantity_per_basis_unit"] is None
