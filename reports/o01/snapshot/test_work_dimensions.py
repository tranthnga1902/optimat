"""Kích thước SYNTHETIC có nguồn, không dùng metadata làm khối lượng net hoặc độ chính xác thực."""
import json
import math

import pytest
from pydantic import ValidationError

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewWall
from optimat.rough.areas import PlanGeometry, PlanParams, area_works
from optimat.rough.beams import Beam, beam_works
from optimat.rough.columns import column_works, Column, schedule_column_works
from optimat.rough.foundations import foundation_works, _neg
from optimat.rough.models import FoundationItem, FootingTier, ProjectParams, WorkDimensions, WorkItem
from optimat.rough.rebar import RebarRow
from optimat.rough.secondary import LinearMember, roof_works
from optimat.rough.stairs import Stair, stair_works
from optimat.rough.steel import schedule_works, steel_works
from optimat.rough.structural import ColumnSpan
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough


@pytest.fixture(scope="module")
def catalog():
    return Catalog.from_csv(None)


def one(works, code):
    return next(w for w in works if w.code == code)


def test_old_payload_and_null_zero_meanings_roundtrip():
    old = WorkItem(code="DAM", name="dầm", unit="m³")
    assert old.dimensions == []
    d = WorkDimensions(label="SYNTHETIC", count=0, area_m2=0, opening_area_m2=None, source="nhập tay")
    assert d.count == 0 and d.area_m2 == 0
    assert d.missing_fields == ["opening_area_m2"]
    assert "length_m" in d.not_applicable_fields and "area_m2" not in d.not_applicable_fields
    assert WorkDimensions.model_validate_json(d.model_dump_json()).model_dump() == d.model_dump()
    assert d.repetitions == 1


