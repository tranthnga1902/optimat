"""Khảo sát bản vẽ để xây bộ quy tắc: tín hiệu nào đang có, tín hiệu nào chưa có quy tắc.

    python scripts/survey_drawings.py data/raw            # quét mọi file .dxf, .dwg trong thư mục
    python scripts/survey_drawings.py a.dxf b.dxf

Kết quả ghi vào reports/survey_*.csv. Dòng ghi "CHUA CO QUY TAC" và layer có vai trò UNKNOWN là chỗ cần
bổ sung vào data/rules/material_rules.csv hoặc src/optimat/drawing/layer_classifier.py.
Chỉ chạy trên nhóm bản vẽ dùng để xây quy tắc (split = build), không chạy trên nhóm kiểm tra.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.drawing.evaluate import survey  # noqa: E402


def main() -> None:
    args = sys.argv[1:] or [str(ROOT / "data/sample")]
    files = []
    for a in args:
        p = Path(a)
        files += sorted(str(f) for f in p.rglob("*") if f.suffix.lower() in (".dxf", ".dwg")) if p.is_dir() else [str(p)]
    if not files:
        sys.exit("Không tìm thấy file .dxf hoặc .dwg nào.")
    tables = survey(files)
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    print(f"Đã quét {len(files)} bản vẽ.")
    for name, df in tables.items():
        df.to_csv(out / f"survey_{name}.csv", index=False, encoding="utf-8-sig")
        missing = (df.ket_qua == "CHUA CO QUY TAC").sum() if "ket_qua" in df else (df.vai_tro == "UNKNOWN").sum()
        print(f"\n== {name}: {len(df)} giá trị, {missing} chưa có quy tắc")
        print(df.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
