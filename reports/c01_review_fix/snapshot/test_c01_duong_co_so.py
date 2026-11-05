"""C01: báo cáo đường cơ sở build (đối chứng phát triển). Fixture SYNTHETIC, không báo độ chính xác."""
import csv
import sys
from pathlib import Path

import pandas as pd
import pytest

from optimat.rough.models import MaterialLine, WorkItem

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import c01_duong_co_so as c01  # noqa: E402

CASE = {"ten": "fx", "split": "build", "data_kind": "SYNTHETIC"}


def _w(id, kl, **kw):
    r = dict(id=id, cha_id="", quan_he_cha="", dong_goc=id.split(".")[0][-2:], noi_dung=id, ma_pt="", pham_vi="IN",
             dem_mau_so="co", ma_cong_tac="", cau_kien="", khoi_luong=kl, don_vi="m³", trang_thai_kiem="nhap", can_kiem="")
    r.update(kw)
    return r


def _sys(code, q, status="C", **kw):
    return WorkItem(code=code, name=code, unit=c01.WORKS[code][1], quantity=q, status=status, **kw)


def _report(works, sys_works, mats=(), sys_mats=(), keys=frozenset()):
    return c01.build_report(list(works), [], list(mats), list(sys_works), list(sys_mats), CASE, keys)


def _line(rep, id):
    return rep["Doi_chieu_cong_tac"].set_index("id").loc[id]


def _grp(rep, key):
    g = rep["So_sanh_nhom"]
    return g[g.nhom == key].iloc[0]


def test_out_unclassified_unmapped_and_missing_rows_stay_visible():
    works = [_w("F-C01", "10", ma_pt="PT32", ma_cong_tac="XAY"),
             _w("F-C02", "5", pham_vi="OUT", dem_mau_so="khong", ma_pt="PT46", don_vi="m²"),
             _w("F-C03", "4", pham_vi="chua_phan_loai", dem_mau_so="cho_phan_loai"),
             _w("F-C04", "3", ma_pt="PT09"),                                       # IN, chưa có mã công tác
             _w("F-C05", "", ma_pt="PT12", ma_cong_tac="COT", can_kiem="thiếu số")]
    rep = _report(works, [_sys("XAY", 9.0)])
    st = rep["Doi_chieu_cong_tac"].set_index("id").trang_thai_de_xuat.to_dict()
    assert st == {"F-C01": "co_ket_qua_chua_xac_nhan", "F-C02": "ngoai_pham_vi", "F-C03": "cho_phan_loai",
                  "F-C04": "chua_anh_xa", "F-C05": "khong_cung_pham_vi_he_thong"}
    assert "F-C05: chưa có số" in _line(rep, "F-C05").phan_khong_so
    assert pd.isna(_line(rep, "F-C05").khoi_luong_doi_chung)                  # None không thành 0


def test_parent_and_children_counted_once_and_shared_total_compared_once():
    works = [_w("F-C01", "10", ma_cong_tac="XAY"),
             _w("F-C01.1", "4", cha_id="F-C01", quan_he_cha="phan", ma_pt="PT32", ma_cong_tac="XAY", dem_mau_so="khong"),
             _w("F-C01.2", "6", cha_id="F-C01", quan_he_cha="phan", ma_pt="PT32", ma_cong_tac="XAY", dem_mau_so="khong"),
             _w("F-C02", "5", ma_pt="PT32", ma_cong_tac="XAY")]
    rep = _report(works, [_sys("XAY", 15.0)])
    g = rep["So_sanh_nhom"]
    assert len(g[g.nhom == "XAY"]) == 1                                         # một tổng hệ thống, một phép so
    assert _grp(rep, "XAY").doi_chung == 15.0 and _grp(rep, "XAY").chenh == 0.0   # 10 + 5, không cộng cha với con
    assert set(rep["Doi_chieu_cong_tac"].id) == {"F-C01", "F-C02"}              # dòng con không thành dòng đối chiếu riêng
    assert "lech_pct" not in rep["Doi_chieu_cong_tac"]                           # không gán khớp cho từng dòng


