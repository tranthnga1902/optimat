"""Gán vai trò cho từng layer theo mẫu tên, cho phép người dùng ghi đè.

Cách tổ chức (quy tắc mặc định theo thứ tự, layer không khớp thì để UNKNOWN chứ không đoán,
người dùng ghi đè theo từng file) lấy từ app/detection/layer_classifier.py của dự án
floor-plan-exit-router (giấy phép MIT, xem THIRD_PARTY_NOTICES.md). Bộ quy tắc được viết lại
cho tên layer tiếng Việt và các vai trò cần cho đo bóc; từ 17/10/2026 quy tắc nằm trong data/rules/concepts.csv.
"""
from __future__ import annotations

from enum import Enum

from .concepts import ROUGH_ROLES, layer_role


class LayerClass(str, Enum):
    WALL = "WALL"
    OPENING = "OPENING"        # cửa đi, cửa sổ
    ANNOTATION = "ANNOTATION"  # kích thước, chữ, trục, khung tên
    IGNORE = "IGNORE"          # nội thất, thiết bị, hatch
    UNKNOWN = "UNKNOWN"


def default_classification(layer_names: list[str]) -> dict[str, LayerClass]:
    """Vai trò theo ký hiệu layer của data/rules/concepts.csv (QU-08); dòng khớp đầu tiên thắng. Đây là mặc định:
    mọi kết quả đều có thể bị người dùng ghi đè."""
    result: dict[str, LayerClass] = {}
    for name in layer_names:
        role = layer_role(name)
        # cột, dầm, thang... không phải tường: nhận tường bỏ qua như trước, bóc phần thô đọc vai trò riêng
        result[name] = LayerClass.IGNORE if role in ROUGH_ROLES else LayerClass(role) if role else LayerClass.UNKNOWN
    return result


def apply_overrides(classification: dict[str, LayerClass],
                    overrides: dict[str, str] | None) -> dict[str, LayerClass]:
    """overrides: {tên layer: "WALL" | "OPENING" | ...}. Giá trị lạ bị bỏ qua thay vì gây lỗi."""
    if not overrides:
        return classification
    merged = dict(classification)
    for layer_name, class_value in overrides.items():
        try:
            merged[layer_name] = LayerClass(class_value)
        except ValueError:
            continue
    return merged
