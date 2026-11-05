"""DTO/helper chi tiết phần thô; không chứng minh đã nối emitter hoặc phủ toàn phần thô."""
import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from optimat.rough.models import (DetailConversion, DetailFactor, FoundationItem, ProjectParams,
    QuantityDetailRow, WorkQuantityDetail, WorkItem)
from optimat.rough.quantity_details import finalize_quantity_details, lean_foundation_row, summarize


def row(**kw):
    return QuantityDetailRow(**(dict(row_id="r1", label="Dòng nguồn", unit="m³", raw_quantity="1",
                                    method="source_quantity", sources=["Nguồn SYNTHETIC"]) | kw))


def test_reference_and_signed_deduction_do_not_count_twice():
    rows = [row(raw_quantity="5"), row(row_id="r2", raw_quantity="2", sign=-1),
            row(row_id="raw", role="reference", raw_quantity="100")]
    out = summarize(rows, "m³", "3", scope_complete=True)
    assert (out.known_part_raw, out.total_raw, out.legacy_delta, out.complete) == ("3", "3", "0", True)


def test_zero_is_known_and_missing_is_not_zero():
    known = summarize([row(raw_quantity="0")], "m³", "0", scope_complete=True)
    unknown = summarize([row(raw_quantity=None, missing=["Chưa đo"])], "m³", None, scope_complete=True)
    assert known.total_raw == "0" and known.complete
    assert unknown.known_part_raw is None and unknown.total_raw is None and not unknown.complete


@pytest.mark.parametrize("scope_complete,missing", [(False, []), (True, ["Còn thiếu phạm vi"])])
def test_known_part_does_not_prove_complete(scope_complete, missing):
    out = summarize([row(raw_quantity=".24", missing=missing)], "m³", ".24", scope_complete=scope_complete)
    assert Decimal(out.known_part_raw) == Decimal(".24") and out.total_raw is None and not out.complete


@pytest.mark.parametrize("patch", [
    {"complete": False}, {"total_raw": "9"}, {"known_part_raw": "9"}, {"legacy_delta": "1"},
    {"scope_complete": False}, {"total_raw": None}, {"known_part_raw": "NaN"},
])
def test_direct_constructor_cannot_forge_totals(patch):
    good = summarize([row()], "m³", "1", scope_complete=True).model_dump()
    with pytest.raises(ValidationError):
        WorkQuantityDetail(**(good | patch))


def test_direct_complete_rejected_when_one_required_row_unknown():
    good = summarize([row()], "m³", "1", scope_complete=True).model_dump()
    good["rows"].append(row(row_id="missing", raw_quantity=None, missing=["Chưa có"] ).model_dump())
    with pytest.raises(ValidationError):
        WorkQuantityDetail(**good)


def test_mixed_unit_duplicate_id_and_reference_only():
    with pytest.raises(ValueError):
        summarize([row(unit="m²")], "m³", None, scope_complete=True)
    with pytest.raises(ValueError):
        summarize([row(), row()], "m³", None, scope_complete=True)
    out = summarize([row(unit="kg", role="reference")], "m³", None, scope_complete=True)
    assert out.total_raw is None and out.known_part_raw is None and not out.complete


@pytest.mark.parametrize("factor", ["NaN", "Infinity", "-Infinity", "0", "-1", "không phải số"])
def test_conversion_must_be_finite_positive(factor):
    with pytest.raises(ValueError):
        DetailConversion(from_unit="m", to_unit="100m", factor=factor, source="Quy đổi chính xác")


@pytest.mark.parametrize("field", ["from_unit", "to_unit", "source"])
def test_conversion_requires_units_and_source(field):
    with pytest.raises(ValidationError):
        DetailConversion(**(dict(from_unit="m", to_unit="100m", factor=".01", source="Quy đổi vật lý") | {field: " "}))


