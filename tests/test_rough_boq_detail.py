"""Consumer Excel detail: pure DTO/serialization, không HTTP/DB/CAD/producer."""
from io import BytesIO

import pandas as pd
import pytest
from openpyxl import load_workbook

from optimat.rough import boq
from optimat.rough.models import DetailFactor, QuantityDetailRow, WorkDimensions, WorkItem
from optimat.rough.quantity_details import summarize
from optimat.rough.takeoff import RoughResult

LEGACY_SHEETS = ["Tổng hợp", "Theo tầng", "Theo cấu kiện", "Cốt thép", "Vật liệu", "Theo nhóm", "Theo loại", "Cảnh báo", "Phạm vi hỗ trợ"]
DETAIL_SHEETS = ["Tiên lượng chi tiết", "Truy vết chi tiết", "Đối soát chi tiết"]


@pytest.fixture(autouse=True)
def pure_support(monkeypatch):
    monkeypatch.setattr(boq, "support_matrix", lambda: pd.DataFrame({"Công tác": ["SYNTHETIC"]}))


def row(**patch):
    return QuantityDetailRow(**(dict(row_id="r1", label="Cấu kiện thử", group="Nhóm thử", unit="m³",
        raw_quantity="1", method="source_quantity", sources=["Nguồn SYNTHETIC"]) | patch))


def work(rows=None, *, legacy=1.0, scope=True, **patch):
    detail = summarize(rows if rows is not None else [row()], "m³", legacy, scope_complete=scope)
    return WorkItem(code="BE_TONG_LOT", name="Công tác thử", unit="m³", quantity=legacy,
                    quantity_detail=detail, status="B", **patch)


def reopen(works, **patch):
    result = RoughResult(works=works, **patch)
    before = result.model_dump_json()
    wb = load_workbook(BytesIO(boq.boq_bytes(result)), data_only=False)
    assert result.model_dump_json() == before
    return wb


def records(ws):
    headers = [c.value for c in ws[5]]
    return [dict(zip(headers, r)) for r in ws.iter_rows(min_row=6, values_only=True)]


def test_detail_roundtrip_sources_and_legacy_separate():
    dimensions = WorkDimensions(label="Cấu kiện", source="Nguồn kích thước", count=2, repetitions=3,
                               length_m=.7, width_m=1.5, height_m=.1)
    factors = [DetailFactor(name="Hệ số thử", value="2", unit="1", meaning="Đã có trong lượng", source="Ô nguồn")]
    w = work([row(raw_quantity="0.1259", dimensions=dimensions, factors=factors)], legacy=.126,
             plan="Tầng 1", variant="Cấu tạo riêng", stage="mong")
    wb = reopen([w], takeoff_id=42)
    assert wb.sheetnames == LEGACY_SHEETS + DETAIL_SHEETS
    assert wb["Tiên lượng chi tiết"].max_column == 12
    line = next(r for r in records(wb["Tiên lượng chi tiết"]) if r["Công tác / vị trí"] == "Cấu kiện thử")
    assert line["Khối lượng"] == .1259  # Không nhân count/repetitions/factor lần nữa.
    assert line["Số cấu kiện"] == 2 and line["Dài (m)"] == .7
    assert "Lặp 3" in line["Thuyết minh"] and "Ô nguồn" in line["Hệ số có nguồn"]
    traced = records(wb["Truy vết chi tiết"])[0]
    assert traced["Lượng tuyệt đối gốc (text)"] == "0.1259"
    assert traced["Nguồn"] == "Nguồn SYNTHETIC" and traced["Công tác trong kết quả"] == "w:0"
    assert "Nguồn kích thước" in traced["Kích thước gốc"]
    comparison = {r["Chỉ tiêu"]: r for r in records(wb["Đối soát chi tiết"])}
    assert comparison["Lượng legacy"]["Giá trị gốc (text)"] == "0.126"
    assert comparison["Chênh raw − legacy"]["Giá trị gốc (text)"] == "-0.0001"
    for name in DETAIL_SHEETS:
        assert wb[name]["A3"].value == "Mã kết quả lưu: 42"
    assert any(c.hyperlink and "Truy vết chi tiết" in c.hyperlink.target for row_cells in wb[DETAIL_SHEETS[0]] for c in row_cells)
    assert any(c.hyperlink and "Tiên lượng chi tiết" in c.hyperlink.target for row_cells in wb[DETAIL_SHEETS[1]] for c in row_cells)


