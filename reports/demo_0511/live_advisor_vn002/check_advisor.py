"""Check the staged advisor on real CAD-derived facts. --live permits one outbound request."""
import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from optimat import config
from optimat.agent import llm
from optimat.catalog.repository import Catalog

QUESTION = ("Tư vấn chọn vật liệu cho toàn bộ phần thô trong phạm vi hồ sơ này. Dòng nào chỉ có một "
            "mã tra được, dòng nào chưa có phương án hoặc chưa có báo giá mua? Nêu cần xác minh gì "
            "trước khi đặt hàng và có đủ căn cứ để so chi phí, lịch giao hay chưa.")


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--live", action="store_true")
    modes.add_argument("--replay", action="store_true", help="Replay the saved real answer; never contact OpenAI.")
    parser.add_argument("--context-only", action="store_true")
    parser.add_argument("--source-sha", help="Pin the offline-tested staged advisor for a live attempt")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--isolated-fix", action="store_true", help="Replay only on the isolated 04 patch.")
    target.add_argument("--canonical", action="store_true", help="Replay on the integrated source using the local catalog only.")
    args = parser.parse_args()
    if (args.isolated_fix or args.canonical) and not args.replay:
        parser.error("The selected target is for replay only")
    source = ROOT / ("src/optimat/agent/material_advisor.py" if args.canonical else
                     "tmp/live04/material_advisor.py" if args.isolated_fix else "tmp/row_assistant_12/agent/material_advisor.py")
    if args.source_sha and sha(source.read_bytes()) != args.source_sha.lower():
        raise ValueError("The handed-off source revision has changed")
    spec = importlib.util.spec_from_file_location("vn002_advisor_under_test", source)
    advisor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = advisor
    spec.loader.exec_module(advisor)
    raw = (OUT / "context.local.json").read_bytes()
    ctx = json.loads(raw)
    request = advisor.MaterialRequest(contextJson=raw.decode(), contextHash=sha(raw),
                                      requestId=uuid.uuid4().hex, question=QUESTION)
    try:
        context = request.context()
    except ValueError as exc:
        issues = [{"field": list(e["loc"]), "type": e["type"]} for e in exc.errors()] if hasattr(exc, "errors") else []
        print(json.dumps({"outcome": "context_rejected", "issues": issues}))
        return 2
    if args.context_only:
        print("Input accepted")
        return 0
    if args.canonical:
        from optimat.db.session import get_database_url
        if get_database_url():
            raise ValueError("Disable the database connection for the offline canonical replay")
        catalog = Catalog.from_csv()
    else:
        catalog = Catalog.from_db()
    facts = advisor.material_facts(context, request.question, catalog)
    rows = []
    for m in facts["materials"]:
        rows.append({"line": m["lineId"], "name": m["name"], "class": m["raw_class"], "complete": m["complete"],
                     "purchase_quantity": m["purchase_quantity"], "options": [{
                         "id": o["material_id"], "name": o["name"], "data_kind": o["data_kind"],
                         "observed_price": bool(o.get("offer")), "reference": bool((o.get("offer") or {}).get("is_reference")),
                         "price_level": (o.get("offer") or {}).get("price_level"),
                         "state": o["state"], "can_apply": o["canApply"],
                     } for o in m["options"]]})
    assert len(facts["coverage"]) == len(ctx["works"]) == 52 and len(rows) == len(ctx["materials"]) == 7
    assert all(not w["checked"] for w in ctx["works"]) and context.partial
    assert all(m["purchase_quantity"] is None and not m["complete"] for m in rows)
    assert all(not o["can_apply"] for m in rows for o in m["options"])
    assert any(len(m["options"]) == 1 and not m["options"][0]["observed_price"] for m in rows)
    assert any(not m["options"] for m in rows)
    receipt = {"mode": "LIVE_STAGING" if args.live else "OFFLINE_FACTS", "start_utc": now(),
               "source_sha256": sha(source.read_bytes()), "context_sha256": sha(raw),
               "work_count": len(facts["coverage"]), "materials": rows,
               "human_approval": False, "CAD_sent": False, "http_attempts": 0}
    if args.replay:
        live = json.loads((OUT / "live_receipt.json").read_text(encoding="utf-8"))
        reply = json.loads((OUT / "reply.openai.json").read_text(encoding="utf-8"))["content"]
        assert live["http_status"] == 200 and live["http_attempts"] == 1
        assert live["context_sha256"] == sha(raw) and live["response_sha256"] == sha(reply.encode())
        replay_file = "replay_canonical.json" if args.canonical else "replay_isolated.json" if args.isolated_fix else "replay.json"
        if args.canonical:
            assert live["materials"] == rows, "Catalog facts differ from the live test"
        audit = {"mode": "REPLAY_CAPTURED_OPENAI_RESPONSE", "isolated_fix": args.isolated_fix, "canonical": args.canonical,
                 "source_file": source.relative_to(ROOT).as_posix(), "openai_calls": 0,
                 "context_sha256": sha(raw), "original_source_sha256": live["source_sha256"],
                 "source_sha256": receipt["source_sha256"], "response_sha256": live["response_sha256"]}
        try:
            result = advisor.advise_materials(request, catalog, chat=lambda *_a, **_kw: {"content": reply})
        except ValueError as exc:
            audit.update(accepted=False, error=str(exc), terminal_utc=now())
            save(replay_file, audit)
            print("Captured response rejected by the current staged validator")
            return 1
        assert result["applied"] is False and result["contextHash"] == request.contextHash
        suggested = {a["lineId"]: a["proposed_material_ids"] for a in result["ai"]["advice"]}
        expected = {m["line"]: [o["id"] for o in m["options"]] for m in rows}
        assert suggested == expected and list(filter(None, suggested.values())) == [["TH10"]]
        bad_cases = [("m0", "Chọn TH10."), ("m5", "Chọn TH100."), ("m5", "TH10 giá 12 triệu."),
                     ("m5", "Dùng X-TH10."), ("m5", "Dùng TH10-A."), ("m5", "Giao trong 7 ngày.")]
        for line, bad_text in bad_cases:
            modified = copy.deepcopy(result["ai"])
            next(a for a in modified["advice"] if a["lineId"] == line)["reason"] = bad_text
            try:
                advisor.advise_materials(request, catalog, chat=lambda *_a, **_kw: {"content": json.dumps(modified)})
            except ValueError:
                continue
            raise AssertionError("Invalid numeric or cross-line claim accepted")
        audit.update(accepted=True, advice_count=len(suggested), only_suggested_material="TH10",
                     zero_option_lines=6, commercial_offer_count=0, applied=False,
                     forbidden_variants_rejected=len(bad_cases), terminal_utc=now())
        save(replay_file, audit)
        print(f"Captured real answer accepted; {len(bad_cases)} false claims rejected; no new OpenAI calls")
        return 0
    save("offline_facts.json", {**receipt, "mode": "OFFLINE_FACTS"})
    if not args.live:
        print("Catalog checked; zero, single-option and missing-price cases present")
        return 0
    if (OUT / "live_attempt.json").exists() or not args.source_sha or receipt["source_sha256"] != args.source_sha.lower():
        raise ValueError("A previous live attempt exists or the tested advisor has changed")
    if config.OPENAI_URL != "https://api.openai.com/v1/chat/completions" or config.LLM_PROVIDER != "openai" or not llm.llm_available():
        raise ValueError("Official OpenAI endpoint and server credential are required")
    transport = llm.requests

    def recorded_post(url, **kwargs):
        messages = kwargs["json"]["messages"]
        outbound = json.dumps(messages, ensure_ascii=False)
        if url != config.OPENAI_URL or re.search(r"\.dw[gfx]\b|projectUid|drawingId|reviewId|nha.sang|nhà sang|hải dương|hai.duong|[A-Z]:\\|Bearer ", outbound, re.I):
            raise ValueError("Payload minimisation check failed before sending")
        # The exclusive file counts attempts even on timeout. Never retry an ambiguous network result.
        with (OUT / "live_attempt.json").open("x", encoding="utf-8") as handle:
            json.dump({"url": url, "model": config.OPENAI_MODEL, "start_utc": now(), "prompt_sha256": sha(outbound.encode())}, handle)
        receipt.update(http_attempts=1, endpoint=url, configured_model=config.OPENAI_MODEL, prompt_sha256=sha(outbound.encode()))
        response = transport.post(url, allow_redirects=False, **kwargs)
        receipt.update(http_status=response.status_code, request_id=response.headers.get("x-request-id"))
        try:
            metadata = response.json()
            receipt.update(returned_model=metadata.get("model"), usage=metadata.get("usage"),
                           provider_error_code=(metadata.get("error") or {}).get("code"))
            if response.status_code == 200:
                choice = (metadata.get("choices") or [{}])[0]
                receipt["finish_reason"] = choice.get("finish_reason")
                reply = (choice.get("message") or {}).get("content") or ""
                receipt["response_sha256"] = sha(reply.encode())
                if len(reply) <= 60000 and not re.search(r"Bearer |sk-[A-Za-z0-9_-]{12,}", reply):
                    save("reply.openai.json", {"content": reply})
        except ValueError:
            pass
        return response

    llm.requests = SimpleNamespace(post=recorded_post, RequestException=transport.RequestException)
    try:
        result = advisor.advise_materials(request, catalog)
        if receipt.get("http_status") != 200 or receipt["http_attempts"] != 1:
            raise ValueError("No successful OpenAI response")
        assert result["contextHash"] == request.contextHash and result["applied"] is False
        assert {a["lineId"] for a in result["ai"]["advice"]} == {r["line"] for r in rows}
        receipt.update(outcome="openai_response_validated", ai=result["ai"])
        return 0
    except Exception as exc:
        receipt.update(outcome="failed", error_type=type(exc).__name__)
        return 1
    finally:
        llm.requests = transport
        receipt["end_utc"] = now()
        save("live_receipt.json", receipt)
        print(json.dumps({k: receipt.get(k) for k in ("outcome", "http_attempts", "http_status", "provider_error_code", "error_type")}))


if __name__ == "__main__":
    sys.exit(main())
