"""P02 SYNTHETIC: raw detail không đổi phép tính legacy, không CAD/DB/HTTP."""
from decimal import Decimal

import pytest

from optimat.rough import areas
from optimat.rough.areas import PlanGeometry, PlanParams, Room
from optimat.rough.models import GroundLayer, ProjectParams, WorkItem


def params(**kw):
    return ProjectParams(**(dict(slab_thickness_mm=100, screed_thickness_mm=30,
        waterproof_upturn_mm=100) | kw))


def run(geom=None, p=None, **plan_kw):
    geom = geom or PlanGeometry(closed=True, outline_area_m2=20, usable_area_m2=15)
    return areas.area_works(geom, p or params(), PlanParams(**(dict(name="TẦNG 2", void_area_m2=0) | plan_kw)))


def one(works, code):
    return next(w for w in works if w.code == code)


@pytest.mark.parametrize("void", [None, 0, 2])
def test_slab_gross_deduction_unknown_zero_and_actual_aggregate(void):
    works, _ = run(void_area_m2=void)
    slab, cp = one(works, "SAN"), one(works, "COP_PHA")
    assert slab.quantity == pytest.approx((20 - (void or 0)) * .1)
    d = slab.quantity_detail
    assert [r.sign for r in d.rows if r.role == "contribution"] == [1, -1]
    assert d.rows[1].dimensions.area_m2 == void
    assert d.rows[-1].role == "reference" and d.rows[-1].raw_quantity == str((20 - (void or 0)) * 100 / 1000)
    if void is None:
        assert d.rows[1].raw_quantity is None and d.rows[1].missing
        assert Decimal(d.known_part_raw) == 2 and d.total_raw is None and not d.complete
        assert cp.quantity_detail.total_raw is None
    else:
        assert Decimal(d.total_raw) == Decimal(str(20 - void)) / 10 and d.complete
        assert Decimal(cp.quantity_detail.total_raw) == 20 - void
    assert WorkItem.model_validate_json(slab.model_dump_json()) == slab


def test_void_larger_than_outline_keeps_legacy_clamp_but_not_fake_complete():
    works, _ = run(void_area_m2=25)
    slab = one(works, "SAN")
    assert slab.quantity == 0 and slab.missing == []
    assert slab.quantity_detail.total_raw is None and not slab.quantity_detail.complete
    assert Decimal(slab.quantity_detail.known_part_raw) == Decimal("-.5")
    assert slab.quantity_detail.rows[1].missing


@pytest.mark.parametrize("t", [None, 0])
def test_thickness_none_and_zero_keep_legacy_branch_without_changing_geometry(t):
    works, _ = run(p=params(slab_thickness_mm=t))
    slab = one(works, "SAN")
    assert slab.quantity is None and slab.missing == ["chiều dày sàn"]
    dimension = slab.quantity_detail.rows[0].dimensions
    assert dimension.thickness_m == (None if t is None else 0)
    assert slab.quantity_detail.total_raw is None
    assert one(works, "COP_PHA").quantity_detail.complete  # CP diện tích không phụ thuộc dày BT


def test_ground_layers_and_missing_structure_are_distinct_from_foundation_lean():
    layers = [GroundLayer(kind="NEN_DEM_CAT", thickness_mm=200),
              GroundLayer(kind="BE_TONG_LOT", thickness_mm=100), GroundLayer(kind="BE_TONG_LOT", thickness_mm=50)]
    works, _ = run(p=params(ground_layers=layers), is_ground=True)
    assert not any(w.code == "SAN" for w in works)
    lots = [w for w in works if w.code == "BE_TONG_LOT"]
    assert [w.quantity for w in lots] == [1.5, .75]
    assert [w.quantity_detail.rows[0].label for w in lots] == ["nền tầng trệt lớp 2: BE_TONG_LOT", "nền tầng trệt lớp 3: BE_TONG_LOT"]
    assert all(w.quantity_detail.rows[0].row_id == "area:quantity" for w in lots)  # scoped work, không dedup r1 toàn cục
    missing, _ = run(p=params(ground_layers=[]), is_ground=True)
    for code in ["NEN_DEM_CAT", "BE_TONG_LOT"]:
        w = one(missing, code)
        assert w.quantity is None and w.quantity_detail.known_part_raw is None and w.quantity_detail.rows[0].missing


