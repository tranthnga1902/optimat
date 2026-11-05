"""Các kiểu dữ liệu trao đổi giữa module, API và agent."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class WallSegment(BaseModel):
    wall_id: str
    layer: str
    thickness_class: str            # "110" | "150" | "220" | "330"
    thickness_mm: Optional[float] = None   # khoảng cách đo được giữa hai nét
    length_mm: float                # theo trục tim
    net_length_mm: Optional[float] = None   # thông thủy giữa các mặt tường giao (walls.net_lengths)
    x1: float
    y1: float
    x2: float
    y2: float
    opening_area_m2: float = 0.0
    confidence: float = 1.0
    # vật liệu theo thiết kế, suy ra từ bộ quy tắc (data/rules/material_rules.csv) rồi quy về mã của danh mục
    material_family: Optional[str] = None       # họ vật liệu của danh mục, ví dụ CLAY_SOLID (nhiều họ: CLAY_SOLID|CLAY_HOLLOW)
    material_id: Optional[str] = None           # mã vật liệu trong bảng materials, ví dụ GN01: dùng để tra giá
    wall_system_id: Optional[str] = None        # phương án tường trong bảng wall_systems, ví dụ W-GN01-220
    material_candidates: list[str] = Field(default_factory=list)   # phương án còn phải chọn khi danh mục có nhiều
    material_source: str = "none"               # text | hatch | hatch_doan (hatch bị phá, dựng lại) | layer | none
    material_rule: Optional[str] = None         # mã quy tắc đã khớp
    material_confidence: float = 0.0
    is_masonry: bool = True                     # False: quy tắc xác định là bê tông, không tính vào khối xây
    role: Optional[str] = None                  # envelope (bao che) | partition (ngăn), xác định bằng hình học


class WallGroup(BaseModel):
    wall_type: str                  # lớp chiều dày
    role: str                       # "envelope" (bao che) | "partition" (ngăn)
    length_m: float                 # theo quy tắc chiều dài đã chọn (TakeoffResult.length_rule)
    gross_area_m2: float
    opening_area_m2: float
    net_area_m2: float
    min_confidence: float
    design_material_id: Optional[str] = None    # vật liệu theo thiết kế của nhóm (theo chiều dài lớn nhất)
    design_wall_system_id: Optional[str] = None # phương án tường theo thiết kế của nhóm
    design_material_share: float = 0.0          # phần chiều dài nhóm đã xác định được vật liệu đó


class OpeningItem(BaseModel):
    """Một lỗ mở (block cửa) và tường chứa nó; wall_id hoặc height_mm trống là chưa trừ."""
    name: str
    x: float
    y: float
    width_mm: float
    height_mm: Optional[float] = None      # None: dự án chưa nhập chiều cao cửa (Quy ước B7), người dùng nhập trên trang kiểm tra
    wall_id: Optional[str] = None
    kind: str = "block"             # block | door | window
    evidence: str = ""              # dấu hiệu nhận ra: block D1, cung cánh cửa, nét kính


class OpeningDefaults(BaseModel):
    """Kích thước cửa của dự án (bảng projects): dùng khi block cửa không ghi kích thước. Trống thì lỗ mở chưa trừ."""
    door_width_mm: Optional[float] = None
    door_height_mm: Optional[float] = None
    window_width_mm: Optional[float] = None
    window_height_mm: Optional[float] = None


class TakeoffResult(BaseModel):
    floor_height_mm: Optional[float] = None     # trống: chưa có chiều cao tầng, chưa tính diện tích
    length_rule: str = "tim"                    # quy tắc chiều dài của groups: tim | thong_thuy
    walls: list[WallSegment]
    groups: list[WallGroup]
    openings_count: int
    openings: list[OpeningItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    layer_classes: dict[str, str] = Field(default_factory=dict)   # vai trò đã gán cho từng layer
    rule_hits: dict[str, int] = Field(default_factory=dict)       # mã quy tắc -> số lần khớp
    unmatched: dict[str, list[str]] = Field(default_factory=dict)  # tín hiệu chưa có quy tắc: hatch, text, block
    wall_layers: list[str] = Field(default_factory=list)           # layer đã dùng làm tường
    auto_wall_layers: list[str] = Field(default_factory=list)      # trong đó, layer tự nhận bằng hình học
    wall_layer_scores: dict[str, float] = Field(default_factory=dict)  # mm cặp nét song song theo layer
    rejected: list[dict] = Field(default_factory=list)              # cặp nét giống tường nhưng bị loại: lý do, tọa độ


class PlanTakeoff(BaseModel):
    """Kết quả đo bóc của một mặt bằng trong file nhiều mặt bằng."""
    name: str
    level_m: Optional[float] = None         # cao độ sàn đọc từ bản vẽ
    height_mm: Optional[float] = None
    height_source: str                      # nhập tay | cao độ tầng trên | chưa có
    bbox: list[float]                       # x0, y0, x1, y1 (mm, tọa độ bản vẽ)
    result: TakeoffResult


class Constraints(BaseModel):
    site_lat: float = 20.9716
    site_lon: float = 105.7725
    budget: Optional[float] = None              # đồng
    deadline_days: Optional[float] = None
    max_vehicle_ton: Optional[float] = None
    excluded_materials: list[str] = Field(default_factory=list)   # họ vật liệu (CLAY_SOLID...) hoặc mã (GN01)
    keep_design_material: bool = False          # True: giữ phương án tường theo thiết kế, chỉ tối ưu nhà cung cấp và xe
    order_date: Optional[str] = None            # YYYY-MM-DD, mặc định hôm nay
    province: Optional[str] = None              # tỉnh để tra đơn giá nhân công (bảng labor_rates)


class GroupChoice(BaseModel):
    wall_type: str
    wall_system_id: Optional[str] = None
    material_id: str
    material_name: str
    supplier_id: str
    supplier_name: str
    vehicle_id: str
    quantity: float
    unit: str
    unit_price: float
    price_source: str                # "model" | "catalog"
    product_url: str
    distance_km: float
    trips: int
    material_cost: float
    transport_cost: float
    install_cost: float


class Solution(BaseModel):
    total_cost: float
    supply_days: float
    u_value: float
    choices: list[GroupChoice]


class OptimizeResult(BaseModel):
    solutions: list[Solution]
    n_evaluated: int
    notes: list[str] = Field(default_factory=list)
