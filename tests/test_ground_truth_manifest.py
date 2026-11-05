"""D01: manifest hồ sơ đánh giá (data/ground_truth/du_toan/cases.csv), kiểm metadata và cổng chọn hồ sơ ở lối vào evaluator."""
import csv
import sys
from pathlib import Path

import pandas as pd
import pytest

from optimat.data_check import CASE_COLUMNS, CASES_FILE, check_cases, select_cases

ROOT = Path(__file__).resolve().parents[1]
COLS = list(CASE_COLUMNS) + ["ghi_chu"]


def _case(ten, **kw):
    row = {"ten": ten, "cong_trinh_id": f"ct_{ten}", "phien_ban": "chua_ro", "data_kind": "ACTUAL", "split": "build",
           "du_toan": f"gt/{ten}.csv", "kien_truc": f"kt/{ten}.dxf", "ket_cau": "", "thong_so": "", "nguon": "x",
           "quyen_dung": "noi_bo", "dap_an_trang_thai": "chua_kiem", "nguoi_kiem": "", "ghi_chu": ""}
    row.update(kw)
    return row


def _manifest(tmp_path, rows, cols=COLS, files=True):
    """Ghi manifest tạm; files=True tạo file đáp án gt/… và bản vẽ giả kt/… đã khai báo để chỉ kiểm điều đang test."""
    if files:
        for r in rows:
            for c in ("du_toan", "kien_truc"):
                if r.get(c, "").startswith(("gt/", "kt/")):
                    p = tmp_path / r[c]
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("stt\n", encoding="utf-8")
    path = tmp_path / "cases.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def _errors(findings):
    return [f for f in findings if f.level == "error"]


def test_real_manifest_keeps_splits_and_has_no_errors():
    findings, _ = check_cases()
    assert not _errors(findings), _errors(findings)
    rows = {r["ten"]: r for r in csv.DictReader(CASES_FILE.open(encoding="utf-8-sig"))}
    assert rows["46_nha_tan_binh"]["split"] == "build" and rows["banve1_nha_pho_di_an"]["split"] == "test"
    assert {r["data_kind"] for r in rows.values()} == {"ACTUAL"}
    # quyền dùng chưa rõ: cảnh báo, không tự ghi được phép phân phối
    assert all(r["quyen_dung"] == "chua_ro" for r in rows.values())
    assert sum("Quyền dùng chưa rõ" in f.message for f in findings) == 2
    # chưa hồ sơ nào có đáp án được người kiểm xác nhận: chỉ tiêu chính chưa chạy hồ sơ nào
    run, skipped = select_cases("bao_cao")
    assert run == [] and {t for t, _ in skipped} == set(rows)


def test_missing_column_is_fatal(tmp_path):
    path = _manifest(tmp_path, [_case("a")], cols=[c for c in COLS if c != "cong_trinh_id"])
    findings, _ = check_cases(path, tmp_path)
    assert any("Thiếu cột: cong_trinh_id" in f.message for f in _errors(findings))
    with pytest.raises(ValueError, match="cong_trinh_id"):
        select_cases("phat_trien", path, tmp_path)


def test_bad_values_reported_with_line_and_not_fixed(tmp_path):
    rows = [_case("a"), _case("b", cong_trinh_id=""), _case("c", split="train"), _case("d", data_kind="REAL"),
            _case("a", cong_trinh_id="ct_khac")]
    path = _manifest(tmp_path, rows)
    findings, blocked = check_cases(path, tmp_path)
    msgs = {(f.item, f.message) for f in _errors(findings)}
    assert ("cases.csv dòng 3 (b)", "Thiếu cong_trinh_id (bắt buộc).") in msgs
    assert any(i == "cases.csv dòng 4 (c)" and "split = \"train\"" in m for i, m in msgs)
    assert any(i == "cases.csv dòng 5 (d)" and "data_kind = \"REAL\"" in m for i, m in msgs)
    assert any(i == "cases.csv dòng 6 (a)" and "trùng dòng 2" in m for i, m in msgs)
    assert {"b", "c", "d", "a"} <= set(blocked)
    run, skipped = select_cases("phat_trien", path, tmp_path)
    assert run == []                                           # không hồ sơ lỗi nào được chạy
    assert path.read_text(encoding="utf-8").count("train") == 1   # manifest giữ nguyên, không tự sửa


def test_same_project_in_build_and_test_blocked(tmp_path):
    rows = [_case("v1", cong_trinh_id="nha_x", split="build"),
            _case("v2", cong_trinh_id="nha_x", split="test", phien_ban="v2")]
    findings, blocked = check_cases(_manifest(tmp_path, rows), tmp_path)
    assert any("Công trình nha_x nằm ở cả build và test" in f.message for f in _errors(findings))
    assert set(blocked) == {"v1", "v2"}


