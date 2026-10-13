"""Đo sai số đo bóc trên bộ bản vẽ có đáp án (data/ground_truth).

    python scripts/evaluate_takeoff.py

In bảng tổng hợp theo nhóm build và test, ghi chi tiết vào reports/takeoff_eval.csv.
Số của nhóm test là số đưa vào báo cáo đồ án.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.drawing.evaluate import evaluate  # noqa: E402


def main() -> None:
    detail, summary = evaluate()
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    detail.to_csv(out / "takeoff_eval.csv", index=False, encoding="utf-8-sig")
    cols = ["drawing_file", "split", "wall_type", "area_true", "area_got", "area_err_%", "material_true", "material_got", "material_ok"]
    print(detail[[c for c in cols if c in detail]].to_string(index=False))
    print("\nTổng hợp theo nhóm:")
    print(summary.to_string(index=False))
    if "test" not in set(summary.split):
        print("\nChưa có bản vẽ nào thuộc nhóm test: các số trên chưa dùng để báo cáo được.")


if __name__ == "__main__":
    main()
