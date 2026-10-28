"""Kiểm soát dữ liệu trước khi phát triển tiếp hoặc chạy thực nghiệm.

    python scripts/check_data.py              # in tóm tắt, ghi reports/data_check.md và reports/data_check.json
    python scripts/check_data.py --strict     # coi cảnh báo như lỗi (dùng trước khi chốt số liệu báo cáo)

Mã thoát: 0 = không có lỗi, 1 = có lỗi (hoặc có cảnh báo khi --strict). Hook pre-commit trong .githooks gọi script này.
Kiểm tra trực tiếp PostgreSQL; cần DATABASE_URL (có thể đặt trong .env).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.data_check import run_checks, to_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="cảnh báo cũng làm thoát mã 1")
    parser.add_argument("--quiet", action="store_true", help="chỉ in dòng kết quả")
    parser.add_argument("--out-dir", default=str(ROOT / "reports"), help="thư mục ghi báo cáo (mặc định reports/)")
    args = parser.parse_args()
    try:
        report = run_checks()
    except RuntimeError as exc:
        print(f"Không thể kiểm soát dữ liệu: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "data_check.md").write_text(to_markdown(report), encoding="utf8")
    (out / "data_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    c = report["counts"]
    print(f"Kiểm soát dữ liệu: {c['error']} lỗi, {c['warning']} cảnh báo, {c['info']} ghi chú. Chi tiết: {out / 'data_check.md'}")
    if not args.quiet:
        for f in report["findings"]:
            if f["level"] == "error" or args.strict and f["level"] == "warning":
                print(f"  [{f['level']}] {f['area']} · {f['item']}: {f['message']}")
    failed = c["error"] > 0 or (args.strict and c["warning"] > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
