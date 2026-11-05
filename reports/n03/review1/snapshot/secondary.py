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
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field

from .. import config
from ..drawing.encoding import normalize
from ..drawing.review import ReviewOpening
from .materials import _fmt
from .models import ROLE_WORK, ProjectParams, WorkItem, worst_status
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
    z_bottom_mm: Optional[float] = Field(default=None, allow_inf_nan=False)
    z_evidence: Optional[str] = None

    @property
    def length_mm(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)


@dataclass(frozen=True)
class _TieGroup:
    members: tuple[LinearMember, ...]
    segments: tuple[tuple[float, float, float, float], ...]
    missing: tuple[str, ...]


def _axis(m: LinearMember):
    values = (m.x1, m.y1, m.x2, m.y2)
    if not all(math.isfinite(v) for v in values) or m.length_mm <= 0:
        return None
    if m.y1 == m.y2:
        return ("H", m.y1, min(m.x1, m.x2), max(m.x1, m.x2))
    if m.x1 == m.x2:
        return ("V", m.x1, min(m.y1, m.y2), max(m.y1, m.y2))
    return None


def normalize_ties(members: list[LinearMember], *, plan_context: bool = False) -> list[_TieGroup]:
    """Hợp đoạn cùng cơ sở đã biết; không suy cùng tầng/cao độ từ hình chiếu."""
    kept = [m for m in members if m.keep and m.kind == "GIANG_TUONG"]
    reasons = [[] for _ in kept]
    axes = [_axis(m) for m in kept]
    for i, m in enumerate(kept):
        if not plan_context:
            reasons[i].append("chưa xác nhận tầng/hệ tọa độ giằng (pending K03)")
        if m.z_bottom_mm is None:
            reasons[i].append("cao độ đáy giằng")
        for value, label in ((m.b_mm, "rộng giằng"), (m.d_mm, "cao giằng")):
            if value is None or not math.isfinite(value) or value <= 0:
                reasons[i].append(label)
        if axes[i] is None:
            reasons[i].append("trục giằng xiên, dài 0 hoặc tọa độ không hữu hạn: chưa hỗ trợ hợp")
    for i, a in enumerate(kept):
        for j in range(i):
            b = kept[j]
            aa, bb = axes[i], axes[j]
            if aa is None or bb is None:
                continue
            if aa[:2] == bb[:2]:
                overlaps = min(aa[3], bb[3]) > max(aa[2], bb[2])
            elif aa[0] != bb[0]:
                h, v = (aa, bb) if aa[0] == "H" else (bb, aa)
                overlaps = h[2] <= v[1] <= h[3] and v[2] <= h[1] <= v[3]
            else:
                overlaps = False
            if not overlaps:
                continue
            if all(x is not None and math.isfinite(x) for x in (a.z_bottom_mm, b.z_bottom_mm, a.d_mm, b.d_mm)):
                if a.z_bottom_mm + a.d_mm <= b.z_bottom_mm or b.z_bottom_mm + b.d_mm <= a.z_bottom_mm:
                    continue
            same = (aa[:2] == bb[:2] and a.z_bottom_mm is not None
                    and (a.z_bottom_mm, a.b_mm, a.d_mm, a.source) == (b.z_bottom_mm, b.b_mm, b.d_mm, b.source))
            if not same:
                reason = f"giằng {a.id}/{b.id} chồng hình chiếu nhưng chưa chứng minh cùng thể tích/nguồn"
                reasons[i].append(reason)
                reasons[j].append(reason)
    buckets = {}
    for i, m in enumerate(kept):
        axis = axes[i]
        key = (axis[:2] if axis else ("pending", i), m.z_bottom_mm, m.b_mm, m.d_mm, m.source)
        buckets.setdefault(key, []).append(i)
    out = []
    for indices in buckets.values():
        items = tuple(kept[i] for i in indices)
        missing = tuple(dict.fromkeys(r for i in indices for r in reasons[i]))
        segments = []
        if not missing:
            spans = sorted((axes[i][2], axes[i][3]) for i in indices)
            merged = []
            for lo, hi in spans:
                if merged and lo <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
                else:
                    merged.append((lo, hi))
            direction, fixed = axes[indices[0]][:2]
            segments = [(lo, fixed, hi, fixed) if direction == "H" else (fixed, lo, fixed, hi) for lo, hi in merged]
        out.append(_TieGroup(items, tuple(segments), missing))
    return out


