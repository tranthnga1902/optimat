"""Chuyển chữ tiếng Việt mã cũ trong bản vẽ về Unicode.

Hiện hỗ trợ TCVN3 (ABC, các font .VnTime, .VnArial, vn*.shx). Bảng VNI chưa có.
LƯU Ý: bảng ánh xạ cần được kiểm tra lại trên chính các bản vẽ bạn thu thập;
font SHX tự chế của từng công ty có thể dùng bảng mã riêng.
"""
from __future__ import annotations

import unicodedata

_TCVN3_LOWER = {
    "µ": "à", "¸": "á", "¶": "ả", "·": "ã", "¹": "ạ",
    "¨": "ă", "»": "ằ", "¾": "ắ", "¼": "ẳ", "½": "ẵ", "Æ": "ặ",
    "©": "â", "Ç": "ầ", "Ê": "ấ", "È": "ẩ", "É": "ẫ", "Ë": "ậ",
    "®": "đ",
    "Ì": "è", "Ð": "é", "Î": "ẻ", "Ï": "ẽ", "Ñ": "ẹ",
    "ª": "ê", "Ò": "ề", "Õ": "ế", "Ó": "ể", "Ô": "ễ", "Ö": "ệ",
    "×": "ì", "Ý": "í", "Ø": "ỉ", "Ü": "ĩ", "Þ": "ị",
    "ß": "ò", "ã": "ó", "á": "ỏ", "â": "õ", "ä": "ọ",
    "«": "ô", "å": "ồ", "è": "ố", "æ": "ổ", "ç": "ỗ", "é": "ộ",
    "¬": "ơ", "ê": "ờ", "í": "ớ", "ë": "ở", "ì": "ỡ", "î": "ợ",
    "ï": "ù", "ó": "ú", "ñ": "ủ", "ò": "ũ", "ô": "ụ",
    "­": "ư", "õ": "ừ", "ø": "ứ", "ö": "ử", "÷": "ữ", "ù": "ự",
    "ú": "ỳ", "ý": "ý", "û": "ỷ", "ü": "ỹ", "þ": "ỵ",
}
_TCVN3_UPPER = {"¡": "Ă", "¢": "Â", "§": "Đ", "£": "Ê", "¤": "Ô", "¥": "Ơ", "¦": "Ư"}
_TCVN3 = {**_TCVN3_LOWER, **_TCVN3_UPPER}

# Ký tự chỉ xuất hiện khi chữ là TCVN3 chưa chuyển mã (dùng để đoán khi không biết font).
_TCVN3_MARKERS = set("µ¸¶·¹¨»¾¼½©®ª«¬­")


def detect_encoding(font_name: str | None, text: str = "") -> str:
    """Trả về 'tcvn3', 'vni' hoặc 'unicode' dựa trên tên font, dự phòng bằng nội dung."""
    font = (font_name or "").lower()
    if font.startswith(".vn") or (font.startswith("vn") and font.endswith(".shx")):
        return "tcvn3"
    if font.startswith("vni"):
        return "vni"
    if any(ch in _TCVN3_MARKERS for ch in text):
        return "tcvn3"
    return "unicode"


def tcvn3_to_unicode(text: str) -> str:
    return "".join(_TCVN3.get(ch, ch) for ch in text)


def to_unicode(text: str, font_name: str | None = None) -> tuple[str, str]:
    """Trả về (chuỗi Unicode, bảng mã đã nhận). VNI chưa hỗ trợ: giữ nguyên và báo 'vni'."""
    enc = detect_encoding(font_name, text)
    if enc == "tcvn3":
        return tcvn3_to_unicode(text), enc
    return text, enc


def normalize(text: str) -> str:
    """Chữ thường, bỏ dấu: dùng để so khớp tên layer và từ khóa ghi chú."""
    text = text.lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
