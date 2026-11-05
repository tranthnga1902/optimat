"""S07: bảng thống kê cốt thép -> kg có nguồn; không nhầm với thép ước theo hàm lượng."""
from io import BytesIO

import pytest

from optimat.drawing.dxf_reader import Drawing, TextItem
from optimat.rough.materials import STEEL_NAME
from optimat.rough.models import WORKS, ProjectParams, WorkItem
from optimat.rough.rebar import RebarRow, _num, element_code, read_rebar_schedules, unit_mass
from optimat.rough.steel import steel_works
from optimat.rough.takeoff import RoughRequest, compute_rough

HEADER = ["CẤU KIỆN", "SỐ HIỆU", "HÌNH DẠNG", "ĐƯỜNG KÍNH (mm)", "CHIỀU DÀI 1 THANH (mm)", "SỐ LƯỢNG", "KHỐI LƯỢNG (kg)"]
ROWS = [["C1", "1", "thẳng", "Ø16", "3200", "32", "161,79"],
        ["", "2", "đai", "Ø8", "1100", "100", "43,45"],          # ô cấu kiện gộp: lấy C1 của dòng trên
        ["DẦM D1", "1", "", "Ø18", "5.000", "8", "0,08"],       # bảng ghi tấn thay kg: cảnh báo lệch 1000 lần
        ["X9", "1", "", "Ø12", "2000", "10", ""],               # cấu kiện chưa có quy ước
        ["S1", "1", "", "Ø10", "3.2", "40", ""],                # chiều dài ghi theo m trong cột mm: nghi sai đơn vị
        ["TỔNG", "", "", "", "", "", "300"],
        ["M1", "1", "", "Ø12", "1500", "4", ""]]                # sau dòng TỔNG: không đọc


def _table(x0, y0, title="BẢNG THỐNG KÊ CỐT THÉP"):
    t = [TextItem(title, x0, y0, "TK", "unicode", 100)]
    t += [TextItem(h, x0 + i * 1000, y0 - 500, "TK", "unicode", 100) for i, h in enumerate(HEADER)]
    for r, row in enumerate(ROWS):
        t += [TextItem(c, x0 + i * 1000, y0 - 700 - r * 150, "TK", "unicode", 100) for i, c in enumerate(row) if c]
    return t


def _drawing(texts):
    return Drawing(segments=[], texts=texts, blocks=[], hatches=[], layers=["TK"], layer_classes={}, unit_scale=1.0, warnings=[])


def test_unit_mass_table_has_source():
    m = unit_mass()
    assert m[16][0] == pytest.approx(1.58) and m[8][0] == pytest.approx(0.395)
    assert all(src.startswith("TCVN 1651") for _, src in m.values())


def test_number_and_element_parsing():
    assert _num("5.000") == 5000 and _num("1,58") == 1.58 and _num("Ø16") == 16 and _num("") is None
    assert element_code("C1") == "COT" and element_code("DẦM D1") == "DAM" and element_code("SÀN") == "SAN"
    assert element_code("GT2") == "GIANG_TUONG" and element_code("SN1") == "SE_NO" and element_code("X9") is None


@pytest.mark.parametrize("text,expected", [("1.200,5", 1200.5), ("1,200.5", 1200.5),
                                          ("1.234.567,89", 1234567.89), ("1,234,567.89", 1234567.89)])
def test_number_mixed_vietnamese_separators(text, expected):
    assert _num(text) == expected


@pytest.mark.parametrize("text", ["12.00,5", "1,20.5", "1.200,", "1,200.", "1.200,5.0", "1,200.5,0"])
def test_number_mixed_invalid_groups_stay_blank(text):
    assert _num(text) is None


@pytest.mark.parametrize("text,expected", [("1200", 1200), ("", None), ("Ø16", 16), ("1,58", 1.58),
                                          ("5.000", 5000), ("3.200", 3200), ("1.200", 1200),
                                          ("1,200", 1.2), ("3.2", 3.2)])
