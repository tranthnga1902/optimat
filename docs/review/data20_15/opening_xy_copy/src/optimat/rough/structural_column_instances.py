"""Cột vật lý theo vị trí và đoạn cao độ; không đồng nhất mã loại với instance."""
from decimal import Decimal
import math
import hashlib
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import QuantityDetailRow
from .quantity_details import summarize
from .walls import _work


class SlabSourceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thickness_mm: float
    level_mm: float
    floor_key: str
    handles: list[str]
    evidence: list[str]
    region_confirmed: Literal[False] = False

    @model_validator(mode="after")
    def _finite(self):
        if not math.isfinite(self.thickness_mm) or self.thickness_mm <= 0 or not math.isfinite(self.level_mm):
            raise ValueError("Ứng viên sàn cần dày dương và cao độ hữu hạn.")
        return self


class StructuralColumnInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instance_id: str
    code: str
    grid_x: str | None = None
    grid_y: str | None = None
    floor_key: str | None = None
    z_from_mm: float | None = None
    z_to_mm: float | None = None
    b_mm: float | None = None
    h_mm: float | None = None
    top_slab_thickness_mm: float | None = None
    top_slab_source: str | None = None
    deduct_top_slab: bool = True
    file: str = ""
    source_sha256: str | None = None
    sheet: str = ""
    layers: list[str] = Field(default_factory=list)
    handles: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    top_slab_candidates: list[SlabSourceCandidate] = Field(default_factory=list)
    matched_plan: str | None = None
    matched_column_id: str | None = None
    mapping_evidence: str | None = None

    @model_validator(mode="after")
    def _valid(self):
        if not self.instance_id.strip() or not self.code.strip():
            raise ValueError("Cần định danh instance và mã cột.")
        if self.source_sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", self.source_sha256):
            raise ValueError("SHA-256 nguồn phải có 64 ký tự hex.")
        for name in ("z_from_mm", "z_to_mm", "b_mm", "h_mm", "top_slab_thickness_mm"):
            value = getattr(self, name)
            if value is not None and (not math.isfinite(value) or (name not in ("z_from_mm", "z_to_mm") and value <= 0)):
                raise ValueError("Kích thước phải hữu hạn, dương; cao độ phải hữu hạn.")
        if self.z_from_mm is not None and self.z_to_mm is not None:
            if self.z_to_mm <= self.z_from_mm:
                raise ValueError("Cao độ trên phải lớn hơn cao độ dưới.")
            if self.top_slab_thickness_mm is not None and self.top_slab_thickness_mm >= self.z_to_mm - self.z_from_mm:
                raise ValueError("Dày sàn không được phủ hết đoạn cột.")
        mapped = (self.matched_plan, self.matched_column_id, self.mapping_evidence)
        if any(v is not None for v in mapped) and not all(v and v.strip() for v in mapped):
            raise ValueError("Mapping cần mặt bằng, ID cột và căn cứ cùng nhau.")
        if self.top_slab_thickness_mm is not None and not (self.top_slab_source and self.top_slab_source.strip()):
            raise ValueError("Dày sàn đỉnh cần nguồn riêng.")
        return self


