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
    "GIANG_TUONG": ("Bê tông giằng tường", "m³"),
    "SE_NO": ("Bê tông sê nô", "m³"),
    "MAI": ("Bê tông mái", "m³"),
    "MONG": ("Bê tông móng", "m³"),
    "BE_TONG_LOT": ("Bê tông lót", "m³"),
    "DAO_DAT": ("Đào đất hố móng", "m³"),
    "DAP_DAT": ("Đắp đất hố móng", "m³"),
    "NEN_DEM_CAT": ("Đệm cát nền", "m³"),
    "CAN_NEN": ("Cán nền", "m²"),
    "CHONG_THAM": ("Chống thấm", "m²"),
    "COT_THEP": ("Cốt thép", "tấn"),
    "COP_PHA": ("Cốp pha", "m²"),
}
CONCRETE_WORKS = ("LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "GIANG_TUONG", "SE_NO", "MAI", "MONG")
# Cấu kiện nhận hàm lượng thép riêng (kg thép / m³ bê tông) và nhận dòng bảng thống kê thép
STEEL_ELEMENTS = {"LANH_TO": "lanh tô", "COT": "cột", "DAM": "dầm", "SAN": "sàn", "CAU_THANG": "cầu thang",
                  "GIANG_TUONG": "giằng tường", "SE_NO": "sê nô", "MAI": "mái", "MONG": "móng"}
# Vai trò ký hiệu cấu kiện (data/rules/ky_hieu_cau_kien.csv) -> mã công tác bê tông
ROLE_WORK = {"COLUMN": "COT", "BEAM": "DAM", "FOUNDATION": "MONG", "SLAB": "SAN", "LINTEL": "LANH_TO", "STAIR": "CAU_THANG",
             "WALL_TIE": "GIANG_TUONG", "GUTTER": "SE_NO", "ROOF": "MAI"}

# Trạng thái dữ liệu (đặc tả 30/10/2026 mục 3): mỗi khối lượng và mỗi dòng vật liệu mang đúng một trạng thái; kết quả
# mang trạng thái YẾU NHẤT của các đầu vào tạo ra nó (D > C > B > A).
#   A  đọc trực tiếp từ hình học hoặc chữ trên bản vẽ (chiều dài, dày tường; cửa có kích thước trong block; thép theo bảng)
#   B  suy luận theo quy tắc đã định (chiều cao tầng từ cao độ; dầm suy từ tường + cột; đường bao từ tường; hatch dựng lại)
#   C  giả định người dùng nhập hoặc mặc định đã công bố (thông số công trình: dày sàn, cao dầm, hàm lượng thép, mác…)
#   D  thiếu dữ liệu: không xác định được, không xuất thành số (quantity trống)
Status = Literal["A", "B", "C", "D"]
STATUS_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
STATUS_LABEL = {"A": "đọc trực tiếp", "B": "suy luận", "C": "tạm tính (giả định người dùng)", "D": "thiếu dữ liệu"}


def worst_status(*statuses: Optional[str]) -> Optional[str]:
    """Trạng thái yếu nhất trong các đầu vào; bỏ qua None. Không có đầu vào nào thì None."""
    known = [s for s in statuses if s]
    return max(known, key=STATUS_ORDER.__getitem__) if known else None


# Loại vật liệu thô (cột raw_class của danh mục, 02/11/2026): nhỏ hơn 5 nhóm của đề cương để mỗi bản vẽ chọn bóc loại
# mong muốn (ProjectParams.material_classes). Dòng vật liệu chưa có mã danh mục xếp loại theo tên (RAW_CLASS_BY_NAME).
RAW_CLASSES = {"xi_mang": "Xi măng", "cat": "Cát", "da": "Đá", "gach": "Gạch xây", "vua_be_tong": "Vữa, bê tông thành phẩm",
               "thep": "Thép cốt, dây buộc", "cop_pha": "Cốp pha, giàn giáo", "chong_tham": "Chống thấm",
               "phu_gia": "Phụ gia, phụ kiện", "coc_san": "Cọc, sàn đặc thù", "khac": "Khác (ngoài phần thô)"}
RAW_CLASS_BY_NAME = (("thép", "thep"), ("gạch", "gach"), ("bê tông", "vua_be_tong"), ("vữa", "vua_be_tong"))


# Giai đoạn thi công của công tác (đặc tả mục 11: gom lượng vật liệu cần theo thời điểm cung ứng)
STAGES = {"dat_mong": "Đất và móng", "khung": "Khung bê tông cốt thép", "tuong": "Tường xây, trát", "chong_tham": "Chống thấm, nền"}
WORK_STAGE = {"DAO_DAT": "dat_mong", "DAP_DAT": "dat_mong", "NEN_DEM_CAT": "dat_mong", "BE_TONG_LOT": "dat_mong", "MONG": "dat_mong",
              "COT": "khung", "DAM": "khung", "SAN": "khung", "CAU_THANG": "khung", "GIANG_TUONG": "khung", "SE_NO": "khung",
              "MAI": "khung", "LANH_TO": "khung", "COT_THEP": "khung", "COP_PHA": "khung",
              "XAY": "tuong", "TRAT": "tuong", "CAN_NEN": "chong_tham", "CHONG_THAM": "chong_tham"}


class GroundLayer(BaseModel):
    """Một lớp cấu tạo nền tầng trệt, từ dưới lên."""
    kind: Literal["NEN_DEM_CAT", "BE_TONG_LOT"]
    thickness_mm: float


class FootingTier(BaseModel):
    """Một lớp (bậc) của móng, kể từ dưới lên: khối hộp dài × rộng × cao; có top_* thì mặt trên thu lại (lớp vát)."""
    length_mm: float
    width_mm: float
    height_mm: float
    top_length_mm: Optional[float] = None
    top_width_mm: Optional[float] = None


class FoundationItem(BaseModel):
    """Một loại móng: n khối dài × rộng × cao, hoặc các lớp (tiers), hoặc thể tích có sẵn (rough/foundations.py)."""
    name: str                                       # M1, móng băng trục A...
    count: int = 1
    kind: Optional[Literal["don", "bang"]] = None    # móng đơn | móng băng (dài = chiều dài băng đã trừ phần giao)
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    tiers: list[FootingTier] = Field(default_factory=list)   # có lớp thì thắng dài × rộng × cao
    volume_m3: Optional[float] = None               # nhập thẳng thể tích một khối (thắng kích thước)
    lean_thickness_mm: Optional[float] = None       # bê tông lót dưới móng, cùng mặt bằng móng
    bottom_level_mm: Optional[float] = None         # cao độ mặt dưới khối móng (trên lớp lót) so với ±0.000
    neck_b_mm: Optional[float] = None               # tiết diện cổ móng (phần chôn dưới đất được trừ khi đắp lại)
    neck_h_mm: Optional[float] = None
    positions: list[tuple[float, float]] = Field(default_factory=list)   # tâm từng khối (mm, tọa độ mặt bằng móng)
    plan: Optional[str] = None                      # mặt bằng móng chứa positions (để cắt giằng qua móng)
    source: str = ""                                # truy ngược: file, hình chi tiết, mặt cắt đã đọc


class RoofItem(BaseModel):
    """Một mái nhập tay. Chỉ mái bê tông có phương pháp đo bóc (S08-03); mái khung (vì kèo, xà gồ, tôn, ngói) ghi
    Not supported, không trả số."""
    name: str = "Mái"
    kind: Literal["be_tong", "khung"]
    area_m2: Optional[float] = None                 # diện tích bản mái theo mặt nghiêng
    thickness_mm: Optional[float] = None
    replaces_slab_of: Optional[str] = None          # mái này là sàn trên của mặt bằng đó: bỏ công tác sàn của mặt bằng


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
    natural_ground_level_mm: Optional[float] = None  # cốt đất tự nhiên so với ±0.000 (đào móng)
    excavation_margin_mm: Optional[float] = None    # mở rộng đáy hố đào mỗi bên so với mép lót (thi công)
    excavation_slope: Optional[float] = None        # hệ số mái taluy m (rộng / cao); 0 = vách đứng
    roofs: list[RoofItem] = Field(default_factory=list)
    ground_layers: list[GroundLayer] = Field(default_factory=list)
    # đặc tả 30/10/2026 mục 4.3: văn bản đo bóc hiện hành không nêu ngưỡng lỗ nhỏ được bỏ qua; ngưỡng là tham số cấu
    # hình do nhóm khai báo và ghi vào hồ sơ. Mặc định 0 = trừ mọi lỗ cửa. Lỗ có diện tích (rộng × cao) nhỏ hơn ngưỡng
    # thì không trừ khỏi khối xây và trát (vẫn liệt kê, ghi trong công thức).
    min_opening_m2: float = 0.0
    # đặc tả mục 11: hướng bắc của bản vẽ (độ, đo từ trục +x ngược chiều kim đồng hồ) để gom diện tích tường bao và cửa
    # theo hướng nhà cho tính nhiệt vỏ bao che; trống: không tính hướng
    north_deg: Optional[float] = None
    # đặc tả mục 7: diện tích xây dựng (m², bảng chỉ tiêu trên bản vẽ) để kiểm tổng sàn từng tầng; bản vẽ build chưa ghi
    # nên người dùng nhập (C); trống: không kiểm
    building_area_m2: Optional[float] = None
    # phương án tường người dùng chọn theo lớp chiều dày (110, 150, 220, 330) cho tường mà bản vẽ không ghi vật liệu
    # (không ghi chú, hatch, layer nào khớp); chỉ áp cho tường còn trống, ghi trạng thái C. Ví dụ {"220": "W-GO01-200"}
    wall_systems_by_class: dict[str, str] = Field(default_factory=dict)
    # loại vật liệu thô cần bóc (khóa RAW_CLASSES); trống = mọi loại. Khối lượng công tác vẫn tính đủ, chỉ lọc bảng vật liệu
    material_classes: list[str] = Field(default_factory=list)
    # loại ván khuôn (đặc tả mục 6, tham số người dùng C): go = ván khuôn gỗ AF.81 theo cấu kiện; van_ep = ván ép phủ phim
    # (chưa có định mức TT 38); trống: chưa chọn, vật liệu cốp pha để trống
    formwork_type: Optional[Literal["go", "van_ep"]] = None


class MasonryGeometry(BaseModel):
    """Hình học gốc của nhóm xây; khối lượng cuối lấy từ WorkItem sau mọi phép trừ."""
    wall_type: str
    role: str
    length_m: float
    gross_area_m2: float
    opening_area_m2: float
    thickness_m: float = Field(gt=0)
    issues: list[str] = Field(default_factory=list)


class WorkDimensions(BaseModel):
    """Kích thước đầu vào để kiểm; đơn vị m, m². Không suy ngược từ khối lượng/công thức.

    Một công tác có thể gồm nhiều cấu kiện/lớp; mỗi phần giữ kích thước và nguồn riêng.
    None là chưa biết/không áp dụng; note phân biệt hai trường hợp trên giao diện.
    """
    label: str
    count: Optional[float] = None
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    thickness_m: Optional[float] = None
    area_m2: Optional[float] = None
    opening_area_m2: Optional[float] = None
    source: str
    note: str = ""


class WorkItem(BaseModel):
    """Một khối lượng công tác. quantity trống: thiếu thông tin, xem missing."""
    code: str                                       # khóa của WORKS
    name: str
    unit: str
    quantity: Optional[float] = None
    plan: Optional[str] = None                      # mặt bằng (tầng) sinh ra công tác này
    element: Optional[str] = None                   # cấu kiện cụ thể (tường 220 bao che, cột C1...)
    variant: Optional[str] = None                   # chiều dày trát, mác bê tông, mã vật liệu chống thấm...
    masonry_geometry: Optional[MasonryGeometry] = None
    dimensions: list[WorkDimensions] = Field(default_factory=list)
    wall_system_id: Optional[str] = None            # công tác xây: phương án tường (định mức gạch, vữa); trát: nền trát
    steel_element: Optional[str] = None             # công tác cốt thép: cấu kiện (COT, DAM...)
    formwork_of: Optional[str] = None               # công tác cốp pha: cấu kiện (mã công tác bê tông)
    formula: str = ""                               # công thức đã thay số, để người dùng kiểm tra
    source: str = "auto"                            # auto (tính từ bản vẽ) | manual (người dùng nhập)
    basis: Optional[str] = None                     # cốt thép, mái: bang_thong_ke | ham_luong | not_supported
    evidence: list[str] = Field(default_factory=list)   # chỗ lấy số trên bản vẽ (bảng, dòng, tọa độ, layer)
    missing: list[str] = Field(default_factory=list)
    # trạng thái dữ liệu A/B/C/D (đặc tả mục 3) và các đầu vào quyết định trạng thái, ví dụ ["chiều cao tầng: B", "dày sàn: C"]
    status: Optional[Status] = None
    inputs: list[str] = Field(default_factory=list)
    stage: Optional[str] = None                     # giai đoạn thi công (WORK_STAGE), gán ở bước gộp


class MaterialUse(BaseModel):
    """Một phần khối lượng của vật liệu, sinh ra từ một công tác (để truy ngược)."""
    work: str
    plan: Optional[str] = None
    quantity: Optional[float] = None
    via: str = ""                                   # chuỗi quy đổi: "XAY 12,5 m³ × 550 viên/m³" ...
    status: Optional[Status] = None                 # = trạng thái công tác, hạ xuống C khi hệ số là kinh nghiệm/tính
    stage: Optional[str] = None
    # lượng đi qua định mức TT 38/2026 (có số hiệu bảng): định mức đã gồm hao hụt thi công (PL II, quy định chung 1)
    waste_included: bool = False


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
    status: Optional[Status] = None                 # xấu nhất trong các uses (D, C, B, A); D khi có phần không tính được
    group_id: Optional[str] = None                  # nhóm vật liệu của danh mục (materials.group): 5 nhóm của đề cương
    raw_class: Optional[str] = None                 # loại vật liệu thô (RAW_CLASSES); chưa có mã thì theo tên
    weight_kg: Optional[float] = None               # quantity × unit_weight_kg (vận chuyển); trống: chưa có khối lượng riêng
    transport_volume_m3: Optional[float] = None     # quantity × transport_volume_m3 của danh mục khi có
    quantity_min: Optional[float] = None            # khoảng giá trị khi hệ số là ước chừng có khoảng (đặc tả 3B)
    quantity_max: Optional[float] = None
    confirmation: Optional[str] = None              # mức xác nhận yếu nhất của hệ số đã dùng: nguon | tinh | kinh_nghiem
    # giá thấp nhất đang có cùng đơn vị (supplier_materials, price_records); trống: chưa có giá hoặc khác đơn vị
    best_price: Optional[float] = None
    price_source: Optional[str] = None              # mức giá (DEALER | QUOTE | BULLETIN), nơi bán, ngày
    est_cost: Optional[float] = None                # khối lượng (có hao hụt nếu biết) × giá; chưa gồm vận chuyển, nhân công


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
