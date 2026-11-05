"""Thang bản theo từng vế/chiếu có nguồn; bậc xây tách khỏi bê tông.
Dữ liệu legacy/nhận nét chỉ là ứng viên, không thay geometry và scope từng thang.
"""
from __future__ import annotations

import math
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from .materials import _fmt
from .models import ProjectParams, WorkItem, QuantityDetailRow
from .quantity_details import summarize
from .walls import _work


class StairFlight(BaseModel):
    model_config=ConfigDict(extra="forbid")
    id: str
    run_mm: float | None = None
    rise_mm: float | None = None
    width_mm: float | None = None
    waist_thickness_mm: float | None = None
    thickness_basis: Literal["normal", "vertical", "unknown"] = "unknown"
    step_count: int | None = None
    tread_mm: float | None = None
    riser_mm: float | None = None
    field_sources: dict[str,str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _measurements(self):
        if not self.id.strip():raise ValueError("ID vế không được trống.")
        for name in ("run_mm","rise_mm","width_mm","waist_thickness_mm","step_count","tread_mm","riser_mm"):
            v=getattr(self,name)
            if v is not None and (not math.isfinite(v) or v<=0):
                raise ValueError("Số đo vế thang phải hữu hạn và dương.")
        return self


class StairLanding(BaseModel):
    model_config=ConfigDict(extra="forbid")
    id: str
    area_m2: float | None = None
    thickness_mm: float | None = None
    ownership: Literal["stair","floor","beam","unknown"] = "unknown"
    field_sources: dict[str,str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _measurements(self):
        if not self.id.strip():raise ValueError("ID chiếu không được trống.")
        if self.area_m2 is not None and (not math.isfinite(self.area_m2) or self.area_m2<0):
            raise ValueError("Diện tích chiếu phải hữu hạn, không âm.")
        if self.thickness_mm is not None and (not math.isfinite(self.thickness_mm) or self.thickness_mm<=0):
            raise ValueError("Dày chiếu phải hữu hạn, dương.")
        return self


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
    steps_material: Literal["concrete","masonry","unknown"] = "unknown"
    steps_material_source: str | None = None
    waist_thickness_mm: float | None = None
    waist_thickness_basis: Literal["normal","vertical","unknown"] = "unknown"
    waist_thickness_source: str | None = None
    scope_source: str | None = None
    formwork_scope_source: str | None = None
    from_floor: str | None = None
    to_floor: str | None = None
    flights: list[StairFlight] | None = None
    landings: list[StairLanding] | None = None

    @model_validator(mode="after")
    def _components(self):
        if not self.id.strip():raise ValueError("ID thang không được trống.")
        if (self.from_floor is None)!=(self.to_floor is None):
            raise ValueError("Phạm vi thang cần cả tầng đầu và tầng cuối.")
        if self.waist_thickness_mm is not None and (not math.isfinite(self.waist_thickness_mm) or self.waist_thickness_mm<=0):
            raise ValueError("Dày bản thang phải hữu hạn và dương.")
        for components in (self.flights,self.landings):
            if components is not None and len({x.id for x in components})!=len(components):
                raise ValueError("ID vế hoặc chiếu bị trùng trong thang.")
        ids=[x.id for group in (self.flights,self.landings) for x in group or []]
        if len(ids)!=len(set(ids)):
            raise ValueError("Vế và chiếu cần ID riêng trong cùng thang.")
        return self


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
            out.append(part)
            warnings.append(f"{name}: thang vẽ dở; mẫu cùng rộng vế có {ref.steps} bậc nhưng chưa xác nhận cùng phạm vi, "
                            "không sao chép số bậc, cấu tạo hoặc cao độ sang thang này.")
        else:
            out.append(own)
    return out, warnings


def _component_row(row_id, label, raw, unit, sources, missing=(), dimensions=None, role="contribution"):
    return QuantityDetailRow(row_id=row_id,label=label,raw_quantity=None if raw is None else str(raw),
        unit=unit,method="box" if unit=="m³" else "area",sources=sources,missing=list(missing),dimensions=dimensions,role=role)


def _component_work(code, rows, plan, stair, missing, **kwargs):
    reasons=list(dict.fromkeys([*missing,*[reason for r in rows if r.role=="contribution" for reason in r.missing]]))
    scope=bool(stair.scope_source and stair.scope_source.strip())
    if not scope:
        reasons.append("chưa xác nhận phạm vi từng thang/vế/chiếu")
    if not stair.from_floor or not stair.to_floor:
        reasons.append("chưa xác nhận tầng đầu/cuối của thang")
    detail=summarize(rows,"m³" if code=="CAU_THANG" else "m²",None,scope_complete=scope and not reasons)
    known=float(detail.known_part_raw) if detail.known_part_raw is not None else None
    work=_work(code,known,plan=plan,element=f"thang {stair.id}",source="auto" if stair.source=="auto" else "manual",
        basis="stair_components",missing=list(dict.fromkeys(reasons)),
        status="D" if reasons or known is None else "C",
        evidence=list(dict.fromkeys([v for r in rows for v in r.sources])),
        dimensions=[r.dimensions for r in rows if r.dimensions is not None],**kwargs)
    work.quantity_detail=summarize(rows,work.unit,work.quantity,scope_complete=scope and not reasons)
    return work


def stair_works(plan: str, stairs: list[Stair], height_mm: float | None, params: ProjectParams) -> tuple[list[WorkItem], list[str]]:
    """Tính theo component có nguồn; H tầng và ProjectParams không thay hình học từng vế."""
    works,warnings=[],[]
    for s in (s for s in stairs if s.keep):
        source=s.scope_source or f"{plan}: Stair.{s.id}; chưa có nguồn phạm vi"
        if s.kind!="ban":
            works.append(_work("CAU_THANG",None,plan=plan,element=f"thang {s.id}",basis="not_supported",
                missing=["thang cốn/xoắn ngoài phạm vi công thức thang bản"]))
            continue
        concrete,forms=[],[]
        missing=[]
        material_known=s.steps_material!="unknown" and bool(s.steps_material_source and s.steps_material_source.strip())
        if not material_known:
            missing.append("cấu tạo và nguồn vật liệu bậc chưa xác định")
        if not s.flights:
            reason="chưa có run/rise/width và nguồn từng vế; không lấy tổng cao tầng hoặc tổng số bậc thay thế"
            concrete.append(_component_row("flights:unknown","Bản nghiêng chưa gán vế",None,"m³",[source],[reason]))
            forms.append(_component_row("flights:unknown","Đáy bản nghiêng chưa gán vế",None,"m²",[source],[reason]))
        for flight in s.flights or []:
            sources=[source,*[v for v in flight.field_sources.values() if v.strip()]]
            errors=[f"{flight.id}: {key} hoặc nguồn" for key in ("run_mm","rise_mm","width_mm")
                if getattr(flight,key) is None or not flight.field_sources.get(key,"").strip()]
            t=flight.waist_thickness_mm if flight.waist_thickness_mm is not None else s.waist_thickness_mm
            basis=flight.thickness_basis if flight.waist_thickness_mm is not None else s.waist_thickness_basis
            t_source=flight.field_sources.get("waist_thickness_mm") if flight.waist_thickness_mm is not None else s.waist_thickness_source
            if t is None or basis!="normal" or not (t_source and t_source.strip()):
                errors.append(f"{flight.id}: dày bản vuông góc và nguồn riêng")
            if t_source and t_source.strip():sources.append(t_source)
            geometry_ok=all(getattr(flight,k) is not None and flight.field_sources.get(k,"").strip() for k in ("run_mm","rise_mm","width_mm"))
            slope=math.hypot(flight.run_mm,flight.rise_mm)/1000 if geometry_ok else None
            area=slope*flight.width_mm/1000 if slope is not None else None
            dims=dict(label=f"{s.id}/{flight.id}: bản nghiêng",count=1,
                length_m=flight.run_mm/1000 if flight.run_mm is not None else None,
                slope_length_m=slope,width_m=flight.width_mm/1000 if flight.width_mm is not None else None,
                height_m=flight.rise_mm/1000 if flight.rise_mm is not None else None,
                thickness_m=t/1000 if t is not None else None,source="; ".join(sources),
                note="Dài ngang/rise riêng vế; dày phải vuông góc; không dùng chiều dài cắt thép")
            concrete.append(_component_row(f"{flight.id}:waist",f"Bản nghiêng {flight.id}",area*t/1000 if area is not None and not errors else None,
                "m³",sources,errors,dims))
            form_errors=[] if geometry_ok else [f"{flight.id}: hình học và nguồn đáy bản nghiêng"]
            forms.append(_component_row(f"{flight.id}:soffit",f"Đáy bản nghiêng {flight.id}",area,"m²",sources,form_errors,dims))
            if material_known and s.steps_material=="masonry":
                concrete.append(_component_row(f"{flight.id}:steps","Bậc xây gạch không thuộc bê tông",0,"m³",[s.steps_material_source],role="reference"))
                forms.append(_component_row(f"{flight.id}:risers","Không đổ BT thành bậc xây",0,"m²",[s.steps_material_source],role="reference"))
            elif material_known and s.steps_material=="concrete":
                step_errors=[f"{flight.id}: {key} hoặc nguồn bậc bê tông" for key in ("step_count","tread_mm","riser_mm","width_mm")
                    if getattr(flight,key) is None or not flight.field_sources.get(key,"").strip()]
                q=flight.step_count*flight.tread_mm*flight.riser_mm*flight.width_mm/2e9 if not step_errors else None
                a=flight.step_count*flight.riser_mm*flight.width_mm/1e6 if not step_errors else None
                step_dims=dict(label=f"{s.id}/{flight.id}: bậc BT",count=flight.step_count,
                    length_m=flight.tread_mm/1000 if flight.tread_mm is not None else None,
                    width_m=flight.width_mm/1000 if flight.width_mm is not None else None,
                    height_m=flight.riser_mm/1000 if flight.riser_mm is not None else None,
                    source="; ".join([*sources,s.steps_material_source]),note="BT bậc tam giác có hệ số1/2; CP chỉ tính mặt đứng bậc")
                concrete.append(_component_row(f"{flight.id}:steps",f"Bậc bê tông {flight.id}",q,"m³",[*sources,s.steps_material_source],step_errors,step_dims))
                forms.append(_component_row(f"{flight.id}:risers",f"Thành bậc bê tông {flight.id}",a,"m²",[*sources,s.steps_material_source],step_errors,step_dims))
            else:
                concrete.append(_component_row(f"{flight.id}:steps","Bậc chưa rõ cấu tạo",None,"m³",sources,["vật liệu và nguồn cấu tạo bậc"]))
                forms.append(_component_row(f"{flight.id}:risers","Thành bậc chưa rõ cấu tạo",None,"m²",sources,["vật liệu và nguồn cấu tạo bậc"]))
        if s.landings is None:
            reason="chưa gán các chiếu và quyền sở hữu; dữ liệu rỗng không phải diện tích0"
            concrete.append(_component_row("landings:unknown","Chiếu chưa gán",None,"m³",[source],[reason]))
            forms.append(_component_row("landings:unknown","Đáy chiếu chưa gán",None,"m²",[source],[reason]))
        for landing in s.landings or []:
            sources=[source,*[v for v in landing.field_sources.values() if v.strip()]]
            owner_source=landing.field_sources.get("ownership","").strip()
            errors=[]
            if landing.ownership=="unknown" or not owner_source:
                errors.append(f"{landing.id}: quyền sở hữu chiếu/giao chưa có nguồn")
            excluded=landing.ownership in ("floor","beam") and bool(owner_source)
            for key in ("area_m2","thickness_mm"):
                if getattr(landing,key) is None or not landing.field_sources.get(key,"").strip():errors.append(f"{landing.id}: {key} hoặc nguồn")
            raw=landing.area_m2*landing.thickness_mm/1000 if not errors else None
            role="reference" if excluded else "contribution"
            dims=dict(label=f"{s.id}/{landing.id}",count=1,area_m2=landing.area_m2,
                thickness_m=landing.thickness_mm/1000 if landing.thickness_mm is not None else None,
                source="; ".join(sources),note=f"Chiếu thuộc {landing.ownership}; không gán dày chiếu sang vế")
            concrete.append(_component_row(f"{landing.id}:landing",f"Chiếu {landing.id}",raw,"m³",sources,errors,dims,role))
            forms.append(_component_row(f"{landing.id}:soffit",f"Đáy chiếu {landing.id}",landing.area_m2 if not errors else None,"m²",sources,errors,dims,role))
        if s.beam_length_mm:
            reason="dầm thang chưa có nguồn, phạm vi và khoản giao riêng; không cộng từ kích thước legacy"
            concrete.append(_component_row("beam:unknown","Dầm thang chưa gán",None,"m³",[source],[reason]))
            forms.append(_component_row("beam:unknown","Mặt/giao dầm thang chưa gán",None,"m²",[source],[reason]))
        if not (s.formwork_scope_source and s.formwork_scope_source.strip()):
            forms.append(_component_row("surfaces:unknown","Cạnh/gối/giao cốp pha chưa kiểm",None,"m²",[source],
                ["chưa kiểm mặt cạnh, gối và khoản giao cốp pha theo từng cấu kiện"]))
        else:
            forms.append(_component_row("surfaces:scope","Nguồn xác nhận phạm vi CP chỉ gồm các mặt đã liệt kê",0,"m²",
                [s.formwork_scope_source],role="reference"))
        works.append(_component_work("CAU_THANG",concrete,plan,s,missing,formula="Σ rộng vế × hypot(run,rise) × dày vuông góc + bậc BT có nguồn + chiếu thuộc thang"))
        works.append(_component_work("COP_PHA",forms,plan,s,missing,formwork_of="CAU_THANG",formula="Σ đáy bản/chiếu và thành bậc đổBT có nguồn; cạnh/gối/giao còn thiếu"))
        if material_known and s.steps_material=="masonry":
            works.append(_work("XAY",None,plan=plan,element=f"bậc xây thang {s.id}",basis="stair_steps_masonry",
                evidence=[s.steps_material_source],missing=["hình học bậc xây từng vế và quy cách gạch/vữa; chưa bóc riêng"],
                formula="Bậc xây gạch tách khỏi bê tông; chưa có lượng xây"))
        warnings.append(f"{plan}, thang {s.id}: chỉ tính component có nguồn; không dùng H tầng, mặc định BT bậc hoặc DAI thép thay hình học.")
    return works,warnings
