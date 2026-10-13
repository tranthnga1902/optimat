"""Đo sai số đo bóc trên bộ bản vẽ có đáp án, và khảo sát tín hiệu trong bản vẽ để xây quy tắc.

Quy trình bóc tách bằng quy tắc:
  1. Chọn 3-5 công trình làm nhóm "build": chạy survey, xem tín hiệu nào chưa có quy tắc, bổ sung
     vào data/rules/material_rules.csv và drawing/layer_classifier.py, lặp lại đến khi sai số ổn.
  2. Giữ 5-10 công trình khác làm nhóm "test": KHÔNG xem khi sửa quy tắc, chỉ chạy evaluate để lấy
     số báo cáo. Sửa quy tắc theo nhóm test sẽ làm kết quả đẹp giả.

Đáp án nằm trong data/ground_truth/:
  index.csv : drawing_file, split (build | test), floor_height_mm
  walls.csv : drawing_file, wall_type, length_m, net_area_m2, material_id (bóc tách thủ công)
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from .. import config
from .dxf_reader import read_drawing
from .encoding import normalize
from .layer_classifier import LayerClass
from .material_rules import MATERIAL_HINTS, _best, all_rules, rule_label
from .takeoff import takeoff_from_file

GT_DIR = config.DATA_DIR / "ground_truth"


def evaluate(gt_dir: Path | str | None = None, root: Path | str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trả về (bảng chi tiết từng nhóm tường, bảng tổng hợp theo split)."""
    gt_dir, root = Path(gt_dir or GT_DIR), Path(root or config.ROOT)
    index = pd.read_csv(gt_dir / "index.csv")
    truth = pd.read_csv(gt_dir / "walls.csv", dtype={"wall_type": str})
    rows = []
    for item in index.itertuples():
        result = takeoff_from_file(str(root / item.drawing_file), float(item.floor_height_mm))
        got = {g.wall_type: g for g in result.groups}
        expected = truth[truth.drawing_file == item.drawing_file]
        for t in expected.itertuples():
            g = got.get(t.wall_type)
            area = g.net_area_m2 if g else 0.0
            length = g.length_m if g else 0.0
            rows.append({
                "drawing_file": item.drawing_file, "split": item.split, "wall_type": t.wall_type,
                "length_true": t.length_m, "length_got": length,
                "length_err_%": round((length - t.length_m) / t.length_m * 100, 2),
                "area_true": t.net_area_m2, "area_got": area,
                "area_err_%": round((area - t.net_area_m2) / t.net_area_m2 * 100, 2),
                "material_true": t.material_id, "material_got": g.design_material_id if g else None,
                "material_ok": bool(g and g.design_material_id == t.material_id),
                "detected": g is not None,
            })
        for wall_type in set(got) - set(expected.wall_type):
            rows.append({"drawing_file": item.drawing_file, "split": item.split, "wall_type": wall_type,
                         "length_true": 0.0, "length_got": got[wall_type].length_m, "area_true": 0.0,
                         "area_got": got[wall_type].net_area_m2, "material_got": got[wall_type].design_material_id,
                         "material_ok": False, "detected": True, "note": "nhận diện thừa: không có trong đáp án"})
    detail = pd.DataFrame(rows)
    scored = detail[detail.area_true > 0]
    summary = scored.groupby("split").agg(
        so_ban_ve=("drawing_file", "nunique"), so_nhom_tuong=("wall_type", "count"),
        MAPE_dien_tich=("area_err_%", lambda s: round(s.abs().mean(), 2)),
        sai_so_lon_nhat=("area_err_%", lambda s: round(s.abs().max(), 2)),
        ty_le_dung_vat_lieu=("material_ok", lambda s: round(s.mean() * 100, 1)),
        ty_le_nhan_dien=("detected", lambda s: round(s.mean() * 100, 1)),
    ).reset_index()
    return detail, summary


def survey(paths: list[str]) -> dict[str, pd.DataFrame]:
    """Thống kê layer, hatch, block và ghi chú vật liệu trong các bản vẽ, đánh dấu tín hiệu chưa có quy tắc."""
    rules = all_rules()
    layers, hatches, blocks, texts = Counter(), Counter(), Counter(), Counter()
    layer_role: dict[str, str] = {}
    for path in paths:
        d = read_drawing(path)
        for name in {s.layer for s in d.segments} | {h.layer for h in d.hatches} | {b.layer for b in d.blocks}:
            layers[name] += 1
            layer_role[name] = d.layer_classes.get(name, LayerClass.UNKNOWN).value
        for h in d.hatches:
            hatches[h.pattern] += 1
        for b in d.blocks:
            blocks[b.name] += 1
        for t in d.texts:
            if any(k in normalize(t.text) for k in MATERIAL_HINTS):
                texts[t.text.strip()[:100]] += 1

    def frame(counter, signal, key=lambda v: v):
        data = []
        for value, n in counter.most_common():
            rule = _best(rules, signal, key(value))
            data.append({"gia_tri": value, "so_lan": n, "quy_tac": rule.rule_id if rule else "",
                         "ket_qua": rule_label(rule) if rule else "CHUA CO QUY TAC"})
        return pd.DataFrame(data, columns=["gia_tri", "so_lan", "quy_tac", "ket_qua"])

    return {
        "layers": pd.DataFrame([{"layer": k, "so_ban_ve": n, "vai_tro": layer_role[k]} for k, n in layers.most_common()],
                               columns=["layer", "so_ban_ve", "vai_tro"]),
        "hatches": frame(hatches, "hatch"),
        "blocks": frame(blocks, "block"),
        "texts": frame(texts, "text", normalize),
    }
