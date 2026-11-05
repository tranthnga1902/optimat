# Tổng hợp cơ sở dữ liệu và định nghĩa dữ liệu đầu vào

**Bản kiểm kê lịch sử.** Hiện hành là [CSDL 20 bảng](schema/CSDL_20_BANG.md). Các tên đã gộp được giữ bằng view; số bảng và cách khởi tạo bên dưới không còn là hợp đồng triển khai.

Cập nhật 29/10/2026. Nguồn: `src/optimat/db/models.py` (lược đồ), `data/` (số liệu), `src/optimat/schemas.py`,
`src/optimat/rough/models.py`, `src/optimat/drawing/ingest.py`, `data/rules/quy_uoc.csv`.
Quy trình sửa và kiểm soát dữ liệu: xem `QUY_TRINH_DU_LIEU.md`.

## 1. Tổng quan

- PostgreSQL, **26 bảng, 4 cụm**. Lược đồ gốc là `db/models.py`; `sql/01`–`05` sinh tự động, không sửa tay.
- Không đặt `DATABASE_URL` thì hệ thống đọc CSV trong `data/catalog`, `data/rules` (chỉ để kiểm thử).
- Mọi bảng số liệu có `data_kind`: `ACTUAL` (có nguồn thật) | `SAMPLE` (mẫu) | `SYNTHETIC` (mô phỏng). Chỉ `ACTUAL` dùng để báo cáo.
- Ô chưa có nguồn để trống, không điền mặc định. Thiếu số thì công tác/phương án bị loại và có cảnh báo.
- Một bộ mã xuyên suốt: vật liệu `GN01`, `AAC01`…; phương án tường `W-<mã vật liệu>-<lớp dày>` (ví dụ `W-GN01-220`).

## 2. Các bảng và số liệu hiện có

Số dòng là của file CSV nguồn trong `data/` (database nạp từ các file này bằng `scripts/init_db.py`).

### 2.1. Danh mục vật liệu và quy tắc (14 bảng)

| Bảng | Tên | Khóa | Nội dung chính | Số dòng | Nguồn |
|---|---|---|---|---|---|
| `material_groups` | Nhóm vật liệu | `group_id` | 5 nhóm: phan_tho, be_tong_cot_thep, ket_cau_thep_bao_che, hoan_thien, khac_phap_ly | 5 | materials_master.xlsx |
| `material_families` | Họ vật liệu | `family_id` | CLAY_SOLID, CLAY_HOLLOW, CMU_SOLID, CMU_HOLLOW, CLC, AAC, ALC_PANEL, EPS_PANEL, CEMBOARD, GYPSUM; `is_wall` | 10 | materials_master.xlsx |
| `materials` | Vật liệu | `material_id` | nhóm, họ, đơn vị tính/mua, quy đổi, kích thước viên, λ, khối lượng, hao hụt, `tier` (1 tối ưu sâu, 2 tối ưu nguồn cung, 3 tham khảo), `price_priority` | 93 (tier 1: 16, tier 2: 32, tier 3: 45) | materials_master.xlsx |
| `wall_systems` | Phương án tường | `wall_system_id` | vật liệu × chiều dày; `detect_class` (110/150/220/330), `role`, định mức viên/m³, vữa m³/m³, công/m³, `r0_reference` | 20 | materials_master.xlsx |
| `material_relations` | Quan hệ vật liệu | `id` | REQUIRES (đi kèm bắt buộc) / COMPOSED_OF (cấp phối) | 13 | materials_master.xlsx |
| `material_aliases` | Tên gọi khác | `id` | tên trên bản vẽ/dự toán → mã vật liệu | 277 | materials_master.xlsx |
| `standards` | Tiêu chuẩn | `standard_id` | TCVN, QCVN, thông tư; hiệu lực | **0** (123 bản ghi chờ nạp) | `init_db.py --standards` |
| `material_standards` | Tiêu chuẩn của vật liệu | (material_id, standard_id) | bảng nối | — | |
| `material_rules` | Vật liệu tường | `rule_id` | tín hiệu text/hatch/layer/block → họ hoặc mã vật liệu; `priority` | 27 | `data/rules/material_rules.csv` |
| `material_notes` | Ghi chú vật liệu phần thô | `rule_id` | cụm chữ bỏ dấu → mã vật liệu (so nguyên từ, QU-20) | 206 | `data/rules/material_notes.csv` |
| `room_rules` | Loại phòng | `rule_id` | tên phòng (regex) → WET / BALCONY (tính chống thấm) | 7 | `data/rules/room_rules.csv` |
| `rough_norms` | Định mức phần thô | `id` | lượng vật liệu / 1 đơn vị công tác, cấp phối bê tông (TT 38/2026/TT-BXD) | 22 | `data/rules/dinh_muc_phan_tho.csv` |
| `drawing_concepts` | Ký hiệu layer, block | `ma` | mẫu tên layer/tiền tố block → vai trò (QU-08, QU-14) | 112 | `data/rules/concepts.csv` |
| `convention_clauses` | Điều khoản quy ước | `ma` | 23 điều khoản QU, mức B/K | 23 | `data/rules/quy_uoc.csv` |

