"""Kiểu dữ liệu của bóc khối lượng phần thô: thông số công trình, công tác, vật liệu mua về.

Theo Quy ước bản vẽ v1.0 (B1, B3, B7): thông số nào người dùng chưa nhập thì để trống; công tác cần thông số đó
không ra số và có cảnh báo, không điền số mặc định im lặng.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    """Kích thước có nguồn: m, m², count cho một lần và repetitions là số lần lặp.

    input là đầu vào; reference không được nhân thành lượng net;
    union/deduction là tổng hợp/khoản trừ, không phải cấu kiện mới.
    None được phân biệt thiếu/không áp dụng bằng hai danh sách trường.
    """
    model_config = ConfigDict(allow_inf_nan=False)

    label: str
    basis: Literal["input", "reference", "union", "deduction"] = "input"
    count: Optional[float] = None
    repetitions: int = Field(default=1, ge=1)
    length_m: Optional[float] = None
    gross_length_m: Optional[float] = None
    deducted_length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    floor_height_m: Optional[float] = None
    bottom_level_m: Optional[float] = None
    top_level_m: Optional[float] = None
    slope_ratio: Optional[float] = None
    faces: Optional[float] = None
    concrete_height_m: Optional[float] = None
    thickness_m: Optional[float] = None
    top_length_m: Optional[float] = None
    top_width_m: Optional[float] = None
    slope_length_m: Optional[float] = None
    diameter_m: Optional[float] = None
    area_m2: Optional[float] = None
    opening_area_m2: Optional[float] = None
    net_area_m2: Optional[float] = None
    source: str
    field_sources: dict[str, str] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    not_applicable_fields: list[str] = Field(default_factory=list)
    note: str = ""

    @model_validator(mode="after")
    def _field_meanings(self):
        numeric = ("count", "length_m", "gross_length_m", "deducted_length_m", "width_m", "height_m",
                   "floor_height_m", "bottom_level_m", "top_level_m", "slope_ratio", "faces",
                   "concrete_height_m", "thickness_m", "top_length_m", "top_width_m", "slope_length_m",
                   "diameter_m", "area_m2", "opening_area_m2", "net_area_m2")
        provided = self.model_fields_set
        # Trường được producer truyền None là thiếu; trường không dùng là không áp dụng.
        # JSON round-trip giữ nguyên hai danh sách, không phân loại lại mọi null thành thiếu.
        if not ({"missing_fields", "not_applicable_fields"} & provided):
            self.missing_fields = [k for k in numeric if k in provided and getattr(self, k) is None]
            self.not_applicable_fields = [k for k in numeric if k not in provided and getattr(self, k) is None]
        if not self.source.strip() and "source" not in self.missing_fields:
            self.missing_fields.append("source")
        self.field_sources = {**{k: self.source for k in numeric if k not in self.not_applicable_fields}, **self.field_sources}
        return self


def _quantity_decimal_text(value) -> str:
    """Giữ giá trị producer đưa vào, không làm tròn hoặc sửa floating artifact."""
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Lượng chi tiết phải là số thập phân hợp lệ.") from exc
    if not number.is_finite():
        raise ValueError("Lượng chi tiết phải là số hữu hạn.")
    return format(number, "f")


def _quantity_detail_amounts(rows, legacy_quantity):
    known = [r for r in rows if r.role == "contribution" and r.raw_quantity is not None]
    numbers = [Decimal(r.raw_quantity) for r in known]
    legacy = None if legacy_quantity is None else Decimal(_quantity_decimal_text(legacy_quantity))
    values = numbers + ([] if legacy is None else [legacy])
    with localcontext() as ctx:
        # Cộng/trừ chính xác theo số chữ số đã nhận, không làm tròn trung gian về context mặc định.
        ctx.prec = max(28, max((n.adjusted() for n in values), default=0)
                       - min((n.as_tuple().exponent for n in values), default=0) + len(str(len(values) + 1)) + 2)
        total = sum((r.sign * n for r, n in zip(known, numbers)), Decimal(0)) if known else None
        delta = total - legacy if total is not None and legacy is not None else None
    return total, delta


class DetailConversion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_unit: str
    to_unit: str
    factor: str
    source: str

    @field_validator("from_unit", "to_unit", "source")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Đơn vị quy đổi và nguồn không được trống.")
        return value

    @field_validator("factor")
    @classmethod
    def _factor(cls, value):
        result = _quantity_decimal_text(value)
        if Decimal(result) <= 0:
            raise ValueError("Hệ số quy đổi phải dương và hữu hạn.")
        return result


class DetailFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    value: str
    unit: str                         # "1" nếu không thứ nguyên
    meaning: str
    source: str

    @field_validator("name", "unit", "meaning", "source")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Hệ số phụ cần tên, đơn vị, ý nghĩa và nguồn.")
        return value

    @field_validator("value")
    @classmethod
    def _value(cls, value):
        result = _quantity_decimal_text(value)
        if Decimal(result) < 0:
            raise ValueError("Hệ số phụ không âm; khoản trừ dùng sign riêng.")
        return result


class QuantityDetailRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    row_id: str                       # chỉ ổn định trong đúng một result snapshot
    label: str
    group: str = ""
    role: Literal["contribution", "reference"] = "contribution"
    sign: Literal[1, -1] = 1
    unit: str
    raw_quantity: str | None = None   # trị tuyệt đối, ĐÃ gồm count/lặp/hệ số/quy đổi nếu áp dụng
    method: Literal["box", "area", "perimeter", "count", "prismoid", "union", "steel", "ratio", "source_quantity"]
    # Không thực thi/parse expression; kích thước và nguồn để hiển thị, không cộng lại.
    dimensions: WorkDimensions | None = None
    conversion: DetailConversion | None = None
    factors: list[DetailFactor] = Field(default_factory=list)
    expression: str = ""
    sources: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)

    @field_validator("row_id", "label", "unit")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Khóa dòng, diễn giải và đơn vị không được trống.")
        return value

    @field_validator("raw_quantity")
    @classmethod
    def _quantity(cls, value):
        if value is None:
            return None
        result = _quantity_decimal_text(value)
        if Decimal(result) < 0:
            raise ValueError("raw_quantity là trị tuyệt đối; khoản trừ dùng sign=-1.")
        return result

    @model_validator(mode="after")
    def _source_and_missing(self):
        if not self.sources or any(not s.strip() for s in self.sources):
            raise ValueError("Mỗi dòng chi tiết cần nguồn.")
        if any(not reason.strip() for reason in self.missing):
            raise ValueError("Lý do thiếu không được chỉ có khoảng trắng.")
        if self.raw_quantity is None and not self.missing:
            raise ValueError("Lượng chưa biết phải có lý do thiếu, không thay bằng 0.")
        if self.conversion and self.conversion.to_unit != self.unit:
            raise ValueError("Quy đổi phải kết thúc ở đơn vị dòng đóng góp.")
        return self


class WorkQuantityDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit: str
    rows: list[QuantityDetailRow]
    detail_level: Literal["components", "aggregate", "unavailable"]
    known_part_raw: str | None
    total_raw: str | None             # chỉ có nếu toàn phạm vi đủ, không dùng known_part giả tổng đủ
    complete: bool
    scope_complete: bool             # producer xác định phạm vi, không suy từ số dòng có lượng
    legacy_quantity: str | None
    legacy_delta: str | None          # raw known part − số legacy, không tự sửa legacy

    @field_validator("known_part_raw", "total_raw", "legacy_quantity", "legacy_delta")
    @classmethod
    def _finite_decimal(cls, value):
        return None if value is None else _quantity_decimal_text(value)

    @model_validator(mode="after")
    def _invariants(self):
        if not self.unit.strip() or len({r.row_id for r in self.rows}) != len(self.rows):
            raise ValueError("Đơn vị tổng không trống; row_id không trùng.")
        contributions = [r for r in self.rows if r.role == "contribution"]
        if any(r.unit != self.unit for r in contributions):
            raise ValueError("Không cộng đóng góp khác đơn vị công tác.")
        value, expected_delta = _quantity_detail_amounts(self.rows, self.legacy_quantity)
        expected_complete = bool(contributions) and self.scope_complete and all(
            r.raw_quantity is not None and not r.missing for r in contributions)
        expected_total = value if expected_complete else None
        def matches(actual, expected):
            return actual is None if expected is None else actual is not None and Decimal(actual) == expected
        if (not matches(self.known_part_raw, value) or self.complete != expected_complete
                or not matches(self.total_raw, expected_total) or not matches(self.legacy_delta, expected_delta)):
            raise ValueError("Tổng detail/complete/delta không khớp signed contribution và phạm vi.")
        return self



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
    quantity_detail: Optional[WorkQuantityDetail] = None
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


    @model_validator(mode="after")
    def _quantity_detail_matches_work(self):
        if self.quantity_detail is not None:
            detail = self.quantity_detail
            if detail.unit != self.unit:
                raise ValueError("Đơn vị detail không khớp công tác.")
            legacy = None if self.quantity is None else _quantity_decimal_text(self.quantity)
            if (legacy is None) != (detail.legacy_quantity is None) or (
                    legacy is not None and Decimal(legacy) != Decimal(detail.legacy_quantity)):
                raise ValueError("Lượng legacy trong detail không khớp công tác của snapshot.")
            if (self.quantity is None or self.missing or self.status == "D") and (detail.complete or detail.total_raw is not None):
                raise ValueError("Công tác chưa có lượng, D hoặc còn thiếu chỉ được giữ phần lượng đã biết trong detail.")
        return self


class MaterialUse(BaseModel):
    """Một phần khối lượng của vật liệu, sinh ra từ một công tác (để truy ngược)."""
    work: str
    rowIndex: Optional[int] = Field(default=None, ge=0)  # works[i] của chính snapshot, tương ứng khóa w:i
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


class QuantityGroupingContext(BaseModel):
    """Chỉ các tham số đã có dùng phân nhóm; lưu cùng snapshot, không suy mã định mức."""
    model_config = ConfigDict(extra="forbid")
    concrete_grade: Optional[str] = None
    lean_concrete_grade: Optional[str] = None
    concrete_supply: Optional[str] = None
    masonry_mortar_grade: Optional[str] = None
    plaster_mortar_grade: Optional[str] = None
    screed_mortar_grade: Optional[str] = None
    formwork_type: Optional[str] = None


class QuantityCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_count: int = Field(default=0, ge=0)
    components: int = Field(default=0, ge=0)
    aggregate: int = Field(default=0, ge=0)
    unavailable: int = Field(default=0, ge=0)
    no_detail: int = Field(default=0, ge=0)
    quantity_complete_works: int = Field(default=0, ge=0)
    quantity_incomplete_works: int = Field(default=0, ge=0)
    contribution_rows: int = Field(default=0, ge=0)
    known_contribution_rows: int = Field(default=0, ge=0)
    unknown_contribution_rows: int = Field(default=0, ge=0)
    reference_rows: int = Field(default=0, ge=0)
    compatibility_pending_works: int = Field(default=0, ge=0)
    legacy_D_works: int = Field(default=0, ge=0)
    legacy_missing_works: int = Field(default=0, ge=0)
    complete_components: bool = False

    @model_validator(mode="after")
    def _counts(self):
        if (self.components + self.aggregate + self.unavailable + self.no_detail != self.work_count
                or self.quantity_complete_works + self.quantity_incomplete_works != self.work_count
                or self.known_contribution_rows + self.unknown_contribution_rows != self.contribution_rows):
            raise ValueError("Các count coverage không khớp phạm vi công tác/dòng.")
        if any(n > self.work_count for n in (self.compatibility_pending_works, self.legacy_D_works, self.legacy_missing_works)):
            raise ValueError("Count theo công tác vượt phạm vi snapshot.")
        expected = self.work_count > 0 and self.components == self.work_count and self.quantity_complete_works == self.work_count
        if self.complete_components != expected:
            raise ValueError("Coverage cấu kiện không khớp số dòng đủ; phạm vi rỗng không được coi là đủ.")
        return self


class QuantityGroupKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: Optional[str] = None
    code: str
    variant: Optional[str] = None
    unit: str
    source: str
    basis: Optional[str] = None
    formwork_of: Optional[str] = None
    steel_element: Optional[str] = None
    wall_system_id: Optional[str] = None
    specification: dict[str, Optional[str]] = Field(default_factory=dict)
    isolated_work_key: Optional[str] = None

    @field_validator("code", "unit")
    @classmethod
    def _nonempty(cls, value):
        if not value.strip():
            raise ValueError("Mã công tác và đơn vị nhóm không được trống.")
        return value


class QuantityMissingRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_key: str
    row_id: Optional[str] = None
    reasons: list[str]


class QuantityRawGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_id: str
    key: QuantityGroupKey
    member_work_keys: list[str]
    compatibility: Literal["resolved", "isolated_unknown"]
    compatibility_reasons: list[str] = Field(default_factory=list)
    calculation_methods: list[str] = Field(default_factory=list)  # trace, không dùng để tách quy cách
    known_part_raw: Optional[str] = None
    total_raw: Optional[str] = None
    complete: bool = False
    coverage: QuantityCoverage
    missing_work_refs: list[QuantityMissingRef] = Field(default_factory=list)

    @field_validator("known_part_raw", "total_raw")
    @classmethod
    def _amount(cls, value):
        return None if value is None else _quantity_decimal_text(value)

    @model_validator(mode="after")
    def _members(self):
        if not self.member_work_keys or len(set(self.member_work_keys)) != len(self.member_work_keys):
            raise ValueError("Nhóm cần thành viên không lặp trong snapshot.")
        if self.coverage.work_count != len(self.member_work_keys):
            raise ValueError("Count nhóm không khớp membership.")
        if any(ref.work_key not in self.member_work_keys for ref in self.missing_work_refs):
            raise ValueError("Dòng thiếu tham chiếu công tác ngoài nhóm.")
        if (self.complete != (self.total_raw is not None) or
                self.complete and (self.known_part_raw is None or Decimal(self.total_raw) != Decimal(self.known_part_raw))):
            raise ValueError("Tổng raw đủ không khớp phần biết của nhóm.")
        return self


class QuantitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    quantity_snapshot_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    context: QuantityGroupingContext
    groups: list[QuantityRawGroup] = Field(default_factory=list)
    coverage: QuantityCoverage