def instance_column_works(instances):
    """Giữ gross và khoản trừ riêng; thiếu nguồn khoản trừ không biến thành net đủ."""
    works = []
    for s in instances:
        missing = [*s.missing, *[name for name in ("b_mm", "h_mm", "z_from_mm", "z_to_mm") if getattr(s, name) is None]]
        if not (s.grid_x and s.grid_y):
            missing.append("vị trí trục của instance")
        if not s.evidence:
            missing.append("bằng chứng instance kết cấu")
        if not s.file:
            missing.append("file nguồn của instance")
        source = [f"instance {s.instance_id}; {s.code}; trục {s.grid_x or '?'} / {s.grid_y or '?'}; file {s.file}; tờ {s.sheet}",
                  *s.evidence, *[f"layer {v}" for v in s.layers], *[f"handle {v}" for v in s.handles]]
        dec = lambda v: Decimal(str(v))
        gross = None
        height = None
        if all(getattr(s, n) is not None for n in ("b_mm", "h_mm", "z_from_mm", "z_to_mm")):
            height = dec(s.z_to_mm) - dec(s.z_from_mm)
            gross = dec(s.b_mm) * dec(s.h_mm) * height / Decimal("1000000000")
        dimensions = dict(label=f"{s.code} [{s.instance_id}]", count=1,
            length_m=s.h_mm / 1000 if s.h_mm is not None else None,
            width_m=s.b_mm / 1000 if s.b_mm is not None else None,
            height_m=float(height / 1000) if height is not None else None,
            bottom_level_m=s.z_from_mm / 1000 if s.z_from_mm is not None else None,
            top_level_m=s.z_to_mm / 1000 if s.z_to_mm is not None else None,
            source="; ".join(source), note="Hình học đoạn cột; net xem khoản trừ có nguồn trong quantity_detail")
        rows = [QuantityDetailRow(row_id="gross", label="Thể tích theo hai cao độ", unit="m³", method="box",
                    raw_quantity=str(gross) if gross is not None else None, sources=source,
                    dimensions=dimensions, missing=list(missing), expression="b × h × (z trên − z dưới); mm³ → m³")]
        deduction = Decimal(0)
        if s.deduct_top_slab:
            slab_missing = []
            if s.top_slab_thickness_mm is None:
                slab_missing.append("dày sàn đỉnh và căn cứ trừ sàn")
            if gross is None:
                slab_missing.append("tiết diện hoặc khoảng cao độ cột")
            deduction = None if slab_missing else dec(s.b_mm) * dec(s.h_mm) * dec(s.top_slab_thickness_mm) / Decimal("1000000000")
            rows.append(QuantityDetailRow(row_id="top-slab", label="Trừ sàn đỉnh có nguồn", sign=-1, unit="m³", method="box",
                        raw_quantity=str(deduction) if deduction is not None else None,
                        sources=[s.top_slab_source or "chưa có nguồn sàn đỉnh"], missing=slab_missing,
                        dimensions={**dimensions, "basis": "deduction", "height_m": s.top_slab_thickness_mm / 1000 if s.top_slab_thickness_mm is not None else None,
                                    "source": s.top_slab_source or "chưa có nguồn sàn đỉnh"},
                        expression="b × h × dày sàn đỉnh; mm³ → m³"))
            missing += slab_missing
        net = gross - deduction if gross is not None and deduction is not None and not missing else None
        item = _work("COT", float(net) if net is not None else None, plan=s.matched_plan or s.floor_key or s.sheet or "kết cấu chưa gắn tầng",
                     element=f"{s.code} [{s.instance_id}]", basis="structural_instance", evidence=source,
                     dimensions=[{**dimensions, "basis": "reference"}],
                     missing=list(dict.fromkeys(missing)), formula="b × h × (z trên − z dưới) − khoản trừ sàn đỉnh có nguồn")
        item.quantity_detail = summarize(rows, "m³", item.quantity, scope_complete=not missing)
        works.append(item)
        cp_missing = list(dict.fromkeys([*missing, "chưa kiểm giao dầm và mặt cốp pha của instance"]))
        works.append(_work("COP_PHA", None, plan=item.plan, element=f"cốp pha {item.element}", formwork_of="COT",
                           basis="structural_instance", evidence=source, missing=cp_missing))
    return works


def allocated_local_columns(plan, columns, instances):
    """Chỉ bỏ đúng instance KT có mapping được xác nhận; không so mã loại hoặc tọa độ khác hệ."""
    matched = {s.matched_column_id for s in instances if s.matched_plan == plan and s.mapping_evidence}
    return [c for c in columns if c.id not in matched]