def test_old_payload_no_detail_preserves_all_legacy_sheets(monkeypatch):
    result = RoughResult.model_validate({"works": [{"code": "DAM", "name": "Dầm cũ", "unit": "m³", "quantity": 0,
        "formula": "Giữ diễn giải cũ", "evidence": ["Nguồn cũ"], "dimensions": [
            {"label": "Không tạo dòng giả", "source": "Kích thước cũ", "count": 99}]}]})
    actual = boq.boq_workbook(result)
    monkeypatch.setattr(boq, "_quantity_detail_sheets", lambda *args: None)
    legacy = boq.boq_workbook(result)
    assert legacy.sheetnames == LEGACY_SHEETS
    for name in LEGACY_SHEETS:
        assert list(actual[name].values) == list(legacy[name].values)
        assert actual[name].freeze_panes == legacy[name].freeze_panes
        assert actual[name]["A1"].font.bold == legacy[name]["A1"].font.bold
    main_values = [r["Công tác / vị trí"] for r in records(actual[DETAIL_SHEETS[0]])]
    assert "Chưa có diễn giải chi tiết" in main_values and "Không tạo dòng giả" not in main_values
    assert actual[DETAIL_SHEETS[1]].max_row == 5
    legacy_row = records(actual[DETAIL_SHEETS[2]])[0]
    assert legacy_row["Giá trị số"] == 0 and legacy_row["Giá trị gốc (text)"] == "0.0"


def test_partial_known_negative_has_no_whole_scope_total():
    w = work([row(raw_quantity="2.5", sign=-1), row(row_id="unknown", raw_quantity=None, missing=["Thiếu chiều cao"])],
             legacy=0, scope=False)
    w = WorkItem.model_validate(w.model_dump() | {"status": "D", "missing": ["Phạm vi chưa đủ"]})
    wb = reopen([w])
    main = records(wb[DETAIL_SHEETS[0]])
    assert next(r for r in main if r["Công tác / vị trí"] == "Phần khối lượng đã biết")["Khối lượng"] == -2.5
    assert next(r for r in main if r["Công tác / vị trí"] == "Tổng toàn phạm vi (chưa đủ)")["Khối lượng"] is None
    assert any("Thiếu chiều cao" in (r["Thuyết minh"] or "") for r in main)
    compare = {r["Chỉ tiêu"]: r for r in records(wb[DETAIL_SHEETS[2]])}
    assert compare["Chênh raw − legacy"]["Giá trị gốc (text)"] == "-2.5"
    assert compare["Tổng raw toàn phạm vi"]["Giá trị gốc (text)"] is None


def test_reference_union_and_complete_negative_not_clamped():
    w = work([row(raw_quantity="3", sign=-1), row(row_id="union", raw_quantity="0.5", method="union"),
              row(row_id="reference", raw_quantity="999", role="reference")], legacy=0)
    wb = reopen([w])
    trace = records(wb[DETAIL_SHEETS[1]])
    assert trace[2]["Lượng tuyệt đối gốc (text)"] == "999"
    assert trace[2]["Đóng góp có dấu (text)"] is None
    main = records(wb[DETAIL_SHEETS[0]])
    assert next(r for r in main if r["Cộng / trừ"] == "Tham khảo")["Khối lượng"] is None
    assert next(r for r in main if r["Công tác / vị trí"] == "Tổng toàn phạm vi")["Khối lượng"] == -2.5


