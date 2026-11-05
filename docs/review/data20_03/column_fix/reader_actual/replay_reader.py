"""Chạy reader KC thật ngoại tuyến từ repo; không nạp oracle hoặc ghi DB."""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time

os.environ["OPTIMAT_NO_DOTENV"] = "1"
os.environ.pop("DATABASE_URL", None)
os.environ.pop("OPTIMAT_TEST_DATABASE_URL", None)
sys.path.insert(0, str(Path.cwd() / "src"))

import ezdxf
from ezdxf import units
from optimat.drawing.dxf_reader import Drawing, declared_insunits, _check_units
from optimat.rough.structural_column_instances import read_column_instances, instance_column_works


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--structural", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    files = [args.structural, args.architecture, Path("src/optimat/rough/structural_column_instances.py"),
             Path("src/optimat/rough/structural.py"), Path("src/optimat/rough/takeoff.py"),
             Path("src/optimat/drawing/dxf_reader.py"), Path("src/optimat/rough/columns.py"),
             Path("data/rules/ky_hieu_cau_kien.csv"), Path("data/rules/loai_ban_ve.csv"),
             Path("data/rules/nguong_nhan_dien.csv")]

    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

    before = hashes()
    (args.out / "hash_before.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    logging.basicConfig(filename=args.out / "cad_warnings.log", encoding="utf-8", level=logging.WARNING, force=True)
    started = time.monotonic()
    doc = ezdxf.readfile(args.structural)
    insunits = declared_insunits(doc, str(args.structural))
    scale = units.conversion_factor(insunits, units.MM) if insunits else 1.0
    warnings = []
    scale = _check_units(doc, scale, warnings)
    if not insunits:
        warnings.append("Nguồn không khai báo INSUNITS; hệ số được đối chiếu DIM theo cùng hàm reader sản xuất.")
    # Reader này chỉ tiêu thụ doc và unit_scale; không chạy lại tường/KT hoặc tạo hình học từ đáp án.
    drawing = Drawing(segments=[], texts=[], blocks=[], hatches=[], layers=[], layer_classes={},
                      unit_scale=scale, warnings=warnings, doc=doc)
    instances = read_column_instances(drawing, [])
    works = instance_column_works(instances)
    data = dict(adapter="production column reader consuming native doc and canonical unit_scale; not full project/API",
                architecture_role="manifest/hash only; architectural takeoff not rerun",
                structural_source=str(args.structural), source_sha256=before[str(args.structural)],
                architecture_source=str(args.architecture), architecture_sha256=before[str(args.architecture)],
                insunits=insunits, unit_scale=scale, warnings=warnings,
                structural_columns=[s.model_dump(mode="json") for s in instances],
                works=[w.model_dump(mode="json") for w in works], elapsed_seconds=time.monotonic()-started)
    (args.out / "reader.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    after = hashes()
    (args.out / "hash_after.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
    diff = {"changed": [p for p in before if before[p] != after[p]]}
    (args.out / "hash_diff.json").write_text(json.dumps(diff, indent=2), encoding="utf-8")
    receipt = dict(exit_code=0, instances=len(instances), known_gross=sum(w.quantity_detail.rows[0].raw_quantity is not None
                   for w in works if w.code == "COT"), elapsed_seconds=data["elapsed_seconds"], **diff)
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