def read_column_instances(drawing, views):
    """Nối CAD qua leader/biên/trục và dấu cắt; thiếu quan hệ thì giữ pending.

    Drawing tổng hợp không có doc vẫn đọc thuộc tính tường minh như hợp đồng cũ.
    """
    from .structural import element_of
    from ..drawing.registry import floors_of

    if getattr(drawing, "doc", None) is not None:
        return _cad_column_instances(drawing)
    file = str(getattr(getattr(drawing, "doc", None), "filename", "") or "")
    result = []
    for view in views:
        if view.ma != "BV06" or view.bbox is None:
            continue
        x0, y0, x1, y1 = view.bbox
        floor = floors_of(view.title)
        candidates = []
        for block in drawing.blocks:
            attrs = {str(k).upper(): str(v).strip() for k, v in block.attribs.items()}
            if attrs.get("COLUMN_CODE"):
                candidates.append((block, attrs["COLUMN_CODE"], attrs))
        for text in drawing.texts:
            role = element_of(text.text)
            if role and role[0] == "COLUMN":
                candidates.append((text, text.text.strip(), {}))
        for entity, code, attrs in candidates:
            if not (x0 <= entity.x <= x1 and y0 <= entity.y <= y1):
                continue
            role = element_of(code)
            if not role or role[0] != "COLUMN":
                continue
            identity = f"{file}|{view.title}|{role[2]}|{entity.x:g}|{entity.y:g}"
            evidence = [f"{view.title}: {code} tại ({entity.x:g}, {entity.y:g}); layer {entity.layer}"]
            values = {}
            for key, field in (("Z_FROM_MM", "z_from_mm"), ("Z_TO_MM", "z_to_mm"),
                               ("WIDTH_MM", "b_mm"), ("DEPTH_MM", "h_mm"),
                               ("TOP_SLAB_THICKNESS_MM", "top_slab_thickness_mm")):
                if attrs.get(key):
                    try:
                        value = float(attrs[key])
                    except ValueError:
                        evidence.append(f"{key} chưa đọc được: {attrs[key]}")
                        continue
                    if not math.isfinite(value) or (key not in ("Z_FROM_MM", "Z_TO_MM") and value <= 0):
                        evidence.append(f"{key} không hợp lệ: {attrs[key]}")
                        continue
                    values[field] = value
                    evidence.append(f"thuộc tính {key}={attrs[key]} mm")
            if values.get("z_to_mm") is not None and values.get("z_from_mm") is not None:
                if values["z_to_mm"] <= values["z_from_mm"]:
                    evidence.append("hai cao độ mâu thuẫn; chưa lập đoạn cột")
                    values.pop("z_to_mm")
            if "top_slab_thickness_mm" in values:
                values["top_slab_source"] = evidence[0] + "; TOP_SLAB_THICKNESS_MM"
                if all(k in values for k in ("z_from_mm", "z_to_mm")) and values["top_slab_thickness_mm"] >= values["z_to_mm"] - values["z_from_mm"]:
                    values.pop("top_slab_thickness_mm")
                    values.pop("top_slab_source")
            result.append(StructuralColumnInstance(instance_id=hashlib.sha256(identity.encode()).hexdigest()[:24],
                code=code, grid_x=attrs.get("GRID_X") or None, grid_y=attrs.get("GRID_Y") or None,
                floor_key=floor[0] if len(floor) == 1 else None, file=file, sheet=view.title,
                layers=[entity.layer], evidence=evidence, **values))
    return result


