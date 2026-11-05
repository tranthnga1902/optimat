"""Preview tham chiếu G8, không nối vào exporter hoặc snapshot sản phẩm."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parent / "exporter_preview_09"
FIXTURE = HERE / "M1_AF11110_REFERENCE.json"
NUMBER_FORMAT = "0.###############;-0.###############;0"
sys.path.insert(0, str(HERE.parents[2] / "src"))
DETAIL_SPEC = importlib.util.spec_from_file_location("g8_staged_detail_09", HERE / "quantity_details_proposed.py")
DETAILS = importlib.util.module_from_spec(DETAIL_SPEC)
sys.modules[DETAIL_SPEC.name] = DETAILS
DETAIL_SPEC.loader.exec_module(DETAILS)


def decimal_value(raw):
    if raw is None:
        return None
    value = Decimal(str(raw))
    if not value.is_finite():
        raise ValueError("Giá trị phải hữu hạn.")
    return value


def raw_text(raw):
    """Giữ nguyên chuỗi nguồn, gồm trailing zero và floating artifact."""
    return None if raw is None else str(raw)


def excel_number(raw):
    value = decimal_value(raw)
    if value is None:
        return None
    significant = list(value.as_tuple().digits)
    while len(significant) > 1 and significant[-1] == 0:
        significant.pop()
    magnitude = value.copy_abs()
    if len(significant) > 15 or (magnitude and not Decimal("1e-307") <= magnitude <= Decimal("1e307")):
        return None
    return float(value)


def signed_text(row):
    raw = row.get("raw_quantity")
    if row.get("role", "contribution") != "contribution" or raw is None:
        return None
    value = decimal_value(raw)
    if value < 0 or row.get("sign", 1) not in (-1, 1):
        raise ValueError("Lượng là trị tuyệt đối và dấu chỉ nhận +1 hoặc -1.")
    return format(value.copy_negate() if row.get("sign", 1) == -1 else value, "f")


def put(ws, row, col, value):
    cell = ws.cell(row, col, value)
    if isinstance(value, str):
        cell.data_type = "s"  # Nhãn/nguồn/expression luôn là text, kể cả bắt đầu bằng '='.
    elif isinstance(value, (float, int)) and not isinstance(value, bool):
        cell.number_format = NUMBER_FORMAT
    cell.font = Font(name="Arial", size=10)
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    return cell


def add_row(ws, values):
    number = ws.max_row + 1
    for col, value in enumerate(values, 1):
        put(ws, number, col, value)
    ws.row_dimensions[number].height = 32
    return number


def sheet(wb, name, title, headers, widths):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    put(ws, 2, 1, title).font = Font(name="Arial", size=14, bold=True)
    put(ws, 3, 1, "Bản tham chiếu staging. Chưa liên kết snapshot sản phẩm đã kiểm.")
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=len(headers))
    for col, header in enumerate(headers, 1):
        c = put(ws, 5, col, header)
        c.font = Font(name="Arial", size=10, color="FFFFFF", bold=True)
        c.fill = PatternFill("solid", fgColor="263B54")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = widths[col - 1]
    ws.row_dimensions[5].height = 32
    ws.freeze_panes = "C6"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.print_title_rows = "1:5"
    return ws


def link(cell, target, label):
    cell.value, cell.data_type = label, "s"
    cell.hyperlink = "#" + target
    cell.font = Font(name="Arial", size=10, color="1256A0", underline="single")


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def preview_workbook(data):
    """Chỉ hiển thị payload tham chiếu; không tính lại lượng từ dimensions/formula."""
    # Tái dùng validator staging03, không viết bộ cộng/kiểm ledger thứ hai ở exporter.
    if "complete" in data:
        if not isinstance(data["complete"], bool):
            raise ValueError("complete phải là boolean.")
        DETAILS.WorkQuantityDetail.model_validate({
            "unit": data["unit"], "rows": data.get("rows", []),
            "detail_level": data.get("detail_level", "components"),
            "known_part_raw": data.get("known_part_raw"), "total_raw": data.get("total_raw"),
            "complete": data["complete"], "scope_complete": data.get("scope_complete", False),
            "legacy_quantity": data.get("legacy_quantity"), "legacy_delta": data.get("legacy_delta"),
        })
    elif data.get("fixture_kind") != "REFERENCE_ONLY_M1":
        raise ValueError("Payload chưa khai báo phạm vi chi tiết; không công bố tổng.")
    wb = Workbook()
    wb.remove(wb.active)
    main = sheet(wb, "Tiên lượng", "TIÊN LƯỢNG THAM CHIẾU", [
        "STT", "Công tác / vị trí", "Số cấu kiện", "Dài (m)", "Rộng (m)", "Cao (m)",
        "Hệ số có nguồn", "Cộng / trừ", "Khối lượng", "Đơn vị", "Thuyết minh", "Căn cứ"],
        [6, 29, 10, 12, 12, 12, 16, 12, 15, 9, 40, 16])
    trace = sheet(wb, "Truy vết", "TRUY VẾT DÒNG TIÊN LƯỢNG", [
        "Dòng tiên lượng", "Khóa dòng", "Nhóm", "Vai trò", "Dấu", "Đơn vị", "Lượng tuyệt đối gốc (text)",
        "Đóng góp có dấu (text)", "Giới hạn số Excel", "Kích thước gốc", "Hệ số và nguồn", "Quy đổi",
        "Phương pháp", "Diễn giải (text)", "Nguồn", "Lý do thiếu"],
        [18, 28, 20, 16, 8, 10, 26, 26, 27, 50, 35, 30, 22, 55, 65, 40])
    compare = sheet(wb, "Đối soát", "ĐỐI SOÁT LƯỢNG VÀ NGUỒN", [
        "Chỉ tiêu", "Giá trị số", "Giá trị gốc (text)", "Đơn vị", "Căn cứ / ý nghĩa"],
        [42, 22, 38, 12, 85])
    work_row = add_row(main, [data.get("norm_code"), data.get("work_name"), None, None, None, None,
                              None, None, None, data.get("unit"), "Khối lượng dòng lấy từ nguồn; không nhân lại kích thước."])
    main.merge_cells(start_row=work_row, start_column=2, end_row=work_row, end_column=7)
    main.row_dimensions[work_row].height = 48
    previous_group = object()
    for index, row in enumerate(data.get("rows", []), 1):
        if row.get("group", "") != previous_group:
            previous_group = row.get("group", "")
            group_row = add_row(main, [None, previous_group])
            for c in main[group_row]:
                c.fill = PatternFill("solid", fgColor="E8EDF3")
                c.font = Font(name="Arial", size=10, bold=True)
        raw = row.get("raw_quantity")
        decimal_value(raw)
        amount = signed_text(row)
        dims = row.get("dimensions") or {}
        factors = row.get("factors", [])
        factor_label = "; ".join(f"{f['name']}={f['value']} ({f['source']})" for f in factors)
        precision = "Xem raw text; vượt precision Excel" if raw is not None and excel_number(raw) is None else ""
        note = "; ".join(filter(None, [row.get("expression", ""), "; ".join(row.get("missing", [])), precision]))
        role = row.get("role", "contribution")
        line = add_row(main, [index, row["label"], excel_number(dims.get("count")), excel_number(dims.get("length_m")),
            excel_number(dims.get("width_m")), excel_number(dims.get("height_m")), factor_label or None,
            "Tham khảo" if role == "reference" else "−" if row.get("sign", 1) == -1 else "+",
            excel_number(amount), row["unit"], note])
        main.row_dimensions[line].height = 60
        trace_line = add_row(trace, [None, row["row_id"], previous_group, role, row.get("sign", 1), row["unit"],
            raw_text(raw), amount, precision, json_text(dims), json_text(factors), json_text(row.get("conversion")),
            row.get("method"), row.get("expression"), "\n".join(row.get("sources", [])), "; ".join(row.get("missing", []))])
        trace.row_dimensions[trace_line].height = 72
        link(main.cell(line, 12), f"'Truy vết'!A{trace_line}", f"Nguồn {index}")
        link(trace.cell(trace_line, 1), f"'Tiên lượng'!B{line}", f"Tiên lượng dòng {line}")
    if not data.get("rows"):
        add_row(main, [None, "Chưa có diễn giải chi tiết"])
    total = data.get("total_raw")
    if "complete" in data and not data["complete"]:
        add_row(main, [None, "Phần khối lượng đã biết", None, None, None, None, None, None,
                      excel_number(data.get("known_part_raw")), data.get("unit"), "Chưa đủ toàn phạm vi"])
    total_label = "Tổng toàn phạm vi" if data.get("complete") else "Tổng lượng nguồn tham chiếu" if "complete" not in data else "Tổng toàn phạm vi (chưa đủ)"
    total_line = add_row(main, [None, total_label, None, None,
                              None, None, None, None, excel_number(total), data.get("unit")])
    for c in main[total_line]:
        c.font = Font(name="Arial", size=10, bold=True)
        c.border = Border(top=Side(style="thin", color="8391A0"))
    diagnostics = [
        ("Phần biết (raw)", data.get("known_part_raw"), "Theo payload; không suy từ lượng legacy"),
        ("Tổng raw đủ phạm vi", total, data.get("source_total_cell", "Theo payload")),
        ("Số lưu nguồn (cached)", data.get("stored_total"), "Giá trị lưu trong workbook nguồn; chưa audit formula"),
        ("Lượng legacy sản phẩm", data.get("legacy_quantity"), "Chỉ có nếu payload cung cấp; không dùng minh họa thay engine"),
        ("Chênh raw − legacy", data.get("legacy_delta"), "Giữ dấu; không bù dòng cuối"),
    ]
    for label, raw, note in diagnostics:
        add_row(compare, [label, excel_number(raw), raw_text(raw), data.get("unit"), note])
    if data.get("fixture_kind") == "REFERENCE_ONLY_M1":
        # Chỉ là đối soát rounding fixture; không dùng hai số này thay quantity engine.
        row_round = sum((Decimal(str(round(float(signed_text(r)), 3))) for r in data["rows"]
                         if r.get("role", "contribution") == "contribution" and r.get("raw_quantity") is not None), Decimal(0))
        after_sum = None if total is None else Decimal(str(round(float(total), 3)))
        for label, value in [("Minh họa round3 từng dòng rồi cộng", row_round), ("Minh họa round3 sau tổng", after_sum)]:
            add_row(compare, [label, excel_number(value), raw_text(value), data.get("unit"), "Minh họa fixture; không phải quantity legacy engine"])
            if value is not None and total is not None:
                delta = decimal_value(total) - value
                add_row(compare, ["Raw − " + label.lower(), excel_number(delta), raw_text(delta), data.get("unit"), "Chênh minh họa có dấu; không thêm dòng bù"])
    add_row(compare, ["Phạm vi đầy đủ", None, str(data.get("complete")) if "complete" in data else "Chưa xác nhận", None,
                      "Fixture tham chiếu không tự xác nhận phạm vi sản phẩm"])
    add_row(compare, ["Nguồn", None, data.get("source"), None, data.get("sha256")])
    if data.get("materials"):
        materials = sheet(wb, "Vật tư tham chiếu", "VẬT TƯ THAM CHIẾU M1", [
            "Mã nguồn", "Vật tư", "Đơn vị", "Mức dùng / m³", "Tích theo raw", "Cached nguồn", "Tích − cached", "Căn cứ"],
            [19, 26, 10, 19, 22, 20, 22, 36])
        for material in data["materials"]:
            raw, cached = material["quantity_from_raw"], material["stored_quantity"]
            with localcontext() as ctx:
                ctx.prec = max(50, len(raw) + len(cached) + 5)
                delta = format(decimal_value(raw) - decimal_value(cached), "f")
            line = add_row(materials, [material["source_material_code"], material["name"], material["unit"],
                excel_number(material["rate_per_m3"]), excel_number(raw), excel_number(cached), excel_number(delta)])
            target = add_row(compare, [material["name"] + " — mức dùng", excel_number(material["rate_per_m3"]),
                material["rate_per_m3"], material["unit"] + "/m³", material["source"]])
            for label, value in [("tích raw", raw), ("cached nguồn", cached), ("tích − cached", delta)]:
                add_row(compare, [material["name"] + " — " + label, excel_number(value), value, material["unit"],
                    "Tham chiếu riêng M1, không phải materials legacy sản phẩm. " + material["source"]])
            link(materials.cell(line, 8), f"'Đối soát'!A{target}", material["source"])
        add_row(materials, [None, "Tách riêng catalog và engine legacy; chưa kiểm công thức nguồn hoặc Excel native."])
        materials.merge_cells(start_row=materials.max_row, start_column=2, end_row=materials.max_row, end_column=8)
    for ws in wb:
        ws.print_area = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
    wb.active = 0
    return wb


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    target = OUTPUT / "M1_AF11110_THAM_CHIEU.xlsx"
    canonical = HERE.parents[2] / "src" / "optimat" / "rough" / "boq.py"
    canonical_hash_before = hashlib.sha256(canonical.read_bytes()).hexdigest()
    preview_workbook(data).save(target)
    reopened = load_workbook(target, data_only=False)
    assert reopened["Tiên lượng"].max_column == 12
    trace = reopened["Truy vết"]
    assert [trace.cell(i, 7).value for i in range(6, trace.max_row + 1)] == [r.get("raw_quantity") for r in data["rows"]]
    assert [trace.cell(i, 8).value for i in range(6, trace.max_row + 1)] == [signed_text(r) for r in data["rows"]]
    assert reopened["Tiên lượng"].cell(reopened["Tiên lượng"].max_row, 9).value == excel_number(data.get("total_raw"))
    for i, material in enumerate(data["materials"], 6):
        assert reopened["Vật tư tham chiếu"].cell(i, 5).value == excel_number(material["quantity_from_raw"])
        assert reopened["Vật tư tham chiếu"].cell(i, 6).value == excel_number(material["stored_quantity"])
    assert not [c.coordinate for ws in reopened for row in ws for c in row if c.data_type == "f"]
    reopened.close()
    canonical_hash_after = hashlib.sha256(canonical.read_bytes()).hexdigest()
    assert canonical_hash_before == canonical_hash_after
    manifest = {"workbook": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), "reference_only": True,
        "staged_validator_sha256": hashlib.sha256((HERE / "quantity_details_proposed.py").read_bytes()).hexdigest(),
        "canonical_boq_sha256_before": canonical_hash_before, "canonical_boq_sha256_after": canonical_hash_after,
        "snapshot_reviewed": False, "openpyxl_reopen": True, "excel_native_checked": False,
        "ui_checked": False, "canonical_changed": False}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
