"""Vẽ lại bản vẽ DXF đúng như phần mềm CAD (giống DWG FastView): đủ mọi đối tượng, màu theo layer (ACI),
kiểu nét, chữ, hatch, kích thước, block; nền đen, nét mảnh 1 px không phụ thuộc mức phóng.

Dùng bộ vẽ của ezdxf (ezdxf.addons.drawing, xuất SVG). Lớp nhận dạng (tường, cửa) trên trang kiểm tra được đặt
chồng lên đúng tọa độ nhờ ma trận biến đổi mà hàm trả về.

Chữ TCVN3 (font .VnTime...) được chuyển sang Unicode và vẽ bằng font Unicode để hiện đúng tiếng Việt.
"""
from __future__ import annotations

import copy
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from .encoding import detect_encoding, tcvn3_to_unicode

UNICODE_STYLE = "OPTIMAT_UNICODE"
UNICODE_FONT = "arial.ttf"
_SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _SVG_NS)


@dataclass
class RenderedView:
    svg: str              # nội dung <g> đã đặt về tọa độ của trang kiểm tra (mm, gốc góc trên trái, y hướng xuống)
    background: str       # màu nền dùng khi vẽ
    display_bbox: tuple[float,float,float,float] | None = None  # viewer mm, y xuống; không phải bbox nhận diện


def _style_font(doc, name: str) -> str:
    try:
        return doc.styles.get(name).dxf.get("font", "") or ""
    except Exception:  # noqa: BLE001 - kiểu chữ không tồn tại
        return ""


def fix_vietnamese_text(doc) -> int:
    """Chuyển chữ TCVN3 trong mọi layout và block sang Unicode, gán kiểu chữ Unicode. Trả về số đối tượng đã chuyển."""
    if UNICODE_STYLE not in doc.styles:
        doc.styles.new(UNICODE_STYLE, dxfattribs={"font": UNICODE_FONT})
    changed = 0
    spaces = [doc.modelspace()] + [b for b in doc.blocks if not b.name.lower().startswith("*paper")]
    for space in spaces:
        for e in space.query("TEXT MTEXT ATTRIB ATTDEF"):
            font = _style_font(doc, e.dxf.get("style", "Standard"))
            if e.dxftype() == "MTEXT":
                raw = e.text
                inline = re.search(r"\\f\.?vn", raw, re.I) is not None
                if detect_encoding(font, raw) == "tcvn3" or inline:
                    e.text = re.sub(r"\\f[^;|]*(\|[^;]*)?;", r"\\fArial;", tcvn3_to_unicode(raw))
                    e.dxf.style = UNICODE_STYLE
                    changed += 1
            else:
                raw = e.dxf.get("text", "")
                if raw and detect_encoding(font, raw) == "tcvn3":
                    e.dxf.text = tcvn3_to_unicode(raw)
                    e.dxf.style = UNICODE_STYLE
                    changed += 1
        if space is not spaces[0]:
            continue
        for ins in space.query("INSERT"):
            for a in ins.attribs:
                font = _style_font(doc, a.dxf.get("style", "Standard"))
                if detect_encoding(font, a.dxf.text) == "tcvn3":
                    a.dxf.text = tcvn3_to_unicode(a.dxf.text)
                    a.dxf.style = UNICODE_STYLE
                    changed += 1
    return changed


