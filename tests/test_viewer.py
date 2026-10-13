"""Trang xem bóc tách: dữ liệu nhúng khớp kết quả đo bóc, không còn chỗ giữ dữ liệu."""
import json
import re

from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.takeoff import compute_takeoff
from optimat.drawing.viewer import build_viewer_html, viewer_data


def test_viewer_data_matches_takeoff(sample_dxf):
    drawing = read_drawing(sample_dxf)
    result = compute_takeoff(drawing, 3300)
    data = viewer_data(drawing, result, "sample_floor.dxf")
    assert len(data["walls"]) == len(result.walls) and len(data["segs"]) == len(drawing.segments)
    assert {o["wall"] for o in data["openings"]} <= {w["id"] for w in data["walls"]}
    # trục y lật: mọi tọa độ nằm trong khung bản vẽ
    w, h = data["size"]
    assert all(0 <= s[0] <= w and 0 <= s[1] <= h for s in data["segs"])


def test_viewer_html_embeds_data(sample_dxf):
    drawing = read_drawing(sample_dxf)
    html = build_viewer_html(drawing, compute_takeoff(drawing, 3300), "sample_floor.dxf")
    assert "/*__DATA__*/" not in html and "<title>" in html
    payload = json.loads(re.search(r"const ALL = (\{.*?\});\n", html, re.S).group(1))
    assert payload["file"] == "sample_floor.dxf" and len(payload["plans"]) == 1


def test_openings_recorded(sample_dxf):
    result = compute_takeoff(read_drawing(sample_dxf), 3300)
    assert [o.name for o in result.openings] == ["D1", "S1"] and all(o.wall_id for o in result.openings)
