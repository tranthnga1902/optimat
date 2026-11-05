"""Đo bóc khối lượng tường: diện tích = dài x cao - lỗ mở, gộp theo loại tường và vai trò.

Vật liệu theo thiết kế của từng tường được suy ra bằng bộ quy tắc trong material_rules.py.
File có nhiều mặt bằng thì takeoff_plans() tách từng mặt bằng (plans.py) và đo bóc riêng.
"""
from __future__ import annotations

import math
from typing import Optional

from ..catalog.repository import Catalog
from ..schemas import OpeningDefaults, OpeningItem, PlanTakeoff, TakeoffResult, WallGroup, WallSegment
from .concepts import match_block
from .dxf_reader import BlockRef, Drawing, crop, read_drawing
from .layer_classifier import LayerClass
from .material_rules import apply_material_rules, block_rule
from .encoding import normalize
from .plans import HEADING_WORDS, find_plans, floor_heights, floor_order, has_only_other_plans, has_only_views, level_chain
from .walls import (LENGTH_RULES, _project, bridge_openings, choose_wall_layers, dedupe_walls, detect_walls, extend_corners,
                    hatch_strip_walls, net_lengths)


def _is_opening(block: BlockRef, drawing: Drawing) -> bool:
    if drawing.layer_classes.get(block.layer) == LayerClass.OPENING or block_rule(block) is not None:
        return True
    return match_block(block.name) is not None


LEAF_REACH_MM = 1500.0      # cung cánh cửa thuộc block khi tâm cung cách điểm chèn không quá chừng này


def leaf_width_mm(block: BlockRef, arcs) -> Optional[float]:
    """KD08: rộng cửa đi đọc từ hình của chính block = tổng bán kính cung cánh cửa (cánh đơn 1 cung, cánh đôi 2 cung,
    góc mở 60–120°). Đọc trực tiếp trên bản vẽ; không có cung thì None (không đoán)."""
    leaves = sorted((a for a in arcs if a.source == block.name and 60 <= a.sweep <= 120
                     and math.hypot(a.cx - block.x, a.cy - block.y) <= LEAF_REACH_MM),
                    key=lambda a: math.hypot(a.cx - block.x, a.cy - block.y))[:2]
    return round(sum(a.r for a in leaves)) if leaves else None


def _opening_size_mm(block: BlockRef, openings: OpeningDefaults | None, arcs=()) -> Optional[tuple[float, float]]:
    """Thứ tự: thuộc tính WIDTH/HEIGHT của block, quy tắc block trong file quy tắc, kích thước cửa của dự án theo loại
    block (QU-14, không khớp thì như cửa đi). Rộng cửa đi còn thiếu thì đo cung cánh cửa trong block (KD08).
    Không có số thì None: chưa trừ lỗ mở (Quy ước B7)."""
    try:
        return float(block.attribs["WIDTH"]), float(block.attribs["HEIGHT"])
    except (KeyError, ValueError):
        pass
    rule = block_rule(block)
    if rule is not None and rule.width_mm and rule.height_mm:
        return rule.width_mm, rule.height_mm
    signal = match_block(block.name)
    kind = signal.vai_tro if signal else "door"
    w, h = getattr(openings, f"{kind}_width_mm", None), getattr(openings, f"{kind}_height_mm", None)
    if not w and kind == "door":
        w = leaf_width_mm(block, arcs)
    return (w, h) if w and h else None


def _dist_point_segment(px: float, py: float, w: WallSegment) -> float:
    dx, dy = w.x2 - w.x1, w.y2 - w.y1
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - w.x1) * dx + (py - w.y1) * dy) / length2))
    return math.hypot(px - (w.x1 + t * dx), py - (w.y1 + t * dy))


def _ray_hits(px: float, py: float, dx: float, dy: float, walls: list[WallSegment], skip: str) -> bool:
    """Tia từ (px, py) theo hướng (dx, dy) có cắt trục tim tường nào khác trong 60 m không."""
    for w in walls:
        if w.wall_id == skip:
            continue
        ex, ey = w.x2 - w.x1, w.y2 - w.y1
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((w.x1 - px) * ey - (w.y1 - py) * ex) / den
        u = ((w.x1 - px) * dy - (w.y1 - py) * dx) / den
        half = ((w.thickness_mm or float(w.thickness_class)) / 2) / (math.hypot(ex, ey) or 1)
        if 0 < t < 60000 and -half <= u <= 1 + half:
            return True
    return False


