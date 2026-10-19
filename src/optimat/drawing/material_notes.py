"""Đọc ghi chú vật liệu phần thô trên bản vẽ (Quy ước QU-20): bê tông, vữa, xi măng, cát, đá, thép, chống thấm, phụ kiện...

Quy tắc trong data/rules/material_notes.csv (sửa bằng Excel): mẫu đã bỏ dấu, chữ thường -> mã vật liệu của danh
mục (có DATABASE_URL thì đọc bảng material_notes). So NGUYÊN TỪ, không so chuỗi con, để "thep tron" không
khớp "thep trong", "ngoi do" không khớp "ngoi dong".
Khác material_rules.py (gán vật liệu cho từng tường): ở đây chỉ báo bản vẽ có ghi vật liệu nào, ghi ở đâu. Một ghi chú có thể
khớp nhiều vật liệu (ví dụ "xi mang bao" -> XM01, XM02): trả hết, người dùng chọn.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from .. import config
from .encoding import normalize

NOTES_FILE = config.DATA_DIR / "rules" / "material_notes.csv"


@dataclass(frozen=True)
class NoteRule:
    rule_id: str
    pattern: str
    material_id: str
    ten: str
    nguon: str           # danh_muc (tên gọi khác của danh mục) | de_xuat (cách ghi tắt trên bản vẽ)
    regex: re.Pattern


@dataclass(frozen=True)
class NoteHit:
    rule_id: str
    material_id: str
    ten: str
    text: str            # chữ gốc trên bản vẽ
    x: float
    y: float


@lru_cache(maxsize=4)
def load_note_rules(path: Optional[str] = None) -> tuple[NoteRule, ...]:
    from ..db.session import read_rule_table      # có DATABASE_URL: bảng material_notes, không thì CSV
    out = []
    for r in read_rule_table("material_notes", path, NOTES_FILE).to_dict("records"):
        p = normalize(r["pattern"]).strip()
        if not p or not r["material_id"].strip():
            raise ValueError(f"material_notes.csv, {r['rule_id']}: thiếu mẫu hoặc mã vật liệu.")
        out.append(NoteRule(r["rule_id"], p, r["material_id"].strip(), r["ten"], r["nguon"],
                            re.compile(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])")))
    return tuple(out)


def match_note(text: str, rules=None) -> list[NoteRule]:
    """Quy tắc khớp một chữ (mỗi mã vật liệu một lần)."""
    norm = normalize(text)
    seen, out = set(), []
    for r in rules or load_note_rules():
        if r.material_id not in seen and r.regex.search(norm):
            seen.add(r.material_id)
            out.append(r)
    return out


def find_material_notes(drawing, rules=None) -> list[NoteHit]:
    return [NoteHit(r.rule_id, r.material_id, r.ten, t.text.strip(), t.x, t.y)
            for t in drawing.texts for r in match_note(t.text, rules)]
