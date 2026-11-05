"""KD03: trích thông số công trình từ ghi chú bản vẽ (TEXT) và đoạn thuyết minh DOCX.

Thứ tự: quy tắc data/rules/ghi_chu_thong_so.csv (không cần AI) → AI gắn nhãn dòng còn lại (danh mục FIELDS) → mã đọc số
từ trích đoạn bằng regex theo loại trường. Mọi giá trị là gợi ý mức B, người dùng xác nhận mới vào ProjectParams (B7).
Nhiều giá trị khác nhau cho cùng thông số: không chọn, đưa vào conflicts để người dùng chọn.
"""
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .. import config
from . import Fact, FactReport, ai
from .verify import norm

RULE_FILE = config.DATA_DIR / "rules" / "ghi_chu_thong_so.csv"
NUM = r"(\d+(?:[.,]\d+)?)"
# trường ProjectParams -> (mô tả cho AI, cách đọc số)
FIELDS = {
    "plaster_thickness_mm": ("Chiều dày lớp vữa trát tường/trần (mm)", "thickness"),
    "screed_thickness_mm": ("Chiều dày lớp vữa cán/lót/lát/tạo phẳng nền (mm)", "thickness"),
    "slab_thickness_mm": ("Chiều dày bản sàn bê tông cốt thép (mm)", "thickness"),
    "stair_slab_thickness_mm": ("Chiều dày bản thang (mm)", "thickness"),
    "lintel_height_mm": ("Chiều cao tiết diện lanh tô (mm)", "thickness"),
    "lintel_bearing_mm": ("Chiều dài gối lanh tô lên tường mỗi bên (mm)", "thickness"),
    "waterproof_upturn_mm": ("Chiều cao quét chống thấm lên chân tường (mm)", "thickness"),
    "beam_section": ("Tiết diện dầm chung cho công trình, rộng x cao (mm)", "section"),
    "concrete_grade": ("Mác bê tông kết cấu cột, dầm, sàn (ghi M…, mác…, #…)", "grade"),
    "lean_concrete_grade": ("Mác bê tông lót", "grade"),
    "masonry_mortar_grade": ("Mác vữa xây", "grade"),
    "plaster_mortar_grade": ("Mác vữa trát", "grade"),
    "screed_mortar_grade": ("Mác vữa cán/lót/lát nền", "grade"),
}
INSTRUCTIONS = ("Gắn nhãn thông số kỹ thuật phần thô được ghi trong dòng. Chỉ gắn khi dòng ghi rõ giá trị (số) của "
                "thông số đó. excerpt phải chứa cả từ khóa và con số, ví dụ 'trát trần #75 dày 15'.")


@lru_cache(maxsize=2)
def load_rules(path: str | None = None) -> tuple[tuple[str, re.Pattern, str], ...]:
    rows = pd.read_csv(Path(path or RULE_FILE), dtype=str, keep_default_na=False).to_dict("records")
    bad = [r["ma"] for r in rows if r["truong"] not in FIELDS]
    if bad:
        raise ValueError(f"ghi_chu_thong_so.csv: trường không hợp lệ ở {', '.join(bad)}.")
    return tuple((r["ma"], re.compile(r["mau"]), r["truong"]) for r in rows)


def _f(text: str) -> float:
    return float(text.replace(",", "."))


def read_value(field: str, excerpt: str):
    """Đọc giá trị từ trích đoạn; None nếu không đọc được chắc chắn (không đoán)."""
    t = norm(excerpt)
    kind = FIELDS[field][1]
    if kind == "grade":
        # mác đọc SAU từ khóa của vật liệu: "gạch đặc mác 75 với vữa xi măng mác 50" -> vữa M50, không phải M75
        anchor = {"lean_concrete_grade": r"be tong lot|lot\b", "concrete_grade": r"be tong|btct"}.get(field, r"vua|vxm")
        a = re.search(anchor, t)
        if not a:
            return None
        t = t[a.start():]
        m = (re.search(r"\bm\s*" + NUM, t) or re.search(r"mac\s*" + NUM, t) or re.search(r"#\s*" + NUM, t)
             or re.search(NUM + r"\s*#", t))
        return f"M{_f(m.group(1)):g}" if m else None
    if kind == "section":
        m = re.search(NUM + r"\s*[x×*]\s*" + NUM, t)
        return [_f(m.group(1)), _f(m.group(2))] if m else None
    m = re.search(r"(?:day|d\s*=|h\s*=|cao|dai)\s*(?:tb\s*)?[:=]?\s*" + NUM + r"\s*(mm|cm|m)?\b", t)
    if not m:
        return None
    scale = {"cm": 10, "m": 1000}.get(m.group(2) or "", 1)
    return _f(m.group(1)) * scale


def candidates(texts) -> list[dict]:
    """Dòng chữ đáng xét: có chữ số, dài vừa phải; gộp dòng trùng (giữ ref đầu)."""
    seen, out = set(), []
    for ref, text in texts:
        key = norm(text)
        if not (6 <= len(key) <= 240) or not re.search(r"\d", key) or not re.search(r"[a-z]{2}", key) or key in seen:
            continue
        seen.add(key)
        out.append({"ref": ref, "text": re.sub(r"\s+", " ", text).strip()})
    return out


def cad_texts(drawing) -> list[tuple[str, str]]:
    return [(f"t{i}", t.text) for i, t in enumerate(drawing.texts)]


def extract(items: list[dict], source_file: str, allow_ai: bool) -> FactReport:
    """items: [{ref, text}] (CAD: cad_texts → candidates; DOCX: đoạn p<n>)."""
    report, rest = FactReport(), []
    for item in items:
        t, hit = norm(item["text"]), False
        for ma, pat, field in load_rules():
            if pat.search(t):
                value = read_value(field, item["text"])
                if value is not None:
                    report.facts.append(Fact(field=field, value=value, task="thong_so", source_file=source_file,
                                             ref=item["ref"], excerpt=item["text"], method="rule", rule=ma))
                    hit = True
        if not hit:
            rest.append(item)
    labels = {k: v[0] for k, v in FIELDS.items()}
    accepted, rejected, report.ai = ai.label("thong_so", INSTRUCTIONS, rest, labels, allow_ai, source_file)
    for p in accepted:
        value = read_value(p["label"], p["excerpt"])
        if value is None:
            rejected.append({**p, "reason": "không đọc được số từ trích đoạn"})
            continue
        report.facts.append(Fact(field=p["label"], value=value, task="thong_so", source_file=source_file, ref=p["ref"],
                                 excerpt=p["excerpt"], method="ai_label", note=p["text"]))
    report.rejected = rejected
    return report


def suggest(facts: list[Fact]) -> tuple[dict, dict]:
    """(gợi ý: trường -> {value, sources}; xung đột: trường -> [{value, sources}]). Không tự chọn khi nhiều giá trị."""
    by_field: dict[str, dict] = defaultdict(lambda: defaultdict(list))
    for f in facts:
        if f.task != "thong_so":
            continue
        by_field[f.field][repr(f.value)].append(f)
    suggestions, conflicts = {}, {}
    for field, values in by_field.items():
        options = [{"value": fs[0].value, "status": "B", "methods": sorted({x.method for x in fs}),
                    "sources": [{"file": x.source_file, "ref": x.ref, "excerpt": x.excerpt} for x in fs[:5]],
                    "count": len(fs)} for fs in values.values()]
        if len(options) == 1:
            suggestions[field] = options[0]
        else:
            conflicts[field] = sorted(options, key=lambda o: -o["count"])
    return suggestions, conflicts
