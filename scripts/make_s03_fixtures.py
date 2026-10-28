"""Sinh bộ bản vẽ con chuẩn S03 (dữ liệu SYNTHETIC) từ data/ground_truth/s03/cases.json.

Mỗi ca là một bản vẽ nhỏ dựng bằng ezdxf để kiểm một tình huống ghép hồ sơ (tiết diện ghi chữ, thiếu chi tiết, xung đột,
đa tầng, lệch phiên bản, ký hiệu lạ...); đáp án viết tay nằm trong khóa "expect" của cùng file, không sinh từ mã.
Chỉ dùng để kiểm thử quy tắc, không dùng để báo cáo độ chính xác (CLAUDE.md: dữ liệu SYNTHETIC).

    python scripts/make_s03_fixtures.py            # ghi data/drawings/s03/<ca>.dxf
    python scripts/make_s03_fixtures.py --schema   # sinh lại docs/schema/ho_so_chuan_hoa.schema.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/ground_truth/s03/cases.json"
OUT = ROOT / "data/drawings/s03"


def load_cases() -> list[dict]:
    """Ca có "entities_from" dùng lại hình của ca khác (cùng bản vẽ, khác thao tác người dùng)."""
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    by_name = {c["name"]: c for c in cases}
    return [{**c, "entities": by_name[c["entities_from"]]["entities"]} if "entities_from" in c else c for c in cases]


def build(case: dict) -> ezdxf.document.Drawing:
    """Thực thể của ca: ["text", chữ, x, y, cao, layer], ["line", x1, y1, x2, y2, layer],
    ["beam", x1, y, x2, rộng] (hai nét song song trên layer DAM), ["hdim", x1, x2, y, y_chữ] (kích thước ngang)."""
    doc = ezdxf.new(setup=True)
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for e in case["entities"]:
        kind, *a = e
        if kind == "text":
            msp.add_text(a[0], height=a[3], dxfattribs={"layer": a[4], "insert": (a[1], a[2])})
        elif kind == "line":
            msp.add_line((a[0], a[1]), (a[2], a[3]), dxfattribs={"layer": a[4]})
        elif kind == "beam":
            x1, y, x2, w = a
            msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "DAM"})
            msp.add_line((x1, y + w), (x2, y + w), dxfattribs={"layer": "DAM"})
        elif kind == "hdim":
            msp.add_linear_dim(base=(a[0], a[3]), p1=(a[0], a[2]), p2=(a[1], a[2]),
                               override={"dimlfac": 1}, dxfattribs={"layer": "DIM"}).render()
        else:
            raise ValueError(f"{case['name']}: thực thể lạ {kind}")
    return doc


def main(out: Path = OUT) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for case in load_cases():
        path = out / f"{case['name']}.dxf"
        build(case).saveas(path)
        paths.append(path)
    return paths


def write_schema() -> Path:
    """Lược đồ JSON của hồ sơ chuẩn hóa (drawing/registry.py Registry) -> docs/schema/ho_so_chuan_hoa.schema.json."""
    sys.path.insert(0, str(ROOT / "src"))
    from optimat.drawing.registry import Registry
    path = ROOT / "docs/schema/ho_so_chuan_hoa.schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(Registry.model_json_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    if sys.argv[1:] == ["--schema"]:
        print(write_schema())
    else:
        for p in main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT):
            print(p)
