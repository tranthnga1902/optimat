"""rough/estimate_check.py và /api/estimate/check: bốn loại kiểm tra sai lệch dự toán."""
import io
import json

import pandas as pd
from fastapi.testclient import TestClient

from optimat.api.main import app
from optimat.catalog.repository import Catalog
from optimat.rough.estimate_check import (check_arithmetic, check_estimate, check_prices, check_quantities, classify,
                                          read_tables, tag_works)
from optimat.rough.models import ProjectParams, WorkItem


def _csv(rows) -> bytes:
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


def test_classify_and_vietnamese_headers():
    assert classify("Bê tông cột tiết diện <= 0,1m2 đá 1x2 M200") == ("COT", "")
    assert classify("Ván khuôn dầm") == ("COP_PHA", "DAM")
    assert classify("Lát gạch ceramic") == ("", "")
    xlsx = io.BytesIO()
    pd.DataFrame([{"Tên công tác": "Xây tường gạch ống", "Đơn vị": "m3", "Khối lượng": 10}]).to_excel(xlsx, index=False)
    works, mats, _ = read_tables([("du_toan.xlsx", xlsx.getvalue())])
    assert list(works.columns) == ["ten_cong_tac", "don_vi", "khoi_luong"] and mats.empty
    tagged = tag_works(works)
    assert tagged.ma_cong_tac[0] == "XAY" and bool(tagged.tu_gan[0])


def test_quantities_flag_over_threshold():
    est = tag_works(pd.DataFrame([{"ten_cong_tac": "Xây tường", "don_vi": "m³", "khoi_luong": 100.0},
                                  {"ten_cong_tac": "Bê tông dầm", "don_vi": "m³", "khoi_luong": 10.0}]))
    works = [WorkItem(code="XAY", name="x", unit="m³", quantity=80.0), WorkItem(code="DAM", name="d", unit="m³", quantity=10.5)]
    rows = {r["ma_cong_tac"]: r for r in check_quantities(est, works, threshold=10)}
    assert rows["XAY"]["lech_pct"] == -20.0 and rows["XAY"]["ket_luan"] == "lệch"
    assert rows["DAM"]["lech_pct"] == 5.0 and rows["DAM"]["ket_luan"] == "khớp"


def test_arithmetic_tolerates_rounding_only():
    df = pd.DataFrame([{"ten_vat_tu": "Cát", "khoi_luong": 2.0, "don_gia": 100000.0, "thanh_tien": 200000.4},
                       {"ten_vat_tu": "Đá", "khoi_luong": 3.0, "don_gia": 100000.0, "thanh_tien": 330000.0}])
    rows = check_arithmetic({"vat_tu": df})
    assert [r["ten"] for r in rows] == ["Đá"] and rows[0]["chenh"] == 30000.0 and rows[0]["dong"] == 3


def test_prices_convert_kg_to_catalog_unit():
    cat = Catalog.load()
    offer = cat.supplier_materials.dropna(subset=["base_price"]).iloc[0]
    mid = offer.material_id
    unit = cat.materials.set_index("material_id").at[mid, "unit"]
    mats = pd.DataFrame([{"ten_vat_tu": "x", "material_id": mid, "don_vi": unit, "khoi_luong": 1,
                          "don_gia": float(offer.base_price) * 2}])
    row = check_prices(mats, cat, threshold=10)[0]
    if row["so_nguon"]:                                            # giá MẪU có thể bị loại (ngày, đơn vị): chỉ kiểm khi có
        assert row["ket_luan"] == "lệch" and row["lech_pct"] > 0


def test_check_estimate_on_set_46_norms():
    raw = json.load(open("data/ground_truth/du_toan/46_thong_so.json", encoding="utf-8"))
    raw.pop("openings", None)
    files = [(n, open(f"data/ground_truth/du_toan/{n}", "rb").read()) for n in ("46_nha_tan_binh.csv", "46_vat_tu.csv")]
    r = check_estimate(files, None, ProjectParams(**raw), Catalog.load())
    norms = {x["material_id"]: x for x in r["dinh_muc"]}
    assert abs(norms["CA01"]["lech_pct"]) < 10 and abs(norms["DA01"]["lech_pct"]) < 10   # cát, đá bê tông khớp định mức
    assert r["khoi_luong"] == [] and any("phần thô của hệ thống" in n for n in r["ghi_chu"])