def _cad_records(drawing):
    """Mở INSERT theo WCS trước khi lọc vùng, giữ đường dẫn entity gốc."""
    from ..drawing.dxf_reader import MAX_BLOCK_DEPTH, _clean_codes
    from ..drawing.encoding import to_unicode
    from ..drawing.dimensions import _shown

    doc, scale = drawing.doc, drawing.unit_scale
    records = []

    def point(p):
        return (p[0] * scale, p[1] * scale)

    def walk(entities, path=(), depth=0):
        for entity in entities:
            original = entity.origin_of_copy or entity
            handle = original.dxf.get("handle", "")
            chain = (*path, handle) if handle else path
            kind = entity.dxftype()
            if kind == "INSERT":
                if depth >= MAX_BLOCK_DEPTH:
                    continue
                for index, insert in enumerate(entity.multi_insert() if entity.mcount > 1 else [entity]):
                    branch = (*chain, f"MINSERT[{index}]") if entity.mcount > 1 else chain
                    yield_from = insert.virtual_entities()
                    walk(yield_from, branch, depth + 1)
                continue
            row = dict(kind=kind, handle="/".join(chain), layer=entity.dxf.layer)
            if kind in ("TEXT", "MTEXT", "ATTRIB"):
                raw = entity.plain_text() if kind == "MTEXT" else entity.dxf.text
                style = entity.dxf.get("style", "Standard")
                font = doc.styles.get(style).dxf.get("font", None) if style in doc.styles else None
                text, _ = to_unicode(_clean_codes(raw), font)
                p = entity.dxf.insert if kind == "MTEXT" else entity.ocs().to_wcs(entity.dxf.insert)
                row.update(text=text.strip(), p=point(p), height=entity.dxf.get("char_height", 0) * scale if kind == "MTEXT"
                           else entity.dxf.get("height", 0) * scale)
            elif kind == "CIRCLE":
                row.update(p=point(entity.ocs().to_wcs(entity.dxf.center)), radius=entity.dxf.radius * scale)
            elif kind == "LINE":
                row.update(a=point(entity.dxf.start), b=point(entity.dxf.end))
            elif kind == "LEADER":
                row.update(vertices=[point(v) for v in entity.vertices])
            elif kind == "LWPOLYLINE":
                row.update(vertices=[point(v) for v in entity.vertices_in_wcs()], closed=entity.closed)
            elif kind == "DIMENSION" and not path:
                if entity.dimtype not in (0, 1):
                    continue
                try:
                    measured = float(entity.get_measurement())
                    value = _shown(doc, entity, measured)
                    a, b = point(entity.dxf.defpoint2), point(entity.dxf.defpoint3)
                except (ValueError, AttributeError, KeyError, TypeError):
                    continue
                if value is None or not math.isfinite(value) or not math.isfinite(measured) or measured <= 0 or value <= 0:
                    continue
                angle = (entity.dxf.get("angle",0) if entity.dimtype==0 else math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))) % 180
                if min(angle,180-angle)>1 and abs(angle-90)>1:
                    continue
                row.update(p=point(entity.dxf.get("text_midpoint") or entity.dxf.defpoint), a=a, b=b,
                           value=value, measured=measured * scale,
                           vertical=abs(angle-90)<=1)
            else:
                continue
            records.append(row)

    walk(doc.modelspace())
    return records


def _rect(row):
    vertices = row.get("vertices", [])
    if row["kind"] != "LWPOLYLINE" or not row.get("closed") or len(vertices) != 4:
        return None
    xs, ys = sorted({round(p[0], 5) for p in vertices}), sorted({round(p[1], 5) for p in vertices})
    return (xs[0], ys[0], xs[-1], ys[-1]) if len(xs) == len(ys) == 2 else None


def _inside_box(p, box, tolerance=0):
    return box[0] - tolerance <= p[0] <= box[2] + tolerance and box[1] - tolerance <= p[1] <= box[3] + tolerance


def _axes(records):
    """Trục cần nhãn trong vòng tròn và nét trục dài thẳng hàng; không lấy tâm chữ làm tim."""
    texts = [r for r in records if "text" in r and re.fullmatch(r"[A-Z]|\d+", r["text"])]
    lines = [r for r in records if r["kind"] == "LINE"]
    axes = {}
    for circle in (r for r in records if r["kind"] == "CIRCLE"):
        cx, cy = circle["p"]
        radius = circle["radius"]
        labels = {t["text"] for t in texts if math.dist(t["p"], (cx, cy)) < radius}
        if radius <= 0 or len(labels) != 1:
            continue
        label = next(iter(labels))
        for line in lines:
            a, b = line["a"], line["b"]
            vertical = abs(a[0] - b[0]) < radius * .01
            horizontal = abs(a[1] - b[1]) < radius * .01
            if math.dist(a, b) < 4 * radius or not (vertical or horizontal):
                continue
            across, along = (cx, cy) if vertical else (cy, cx)
            coord = (a[0] + b[0]) / 2 if vertical else (a[1] + b[1]) / 2
            limits = sorted((a[1], b[1]) if vertical else (a[0], b[0]))
            if abs(across - coord) > radius * .01 or not limits[0] - 2 * radius <= along <= limits[1] + 2 * radius:
                continue
            key = (vertical, round(coord, 3), label)
            axis = axes.setdefault(key, dict(vertical=vertical, coord=coord, label=label, limits=limits, refs=[]))
            axis["refs"] += [circle, line, *[t for t in texts if t["text"] == label and math.dist(t["p"], (cx, cy)) < radius]]
    return list(axes.values())