def test_number_single_separator_contract(text, expected):
    assert _num(text) == expected


@pytest.mark.parametrize("length,unit,quantity,recorded,expected_mm,expected_kg", [
    ("1.200,5", "mm", "1.000,0", "1.896,79", 1200.5, 1896.79),
    ("1,200.5", "mm", "1,000.0", "1,896.79", 1200.5, 1896.79),
    ("0.001,5", "m", "1.000,0", "2.370,00", 1500, 2370),
    ("0,001.5", "m", "1,000.0", "2,370.00", 1500, 2370),
    ("1,200.5", "m", "1.000,0", "1.896,79", None, 1896.79),
])
def test_schedule_mixed_separators_preserves_units_and_evidence(length, unit, quantity, recorded, expected_mm, expected_kg):
    texts = _table(0, 1000)
    for t in texts:
        if t.text == HEADER[4]:
            t.text = f"CHIỀU DÀI 1 THANH ({unit})"
        elif t.y == 300 and t.x in (4000, 5000, 6000):
            t.text = {4000: length, 5000: quantity, 6000: recorded}[t.x]
    rows, _ = read_rebar_schedules(_drawing(texts))
    row = rows[0]
    assert row.total_bars == 1000 and row.schedule_kg == expected_kg
    assert all(value in row.evidence for value in (length, quantity, recorded))
    assert row.cut_length_mm == expected_mm
    if expected_mm is not None:
        assert row.kg == pytest.approx(expected_kg) and not row.missing and not row.notes
    else:
        assert row.cut_length_mm is None and row.kg is None
        assert any("1.2005e+06 mm" in m and "sai đơn vị" in m for m in row.missing)


@pytest.mark.parametrize("length", ["12.00,5", "1,20.5"])
def test_schedule_invalid_mixed_length_keeps_row_and_missing(length):
    texts = _table(0, 1000)
    for t in texts:
        if t.y == 300 and t.x == 4000:
            t.text = length
    rows, _ = read_rebar_schedules(_drawing(texts))
    assert len(rows) == 5 and rows[0].dia_mm == 16
    assert rows[0].cut_length_mm is None and rows[0].kg is None
    assert any("chiều dài cắt" in m for m in rows[0].missing)
    assert length in rows[0].evidence


@pytest.mark.xfail(strict=True, reason="Bảng lặp không có số hiệu đang được cộng hai lần")
def test_duplicate_table_without_mark_counted_once():
    title = "BẢNG THỐNG KÊ CỐT THÉP TOÀN BỘ CẤU KIỆN TẦNG 1 (TỔNG TOÀN TẦNG)"
    texts = _table(0, 1000, title) + _table(0, -5000, title)
    for t in texts:
        if t.text in {"1", "2"}:
            t.text = ""
    rows, _ = read_rebar_schedules(_drawing(texts))
    assert len(rows) == 5


def test_read_schedule_and_kg():
    rows, warnings = read_rebar_schedules(_drawing(_table(0, 1000)))
    assert [r.element for r in rows] == ["C1", "C1", "DẦM D1", "X9", "S1"]       # dừng ở dòng TỔNG
    c1 = rows[0]
    assert c1.kg == pytest.approx(32 * 3.2 * 1.58, abs=0.01) and c1.kg_per_m_source.startswith("TCVN")
    assert c1.evidence.startswith("BẢNG THỐNG KÊ CỐT THÉP, dòng 1") and not c1.notes
    assert rows[1].element_code == "COT" and rows[1].kg == pytest.approx(43.45, abs=0.01)
    assert rows[2].kg == pytest.approx(80) and any("1000 lần" in n for n in rows[2].notes)
    assert rows[3].element_code is None and any("Not supported" in n for n in rows[3].notes)
    assert rows[4].kg is None and any("sai đơn vị" in m for m in rows[4].missing)
    assert any("neo, nối" in w for w in warnings)


