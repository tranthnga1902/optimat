"""SYNTHETIC: không mượn header/số lượng của bảng thép bên cạnh."""
import pytest

from optimat.drawing.dxf_reader import Drawing, TextItem
from optimat.rough.rebar import collect_rebar_tables


def text(value, x, y):
    return TextItem(value, x, y, "TK", "unicode", 100)


def table(x, label, length, count, valid=True, multiline=False):
    out = [text(f"THỐNG KÊ THÉP {label}", x, 2000)]
    headers = ["CẤU KIỆN", "ĐƯỜNG KÍNH", "CHIỀU DÀI 1 THANH (mm)", "SỐ LƯỢNG"]
    if not valid:
        headers[1] = "KHÔNG RÕ"
    out += [text(h, x+i*1000, 1500 if not (multiline and i == 2) else 1350)
            for i, h in enumerate(headers)]
    out += [text(h, x+i*1000, 1100) for i, h in enumerate([label, "Ø16", str(length), str(count)])]
    out += [text("TỔNG", x, 900)]
    return out


def drawing(texts):
    return Drawing(segments=[], texts=texts, blocks=[], hatches=[], layers=["TK"],
                   layer_classes={}, unit_scale=1, warnings=[])


@pytest.mark.parametrize("reverse", [False, True])
def test_side_by_side_tables_keep_their_own_rows(reverse):
    texts = table(0, "C1", 3200, 32) + table(6000, "D1", 2000, 5)
    tables, _ = collect_rebar_tables(drawing(list(reversed(texts)) if reverse else texts))
    assert len(tables) == 2
    assert [[(r.element, r.cut_length_mm, r.total_bars) for r in t.rows] for t in tables] == [
        [("C1", 3200, 32)], [("D1", 2000, 5)]]


def test_title_without_local_valid_header_does_not_borrow_neighbor():
    tables, warnings = collect_rebar_tables(drawing(table(0, "C1", 3200, 32, valid=False)
                                                   + table(6000, "D1", 2000, 5)))
    assert tables[0].rows == []
    assert [(r.element, r.total_bars) for r in tables[1].rows] == [("D1", 5)]
    assert any("C1" in w and "tiêu đề cột" in w for w in warnings)


def test_header_on_two_rows_stays_in_its_table():
    tables, _ = collect_rebar_tables(drawing(table(0, "C1", 3200, 32, multiline=True)
                                           + table(6000, "D1", 2000, 5, multiline=True)))
    assert [[r.total_bars for r in t.rows] for t in tables] == [[32], [5]]


def test_centered_titles_and_calculated_kg_keep_local_table():
    texts = table(0, "C1", 3200, 32) + table(6000, "D1", 2000, 5)
    for t in texts:
        if "THỐNG KÊ" in t.text:
            t.x += 1500
    tables, _ = collect_rebar_tables(drawing(texts))
    assert [t.rows[0].kg for t in tables] == pytest.approx([161.79, 15.8], abs=0.01)


def test_title_between_two_header_regions_is_ambiguous():
    texts = table(0, "C1", 3200, 32) + table(4000, "D1", 2000, 5)
    texts[0].x = 3500
    tables, warnings = collect_rebar_tables(drawing(texts))
    assert tables[0].rows == []
    assert any("C1" in w and "mơ hồ" in w for w in warnings)
