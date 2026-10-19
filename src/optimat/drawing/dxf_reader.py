"""Đọc bản vẽ DXF (hoặc DWG qua chuyển đổi) bằng ezdxf, đưa về cấu trúc đơn giản, đơn vị mm.

Bản vẽ thật thường không sạch: nét tường nằm trong block, hatch bị phá thành hàng nghìn nét rời
(khi xuất qua phần mềm xem nhanh), cửa vẽ bằng cung tròn. Bộ đọc vì thế:
- mở block lồng nhau (tối đa 4 cấp) để lấy nét thật ở tọa độ thế giới;
- nhận ra block chỉ gồm nét song song cách đều (hatch đã bị phá), đánh dấu các nét đó là "hatch"
  và dựng lại vùng hatch, để chúng không bị ghép nhầm thành tường;
- đọc cung tròn (kể cả cung trong polyline) để tìm cánh cửa;
- đọc vùng tô đặc (SOLID, TRACE, HATCH tô đặc) làm dấu hiệu cột, vách bê tông.
"""
from __future__ import annotations

import math
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import ezdxf
from ezdxf import disassemble
from ezdxf import path as ezpath
from ezdxf import units

from .dwg_convert import DrawingError, convert_dwg_to_dxf
from .encoding import to_unicode
from .layer_classifier import LayerClass, apply_overrides, default_classification

# Quy tắc chung: mọi tọa độ lấy từ đối tượng phải đổi sang hệ tọa độ thế giới (WCS). Đối tượng 2D (ARC, CIRCLE, SOLID,
# TEXT, HATCH...) ghi tọa độ theo hệ OCS của nó; block lật gương hoặc vẽ lật làm OCS khác WCS.
MAX_BLOCK_DEPTH = 16
HATCH_MIN_LINES = 8          # block có ít nhất chừng này nét cùng phương, cách đều, thì coi là hatch bị phá
FLATTEN_MM = 10.0            # sai lệch tối đa khi chia đường cong (đường tròn, elip, spline, biên hatch) thành đoạn thẳng
# Đối tượng chú thích hoặc không có hình trên mặt bằng: bỏ qua có chủ ý, không cảnh báo
_IGNORED = {"DIMENSION", "ARC_DIMENSION", "LEADER", "MLEADER", "MULTILEADER", "TOLERANCE", "POINT", "XLINE", "RAY",
            "VIEWPORT", "IMAGE", "WIPEOUT", "OLE2FRAME", "ATTDEF", "ACAD_TABLE", "SEQEND", "VERTEX"}


@dataclass
class Segment:
    x1: float
    y1: float
    x2: float
    y2: float
    layer: str
    kind: str = "line"       # line | hatch (nét của hatch bị phá) | small (cạnh của hình kín nhỏ, thường là cột)
    source: str = ""         # tên block chứa nét, rỗng nếu nằm thẳng trong model


@dataclass
class TextItem:
    text: str
    x: float
    y: float
    layer: str
    encoding: str
    height: float = 0.0


@dataclass
class BlockRef:
    name: str
    x: float
    y: float
    layer: str
    attribs: dict = field(default_factory=dict)


@dataclass
class HatchItem:
    pattern: str
    layer: str
    polygons: list[list[tuple[float, float]]]   # các đường biên; biên nằm trong biên khác là lỗ rỗng


@dataclass
class ArcItem:
    cx: float
    cy: float
    r: float
    start: float             # độ
    end: float
    layer: str
    source: str = ""

    @property
    def sweep(self) -> float:
        return (self.end - self.start) % 360