def test_duplicate_table_counted_once():
    title = "BẢNG THỐNG KÊ CỐT THÉP TOÀN BỘ CẤU KIỆN TẦNG 1 (TỔNG TOÀN TẦNG)"
    rows, warnings = read_rebar_schedules(_drawing(_table(0, 1000, title) + _table(0, -5000, title)))
    assert len(rows) == 5 and any("trùng hệt" in w for w in warnings)


def _scoped_table(y, level="1", records=None, title=None):
    """Bảng SYNTHETIC: toàn bộ số thanh trong phạm vi đã ghi, không phải đáp án build."""
    title = title or f"BẢNG THỐNG KÊ CỐT THÉP DẦM TẦNG {level} (TỔNG TOÀN TẦNG)"
    records = records if records is not None else [["D1", "1", "thẳng", "Ø16", "2000", "10", "31,60"]]
    texts = [TextItem(title, 0, y, "TK", "unicode", 100)]
    texts += [TextItem(h, i * 1000, y - 500, "TK", "unicode", 100) for i, h in enumerate(HEADER)]
    for j, record in enumerate(records + [["TỔNG", "", "", "", "", "", ""]]):
        texts += [TextItem(value, i * 1000, y - 700 - j * 150, "TK", "unicode", 100)
                  for i, value in enumerate(record) if value]
    return texts


@pytest.mark.parametrize("mark", ["1", ""])
def test_scoped_whole_table_copy_keeps_one_with_source(mark):
    records = [["D1", mark, "thẳng", "Ø16", "2000", "10", "31,60"]]
    rows, warnings = read_rebar_schedules(_drawing(_scoped_table(1000, records=records)
                                                + _scoped_table(-5000, records=records)))
    assert len(rows) == 1 and rows[0].kg == pytest.approx(31.6)
    assert rows[0].scope.levels == (1,) and rows[0].scope.quantity_basis == "total"
    assert rows[0].scope_source == "title" and "TẦNG 1" in rows[0].scope_evidence
    assert rows[0].table_id and not rows[0].missing
    assert any("trùng hệt" in w and "giữ" in w and "table:" in w for w in warnings)


def test_independent_levels_same_content_both_survive():
    rows, warnings = read_rebar_schedules(_drawing(_scoped_table(1000, "1") + _scoped_table(-5000, "2")))
    assert len(rows) == 2 and sum(r.kg for r in rows) == pytest.approx(63.2)
    assert {r.scope.levels for r in rows} == {(1,), (2,)}
    assert len({r.table_id for r in rows}) == 2 and all(r.evidence for r in rows)
    assert not any(r.missing for r in rows) and not any("trùng hệt" in w for w in warnings)


def test_whole_table_comparison_preserves_repeated_rows():
    record = ["D1", "1", "thẳng", "Ø16", "2000", "10", "31,60"]
    texts = _scoped_table(1000, records=[record, record]) + _scoped_table(-5000, records=[record, record])
    rows, _ = read_rebar_schedules(_drawing(texts))
    assert len(rows) == 2 and sum(r.kg for r in rows) == pytest.approx(63.2)


@pytest.mark.parametrize("second", [
    ["D1", "1", "thẳng", "Ø16", "1000", "20", "31,60"],
    ["D1", "1", "uốn", "Ø16", "2000", "10", "31,60"],
])
def test_equal_kg_or_changed_shape_not_proof_of_copy(second):
    rows, warnings = read_rebar_schedules(_drawing(_scoped_table(1000)
                                                + _scoped_table(-5000, records=[second])))
    assert len(rows) == 2 and sum(r.kg for r in rows) == pytest.approx(63.2)
    assert all(any("chờ xác nhận" in m for m in r.missing) for r in rows)
    assert any("khác nội dung" in w for w in warnings)


