"""Móng, bê tông lót, đào và đắp đất hố móng (sprint S05). Kích thước móng nhập tay hoặc đọc từ chi tiết (structural.py);
thiếu số thì để trống kèm cảnh báo, không lấy kích thước mặc định (Quy ước B7).

Biểu thức theo loại móng (mm đổi ra m; n = số khối):
    móng đơn, móng băng  một khối = Σ thể tích từng lớp (tiers, kể từ dưới lên); không có lớp thì một lớp dài × rộng × cao
                         (móng băng: dài = chiều dài băng đã trừ phần giao với băng khác)
    lớp hộp              V = dài × rộng × cao                      cốp pha = 2 × (dài + rộng) × cao
    lớp vát (top_*)      V = h/6 × (A_đáy + 4 A_giữa + A_đỉnh)     cốp pha: không tính (mặt vát đổ không ghép ván)
    bê tông lót          n × dài × rộng lớp dưới cùng × dày lót (tách khỏi bê tông kết cấu)
    sâu đào H            cốt tự nhiên − (cao độ đáy móng − dày lót)
    hố đào               đáy (dài + 2c) × (rộng + 2c), mái m: đỉnh rộng thêm 2mH mỗi chiều; V = H/6 × (A_đáy + 4 A_giữa + A_đỉnh)
    đắp lại              V hố − V lót − V móng − V cổ móng chôn dưới cốt tự nhiên; âm thì để trống và báo
Hố chồng lấn (có vị trí từng khối): phần chung chỉ tính một lần, trừ bằng tích phân diện tích hợp theo độ sâu.
c (mở rộng đáy hố), m (hệ số mái), cốt tự nhiên do người dùng xác nhận theo hồ sơ; chưa nhập thì chưa tính đào đắp.
"""
from __future__ import annotations

import math

from .materials import _fmt
from .models import FootingTier, FoundationItem, ProjectParams, WorkItem
from .quantity_details import lean_foundation_row, summarize
from .walls import _work

SLICES = 200                 # số lát cắt theo độ sâu khi tính phần hố chồng lấn
SAME_SPOT_MM = 100.0         # hai khối cùng loại có tâm gần hơn khoảng này là một khối vẽ trùng


def tiers_of(f: FoundationItem) -> list[FootingTier] | None:
    if f.tiers:
        return f.tiers
    if None in (f.length_mm, f.width_mm, f.height_mm):
        return None
    return [FootingTier(length_mm=f.length_mm, width_mm=f.width_mm, height_mm=f.height_mm)]


def _prismoid(l0: float, w0: float, l1: float, w1: float, h: float) -> float:
    """Khối có hai đáy chữ nhật song song, cạnh thay đổi tuyến tính (đúng cho cả hộp và chóp cụt)."""
    return h / 6 * (l0 * w0 + 4 * (l0 + l1) / 2 * (w0 + w1) / 2 + l1 * w1)


def tier_volume_m3(t: FootingTier) -> float:
    l1, w1 = t.top_length_mm if t.top_length_mm is not None else t.length_mm, t.top_width_mm if t.top_width_mm is not None else t.width_mm
    return _prismoid(t.length_mm, t.width_mm, l1, w1, t.height_mm) / 1e9


def tier_formwork_m2(t: FootingTier) -> float:
    return 0.0 if t.top_length_mm is not None or t.top_width_mm is not None else 2 * (t.length_mm + t.width_mm) * t.height_mm / 1e6


def _tier_text(t: FootingTier) -> str:
    s = f"{_fmt(t.length_mm / 1000)}×{_fmt(t.width_mm / 1000)}×{_fmt(t.height_mm / 1000)}"
    if t.top_length_mm is not None or t.top_width_mm is not None:
        s += f" vát lên {_fmt((t.top_length_mm or t.length_mm) / 1000)}×{_fmt((t.top_width_mm or t.width_mm) / 1000)}"
    return s


