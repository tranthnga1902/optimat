"""Xuất BOQ phần thô ra Excel (S07-06): mọi dòng có công thức, nguồn (evidence) và lý do thiếu (missing_reason).

Sheet: Tổng hợp · Theo tầng · Theo cấu kiện · Cốt thép (dòng bảng thống kê) · Vật liệu · Theo nhóm · Theo loại · Cảnh báo · Phạm vi hỗ trợ.
"""
from __future__ import annotations

from io import BytesIO
from decimal import Decimal
import json

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .. import config
from .models import RAW_CLASSES, STAGES, STATUS_LABEL, STEEL_ELEMENTS, WORKS

SUPPORT_FILE = config.DATA_DIR / "rules" / "ho_tro_cau_kien.csv"
COMMON = "Chung (không theo tầng)"


def support_matrix() -> pd.DataFrame:
    return pd.read_csv(SUPPORT_FILE, dtype=str, keep_default_na=False)


def _component(w) -> str:
    """Cấu kiện của một công tác: cốp pha, cốt thép quy về cấu kiện bê tông của nó."""
    code = w.formwork_of if w.code == "COP_PHA" else w.steel_element if w.code == "COT_THEP" else w.code
    if code in STEEL_ELEMENTS:
        return WORKS[code][0].replace("Bê tông ", "").capitalize()
    return WORKS[code][0] if code in WORKS else "Chưa rõ cấu kiện"


def _status(s) -> str:
    return f"{s} ({STATUS_LABEL[s]})" if s in STATUS_LABEL else ""


def _row(w) -> list:
    return [w.plan or COMMON, _component(w), w.name, w.element or "", w.unit, w.quantity, _status(w.status),
            STAGES.get(w.stage or "", ""), w.basis or w.source, w.formula, " | ".join(w.inputs), " | ".join(w.evidence),
            "; ".join(w.missing)]


def _sheet(wb, title: str, header: list[str], rows: list[list]) -> None:
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append(r)
    ws.freeze_panes = "A2"
    for i, h in enumerate(header, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = max(10, min(60, len(h) + 4))


def _detail_number(raw):
    """Bản số Excel bảo thủ; raw string luôn được lưu riêng để truy vết."""
    if raw is None:
        return None
    value = Decimal(str(raw))
    if not value.is_finite():
        raise ValueError("Lượng chi tiết phải hữu hạn.")
    digits = list(value.as_tuple().digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
    magnitude = value.copy_abs()
    if len(digits) > 15 or (magnitude and not Decimal("1e-307") <= magnitude <= Decimal("1e307")):
        return None
    return float(value)


def _detail_append(ws, values):
    line = ws.max_row + 1
    for column, value in enumerate(values, 1):
        cell = ws.cell(line, column, value)
        if isinstance(value, str):
            cell.data_type = "s"  # Không cho nhãn/nguồn/expression trở thành công thức Excel.
        elif isinstance(value, (int, float)):
            cell.number_format = "0.##############E+00" if 0 < abs(value) < 1e-14 else "0.###############;-0.###############;0"
        cell.font = Font(name="Arial", size=10)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[line].height = 48
    return line


def _detail_sheet(wb, title, headers, widths, result):
    _sheet(wb, title, headers, [])
    ws = wb[title]
    ws.insert_rows(1, 4)
    ws.sheet_view.showGridLines = False
    summary = getattr(result, "quantity_summary", None)
    for row, text in ((2, title.upper()), (3, f"Mã kết quả lưu: {result.takeoff_id}" if getattr(result, "takeoff_id", None) is not None
                       else "Chưa có mã kết quả lưu; không tự xác nhận trạng thái duyệt."),
                      (4, f"Snapshot khối lượng: {summary.quantity_snapshot_hash}" if summary else "Chưa có tổng raw nhóm.")):
        cell = ws.cell(row, 1, text)
        cell.data_type = "s"
        cell.font = Font(name="Arial", size=14 if row == 2 else 10, bold=row == 2)
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(headers))
    for cell, width in zip(ws[5], widths):
        cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="263B54")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = width
    ws.row_dimensions[5].height = 32
    ws.freeze_panes = "C6"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.print_title_rows = "1:5"
    return ws


