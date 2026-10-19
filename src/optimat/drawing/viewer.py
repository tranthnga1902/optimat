"""Trang xem trực quan quá trình bóc tách một bản vẽ.

    python scripts/view_takeoff.py data/drawings/build/H01_T1.dxf --height 3300

Trang HTML tự chứa (mở bằng trình duyệt, không cần mạng ngoài phông chữ): vẽ lại bản vẽ và cho xem
từng bước của luồng đo bóc thật (cùng mã với API): nét và layer, cặp nét thành tường, trừ lỗ mở,
gán vật liệu, bảng khối lượng. Trang chỉ hiển thị, không tính lại gì.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..catalog.repository import Catalog, default_catalog
from ..schemas import PlanTakeoff, TakeoffResult
from .dxf_reader import Drawing, crop
from .render import DrawingRenderer
from .material_rules import _best, load_rules, rule_label
from ..rough.areas import room_labels
from ..rough.columns import detect_columns

TEMPLATE = Path(__file__).with_name("viewer_template.html")          # trang 5 bước (giải thích thuật toán)
REVIEW_TEMPLATE = Path(__file__).with_name("review_app.html")       # trang Kiểm tra bóc tách (sửa, bổ sung, xác nhận)


def _r(v: float) -> float:
    return round(v, 1)


def viewer_data(drawing: Drawing, result: TakeoffResult, file_name: str, plan: dict | None = None) -> dict:
    """Gom dữ liệu cho trang xem. Tọa độ đổi về gốc góc trên trái, trục y hướng xuống (mm)."""
    xs = [c for s in drawing.segments for c in (s.x1, s.x2)] or [0.0, 1.0]
    ys = [c for s in drawing.segments for c in (s.y1, s.y2)] or [0.0, 1.0]
    x0, y1 = min(xs), max(ys)

    def tx(x: float) -> float:
        return _r(x - x0)

    def ty(y: float) -> float:
        return _r(y1 - y)

    layer_names = sorted({s.layer for s in drawing.segments})
    index = {name: i for i, name in enumerate(layer_names)}
    role_of_class = {g.wall_type: g.role for g in result.groups}
    rules = load_rules()
    hatches = []
    for h in drawing.hatches:
        rule = _best(rules, "hatch", h.pattern)
        hatches.append({
            "pattern": h.pattern, "layer": h.layer,
            "rule": rule.rule_id if rule else None,
            "result": rule_label(rule) if rule else None,
            "concrete": bool(rule and rule.element == "CONCRETE"),
            "polys": [[[tx(x), ty(y)] for x, y in poly] for poly in h.polygons],
        })
    return {
        "file": file_name,
        "height_mm": result.floor_height_mm,
        "size": [_r(max(xs) - x0), _r(y1 - min(ys))],
        "layers": [{"name": n, "role": result.layer_classes.get(n, "UNKNOWN")} for n in layer_names],
        "segs": [[tx(s.x1), ty(s.y1), tx(s.x2), ty(s.y2), index[s.layer], 1 if s.kind == "hatch" else 0]
                 for s in drawing.segments],
        "walls": [{
            "id": w.wall_id, "cls": w.thickness_class, "layer": w.layer,
            "x1": tx(w.x1), "y1": ty(w.y1), "x2": tx(w.x2), "y2": ty(w.y2),
            "len": round(w.length_mm / 1000, 3), "open": round(w.opening_area_m2, 2),
            "conf": w.confidence, "masonry": w.is_masonry, "role": w.role or role_of_class.get(w.thickness_class),
            "mat": w.material_id, "fam": w.material_family, "sys": w.wall_system_id, "cand": w.material_candidates,
            "t": w.thickness_mm, "src": w.material_source,
            "rule": w.material_rule, "mconf": w.material_confidence,
        } for w in result.walls],
        "rejected": [{"reason": r["reason"], "cls": r["cls"], "x1": tx(r["x1"]), "y1": ty(r["y1"]), "x2": tx(r["x2"]),
                      "y2": ty(r["y2"])} for r in result.rejected],
        "openings": [{"name": o.name, "x": tx(o.x), "y": ty(o.y), "w": o.width_mm, "h": o.height_mm,
                      "wall": o.wall_id, "kind": o.kind, "ev": o.evidence} for o in result.openings],
        "hatches": hatches,
        "texts": [{"t": t.text.strip()[:120], "x": tx(t.x), "y": ty(t.y), "enc": t.encoding}
                  for t in drawing.texts if t.text.strip()],
        "arcs": [[tx(a.cx), ty(a.cy), _r(a.r), round(a.start, 1), round(a.end, 1)] for a in drawing.arcs if a.r >= 300],
        "hatchsegs": len([s for s in drawing.segments if s.kind == "hatch"]),
        "plan": plan or {"name": file_name},
        "origin": [_r(x0), _r(y1)], "bbox_mm": [_r(x0), _r(min(ys)), _r(max(xs)), _r(y1)],
        "wall_layers": result.wall_layers, "auto_wall_layers": result.auto_wall_layers,
        "wall_layer_scores": result.wall_layer_scores,
        "groups": [g.model_dump() for g in result.groups],
        "warnings": result.warnings,
        "unmatched": result.unmatched,
        "rule_hits": result.rule_hits,
        # phần thô: cột nhận từ vùng tô đặc và tên phòng (WC, ban công) để tính chống thấm; cùng hệ tọa độ trang
        "columns": [{"id": c.id, "x": tx(c.x), "y": ty(c.y), "b_mm": c.b_mm, "h_mm": c.h_mm} for c in detect_columns(drawing)],
        "labels": [{"kind": k, "text": t, "x": tx(x), "y": ty(y)} for k, t, x, y in room_labels(drawing)],
    }


def plans_data(drawing: Drawing, plans: list[PlanTakeoff], file_name: str) -> dict:
    from ..rough.takeoff import ground_index
    ground = ground_index([p.name for p in plans], [p.level_m for p in plans])
    out = []
    for i, p in enumerate(plans):
        sub = crop(drawing, tuple(p.bbox)) if p.name != "Toàn bộ bản vẽ" else drawing
        info = {"name": p.name, "level_m": p.level_m, "height_mm": p.height_mm, "height_source": p.height_source,
                "is_ground": i == ground}
        out.append(viewer_data(sub, p.result, file_name, info))
    return {"file": file_name, "plans": out}


def material_options(catalog: Catalog | None = None) -> list[dict]:
    """Vật liệu tường người dùng chọn được trên trang: lấy từ danh mục (cùng mã dùng để tra giá).
    systems: lớp chiều dày -> phương án tường; ready: phương án đủ số liệu để tối ưu."""
    catalog = catalog or default_catalog()
    view = catalog.wall_view()
    families = catalog.wall_families()
    mats = catalog.materials[catalog.materials.get("family").isin(list(families))] if "family" in catalog.materials else []
    out = []
    for m in (mats.itertuples() if len(mats) else []):
        rows = view[view.material_id == m.material_id] if len(view) else view
        out.append({
            "id": m.material_id, "name": m.name, "label": f"{m.material_id} · {m.name}", "unit": m.unit,
            "family": m.family, "family_label": families[m.family],
            "systems": {r.detect_class: r.wall_system_id for r in rows.itertuples() if r.detect_class},
            "ready": {r.detect_class: bool(r.ready) for r in rows.itertuples() if r.detect_class},
        })
    order = list(families)
    return sorted(out, key=lambda o: (order.index(o["family"]), o["id"]))


def add_cad_layers(drawing: Drawing, payload: dict, plans: list[PlanTakeoff] | None) -> None:
    """Thêm nền bản vẽ gốc vẽ đúng như phần mềm CAD cho từng mặt bằng ("cad") và trang tổng thể cả file ("overview")."""
    if getattr(drawing, "doc", None) is None:
        return
    try:
        renderer = DrawingRenderer(drawing.doc, drawing.unit_scale)
    except Exception as exc:  # noqa: BLE001 - vẽ nền lỗi không được làm hỏng kết quả nhận dạng
        payload.setdefault("warnings", []).append(f"Không vẽ được nền bản vẽ gốc: {exc}")
        return
    for i, p in enumerate(payload["plans"]):
        box = tuple(plans[i].bbox) if plans and plans[i].name != "Toàn bộ bản vẽ" else None
        p["cad"] = renderer.view(box or tuple(p["bbox_mm"]), tuple(p["origin"])).svg
    xs = [c for s in drawing.segments for c in (s.x1, s.x2)] or [0.0, 1.0]
    ys = [c for s in drawing.segments for c in (s.y1, s.y2)] or [0.0, 1.0]
    ox, oy = min(xs), max(ys)
    boxes = []
    for i, p in enumerate(payload["plans"]):
        bx = plans[i].bbox if plans else p["bbox_mm"]
        boxes.append({"name": p["plan"]["name"], "x": _r(bx[0] - ox), "y": _r(oy - bx[3]),
                      "w": _r(bx[2] - bx[0]), "h": _r(bx[3] - bx[1])})
    payload["overview"] = {"cad": renderer.view(None, (ox, oy)).svg, "size": [_r(max(xs) - ox), _r(oy - min(ys))],
                           "plans": boxes}


def view_payload(drawing: Drawing, result, file_name: str, cad: bool = True) -> dict:
    """result: một TakeoffResult (cả bản vẽ) hoặc danh sách PlanTakeoff (từng mặt bằng).
    cad: thêm nền bản vẽ gốc vẽ như phần mềm CAD (chậm hơn với file lớn)."""
    plans = result if isinstance(result, list) else None
    if plans is not None:
        payload = plans_data(drawing, result, file_name)
    else:
        payload = {"file": file_name, "plans": [viewer_data(drawing, result, file_name)]}
    if cad:
        add_cad_layers(drawing, payload, plans)
    if plans is not None:
        payload["conventions"] = convention_summary(drawing, plans, file_name)
    payload["materials"] = material_options()
    payload["families"] = [{"id": k, "label": v} for k, v in default_catalog().wall_families().items()]
    return payload


def convention_summary(drawing: Drawing, plans: list, file_name: str) -> dict:
    """Đối chiếu Quy ước v1.0 cho tab Cảnh báo: kết luận và từng điều khoản (chi tiết: scripts/concept_report.py).
    Phần này chỉ để báo; lỗi ở đây không được chặn việc mở bản vẽ, nên trả lời báo lỗi thay vì ném ngoại lệ."""
    from .convention_check import analyze_drawing
    try:
        r = analyze_drawing(drawing, plans, file_name)
    except Exception as exc:   # noqa: BLE001
        return {"error": f"Chưa đối chiếu được quy ước: {exc}"}
    return {"trong_quy_uoc": r.trong_quy_uoc,
            "checks": [c.model_dump(include={"ma", "muc", "nhom", "dieu_khoan", "trang_thai", "ket_qua", "bang_chung"})
                       for c in r.checks]}


def _embed(template: Path, payload: dict | None) -> str:
    html = template.read_text(encoding="utf8")
    if payload is None:
        return html
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return html.replace("/*__DATA__*/null", data, 1)


def build_viewer_html(drawing: Drawing, result, file_name: str) -> str:
    """Trang 5 bước, dữ liệu nhúng sẵn."""
    return _embed(TEMPLATE, view_payload(drawing, result, file_name))


def build_review_html(drawing: Drawing | None = None, result=None, file_name: str = "") -> str:
    """Trang Kiểm tra bóc tách. Không truyền bản vẽ: trang rỗng để chạy trong API (tải file lên)."""
    return _embed(REVIEW_TEMPLATE, None if drawing is None else view_payload(drawing, result, file_name))
