"""Cốt thép (đặc tả mục 3.11) và móng nhập tay (mục 3.12).

    cốt thép (tấn) = bảng thống kê thép của cấu kiện nếu có; không thì Σ m³ bê tông của cấu kiện × hàm lượng (kg/m³) / 1000
Hàm lượng nhập riêng cho từng loại cấu kiện; thiếu loại nào thì cốt thép loại đó để trống. Chưa chia nhóm đường kính
(cần bảng thống kê thép).

Móng: Quy ước B3 chưa có công thức, người dùng nhập từng loại móng (số khối × dài × rộng × cao hoặc thể tích):
    bê tông móng = Σ số khối × thể tích một khối
    bê tông lót  = Σ số khối × dài × rộng × dày lót
    cốp pha móng = Σ số khối × 2 × (dài + rộng) × cao
Đào đắp đất không sinh vật liệu mua về nên không tính ở đây.
"""
from __future__ import annotations

from .materials import _fmt
from .models import STEEL_ELEMENTS, ProjectParams, WorkItem
from .walls import _work


def steel_works(works: list[WorkItem], params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    out, warnings = [], []
    for code, label in STEEL_ELEMENTS.items():
        if code in params.steel_schedule_t:
            out.append(_work("COT_THEP", params.steel_schedule_t[code], element=f"thép {label}", steel_element=code,
                             source="manual", formula=f"{_fmt(params.steel_schedule_t[code])} tấn theo bảng thống kê thép"))
            continue
        members = [w for w in works if w.code == code]
        if not members:
            continue
        plans = sorted({w.plan for w in members}, key=lambda p: [m.plan for m in members].index(p))
        kg = params.steel_kg_per_m3.get(code)
        for plan in plans:
            items = [w for w in members if w.plan == plan]
            known = [w.quantity for w in items if w.quantity is not None]
            m3 = sum(known)
            missing = ([] if kg is not None else [f"hàm lượng thép {label} (kg/m³)"]) + \
                      ([f"khối lượng bê tông {label}"] if len(known) < len(items) else [])
            out.append(_work("COT_THEP", m3 * kg / 1000 if kg is not None and known else None, plan=plan,
                             element=f"thép {label}", steel_element=code, missing=missing,
                             formula=f"{_fmt(m3)} m³ × " + (f"{_fmt(kg)} kg/m³" if kg is not None else "hàm lượng")))
    return out, warnings


def foundation_works(params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    out, warnings = [], []
    for f in params.foundations:
        dims = (f.length_mm, f.width_mm, f.height_mm)
        one = f.volume_m3 if f.volume_m3 is not None else (
            f.length_mm * f.width_mm * f.height_mm / 1e9 if None not in dims else None)
        miss = [] if one is not None else ["kích thước hoặc thể tích móng"]
        label = f"{f.count} móng {f.name}"
        out.append(_work("MONG", f.count * one if one is not None else None, element=label, source="manual", missing=miss,
                         formula=(f"{f.count} × {_fmt(one)} m³" if f.volume_m3 is not None or one is None else
                                  f"{f.count} × {_fmt(f.length_mm / 1000)} × {_fmt(f.width_mm / 1000)} × {_fmt(f.height_mm / 1000)} m")))
        if f.lean_thickness_mm is not None:
            ok = f.length_mm is not None and f.width_mm is not None
            out.append(_work("BE_TONG_LOT", f.count * f.length_mm * f.width_mm * f.lean_thickness_mm / 1e9 if ok else None,
                             element=f"lót {label}", source="manual", missing=[] if ok else ["dài, rộng móng"],
                             formula=f"{f.count} × dài × rộng × {_fmt(f.lean_thickness_mm / 1000)} m"))
        if None not in dims:
            out.append(_work("COP_PHA", f.count * 2 * (f.length_mm + f.width_mm) * f.height_mm / 1e6, element=f"cốp pha {label}",
                             formwork_of="MONG",
                             source="manual", formula=f"{f.count} × 2 × ({_fmt(f.length_mm / 1000)} + {_fmt(f.width_mm / 1000)}) × "
                                                      f"{_fmt(f.height_mm / 1000)} m"))
        else:
            warnings.append(f"Móng {f.name}: chưa có đủ dài, rộng, cao nên chưa tính cốp pha móng.")
    return out, warnings
