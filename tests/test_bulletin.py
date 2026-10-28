"""Đọc bảng công bố giá (catalog/bulletin.py) và quy tắc ghép mã data/rules/cong_bo_gia.csv."""
import pandas as pd

from optimat.catalog.bulletin import load_rules, match, parse_price, parse_tables, supplier_id, transport_included

HEAD = ["STT", "Nhóm", "Tên", "Đơn vị", "TC", "Quy cách", "Nhà sản xuất", "Xuất xứ", "Điều kiện", "Vận chuyển", "Ghi chú", "Giá"]


def _row(stt="", name="", unit="", price="", maker=None, terms=None):
    return [stt, "", name, unit, "", "", maker, None, terms, None, None, price]


def test_parse_and_match():
    tables = [
        (3, [["STT", "Danh mục", "Đơn vị", "Giá"], ["", "I - NHÓM VẬT LIỆU CÁT:", "", ""],
             ["", "Bãi Tàm Xá - xã Vĩnh Thanh", None, None], ["1", "Cát vàng", "m 3", "850.000"]]),
        (5, [HEAD, _row("1", "CÔNG TY CP XI MĂNG A", *[""] * 2),
             _row(name="Xi măng bao PCB30", unit="tấn", price="1.810.000", maker="Nhà máy A", terms="Giao tại nhà máy"),
             _row(name="Xi măng bao PCB30 vỏ PP công trình", unit="tấn", price="1.466.000"),   # loại trừ
             _row(name="Xi măng bao PCB40", unit="đồng/t\nấn", price="1.830.000")]),
        # sang trang: ô trống "" không được xóa điều kiện của dòng trên
        (6, [HEAD, ["", "", "Xi măng bao PCB30 loại 2", "tấn", "", "", "", "", "", "", "", "1.900.000"],
             _row("2", "Công ty TNHH Thép B", *[""] * 2),
             _row(name="Thép thanh vằn d10 CB400-V", unit="kg", price="16,120"),
             _row(name="Thép thanh vằn d12 CB400-V", unit="kg", price="15.920"),
             _row(name="Thép thanh vằn d14 CB400-V", unit="tấn", price="15.920.000")]),
    ]
    rows = match(parse_tables(tables), load_rules())
    got = {(r.supplier, r.material_id): r for r in rows if r.material_id}
    assert set(got) == {("Bãi Tàm Xá - xã Vĩnh Thanh", "CA01"), ("CÔNG TY CP XI MĂNG A", "XM01"),
                        ("CÔNG TY CP XI MĂNG A", "XM02"), ("Công ty TNHH Thép B", "TH07")}
    assert got[("CÔNG TY CP XI MĂNG A", "XM01")].catalog_price == 1_810_000           # dòng đầu, không lấy "vỏ PP"
    assert got[("Công ty TNHH Thép B", "TH07")].catalog_price == 16_120_000           # kg -> tấn
    assert transport_included(got[("CÔNG TY CP XI MĂNG A", "XM02")].terms) == "NO"   # ô gộp lấy theo dòng trên
    assert transport_included(got[("Bãi Tàm Xá - xã Vĩnh Thanh", "CA01")].terms) == "NO"
    reasons = {r.name: r.reason for r in rows if not r.material_id}
    assert "trùng" in reasons["Xi măng bao PCB30 loại 2"]
    assert "đơn vị" in reasons["Thép thanh vằn d14 CB400-V"]          # TH03 cần giá theo kg
    assert reasons["Xi măng bao PCB30 vỏ PP công trình"] == "không có quy tắc khớp"


def test_helpers():
    assert parse_price("1.810.000") == parse_price("1,810,000") == 1_810_000
    assert parse_price("5.010") == 5010 and parse_price("1 19.022") == 119_022   # PDF tách chữ số
    assert parse_price("Liên hệ") is None
    assert supplier_id("Bãi Tàm Xá - xã Vĩnh Thanh") == supplier_id("Bãi Tàm Xá-xã Vĩnh Thanh")
    assert transport_included("Giá đến công trình đã bao gồm bốc xếp") == "YES"
    assert transport_included("") == "UNKNOWN"


def test_rules_point_to_catalog():
    from pathlib import Path
    mats = set(pd.read_csv(Path(__file__).resolve().parents[1] / "data/catalog/materials.csv").material_id)
    rules = load_rules()
    assert len({r.rule_id for r in rules}) == len(rules)
    assert {r.material_id for r in rules} <= mats
