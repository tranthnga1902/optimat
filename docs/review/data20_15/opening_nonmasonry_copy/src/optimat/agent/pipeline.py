"""Luồng điều phối của agent: đo bóc -> kiểm tra -> tối ưu -> giải thích.

Thứ tự các bước được cố định bằng mã, mô hình ngôn ngữ không được bỏ bước.
Mỗi bước là một hàm nhận và trả về trạng thái, nên chuyển sang LangGraph về sau
chỉ là khai báo các hàm này thành nút của đồ thị.
Mọi con số và liên kết trong lời giải thích lấy từ kết quả tính toán, không do LLM sinh ra.
"""
from __future__ import annotations

from ..catalog.pricing import BillLine, bill_of_materials
from ..catalog.repository import Catalog
from ..drawing.takeoff import takeoff_building_from_file
from ..optimize.problem import optimize
from ..predict.cost_model import MaterialPriceModel
from ..rough.models import ProjectParams
from ..schemas import Constraints, OptimizeResult, Solution, TakeoffResult
from .llm import parse_constraints, write_explanation

LOW_CONFIDENCE = 0.7


def step_takeoff(state: dict) -> dict:
    state["takeoff"] = takeoff_building_from_file(state["drawing_path"], state.get("floor_height_mm"), state.get("layer_overrides"))
    return state


def step_check(state: dict) -> dict:
    takeoff: TakeoffResult = state["takeoff"]
    questions = [f"Tường {w.wall_id} (dài {w.length_mm / 1000:.1f} m) có độ tin cậy {w.confidence:.0%}, cần xác nhận."
                 for w in takeoff.walls if w.confidence < LOW_CONFIDENCE]
    if not takeoff.groups:
        questions.append("Chưa nhận diện được tường. Hãy chọn layer tường hoặc kiểm tra bản vẽ.")
    state["questions"] = questions
    return state


def step_constraints(state: dict) -> dict:
    cons: Constraints = state.get("constraints") or Constraints()
    if state.get("message"):
        parsed = parse_constraints(state["message"], use_llm=state.get("use_llm", True))
        updates = {k: v for k, v in parsed.model_dump(exclude={"source"}).items() if v not in (None, [])}
        cons = cons.model_copy(update=updates)
        state["constraint_source"] = parsed.source
    state["constraints"] = cons
    return state


def step_bill(state: dict) -> dict:
    """Vật liệu theo thiết kế đọc từ bản vẽ, quy về mã danh mục, kèm giá đang có (trước khi tối ưu)."""
    state["catalog"] = state.get("catalog") or Catalog.load()
    state["bill"] = bill_of_materials(state["takeoff"].groups, state["catalog"])
    return state


def step_rough(state: dict) -> dict:
    """Bóc phần thô (xây, trát, bê tông, thép, cốp pha... và vật liệu mua về), có bản vẽ kết cấu thì đọc thêm móng, dầm.
    Không gửi thông số công trình thì vẫn bóc: phần cần thông số (mác bê tông, dày sàn...) để trống kèm cảnh báo (B7)."""
    params: ProjectParams = state.get("rough_params") or ProjectParams()
    from ..drawing.dxf_reader import read_drawing
    from ..rough.takeoff import compute_rough, rough_from_drawing
    catalog = state.get("catalog") or Catalog.load()
    structural = [read_drawing(p) for p in state.get("structural_paths") or []] or None
    req = rough_from_drawing(read_drawing(state["drawing_path"], state.get("layer_overrides")), params,
                             state.get("floor_height_mm"), catalog, structural=structural)
    state["rough"] = compute_rough(req, catalog)
    return state


def describe_rough(rough) -> str:
    """Tổng khối lượng từng công tác và vật liệu mua về; phần chưa tính được ghi rõ."""
    lines = ["Phần thô (khối lượng công tác):"]
    for t in rough.totals:
        q = f"{t.quantity:.2f} {t.unit}" if t.quantity is not None else "chưa tính được"
        lines.append(f"  {t.name}: {q}{'' if t.complete else ' (còn phần thiếu thông số)'}")
    lines.append("Vật liệu mua về:")
    for m in rough.materials:
        q = f"{m.quantity:.2f} {m.unit}" if m.quantity is not None else "chưa tính được"
        miss = f" (thiếu: {', '.join(m.missing[:3])})" if not m.complete and m.missing else ""
        lines.append(f"  {m.material_id or '-'} {m.name}: {q}{miss}")
    return "\n".join(lines)


