"""Cấu kiện phụ (S08): giằng tường, sê nô, mái, và các luật không cộng trùng khối lượng.

Giằng tường, sê nô (S08-02): đọc trên mặt bằng kết cấu theo ký hiệu GT…/SN… (ky_hieu_cau_kien.csv) + cặp nét như dầm,
hoặc người dùng nhập vào mặt bằng kiến trúc (PlanInput.members). Tiết diện chữ nhật, không trừ dày sàn:
    bê tông            = dài × rộng × cao
    cốp pha giằng      = 2 × cao × dài (đáy nằm trên tường)
    cốp pha sê nô      = (2 × cao + rộng) × dài; sê nô chữ U: chữ nhật là quy ước gần đúng (cảnh báo)
Lanh tô ký hiệu LT… trên bản vẽ kết cấu: chỉ lấy tiết diện (cao lanh tô); khối lượng vẫn tính theo lỗ cửa (walls.py).
Mái (S08-03): mái bê tông = diện tích × dày, cốp pha = diện tích; mái khung (vì kèo, xà gồ, tôn, ngói) Not supported.

Luật không cộng trùng (S08-04):
    L1 lanh tô – dầm   : lỗ cửa có cao cửa + cao lanh tô > cao xây (đỉnh lanh tô chạm đáy dầm/sàn) thì không có lanh tô
                         riêng; phần lanh tô đã trừ khỏi khối xây được trả lại (dải còn lại là tường)
    L2 giằng – tường   : giằng nằm trên trục tường xây của cùng mặt bằng thì trừ dài chồng × cao giằng × dày tường khỏi xây
    L3 mái – sàn       : mái bê tông có replaces_slab_of thì bỏ sàn + cốp pha sàn của mặt bằng đó
    L4 lanh tô kết cấu : không sinh khối lượng từ ký hiệu LT… (tránh trùng lanh tô theo lỗ cửa)
Giằng, sê nô đọc từ mặt bằng kết cấu chưa gắn được tầng kiến trúc nên chưa trừ khỏi khối xây (cảnh báo, ma trận: conditional).
"""
from __future__ import annotations

import math
import re
from functools import lru_cache
from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel

from .. import config
from ..drawing.encoding import normalize
from .materials import _fmt
from .models import ROLE_WORK, ProjectParams, WorkItem
from .walls import ROLE_VI, _thickness_m, _work

ROOF_FILE = config.DATA_DIR / "rules" / "loai_mai.csv"
LINEAR_ROLES = ("WALL_TIE", "GUTTER")
AXIS_TOL_MM = 150.0
NOT_SUPPORTED_FRAME_ROOF = "Not supported: mái khung (vì kèo, xà gồ, tôn, ngói) chưa có phương pháp đo bóc"


class LinearMember(BaseModel):
    """Giằng tường hoặc sê nô: trục, tiết diện chữ nhật."""
    id: str
    kind: Literal["GIANG_TUONG", "SE_NO"]
    x1: float
    y1: float
    x2: float
    y2: float
    b_mm: Optional[float] = None
    d_mm: Optional[float] = None
    source: str = "manual"            # manual | structural
    keep: bool = True

    @property
    def length_mm(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)


def linear_works(plan: str, members: list[LinearMember]) -> tuple[list[WorkItem], list[str]]:
    works, warnings = [], []
    for code, name in (("GIANG_TUONG", "giằng"), ("SE_NO", "sê nô")):
        groups: dict[tuple, list[LinearMember]] = {}
        for m in members:
            if m.keep and m.kind == code:
                groups.setdefault((m.b_mm, m.d_mm), []).append(m)
        for (b, d), items in sorted(groups.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1] or 0)):
            L = sum(m.length_mm for m in items) / 1000
            missing = [lab for v, lab in ((b, f"rộng {name}"), (d, f"cao {name}")) if v is None]
            ids = ", ".join(sorted({m.id for m in items})[:5])
            label = f"{len(items)} {name}" + (f" {b:.0f}×{d:.0f}" if not missing else "") + f" ({ids})"
            evidence = [f"{m.id} ({m.source}) trục ({m.x1:.0f},{m.y1:.0f})–({m.x2:.0f},{m.y2:.0f})" for m in items]
            works.append(_work(code, L * b * d / 1e6 if not missing else None, plan=plan, element=label, missing=missing,
                               evidence=evidence, formula=f"{_fmt(L)} m × {_fmt(b / 1000) if b else 'rộng'} m × "
                                                          f"{_fmt(d / 1000) if d else 'cao'} m"))
            form = None if missing else (2 * d / 1000 * L if code == "GIANG_TUONG" else (2 * d + b) / 1000 * L)
            works.append(_work("COP_PHA", form, plan=plan, element=f"cốp pha {label}", formwork_of=code, missing=missing,
                               formula="2 × cao × dài (đáy nằm trên tường)" if code == "GIANG_TUONG"
                               else "(2 × cao + rộng) × dài"))
        if code == "SE_NO" and groups:
            warnings.append(f"{plan}: sê nô tính theo tiết diện chữ nhật rộng × cao (quy ước gần đúng); sê nô chữ U cần sửa tay.")
    return works, warnings


