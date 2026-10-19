"""Phần thô S6b: API bóc phần thô."""
import json

from fastapi.testclient import TestClient

from optimat.api.main import app

client = TestClient(app)


def test_rough_auto_then_confirm(sample_dxf):
    params = {"slab_thickness_mm": 100, "beam_depth_mm": 400, "concrete_supply": "ready_mix", "concrete_grade": "M250"}
    with open(sample_dxf, "rb") as f:
        r = client.post("/api/takeoff/rough/auto", files={"file": ("mau.dxf", f)},
                        data={"floor_height_mm": "3300", "params": json.dumps(params)})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["request"]["plans"] and any(t["code"] == "XAY" for t in body["result"]["totals"])
    req = body["request"]
    req["plans"][0]["walls"][0]["keep"] = False                    # người dùng loại một tường
    req["plans"][0]["void_area_m2"] = 0
    conf = client.post("/api/takeoff/rough", json=req)
    assert conf.status_code == 200, conf.text
    xay = lambda b: next(t for t in b["totals"] if t["code"] == "XAY")["quantity"]   # noqa: E731
    assert xay(conf.json()) < xay(body["result"])


def test_rough_rejects_bad_input(sample_dxf):
    with open(sample_dxf, "rb") as f:
        r = client.post("/api/takeoff/rough/auto", files={"file": ("mau.dxf", f)}, data={"params": "{không phải json"})
    assert r.status_code == 400
    bad = client.post("/api/takeoff/rough", json={"plans": [{"name": "T1", "height_mm": 300, "walls": []}],
                                                  "params": {"beam_depth_mm": 400}})
    assert bad.status_code == 422


def test_review_page_has_rough_tab_and_payload_has_columns(sample_dxf):
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.drawing.takeoff import takeoff_plans
    from optimat.drawing.viewer import view_payload
    page = client.get("/ui/takeoff").text
    assert 'data-tab="rough"' in page and "/api/takeoff/rough" in page
    d = read_drawing(sample_dxf)
    p = view_payload(d, takeoff_plans(d, 3300), "mau.dxf", cad=False)["plans"][0]
    assert "columns" in p and "labels" in p and "is_ground" in p["plan"]
    assert "phan-tho" in client.get("/app").text