### 2.2. Nguồn cung và giá (5 bảng)

| Bảng | Tên | Khóa | Nội dung chính | Số dòng | Ghi chú |
|---|---|---|---|---|---|
| `suppliers` | Đại lý, nhà cung cấp | `supplier_id` | tên, tỉnh, tọa độ, thời gian cung ứng, liên hệ, giao hàng, tải xe tối đa, hóa đơn VAT | 2 843 (Hà Nội 1 267, Hải Phòng 155, Bắc Ninh 125…) | `import_dealers.py`, `import_price_bulletin.py` |
| `supplier_materials` | Giá đại lý | `id`, UNIQUE(supplier, material) | giá hiện hành, `price_level` DEALER/QUOTE, `price_date`, VAT, vận chuyển, còn hàng | **0** | có giá thì bắt buộc có mức giá và ngày |
| `vehicles` | Phương tiện vận chuyển | `vehicle_id` | tải trọng, phí cố định, phí/km | **0** | |
| `price_records` | Lịch sử giá (huấn luyện XGBoost) | `id` | ngày, vật liệu, đại lý (trống nếu BULLETIN), tỉnh, khối lượng, đơn giá > 0, `price_level` DEALER/QUOTE/BULLETIN | công bố giá Sở XD 02.01/2026: ~6 970 dòng duyệt; mẫu `prices_sample.csv`: 1 248 dòng SYNTHETIC | chống nạp trùng theo (vật liệu, đại lý, ngày, khối lượng, nguồn) |
| `labor_rates` | Đơn giá nhân công | `id` | tỉnh, bậc thợ, đơn giá/ngày, hiệu lực | **0** | |

### 2.3. Người dùng và dự án (5 bảng)

| Bảng | Tên | Nội dung chính |
|---|---|---|
| `users` | Người dùng | email (duy nhất), `password_hash` (chỉ lưu băm), `role` admin/user |
| `projects` | Dự án | địa chỉ, tọa độ công trường, **chiều cao tầng, kích thước cửa đi/cửa sổ**, ngân sách, hạn, tải xe tối đa, vật liệu loại trừ |
| `project_files` | File của dự án | tên file, loại dwg/dxf/xlsx, đường dẫn lưu |
| `takeoff_results` | Kết quả bóc tách | JSON `TakeoffResult`, layer sửa tay, thời điểm xác nhận |
| `optimization_runs` | Lần tối ưu | phương pháp nsga2/brute, cấu hình, tập Pareto, phương án chọn, ngày bảng giá, mô hình LLM, nhật ký công cụ |

### 2.4. Vận hành hệ thống (2 bảng)

| Bảng | Tên | Nội dung chính |
|---|---|---|
| `model_versions` | Phiên bản mô hình | mục tiêu (material_price/transport_cost), số dòng huấn luyện, có dữ liệu mô phỏng không, MAE/RMSE/R²/MAPE, đang dùng |
| `audit_logs` | Nhật ký thao tác | người dùng, hành động, chi tiết JSON |

### 2.5. Quy tắc chỉ có ở file (chưa thành bảng)

`data/rules/`: `bang_thep.csv` (18), `cong_bo_gia.csv` (26, ghép tên công bố giá → mã), `do_tin_cay.csv` (9),
`ho_tro_cau_kien.csv` (21), `ky_hieu_cau_kien.csv` (11), `loai_ban_ve.csv` (15), `loai_mai.csv` (2),
`nguong_nhan_dien.csv` (10, ngưỡng nhận diện), `thep_kg_m.csv` (12, kg/m theo đường kính).