def _detail_link(cell, target, label):
    cell.value, cell.data_type = label, "s"
    cell.hyperlink = "#" + target
    cell.font = Font(name="Arial", size=10, color="1256A0", underline="single")


_SPEC_LABELS = {
    "stage": "Hạng mục", "code": "Mã công tác", "variant": "Cấu tạo", "unit": "Đơn vị", "source": "Nguồn",
    "basis": "Căn cứ", "formwork_of": "Cốp pha cho", "steel_element": "Cấu kiện thép", "wall_system_id": "Hệ tường",
    "lean_concrete_grade": "Mác bê tông lót", "concrete_grade": "Mác bê tông", "concrete_supply": "Cách cấp bê tông",
    "formwork_type": "Loại cốp pha", "masonry_mortar_grade": "Mác vữa xây", "plaster_mortar_grade": "Mác vữa trát",
    "thickness_variant": "Quy cách chiều dày", "screed_mortar_grade": "Mác vữa cán",
    "waterproof_material_variant": "Quy cách chống thấm",
}


_DETAIL_LEVEL_LABEL = {
    "components": "Chi tiết theo cấu kiện",
    "aggregate": "Chỉ có tổng",
    "unavailable": "Chưa có chi tiết khả dụng",
}


def _coverage_text(c):
    component_scope = ("Không có công tác để đánh giá" if not c.work_count else
                       "Đủ chi tiết cấu kiện" if c.complete_components else "Chưa đủ chi tiết cấu kiện")
    return (f"{c.quantity_complete_works}/{c.work_count} công tác đủ lượng; {c.quantity_incomplete_works} chưa đủ. "
            f"Dòng đóng góp: {c.known_contribution_rows} đã biết, {c.unknown_contribution_rows} chưa biết; "
            f"{c.reference_rows} dòng tham khảo. "
            f"Theo cấu kiện: {c.components}; chỉ có tổng: {c.aggregate}; "
            f"chi tiết chưa khả dụng: {c.unavailable}; chưa có diễn giải: {c.no_detail}. "
            f"{component_scope}. Chờ xác định quy cách để gộp: {c.compatibility_pending_works} công tác.")


