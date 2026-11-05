"""Chuyển yêu cầu tiếng Việt thành ràng buộc có cấu trúc.

Mô hình chính là mô hình của OpenAI gọi qua API (config.LLM_PROVIDER = "openai"); kết quả phải qua kiểm tra
của Pydantic. Không có khóa API, mất mạng hoặc mô hình trả sai định dạng thì dùng bộ trích bằng biểu thức
chính quy, nhờ vậy hệ thống vẫn chạy đủ khi không có LLM. Ollama còn giữ làm lựa chọn chạy cục bộ.
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

import requests
from pydantic import BaseModel, Field, ValidationError

from .. import config
from ..drawing.encoding import normalize

# từ khóa (đã bỏ dấu) -> họ vật liệu bị loại (cột family của danh mục). Từ khóa dài xét trước.
_CLAY, _CMU = ("CLAY_SOLID", "CLAY_HOLLOW"), ("CMU_SOLID", "CMU_HOLLOW")
EXCLUDE_KEYWORDS = {"gach nung": _CLAY, "gach dat nung": _CLAY, "gach do": _CLAY, "gach tuynel": _CLAY,
                    "gach be tong khi": ("AAC",), "be tong khi": ("AAC",), "aac": ("AAC",),
                    "gach be tong bot": ("CLC",), "clc": ("CLC",), "alc": ("ALC_PANEL",),
                    "gach be tong": _CMU, "gach block": _CMU, "gach xi mang": _CMU,
                    "gach khong nung": _CMU + ("CLC", "AAC"), "thach cao": ("GYPSUM",)}
FAMILIES = ("CLAY_SOLID", "CLAY_HOLLOW", "CMU_SOLID", "CMU_HOLLOW", "CLC", "AAC", "ALC_PANEL", "EPS_PANEL",
            "CEMBOARD", "GYPSUM")
NEGATIONS = ("khong dung", "khong muon", "khong thich", "loai", "tranh", "bo ")


class ParsedConstraints(BaseModel):
    budget: Optional[float] = Field(None, description="Ngân sách, đơn vị đồng")
    deadline_days: Optional[float] = None
    max_vehicle_ton: Optional[float] = None
    excluded_materials: list[str] = Field(default_factory=list)
    source: str = "regex"


def _number(text: str) -> float:
    """'2,5' -> 2.5; '1.5' -> 1.5; '150.000.000' -> 150000000."""
    if "," in text:
        return float(text.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        return float(text.replace(".", ""))
    return float(text)


def parse_with_regex(message: str) -> ParsedConstraints:
    text = normalize(message)
    out = ParsedConstraints()
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ty|trieu|tr)\b", text)
    if m:
        out.budget = _number(m.group(1)) * (1e9 if m.group(2) == "ty" else 1e6)
    else:
        m = re.search(r"(\d{1,3}(?:\.\d{3}){2,})\s*(d|dong|vnd)\b", text)
        if m:
            out.budget = _number(m.group(1))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(tan|t)\b", text)
    if m:
        out.max_vehicle_ton = _number(m.group(1))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ngay|tuan)\b", text)
    if m:
        out.deadline_days = _number(m.group(1)) * (7 if m.group(2) == "tuan" else 1)
    for sentence in re.split(r"[.;\n]", text):
        if any(neg in sentence for neg in NEGATIONS):
            for keyword in sorted(EXCLUDE_KEYWORDS, key=len, reverse=True):
                if keyword in sentence:
                    sentence = sentence.replace(keyword, " ")
                    for family in EXCLUDE_KEYWORDS[keyword]:
                        if family not in out.excluded_materials:
                            out.excluded_materials.append(family)
    return out


_SYSTEM = (
    "Bạn trích ràng buộc từ yêu cầu của chủ nhà về vật liệu xây tường. Chỉ trả về JSON với các khóa: "
    "budget (đồng, số hoặc null), deadline_days (số hoặc null), max_vehicle_ton (số hoặc null), "
    "excluded_materials (danh sách họ vật liệu bị loại, chỉ dùng các giá trị " + ", ".join(FAMILIES) + "; "
    "gạch nung là CLAY_SOLID và CLAY_HOLLOW, gạch bê tông là CMU_SOLID và CMU_HOLLOW). "
    "Không suy đoán: thông tin nào không được nêu thì để null hoặc danh sách rỗng."
)


def parse_with_ollama(message: str, timeout: float = 30.0) -> ParsedConstraints | None:
    try:
        resp = requests.post(config.OLLAMA_URL, timeout=timeout, json={
            "model": config.OLLAMA_MODEL, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": message}],
        })
        resp.raise_for_status()
        data = json.loads(resp.json()["message"]["content"])
        parsed = ParsedConstraints(**{k: data.get(k) for k in ("budget", "deadline_days", "max_vehicle_ton")},
                                   excluded_materials=data.get("excluded_materials") or [], source="ollama")
        parsed.excluded_materials = [m for m in parsed.excluded_materials if m in FAMILIES]
        return parsed
    except (requests.RequestException, KeyError, ValueError, ValidationError, TypeError):
        return None


class LLMUnavailable(Exception):
    """Không gọi được mô hình: thiếu khóa API, mất mạng, hết hạn mức hoặc trả về sai định dạng."""


def llm_available() -> bool:
    if config.LLM_PROVIDER == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    return config.LLM_PROVIDER == "ollama"


LAST_USAGE: dict = {}   # token của lần gọi gần nhất (KD02 ghi vào nhật ký chi phí)


def chat_openai(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False,
                schema: tuple[str, dict] | None = None) -> dict:
    """Gọi Chat Completions của OpenAI, trả về message của trợ lý (có thể kèm tool_calls).
    schema = (tên, JSON Schema): ép đầu ra đúng schema (Structured Outputs, strict)."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise LLMUnavailable("Chưa đặt biến môi trường OPENAI_API_KEY.")
    body: dict = {"model": config.OPENAI_MODEL, "messages": messages}
    if tools:
        body["tools"] = tools
    if schema:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": schema[0], "schema": schema[1], "strict": True}}
    elif json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        resp = requests.post(config.OPENAI_URL, json=body, timeout=config.OPENAI_TIMEOUT_S,
                             headers={"Authorization": f"Bearer {key}"})
        resp.raise_for_status()
        data = resp.json()
        LAST_USAGE.clear()
        LAST_USAGE.update(data.get("usage") or {})
        return data["choices"][0]["message"]
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        raise LLMUnavailable(f"Không gọi được mô hình {config.OPENAI_MODEL}: {exc}") from exc