@pytest.mark.parametrize("raw,scope,missing,expected", [("0", True, [], 0), (None, False, ["Chưa đo"], None)])
def test_zero_and_unknown_remain_distinct(raw, scope, missing, expected):
    wb = reopen([work([row(raw_quantity=raw, missing=missing)], scope=scope)])
    comparison = {r["Chỉ tiêu"]: r for r in records(wb[DETAIL_SHEETS[2]])}
    assert comparison["Phần biết raw"]["Giá trị số"] == expected
    assert comparison["Tổng raw toàn phạm vi"]["Giá trị số"] == expected
    assert comparison["Phần biết raw"]["Giá trị gốc (text)"] == raw


@pytest.mark.parametrize("raw", ["1234567890123456", "0.123456789012345678901234567890123456", "1e308", "1e-308"])
def test_precision_retains_exact_raw_text(raw):
    wb = reopen([work([row(raw_quantity=raw)])])
    main = next(r for r in records(wb[DETAIL_SHEETS[0]]) if r["Công tác / vị trí"] == "Cấu kiện thử")
    assert main["Khối lượng"] is None and "precision" in main["Thuyết minh"]
    trace = records(wb[DETAIL_SHEETS[1]])[0]
    assert trace["Lượng tuyệt đối gốc (text)"] == row(raw_quantity=raw).raw_quantity
    assert trace["Đóng góp có dấu (text)"] == row(raw_quantity=raw).raw_quantity
    assert wb[DETAIL_SHEETS[1]]["H6"].data_type == "s"


@pytest.mark.parametrize("text", ["=1+1", "+SUM(1,2)", "-1+2", "@SUM(1,2)"])
def test_labels_sources_and_expression_are_literal_text(text):
    w = work([row(label=text, group=text, sources=[text], expression=text)], variant=text)
    w = WorkItem.model_validate(w.model_dump() | {"name": text})
    wb = reopen([w])
    trace = records(wb[DETAIL_SHEETS[1]])[0]
    assert trace["Nguồn"] == text and trace["Diễn giải (text)"] == text
    assert wb[DETAIL_SHEETS[1]]["P6"].data_type == "s"
    assert not [c.coordinate for name in DETAIL_SHEETS for row_cells in wb[name] for c in row_cells if c.data_type == "f"]


def test_nine_work_items_do_not_invent_raw_group_total():
    wb = reopen([work([row(raw_quantity="0.1259")], legacy=.126, element=f"Cấu kiện {i}") for i in range(9)])
    comparison = records(wb[DETAIL_SHEETS[2]])
    assert len(comparison) == 9 * 4
    assert len({r["Công tác trong kết quả"] for r in comparison}) == 9
    assert sum(r["Chỉ tiêu"] == "Tổng raw toàn phạm vi" for r in comparison) == 9
    assert "Chưa có tổng raw nhóm" in wb[DETAIL_SHEETS[0]]["A4"].value
    assert len(records(wb[DETAIL_SHEETS[1]])) == 9


def test_empty_result_and_optimizer_payload_unchanged():
    result = RoughResult(works=[])
    before = boq.export_for_optimizer(result)
    wb = load_workbook(BytesIO(boq.boq_bytes(result)))
    assert wb.sheetnames == LEGACY_SHEETS + DETAIL_SHEETS
    assert wb[DETAIL_SHEETS[1]].max_row == 5
    assert boq.export_for_optimizer(result) == before


