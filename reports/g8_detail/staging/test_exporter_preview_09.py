"""Pure serialization staging09; không HTTP/DB/producer hoặc Excel native."""
import copy
import importlib.util
import json
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

PATH = Path(__file__).with_name("exporter_preview_09.py")
SPEC = importlib.util.spec_from_file_location("exporter_preview_09", PATH)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


@pytest.fixture
def fixture():
    return json.loads(exporter.FIXTURE.read_text(encoding="utf-8"))


def reopen(data):
    buffer = BytesIO()
    exporter.preview_workbook(data).save(buffer)
    buffer.seek(0)
    return load_workbook(buffer, data_only=False)


def test_m1_nine_contributions_and_groups(fixture):
    wb = reopen(fixture)
    ws, trace = wb["Tiên lượng"], wb["Truy vết"]
    assert ws.max_column == 12
    assert [trace.cell(r, 2).value for r in range(6, 15)] == [r["row_id"] for r in fixture["rows"]]
    groups = [row for row in ws if row[1].value in {"Đài móng", "Giằng móng", "Dầm tường"}]
    assert len(groups) == 3 and all(row[8].value is None for row in groups)
    amounts = [Decimal(trace.cell(r, 8).value) for r in range(6, 15)]
    assert sum(amounts) == Decimal("3.2515")
    assert [str(v) for v in amounts] == [r["raw_quantity"] for r in fixture["rows"]]
    assert ws.cell(8, 3).value == 2
    assert [ws.cell(8, c).value for c in (4, 5, 6)] == [0.75, 2.15, 0.1]
    assert ws.cell(8, 7).value is None
    assert ws.cell(8, 9).value == 0.3225
    assert ws.cell(ws.max_row, 9).value == 3.2515
    assert ws.cell(8, 12).hyperlink.target == "#'Truy vết'!A6"
    assert trace.cell(6, 1).hyperlink.target == "#'Tiên lượng'!B8"
    assert "9.930000000000001" in trace.cell(9, 10).value
    assert "3.6699999999999995" in trace.cell(10, 10).value


def test_materials_raw_cached_and_signed_delta(fixture):
    wb = reopen(fixture)
    ws = wb["Vật tư tham chiếu"]
    expected = ["-0.0000125", "0.0000282125", "0.000005475", "-0.000025"]
    for number, material in enumerate(fixture["materials"], 6):
        assert ws.cell(number, 1).value == material["source_material_code"]
        assert ws.cell(number, 5).value == float(material["quantity_from_raw"])
        assert ws.cell(number, 6).value == float(material["stored_quantity"])
        assert ws.cell(number, 7).value == float(expected[number - 6])
    raw_values = [row[2].value for row in wb["Đối soát"]]
    assert all(m["quantity_from_raw"] in raw_values and m["stored_quantity"] in raw_values for m in fixture["materials"])
    assert all(d in raw_values for d in expected)


@pytest.mark.parametrize("raw,sign,role,expected", [
    ("0", 1, "contribution", 0), (None, 1, "contribution", None),
    ("7.25", -1, "contribution", -7.25), ("99", 1, "reference", None),
])
def test_zero_null_sign_reference(fixture, raw, sign, role, expected):
    data = copy.deepcopy(fixture)
    row = data["rows"][0]
    row.update(raw_quantity=raw, sign=sign, role=role, missing=["Thiếu chiều cao"] if raw is None else [])
    row["dimensions"].update(count=100, repetitions=9)
    row["factors"] = [{"name": "Hệ số nguồn", "value": "2", "source": "Ô gốc", "unit": "1", "meaning": "Hệ số đã có trong lượng"}]
    known = exporter.signed_text(row)
    data.update(rows=[row], total_raw=None, known_part_raw=known, complete=False, scope_complete=False)
    wb = reopen(data)
    assert wb["Tiên lượng"].cell(8, 9).value == expected
    assert wb["Truy vết"].cell(6, 7).value == raw
    assert wb["Tiên lượng"].cell(wb["Tiên lượng"].max_row, 9).value is None
    if raw is None:
        assert "Thiếu chiều cao" in wb["Tiên lượng"].cell(8, 11).value
    if role == "reference":
        assert wb["Truy vết"].cell(6, 8).value is None