def mark_envelope(walls: list[WallSegment]) -> dict[str, str]:
    """Vai trò từng tường: một phía nhìn ra ngoài nhà (tia không gặp tường nào) là tường bao che."""
    roles = {}
    for w in walls:
        L = math.hypot(w.x2 - w.x1, w.y2 - w.y1) or 1.0
        nx, ny = -(w.y2 - w.y1) / L, (w.x2 - w.x1) / L
        off = (w.thickness_mm or float(w.thickness_class)) / 2 + 50
        outside = 0
        for f in (0.25, 0.5, 0.75):
            mx, my = w.x1 + (w.x2 - w.x1) * f, w.y1 + (w.y2 - w.y1) * f
            for sgn in (1, -1):
                if not _ray_hits(mx + sgn * nx * off, my + sgn * ny * off, sgn * nx, sgn * ny, walls, w.wall_id):
                    outside += 1
                    break
        roles[w.wall_id] = "envelope" if outside >= 2 else "partition"
    return roles


def compute_takeoff(drawing: Drawing, floor_height_mm: float | None = None,
                    catalog: "Catalog | None" = None, height_note: str | None = None,
                    openings: OpeningDefaults | None = None, length_rule: str = "tim") -> TakeoffResult:
    """catalog: danh mục vật liệu để quy đổi vật liệu ghi trên bản vẽ sang mã thật (GN01, W-GN01-220);
    None thì dùng danh mục mặc định (PostgreSQL hoặc data/catalog). openings: kích thước cửa của dự án.
    Không có chiều cao tầng thì vẫn nhận tường, cửa nhưng chưa tính diện tích (groups rỗng).
    length_rule: "tim" (trục tim) hoặc "thong_thuy" (giữa các mặt tường giao) cho chiều dài và diện tích của groups."""
    if length_rule not in LENGTH_RULES:
        raise ValueError(f"Quy tắc chiều dài không hợp lệ: {length_rule} (chỉ nhận {', '.join(LENGTH_RULES)}).")
    height = floor_height_mm or None
    warnings = list(drawing.warnings)
    if height is None:
        warnings.append("Chưa có chiều cao tầng (nhập tay, cao độ sàn trên bản vẽ hay thông số dự án): "
                        "chưa tính diện tích tường.")
    elif height_note:
        warnings.append(height_note)

    wall_layers, scores, auto = choose_wall_layers(drawing)
    if not wall_layers:
        warnings.append("Không tìm thấy layer tường theo mẫu tên hay theo hình học; cần người dùng chọn layer tường.")
    elif auto:
        warnings.append("Tự nhận layer tường theo cặp nét song song: " + ", ".join(auto) + ". Kiểm tra lại trên trang xem.")
    walls = detect_walls(drawing, wall_layers)
    strip = hatch_strip_walls(drawing, walls, set(wall_layers))
    if strip:
        walls += strip
        warnings.append(f"{len(strip)} đoạn tường nhận theo một nét mặt + hatch (mặt kia không vẽ): độ tin cậy thấp, cần kiểm tra.")
    if not walls:
        warnings.append("Không nhận diện được tường nào.")
    walls = dedupe_walls(walls)
    extend_corners(walls)
    opening_blocks = [b for b in drawing.blocks if _is_opening(b, drawing)]
    walls, gap_openings, used_blocks = bridge_openings(walls, drawing, wall_layers, opening_blocks, openings)
    # nối khe xong có thể sinh đoạn đè lên nhau: gộp lại, lỗ mở đi theo đoạn được giữ
    before = {id(w): w.wall_id for w in walls}
    walls_after = dedupe_walls([w for w in walls])
    survivors = {id(w) for w in walls_after}
    for w in walls:
        if id(w) not in survivors:
            mx, my = (w.x1 + w.x2) / 2, (w.y1 + w.y2) / 2
            host = min(walls_after, key=lambda k: _dist_point_segment(mx, my, k))
            for o in gap_openings:
                if o.wall_id == before[id(w)]:
                    o.wall_id = before[id(host)]
    walls = walls_after
    # đổi mã một lần theo bảng cũ -> mới: đổi tuần tự từng tường làm tráo mã (W2 -> W1 rồi W1 -> W2)
    renamed = {}
    for k, w in enumerate(walls, start=1):
        renamed[before.get(id(w), w.wall_id)] = w.wall_id = f"W{k}"
    for o in gap_openings:
        o.wall_id = renamed.get(o.wall_id, o.wall_id)
    roles = mark_envelope(walls)
    rule_hits, unmatched, material_notes = apply_material_rules(drawing, walls, catalog)
    warnings += material_notes
    concrete = [w for w in walls if not w.is_masonry]
    if concrete:
        warnings.append(f"{len(concrete)} đoạn được quy tắc xác định là bê tông (cột hoặc vách), không tính vào khối xây.")
    no_material = sum(w.length_mm for w in walls if w.is_masonry and w.material_family is None)
    if walls and no_material > 0:
        warnings.append(f"{no_material / 1000:.1f} m tường chưa xác định được vật liệu theo thiết kế.")

    opening_items: list[OpeningItem] = []
    wall_by_id = {w.wall_id: w for w in walls}
    no_size: list[str] = []
    for o in gap_openings:
        name = "Cửa đi" if o.kind == "door" else "Cửa sổ"
        # thiếu chiều cao: vẫn giữ trong danh sách (đã biết rộng, tường) để trang kiểm tra nhập cao; chưa trừ
        if o.height_mm is None:
            no_size.append(f"{name} ({o.evidence})")
        else:
            wall_by_id[o.wall_id].opening_area_m2 += o.width_mm * min(o.height_mm, height or o.height_mm) / 1e6
        opening_items.append(OpeningItem(name=name, x=o.x, y=o.y,
                                         width_mm=round(o.width_mm), height_mm=o.height_mm, wall_id=o.wall_id,
                                         kind=o.kind, evidence=o.evidence))
    if any(o.height_mm is not None and not o.evidence.startswith("block") for o in gap_openings):
        warnings.append("Cửa nhận từ khe tường (cung cánh cửa, nét kính): rộng lấy theo khe, cao theo thông số cửa của dự án.")
    merged: list[str] = []
    for block in [b for b in opening_blocks if b not in used_blocks]:
        size = _opening_size_mm(block, openings, drawing.arcs)
        if size is None:
            no_size.append(block.name)
        # thiếu kích thước: vẫn giữ trong danh sách, gắn tường gần nhất để trang kiểm tra nhập rộng × cao; chưa trừ
        width, h = size or (None, None)
        item = OpeningItem(name=block.name, x=block.x, y=block.y, width_mm=width, height_mm=h,
                           kind="block", evidence=f"block {block.name}")
        nearest = min(walls, key=lambda w: _dist_point_segment(block.x, block.y, w)) if walls else None
        if nearest is None or _dist_point_segment(block.x, block.y, nearest) > 600:
            warnings.append(f"Lỗ mở {block.name} không nằm gần tường nào, chưa được trừ.")
            opening_items.append(item)          # wall_id trống: chưa trừ, để người dùng gắn trên trang kiểm tra
            continue
        # cùng tường chủ và khoảng cửa dọc trục chồng lên lỗ đã trừ (khe cửa, block khác tên hay chép đè) là một cửa:
        # ghi thêm nguồn, không trừ lần hai.
        # shortcut: coi điểm chèn block là tâm cửa; block chèn ở mép cửa có thể lệch nửa bề rộng, đọc bảng thống kê cửa (QU-15) thì bỏ
        p = _project(nearest, block.x, block.y)[0]
        same = next((o for o in opening_items if o.wall_id == nearest.wall_id
                     and min(p + (width or 0) / 2, _project(nearest, o.x, o.y)[0] + (o.width_mm or 0) / 2)
                     - max(p - (width or 0) / 2, _project(nearest, o.x, o.y)[0] - (o.width_mm or 0) / 2) > 50), None)
        if same is not None:
            same.evidence += f" + block {block.name}"
            merged.append(block.name)
            continue
        opening_items.append(item)
        if size is not None:
            nearest.opening_area_m2 += width * min(h, height or h) / 1e6
        item.wall_id = nearest.wall_id
    if merged:
        warnings.append(f"{len(merged)} block cửa trùng chỗ với lỗ mở đã trừ trên cùng tường, chỉ trừ một lần: "
                        + ", ".join(merged) + ".")
    if no_size:
        warnings.append(f"{len(no_size)} lỗ mở chưa có kích thước (block không ghi, dự án chưa nhập kích thước cửa), "
                        "chưa được trừ; vẫn có trong danh sách lỗ mở để nhập kích thước: " + ", ".join(no_size) + ".")

    nets = net_lengths([(w.wall_id, w.x1, w.y1, w.x2, w.y2, w.thickness_mm or float(w.thickness_class)) for w in walls])
    for w in walls:
        w.net_length_mm = round(nets[w.wall_id], 1)
    rule_len = (lambda w: w.net_length_mm) if length_rule == "thong_thuy" else (lambda w: w.length_mm)
    if height:
        for w in walls:
            gross_w = rule_len(w) * height / 1e6
            if w.opening_area_m2 > gross_w + 1e-6:
                warnings.append(f"Tường {w.wall_id}: lỗ mở {w.opening_area_m2:.2f} m² lớn hơn diện tích tường {gross_w:.2f} m², "
                                "chỉ trừ bằng diện tích tường. Kiểm tra cửa gắn nhầm tường hoặc cửa trùng.")
                w.opening_area_m2 = gross_w

    groups: list[WallGroup] = []
    masonry = [w for w in walls if w.is_masonry] if height else []
    # mỗi phương án tường một nhóm: bảng vật liệu áp đúng định mức của từng phương án, không gộp hai vật liệu khác nhau
    kind = lambda w: w.wall_system_id or w.material_id or w.material_family or ""  # noqa: E731
    for cls, role, k in sorted({(w.thickness_class, roles[w.wall_id], kind(w)) for w in masonry}):
        members = [w for w in masonry if w.thickness_class == cls and roles[w.wall_id] == role and kind(w) == k]
        length_m = sum(rule_len(w) for w in members) / 1000.0
        by_material: dict[str, float] = {}
        by_system: dict[str, float] = {}
        for w in members:
            key = w.material_id or w.material_family
            if key:
                by_material[key] = by_material.get(key, 0.0) + rule_len(w)
            if w.wall_system_id:
                by_system[w.wall_system_id] = by_system.get(w.wall_system_id, 0.0) + rule_len(w)
        design = max(by_material, key=by_material.get) if by_material else None
        system = max(by_system, key=by_system.get) if by_system else None
        gross = length_m * height / 1000.0
        opening = sum(w.opening_area_m2 for w in members)
        groups.append(WallGroup(
            wall_type=cls, role=role,
            length_m=round(length_m, 2), gross_area_m2=round(gross, 2),
            opening_area_m2=round(opening, 2), net_area_m2=round(max(0.0, gross - opening), 2),
            min_confidence=min(w.confidence for w in members),
            design_material_id=design, design_wall_system_id=system,
            design_material_share=round(by_material[design] / (length_m * 1000.0), 3) if design and length_m else 0.0,
        ))
    for w in walls:
        w.role = roles[w.wall_id]
    return TakeoffResult(floor_height_mm=height, length_rule=length_rule, walls=walls, groups=groups,
                         openings_count=sum(1 for o in opening_items if o.wall_id and o.height_mm is not None), openings=opening_items, warnings=warnings,
                         layer_classes={name: c.value for name, c in drawing.layer_classes.items()},
                         rule_hits=rule_hits, unmatched=unmatched, wall_layers=sorted(wall_layers),
                         auto_wall_layers=auto, wall_layer_scores=scores,
                         rejected=[{"reason": r, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "cls": c}
                                   for r, x1, y1, x2, y2, c in getattr(drawing, "rejected_pairs", [])])


