"""Phần thô S6a: gộp các mặt bằng thành một bảng công tác + vật liệu."""
import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening, ReviewWall
from optimat.rough.columns import Column
from optimat.rough.models import GroundLayer, ProjectParams
from optimat.rough.stairs import Stair
from optimat.rough.takeoff import PlanInput, RoomLabel, RoughRequest, compute_rough, ground_index


def walls():
    e = dict(cls="220", role="envelope", mat="GN01")
    return [ReviewWall(id="A", x1=0, y1=0, x2=10000, y2=0, **e), ReviewWall(id="B", x1=10000, y1=0, x2=10000, y2=6000, **e),
            ReviewWall(id="C", x1=10000, y1=6000, x2=0, y2=6000, **e), ReviewWall(id="D", x1=0, y1=6000, x2=0, y2=0, **e),
            ReviewWall(id="P", cls="110", role="partition", x1=3000, y1=0, x2=3000, y2=6000, mat="GN01")]


COLS = [Column(id=f"C{i}", x=x, y=y, b_mm=220, h_mm=220) for i, (x, y) in enumerate(
    [(0, 0), (5000, 0), (10000, 0), (0, 6000), (5000, 6000), (10000, 6000)])]


def plan(name, ground):
    return PlanInput(name=name, is_ground=ground, height_mm=3300, walls=walls(), columns=COLS, void_area_m2=0 if not ground else None,
                     openings=[ReviewOpening(id="O1", wall="A", w=1000, h=2200)],
                     labels=[RoomLabel(kind="WET", text="WC", x=1500, y=3000)],
                     stairs=[] if not ground else [Stair(steps=22, flight_width_mm=1000, tread_mm=250, landing_area_m2=2)])


FULL = ProjectParams(concrete_supply="ready_mix", concrete_grade="M250", lean_concrete_grade="M100", masonry_mortar_grade="M75",
                     plaster_mortar_grade="M75", screed_mortar_grade="M75", plaster_thickness_mm=15, screed_thickness_mm=30,
                     slab_thickness_mm=100, beam_depth_mm=400, beam_width_mm=220, lintel_height_mm=200, lintel_bearing_mm=200,
                     waterproof_upturn_mm=300, waterproof_material_id="CT02", stair_slab_thickness_mm=120,
                     steel_kg_per_m3={"COT": 150, "DAM": 130, "SAN": 90, "LANH_TO": 80, "CAU_THANG": 100},
                     ground_layers=[GroundLayer(kind="NEN_DEM_CAT", thickness_mm=300), GroundLayer(kind="BE_TONG_LOT", thickness_mm=100)])


def test_two_floor_house():
    res = compute_rough(RoughRequest(params=FULL, plans=[plan("Trệt", True), plan("Tầng 2", False)]), Catalog.from_csv(None))
    codes = {t.code: t for t in res.totals}
    assert {"XAY", "TRAT", "LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "NEN_DEM_CAT", "BE_TONG_LOT", "CAN_NEN",
            "CHONG_THAM", "COT_THEP", "COP_PHA"} <= set(codes)
    assert all(t.complete for t in res.totals), [t for t in res.totals if not t.complete]
    assert len([w for w in res.works if w.code == "SAN"]) == 1                 # tầng trệt không có sàn
    assert len(res.beams["Trệt"]) == 6                       # 4 nhịp dọc + 2 nhịp ngang có tường
    bt = next(m for m in res.materials if m.material_id == "BT03")
    concrete = sum(t.quantity for t in res.totals if t.code in ("LANH_TO", "COT", "DAM", "SAN", "CAU_THANG"))
    assert bt.quantity == pytest.approx(concrete, abs=0.01)
    assert next(m for m in res.materials if m.material_id == "GN01").quantity > 0
    assert any("Ca máy" in w for w in res.warnings)


def test_no_params_everything_flagged_not_guessed():
    res = compute_rough(RoughRequest(plans=[plan("Trệt", True), plan("Tầng 2", False)]), Catalog.from_csv(None))
    incomplete = {t.code for t in res.totals if not t.complete}
    assert {"LANH_TO", "DAM", "SAN", "COT_THEP", "NEN_DEM_CAT", "CHONG_THAM", "CAU_THANG"} <= incomplete
    assert next(t for t in res.totals if t.code == "XAY").complete      # xây không cần thông số bắt buộc


def test_ground_index():
    assert ground_index(["MẶT BẰNG LỬNG", "MẶT BẰNG TRỆT"], [None, None]) == 1
    assert ground_index(["a", "b"], [3.3, 0.0]) == 1
    assert ground_index(["mặt bằng tầng 1", "mặt bằng tầng 2 (+3.30)"], [None, 3.3]) == 0
    assert ground_index(["Toàn bộ bản vẽ"], [None]) is None


def test_formwork_summary_no_double_count():
    res = compute_rough(RoughRequest(params=FULL, plans=[plan("Trệt", True), plan("Tầng 2", False)]), Catalog.from_csv(None))
    total = next(t for t in res.totals if t.code == "COP_PHA").quantity
    assert {f.code for f in res.formwork} == {"LANH_TO", "COT", "DAM", "SAN", "CAU_THANG"}
    assert sum(f.quantity for f in res.formwork) == pytest.approx(total, abs=0.01)


def test_manual_beam_depth_used_for_walls():
    from optimat.rough.beams import Beam
    p = plan("Tầng 2", False)
    p.beams = [Beam(id="D1", x1=0, y1=0, x2=5000, y2=0, b_mm=220, d_mm=400, source="manual")]
    res = compute_rough(RoughRequest(params=ProjectParams(), plans=[p]), Catalog.from_csv(None))
    assert not any("chưa trừ dầm" in w for w in res.warnings)


def test_duplicate_plan_names_kept_apart():
    # nhà phố build có hai tiêu đề "tầng 3": dầm, chi tiết theo tầng không được ghi đè nhau
    res = compute_rough(RoughRequest(params=FULL, plans=[plan("Trệt", True), plan("Tầng 3", False), plan("Tầng 3", False)]),
                        Catalog.from_csv(None))
    assert set(res.beams) == {"Trệt", "Tầng 3", "Tầng 3 (2)"}
    assert {w.plan for w in res.works if w.code == "COT"} == {"Trệt", "Tầng 3", "Tầng 3 (2)"}


def test_no_plans_warns():
    res = compute_rough(RoughRequest(plans=[]), Catalog.from_csv(None))
    assert not res.works and "Không tìm thấy mặt bằng" in res.warnings[0]
