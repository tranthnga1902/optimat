"""Bản nháp G8, CHƯA nối vào source/API; chờ 01 duyệt DTO và hunk producer."""
from decimal import Decimal, InvalidOperation, localcontext
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from optimat.rough.models import WorkDimensions


def decimal_text(value) -> str:
    """Giữ giá trị producer đưa vào, không làm tròn hoặc sửa floating artifact."""
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Lượng chi tiết phải là số thập phân hợp lệ.") from exc
    if not number.is_finite():
        raise ValueError("Lượng chi tiết phải là số hữu hạn.")
    return format(number, "f")


def _amounts(rows, legacy_quantity):
    known = [r for r in rows if r.role == "contribution" and r.raw_quantity is not None]
    numbers = [Decimal(r.raw_quantity) for r in known]
    legacy = None if legacy_quantity is None else Decimal(decimal_text(legacy_quantity))
    values = numbers + ([] if legacy is None else [legacy])
    with localcontext() as ctx:
        # Cộng/trừ chính xác theo số chữ số đã nhận, không làm tròn trung gian về context mặc định.
        ctx.prec = max(28, max((n.adjusted() for n in values), default=0)
                       - min((n.as_tuple().exponent for n in values), default=0) + len(str(len(values) + 1)) + 2)
        total = sum((r.sign * n for r, n in zip(known, numbers)), Decimal(0)) if known else None
        delta = total - legacy if total is not None and legacy is not None else None
    return total, delta


class DetailConversion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_unit: str
    to_unit: str
    factor: str
    source: str

    @field_validator("from_unit", "to_unit", "source")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Đơn vị quy đổi và nguồn không được trống.")
        return value

    @field_validator("factor")
    @classmethod
    def _factor(cls, value):
        result = decimal_text(value)
        if Decimal(result) <= 0:
            raise ValueError("Hệ số quy đổi phải dương và hữu hạn.")
        return result


class DetailFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    value: str
    unit: str                         # "1" nếu không thứ nguyên
    meaning: str
    source: str

    @field_validator("name", "unit", "meaning", "source")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Hệ số phụ cần tên, đơn vị, ý nghĩa và nguồn.")
        return value

    @field_validator("value")
    @classmethod
    def _value(cls, value):
        result = decimal_text(value)
        if Decimal(result) < 0:
            raise ValueError("Hệ số phụ không âm; khoản trừ dùng sign riêng.")
        return result


class QuantityDetailRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    row_id: str                       # chỉ ổn định trong đúng một result snapshot
    label: str
    group: str = ""
    role: Literal["contribution", "reference"] = "contribution"
    sign: Literal[1, -1] = 1
    unit: str
    raw_quantity: str | None = None   # trị tuyệt đối, ĐÃ gồm count/lặp/hệ số/quy đổi nếu áp dụng
    method: Literal["box", "area", "perimeter", "count", "prismoid", "union", "steel", "ratio", "source_quantity"]
    # Không thực thi/parse expression; kích thước và nguồn để hiển thị, không cộng lại.
    dimensions: WorkDimensions | None = None
    conversion: DetailConversion | None = None
    factors: list[DetailFactor] = Field(default_factory=list)
    expression: str = ""
    sources: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)

    @field_validator("row_id", "label", "unit")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Khóa dòng, diễn giải và đơn vị không được trống.")
        return value

    @field_validator("raw_quantity")
    @classmethod
    def _quantity(cls, value):
        if value is None:
            return None
        result = decimal_text(value)
        if Decimal(result) < 0:
            raise ValueError("raw_quantity là trị tuyệt đối; khoản trừ dùng sign=-1.")
        return result

    @model_validator(mode="after")
    def _source_and_missing(self):
        if not self.sources or any(not s.strip() for s in self.sources):
            raise ValueError("Mỗi dòng chi tiết cần nguồn.")
        if self.raw_quantity is None and not self.missing:
            raise ValueError("Lượng chưa biết phải có lý do thiếu, không thay bằng 0.")
        if self.conversion and self.conversion.to_unit != self.unit:
            raise ValueError("Quy đổi phải kết thúc ở đơn vị dòng đóng góp.")
        return self


class WorkQuantityDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit: str
    rows: list[QuantityDetailRow]
    detail_level: Literal["components", "aggregate", "unavailable"]
    known_part_raw: str | None
    total_raw: str | None             # chỉ có nếu toàn phạm vi đủ, không dùng known_part giả tổng đủ
    complete: bool
    scope_complete: bool             # producer xác định phạm vi, không suy từ số dòng có lượng
    legacy_quantity: str | None
    legacy_delta: str | None          # raw known part − số legacy, không tự sửa legacy

    @field_validator("known_part_raw", "total_raw", "legacy_quantity", "legacy_delta")
    @classmethod
    def _finite_decimal(cls, value):
        return None if value is None else decimal_text(value)

    @model_validator(mode="after")
    def _invariants(self):
        if not self.unit.strip() or len({r.row_id for r in self.rows}) != len(self.rows):
            raise ValueError("Đơn vị tổng không trống; row_id không trùng.")
        contributions = [r for r in self.rows if r.role == "contribution"]
        if any(r.unit != self.unit for r in contributions):
            raise ValueError("Không cộng đóng góp khác đơn vị công tác.")
        value, expected_delta = _amounts(self.rows, self.legacy_quantity)
        expected_complete = bool(contributions) and self.scope_complete and all(
            r.raw_quantity is not None and not r.missing for r in contributions)
        expected_total = value if expected_complete else None
        def matches(actual, expected):
            return actual is None if expected is None else actual is not None and Decimal(actual) == expected
        if (not matches(self.known_part_raw, value) or self.complete != expected_complete
                or not matches(self.total_raw, expected_total) or not matches(self.legacy_delta, expected_delta)):
            raise ValueError("Tổng detail/complete/delta không khớp signed contribution và phạm vi.")
        return self


def summarize(rows: list[QuantityDetailRow], unit: str, legacy_quantity, *,
              scope_complete: bool, detail_level="components") -> WorkQuantityDetail:
    if len({r.row_id for r in rows}) != len(rows):
        raise ValueError("row_id trùng trong cùng công tác.")
    contributions = [r for r in rows if r.role == "contribution"]
    if any(r.unit != unit for r in contributions):
        raise ValueError("Không cộng đóng góp khác đơn vị công tác.")
    value, delta = _amounts(rows, legacy_quantity)
    complete = bool(contributions) and scope_complete and all(r.raw_quantity is not None and not r.missing for r in contributions)
    legacy = None if legacy_quantity is None else Decimal(decimal_text(legacy_quantity))
    return WorkQuantityDetail(unit=unit, rows=rows, detail_level=detail_level,
        known_part_raw=None if value is None else decimal_text(value),
        total_raw=decimal_text(value) if complete else None, complete=complete, scope_complete=scope_complete,
        legacy_quantity=None if legacy is None else decimal_text(legacy),
        legacy_delta=decimal_text(delta) if delta is not None else None)


def lean_foundation_row(f, base, *, row_id: str, raw_quantity) -> QuantityDetailRow:
    """Hunk producer dự kiến: nhận CHÍNH q trước _work round3, không tính lại từ dimensions."""
    source = f"FoundationItem {f.name}: count; lớp đáy; lean_thickness_mm"
    missing = [] if raw_quantity is not None else ["kích thước lớp đáy hoặc dày lót móng"]
    return QuantityDetailRow(row_id=row_id, label=f"lót {f.name}", group="Móng", unit="m³", method="box",
        raw_quantity=None if raw_quantity is None else decimal_text(raw_quantity),
        dimensions={"label": f"lót {f.name}", "source": source, "count": f.count, "repetitions": 1,
                    "length_m": base.length_mm / 1000 if base else None,
                    "width_m": base.width_mm / 1000 if base else None,
                    "height_m": f.lean_thickness_mm / 1000 if f.lean_thickness_mm is not None else None},
        expression="count × dài đáy × rộng đáy × dày lót; mm³ → m³",
        sources=[source], missing=missing)