def test_same_answer_file_across_splits_blocked_but_same_basename_is_not(tmp_path):
    rows = [_case("p", split="build", du_toan="gt/chung.csv"), _case("q", split="test", du_toan="gt/chung.csv"),
            _case("r", split="build", du_toan="gt/build/dap_an.csv"), _case("s", split="test", du_toan="gt/test/dap_an.csv")]
    findings, blocked = check_cases(_manifest(tmp_path, rows), tmp_path)
    assert any("File chung.csv nằm ở cả build và test" in f.message for f in _errors(findings))
    assert {"p", "q"} <= set(blocked) and "r" not in blocked and "s" not in blocked


def test_missing_referenced_answer_is_error(tmp_path):
    rows = [_case("a", thong_so="gt/khong_co.json")]
    path = _manifest(tmp_path, rows)
    (tmp_path / "gt/a.csv").unlink()
    findings, blocked = check_cases(path, tmp_path)
    msgs = [f.message for f in _errors(findings)]
    assert "du_toan: không có file gt/a.csv." in msgs and "thong_so: không có file gt/khong_co.json." in msgs
    assert "a" in blocked


def test_rights_unknown_warns_and_checked_key_needs_reviewer(tmp_path):
    rows = [_case("a", quyen_dung="chua_ro"), _case("b", quyen_dung=""), _case("c", dap_an_trang_thai="da_kiem")]
    findings, blocked = check_cases(_manifest(tmp_path, rows), tmp_path)
    warns = [f.item for f in findings if f.level == "warning" and "Quyền dùng chưa rõ" in f.message]
    assert len(warns) == 2 and "a" not in blocked and "b" not in blocked     # chỉ cảnh báo, không chặn
    assert blocked["c"] == ["Đáp án ghi đã kiểm nhưng chưa có người kiểm."]


def test_missing_local_drawing_skips_case_with_reason(tmp_path):
    rows = [_case("a", kien_truc="data/drawings/build/khong_co.dxf")]
    path = _manifest(tmp_path, rows)
    findings, blocked = check_cases(path, tmp_path)
    assert not _errors(findings)                               # không làm CI thất bại vô điều kiện
    assert any(f.level == "warning" and "thiếu file cục bộ" in f.message for f in findings)
    run, skipped = select_cases("phat_trien", path, tmp_path)
    assert run == [] and skipped == [("a", "thiếu file cục bộ data/drawings/build/khong_co.dxf")]


def test_report_entry_rejects_sample_synthetic_and_unchecked(tmp_path):
    ok = dict(split="test", dap_an_trang_thai="da_kiem", nguoi_kiem="KS. A")
    rows = [_case("that", **ok), _case("mau", data_kind="SAMPLE", **ok), _case("mo_phong", data_kind="SYNTHETIC", **ok),
            _case("chua_kiem", split="test"), _case("build_kiem", split="build", dap_an_trang_thai="da_kiem", nguoi_kiem="B"),
            _case("loi", data_kind="BAD", **ok)]
    path = _manifest(tmp_path, rows)
    run, skipped = select_cases("bao_cao", path, tmp_path)
    assert [r["ten"] for r in run] == ["that"]
    why = dict(skipped)
    assert "không vào chỉ tiêu chính" in why["mau"] and "không vào chỉ tiêu chính" in why["mo_phong"]
    assert why["chua_kiem"] == "đáp án chưa được người kiểm xác nhận" and "chỉ dùng test" in why["build_kiem"]
    assert "không vào chỉ tiêu chính" in why["loi"]
    # phát triển: fixture SAMPLE ở build vẫn chạy, giữ nguyên data_kind; không chạy bộ test
    dev = _manifest(tmp_path, [_case("fx", data_kind="SAMPLE"), _case("t", split="test")])
    run, skipped = select_cases("phat_trien", dev, tmp_path)
    assert [(r["ten"], r["data_kind"], r["split"]) for r in run] == [("fx", "SAMPLE", "build")]
    assert skipped == [("t", "không phải split build (phát triển không chạy bộ test)")]


