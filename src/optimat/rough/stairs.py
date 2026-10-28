"""Cầu thang bê tông cốt thép (đặc tả mục 3.7). Quy ước B3 chưa có công thức chi tiết; công thức dưới đây là cách
bóc thông dụng, cần giảng viên duyệt. Thông số thang người dùng nhập (bản vẽ chỉ cho biết có thang: cặp nét bị loại vì
"bậc thang / lan can").

Một thang nối mặt bằng này với tầng trên, cao H:
    cao bậc               = H / số bậc
    dài bản thang (m)     = √((số bậc × rộng bậc)² + H²)
    bê tông bản thang     = rộng vế × dài bản thang × dày bản thang
    bê tông bậc           = số bậc × (rộng bậc × cao bậc / 2) × rộng vế
    bê tông chiếu nghỉ    = diện tích chiếu nghỉ × dày bản thang
    cốp pha               = rộng vế × dài bản thang + diện tích chiếu nghỉ (đáy) + số bậc × cao bậc × rộng vế (thành bậc)
    dầm thang/chiếu nghỉ  = dài × rộng × cao (nhập riêng; cộng vào bê tông cầu thang), cốp pha (2 × cao + rộng) × dài
Quy ước đầu vào (S08-01): chỉ thang bản (kind = "ban"); thang cốn, thang xoắn ghi Not supported, không trả số.
"""
from __future__ import annotations

import math
from typing import Literal, Optional

from pydantic import BaseModel

from .materials import _fmt
from .models import ProjectParams, WorkItem
from .walls import _work


class Stair(BaseModel):
    id: str = "T1"
    steps: Optional[int] = None              # tổng số bậc từ sàn này lên sàn trên
    flight_width_mm: Optional[float] = None  # bề rộng vế
    tread_mm: Optional[float] = None         # bề rộng mặt bậc
    landing_area_m2: float = 0.0             # chiếu nghỉ (0: thang một vế)
    kind: Literal["ban", "con", "xoan"] = "ban"   # thang bản | thang cốn | thang xoắn
    beam_length_mm: float = 0.0              # tổng dài dầm thang, dầm chiếu nghỉ (0: không có)
    beam_width_mm: Optional[float] = None
    beam_depth_mm: Optional[float] = None
    keep: bool = True


def stair_works(plan: str, stairs: list[Stair], height_mm: float, params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    works, warnings = [], []
    t = params.stair_slab_thickness_mm
    for s in (s for s in stairs if s.keep):
        missing = [label for v, label in ((s.steps, "số bậc"), (s.flight_width_mm, "bề rộng vế"),
                                          (s.tread_mm, "bề rộng bậc"), (t, "dày bản thang")) if v is None]
        label = f"thang {s.id}"
        if s.kind != "ban":
            works.append(_work("CAU_THANG", None, plan=plan, element=label, basis="not_supported",
                               missing=[f"Not supported: thang {'cốn' if s.kind == 'con' else 'xoắn'} chưa có quy ước đo bóc"]))
            continue
        if s.beam_length_mm and (s.beam_width_mm is None or s.beam_depth_mm is None):
            missing.append("tiết diện dầm thang")
        if missing:
            works.append(_work("CAU_THANG", None, plan=plan, element=label, missing=missing))
            works.append(_work("COP_PHA", None, plan=plan, element=f"cốp pha {label}", formwork_of="CAU_THANG", missing=missing))
            continue
        H, n, w, b, tt = height_mm / 1000, s.steps, s.flight_width_mm / 1000, s.tread_mm / 1000, t / 1000
        riser = H / n
        slope = math.hypot(n * b, H)
        slab = w * slope * tt
        steps = n * b * riser / 2 * w
        landing = s.landing_area_m2 * tt
        bl = s.beam_length_mm / 1000
        bb, bd = (s.beam_width_mm or 0) / 1000, (s.beam_depth_mm or 0) / 1000
        beam_txt = f" + dầm thang {_fmt(bl)} × {_fmt(bb)} × {_fmt(bd)}" if bl else ""
        works.append(_work("CAU_THANG", slab + steps + landing + bl * bb * bd, plan=plan, element=label,
                           formula=f"bản {_fmt(w)} × {_fmt(slope)} × {_fmt(tt)} + bậc {n} × {_fmt(b)} × {_fmt(riser)} / 2 × {_fmt(w)}"
                                   f" + chiếu nghỉ {_fmt(s.landing_area_m2)} × {_fmt(tt)}" + beam_txt))
        works.append(_work("COP_PHA", w * slope + s.landing_area_m2 + n * riser * w + (2 * bd + bb) * bl, plan=plan,
                           element=f"cốp pha {label}", formwork_of="CAU_THANG",
                           formula=f"{_fmt(w)} × {_fmt(slope)} + {_fmt(s.landing_area_m2)} + {n} × {_fmt(riser)} × {_fmt(w)}"
                                   + (f" + (2 × {_fmt(bd)} + {_fmt(bb)}) × {_fmt(bl)}" if bl else "")))
    if works:
        warnings.append(f"{plan}: công thức cầu thang là cách bóc thông dụng, Quy ước B3 chưa có; cần giảng viên duyệt.")
    return works, warnings
