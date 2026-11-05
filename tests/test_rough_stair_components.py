"""Hình học, cấu tạo và nguồn riêng từng thang/vế/chiếu."""
import math
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewWall
from optimat.rough.models import ProjectParams
from optimat.rough.stairs import Stair, StairFlight, StairLanding, stair_works, building_stairs
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough


def flight(id="V1",**kw):
    data=dict(id=id,run_mm=2400,rise_mm=1500,width_mm=1000,
        field_sources={k:"SYNTHETIC DIM riêng vế" for k in ["run_mm","rise_mm","width_mm","step_count","tread_mm","riser_mm"]})
    return StairFlight(**(data|kw))


def stair(**kw):
    data=dict(id="T1",from_floor="T1",to_floor="T2",scope_source="SYNTHETIC phạm vi thang",
        steps_material="masonry",steps_material_source="SYNTHETIC note bậc xây",
        waist_thickness_mm=120,waist_thickness_basis="normal",waist_thickness_source="SYNTHETIC DIM vuông góc",
        flights=[flight()],landings=[])
    return Stair(**(data|kw))


def concrete(s,params=None,height=9999):
    return next(w for w in stair_works("T1",[s],height,params or ProjectParams())[0] if w.code=="CAU_THANG")


def test_masonry_does_not_add_concrete_wedges_or_cast_riser_faces():
    works,_=stair_works("T1",[stair()],9999,ProjectParams(stair_slab_thickness_mm=999))
    bt=next(w for w in works if w.code=="CAU_THANG")
    assert bt.quantity==pytest.approx(round(math.hypot(2.4,1.5)*.12,3))
    refs=[r for r in bt.quantity_detail.rows if r.row_id.endswith(":steps")]
    assert len(refs)==1 and refs[0].role=="reference" and refs[0].raw_quantity=="0"
    cp=next(w for w in works if w.code=="COP_PHA")
    assert cp.quantity==pytest.approx(round(math.hypot(2.4,1.5),3))
    assert cp.missing and not cp.quantity_detail.complete
    assert next(w for w in works if w.code=="XAY").quantity is None


@pytest.mark.parametrize("material,source",[("unknown",None),("masonry",None),("concrete",None)])
def test_unconfirmed_steps_keep_known_slab_but_not_complete(material,source):
    w=concrete(stair(steps_material=material,steps_material_source=source))
    assert w.quantity is not None and w.missing
    assert w.quantity_detail.total_raw is None and not w.quantity_detail.complete
    assert next(r for r in w.quantity_detail.rows if r.row_id.endswith(":steps")).raw_quantity is None


def test_concrete_steps_need_own_counts_dimensions_and_sources():
    f=flight(step_count=8,tread_mm=250,riser_mm=180)
    w=concrete(stair(steps_material="concrete",steps_material_source="SYNTHETIC BT bậc",flights=[f]))
    assert w.quantity_detail.complete
    assert w.quantity==pytest.approx(round(math.hypot(2.4,1.5)*.12+8*.25*.18/2,3))
    missing=concrete(stair(steps_material="concrete",steps_material_source="SYNTHETIC",flights=[flight()]))
    assert missing.quantity is not None and missing.missing and not missing.quantity_detail.complete


def test_separate_flights_do_not_receive_floor_height_or_total_steps():
    f2=flight("V2",run_mm=3000,rise_mm=1800)
    s=stair(flights=[flight(),f2],steps=17,tread_mm=250)
    a=concrete(s,height=3150);b=concrete(s,height=9999)
    expected=(math.hypot(2.4,1.5)+math.hypot(3,1.8))*.12
    assert a.quantity==b.quantity==pytest.approx(round(expected,3))
    assert [d.height_m for d in a.dimensions]==[1.5,1.8]


def test_landing_150_does_not_change_normal_waist_120_or_double_count_floor():
    sources={k:"SYNTHETIC chiếu tới riêng" for k in ["area_m2","thickness_mm","ownership"]}
    landing=StairLanding(id="CT",area_m2=2,thickness_mm=150,ownership="stair",field_sources=sources)
    base=math.hypot(2.4,1.5)*.12
    w=concrete(stair(landings=[landing]))
    assert w.quantity==pytest.approx(round(base+.3,3)) and w.quantity_detail.complete
    excluded=concrete(stair(landings=[landing.model_copy(update={"ownership":"floor"})]))
    assert excluded.quantity==pytest.approx(round(base,3))
    assert next(r for r in excluded.quantity_detail.rows if r.row_id=="CT:landing").role=="reference"


