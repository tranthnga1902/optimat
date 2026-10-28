"""Chạy nhận diện + bóc phần thô trên nhiều bản vẽ một lần, gộp báo cáo để thấy chỗ bộ nhận diện chưa tổng quát.

    python scripts/batch_takeoff.py "D:/Bo cong trinh" a.dxf b.dxf [--height 3300] [--out reports/batch]

Mỗi bản vẽ chạy độc lập (không ghép kiến trúc với kết cấu), thông số công trình để trống (Quy ước B7): công tác thiếu
số sẽ trống kèm lý do. Kết quả: reports/batch/tong_hop.xlsx gồm các sheet
    Doi_tuong   mỗi bản vẽ một dòng: loại bản vẽ, mặt bằng, tường, cửa, cột, dầm, móng, thang, bảng thép...
    Cong_tac    mã công tác × bản vẽ: số đã tính / "trống" / không có
    Ly_do_trong lý do công tác trống, đếm qua mọi bản vẽ (chỗ cần bổ sung định mức, thông số hoặc quy tắc)
    Canh_bao    cảnh báo đọc bản vẽ, đếm qua mọi bản vẽ
    Chi_tiet    mọi dòng công tác
Chỉ chỉnh quy tắc theo bản vẽ build; bản vẽ test chỉ để báo cáo.
"""
import argparse
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.rough.models import ProjectParams  # noqa: E402
from optimat.rough.takeoff import compute_rough, rough_from_drawing  # noqa: E402


def _pattern(msg: str) -> str:
    """Gom cảnh báo, lý do cùng dạng: bỏ số, mã cấu kiện, tên trong ngoặc kép."""
    msg = re.sub(r"\"[^\"]*\"|«[^»]*»", "«…»", msg)
    msg = re.sub(r"\b[A-ZĐ]{1,3}\d+[a-z]?\b", "X", msg)
    return re.sub(r"\d+(?:[.,]\d+)?", "#", msg).strip()


def run_one(path: Path, height, catalog) -> tuple[dict, list[dict], list[str]]:
    t0 = time.time()
    drawing = read_drawing(str(path))
    req = rough_from_drawing(drawing, ProjectParams(), height, catalog, path.name)
    res = compute_rough(req, catalog)
    plans = [p for p in req.plans if p.name != "Toàn bộ bản vẽ"]
    walls = [w for p in req.plans for w in p.walls]
    by_cls = Counter()
    for w in walls:
        by_cls[w.cls] += ((w.x2 - w.x1) ** 2 + (w.y2 - w.y1) ** 2) ** 0.5 / 1000
    found = Counter(r for p in req.plans for r in p.found)
    row = {
        "ban_ve": path.name,
        "loai_ban_ve": ", ".join(s["loai_ban_ve"] for s in req.sheets if s["co"]),
        "mat_bang": len(plans),
        "ten_mat_bang": "; ".join(p.name for p in plans),
        "co_chieu_cao": sum(p.height_mm is not None for p in req.plans),
        "tuong": len(walls),
        **{f"tuong_{c}_m": round(v, 1) for c, v in sorted(by_cls.items())},
        "cua": sum(len(p.openings) for p in req.plans),
        "cot": sum(len(p.columns) for p in req.plans),
        "phong": sum(len(p.labels) for p in req.plans),
        "dam_ket_cau": sum(len(v) for v in req.structural_beams.values()),
        "mong": ", ".join(f"{f.name}×{f.count}" + ("" if f.length_mm and f.width_mm and f.height_mm else "?")
                          for f in req.params.foundations),
        "tiet_dien_cot": ", ".join(f"{k}" for k in sorted(req.column_sections)),
        "dong_thep": len(req.rebar),
        "giang_seno": len(req.members),
        **{f"thay_{k.lower()}": v for k, v in sorted(found.items())},
        "cong_tac": len(res.works),
        "cong_tac_trong": sum(w.quantity is None for w in res.works),
        "vat_lieu": len(res.materials),
        "vat_lieu_thieu": sum(not m.complete for m in res.materials),
        "canh_bao": len(req.notes) + len(res.warnings),
        "giay": round(time.time() - t0, 1),
        "loi": "",
    }
    works = [{"ban_ve": path.name, "mat_bang": w.plan, "ma": w.code, "cong_tac": w.name, "cau_kien": w.element,
              "bien_the": w.variant, "don_vi": w.unit, "khoi_luong": w.quantity, "co_so": w.basis,
              "cong_thuc": w.formula, "thieu": " | ".join(w.missing)} for w in res.works]
    return row, works, req.notes + res.warnings


