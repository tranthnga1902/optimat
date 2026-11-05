"""Chạy nhận diện + bóc phần thô trên nhiều bản vẽ một lần, gộp báo cáo để thấy chỗ bộ nhận diện chưa tổng quát.

    python scripts/batch_takeoff.py "D:/Bo cong trinh" a.dxf b.dxf [--height 3300] [--params thong_so.json] [--out reports/batch] [--jobs 4]

Mỗi bản vẽ chạy độc lập (không ghép kiến trúc với kết cấu). Thông số công trình để trống (Quy ước B7): công tác thiếu
số sẽ trống kèm lý do; --params: một file JSON ProjectParams dùng chung cho mọi bản vẽ (số người dùng chọn, trạng thái C),
ví dụ data/sample/thong_so_mau.json. --jobs N: chạy N bản vẽ cùng lúc trên N tiến trình (mỗi tiến trình nạp danh mục một lần);
mặc định 1 (tuần tự, in log theo thứ tự). Kết quả: reports/batch/tong_hop.xlsx gồm các sheet
    Đối tượng   mỗi bản vẽ một dòng: loại bản vẽ, mặt bằng, tường, cửa, cột, dầm, móng, thang, bảng thép...
    Công tác    mã công tác × bản vẽ: số đã tính / "trống" / không có
    Lý do trống lý do công tác trống, đếm qua mọi bản vẽ (chỗ cần bổ sung định mức, thông số hoặc quy tắc)
    Cảnh báo    cảnh báo đọc bản vẽ, đếm qua mọi bản vẽ
    Chi tiết    mọi dòng công tác
Chỉ chỉnh quy tắc theo bản vẽ build; bản vẽ test chỉ để báo cáo.
"""
import argparse
import json
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


_CATALOG = None


def _catalog():
    """Danh mục nạp một lần cho mỗi tiến trình (tiến trình con của --jobs cũng chỉ nạp một lần)."""
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = Catalog.load()
    return _CATALOG


def _run_safe(args: tuple) -> tuple[Path, dict, list[dict], list[str]]:
    """Một bản vẽ, không ném lỗi (dùng được trong tiến trình con): lỗi ghi vào dòng kết quả."""
    path, height, params = args
    try:
        row, works, notes = run_one(path, height, _catalog(), params)
    except Exception as e:  # một bản vẽ lỗi không dừng cả loạt
        row, works, notes = {"ban_ve": path.name, "loi": f"{type(e).__name__}: {e}"}, [], []
        traceback.print_exc()
    row.setdefault("loi", "")
    return path, row, works, notes


def run_one(path: Path, height, catalog, params: ProjectParams | None = None) -> tuple[dict, list[dict], list[str]]:
    t0 = time.time()
    drawing = read_drawing(str(path))
    req = rough_from_drawing(drawing, params or ProjectParams(), height, catalog, path.name)
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


# Nhãn trong báo cáo Excel. Khóa xử lý nội bộ vẫn dùng để nhóm và đối chiếu.
COLUMN_LABELS = {
    "ban_ve": "Bản vẽ", "loai_ban_ve": "Loại bản vẽ", "mat_bang": "Mặt bằng",
    "ten_mat_bang": "Tên mặt bằng", "co_chieu_cao": "Có chiều cao", "tuong": "Tường",
    "cua": "Cửa", "cot": "Cột", "phong": "Phòng", "dam_ket_cau": "Dầm kết cấu",
    "mong": "Móng", "tiet_dien_cot": "Tiết diện cột", "dong_thep": "Dòng thép",
    "giang_seno": "Giằng, sê nô", "cong_tac": "Công tác", "cong_tac_trong": "Công tác trống",
    "vat_lieu": "Vật liệu", "vat_lieu_thieu": "Vật liệu thiếu", "canh_bao": "Cảnh báo",
    "giay": "Thời gian (giây)", "loi": "Lỗi", "ma": "Mã", "cau_kien": "Cấu kiện",
    "bien_the": "Biến thể", "don_vi": "Đơn vị", "khoi_luong": "Khối lượng",
    "co_so": "Cơ sở", "cong_thuc": "Công thức", "thieu": "Thông tin còn thiếu",
    "ly_do": "Lý do", "so_dong": "Số dòng", "so_ban_ve": "Số bản vẽ",
}


