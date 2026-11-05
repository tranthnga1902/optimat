"""KD02: gọi OpenAI gắn nhãn mục chữ theo danh mục đóng (Structured Outputs strict), có cache và kiểm chứng.

Chỉ gửi chữ (không hình, không tọa độ). Bật theo từng lần phân tích (allow) + LLM_PROVIDER=openai + có khóa;
hồ sơ không được phép gửi ra ngoài thì để allow=False (R8). Lỗi mạng: trả rỗng, luồng quy tắc vẫn chạy (R5).
"""
import hashlib
import json
import os
from pathlib import Path

from .. import config
from ..agent import llm
from . import review
from .verify import check

PROMPT_VERSION = "kd-1"
BATCH = 120               # số mục chữ mỗi lần gọi
MAX_ITEMS = 600           # trần mục chữ mỗi lần phân tích (chi phí)

SYSTEM = ("Bạn gắn nhãn các dòng chữ trích từ hồ sơ thiết kế nhà ở (bản vẽ CAD, thuyết minh, dự toán) tiếng Việt. "
          "Chỉ dùng nhãn trong danh sách. Với mỗi dòng có thông tin khớp nhãn, trả ref của dòng, nhãn, và excerpt là "
          "đoạn chép NGUYÊN VĂN từ dòng đó chứa thông tin (không sửa chữ, không thêm số). Một dòng có thể có nhiều nhãn. "
          "Dòng không liên quan thì bỏ qua. Không đoán, không suy ra số không có trong dòng.")


def enabled(allow: bool) -> bool:
    return bool(allow) and config.LLM_PROVIDER == "openai" and llm.llm_available()


def _cache_dir() -> Path:
    return Path(os.environ.get("OPTIMAT_AI_CACHE_DIR") or config.DATA_DIR / "cache" / "ai")


def _schema(refs: list[str], labels: list[str]) -> dict:
    item = {"type": "object", "additionalProperties": False, "required": ["ref", "label", "excerpt"],
            "properties": {"ref": {"type": "string", "enum": refs}, "label": {"type": "string", "enum": labels},
                           "excerpt": {"type": "string"}}}
    return {"type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"items": {"type": "array", "items": item}}}


def _call(task: str, instructions: str, items: list[dict], labels: dict[str, str]) -> list[dict]:
    body = {"v": PROMPT_VERSION, "model": config.OPENAI_MODEL, "task": task, "instructions": instructions,
            "items": items, "labels": labels}
    key = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    path = _cache_dir() / f"{key}.json"
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        llm.LAST_USAGE.clear()   # lấy từ cache: không tốn token
        return cached
    except (OSError, ValueError):
        pass
    label_text = "\n".join(f"- {k}: {v}" for k, v in labels.items())
    lines = "\n".join(f"{i['ref']}: {i['text']}" for i in items)
    reply = llm.chat_openai([{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": f"{instructions}\n\nNHÃN:\n{label_text}\n\nCÁC DÒNG:\n{lines}"}],
                            schema=(f"kd_{task}", _schema([i["ref"] for i in items], list(labels))))
    result = json.loads(reply.get("content") or "{}").get("items") or []
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return result


def label(task: str, instructions: str, items: list[dict], labels: dict[str, str], allow: bool,
          source_file: str = "") -> tuple[list[dict], list[dict], dict]:
    """items: [{ref, text}]. Trả (đạt kiểm chứng, bị loại kèm lý do, trạng thái). Đề xuất đạt vào hàng chờ duyệt (KD06)."""
    if not items:
        return [], [], {"status": "khong_co_muc"}
    if not enabled(allow):
        return [], [], {"status": "off"}
    items = items[:MAX_ITEMS]
    sources = {i["ref"]: i["text"] for i in items}
    accepted, rejected, calls, tokens = [], [], 0, 0
    try:
        for start in range(0, len(items), BATCH):
            for proposal in _call(task, instructions, items[start:start + BATCH], labels):
                reason = check(proposal, sources, labels)
                entry = {**proposal, "text": sources.get(proposal.get("ref"), "")}
                (rejected if reason else accepted).append({**entry, "reason": reason} if reason else entry)
            calls += 1
            tokens += int(llm.LAST_USAGE.get("total_tokens") or 0)
    except (llm.LLMUnavailable, ValueError, TypeError, AttributeError) as exc:
        return accepted, rejected, {"status": "loi", "message": str(exc)[:200], "calls": calls}
    review.enqueue(task, accepted, source_file)
    return accepted, rejected, {"status": "ok", "calls": calls, "tokens": tokens, "model": config.OPENAI_MODEL}