@pytest.mark.parametrize("kw",[dict(flights=None),dict(landings=None),dict(scope_source=None),
    dict(flights=[flight(rise_mm=None)]),dict(waist_thickness_basis="vertical"),dict(waist_thickness_source=None)])
def test_missing_scope_or_measurement_does_not_become_complete(kw):
    w=concrete(stair(**kw))
    assert w.missing and not w.quantity_detail.complete and w.quantity_detail.total_raw is None


def test_sources_do_not_leak_between_stairs():
    works,_=stair_works("T1",[stair(id="A"),stair(id="B",steps_material="unknown",steps_material_source=None)],None,ProjectParams())
    a=next(w for w in works if w.code=="CAU_THANG" and w.element=="thang A")
    b=next(w for w in works if w.code=="CAU_THANG" and w.element=="thang B")
    assert a.quantity_detail.complete and not b.quantity_detail.complete


def test_component_scope_computes_when_plan_height_is_missing_and_walls_stay_blocked():
    wall=ReviewWall(id="W",cls="220",x1=0,y1=0,x2=4000,y2=0)
    req=RoughRequest(plans=[PlanInput(name="Tầng 1",height_mm=None,walls=[wall],stairs=[stair()])])
    result=compute_rough(req,Catalog.from_csv())
    bt=[w for w in result.works if w.code=="CAU_THANG"]
    assert len(bt)==1 and bt[0].quantity is not None and bt[0].status=="C" and bt[0].quantity_detail.complete
    assert not any(w.code=="TRAT" for w in result.works)
    assert not any(w.code=="XAY" and not (w.element or "").startswith("bậc xây") for w in result.works)


def test_unresolved_source_replay_is_null_not_zero():
    s=stair(flights=[StairFlight(id=f"V{i}") for i in range(1,4)],
        landings=[StairLanding(id="CT",thickness_mm=150,field_sources={"thickness_mm":"KC source"})])
    result=compute_rough(RoughRequest(plans=[PlanInput(name="Tầng 1",walls=[],stairs=[s])]),Catalog.from_csv())
    for w in result.works:
        if w.code=="CAU_THANG" or w.formwork_of=="CAU_THANG":
            assert w.quantity is None and w.status=="D" and w.missing
            assert w.quantity_detail.known_part_raw is None


@pytest.mark.parametrize("kw",[dict(width_mm=float("nan")),dict(rise_mm=-1),dict(waist_thickness_mm=float("inf"))])
def test_bad_geometry_rejected(kw):
    with pytest.raises(ValidationError):flight(**kw)


def test_partial_reader_does_not_copy_material_thickness_or_confirmed_source(monkeypatch):
    from optimat.rough import stairs as module
    full=stair(steps=20,flight_width_mm=1000)
    part=Stair(steps=4,flight_width_mm=1000)
    monkeypatch.setattr(module,"detect_stairs",lambda d,*args:[full] if d=="full" else [part])
    found,_=building_stairs(["part","full"],["Tầng 1","Tầng 2"])
    assert found[0][0].steps==4 and found[0][0].steps_material=="unknown"
    assert found[0][0].waist_thickness_mm is None and found[0][0].scope_source is None


def test_formwork_scope_requires_own_source_and_cannot_fill_missing_geometry():
    confirmed=stair(formwork_scope_source="SYNTHETIC đã kiểm chỉ đáy, không cạnh/gối/giao khác")
    works,_=stair_works("T1",[confirmed],None,ProjectParams())
    cp=next(w for w in works if w.code=="COP_PHA")
    assert cp.quantity_detail.complete and cp.status=="C"
    unresolved=confirmed.model_copy(update={"flights":[flight(rise_mm=None)]})
    cp=next(w for w in stair_works("T1",[unresolved],None,ProjectParams())[0] if w.code=="COP_PHA")
    assert cp.quantity is None and cp.status=="D" and not cp.quantity_detail.complete


def test_component_ids_and_unknown_fields_are_validated():
    with pytest.raises(ValidationError):
        stair(landings=[StairLanding(id="V1")])
    with pytest.raises(ValidationError):
        StairFlight(id="V1",height_floor_mm=3300)