### 2.6. Quan hệ chính

```
material_groups ─< materials >─ material_families
materials ─< wall_systems (material_id, mortar_material_id)
materials ─< material_relations, material_aliases, material_standards >─ standards
suppliers ─< supplier_materials >─ materials
suppliers ─< price_records >─ materials
users ─< projects ─< project_files
projects ─< takeoff_results ─< optimization_runs >─ model_versions
```

## 3. Định nghĩa dữ liệu đầu vào

Hệ thống nhận 3 loại đầu vào từ người dùng: **bản vẽ**, **thông số dự án/công trình**, **ràng buộc tối ưu**.
Số liệu danh mục và giá (mục 2) do quản trị viên nạp, không phải đầu vào mỗi lần chạy.

### 3.1. Bản vẽ (bắt buộc)

**Kiểm tra khi tải lên** (`drawing/ingest.py`, API `/api/ingest`):

| Điều kiện | Giá trị |
|---|---|
| Đuôi file | `.dxf`, `.dwg` (không nhận PDF, ảnh, DWF) |
| Nhận dạng | theo nội dung file, không tin đuôi; DWG chuyển sang DXF bằng ODA File Converter |
| Dung lượng | ≤ 50 MB (`config.MAX_UPLOAD_MB`), không rỗng |
| Phiên bản DWG | R12 → 2018 (AC1009 … AC1032) |
| Kích thước hình | 1 m – 1 000 m (ngoài khoảng: nghi sai đơn vị/tỷ lệ) |
| Đối tượng đọc | INSERT, LINE, LWPOLYLINE, POLYLINE, ARC, CIRCLE, HATCH, TEXT, MTEXT, DIMENSION, ATTDEF, VIEWPORT; loại khác đếm và cảnh báo |
| Lỗi chặn | model space rỗng, chuyển đổi thất bại, file hỏng |
| Lưu trữ | theo SHA-256 (trùng nội dung không lưu lại), cùng tên khác nội dung thì tăng phiên bản |

**Quy ước bản vẽ v1.0** (23 điều khoản, `data/rules/quy_uoc.csv`; B = bắt buộc, K = khuyến nghị):

| Nhóm | Bắt buộc (B) | Khuyến nghị (K) |
|---|---|---|
| Định dạng, đơn vị | QU-01 DWG/DXF; QU-02 model space, 1:1, mm; QU-03 chữ Unicode hoặc TCVN3 | |
| Tổ chức mặt bằng | QU-04 tiêu đề "MẶT BẰNG …" dưới hình; QU-05 tên không trùng, mái ghi chữ MÁI | QU-06 cao độ sàn (+3.30); QU-07 chung hệ trục |
| Layer | | QU-08 tên layer TUONG/WALL/XAY, CUA/DOOR/WINDOW, TRUC/GRID, DIM, NOI THAT |
| Tường | QU-09 hai nét song song: 85–135 (lớp 110), 136–175 (150), 176–260 (220), 280–370 (330) mm; QU-11 không nằm trong block có tên; QU-12 tường thẳng | QU-10 hatch giữa hai nét; QU-13 tường bao khép kín |
| Cửa | | QU-14 cung cánh cửa / nét kính / block D, CD, S, CS, W; QU-15 bảng thống kê cửa |
| Bộ phận khác | | QU-16 cột; QU-17 cầu thang; QU-18 ô trống sàn; QU-19 tên phòng; QU-20 ghi chú vật liệu |
| Kết cấu (khi có) | QU-21 cùng hệ trục, tỷ lệ với kiến trúc | QU-22 tên + tiết diện cấu kiện; QU-23 bảng thép là chữ CAD |

Bản vẽ kết cấu là file thứ hai, không bắt buộc (`structural_file` của `/api/takeoff/rough/auto`, kèm `structural_scale`).

### 3.2. Thông số dự án (bảng `projects`, truyền qua `project_id`)