def _group_block(ws, main, trace, summary, locations, trace_rows):
    """Các giá trị và nhóm trong snapshot do backend lập; không tổng hợp lại trong Excel."""
    _detail_append(ws, ["Tổng raw theo nhóm", "Snapshot", summary.quantity_snapshot_hash])
    _detail_append(ws, ["Phạm vi toàn bộ", _coverage_text(summary.coverage), summary.coverage.model_dump_json()])
    headers = ["Nhóm", "Công tác / quy cách", "Tương thích quy cách", "Đơn vị", "Chỉ tiêu",
               "Giá trị số", "Giá trị gốc (text)", "Đủ khối lượng", "Phạm vi / lý do", "Diễn giải độ bao phủ"]
    _detail_append(ws, headers)
    ws.column_dimensions["J"].width = 55
    _detail_append(main, [None, "Tổng khối lượng theo nhóm", *([None] * 8),
                          "Đối soát từ cùng kết quả; các dòng tổng không phải dòng đóng góp. " + _coverage_text(summary.coverage)])
    for group in summary.groups:
        key = group.key
        fields = key.model_dump(exclude_none=True, exclude={"specification", "isolated_work_key"})
        spec = "\n".join(f"{_SPEC_LABELS.get(k, k)}: {v}" for k, v in (fields | key.specification).items() if v is not None)
        compatibility = "Quy cách tương thích" if group.compatibility == "resolved" else "Tách riêng: chưa đủ căn cứ gộp"
        reasons = "; ".join(group.compatibility_reasons)
        for field, label in _SPEC_LABELS.items():
            reasons = reasons.replace(field, label)
        group_line = _detail_append(main, [None, f"{STAGES.get(key.stage, key.stage) or 'Chưa rõ hạng mục'} · {key.code}",
                                           None, None, None, None, None, None, None, key.unit, spec, group.group_id])
        main.row_dimensions[group_line].height = min(300, 16 * (spec.count("\n") + 2))
        base = [group.group_id, spec, compatibility, key.unit]
        missing_reasons = "; ".join(dict.fromkeys(reason for ref in group.missing_work_refs for reason in ref.reasons))
        note = "; ".join(filter(None, [compatibility, reasons, _coverage_text(group.coverage), missing_reasons]))
        for label, raw in (("Phần biết raw", group.known_part_raw), ("Tổng raw toàn phạm vi", group.total_raw)):
            _detail_append(ws, base + [label, _detail_number(raw), raw, "Có" if group.complete else "Không",
                                       reasons])
            numeric = _detail_number(raw)
            _detail_append(main, [None, label, None, None, None, None, None, "Tổng nhóm",
                                  raw if numeric is None else numeric, key.unit, note, group.group_id])
        coverage = group.coverage
        _detail_append(ws, [group.group_id, key.code, None, key.unit, "Độ bao phủ",
                            None, None, f"{coverage.quantity_complete_works}/{coverage.work_count} công tác đủ lượng",
                            coverage.model_dump_json(), _coverage_text(coverage)])
        for member in group.member_work_keys:
            heading = locations[member, None]
            _detail_link(main.cell(heading, 12), f"'Tiên lượng chi tiết'!B{group_line}", f"Nhóm {group.group_id}")
            back = _detail_append(main, [None, member, None, None, None, None, None, "Thành viên"])
            _detail_link(main.cell(back, 2), f"'Tiên lượng chi tiết'!B{heading}", f"{member} · {main.cell(heading, 2).value}")
            line = _detail_append(ws, [group.group_id, member, None, None, "Thành viên"])
            _detail_link(ws.cell(line, 2), f"'Tiên lượng chi tiết'!B{locations[member, None]}", member)
            tr = _detail_append(trace, [None, member, None, None, "Thành viên"])
            _detail_link(trace.cell(tr, 1), f"'Tiên lượng chi tiết'!B{heading}", member)
            trace_rows.setdefault(member, {})[None] = tr
            for tr in trace_rows[member].values():
                _detail_link(trace.cell(tr, 18), f"'Tiên lượng chi tiết'!B{group_line}", group.group_id)
        for ref in group.missing_work_refs:
            tr = trace_rows[ref.work_key][ref.row_id]
            trace.cell(tr, 19, "; ".join(ref.reasons)).data_type = "s"
            line = _detail_append(ws, [group.group_id, ref.work_key, ref.row_id, None, "Thiếu dữ liệu",
                                       None, None, None, "; ".join(ref.reasons)])
            _detail_link(ws.cell(line, 2), f"'Tiên lượng chi tiết'!B{locations[ref.work_key, ref.row_id]}", ref.work_key)