def pit(f: FoundationItem, params: ProjectParams) -> tuple[dict | None, list[str], list[str]]:
    """Hố đào của một khối: ({dài đáy, rộng đáy, sâu, mái} mm) hoặc None, thiếu gì, cảnh báo cao độ."""
    tiers = tiers_of(f)
    need = [(params.natural_ground_level_mm, "cốt đất tự nhiên"), (params.excavation_margin_mm, "mở rộng đáy hố đào"),
            (params.excavation_slope, "hệ số mái taluy"), (f.bottom_level_mm, f"cao độ đáy móng {f.name}"),
            (f.lean_thickness_mm, f"dày lót móng {f.name}"), (tiers, f"kích thước móng {f.name}")]
    missing = [label for v, label in need if v is None]
    if missing:
        return None, missing, []
    depth = params.natural_ground_level_mm - (f.bottom_level_mm - f.lean_thickness_mm)
    top = f.bottom_level_mm + sum(t.height_mm for t in tiers)
    if depth <= 0:
        return None, [f"cao độ đáy móng {f.name} thấp hơn cốt đất tự nhiên"], [
            f"Móng {f.name}: đáy lót ({f.bottom_level_mm - f.lean_thickness_mm:.0f}) không thấp hơn cốt tự nhiên "
            f"({params.natural_ground_level_mm:.0f}): không đủ cao độ để đào, kiểm tra cao độ."]
    warn = []
    if top > params.natural_ground_level_mm:
        warn.append(f"Móng {f.name}: mặt móng ({top:.0f}) cao hơn cốt đất tự nhiên ({params.natural_ground_level_mm:.0f}): "
                    "hố đào không đủ sâu để chôn móng, kiểm tra cốt tự nhiên và cao độ đáy móng.")
    c = params.excavation_margin_mm
    return ({"l": tiers[0].length_mm + 2 * c, "w": tiers[0].width_mm + 2 * c, "d": depth, "m": params.excavation_slope,
             "top": top}, [], warn)


def pit_volume_m3(p: dict) -> float:
    grow = 2 * p["m"] * p["d"]
    return _prismoid(p["l"], p["w"], p["l"] + grow, p["w"] + grow, p["d"]) / 1e9


def _union_area(rects: list[tuple[float, float, float, float]]) -> float:
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    area = 0.0
    for xa, xb in zip(xs, xs[1:]):
        spans = sorted((r[1], r[3]) for r in rects if r[0] <= xa and r[2] >= xb)
        cover, end = 0.0, -math.inf
        for y0, y1 in spans:
            if y1 > end:
                cover += y1 - max(y0, end)
                end = y1
        area += cover * (xb - xa)
    return area


def pit_overlap_m3(pits: list[tuple[float, float, dict]]) -> float:
    """Thể tích bị đếm lặp khi cộng riêng từng hố: ∫ (Σ diện tích − diện tích hợp) theo độ sâu. Hố tách rời: 0."""
    deepest = max(p["d"] for _, _, p in pits)
    dz = deepest / SLICES
    extra = 0.0
    for k in range(SLICES):
        z = (k + 0.5) * dz                    # độ sâu tính từ cốt tự nhiên
        rects = []
        for x, y, p in pits:
            if z < p["d"]:
                hl, hw = p["l"] / 2 + p["m"] * (p["d"] - z), p["w"] / 2 + p["m"] * (p["d"] - z)
                rects.append((x - hl, y - hw, x + hl, y + hw))
        if len(rects) > 1:
            extra += (sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects) - _union_area(rects)) * dz
    return extra / 1e9


def _neg(code: str, q: float, **kw) -> WorkItem:
    """Dòng trừ (số âm): _work không nhận số âm."""
    kw.setdefault("dimensions", [dict(label=kw.get("element", "khoản trừ"), basis="deduction",
        source="Hình học khoản trừ, xem evidence của công tác",
        note="Khoản trừ không có dài/rộng/cao độc lập; không phải cấu kiện mới")])
    w = _work(code, 0.0, **kw)
    return w.model_copy(update={"quantity": round(-q, 3)})


