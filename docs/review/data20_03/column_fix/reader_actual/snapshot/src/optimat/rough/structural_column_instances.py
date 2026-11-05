"""Cột vật lý theo vị trí và đoạn cao độ; không đồng nhất mã loại với instance."""
from decimal import Decimal
import math
import hashlib

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import QuantityDetailRow
from .quantity_details import summarize
from .walls import _work


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
    sheet: str = ""
    layers: list[str] = Field(default_factory=list)
    handles: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    matched_plan: str | None = None
    matched_column_id: str | None = None
    mapping_evidence: str | None = None

    @model_validator(mode="after")
    def _valid(self):
        if not self.instance_id.strip() or not self.code.strip():
            raise ValueError("Cần định danh instance và mã cột.")
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
        missing = [name for name in ("b_mm", "h_mm", "z_from_mm", "z_to_mm") if getattr(s, name) is None]
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
    """Đọc thuộc tính có đơn vị rõ; nhãn mặt bằng thiếu liên kết được giữ thành pending.

    shortcut: chưa suy nối mặt cắt/cao độ từ khoảng cách chữ; chỉ mở khi có
    chứng cứ trục và phạm vi hình, tránh lấy một tiết diện cho mọi mã giống nhau.
    """
    from .structural import element_of
    from ..drawing.registry import floors_of

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
