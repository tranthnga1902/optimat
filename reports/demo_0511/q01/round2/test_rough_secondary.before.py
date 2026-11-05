"""S08: cầu thang, giằng tường, sê nô, mái; không cộng trùng lanh tô – dầm, giằng – tường, mái – sàn."""
import math
from pathlib import Path

import pandas as pd
import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.dxf_reader import Drawing, Segment, TextItem
from optimat.drawing.review import ReviewOpening, ReviewWall
from optimat.rough.beams import Beam
from optimat.rough.models import ProjectParams, RoofItem
from optimat.rough.secondary import LinearMember, read_secondary, roof_kind
from optimat.rough.stairs import Stair, stair_works
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough

ROOT = Path(__file__).resolve().parents[1]
WALL = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
P = ProjectParams(beam_depth_mm=300, lintel_height_mm=200, lintel_bearing_mm=200, plaster_thickness_mm=15)


@pytest.fixture(scope="module")
def cat():
    return Catalog.from_csv(None)


def _one(res, code, plan="T1"):
    return next(w for w in res.works if w.code == code and w.plan == plan)


def _plan(**kw):
    return PlanInput(name="T1", height_mm=3300, walls=[WALL], **kw)


def test_lintel_not_double_counted_with_beam(cat):
    """Cửa cao 2900: đỉnh lanh tô (2900 + 200) vượt đáy dầm (3300 − 300) -> dầm làm lanh tô, không lanh tô riêng."""
    beam = Beam(id="D1", x1=0, y1=0, x2=10000, y2=0, b_mm=220, d_mm=300, source="manual")
    p = P.model_copy(update={"slab_thickness_mm": 120})
    res = compute_rough(RoughRequest(params=p, plans=[_plan(openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2900)],
                                                            beams=[beam])]), cat)
    assert _one(res, "LANH_TO").quantity == 0 and _one(res, "DAM").quantity
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 1.0 * 2.9 * 0.22, abs=1e-3)
    assert any("tránh trùng dầm" in w for w in res.warnings)


def test_lintel_kept_when_below_beam(cat):
    res = compute_rough(RoughRequest(params=P, plans=[_plan(openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2200)],
                                                            beams=[])]), cat)
    assert _one(res, "LANH_TO").quantity == pytest.approx(1.4 * 0.22 * 0.2, abs=1e-3)
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 2.2 * 0.22 - 1.4 * 0.22 * 0.2, abs=1e-3)


def test_tie_deducted_from_masonry(cat):
    tie = LinearMember(id="GT1", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0, b_mm=220, d_mm=150)
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[tie])]), cat)
    assert _one(res, "GIANG_TUONG").quantity == pytest.approx(4 * 0.22 * 0.15, abs=1e-3)
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 4 * 0.15 * 0.22, abs=1e-3)
    form = next(w for w in res.works if w.formwork_of == "GIANG_TUONG")
    assert form.quantity == pytest.approx(2 * 0.15 * 4, abs=1e-3)
    assert any(t.code == "GIANG_TUONG" for t in res.formwork)


def test_tie_without_depth_left_blank(cat):
    tie = LinearMember(id="GT1", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0, b_mm=220)
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[tie])]), cat)
    assert _one(res, "GIANG_TUONG").quantity is None and "cao giằng" in _one(res, "GIANG_TUONG").missing
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22, abs=1e-3)


@pytest.mark.xfail(strict=True, reason="Hai giằng cùng đoạn trừ khối xây hai lần")
def test_overlapping_ties_deduct_masonry_once(cat):
    ties = [LinearMember(id=f"GT{i}", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0,
                         b_mm=220, d_mm=150) for i in (1, 2)]
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=ties)]), cat)
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 4 * 0.15 * 0.22, abs=1e-3)


def test_gutter_rectangular_with_warning(cat):
    sn = LinearMember(id="SN1", kind="SE_NO", x1=0, y1=0, x2=6000, y2=0, b_mm=600, d_mm=400)
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[sn])]), cat)
    assert _one(res, "SE_NO").quantity == pytest.approx(6 * 0.6 * 0.4, abs=1e-3)
    assert any("chữ U" in w for w in res.warnings)