def test_combined_line_with_unsupported_part_is_not_complete():
    works = [_w("F-C01", "7", ma_cong_tac="XAY"),
             _w("F-C01.1", "4", cha_id="F-C01", quan_he_cha="phan", ma_pt="PT32", ma_cong_tac="XAY", dem_mau_so="khong"),
             _w("F-C01.2", "3", cha_id="F-C01", quan_he_cha="phan", ma_pt="PT31", ma_cong_tac="XAY", dem_mau_so="khong")]
    rep = _report(works, [_sys("XAY", 4.0)])
    assert _line(rep, "F-C01").trang_thai_de_xuat == "mot_phan"
    assert "PT31: hệ thống chưa có công tác cùng phạm vi" in _line(rep, "F-C01").phan_khong_so
    assert _grp(rep, "XAY").doi_chung == 4.0                                     # chỉ phần cùng phạm vi, không chia tỷ lệ


def test_groups_without_same_scope_are_kept_with_reason():
    works = [_w("F-C01", "10", ma_pt="PT12", ma_cong_tac="COT"), _w("F-C02", "8", ma_pt="PT13", ma_cong_tac="DAM"),
             _w("F-C03", "5", ma_pt="PT17", ma_cong_tac="SAN", don_vi="m²")]
    rep = _report(works, [_sys("COT", 9.0), _sys("COT", None, missing=["cao tầng"]), _sys("CAN_NEN", 30.0)])
    assert not _grp(rep, "COT").so_duoc and _grp(rep, "COT").he_thong == 9.0 and "một phần" in _grp(rep, "COT").ly_do_khong_so
    assert _grp(rep, "DAM").ly_do_khong_so == "hệ thống không sinh dòng"
    assert "thừa" in _grp(rep, "CAN_NEN").ly_do_khong_so                           # phần hệ thống không có đối chứng vẫn hiện
    assert "khác đơn vị" in _line(rep, "F-C03").phan_khong_so


def test_status_groups_split_zero_reference_not_divided():
    works = [_w("F-C01", "10", ma_pt="PT12", ma_cong_tac="COT"), _w("F-C02", "0.000001", ma_pt="PT13", ma_cong_tac="DAM"),
             _w("F-C03", "4", ma_pt="PT19", ma_cong_tac="CAU_THANG")]
    works[1]["khoi_luong"] = "0"
    rep = _report(works, [_sys("COT", 11.0, "A"), _sys("DAM", 2.0, "C"), _sys("CAU_THANG", None, "D", missing=["dày bản"])])
    dam = _grp(rep, "DAM")
    assert dam.so_duoc and dam.chenh == 2.0 and pd.isna(dam.lech_pct) and "% không xác định" in dam.ghi_chu
    ts = rep["Theo_trang_thai"].set_index("nhom_trang_thai")
    assert ts.loc["A/B"].co_so == 1 and ts.loc["A/B"].lech_tb_pct == 10.0          # A/B riêng
    assert ts.loc["C/D"].so_dong == 2 and ts.loc["C/D"].co_so == 0                 # D không có số, không trộn vào A/B
    assert pd.isna(_grp(rep, "CAU_THANG").he_thong)


def test_param_dependency_flagged():
    works = [_w("F-C01", "14", ma_pt="PT06", ma_cong_tac="MONG")]
    rep = _report(works, [_sys("MONG", 14.0)], keys=frozenset({"foundations"}))
    assert "dựa trên foundations" in _grp(rep, "MONG").ghi_chu


def _mat(id, mid, qc, unit, luong, coso="mua", dung="cho_kiem"):
    return dict(id=id, material_id=mid, quy_cach=qc, don_vi=unit, luong=luong, co_so_luong=coso, dung_lam_dap_an=dung, thieu="x")


