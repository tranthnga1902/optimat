"""Thang bản có nguồn theo từng vế; không mặc định bậc bê tông."""
import math
import pytest
from optimat.rough.models import ProjectParams
from optimat.rough.stairs import Stair, StairFlight, StairLanding, stair_works


def test_two_flight_stair():
    fs={k:"SYNTHETIC mặt cắt vế" for k in ["run_mm","rise_mm","width_mm","step_count","tread_mm","riser_mm"]}
    s=Stair(id="T1",steps_material="concrete",steps_material_source="SYNTHETIC bậc đổBT",
        from_floor="T1",to_floor="T2",scope_source="SYNTHETIC phạm vi thang",
        waist_thickness_mm=120,waist_thickness_basis="normal",waist_thickness_source="SYNTHETIC DIM vuông góc",
        flights=[StairFlight(id=f"V{i}",run_mm=2750,rise_mm=1650,width_mm=1000,step_count=11,tread_mm=250,riser_mm=150,field_sources=fs) for i in (1,2)],
        landings=[StairLanding(id="CN",area_m2=2,thickness_mm=120,ownership="stair",field_sources={k:"SYNTHETIC chiếu" for k in ["area_m2","thickness_mm","ownership"]})])
    works,_=stair_works("T1",[s],3300,ProjectParams())
    slope=math.hypot(2.75,1.65)*2
    beton=next(w for w in works if w.code=="CAU_THANG")
    assert beton.quantity==pytest.approx(slope*.12+22*.25*.15/2+2*.12,abs=1e-3)
    assert beton.quantity_detail.complete
    cp=next(w for w in works if w.code=="COP_PHA")
    assert cp.quantity==pytest.approx(slope+2+22*.15,abs=1e-3)
    assert cp.missing and not cp.quantity_detail.complete  # mặt cạnh/gối/giao chưa được kiểm


def test_stair_missing_inputs():
    works,_=stair_works("T1",[Stair(steps=20)],3300,ProjectParams(stair_slab_thickness_mm=150))
    assert works[0].quantity is None
    assert any("từng vế" in m for m in works[0].missing)
    assert works[0].quantity_detail.total_raw is None
