"""Tiếp nhận hồ sơ CAD: kiểm tra, lưu theo hash, chuyển DWG, kiểm kê đối tượng (S02).

    python scripts/ingest_cad.py data/sample/ingest                 # mọi .dxf, .dwg trong thư mục
    python scripts/ingest_cad.py a.dxf b.dwg --out reports/ingest --store data/uploads

Mỗi file ghi một <tên>.inventory.json vào --out (mặc định reports/ingest). --store: lưu bản gốc theo hash
kèm số phiên bản (manifest.jsonl). Mã thoát 1 nếu có file bị từ chối hoặc thất bại.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.drawing.ingest import ingest_file  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default=str(ROOT / "reports/ingest"))
    ap.add_argument("--store", default=None, help="thư mục lưu file gốc theo hash (bỏ trống: không lưu)")
    args = ap.parse_args()
    files = []
    for a in args.paths:
        p = Path(a)
        files += sorted(f for f in p.rglob("*") if f.is_file() and f.name != "expected.json") if p.is_dir() else [p]
    if not files:
        sys.exit("Không tìm thấy file nào.")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for f in files:
        res = ingest_file(f.name, f.read_bytes(), store_dir=Path(args.store) if args.store else None)
        (out / f"{f.name}.inventory.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        bad += res["status"] != "ok"
        codes = ", ".join(w["code"] for w in res["warnings"]) or "-"
        print(f"{res['status']:8} {f.name:32} entity={res['entity_total']:<6} layer={len(res['layers']):<4} "
              f"block={len(res['blocks']):<5} cảnh báo: {codes}")
    print(f"\n{len(files)} file, {bad} file bị từ chối hoặc thất bại. Kết quả: {out}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
