"""Tổng raw/coverage từ finalized works; không chạy lại engine hoặc sửa tổng legacy."""
from decimal import Decimal, localcontext
import hashlib
import json

from .models import (ProjectParams, QuantityCoverage, QuantityGroupKey, QuantityGroupingContext,
    QuantityMissingRef, QuantityRawGroup, QuantitySummary, WorkItem, _quantity_decimal_text)


def grouping_context(params: ProjectParams) -> QuantityGroupingContext:
    """Nguồn là tham số đã khai báo, không phải thiết kế được xác minh độc lập."""
    return QuantityGroupingContext(**{key: getattr(params, key) for key in QuantityGroupingContext.model_fields})


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sum(values):
    numbers = [Decimal(v) for v in values if v is not None]
    if not numbers:
        return None
    with localcontext() as ctx:
        ctx.prec = max(28, max(n.adjusted() for n in numbers) - min(n.as_tuple().exponent for n in numbers)
                       + len(str(len(numbers) + 1)) + 2)
        return _quantity_decimal_text(sum(numbers, Decimal(0)))


def _group_key(work, work_key, context):
    spec, reasons = {}, []
    def require(name, value):
        spec[name] = value
        if value is None or not str(value).strip():
            reasons.append(f"chưa có {name} để gộp cùng quy cách")
    if not work.stage:
        reasons.append("chưa có hạng mục công tác")
    if not work.source.strip():
        reasons.append("chưa có nguồn công tác")
    concrete = {"COT", "DAM", "SAN", "CAU_THANG", "GIANG_TUONG", "SE_NO", "MAI", "MONG", "LANH_TO", "BE_TONG_LOT"}
    if work.code in concrete:
        grade_field = "lean_concrete_grade" if work.code == "BE_TONG_LOT" else "concrete_grade"
        require(grade_field, getattr(context, grade_field))
        require("concrete_supply", context.concrete_supply)
    elif work.code == "COP_PHA":
        require("formwork_type", context.formwork_type)
        require("formwork_of", work.formwork_of)
    elif work.code == "XAY":
        require("masonry_mortar_grade", context.masonry_mortar_grade)
        require("wall_system_id", work.wall_system_id)
    elif work.code == "TRAT":
        require("plaster_mortar_grade", context.plaster_mortar_grade)
        require("thickness_variant", work.variant)
        require("wall_system_id", work.wall_system_id)
    elif work.code == "CAN_NEN":
        require("screed_mortar_grade", context.screed_mortar_grade)
        require("thickness_variant", work.variant)
    elif work.code == "CHONG_THAM":
        require("waterproof_material_variant", work.variant)
    elif work.code in {"DAO_DAT", "DAP_DAT"}:
        reasons.append("chưa có phân loại đất/biện pháp có cấu trúc để gộp")
    elif work.code == "COT_THEP":
        reasons.append("chưa có quy cách/cấp thép có cấu trúc để gộp; không đoán từ ký hiệu")
    elif work.code == "NEN_DEM_CAT":
        reasons.append("chưa có quy cách lớp đệm cát có cấu trúc để gộp")
    else:
        reasons.append("chưa có quy tắc tương thích của công tác")
    return QuantityGroupKey(stage=work.stage, code=work.code, variant=work.variant, unit=work.unit,
        source=work.source, basis=work.basis, formwork_of=work.formwork_of, steel_element=work.steel_element,
        wall_system_id=work.wall_system_id, specification=spec, isolated_work_key=work_key if reasons else None), reasons


def _quantity_complete(work):
    d = work.quantity_detail
    return d is not None and d.detail_level != "unavailable" and d.complete and d.total_raw is not None