def test_snapshot_groups_links_coverage_and_precision_after_reopen(monkeypatch):
    from optimat.rough import quantity_summary, takeoff
    from optimat.rough.models import QuantityGroupingContext

    raw = "0.1234567890123456789"
    works = [
        work([row(raw_quantity=raw), row(row_id="geometry", role="reference", raw_quantity="90")],
             variant="=thiết kế", stage="mong", plan="Tầng 2", legacy=.123),
        work([row(raw_quantity=None, missing=["Thiếu chiều cao"])], scope=False, legacy=None,
             variant="=thiết kế", stage="mong", plan="Tầng 1"),
        work([row(raw_quantity="0")], variant="Riêng", legacy=0),
        work([row(raw_quantity="2", sign=-1)], variant="Trừ", legacy=-2),
        WorkItem(code="DAM", name="Dầm khác đơn vị", unit="m", quantity=37),
    ]
    context = QuantityGroupingContext(lean_concrete_grade="M100", concrete_supply="Trộn tại chỗ")
    summary = quantity_summary.build_quantity_summary(works, context)
    result = RoughResult(works=works, quantity_summary=summary)
    def forbidden(*args, **kwargs):
        pytest.fail("Exporter gọi lại producer, builder hoặc pricing")

    for module, name in [(quantity_summary, "build_quantity_summary"), (takeoff, "build_quantity_summary"),
                         (takeoff, "compute_rough"), (takeoff, "attach_prices")]:
        monkeypatch.setattr(module, name, forbidden)
    wb = load_workbook(BytesIO(boq.boq_bytes(result)))
    assert wb.sheetnames == LEGACY_SHEETS + DETAIL_SHEETS
    main, compare = wb[DETAIL_SHEETS[0]], wb[DETAIL_SHEETS[2]]
    assert summary.quantity_snapshot_hash in main["A4"].value
    r = list(compare.values)
    groups = summary.groups
    assert len(groups) == 4
    for group in groups:
        lines = [v for v in r if v[0] == group.group_id]
        known, total, coverage = lines[:3]
        assert (known[6], total[6]) == (group.known_part_raw, group.total_raw)
        assert total[2] == ("Quy cách tương thích" if group.compatibility == "resolved" else "Tách riêng: chưa đủ căn cứ gộp")
        assert total[3] == group.key.unit
        assert [v[1] for v in lines if v[4] == "Thành viên"] == group.member_work_keys
        assert coverage[8] == group.coverage.model_dump_json()
    main_rows = records(main)
    totals = [x for x in main_rows if x["Cộng / trừ"] == "Tổng nhóm"]
    assert len(totals) == 2 * len(groups)
    assert totals[0]["Khối lượng"] == raw and totals[1]["Khối lượng"] is None
    assert "Thiếu chiều cao" in totals[1]["Thuyết minh"]
    assert "1 chưa biết" in totals[1]["Thuyết minh"]
    trace = wb[DETAIL_SHEETS[1]]
    membership = {member: g.group_id for g in groups for member in g.member_work_keys}
    for i, rec in enumerate(records(trace), 6):
        member = rec["Công tác trong kết quả"]
        assert rec["Mã nhóm đối soát"] == membership[member]
        group_cell = main[trace.cell(i, 18).hyperlink.target.split("!")[-1]]
        assert "Mã công tác:" in main.cell(group_cell.row, 11).value
        if rec["Vai trò"] == "Thành viên":
            heading = main[trace.cell(i, 1).hyperlink.target.split("!")[-1]]
            assert main.cell(heading.row, 12).hyperlink.target.endswith("!" + group_cell.coordinate)
            continue
        assert rec["Nhóm"] == "Nhóm thử"
        if member == "w:1":
            assert rec["Lý do thiếu theo nhóm"] == "Thiếu chiều cao"
    partial = [v for v in r if v[0] == groups[0].group_id]
    assert partial[0][5:7] == (None, raw) and partial[1][5:7] == (None, None)
    assert groups[0].coverage.reference_rows == 1
    assert [g.total_raw for g in groups[1:]] == ["0", "-2", None]
    for index, values in enumerate(r, 1):
        if values[4] not in ("Thiếu dữ liệu", "Thành viên"):
            continue
        target = compare.cell(index, 2).hyperlink.target.split("!")[-1]
        work_index = int(values[1].split(":")[1])
        if values[2] is None:
            assert main[target].value.startswith(works[work_index].name)
            assert main.cell(main[target].row, 1).value == work_index + 1
        else:
            assert values[1:3] == ("w:1", "r1")
            assert "Thiếu chiều cao" in main.cell(main[target].row, 11).value
    assert all(c.data_type != "f" for sh in DETAIL_SHEETS for cells in wb[sh] for c in cells)