@dataclass
class Drawing:
    segments: list[Segment]
    texts: list[TextItem]
    blocks: list[BlockRef]
    hatches: list[HatchItem]
    layers: list[str]
    layer_classes: dict[str, LayerClass]
    unit_scale: float
    warnings: list[str]
    arcs: list[ArcItem] = field(default_factory=list)
    user_wall_layers: bool = False   # người dùng đã chỉ định layer tường: không tự nhận thêm
    doc: object = field(default=None, repr=False, compare=False)
    rejected_pairs: list = field(default_factory=list, repr=False, compare=False)   # cặp nét bị loại khi nhận tường   # tài liệu ezdxf gốc, để vẽ lại đúng như phần mềm CAD


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _is_hatch_like(lines: list[tuple[float, float, float, float]]) -> bool:
    """Nhiều nét cùng phương và cách đều nhau: dấu hiệu hatch đã bị phá thành nét rời."""
    if len(lines) < HATCH_MIN_LINES:
        return False
    angles = Counter()
    for x1, y1, x2, y2 in lines:
        if math.hypot(x2 - x1, y2 - y1) > 1e-6:
            angles[round(math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180)] += 1
    if not angles:
        return False
    ang, count = angles.most_common(1)[0]
    if count < HATCH_MIN_LINES:
        return False
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    offsets = sorted({round(-uy * x1 + ux * y1) for x1, y1, x2, y2 in lines
                      if round(math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180) == ang})
    gaps = [b - a for a, b in zip(offsets, offsets[1:]) if b - a > 0]
    if len(gaps) < HATCH_MIN_LINES - 2:
        return False
    common, n = Counter(gaps).most_common(1)[0]
    near = sum(1 for g in gaps if abs(g - common) <= 2)
    return near / len(gaps) >= 0.6 and common < 400