def _tie_evidence(group: _TieGroup) -> list[str]:
    evidence = []
    for m in group.members:
        raw = m.length_mm * m.b_mm * m.d_mm / 1e9 if m.b_mm is not None and m.d_mm is not None else None
        evidence.append(f"{m.id} ({m.source}) trục ({m.x1:g},{m.y1:g})–({m.x2:g},{m.y2:g}); "
                        f"b={m.b_mm}, d={m.d_mm} mm; z đáy={m.z_bottom_mm} mm tương đối đáy tầng/tường; "
                        f"{m.z_evidence or 'chưa ghi chứng cứ cao độ'}; BT thô trước hợp={raw} m³")
    return evidence


def linear_works(plan: str, members: list[LinearMember], *,
                 tie_groups: list[_TieGroup] | None = None) -> tuple[list[WorkItem], list[str]]:
    works, warnings = [], []
    ties = normalize_ties(members) if tie_groups is None else tie_groups
    for group in ties:
        first = group.members[0]
        b, d = first.b_mm, first.d_mm
        missing = list(group.missing)
        length = sum(math.hypot(x2 - x1, y2 - y1) for x1, y1, x2, y2 in group.segments) / 1000
        evidence = _tie_evidence(group)
        ids = ", ".join(m.id for m in group.members[:5])
        label = f"giằng ({ids})"
        inputs = ["cao độ đáy giằng: C (người dùng xác nhận trong mặt bằng)"] if not missing else []
        for code, quantity, formula, extra in (
            ("GIANG_TUONG", None if missing else length * b * d / 1e6,
             f"dài hợp {_fmt(length)} m × b={b} mm × d={d} mm; z đáy={first.z_bottom_mm} mm", {}),
            ("COP_PHA", None if missing else 2 * d / 1000 * length,
             f"2 × cao {d} mm × dài hợp {_fmt(length)} m (đáy nằm trên tường)", {"formwork_of": "GIANG_TUONG"}),
        ):
            works.append(_work(code, quantity, plan=plan, element=label, source=first.source,
                               formula=formula, missing=missing, evidence=evidence,
                               status="D" if missing else "C", inputs=inputs, **extra))
        warnings += [f"{plan}, {label}: {reason}." for reason in missing]
    # Sê nô giữ cách tính cũ, không đi qua quy tắc hợp giằng.
    groups = {}
    for m in members:
        if m.keep and m.kind == "SE_NO":
            groups.setdefault((m.b_mm, m.d_mm, m.source), []).append(m)
    for (b, d, source), items in sorted(groups.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1] or 0, kv[0][2])):
        length = sum(m.length_mm for m in items) / 1000
        missing = [lab for value, lab in ((b, "rộng sê nô"), (d, "cao sê nô")) if value is None]
        ids = ", ".join(sorted({m.id for m in items})[:5])
        label = f"{len(items)} sê nô" + (f" {b:.0f}×{d:.0f}" if not missing else "") + f" ({ids})"
        evidence = [f"{m.id} ({m.source}) trục ({m.x1:.0f},{m.y1:.0f})–({m.x2:.0f},{m.y2:.0f})" for m in items]
        works.append(_work("SE_NO", length * b * d / 1e6 if not missing else None, plan=plan, element=label,
                           missing=missing, source=source, evidence=evidence,
                           formula=f"{_fmt(length)} m × {_fmt(b / 1000) if b else 'rộng'} m × {_fmt(d / 1000) if d else 'cao'} m"))
        works.append(_work("COP_PHA", None if missing else (2 * d + b) / 1000 * length, plan=plan,
                           element=f"cốp pha {label}", formwork_of="SE_NO", missing=missing, source=source,
                           formula="(2 × cao + rộng) × dài"))
    if groups:
        warnings.append(f"{plan}: sê nô tính theo tiết diện chữ nhật rộng × cao (quy ước gần đúng); sê nô chữ U cần sửa tay.")
    return works, warnings


def _clip(x1, y1, x2, y2, rect) -> float:
    from .columns import _clip_length
    return _clip_length(x1, y1, x2, y2, rect)


def _xay_of(works: list[WorkItem], plan: str, wall, system) -> Optional[WorkItem]:
    label = f"tường {wall.cls} {ROLE_VI.get(wall.role, wall.role)}"
    return next((w for w in works if w.code == "XAY" and w.plan == plan and w.element == label
                 and w.wall_system_id == system), None)