def test_screed_quantity_stays_area_when_thickness_missing():
    works, _ = run(p=params(screed_thickness_mm=None))
    w = one(works, "CAN_NEN")
    assert w.unit == "m²" and w.quantity == 15 and w.missing == ["chiều dày cán nền"]
    assert Decimal(w.quantity_detail.known_part_raw) == 15 and w.quantity_detail.total_raw is None


def test_wc_float_aggregate_is_reference_without_residual():
    geom = PlanGeometry(closed=True, outline_area_m2=20, usable_area_m2=15,
                        rooms=[Room(kind="WET", label="WC", area_m2=2.1, perimeter_m=8)])
    works, _ = run(geom)
    w = one(works, "CHONG_THAM");d = w.quantity_detail
    assert w.quantity == 2.9 and d.total_raw == "2.9"
    assert [(r.raw_quantity, r.role) for r in d.rows] == [("2.1", "contribution"), ("0.8", "contribution"),
                                                       ("2.9000000000000004", "reference")]
    assert d.legacy_delta == "0.0" and len(d.rows) == 3


def test_wc_unknown_upturn_keeps_known_floor_and_does_not_use_fallback_zero():
    geom = PlanGeometry(closed=True, outline_area_m2=20, usable_area_m2=15,
                        rooms=[Room(kind="WET", label="WC", area_m2=2.1, perimeter_m=8)])
    works, _ = run(geom, p=params(waterproof_upturn_mm=None))
    w = one(works, "CHONG_THAM")
    assert w.quantity is None and w.quantity_detail.known_part_raw == "2.1"
    assert w.quantity_detail.rows[1].raw_quantity is None and w.quantity_detail.total_raw is None


def test_balcony_zero_and_unknown_preserve_existing_non_emitted_branch():
    for value in [None, 0]:
        works, _ = run(balcony_area_m2=value)
        assert not any(w.code == "CHONG_THAM" for w in works)
    works, _ = run(balcony_area_m2=4.25)
    w = one(works, "CHONG_THAM")
    assert w.quantity == 4.25 and w.quantity_detail.total_raw == "4.25"


@pytest.mark.parametrize("geom,plan_kw", [
    (PlanGeometry(closed=True, outline_area_m2=20, usable_area_m2=15), {}),
    (PlanGeometry(closed=True, outline_area_m2=20, usable_area_m2=15, hull=True), {}),
    (PlanGeometry(closed=False), dict(outline_area_m2=23.5, usable_area_m2=18.2)),
])
def test_legacy_payload_and_warnings_unchanged_with_or_without_detail(monkeypatch, geom, plan_kw):
    actual, warnings = run(geom, **plan_kw)
    monkeypatch.setattr(areas, "area_detail", lambda work, *a, **kw: work)
    baseline, old_warnings = run(geom, **plan_kw)
    assert warnings == old_warnings
    assert [w.model_dump(exclude={"quantity_detail"}) for w in actual] == [w.model_dump(exclude={"quantity_detail"}) for w in baseline]


def test_pipeline_parent_c_and_ledger_partial_remain_distinct(monkeypatch):
    from optimat.catalog.repository import Catalog
    from optimat.rough.beams import Beam
    from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough
    req = RoughRequest(params=params(concrete_grade="M250", concrete_supply="ready_mix", formwork_type="go"),
        plans=[PlanInput(name="TẦNG 2", height_mm=3000, walls=[], outline_area_m2=20, usable_area_m2=15, void_area_m2=None,
            beams=[Beam(id="D1", source="manual", x1=0, y1=0, x2=4000, y2=0, b_mm=200, d_mm=400)])])
    cat = Catalog.from_csv(None)
    actual = compute_rough(req, cat)
    slab = one(actual.works, "SAN")
    assert slab.status == "C" and slab.quantity == 2 and not slab.quantity_detail.complete
    assert slab.quantity_detail.total_raw is None
    deductions = [w for w in actual.works if w.formwork_of == "SAN" and w.quantity is not None and w.quantity < 0]
    assert deductions and all(w.quantity_detail is None for w in deductions)  # CP âm ngoài P02
    monkeypatch.setattr(areas, "area_detail", lambda work, *a, **kw: work)
    baseline = compute_rough(req, cat)
    dumped = actual.model_dump(exclude={"quantity_summary"})
    for w in dumped["works"]:w["quantity_detail"] = None
    assert dumped == baseline.model_dump(exclude={"quantity_summary"})  # nguồn/status/totals/materials/giá không đổi
