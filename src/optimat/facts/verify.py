"""KD02: bộ kiểm chứng đề xuất của AI. Không tin AI: chỉ nhận khi nhãn thuộc danh mục và trích đoạn có thật trong nguồn."""
import re

from ..drawing.encoding import normalize


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", normalize(text or "")).strip()


def check(proposal: dict, sources: dict[str, str], labels) -> str | None:
    """None: đạt. Ngược lại: lý do loại."""
    ref, label, excerpt = proposal.get("ref"), proposal.get("label"), proposal.get("excerpt") or ""
    if ref not in sources:
        return "nguồn không tồn tại"
    if label not in labels:
        return "nhãn ngoài danh mục"
    if not norm(excerpt):
        return "thiếu trích đoạn"
    if norm(excerpt) not in norm(sources[ref]):
        return "trích đoạn không có trong nguồn"
    return None
