"""Chuyển sheet khối lượng của một dự toán Excel (.xlsx) sang CSV đáp án dạng data/ground_truth/du_toan/*.csv.

    python scripts/import_estimate.py du_toan.xlsx --sheet "Bang khoi luong" --first-col 2 --encoding vni --out data/ground_truth/du_toan/<tên>.csv

Dòng công tác: ô đầu là số thứ tự và ô thứ hai là mã định mức (hoặc TT); các dòng sau đến công tác kế là diễn giải.
Chữ VNI / TCVN3 được đổi sang Unicode. ma_cong_tac, cau_kien gắn theo tên công tác (mã định mức khác nhau giữa các bộ
định mức cũ nên không dùng mã); không khớp thì để trống = ngoài phạm vi phần thô. Kết quả cần người xem lại từng dòng.
File .xls cũ: mở bằng Excel và lưu thành .xlsx trước.
"""
import argparse
import sys
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.drawing.encoding import tcvn3_to_unicode, to_unicode, vni_to_unicode  # noqa: E402
from optimat.rough.estimate_check import classify  # noqa: E402

FORCE = {"vni": vni_to_unicode, "tcvn3": tcvn3_to_unicode}

UNITS = {"100m2": ("m²", 100), "100m3": ("m³", 100), "100m": ("m", 100), "m3": ("m³", 1), "m2": ("m²", 1),
         "tấn": ("tấn", 1), "m": ("m", 1)}
def text(v, enc: str = "auto") -> str:
    """Ô Excel -> chữ Unicode; enc: auto (đoán từng ô, ô ngắn dễ đoán sai) | vni | tcvn3 (cả file một bảng mã)."""
    if v is None:
        return ""
    return (FORCE[enc](str(v)) if enc in FORCE else to_unicode(str(v))[0]).strip()


def rows_of(path: Path, sheet: str, first_col: int = 1, enc: str = "auto") -> list[dict]:
    t = lambda v: text(v, enc)  # noqa: E731
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)[sheet]
    out: list[dict] = []
    for r in ws.iter_rows(values_only=True):
        cells = list(r)[first_col - 1:] + [None] * 6
        stt, code = cells[0], t(cells[1])
        if isinstance(stt, (int, float)) and code and isinstance(cells[5], (int, float)):
            name, unit = t(cells[2]), t(cells[3]).lower().replace(" ", "")
            u, k = UNITS.get(unit, (unit, 1))
            mc, ck = classify(name)
            out.append({"stt": int(stt), "ma_dinh_muc": code, "ten_cong_tac": name, "don_vi_goc": t(cells[3]),
                        "khoi_luong_goc": cells[5], "don_vi": u, "khoi_luong": round(cells[5] * k, 4),
                        "ma_cong_tac": mc, "cau_kien": ck, "dien_giai": []})
        elif out:
            line = " ".join(t(c) for c in cells[:5] if t(c))
            if line:
                out[-1]["dien_giai"].append(line)
    for o in out:
        o["dien_giai"] = " | ".join(o["dien_giai"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("xlsx")
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--encoding", default="auto", choices=["auto", "vni", "tcvn3"], help="bảng mã chữ của file")
    ap.add_argument("--first-col", type=int, default=1, help="cột chứa số thứ tự (A = 1, B = 2)")
    a = ap.parse_args()
    df = pd.DataFrame(rows_of(Path(a.xlsx), a.sheet, a.first_col, a.encoding))
    if df.empty:
        sys.exit("Không nhận được dòng công tác nào: kiểm tra --sheet và --first-col.")
    df.to_csv(a.out, index=False, encoding="utf-8-sig")
    print(f"Đã ghi {a.out}: {len(df)} công tác, {(df.ma_cong_tac != '').sum()} gắn mã phần thô.")


if __name__ == "__main__":
    main()
