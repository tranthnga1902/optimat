"""Ánh xạ tương thích PostgreSQL của các luồng/API hiện có.

Lược đồ lưu trữ chính thức gồm 20 bảng trong db/schema20.py. Một số lớp ở đây
ánh xạ view có thể ghi, không phải bảng vật lý. Khởi tạo qua compat20.initialize_database;
chuyển dữ liệu cũ bằng scripts/migrate_schema20.py, không gọi Base.metadata.create_all.

Các cấu trúc tương thích chia 4 cụm:
danh mục vật liệu, nguồn cung và giá, người dùng và dự án, vận hành hệ thống.

Tên cột của các bảng danh mục trùng với tên cột trong các file CSV để phần còn lại của hệ thống
không phải đổi. Số thực dùng Float thay vì Numeric để pandas nhận về float, không phải Decimal.
File sql/schema.sql được sinh từ file này bằng scripts/export_sql.py; sửa ở đây rồi sinh lại.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer,
                        MetaData, String, Text, UniqueConstraint, func, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATA_KINDS = "('ACTUAL', 'SAMPLE', 'SYNTHETIC')"
YES_NO = "('YES', 'NO', 'UNKNOWN')"
# Mức giá lưu trong database. PREDICTED (giá dự đoán) chỉ có ở đầu ra công cụ Price, không lưu ở đây.
PRICE_LEVELS_OBSERVED = "('DEALER', 'QUOTE', 'BULLETIN')"   # giá đại lý, báo giá trực tiếp, công bố giá


class Base(DeclarativeBase):
    # Đặt tên ràng buộc UNIQUE giống tên PostgreSQL tự sinh, để script nâng cấp nhận ra ràng buộc đã có.
    metadata = MetaData(naming_convention={"ix": "ix_%(column_0_label)s",
                                         "uq": "%(table_name)s_%(column_0_N_name)s_key"})


# ============================== 1. Danh mục vật liệu ==============================

class MaterialGroup(Base):
    """Năm nhóm vật liệu tổng thể của đề tài."""
    __tablename__ = "material_groups"
    group_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")


class MaterialFamily(Base):
    """Họ vật liệu (cột family của bảng materials). is_wall: họ vật liệu xây tường, dùng cho quy tắc bóc tách và tối ưu."""
    __tablename__ = "material_families"
    family_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer)
    is_wall: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_materials_data_kind"),)
    material_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    group: Mapped[str] = mapped_column(ForeignKey("material_groups.group_id"))
    thickness_mm: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))
    qty_per_m2: Mapped[Optional[float]] = mapped_column(Float)
    weight_kg_per_m2: Mapped[Optional[float]] = mapped_column(Float)
    lambda_w_mk: Mapped[Optional[float]] = mapped_column(Float)
    labor_days_per_m2: Mapped[Optional[float]] = mapped_column(Float)
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")
    # --- Danh mục 93 vật liệu (nạp bằng sql/03_materials.sql). Các cột thickness_mm, qty_per_m2, weight_kg_per_m2,
    # labor_days_per_m2 ở trên là của dữ liệu mẫu cũ; định mức theo chiều dày tường nay nằm ở bảng wall_systems.
    subgroup: Mapped[Optional[str]] = mapped_column(String(128))
    family: Mapped[Optional[str]] = mapped_column(ForeignKey("material_families.family_id"))   # họ vật liệu, dùng cho quy tắc bóc tách
    usage_text: Mapped[Optional[str]] = mapped_column(String(255))
    usage_role: Mapped[Optional[str]] = mapped_column(String(128))
    tier: Mapped[Optional[int]] = mapped_column(Integer)                 # 1 tối ưu sâu, 2 tối ưu nguồn cung, 3 tham khảo
    purchase_unit: Mapped[Optional[str]] = mapped_column(String(32))
    unit_conversion: Mapped[Optional[float]] = mapped_column(Float)      # số đơn vị mua trong một đơn vị tính
    length_mm: Mapped[Optional[float]] = mapped_column(Float)
    width_mm: Mapped[Optional[float]] = mapped_column(Float)
    height_mm: Mapped[Optional[float]] = mapped_column(Float)
    price_priority: Mapped[Optional[str]] = mapped_column(String(4))     # A, B, C hoặc — (không cào giá)
    needs_lambda: Mapped[Optional[bool]] = mapped_column(Boolean)
    lambda_source: Mapped[Optional[str]] = mapped_column(String(255))
    unit_weight_kg: Mapped[Optional[float]] = mapped_column(Float)       # kg trên một đơn vị tính
    weight_source: Mapped[Optional[str]] = mapped_column(String(255))
    transport_volume_m3: Mapped[Optional[float]] = mapped_column(Float)
    waste_pct: Mapped[Optional[float]] = mapped_column(Float)
    waste_source: Mapped[Optional[str]] = mapped_column(String(255))
    standards_text: Mapped[Optional[str]] = mapped_column(Text)
    reference_brands: Mapped[Optional[str]] = mapped_column(Text)
    tech_notes: Mapped[Optional[str]] = mapped_column(Text)
    data_note: Mapped[Optional[str]] = mapped_column(Text)
    raw_class: Mapped[Optional[str]] = mapped_column(String(32))         # loại vật liệu thô (RAW_CLASSES trong rough/models.py) để chọn vật liệu cần bóc


class WallSystem(Base):
    """Phương án xây tường: một vật liệu ở một chiều dày tường, kèm định mức theo 1 m3 khối xây."""
    __tablename__ = "wall_systems"
    __table_args__ = (CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_wall_systems_data_kind"),)
    wall_system_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id", ondelete="CASCADE"), index=True)
    wall_thickness_mm: Mapped[Optional[float]] = mapped_column(Float)    # chiều dày danh nghĩa
    detect_class: Mapped[Optional[str]] = mapped_column(String(8))       # lớp nhận diện bản vẽ: 110, 150, 220, 330
    role: Mapped[Optional[str]] = mapped_column(String(16))              # envelope | partition
    masonry_thickness_mm: Mapped[Optional[float]] = mapped_column(Float)
    norm_code: Mapped[Optional[str]] = mapped_column(String(32))
    units_per_m3: Mapped[Optional[float]] = mapped_column(Float)
    mortar_m3_per_m3: Mapped[Optional[float]] = mapped_column(Float)
    labor_day_per_m3: Mapped[Optional[float]] = mapped_column(Float)
    unit_factor: Mapped[Optional[float]] = mapped_column(Float)          # đổi viên sang đơn vị tính của vật liệu
    mortar_material_id: Mapped[Optional[str]] = mapped_column(ForeignKey("materials.material_id"))
    mortar_density: Mapped[Optional[float]] = mapped_column(Float)
    r0_reference: Mapped[Optional[float]] = mapped_column(Float)         # R0 tường mẫu QCVN 09:2017, để kiểm tra phép tính U
    norm_source: Mapped[Optional[str]] = mapped_column(String(255))
    note: Mapped[Optional[str]] = mapped_column(Text)
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")


class MaterialRelation(Base):
    """Vật liệu đi kèm bắt buộc (REQUIRES) và cấp phối (COMPOSED_OF)."""
    __tablename__ = "material_relations"
    __table_args__ = (UniqueConstraint("material_id", "related_material_id", "relation_type"),
                      CheckConstraint("relation_type IN ('REQUIRES', 'COMPOSED_OF')", name="ck_material_relations_type"))
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(16))
    related_material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id", ondelete="CASCADE"))
    quantity: Mapped[Optional[float]] = mapped_column(Float)
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(64))
    source: Mapped[Optional[str]] = mapped_column(String(255))
    note: Mapped[Optional[str]] = mapped_column(Text)


class MaterialAlias(Base):
    """Tên gọi khác của vật liệu trong bản vẽ và dự toán, dùng để khớp tên."""
    __tablename__ = "material_aliases"
    __table_args__ = (UniqueConstraint("alias", "material_id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alias: Mapped[str] = mapped_column(String(255), index=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(255), default="", server_default="")


class Standard(Base):
    """Tiêu chuẩn, quy chuẩn, văn bản (TCVN, QCVN, thông tư)."""
    __tablename__ = "standards"
    standard_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(32), default="", server_default="")           # TCVN | QCVN | THONG_TU | KHAC
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", server_default="UNKNOWN")  # CON_HIEU_LUC | HET_HIEU_LUC | UNKNOWN
    valid_from: Mapped[Optional[date]] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(String(1024), default="", server_default="")


class MaterialStandard(Base):
    __tablename__ = "material_standards"
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id", ondelete="CASCADE"), primary_key=True)
    standard_id: Mapped[int] = mapped_column(ForeignKey("standards.standard_id", ondelete="CASCADE"), primary_key=True)
    note: Mapped[str] = mapped_column(String(255), default="", server_default="")


class MaterialRule(Base):
    """Quy tắc gán vật liệu theo thiết kế khi bóc tách (nạp từ data/rules/material_rules.csv). id giữ thứ tự dòng."""
    __tablename__ = "material_rules"
    __table_args__ = (CheckConstraint("signal IN ('text', 'hatch', 'layer', 'block')", name="ck_material_rules_signal"), {"comment": "Tín hiệu trên bản vẽ (ghi chú, hatch, layer, block) → vật liệu của tường. Nhiều quy tắc cùng khớp: priority lớn hơn thắng. Không khớp quy tắc nào thì để trống, không đoán."})
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(32), unique=True, comment="mã quy tắc, ví dụ T28")
    signal: Mapped[str] = mapped_column(String(16), comment="text | hatch | layer | block")
    pattern: Mapped[str] = mapped_column(String(255), comment="text, layer: chuỗi con, chữ thường bỏ dấu; hatch: tên mẫu; block: biểu thức chính quy trên tên viết hoa")
    target: Mapped[Optional[str]] = mapped_column(String(255), comment="họ vật liệu (AAC, CLAY_SOLID…) hoặc mã (GN01); nhiều giá trị cách nhau bằng |")          # họ hoặc mã vật liệu, ngăn cách bằng |
    element: Mapped[Optional[str]] = mapped_column(String(32), comment="WALL_MASONRY | CONCRETE | DOOR | WINDOW")
    width_mm: Mapped[Optional[float]] = mapped_column(Float, comment="chiều rộng (cửa), mm")
    height_mm: Mapped[Optional[float]] = mapped_column(Float, comment="chiều cao (cửa), mm")
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="số lớn hơn thắng")
    note: Mapped[Optional[str]] = mapped_column(Text, comment="ghi chú")


class RoomRule(Base):
    """Nhận loại phòng từ tên phòng trên bản vẽ (nạp từ data/rules/room_rules.csv). Quy tắc khớp trước thắng."""
    __tablename__ = "room_rules"
    __table_args__ = {"comment": "Tên phòng trên bản vẽ → loại phòng, dùng để tính chống thấm."}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(32), unique=True, comment="mã quy tắc, ví dụ R08")
    pattern: Mapped[str] = mapped_column(String(255), comment="biểu thức chính quy trên chữ thường bỏ dấu, ví dụ wc")                    # biểu thức chính quy trên chữ đã bỏ dấu
    kind: Mapped[str] = mapped_column(String(16), comment="WET | BALCONY")                        # WET | BALCONY
    note: Mapped[Optional[str]] = mapped_column(Text, comment="ghi chú")


class RoughNorm(Base):
    """Định mức công tác phần thô, cấp phối bê tông trộn tại chỗ (nạp từ data/rules/dinh_muc_phan_tho.csv)."""
    __tablename__ = "rough_norms"
    __table_args__ = {"comment": "Lượng vật liệu trên 1 đơn vị công tác phần thô và cấp phối bê tông trộn tại chỗ. Điền qty thì bắt buộc ghi norm_code."}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    work_code: Mapped[str] = mapped_column(String(32), index=True, comment="TRAT | CAN_NEN | COT_THEP | CHONG_THAM | NEN_DEM_CAT | COP_PHA | BE_TONG_TRON")
    variant: Mapped[Optional[str]] = mapped_column(String(32), comment="dày (mm), mác (M250) hoặc mã vật liệu; trống: mọi trường hợp")
    material_id: Mapped[Optional[str]] = mapped_column(String(64), comment="mã danh mục; @VUA là vữa theo mác công trình")       # mã danh mục, "@VUA" = vữa theo mác công trình
    material_name: Mapped[Optional[str]] = mapped_column(String(255), comment="tên vật liệu")
    qty: Mapped[Optional[float]] = mapped_column(Float, comment="lượng trên 1 đơn vị công tác")
    qty_unit: Mapped[Optional[str]] = mapped_column(String(64), comment="ví dụ kg / m³")
    qty_min: Mapped[Optional[float]] = mapped_column(Float, comment="cận dưới khi hệ số là khoảng (đặc tả 30/10/2026 mục 3B)")
    qty_max: Mapped[Optional[float]] = mapped_column(Float, comment="cận trên khi hệ số là khoảng")
    muc_xac_nhan: Mapped[Optional[str]] = mapped_column(String(16), comment="nguon | tinh | kinh_nghiem")
    ngay_tra: Mapped[Optional[str]] = mapped_column(String(10), comment="ngày tra số, YYYY-MM-DD")
    norm_code: Mapped[Optional[str]] = mapped_column(String(64), comment="số hiệu bảng TT 38/2026/TT-BXD")         # số hiệu bảng TT 38/2026/TT-BXD
    source: Mapped[Optional[str]] = mapped_column(String(255), comment="nguồn")
    note: Mapped[Optional[str]] = mapped_column(Text, comment="ghi chú")

class MaterialNote(Base):
    """Ghi chú vật liệu phần thô trên bản vẽ (nạp từ data/rules/material_notes.csv): mẫu chữ đã bỏ dấu -> mã vật liệu.
    So nguyên từ (drawing/material_notes.py). kiem_chung: ban_ve_build = có ghi chú thật trên bản vẽ nhóm build khớp mẫu."""
    __tablename__ = "material_notes"
    __table_args__ = {"comment": "Chữ ghi trên bản vẽ → mã vật liệu trong danh mục (QU-20). So nguyên từ, không so chuỗi con."}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(32), unique=True, comment="mã quy tắc, ví dụ N207")
    pattern: Mapped[str] = mapped_column(String(255), comment="cụm từ chữ thường bỏ dấu, ví dụ: xi mang pcb40")
    material_id: Mapped[str] = mapped_column(String(32), index=True, comment="mã vật liệu phải có trong danh mục")
    ten: Mapped[Optional[str]] = mapped_column(String(255), comment="tên vật liệu")
    nguon: Mapped[Optional[str]] = mapped_column(String(32), comment="danh_muc | de_xuat")           # danh_muc | de_xuat
    kiem_chung: Mapped[Optional[str]] = mapped_column(String(32), comment="ban_ve_build | chua_kiem")      # ban_ve_build | chua_kiem
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, comment="ghi chú")


class DrawingConcept(Base):
    """Ký hiệu nhận dạng theo Quy ước bản vẽ v1.0 (nạp từ data/rules/concepts.csv): tên layer -> vai trò, tiền tố block cửa.
    id giữ thứ tự dòng: ký hiệu khớp đầu tiên thắng."""
    __tablename__ = "drawing_concepts"
    __table_args__ = (CheckConstraint("tin_hieu IN ('layer', 'block')", name="ck_drawing_concepts_signal"), {"comment": "Tên layer → vai trò (QU-08), tiền tố block → cửa đi, cửa sổ hoặc đối tượng khác (QU-14). Dòng khớp đầu tiên thắng."})
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ma: Mapped[str] = mapped_column(String(16), unique=True, comment="mã, ví dụ L50")
    khai_niem: Mapped[str] = mapped_column(String(64), comment="tên khái niệm, ví dụ Cửa")
    qu: Mapped[Optional[str]] = mapped_column(String(16), comment="điều khoản, ví dụ QU-08")
    tin_hieu: Mapped[str] = mapped_column(String(16), comment="layer | block")
    mau: Mapped[str] = mapped_column(String(128), comment="mẫu tên layer hoặc tiền tố block")
    vai_tro: Mapped[str] = mapped_column(String(16), comment="layer: WALL | OPENING | ANNOTATION | IGNORE | COLUMN | BEAM | SLAB | STAIR | LINTEL | FOUNDATION; block: door | window | ANNOTATION | IGNORE | …")
    rong_mm: Mapped[Optional[float]] = mapped_column(Float, comment="rộng mặc định, mm")
    cao_mm: Mapped[Optional[float]] = mapped_column(Float, comment="cao mặc định, mm")
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, comment="ghi chú")


class ConventionClause(Base):
    """23 điều khoản của Quy ước bản vẽ v1.0 (nạp từ data/rules/quy_uoc.csv); mức B bắt buộc, K khuyến nghị."""
    __tablename__ = "convention_clauses"
    __table_args__ = (CheckConstraint("muc IN ('B', 'K')", name="ck_convention_clauses_muc"), {"comment": "Các điều khoản QU của Quy ước bản vẽ đầu vào."})
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ma: Mapped[str] = mapped_column(String(16), unique=True, comment="mã, ví dụ QU-24")
    nhom: Mapped[str] = mapped_column(String(64), comment="nhóm điều khoản")
    dieu_khoan: Mapped[str] = mapped_column(Text, comment="nội dung")
    muc: Mapped[str] = mapped_column(String(1), comment="B (bắt buộc) | K (khuyến nghị)")
    cach_kiem: Mapped[Optional[str]] = mapped_column(Text, comment="cách kiểm")


# ============================== 2. Nguồn cung và giá ==============================

class Supplier(Base):
    """Nhà cung cấp, đại lý. Các cột thông tin chi tiết khớp với sheet "Dai ly" của mẫu thu thập đại lý."""
    __tablename__ = "suppliers"
    __table_args__ = (CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_suppliers_data_kind"),
                      CheckConstraint("price_public IS NULL OR price_public IN ('YES', 'NO', 'PARTIAL')",
                                      name="ck_suppliers_price_public"),
                      CheckConstraint("lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180", name="ck_suppliers_latlon"))
    supplier_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    province: Mapped[str] = mapped_column(String(64))
    # Chưa tra được tọa độ / chưa hỏi thời gian cung ứng thì để trống (không điền mặc định); tối ưu bỏ qua đại lý đó.
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    lead_time_days: Mapped[Optional[float]] = mapped_column(Float)
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")
    # --- Thông tin chi tiết đại lý (thu thập thủ công từ Google Maps và gọi điện)
    dealer_type: Mapped[Optional[str]] = mapped_column(String(64))       # nhà máy, nhà phân phối, đại lý cấp 1, cấp 2...
    brands: Mapped[Optional[str]] = mapped_column(Text)                  # hãng phân phối, ngăn cách bằng dấu ;
    address: Mapped[Optional[str]] = mapped_column(String(512))
    ward: Mapped[Optional[str]] = mapped_column(String(128))
    district: Mapped[Optional[str]] = mapped_column(String(128))
    maps_url: Mapped[Optional[str]] = mapped_column(String(1024))       # liên kết Google Maps, dùng để chỉ đường
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    zalo: Mapped[Optional[str]] = mapped_column(String(64))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(1024))
    facebook: Mapped[Optional[str]] = mapped_column(String(1024))
    tax_code: Mapped[Optional[str]] = mapped_column(String(32))
    opening_hours: Mapped[Optional[str]] = mapped_column(String(255))
    delivers: Mapped[Optional[bool]] = mapped_column(Boolean)
    delivery_radius_km: Mapped[Optional[float]] = mapped_column(Float)
    max_truck_ton: Mapped[Optional[float]] = mapped_column(Float)
    min_order: Mapped[Optional[str]] = mapped_column(String(255))
    vat_invoice: Mapped[Optional[bool]] = mapped_column(Boolean)
    payment: Mapped[Optional[str]] = mapped_column(String(255))
    price_public: Mapped[Optional[str]] = mapped_column(String(8))       # YES | NO | PARTIAL
    price_page_url: Mapped[Optional[str]] = mapped_column(String(1024))
    verified: Mapped[Optional[bool]] = mapped_column(Boolean)            # đã gọi điện xác minh
    collected_at: Mapped[Optional[date]] = mapped_column(Date)
    collected_by: Mapped[Optional[str]] = mapped_column(String(128))
    source: Mapped[Optional[str]] = mapped_column(String(1024))
    note: Mapped[Optional[str]] = mapped_column(Text)
    # Nhà cung cấp trong công bố giá (CBG-...) là cùng công ty với đại lý này: dùng vị trí, thời gian cung ứng của đại lý.
    linked_supplier_id: Mapped[Optional[str]] = mapped_column(ForeignKey("suppliers.supplier_id", ondelete="SET NULL"))


class SupplierMaterial(Base):
    """Giá hiện hành của một vật liệu tại một nhà cung cấp, kèm liên kết trang sản phẩm."""
    __tablename__ = "supplier_materials"
    __table_args__ = (UniqueConstraint("supplier_id", "material_id"),
                      CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_supplier_materials_data_kind"),
                      CheckConstraint("price_level IS NULL OR price_level IN ('DEALER', 'QUOTE')",
                                      name="ck_supplier_materials_price_level"),
                      CheckConstraint("base_price IS NULL OR (base_price > 0 AND price_level IS NOT NULL "
                                      "AND price_date IS NOT NULL)", name="ck_supplier_materials_price_complete"),
                      CheckConstraint(f"vat_included IN {YES_NO} AND transport_included IN {YES_NO}",
                                      name="ck_supplier_materials_basis"))
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.supplier_id", ondelete="CASCADE"))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id", ondelete="CASCADE"))
    # Đại lý không công khai giá thì base_price để trống; có giá thì bắt buộc có mức giá và ngày của giá.
    base_price: Mapped[Optional[float]] = mapped_column(Float)
    product_url: Mapped[Optional[str]] = mapped_column(String(1024))
    collected_at: Mapped[date] = mapped_column(Date)
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")
    dealer_product_name: Mapped[Optional[str]] = mapped_column(String(255))   # tên sản phẩm tại đại lý
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    sale_unit: Mapped[Optional[str]] = mapped_column(String(32))              # đơn vị bán tại đại lý
    unit_conversion: Mapped[Optional[float]] = mapped_column(Float)           # 1 đơn vị bán = ? đơn vị tính chuẩn
    price_level: Mapped[Optional[str]] = mapped_column(String(16))            # DEALER | QUOTE
    price_date: Mapped[Optional[date]] = mapped_column(Date)
    vat_included: Mapped[str] = mapped_column(String(8), default="UNKNOWN", server_default="UNKNOWN")
    transport_included: Mapped[str] = mapped_column(String(8), default="UNKNOWN", server_default="UNKNOWN")
    in_stock: Mapped[Optional[bool]] = mapped_column(Boolean)
    note: Mapped[Optional[str]] = mapped_column(Text)
    quote_reference: Mapped[Optional[str]] = mapped_column(String(1024))     # số/ngày báo giá, người báo, file lưu
    valid_until: Mapped[Optional[date]] = mapped_column(Date)                 # báo giá hết hiệu lực sau ngày này
    lead_time_days: Mapped[Optional[float]] = mapped_column(Float)            # trống: lấy thời gian cung ứng của đại lý


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_vehicles_data_kind"),)
    vehicle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    payload_ton: Mapped[float] = mapped_column(Float)
    base_fee: Mapped[float] = mapped_column(Float)
    fee_per_km: Mapped[float] = mapped_column(Float)
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")


class PriceRecord(Base):
    """Lịch sử giá: dữ liệu huấn luyện cho mô hình XGBoost."""
    __tablename__ = "price_records"
    __table_args__ = (Index("ix_price_records_lookup", "material_id", "supplier_id", "date"),
                      # chống nạp trùng: cùng vật liệu, nhà cung cấp, ngày, khối lượng và nguồn
                      Index("uq_price_records_dedup", "material_id", text("COALESCE(supplier_id, '')"), "date",
                            "quantity", "source", unique=True),
                      CheckConstraint("unit_price > 0", name="ck_price_records_positive"),
                      CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_price_records_data_kind"),
                      CheckConstraint(f"price_level IN {PRICE_LEVELS_OBSERVED}", name="ck_price_records_price_level"),
                      CheckConstraint("supplier_id IS NOT NULL OR price_level = 'BULLETIN'",
                                      name="ck_price_records_supplier"),
                      CheckConstraint(f"vat_included IN {YES_NO} AND transport_included IN {YES_NO}",
                                      name="ck_price_records_basis"))
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date)
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.material_id"))
    # công bố giá của Sở Xây dựng không gắn với đại lý nào nên supplier_id có thể trống
    supplier_id: Mapped[Optional[str]] = mapped_column(ForeignKey("suppliers.supplier_id"))
    province: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))
    unit_price: Mapped[float] = mapped_column(Float)
    vat_included: Mapped[str] = mapped_column(String(8), default="UNKNOWN", server_default="UNKNOWN")        # YES | NO | UNKNOWN
    transport_included: Mapped[str] = mapped_column(String(8), default="UNKNOWN", server_default="UNKNOWN")
    source: Mapped[str] = mapped_column(String(1024), default="", server_default="")
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")
    price_level: Mapped[str] = mapped_column(String(16), default="DEALER", server_default="DEALER")


class LaborRate(Base):
    """Đơn giá nhân công do địa phương công bố."""
    __tablename__ = "labor_rates"
    __table_args__ = (CheckConstraint(f"data_kind IN {DATA_KINDS}", name="ck_labor_rates_data_kind"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    province: Mapped[str] = mapped_column(String(64), index=True)
    grade: Mapped[str] = mapped_column(String(32))                # bậc thợ, ví dụ "3,5/7"
    rate_per_day: Mapped[float] = mapped_column(Float)
    valid_from: Mapped[Optional[date]] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(1024), default="", server_default="")
    data_kind: Mapped[str] = mapped_column(String(16), default="ACTUAL", server_default="ACTUAL")


# ============================== 3. Người dùng và dự án ==============================

class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),)
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), default="", server_default="")
    password_hash: Mapped[str] = mapped_column(String(255))     # chỉ lưu dạng băm, không lưu mật khẩu nguyên văn
    role: Mapped[str] = mapped_column(String(16), default="user", server_default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    project_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(512), default="", server_default="")
    site_lat: Mapped[Optional[float]] = mapped_column(Float)
    site_lon: Mapped[Optional[float]] = mapped_column(Float)
    floor_height_mm: Mapped[Optional[float]] = mapped_column(Float)
    # kích thước cửa của dự án: dùng khi block cửa không ghi kích thước, trống thì lỗ mở chưa được trừ (Quy ước B7)
    door_width_mm: Mapped[Optional[float]] = mapped_column(Float)
    door_height_mm: Mapped[Optional[float]] = mapped_column(Float)
    window_width_mm: Mapped[Optional[float]] = mapped_column(Float)
    window_height_mm: Mapped[Optional[float]] = mapped_column(Float)
    budget: Mapped[Optional[float]] = mapped_column(Float)
    deadline_days: Mapped[Optional[float]] = mapped_column(Float)
    max_vehicle_ton: Mapped[Optional[float]] = mapped_column(Float)
    excluded_materials: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProjectFile(Base):
    __tablename__ = "project_files"
    file_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(16))           # dwg | dxf | xlsx
    stored_path: Mapped[str] = mapped_column(String(1024))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TakeoffResultRow(Base):
    """Kết quả đo bóc của một dự án và trạng thái xác nhận của người dùng."""
    __tablename__ = "takeoff_results"
    takeoff_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_files.file_id", ondelete="SET NULL"))
    result: Mapped[dict] = mapped_column(JSONB)                   # nội dung TakeoffResult
    layer_overrides: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OptimizationRun(Base):
    """Một lần chạy tối ưu: cấu hình, tập phương án Pareto và phương án người dùng chọn."""
    __tablename__ = "optimization_runs"
    run_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    takeoff_id: Mapped[Optional[int]] = mapped_column(ForeignKey("takeoff_results.takeoff_id", ondelete="SET NULL"))
    model_version: Mapped[Optional[str]] = mapped_column(ForeignKey("model_versions.version", ondelete="SET NULL"))
    method: Mapped[str] = mapped_column(String(16))               # nsga2 | brute
    config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    solutions: Mapped[list] = mapped_column(JSONB)                # danh sách Solution
    chosen_index: Mapped[Optional[int]] = mapped_column(Integer)
    # --- Truy vết để chạy lại cho cùng kết quả
    price_snapshot_date: Mapped[Optional[date]] = mapped_column(Date)   # ngày của bảng giá đã dùng
    llm_model: Mapped[Optional[str]] = mapped_column(String(64))       # mã mô hình ngôn ngữ; trống khi chạy luồng cố định
    tool_calls: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")         # [{tool, args, status}]
    excluded_materials: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")  # [{material_id, reason}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================== 4. Vận hành hệ thống ==============================

class ModelVersion(Base):
    __tablename__ = "model_versions"
    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    target: Mapped[str] = mapped_column(String(32))               # material_price | transport_cost
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data_rows: Mapped[int] = mapped_column(Integer)
    contains_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    metrics: Mapped[dict] = mapped_column(JSONB)                  # MAE, RMSE, R2, MAPE của từng mô hình
    file_path: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class AuditLog(Base):
    """Nhật ký thao tác quản trị và các lần thu thập giá."""
    __tablename__ = "audit_logs"
    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Tên tiếng Việt của 26 bảng, hiện trên trang quản trị /co-so-du-lieu (tên bảng trong SQL giữ nguyên).
TITLES = {
    "material_groups": "Nhóm vật liệu", "material_families": "Họ vật liệu", "materials": "Vật liệu",
    "wall_systems": "Phương án tường", "material_relations": "Quan hệ vật liệu", "material_aliases": "Tên gọi khác của vật liệu",
    "standards": "Tiêu chuẩn", "material_standards": "Tiêu chuẩn của vật liệu",
    "material_rules": "Vật liệu tường", "material_notes": "Ghi chú vật liệu phần thô", "room_rules": "Loại phòng",
    "rough_norms": "Định mức phần thô", "drawing_concepts": "Ký hiệu layer, block", "convention_clauses": "Điều khoản quy ước",
    "suppliers": "Đại lý, nhà cung cấp", "supplier_materials": "Giá đại lý", "vehicles": "Phương tiện vận chuyển",
    "price_records": "Lịch sử giá", "labor_rates": "Đơn giá nhân công",
    "users": "Người dùng", "projects": "Dự án", "project_files": "File của dự án", "takeoff_results": "Kết quả bóc tách",
    "optimization_runs": "Lần tối ưu", "model_versions": "Phiên bản mô hình", "audit_logs": "Nhật ký thao tác",
}
for _name, _title in TITLES.items():
    Base.metadata.tables[_name].info["title"] = _title
