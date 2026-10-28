"""Demo S07: từ một hay nhiều bản vẽ DXF/DWG ra Excel BOQ phần thô có dòng nguồn.

    python scripts/export_boq.py kien_truc.dxf --structural ket_cau.dxf [--structural thep.dxf] --height 3300 \
        --params thong_so.json --out boq.xlsx

Bản vẽ đầu là kiến trúc (mặt bằng tầng); --structural nhận nhiều file (mặt bằng móng/dầm, bảng thống kê thép, mái).
--params: file JSON thông số công trình (ProjectParams); thiếu số thì BOQ để trống kèm missing_reason.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.rough.boq import boq_workbook  # noqa: E402
from optimat.rough.models import ProjectParams  # noqa: E402
from optimat.rough.takeoff import compute_rough, rough_from_drawing  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Xuất BOQ phần thô ra Excel")
    ap.add_argument("drawing", help="bản vẽ kiến trúc .dxf/.dwg")
    ap.add_argument("--structural", action="append", default=[], help="bản vẽ kết cấu (lặp lại được)")
    ap.add_argument("--height", type=float, help="chiều cao tầng (mm)")
    ap.add_argument("--scale", type=float, help="hệ số tỷ lệ mặt bằng kết cấu (vẽ phóng to 2 lần: 0.5)")
    ap.add_argument("--params", help="file JSON thông số công trình")
    ap.add_argument("--out", help="file .xlsx ghi ra (mặc định cạnh bản vẽ)")
    a = ap.parse_args()
    params = ProjectParams(**json.loads(Path(a.params).read_text(encoding="utf-8"))) if a.params else ProjectParams()
    catalog = Catalog.load()
    req = rough_from_drawing(read_drawing(a.drawing), params, a.height, catalog, Path(a.drawing).name,
                             structural=[read_drawing(s) for s in a.structural], structural_scale=a.scale)
    result = compute_rough(req, catalog)
    out = Path(a.out or Path(a.drawing).with_suffix(".boq.xlsx"))
    boq_workbook(result, req).save(out)
    blank = sum(1 for w in result.works if w.quantity is None)
    print(f"Đã ghi {out}: {len(result.works)} dòng công tác ({blank} để trống), {len(req.rebar)} dòng thép, "
          f"{len(result.warnings)} cảnh báo.")


if __name__ == "__main__":
    main()