def _quantity_detail_sheets(wb, result):
    """Consume đúng detail của result truyền vào, không tính lại lượng hoặc gộp raw nhóm."""
    main = _detail_sheet(wb, "Tiên lượng chi tiết", ["STT", "Công tác / vị trí", "Số cấu kiện", "Dài (m)", "Rộng (m)",
        "Cao (m)", "Hệ số có nguồn", "Cộng / trừ", "Khối lượng", "Đơn vị", "Thuyết minh", "Căn cứ"],
        [6, 34, 10, 12, 12, 12, 18, 12, 16, 10, 40, 18], result)
    trace = _detail_sheet(wb, "Truy vết chi tiết", ["Dòng tiên lượng", "Công tác trong kết quả", "Khóa dòng", "Nhóm", "Vai trò", "Dấu",
        "Đơn vị", "Lượng tuyệt đối gốc (text)", "Đóng góp có dấu (text)", "Giới hạn số Excel", "Kích thước gốc",
        "Hệ số và nguồn", "Quy đổi", "Phương pháp", "Diễn giải (text)", "Nguồn", "Lý do thiếu", "Mã nhóm đối soát", "Lý do thiếu theo nhóm"],
        [19, 22, 28, 22, 16, 8, 10, 28, 28, 30, 55, 40, 35, 22, 55, 65, 40, 22, 45], result)
    compare = _detail_sheet(wb, "Đối soát chi tiết", ["Công tác trong kết quả", "Công tác / cấu tạo", "Tầng / vị trí", "Đơn vị",
        "Chỉ tiêu", "Giá trị số", "Giá trị gốc (text)", "Mức chi tiết / phạm vi", "Căn cứ / lý do thiếu"],
        [22, 40, 25, 10, 28, 22, 38, 28, 65], result)
    locations = {}
    trace_rows = {}
    for ordinal, work in enumerate(result.works):
        key = f"w:{ordinal}"  # Chỉ ổn định trong chính result snapshot, không dùng qua lần tính lại.
        name = " · ".join(filter(None, [work.name, work.code, work.variant]))
        position = " · ".join(filter(None, [STAGES.get(work.stage or "", work.stage), work.plan or COMMON, work.element]))
        heading = _detail_append(main, [ordinal + 1, name, None, None, None, None, None, None, None, work.unit, position])
        locations[key, None] = heading
        main.merge_cells(start_row=heading, start_column=2, end_row=heading, end_column=8)
        main.row_dimensions[heading].height = 48
        detail = getattr(work, "quantity_detail", None)
        base = [key, name, position, work.unit]
        if detail is None:
            _detail_append(main, [None, "Chưa có diễn giải chi tiết"])
            _detail_append(compare, base + ["Lượng legacy", work.quantity, None if work.quantity is None else str(work.quantity),
                "Chưa có diễn giải chi tiết", "; ".join(work.missing + work.evidence)])
            continue
        group = object()
        for index, row in enumerate(detail.rows, 1):
            if row.group != group:
                group = row.group
                line = _detail_append(main, [None, group or "Chi tiết"])
                for cell in main[line]:
                    cell.fill = PatternFill("solid", fgColor="E8EDF3")
            raw = row.raw_quantity
            amount = None if raw is None or row.role == "reference" else format(
                Decimal(raw).copy_negate() if row.sign == -1 else Decimal(raw), "f")
            dimensions = row.dimensions
            dimensions_json = dimensions.model_dump(mode="json") if dimensions is not None else None
            factors = "; ".join(f"{f.name}={f.value} ({f.source})" for f in row.factors)
            precision = "Xem raw text; vượt precision Excel" if raw is not None and _detail_number(raw) is None else ""
            repetition = f"Lặp {dimensions.repetitions} lần; đã có trong lượng" if dimensions and dimensions.repetitions != 1 else ""
            note = "; ".join(filter(None, [row.expression, repetition, "; ".join(row.missing), precision]))
            d = lambda field: _detail_number(getattr(dimensions, field)) if dimensions is not None else None
            line = _detail_append(main, [index, row.label, d("count"), d("length_m"), d("width_m"), d("height_m"), factors or None,
                "Tham khảo" if row.role == "reference" else "−" if row.sign == -1 else "+", _detail_number(amount), row.unit, note])
            locations[key, row.row_id] = line
            main.row_dimensions[line].height = 60
            traced = _detail_append(trace, [None, key, row.row_id, row.group, row.role, row.sign, row.unit, raw, amount, precision,
                json.dumps(dimensions_json, ensure_ascii=False), json.dumps([f.model_dump(mode="json") for f in row.factors], ensure_ascii=False),
                json.dumps(row.conversion.model_dump(mode="json") if row.conversion else None, ensure_ascii=False), row.method,
                row.expression, "\n".join(row.sources), "; ".join(row.missing)])
            trace_rows.setdefault(key, {})[row.row_id] = traced
            trace.row_dimensions[traced].height = 72
            _detail_link(main.cell(line, 12), f"'Truy vết chi tiết'!A{traced}", f"Nguồn {ordinal + 1}.{index}")
            _detail_link(trace.cell(traced, 1), f"'Tiên lượng chi tiết'!B{line}", f"Tiên lượng dòng {line}")
        for label, value in (("Phần khối lượng đã biết", detail.known_part_raw),
                             ("Tổng toàn phạm vi" if detail.complete else "Tổng toàn phạm vi (chưa đủ)", detail.total_raw)):
            precision = "Xem Đối soát chi tiết; vượt precision Excel" if value is not None and _detail_number(value) is None else ""
            _detail_append(main, [None, label, None, None, None, None, None, None, _detail_number(value), work.unit, precision])
        scope = _DETAIL_LEVEL_LABEL[detail.detail_level] + ("; đủ lượng toàn phạm vi" if detail.complete else "; chưa đủ lượng toàn phạm vi")
        for label, value in (("Phần biết raw", detail.known_part_raw), ("Tổng raw toàn phạm vi", detail.total_raw),
                             ("Lượng legacy", detail.legacy_quantity), ("Chênh raw − legacy", detail.legacy_delta)):
            _detail_append(compare, base + [label, _detail_number(value), value, scope, "; ".join(work.missing + work.evidence)])
    if getattr(result, "quantity_summary", None) is not None:
        _group_block(compare, main, trace, result.quantity_summary, locations, trace_rows)
    for ws in (main, trace, compare):
        ws.print_area = ws.dimensions


