"""Kiểu dữ liệu của bóc khối lượng phần thô: thông số công trình, công tác, vật liệu mua về.

Theo Quy ước bản vẽ v1.0 (B1, B3, B7): thông số nào người dùng chưa nhập thì để trống; công tác cần thông số đó
không ra số và có cảnh báo, không điền số mặc định im lặng.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Mã công tác -> (tên, đơn vị). Thứ tự này là thứ tự hiển thị.
WORKS = {
    "XAY": ("Xây tường", "m³"),
    "TRAT": ("Trát tường", "m²"),
    "LANH_TO": ("Bê tông lanh tô", "m³"),
    "COT": ("Bê tông cột", "m³"),
    "DAM": ("Bê tông dầm", "m³"),
    "SAN": ("Bê tông sàn", "m³"),
    "CAU_THANG": ("Bê tông cầu thang", "m³"),
    "MONG": ("Bê tông móng", "m³"),
    "BE_TONG_LOT": ("Bê tông lót", "m³"),
    "NEN_DEM_CAT": ("Đệm cát nền", "m³"),
    "CAN_NEN": ("Cán nền", "m²"),
    "CHONG_THAM": ("Chống thấm", "m²"),
    "COT_THEP": ("Cốt thép", "tấn"),
    "COP_PHA": ("Cốp pha", "m²"),
}
CONCRETE_WORKS = ("LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "MONG")
# Cấu kiện nhận hàm lượng thép riêng (kg thép / m³ bê tông)
STEEL_ELEMENTS = {"LANH_TO": "lanh tô", "COT": "cột", "DAM": "dầm", "SAN": "sàn", "CAU_THANG": "cầu thang", "MONG": "móng"}


class GroundLayer(BaseModel):
    """Một lớp cấu tạo nền tầng trệt, từ dưới lên."""
    kind: Literal["NEN_DEM_CAT", "BE_TONG_LOT"]
    thickness_mm: float


class FoundationItem(BaseModel):
    """Một loại móng nhập tay (Quy ước B3 chưa có công thức móng): n khối dài × rộng × cao, hoặc thể tích có sẵn."""
    name: str                                       # M1, móng băng trục A...
    count: int = 1
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    volume_m3: Optional[float] = None               # nhập thẳng thể tích một khối (thắng kích thước)
    lean_thickness_mm: Optional[float] = None       # bê tông lót dưới móng, cùng mặt bằng móng


class ProjectParams(BaseModel):
    """Thông số công trình người dùng nhập một lần (Quy ước B1). Mọi trường đều có thể trống."""
    concrete_supply: Optional[Literal["ready_mix", "site_mix"]] = None   # bê tông thương phẩm | trộn tại chỗ
    concrete_grade: Optional[str] = None            # mác bê tông kết cấu, ví dụ M250
    lean_concrete_grade: Optional[str] = None       # mác bê tông lót, ví dụ M100
    masonry_mortar_grade: Optional[str] = None      # mác vữa xây, ví dụ M75 (trống: theo phương án tường)
    plaster_mortar_grade: Optional[str] = None      # mác vữa trát
    screed_mortar_grade: Optional[str] = None       # mác vữa cán nền
    plaster_thickness_mm: Optional[float] = None
    screed_thickness_mm: Optional[float] = None
    slab_thickness_mm: Optional[float] = None
    beam_depth_mm: Optional[float] = None           # cao dầm (gồm cả phần sàn)
    beam_width_mm: Optional[float] = None
    lintel_height_mm: Optional[float] = None
    lintel_bearing_mm: Optional[float] = None       # chiều dài gối lanh tô mỗi bên
    waterproof_upturn_mm: Optional[float] = None    # chiều cao cổ tường chống thấm
    waterproof_material_id: Optional[str] = None    # CT01 | CT02 | CT03
    stair_slab_thickness_mm: Optional[float] = None
    steel_kg_per_m3: dict[str, float] = Field(default_factory=dict)      # LANH_TO, COT, DAM, SAN, CAU_THANG, MONG
    steel_schedule_t: dict[str, float] = Field(default_factory=dict)     # tấn thép theo bảng thống kê, thắng hàm lượng
    foundations: list[FoundationItem] = Field(default_factory=list)
    ground_layers: list[GroundLayer] = Field(default_factory=list)


class WorkItem(BaseModel):
    """Một khối lượng công tác. quantity trống: thiếu thông tin, xem missing."""
    code: str                                       # khóa của WORKS
    name: str
    unit: str
    quantity: Optional[float] = None
    plan: Optional[str] = None                      # mặt bằng (tầng) sinh ra công tác này
    element: Optional[str] = None                   # cấu kiện cụ thể (tường 220 bao che, cột C1...)
    variant: Optional[str] = None                   # chiều dày trát, mác bê tông, mã vật liệu chống thấm...
    wall_system_id: Optional[str] = None            # công tác xây: phương án tường (định mức gạch, vữa)
    steel_element: Optional[str] = None             # công tác cốt thép: cấu kiện (COT, DAM...)
    formwork_of: Optional[str] = None               # công tác cốp pha: cấu kiện (LANH_TO, COT, DAM, SAN, CAU_THANG, MONG)
    formula: str = ""                               # công thức đã thay số, để người dùng kiểm tra
    source: str = "auto"                            # auto (tính từ bản vẽ) | manual (người dùng nhập)
    missing: list[str] = Field(default_factory=list)


class MaterialUse(BaseModel):
    """Một phần khối lượng của vật liệu, sinh ra từ một công tác (để truy ngược)."""
    work: str
    plan: Optional[str] = None
    quantity: Optional[float] = None
    via: str = ""                                   # chuỗi quy đổi: "XAY 12,5 m³ × 550 viên/m³" ...


class MaterialLine(BaseModel):
    """Vật liệu mua về, đã cộng mọi công tác. quantity chưa gồm hao hụt; quantity_with_waste có hao hụt khi biết %."""
    material_id: Optional[str] = None               # trống: danh mục chưa có mã (xem name)
    name: str
    unit: str
    quantity: Optional[float] = None                # tổng phần đã tính được
    complete: bool = True                           # False: có phần không tính được (thiếu định mức, thông số)
    waste_pct: Optional[float] = None
    quantity_with_waste: Optional[float] = None
    uses: list[MaterialUse] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class IntermediateLine(BaseModel):
    """Vật liệu trung gian (vữa, bê tông) trước khi tách ra vật liệu gốc."""
    kind: str                                       # vua | be_tong
    grade: Optional[str] = None
    material_id: Optional[str] = None
    name: str
    unit: str = "m³"
    quantity: Optional[float] = None
    complete: bool = True


class RoughBill(BaseModel):
    works: list[WorkItem]
    intermediates: list[IntermediateLine] = Field(default_factory=list)
    materials: list[MaterialLine] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
