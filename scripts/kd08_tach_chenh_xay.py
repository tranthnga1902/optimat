"""KD08: tách chênh lệch khối lượng XÂY giữa hệ thống và dự toán đối chứng thành 3 phần, theo từng tầng.

    python scripts/kd08_tach_chenh_xay.py [--case 46_nha_tan_binh] [--out reports/kd08]

1. Quy ước chiều cao: dự toán lấy cao trọn tầng, hệ thống trừ cao dầm (chiều cao xây thực).
2. Quy ước chiều dày: dự toán dày thực viên gạch (0,1 / 0,2 m), hệ thống dày danh nghĩa lớp (0,11 / 0,22 m).
3. Phần còn lại sau khi đưa hệ thống về quy ước của dự toán = chênh do HÌNH HỌC (chiều dài tường nhận được, lỗ mở).
Chỉ chạy hồ sơ build. Đối chứng là dự toán của người lập (chưa xác nhận), không phải đáp án nghiệm thu.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

from evaluate_rough import rough_for_case  # noqa: E402
from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.drawing.encoding import normalize  # noqa: E402
from optimat.drawing.registry import floors_of  # noqa: E402

ACTUAL_T = {"110": 0.10, "150": 0.15, "220": 0.20, "330": 0.30}   # dày thực theo cách ghi của dự toán bộ 46


def floor_key(text: str) -> list[str]:
    return floors_of(text) or [text.strip()]


def estimate_by_floor(case: str) -> dict[str, float]:
    """Dòng con 'phan' của XAY theo tầng ghi ở vi_tri/noi_dung; dòng ghi trục thì cùng tầng dòng trên;
    'Lầu 2-3-4' chia đều 3 tầng."""
    rows = pd.read_csv(ROOT / f"data/ground_truth/du_toan/d02/{case}/dap_an_cong_tac.csv", dtype=str, keep_default_na=False)
    out, place = defaultdict(float), ""
    for r in rows.itertuples():
        if r.quan_he_cha != "phan" or r.ma_pt != "PT32" or not r.khoi_luong:
            continue
        where = (r.vi_tri or r.noi_dung).strip()
        if not normalize(where).startswith(("truc", "tru ")):
            place = where
        floors = floor_key(place)
        for f in floors:
            out[f] += float(r.khoi_luong) / len(floors)
    return dict(out)


def system_by_floor(result, storey_m: dict[str, float]) -> dict[str, dict]:
    out = defaultdict(lambda: defaultdict(float))
    for w in result.works:
        g = w.masonry_geometry
        if w.code != "XAY" or g is None or not g.length_m:
            continue
        floors = floor_key(w.plan or "")
        f = floors[0]
        h_sys = g.gross_area_m2 / g.length_m
        cls = (g.wall_type or "").split()[0] if g.wall_type else next((c for c in ACTUAL_T if c in (w.element or "")), None)
        t_act = ACTUAL_T.get(cls, g.thickness_m)
        h_storey = storey_m.get(f, h_sys)
        out[f]["he_thong"] += w.quantity or 0.0
        out[f]["he_thong_du_hinh"] += (g.gross_area_m2 - g.opening_area_m2) * g.thickness_m
        out[f]["quy_uoc_cao"] += (g.length_m * h_storey - g.opening_area_m2) * g.thickness_m
        out[f]["quy_uoc_cao_day"] += (g.length_m * h_storey - g.opening_area_m2) * t_act
        out[f]["dai_m"] += g.length_m
        out[f]["thieu_so"] += 0 if w.quantity is not None else 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="46_nha_tan_binh")
    ap.add_argument("--out", default=str(ROOT / "reports" / "kd08"))
    a = ap.parse_args()
    case = next(r for r in csv.DictReader(open(ROOT / "data/ground_truth/du_toan/cases.csv", encoding="utf-8-sig"))
                if r["ten"] == a.case)
    if case["split"] != "build":
        sys.exit("KD08 chỉ chạy hồ sơ build (bộ test chỉ dùng báo cáo cuối).")
    params = json.loads((ROOT / case["thong_so"]).read_text(encoding="utf-8")) if case.get("thong_so") else {}
    result = rough_for_case(case, Catalog.load())
    est = estimate_by_floor(a.case)
    # chiều cao tầng của dự toán: trệt 3,4 m, lầu 3,0 m (đọc từ công thức dòng con của bộ 46; hồ sơ khác cần nhập)
    storey = {f: (3.4 if f in ("T1",) else 3.0) for f in set(est) | {floor_key(w.plan or "")[0] for w in result.works}}
    sys_ = system_by_floor(result, storey)
    rows = []
    for f in sorted(set(est) | set(sys_)):
        s = sys_.get(f, {})
        e = est.get(f)
        base = s.get("he_thong_du_hinh", 0.0)
        rows.append({"tang": f, "du_toan_m3": round(e, 3) if e is not None else None,
                     "he_thong_m3": round(s.get("he_thong", 0.0), 3), "he_thong_du_hinh_m3": round(base, 3),
                     "do_cao_m3": round(s.get("quy_uoc_cao", 0.0) - base, 3),
                     "do_day_m3": round(s.get("quy_uoc_cao_day", 0.0) - s.get("quy_uoc_cao", 0.0), 3),
                     "theo_quy_uoc_du_toan_m3": round(s.get("quy_uoc_cao_day", 0.0), 3),
                     "con_lai_hinh_hoc_m3": round(e - s.get("quy_uoc_cao_day", 0.0), 3) if e is not None else None,
                     "dai_tuong_m": round(s.get("dai_m", 0.0), 2), "dong_thieu_so": int(s.get("thieu_so", 0))})
    df = pd.DataFrame(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"{a.case}_xay.csv", index=False, encoding="utf-8-sig")
    print(df.to_string(index=False))
    tot = df.sum(numeric_only=True)
    print(f"\nTổng: dự toán {tot.du_toan_m3:.2f} | hệ thống đủ hình {tot.he_thong_du_hinh_m3:.2f} | do cao {tot.do_cao_m3:+.2f} "
          f"| do dày {tot.do_day_m3:+.2f} | còn lại (hình học) {tot.con_lai_hinh_hoc_m3:+.2f} m³")
    print("Ghi chú: thông số hồ sơ", ", ".join(k for k in params if not k.startswith("_")) or "(trống)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