def _footing_rows(foundations: list[FoundationItem]):
    """Một ký hiệu có thể xuất hiện ở nhiều vị trí hoặc trong hai chi tiết mâu thuẫn."""
    groups: dict[str, list[FoundationItem]] = {}
    warnings = []
    for f in foundations:
        key = f.name.strip().upper()
        group = groups.setdefault(key, [])
        if any(f.model_copy(update={"name": prev.name}) == prev for prev in group):
            warnings.append(f"Móng {f.name} nhập hai lần với cùng dữ liệu và nguồn: chỉ giữ một dòng.")
        else:
            group.append(f)

    rows = []
    for key, group in groups.items():
        issue = ""
        if len(group) > 1:
            located = all(f.plan and f.plan == group[0].plan and len(f.positions) == f.count and f.count > 0 for f in group)
            if not located or any(math.dist(p, q) < SAME_SPOT_MM for i, f in enumerate(group)
                                  for other in group[:i] for p in f.positions for q in other.positions):
                issue = f"Móng {key} có nhiều dòng cùng ký hiệu: cần đối chiếu vị trí từng khối trên cùng mặt bằng."
                warnings.append(issue)
        for i, f in enumerate(group, 1):
            rows.append((f, key if len(group) == 1 else f"{key}:{i}", issue))
    return rows, warnings