def main() -> None:
    ap = argparse.ArgumentParser(description="Bóc phần thô hàng loạt, gộp báo cáo")
    ap.add_argument("paths", nargs="+", help="file .dxf/.dwg hoặc thư mục (quét đệ quy)")
    ap.add_argument("--height", type=float, help="chiều cao tầng (mm) dùng chung, trống: đọc từ cao độ sàn")
    ap.add_argument("--out", default=str(ROOT / "reports/batch"))
    a = ap.parse_args()
    files = []
    for s in a.paths:
        p = Path(s)
        files += sorted(f for f in p.rglob("*") if f.suffix.lower() in (".dxf", ".dwg")) if p.is_dir() else [p]
    # file DWG đã có bản DXF cùng thư mục (xuất qua phần mềm xem nhanh) thì bỏ, khỏi đọc hai lần
    def key(f: Path) -> str:
        return re.sub(r"[\s_]+", "_", f.stem.lower())
    dxf = {(f.parent, key(f)) for f in files if f.suffix.lower() == ".dxf"}
    files = [f for f in files if f.suffix.lower() == ".dxf"
             or not any(d == f.parent and k.startswith(key(f)) for d, k in dxf)]
    if not files:
        sys.exit("Không tìm thấy file .dxf hoặc .dwg nào.")
    catalog = Catalog.load()
    rows, works, warns = [], [], Counter()
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name} ...", flush=True)
        try:
            row, w, notes = run_one(f, a.height, catalog)
            works += w
            warns.update((_pattern(n), f.name) for n in notes)
        except Exception as e:  # một bản vẽ lỗi không dừng cả loạt
            row = {"ban_ve": f.name, "loi": f"{type(e).__name__}: {e}"}
            traceback.print_exc()
        rows.append(row)
        print(f"    {row.get('mat_bang', '-')} mặt bằng, {row.get('tuong', '-')} tường, "
              f"{row.get('cong_tac_trong', '-')}/{row.get('cong_tac', '-')} công tác trống {row['loi']}", flush=True)

    objs = pd.DataFrame(rows)
    detail = pd.DataFrame(works)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out / "tong_hop.xlsx") as xw:
        objs.to_excel(xw, sheet_name="Doi_tuong", index=False)
        if not detail.empty:
            d = detail.assign(gia_tri=detail.khoi_luong.map(lambda q: "trống" if pd.isna(q) else "có số"))
            piv = d.pivot_table(index=["ma", "cong_tac"], columns="ban_ve", values="gia_tri",
                                aggfunc=lambda s: "có số" if (s == "có số").all() else
                                "trống" if (s == "trống").all() else f"{(s == 'có số').sum()}/{len(s)} có số")
            piv.to_excel(xw, sheet_name="Cong_tac")
            reasons, seen = Counter(), {}
            for _, r in d[d.thieu != ""].iterrows():
                for m in r.thieu.split(" | "):
                    reasons[(r.ma, _pattern(m))] += 1
                    seen.setdefault((r.ma, _pattern(m)), set()).add(r.ban_ve)
            pd.DataFrame([{"ma": k[0], "ly_do": k[1], "so_dong": v, "so_ban_ve": len(seen[k])}
                          for k, v in reasons.most_common()]).to_excel(xw, sheet_name="Ly_do_trong", index=False)
            detail.to_excel(xw, sheet_name="Chi_tiet", index=False)
        per = Counter(k[0] for k in warns)
        pd.DataFrame([{"canh_bao": k, "so_ban_ve": v} for k, v in per.most_common()]).to_excel(xw, sheet_name="Canh_bao", index=False)
    print(f"\nĐã ghi {out / 'tong_hop.xlsx'}: {len(files)} bản vẽ, {sum(bool(r['loi']) for r in rows)} lỗi.")


if __name__ == "__main__":
    main()