def boq_workbook(result, req=None) -> Workbook:
    wb = Workbook()
    wb.remove(wb.active)
    head = ["Tầng", "Cấu kiện", "Công tác", "Chi tiết", "Đơn vị", "Khối lượng", "Trạng thái (A đọc / B suy / C tạm tính / D thiếu)",
            "Giai đoạn", "Nguồn số (basis)", "formula", "Đầu vào quyết định trạng thái", "evidence", "missing_reason"]
    _sheet(wb, "Tổng hợp", ["Mã", "Công tác", "Đơn vị", "Khối lượng", "Đủ số", "Trạng thái", "Số dòng"],
           [[t.code, t.name, t.unit, t.quantity, "có" if t.complete else "thiếu", _status(t.status), t.items] for t in result.totals]
           + [["COP_PHA/" + t.code, t.name, t.unit, t.quantity, "có" if t.complete else "thiếu", _status(t.status), t.items]
              for t in result.formwork])
    plan_order = {p.name: i for i, p in enumerate(req.plans)} if req is not None else {}
    works = sorted(result.works, key=lambda w: (plan_order.get(w.plan, len(plan_order) + (w.plan is None)), list(WORKS).index(w.code)))
    _sheet(wb, "Theo tầng", head, [_row(w) for w in works])
    _sheet(wb, "Theo cấu kiện", head[1:2] + head[:1] + head[2:],
           [[r[1], r[0]] + r[2:] for r in sorted((_row(w) for w in result.works), key=lambda r: (r[1], r[0]))])
    rebar = req.rebar if req is not None else []
    _sheet(wb, "Cốt thép", ["Bảng", "Dòng", "Cấu kiện", "Mã cấu kiện", "Số hiệu", "Hình dạng", "Ø (mm)", "Chiều dài cắt (mm)",
                            "Số thanh", "kg/m", "Nguồn kg/m", "kg (tính)", "kg (bảng ghi)", "formula", "evidence",
                            "missing_reason", "Ghi chú"],
           [[r.table, r.row, r.element, r.element_code or "Not supported", r.mark, r.shape, r.dia_mm, r.cut_length_mm,
             r.total_bars, r.kg_per_m, r.kg_per_m_source, r.kg, r.schedule_kg, r.formula, r.evidence, "; ".join(r.missing),
             "; ".join(r.notes)] for r in rebar])
    _sheet(wb, "Vật liệu", ["Mã", "Vật liệu", "Nhóm", "Loại", "Đơn vị", "Khối lượng", "Khoảng (min–max)", "Khối lượng kg", "Đủ số",
                            "Trạng thái", "Mức xác nhận hệ số", "missing_reason", "Từ công tác"],
           [[m.material_id or "", m.name, m.group_id or "", RAW_CLASSES.get(m.raw_class or "", ""), m.unit, m.quantity,
             f"{m.quantity_min} – {m.quantity_max}" if m.quantity_min is not None else "", m.weight_kg,
             "có" if m.complete else "thiếu", _status(m.status), m.confirmation or "", "; ".join(m.missing),
             "; ".join(u.via for u in m.uses[:8])] for m in result.materials])
    groups = getattr(result, "by_group", [])
    _sheet(wb, "Theo nhóm", ["Nhóm", "Tên nhóm", "Trong phạm vi phần thô", "Vật liệu", "Khối lượng kg", "Đủ kg", "Trạng thái"],
           [[g.group_id, g.name, "có" if g.in_scope else "ngoài phạm vi", ", ".join(g.materials), g.weight_kg,
             "có" if g.weight_complete else "chưa đủ dữ liệu khối lượng", _status(g.status)] for g in groups])
    classes = getattr(result, "by_class", [])
    _sheet(wb, "Theo loại", ["Loại", "Tên loại", "Vật liệu", "Khối lượng kg", "Đủ kg", "Trạng thái"],
           [[g.group_id, g.name, ", ".join(g.materials), g.weight_kg, "có" if g.weight_complete else "chưa đủ dữ liệu khối lượng",
             _status(g.status)] for g in classes])
    _sheet(wb, "Cảnh báo", ["#", "Cảnh báo"], [[i, w] for i, w in enumerate(result.warnings, start=1)])
    m = support_matrix()
    _sheet(wb, "Phạm vi hỗ trợ", list(m.columns), m.values.tolist())
    _quantity_detail_sheets(wb, result)
    return wb