@pytest.mark.parametrize("field", ["count", "length_m", "top_length_m", "slope_length_m", "diameter_m", "area_m2"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_metadata_rejects_nonfinite_instead_of_zero(field, value):
    with pytest.raises(ValidationError):
        WorkDimensions(label="SYNTHETIC", source="đầu vào chưa hợp lệ", **{field: value})


def test_beam_net_cut_full_height_and_mixed_sources_are_distinct():
    b = Beam(id="D1", x1=0, y1=0, x2=4000, y2=0, b_mm=None, d_mm=400, cut_mm=200, source="structural")
    works, _ = beam_works("T2", [b], ProjectParams(beam_width_mm=200, slab_thickness_mm=100))
    w = one(works, "DAM"); d = w.dimensions[0]
    assert w.quantity == pytest.approx(0.228)
    assert one(works, "COP_PHA").quantity == pytest.approx(3.04)
    assert (d.gross_length_m, d.deducted_length_m, d.length_m) == (4, 0.2, 3.8)
    assert (d.height_m, d.concrete_height_m) == pytest.approx((0.4, 0.3))
    assert "đã trừ giao 0.2" in d.note and "Dài sau trừ giao 0.2" not in d.note
    assert d.field_sources["width_m"] == "ProjectParams.beam_width_mm"
    assert "Beam.D1.d_mm" in d.field_sources["height_m"]


def test_beam_group_retains_each_length_and_missing_section():
    beams = [Beam(id="D1", x1=0, y1=0, x2=n, y2=0, b_mm=200, d_mm=400, source="manual")
             for n in (3000, 4000)]
    w = one(beam_works("T2", beams, ProjectParams(slab_thickness_mm=100))[0], "DAM")
    assert [d.length_m for d in w.dimensions] == [3, 4]
    assert w.quantity == pytest.approx(0.42)
    missing = one(beam_works("T2", [beams[0].model_copy(update={"d_mm": None})], ProjectParams())[0], "DAM")
    assert missing.quantity is None and missing.missing
    assert missing.dimensions[0].height_m is None and "height_m" in missing.dimensions[0].missing_fields


def test_columns_section_and_signed_elevations_have_correct_units():
    columns = [Column(id="C1", x=0, y=0, b_mm=200, h_mm=300),
               Column(id="C2", x=2000, y=0, b_mm=220, h_mm=220)]
    works, _ = column_works("T2", columns, 3300, ProjectParams(slab_thickness_mm=100))
    assert sorted((d.width_m, d.length_m) for w in works if w.code == "COT" for d in w.dimensions) == [(0.2, 0.3), (0.22, 0.22)]
    assert all(d.height_m == 3.2 and d.floor_height_m == 3.3 for w in works for d in w.dimensions)
    spans = [ColumnSpan(code="C1", count=2, z_from_mm=-500, z_to_mm=2500, b_mm=200, h_mm=300)]
    w = one(schedule_column_works(spans), "COT"); d = w.dimensions[0]
    assert w.quantity == pytest.approx(0.36)
    assert (d.count, d.bottom_level_m, d.top_level_m, d.height_m) == (2, -0.5, 2.5, 3)


def test_footing_layers_taper_and_direct_volume_override():
    f = FoundationItem(name="M1", count=2, source="SYNTHETIC chi tiết M1", tiers=[
        FootingTier(length_mm=2000, width_mm=2000, height_mm=200),
        FootingTier(length_mm=2000, width_mm=2000, height_mm=600, top_length_mm=1000, top_width_mm=1000)])
    w = one(foundation_works(ProjectParams(foundations=[f]))[0], "MONG")
    assert w.quantity == pytest.approx(4.4) and len(w.dimensions) == 2
    assert w.dimensions[1].top_length_m == w.dimensions[1].top_width_m == 1
    assert w.dimensions[0].height_m == 0.2 and w.dimensions[1].height_m == 0.6
    w = one(foundation_works(ProjectParams(foundations=[f.model_copy(update={"volume_m3": 3.5})]))[0], "MONG")
    assert w.quantity == 7 and all(d.basis == "reference" for d in w.dimensions)
    assert all("nhập trực tiếp" in d.note for d in w.dimensions)
    w = one(foundation_works(ProjectParams(foundations=[FoundationItem(name="MV", volume_m3=2)]))[0], "MONG")
    assert w.quantity == 2 and w.dimensions[0].length_m is None
    assert w.dimensions[0].width_m is None and w.dimensions[0].height_m is None


def test_pit_and_fill_dimensions_are_references_not_fill_box():
    f = FoundationItem(name="M1", length_mm=1000, width_mm=1000, height_mm=500,
                       bottom_level_mm=-1000, lean_thickness_mm=100, neck_b_mm=200, neck_h_mm=200)
    params = ProjectParams(foundations=[f], natural_ground_level_mm=0, excavation_margin_mm=100, excavation_slope=0)
    works, _ = foundation_works(params)
    pit, fill = one(works, "DAO_DAT"), one(works, "DAP_DAT")
    assert pit.quantity == pytest.approx(1.584) and fill.quantity == pytest.approx(0.964)
    d = fill.dimensions[0]
    assert (d.length_m, d.width_m, d.height_m, d.slope_ratio) == (1.2, 1.2, 1.1, 0)
    assert d.basis == "reference" and "không phải kích thước khối đất đắp" in d.note
    assert d.bottom_level_m == -1.1 and d.top_level_m == 0
    deduction = _neg("DAO_DAT", 0.3, element="trừ giao", source="auto")
    assert deduction.quantity == -0.3 and deduction.dimensions[0].basis == "deduction"
    assert deduction.dimensions[0].length_m is None


@pytest.mark.parametrize("void", [None, 0, 2])
def test_slab_is_area_without_invented_rectangle_and_void_zero_is_known(void):
    plan = PlanParams(name="T2", outline_area_m2=30, usable_area_m2=20, void_area_m2=void)
    works, _ = area_works(PlanGeometry(closed=True), ProjectParams(slab_thickness_mm=100), plan)
    w = one(works, "SAN"); d = w.dimensions[0]
    assert d.area_m2 == 30 and d.opening_area_m2 == void
    assert d.length_m is None and "length_m" in d.not_applicable_fields
    if void is None:
        assert d.net_area_m2 is None and "opening_area_m2" in d.missing_fields
    else:
        assert d.net_area_m2 == 30 - void and "opening_area_m2" not in d.missing_fields
        assert w.quantity == pytest.approx((30 - void) * 0.1)


def test_ground_layers_and_roof_have_real_thickness_area():
    params = ProjectParams(ground_layers=[{"kind": "BE_TONG_LOT", "thickness_mm": 100},
                                         {"kind": "BE_TONG_LOT", "thickness_mm": 200}])
    works, _ = area_works(PlanGeometry(closed=True), params, PlanParams(name="Trệt", is_ground=True, usable_area_m2=20))
    layers = [w for w in works if w.code == "BE_TONG_LOT"]
    assert [w.quantity for w in layers] == [2, 4]
    assert len({w.dimensions[0].label for w in layers}) == 2
    roofs, _ = roof_works(ProjectParams(roofs=[{"kind": "be_tong", "area_m2": 25, "thickness_mm": 120}]))
    d = one(roofs, "MAI").dimensions[0]
    assert (d.area_m2, d.thickness_m) == (25, 0.12) and d.length_m is None


def test_stair_horizontal_slope_steps_landing_and_beam_are_separate():
    s = Stair(id="T1", steps=20, flight_width_mm=1000, tread_mm=250, landing_area_m2=1.5,
              beam_length_mm=2400, beam_width_mm=220, beam_depth_mm=300)
    works, _ = stair_works("T2", [s], 3000, ProjectParams(stair_slab_thickness_mm=120))
    w = one(works, "CAU_THANG"); dims = {d.label: d for d in w.dimensions}
    assert dims["T1: hình học thang"].length_m == 5
    assert dims["T1: hình học thang"].slope_length_m == pytest.approx(math.sqrt(34))
    assert (dims["T1: bậc thang"].count, dims["T1: bậc thang"].height_m) == (20, 0.15)
    assert dims["T1: chiếu nghỉ"].area_m2 == 1.5
    assert dims["T1: dầm thang"].length_m == 2.4
    expected = math.sqrt(34) * 0.12 + 20 * 0.25 * 0.15 / 2 + 1.5 * 0.12 + 2.4 * 0.22 * 0.3
    assert w.quantity == pytest.approx(round(expected, 3))
    missing = one(stair_works("T2", [s.model_copy(update={"tread_mm": None})], 3000, ProjectParams())[0], "CAU_THANG")
    assert missing.quantity is None and missing.dimensions[0].length_m is None


def test_steel_table_keeps_diameter_cut_count_but_ratio_and_manual_have_no_fake_geometry():
    rows = [RebarRow(table="B1", row=1, element="C1", element_code="COT", dia_mm=10, cut_length_mm=1200,
                     total_bars=4, kg=2.96, evidence="SYNTHETIC bảng B1 dòng1")]
    w = schedule_works(rows)[0]; d = w.dimensions[0]
    assert (d.count, d.length_m, d.diameter_m) == (4, 1.2, 0.01)
    assert w.quantity == pytest.approx(0.003)
    concrete = WorkItem(code="COT", name="cột", unit="m³", quantity=2)
    ratio = steel_works([concrete], ProjectParams(steel_kg_per_m3={"COT": 100}))[0][0]
    manual = steel_works([concrete], ProjectParams(steel_schedule_t={"COT": 1}))[0][0]
    assert ratio.dimensions == manual.dimensions == []


def test_structural_repetition_changes_only_repetitions_not_length_or_count(catalog):
    b = Beam(id="D1", x1=0, y1=0, x2=4000, y2=0, b_mm=200, d_mm=400, source="structural")
    req = RoughRequest(plans=[], params=ProjectParams(slab_thickness_mm=100), structural_beams={"KC T2-3-4": [b]},
                       structural_floors={"KC T2-3-4": 3})
    w = one(compute_rough(req, catalog).works, "DAM"); d = w.dimensions[0]
    assert w.quantity == pytest.approx(0.72)
    assert (d.length_m, d.count, d.repetitions) == (4, 1, 3)
    assert "lặp 3 tầng" in d.note


def request_for_http(opening=False):
    wall = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    ties = [LinearMember(id=f"G{i}", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0,
                         b_mm=220, d_mm=150, z_bottom_mm=1000) for i in (1, 2)]
    return RoughRequest(params=ProjectParams(beam_depth_mm=300, slab_thickness_mm=100),
        plans=[PlanInput(name="T2", height_mm=3300, walls=[wall], beams=[], members=ties,
            outline_area_m2=30, usable_area_m2=20, void_area_m2=0,
            openings=[{"id": "O1", "wall": "W1", "w": 1000, "h": 2000}] if opening else [])])


@pytest.mark.parametrize("opening", [False, True])
def test_n03_raw_dimensions_do_not_replace_final_net_or_missing(catalog, opening):
    res = compute_rough(request_for_http(opening), catalog)
    tie = one(res.works, "GIANG_TUONG")
    assert tie.quantity == pytest.approx(0.132)
    assert [d.basis for d in tie.dimensions] == ["reference", "reference", "union"]
    assert tie.dimensions[-1].length_m == 4
    assert sum(d.length_m for d in tie.dimensions if d.basis == "reference") == 8
    xay = one(res.works, "XAY")
    if opening:
        assert xay.quantity is None and xay.status == "D" and xay.missing
    else:
        assert xay.quantity == pytest.approx(6.468)
    assert xay.dimensions[0].length_m == 10 and "raw" in xay.dimensions[0].note


@pytest.fixture
def client(catalog, monkeypatch):
    from fastapi.testclient import TestClient
    from optimat.api.main import app
    from optimat.rough import takeoff
    monkeypatch.setattr(takeoff, "default_catalog", lambda: catalog)
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("opening", [False, True])
def test_http_rough_json_preserves_dimensions_and_n03_partial(client, opening):
    r = client.post("/api/takeoff/rough", json=request_for_http(opening).model_dump(mode="json"))
    assert r.status_code == 200, r.text
    result = r.json(); json.dumps(result, allow_nan=False)
    tie = next(w for w in result["works"] if w["code"] == "GIANG_TUONG")
    assert tie["quantity"] == pytest.approx(0.132) and len(tie["dimensions"]) == 3
    xay = next(w for w in result["works"] if w["code"] == "XAY")
    assert (xay["quantity"] is None) == opening
    if opening:
        assert xay["status"] == "D" and xay["missing"]


def test_http_nonfinite_computed_metadata_is_clear_422_not_json_nan(client):
    payload = request_for_http().model_dump(mode="json")
    payload["params"]["slab_thickness_mm"] = float("nan")
    r = client.post("/api/takeoff/rough", content=json.dumps(payload), headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    json.dumps(r.json(), allow_nan=False)
    assert "finite" in str(r.json()).lower() or "hữu hạn" in str(r.json()).lower()


@pytest.mark.parametrize("source", ["manual", "structural"])
def test_wall_height_metadata_keeps_beam_source_injected_by_caller(catalog, source):
    req = request_for_http()
    req.params.beam_depth_mm = None
    req.plans[0].members = []
    req.plans[0].beams = [Beam(id="D7", x1=0, y1=0, x2=4000, y2=0,
                              b_mm=200, d_mm=400, source=source)]
    w = one(compute_rough(req, catalog).works, "XAY"); d = w.dimensions[0]
    assert d.height_m == pytest.approx(2.9) and w.quantity == pytest.approx(6.38)
    assert "D7" in d.field_sources["height_m"] and source in d.field_sources["height_m"]
    assert "d=400" in d.source and "ProjectParams.beam_depth_mm" not in d.field_sources["height_m"]


def test_wall_height_explicit_zero_parameter_is_not_replaced_by_beam_source(catalog):
    req = request_for_http()
    req.params.beam_depth_mm = 0
    req.plans[0].members = []
    req.plans[0].beams = [Beam(id="D7", x1=0, y1=0, x2=4000, y2=0,
                              b_mm=200, d_mm=400, source="structural")]
    d = one(compute_rough(req, catalog).works, "XAY").dimensions[0]
    assert d.height_m == pytest.approx(3.3)
    assert "ProjectParams.beam_depth_mm" in d.field_sources["height_m"]
    assert "D7" not in d.field_sources["height_m"]