def test_evaluator_entry_uses_gate(tmp_path, monkeypatch, capsys):
    """Đường báo cáo của evaluate_rough không gọi run_case cho hồ sơ bị loại; số tổng hợp cũ không đổi."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_rough
    path = _manifest(tmp_path, [_case("mau", data_kind="SAMPLE", split="test", dap_an_trang_thai="da_kiem", nguoi_kiem="A")])
    monkeypatch.setattr(evaluate_rough, "run_case", lambda *a: pytest.fail("không được chạy hồ sơ bị loại"))
    monkeypatch.setattr(evaluate_rough.Catalog, "load", classmethod(lambda cls: pytest.fail("không cần nạp danh mục")))
    monkeypatch.setattr(sys, "argv", ["evaluate_rough.py", "--muc-dich", "bao_cao", "--cases", str(path),
                                      "--out", str(tmp_path / "out.xlsx")])
    evaluate_rough.ROOT = tmp_path
    try:
        evaluate_rough.main()
    finally:
        evaluate_rough.ROOT = ROOT
    out = capsys.readouterr().out
    assert "chạy 0 hồ sơ, loại 1" in out and "bỏ qua mau: data_kind SAMPLE" in out
    sheets = pd.read_excel(tmp_path / "out.xlsx", sheet_name=None)
    assert set(sheets) == {"Trạng thái", "Bỏ qua"}
    assert sheets["Trạng thái"].iloc[0]["Kết quả"] == "không có hồ sơ đủ điều kiện"


def test_gate_blocks_missing_architecture_drawing_and_directory_paths(tmp_path):
    """Hồ sơ ACTUAL–test đã kiểm nhưng chưa khai báo kien_truc, hoặc khai báo thư mục thay file, không được chạy."""
    ok = dict(split="test", dap_an_trang_thai="da_kiem", nguoi_kiem="KS. A")
    (tmp_path / "data/drawings/test").mkdir(parents=True)
    (tmp_path / "data/drawings/test/kt.dxf").write_text("bản vẽ giả: cổng chỉ kiểm là file", encoding="utf-8")
    rows = [_case("khong_kt", kien_truc="", **ok), _case("thu_muc", kien_truc="data/drawings/test", **ok),
            _case("du_toan_thu_muc", du_toan="gt", **ok), _case("du", kien_truc="data/drawings/test/kt.dxf", **ok)]
    path = _manifest(tmp_path, rows, files=False)
    for t in ("khong_kt", "thu_muc", "du"):
        (tmp_path / f"gt/{t}.csv").parent.mkdir(exist_ok=True)
        (tmp_path / f"gt/{t}.csv").write_text("stt\n", encoding="utf-8")
    findings, blocked = check_cases(path, tmp_path)
    msgs = {(f.item, f.message) for f in _errors(findings)}
    assert ("cases.csv dòng 3 (thu_muc)", "kien_truc: data/drawings/test không phải file.") in msgs
    assert ("cases.csv dòng 4 (du_toan_thu_muc)", "du_toan: gt không phải file.") in msgs
    assert "khong_kt" not in blocked                         # manifest cho phép chưa khai báo bản vẽ
    run, skipped = select_cases("bao_cao", path, tmp_path)
    assert [r["ten"] for r in run] == ["du"]
    why = dict(skipped)
    assert why["khong_kt"] == "chưa khai báo bản vẽ kiến trúc (kien_truc): evaluator không chạy được"
    assert "không phải file" in why["thu_muc"] and "không phải file" in why["du_toan_thu_muc"]


def test_stale_report_replaced_when_new_run_has_no_case(tmp_path, monkeypatch):
    """Đã có báo cáo cũ có số; lần chạy mới loại toàn bộ hồ sơ: file đầu ra là của lần mới, không còn số cũ."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_rough
    out = tmp_path / "out.xlsx"
    with pd.ExcelWriter(out) as xw:
        pd.DataFrame([{"bo": "cu", "cong_tac": 9, "lech_tb_pct": 4.2}]).to_excel(xw, sheet_name="Tong_hop", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(xw, sheet_name="cu", index=False)
    path = _manifest(tmp_path, [_case("t", split="test")])
    monkeypatch.setattr(evaluate_rough, "run_case", lambda *a: pytest.fail("không được chạy hồ sơ bị loại"))
    monkeypatch.setattr(sys, "argv", ["evaluate_rough.py", "--muc-dich", "phat_trien", "--cases", str(path), "--out", str(out)])
    evaluate_rough.ROOT = tmp_path
    try:
        evaluate_rough.main()
    finally:
        evaluate_rough.ROOT = ROOT
    sheets = pd.read_excel(out, sheet_name=None)
    assert set(sheets) == {"Trạng thái", "Bỏ qua"}
    st = sheets["Trạng thái"].iloc[0]
    assert st["Mục đích"] == "Phát triển" and st["Số hồ sơ đã chạy"] == 0 and st["Số hồ sơ bị loại"] == 1
    assert st["Kết quả"] == "không có hồ sơ đủ điều kiện"
    assert sheets["Bỏ qua"]["Bộ hồ sơ"].tolist() == ["t"]
