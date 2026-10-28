"""Phần thô S6c: bước phần thô trong luồng cố định (tắt LLM), công cụ boc_phan_tho, kiểm soát định mức."""
import json

from fastapi.testclient import TestClient

from optimat.agent.orchestrator import run_agent
from optimat.agent.pipeline import run_pipeline
from optimat.api.main import app
from optimat.catalog.repository import Catalog
from optimat.data_check import run_checks
from optimat.rough.models import ProjectParams


def test_pipeline_without_llm_adds_rough_when_params_given(sample_dxf):
    state = run_pipeline(sample_dxf, floor_height_mm=3300, use_llm=False,
                         rough_params=ProjectParams(concrete_supply="ready_mix", concrete_grade="M250"))
    assert state["rough"].totals and "Phần thô" in state["facts"] and "Xây tường" in state["facts"]
    plain = run_pipeline(sample_dxf, floor_height_mm=3300, use_llm=False)
    assert plain.get("rough") is None and "Phần thô" not in plain["facts"]   # không có thông số: không bóc, không đoán


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
