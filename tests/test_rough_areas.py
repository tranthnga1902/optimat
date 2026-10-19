"""Phần thô bước 3: sàn, cán nền, nền tầng trệt, chống thấm từ đường bao và phòng."""
import pytest

from optimat.drawing.review import ReviewWall
from optimat.rough.areas import PlanParams, area_works, plan_geometry, room_kind
from optimat.rough.models import GroundLayer, ProjectParams


def box():
    e = dict(cls="220", role="envelope")
    return [ReviewWall(id="A", x1=0, y1=0, x2=10000, y2=0, **e), ReviewWall(id="B", x1=10000, y1=0, x2=10000, y2=8000, **e),
            ReviewWall(id="C", x1=10000, y1=8000, x2=0, y2=8000, **e), ReviewWall(id="D", x1=0, y1=8000, x2=0, y2=0, **e),
            ReviewWall(id="P", cls="110", role="partition", x1=3000, y1=0, x2=3000, y2=8000)]


LABELS = [("WET", "WC", 1500, 4000), ("BALCONY", "BAN CÔNG", 5000, -2000)]


def test_room_rules():
    assert room_kind("WC 1") == "WET" and room_kind("Phòng tắm") == "WET" and room_kind("VS2") == "WET"
    assert room_kind("BAN CÔNG") == "BALCONY" and room_kind("Phòng ngủ") is None and room_kind("Cửa sổ") is None


def test_geometry_of_closed_box():
    g = plan_geometry(box(), LABELS)
    assert g.closed
    assert g.outline_area_m2 == pytest.approx(80.0, rel=0.005)
    assert g.usable_area_m2 == pytest.approx(9.78 * 7.78 - 0.11 * 7.78, rel=0.005)
    wc = next(r for r in g.rooms if r.kind == "WET")
    assert wc.area_m2 == pytest.approx(2.835 * 7.78, rel=0.01) and wc.perimeter_m == pytest.approx(2 * (2.835 + 7.78), rel=0.01)
    assert g.labels_outside == ["BAN CÔNG"]


def test_open_outline_gives_no_area():
    walls = box()[:3]
    g = plan_geometry(walls, LABELS)
    works, warnings = area_works(g, ProjectParams(), PlanParams(name="T2"))
    assert not g.closed and works == [] and "khép kín" in warnings[0]


def test_upper_floor_works():
    g = plan_geometry(box(), LABELS)
    p = ProjectParams(slab_thickness_mm=120, screed_thickness_mm=30, waterproof_upturn_mm=300, waterproof_material_id="CT02")
    works, warnings = area_works(g, p, PlanParams(name="Tầng 2", void_area_m2=6.0))
    san = next(w for w in works if w.code == "SAN")
    assert san.quantity == pytest.approx((g.outline_area_m2 - 6.0) * 0.12, abs=1e-3)
    assert next(w for w in works if w.code == "CAN_NEN").variant == "30"
    assert next(w for w in works if w.code == "COP_PHA").quantity == pytest.approx(g.outline_area_m2 - 6.0, abs=1e-2)
    ct = next(w for w in works if w.code == "CHONG_THAM")
    assert ct.quantity == pytest.approx(g.rooms[0].area_m2 + 0.3 * g.rooms[0].perimeter_m, rel=1e-3) and ct.variant == "CT02"
    assert any("ban công" in w for w in warnings)
    assert not any(w.code in ("NEN_DEM_CAT", "BE_TONG_LOT") for w in works)


def test_ground_floor_and_missing_params():
    g = plan_geometry(box(), LABELS)
    works, warnings = area_works(g, ProjectParams(), PlanParams(name="Trệt", is_ground=True, balcony_area_m2=4.5))
    assert not any(w.code == "SAN" for w in works)
    assert {w.code for w in works if w.quantity is None} >= {"NEN_DEM_CAT", "BE_TONG_LOT", "CHONG_THAM"}
    p = ProjectParams(ground_layers=[GroundLayer(kind="NEN_DEM_CAT", thickness_mm=300),
                                     GroundLayer(kind="BE_TONG_LOT", thickness_mm=100)])
    works, _ = area_works(g, p, PlanParams(name="Trệt", is_ground=True))
    cat = next(w for w in works if w.code == "NEN_DEM_CAT")
    assert cat.quantity == pytest.approx(g.usable_area_m2 * 0.3, abs=1e-3)


def test_manual_area_when_outline_open():
    g = plan_geometry(box()[:3], LABELS)
    works, _ = area_works(g, ProjectParams(slab_thickness_mm=100), PlanParams(name="T2", outline_area_m2=50.0, void_area_m2=0))
    san = next(w for w in works if w.code == "SAN")
    assert san.quantity == pytest.approx(5.0) and san.source == "manual"
    can = next(w for w in works if w.code == "CAN_NEN")
    assert can.quantity is None and any("diện tích sử dụng" in m for m in can.missing)