def test_material_comparison_basis_unit_and_excluded_rows():
    mats = [_mat("V1", "XM02", "Xi măng PC40", "kg", "1000", dung="khong"),
            _mat("V2", "TH03", "Thép Ø ≤ 18", "kg", "1020"),
            _mat("V3", "", "Thép Ø > 10 (chưa xác định nhóm)", "kg", "500", coso="lap_dat"),
            _mat("V4", "DA01", "Đá 1×2", "viên", "10")]
    sys_mats = [MaterialLine(material_id="TH03", name="thép", unit="tấn", quantity=1.0, quantity_with_waste=1.02, complete=True),
                MaterialLine(material_id="XM02", name="xm", unit="kg", quantity=900, quantity_with_waste=900, complete=True),
                MaterialLine(material_id="DA01", name="đá", unit="m³", quantity=5, quantity_with_waste=5, complete=True)]
    t = c01.material_table(mats, sys_mats).set_index("id")
    assert t.loc["V2"].so_duoc and t.loc["V2"].he_thong_co_hao_hut == 1020.0 and t.loc["V2"].chenh == 0.0   # tấn → kg chính xác
    assert not t.loc["V1"].so_duoc and t.loc["V1"].ly_do_khong_so.startswith("không dùng làm đáp án")
    assert not t.loc["V3"].so_duoc and "lắp đặt" in t.loc["V3"].ly_do_khong_so and "> 10" in t.loc["V3"].quy_cach
    assert not t.loc["V4"].so_duoc and "khác đại lượng" in t.loc["V4"].ly_do_khong_so
    sys_mats[0] = MaterialLine(material_id="TH03", name="thép", unit="tấn", quantity=1.0, quantity_with_waste=1.02, complete=False)
    assert "một phần" in c01.material_table(mats, sys_mats).set_index("id").loc["V2"].ly_do_khong_so   # có số nhưng chưa đủ: không so


def test_main_writes_fresh_status_when_no_case_runs(tmp_path, monkeypatch):
    cases = tmp_path / "cases.csv"
    cols = ["ten", "cong_trinh_id", "phien_ban", "data_kind", "split", "du_toan", "kien_truc", "ket_cau", "thong_so", "nguon",
            "quyen_dung", "dap_an_trang_thai", "nguoi_kiem", "ghi_chu"]
    (tmp_path / "gt").mkdir()
    for n in ("a.csv", "b.csv", "a.dxf", "b.dxf"):
        (tmp_path / "gt" / n).write_text("x", encoding="utf-8")
    with cases.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerow(dict(ten="t", cong_trinh_id="ct_t", data_kind="ACTUAL", split="test", du_toan="gt/b.csv", kien_truc="gt/b.dxf", quyen_dung="noi_bo"))
        w.writerow(dict(ten="b", cong_trinh_id="ct_b", data_kind="SYNTHETIC", split="build", du_toan="gt/a.csv", kien_truc="gt/a.dxf", quyen_dung="noi_bo"))
    out = tmp_path / "c01.xlsx"
    with pd.ExcelWriter(out) as xw:                                                   # báo cáo cũ có số
        pd.DataFrame([{"nhom": "XAY", "chenh": 1.0}]).to_excel(xw, sheet_name="So_sanh_nhom", index=False)
    monkeypatch.setattr(c01, "ROOT", tmp_path)
    monkeypatch.setattr(c01, "D02_DIR", tmp_path / "d02")
    monkeypatch.setattr(c01, "rough_for_case", lambda *a: pytest.fail("không được tính hồ sơ thiếu D02"))
    monkeypatch.setattr(sys, "argv", ["c01", "--cases", str(cases), "--out", str(out)])
    c01.main()
    sheets = pd.read_excel(out, sheet_name=None)
    assert "So_sanh_nhom" not in sheets and sheets["Trang_thai"].iloc[0].ket_qua == "không có hồ sơ chạy được"
    why = dict(zip(sheets["Bo_qua"].bo, sheets["Bo_qua"].ly_do))
    assert why == {"t": "không phải split build (phát triển không chạy bộ test)", "b": "chưa có bộ đáp án D02"}
