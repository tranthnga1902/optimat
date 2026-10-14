"""Đo độ chính xác nhận diện so với đáp án người dùng sửa tay."""
import json

import ezdxf
from fastapi.testclient import TestClient

from optimat.drawing import recognition_eval as ev
from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.takeoff import takeoff_plans


def _gt_from(plan, file_name, drop_last=False, add=None):
    walls = [{"id": w.wall_id, "cls": w.thickness_class, "role": w.role, "x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2,
              "src": "auto"} for w in plan.result.walls]
    removed = []
    if drop_last:
        removed.append({**walls.pop(), "reason": "cầu thang"})
    if add:
        walls.append(add)
    return {"file": file_name, "plan": plan.name, "height_mm": 3000, "walls": walls, "removed": removed}


def test_perfect_and_imperfect_scores(sample_dxf):
    plan = takeoff_plans(read_drawing(sample_dxf), 3300)[0]
    auto = [w for w in plan.result.walls if w.is_masonry]
    r = ev.evaluate_plan(_gt_from(plan, "s.dxf"), auto)
    assert r["precision"] == 1.0 and r["recall"] == 1.0 and r["class_ok"] == 1.0 and r["area_err"] == 0.0
    # người dùng loại một tường (nhận thừa) và vẽ thêm một tường 3 m bị sót
    extra = {"id": "M1", "cls": "110", "role": "partition", "x1": 50000, "y1": 50000, "x2": 53000, "y2": 50000, "src": "manual"}
    r = ev.evaluate_plan(_gt_from(plan, "s.dxf", drop_last=True, add=extra), auto)
    assert r["precision"] < 1.0 and r["recall"] < 1.0 and r["missed_m"] == 3.0 and "cầu thang" in r["fp_by_reason_m"]


def test_evaluate_all_and_api(sample_dxf, tmp_path, monkeypatch):
    plan = takeoff_plans(read_drawing(sample_dxf))[0]
    monkeypatch.setattr(ev, "GT_PLANS_DIR", tmp_path)
    from optimat.api.main import app
    body = _gt_from(plan, "sample_floor.dxf")
    r = TestClient(app).post("/api/ground-truth", json=body)
    assert r.status_code == 200 and r.json()["path"].endswith(".gt.json")
    saved = list(tmp_path.glob("*.gt.json"))
    assert len(saved) == 1 and json.loads(saved[0].read_text(encoding="utf8"))["plan"] == plan.name
    rows = ev.evaluate_all(tmp_path)
    assert rows[0]["precision"] == 1.0 and ev.summarize(rows)["recall"] == 1.0


def test_ladder_pairs_rejected(tmp_path):
    """Bậc thang (nét song song cách đều 280) không bị nhận thành tường 330; tường thật bên cạnh vẫn nhận."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for k in range(6):                                      # 6 bậc rộng 1000, cách nhau 280
        msp.add_line((0, k * 280), (1000, k * 280), dxfattribs={"layer": "TUONG"})
    msp.add_line((3000, 0), (3000, 4000), dxfattribs={"layer": "TUONG"})
    msp.add_line((3220, 0), (3220, 4000), dxfattribs={"layer": "TUONG"})
    path = tmp_path / "t.dxf"
    doc.saveas(path)
    d = read_drawing(str(path))
    plan = takeoff_plans(d, 3000)[0]
    assert [w.thickness_class for w in plan.result.walls] == ["220"]
    assert any(r["reason"] == "bậc thang / lan can" for r in plan.result.rejected)
