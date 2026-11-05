"""Phần thô S4a: nhận cột từ vùng tô đặc, khối lượng cột, cốp pha cột, trừ cột khỏi tường."""
import pytest

from optimat.drawing.dxf_reader import Drawing, HatchItem
from optimat.drawing.review import ReviewWall
from optimat.rough.columns import Column, column_overlaps, column_works, detect_columns
from optimat.rough.models import ProjectParams


def drawing(hatches):
    return Drawing(segments=[], texts=[], blocks=[], hatches=hatches, layers=[], layer_classes={}, unit_scale=1.0, warnings=[])


def test_detect_columns_from_solid_fills():
    tri = [HatchItem("SOLID", "0", [[(0, 0), (220, 0), (220, 220)]]),           # cột 220×220 bị tách hai tam giác
           HatchItem("SOLID", "0", [[(0, 0), (220, 220), (0, 220)]])]
    square = HatchItem("SOLID", "HATCHTUONG", [[(5000, 0), (5200, 0), (5200, 200), (5000, 200)]])
    strip = HatchItem("SOLID", "0", [[(0, 3000), (2000, 3000), (2000, 3100), (0, 3100)]])     # dải dài: không phải cột
    tiny = HatchItem("SOLID", "0", [[(8000, 0), (8050, 0), (8050, 50)]])                       # mũi tên, ký hiệu nhỏ
    ansi = HatchItem("ANSI31", "0", [[(9000, 0), (9300, 0), (9300, 300), (9000, 300)]])        # không phải tô đặc
    cols = detect_columns(drawing(tri + [square, strip, tiny, ansi]))
    sizes = sorted((c.b_mm, c.h_mm) for c in cols)
    assert sizes == [(200, 200), (220, 220)]
    c220 = next(c for c in cols if c.b_mm == 220)
    assert c220.x == pytest.approx(110, abs=10) and c220.y == pytest.approx(110, abs=10)


def test_columns_far_apart_do_not_need_one_huge_grid():
    """Hai khung vẽ cách nhau 50 km trong một file (bản vẽ banve1, 02/11/2026): trước đây một lưới 10 mm phủ cả hai
    cần hàng trăm GiB; nay mỗi cụm một lưới, vẫn nhận đủ hai cột, id theo thứ tự quét lưới."""
    sq = lambda x, y: HatchItem("SOLID", "0", [[(x, y), (x + 220, y), (x + 220, y + 220), (x, y + 220)]])  # noqa: E731
    cols = detect_columns(drawing([sq(50_000_000, 40_000_000), sq(0, 0)]))
    assert [(c.id, c.b_mm, round(c.x, -3)) for c in cols] == [("C1", 220, 0), ("C2", 220, 50_000_000)]


def test_column_works_and_formwork():
    cols = [Column(id="C1", x=0, y=0, b_mm=220, h_mm=220), Column(id="C2", x=5000, y=0, b_mm=220, h_mm=220),
            Column(id="C3", x=9000, y=0, b_mm=220, h_mm=300), Column(id="C4", x=0, y=9000, b_mm=220, h_mm=220, keep=False)]
    works, warnings = column_works("T1", cols, 3300, ProjectParams(slab_thickness_mm=100))
    cot = next(w for w in works if w.code == "COT" and w.element.startswith("2 cột 220×220"))
    assert cot.quantity == pytest.approx(2 * 0.22 * 0.22 * 3.2, abs=1e-3)
    cp = next(w for w in works if w.code == "COP_PHA" and "220×300" in w.element)
    assert cp.quantity == pytest.approx(2 * (0.22 + 0.3) * 3.2, abs=1e-3)
    assert not warnings
    _, warnings = column_works("T1", cols, 3300, ProjectParams())
    assert "dày sàn" in warnings[0]


def test_wall_through_column_overlap():
    cols = [Column(id="C1", x=0, y=0, b_mm=220, h_mm=220), Column(id="C2", x=5000, y=0, b_mm=220, h_mm=220)]
    walls = [ReviewWall(id="W1", cls="220", x1=0, y1=0, x2=5000, y2=0),
             ReviewWall(id="W2", cls="110", x1=0, y1=2000, x2=4000, y2=2000)]
    assert column_overlaps(cols, walls) == {"W1": pytest.approx(220)}


def test_manual_and_removed_columns():
    from optimat.rough.columns import columns_from_dicts
    cols = columns_from_dicts([{"id": "C1", "x": 0, "y": 0, "b_mm": 220, "h_mm": 220},
                               {"id": "C2", "x": 3000, "y": 0, "b_mm": 300, "h_mm": 300, "source": "manual"},
                               {"id": "C3", "x": 6000, "y": 0, "b_mm": 220, "h_mm": 220, "keep": False}])
    works, _ = column_works("T1", cols, 3000, ProjectParams(slab_thickness_mm=0))
    cot = {w.element: w.quantity for w in works if w.code == "COT"}
    assert cot == {"1 cột 220×220": pytest.approx(0.145, abs=1e-3), "1 cột 300×300": pytest.approx(0.27)}
    assert columns_from_dicts(None) == []


def test_signal_columns_from_column_layer():
    from optimat.drawing.dxf_reader import Segment
    from optimat.rough.columns import signal_columns
    def rect(x, y, b, h, layer):
        p = [(x, y), (x + b, y), (x + b, y + h), (x, y + h)]
        return [Segment(*p[i], *p[(i + 1) % 4], layer, "small") for i in range(4)]
    d = Drawing(segments=rect(0, 0, 220, 300, "COT") + rect(1000, 0, 220, 220, "TUONG") + rect(2000, 0, 2000, 220, "COT"),
                texts=[], blocks=[], hatches=[], layers=["COT", "TUONG"], layer_classes={}, unit_scale=1.0, warnings=[])
    cols = signal_columns(d)       # chỉ hình cỡ cột trên layer cột; tường và dải dài bị bỏ
    assert [(c.b_mm, c.h_mm, c.x, c.y, c.source) for c in cols] == [(220, 300, 110, 150, "signal")]
    both = detect_columns(Drawing(segments=d.segments, texts=[], blocks=[], hatches=[HatchItem("SOLID", "0", [[(0, 0), (220, 0), (220, 300), (0, 300)]])],
                                  layers=d.layers, layer_classes={}, unit_scale=1.0, warnings=[]))
    assert len(both) == 1 and both[0].source == "hatch"     # cột tô đặc trùng cột ký hiệu: giữ một
