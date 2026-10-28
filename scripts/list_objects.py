"""Liệt kê từng đối tượng nhận diện được trên bản vẽ: tường, cửa, cặp nét bị loại (kèm lý do) và block khớp
ký hiệu không phải cửa trong data/rules/concepts.csv (cột, cao độ, trục, nội thất...).

    python scripts/list_objects.py [file.dxf ...]

Không truyền file thì chạy data/sample/*.dxf và data/drawings/**/*.dxf.
Ghi reports/doi_tuong_nhan_dien.csv, in số đếm theo bản vẽ và mặt bằng.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.drawing.objects import COLS, list_objects  # noqa: E402


def rows_for(path: Path):
    return list_objects(read_drawing(str(path)), path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path))


def main() -> None:
    files = [Path(a).resolve() for a in sys.argv[1:]] or \
        sorted((ROOT / "data" / "sample").glob("*.dxf")) + sorted((ROOT / "data" / "drawings").rglob("*.dxf"))
    rows = []
    for f in files:
        try:
            got = list(rows_for(f))
        except Exception as e:  # một bản vẽ hỏng không làm dừng cả danh sách
            print(f"{f.name}: LỖI {e}")
            continue
        rows += got
        print(f"{f.name}: {len(got)} đối tượng")
        for (plan, kind), n in Counter((x["mat_bang"], x["loai"]) for x in got).items():
            print(f"    {plan} | {kind}: {n}")
    out = ROOT / "reports" / "doi_tuong_nhan_dien.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        wr = csv.DictWriter(fh, COLS)
        wr.writeheader()
        wr.writerows(rows)
    print(f"\nTổng {len(rows)} dòng: {dict(Counter(x['loai'] for x in rows))} -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
