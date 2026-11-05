"""Báo cáo sai số phần thô theo cấu kiện × trạng thái dữ liệu (đặc tả 30/10/2026 mục 7, 11) trên mọi bộ có đáp án.

    python scripts/evaluate_rough.py [--muc-dich phat_trien | bao_cao] [--cases data/ground_truth/du_toan/cases.csv]
                                     [--out reports/danh_gia_phan_tho.xlsx]

cases.csv: manifest hồ sơ (cột và quy ước: data/ground_truth/du_toan/README.md). Hồ sơ được chọn ở lối vào bằng
optimat.data_check.select_cases (D01): phat_trien (mặc định) chỉ chạy split build, mọi data_kind, kết quả ghi nhãn
phát triển; bao_cao chỉ chạy ACTUAL + test + đáp án đã có người kiểm. Hồ sơ lỗi manifest, thiếu bản vẽ cục bộ hoặc
không đủ điều kiện bị loại kèm lý do (sheet Bỏ qua), không âm thầm đổi split/data_kind. File --out luôn bị
ghi đè bởi lần chạy mới (sheet Trạng thái), kể cả khi không có hồ sơ đủ điều kiện.
Mỗi bộ chạy compute_rough rồi so với đáp án bằng compare() của compare_estimate.py. Chỉ tiêu "< 10%" chỉ tính trên dòng
trạng thái A, B (mục 3, quy tắc 4); dòng C, D báo riêng. Đáp án hiện là dự toán thật (không phải đo tay): phạm vi, quy
tắc bóc của người lập có thể khác, nên con số là đối chứng, chưa phải sai số đo tay. Sheet: Tổng hợp, Theo trạng thái, mỗi bộ.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from compare_estimate import compare  # noqa: E402
from report_labels import SHEETS, display  # noqa: E402
from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.data_check import CASE_PURPOSES, select_cases  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.rough.models import ProjectParams  # noqa: E402
from optimat.rough.takeoff import compute_rough, rough_from_drawing  # noqa: E402
from optimat.schemas import OpeningDefaults  # noqa: E402

TARGET_PCT = 10.0


def rough_for_case(case: dict, catalog: Catalog):
    """Kết quả compute_rough của một hồ sơ trong manifest (dùng chung với scripts/c01_duong_co_so.py)."""
    raw = json.loads((ROOT / case["thong_so"]).read_text(encoding="utf-8")) if case.get("thong_so") else {}
    openings = OpeningDefaults(**raw.pop("openings")) if "openings" in raw else None
    raw.pop("_ghi_chu", None)
    structural = [read_drawing(str(ROOT / case["ket_cau"]))] if case.get("ket_cau") else []
    req = rough_from_drawing(read_drawing(str(ROOT / case["kien_truc"])), ProjectParams(**raw), None, catalog, case["ten"],
                             openings=openings, structural=structural)
    return compute_rough(req, catalog)


def run_case(case: dict, catalog: Catalog) -> pd.DataFrame:
    table = compare(pd.read_csv(ROOT / case["du_toan"], encoding="utf-8-sig"), rough_for_case(case, catalog).works)
    return table.assign(bo=case["ten"], split=case["split"], data_kind=case.get("data_kind", ""))


def summarize(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tổng hợp theo bộ × nhóm trạng thái (A/B tính chỉ tiêu, C/D báo riêng, không có số)."""
    d = rows.copy()
    d["nhom_trang_thai"] = d.status.map(lambda s: "A/B" if s in ("A", "B") else "C/D" if s in ("C", "D") else "không có số")
    d["abs_lech"] = d.lech_pct.abs()
    by_status = (d.groupby(["bo", "split", "nhom_trang_thai"], dropna=False)
                 .agg(so_dong=("ma_cong_tac", "size"), co_so=("lech_pct", "count"), lech_tb_pct=("abs_lech", "mean"),
                      dat_10pct=("abs_lech", lambda s: int((s <= TARGET_PCT).sum())))
                 .reset_index())
    by_status["lech_tb_pct"] = by_status.lech_tb_pct.round(1)
    summary = (d.groupby(["bo", "split"])
               .agg(cong_tac=("ma_cong_tac", "size"), co_so=("lech_pct", "count"), lech_tb_pct=("abs_lech", "mean"),
                    dat_10pct=("abs_lech", lambda s: int((s <= TARGET_PCT).sum())))
               .reset_index())
    summary["lech_tb_pct"] = summary.lech_tb_pct.round(1)
    return summary, by_status


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--muc-dich", choices=CASE_PURPOSES, default="phat_trien",
                    help="phat_trien: chỉ build, ghi nhãn phát triển; bao_cao: chỉ ACTUAL-test có đáp án đã kiểm")
    ap.add_argument("--cases", default=str(ROOT / "data/ground_truth/du_toan/cases.csv"))
    ap.add_argument("--out", default=str(ROOT / "reports/danh_gia_phan_tho.xlsx"))
    a = ap.parse_args()
    cases, skipped = select_cases(a.muc_dich, a.cases, ROOT)
    label = "PHÁT TRIỂN (không phải chỉ tiêu nghiệm thu)" if a.muc_dich == "phat_trien" else "BÁO CÁO CHỈ TIÊU CHÍNH (ACTUAL–test)"
    print(f"Mục đích: {label}; chạy {len(cases)} hồ sơ, loại {len(skipped)}.")
    for ten, why in skipped:
        print(f"  bỏ qua {ten}: {why}")
    per = {}
    if cases:
        catalog = Catalog.load()
        per = {c["ten"]: run_case(c, catalog) for c in cases}
    else:
        print("Không có hồ sơ đủ điều kiện: chưa có số để báo cáo.")
    # luôn ghi đè --out bằng lần chạy này (kể cả khi không có hồ sơ) để không còn số của lần trước
    state = pd.DataFrame([{"muc_dich": a.muc_dich, "thoi_diem": datetime.now().isoformat(timespec="seconds"),
                           "ho_so_chay": len(per), "ho_so_loai": len(skipped),
                           "ket_qua": "có số" if per else "không có hồ sơ đủ điều kiện"}])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(a.out) as xw:
        display(state).to_excel(xw, sheet_name=SHEETS["Trang_thai"], index=False)
        if per:
            rows = pd.concat(per.values(), ignore_index=True)
            summary, by_status = (t.assign(muc_dich=a.muc_dich) for t in summarize(rows))   # nhãn mục đích trên sheet tổng
            print(summary.to_string(index=False))
            print()
            print(by_status.to_string(index=False))
            display(summary).to_excel(xw, sheet_name=SHEETS["Tong_hop"], index=False)
            display(by_status).to_excel(xw, sheet_name=SHEETS["Theo_trang_thai"], index=False)
        display(pd.DataFrame(skipped, columns=["bo", "ly_do"]).assign(muc_dich=a.muc_dich)).to_excel(xw, sheet_name=SHEETS["Bo_qua"], index=False)
        for number, t in enumerate(per.values(), start=1):
            display(t).to_excel(xw, sheet_name=f"Hồ sơ {number}", index=False)
    print(f"Đã ghi {a.out}")


if __name__ == "__main__":
    main()
