"""Nền bản vẽ gốc vẽ như phần mềm CAD và khớp tọa độ với lớp nhận dạng."""
import re

import ezdxf

from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.encoding import tcvn3_to_unicode
from optimat.drawing.render import DrawingRenderer, fix_vietnamese_text
from optimat.drawing.takeoff import compute_takeoff
from optimat.drawing.viewer import view_payload


def test_payload_has_cad_layer_and_overview(sample_dxf):
    d = read_drawing(sample_dxf)
    p = view_payload(d, compute_takeoff(d, 3300), "s.dxf")
    plan = p["plans"][0]
    assert plan["cad"].startswith('<g class="cad" transform="matrix(') and "<path" in plan["cad"]
    assert p["overview"]["cad"] and p["overview"]["size"][0] > 0
    assert view_payload(d, compute_takeoff(d, 3300), "s.dxf", cad=False)["plans"][0].get("cad") is None


def test_cad_transform_maps_drawing_to_viewer_coords(tmp_path):
    """Một đoạn thẳng biết trước phải rơi đúng tọa độ trang kiểm tra (mm, gốc trên trái, y hướng xuống)."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    msp.add_line((1000, 2000), (5000, 2000))
    msp.add_line((1000, 0), (1000, 3000))
    path = tmp_path / "a.dxf"
    doc.saveas(path)
    d = read_drawing(str(path))
    g = DrawingRenderer(d.doc, d.unit_scale).view(None, (1000.0, 3000.0), margin_mm=0).svg
    A, _, _, D, E, F = map(float, re.search(r"matrix\(([^)]*)\)", g).group(1).split(","))
    starts = [tuple(map(float, m)) for m in re.findall(r'<path d="M (-?[\d.]+) (-?[\d.]+)', g)]
    pts = {(round(A * x + E), round(D * y + F)) for x, y in starts}
    # điểm đầu (1000, 2000) và (1000, 0) của bản vẽ -> (0, 1000) và (0, 3000) trên trang kiểm tra
    assert pts == {(0, 1000), (0, 3000)}


def test_tcvn3_text_converted_for_display():
    doc = ezdxf.new("R2010")
    doc.styles.new("VN", dxfattribs={"font": ".VnTime.ttf"})
    raw = "MÆt b»ng tÇng 1"
    e = doc.modelspace().add_text(raw, dxfattribs={"style": "VN"})
    assert fix_vietnamese_text(doc) == 1
    assert e.dxf.text == tcvn3_to_unicode(raw) and e.dxf.style == "OPTIMAT_UNICODE"