def _coverage(works, pending_count):
    values = dict(work_count=len(works), components=0, aggregate=0, unavailable=0, no_detail=0,
        quantity_complete_works=0, quantity_incomplete_works=0, contribution_rows=0,
        known_contribution_rows=0, unknown_contribution_rows=0, reference_rows=0,
        compatibility_pending_works=pending_count, legacy_D_works=0, legacy_missing_works=0)
    for work in works:
        d = work.quantity_detail
        values["no_detail" if d is None else d.detail_level] += 1
        values["quantity_complete_works" if _quantity_complete(work) else "quantity_incomplete_works"] += 1
        values["legacy_D_works"] += work.status == "D"
        values["legacy_missing_works"] += bool(work.missing)
        for row in d.rows if d else []:
            if row.role == "reference":
                values["reference_rows"] += 1
            else:
                values["contribution_rows"] += 1
                values["unknown_contribution_rows" if row.raw_quantity is None else "known_contribution_rows"] += 1
    return QuantityCoverage(**values, complete_components=bool(works) and values["components"] == len(works)
                           and values["quantity_complete_works"] == len(works))


def _missing(work, key):
    d = work.quantity_detail
    if d is None:
        return [QuantityMissingRef(work_key=key, reasons=["chưa có diễn giải raw"]) ]
    refs = [QuantityMissingRef(work_key=key, row_id=r.row_id, reasons=r.missing or ["chưa có lượng"])
            for r in d.rows if r.role == "contribution" and (r.raw_quantity is None or r.missing)]
    if not _quantity_complete(work):
        refs.append(QuantityMissingRef(work_key=key, reasons=work.missing or ["phạm vi detail chưa đủ"]))
    return refs


def build_quantity_summary(works: list[WorkItem], context: QuantityGroupingContext) -> QuantitySummary:
    # Dump/constructor ngăn mutable/model_copy bỏ qua invariant của detail và parent.
    finalized = [WorkItem.model_validate(w.model_dump()) for w in works]
    context = QuantityGroupingContext.model_validate(context.model_dump())
    snapshot = hashlib.sha256(_json(dict(schema_version=1, works=[w.model_dump(mode="json") for w in finalized],
                                        context=context.model_dump(mode="json"))).encode("utf-8")).hexdigest()
    partitions = {}
    all_pending = 0
    for index, work in enumerate(finalized):
        work_key = f"w:{index}"
        key, reasons = _group_key(work, work_key, context)
        all_pending += bool(reasons)
        partition = partitions.setdefault(_json(key.model_dump()), dict(key=key, reasons=reasons, members=[]))
        partition["members"].append((work_key, work))
    groups = []
    for index, partition in enumerate(partitions.values()):
        members = partition["members"]
        items = [w for _, w in members]
        known = _sum([w.quantity_detail.known_part_raw for w in items if w.quantity_detail is not None])
        complete = all(_quantity_complete(w) for w in items)
        methods = sorted({r.method for w in items if w.quantity_detail for r in w.quantity_detail.rows if r.role == "contribution"})
        groups.append(QuantityRawGroup(group_id=f"g:{index}", key=partition["key"],
            member_work_keys=[k for k, _ in members], compatibility="isolated_unknown" if partition["reasons"] else "resolved",
            compatibility_reasons=partition["reasons"], calculation_methods=methods,
            known_part_raw=known, total_raw=_sum([w.quantity_detail.total_raw for w in items]) if complete else None,
            complete=complete, coverage=_coverage(items, len(items) if partition["reasons"] else 0),
            missing_work_refs=[ref for k, w in members for ref in _missing(w, k)]))
    return QuantitySummary(quantity_snapshot_hash=snapshot, context=context, groups=groups,
                           coverage=_coverage(finalized, all_pending))


def validate_quantity_summary(works: list[WorkItem], summary: QuantitySummary) -> None:
    """So expected với payload; không ghi đè tổng/count/hash giả hoặc stale để làm hợp lệ."""
    expected = build_quantity_summary(works, summary.context)
    if expected.model_dump() != summary.model_dump():
        raise ValueError("quantity_summary không khớp works/context của snapshot: hash, membership, key, raw total hoặc coverage đã đổi.")
