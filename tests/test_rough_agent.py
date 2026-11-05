"""Phần thô S6c: bước phần thô trong luồng cố định (tắt LLM), công cụ boc_phan_tho, kiểm soát định mức."""
import json

from fastapi.testclient import TestClient

from optimat.agent.orchestrator import run_agent
from optimat.agent.pipeline import run_pipeline
from optimat.api.main import app
from optimat.catalog.repository import Catalog
from optimat.data_check import run_checks
from optimat.rough.models import ProjectParams


def test_pipeline_without_llm_always_adds_rough(sample_dxf):
    state = run_pipeline(sample_dxf, floor_height_mm=3300, use_llm=False,
                         rough_params=ProjectParams(concrete_supply="ready_mix", concrete_grade="M250"))
    assert state["rough"].totals and "Phần thô" in state["facts"] and "Xây tường" in state["facts"]
    plain = run_pipeline(sample_dxf, floor_height_mm=3300, use_llm=False)
    assert plain["rough"].totals and "Phần thô" in plain["facts"]
    # không có thông số vẫn bóc, nhưng không đoán: phần cần thông số để trống
    assert any(not m.complete for m in plain["rough"].materials)


def test_agent_tool_rough(sample_dxf):
    calls = iter([{"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
        "name": "boc_phan_tho", "arguments": json.dumps({"slab_thickness_mm": 100, "concrete_grade": "M250"})}}]}])

    def fake_chat(messages, tools=None, json_mode=False):
        try:
            return next(calls)
        except StopIteration:
            return {"role": "assistant", "content": messages[-1]["content"]}

    out = run_agent(sample_dxf, "bóc phần thô giúp tôi", floor_height_mm=3300, chat=fake_chat)
    assert out["mode"] == "agent" and out["rough"] is not None and not out["guarded"]
    assert "Xây tường" in out["answer"]


def test_agent_api_rough_params(sample_dxf):
    with open(sample_dxf, "rb") as f:
        r = TestClient(app).post("/api/agent/run", files={"file": ("mau.dxf", f)},
                                 data={"use_llm": "false", "floor_height_mm": "3300",
                                       "rough_params": json.dumps({"concrete_grade": "M250"})})
    assert r.status_code == 200 and r.json()["rough"]["totals"]


def test_data_check_reports_blank_norms():
    rep = run_checks(Catalog.load())   # danh mục CSV: không có catalog thì run_checks đòi PostgreSQL
    rough = [f for f in rep["findings"] if f["area"] == "dinh_muc_phan_tho"]
    assert rep["counts"]["error"] == 0 and any("còn trống" in f["message"] for f in rough)
    assert rep["summary"]["dinh_muc_phan_tho"]["dong"] > 0


def test_rough_materials_get_prices_same_unit_only():
    """Vật liệu phần thô có giá thấp nhất cùng đơn vị; khác đơn vị không quy đổi; thiếu số thì không ra thành tiền."""
    from optimat.catalog.repository import Catalog
    from optimat.rough.models import MaterialLine
    from optimat.rough.takeoff import attach_prices
    lines = [MaterialLine(material_id="GN01", name="gạch", unit="viên", quantity=1000),
             MaterialLine(material_id="GN01", name="gạch", unit="m³", quantity=2),
             MaterialLine(material_id="GN01", name="gạch", unit="viên", quantity=10, complete=False)]
    cat = Catalog.load()
    cat.supplier_materials.loc[cat.supplier_materials.material_id == "GN01", "sale_unit"] = "viên"
    attach_prices(lines, cat)
    assert lines[0].best_price == 1350 and lines[0].est_cost == 1350000 and "SAMPLE" in lines[0].price_source
    assert lines[1].best_price is None
    assert lines[2].best_price == 1350 and lines[2].est_cost is None
