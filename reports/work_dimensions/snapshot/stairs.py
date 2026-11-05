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
import re
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
    source: str = "manual"                   # manual (người dùng nhập) | auto (nhận từ nét mũi bậc trên mặt bằng, B)


# Nhận thang trên mặt bằng: các nét mũi bậc là chuỗi nét thẳng song song, cùng dài (bề rộng vế), cách đều (bề rộng bậc).
TREAD_MM = (200.0, 350.0)        # bề rộng bậc
FLIGHT_MM = (600.0, 1800.0)      # bề rộng vế
MIN_LINES = 5                    # ít nhất 5 nét mũi bậc liên tiếp mới coi là một vế
GRID_CROSS = 3                   # có từ chừng này nét vuông góc cắt ngang cả vế: lưới gạch lát, không phải thang
RISER_MAX_M = 0.22               # cao bậc lớn hơn: số bậc nhận được có thể thiếu (chỉ cảnh báo, không sửa số)


def _flights(segs, axis: int) -> list[dict]:
    """Chuỗi nét mũi bậc theo một phương. axis 0: nét nằm ngang (bậc xếp theo y), 1: nét đứng (bậc xếp theo x)."""
    lines = []
    for s in segs:
        (a1, b1), (a2, b2) = ((s.x1, s.y1), (s.x2, s.y2)) if axis == 0 else ((s.y1, s.x1), (s.y2, s.x2))
        if abs(b1 - b2) > 20 or not FLIGHT_MM[0] <= abs(a2 - a1) <= FLIGHT_MM[1]:
            continue
        lines.append((min(a1, a2), max(a1, a2), (b1 + b2) / 2))
    groups: dict[tuple, list] = {}
    for lo, hi, pos in lines:      # cùng hai đầu (sai 50 mm) = cùng một vế
        groups.setdefault((round(lo / 50), round(hi / 50)), []).append((lo, hi, pos))
    out = []
    for g in groups.values():
        ps = sorted({round(p) for _, _, p in g})
        run = [ps[0]] if ps else []
        for p in ps[1:] + [None]:
            d = None if p is None else p - run[-1]
            step = run[1] - run[0] if len(run) > 1 else None
            if d is not None and TREAD_MM[0] <= d <= TREAD_MM[1] and (step is None or abs(d - step) <= 15):
                run.append(p)
                continue
            if len(run) >= 3:
                lo = sum(x[0] for x in g) / len(g)
                hi = sum(x[1] for x in g) / len(g)
                out.append({"axis": axis, "lo": lo, "hi": hi, "start": run[0], "end": run[-1], "lines": len(run),
                            "tread": (run[-1] - run[0]) / (len(run) - 1)})
            run = [] if p is None else ([run[-1], p] if d is not None and TREAD_MM[0] <= d <= TREAD_MM[1] else [p])
    return out


def _crossings(f: dict, segs) -> int:
    """Số nét vuông góc cắt ngang trọn chiều dài vế (lưới gạch lát có nhiều, thang chỉ có tay vịn, đường cắt)."""
    n = 0
    for s in segs:
        (a1, b1), (a2, b2) = ((s.x1, s.y1), (s.x2, s.y2)) if f["axis"] == 0 else ((s.y1, s.x1), (s.y2, s.x2))
        if abs(a1 - a2) <= 20 and f["lo"] + 20 < a1 < f["hi"] - 20 and min(b1, b2) <= f["start"] + 5 and max(b1, b2) >= f["end"] - 5:
            n += 1
    return n


def detect_stairs(drawing, min_lines: int = MIN_LINES) -> list[Stair]:
    """Thang trên một mặt bằng (đã cắt): mỗi vế là chuỗi nét mũi bậc; hai vế cạnh nhau cùng phương là thang hai vế,
    chiếu nghỉ = bề ngang hai vế × bề rộng vế. Số bậc = số nét mũi bậc + 1 mỗi vế. Kết quả là suy luận (B): người dùng kiểm tra."""
    segs = [s for s in drawing.segments if s.kind != "hatch"]
    flights = [f for axis in (0, 1) for f in _flights(segs, axis)
               if f["lines"] >= min_lines and _crossings(f, segs) < GRID_CROSS]
    stairs: list[Stair] = []
    used = set()
    for i, f in enumerate(flights):
        if i in used:
            continue
        used.add(i)
        w = f["hi"] - f["lo"]
        # vế song song kế bên (khe giữa hai vế < 1 vế, chồng lên nhau theo phương bậc): thang hai vế có chiếu nghỉ
        mate = next((j for j, g in enumerate(flights) if j not in used and g["axis"] == f["axis"]
                     and abs((g["hi"] - g["lo"]) - w) < 150 and 0 <= max(g["lo"], f["lo"]) - min(g["hi"], f["hi"]) < w
                     and min(g["end"], f["end"]) > max(g["start"], f["start"])), None)
        group = [f] + ([flights[mate]] if mate is not None else [])
        if mate is not None:
            used.add(mate)
        span = max(g["hi"] for g in group) - min(g["lo"] for g in group)
        stairs.append(Stair(id=f"T{len(stairs) + 1}", steps=sum(g["lines"] + 1 for g in group), flight_width_mm=round(w),
                            tread_mm=round(sum(g["tread"] for g in group) / len(group)),
                            landing_area_m2=round(span * w / 1e6, 3) if mate is not None else 0.0, source="auto"))
    return stairs


