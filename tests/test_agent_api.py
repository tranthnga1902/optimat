from fastapi.testclient import TestClient

from optimat.agent.llm import parse_with_regex
from optimat.agent.pipeline import run_pipeline
from optimat.api.main import app

client = TestClient(app)


def test_parse_regex():
    p = parse_with_regex("Ngõ nhà tôi chỉ xe 2,5 tấn vào được, ngân sách phần tường 150 triệu, cần hàng trong 1 tuần. "
                         "Tôi không muốn dùng gạch nung.")
    assert p.max_vehicle_ton == 2.5
    assert p.budget == 150e6
    assert p.deadline_days == 7
    assert p.excluded_materials == ["CLAY_SOLID", "CLAY_HOLLOW"]
    assert parse_with_regex("không dùng gạch bê tông khí").excluded_materials == ["AAC"]
    assert parse_with_regex("Ngân sách 150.000.000 đ").budget == 150e6
    assert parse_with_regex("xe 1.5 tấn").max_vehicle_ton == 1.5


def test_pipeline(sample_dxf):
    state = run_pipeline(sample_dxf, message="xe 2,5 tấn, không dùng gạch nung", floor_height_mm=3300, use_llm=False)
    assert state["constraints"].max_vehicle_ton == 2.5
    assert state["result"].solutions
    assert "Chi phí thấp nhất" in state["explanation"]


def test_api_flow(sample_dxf):
    assert client.get("/api/health").json()["status"] == "ok"
    with open(sample_dxf, "rb") as f:
        r = client.post("/api/takeoff", files={"file": ("nha.dxf", f, "application/dxf")}, data={"floor_height_mm": "3300"})
    assert r.status_code == 200
    groups = r.json()["groups"]
    r = client.post("/api/optimize", json={"groups": groups, "constraints": {"max_vehicle_ton": 2.5}})
    assert r.status_code == 200 and r.json()["solutions"]
    r = client.post("/api/takeoff", files={"file": ("nha.pdf", b"x", "application/pdf")})
    assert r.status_code == 400


def test_api_dwg_without_converter(monkeypatch):
    """Tải DWG khi máy chưa có ODA File Converter: trả 422 kèm hướng dẫn cài đặt, không báo lỗi hệ thống."""
    from optimat.drawing import dwg_convert
    monkeypatch.delenv("ODA_CONVERTER_PATH", raising=False)
    monkeypatch.setattr(dwg_convert.shutil, "which", lambda name: None)
    monkeypatch.setattr(dwg_convert.glob, "glob", lambda pattern: [])
    r = client.post("/api/takeoff", files={"file": ("nha.dwg", b"x", "application/octet-stream")})
    assert r.status_code == 422 and "ODA File Converter" in r.json()["detail"]
    assert client.get("/api/health").json()["dwg_converter_available"] is False


def test_pipeline_includes_design_bill(sample_dxf):
    """Luồng agent: vật liệu đọc từ bản vẽ (mã danh mục) và giá có trong lời giải thích, trước phần tối ưu."""
    state = run_pipeline(sample_dxf, floor_height_mm=3300, use_llm=False)
    assert {b.material_id for b in state["bill"] if b.kind == "main"} == {"GN01", "AAC01"}
    assert "Vật liệu theo thiết kế" in state["explanation"] and "W-GN01-220" in state["explanation"]


def test_api_catalog_bill_and_keep_design(sample_dxf):
    mats = client.get("/api/catalog/wall-materials").json()
    systems = {s["wall_system_id"]: s for s in mats["wall_systems"]}
    assert systems["W-GN01-220"]["ready"] and not systems["W-GK01-220"]["ready"]   # GK01-220: TT 38 chưa có cột dày 220
    assert "số lượng vật liệu / m² tường" in systems["W-GK01-220"]["missing"]
    assert {m["id"] for m in mats["materials"]} >= {"GN01", "AAC01", "GK02"}
    with open(sample_dxf, "rb") as f:
        groups = client.post("/api/takeoff", files={"file": ("nha.dxf", f, "application/dxf")},
                             data={"floor_height_mm": "3300"}).json()["groups"]
    bill = client.post("/api/price/bill", json={"groups": groups}).json()
    assert {(b["wall_type"], b["kind"], b["material_id"]) for b in bill} >= {("220", "main", "GN01"), ("220", "mortar", "VU02")}
    r = client.post("/api/optimize", json={"groups": groups, "constraints": {"keep_design_material": True}}).json()
    assert r["solutions"] and all(c["wall_system_id"] in ("W-GN01-220", "W-AAC01-100")
                                  for s in r["solutions"] for c in s["choices"])
    no_design = [{**g, "design_wall_system_id": None} for g in groups]
    assert client.post("/api/optimize", json={"groups": no_design, "constraints": {"keep_design_material": True}}).status_code == 422


def test_api_agent_run_without_llm(sample_dxf):
    with open(sample_dxf, "rb") as f:
        r = client.post("/api/agent/run", files={"file": ("nha.dxf", f, "application/dxf")},
                        data={"message": "xe 2,5 tấn", "floor_height_mm": "3300", "use_llm": "false"})
    body = r.json()
    assert r.status_code == 200 and body["mode"] == "pipeline"
    assert body["constraints"]["max_vehicle_ton"] == 2.5 and body["bill"] and body["result"]["solutions"]
