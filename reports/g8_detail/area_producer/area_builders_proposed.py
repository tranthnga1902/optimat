"""P02 staging: chỉ các hàm mới; chưa nối vào helper đang HOLD cho API reload."""
from decimal import Decimal

from optimat.rough.models import QuantityDetailRow, WorkItem, _quantity_decimal_text
from optimat.rough.quantity_details import summarize


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