class _Collector:
    def __init__(self, doc, scale: float):
        self.doc, self.s = doc, scale
        self.segments: list[Segment] = []
        self.arcs: list[ArcItem] = []
        self.hatches: list[HatchItem] = []
        self.texts: list[TextItem] = []
        self.blocks: list[BlockRef] = []
        self.warnings: list[str] = []
        self.skipped: Counter = Counter()

    def seg(self, a, b, layer, kind="line", source=""):
        s = self.s
        self.segments.append(Segment(a[0] * s, a[1] * s, b[0] * s, b[1] * s, layer, kind, source))

    def arc(self, e, source=""):
        c, s = e.dxf.center, self.s
        start, end = e.dxf.start_angle, e.dxf.end_angle
        if e.dxf.extrusion.z < 0:
            # cung lật (block lật gương): tâm, góc ghi theo hệ OCS; đổi sang WCS, chiều quay đảo nên đổi đầu cuối
            c = e.ocs().to_wcs(c)
            a, b = e.start_point, e.end_point
            start = math.degrees(math.atan2(b.y - c.y, b.x - c.x)) % 360
            end = math.degrees(math.atan2(a.y - c.y, a.x - c.x)) % 360
        self.arcs.append(ArcItem(c.x * s, c.y * s, e.dxf.radius * s, start, end, e.dxf.layer, source))

    def polyline(self, e, source=""):
        try:
            parts = list(e.virtual_entities())          # tách cả đoạn cong (bulge) thành ARC
        except Exception:                               # polyface, mesh: bỏ qua
            return
        pts = []
        for p in parts:
            if p.dxftype() == "LINE":
                pts.append(((p.dxf.start.x, p.dxf.start.y), (p.dxf.end.x, p.dxf.end.y)))
            elif p.dxftype() == "ARC":
                self.arc(p, source)
        small = False
        closed = e.closed if e.dxftype() == "LWPOLYLINE" else e.is_closed
        if closed and pts:
            xs = [c for a, b in pts for c in (a[0], b[0])]
            ys = [c for a, b in pts for c in (a[1], b[1])]
            small = max(max(xs) - min(xs), max(ys) - min(ys)) * self.s <= 600 and len(pts) <= 8
        for a, b in pts:
            self.seg(a, b, e.dxf.layer, "small" if small else "line", source)
        if getattr(e, "has_width", False):            # pline có bề rộng hiện thành dải tô đặc: thêm vùng tô đúng hình
            mesh = disassemble.make_primitive(e, FLATTEN_MM / self.s).mesh
            if mesh is not None:
                faces = [[(v.x * self.s, v.y * self.s) for v in f] for f in mesh.faces_as_vertices()]
                self.hatches.append(HatchItem("SOLID", e.dxf.layer, [f for f in faces if len(f) >= 3]))

    def solid(self, e, source=""):
        s, ocs = self.s, e.ocs()
        vs = [ocs.to_wcs(e.dxf.get(f"vtx{i}")) for i in range(4) if e.dxf.hasattr(f"vtx{i}")]
        pts = [(v.x * s, v.y * s) for v in vs]
        if len(pts) >= 3:
            self.hatches.append(HatchItem("SOLID", e.dxf.layer, [_convex_hull(pts)]))

    def hatch(self, e):
        s = self.s
        polygons = []
        for p in ezpath.from_hatch(e):                  # biên đã ở WCS, cạnh cong được chia nhỏ
            pts = [(v.x * s, v.y * s) for v in p.flattening(FLATTEN_MM / s)]
            if len(pts) >= 3:
                polygons.append(pts)
        if polygons:
            self.hatches.append(HatchItem(e.dxf.pattern_name, e.dxf.layer, polygons))

    def curve(self, e, source=""):
        """CIRCLE, ELLIPSE, SPLINE: chia thành đoạn thẳng ở WCS; hình kín nhỏ (cột tròn) đánh dấu "small" như polyline."""
        pts = [(v.x, v.y) for v in disassemble.make_primitive(e, FLATTEN_MM / self.s).vertices()]
        if len(pts) < 2:
            return
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        closed = math.dist(pts[0], pts[-1]) * self.s < 1
        small = closed and max(max(xs) - min(xs), max(ys) - min(ys)) * self.s <= 600
        for a, b in zip(pts, pts[1:]):
            self.seg(a, b, e.dxf.layer, "small" if small else "line", source)

    def face(self, e, source=""):
        """3DFACE: các cạnh nhìn thấy (đã ở WCS)."""
        vs = [e.dxf.get(f"vtx{i}") for i in range(4)]
        for i in range(4):
            a, b = vs[i], vs[(i + 1) % 4]
            if not e.is_invisible_edge(i) and a.distance(b) > 1e-9:
                self.seg((a.x, a.y), (b.x, b.y), e.dxf.layer, "line", source)

    def text(self, e):
        raw = e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text
        if not raw.strip():
            return
        raw = _clean_codes(raw)
        style_name = e.dxf.get("style", "Standard")
        styles = self.doc.styles
        font = styles.get(style_name).dxf.get("font", None) if style_name in styles else None
        text, enc = to_unicode(raw, font)
        if enc == "vni":
            self.warnings.append(f"Chữ dùng bảng mã VNI chưa được chuyển: {raw[:30]!r}")
        # MTEXT ghi điểm chèn ở WCS; TEXT, ATTRIB ghi ở OCS
        p = e.dxf.insert if e.dxftype() == "MTEXT" else e.ocs().to_wcs(e.dxf.insert)
        h = e.dxf.get("char_height", 0) if e.dxftype() == "MTEXT" else e.dxf.get("height", 0)
        self.texts.append(TextItem(text, p.x * self.s, p.y * self.s, e.dxf.layer, enc, (h or 0) * self.s))

    def walk(self, entities, source: str = "", depth: int = 0) -> None:
        for e in entities:
            t = e.dxftype()
            if t == "LINE":
                a, b = e.dxf.start, e.dxf.end
                self.seg((a.x, a.y), (b.x, b.y), e.dxf.layer, "line", source)
            elif t in ("LWPOLYLINE", "POLYLINE"):
                self.polyline(e, source)
            elif t == "ARC":
                self.arc(e, source)
            elif t in ("CIRCLE", "ELLIPSE", "SPLINE"):
                self.curve(e, source)
            elif t in ("SOLID", "TRACE"):
                self.solid(e, source)
            elif t == "3DFACE":
                self.face(e, source)
            elif t == "HATCH":
                self.hatch(e)
            elif t in ("TEXT", "MTEXT"):
                self.text(e)
            elif t in ("INSERT", "MLINE"):
                if depth < MAX_BLOCK_DEPTH:
                    self.insert(e, source, depth)
                else:
                    self.skipped[f"block lồng quá {MAX_BLOCK_DEPTH} cấp"] += 1
            elif t not in _IGNORED:
                self.skipped[t] += 1

    def insert(self, e, source: str, depth: int) -> None:
        if e.dxftype() == "INSERT" and e.mcount > 1:      # MINSERT: chèn thành mảng hàng × cột
            for one in e.multi_insert():
                self.insert(one, source, depth)
            return
        try:
            children = list(e.virtual_entities())
        except Exception:
            self.skipped[f"{e.dxftype()} không mở được"] += 1
            return
        if e.dxftype() == "INSERT":
            p = e.ocs().to_wcs(e.dxf.insert)
            self.blocks.append(BlockRef(block_name(e), p.x * self.s, p.y * self.s, e.dxf.layer,
                                        {a.dxf.tag.upper(): a.dxf.text for a in e.attribs}))
        for a in getattr(e, "attribs", []):             # chữ trong thuộc tính block (ký hiệu cao độ, tên phòng...)
            self.text(a)
        if e.dxftype() == "MLINE":
            self.walk(children, source, depth + 1)
            return
        name = block_name(e) if e.dxftype() == "INSERT" else e.dxf.name
        lines = [(c.dxf.start.x, c.dxf.start.y, c.dxf.end.x, c.dxf.end.y) for c in children if c.dxftype() == "LINE"]
        if _is_hatch_like(lines):
            for x1, y1, x2, y2 in lines:
                self.seg((x1, y1), (x2, y2), e.dxf.layer, "hatch", name)
            pts = [(x * self.s, y * self.s) for x1, y1, x2, y2 in lines for x, y in ((x1, y1), (x2, y2))]
            self.hatches.append(HatchItem("*EXPLODED*", e.dxf.layer, [_convex_hull(pts)]))
            rest = [c for c in children if c.dxftype() != "LINE"]
            self.walk(rest, name, depth + 1)
            return
        self.walk(children, name if not source else f"{source}/{name}", depth + 1)