def export_for_optimizer(result) -> dict:
    """Bảng vật liệu thô cho bộ tối ưu (đặc tả 1A, 11): mỗi vật liệu có nhóm, số lượng (khoảng nếu có), kg, m³ vận chuyển,
    trạng thái, mức xác nhận và lượng theo giai đoạn thi công. Quy tắc 3.1: dòng D không xuất số mà vào danh sách thiếu."""
    materials, missing = [], []
    for m in result.materials:
        if m.status == "D":
            missing.append({"material_id": m.material_id, "name": m.name, "raw_class": m.raw_class, "unit": m.unit, "known_part": m.quantity,
                            "reason": "; ".join(m.missing)})
            continue
        stages: dict[str, float] = {}
        for u in m.uses:
            if u.quantity is not None:
                stages[u.stage or "chua_ro"] = round(stages.get(u.stage or "chua_ro", 0.0) + u.quantity, 3)
        materials.append({"material_id": m.material_id, "name": m.name, "group_id": m.group_id, "raw_class": m.raw_class, "unit": m.unit,
                          "quantity": m.quantity, "quantity_min": m.quantity_min, "quantity_max": m.quantity_max,
                          "weight_kg": m.weight_kg, "transport_volume_m3": m.transport_volume_m3, "status": m.status,
                          "provisional": m.status == "C", "confirmation": m.confirmation, "by_stage": stages})
    return {"status": result.status, "stages": STAGES, "materials": materials, "missing": missing,
            "groups": [g.model_dump(mode="json") for g in result.by_group],
            "classes": [g.model_dump(mode="json") for g in getattr(result, "by_class", [])],
            "envelope_by_orientation": result.envelope_by_orientation}


def boq_bytes(result, req=None) -> bytes:
    buf = BytesIO()
    boq_workbook(result, req).save(buf)
    return buf.getvalue()