def _section_boundary(records, width, depth):
    """Hai DIM phải đo hai cạnh của cùng một biên chữ nhật kín."""
    x0, x1 = sorted((width["a"][0], width["b"][0]))
    y0, y1 = sorted((depth["a"][1], depth["b"][1]))
    box = (x0, y0, x1, y1)
    tolerance = min(x1-x0, y1-y0) * .00001
    if tolerance <= 0:
        return []
    for row in records:
        rect = _rect(row)
        if rect and all(abs(a-b) <= tolerance for a,b in zip(rect, box)):
            return [row]
    corners = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    refs = []
    for start, end in zip(corners, corners[1:] + corners[:1]):
        edge = [r for r in records if r["kind"] == "LINE" and (
            (math.dist(r["a"],start) <= tolerance and math.dist(r["b"],end) <= tolerance) or
            (math.dist(r["b"],start) <= tolerance and math.dist(r["a"],end) <= tolerance))]
        if not edge:
            return []
        refs += edge
    return refs


def _section_spans(records, heading, all_headings, *, issues=None):
    from types import SimpleNamespace
    from .. import config
    from ..drawing.sheets import _window
    from ..drawing.encoding import normalize
    from .structural import _z

    heads = [SimpleNamespace(x=r["p"][0], y=r["p"][1]) for r in all_headings]
    own = heads[all_headings.index(heading)]
    scope = _window(own, heads)
    # Các loại cột có thể đặt lệch hàng; vẫn chia ranh theo tiêu đề hai bên.
    from .structural import SECTION_REACH_MM
    left, bottom, right, top = scope
    for other in heads:
        if other is own or abs(other.y - own.y) >= SECTION_REACH_MM:
            continue
        if other.x < own.x:
            left = max(left, (other.x + own.x) / 2)
        elif other.x > own.x:
            right = min(right, (other.x + own.x) / 2)
    top = _window(own, [h for h in heads if left <= h.x <= right])[3]
    scope = (left, bottom, right, top)
    local = [r for r in records if "p" in r and _inside_box(r["p"], scope)]
    levels = [r for r in local if "text" in r and re.fullmatch(r"[+−-]\d+[.,]\d+", r["text"])]
    if len(levels) < 2:
        return []
    # Một hình đứng có cột cao độ thẳng hàng; nhiều cột cao độ không được tự chọn.
    groups = []
    for row in sorted(levels, key=lambda r: r["p"][0]):
        if not groups or abs(row["p"][0] - groups[-1][0]["p"][0]) > 2 * max(row["height"], groups[-1][0]["height"]):
            groups.append([])
        groups[-1].append(row)
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) != 1:
        return []
    levels = sorted(groups[0], key=lambda r: r["p"][1])
    level = lambda r: _z(r["text"].replace("−", "-"))
    if any(level(b) <= level(a) for a, b in zip(levels, levels[1:])):
        return []
    captions = [r for r in local if "text" in r and re.fullmatch(r"(\d+)\s*[-–]\s*\1", normalize(r["text"]))]
    spans = []
    for low, high in zip(levels, levels[1:]):
        markers = [r for r in local if "text" in r and r["text"].isdigit()
                   and r["p"][0] < min(low["p"][0], high["p"][0])
                   and low["p"][1] < r["p"][1] < high["p"][1]]
        pairs = []
        for caption in captions:
            mark = re.match(r"\d+", caption["text"])[0]
            same = [r for r in markers if r["text"] == mark]
            if len(same) != 2 or abs(same[0]["p"][1] - same[1]["p"][1]) > max(r["height"] for r in same) / 2:
                continue
            if abs(same[0]["p"][0] - same[1]["p"][0]) <= max(r["height"] for r in same):
                continue
            # Dấu cắt phải có nét ngang riêng ngay dưới cả hai số hiệu.
            strokes = []
            marks_with_stroke = 0
            for marker in same:
                hits = []
                for line in records:
                    points = [line["a"], line["b"]] if line["kind"] == "LINE" else line.get("vertices", [])
                    if len(points) == 2 and abs(points[0][1] - points[1][1]) < 1 and min(p[0] for p in points) <= marker["p"][0] <= max(p[0] for p in points) and 0 <= marker["p"][1] - points[0][1] <= marker["height"]:
                        hits.append(line)
                if hits:
                    marks_with_stroke += 1
                    strokes += hits
            if marks_with_stroke != 2 or len({r["handle"] for r in strokes}) < 2:
                continue
            upper = min((r["p"][1] for r in captions if r["p"][1] > caption["p"][1] + caption["height"]), default=scope[3])
            upper = min(upper, max(r["p"][1] for r in levels) + 2 * caption["height"])
            ds = [r for r in local if r["kind"] == "DIMENSION" and abs(r["p"][0] - caption["p"][0]) <= 8 * caption["height"]
                  and caption["p"][1] < r["p"][1] < upper and config.COLUMN_SIDE_MM[0] <= r["value"] <= config.COLUMN_SIDE_MM[1]]
            cell = (caption["p"][0]-8*caption["height"],caption["p"][1],caption["p"][0]+8*caption["height"],upper)
            geometry = [r for r in records if
                (r["kind"]=="LINE" and _inside_box(r["a"],cell) and _inside_box(r["b"],cell)) or
                (r["kind"]=="LWPOLYLINE" and r.get("closed") and all(_inside_box(p,cell) for p in r["vertices"]))]
            valid = {}
            for width in (r for r in ds if not r["vertical"]):
                for depth in (r for r in ds if r["vertical"]):
                    if not math.isclose(width["value"] / width["measured"], depth["value"] / depth["measured"], rel_tol=.01):
                        continue
                    boundary = _section_boundary(geometry, width, depth)
                    if not boundary:
                        continue
                    key = (width["value"], depth["value"], *[round(v,5) for v in
                           (*sorted((width["a"][0],width["b"][0])), *sorted((depth["a"][1],depth["b"][1])))])
                    refs = valid.setdefault(key, [])
                    for ref in (width, depth, *boundary):
                        if ref not in refs:
                            refs.append(ref)
            if len(valid) == 1:
                key, dimension_refs = next(iter(valid.items()))
                pairs.append(dict(z0=level(low), z1=level(high), b=key[0], h=key[1], expected_count=len(levels)-1,
                                  refs=[heading, low, high, caption, *same, *strokes, *dimension_refs]))
            elif len(valid) > 1 and issues is not None:
                issues.append(dict(reason="nhiều cặp DIM/biên kín hợp lệ cho cùng mặt cắt; chưa chọn nguồn",
                    refs=[heading,caption,low,high,*[r for group in valid.values() for r in group]]))
        if len(pairs) == 1:
            spans.append(pairs[0])
        elif len(pairs) > 1 and issues is not None:
            issues.append(dict(reason="nhiều mặt cắt hợp lệ cùng đoạn; chưa xác định duy nhất",refs=[r for p in pairs for r in p["refs"]]))
    return spans


