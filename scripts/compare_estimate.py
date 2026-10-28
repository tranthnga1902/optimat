"""So khối lượng phần thô bóc từ bản vẽ với dự toán thật (data/ground_truth/du_toan/*.csv).

    python scripts/compare_estimate.py data/ground_truth/du_toan/46_nha_tan_binh.csv kien_truc.dxf \
        --structural ket_cau.dwg [--params thong_so.json] [--out so_sanh.xlsx]

Gom theo mã công tác (cốp pha, cốt thép thêm cấu kiện). Dòng hệ thống "thiếu" là khối lượng chưa đủ (thông số trống,
Quy ước B7): số đã tính chỉ là một phần, không so lệch. Không dùng để chỉnh quy tắc trên bản vẽ nhóm test.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.rough.models import WORKS, ProjectParams  # noqa: E402
from optimat.rough.takeoff import compute_rough, rough_from_drawing  # noqa: E402
from optimat.schemas import OpeningDefaults  # noqa: E402


def compare(estimate: pd.DataFrame, works) -> pd.DataFrame:
    """estimate: cột ma_cong_tac, cau_kien, khoi_luong; works: WorkItem của compute_rough."""
    est = estimate[estimate.ma_cong_tac.fillna("") != ""].fillna({"cau_kien": ""})
    got: dict[tuple, list] = {}
    for w in works:
        elem = w.formwork_of if w.code == "COP_PHA" else w.steel_element if w.code == "COT_THEP" else ""
        got.setdefault((w.code, elem or ""), []).append(w.quantity)
    rows = []
    for (code, elem), g in est.groupby(["ma_cong_tac", "cau_kien"], sort=False):
        q = got.get((code, elem), [])
        known = [x for x in q if x is not None]
        sys_q = round(sum(known), 3) if known else None
        complete = bool(q) and len(known) == len(q)
        ref = round(g.khoi_luong.sum(), 3)
        rows.append({"ma_cong_tac": code, "cau_kien": elem, "ten": WORKS[code][0], "don_vi": WORKS[code][1],
                     "du_toan": ref, "he_thong": sys_q,
                     "trang_thai": "không có" if not q else "đủ" if complete else "thiếu",
                     "lech_pct": round((sys_q - ref) / ref * 100, 1) if complete and ref else None,
                     "ma_dinh_muc": ", ".join(sorted(set(g.ma_dinh_muc.astype(str))))})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="So khối lượng bóc từ bản vẽ với dự toán")
    ap.add_argument("estimate", help="CSV dự toán (data/ground_truth/du_toan)")
    ap.add_argument("drawing", help="bản vẽ kiến trúc")
    ap.add_argument("--structural", action="append", default=[], help="bản vẽ kết cấu (lặp lại được)")
    ap.add_argument("--params", help="file JSON thông số công trình")
    ap.add_argument("--out", help="file .xlsx ghi ra")
    a = ap.parse_args()
    raw = json.loads(Path(a.params).read_text(encoding="utf-8")) if a.params else {}
    # "openings": kích thước cửa của dự án (bảng projects), không thuộc ProjectParams
    openings = OpeningDefaults(**raw.pop("openings")) if "openings" in raw else None
    params = ProjectParams(**raw)
    catalog = Catalog.load()
    req = rough_from_drawing(read_drawing(a.drawing), params, None, catalog, Path(a.drawing).name, openings=openings,
                             structural=[read_drawing(s) for s in a.structural])
    table = compare(pd.read_csv(a.estimate, encoding="utf-8-sig"), compute_rough(req, catalog).works)
    print(table.drop(columns="ma_dinh_muc").to_string(index=False))
    if a.out:
        table.to_excel(a.out, index=False)
        print(f"Đã ghi {a.out}")


if __name__ == "__main__":
    main()
