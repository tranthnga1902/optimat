"""S05: móng nhiều lớp, bê tông lót, đào đắp hố móng, móng trùng, hố chồng lấn, giằng qua móng, thiếu cao độ."""
import pytest

from optimat.catalog.repository import Catalog
from optimat.rough.beams import Beam
from optimat.rough.foundations import foundation_works, pit_overlap_m3, tier_volume_m3
from optimat.rough.models import FootingTier, FoundationItem, ProjectParams
from optimat.rough.structural import _footing_center
from optimat.rough.takeoff import RoughRequest, compute_rough

EARTH = dict(natural_ground_level_mm=-450, excavation_margin_mm=300, excavation_slope=0.5)


def _m1(**kw):
    base = dict(name="M1", count=2, length_mm=1200, width_mm=1200, height_mm=400, lean_thickness_mm=100,
                bottom_level_mm=-1500, neck_b_mm=220, neck_h_mm=220, source="ket_cau.dxf: MÓNG M1, 2 mặt cắt")
    return FoundationItem(**{**base, **kw})


def _one(works, code, name="M1"):
    return next(w for w in works if w.code == code and name in w.element)


def test_stepped_and_sloped_tiers():
    f = FoundationItem(name="M2", tiers=[FootingTier(length_mm=1500, width_mm=1500, height_mm=300),
                                         FootingTier(length_mm=1500, width_mm=1500, height_mm=300, top_length_mm=400, top_width_mm=400),
                                         FootingTier(length_mm=400, width_mm=400, height_mm=200)], lean_thickness_mm=100)
    out, _ = foundation_works(ProjectParams(foundations=[f]))
    sloped = 0.3 / 6 * (1.5 * 1.5 + 4 * 0.95 * 0.95 + 0.4 * 0.4)
    assert tier_volume_m3(f.tiers[1]) == pytest.approx(sloped)
    assert _one(out, "MONG", "M2").quantity == pytest.approx(0.675 + sloped + 0.032, abs=1e-3)
    assert _one(out, "BE_TONG_LOT", "M2").quantity == pytest.approx(1.5 * 1.5 * 0.1, abs=1e-3)   # lót tách khỏi móng
    # cốp pha chỉ mặt đứng tiếp xúc: lớp dưới + cổ trên, mặt vát không tính
    assert _one(out, "COP_PHA", "M2").quantity == pytest.approx(2 * 3.0 * 0.3 + 2 * 0.8 * 0.2, abs=1e-3)


def test_footing_without_detail_stays_blank():
    out, warnings = foundation_works(ProjectParams(foundations=[FoundationItem(name="M4", count=2)]))
    mong = _one(out, "MONG", "M4")
    assert mong.quantity is None and "chưa có chi tiết móng" in mong.missing[0]
    assert any("M4" in w for w in warnings)


def test_excavation_and_backfill():
    out, warnings = foundation_works(ProjectParams(foundations=[_m1()], **EARTH))
    depth = -0.45 - (-1.6)                                         # cốt tự nhiên − đáy lót
    a0, a1 = 1.8, 1.8 + 2 * 0.5 * depth
    pit = depth / 6 * (a0 * a0 + 4 * ((a0 + a1) / 2) ** 2 + a1 * a1)
    assert _one(out, "DAO_DAT").quantity == pytest.approx(2 * pit, abs=1e-3)
    neck = 0.22 * 0.22 * (-0.45 - (-1.1))                          # cổ móng chôn từ mặt móng tới cốt tự nhiên
    fill = pit - 1.2 * 1.2 * 0.1 - 1.2 * 1.2 * 0.4 - neck
    assert _one(out, "DAP_DAT").quantity == pytest.approx(2 * fill, abs=1e-3)
    assert "ket_cau.dxf" in _one(out, "MONG").formula                 # truy ngược file, chi tiết
    assert any("Chưa có vị trí móng M1" in w for w in warnings)


