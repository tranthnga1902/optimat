"""Phần thô bước 2: xây, trát, lanh tô từ tường đã chốt."""
import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening, ReviewWall
from optimat.rough.models import ProjectParams
from optimat.rough.walls import wall_works


@pytest.fixture(scope="module")
def cat():
    return Catalog.from_csv(None)


WALLS = [ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01"),
         ReviewWall(id="W2", cls="110", role="partition", x1=0, y1=2000, x2=5000, y2=2000),
         ReviewWall(id="W3", cls="110", role="partition", x1=0, y1=4000, x2=3000, y2=4000, keep=False)]
OPENINGS = [ReviewOpening(id="O1", wall="W1", kind="door", w=1000, h=2200),
            ReviewOpening(id="O2", wall="W3", kind="door", w=800, h=2200)]      # gắn tường đã loại: bỏ qua


def by(works, code, element_start):
    return next(w for w in works if w.code == code and (w.element or "").startswith(element_start))


def test_full_params(cat):
    p = ProjectParams(beam_depth_mm=300, lintel_height_mm=200, lintel_bearing_mm=200, plaster_thickness_mm=15)
    works, warnings = wall_works("Tầng 1", 3300, WALLS, OPENINGS, p, cat)
    xay = by(works, "XAY", "tường 220")
    assert xay.wall_system_id == "W-GN01-220" and not xay.missing
    assert xay.quantity == pytest.approx(10 * 3.0 * 0.22 - 2.2 * 0.22 - 1.4 * 0.22 * 0.2, abs=1e-3)
    assert by(works, "TRAT", "tường 220 bao che, mặt ngoài").quantity == pytest.approx(27.8)
    assert by(works, "TRAT", "tường 220 bao che, mặt trong").variant == "15"
    part = by(works, "XAY", "tường 110")
    assert part.quantity == pytest.approx(5 * 3.0 * 0.11) and "phương án tường (vật liệu xây)" in part.missing
    assert by(works, "TRAT", "tường 110").quantity == pytest.approx(30.0)
    lt = by(works, "LANH_TO", "1 lanh tô")
    assert lt.quantity == pytest.approx(0.062, abs=1e-3) and not lt.missing
    cp = by(works, "COP_PHA", "cốp pha 1 lanh tô")
    assert cp.quantity == pytest.approx(1.0 * 0.22 + 2 * 1.4 * 0.2, abs=1e-3)
    assert not warnings


def test_missing_params_warn_not_guess(cat):
    works, warnings = wall_works("Tầng 1", 3300, WALLS, OPENINGS, ProjectParams(), cat)
    xay = by(works, "XAY", "tường 220")
    assert xay.quantity == pytest.approx(10 * 3.3 * 0.22 - 2.2 * 0.22, abs=1e-3)      # chưa trừ dầm, chưa trừ lanh tô
    assert any("chưa trừ dầm" in w for w in warnings) and any("chưa trừ lanh tô" in w for w in warnings)
    lt = by(works, "LANH_TO", "1 lanh tô")
    assert lt.quantity is None and set(lt.missing) == {"cao lanh tô", "chiều dài gối lanh tô"}
    assert by(works, "TRAT", "tường 220").missing == ["chiều dày trát"]


def test_column_volume_deducted(cat):
    p = ProjectParams(beam_depth_mm=300)
    works, _ = wall_works("Tầng 1", 3300, WALLS[:1], [], p, cat, column_len_in_walls={"W1": 440})
    assert works[0].quantity == pytest.approx((10 - 0.44) * 3.0 * 0.22, abs=1e-3)


def test_beam_deeper_than_floor_rejected(cat):
    with pytest.raises(ValueError):
        wall_works("Tầng 1", 300, WALLS, [], ProjectParams(beam_depth_mm=400), cat)


def test_from_auto_takeoff(sample_dxf, cat):
    from optimat.drawing.takeoff import takeoff_from_file
    from optimat.rough.walls import review_input_from_takeoff
    result = takeoff_from_file(sample_dxf, 3300)
    walls, openings, systems = review_input_from_takeoff(result)
    works, _ = wall_works("Mẫu", 3300, walls, openings, ProjectParams(), cat, systems)
    area = sum(w.quantity for w in works if w.code == "TRAT")
    net = sum(2 * g.net_area_m2 for g in result.groups)            # mọi tường trát hai mặt
    assert area == pytest.approx(net, rel=0.01)          # cùng công thức diện tích với bước đo bóc
