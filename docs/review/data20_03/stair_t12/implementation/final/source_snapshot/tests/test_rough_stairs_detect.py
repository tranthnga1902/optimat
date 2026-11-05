"""Nhận thang tự động trên mặt bằng: chuỗi nét mũi bậc song song, cùng dài, cách đều."""
from optimat.drawing.dxf_reader import Drawing, Segment
from optimat.rough.stairs import building_stairs, detect_stairs


def _drawing(segs) -> Drawing:
    return Drawing(segments=segs, texts=[], blocks=[], hatches=[], layers=["0"], layer_classes={}, unit_scale=1.0, warnings=[])


def _flight(x0, n, width=1000, tread=250, y0=0.0):
    return [Segment(x0, y0 + i * tread, x0 + width, y0 + i * tread, "0") for i in range(n)]


def test_two_flight_stair_with_landing():
    st = detect_stairs(_drawing(_flight(0, 9) + _flight(1100, 9)))
    assert len(st) == 1
    s = st[0]
    assert s.steps == 20 and s.flight_width_mm == 1000 and s.tread_mm == 250 and s.source == "auto"
    assert s.landing_area_m2 == 2.1          # bề ngang hai vế 2,1 m × bề rộng vế 1 m


def test_tile_grid_is_not_a_stair():
    rows = _flight(0, 9, width=1200, tread=300)
    cols = [Segment(x, 0, x, 2400, "0") for x in (300, 600, 900)]   # lưới gạch: nét vuông góc cắt ngang cả vế
    assert detect_stairs(_drawing(rows + cols)) == []


def test_partial_flight_does_not_take_unscoped_template():
    full = _drawing(_flight(0, 9) + _flight(1100, 9))
    cut = _drawing(_flight(0, 3))            # tầng trệt: vài bậc trước đường cắt
    roof = _drawing(_flight(0, 9))
    stairs, notes = building_stairs([cut, full, roof], ["MẶT BẰNG TRỆT", "MẶT BẰNG LẦU 1", "MẶT BẰNG SÂN THƯỢNG"])
    assert stairs[0][0].steps == 4 and stairs[1][0].steps == 20
    assert stairs[2] == []                   # thang trên sân thượng là thang đi xuống, không tính thêm
    assert any(n.startswith("MẶT BẰNG TRỆT:") and "không sao chép" in n for n in notes)