def step_optimize(state: dict) -> dict:
    try:
        state["result"] = optimize(state["takeoff"].groups, state["constraints"], state.get("catalog") or Catalog.load(),
                                   MaterialPriceModel.load())
    except ValueError as exc:                      # thiếu số liệu danh mục hoặc giá: báo lại, không làm sập luồng
        state["result"] = OptimizeResult(solutions=[], n_evaluated=0, notes=[str(exc)])
    return state


def describe_bill(bill: list[BillLine]) -> str:
    """Một dòng cho mỗi vật liệu theo thiết kế; thiếu số liệu thì ghi rõ thiếu gì."""
    lines = []
    for b in bill:
        name = f"{'vữa ' if b.kind == 'mortar' else ''}{b.material_id or 'chưa xác định'}"
        qty = f"{b.quantity:.2f} {b.unit}" if b.quantity is not None else "chưa tính được khối lượng"
        price = f", giá thấp nhất {b.best_price:,.0f} đồng/{b.unit}" if b.best_price is not None else ", chưa có giá"
        miss = f" (thiếu: {', '.join(b.missing)})" if b.missing else ""
        lines.append(f"  Tường {b.wall_type} theo thiết kế {b.wall_system_id or ''}: {name} {qty}{price}{miss}")
    return "\n".join(lines)


def describe(sol: Solution, label: str) -> str:
    parts = [f"{label}: tổng {sol.total_cost / 1e6:.1f} triệu đồng, cung ứng {sol.supply_days:.0f} ngày, "
             f"hệ số truyền nhiệt {sol.u_value:.2f} W/m²K."]
    for c in sol.choices:
        parts.append(f"  Tường {c.wall_type}: {c.material_name} ({c.wall_system_id}), mua tại {c.supplier_name} cách {c.distance_km} km, "
                     f"{c.trips} chuyến {c.vehicle_id}. Nguồn giá: {c.product_url}")
    return "\n".join(parts)


def step_explain(state: dict) -> dict:
    result: OptimizeResult = state["result"]
    design = ("Vật liệu theo thiết kế:\n" + describe_bill(state["bill"])) if state.get("bill") else ""
    if state.get("rough") is not None:
        design = "\n".join(x for x in (design, describe_rough(state["rough"])) if x)
    if not result.solutions:
        state["facts"] = "\n".join(x for x in [design] + result.notes if x)
        state["explanation"] = "Không có phương án nào thỏa các ràng buộc hiện tại." + \
            ("\n" + "\n".join(result.notes) if result.notes else "") + ("\n" + design if design else "")
        return state
    sols = result.solutions
    picks = [("Chi phí thấp nhất", sols[0]),
             ("Cung ứng nhanh nhất", min(sols, key=lambda s: (s.supply_days, s.total_cost))),
             ("Cách nhiệt tốt nhất", min(sols, key=lambda s: (s.u_value, s.total_cost)))]
    seen, lines = set(), []
    for label, sol in picks:
        key = tuple((c.material_id, c.supplier_id, c.vehicle_id) for c in sol.choices)
        if key not in seen:
            seen.add(key)
            lines.append(describe(sol, label))
    state["facts"] = "\n".join(([design] if design else []) + lines)
    state["explanation"], state["explanation_source"] = write_explanation(state["facts"], use_llm=state.get("use_llm", True))
    return state


STEPS = [step_takeoff, step_check, step_bill, step_rough, step_constraints, step_optimize, step_explain]


def run_pipeline(drawing_path: str, message: str | None = None, constraints: Constraints | None = None,
                 floor_height_mm: float | None = None, layer_overrides: dict[str, str] | None = None,
                 use_llm: bool = True, catalog: Catalog | None = None, rough_params: ProjectParams | None = None,
                 structural_paths: list[str] | None = None) -> dict:
    """drawing_path: bản vẽ kiến trúc .dxf/.dwg. rough_params: thông số công trình (trống được).
    structural_paths: bản vẽ kết cấu tách file (móng, dầm, cột)."""
    state = {"drawing_path": drawing_path, "message": message, "constraints": constraints,
             "floor_height_mm": floor_height_mm, "layer_overrides": layer_overrides, "use_llm": use_llm,
             "catalog": catalog, "rough_params": rough_params, "structural_paths": structural_paths}
    for step in STEPS:
        state = step(state)
    return state