def takeoff_from_file(path: str, floor_height_mm: float | None = None,
                      layer_overrides: dict[str, str] | None = None,
                      openings: OpeningDefaults | None = None, length_rule: str = "tim") -> TakeoffResult:
    """Nhận .dxf hoặc .dwg. layer_overrides: {tên layer: "WALL" | "OPENING" | "ANNOTATION" | "IGNORE"}."""
    return compute_takeoff(read_drawing(path, layer_overrides), floor_height_mm, openings=openings, length_rule=length_rule)


def takeoff_plans(drawing: Drawing, floor_height_mm: float | None = None,
                  catalog: "Catalog | None" = None, openings: OpeningDefaults | None = None,
                  length_rule: str = "tim") -> list[PlanTakeoff]:
    """Đo bóc từng mặt bằng tầng trong file. Không tìm thấy tiêu đề mặt bằng thì đo cả bản vẽ như một mặt bằng."""
    plans = find_plans(drawing)
    if not plans and (has_only_other_plans(drawing) or has_only_views(drawing)):
        return []          # chỉ có mặt bằng kết cấu, móng, điện nước, hoặc mặt cắt, mặt đứng, chi tiết: không đo tường ở đây
    if not plans:
        xs = [c for s in drawing.segments for c in (s.x1, s.x2)] or [0.0]
        ys = [c for s in drawing.segments for c in (s.y1, s.y2)] or [0.0]
        result = compute_takeoff(drawing, floor_height_mm, catalog, openings=openings, length_rule=length_rule)
        return [PlanTakeoff(name="Toàn bộ bản vẽ", height_mm=result.floor_height_mm,
                            height_source="nhập tay" if floor_height_mm else "chưa có",
                            bbox=[min(xs), min(ys), max(xs), max(ys)], result=result)]
    heights = floor_heights(plans, level_chain(drawing))
    out = []
    for i, p in enumerate(plans):
        if floor_height_mm:
            h, src, note = floor_height_mm, "nhập tay", None
        elif i in heights:
            h, src = heights[i], "cao độ tầng trên"
            note = f"Chiều cao tầng {h:.0f} mm suy từ cao độ sàn trên bản vẽ ({p.level_source})."
        else:
            h, src, note = None, "chưa có", None
        sub = crop(drawing, p.bbox)
        result = compute_takeoff(sub, h, catalog, note, openings, length_rule)
        if p.title:
            result.warnings.insert(0, f"QU-05: bản vẽ có hai mặt bằng cùng tiêu đề \"{p.title}\"; mặt bằng này đổi tên thành "
                                      f"\"{p.name}\" để không ghi đè mặt bằng kia. Nên sửa tiêu đề trên bản vẽ.")
        out.append(PlanTakeoff(name=p.name, level_m=p.level_m, height_mm=result.floor_height_mm, height_source=src,
                               bbox=[round(v, 1) for v in p.bbox], result=result))
    return out


