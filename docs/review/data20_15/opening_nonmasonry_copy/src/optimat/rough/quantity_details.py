"""Tạo diễn giải từ lượng producer đã tính; không tính lại engine hoặc sửa quantity legacy."""
from decimal import Decimal

from .models import (FoundationItem, FootingTier, QuantityDetailRow, WorkItem, WorkQuantityDetail,
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
    """Nhận chính q trước _work round3, không phục hồi từ lượng đã làm tròn."""
    source = f"{f.source or 'Thông số móng người dùng nhập'}; FoundationItem {f.name}: count; lớp đáy; lean_thickness_mm"
    missing = [] if raw_quantity is not None else ["kích thước lớp đáy hoặc dày lót móng"]
    raw = None if raw_quantity is None else Decimal(_quantity_decimal_text(raw_quantity))
    negative = raw is not None and raw < 0
    if negative:
        missing.append("lượng thô âm; legacy đã chặn về 0, chưa có diễn giải đóng góp hợp lệ")
    return QuantityDetailRow(row_id=row_id, label=f"lót {f.name}", group="Móng", unit="m³", method="box",
        role="reference" if negative else "contribution", sign=-1 if negative else 1,
        raw_quantity=None if raw is None else _quantity_decimal_text(raw.copy_abs()),
        dimensions={"label": f"lót {f.name}", "source": source, "count": f.count, "repetitions": 1,
                    "length_m": base.length_mm / 1000 if base else None,
                    "width_m": base.width_mm / 1000 if base else None,
                    "height_m": f.lean_thickness_mm / 1000 if f.lean_thickness_mm is not None else None},
        expression="count × dài đáy × rộng đáy × dày lót; mm³ → m³",
        sources=[source], missing=missing)


def finalize_quantity_details(works: list[WorkItem]) -> list[WorkItem]:
    """Kiểm lại từ dump sau net/status/scope; không dùng model_copy để bỏ qua validator."""
    result = []
    for work in works:
        if work.quantity_detail is None:
            result.append(work)
            continue
        detail = WorkQuantityDetail.model_validate(work.quantity_detail.model_dump())
        legacy = None if work.quantity is None else _quantity_decimal_text(work.quantity)
        same_quantity = ((legacy is None and detail.legacy_quantity is None) or
                         (legacy is not None and detail.legacy_quantity is not None
                          and Decimal(legacy) == Decimal(detail.legacy_quantity)))
        if work.unit != detail.unit or not same_quantity:
            raise ValueError(f"{work.element or work.name}: lượng/đơn vị đã đổi sau capture detail; "
                             "cần producer dựng lại diễn giải net, không dùng gross hoặc tự bù lượng.")
        final = summarize(detail.rows, work.unit, work.quantity,
                          scope_complete=detail.scope_complete and not work.missing and work.status != "D",
                          detail_level=detail.detail_level)
        result.append(WorkItem.model_validate({**work.model_dump(), "quantity_detail": final.model_dump()}))
    return result


def area_quantity_row(row_id, label, raw_quantity, unit, sources, *, dimensions=None,
                      sign=1, role="contribution", method="area", missing=(), expression=""):
    """Lượng do emitter cung cấp; dimensions chỉ để diễn giải, không dùng tính ngược."""
    raw = None if raw_quantity is None else Decimal(_quantity_decimal_text(raw_quantity))
    reasons = list(missing)
    if raw is None and not reasons:
        reasons.append("chưa đủ đầu vào cho lượng diện tích/lớp")
    if raw is not None and raw < 0:
        role, sign = "reference", -sign
        reasons.append("giá trị thô âm: giữ tham khảo, không giả đóng góp hợp lệ từ clamp legacy")
    return QuantityDetailRow(row_id=row_id, label=label, unit=unit, role=role, sign=sign, method=method,
        raw_quantity=None if raw is None else _quantity_decimal_text(raw.copy_abs()),
        dimensions=dimensions, sources=sources, missing=reasons, expression=expression)


def area_detail(work: WorkItem, raw_quantity, *, rows=None, scope_complete=True) -> WorkItem:
    """Raw aggregate thật giữ reference khi emitter có các dòng thành phần riêng."""
    if rows is None:
        dimension = work.dimensions[0] if len(work.dimensions) == 1 else None
        source = dimension.source if dimension else f"{work.plan}: area_works/{work.code} và thông số lớp nền"
        rows = [area_quantity_row("area:quantity", dimension.label if dimension else work.element or work.name, raw_quantity, work.unit,
            [source], dimensions=dimension, missing=work.missing, expression=work.formula)]
    else:
        rows = [*rows, area_quantity_row("producer:raw", "Lượng producer đưa vào _work trước round3",
            raw_quantity, work.unit, [f"{work.plan}: area_works/{work.code}; giá trị tính thực tế trước round3"],
            role="reference", method="source_quantity", missing=work.missing,
            expression="Giá trị float aggregate của producer; không cộng lần nữa vào các thành phần")]
    detail = summarize(rows, work.unit, work.quantity,
        scope_complete=scope_complete and not work.missing and work.status != "D" and not any(r.missing for r in rows),
        detail_level="components" if any(r.role == "contribution" for r in rows) else "unavailable")
    return WorkItem.model_validate({**work.model_dump(), "quantity_detail": detail.model_dump()})
