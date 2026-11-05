"""Cốt thép (đặc tả mục 3.11). Móng, đào đắp: rough/foundations.py.

    cốt thép (tấn) = bảng thống kê thép của cấu kiện nếu có (rebar.py: Σ số thanh × chiều dài cắt × kg/m);
                     không thì Σ m³ bê tông của cấu kiện × hàm lượng (kg/m³) / 1000 (ước tính, cần review)
Hàm lượng nhập riêng cho từng loại cấu kiện; thiếu cả bảng thép lẫn hàm lượng thì cốt thép loại đó để trống.
"""
from __future__ import annotations

from .materials import _fmt
from .models import STEEL_ELEMENTS, ProjectParams, WorkItem
from .rebar import RebarRow
from .walls import _work


def schedule_works(rows: list[RebarRow]) -> list[WorkItem]:
    """Dòng bảng thống kê thép -> công tác cốt thép, mỗi cấu kiện (C1, D2...) một dòng; basis = bang_thong_ke.
    Cấu kiện chưa có quy ước: một dòng Not supported, không trả số."""
    out = []
    groups: dict[tuple, list[RebarRow]] = {}
    for r in rows:
        groups.setdefault((r.element_code, r.element.strip().upper()), []).append(r)
    for (code, el), items in groups.items():
        evidence = [r.evidence for r in items]
        if code is None:
            out.append(_work("COT_THEP", None, element=f"thép {el or '(chưa rõ cấu kiện)'}", basis="not_supported",
                             evidence=evidence, formula="; ".join(r.formula for r in items),
                             missing=[f"Not supported: cấu kiện '{el}' chưa có quy ước (ky_hieu_cau_kien.csv, bang_thep.csv)"]))
            continue
        known = [r.kg for r in items if r.kg is not None]
        miss = [f"dòng {r.row} ({r.mark or r.dia_mm}): " + ", ".join(r.missing or ["khối lượng thép chưa xác định"])
                for r in items if r.missing or r.kg is None]
        out.append(_work("COT_THEP", sum(known) / 1000 if known else None, element=f"thép {STEEL_ELEMENTS[code]} {el}",
                         dimensions=[dict(label=f"{r.mark or r.row}: Ø{r.dia_mm:g}" if r.dia_mm is not None else f"dòng {r.row}", count=r.total_bars,
                            length_m=r.cut_length_mm/1000 if r.cut_length_mm is not None else None,
                            diameter_m=r.dia_mm/1000 if r.dia_mm is not None else None,
                            source=r.evidence, note="Dài cắt một thanh theo bảng; rộng/cao không áp dụng") for r in items],
                         steel_element=code, basis="bang_thong_ke", evidence=evidence, missing=miss,
                         formula=f"Σ {len(items)} dòng bảng thép: " + " + ".join(r.formula for r in items[:6])
                                 + (" + …" if len(items) > 6 else "") + " = " + _fmt(sum(known)) + " kg"))
    return out


def steel_works(works: list[WorkItem], params: ProjectParams,
                rebar: list[RebarRow] | None = None) -> tuple[list[WorkItem], list[str]]:
    """Ưu tiên: tấn nhập tay (steel_schedule_t) > bảng thống kê thép trên bản vẽ > hàm lượng kg/m³ người dùng nhập.
    Không có cả ba thì để trống và yêu cầu review; không bao giờ tự suy thép từ hình vẽ."""
    out, warnings = [], []
    rebar = rebar or []
    scheduled = {r.element_code for r in rebar if r.element_code}
    schedules = schedule_works(rebar)
    out += [w for w in schedules if w.steel_element not in params.steel_schedule_t]
    ratio_used = []
    for code, label in STEEL_ELEMENTS.items():
        if code in params.steel_schedule_t:
            inputs = [w for w in schedules if w.steel_element == code]
            out.append(_work("COT_THEP", params.steel_schedule_t[code], element=f"thép {label}", steel_element=code,
                             source="manual", basis="bang_thong_ke",
                             missing=[m for w in inputs for m in w.missing],
                             evidence=[e for w in inputs for e in w.evidence],
                             formula=f"{_fmt(params.steel_schedule_t[code])} tấn theo bảng thống kê thép"))
            continue
        if code in scheduled:
            continue
        members = [w for w in works if w.code == code]
        if not members:
            continue
        if params.steel_kg_per_m3.get(code) is not None:
            ratio_used.append(label)
        plans = sorted({w.plan for w in members}, key=lambda p: [m.plan for m in members].index(p))
        kg = params.steel_kg_per_m3.get(code)
        for plan in plans:
            items = [w for w in members if w.plan == plan]
            known = [w.quantity for w in items if w.quantity is not None]
            m3 = sum(known)
            missing = ([] if kg is not None else [f"hàm lượng thép {label} (kg/m³)", f"bảng thống kê thép {label}"]) + \
                      ([f"khối lượng bê tông {label}"] if len(known) < len(items) else []) + \
                      [m for w in items for m in w.missing]
            out.append(_work("COT_THEP", m3 * kg / 1000 if kg is not None and known else None, plan=plan,
                             element=f"thép {label}", steel_element=code, missing=missing,
                             basis="ham_luong" if kg is not None else None,
                             formula=f"{_fmt(m3)} m³ × " + (f"{_fmt(kg)} kg/m³" if kg is not None else "hàm lượng")))
    if ratio_used:
        warnings.append(f"Thép {', '.join(ratio_used)} ước theo hàm lượng kg/m³ người dùng nhập, không phải bảng thống kê "
                        "thép: cần review.")
    return out, warnings

