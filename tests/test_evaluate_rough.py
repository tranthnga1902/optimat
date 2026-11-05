"""Báo cáo sai số theo trạng thái (S13c): chỉ dòng A/B tính chỉ tiêu 10%, dòng C/D và dòng không có số báo riêng."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_rough import summarize  # noqa: E402


def test_summary_splits_status_groups():
    rows = pd.DataFrame([
        {"bo": "x", "split": "build", "ma_cong_tac": "XAY", "status": "B", "lech_pct": -5.0},
        {"bo": "x", "split": "build", "ma_cong_tac": "SAN", "status": "A", "lech_pct": 20.0},
        {"bo": "x", "split": "build", "ma_cong_tac": "DAM", "status": "C", "lech_pct": 8.0},
        {"bo": "x", "split": "build", "ma_cong_tac": "CAU_THANG", "status": None, "lech_pct": None}])
    summary, by_status = summarize(rows)
    ab = by_status[by_status.nhom_trang_thai == "A/B"].iloc[0]
    assert ab.so_dong == 2 and ab.dat_10pct == 1 and ab.lech_tb_pct == 12.5
    assert set(by_status.nhom_trang_thai) == {"A/B", "C/D", "không có số"}
    assert summary.iloc[0].cong_tac == 4 and summary.iloc[0].co_so == 3

def test_populated_workbook_labels(tmp_path, monkeypatch):
    import evaluate_rough as report

    case = {"ten": "46_nha_tan_binh"}
    rows = pd.DataFrame([{"bo": case["ten"], "split": "build", "ma_cong_tac": "XAY",
                          "status": "B", "lech_pct": -5.0}])
    out = tmp_path / "đối chứng.xlsx"
    monkeypatch.setattr(sys, "argv", ["evaluate_rough", "--out", str(out)])
    monkeypatch.setattr(report, "select_cases", lambda *args: ([case], []))
    monkeypatch.setattr(report.Catalog, "load", lambda: None)
    monkeypatch.setattr(report, "run_case", lambda *args: rows)
    report.main()

    sheets = pd.read_excel(out, sheet_name=None)
    assert list(sheets) == ["Trạng thái", "Tổng hợp", "Theo trạng thái", "Bỏ qua", "Hồ sơ 1"]
    detail = sheets["Hồ sơ 1"].iloc[0]
    assert detail["Bộ hồ sơ"] == case["ten"] and detail["Độ lệch (%)"] == -5
    assert sheets["Theo trạng thái"].iloc[0]["Nhóm trạng thái"] == "A/B"
    assert detail["Trạng thái dữ liệu"] == "B"
    assert detail["Tập dữ liệu"] == "build"
    assert rows.iloc[0]["status"] == "B"


def test_labels_apply_only_to_the_displayed_column():
    from report_labels import display

    raw = pd.DataFrame({"id": ["cho_kiem", "nhap"], "trang_thai_kiem": ["cho_kiem", "nhap"],
                        "pham_vi": ["IN", "hon_hop"], "so_duoc": [False, True],
                        "doi_chung": [0.0, None]})
    original = raw.copy()
    exported = display(raw)
    assert exported["Trạng thái kiểm tra"].tolist() == ["Chờ kiểm tra", "Nháp"]
    assert exported["Phạm vi"].tolist() == ["IN", "Hỗn hợp"]
    assert exported["Có thể so sánh"].tolist() == ["Không", "Có"]
    assert exported["Mã dòng"].tolist() == original.id.tolist()
    pd.testing.assert_series_equal(exported["Đối chứng"], original.doi_chung, check_names=False)
    pd.testing.assert_frame_equal(raw, original)
