"""Đọc đường kích thước (DIMENSION) của bản vẽ: số người thiết kế thấy trên bản vẽ và số đo hình học.

Hình chi tiết thường vẽ phóng to (TL 1/20 trên khung 1/100): nét dài gấp 5 lần, số hiển thị vẫn là mm thật. Số hiển thị
lấy từ block hình của đường kích thước (chữ phần mềm CAD đã vẽ ra), không có thì chữ ghi đè, cuối cùng là số đo × DIMLFAC.
    tỷ lệ hình vẽ = số hiển thị / số đo   (dùng để đổi nét đo trên hình vẽ đó ra mm thật)
Chỉ đọc đường kích thước nằm thẳng trong model, ngang hoặc đứng; chữ không phải một số (Ø6a200, 2x100) bị bỏ.
"""
from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass
class Dim:
    x: float                # vị trí chữ, mm theo tọa độ bản vẽ
    y: float
    value: float            # số hiển thị (mm thật)
    measured: float         # số đo hình học (mm bản vẽ)
    vertical: bool          # True: đo theo phương đứng


def _number(text: str) -> float | None:
    t = re.sub(r"\\[A-Za-z][^;]*;|[{}]", "", text).strip()     # bỏ mã định dạng MTEXT
    return float(t.replace(",", ".")) if NUMBER_RE.fullmatch(t) else None


def _shown(doc, e, measured: float) -> float | None:
    if e.dxf.hasattr("geometry") and (blk := doc.blocks.get(e.dxf.geometry)) is not None:
        texts = [t.dxf.text if t.dxftype() == "TEXT" else t.plain_text() for t in blk if t.dxftype() in ("TEXT", "MTEXT")]
        if texts:
            return _number(texts[0])
    raw = e.dxf.get("text", "")
    if raw not in ("", "<>"):
        return _number(raw)
    return measured * float(e.override().get("dimlfac", 1.0) or 1.0)


def read_dimensions(drawing) -> list[Dim]:
    doc = getattr(drawing, "doc", None)
    if doc is None:
        return []
    s = drawing.unit_scale
    out = []
    for e in doc.modelspace().query("DIMENSION"):
        if e.dimtype not in (0, 1):                     # 0 thẳng (có góc), 1 thẳng hàng theo hai điểm
            continue
        try:
            measured = float(e.get_measurement())
        except Exception:
            continue
        if e.dimtype == 0:
            angle = e.dxf.get("angle", 0.0) % 180
        else:
            a, b = e.dxf.defpoint2, e.dxf.defpoint3
            angle = math.degrees(math.atan2(b.y - a.y, b.x - a.x)) % 180
        if min(angle, 180 - angle) > 1 and abs(angle - 90) > 1:
            continue
        value = _shown(doc, e, measured)
        if value is None or measured <= 0 or value <= 0:
            continue
        p = e.dxf.get("text_midpoint") or e.dxf.defpoint
        out.append(Dim(p.x * s, p.y * s, value, measured * s, abs(angle - 90) <= 1))
    return out


def inside(dims: list[Dim], bbox) -> list[Dim]:
    x0, y0, x1, y1 = bbox
    return [d for d in dims if x0 <= d.x <= x1 and y0 <= d.y <= y1]


def view_scale(dims: list[Dim]) -> float | None:
    """Tỷ lệ số hiển thị / số đo của các đường kích thước trong một hình vẽ (trung vị); None nếu không có."""
    return statistics.median(d.value / d.measured for d in dims) if dims else None
