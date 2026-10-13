"""Xuất trang Kiểm tra bóc tách (bản vẽ bên trái, danh sách nhận dạng bên phải; sửa, bổ sung, xác nhận)
cho một bản vẽ. Thêm --steps để xuất trang 5 bước giải thích thuật toán.

    python scripts/view_takeoff.py data/drawings/build/H01_T1.dxf --height 3300
    python scripts/view_takeoff.py nha.dwg --height 3600 --layers "{\\"A-TUONG\\": \\"WALL\\"}" --open

Trang được ghi cạnh bản vẽ (tên_ban_ve.takeoff.html) hoặc vào --out. Mở bằng trình duyệt bất kỳ.
Trang dùng đúng mã đo bóc của hệ thống, nên những gì thấy trên trang là kết quả thật của bản vẽ đó.
"""
import argparse
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.drawing.takeoff import compute_takeoff, takeoff_plans  # noqa: E402
from optimat.drawing.viewer import build_review_html, build_viewer_html  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Xem trực quan quá trình bóc tách một bản vẽ")
    parser.add_argument("drawing", help="file .dxf hoặc .dwg")
    parser.add_argument("--height", type=float, help="chiều cao tầng (mm); bỏ trống thì suy từ cao độ trên bản vẽ hoặc mặc định")
    parser.add_argument("--layers", help='ghi đè vai trò layer, chuỗi JSON: {"tên layer": "WALL"}')
    parser.add_argument("--out", help="đường dẫn file HTML ghi ra")
    parser.add_argument("--steps", action="store_true", help="trang 5 bước giải thích thuật toán thay cho trang kiểm tra")
    parser.add_argument("--whole", action="store_true", help="đo cả bản vẽ như một mặt bằng, không tách theo tiêu đề")
    parser.add_argument("--open", action="store_true", help="mở trang bằng trình duyệt sau khi ghi")
    args = parser.parse_args()

    path = Path(args.drawing)
    drawing = read_drawing(str(path), json.loads(args.layers) if args.layers else None)
    catalog = Catalog.load()
    if args.whole:
        result = compute_takeoff(drawing, args.height, catalog)
        summary = f"{len(result.walls)} đoạn tường, {len(result.openings)} lỗ mở"
    else:
        result = takeoff_plans(drawing, args.height, catalog)
        if not result:
            print("Bản vẽ chỉ có mặt bằng kết cấu, móng hoặc điện nước, không có mặt bằng kiến trúc để đo tường. "
                  "Dùng --whole nếu vẫn muốn đo cả bản vẽ.")
            return
        summary = "; ".join(f"{p.name}: {len(p.result.walls)} đoạn tường" for p in result)
    out = Path(args.out) if args.out else path.with_suffix(".takeoff.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    build = build_viewer_html if args.steps else build_review_html
    out.write_text(build(drawing, result, path.name), encoding="utf8")
    print(f"Đã ghi {out}: {summary}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
