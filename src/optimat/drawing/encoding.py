"""Chuyển chữ tiếng Việt mã cũ trong bản vẽ về Unicode.

Hỗ trợ:
- TCVN3 (ABC, các font .VnTime, .VnArial, vn*.shx): mỗi chữ có dấu là một ký tự.
- VNI-Windows (font VNI-…): nguyên âm + ký tự dấu đứng sau ("MAËT BAÈNG" = MẶT BẰNG).
- Mã cũ 2 (chưa rõ tên, kiểu chữ không khai báo font): chữ gốc ă â ê ô ơ ư đ là một ký tự, dấu thanh đứng sau
  ("MÀÛT BÀÒNG TÁÖNG" = MẶT BẰNG TẦNG). Không tìm được tài liệu gốc; bảng dưới suy từ chữ trên bản vẽ
  Mau_nha_25x5 (28/10/2026), các ký tự chưa thấy trên bản vẽ để nguyên.
Font VH*.TTF (VHARIAL, VHAVAN, VHELVCN0…) là font TCVN3 ("Mãng" = Móng, "nhµ ë biÖt thù" = nhà ở biệt thự).
LƯU Ý: bảng ánh xạ cần được kiểm tra lại trên chính các bản vẽ bạn thu thập;
font SHX tự chế của từng công ty có thể dùng bảng mã riêng.
"""
from __future__ import annotations

import re
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


_ACUTE, _GRAVE, _HOOK, _TILDE, _DOT = "́", "̀", "̉", "̃", "̣"
_CIRC, _BREVE = "̂", "̆"
_VOWELS = set("aeiouyAEIOUY")


def _pairs(table: dict[str, str]) -> dict[str, str]:
    """Bảng chữ hoa -> thêm chữ thường tương ứng."""
    return {**table, **{k.lower(): v.lower() for k, v in table.items()}}


# VNI-Windows: ký tự dấu ghép vào nguyên âm đứng trước; Ô, Ö, Ñ... là chữ đứng riêng
_VNI_MARK = _pairs({"Ù": _ACUTE, "Ø": _GRAVE, "Û": _HOOK, "Õ": _TILDE, "Ï": _DOT,
                    "Â": _CIRC, "Á": _CIRC + _ACUTE, "À": _CIRC + _GRAVE, "Å": _CIRC + _HOOK,
                    "Ã": _CIRC + _TILDE, "Ä": _CIRC + _DOT,
                    "Ê": _BREVE, "É": _BREVE + _ACUTE, "È": _BREVE + _GRAVE, "Ú": _BREVE + _HOOK,
                    "Ü": _BREVE + _TILDE, "Ë": _BREVE + _DOT})
_VNI_CHAR = _pairs({"Ñ": "Đ", "Ö": "Ư", "Ô": "Ơ", "Ò": "Ị", "Ó": "Ỉ", "Æ": "Ĩ"})

# Mã cũ 2: chữ gốc một ký tự, dấu thanh đứng sau (mỗi nhóm nguyên âm một dãy ký tự dấu riêng)
_MC2_CHAR = _pairs({"À": "Ă", "Á": "Â", "Â": "Đ", "Ã": "Ê", "Ä": "Ô", "Å": "Ơ", "Æ": "Ư", "Ê": "Í", "Ë": "Ị"})
_MC2_MARK = _pairs({"Ì": _GRAVE, "Í": _HOOK, "Î": _TILDE, "Ï": _ACUTE,        # sau a e i o u y ơ ư
                   "Ò": _GRAVE, "Ó": _HOOK, "Ô": _TILDE, "Õ": _ACUTE,        # sau ă (Ó, Ô suy theo dãy, chưa thấy)
                   "Ö": _GRAVE, "Ø": _HOOK, "Ù": _TILDE, "Ú": _ACUTE,        # sau â ê ô
                   "Û": _DOT, "Ü": _DOT})

# Ký tự không bao giờ có trong tiếng Việt Unicode: có chúng (và không có chữ Unicode tiếng Việt) là mã cũ
_LEGACY = set("ÄÅÆËÎÏÑÖØÛÜäåæëîïñöøûü")
_UNICODE_VI = re.compile("[ĂăĐđƠơƯưẠ-ỹ]")
_VNI_SIGN = re.compile("[AEIOUYaeiouy][ÂÁÀÅÃÄÊÉÈÚÜËÙØÛÕÏâáàåãäêéèúüëùøûõï]|[Ññ]|[Öö][ÔôÙØÛÕÏùøûõï]")
_MC2_SIGN = re.compile("[AEIOUYaeiouy][ÌÍÎìíî]|Â[A-Z0-9]")
# chữ gốc + dấu thanh của mã cũ 2: VNI không có cặp này; nguyên âm đôi mã cũ 2 (iã = iê, uä = uô) lại giống dấu VNI nên cặp này tính 2
_MC2_PAIR = re.compile("[ÀÁÃÄÅÆàáãäåæ][ÌÍÎÏÒÓÔÕÖØÙÚÛÜìíîïòóôõöøùúûü]")