@pytest.mark.parametrize("marked", [True, False])
def test_legacy_unscoped_tables_are_not_deduplicated(marked):
    texts = _table(0, 1000) + _table(0, -5000)
    if not marked:
        for t in texts:
            if t.text in {"1", "2"}:
                t.text = ""
    rows, warnings = read_rebar_schedules(_drawing(texts))
    assert len(rows) == 10 and all(r.scope is None for r in rows)
    assert all(any("chờ xác nhận" in m for m in r.missing) for r in rows)
    assert any("nghi lặp" in w for w in warnings)


@pytest.mark.parametrize("title", [
    "BẢNG THỐNG KÊ CỐT THÉP", "BẢNG THỐNG KÊ CỐT THÉP DẦM TẦNG 1",
    "BẢNG THỐNG KÊ CỐT THÉP DẦM TẦNG 1 (MỘT MẪU)",
    "BẢNG THỐNG KÊ CỐT THÉP DẦM TẦNG 1,2 (TỔNG TOÀN TẦNG)",
    "BẢNG THỐNG KÊ CỐT THÉP CỘT TẦNG 1 (TỔNG TOÀN TẦNG)",
])
def test_ambiguous_or_conflicting_title_never_establishes_scope(title):
    rows, _ = read_rebar_schedules(_drawing(_scoped_table(1000, title=title)
                                          + _scoped_table(-5000, title=title)))
    assert len(rows) == 2 and all(r.scope is None and r.missing for r in rows)


def test_multi_level_total_is_not_multiplied_or_merged_with_one_level():
    title = "BẢNG THỐNG KÊ CỐT THÉP DẦM TẦNG 1,2 (TỔNG PHẠM VI)"
    rows, _ = read_rebar_schedules(_drawing(_scoped_table(1000, title=title)
                                          + _scoped_table(-5000, title=title)))
    assert len(rows) == 1 and rows[0].kg == pytest.approx(31.6) and rows[0].scope.levels == (1, 2)
    rows, _ = read_rebar_schedules(_drawing(_scoped_table(1000, title=title) + _scoped_table(-5000)))
    assert len(rows) == 2 and all(r.missing for r in rows)


def test_partial_table_overlap_does_not_remove_rows():
    a = ["D1", "1", "thẳng", "Ø16", "2000", "10", "31,60"]
    b = ["D2", "2", "thẳng", "Ø16", "1000", "10", "15,80"]
    rows, _ = read_rebar_schedules(_drawing(_scoped_table(1000, records=[a, b]) + _scoped_table(-5000)))
    assert len(rows) == 3 and all(r.missing for r in rows)


def test_unreadable_cells_not_compared_as_equal_none():
    a = ["D1", "1", "thẳng", "Ø16", "12.00,5", "10", ""]
    b = ["D1", "1", "thẳng", "Ø16", "1,20.5", "10", ""]
    rows, _ = read_rebar_schedules(_drawing(_scoped_table(1000, records=[a])
                                          + _scoped_table(-5000, records=[b])))
    assert len(rows) == 2 and all(r.kg is None and r.cut_length_mm is None for r in rows)
    assert rows[0].raw_cells["chieu_dai"] != rows[1].raw_cells["chieu_dai"]
    assert all(any("chiều dài cắt" in m for m in r.missing) for r in rows)


def test_scope_comparison_is_local_and_repeatable():
    texts = _scoped_table(1000) + _scoped_table(-5000) + _scoped_table(-11000, "2")
    for ordered in (texts, list(reversed(texts))):
        for _ in range(2):
            rows, _ = read_rebar_schedules(_drawing(ordered))
            assert len(rows) == 2 and sum(r.kg for r in rows) == pytest.approx(63.2)
    first, _ = read_rebar_schedules(_drawing(_scoped_table(1000)))
    second, _ = read_rebar_schedules(_drawing(_scoped_table(1000)))
    assert len(first + second) == 2


