"""D02: hợp đồng dữ liệu bộ đáp án công tác/vật tư (data/ground_truth/du_toan/d02). Fixture SYNTHETIC, không báo độ chính xác."""
import csv
import hashlib

import pytest

from optimat.data_check import (CASES_FILE, D02_COLUMNS, D02_DIR, M01_PT, M01_PT_OUT, check_answer_set, check_cases,
                                denominator_ids, material_totals, select_cases)


def _write(path, cols, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows([{c: r.get(c, "") for c in cols} for r in rows])


def _work(id, dong, kl, **kw):
    r = dict(id=id, cong_trinh_id="ct_fx", dong_goc=dong, pham_vi="IN", dem_mau_so="co", khoi_luong=kl, don_vi="m³",
             loai_nguon="du_toan", nguon=f"gt/fx.csv stt {dong}", trang_thai_kiem="nhap")
    r.update(kw)
    return r


def _base():
    """Bộ SYNTHETIC hợp lệ: 3 dòng dự toán (lót gộp móng + nền, cột, sơn OUT), 47 hạng mục, thép lắp đặt và mua."""
    src = [dict(stt="1", ten_cong_tac="Bê tông lót", don_vi="m³", khoi_luong="3.0", ma_cong_tac="BE_TONG_LOT"),
           dict(stt="2", ten_cong_tac="Bê tông cột", don_vi="m³", khoi_luong="2.0", ma_cong_tac="COT"),
           dict(stt="3", ten_cong_tac="Sơn tường", don_vi="m²", khoi_luong="10.0", ma_cong_tac="")]
    vt = [dict(stt="1", ten_vat_tu="Thép tròn", don_vi="kg", khoi_luong="102")]
    hm = [dict(id=f"F-HM-{p}", cong_trinh_id="ct_fx", vi_tri="toàn công trình", ma_pt=p, ton_tai="chua_ro", nguon_ton_tai="fixture",
               pham_vi="OUT" if p in M01_PT_OUT else "IN", ma_qd="QĐ-chung", ly_do="fixture", trang_thai_kiem="nhap") for p in M01_PT]
    works = [_work("F-C01", "1", "3", ma_cong_tac="BE_TONG_LOT"),
             _work("F-C01.1", "1", "1", cha_id="F-C01", quan_he_cha="phan", ma_pt="PT04", hang_muc_id="F-HM-PT04", dem_mau_so="khong",
                   ma_cong_tac="BE_TONG_LOT"),
             _work("F-C01.2", "1", "2", cha_id="F-C01", quan_he_cha="phan", ma_pt="PT05", hang_muc_id="F-HM-PT05", dem_mau_so="khong",
                   ma_cong_tac="BE_TONG_LOT"),
             _work("F-C02", "2", "2", ma_pt="PT12", hang_muc_id="F-HM-PT12", ma_cong_tac="COT"),
             _work("F-C03", "3", "10", ma_pt="PT46", pham_vi="OUT", ma_qd="QĐ-chung", dem_mau_so="khong", don_vi="m²")]
    mats = [dict(id="F-V01", cong_trinh_id="ct_fx", cong_tac_id="F-C02", quy_cach="Thép tròn Ø ≤ 10", don_vi_goc="tấn", don_vi="kg",
                 luong="100", co_so_luong="lap_dat", hao_hut="chua_gom", dung_lam_dap_an="cho_kiem", loai_nguon="du_toan", nguon="x",
                 trang_thai_kiem="nhap"),
            dict(id="F-V02", cong_trinh_id="ct_fx", cong_tac_id="F-C02", dong_vat_tu_goc="2", quy_cach="Thép tròn Ø ≤ 10",
                 don_vi_goc="kg", don_vi="kg", luong="102", co_so_luong="mua", he_so="1.02", nguon_he_so="fixture", hao_hut="da_gom",
                 dung_lam_dap_an="cho_kiem", loai_nguon="du_toan", nguon="x", trang_thai_kiem="nhap")]
    return dict(src=src, vt=vt, hm=hm, works=works, mats=mats)


def _build(tmp_path, d):
    _write(tmp_path / "gt/fx.csv", ["stt", "ten_cong_tac", "don_vi", "khoi_luong", "ma_cong_tac"], d["src"])
    _write(tmp_path / "gt/fx_vt.csv", ["stt", "ten_vat_tu", "don_vi", "khoi_luong"], d["vt"])
    _write(tmp_path / "cases.csv", ["ten", "cong_trinh_id", "data_kind", "split", "du_toan"],
           [dict(ten="fx", cong_trinh_id="ct_fx", data_kind="SYNTHETIC", split="build", du_toan="gt/fx.csv")])
    folder = tmp_path / "d02/fx"
    lock = [dict(duong_dan=p, vai_tro=role, sha256=hashlib.sha256((tmp_path / p).read_bytes()).hexdigest(), trong_kho="co")
            for p, role in (("gt/fx.csv", "du_toan_cong_tac"), ("gt/fx_vt.csv", "du_toan_vat_tu"))]
    for name, rows in (("so_hang_muc.csv", d["hm"]), ("dap_an_cong_tac.csv", d["works"]), ("dap_an_vat_tu.csv", d["mats"]),
                       ("khoa_nguon.csv", lock)):
        _write(folder / name, list(D02_COLUMNS[name]), rows)
    return folder


def _check(tmp_path, d):
    return check_answer_set(_build(tmp_path, d), tmp_path / "cases.csv", tmp_path)


def _err(findings):
    return [f.message for f in findings if f.level == "error"]


def _find(d, key, id):
    return next(r for r in d[key] if r["id"] == id)


def test_valid_fixture_passes(tmp_path):
    assert _err(_check(tmp_path, _base())) == []


def test_broken_ids_and_links_detected(tmp_path):
    d = _base()
    _find(d, "works", "F-C01.2")["cha_id"] = "F-C99"
    _find(d, "works", "F-C02")["hang_muc_id"] = "F-HM-PT99"
    d["mats"][0]["cong_tac_id"] = "F-C77"
    d["works"].append(_work("F-C02", "2", "2", ma_pt="PT12"))
    msgs = _err(_check(tmp_path, d))
    assert "cha_id F-C99 không có." in msgs and "hang_muc_id F-HM-PT99 không có trong sổ hạng mục." in msgs
    assert "cong_tac_id F-C77 không có trong đáp án công tác." in msgs and "id F-C02 trùng." in msgs


def test_combined_line_counts_once_and_split_does_not_add(tmp_path):
    d = _base()
    assert denominator_ids(d["works"]) == ["F-C01", "F-C02"]       # dòng gộp F-C01 một mẫu số dù có hai dòng con
    _find(d, "works", "F-C01.1")["dem_mau_so"] = "co"                # cố đếm dòng con để tăng mẫu số
    assert "Dòng con không được tính mẫu số (dem_mau_so = khong)." in _err(_check(tmp_path, d))


def test_children_sum_checked_and_mismatch_must_be_recorded(tmp_path):
    d = _base()
    _find(d, "works", "F-C01.2")["khoi_luong"] = "2.5"
    assert any("Tổng phần con 3.5 lệch số gốc 3" in m for m in _err(_check(tmp_path, d)))
    _find(d, "works", "F-C01")["khoi_luong_tinh_lai"] = "3.5"        # giữ chênh lệch, không sửa số gốc
    f = _check(tmp_path, d)
    assert _err(f) == [] and any(x.level == "warning" and "đã ghi khoi_luong_tinh_lai" in x.message for x in f)
    _find(d, "works", "F-C01")["khoi_luong"] = "3.5"                 # sửa số gốc để ép khớp: bị chặn
    assert any("khác số gốc 3.0" in m for m in _err(_check(tmp_path, d)))


def test_unclassified_and_missing_numbers_kept_not_zero(tmp_path):
    d = _base()
    _find(d, "works", "F-C03").update(pham_vi="chua_phan_loai", ma_pt="", ma_qd="", dem_mau_so="cho_phan_loai")
    f = _check(tmp_path, d)
    assert _err(f) == [] and any("1 dòng chưa phân loại IN/OUT" in x.message and "F-C03" in x.message for x in f)
    _find(d, "works", "F-C01.1")["khoi_luong"] = "0"
    _find(d, "works", "F-C02")["khoi_luong"] = ""
    msgs = _err(_check(tmp_path, d))
    assert "khoi_luong = 0: chưa có số thì để trống và ghi lý do." in msgs
    assert "Chưa có khối lượng nhưng không ghi lý do (can_kiem)." in msgs
    _find(d, "works", "F-C03")["dem_mau_so"] = "khong"               # chưa phân loại không được lặng lẽ ra khỏi mẫu số
    assert any("theo phạm vi phải là cho_phan_loai" in m for m in _err(_check(tmp_path, d)))


def test_checked_without_evidence_blocked(tmp_path):
    d = _base()
    _find(d, "works", "F-C02")["trang_thai_kiem"] = "da_kiem"
    assert "Ghi đã kiểm nhưng thiếu nguoi_kiem, ngay_kiem." in _err(_check(tmp_path, d))
    _find(d, "works", "F-C02").update(nguoi_kiem="KS. Thử", ngay_kiem="2026-11-03")
    assert _err(_check(tmp_path, d)) == []


def test_m01_scope_out_and_in_items_not_dropped(tmp_path):
    d = _base()
    d["works"] += [_work("F-C04", "9", "", pham_vi="IN", ma_pt="PT25", dem_mau_so="co", can_kiem="x"),
                   _work("F-C05", "9", "", pham_vi="OUT", ma_pt="PT15", ma_qd="QĐ-chung", dem_mau_so="khong", can_kiem="x")]
    msgs = _err(_check(tmp_path, d))
    assert "PT25 là OUT theo M01 (H5), không được đặt IN." in msgs and "PT15 là IN theo M01, không được đặt OUT." in msgs
    d = _base()
    d["works"].append(_work("F-C04", "2", "", pham_vi="OUT", ma_pt="PT22", ma_qd="QĐ-05", dem_mau_so="khong", can_kiem="x"))
    assert any("QĐ-05 không phải quyết định đặt ngoài phạm vi" in m for m in _err(_check(tmp_path, d)))
    d = _base()
    d["hm"] = [r for r in d["hm"] if r["ma_pt"] not in ("PT15", "PT30")]     # vách, bể chưa thấy trong dự toán
    assert any("Thiếu hạng mục M01: PT15, PT30" in m for m in _err(_check(tmp_path, d)))


def test_installed_and_purchased_steel_not_mixed(tmp_path):
    d = _base()
    assert material_totals(d["mats"]) == {("Thép tròn Ø ≤ 10", "kg", "lap_dat"): 100.0, ("Thép tròn Ø ≤ 10", "kg", "mua"): 102.0}
    d["mats"][0]["hao_hut"] = "da_gom"
    d["mats"][1].update(don_vi_goc="m³", don_vi="viên")
    msgs = _err(_check(tmp_path, d))
    assert "Lượng lắp đặt không được gồm hao hụt: trộn cơ sở lắp đặt và mua." in msgs
    assert "Đổi m³ → viên thiếu căn cứ (chỉ đổi đơn vị chính xác)." in msgs


def test_locked_source_change_detected(tmp_path):
    folder = _build(tmp_path, _base())
    (tmp_path / "gt/fx.csv").write_text("stt,ten_cong_tac,don_vi,khoi_luong,ma_cong_tac\n1,x,m³,9,\n", encoding="utf-8")
    assert "Nội dung file đã đổi sau khi khóa (sha256 khác)." in _err(check_answer_set(folder, tmp_path / "cases.csv", tmp_path))


def test_empty_or_missing_source_lock_is_blocked(tmp_path):
    """Không có nguồn công tác đã khóa thì không được bỏ qua đối chiếu số gốc (số gốc 999, tổng con 3)."""
    d = _base()
    d["src"][0]["khoi_luong"] = "999"
    folder = _build(tmp_path, d)
    _write(folder / "khoa_nguon.csv", list(D02_COLUMNS["khoa_nguon.csv"]), [])
    msgs = _err(check_answer_set(folder, tmp_path / "cases.csv", tmp_path))
    assert any("Phải có đúng một nguồn vai_tro = du_toan_cong_tac (đang có 0)" in m for m in msgs)
    assert "Đáp án vật tư tham chiếu dong_vat_tu_goc nhưng không có nguồn du_toan_vat_tu đọc được." in msgs
    # có nguồn công tác nhưng thiếu vai trò vật tư: vẫn chặn vì dòng vật tư tham chiếu tổng hợp
    folder = _build(tmp_path, _base())
    rows = [r for r in csv.DictReader((folder / "khoa_nguon.csv").open(encoding="utf-8")) if r["vai_tro"] == "du_toan_cong_tac"]
    _write(folder / "khoa_nguon.csv", list(D02_COLUMNS["khoa_nguon.csv"]), rows)
    assert _err(check_answer_set(folder, tmp_path / "cases.csv", tmp_path)) == [
        "Đáp án vật tư tham chiếu dong_vat_tu_goc nhưng không có nguồn du_toan_vat_tu đọc được."]


def test_non_finite_and_negative_numbers(tmp_path):
    d = _base()
    _find(d, "works", "F-C02")["khoi_luong"] = "NaN"
    d["mats"][0]["luong"] = "inf"
    d["mats"][1]["he_so"] = "-1"
    msgs = _err(_check(tmp_path, d))
    assert "khoi_luong \"NaN\" không phải số hữu hạn." in msgs and "luong \"inf\" không phải số hữu hạn." in msgs
    assert "he_so \"-1\" phải là số hữu hạn dương." in msgs
    assert material_totals(d["mats"]) == {("Thép tròn Ø ≤ 10", "kg", "mua"): 102.0}        # NaN/inf không lọt vào tổng
    d = _base()
    _find(d, "works", "F-C01.2")["khoi_luong"] = "2.5"                                   # phần trừ ghi âm, có cong_tru = tru
    d["works"].append(_work("F-C01.3", "1", "-0.5", cha_id="F-C01", quan_he_cha="phan", cong_tru="tru", dem_mau_so="khong",
                            ma_cong_tac="BE_TONG_LOT", ma_pt="PT05"))
    assert _err(_check(tmp_path, d)) == []
    _find(d, "works", "F-C02")["khoi_luong"] = "-2"
    d["mats"][0]["luong"] = "-5"
    msgs = _err(_check(tmp_path, d))
    assert "Số âm chỉ dùng cho dòng con phần trừ (quan_he_cha = phan, cong_tru = tru)." in msgs
    assert "luong âm: lượng vật tư không được âm." in msgs


def test_exact_unit_conversion_compared_after_conversion(tmp_path):
    d = _base()
    d["vt"].append(dict(stt="2", ten_vat_tu="Thép tròn", don_vi="tấn", khoi_luong="0.102"))
    d["mats"].append(dict(d["mats"][1], id="F-V03", dong_vat_tu_goc="3", don_vi_goc="tấn", don_vi="kg", luong="102"))
    assert _err(_check(tmp_path, d)) == []                                           # 0,102 tấn = 102 kg
    d["mats"][-1]["luong"] = "103"
    assert any("khác số gốc 0.102 tấn sau quy đổi" in m for m in _err(_check(tmp_path, d)))
    d["mats"][-1].update(luong="102", don_vi_goc="kg")                                 # khai báo sai đơn vị nguồn
    assert "don_vi_goc kg khác đơn vị nguồn tấn." in _err(_check(tmp_path, d))


def test_steel_only_known_above_10mm_not_assigned_to_le_18_group():
    """46: stt 25, 26 chỉ ghi Ø > 10 mm; không tự xếp vào nhóm ≤ 18 mm; dòng mua ≤ 18 không mang hệ số suy từ giả thuyết."""
    mats = list(csv.DictReader((D02_DIR / "46_nha_tan_binh/dap_an_vat_tu.csv").open(encoding="utf-8")))
    le18 = [r for r in mats if "≤ 18" in r["quy_cach"]]
    assert all(not ({"46-C25", "46-C26"} & set(r["cong_tac_id"].split(";"))) for r in le18)
    gt10 = [r for r in mats if "> 10" in r["quy_cach"]]
    assert [(r["co_so_luong"], r["cong_tac_id"], r["luong"]) for r in gt10] == [("lap_dat", "46-C25;46-C26", "1570.8")]
    buy = next(r for r in le18 if r["co_so_luong"] == "mua")
    assert buy["he_so"] == "" and "Giả thuyết chờ kiểm" in buy["thieu"]
    assert material_totals(mats)[("Thép tròn Ø ≤ 18 mm", "kg", "lap_dat")] == pytest.approx(15503.4)


def test_real_set_46_build_has_no_errors_and_nothing_confirmed_on_behalf():
    folder = D02_DIR / "46_nha_tan_binh"
    assert _err(check_answer_set(folder)) == []
    for name in ("so_hang_muc.csv", "dap_an_cong_tac.csv", "dap_an_vat_tu.csv"):
        rows = list(csv.DictReader((folder / name).open(encoding="utf-8")))
        assert {r["trang_thai_kiem"] for r in rows} <= {"nhap", "cho_kiem"} and not any(r["nguoi_kiem"] for r in rows)
    works = list(csv.DictReader((folder / "dap_an_cong_tac.csv").open(encoding="utf-8")))
    assert len([r for r in works if not r["cha_id"]]) == 64 and len(denominator_ids(works)) == 34
    assert not (D02_DIR / "banve1_nha_pho_di_an").exists()                       # D02 không làm trên bộ test


def test_d01_manifest_and_evaluator_entry_unchanged():
    assert _err(check_cases()[0]) == []
    rows = {r["ten"]: r for r in csv.DictReader(CASES_FILE.open(encoding="utf-8-sig"))}
    assert rows["46_nha_tan_binh"]["du_toan"] == "data/ground_truth/du_toan/46_nha_tan_binh.csv"
    assert [r["ten"] for r in select_cases("phat_trien")[0]] == ["46_nha_tan_binh"]
    assert select_cases("bao_cao")[0] == []