| Trường | Đơn vị | Dùng cho | Trống thì |
|---|---|---|---|
| `floor_height_mm` | mm | diện tích tường | lấy từ cao độ sàn bản vẽ; vẫn không có → không tính diện tích (`groups` rỗng) |
| `door_width_mm`, `door_height_mm` | mm | trừ lỗ cửa đi khi block không ghi kích thước | lỗ mở đó không trừ, cảnh báo (B7) |
| `window_width_mm`, `window_height_mm` | mm | trừ lỗ cửa sổ | như trên |
| `site_lat`, `site_lon` | độ | khoảng cách vận chuyển | |
| `budget` | đồng | ràng buộc tối ưu | không ràng buộc |
| `deadline_days` | ngày | ràng buộc thời gian cung ứng | không ràng buộc |
| `max_vehicle_ton` | tấn | giới hạn xe vào công trường | không ràng buộc |
| `excluded_materials` | danh sách mã/họ | loại vật liệu khỏi tối ưu | |

Thứ tự ưu tiên kích thước cửa: thuộc tính block → quy tắc block → thông số dự án.
Chiều cao tầng: nhập tay → cao độ tầng trên − tầng này → dự án.

### 3.3. Thông số công trình phần thô (`ProjectParams`, `rough/models.py`)

Nhập một lần (JSON `params` / `rough_params`). Mọi trường có thể trống; công tác cần trường đó không ra số và có cảnh báo.

| Nhóm | Trường |
|---|---|
| Bê tông | `concrete_supply` (ready_mix / site_mix), `concrete_grade` (M250…), `lean_concrete_grade` |
| Vữa | `masonry_mortar_grade`, `plaster_mortar_grade`, `screed_mortar_grade` |
| Chiều dày | `plaster_thickness_mm`, `screed_thickness_mm`, `slab_thickness_mm`, `stair_slab_thickness_mm` |
| Dầm, lanh tô | `beam_depth_mm` (gồm sàn), `beam_width_mm`, `lintel_height_mm`, `lintel_bearing_mm` |
| Chống thấm | `waterproof_upturn_mm`, `waterproof_material_id` (CT01/CT02/CT03) |
| Thép | `steel_kg_per_m3` {LANH_TO, COT, DAM, SAN, CAU_THANG, MONG…}, `steel_schedule_t` (tấn theo bảng thống kê, thắng hàm lượng) |
| Móng | `foundations[]`: tên, số lượng, đơn/băng, dài × rộng × cao hoặc `tiers[]` hoặc `volume_m3`, lót, cao độ đáy, cổ móng, vị trí |
| Đào đắp | `natural_ground_level_mm`, `excavation_margin_mm`, `excavation_slope` |
| Mái | `roofs[]`: be_tong (diện tích, dày) / khung (chưa hỗ trợ) |
| Nền | `ground_layers[]`: NEN_DEM_CAT / BE_TONG_LOT + chiều dày, từ dưới lên |

Ví dụ đầy đủ: `data/ground_truth/du_toan/46_thong_so.json`.

### 3.4. Ràng buộc tối ưu (`Constraints`, API `/api/optimize`)

`site_lat`, `site_lon`, `budget`, `deadline_days`, `max_vehicle_ton`, `excluded_materials`, `keep_design_material`
(giữ phương án thiết kế, chỉ tối ưu đại lý và xe), `order_date` (YYYY-MM-DD, mặc định hôm nay),
`province` (tra `labor_rates`). Có thể nhập bằng câu chữ qua `/api/constraints/parse`.

### 3.5. Thao tác của người dùng trên trang kiểm tra (`/do-boc`)

`layer_overrides` (gán lại vai trò layer), `length_rule` (`tim` theo trục tim | `thong_thuy`), loại bỏ/sửa tường, vật liệu,
cửa, chiều cao → gửi `/api/takeoff/confirm` (công thức chốt duy nhất), lưu vào `takeoff_results` khi có `project_id`.

## 4. Tồn tại cần xử lý

1. `supplier_materials`, `vehicles`, `labor_rates` chưa có dòng nào: tối ưu chi phí vận chuyển và nhân công chưa có số thật.
2. `price_records` thật mới có công bố giá Sở XD (BULLETIN, không gắn đại lý); dữ liệu huấn luyện còn lại là SYNTHETIC.
3. `wall_systems` chưa có phương án lớp 330 (cảnh báo của `check_data.py`).
4. Đáp án đo tay `data/ground_truth/walls.csv` mới có 2 dòng, `index.csv` 1 bản vẽ.