@pytest.mark.parametrize("raw", ["1234567890123456", "0.1234567890123456", "1e308", "1e-308"])
def test_precision_keeps_raw_text(fixture, raw):
    data = copy.deepcopy(fixture)
    data["rows"] = [data["rows"][0]]
    data["rows"][0]["raw_quantity"] = raw
    wb = reopen(data)
    assert wb["Tiên lượng"].cell(8, 9).value is None
    assert wb["Truy vết"].cell(6, 7).value == raw
    assert wb["Truy vết"].cell(6, 7).data_type == "s"
    assert "precision" in wb["Tiên lượng"].cell(8, 11).value


@pytest.mark.parametrize("prefix", ["=1+1", "+SUM(1,2)", "-1+2", "@SUM(1,2)"])
def test_untrusted_text_never_becomes_formula(fixture, prefix):
    data = copy.deepcopy(fixture)
    data["work_name"] = prefix
    data["rows"] = [data["rows"][0]]
    row = data["rows"][0]
    row.update(label=prefix, group=prefix, expression=prefix, sources=[prefix], missing=[prefix])
    wb = reopen(data)
    assert wb["Tiên lượng"].cell(8, 2).value == prefix
    assert wb["Tiên lượng"].cell(8, 2).data_type == "s"
    assert wb["Truy vết"].cell(6, 15).value == prefix
    assert not [c.coordinate for ws in wb for row in ws for c in row if c.data_type == "f"]


def test_no_detail_no_fake_rows(fixture):
    fixture.update(rows=[], total_raw=None)
    wb = reopen(fixture)
    assert wb["Truy vết"].max_row == 5
    assert any(row[1].value == "Chưa có diễn giải chi tiết" for row in wb["Tiên lượng"])


def test_legacy_and_negative_total_are_payload_values(fixture):
    fixture["rows"] = [fixture["rows"][0]]
    fixture["rows"][0].update(raw_quantity="2.5", sign=-1)
    fixture.update(total_raw="-2.5", known_part_raw="-2.5", legacy_quantity="3.251", legacy_delta="-5.751",
                   complete=True, scope_complete=True)
    wb = reopen(fixture)
    compare = {row[0].value: row[2].value for row in wb["Đối soát"] if row[0].value}
    assert compare["Lượng legacy sản phẩm"] == "3.251"
    assert compare["Chênh raw − legacy"] == "-5.751"
    assert wb["Tiên lượng"].cell(wb["Tiên lượng"].max_row, 9).value == -2.5


def test_partial_negative_known_part_has_no_total(fixture):
    fixture["rows"] = [fixture["rows"][0], copy.deepcopy(fixture["rows"][1])]
    fixture["rows"][0].update(raw_quantity="2.5", sign=-1)
    fixture["rows"][1].update(raw_quantity=None, missing=["Thiếu chiều cao"])
    fixture.update(total_raw=None, known_part_raw="-2.5", complete=False, scope_complete=False,
                   legacy_quantity="3.251", legacy_delta="-5.751")
    wb = reopen(fixture)
    ws = wb["Tiên lượng"]
    assert ws.cell(ws.max_row, 9).value is None
    assert ws.cell(ws.max_row - 1, 2).value == "Phần khối lượng đã biết"
    assert ws.cell(ws.max_row - 1, 9).value == -2.5
    assert wb["Đối soát"].cell(10, 3).value == "-5.751"


@pytest.mark.parametrize("mutation", [
    {"complete": False, "total_raw": "3.2515"},
    {"complete": True, "scope_complete": False},
    {"complete": True, "total_raw": "99"},
    {"known_part_raw": "99"}, {"legacy_delta": "99"},
])
def test_invalid_ledger_payload_rejected(fixture, mutation):
    fixture.update(complete=True, scope_complete=True, known_part_raw="3.2515", total_raw="3.2515",
                   legacy_quantity="3.251", legacy_delta="0.0005")
    fixture.update(mutation)
    with pytest.raises(ValueError):
        exporter.preview_workbook(fixture)


def test_rounding_examples_do_not_fabricate_legacy(fixture):
    wb = reopen(fixture)
    values = {row[0].value: row[2].value for row in wb["Đối soát"] if row[0].value}
    assert values["Minh họa round3 từng dòng rồi cộng"] == "3.251"
    assert values["Minh họa round3 sau tổng"] == "3.252"
    assert values["Raw − minh họa round3 từng dòng rồi cộng"] == "0.0005"
    assert values["Raw − minh họa round3 sau tổng"] == "-0.0005"
    assert values["Lượng legacy sản phẩm"] is None


@pytest.mark.parametrize("raw", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_rejected(raw):
    with pytest.raises(ValueError, match="hữu hạn"):
        exporter.excel_number(raw)
