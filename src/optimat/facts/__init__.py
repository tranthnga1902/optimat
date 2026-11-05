"""Kho dữ kiện đầu vào (KD01–KD07, docs/KE_HOACH_KHO_DU_KIEN_AI.md).

Mỗi dữ kiện có nguồn (tệp, ref trong tệp, trích đoạn), cách lấy (rule | ai_label | user) và trạng thái A/B/C/D.
AI chỉ gắn nhãn trong danh mục đóng và chỉ ra trích đoạn; số luôn do mã đọc từ trích đoạn (verify.py).
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Fact(BaseModel):
    field: str                                  # tên thông số (ProjectParams) hoặc nhãn (loại tờ, vai trò cột bảng…)
    value: Optional[object] = None              # giá trị mã đọc từ trích đoạn; None khi chỉ là nhãn
    task: str                                   # thong_so | tieu_de_bang | loai_ban_ve | ky_hieu | du_toan
    source_file: str = ""
    ref: str = ""                               # t<i> chữ CAD, p<i> đoạn DOCX, ô Excel, …
    excerpt: str = ""
    method: Literal["rule", "ai_label", "user"] = "rule"
    status: Literal["A", "B", "C", "D"] = "B"
    rule: Optional[str] = None                  # mã dòng quy tắc CSV đã khớp
    note: str = ""


class FactReport(BaseModel):
    facts: list[Fact] = Field(default_factory=list)
    rejected: list[dict] = Field(default_factory=list)   # đề xuất AI bị bộ kiểm chứng loại, kèm lý do
    ai: dict = Field(default_factory=dict)               # trạng thái gọi AI: off | ok | lỗi, số lần gọi, token
