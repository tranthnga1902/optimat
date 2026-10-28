"""S06: nút giao cột – dầm – sàn, dầm giao nhau, dầm trùng, lỗ mở sàn, xung đột cao độ, cột kiến trúc."""
import pytest

from optimat.rough.areas import PlanGeometry, PlanParams, area_works
from optimat.rough.beams import Beam, beam_joints, beam_works
from optimat.rough.columns import Column, column_works
from optimat.rough.models import ProjectParams
from optimat.rough.takeoff import PlanInput, _section_checks, _slab_form_deduction

P = ProjectParams(slab_thickness_mm=100)
COLS = [Column(id="C1", x=0, y=0, b_mm=200, h_mm=200), Column(id="C2", x=5000, y=0, b_mm=200, h_mm=200)]


def _q(works, code, of=None):
    return sum(w.quantity for w in works if w.code == code and (of is None or w.formwork_of == of))


def test_column_beam_slab_node_no_double_count():
    beam = Beam(id="D1", x1=0, y1=0, x2=5000, y2=0, b_mm=200, d_mm=400, source="manual")     # vẽ tim cột – tim cột
    beams, _ = beam_joints([beam], COLS, P)
    assert beams[0].cut_mm == pytest.approx(200) and beam.cut_mm == 0                       # không sửa dầm gốc
    bw, _ = beam_works("T1", beams, P)
    cw, _ = column_works("T1", COLS, 3000, P, beams)
    # thể tích hợp của khung: cột tới đáy sàn, dầm giữa hai mặt cột và dưới sàn
    assert _q(cw, "COT") + _q(bw, "DAM") == pytest.approx(2 * 0.04 * 2.9 + 4.8 * 0.2 * 0.3, abs=1e-3)
    assert _q(cw, "COP_PHA") == pytest.approx(2 * 0.8 * 2.9 - 2 * 0.2 * 0.3, abs=1e-3)       # trừ đầu dầm che mặt cột
    again, _ = beam_joints(beams, COLS, P)                                                    # gọi lại không trừ thêm
    assert again[0].cut_mm == pytest.approx(200)


def test_crossing_beams_main_continuous():
    main = Beam(id="D1", x1=0, y1=0, x2=6000, y2=0, b_mm=220, d_mm=500, source="manual")
    sec = Beam(id="D2", x1=3000, y1=-3000, x2=3000, y2=3000, b_mm=200, d_mm=400, source="manual")
    beams, _ = beam_joints([sec, main], [], P)
    d1, d2 = beams[1], beams[0]
    assert d1.cut_mm == 0 and d2.cut_mm == pytest.approx(220) and len(d1.framed) == 2
    works, _ = beam_works("T1", beams, P)
    assert _q(works, "DAM") == pytest.approx(6 * 0.22 * 0.4 + 5.78 * 0.2 * 0.3, abs=1e-3)
    d1_form = next(w for w in works if w.code == "COP_PHA" and "D1" in w.element)
    assert d1_form.quantity == pytest.approx((2 * 0.4 + 0.22) * 6 - 2 * 0.2 * 0.3, abs=1e-3)


def test_t_junction_and_duplicate_beam():
    main = Beam(id="D1", x1=0, y1=0, x2=6000, y2=0, b_mm=220, d_mm=500, source="manual")
    tee = Beam(id="D2", x1=3000, y1=0, x2=3000, y2=3000, b_mm=200, d_mm=400, source="manual")   # dừng ở tim dầm chính
    beams, _ = beam_joints([main, tee], [], P)
    assert beams[1].cut_mm == pytest.approx(110) and len(beams[0].framed) == 1
    dup = Beam(id="D1b", x1=2000, y1=0, x2=6000, y2=0, b_mm=220, d_mm=500, source="manual")
    beams, warnings = beam_joints([main, dup], [], P)
    assert beams[1].length_mm == 0 and any("chồng lên" in w for w in warnings)


def test_slab_opening_and_bottom_form_deduction():
    plan = PlanParams(name="T2", void_area_m2=4.0)
    works, _ = area_works(PlanGeometry(closed=True, outline_area_m2=60, usable_area_m2=50), P, plan)
    san = next(w for w in works if w.code == "SAN")
    assert san.quantity == pytest.approx((60 - 4) * 0.1)                                      # trừ lỗ mở sàn
    beams, _ = beam_joints([Beam(id="D1", x1=0, y1=0, x2=5000, y2=0, b_mm=200, d_mm=400, source="manual")], COLS, P)
    ded = _slab_form_deduction("T2", beams, COLS, P)[0]
    assert ded.formwork_of == "SAN" and ded.quantity == pytest.approx(-(4.8 * 0.2 + 2 * 0.04), abs=1e-3)


def test_elevation_conflict_and_column_sections():
    p = PlanInput(name="T1", height_mm=3000, walls=[], columns=COLS + [Column(id="C3", x=9000, y=0, b_mm=400, h_mm=150)])
    beams = [Beam(id="D9", x1=0, y1=0, x2=1, y2=0, b_mm=200, d_mm=3200, source="manual")]
    msgs = _section_checks(p, beams, P, {"c1": (200, 200)})
    assert any("xung đột cao độ" in m and "D9" in m for m in msgs)
    assert any("C3" in m and "không khớp" in m for m in msgs) and not any("C1," in m for m in msgs)


def test_architectural_column_and_slab_thicker_than_floor():
    cols = COLS + [Column(id="C3", x=9000, y=0, b_mm=300, h_mm=300, role="kien_truc")]
    works, warnings = column_works("T1", cols, 3000, P)
    assert _q(works, "COT") == pytest.approx(2 * 0.04 * 2.9, abs=1e-3) and any("cột kiến trúc" in w for w in warnings)
    works, warnings = column_works("T1", COLS, 100, P)
    assert not works and any("xung đột cao độ" in w for w in warnings)


def test_missing_section_blocked():
    works, _ = beam_works("T1", [Beam(id="D5", x1=0, y1=0, x2=4000, y2=0, source="structural")], P)
    dam = next(w for w in works if w.code == "DAM")
    assert dam.quantity is None and {"rộng dầm", "cao dầm"} <= set(dam.missing) and dam.element.startswith("D5:")