def column_label(key: str) -> str:
    if key.startswith("tuong_") and key.endswith("_m"):
        return f"Tường {key[6:-2]} (m)"
    if key.startswith("thay_"):
        return f"Đã nhận diện ({key[5:].upper()})"
    return COLUMN_LABELS[key]


def main() -> None:
    ap = argparse.ArgumentParser(description="Bóc phần thô hàng loạt, gộp báo cáo")
    ap.add_argument("paths", nargs="+", help="file .dxf/.dwg hoặc thư mục (quét đệ quy)")
    ap.add_argument("--height", type=float, help="chiều cao tầng (mm) dùng chung, trống: đọc từ cao độ sàn")
    ap.add_argument("--out", default=str(ROOT / "reports/batch"))
    ap.add_argument("--jobs", type=int, default=1, help="số bản vẽ chạy cùng lúc (tiến trình); 1 = tuần tự")
    ap.add_argument("--params", help="file JSON thông số công trình dùng chung (ProjectParams)")
    a = ap.parse_args()
    params = ProjectParams(**json.loads(Path(a.params).read_text(encoding="utf-8"))) if a.params else None
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
    rows, works, warns = [], [], Counter()
    t_all = time.time()
    jobs = max(1, min(a.jobs, len(files)))
    tasks = [(f, a.height, params) for f in files]
    if jobs == 1:
        results = map(_run_safe, tasks)
    else:
        from concurrent.futures import ProcessPoolExecutor
        pool = ProcessPoolExecutor(max_workers=jobs)
        results = pool.map(_run_safe, tasks)          # giữ thứ tự file; mỗi tiến trình con nạp danh mục một lần
    for i, (f, row, w, notes) in enumerate(results, 1):
        works += w
        warns.update((_pattern(n), f.name) for n in notes)
        rows.append(row)
        print(f"[{i}/{len(files)}] {f.name}: {row.get('mat_bang', '-')} mặt bằng, {row.get('tuong', '-')} tường, "
              f"{row.get('cong_tac_trong', '-')}/{row.get('cong_tac', '-')} công tác trống, {row.get('giay', '-')} s {row['loi']}",
              flush=True)
    if jobs > 1:
        pool.shutdown()
    print(f"Tổng {time.time() - t_all:.1f} s với --jobs {jobs}.", flush=True)

    objs = pd.DataFrame(rows)
    detail = pd.DataFrame(works)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out / "tong_hop.xlsx") as xw:
        objs.rename(columns=column_label).to_excel(xw, sheet_name="Đối tượng", index=False)
        if not detail.empty:
            d = detail.assign(gia_tri=detail.khoi_luong.map(lambda q: "trống" if pd.isna(q) else "có số"))
            piv = d.pivot_table(index=["ma", "cong_tac"], columns="ban_ve", values="gia_tri",
                                aggfunc=lambda s: "có số" if (s == "có số").all() else
                                "trống" if (s == "trống").all() else f"{(s == 'có số').sum()}/{len(s)} có số")
            piv.rename_axis(index=["Mã", "Công tác"], columns="Bản vẽ").to_excel(xw, sheet_name="Công tác")
            reasons, seen = Counter(), {}
            for _, r in d[d.thieu != ""].iterrows():
                for m in r.thieu.split(" | "):
                    reasons[(r.ma, _pattern(m))] += 1
                    seen.setdefault((r.ma, _pattern(m)), set()).add(r.ban_ve)
            pd.DataFrame([{"ma": k[0], "ly_do": k[1], "so_dong": v, "so_ban_ve": len(seen[k])}
                          for k, v in reasons.most_common()], columns=["ma", "ly_do", "so_dong", "so_ban_ve"]).rename(columns=column_label).to_excel(xw, sheet_name="Lý do trống", index=False)
            detail.rename(columns=column_label).to_excel(xw, sheet_name="Chi tiết", index=False)
        per = Counter(k[0] for k in warns)
        pd.DataFrame([{"canh_bao": k, "so_ban_ve": v} for k, v in per.most_common()], columns=["canh_bao", "so_ban_ve"]).rename(columns=column_label).to_excel(xw, sheet_name="Cảnh báo", index=False)
    print(f"\nĐã ghi {out / 'tong_hop.xlsx'}: {len(files)} bản vẽ, {sum(bool(r['loi']) for r in rows)} lỗi.")


if __name__ == "__main__":
    main()
