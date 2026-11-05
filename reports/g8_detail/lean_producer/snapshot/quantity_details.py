"""Tạo diễn giải từ lượng producer đã tính; không tính lại engine hoặc sửa quantity legacy."""
from decimal import Decimal

from .models import (FoundationItem, FootingTier, QuantityDetailRow, WorkQuantityDetail,
                     _quantity_decimal_text, _quantity_detail_amounts)


def summarize(rows: list[QuantityDetailRow], unit: str, legacy_quantity, *,
              scope_complete: bool, detail_level="components") -> WorkQuantityDetail:
    if len({r.row_id for r in rows}) != len(rows):
        raise ValueError("row_id trùng trong cùng công tác.")
    contributions = [r for r in rows if r.role == "contribution"]
    if any(r.unit != unit for r in contributions):
        raise ValueError("Không cộng đóng góp khác đơn vị công tác.")
    value, delta = _quantity_detail_amounts(rows, legacy_quantity)
    complete = bool(contributions) and scope_complete and all(r.raw_quantity is not None and not r.missing for r in contributions)
    legacy = None if legacy_quantity is None else Decimal(_quantity_decimal_text(legacy_quantity))
    return WorkQuantityDetail(unit=unit, rows=rows, detail_level=detail_level,
        known_part_raw=None if value is None else _quantity_decimal_text(value),
        total_raw=_quantity_decimal_text(value) if complete else None, complete=complete, scope_complete=scope_complete,
        legacy_quantity=None if legacy is None else _quantity_decimal_text(legacy),
        legacy_delta=_quantity_decimal_text(delta) if delta is not None else None)


def lean_foundation_row(f: FoundationItem, base: FootingTier | None, *, row_id: str, raw_quantity) -> QuantityDetailRow:
    """Nhận chính q trước _work round3; chưa được gọi từ emitter trong gói DTO."""
    source = f"FoundationItem {f.name}: count; lớp đáy; lean_thickness_mm"
    missing = [] if raw_quantity is not None else ["kích thước lớp đáy hoặc dày lót móng"]
    return QuantityDetailRow(row_id=row_id, label=f"lót {f.name}", group="Móng", unit="m³", method="box",
        raw_quantity=None if raw_quantity is None else _quantity_decimal_text(raw_quantity),
        dimensions={"label": f"lót {f.name}", "source": source, "count": f.count, "repetitions": 1,
                    "length_m": base.length_mm / 1000 if base else None,
                    "width_m": base.width_mm / 1000 if base else None,
                    "height_m": f.lean_thickness_mm / 1000 if f.lean_thickness_mm is not None else None},
        expression="count × dài đáy × rộng đáy × dày lót; mm³ → m³",
        sources=[source], missing=missing)
