"""G8-SUM SYNTHETIC: nội dung snapshot, lượng raw và coverage; không API/DB/CAD."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from optimat.rough.models import (ProjectParams, QuantityDetailRow, QuantityGroupingContext,
    QuantitySummary, WorkItem)
from optimat.rough.quantity_details import summarize
from optimat.rough.quantity_summary import build_quantity_summary, grouping_context, validate_quantity_summary
from optimat.rough.takeoff import RoughResult


def context(**kw):
    return QuantityGroupingContext(**(dict(concrete_grade="M250", lean_concrete_grade="M100", concrete_supply="site_mix",
        masonry_mortar_grade="M75", plaster_mortar_grade="M75", screed_mortar_grade="M75", formwork_type="go") | kw))


def work(label="A", raw="0.3225", legacy=.323, *, no_detail=False, method="box", sign=1,
         role="contribution", extra_rows=(), scope=True, level="components", **kw):
    unit = kw.get("unit", "m³")
    rows = [QuantityDetailRow(row_id="r1", label=label, unit=unit, raw_quantity=raw, sign=sign, role=role,
        method=method, sources=["Nguồn SYNTHETIC"], missing=[] if raw is not None else ["Chưa đo"]), *extra_rows]
    detail = None if no_detail else summarize(rows, unit, legacy, scope_complete=scope, detail_level=level)
    return WorkItem(**(dict(code="BE_TONG_LOT", name="Bê tông lót", unit=unit, element=label,
        source="manual", stage="mong", quantity=legacy, status="C", quantity_detail=detail) | kw))


def partial_case():
    ref = QuantityDetailRow(row_id="raw", label="Chỉ tham khảo", unit="m³", raw_quantity="100",
                            role="reference", method="source_quantity", sources=["Nguồn SYNTHETIC"])
    return [work(extra_rows=[ref]), work("B"), work("C", raw=None, legacy=None, status="D", scope=False),
            work("D", legacy=1, no_detail=True)]


def result(works, summary):
    return RoughResult(works=works, materials=[], intermediates=[], quantity_summary=summary)


def test_raw_known_partial_no_fallback_and_scoped_duplicate_row_ids():
    items = partial_case();out = build_quantity_summary(items, context())
    assert len(out.groups) == 1
    g = out.groups[0]
    assert g.member_work_keys == ["w:0", "w:1", "w:2", "w:3"]
    assert g.known_part_raw == "0.6450" and g.total_raw is None and not g.complete
    c = out.coverage
    assert (c.work_count, c.components, c.no_detail, c.quantity_complete_works, c.quantity_incomplete_works) == (4, 3, 1, 2, 2)
    assert (c.contribution_rows, c.known_contribution_rows, c.unknown_contribution_rows, c.reference_rows) == (3, 2, 1, 1)
    assert not c.complete_components
    assert any(r.work_key == "w:2" and r.row_id == "r1" for r in g.missing_work_refs)
    assert any(r.work_key == "w:3" and r.row_id is None for r in g.missing_work_refs)


def test_complete_raw_differs_from_rounded_legacy_sum():
    items = [work(), work("B")]
    out = build_quantity_summary(items, context())
    assert out.groups[0].total_raw == "0.6450" and sum(w.quantity for w in items) == .646
    assert out.groups[0].complete and out.coverage.complete_components
    assert result(items, out).quantity_summary == out


def test_geometry_methods_are_trace_not_specification_partition():
    out = build_quantity_summary([work(method="box"), work("B", method="prismoid"), work("C", method="area")], context())
    assert len(out.groups) == 1 and out.groups[0].calculation_methods == ["area", "box", "prismoid"]


@pytest.mark.parametrize("patch", [{"variant": "khác"}, {"unit": "m²"}, {"source": "structural"},
                                   {"basis": "bang_thong_ke"}, {"stage": "nen"}])
def test_incompatible_fields_are_not_merged(patch):
    out = build_quantity_summary([work(), work("B", **patch)], context())
    assert len(out.groups) == 2


def test_formwork_parent_families_not_merged():
    a = work(code="COP_PHA", unit="m²", formwork_of="COT")
    b = work("B", code="COP_PHA", unit="m²", formwork_of="SAN")
    assert len(build_quantity_summary([a, b], context()).groups) == 2


@pytest.mark.parametrize("ctx", [context(lean_concrete_grade=None), context(concrete_supply=None)])
def test_unknown_specification_isolates_without_changing_quantity_complete(ctx):
    out = build_quantity_summary([work(), work("B")], ctx)
    assert len(out.groups) == 2 and out.coverage.compatibility_pending_works == 2
    assert out.coverage.quantity_complete_works == 2
    assert all(g.compatibility == "isolated_unknown" and g.compatibility_reasons and g.complete for g in out.groups)


@pytest.mark.parametrize("code", ["DAO_DAT", "DAP_DAT", "COT_THEP"])
def test_unavailable_soil_or_steel_class_not_inferred_from_evidence(code):
    out = build_quantity_summary([work(code=code, evidence=["AF giả M100"]), work("B", code=code)], context())
    assert len(out.groups) == 2 and out.coverage.compatibility_pending_works == 2


def test_signed_amount_zero_and_reference_only():
    positive = work(raw="1", legacy=1)
    negative = work("B", raw="1", legacy=-1, sign=-1)
    out = build_quantity_summary([positive, negative], context())
    assert out.groups[0].known_part_raw == "0" and out.groups[0].total_raw == "0"
    ref = work(role="reference", scope=False)
    out = build_quantity_summary([ref], context())
    assert out.groups[0].known_part_raw is None and out.groups[0].total_raw is None
    assert out.coverage.contribution_rows == 0 and out.coverage.reference_rows == 1


def test_aggregate_quantity_complete_is_not_component_coverage():
    out = build_quantity_summary([work(level="aggregate")], context())
    assert out.groups[0].complete and out.coverage.quantity_complete_works == 1
    assert out.coverage.aggregate == 1 and not out.coverage.complete_components


def test_empty_is_not_full_and_has_no_fabricated_zero_total():
    out = build_quantity_summary([], context())
    assert out.groups == [] and out.coverage.work_count == 0 and not out.coverage.complete_components
    assert result([], out).quantity_summary == out


def test_long_decimal_precision_and_json_roundtrip():
    raw = "1.12345678901234567890123456789"
    item = work(raw=raw, legacy=0)
    out = build_quantity_summary([item, work("B", raw=".00000000000000000000000000001", legacy=0)], context())
    assert out.groups[0].total_raw == "1.12345678901234567890123456790"
    r = result([item, work("B", raw=".00000000000000000000000000001", legacy=0)], out)
    assert RoughResult.model_validate_json(r.model_dump_json()) == r


@pytest.mark.parametrize("field", ["hash", "sum", "membership", "group_key", "coverage", "context", "row_ref"])
def test_parent_rejects_stale_or_forged_summary_without_repair(field):
    items = partial_case();out = build_quantity_summary(items, context())
    data = out.model_dump()
    if field == "hash":data["quantity_snapshot_hash"] = "0" * 64
    elif field == "sum":data["groups"][0]["known_part_raw"] = "999"
    elif field == "membership":data["groups"][0]["member_work_keys"][0] = "w:999"
    elif field == "group_key":data["groups"][0]["key"]["source"] = "khác"
    elif field == "coverage":
        data["coverage"]["reference_rows"] += 1
    elif field == "context":data["context"]["lean_concrete_grade"] = "M200"
    else:data["groups"][0]["missing_work_refs"][0]["row_id"] = "missing-fake"
    copy = deepcopy(data)
    with pytest.raises(ValueError):
        result(items, QuantitySummary(**data))
    assert data == copy


def test_changed_work_order_or_raw_detail_invalidates_snapshot():
    items = [work(), work("B")];out = build_quantity_summary(items, context())
    with pytest.raises(ValueError):result(list(reversed(items)), out)
    changed = [work(raw="0.3226"), items[1]]
    with pytest.raises(ValueError):result(changed, out)


def test_summary_revalidates_mutable_parent_and_nested_receipts():
    item = work();item.status = "D"
    with pytest.raises(ValueError):build_quantity_summary([item], context())
    item = work();item.quantity_detail.rows[0].raw_quantity = "999"
    with pytest.raises(ValueError):build_quantity_summary([item], context())


def test_legacy_none_parent_cannot_claim_complete_detail_but_keeps_partial_known():
    r = QuantityDetailRow(row_id="r1", label="Phần biết", unit="m³", raw_quantity="1",
                          method="source_quantity", sources=["SYNTHETIC"])
    full = summarize([r], "m³", None, scope_complete=True)
    with pytest.raises(ValidationError):
        WorkItem(code="BE_TONG_LOT", name="Lót", unit="m³", quantity=None, quantity_detail=full)
    partial = summarize([r], "m³", None, scope_complete=False)
    item = WorkItem(code="BE_TONG_LOT", name="Lót", unit="m³", stage="mong", source="manual", quantity=None,
                    quantity_detail=partial, status="D", missing=["Còn thiếu phạm vi"])
    out = build_quantity_summary([item], context())
    assert item.quantity is None and out.groups[0].known_part_raw == "1"
    assert not out.groups[0].complete and out.groups[0].total_raw is None


def test_old_result_payload_has_no_summary_and_context_uses_exact_declared_params():
    old = RoughResult(works=[work(no_detail=True)], materials=[], intermediates=[])
    assert old.quantity_summary is None and RoughResult.model_validate_json(old.model_dump_json()) == old
    p = ProjectParams(concrete_grade="M300", lean_concrete_grade="M150", concrete_supply="ready_mix")
    ctx = grouping_context(p)
    assert ctx.concrete_grade == "M300" and ctx.lean_concrete_grade == "M150"
    assert set(ctx.model_dump()) == set(QuantityGroupingContext.model_fields)


def test_compute_integration_only_adds_summary_and_preserves_legacy(monkeypatch):
    from optimat.catalog.repository import Catalog
    from optimat.rough import takeoff
    from optimat.rough.models import FoundationItem
    p = ProjectParams(concrete_supply="ready_mix", lean_concrete_grade="M100", foundations=[FoundationItem(
        name="M1", count=2, length_mm=750, width_mm=2150, height_mm=500, lean_thickness_mm=100)])
    req = takeoff.RoughRequest(plans=[], params=p)
    cat = Catalog.from_csv(None)
    actual = takeoff.compute_rough(req, cat)
    assert actual.quantity_summary and any(g.known_part_raw == "0.3225" for g in actual.quantity_summary.groups)
    monkeypatch.setattr(takeoff, "build_quantity_summary", lambda *a: None)
    baseline = takeoff.compute_rough(req, cat)
    assert actual.model_dump(exclude={"quantity_summary"}) == baseline.model_dump(exclude={"quantity_summary"})
    assert RoughResult.model_validate_json(actual.model_dump_json()) == actual