def parse_with_openai(message: str) -> ParsedConstraints | None:
    try:
        reply = chat_openai([{"role": "system", "content": _SYSTEM}, {"role": "user", "content": message}], json_mode=True)
        data = json.loads(reply["content"])
        parsed = ParsedConstraints(**{k: data.get(k) for k in ("budget", "deadline_days", "max_vehicle_ton")},
                                   excluded_materials=data.get("excluded_materials") or [], source="openai")
        parsed.excluded_materials = [m for m in parsed.excluded_materials if m in FAMILIES]
        return parsed
    except (LLMUnavailable, KeyError, ValueError, ValidationError, TypeError):
        return None


_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", ".").rstrip("0").rstrip(".") if "." in n.replace(",", ".") else n for n in _NUMBER.findall(text)}


def unsupported_numbers(answer: str, facts: str) -> set[str]:
    """Các con số có trong câu trả lời nhưng không có trong dữ kiện: dấu hiệu mô hình tự sinh số."""
    return numbers_in(answer) - numbers_in(facts)


_EXPLAIN = (
    "Bạn là trợ lý tư vấn vật liệu xây dựng. Viết lại phần DỮ KIỆN dưới đây thành lời giải thích ngắn gọn bằng tiếng Việt "
    "cho chủ nhà: nêu từng phương án, điểm mạnh, điểm đánh đổi. Chỉ dùng con số, tên nhà cung cấp và liên kết có trong "
    "DỮ KIỆN, chép nguyên văn; không thêm số liệu mới, không làm tròn lại, không tự tính."
)


def write_explanation(facts: str, use_llm: bool = True) -> tuple[str, str]:
    """Trả về (lời giải thích, nguồn). Mô hình chỉ diễn đạt lại; câu trả lời có số lạ thì bỏ, dùng nguyên dữ kiện."""
    if use_llm and config.LLM_PROVIDER == "openai" and llm_available():
        try:
            answer = chat_openai([{"role": "system", "content": _EXPLAIN}, {"role": "user", "content": "DỮ KIỆN:\n" + facts}]).get("content") or ""
            if answer.strip() and not unsupported_numbers(answer, facts):
                return answer.strip(), "openai"
        except LLMUnavailable:
            pass
    return facts, "template"


def parse_constraints(message: str, use_llm: bool = True) -> ParsedConstraints:
    if use_llm and config.LLM_PROVIDER == "openai":
        parsed = parse_with_openai(message)
        if parsed is not None:
            return parsed
    elif use_llm and config.LLM_PROVIDER == "ollama":
        parsed = parse_with_ollama(message)
        if parsed is not None:
            return parsed
    return parse_with_regex(message)