def test_exact_conversion_is_applied_once():
    r = row(unit="100m", raw_quantity="3.08", conversion=DetailConversion(
        from_unit="m", to_unit="100m", factor=".01", source="308m / 100; ca đơn vị, ngoài công tác ép cọc"))
    assert summarize([r], "100m", None, scope_complete=True).total_raw == "3.08"
    with pytest.raises(ValidationError):
        row(unit="m³", conversion=r.conversion)


@pytest.mark.parametrize("field", ["name", "unit", "meaning", "source"])
def test_factors_have_meaning_and_source(field):
    with pytest.raises(ValidationError):
        DetailFactor(**(dict(name="k", value="1.02", unit="1", meaning="Hệ số được khai báo", source="Nguồn") | {field: " "}))


def test_unknown_factor_keys_and_nonfinite_values_rejected():
    with pytest.raises(ValidationError):
        DetailFactor(name="k", value="NaN", unit="1", meaning="Hệ số", source="Nguồn")
    with pytest.raises(ValidationError):
        DetailFactor(name="k", value="1", unit="1", meaning="Hệ số", source="Nguồn", guessed=True)


def test_count_repetition_are_display_metadata_not_second_multiplier():
    r = row(raw_quantity="1.44", dimensions=dict(label="D1", source="Kích thước đã tính vào lượng",
        count=2, repetitions=3, length_m=4, width_m=.2, concrete_height_m=.3))
    assert summarize([r], "m³", None, scope_complete=True).total_raw == "1.44"


def test_long_decimal_sum_and_delta_do_not_fall_back_to_precision28():
    raw = "1.12345678901234567890123456789"
    out = summarize([row(raw_quantity=raw)], "m³", "0", scope_complete=True)
    assert out.total_raw == raw and out.legacy_delta == raw
    assert WorkQuantityDetail.model_validate_json(out.model_dump_json()) == out


def test_missing_reason_and_negative_magnitude_rejected():
    with pytest.raises(ValidationError):
        row(raw_quantity=None)
    with pytest.raises(ValidationError):
        row(raw_quantity="-1")


def test_lean_hook_receives_pre_round_quantity():
    f = FoundationItem(name="DC-1", count=2, lean_thickness_mm=100)
    base = SimpleNamespace(length_mm=750, width_mm=2150)
    q = f.count * base.length_mm * base.width_mm * f.lean_thickness_mm / 1e9
    r = lean_foundation_row(f, base, row_id="lean-1", raw_quantity=q)
    out = summarize([r], "m³", round(q, 3), scope_complete=True)
    assert out.total_raw == "0.3225" and out.legacy_delta == "-0.0005"
    assert r.dimensions.count == 2 and r.dimensions.repetitions == 1


def test_m1_reference_nine_rows_and_material_products():
    f = json.loads((Path(__file__).resolve().parents[1] / "reports/g8_detail/staging/M1_AF11110_REFERENCE.json").read_text(encoding="utf-8"))
    rows = [QuantityDetailRow(**r) for r in f["rows"]]
    out = summarize(rows, "m³", "3.251", scope_complete=True)
    assert len(rows) == 9 and out.total_raw == f["total_raw"] == "3.2515"
    assert out.legacy_delta == "0.0005"
    for material in f["materials"]:
        assert Decimal(out.total_raw) * Decimal(material["rate_per_m3"]) == Decimal(material["quantity_from_raw"])
    assert not f["production_catalog_changed"] and not f["independent_ground_truth_confirmed"]


@pytest.mark.parametrize("quantity", [None, 0, 1.25])
def test_old_work_payload_without_detail_keeps_quantity_and_status(quantity):
    w = WorkItem(code="DAM", name="Dầm", unit="m³", quantity=quantity, status="C")
    assert w.quantity_detail is None and w.quantity == quantity and w.status == "C"
    assert WorkItem.model_validate_json(w.model_dump_json()) == w


def test_work_detail_roundtrip_and_current_quantity_unchanged():
    d = summarize([row(raw_quantity=".3225")], "m³", ".323", scope_complete=True)
    w = WorkItem(code="BE_TONG_LOT", name="Lót", unit="m³", quantity=.323, quantity_detail=d, status="C")
    out = WorkItem.model_validate_json(w.model_dump_json())
    assert out == w and out.quantity == .323 and out.quantity_detail.total_raw == "0.3225"
    assert out.status == "C" and out.quantity_detail.legacy_delta == "-0.0005"


