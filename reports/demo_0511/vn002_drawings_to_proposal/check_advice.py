"""Kiểm tư vấn VN002 trên bản bóc mới. Chỉ --live mới gửi dữ kiện rút gọn."""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[2] / "src"))

from optimat import config
from optimat.agent.material_advisor import MaterialRequest, advise_materials, material_facts
from optimat.agent.llm import chat_openai
from optimat.catalog.repository import Catalog


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--replay", action="store_true")
    parser.add_argument("--saved-request", action="store_true")
    args = parser.parse_args()
    os.environ.pop("DATABASE_URL", None)
    catalog = Catalog.from_csv()
    source = "context.from_saved_request.json" if args.saved_request else "context.local.json"
    raw = (OUT / source).read_text(encoding="utf-8")
    req = MaterialRequest(question="Đề xuất cho toàn bộ phần thô theo thiết kế. Giải thích vì sao từng dòng chỉ có một lựa chọn nếu gặp. Giữ các vật tư thiếu giá và ghi rõ cần bổ sung gì để lấy báo giá.",
                          contextJson=raw, contextHash=hashlib.sha256(raw.encode()).hexdigest(), requestId=uuid4().hex)
    ctx = req.context()
    assert ctx.partial and all(not w.checked for w in ctx.works)
    facts = material_facts(ctx, req.question, catalog)
    assert len(facts["coverage"]) == len(ctx.works)
    assert {r["lineId"] for r in facts["materials"]} == {m.lineId for m in ctx.materials}
    save("facts.from_saved_request.json" if args.saved_request else "facts.local.json", facts)
    if args.replay:
        receipt = json.loads((OUT / "live_receipt.json").read_text(encoding="utf-8"))
        assert req.contextHash == receipt["context_sha256"] and receipt["provider_returned"]
        reply = json.loads((OUT / "provider_reply.json").read_text(encoding="utf-8"))
        def replay(messages, **kwargs):
            raw_facts = messages[1]["content"].encode("utf-8")
            payload = json.loads(raw_facts)
            assert hashlib.sha256(raw_facts).hexdigest() == receipt["payload_sha256"]
            assert all(row["lineId"] == m.lineId and all(gap in row["missing"] for gap in m.missing)
                       for row, m in zip(payload["materials"], ctx.materials, strict=True))
            (OUT / "outbound.replay.user.json").write_bytes(raw_facts)
            return reply

        answer = advise_materials(req, catalog, chat=replay)
        assert all(set(m.missing) <= set(row["missing"]) for m, row in zip(ctx.materials, answer["facts"]["materials"]))
        assert [(a["lineId"], a["proposed_material_ids"]) for a in answer["ai"]["advice"] if a["proposed_material_ids"]] == [
            (m["lineId"], ["TH10"]) for m in facts["materials"] if m["options"] and m["options"][0]["material_id"] == "TH10"]
        assert not answer["applied"] and all(o["offer"] is None for m in facts["materials"] for o in m["options"])
        save("answer.validated.json", answer)
        print(len(answer["ai"]["advice"]), "validated advice rows, 0 new calls")
        return
    if not args.live:
        print(len(facts["coverage"]), "works;", len(facts["materials"]), "material rows")
        return
    if config.OPENAI_URL != "https://api.openai.com/v1/chat/completions" or config.LLM_PROVIDER != "openai":
        raise ValueError("Cần cấu hình OpenAI chính thức của ứng dụng.")
    receipt = {"mode": "actual_CAD_local_advisor", "context_file": source, "model_requested": config.OPENAI_MODEL,
               "utc": datetime.now(timezone.utc).isoformat(), "context_sha256": req.contextHash,
               "human_approval": False, "drawings_sent": False, "browser_e2e": False, "calls": 0}

    def recorded(messages, **kwargs):
        outbound = json.loads(messages[1]["content"])
        assert set(outbound) == {"question", "partial", "materials", "coverage", "missing_work_count"}
        payload = json.dumps(outbound, ensure_ascii=False).casefold()
        assert not any(s in payload for s in ("nha_sang", ".dxf", ".dwg", "vn002", "hải dương", "c:\\users", "projectuid", "drawingid"))
        receipt["calls"] += 1
        receipt["payload_sha256"] = hashlib.sha256(messages[1]["content"].encode()).hexdigest()
        reply = chat_openai(messages, **kwargs)
        save("provider_reply.json", reply)
        receipt["provider_returned"] = True
        return reply

    try:
        result = advise_materials(req, catalog, chat=recorded)
        save("answer.json", result)
        receipt.update(accepted=True, suggested=[r for r in result["ai"]["advice"] if r["proposed_material_ids"]],
                       rows=len(result["ai"]["advice"]), applied=result["applied"])
    finally:
        save("live_receipt.json", receipt)
    print(receipt["rows"], "verified advice rows")


if __name__ == "__main__":
    main()
