"""Gán vai trò cho từng layer theo mẫu tên, cho phép người dùng ghi đè.

Cách tổ chức (quy tắc mặc định theo thứ tự, layer không khớp thì để UNKNOWN chứ không đoán,
người dùng ghi đè theo từng file) lấy từ app/detection/layer_classifier.py của dự án
floor-plan-exit-router (giấy phép MIT, xem THIRD_PARTY_NOTICES.md). Bộ quy tắc được viết lại
cho tên layer tiếng Việt và các vai trò cần cho đo bóc.
"""
from __future__ import annotations

from enum import Enum

from .encoding import normalize


class LayerClass(str, Enum):
    WALL = "WALL"
    OPENING = "OPENING"        # cửa đi, cửa sổ
    ANNOTATION = "ANNOTATION"  # kích thước, chữ, trục, khung tên
    IGNORE = "IGNORE"          # nội thất, thiết bị, hatch
    UNKNOWN = "UNKNOWN"


# (mẫu, vai trò): so trên tên layer đã chuẩn hóa (chữ thường, bỏ dấu). Mẫu khớp đầu tiên thắng.
# Đây là mặc định: mọi kết quả đều có thể bị người dùng ghi đè.
_DEFAULT_RULES: list[tuple[str, LayerClass]] = [
    ("cua", LayerClass.OPENING), ("door", LayerClass.OPENING), ("window", LayerClass.OPENING),
    ("glaz", LayerClass.OPENING),
    ("tuong", LayerClass.WALL), ("wall", LayerClass.WALL), ("xay", LayerClass.WALL),
    ("kich thuoc", LayerClass.ANNOTATION), ("kichthuoc", LayerClass.ANNOTATION), ("dim", LayerClass.ANNOTATION),
    ("text", LayerClass.ANNOTATION), ("chu", LayerClass.ANNOTATION), ("ghi chu", LayerClass.ANNOTATION),
    ("truc", LayerClass.ANNOTATION), ("grid", LayerClass.ANNOTATION), ("axis", LayerClass.ANNOTATION),
    ("khung", LayerClass.ANNOTATION), ("title", LayerClass.ANNOTATION), ("anno", LayerClass.ANNOTATION),
    ("noi that", LayerClass.IGNORE), ("noithat", LayerClass.IGNORE), ("furn", LayerClass.IGNORE),
    ("thiet bi", LayerClass.IGNORE), ("hatch", LayerClass.IGNORE), ("defpoints", LayerClass.IGNORE),
]


def default_classification(layer_names: list[str]) -> dict[str, LayerClass]:
    result: dict[str, LayerClass] = {}
    for name in layer_names:
        normalized = normalize(name).replace("_", " ").replace("-", " ")
        compact = normalized.replace(" ", "")
        matched = LayerClass.UNKNOWN
        for pattern, layer_class in _DEFAULT_RULES:
            if pattern in normalized or pattern.replace(" ", "") in compact:
                matched = layer_class
                break
        result[name] = matched
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
