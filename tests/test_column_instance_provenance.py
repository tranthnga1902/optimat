"""QA15: fixtures SYNTHETIC kiểm hợp đồng, không là đáp án ACTUAL đã kiểm."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from optimat.rough.columns import Column
from optimat.rough.structural_column_instances import (
    StructuralColumnInstance,
    allocated_local_columns,
    instance_column_works,
)
from optimat.rough.takeoff import RoughRequest


def instance(**changes):
    data = dict(instance_id="syn-4A-L2-L3", code="C-2", grid_x="4", grid_y="A",
                floor_key="L2-L3", z_from_mm=3150, z_to_mm=6750, b_mm=220, h_mm=220,
                top_slab_thickness_mm=120, top_slab_source="SYNTHETIC slab at 4/A",
                file="synthetic-source.dxf", sheet="SYNTHETIC sheet",
                layers=["synthetic-column"], handles=["SYN-A"],
                evidence=["SYNTHETIC section and level evidence"])
    return StructuralColumnInstance(**(data | changes))


def concrete(items):
    return [w for w in instance_column_works(items) if w.code == "COT"]


def test_same_code_keeps_grid_and_floor_instances_separate():
    items = [instance(), instance(instance_id="syn-4B-L2-L3", grid_y="B"),
             instance(instance_id="syn-4A-L3-L4", floor_key="L3-L4",
                      z_from_mm=6750, z_to_mm=10350)]
    works = concrete(items)
    assert len(works) == 3
    assert len({w.element for w in works}) == 3
    assert [w.plan for w in works] == ["L2-L3", "L2-L3", "L3-L4"]
    assert all(Decimal(w.quantity_detail.total_raw) == Decimal("0.168432") for w in works)


def test_one_instance_has_one_gross_and_one_slab_deduction():
    work = concrete([instance()])[0]
    rows = {r.row_id: r for r in work.quantity_detail.rows}
    assert Decimal(rows["gross"].raw_quantity) == Decimal("0.174240")
    assert Decimal(rows["top-slab"].raw_quantity) == Decimal("0.005808")
    assert rows["top-slab"].sign == -1
    assert Decimal(work.quantity_detail.total_raw) == Decimal("0.168432")
    assert len(rows) == 2  # Không thêm khoản trừ chiều cao dầm hoặc nhân SL loại.


@pytest.mark.parametrize("field", ["b_mm", "h_mm", "z_from_mm", "z_to_mm"])
def test_missing_section_or_span_stays_unknown(field):
    item = instance(**{field: None})
    work = concrete([item])[0]
    assert getattr(item, field) is None
    assert work.quantity is None and field in work.missing
    assert work.quantity_detail.total_raw is None


def test_missing_slab_keeps_known_gross_without_claiming_net():
    work = concrete([instance(top_slab_thickness_mm=None, top_slab_source=None)])[0]
    assert work.quantity is None and work.missing
    assert work.quantity_detail.total_raw is None
    gross = next(r for r in work.quantity_detail.rows if r.row_id == "gross")
    assert Decimal(gross.raw_quantity) == Decimal("0.174240")


def test_slab_value_without_source_is_rejected():
    with pytest.raises(ValidationError):
        instance(top_slab_source=None)


@pytest.mark.parametrize("changes", [dict(grid_y=None), dict(evidence=[])])
def test_ambiguous_position_or_missing_evidence_cannot_claim_complete(changes):
    work = concrete([instance(**changes)])[0]
    assert work.quantity is None and work.missing


def test_partial_kc_mapping_removes_only_proven_kt_instance():
    columns = [Column(id="KT-A", x=0, y=0, b_mm=220, h_mm=220),
               Column(id="KT-B", x=5000, y=0, b_mm=220, h_mm=220)]
    kc = instance(matched_plan="L2", matched_column_id="KT-A",
                  mapping_evidence="SYNTHETIC verified instance mapping")
    assert [c.id for c in allocated_local_columns("L2", columns, [kc])] == ["KT-B"]
    assert allocated_local_columns("L3", columns, [kc]) == columns
    assert allocated_local_columns("L2", columns, [instance()]) == columns


def test_partial_mapping_cannot_be_fabricated_from_code():
    with pytest.raises(ValidationError):
        instance(matched_plan="L2", matched_column_id="KT-A")


def test_request_roundtrip_preserves_instance_provenance_and_nulls():
    item = instance(z_from_mm=None, top_slab_thickness_mm=None, top_slab_source=None)
    request = RoughRequest(plans=[], structural_columns=[item])
    restored = RoughRequest.model_validate_json(request.model_dump_json())
    assert restored.structural_columns[0].model_dump() == item.model_dump()


def test_other_code_and_dimensions_are_computed_without_oracle_defaults():
    work = concrete([instance(instance_id="syn-other", code="Z-9", grid_x="9", grid_y="Q",
                              b_mm=300, h_mm=250, z_from_mm=-500, z_to_mm=2500,
                              top_slab_thickness_mm=150)])[0]
    assert Decimal(work.quantity_detail.total_raw) == Decimal("0.213750")
    assert "Z-9" in work.element


@pytest.mark.parametrize("start", [3150, 6000, 6749])
def test_overlapping_spans_rejected_even_with_different_ids_and_floor_names(start):
    with pytest.raises(ValidationError):
        RoughRequest(plans=[], structural_columns=[instance(), instance(
            instance_id="syn-overlap", floor_key="other-label", z_from_mm=start, z_to_mm=10350)])


def test_adjacent_spans_are_separate_and_roundtrip_exactly():
    items = [instance(), instance(instance_id="syn-adjacent", floor_key="L3-L4",
                                 z_from_mm=6750, z_to_mm=10350)]
    req = RoughRequest(plans=[], structural_columns=items)
    assert len(req.structural_columns) == 2
    assert RoughRequest.model_validate_json(req.model_dump_json()).structural_columns == items


def test_compute_partial_mapping_keeps_kt_on_other_floor():
    from optimat.catalog.repository import Catalog
    from optimat.rough.takeoff import PlanInput, compute_rough

    col = Column(id="KT-A", x=0, y=0, b_mm=220, h_mm=220)
    req = RoughRequest(plans=[PlanInput(name=f"Tầng {n}", height_mm=3600,
                                       walls=[], columns=[col]) for n in (2, 3)],
                       structural_columns=[instance(floor_key="T2", matched_plan="Tầng 2",
                           matched_column_id="KT-A", mapping_evidence="SYNTHETIC mapping")])
    works = [w for w in compute_rough(req, Catalog.from_csv()).works if w.code == "COT"]
    assert len(works) == 2
    assert next(w for w in works if w.plan == "Tầng 3").quantity is not None
    assert len([w for w in works if w.basis == "structural_instance"]) == 1