def building_stairs(subs: list, names: list[str]) -> tuple[list[list[Stair]], list[str]]:
    """Thang từng mặt bằng của cả nhà. Mặt bằng trệt thường chỉ vẽ vài bậc trước đường cắt: lấy thang đủ nhất trong nhà
    làm mẫu, áp cho mặt bằng có nét mũi bậc cùng bề rộng vế (nhà ở riêng lẻ thường một mẫu thang). Sân thượng, mái:
    thang vẽ ở đó là thang đi xuống, không tính thêm."""
    from ..drawing.encoding import normalize
    full = [detect_stairs(d) for d in subs]
    ref = max((s for st in full for s in st), key=lambda s: s.steps or 0, default=None)
    out, warnings = [], []
    for d, name, own in zip(subs, names, full):
        if re.search(r"san thuong|\bmai\b", normalize(name)):
            out.append([])
            continue
        part = own or detect_stairs(d, 3)
        if ref and any(abs((s.flight_width_mm or 0) - ref.flight_width_mm) < 150 for s in part) and (
                not own or max(s.steps or 0 for s in own) < ref.steps):
            out.append([ref.model_copy(update={"id": "T1"})])
            warnings.append(f"{name}: thang vẽ dở (đường cắt), lấy theo thang đủ nhất trong nhà: {ref.steps} bậc, "
                            f"vế {ref.flight_width_mm:.0f} mm, bậc {ref.tread_mm:.0f} mm; kiểm tra.")
        else:
            out.append(own)
    return out, warnings


def stair_works(plan: str, stairs: list[Stair], height_mm: float, params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    works, warnings = [], []
    t = params.stair_slab_thickness_mm
    for s in (s for s in stairs if s.keep):
        missing = [label for v, label in ((s.steps, "số bậc"), (s.flight_width_mm, "bề rộng vế"),
                                          (s.tread_mm, "bề rộng bậc"), (t, "dày bản thang")) if v is None]
        label = f"thang {s.id}"
        dimensions = [dict(label=f"{s.id}: hình học thang", count=1,
                           length_m=s.steps*s.tread_mm/1000 if s.steps is not None and s.tread_mm is not None else None,
                           width_m=s.flight_width_mm/1000 if s.flight_width_mm is not None else None,
                           height_m=height_mm/1000 if height_mm is not None else None,
                           thickness_m=t/1000 if t is not None else None,
                           source=f"{plan}: thang {s.id} ({s.source}); cao tầng và dày bản từ thông số",
                           note=f"Dài là tổng chạy ngang; {s.steps if s.steps is not None else '?'} bậc; chiếu nghỉ {s.landing_area_m2:g} m²")]
        if s.beam_length_mm:
            dimensions.append(dict(label=f"{s.id}: dầm thang", length_m=s.beam_length_mm/1000,
                width_m=s.beam_width_mm/1000 if s.beam_width_mm is not None else None,
                height_m=s.beam_depth_mm/1000 if s.beam_depth_mm is not None else None, source="Thông số dầm thang"))
        src = "auto" if s.source == "auto" else "manual"   # trạng thái: auto -> B (suy luận), manual -> C
        if s.kind != "ban":
            works.append(_work("CAU_THANG", None, plan=plan, dimensions=dimensions, element=label, basis="not_supported",
                               missing=[f"Not supported: thang {'cốn' if s.kind == 'con' else 'xoắn'} chưa có quy ước đo bóc"]))
            continue
        if s.beam_length_mm and (s.beam_width_mm is None or s.beam_depth_mm is None):
            missing.append("tiết diện dầm thang")
        if missing:
            works.append(_work("CAU_THANG", None, plan=plan, dimensions=dimensions, element=label, missing=missing))
            works.append(_work("COP_PHA", None, plan=plan, dimensions=dimensions, element=f"cốp pha {label}", formwork_of="CAU_THANG", missing=missing))
            continue
        H, n, w, b, tt = height_mm / 1000, s.steps, s.flight_width_mm / 1000, s.tread_mm / 1000, t / 1000
        riser = H / n
        if riser > RISER_MAX_M:
            warnings.append(f"{plan}, {label}: cao bậc {riser * 1000:.0f} mm (tầng {height_mm:.0f} / {n} bậc) quá lớn: "
                            "số bậc có thể thiếu (nhận sót vế), kiểm tra lại số bậc.")
        slope = math.hypot(n * b, H)
        slab = w * slope * tt
        steps = n * b * riser / 2 * w
        landing = s.landing_area_m2 * tt
        bl = s.beam_length_mm / 1000
        bb, bd = (s.beam_width_mm or 0) / 1000, (s.beam_depth_mm or 0) / 1000
        beam_txt = f" + dầm thang {_fmt(bl)} × {_fmt(bb)} × {_fmt(bd)}" if bl else ""
        works.append(_work("CAU_THANG", slab + steps + landing + bl * bb * bd, plan=plan, dimensions=dimensions, element=label, source=src,
                           formula=f"bản {_fmt(w)} × {_fmt(slope)} × {_fmt(tt)} + bậc {n} × {_fmt(b)} × {_fmt(riser)} / 2 × {_fmt(w)}"
                                   f" + chiếu nghỉ {_fmt(s.landing_area_m2)} × {_fmt(tt)}" + beam_txt))
        works.append(_work("COP_PHA", w * slope + s.landing_area_m2 + n * riser * w + (2 * bd + bb) * bl, plan=plan, dimensions=dimensions, source=src,
                           element=f"cốp pha {label}", formwork_of="CAU_THANG",
                           formula=f"{_fmt(w)} × {_fmt(slope)} + {_fmt(s.landing_area_m2)} + {n} × {_fmt(riser)} × {_fmt(w)}"
                                   + (f" + (2 × {_fmt(bd)} + {_fmt(bb)}) × {_fmt(bl)}" if bl else "")))
    if works:
        warnings.append(f"{plan}: công thức cầu thang là cách bóc thông dụng, Quy ước B3 chưa có; cần giảng viên duyệt.")
    return works, warnings
