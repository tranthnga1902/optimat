"""Xuất trang quan sát khái niệm: định nghĩa của Quy ước bản vẽ v1.0 đặt cạnh kết quả đối chiếu trên một bản vẽ.

    python scripts/concept_report.py data/drawings/build/nha_dan.dxf --open
    python scripts/concept_report.py nha.dwg --height 3300 --layers "{\\"A-TUONG\\": \\"WALL\\"}" --json

Trang ghi cạnh bản vẽ (tên_ban_ve.khai_niem.html) hoặc vào --out. --json ghi thêm kết quả dạng JSON cùng tên.
"""
import argparse
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.drawing.concept_view import build_concept_html  # noqa: E402
from optimat.drawing.convention_check import analyze  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Đối chiếu bản vẽ với Quy ước bản vẽ v1.0")
    parser.add_argument("drawing", help="file .dxf hoặc .dwg")
    parser.add_argument("--height", type=float, help="chiều cao tầng (mm); bỏ trống thì suy từ cao độ trên bản vẽ")
    parser.add_argument("--layers", help='ghi đè vai trò layer, chuỗi JSON: {"tên layer": "WALL"}')
    parser.add_argument("--out", help="đường dẫn file HTML ghi ra")
    parser.add_argument("--json", action="store_true", help="ghi thêm kết quả JSON cạnh file HTML")
    parser.add_argument("--open", action="store_true", help="mở trang bằng trình duyệt sau khi ghi")
    args = parser.parse_args()

    path = Path(args.drawing)
    report = analyze(str(path), args.height, json.loads(args.layers) if args.layers else None)
    out = Path(args.out) if args.out else path.with_suffix(".khai_niem.html")
    out.write_text(build_concept_html(report), encoding="utf8")
    if args.json:
        out.with_suffix(".json").write_text(report.model_dump_json(indent=1), encoding="utf8")
    b = sum(1 for c in report.checks if c.trang_thai == "vi_pham" and c.muc == "B")
    k = sum(1 for c in report.checks if c.trang_thai == "vi_pham" and c.muc == "K")
    verdict = "không áp dụng" if report.trong_quy_uoc is None else "trong quy ước" if report.trong_quy_uoc else "ngoài quy ước"
    print(f"{report.file}: {verdict}; vi phạm B: {b}, K: {k}; {len(report.plans)} mặt bằng -> {out}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
