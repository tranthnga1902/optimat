"""Đo độ chính xác nhận diện tường trên bản vẽ gốc so với đáp án người dùng đã sửa trên trang Kiểm tra bóc tách.

Đáp án: data/ground_truth/plans/<file>_<mặt bằng>.gt.json (nút "Lưu làm đáp án"), tọa độ theo hệ bản vẽ (mm).

Chỉ số, tính theo chiều dài trục tim:
    precision = phần chiều dài tường tự nhận nằm trùng tường đáp án / tổng chiều dài tự nhận
    recall    = phần chiều dài tường đáp án được tự nhận phủ / tổng chiều dài đáp án
    đúng loại = trong phần trùng, tỉ lệ chiều dài cùng lớp chiều dày (110, 150, 220, 330)
    sai số diện tích = (diện tích tự nhận - diện tích đáp án) / diện tích đáp án, cùng chiều cao tầng, chưa trừ cửa
Hai đoạn "trùng" khi song song (lệch dưới 3 độ) và trục tim cách nhau không quá TOL_MM.
Lỗi nhận thừa được chia theo lý do người dùng ghi khi loại tường (cầu thang, khung cửa...).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .. import config

GT_PLANS_DIR = config.DATA_DIR / "ground_truth" / "plans"
TOL_MM = 150.0
STEP_MM = 50.0
COS_MAX = math.cos(math.radians(3))


def _seg(w) -> tuple[float, float, float, float]:
    if isinstance(w, dict):
        return w["x1"], w["y1"], w["x2"], w["y2"]
    return w.x1, w.y1, w.x2, w.y2


def _cls(w) -> str:
    return w["cls"] if isinstance(w, dict) else w.thickness_class


def _covered_length(src: list, ref: list, same_class: bool = False) -> float:
    """Chiều dài của các đoạn src nằm trùng (song song, gần) một đoạn trong ref; lấy mẫu mỗi STEP_MM."""
    total = 0.0
    refs = []
    for r in ref:
        x1, y1, x2, y2 = _seg(r)
        L = math.hypot(x2 - x1, y2 - y1)
        if L > 0:
            refs.append((x1, y1, (x2 - x1) / L, (y2 - y1) / L, L, _cls(r)))
    for w in src:
        x1, y1, x2, y2 = _seg(w)
        L = math.hypot(x2 - x1, y2 - y1)
        if L <= 0:
            continue
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        n = max(1, int(L // STEP_MM))
        cand = [r for r in refs if abs(ux * r[2] + uy * r[3]) >= COS_MAX and (not same_class or r[5] == _cls(w))]
        hit = 0
        for k in range(n):
            t = (k + 0.5) * L / n
            px, py = x1 + ux * t, y1 + uy * t
            for rx, ry, rux, ruy, rL, _ in cand:
                s = (px - rx) * rux + (py - ry) * ruy
                if -TOL_MM <= s <= rL + TOL_MM and abs((px - rx) * (-ruy) + (py - ry) * rux) <= TOL_MM:
                    hit += 1
                    break
        total += L * hit / n
    return total


def _length(ws: list) -> float:
    return sum(math.hypot(x2 - x1, y2 - y1) for x1, y1, x2, y2 in map(_seg, ws))


def _absolute_walls(result, bbox) -> list:
    """Tường tự nhận của một mặt bằng: tọa độ đã ở hệ bản vẽ (mm)."""
    return [w for w in result.walls if w.is_masonry]


def evaluate_plan(gt: dict, auto_walls: list) -> dict:
    gt_walls = gt["walls"]
    L_auto, L_gt = _length(auto_walls), _length(gt_walls)
    tp_auto = _covered_length(auto_walls, gt_walls)
    tp_gt = _covered_length(gt_walls, auto_walls)
    same = _covered_length(auto_walls, gt_walls, same_class=True)
    H = gt.get("height_mm") or config.DEFAULT_FLOOR_HEIGHT_MM
    fp_by_reason: dict[str, float] = {}
    for r in gt.get("removed", []):
        fp_by_reason[r.get("reason", "khác")] = fp_by_reason.get(r.get("reason", "khác"), 0.0) + _length([r]) / 1000
    missed = [w for w in gt_walls if w.get("src") == "manual"]
    return {
        "file": gt["file"], "plan": gt["plan"],
        "auto_m": round(L_auto / 1000, 2), "gt_m": round(L_gt / 1000, 2),
        "precision": round(tp_auto / L_auto, 3) if L_auto else None,
        "recall": round(tp_gt / L_gt, 3) if L_gt else None,
        "class_ok": round(same / tp_auto, 3) if tp_auto else None,
        "area_err": round((L_auto - L_gt) / L_gt, 3) if L_gt else None,
        "area_auto_m2": round(L_auto * H / 1e6, 2), "area_gt_m2": round(L_gt * H / 1e6, 2),
        "missed_m": round(_length(missed) / 1000, 2), "fp_by_reason_m": {k: round(v, 2) for k, v in fp_by_reason.items()},
    }


def load_ground_truth(folder: Path | str | None = None) -> list[dict]:
    folder = Path(folder or GT_PLANS_DIR)
    return [json.loads(p.read_text(encoding="utf8")) for p in sorted(folder.glob("*.gt.json"))]


def find_drawing(file_name: str, roots: list[Path] | None = None) -> Path | None:
    roots = roots or [config.DATA_DIR / "drawings" / "build", config.DATA_DIR / "drawings" / "test", config.DATA_DIR / "sample"]
    for r in roots:
        p = r / file_name
        if p.exists():
            return p
    return None


def evaluate_all(folder: Path | str | None = None, roots: list[Path] | None = None) -> list[dict]:
    """Chạy lại nhận diện trên từng bản vẽ có đáp án và so sánh. Bản vẽ không tìm thấy thì báo, không bỏ qua im lặng."""
    from .dxf_reader import read_drawing
    from .takeoff import takeoff_plans
    gts = load_ground_truth(folder)
    rows, cache = [], {}
    for gt in gts:
        path = find_drawing(gt["file"], roots)
        if path is None:
            rows.append({"file": gt["file"], "plan": gt["plan"], "error": "không tìm thấy bản vẽ trong data/drawings"})
            continue
        if path not in cache:
            cache[path] = takeoff_plans(read_drawing(str(path)))
        plans = cache[path]
        match = next((p for p in plans if p.name == gt["plan"]), None)
        if match is None and len(plans) == 1:
            match = plans[0]
        if match is None:
            rows.append({"file": gt["file"], "plan": gt["plan"], "error": "không tách được mặt bằng có tên này"})
            continue
        rows.append(evaluate_plan(gt, _absolute_walls(match.result, match.bbox)))
    return rows


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    L_auto = sum(r["auto_m"] for r in ok)
    L_gt = sum(r["gt_m"] for r in ok)
    tp_a = sum(r["auto_m"] * (r["precision"] or 0) for r in ok)
    tp_g = sum(r["gt_m"] * (r["recall"] or 0) for r in ok)
    reasons: dict[str, float] = {}
    for r in ok:
        for k, v in r["fp_by_reason_m"].items():
            reasons[k] = round(reasons.get(k, 0.0) + v, 2)
    return {"plans": len(ok), "errors": len(rows) - len(ok),
            "precision": round(tp_a / L_auto, 3) if L_auto else None,
            "recall": round(tp_g / L_gt, 3) if L_gt else None,
            "area_err": round((L_auto - L_gt) / L_gt, 3) if L_gt else None,
            "fp_by_reason_m": dict(sorted(reasons.items(), key=lambda kv: -kv[1]))}