def _slab_source_candidates(records, top_level, upper_floor):
    """Ghi chú h và cao độ chỉ là ứng viên; chưa chứng minh vùng tại cột thì không trừ."""
    from ..drawing.sheets import sheet_type_of, VIEW_REACH_MM
    from ..drawing.registry import floors_of
    from ..drawing.encoding import normalize
    from .structural import _z

    heads = [r for r in records if "text" in r and (kind := sheet_type_of(r["text"])) and kind.ma in ("BV08", "BV10")]
    levels = [r for r in records if "text" in r and re.fullmatch(r"[+−-]\d+[.,]\d+", r["text"])
              and math.isclose(_z(r["text"].replace("−", "-")), top_level, abs_tol=.01)]
    found = []
    for row in records:
        if "text" not in row:
            continue
        match = re.fullmatch(r"h\s*=\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)", normalize(row["text"]))
        if not match:
            continue
        near = [r for r in levels if math.dist(r["p"], row["p"]) <= 3 * max(r["height"], row["height"])]
        titles = sorted(heads, key=lambda r: math.dist(r["p"], row["p"]))
        if len(near) != 1 or not titles or math.dist(titles[0]["p"], row["p"]) > VIEW_REACH_MM or floors_of(titles[0]["text"]) != [upper_floor]:
            continue
        value = float(match[1].replace(",", ".")) * {"mm": 1, "cm": 10, "m": 1000}[match[2]]
        if not math.isfinite(value) or value <= 0:
            continue
        refs = [row, near[0], titles[0]]
        found.append(SlabSourceCandidate(thickness_mm=value, level_mm=top_level, floor_key=upper_floor,
            handles=[r["handle"] for r in refs], evidence=[f"{r['handle']}: {r['text']}" for r in refs] +
                ["chưa đối chiếu biên vùng sàn với vị trí cột; không dùng ứng viên để tự trừ"]))
    return found