def _clip(x1, y1, x2, y2, rect) -> float:
    from .columns import _clip_length
    return _clip_length(x1, y1, x2, y2, rect)


def _xay_of(works: list[WorkItem], plan: str, wall, system) -> Optional[WorkItem]:
    label = f"tường {wall.cls} {ROLE_VI.get(wall.role, wall.role)}"
    return next((w for w in works if w.code == "XAY" and w.plan == plan and w.element == label
                 and w.wall_system_id == system), None)


def deduct_ties(works: list[WorkItem], plan: str, walls, systems: dict, members: list[LinearMember], catalog) -> list[str]:
    """L2: trừ giằng tường khỏi khối xây của tường nó nằm trên (sửa tại chỗ công tác XAY)."""
    warnings = []
    view = catalog.wall_view().set_index("wall_system_id") if not catalog.wall_systems.empty else pd.DataFrame()
    for m in (m for m in members if m.keep and m.kind == "GIANG_TUONG"):
        if m.d_mm is None:
            warnings.append(f"{plan}: giằng {m.id} chưa có cao giằng, khối xây chưa trừ giằng.")
            continue
        horizontal = abs(m.y2 - m.y1) < abs(m.x2 - m.x1)
        tx, ty = (0, AXIS_TOL_MM) if horizontal else (AXIS_TOL_MM, 0)     # dung sai chỉ theo phương ngang trục
        rect = (min(m.x1, m.x2) - tx, min(m.y1, m.y2) - ty, max(m.x1, m.x2) + tx, max(m.y1, m.y2) + ty)
        for w in walls:
            if not (w.keep and w.masonry) or (abs(w.y2 - w.y1) < abs(w.x2 - w.x1)) != horizontal:
                continue
            lap = _clip(w.x1, w.y1, w.x2, w.y2, rect)
            xay = _xay_of(works, plan, w, systems.get(w.id))
            if lap <= 0 or xay is None or xay.quantity is None:
                continue
            thick, _ = _thickness_m(systems.get(w.id), w.cls, view)
            v = lap / 1000 * m.d_mm / 1000 * thick
            xay.quantity = round(max(0.0, xay.quantity - v), 3)
            xay.formula += f" − {_fmt(v)} m³ giằng {m.id}"
    return warnings


def lintel_under_beam(works: list[WorkItem], plan: str, height_mm: float, walls, openings, systems: dict,
                      params: ProjectParams, catalog) -> list[str]:
    """L1: lỗ cửa mà đỉnh lanh tô chạm đáy dầm/sàn thì bỏ lanh tô của lỗ đó (dầm làm lanh tô), trả thể tích về khối xây.
    shortcut: chép công thức lanh tô của walls.wall_works; chuyển vào wall_works khi phiên S04 xong walls.py."""
    lt, bearing = params.lintel_height_mm, params.lintel_bearing_mm
    if lt is None or bearing is None:
        return []
    h_wall = height_mm - (params.beam_depth_mm or 0.0)
    view = catalog.wall_view().set_index("wall_system_id") if not catalog.wall_systems.empty else pd.DataFrame()
    by_id = {w.id: w for w in walls if w.keep and w.masonry}
    lintel = next((w for w in works if w.code == "LANH_TO" and w.plan == plan and w.quantity is not None), None)
    form = next((w for w in works if w.code == "COP_PHA" and w.formwork_of == "LANH_TO" and w.plan == plan
                 and w.quantity is not None), None)
    if lintel is None:
        return []
    skipped = []
    for o in openings:
        w = by_id.get(o.wall)
        if not o.keep or w is None or o.h + lt <= h_wall:
            continue
        thick, _ = _thickness_m(systems.get(w.id), w.cls, view)
        v = (o.w + 2 * bearing) / 1000 * thick * lt / 1000
        lintel.quantity = round(max(0.0, lintel.quantity - v), 3)
        if form is not None:
            form.quantity = round(max(0.0, form.quantity - (o.w / 1000 * thick + 2 * (o.w + 2 * bearing) / 1000 * lt / 1000)), 3)
        if (xay := _xay_of(works, plan, w, systems.get(w.id))) is not None and xay.quantity is not None:
            xay.quantity = round(xay.quantity + v, 3)
            xay.formula += f" + {_fmt(v)} m³ (lỗ {o.id}: dầm làm lanh tô)"
        skipped.append(o.id)
    if skipped:
        lintel.formula += f"; bỏ lanh tô lỗ {', '.join(skipped)} (cao cửa + cao lanh tô > cao xây {h_wall:.0f} mm: dầm làm lanh tô)"
        return [f"{plan}: {len(skipped)} lỗ cửa sát đáy dầm ({', '.join(skipped[:5])}) không tính lanh tô riêng (tránh trùng dầm)."]
    return []


