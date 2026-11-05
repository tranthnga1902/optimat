"""Đo thời gian đọc bản vẽ và gán vật liệu trên một mặt bằng tổng hợp lớn (tự dựng), để so trước/sau khi tối ưu.

    python scripts/benchmark_material_rules.py [--walls 400] [--repeat 5] [--file <bản vẽ thật.dxf>]

Bản vẽ tự dựng: lưới tường 220 / 110, mỗi tường một ghi chú viết tắt, một hatch ANSI31 bị phá thành nét rời (như bản vẽ
xuất qua phần mềm xem nhanh). Đo riêng từng bước: read_drawing, compute_takeoff (gồm apply_material_rules), và
apply_material_rules gọi lặp (như takeoff_plans gọi cho từng mặt bằng) có / không có cache quy tắc.
Số đo chỉ để so tương đối trên cùng máy; ghi vào NHAT_KY.md khi thay đổi mã.
"""
import argparse
import statistics
import sys
import time
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimat.catalog.repository import Catalog  # noqa: E402
from optimat.drawing import material_rules as mr  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.drawing.takeoff import compute_takeoff  # noqa: E402

NOTES = ["Tường 220 xây gạch kg nung", "xây gạch bt", "T. 110 xây gạch đặc", "vữa XM mác 75", "sàn BTCT dày 120"]


def make_drawing(path: Path, walls: int) -> None:
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    doc.layers.add("TUONG")
    doc.layers.add("GHICHU")
    msp = doc.modelspace()
    per_row = max(1, int(walls ** 0.5))
    for k in range(walls):
        r, c = divmod(k, per_row)
        x0, y0 = c * 6000.0, r * 5000.0
        t = 220 if k % 3 else 110
        msp.add_line((x0, y0), (x0 + 4000, y0), dxfattribs={"layer": "TUONG"})
        msp.add_line((x0, y0 + t), (x0 + 4000, y0 + t), dxfattribs={"layer": "TUONG"})
        if k % 4 == 0:   # hatch bị phá: nét xiên cách đều 40 mm
            for off in range(0, 4000, 40):
                msp.add_line((x0 + off, y0), (x0 + off + t, y0 + t), dxfattribs={"layer": "0"})
        msp.add_text(NOTES[k % len(NOTES)], dxfattribs={"layer": "GHICHU", "height": 150}).set_placement((x0, y0 + 600))
    doc.saveas(path)


def timed(fn, repeat: int) -> tuple[float, float]:
    ts = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts), min(ts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--walls", type=int, default=400)
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--file", help="đo trên bản vẽ thật thay cho bản vẽ tự dựng")
    a = ap.parse_args()
    if a.file:
        path = Path(a.file)
    else:
        path = ROOT / "reports" / "benchmark_mat_bang.dxf"
        path.parent.mkdir(exist_ok=True)
        make_drawing(path, a.walls)
    catalog = Catalog.load()

    med, best = timed(lambda: read_drawing(str(path)), a.repeat)
    print(f"read_drawing         : trung vị {med:.3f} s, nhanh nhất {best:.3f} s")
    drawing = read_drawing(str(path))
    print(f"  {len(drawing.segments)} nét, {len(drawing.texts)} chữ, {len(drawing.hatches)} vùng hatch "
          f"({sum(h.synthetic for h in drawing.hatches)} dựng lại từ nét rời)")

    med, best = timed(lambda: compute_takeoff(drawing, 3300, catalog), a.repeat)
    res = compute_takeoff(drawing, 3300, catalog)
    print(f"compute_takeoff      : trung vị {med:.3f} s, nhanh nhất {best:.3f} s "
          f"({len(res.walls)} tường, {sum(w.material_source != 'none' for w in res.walls)} có căn cứ vật liệu, "
          f"nguồn: {sorted({w.material_source for w in res.walls})})")

    walls = [w.model_copy() for w in res.walls]

    def rules_cached():
        mr.apply_material_rules(drawing, [w.model_copy() for w in walls], catalog)

    def rules_uncached():
        mr.clear_rule_cache()
        mr.apply_material_rules(drawing, [w.model_copy() for w in walls], catalog)

    med_u, _ = timed(rules_uncached, a.repeat)
    med_c, _ = timed(rules_cached, a.repeat)
    print(f"apply_material_rules : không cache {med_u:.3f} s, có cache {med_c:.3f} s mỗi lần gọi "
          f"(x{med_u / med_c if med_c else float('inf'):.1f})")
    mr.clear_rule_cache()


if __name__ == "__main__":
    main()
