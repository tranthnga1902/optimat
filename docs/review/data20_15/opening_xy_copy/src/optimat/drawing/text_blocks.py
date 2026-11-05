"""Ghép ghi chú nhiều dòng trên bản vẽ thành một đoạn.

Bản vẽ thật hay ghi chú vật liệu bằng nhiều TEXT rời xếp thành cột (không dùng MTEXT), ví dụ
    - TƯỜNG XÂY
    GẠCH KHÔNG NUNG 220
Từng dòng riêng không đủ nghĩa để khớp quy tắc ("tuong xay" không nói loại gạch; "gach khong nung 220" không có chữ
"tuong"). Gom các TEXT cùng layer, cùng cỡ chữ, canh lề trái gần nhau và cách nhau theo chiều đứng không quá
LINE_GAP_FACTOR × cỡ chữ thành một đoạn; vị trí đoạn lấy ở dòng đầu.

Đoạn ghép chỉ là TÍN HIỆU BỔ SUNG: từng dòng gốc vẫn được so khớp như trước, nên kết quả cũ không đổi khi không có
ghi chú nhiều dòng. Không ghép TEXT cách xa nhau hay khác cỡ chữ (bảng thống kê, khung tên).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .dxf_reader import TextItem

LINE_GAP_FACTOR = 2.2      # khoảng cách tâm hai dòng kế tiếp ≤ hệ số × cỡ chữ (dòng cách dòng thường 1,5–2 lần)
LEFT_ALIGN_FACTOR = 1.5    # lệch mép trái hai dòng ≤ hệ số × cỡ chữ
MIN_LINES = 2


@dataclass
class TextBlock:
    text: str                  # các dòng nối bằng dấu cách, theo thứ tự từ trên xuống
    x: float                   # vị trí dòng đầu
    y: float
    layer: str
    lines: list[TextItem]


def _height(t: TextItem) -> float:
    return t.height if t.height and t.height > 0 else 0.0


def group_text_lines(texts: list[TextItem]) -> list[TextBlock]:
    """Các đoạn ghi chú có từ MIN_LINES dòng trở lên. TEXT không có cỡ chữ (height = 0) không ghép."""
    by_key: dict[tuple[str, int], list[TextItem]] = defaultdict(list)
    for t in texts:
        h = _height(t)
        if h <= 0 or not t.text.strip():
            continue
        by_key[(t.layer, int(round(h)))].append(t)
    out: list[TextBlock] = []
    for (layer, _), items in by_key.items():
        items = sorted(items, key=lambda t: (-t.y, t.x))      # từ trên xuống, trái sang phải
        used = [False] * len(items)
        for i, head in enumerate(items):
            if used[i]:
                continue
            h = _height(head)
            chain = [head]
            used[i] = True
            last = head
            for j in range(i + 1, len(items)):
                if used[j]:
                    continue
                cand = items[j]
                dy = last.y - cand.y
                if dy > LINE_GAP_FACTOR * h:
                    break                                     # danh sách đã sắp theo y: các dòng sau còn xa hơn
                if dy <= 0 or abs(cand.x - head.x) > LEFT_ALIGN_FACTOR * h:
                    continue
                chain.append(cand)
                used[j] = True
                last = cand
            if len(chain) >= MIN_LINES:
                out.append(TextBlock(" ".join(t.text.strip() for t in chain), head.x, head.y, layer, chain))
    return out