def block_name(e) -> str:
    """Tên block; block động lưu thành block ẩn danh *U… thì lấy tên block gốc (xdata AcDbBlockRepBTag)."""
    name = e.dxf.name
    doc = getattr(e, "doc", None)
    if name.startswith("*") and doc is not None:
        try:
            rec = doc.blocks.get(name).block_record
            handle = next(v for c, v in rec.get_xdata("AcDbBlockRepBTag") if c == 1005)
            return doc.entitydb[handle].dxf.name
        except Exception:     # không phải block động (bảng, kích thước…): giữ tên ẩn danh
            pass
    return name


def _clean_codes(raw: str) -> str:
    """Mã điều khiển chữ của AutoCAD: %%U gạch chân, %%C đường kính, %%P cộng trừ, %%D độ."""
    for code, rep in (("%%U", ""), ("%%u", ""), ("%%C", "Ø"), ("%%c", "Ø"), ("%%P", "±"), ("%%p", "±"),
                      ("%%D", "°"), ("%%d", "°")):
        raw = raw.replace(code, rep)
    return raw


def mark_loose_hatch(segments: list[Segment]) -> int:
    """Hatch bị phá thẳng ra model (không nằm trong block): họ nét cùng layer, cùng phương, cách đều nhau.

    Bậc cầu thang và ngói mái cũng có dạng này; đánh dấu chúng là hatch để không bị ghép nhầm thành tường.
    Trả về số nét đã đánh dấu.
    """
    groups: dict[tuple[str, int], list[int]] = {}
    for i, sg in enumerate(segments):
        if sg.kind != "line":
            continue
        dx, dy = sg.x2 - sg.x1, sg.y2 - sg.y1
        if math.hypot(dx, dy) < 1e-6:
            continue
        groups.setdefault((sg.layer, round(math.degrees(math.atan2(dy, dx)) % 180)), []).append(i)
    marked = 0
    for (layer, ang), idx in groups.items():
        if len(idx) < HATCH_MIN_LINES:
            continue
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        # gom các nét cùng khoảng cách vuông góc (nhiều mặt bằng cạnh nhau có nét trùng hàng)
        by_off: dict[int, list[int]] = {}
        for i in idx:
            by_off.setdefault(round(-uy * segments[i].x1 + ux * segments[i].y1), []).append(i)
        offs = sorted(by_off)
        runs, run = [], [offs[0]]
        for prev, cur in zip(offs, offs[1:]):
            gap = cur - prev
            ok = 1 < gap < 400 and (len(run) < 2 or abs(gap - (run[1] - run[0])) <= 2)
            if ok:
                run.append(cur)
            else:
                runs.append(run)
                run = [cur] if not (1 < gap < 400) else [prev, cur]
        runs.append(run)
        for run in runs:
            if len(run) < HATCH_MIN_LINES:
                continue
            members = [i for o in run for i in by_off[o]]
            lengths = sorted(math.hypot(segments[i].x2 - segments[i].x1, segments[i].y2 - segments[i].y1) for i in members)
            median = lengths[len(lengths) // 2]
            for i in members:      # bỏ qua nét dài bất thường trùng hàng (thường là tường)
                if math.hypot(segments[i].x2 - segments[i].x1, segments[i].y2 - segments[i].y1) <= 3 * median:
                    segments[i].kind = "hatch"
                    marked += 1
    return marked


MISMATCH_WARNING = "Bản vẽ có thể bị đọc sai vị trí so với phần mềm CAD, cần kiểm tra lại trước khi đo bóc."
_READ_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "SOLID", "TRACE", "3DFACE", "HATCH"}