def test_concrete_roof_replaces_slab(cat):
    p = P.model_copy(update={"slab_thickness_mm": 120,
                             "roofs": [RoofItem(kind="be_tong", area_m2=50, thickness_mm=100, replaces_slab_of="T1")]})
    res = compute_rough(RoughRequest(params=p, plans=[_plan(beams=[])]), cat)
    mai = next(w for w in res.works if w.code == "MAI")
    assert mai.quantity == pytest.approx(5.0) and not any(w.code == "SAN" for w in res.works)
    assert not any(w.formwork_of == "SAN" for w in res.works) and any(t.code == "MAI" for t in res.formwork)


def test_frame_roof_not_supported(cat):
    res = compute_rough(RoughRequest(params=ProjectParams(roofs=[RoofItem(name="Mái tôn", kind="khung", area_m2=80)]),
                                     plans=[]), cat)
    mai = next(w for w in res.works if w.code == "MAI")
    assert mai.quantity is None and mai.basis == "not_supported" and "Not supported" in mai.missing[0]
    assert not any(u.work == "MAI" for m in res.materials for u in m.uses)
    assert roof_kind("CHI TIẾT VÌ KÈO MÁI") == "khung" and roof_kind("MẶT BẰNG KẾT CẤU SÀN MÁI") == "be_tong"


def test_stair_with_landing_beam():
    s = Stair(steps=22, flight_width_mm=1000, tread_mm=250, landing_area_m2=2.0, beam_length_mm=2400,
              beam_width_mm=220, beam_depth_mm=300)
    works, _ = stair_works("T1", [s], 3300, ProjectParams(stair_slab_thickness_mm=120))
    riser, slope = 3.3 / 22, math.hypot(22 * 0.25, 3.3)
    assert works[0].quantity == pytest.approx(slope * 0.12 + 22 * 0.25 * riser / 2 + 0.24 + 2.4 * 0.22 * 0.3, abs=1e-3)
    assert works[1].quantity == pytest.approx(slope + 2.0 + 22 * riser + (0.6 + 0.22) * 2.4, abs=1e-3)


def test_stair_con_not_supported():
    works, _ = stair_works("T1", [Stair(kind="con", steps=20, flight_width_mm=1000, tread_mm=250)], 3300,
                           ProjectParams(stair_slab_thickness_mm=120))
    assert len(works) == 1 and works[0].quantity is None and works[0].basis == "not_supported"
    works, _ = stair_works("T1", [Stair(steps=20, flight_width_mm=1000, tread_mm=250, beam_length_mm=2000)], 3300,
                           ProjectParams(stair_slab_thickness_mm=120))
    assert works[0].quantity is None and "tiết diện dầm thang" in works[0].missing


def test_read_secondary_from_structural_plan():
    segs = [Segment(0, 0, 6000, 0, "KC"), Segment(0, 220, 6000, 220, "KC")]
    texts = [TextItem("MẶT BẰNG DẦM SÀN LẦU 1", 3000, -2000, "T", "unicode", 600),
             TextItem("GT1", 3000, 400, "T", "unicode", 300),
             TextItem("GT1 220x150", 20000, -3000, "T", "unicode", 300),
             TextItem("LT1 220x200", 20000, -4000, "T", "unicode", 300),
             TextItem("CHI TIẾT VÌ KÈO", 30000, -9000, "T", "unicode", 600)]
    d = Drawing(segments=segs, texts=texts, blocks=[], hatches=[], layers=["KC"], layer_classes={}, unit_scale=1.0, warnings=[])
    members, lintel_h, warnings = read_secondary(d)
    assert len(members) == 1 and members[0].kind == "GIANG_TUONG" and (members[0].b_mm, members[0].d_mm) == (220, 150)
    assert members[0].length_mm == pytest.approx(6000) and lintel_h == {"lt1": 200}
    assert any("chưa trừ khỏi khối xây" in w for w in warnings) and any("Not supported" in w for w in warnings)


def test_support_matrix_backed_by_tests():
    """Nhóm 'supported' phải có ít nhất một test chuẩn và một case âm tính, và các test đó tồn tại."""
    m = pd.read_csv(ROOT / "data/rules/ho_tro_cau_kien.csv", dtype=str, keep_default_na=False)
    assert set(m.trang_thai) <= {"supported", "conditional", "not_supported"}
    for row in m[m.trang_thai == "supported"].itertuples():
        refs = [r.strip() for r in row.kiem_thu.split(";") if r.strip()]
        assert len(refs) >= 2, row.cau_kien
        for ref in refs:
            f, name = ref.split("::")
            assert f"def {name}(" in (ROOT / f).read_text(encoding="utf-8"), ref