@pytest.mark.parametrize("quantity,unit", [(2, "m³"), (None, "m³"), (1, "m²")])
def test_attached_detail_must_match_work_unit_and_legacy(quantity, unit):
    detail = summarize([row()], "m³", "1", scope_complete=True)
    with pytest.raises(ValidationError):
        WorkItem(code="DAM", name="Dầm", unit=unit, quantity=quantity, quantity_detail=detail)


@pytest.mark.parametrize("raw", [None, "1"])
def test_missing_reason_cannot_be_only_whitespace(raw):
    with pytest.raises(ValidationError):
        row(raw_quantity=raw, missing=[" "])


@pytest.mark.parametrize("status,missing", [("D", []), ("C", ["Chưa xác nhận phạm vi"]),
                                          (None, ["Chưa có đủ căn cứ"])])
def test_incomplete_parent_cannot_claim_complete_detail(status, missing):
    detail = summarize([row()], "m³", "1", scope_complete=True)
    with pytest.raises(ValidationError):
        WorkItem(code="DAM", name="Dầm", unit="m³", quantity=1, status=status,
                 missing=missing, quantity_detail=detail)


def test_incomplete_parent_keeps_known_part_and_legacy_unchanged():
    detail = summarize([row()], "m³", "1", scope_complete=False)
    w = WorkItem(code="DAM", name="Dầm", unit="m³", quantity=1, status="D",
                 missing=["Chưa xác nhận phạm vi"], quantity_detail=detail)
    assert w.quantity == 1 and w.status == "D" and w.missing == ["Chưa xác nhận phạm vi"]
    assert w.quantity_detail.known_part_raw == "1" and w.quantity_detail.total_raw is None
    assert not w.quantity_detail.complete
    assert WorkItem.model_validate_json(w.model_dump_json()) == w


def lean_params(**kw):
    f = FoundationItem(**(dict(name="DC-1", count=2, length_mm=750, width_mm=2150, height_mm=500,
        lean_thickness_mm=100, source="SYNTHETIC/chi tiết móng DC-1") | kw))
    return ProjectParams(foundations=[f], concrete_supply="ready_mix", lean_concrete_grade="M100")


@pytest.mark.parametrize("count,raw,legacy", [(2, "0.3225", .323), (0, "0.0", 0)])
def test_lean_emitter_captures_pre_round_once_with_actual_source(count, raw, legacy):
    from optimat.rough.foundations import foundation_works
    works, _ = foundation_works(lean_params(count=count))
    w = next(w for w in works if w.code == "BE_TONG_LOT")
    assert w.quantity == legacy and w.quantity_detail.total_raw == raw
    r = w.quantity_detail.rows[0]
    assert r.dimensions.count == count and r.dimensions.repetitions == 1
    assert "SYNTHETIC/chi tiết móng DC-1" in r.sources[0]
    assert all(x.quantity_detail is None for x in works if x.code != "BE_TONG_LOT")


def test_lean_missing_geometry_stays_unknown_not_zero():
    from optimat.rough.foundations import foundation_works
    works, _ = foundation_works(lean_params(length_mm=None))
    w = next(w for w in works if w.code == "BE_TONG_LOT")
    assert w.quantity is None and w.missing == ["dài, rộng móng"]
    assert w.quantity_detail.known_part_raw is None and w.quantity_detail.total_raw is None
    assert w.quantity_detail.rows[0].raw_quantity is None and w.quantity_detail.rows[0].missing


def test_negative_raw_does_not_change_legacy_clamp_or_fake_contribution():
    from optimat.rough.foundations import foundation_works
    works, _ = foundation_works(lean_params(count=-2))
    w = next(w for w in works if w.code == "BE_TONG_LOT")
    assert w.quantity == 0
    assert w.quantity_detail.detail_level == "unavailable" and w.quantity_detail.total_raw is None
    assert w.quantity_detail.rows[0].role == "reference" and w.quantity_detail.rows[0].sign == -1
    assert w.quantity_detail.rows[0].raw_quantity == "0.3225"