def geometry_mismatch(drawing: Drawing, tol_mm: float = 2 * FLATTEN_MM) -> dict[str, float]:
    """Đối chiếu hình đã đọc với ezdxf (mở block và đổi tọa độ bằng đường riêng của ezdxf).

    Mọi điểm đã đọc (đầu nét, đầu cung, đỉnh vùng tô, biên hatch) phải trùng một điểm ezdxf vẽ ra (lệch tối đa 1 mm),
    và khung toàn bản vẽ phải khớp trong tol_mm. Trả {layer: số điểm lệch} và "*" (độ lệch khung, mm); rỗng là đọc đúng.
    """
    from ezdxf.math import BoundingBox2d
    s = drawing.unit_scale

    def flat(entities, depth=0):
        for e in entities:
            t = e.dxftype()
            if t == "INSERT" and depth < MAX_BLOCK_DEPTH:
                for one in e.multi_insert():
                    yield from flat(one.virtual_entities(), depth + 1)
            elif t == "MLINE":
                yield from flat(e.virtual_entities(), depth + 1)
            elif t in _READ_TYPES:
                if getattr(e, "has_width", False):   # bộ đọc giữ cả nét tim của pline có bề rộng
                    yield from e.virtual_entities()
                yield e

    ref_pts: set[tuple[int, int]] = set()
    whole = BoundingBox2d()
    for prim in disassemble.to_primitives(flat(drawing.doc.modelspace()), max_flattening_distance=FLATTEN_MM / s):
        pts = [(v.x * s, v.y * s) for v in prim.vertices()]
        whole.extend(pts)
        ref_pts.update((round(x), round(y)) for x, y in pts)

    def known(x, y):
        rx, ry = round(x), round(y)
        return any((rx + i, ry + j) in ref_pts for i in (-1, 0, 1) for j in (-1, 0, 1))

    ours: list[tuple[str, float, float]] = []
    for g in drawing.segments:
        ours += [(g.layer, g.x1, g.y1), (g.layer, g.x2, g.y2)]
    for c in drawing.arcs:
        for ang in (c.start, c.end):
            ours.append((c.layer, c.cx + c.r * math.cos(math.radians(ang)), c.cy + c.r * math.sin(math.radians(ang))))
    for h in drawing.hatches:
        if h.pattern != "*EXPLODED*":                 # khung bao lồi tự dựng, không phải điểm của bản vẽ
            ours += [(h.layer, x, y) for poly in h.polygons for x, y in poly]
    bad: dict[str, float] = {}
    every = BoundingBox2d()
    for layer, x, y in ours:
        every.extend([(x, y)])
        if not known(x, y):
            bad[layer] = bad.get(layer, 0) + 1
    if whole.has_data and every.has_data:
        d = max(abs(whole.extmin.x - every.extmin.x), abs(whole.extmin.y - every.extmin.y),
                abs(whole.extmax.x - every.extmax.x), abs(whole.extmax.y - every.extmax.y))
    else:
        d = 0.0 if whole.has_data == every.has_data else math.inf
    if d > tol_mm:
        bad["*"] = d
    return bad