class DrawingRenderer:
    """Vẽ một lần cả modelspace, sau đó cắt ra từng vùng (mỗi mặt bằng) mà không phải vẽ lại."""

    def __init__(self, doc, unit_scale: float):
        from ezdxf.addons.drawing import Frontend, RenderContext, config
        from ezdxf.addons.drawing.svg import SVGBackend

        self.scale = unit_scale or 1.0
        fix_vietnamese_text(doc)
        self.backend = SVGBackend()
        cfg = config.Configuration(background_policy=config.BackgroundPolicy.BLACK,
                                   color_policy=config.ColorPolicy.COLOR,
                                   lineweight_policy=config.LineweightPolicy.ABSOLUTE)
        Frontend(RenderContext(doc), self.backend, config=cfg).draw_layout(doc.modelspace(), finalize=True)
        bounds = self.backend.player().bbox()
        self.bounds_mm = None
        if bounds.has_data:
            values = (bounds.extmin.x*self.scale,bounds.extmin.y*self.scale,
                      bounds.extmax.x*self.scale,bounds.extmax.y*self.scale)
            if all(math.isfinite(v) for v in values):
                self.bounds_mm = values

    def view(self, bbox_mm: tuple[float, float, float, float] | None, origin_mm: tuple[float, float],
             margin_mm: float = 1500.0) -> RenderedView:
        """bbox_mm: vùng cần vẽ (tọa độ bản vẽ đã đổi ra mm); None là cả bản vẽ.
        origin_mm = (x0, y1): gốc mà trang kiểm tra dùng (x trừ x0, y lấy y1 trừ y)."""
        from ezdxf.addons.drawing import layout
        from ezdxf.math import BoundingBox2d, Vec2

        s = self.scale
        backend = copy.deepcopy(self.backend)          # get_string biến đổi bản ghi tại chỗ: dùng bản sao
        box = None
        visible_mm = self.bounds_mm
        if bbox_mm is not None:
            x0, y0, x1, y1 = bbox_mm
            box = BoundingBox2d([Vec2((x0 - margin_mm) / s, (y0 - margin_mm) / s), Vec2((x1 + margin_mm) / s, (y1 + margin_mm) / s)])
            visible_mm = (x0-margin_mm,y0-margin_mm,x1+margin_mm,y1+margin_mm)
        page = layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(0))
        settings = layout.Settings(output_coordinate_space=1_000_000, crop_at_margins=box is not None)
        root = backend.get_xml_root_element(page, settings=settings, render_box=box)
        m = backend.transformation_matrix
        if m is None:
            return RenderedView("", "#000000")
        p0, p1 = m.transform((0, 0, 0)), m.transform((1, 1, 0))
        a, b = p1.x - p0.x, p1.y - p0.y               # hệ số tỉ lệ theo x, y (b âm: trục y lật)
        c, d = p0.x, p0.y
        ox, oy = origin_mm
        # tọa độ SVG (sx, sy) -> tọa độ trang kiểm tra (mm): vx = s*(sx-c)/a - ox ; vy = oy - s*(sy-d)/b
        A, D = s / a, -s / b
        E, F = -s * c / a - ox, oy + s * d / b
        inner = "".join(ET.tostring(child, encoding="unicode") for child in root)
        inner = re.sub(r"stroke-width: [0-9.]+;", "stroke-width: 1px;", inner)
        inner = re.sub(r'stroke-width="[0-9.]+"', 'stroke-width="1px"', inner)
        inner = inner.replace("ns0:", "").replace(' xmlns:ns0="http://www.w3.org/2000/svg"', "")
        g = (f'<g class="cad" transform="matrix({A:.9g},0,0,{D:.9g},{E:.6f},{F:.6f})">'
             '<style>.cad path,.cad polyline,.cad polygon,.cad line,.cad circle,.cad ellipse{vector-effect:non-scaling-stroke}</style>'
             f"{inner}</g>")
        display = None if visible_mm is None else (visible_mm[0]-ox,oy-visible_mm[3],visible_mm[2]-ox,oy-visible_mm[1])
        return RenderedView(g, "#000000", display)


def render_drawing(drawing, bbox_mm=None, origin_mm=(0.0, 0.0)) -> RenderedView | None:
    """Tiện ích một lần: None khi bản vẽ không còn tài liệu ezdxf gốc."""
    if getattr(drawing, "doc", None) is None:
        return None
    return DrawingRenderer(drawing.doc, drawing.unit_scale).view(bbox_mm, origin_mm)