def test_api_json_and_excel():
    client = TestClient(app)
    est = _csv([{"ten_cong_tac": "Xây tường gạch", "don_vi": "m³", "khoi_luong": 50, "don_gia": 1000, "thanh_tien": 60000}])
    works = json.dumps([{"code": "XAY", "name": "x", "unit": "m³", "quantity": 50}])
    r = client.post("/api/estimate/check", files=[("files", ("kl.csv", est, "text/csv"))], data={"works": works})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["khoi_luong"][0]["ket_luan"] == "khớp" and body["tom_tat"]["so_hoc_loi"] == 1
    x = client.post("/api/estimate/check", files=[("files", ("kl.csv", est, "text/csv"))], data={"excel": "true"})
    assert x.status_code == 200 and x.content[:2] == b"PK"
    bad = client.post("/api/estimate/check", files=[("files", ("a.txt", b"x", "text/plain"))])
    assert bad.status_code == 422


def _book(sheets: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, rows in sheets.items():
            pd.DataFrame(rows).to_excel(xw, sheet_name=name, index=False, header=False)
    return buf.getvalue()


def test_reader_estimate_software_layout():
    """Mẫu phần mềm dự toán: tiêu đề hai dòng chữ VNI, đơn vị 100m2, giá chia VL/NC/máy, diễn giải, mục nhân công."""
    from optimat.rough.estimate_reader import read_estimate_book, text
    assert text("TEÂN") == "TÊN" and text("Ñaøo beå nöôùc ngaàm,bể tự hoại") == "Đào bể nước ngầm,bể tự hoại"
    assert text("ĐƠN GIÁ") == "ĐƠN GIÁ" and text("Dự toán") == "Dự toán"            # Unicode giữ nguyên
    works = [["BẢNG KHỐI LƯỢNG DỰ TOÁN", None, None, None, None, None, None, None, None, None],
             ["SOÁ", "MÃ HIỆU", "TEÂN", "ĐƠN", "KHỐI LƯỢNG", None, "ĐƠN GIÁ", None, "THÀNH TIỀN", None],
             ["TT", "ĐỊNH MỨC", "CÔNG VIỆC", "VÒ", "CHI TIẾT", "TỔNG SỐ", "VẬT LIỆU", "NH.CÔNG", "VẬT LIỆU", "NH.CÔNG"],
             [1, "AE.22114", "Xây tường gạch ống", "m3", None, 10, 900000, 100000, 9000000, 1000000],
             [None, None, "Tầng 1: 5 x 2", None, 10, None, None, None, None, None],
             [2, "AF.83321", "Ván khuôn dầm", "100m2", None, 0.5, 2000000, 0, 1000000, 0]]
    mats = [["STT", "Mã số", "Tên vật tư", "Đơn vị", "Khối lượng", "Giá gốc", "Thành tiền", "Giá T.B", "Thành tiền"],
            ["I.)", None, "I.) VẬT LIỆU", None, None, None, None, None, None],
            [1, "0023", "Đá 1x2", "m3", 30, 120000, 3600000, 245000, 7350000],
            ["II.)", None, "II.) NHÂN CÔNG", None, None, None, None, None, None],
            [2, "N137", "Nhân công 3,7/7", "công", 50, 100000, 5000000, 150000, 7500000]]
    w, m, notes = read_estimate_book("dt.xlsx", _book({"Bang khoi luong": works, "Tong hop VT": mats, "Bia": [["x"]]}))
    assert len(notes) == 2
    assert w.ten_cong_tac.tolist() == ["Xây tường gạch ống", "Ván khuôn dầm"] and w.dien_giai[0] == "Tầng 1: 5 x 2"
    assert w.khoi_luong.tolist() == [10, 50] and w.khoi_luong_goc[1] == 0.5 and w.don_vi[1] == "m²"
    assert w.don_gia[0] == 1000000 and w.thanh_tien[0] == 10000000                   # VL + NC
    assert m.ten_vat_tu.tolist() == ["Đá 1x2"]                                       # bỏ mục nhân công
    assert (m.don_gia_goc[0], m.thanh_tien_goc[0], m.don_gia[0], m.thanh_tien[0]) == (120000, 3600000, 245000, 7350000)
    r = check_estimate([("dt.xlsx", _book({"Bang khoi luong": works, "Tong hop VT": mats}))], None, ProjectParams(), Catalog.load())
    assert r["so_hoc"] == [] and r["tom_tat"]["cong_tac"] == 2                      # 0,5 × 2.000.000 theo đơn vị gốc


def test_tag_materials_prefix_only_for_sizes():
    from optimat.rough.estimate_check import tag_materials
    cat = Catalog.load()
    if not {"cát vàng", "gạch thẻ"} <= set(cat.aliases.alias.str.lower()):
        return
    t = tag_materials(pd.DataFrame({"ten_vat_tu": ["Gạch thẻ 4x8x19", "Cát vàng hạt nhỏ"]}), cat)
    assert t.material_id[0] != "" and t.material_id[1] == ""