def takeoff_plans_from_file(path: str, floor_height_mm: float | None = None,
                            layer_overrides: dict[str, str] | None = None,
                            openings: OpeningDefaults | None = None, length_rule: str = "tim") -> list[PlanTakeoff]:
    return takeoff_plans(read_drawing(path, layer_overrides), floor_height_mm, openings=openings, length_rule=length_rule)


def _floor_key(name: str):
    """Mặt bằng cùng một tầng: theo thứ tự tầng nếu đọc được, không thì theo tiêu đề bỏ hậu tố " (2)"."""
    order = floor_order(name)
    return order if order is not None else normalize(name.rsplit(" (", 1)[0])


def merge_plans(plans: list[PlanTakeoff], floor_height_mm: float | None = None, length_rule: str = "tim") -> TakeoffResult:
    """Gộp các mặt bằng thành một kết quả cả nhà: nhóm tường giữ riêng từng tầng, cảnh báo ghi tên mặt bằng.
    Một tầng vẽ nhiều hình (mặt bằng kích thước, kí hiệu cửa, vật dụng, bản chép) chỉ tính một lần: giữ hình nhiều tường nhất."""
    warnings: list[str] = []
    kept: dict = {}
    for p in plans:
        key, area = _floor_key(p.name), sum(g.net_area_m2 for g in p.result.groups)
        if key in kept:
            old = kept[key]
            keep, drop = (p, old) if area > sum(g.net_area_m2 for g in old.result.groups) else (old, p)
            kept[key] = keep
            warnings.append(f"\"{drop.name}\" cùng tầng với \"{keep.name}\": chỉ tính \"{keep.name}\" (nhiều tường hơn).")
        else:
            kept[key] = p
    plans = list(kept.values())
    if not plans:
        return TakeoffResult(floor_height_mm=floor_height_mm, length_rule=length_rule, walls=[], groups=[], openings_count=0,
                             warnings=["Không tìm thấy mặt bằng kiến trúc trong file (chỉ có mặt cắt, mặt đứng, kết cấu...)."])
    rs = [p.result for p in plans]
    return TakeoffResult(floor_height_mm=floor_height_mm, length_rule=length_rule,
                         walls=[w for r in rs for w in r.walls], groups=[g for r in rs for g in r.groups],
                         openings_count=sum(r.openings_count for r in rs), openings=[o for r in rs for o in r.openings],
                         warnings=warnings + [f"{p.name}: {w}" for p in plans for w in p.result.warnings])


def takeoff_building_from_file(path: str, floor_height_mm: float | None = None,
                               layer_overrides: dict[str, str] | None = None) -> TakeoffResult:
    """Đo bóc cả nhà theo từng mặt bằng tầng; đo cả file như một mặt bằng sẽ cộng cả mặt đứng, mặt cắt, chi tiết."""
    drawing = read_drawing(path, layer_overrides)
    plans = takeoff_plans(drawing, floor_height_mm)
    views = sum(1 for t in drawing.texts if any(w in normalize(t.text) for w in HEADING_WORDS))
    if len(plans) == 1 and plans[0].name == "Toàn bộ bản vẽ" and views >= 2:
        # file nhiều hình (điện, nước, mặt cắt...) mà không tách được mặt bằng kiến trúc: đo cả file sẽ ra số sai
        r = merge_plans([], floor_height_mm)
        r.warnings = [f"File có {views} tiêu đề hình (mặt bằng điện nước, mặt cắt...) nhưng không tách được mặt bằng kiến "
                      "trúc nào; không đo cả bản vẽ để tránh cộng nhầm. Kiểm tra tiêu đề \"MẶT BẰNG TẦNG ...\" trên bản vẽ."]
        return r
    return merge_plans(plans, floor_height_mm)