def foundation_works(params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    rows, warnings = _footing_rows(params.foundations)
    out = []
    earth = any(v is not None for v in (params.natural_ground_level_mm, params.excavation_margin_mm, params.excavation_slope))
    pits: list[tuple[float, float, dict]] = []
    no_pos = []
    for f, key, issue in rows:
        label = f"{f.count} móng {f.name}"
        src = f" [{f.source}]" if f.source else ""
        tiers = tiers_of(f)
        one = f.volume_m3 if f.volume_m3 is not None else (sum(tier_volume_m3(t) for t in tiers) if tiers else None)
        if f.volume_m3 is not None or one is None:
            formula = f"{f.count} × {_fmt(one) if one is not None else 'thể tích một khối'} m³"
        else:
            formula = f"{f.count} × (" + " + ".join(_tier_text(t) for t in tiers) + ") m"
        dimensions = [dict(label=f"{f.name} lớp {i+1}", count=f.count, length_m=t.length_mm/1000,
                           width_m=t.width_mm/1000, height_m=t.height_mm/1000,
                           top_length_m=(t.top_length_mm if t.top_length_mm is not None else t.length_mm)/1000,
                           top_width_m=(t.top_width_mm if t.top_width_mm is not None else t.width_mm)/1000,
                           basis="reference" if f.volume_m3 is not None else "input", source=f.source or "Thông số móng người dùng nhập",
                           note=(f"Đỉnh lớp vát: {t.top_length_mm if t.top_length_mm is not None else t.length_mm:g} × {t.top_width_mm if t.top_width_mm is not None else t.width_mm:g} mm" if t.top_length_mm is not None or t.top_width_mm is not None else "Lớp hộp") + ("; thể tích nhập trực tiếp được ưu tiên, kích thước chỉ tham khảo" if f.volume_m3 is not None else "")) for i,t in enumerate(tiers or [])]
        if not dimensions:
            dimensions = [dict(label=f.name, count=f.count, basis="reference" if f.volume_m3 is not None else "input", length_m=None if f.length_mm is None else f.length_mm/1000,
                width_m=None if f.width_mm is None else f.width_mm/1000, height_m=None if f.height_mm is None else f.height_mm/1000,
                source=f.source or "Thông số móng người dùng nhập", note="Nhập thể tích không suy ra dài/rộng/cao" if f.volume_m3 is not None else "Thiếu kích thước móng")]
        if f.gross_length_mm is not None:
            dimensions.append(dict(label=f"{f.name} toàn băng", count=f.count, length_m=f.gross_length_mm / 1000,
                                   basis="reference", source=f.source or "Chi tiết móng băng",
                                   note="Chiều dài gộp trên bản vẽ, chưa trừ phần giao"))
        if issue:
            codes = ["MONG", "COP_PHA"]
            if f.lean_thickness_mm is not None:
                codes.append("BE_TONG_LOT")
            if earth:
                codes.extend(["DAO_DAT", "DAP_DAT"])
            for code in codes:
                out.append(_work(code, None, element=f"{label} ({key})", missing=[issue],
                                 evidence=[f.source] if f.source else [], formwork_of="MONG" if code == "COP_PHA" else None,
                                 dimensions=[{**dim, "basis": "reference"} for dim in dimensions]))
            continue
        out.append(_work("MONG", f.count * one if one is not None else None, dimensions=dimensions, element=label, source="manual",
                         missing=[] if one is not None else [
                             f"móng băng {f.name}: cần tiết diện và chiều dài sau khi xử lý phần giao"
                             if f.kind == "bang" else f"kích thước móng {f.name} (chưa có chi tiết móng)"],
                         formula=formula + src))
        base = tiers[0] if tiers else None
        if f.lean_thickness_mm is not None:
            lean_q = f.count * base.length_mm * base.width_mm * f.lean_thickness_mm / 1e9 if base else None
            lean = _work("BE_TONG_LOT", lean_q,
                             dimensions=[dict(label=f"lót {f.name}", count=f.count, length_m=base.length_mm/1000 if base else None,
                                width_m=base.width_mm/1000 if base else None, thickness_m=f.lean_thickness_mm/1000,
                                source=f.source or "Thông số móng người dùng nhập")], element=f"lót {label}", source="manual", missing=[] if base else ["dài, rộng móng"],
                             formula=(f"{f.count} × {_fmt(base.length_mm / 1000)} × {_fmt(base.width_mm / 1000)} × "
                                      if base else f"{f.count} × dài × rộng × ") + f"{_fmt(f.lean_thickness_mm / 1000)} m" + src)
            row = lean_foundation_row(f, base, row_id=f"lean:{key}", raw_quantity=lean_q)
            detail = summarize([row], lean.unit, lean.quantity, scope_complete=not lean.missing,
                               detail_level="unavailable" if row.role == "reference" else "components")
            out.append(WorkItem.model_validate({**lean.model_dump(), "quantity_detail": detail.model_dump()}))
        if tiers:
            form = sum(tier_formwork_m2(t) for t in tiers)
            out.append(_work("COP_PHA", f.count * form, dimensions=dimensions, element=f"cốp pha {label}", formwork_of="MONG", source="manual",
                             formula=f"{f.count} × Σ 2 × (dài + rộng) × cao các lớp thẳng đứng = {f.count} × {_fmt(form)} m²"
                                     + (" (mặt vát không tính)" if any(tier_formwork_m2(t) == 0 for t in tiers) else "") + src))
        elif f.volume_m3 is None:
            warnings.append(f"Móng {f.name}: chưa có đủ dài, rộng, cao nên chưa tính cốp pha móng.")
        else:
            warnings.append(f"Móng {f.name}: nhập thể tích, chưa tính cốp pha móng (cần kích thước).")
        if not earth:
            continue
        p, miss, warn = pit(f, params)
        warnings += warn
        if p is None:
            out.append(_work("DAO_DAT", None, element=f"hố {label}", missing=miss))
            out.append(_work("DAP_DAT", None, element=f"hố {label}", missing=miss))
            continue
        pit_dimensions = [dict(label=f"hố {f.name}", count=f.count, basis="reference", length_m=p['l']/1000, width_m=p['w']/1000,
                               height_m=p['d']/1000, slope_ratio=p['m'],
                               top_level_m=params.natural_ground_level_mm/1000,
                               bottom_level_m=(params.natural_ground_level_mm-p['d'])/1000, source=f.source or "Thông số móng và hố đào người dùng nhập",
                               note=f"Dài/rộng đáy hố; cao là sâu đào; taluy {p['m']:g}; không phải kích thước khối đất đắp")]
        v_pit = pit_volume_m3(p)
        out.append(_work("DAO_DAT", f.count * v_pit, dimensions=pit_dimensions, element=f"hố {label}", source="manual",
                         formula=f"{f.count} × H/6 × (A đáy + 4 A giữa + A đỉnh): đáy {_fmt(p['l'] / 1000)}×{_fmt(p['w'] / 1000)} m, "
                                 f"sâu H {_fmt(p['d'] / 1000)} m, mái m {_fmt(p['m'])}" + src))
        buried = 0.0 if p["top"] >= params.natural_ground_level_mm else params.natural_ground_level_mm - p["top"]
        neck_ok = buried == 0 or None not in (f.neck_b_mm, f.neck_h_mm)
        if one is None or not neck_ok:
            out.append(_work("DAP_DAT", None, dimensions=pit_dimensions, element=f"hố {label}",
                             missing=([] if one is not None else [f"thể tích móng {f.name}"]) +
                                     ([] if neck_ok else [f"tiết diện cổ móng {f.name}"])))
        else:
            neck = (f.neck_b_mm * f.neck_h_mm * buried / 1e9) if buried else 0.0
            lean = base.length_mm * base.width_mm * f.lean_thickness_mm / 1e9
            fill = v_pit - lean - one - neck
            if fill < 0:
                warnings.append(f"Móng {f.name}: khối lượng đắp âm ({_fmt(fill)} m³/khối): hố đào nhỏ hơn khối móng, "
                                "kiểm tra mở rộng đáy hố, cao độ và kích thước móng.")
                out.append(_work("DAP_DAT", None, dimensions=pit_dimensions, element=f"hố {label}", missing=["khối lượng đắp âm (xem cảnh báo)"]))
            else:
                out.append(_work("DAP_DAT", f.count * fill, dimensions=pit_dimensions, element=f"hố {label}", source="manual",
                                 formula=f"{f.count} × ({_fmt(v_pit)} hố − {_fmt(lean)} lót − {_fmt(one)} móng − {_fmt(neck)} cổ móng) m³"))
        if f.positions:
            if len(f.positions) != f.count:
                warnings.append(f"Móng {f.name}: {len(f.positions)} vị trí khác {f.count} khối, chưa kiểm tra chồng lấn hố đào.")
                no_pos.append(f.name)
            else:
                pits += [(x, y, p) for x, y in f.positions]
        else:
            no_pos.append(f.name)
    if earth and no_pos:
        warnings.append(f"Chưa có vị trí móng {', '.join(no_pos)}: chưa kiểm tra hố đào chồng lấn.")
    if len(pits) > 1:
        extra = pit_overlap_m3(pits)
        if extra > 1e-4:
            warnings.append(f"Hố đào chồng lấn nhau: phần chung {_fmt(extra)} m³ đã trừ một lần (nên xét đào chung hố hoặc đào băng).")
            out.append(_neg("DAO_DAT", extra, element="trừ phần hố đào chồng lấn", source="auto",
                            formula=f"−∫(Σ diện tích hố − diện tích hợp) dz = −{_fmt(extra)} m³"))
            if any(w.code == "DAP_DAT" and w.quantity is not None for w in out):
                out.append(_neg("DAP_DAT", extra, element="trừ phần hố đào chồng lấn", source="auto",
                                formula=f"−{_fmt(extra)} m³ (đất đắp trong phần hố chung)"))
    elif not earth and params.foundations:
        warnings.append("Chưa tính đào, đắp đất hố móng: nhập cốt đất tự nhiên, mở rộng đáy hố, hệ số mái theo hồ sơ.")
    return out, warnings


def footing_rects(foundations: list[FoundationItem], plan: str) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Khung mặt bằng (lớp trên cùng, nơi giằng gối vào) của từng khối móng có vị trí trên mặt bằng móng `plan`.
    shortcut: coi cạnh dài theo trục x như pit_overlap_m3; móng xoay 90° cần thêm hướng vào positions."""
    out = []
    rows, _ = _footing_rows(foundations)
    for f, _, issue in rows:
        tiers = tiers_of(f)
        if issue or f.plan != plan or not tiers:
            continue
        t = tiers[-1]
        hl, hw = (t.top_length_mm or t.length_mm) / 2, (t.top_width_mm or t.width_mm) / 2
        out += [(f.name, (x - hl, y - hw, x + hl, y + hw)) for x, y in f.positions]
    return out