def read_dxf(path: str, layer_overrides: dict[str, str] | None = None) -> Drawing:
    try:
        doc = ezdxf.readfile(path)
    except (ezdxf.DXFStructureError, OSError) as exc:
        raise DrawingError(f"Không mở được file DXF: {exc}") from exc
    msp = doc.modelspace()
    warnings: list[str] = []

    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    try:
        scale = units.conversion_factor(insunits, units.MM) if insunits else 1.0
    except (TypeError, ValueError):                    # mã ngoài bảng hoặc đơn vị không đổi được (độ, parsec...)
        scale = 1.0
        warnings.append(f"Mã đơn vị $INSUNITS = {insunits} không xác định, đang coi là mm.")
    if insunits == 0:
        warnings.append("Bản vẽ không khai báo đơn vị ($INSUNITS = 0), đang coi là mm.")

    col = _Collector(doc, scale)
    col.walk(msp)
    mark_loose_hatch(col.segments)
    warnings += col.warnings
    if col.skipped:
        warnings.append("Đối tượng chưa đọc được (không dùng để nhận dạng): "
                        + ", ".join(f"{t} ×{n}" for t, n in col.skipped.most_common()))

    layers = sorted({layer.dxf.name for layer in doc.layers})
    classes = apply_overrides(default_classification(layers), layer_overrides)
    user_walls = bool(layer_overrides) and any(v == "WALL" for v in layer_overrides.values())
    unknown = [name for name, c in classes.items() if c == LayerClass.UNKNOWN and name != "0"]
    if unknown:
        warnings.append("Layer chưa xác định vai trò: " + ", ".join(unknown[:8]) + (" ..." if len(unknown) > 8 else ""))
    drawing = Drawing(col.segments, col.texts, col.blocks, col.hatches, layers, classes, scale, warnings, col.arcs,
                      user_walls, doc)
    bad = geometry_mismatch(drawing)
    if bad:
        msg = MISMATCH_WARNING
        if "*" in bad:
            msg += f" Khung bản vẽ lệch {bad.pop('*'):.0f} mm."
        if bad:
            msg += " Điểm không trùng hình gốc: " + ", ".join(f"{k} ×{v:.0f}" for k, v in Counter(bad).most_common(8))
        warnings.append(msg)
    return drawing


def crop(drawing: Drawing, bbox: tuple[float, float, float, float]) -> Drawing:
    """Phần bản vẽ nằm trong khung (x0, y0, x1, y1): dùng để đo bóc riêng từng mặt bằng trong một file."""
    x0, y0, x1, y1 = bbox

    def inside(x, y):
        return x0 <= x <= x1 and y0 <= y <= y1
    segs = [s for s in drawing.segments if inside(s.x1, s.y1) and inside(s.x2, s.y2)]
    hatches = [h for h in drawing.hatches if any(inside(*p) for poly in h.polygons for p in poly)]
    return Drawing(
        segments=segs, texts=[t for t in drawing.texts if inside(t.x, t.y)],
        blocks=[b for b in drawing.blocks if inside(b.x, b.y)], hatches=hatches, layers=drawing.layers,
        layer_classes=drawing.layer_classes, unit_scale=drawing.unit_scale,
        warnings=[w for w in drawing.warnings if w.startswith(MISMATCH_WARNING)],   # mặt bằng nào cũng phải thấy
        arcs=[a for a in drawing.arcs if inside(a.cx, a.cy)], user_wall_layers=drawing.user_wall_layers, doc=drawing.doc)


def read_drawing(path: str, layer_overrides: dict[str, str] | None = None) -> Drawing:
    """Đọc .dxf trực tiếp; .dwg được chuyển sang DXF bằng ODA File Converter trước."""
    suffix = Path(path).suffix.lower()
    if suffix == ".dxf":
        return read_dxf(path, layer_overrides)
    if suffix == ".dwg":
        with tempfile.TemporaryDirectory() as out_dir:
            return read_dxf(convert_dwg_to_dxf(path, out_dir), layer_overrides)
    raise DrawingError(f"Định dạng {suffix or '(không có đuôi)'} chưa được hỗ trợ. Chỉ nhận .dxf và .dwg.")