def legacy_kind(text: str) -> str | None:
    """'vni' hoặc 'ma_cu_2' khi nội dung là chữ mã cũ (đếm các cặp nguyên âm + dấu đặc trưng), không thì None."""
    if not any(ch in _LEGACY for ch in text) or _UNICODE_VI.search(text):
        return None
    vni = len(_VNI_SIGN.findall(text))
    vh = len(_MC2_SIGN.findall(text)) + 2 * len(_MC2_PAIR.findall(text))
    if vni == vh == 0:
        return None
    return "vni" if vni > vh else "ma_cu_2"


def detect_encoding(font_name: str | None, text: str = "", hint: str | None = None) -> str:
    """Trả về 'tcvn3', 'vni', 'ma_cu_2' hoặc 'unicode' dựa trên tên font, dự phòng bằng nội dung.
    hint: bảng mã cũ đoán trên mọi chữ cùng kiểu chữ (legacy_kind), dùng khi tên font và chính dòng chữ không đủ.
    Font TCVN3 mà chữ không có ký tự đặc trưng TCVN3 nhưng rõ là VNI / mã cũ 2 (bản vẽ đổi font giữa chừng): theo nội dung."""
    font = (font_name or "").lower()
    if font.startswith((".vn", "vh")) or (font.startswith("vn") and font.endswith(".shx")):
        if text and not any(ch in _TCVN3_MARKERS for ch in text) and (kind := legacy_kind(text)):
            return kind
        return "tcvn3"
    if font.startswith("vni"):
        return "vni"
    if any(ch in _TCVN3_MARKERS for ch in text):
        return "tcvn3"
    if _UNICODE_VI.search(text):
        return "unicode"
    return legacy_kind(text) or (hint if any(ord(ch) > 127 for ch in text) else None) or "unicode"


def tcvn3_to_unicode(text: str) -> str:
    return "".join(_TCVN3.get(ch, ch) for ch in text)


def _compose(text: str, chars: dict[str, str], marks: dict[str, str]) -> str:
    """Ký tự dấu ghép vào chữ đứng trước nếu đó là nguyên âm; không thì đổi theo bảng chữ đứng riêng."""
    out: list[str] = []
    for ch in text:
        base = unicodedata.normalize("NFD", out[-1])[0] if out else ""
        if out and ch in marks and (base in _VOWELS or base in "ƠơƯư"):
            out[-1] = unicodedata.normalize("NFC", out[-1] + marks[ch])
        else:
            out.append(chars.get(ch, ch))
    return "".join(out)


def vni_to_unicode(text: str) -> str:
    return _compose(text, _VNI_CHAR, _VNI_MARK)


def ma_cu_2_to_unicode(text: str) -> str:
    return _compose(text, _MC2_CHAR, _MC2_MARK)


def to_unicode(text: str, font_name: str | None = None, hint: str | None = None) -> tuple[str, str]:
    """Trả về (chuỗi Unicode, bảng mã đã nhận)."""
    enc = detect_encoding(font_name, text, hint)
    if enc == "tcvn3":
        return tcvn3_to_unicode(text), enc
    if enc == "vni":
        return vni_to_unicode(text), enc
    if enc == "ma_cu_2":
        return ma_cu_2_to_unicode(text), enc
    return text, enc


def normalize(text: str) -> str:
    """Chữ thường, bỏ dấu: dùng để so khớp tên layer và từ khóa ghi chú."""
    text = text.lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


# ---- Từ viết tắt trên bản vẽ (data/rules/viet_tat.csv) ----
# Ghi chú vật liệu hay viết tắt ("BTCT", "vữa XM", "gạch kg nung"): giãn ra chữ đầy đủ (đã bỏ dấu) trước khi so với
# material_rules.csv / material_notes.csv, để không phải thêm một dòng quy tắc cho mỗi cách viết tắt.
# Chỉ áp cho ghi chú chữ, không áp cho tên layer. So nguyên từ, mẫu dài xét trước ("gach bt" trước "bt").
_ABBREV: list[tuple["re.Pattern", str]] | None = None     # đọc ở lần dùng đầu (config import muộn, tránh import vòng)


def load_abbreviations(path=None) -> list[tuple[str, str]]:
    """Danh sách (viết tắt đã bỏ dấu, chữ đầy đủ đã bỏ dấu) theo thứ tự mẫu dài trước. Thiếu ô thì báo lỗi."""
    import csv

    from .. import config
    p = path or config.DATA_DIR / "rules" / "viet_tat.csv"
    out = []
    with open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            short, full = normalize(r["viet_tat"]).strip(), normalize(r["day_du"]).strip()
            if not short or not full:
                raise ValueError(f"viet_tat.csv, {r['ma']}: thiếu viết tắt hoặc chữ đầy đủ.")
            out.append((short, full))
    return sorted(out, key=lambda x: -len(x[0]))


def expand_abbreviations(normalized: str) -> str:
    """Giãn từ viết tắt trong chuỗi đã normalize(). Không khớp gì thì trả nguyên chuỗi."""
    global _ABBREV
    if _ABBREV is None:
        _ABBREV = [(re.compile(rf"(?<![a-z0-9]){re.escape(s)}(?![a-z0-9])"), f) for s, f in load_abbreviations()]
    for rx, full in _ABBREV:
        normalized = rx.sub(full, normalized)
    return normalized


def reset_abbreviations() -> None:
    """Đọc lại viet_tat.csv ở lần gọi sau (sau khi sửa file trong cùng tiến trình, hoặc trong kiểm thử)."""
    global _ABBREV
    _ABBREV = None