def roof_works(params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    works, warnings = [], []
    for r in params.roofs:
        if r.kind == "khung":
            works.append(_work("MAI", None, element=r.name, source="manual", basis="not_supported",
                               missing=[NOT_SUPPORTED_FRAME_ROOF]))
            warnings.append(f"{r.name}: {NOT_SUPPORTED_FRAME_ROOF}; không trả số.")
            continue
        missing = [lab for v, lab in ((r.area_m2, "diện tích mái"), (r.thickness_mm, "dày bản mái")) if v is None]
        ok = not missing
        works.append(_work("MAI", r.area_m2 * r.thickness_mm / 1000 if ok else None, element=r.name, source="manual",
                           missing=missing, formula=f"{_fmt(r.area_m2) if r.area_m2 else 'diện tích'} m² × "
                                                    f"{_fmt(r.thickness_mm / 1000) if r.thickness_mm else 'dày'} m"))
        works.append(_work("COP_PHA", r.area_m2, element=f"cốp pha {r.name}", formwork_of="MAI", source="manual",
                           missing=[] if r.area_m2 is not None else ["diện tích mái"],
                           formula=f"{_fmt(r.area_m2) if r.area_m2 else 'diện tích'} m² (đáy bản mái)"))
    return works, warnings


def drop_slab_under_roof(works: list[WorkItem], params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    """L3: mái bê tông thay sàn của mặt bằng đã chọn thì bỏ sàn + cốp pha sàn của mặt bằng đó."""
    plans = {r.replaces_slab_of for r in params.roofs if r.kind == "be_tong" and r.replaces_slab_of}
    if not plans:
        return works, []
    keep = [w for w in works if not (w.plan in plans and (w.code == "SAN" or (w.code == "COP_PHA" and w.formwork_of == "SAN")))]
    return keep, [f"{p}: sàn trên tính là mái bê tông, bỏ công tác sàn của mặt bằng này (tránh trùng mái)." for p in sorted(plans)]


@lru_cache(maxsize=2)
def load_roof_rules(path: str | None = None) -> tuple[tuple[re.Pattern, str], ...]:
    rows = pd.read_csv(path or ROOF_FILE, dtype=str, keep_default_na=False).to_dict("records")
    return tuple((re.compile(r["mau"]), r["loai"]) for r in rows)


def roof_kind(title: str) -> Optional[str]:
    key = normalize(title)
    return next((kind for pat, kind in load_roof_rules() if pat.search(key)), None)


def read_secondary(drawing, scale: float | None = None) -> tuple[list[LinearMember], dict[str, float], list[str]]:
    """Từ bản vẽ kết cấu: giằng tường, sê nô (GT…, SN… + cặp nét), cao lanh tô (LT… ghi tiết diện), loại mái theo tiêu đề.
    Trả (cấu kiện tuyến tính, {khóa LT: cao}, cảnh báo)."""
    from .structural import SIZE_RE, PLAN_TYPES, _grown, _labels, _lines, _nearest_pair, element_of
    from ..drawing.sheets import find_views
    views = find_views(drawing, bbox_for=PLAN_TYPES)
    sizes, lintels = {}, {}
    for t in drawing.texts:
        if not (m := SIZE_RE.search(t.text)):
            continue
        for word in re.split(r"[\s(),:]+", t.text[:m.start()]):
            if word and (e := element_of(word)) and e[0] in LINEAR_ROLES + ("LINTEL",):
                (lintels if e[0] == "LINTEL" else sizes)[e[2]] = (float(m.group(1)), float(m.group(2)))
    members, warnings = [], []
    for v in views:
        if v.ma not in ("BV04", "BV08") or v.bbox is None:
            continue
        s = scale or 1.0
        lines = _lines(drawing, _grown(v.bbox))
        for t, e in _labels(drawing, v.bbox):
            if e[0] not in LINEAR_ROLES:
                continue
            p = _nearest_pair(lines, t.x, t.y)
            if p is None:
                warnings.append(f"{v.title}: ký hiệu {t.text.strip()} không có cặp nét, chưa đo.")
                continue
            _, o, axis, lo, hi, width, _ = p
            pts = ((lo, axis), (hi, axis)) if o == "h" else ((axis, lo), (axis, hi))
            sec = sizes.get(e[2])
            members.append(LinearMember(id=t.text.strip().upper(), kind=ROLE_WORK[e[0]], source="structural",
                                        x1=pts[0][0] * s, y1=pts[0][1] * s, x2=pts[1][0] * s, y2=pts[1][1] * s,
                                        b_mm=sec[0] if sec else round(width * s / 10) * 10, d_mm=sec[1] if sec else None))
    if any(m.kind == "GIANG_TUONG" for m in members):
        warnings.append("Giằng tường đọc từ mặt bằng kết cấu chưa gắn tầng kiến trúc: chưa trừ khỏi khối xây; nhập giằng vào "
                        "mặt bằng kiến trúc tương ứng để trừ.")
    for v in find_views(drawing):
        if v.ma == "BV13":
            kind = roof_kind(v.title)
            warnings.append(f"Bản vẽ mái '{v.title}': " + (
                NOT_SUPPORTED_FRAME_ROOF + "." if kind == "khung" else
                "mái bê tông, nhập diện tích và dày trong thông số mái (roofs)." if kind == "be_tong" else
                "chưa nhận loại mái (loai_mai.csv), nhập tay trong thông số mái."))
    return members, {k: h for k, (_, h) in lintels.items()}, warnings
