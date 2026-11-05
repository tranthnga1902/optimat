"""Bóc tách bằng quy tắc: từ tín hiệu trong bản vẽ (ghi chú, hatch, layer, block) suy ra vật liệu.

Bộ quy tắc nằm trong data/rules/material_rules.csv, sửa được bằng Excel, không cần sửa mã:
    signal   = text | hatch | layer | block
    pattern  = text, layer: chuỗi con trên tên đã chuẩn hóa (chữ thường, bỏ dấu)
               hatch: tên mẫu hatch (không phân biệt hoa thường)
               block: biểu thức chính quy trên tên block viết hoa
    target   = họ vật liệu của danh mục (AAC, CLAY_SOLID...) hoặc mã vật liệu (GN01); nhiều giá trị cách nhau bằng |
    element  = WALL_MASONRY | CONCRETE (không phải tường xây, loại khỏi khối lượng) | DOOR | WINDOW
    priority = số lớn hơn thắng khi nhiều quy tắc cùng khớp một tường

Cách áp dụng cho tường:
    text  : ghi chú có số chiều dày (110, 220...) áp dụng cho mọi tường cùng lớp chiều dày;
            ghi chú không có số chỉ áp dụng cho tường trong bán kính TEXT_RADIUS_MM.
            Viết tắt giãn trước theo data/rules/viet_tat.csv ("gạch kg nung" -> gạch không nung); ghi chú nhiều dòng
            xếp cột được ghép thành một đoạn làm tín hiệu bổ sung (text_blocks.py), từng dòng vẫn so như cũ
    hatch : áp dụng cho tường có ≥ NG10 chiều dài trục nằm trong vùng hatch. Hatch bị phá thành nét rời (trong block
            hoặc thẳng ra model) được dựng lại thành vùng "ANSI31" đoán (HatchItem.synthetic): nguồn "hatch_doan",
            tin cậy thấp hơn. Quy tắc không có target (H01) chỉ ghi căn cứ "là khối xây", không tranh với quy tắc có vật liệu
    layer : áp dụng cho tường nằm trên layer có tên khớp
Không quy tắc nào khớp thì vật liệu để trống: hệ thống không đoán.

Khớp với danh mục vật liệu (một nguồn: materials_master.xlsx -> bảng materials, wall_systems, material_aliases):
    - ngoài các quy tắc trong CSV, mỗi tên gọi khác của vật liệu tường (material_aliases) sinh một quy tắc ghi chú
      trỏ thẳng tới mã vật liệu, ưu tiên ALIAS_PRIORITY (tên gọi cụ thể thắng quy tắc theo họ);
    - họ hoặc mã vật liệu + lớp chiều dày tường được quy đổi sang phương án tường (wall_systems.detect_class) để có
      material_id và wall_system_id thật, dùng để tra giá. Danh mục có nhiều phương án thì để người dùng chọn.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache


from .. import config
from ..catalog.repository import Catalog, default_catalog
from ..db.session import read_rule_table
from ..schemas import WallSegment
from .dxf_reader import BlockRef, Drawing
from .encoding import expand_abbreviations, normalize
from .text_blocks import TextBlock, group_text_lines

RULES_PATH = config.DATA_DIR / "rules" / "material_rules.csv"
TEXT_RADIUS_MM = 2000.0
ALIAS_PRIORITY = 95
# hatch_doan: vùng hatch dựng lại từ nét rời (HatchItem.synthetic, tên mẫu đoán): tin cậy thấp hơn hatch đọc được thẳng
CONFIDENCE = {"text_thickness": 0.8, "hatch": 0.7, "text_near": 0.5, "layer": 0.5, "hatch_doan": 0.4}
MATERIAL_HINTS = ("gach", "tuong", "xay", "be tong", "vua")     # ghi chú có các từ này mà không khớp quy tắc sẽ được báo
_THICKNESS = {"100": "110", "105": "110", "110": "110", "150": "150", "200": "220", "220": "220", "300": "330", "330": "330"}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    signal: str
    pattern: str
    target: tuple[str, ...]          # họ hoặc mã vật liệu; rỗng: quy tắc không cho biết vật liệu
    element: str
    width_mm: float | None
    height_mm: float | None
    priority: int
    note: str


@lru_cache(maxsize=8)
def load_rules(path: str | None = None) -> tuple[Rule, ...]:
    df = read_rule_table("material_rules", path, RULES_PATH)
    rules = []
    for r in df.to_dict("records"):
        if r["signal"] not in ("text", "hatch", "layer", "block"):
            raise ValueError(f"Quy tắc {r['rule_id']}: signal không hợp lệ: {r['signal']}")
        rules.append(Rule(
            rule_id=r["rule_id"], signal=r["signal"], pattern=r["pattern"].strip(),
            target=tuple(t.strip() for t in r["target"].split("|") if t.strip()), element=r["element"].strip() or "WALL_MASONRY",
            width_mm=float(r["width_mm"]) if r["width_mm"] else None,
            height_mm=float(r["height_mm"]) if r["height_mm"] else None,
            priority=int(r["priority"] or 0), note=r["note"]))
    return _sorted(rules)


def _sorted(rules) -> tuple[Rule, ...]:
    return tuple(sorted(rules, key=lambda x: (-x.priority, -len(x.pattern))))


def alias_rules(catalog: Catalog) -> tuple[Rule, ...]:
    """Mỗi tên gọi khác của vật liệu tường trong danh mục thành một quy tắc ghi chú trỏ tới mã vật liệu."""
    if catalog.aliases.empty or "family" not in catalog.materials:
        return ()
    fam = catalog.materials.set_index("material_id").family
    wall_families = catalog.wall_families()
    out, seen = [], set()
    for a in catalog.aliases.sort_values(["material_id", "alias"]).itertuples():
        if fam.get(a.material_id) not in wall_families:
            continue
        pattern = normalize(str(a.alias)).strip()
        if len(pattern) < 4 or (pattern, a.material_id) in seen:
            continue
        seen.add((pattern, a.material_id))
        out.append(Rule(rule_id=f"A-{a.material_id}-{len([k for k in seen if k[1] == a.material_id])}", signal="text",
                        pattern=pattern, target=(a.material_id,), element="WALL_MASONRY", width_mm=None, height_mm=None,
                        priority=ALIAS_PRIORITY, note=f"Tên gọi khác trong danh mục: {a.alias}"))
    return tuple(out)


# bộ quy tắc gộp theo từng danh mục: Catalog chứa DataFrame nên không hash được, cache theo id() và giữ tham chiếu để
# id không bị tái dùng; apply_material_rules gọi cho từng mặt bằng của một file (takeoff_plans) và cho từng bản vẽ khi
# chạy hàng loạt (batch_takeoff), trước đây mỗi lần đều quét lại bảng material_aliases
_RULES_CACHE: dict[int, tuple[Catalog, tuple[Rule, ...], tuple[Rule, ...]]] = {}   # id(catalog) -> (catalog, csv, gộp)
_RULES_CACHE_MAX = 8


def all_rules(catalog: Catalog | None = None) -> tuple[Rule, ...]:
    """Quy tắc trong CSV + quy tắc sinh từ tên gọi khác của danh mục vật liệu (cache theo danh mục).
    Khóa cache gồm cả tuple của load_rules(): sau load_rules.cache_clear() (trang quản trị sửa quy tắc) bản gộp tự tính lại."""
    catalog = catalog or default_catalog()
    base = load_rules()
    hit = _RULES_CACHE.get(id(catalog))
    if hit is not None and hit[0] is catalog and hit[1] is base:
        return hit[2]
    rules = _sorted(base + alias_rules(catalog))
    if len(_RULES_CACHE) >= _RULES_CACHE_MAX:
        _RULES_CACHE.pop(next(iter(_RULES_CACHE)))
    _RULES_CACHE[id(catalog)] = (catalog, base, rules)
    return rules


def clear_rule_cache() -> None:
    """Xóa cache quy tắc (sau khi sửa material_rules.csv / danh mục trong cùng tiến trình, hoặc trong kiểm thử)."""
    _RULES_CACHE.clear()
    load_rules.cache_clear()


def rule_label(rule: Rule) -> str:
    """Kết quả của quy tắc để hiển thị: họ/mã vật liệu hoặc loại cấu kiện."""
    return "|".join(rule.target) or rule.element


def _best(rules, signal: str, value: str) -> Rule | None:
    """Quy tắc ưu tiên cao nhất khớp giá trị (danh sách đã sắp theo ưu tiên giảm dần)."""
    for rule in rules:
        if rule.signal != signal:
            continue
        if signal == "hatch" and rule.pattern.upper() == value.upper():
            return rule
        if signal == "block" and re.match(rule.pattern, value.upper()):
            return rule
        if signal in ("text", "layer") and _word(rule.pattern).search(value):
            return rule
    return None


def _best_text(rules, normalized: str) -> Rule | None:
    """Quy tắc ghi chú ưu tiên cao nhất, so trên chuỗi gốc đã bỏ dấu VÀ chuỗi đã giãn viết tắt (data/rules/viet_tat.csv):
    "gach kg nung" -> khớp T07 "gach khong nung"; quy tắc / tên gọi khác viết sẵn dạng tắt vẫn khớp như cũ."""
    expanded = expand_abbreviations(normalized)
    a = _best(rules, "text", normalized)
    if expanded == normalized:
        return a
    b = _best(rules, "text", expanded)
    if a is None or b is None:
        return a or b
    return a if (a.priority, len(a.pattern)) >= (b.priority, len(b.pattern)) else b


@lru_cache(maxsize=2048)
def _word(pattern: str) -> re.Pattern:
    """So nguyên từ: "thep tron" không khớp "thep trong", "ngoi do" không khớp "ngoi dong"."""
    return re.compile(rf"(?<![a-z0-9]){re.escape(pattern)}(?![a-z0-9])")


def block_rule(block: BlockRef, rules=None) -> Rule | None:
    return _best(rules or load_rules(), "block", block.name)


def _hatch_share(w, polygons, n: int = 9) -> float:
    """Phần chiều dài tường nằm trong vùng hatch (n điểm đều dọc trục). Trước đây chỉ thử điểm giữa: tường 7,7 m có điểm
    giữa rơi vào ô tô đặc của một cột bị coi cả bức là vách bê tông (bộ 46)."""
    xs = [x for p in polygons for x, _ in p]
    ys = [y for p in polygons for _, y in p]
    if not xs or max(w.x1, w.x2) < min(xs) or min(w.x1, w.x2) > max(xs) or max(w.y1, w.y2) < min(ys) or min(w.y1, w.y2) > max(ys):
        return 0.0
    ts = [(k + 0.5) / n for k in range(n)]
    return sum(_inside(w.x1 + (w.x2 - w.x1) * t, w.y1 + (w.y2 - w.y1) * t, polygons) for t in ts) / n


def _inside(px: float, py: float, polygons) -> bool:
    """Điểm nằm trong vùng hatch theo quy tắc chẵn lẻ (biên lồng trong biên là lỗ rỗng)."""
    inside = False
    for poly in polygons:
        j = len(poly) - 1
        for i in range(len(poly)):
            (xi, yi), (xj, yj) = poly[i], poly[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
    return inside


def _dist_to_wall(px: float, py: float, w: WallSegment) -> float:
    dx, dy = w.x2 - w.x1, w.y2 - w.y1
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - w.x1) * dx + (py - w.y1) * dy) / length2))
    return math.hypot(px - (w.x1 + t * dx), py - (w.y1 + t * dy))


def apply_material_rules(drawing: Drawing, walls: list[WallSegment], catalog: Catalog | None = None,
                         rules=None) -> tuple[dict[str, int], dict[str, list[str]], list[str]]:
    """Gán vật liệu theo thiết kế cho từng tường, quy về mã của danh mục.
    Trả về (số lần khớp của từng quy tắc, tín hiệu chưa có quy tắc, ghi chú khi chưa quy đổi được sang danh mục)."""
    catalog = catalog or default_catalog()
    rules = rules or all_rules(catalog)
    candidates: dict[str, list[tuple[int, float, Rule, str]]] = {w.wall_id: [] for w in walls}
    confirm_only: dict[str, list[tuple[int, float, Rule, str]]] = {w.wall_id: [] for w in walls}   # H01: chỉ xác nhận xây
    hits: dict[str, int] = {}
    unmatched = {"hatch": set(), "text": set(), "block": set()}

    # ghi chú: từng dòng TEXT như trước, cộng thêm đoạn ghép từ nhiều dòng xếp cột (text_blocks.py) làm tín hiệu bổ sung
    blocks = group_text_lines(drawing.texts)
    for text in list(drawing.texts) + blocks:
        norm = normalize(text.text)
        rule = _best_text(rules, norm)
        if rule is None:
            if any(h in norm for h in MATERIAL_HINTS) and not isinstance(text, TextBlock):
                unmatched["text"].add(text.text.strip()[:80])
            continue
        classes = {_THICKNESS[m] for m in re.findall(r"\b(100|105|110|150|200|220|300|330)\b", norm)}
        for w in walls:
            if classes and w.thickness_class in classes:
                candidates[w.wall_id].append((rule.priority, CONFIDENCE["text_thickness"], rule, "text"))
            elif not classes and _dist_to_wall(text.x, text.y, w) <= TEXT_RADIUS_MM:
                candidates[w.wall_id].append((rule.priority, CONFIDENCE["text_near"], rule, "text"))
    if blocks:   # dòng lẻ bị báo "chưa có quy tắc" nhưng đoạn ghép chứa nó đã khớp: không báo nữa
        matched_lines = {id(line) for b in blocks if _best_text(rules, normalize(b.text)) for line in b.lines}
        unmatched["text"] -= {t.text.strip()[:80] for t in drawing.texts if id(t) in matched_lines}

    for hatch in drawing.hatches:
        rule = _best(rules, "hatch", hatch.pattern)
        if rule is None:
            # *EXPLODED* là khung bao tự dựng của hatch bị phá (đã có bản synthetic ANSI31 đi kèm): không phải mẫu lạ
            if not getattr(hatch, "synthetic", False) and hatch.pattern != "*EXPLODED*":
                unmatched["hatch"].add(hatch.pattern)
            continue
        # hatch dựng lại từ nét rời (bị phá, tên mẫu đoán): ghi nguồn riêng, tin cậy thấp hơn hatch đọc được thẳng
        source = "hatch_doan" if getattr(hatch, "synthetic", False) else "hatch"
        # quy tắc không có target (H01 ANSI31): chỉ xác nhận là khối xây, không cho biết vật liệu -> không tranh với
        # quy tắc có vật liệu; chỉ ghi nguồn khi tường không có quy tắc nào khác
        bucket = confirm_only if not rule.target and rule.element == "WALL_MASONRY" else candidates
        for w in walls:
            if _hatch_share(w, hatch.polygons) >= config.threshold("NG10"):
                bucket[w.wall_id].append((rule.priority, CONFIDENCE[source], rule, source))

    for w in walls:
        rule = _best(rules, "layer", normalize(w.layer).replace("_", " ").replace("-", " "))
        if rule is not None:
            candidates[w.wall_id].append((rule.priority, CONFIDENCE["layer"], rule, "layer"))

    for block in drawing.blocks:
        if drawing.layer_classes.get(block.layer) is not None and str(drawing.layer_classes[block.layer].value) == "OPENING" \
                and block_rule(block, rules) is None:
            unmatched["block"].add(block.name)

    notes: dict[str, set[str]] = {}
    # quy đổi (họ/mã vật liệu, lớp dày) -> phương án tường chỉ tính một lần cho mỗi cặp: resolve_wall lọc DataFrame
    # (đo trên mặt bằng 400 tường: 95% thời gian apply_material_rules nằm ở đây khi gọi riêng cho từng tường)
    resolved: dict[tuple[tuple[str, ...], str], object] = {}
    for w in walls:
        if not candidates[w.wall_id]:
            if confirm_only[w.wall_id]:      # chỉ có hatch mặt cắt khối xây: ghi căn cứ, vật liệu vẫn để trống
                _, conf, rule, source = max(confirm_only[w.wall_id], key=lambda c: (c[0], c[1]))
                hits[rule.rule_id] = hits.get(rule.rule_id, 0) + 1
                w.material_source, w.material_rule, w.material_confidence = source, rule.rule_id, conf
            continue
        priority, conf, rule, source = max(candidates[w.wall_id], key=lambda c: (c[0], c[1]))
        hits[rule.rule_id] = hits.get(rule.rule_id, 0) + 1
        w.material_source, w.material_rule, w.material_confidence = source, rule.rule_id, conf
        if rule.element == "CONCRETE":
            w.is_masonry = False
            continue
        key = (rule.target, w.thickness_class)
        if key not in resolved:
            resolved[key] = resolve(catalog, rule.target, w.thickness_class)
        res = resolved[key]
        w.material_family, w.material_id, w.wall_system_id = res.family, res.material_id, res.wall_system_id
        w.material_candidates = list(res.candidates)
        if res.note:
            notes.setdefault(res.note, set()).add(w.wall_id)
    messages = [f"{note} ({len(ids)} tường)" for note, ids in sorted(notes.items())]
    return hits, {k: sorted(v)[:50] for k, v in unmatched.items() if v}, messages


def resolve(catalog: Catalog, target: tuple[str, ...], thickness_class: str):
    """Mã vật liệu cụ thể (tên gọi khác) không có phương án ở lớp chiều dày này thì xét cả họ của nó:
    ví dụ "gạch siêu nhẹ" là tên gọi của AAC01 nhưng ghi cho tường 220 thì phương án đúng là W-AAC03-200."""
    res = catalog.resolve_wall(list(target), thickness_class)
    if res.wall_system_id is None and not res.candidates and res.family and "|" not in res.family:
        by_family = catalog.resolve_wall([res.family], thickness_class)
        if by_family.wall_system_id or by_family.candidates:
            return by_family
    return res