def test_whole_table_content_ignores_row_order_but_keeps_raw_cells():
    a = ["D1", "1", "thẳng", "Ø16", "2000", "10", "31,60"]
    b = ["D2", "2", "uốn", "Ø16", "1000", "10", "15,80"]
    rows, _ = read_rebar_schedules(_drawing(_scoped_table(1000, records=[a, b])
                                          + _scoped_table(-5000, records=[b, a])))
    assert len(rows) == 2 and sum(r.kg for r in rows) == pytest.approx(47.4)
    copied = RebarRow.model_validate_json(rows[0].model_dump_json())
    assert copied.raw_cells == rows[0].raw_cells and copied.raw_cells["_length_unit"] == "mm"
    assert copied.scope == rows[0].scope and copied.scope_evidence == rows[0].scope_evidence
    assert copied.table_id == rows[0].table_id


def test_legacy_rebar_row_roundtrip_needs_no_scope():
    payload = dict(table="Bảng cũ", row=1, element="D1", element_code="DAM", kg=31.6,
                   evidence="nguồn cũ", missing=["lý do cũ"])
    row = RebarRow(**payload)
    copied = RebarRow(**row.model_dump())
    assert all(getattr(copied, key) == value for key, value in payload.items())
    assert copied.scope is None and copied.table_id == "" and copied.raw_cells == {}


def test_schedule_steel_separate_from_ratio():
    rows, _ = read_rebar_schedules(_drawing(_table(0, 1000)))
    res = compute_rough(RoughRequest(plans=[], params=ProjectParams(steel_kg_per_m3={"COT": 150}), rebar=rows))
    steel = [w for w in res.works if w.code == "COT_THEP"]
    cot = next(w for w in steel if w.steel_element == "COT")
    assert cot.basis == "bang_thong_ke" and cot.quantity == pytest.approx((161.79 + 43.45) / 1000, abs=1e-3)
    assert len(cot.evidence) == 2 and not any(w.basis == "ham_luong" for w in steel)
    x9 = next(w for w in steel if "X9" in (w.element or ""))
    assert x9.basis == "not_supported" and x9.quantity is None
    san = next(w for w in steel if w.steel_element == "SAN")
    assert san.quantity is None and san.missing                      # dòng sai đơn vị: để trống kèm lý do
    line = next(m for m in res.materials if m.name == STEEL_NAME)
    assert len(line.uses) == len([w for w in steel if w.basis != "not_supported"])   # Not supported không sinh vật liệu


def test_no_schedule_leaves_steel_blank():
    works = [WorkItem(code="COT", name=WORKS["COT"][0], unit="m³", quantity=2.0, plan="T1")]
    out, _ = steel_works(works, ProjectParams())
    assert out[0].quantity is None and "bảng thống kê thép cột" in out[0].missing and out[0].basis is None
    out, warnings = steel_works(works, ProjectParams(steel_kg_per_m3={"COT": 150}))
    assert out[0].basis == "ham_luong" and any("cần review" in w for w in warnings)


def test_boq_excel_sheets():
    from openpyxl import load_workbook

    from optimat.rough.boq import boq_bytes
    rows, _ = read_rebar_schedules(_drawing(_table(0, 1000)))
    req = RoughRequest(plans=[], rebar=rows)
    wb = load_workbook(BytesIO(boq_bytes(compute_rough(req), req)))
    assert wb.sheetnames == ["Tổng hợp", "Theo tầng", "Theo cấu kiện", "Cốt thép", "Vật liệu", "Theo nhóm", "Theo loại", "Cảnh báo", "Phạm vi hỗ trợ"]
    assert "Trạng thái (A đọc / B suy / C tạm tính / D thiếu)" in [c.value for c in wb["Theo tầng"][1]]
    assert [c.value for c in wb["Theo tầng"][1]][-2:] == ["evidence", "missing_reason"]
    assert "formula" in [c.value for c in wb["Theo tầng"][1]]
    assert wb["Cốt thép"].max_row == 1 + len(rows)
