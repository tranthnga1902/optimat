"""Kiểm thử phần agent dùng mô hình OpenAI bằng hàm giả: không gọi mạng, không cần khóa API."""
import json

from optimat.agent import llm
from optimat.agent.orchestrator import run_agent
from optimat.agent.pipeline import run_pipeline


def _call(name, args, call_id):
    return {"role": "assistant", "content": None,
            "tool_calls": [{"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def test_agent_calls_tools_and_keeps_tool_numbers(sample_dxf):
    seen = []

    def fake_chat(messages, tools=None, json_mode=False):
        seen.append(len(messages))
        if len(seen) == 1:
            return _call("do_boc_ban_ve", {"floor_height_mm": 3300}, "c1")
        if len(seen) == 2:
            return _call("toi_uu_vat_lieu", {"max_vehicle_ton": 2.5, "excluded_materials": ["CLAY_SOLID", "CLAY_HOLLOW"]}, "c2")
        facts = messages[-1]["content"]                       # trả lời bằng chính kết quả công cụ
        return {"role": "assistant", "content": "Đề xuất cho bạn:\n" + facts}

    out = run_agent(sample_dxf, "xe 2,5 tấn, không dùng gạch nung", chat=fake_chat)
    assert out["mode"] == "agent" and not out["guarded"]
    assert [t["tool"] for t in out["trace"]] == ["do_boc_ban_ve", "toi_uu_vat_lieu"]
    assert out["constraints"].max_vehicle_ton == 2.5 and out["result"].solutions
    assert "Chi phí thấp nhất" in out["answer"]


def test_agent_replaces_answer_with_invented_numbers(sample_dxf):
    replies = iter([_call("do_boc_ban_ve", {}, "c1"), _call("toi_uu_vat_lieu", {}, "c2"),
                    {"role": "assistant", "content": "Phương án tốt nhất chỉ tốn 12345 triệu đồng."}])
    out = run_agent(sample_dxf, "tư vấn giúp tôi", 3300, chat=lambda messages, tools=None, json_mode=False: next(replies))
    assert out["guarded"] and "12345" not in out["answer"] and "Chi phí thấp nhất" in out["answer"]


def test_agent_falls_back_when_model_unavailable(sample_dxf):
    def down(messages, tools=None, json_mode=False):
        raise llm.LLMUnavailable("mất mạng")
    out = run_agent(sample_dxf, "xe 2,5 tấn", 3300, chat=down)
    assert out["mode"] == "fallback" and out["result"].solutions and out["constraints"].max_vehicle_ton == 2.5


def test_tool_order_error_is_reported_to_model(sample_dxf):
    replies = iter([_call("toi_uu_vat_lieu", {}, "c1"), {"role": "assistant", "content": "Cần đo bóc trước."}])
    out = run_agent(sample_dxf, "tối ưu ngay", chat=lambda messages, tools=None, json_mode=False: next(replies))
    assert "do_boc_ban_ve trước" in out["trace"][0]["result"]


def test_parse_with_openai_and_fallback(monkeypatch):
    monkeypatch.setattr(llm.config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm, "chat_openai", lambda messages, tools=None, json_mode=False: {
        "content": json.dumps({"budget": 150000000, "deadline_days": 7, "max_vehicle_ton": None, "excluded_materials": ["AAC", "KHAC"]})})
    p = llm.parse_constraints("ngân sách 150 triệu trong 1 tuần, không dùng AAC")
    assert (p.source, p.budget, p.deadline_days, p.excluded_materials) == ("openai", 150e6, 7, ["AAC"])
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.undo()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm.parse_constraints("ngân sách 150 triệu").source == "regex"       # không có khóa API thì dùng regex


def test_explanation_guard(monkeypatch, sample_dxf):
    monkeypatch.setattr(llm.config, "LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "khoa-gia")
    monkeypatch.setattr(llm, "chat_openai", lambda messages, tools=None, json_mode=False: {"content": "Chỉ mất 999 ngày."})
    state = run_pipeline(sample_dxf, message="xe 2,5 tấn", floor_height_mm=3300)
    assert state["explanation_source"] == "template" and state["explanation"] == state["facts"]
