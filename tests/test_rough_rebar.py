"""S07: bảng thống kê cốt thép -> kg có nguồn; không nhầm với thép ước theo hàm lượng."""
from io import BytesIO

import pytest

from optimat.drawing.dxf_reader import Drawing, TextItem
from optimat.rough.materials import STEEL_NAME
from optimat.rough.models import WORKS, ProjectParams, WorkItem
from optimat.rough.rebar import _num, element_code, read_rebar_schedules, unit_mass
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


def _table(x0, y0):
    t = [TextItem("BẢNG THỐNG KÊ CỐT THÉP", x0, y0, "TK", "unicode", 100)]
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


@pytest.mark.xfail(strict=True, reason="Ô số có dấu phân cách nghìn và thập phân đang bị đọc thành None")
def test_number_mixed_vietnamese_separators():
    assert _num("1.200,5") == 1200.5


@pytest.mark.xfail(strict=True, reason="Bảng lặp không có số hiệu đang được cộng hai lần")
def test_duplicate_table_without_mark_counted_once():
    texts = _table(0, 1000) + _table(0, -5000)
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
    rows, warnings = read_rebar_schedules(_drawing(_table(0, 1000) + _table(0, -5000)))
    assert len(rows) == 5 and any("trùng hệt" in w for w in warnings)


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
    assert wb.sheetnames == ["Tổng hợp", "Theo tầng", "Theo cấu kiện", "Cốt thép", "Vật liệu", "Cảnh báo", "Phạm vi hỗ trợ"]
    assert [c.value for c in wb["Theo tầng"][1]][-3:] == ["formula", "evidence", "missing_reason"]
    assert wb["Cốt thép"].max_row == 1 + len(rows)