@pytest.mark.parametrize("raw,sign,expected", [("0.0000000000000001", 1, 1e-16),
                                              ("0.0000000000000001", -1, -1e-16),
                                              ("0", 1, 0), (None, 1, None)])
def test_small_excel_numbers_remain_distinct_from_zero_and_missing(raw, sign, expected):
    w = work([row(raw_quantity=raw, sign=sign, missing=["Cần số đo"] if raw is None else [])],
             legacy=expected, scope=raw is not None)
    wb = reopen([w])
    cell = next(cells[8] for cells in wb[DETAIL_SHEETS[0]].iter_rows() if cells[1].value == "Cấu kiện thử")
    assert cell.value == expected
    assert ("E+" in cell.number_format) == (expected in (1e-16, -1e-16))
    assert wb[DETAIL_SHEETS[1]]["H6"].value == w.quantity_detail.rows[0].raw_quantity


@pytest.mark.parametrize("levels,quantity,component_scope,pending", [
    (["aggregate"], "1/1", "Chưa đủ chi tiết cấu kiện", 0),
    (["components", "aggregate", "unavailable", None], "2/4", "Chưa đủ chi tiết cấu kiện", 4),
    (["components"], "1/1", "Đủ chi tiết cấu kiện", 0),
    ([], "0/0", "Không có công tác để đánh giá", 0),
])
def test_excel_coverage_in_vietnamese(levels, quantity, component_scope, pending):
    from optimat.rough import quantity_summary
    from optimat.rough.models import QuantityGroupingContext

    works = []
    for level in levels:
        available = level in ("components", "aggregate")
        detail = summarize([row()] if available else [], "m³", 1 if available else None,
                           scope_complete=available, detail_level=level) if level else None
        works.append(WorkItem(code="BE_TONG_LOT", name="Lót móng", unit="m³", stage="mong",
                              quantity=1 if available else None, quantity_detail=detail))
    context = QuantityGroupingContext(lean_concrete_grade=None if pending else "M100", concrete_supply="Trộn tại chỗ")
    wb = reopen(works, quantity_summary=quantity_summary.build_quantity_summary(works, context))
    main, _, compare = (wb[name] for name in DETAIL_SHEETS)
    main_text = next(r[10] for r in main.values if r[1] == "Tổng khối lượng theo nhóm")
    compare_text = next(r[1] for r in compare.values if r[0] == "Phạm vi toàn bộ")
    for text in (main_text, compare_text):
        for phrase in [f"{quantity} công tác đủ lượng", component_scope,
                       f"Theo cấu kiện: {levels.count('components')}", f"chỉ có tổng: {levels.count('aggregate')}",
                       f"chi tiết chưa khả dụng: {levels.count('unavailable')}", f"chưa có diễn giải: {levels.count(None)}",
                       f"Chờ xác định quy cách để gộp: {pending} công tác"]:
            assert phrase in text
    expected_labels = {"components": "Chi tiết theo cấu kiện; đủ lượng toàn phạm vi",
                       "aggregate": "Chỉ có tổng; đủ lượng toàn phạm vi",
                       "unavailable": "Chưa có chi tiết khả dụng; chưa đủ lượng toàn phạm vi",
                       None: "Chưa có diễn giải chi tiết"}
    for index, level in enumerate(levels):
        assert any(r[0] == f"w:{index}" and r[7] == expected_labels[level] for r in compare.values)
