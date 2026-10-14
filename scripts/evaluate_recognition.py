"""Đo độ chính xác nhận diện tường trên bản vẽ gốc so với đáp án đã sửa tay.

    python scripts/evaluate_recognition.py

Đáp án lấy từ data/ground_truth/plans/*.gt.json (nút "Lưu làm đáp án" trên trang Kiểm tra bóc tách);
bản vẽ tìm trong data/drawings/build, data/drawings/test. Ghi reports/recognition_eval.md và .csv.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from optimat.drawing.recognition_eval import evaluate_all, summarize  # noqa: E402


def pct(v):
    return "" if v is None else f"{v * 100:.1f}%"


def main() -> int:
    rows = evaluate_all()
    if not rows:
        print("Chưa có đáp án nào trong data/ground_truth/plans. Sửa một mặt bằng trên trang kiểm tra rồi bấm \"Lưu làm đáp án\".")
        return 1
    s = summarize(rows)
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "recognition_eval.csv", index=False)
    lines = ["# Độ chính xác nhận diện tường", "",
             f"{s['plans']} mặt bằng có đáp án · precision {pct(s['precision'])} · recall {pct(s['recall'])} · "
             f"sai số chiều dài (≈ diện tích, chưa trừ cửa) {pct(s['area_err'])}", "",
             "| Bản vẽ | Mặt bằng | Tự nhận m | Đáp án m | Precision | Recall | Đúng loại | Sai số | Sót (vẽ thêm) m |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['file']} | {r['plan']} | lỗi: {r['error']} | | | | | | |")
        else:
            lines.append(f"| {r['file']} | {r['plan']} | {r['auto_m']} | {r['gt_m']} | {pct(r['precision'])} | {pct(r['recall'])} | "
                         f"{pct(r['class_ok'])} | {pct(r['area_err'])} | {r['missed_m']} |")
    lines += ["", "## Nhận thừa theo lý do (m)", "", "| Lý do | m |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in s["fp_by_reason_m"].items()]
    (out / "recognition_eval.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines[:3]))
    print(f"Chi tiết: {out / 'recognition_eval.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