def _merge_column_spans(spans):
    """Giữ mọi provenance; cùng số đo không được xóa xung đột phạm vi nguồn."""
    groups = {}
    conflict = False
    for span in spans:
        key = (span["z0"],span["z1"],span["b"],span["h"])
        if key not in groups:
            groups[key] = {**span, "refs": list(span["refs"])}
            continue
        group = groups[key]
        conflict |= group["expected_count"] != span["expected_count"]
        for ref in span["refs"]:
            if ref not in group["refs"]:
                group["refs"].append(ref)
    merged = sorted(groups.values(),key=lambda s:s["z0"])
    intervals = [(s["z0"],s["z1"]) for s in merged]
    conflict |= len(intervals) != len(set(intervals))
    return ([] if conflict else merged), conflict


def _plan_heads_at_axes(headings, vertical, horizontal):
    """View phải kề footprint của hệ trục; không chọn tiêu đề gần nhất toàn tệp."""
    box = (horizontal["limits"][0],vertical["limits"][0],horizontal["limits"][1],vertical["limits"][1])
    return [h for h in headings if _inside_box(h["p"],box,10*h["height"])]


def _cad_column_instances(drawing):
    from ..drawing.encoding import normalize
    from ..drawing.registry import floors_of
    from ..drawing.sheets import sheet_type_of, VIEW_REACH_MM
    from .structural import element_of

    records = _cad_records(drawing)
    texts = [r for r in records if "text" in r]
    plan_heads = [r for r in texts if (kind := sheet_type_of(r["text"])) and kind.ma == "BV06"]
    detail_heads = []
    for row in texts:
        match = re.match(r"(?:chi tiet )?cot\s+([a-z]+[-–]?\d+[a-z]?)\b", normalize(row["text"]))
        if match and (kind := element_of(match[1])) and kind[0] == "COLUMN":
            detail_heads.append({**row, "code": kind[2]})
    axes = _axes(records)
    leaders = [r for r in records if r["kind"] == "LEADER" and len(r["vertices"]) >= 2]
    rectangles = [(r, box) for r in records if (box := _rect(r))]
    spans_by_code = {}
    issues_by_code = {}
    for heading in detail_heads:
        issues = []
        spans_by_code.setdefault(heading["code"], []).extend(_section_spans(records, heading, detail_heads,issues=issues))
        issues_by_code.setdefault(heading["code"], []).extend(issues)
    file = str(getattr(drawing.doc, "filename", "") or "")
    source_sha256 = hashlib.sha256(Path(file).read_bytes()).hexdigest() if file and Path(file).is_file() else None
    found = {}
    slab_cache = {}
    for label in texts:
        role = element_of(label["text"])
        if not role or role[0] != "COLUMN":
            continue
        linked = [r for r in leaders if math.dist(r["vertices"][-1], label["p"]) <= 2 * label["height"]]
        if len(linked) != 1:
            continue
        leader = linked[0]
        arrow = leader["vertices"][0]
        shapes = [(r, box) for r, box in rectangles
                  if _inside_box(arrow, box, .02 * min(box[2]-box[0], box[3]-box[1]))
                  and min(abs(arrow[0]-box[0]), abs(arrow[0]-box[2]), abs(arrow[1]-box[1]), abs(arrow[1]-box[3]))
                  <= .02 * min(box[2]-box[0], box[3]-box[1])]
        if len(shapes) != 1:
            continue
        shape, box = shapes[0]
        vx = [a for a in axes if a["vertical"] and box[0] <= a["coord"] <= box[2] and a["limits"][0] <= (box[1]+box[3])/2 <= a["limits"][1]]
        hy = [a for a in axes if not a["vertical"] and box[1] <= a["coord"] <= box[3] and a["limits"][0] <= (box[0]+box[2])/2 <= a["limits"][1]]
        if len(vx) != 1 or len(hy) != 1:
            key = hashlib.sha256(f"{file}|{shape['handle']}|chưa nối trục".encode()).hexdigest()[:24]
            trace = [label, leader, shape]
            found[key] = StructuralColumnInstance(instance_id=key, code=label["text"], file=file,
                source_sha256=source_sha256,
                grid_x=vx[0]["label"] if len(vx) == 1 else None, grid_y=hy[0]["label"] if len(hy) == 1 else None,
                evidence=[f"{r['handle']}: {r.get('text',r['kind'])}" for r in trace],
                handles=[r["handle"] for r in trace], layers=sorted({r["layer"] for r in trace}),
                missing=["đã nối nhãn/leader/hình cột, chưa xác định duy nhất hai trục"])
            continue
        eligible_heads = _plan_heads_at_axes(plan_heads,vx[0],hy[0])
        if len(eligible_heads) != 1:
            key = hashlib.sha256(f"{file}|{shape['handle']}|view pending".encode()).hexdigest()[:24]
            trace = [label,leader,shape,*eligible_heads,*vx[0]["refs"],*hy[0]["refs"]]
            found[key] = StructuralColumnInstance(instance_id=key,code=label["text"],file=file,source_sha256=source_sha256,
                grid_x=vx[0]["label"],grid_y=hy[0]["label"],
                handles=sorted({r["handle"] for r in trace}),layers=sorted({r["layer"] for r in trace}),
                evidence=[f"{r['handle']}: {r.get('text',r['kind'])}" for r in trace],
                missing=["chưa xác định duy nhất view cột trong footprint hệ trục; không chọn tiêu đề gần nhất"])
            continue
        heading = eligible_heads[0]
        floors = floors_of(heading["text"])
        spans = spans_by_code.get(role[2], [])
        refs = [label, leader, shape, heading, *vx[0]["refs"], *hy[0]["refs"]]
        issues = issues_by_code.get(role[2],[])
        refs += [r for issue in issues for r in issue["refs"]]
        # Chỉ gán tầng khi số đoạn liên tiếp khớp toàn bộ phạm vi ghi trên mặt bằng.
        original_span_refs = [r for s in spans for r in s["refs"]]
        spans, conflict = _merge_column_spans(spans)
        if conflict:
            refs += original_span_refs
        floor_ready = bool(spans) and len(floors) == len(spans) and all(s["expected_count"] == len(spans) for s in spans)
        floor_ready = floor_ready and all(a["z1"] == b["z0"] for a,b in zip(spans, spans[1:]))
        if not spans:
            spans = [None]
        for index, span in enumerate(spans):
            values = {} if span is None else dict(z_from_mm=span["z0"], z_to_mm=span["z1"], b_mm=span["b"], h_mm=span["h"])
            trace = refs + (span["refs"] if span else [])
            identity = f"{file}|{shape['handle']}|{values.get('z_from_mm')}|{values.get('z_to_mm')}"
            key = hashlib.sha256(identity.encode()).hexdigest()[:24]
            slab_candidates = []
            if span and floor_ready and re.fullmatch(r"T\d+", floors[index]):
                slab_key = (span["z1"], f"T{int(floors[index][1:]) + 1}")
                if slab_key not in slab_cache:
                    slab_cache[slab_key] = _slab_source_candidates(records, *slab_key)
                slab_candidates = slab_cache[slab_key]
            found[key] = StructuralColumnInstance(instance_id=key, code=label["text"], grid_x=vx[0]["label"], grid_y=hy[0]["label"],
                floor_key=floors[index] if floor_ready and span else None,
                file=file, source_sha256=source_sha256, sheet=heading["text"], layers=sorted({r["layer"] for r in trace}),
                top_slab_candidates=slab_candidates,
                handles=sorted({r["handle"] for r in trace if r["handle"]}),
                missing=(["mâu thuẫn tiết diện hoặc phạm vi nguồn cùng đoạn; chưa chọn nguồn"] if conflict else []) +
                        [issue["reason"] for issue in issues] +
                        (["chưa nối đầy đủ đoạn cột với phạm vi tầng"] if not floor_ready else []),
                evidence=[f"{r['handle']}: {r.get('text', r['kind'])}; layer {r['layer']}" for r in trace], **values)
    return list(found.values())
