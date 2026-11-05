"""Đối chiếu hồi quy cho các bảng ô gộp, đơn vị tiếp nối và đơn vị theo từng hàng/cột."""
import json
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from optimat.rough.quantity_knowledge import DEFAULT_PATH, QuantityKnowledge, resource_consumption

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from quantity_completion import parse_basis  # noqa: E402


@pytest.fixture(scope="module")
def data():
    norms = list(map(json.loads, (DEFAULT_PATH / "norms.jsonl").open(encoding="utf-8")))
    by_code = defaultdict(list)
    for r in norms:
        by_code[r["norm_code"]].append(r)
    refs = {r["table_id"]: r for r in map(json.loads, (DEFAULT_PATH / "reference_tables.jsonl").open(encoding="utf-8"))}
    return norms, by_code, refs


def test_all_original_missing_bases_are_resolved_with_source_evidence(data):
    norms, _, _ = data
    evidence = json.loads((DEFAULT_PATH / "basis_evidence.json").read_text(encoding="utf-8"))
    assert len(evidence) == 3271
    by_id = {r["record_id"]: r for r in norms}
    assert len({r["record_id"] for r in evidence}) == 3271
    for row in evidence:
        r = by_id[row["record_id"]]
        assert row["basis"] == r["basis"] and r["basis_evidence"] == row["evidence"]
        assert "missing_explicit_work_basis" not in r["review_issues"]
        assert row["evidence"]["quote"] and row["evidence"]["pdf_page"] >= 1
        if r["quantity"] is not None and r["value_type"] == "resource_quantity":
            assert Decimal(r["quantity_per_basis_unit"]) == Decimal(r["quantity"]) / Decimal(r["basis"]["quantity"])


def test_formwork_basis_is_hundred_square_meters_not_one(data):
    _, by_code, _ = data
    wood = next(r for r in by_code["11.31012"] if r["resource_name"] == "Gỗ ván khuôn 3cm")
    assert wood["basis"]["quantity"] == "100" and wood["basis"]["unit"] == "m2"
    assert wood["basis_evidence"]["pdf_page"] == 33
    assert resource_consumption(wood, "10", "m2", preview=True) == Decimal("0.300")


def test_experiment_is_per_indicator_not_per_sample(data):
    _, by_code, _ = data
    r = by_code["DA.01005"][0]
    assert r["basis"]["unit"] == "chỉ tiêu"
    assert r["basis_evidence"]["pdf_page"] == 4
    assert r["basis_evidence"]["method"] == "same_code_continuation"
    with pytest.raises(ValueError, match="đơn vị"):
        resource_consumption(r, "1", "mẫu", preview=True)


def test_unit_caption_before_page_break_is_not_lost(data):
    _, by_code, _ = data
    r = by_code["SB.32211"][0]
    assert r["pdf_page"] == 54 and r["basis_evidence"]["pdf_page"] == 53
    assert r["basis_evidence"]["method"] == "heading_caption_before_page_break"
    assert r["basis"]["unit"] == "m3"


def test_work_column_units_are_different_for_hard_and_metal_barriers(data):
    _, by_code, _ = data
    assert {r["basis"]["unit"] for r in by_code["AD.34110"]} == {"cái"}
    assert {r["basis"]["unit"] for r in by_code["AD.34130"]} == {"m"}


def test_height_and_span_axes_are_not_work_basis(data):
    _, by_code, _ = data
    assert {(r["basis"]["quantity"], r["basis"]["unit"]) for r in by_code["AG.22512"]} == {("100", "m2")}
    assert {r["basis"]["unit"] for r in by_code["AH.12222"]} == {"m3"}


def test_insulator_assembly_is_not_one_individual_insulator(data):
    _, by_code, _ = data
    assert by_code["BA.15201"][0]["basis"]["unit"] == "sứ"
    assert by_code["BA.15203"][0]["basis"]["unit"] == "sứ_nguyên_bộ"
    assert by_code["BA.15203"][0]["basis"]["qualifiers"] == ["2 sứ"]


def test_per_move_qualifier_must_not_be_dropped(data):
    _, by_code, _ = data
    r = by_code["AF.88431"][0]
    assert "lần_di_chuyển" in r["basis"]["unit"]
    with pytest.raises(ValueError, match="đơn vị"):
        resource_consumption(r, "1", "t", preview=True)


def test_all_558_tables_have_semantic_records_and_no_unresolved_resource_basis(data):
    _, _, refs = data
    assert len(refs) == 558
    assert sum(t["table_kind"] == "cost_rate" for t in refs.values()) == 33
    assert sum(t["table_kind"] == "document_index" for t in refs.values()) == 48
    for t in refs.values():
        assert t["column_paths"] and t["records"]
        assert t["enabled"] is False
        if t["table_kind"] in ("resource_matrix", "labor_matrix"):
            assert t["resources"]
            assert all(r["basis"] and r["basis_evidence"] for r in t["resources"])
        else:
            assert not t["resources"]


def test_loading_labor_is_not_material_consumption(data):
    _, by_code, refs = data
    table = refs["TT38_2026_3-p688-t2"]
    assert table["table_kind"] == "labor_matrix"
    brick = by_code["AM.11211"][0]
    cement = by_code["AM.11241"][0]
    assert brick["resource_unit"] == cement["resource_unit"] == "công"
    assert (brick["basis"]["quantity"], brick["basis"]["unit"]) == ("1000", "v")
    assert cement["basis"]["unit"] == "t"
    assert resource_consumption(brick, "1000", "v", preview=True) == Decimal("0.34")


def test_horizontal_mortar_mix_has_independent_resource_units(data):
    _, by_code, _ = data
    rows = by_code["12.10101"]
    assert {r["resource_name"]: r["quantity"] for r in rows} == {"Xi măng": "71", "Vôi cục": "118", "Cát": "1.27", "Nước": "221"}
    assert next(r for r in rows if r["resource_name"] == "Nước")["resource_unit"] == "l"


def test_cost_rates_and_catalog_indexes_are_reference_only(data):
    norms, _, refs = data
    assert not any(r["source_id"] == "TT38_2026_9" for r in norms)
    kb = QuantityKnowledge()
    assert kb.reference_table("TT38_2026_9-p11-t1") is None
    t = kb.reference_table("TT38_2026_9-p11-t1", include_candidates=True)
    assert t["table_kind"] == "cost_rate"
    assert any(f.get("value_type") == "percentage" for r in t["records"] for f in r["fields"])


@pytest.mark.parametrize("raw,amount,unit", [("100m3 đất nguyên thổ", "100", "m3"), ("1 chỉ tiêu", "1", "chỉ tiêu"), ("Cắt 10 chiếc", "10", "chiếc"), ("1m3", "1", "m3")])
def test_explicit_basis_parser(raw, amount, unit):
    b = parse_basis(raw)
    assert (b["quantity"], b["unit"]) == (amount, unit)


def test_resource_unit_header_is_not_mistaken_for_work_basis():
    from quantity_completion import local_basis
    t = {"context_before": "Mã hiệu Công tác Thành phần hao phí Đơn vị\nkg 1,0\nMáy thi công", "grid": [["Mã hiệu", "Đơn vị"], ["AB.123", "kg"]]}
    assert local_basis(t) is None
