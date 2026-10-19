"""Các tình huống của bản vẽ thật: tường trên layer tên lạ, hatch bị phá thành nét rời, cửa vẽ bằng cung tròn,
nhiều mặt bằng trong một file kèm cao độ. Bản vẽ được sinh ngay trong bài kiểm thử."""
import ezdxf
import pytest

from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.takeoff import compute_takeoff, takeoff_plans
from optimat.schemas import OpeningDefaults


def _house(msp, ox: float, oy: float, title: str, layer: str = "NET_1") -> None:
    """Nhà 6 x 4 m, tường 220 trên layer tên lạ; tường trước bị ngắt tại cửa đi 900 có cung cánh cửa."""
    W, L, T = 6000, 4000, 220
    p = lambda pts: [(ox + x, oy + y) for x, y in pts]
    # ba cạnh liền
    msp.add_lwpolyline(p([(1950, 0), (W, 0), (W, L), (0, L), (0, 0), (1050, 0)]), dxfattribs={"layer": layer})
    msp.add_lwpolyline(p([(1950, T), (W - T, T), (W - T, L - T), (T, L - T), (T, T), (1050, T)]),
                       dxfattribs={"layer": layer})
    # cánh cửa: cung 90 độ bán kính 900, tâm tại bản lề
    msp.add_arc((ox + 1050, oy + T), 900, 0, 90, dxfattribs={"layer": "NOI THAT"})
    # hatch gạch bị phá: các nét xiên ngắn cách đều nằm trong tường trên (đưa vào block vô danh như phần mềm xuất)
    for k in range(40):
        x = ox + 300 + k * 120
        msp.add_line((x, oy + L - T + 10), (x + 200, oy + L - 10), dxfattribs={"layer": "HATCH"})
    # bậc thang: các nét song song cách đều cắt ngang hai thành thang 110
    for k in range(10):
        y = oy + 800 + k * 250
        msp.add_line((ox + 3000, y), (ox + 4000, y), dxfattribs={"layer": "NET_1"})
    msp.add_line((ox + 3000, oy + 700), (ox + 3000, oy + 3200), dxfattribs={"layer": "NET_1"})
    msp.add_line((ox + 3110, oy + 700), (ox + 3110, oy + 3200), dxfattribs={"layer": "NET_1"})
    msp.add_text(title, dxfattribs={"layer": "TEXT", "height": 300}).set_placement((ox + 1500, oy - 1200))


@pytest.fixture(scope="module")
def messy_dxf(tmp_path_factory):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for name in ("NET_1", "NOI THAT", "HATCH", "TEXT"):
        doc.layers.add(name)
    _house(msp, 0, 0, "MẶT BẰNG TẦNG 1")
    _house(msp, 20000, 0, "MẶT BẰNG TẦNG 2 (+3.60)")
    msp.add_text("%%p0.000", dxfattribs={"layer": "TEXT", "height": 200}).set_placement((2500, 2000))
    path = tmp_path_factory.mktemp("dxf") / "nha_that.dxf"
    doc.saveas(path)
    return str(path)


def test_loose_hatch_and_stairs_marked(messy_dxf):
    d = read_drawing(messy_dxf)
    kinds = {}
    for s in d.segments:
        kinds.setdefault(s.layer, set()).add(s.kind)
    assert "hatch" in kinds["HATCH"]                       # nét hatch rời được nhận ra
    assert sum(1 for s in d.segments if s.layer == "NET_1" and s.kind == "hatch") >= 20   # bậc thang của 2 nhà
    assert len(d.arcs) == 2


def test_wall_layer_found_by_geometry_and_door_bridged(messy_dxf):
    plans = takeoff_plans(read_drawing(messy_dxf), openings=OpeningDefaults(door_height_mm=2200))
    assert [p.name for p in plans] == ["MẶT BẰNG TẦNG 1", "MẶT BẰNG TẦNG 2 (+3.60)"]
    r = plans[0].result
    assert r.wall_layers == ["NET_1"] and r.auto_wall_layers == ["NET_1"]
    assert all(w.thickness_class == "220" for w in r.walls)          # thành thang không bị tính là tường
    g = {(x.wall_type, x.role): x for x in r.groups}[("220", "envelope")]
    # trục tim: 2 x 5,78 + 2 x 3,78 = 19,12 m, cửa đi được nối qua và trừ 0,9 x 2,2
    assert g.length_m == pytest.approx(19.12, abs=0.02)
    assert [(o.kind, o.width_mm) for o in r.openings] == [("door", 900)]
    assert g.opening_area_m2 == pytest.approx(0.9 * 2.2, abs=0.01)


def test_levels_give_floor_height(messy_dxf):
    plans = takeoff_plans(read_drawing(messy_dxf))
    assert plans[0].level_m == 0.0 and plans[1].level_m == pytest.approx(3.6)
    assert plans[0].height_mm == 3600 and plans[0].height_source == "cao độ tầng trên"
    assert plans[1].height_mm is None and plans[1].height_source == "chưa có"
    assert plans[1].result.groups == [] and any("Chưa có chiều cao tầng" in w for w in plans[1].result.warnings)


def test_missing_opening_size_not_subtracted(messy_dxf):
    """Dự án chưa nhập kích thước cửa: cửa vẫn được nối qua nhưng không trừ lỗ mở, có cảnh báo (Quy ước B7)."""
    r = takeoff_plans(read_drawing(messy_dxf))[0].result
    g = {(x.wall_type, x.role): x for x in r.groups}[("220", "envelope")]
    assert g.length_m == pytest.approx(19.12, abs=0.02) and g.opening_area_m2 == 0
    assert r.openings == [] and any("chưa có kích thước" in w and "Cửa đi" in w for w in r.warnings)


def test_user_choice_disables_auto_detection(messy_dxf):
    d = read_drawing(messy_dxf, {"TEXT": "WALL"})
    r = compute_takeoff(d, 3300)
    assert r.auto_wall_layers == [] and r.walls == []


def test_api_plans_endpoint(messy_dxf):
    from fastapi.testclient import TestClient

    from optimat.api.main import app
    with open(messy_dxf, "rb") as f:
        r = TestClient(app).post("/api/takeoff/plans", files={"file": ("nha.dxf", f, "application/dxf")})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2 and body[0]["height_source"] == "cao độ tầng trên"
