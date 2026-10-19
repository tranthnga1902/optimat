"""Agent gọi công cụ: mô hình của OpenAI quyết định gọi công cụ nào và theo thứ tự nào.

Mô hình chỉ điều hướng và diễn đạt. Khối lượng, giá, phương án và liên kết do các công cụ tất định tính ra;
câu trả lời cuối có con số không nằm trong kết quả công cụ thì bị thay bằng bản dữ kiện nguyên gốc.
Không gọi được mô hình thì chạy luồng cố định trong pipeline.py, nên hệ thống vẫn dùng được khi mất mạng.
"""
from __future__ import annotations

import json
from typing import Callable

from .. import config
from ..catalog.pricing import bill_of_materials
from ..catalog.repository import Catalog
from ..drawing.takeoff import takeoff_from_file
from ..optimize.problem import optimize
from ..predict.cost_model import MaterialPriceModel
from ..schemas import Constraints
from .llm import FAMILIES, LLMUnavailable, chat_openai, unsupported_numbers
from ..rough.models import ProjectParams
from .pipeline import describe, describe_bill, describe_rough, run_pipeline

SYSTEM = (
    "Bạn là OptiMat AI, trợ lý chọn vật liệu xây tường cho nhà ở riêng lẻ. Bạn KHÔNG tự tính và KHÔNG tự nêu giá, "
    "khối lượng, nhà cung cấp hay liên kết: mọi số liệu phải lấy từ kết quả công cụ và chép nguyên văn. "
    "Quy trình thường dùng: do_boc_ban_ve trước, tra_gia_theo_thiet_ke khi người dùng hỏi giá vật liệu theo bản vẽ, "
    "rồi toi_uu_vat_lieu với ràng buộc người dùng nêu. Hỏi khối lượng phần thô (bê tông, thép, cốp pha, trát, cán nền...) "
    "thì gọi boc_phan_tho; thông số nào người dùng không nêu thì để trống, không tự điền. "
    "Thiếu thông tin thì dùng mặc định và nói rõ. Từ chối yêu cầu về chịu lực, kết cấu, hoặc ngoài phạm vi nhà ở riêng lẻ. "
    "Trả lời bằng tiếng Việt, ngắn gọn."
)
TOOLS = [
    {"type": "function", "function": {
        "name": "do_boc_ban_ve", "description": "Đọc bản vẽ đã tải lên, nhận diện tường và đo bóc diện tích từng nhóm tường.",
        "parameters": {"type": "object", "properties": {
            "floor_height_mm": {"type": "number", "description": "Chiều cao tầng, mm. Bỏ trống để dùng mặc định."}}}}},
    {"type": "function", "function": {
        "name": "tra_gia_theo_thiet_ke", "description": "Lập bảng vật liệu theo thiết kế (mã danh mục, khối lượng gạch và vữa) "
        "kèm giá đang có trong cơ sở dữ liệu. Phải đo bóc trước.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "boc_phan_tho", "description": "Bóc khối lượng phần thô của mọi mặt bằng (xây, trát, lanh tô, cột, dầm, sàn, "
        "cầu thang, cán nền, chống thấm, nền, cốt thép, cốp pha) và vật liệu mua về. Thông số không nêu thì để trống.",
        "parameters": {"type": "object", "properties": {
            "concrete_supply": {"type": "string", "enum": ["ready_mix", "site_mix"],
                                "description": "Bê tông thương phẩm (ready_mix) hay trộn tại chỗ (site_mix)"},
            "concrete_grade": {"type": "string", "description": "Mác bê tông, ví dụ M250"},
            "slab_thickness_mm": {"type": "number", "description": "Dày sàn, mm"},
            "beam_depth_mm": {"type": "number", "description": "Cao dầm, mm"},
            "beam_width_mm": {"type": "number", "description": "Rộng dầm, mm"},
            "plaster_thickness_mm": {"type": "number", "description": "Dày trát, mm"},
            "screed_thickness_mm": {"type": "number", "description": "Dày cán nền, mm"}}}}},
    {"type": "function", "function": {
        "name": "toi_uu_vat_lieu", "description": "Tối ưu vật liệu tường theo chi phí, thời gian cung ứng, hệ số truyền nhiệt. Phải đo bóc trước.",
        "parameters": {"type": "object", "properties": {
            "budget": {"type": "number", "description": "Ngân sách, đồng"},
            "deadline_days": {"type": "number", "description": "Số ngày tối đa để có vật liệu"},
            "max_vehicle_ton": {"type": "number", "description": "Tải trọng xe lớn nhất vào được, tấn"},
            "excluded_materials": {"type": "array", "items": {"type": "string", "enum": list(FAMILIES)},
                                   "description": "Họ vật liệu bị loại. Gạch nung: CLAY_SOLID, CLAY_HOLLOW; gạch bê tông: CMU_SOLID, CMU_HOLLOW."}}}}},
]


class AgentSession:
    """Giữ trạng thái của một lần chạy và thực thi công cụ."""

    def __init__(self, drawing_path: str, floor_height_mm: float | None = None, layer_overrides: dict | None = None,
                 rough_params: ProjectParams | None = None):
        self.drawing_path, self.floor_height_mm, self.layer_overrides = drawing_path, floor_height_mm, layer_overrides
        self.rough_params = rough_params or ProjectParams()
        self.rough = None
        self.takeoff = None
        self.result = None
        self.bill = None
        self.constraints = Constraints()
        self.facts: list[str] = []
        self.trace: list[dict] = []

    def call(self, name: str, args: dict) -> str:
        try:
            out = getattr(self, f"tool_{name}")(**args)
        except AttributeError:
            out = f"Không có công cụ {name}."
        except Exception as exc:                                   # lỗi công cụ được trả cho mô hình, không làm sập lần chạy
            out = f"Lỗi khi chạy {name}: {exc}"
        self.trace.append({"tool": name, "args": args, "result": out})
        self.facts.append(out)
        return out

    def tool_do_boc_ban_ve(self, floor_height_mm: float | None = None) -> str:
        self.takeoff = takeoff_from_file(self.drawing_path, floor_height_mm or self.floor_height_mm, self.layer_overrides)
        if not self.takeoff.groups:
            return "Chưa nhận diện được tường. " + " ".join(self.takeoff.warnings)
        lines = [f"Tường {g.wall_type} ({g.role}): dài {g.length_m:.2f} m, diện tích thực {g.net_area_m2:.2f} m2, "
                 f"vật liệu theo thiết kế: {g.design_material_id or 'chưa xác định'}." for g in self.takeoff.groups]
        return "\n".join(lines + [f"Cảnh báo: {w}" for w in self.takeoff.warnings])

    def tool_tra_gia_theo_thiet_ke(self) -> str:
        if self.takeoff is None:
            return "Chưa đo bóc bản vẽ. Hãy gọi do_boc_ban_ve trước."
        self.bill = bill_of_materials(self.takeoff.groups, Catalog.load())
        return "Vật liệu theo thiết kế:\n" + describe_bill(self.bill) if self.bill else "Chưa có nhóm tường nào."

    def tool_boc_phan_tho(self, **kwargs) -> str:
        from ..drawing.dxf_reader import read_drawing
        from ..rough.takeoff import compute_rough, rough_from_drawing
        params = self.rough_params.model_copy(update={k: v for k, v in kwargs.items() if v not in (None, "")})
        catalog = Catalog.load()
        req = rough_from_drawing(read_drawing(self.drawing_path, self.layer_overrides), params, self.floor_height_mm, catalog)
        self.rough = compute_rough(req, catalog)
        return describe_rough(self.rough) + "\n" + "\n".join(f"Cảnh báo: {w}" for w in self.rough.warnings[:10])

    def tool_toi_uu_vat_lieu(self, **kwargs) -> str:
        if self.takeoff is None:
            return "Chưa đo bóc bản vẽ. Hãy gọi do_boc_ban_ve trước."
        self.constraints = self.constraints.model_copy(update={k: v for k, v in kwargs.items() if v not in (None, [])})
        self.result = optimize(self.takeoff.groups, self.constraints, Catalog.load(), MaterialPriceModel.load())
        sols = self.result.solutions
        if not sols:
            return "Không có phương án nào thỏa các ràng buộc hiện tại."
        picks = {"Chi phí thấp nhất": sols[0],
                 "Cung ứng nhanh nhất": min(sols, key=lambda s: (s.supply_days, s.total_cost)),
                 "Cách nhiệt tốt nhất": min(sols, key=lambda s: (s.u_value, s.total_cost))}
        seen, lines = set(), [f"Có {len(sols)} phương án không bị trội."]
        for label, sol in picks.items():
            key = tuple((c.material_id, c.supplier_id, c.vehicle_id) for c in sol.choices)
            if key not in seen:
                seen.add(key)
                lines.append(describe(sol, label))
        return "\n".join(lines)


def run_agent(drawing_path: str, message: str, floor_height_mm: float | None = None, layer_overrides: dict | None = None,
              chat: Callable[..., dict] = chat_openai, rough_params: ProjectParams | None = None) -> dict:
    """Chạy agent gọi công cụ. `chat` thay được bằng hàm giả khi kiểm thử. rough_params: thông số công trình đã nhập."""
    session = AgentSession(drawing_path, floor_height_mm, layer_overrides, rough_params)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": message}]
    try:
        for _ in range(config.AGENT_MAX_TURNS):
            reply = chat(messages, tools=TOOLS)
            messages.append(reply)
            calls = reply.get("tool_calls") or []
            if not calls:
                answer, facts = (reply.get("content") or "").strip(), "\n".join(session.facts)
                guarded = bool(unsupported_numbers(answer, facts + "\n" + message))
                return {"mode": "agent", "answer": facts if guarded or not answer else answer, "guarded": guarded,
                        "trace": session.trace, "takeoff": session.takeoff, "result": session.result, "bill": session.bill,
                        "constraints": session.constraints, "rough": session.rough}
            for call in calls:
                try:
                    args = json.loads(call["function"].get("arguments") or "{}")
                except ValueError:
                    args = {}
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": session.call(call["function"]["name"], args)})
    except LLMUnavailable as exc:
        reason = str(exc)
    else:
        reason = f"Mô hình không kết thúc sau {config.AGENT_MAX_TURNS} lượt."
    state = run_pipeline(drawing_path, message=message, floor_height_mm=floor_height_mm, layer_overrides=layer_overrides,
                         use_llm=False, rough_params=rough_params)
    return {"mode": "fallback", "reason": reason, "answer": state["explanation"], "guarded": False, "trace": session.trace,
            "takeoff": state["takeoff"], "result": state["result"], "constraints": state["constraints"], "bill": state["bill"],
            "rough": state.get("rough")}