@pytest.mark.parametrize("status,missing", [("D", []), ("C", ["Chưa chốt phạm vi"]), ("C", [])])
def test_finalize_after_parent_status_mutation_preserves_legacy(status, missing):
    detail = summarize([row(raw_quantity="0")], "m³", "0", scope_complete=True)
    w = WorkItem(code="DAM", name="Dầm", unit="m³", quantity=0, status="C", quantity_detail=detail)
    # Mô phỏng assign_status/net pipeline: assignment/model_copy không tự chạy validator.
    w.status, w.missing = status, missing
    final = finalize_quantity_details([w])[0]
    assert final.quantity == 0 and final.status == status and final.missing == missing
    assert final.quantity_detail.known_part_raw == "0"
    if status == "D" or missing:
        assert not final.quantity_detail.complete and final.quantity_detail.total_raw is None
    else:
        assert final.quantity_detail.complete and final.quantity_detail.total_raw == "0"
    assert WorkItem.model_validate_json(final.model_dump_json()) == final


@pytest.mark.parametrize("mutation", [{"quantity": 2}, {"quantity": None}, {"unit": "m²"}])
def test_finalize_rejects_changed_quantity_or_unit_instead_of_relabeling_gross(mutation):
    w = WorkItem(code="DAM", name="Dầm", unit="m³", quantity=1,
                 quantity_detail=summarize([row()], "m³", "1", scope_complete=True))
    mutated = w.model_copy(update=mutation)
    with pytest.raises(ValueError, match="đã đổi sau capture"):
        finalize_quantity_details([mutated])
    assert mutated.quantity == mutation.get("quantity", 1) and mutated.unit == mutation.get("unit", "m³")


def test_finalize_revalidates_nested_dump_not_model_instance():
    w = WorkItem(code="DAM", name="Dầm", unit="m³", quantity=1,
                 quantity_detail=summarize([row()], "m³", "1", scope_complete=True))
    w.quantity_detail.rows[0].raw_quantity = "2"  # cache total cũ không được tự bù theo raw mới
    with pytest.raises(ValueError):
        finalize_quantity_details([w])


def test_finalize_does_not_upgrade_unconfirmed_scope_and_skips_uncovered_works():
    w = WorkItem(code="DAM", name="Dầm", unit="m³", quantity=1, status="C",
                 quantity_detail=summarize([row()], "m³", "1", scope_complete=False))
    other = WorkItem(code="COT", name="Cột", unit="m³", quantity=2, status="C")
    final = finalize_quantity_details([w, other])
    assert not final[0].quantity_detail.complete and final[0].quantity_detail.total_raw is None
    assert final[1] is other and other.quantity_detail is None


def test_lean_pipeline_totals_status_materials_match_without_detail(monkeypatch):
    from optimat.catalog.repository import Catalog
    from optimat.rough import takeoff
    req = takeoff.RoughRequest(plans=[], params=lean_params())
    cat = Catalog.from_csv(None)
    with_detail = takeoff.compute_rough(req, cat)
    producer = takeoff.foundation_works
    def without_details(params):
        works, warnings = producer(params)
        return [w.model_copy(update={"quantity_detail": None}) for w in works], warnings
    monkeypatch.setattr(takeoff, "foundation_works", without_details)
    baseline = takeoff.compute_rough(req, cat)
    actual = with_detail.model_dump(exclude={"quantity_summary"})
    for item in actual["works"]:
        item["quantity_detail"] = None
    assert actual == baseline.model_dump(exclude={"quantity_summary"})  # toàn payload legacy, gồm totals/materials/status/giá
    lean = next(w for w in with_detail.works if w.code == "BE_TONG_LOT")
    assert lean.quantity == .323 and lean.quantity_detail.total_raw == "0.3225"