def test_earthworks_need_confirmed_inputs():
    out, warnings = foundation_works(ProjectParams(foundations=[_m1()]))
    assert not any(w.code in ("DAO_DAT", "DAP_DAT") for w in out) and any("Chưa tính đào" in w for w in warnings)
    out, _ = foundation_works(ProjectParams(foundations=[_m1(neck_b_mm=None)], **EARTH))
    assert _one(out, "DAP_DAT").quantity is None and "tiết diện cổ móng M1" in _one(out, "DAP_DAT").missing


def test_insufficient_elevation():
    out, warnings = foundation_works(ProjectParams(foundations=[_m1(bottom_level_mm=0)], **EARTH))
    assert _one(out, "DAO_DAT").quantity is None and any("không đủ cao độ" in w for w in warnings)
    out, warnings = foundation_works(ProjectParams(foundations=[_m1(bottom_level_mm=-700)], **EARTH))
    assert _one(out, "DAO_DAT").quantity is not None and any("mặt móng (-300) cao hơn cốt đất tự nhiên" in w for w in warnings)


def test_negative_backfill_blocked():
    f = FoundationItem(name="M9", tiers=[FootingTier(length_mm=500, width_mm=500, height_mm=200),
                                         FootingTier(length_mm=3000, width_mm=3000, height_mm=500)],
                       lean_thickness_mm=100, bottom_level_mm=-1150)   # mặt móng = cốt tự nhiên
    out, warnings = foundation_works(ProjectParams(foundations=[f], natural_ground_level_mm=-450,
                                                   excavation_margin_mm=0, excavation_slope=0))
    assert _one(out, "DAP_DAT", "M9").quantity is None and any("đắp âm" in w for w in warnings)


def test_duplicate_footing_counted_once():
    out, warnings = foundation_works(ProjectParams(foundations=[_m1(), _m1()]))
    assert len([w for w in out if w.code == "MONG"]) == 1 and any("nhập hai lần" in w for w in warnings)


def test_overlapping_pits_counted_once():
    f = _m1(positions=[(0, 0), (1500, 0)])                         # hố 1,8 m, tâm cách 1,5 m: chồng 0,3 m
    out, warnings = foundation_works(ProjectParams(foundations=[f], **{**EARTH, "excavation_slope": 0}))
    lap = next(w for w in out if w.code == "DAO_DAT" and "chồng lấn" in w.element)
    assert lap.quantity == pytest.approx(-0.3 * 1.8 * 1.15, abs=1e-3) and any("chồng lấn" in w for w in warnings)
    far = _m1(positions=[(0, 0), (9000, 0)])
    assert pit_overlap_m3([(x, y, {"l": 1800, "w": 1800, "d": 1150, "m": 0.5}) for x, y in far.positions]) == 0


def test_tie_beam_through_footing_not_double_counted():
    plan = "MẶT BẰNG MÓNG"
    f = _m1(count=1, positions=[(0, 0)], plan=plan)
    gm = Beam(id="GM1", x1=-3000, y1=0, x2=3000, y2=0, b_mm=200, d_mm=300, source="structural")
    res = compute_rough(RoughRequest(plans=[], params=ProjectParams(foundations=[f]), structural_beams={plan: [gm]}),
                        Catalog.from_csv(None))
    dam = next(w for w in res.works if w.code == "DAM")
    assert dam.quantity == pytest.approx((6 - 1.2) * 0.2 * 0.3, abs=1e-3)        # giằng: đủ cao, không trừ sàn
    form = next(w for w in res.works if w.code == "COP_PHA" and w.formwork_of == "DAM")
    assert form.quantity == pytest.approx(2 * 0.3 * 4.8, abs=1e-3)                # hai thành, không ván đáy
    assert not any(w.formwork_of == "SAN" for w in res.works)                      # không có sàn thì không trừ


def test_footing_center_from_plan_rectangle():
    lines = [("h", 0, 0, 1350), ("h", 1700, 0, 1350), ("v", 0, 0, 1700), ("v", 1350, 0, 1700), ("h", 5000, 0, 900)]
    assert _footing_center(lines, 700, 2200, 1350, 1700) == (675, 850)            # ký hiệu ngay trên khung
    assert _footing_center(lines, 700, 2200, 1000, 1000) is None