def deduct_ties(works: list[WorkItem], plan: str, walls, systems: dict, members: list[LinearMember], catalog, *,
                tie_groups: list[_TieGroup] | None = None, wall_height_mm: float | None = None,
                openings: list[ReviewOpening] | None = None,
                column_len_in_walls: dict[str, float] | None = None) -> list[str]:
    """Trừ dải giằng đã xác nhận; thiếu cơ sở giao thì giữ raw và treo net đúng nhóm XAY."""
    warnings = []
    view = catalog.wall_view().set_index("wall_system_id") if not catalog.wall_systems.empty else pd.DataFrame()
    ties = normalize_ties(members) if tie_groups is None else tie_groups
    affected = {}
    for group in ties:
        first = group.members[0]
        segments = group.segments or tuple((m.x1, m.y1, m.x2, m.y2) for m in group.members)
        for wall in walls:
            if not (wall.keep and wall.masonry):
                continue
            laps, off_axis = [], False
            for x1, y1, x2, y2 in segments:
                if not all(math.isfinite(v) for v in (x1, y1, x2, y2)):
                    laps.append(1.0)  # vị trí chưa biết: mọi tường có thể bị ảnh hưởng, không dùng làm lượng
                    off_axis = True
                    continue
                horizontal = abs(y2 - y1) < abs(x2 - x1)
                tx, ty = (0, AXIS_TOL_MM) if horizontal else (AXIS_TOL_MM, 0)
                rect = (min(x1, x2) - tx, min(y1, y2) - ty, max(x1, x2) + tx, max(y1, y2) + ty)
                lap = _clip(wall.x1, wall.y1, wall.x2, wall.y2, rect)
                if lap <= 0:
                    continue
                laps.append(lap)
                if not (wall.y1 == wall.y2 == y1 == y2 or wall.x1 == wall.x2 == x1 == x2):
                    off_axis = True
            xay = _xay_of(works, plan, wall, systems.get(wall.id))
            if not laps or xay is None:
                continue
            target = affected.setdefault(id(xay), {"work": xay, "raw": xay.quantity, "volume": 0.0, "missing": [], "evidence": []})
            reasons = list(group.missing)
            if off_axis:
                reasons.append("trục giằng/tường chưa cùng trục thực hoặc chưa xác định: chưa thể trừ chính xác")
            if wall_height_mm is None or not math.isfinite(wall_height_mm) or wall_height_mm <= 0:
                reasons.append("chiều cao khối xây thực để kiểm vị trí đứng giằng")
            elif first.z_bottom_mm is not None and first.d_mm is not None:
                if first.z_bottom_mm < 0 or first.z_bottom_mm + first.d_mm > wall_height_mm:
                    reasons.append("giằng vượt đáy/đỉnh khối xây: chưa hỗ trợ cắt giao đứng")
            if openings is None:
                reasons.append("chưa có danh sách lỗ mở để kiểm giao giằng")
            elif any(o.keep and o.wall == wall.id for o in openings):
                reasons.append("tường có lỗ mở/lanh tô nhưng thiếu vị trí giao giằng (cần kiểm, chưa khẳng định giao)")
            if column_len_in_walls is None:
                reasons.append("chưa có phần cột đã trừ khỏi tường để kiểm giao giằng")
            elif column_len_in_walls.get(wall.id, 0) > 0:
                reasons.append("tường đã trừ cột nhưng chưa có khoảng giao giằng (cần kiểm)")
            ids = ", ".join(m.id for m in group.members)
            target["evidence"] += [f"tường {wall.id}; giằng {ids}; cao xây thực={wall_height_mm} mm", *_tie_evidence(group)]
            target["missing"] += [f"tường {wall.id}: {r}" for r in reasons]
            if not reasons:
                thick, _ = _thickness_m(systems.get(wall.id), wall.cls, view)
                volume = sum(laps) / 1000 * first.d_mm / 1000 * thick
                target["volume"] += volume
                target["evidence"].append(f"phần trừ giằng đã hợp {ids}: {_fmt(volume)} m³")
    for target in affected.values():
        xay, raw, volume = target["work"], target["raw"], target["volume"]
        evidence = [f"XAY trước trừ giằng của nhóm '{xay.element}': {raw} m³", *target["evidence"]]
        xay.evidence = list(dict.fromkeys([*xay.evidence, *evidence]))
        if raw is not None and volume > raw:
            target["missing"].append("tổng dải giằng vượt lượng xây trước trừ: cần kiểm giao, không ép về 0")
        reasons = list(dict.fromkeys(target["missing"]))
        if reasons:
            xay.quantity = None
            xay.status = "D"
            xay.missing = list(dict.fromkeys([*xay.missing, *reasons]))
            xay.formula += f"; trước trừ giằng={raw} m³; net chưa xác định (xem evidence/missing)"
            warnings += [f"{plan}, {xay.element}: {r}." for r in reasons]
        elif raw is not None:
            xay.quantity = round(raw - volume, 3)
            xay.status = worst_status(xay.status, "C")
            xay.inputs = list(dict.fromkeys([*xay.inputs, "cao độ giằng dùng trừ xây: C (người dùng xác nhận)"]))
            xay.formula += f" − {_fmt(volume)} m³ giằng đã hợp theo cao độ"
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
        if not o.keep or w is None or o.h is None or o.h + lt <= h_wall:
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
