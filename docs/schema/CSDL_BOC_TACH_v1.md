# CSDL bóc tách: cột, khóa, ràng buộc · v1 (đề xuất chốt 04/11/2026)

**Đã thay bằng [CSDL 20 bảng](CSDL_20_BANG.md).** Thiết kế 45 bảng bên dưới chỉ giữ để đối chiếu; không áp DDL đề xuất cũ lên hệ thống 20 bảng.

> Bản chính thức, đã chạy thử: `CSDL_OPTIMAT_20261104.docx` (toàn bộ 45 bảng), `ddl_de_xuat_20261104.sql` và `ddl_de_xuat_20261104_tests.sql` (41/41 đạt). Khi hai nơi khác nhau, theo DDL.

Chuỗi dữ liệu: **phiên bản hồ sơ → hình vẽ → đối tượng CAD làm bằng chứng → cấu kiện → số đo (nhiều ứng viên) → lần tính → khối lượng → phương án vật liệu → nhu cầu vật liệu**.

Tài liệu này mới là đặc tả. Chưa sửa `db/models.py`, chưa sinh `sql/04_upgrade.sql`, chưa chạy migration.

## 0. Quy ước chung

- Khóa chính `BIGINT GENERATED ALWAYS AS IDENTITY`, tên `<bảng số ít>_id`. Riêng các bảng danh mục giữ khóa chuỗi sẵn có (`materials.material_id`, `wall_systems.wall_system_id`).
- Thời gian dùng `TIMESTAMPTZ DEFAULT now()`.
- Mọi bảng có `project_id` để lọc theo chủ sở hữu (API đã kiểm `projects.user_id`). Chỉ khóa ngoại trực tiếp mới được `ON DELETE CASCADE` từ `projects`.
- **Đơn vị lưu cố định theo loại đại lượng:** dài `mm`, diện tích `m2`, thể tích `m3`, khối lượng `kg`, số lượng `cai`. Giá trị gốc trên bản vẽ (`"a = 15"`, `"4.000"`) lưu riêng ở bằng chứng. Tên cột số đo không mang đơn vị; đơn vị nằm trong cột `unit` và có CHECK theo `quantity_kind`.
- **Trạng thái dữ liệu dùng lại A/B/C/D** của `rough/status.py`: A đọc trực tiếp, B suy luận, C người dùng nhập hoặc hệ số tham khảo, D thiếu số. Không đặt bộ trạng thái mới.
- **Không cho chép đè.** Sửa một số đo là thêm dòng ứng viên mới, rồi đổi `selected` (mục 2.3).
- `compute_rough` vẫn là **công thức duy nhất**. Các bảng ở mục 4 chỉ lưu kết quả và đầu vào đã dùng, không bao giờ tự tính lại.

## 1. Hồ sơ và bản vẽ

**Không sửa `project_files`.** Phiên bản, sha256, vai trò, định dạng đã có trong `project_document_revisions` (khóa `revision_id`). Mọi bảng dưới đây khóa vào `revision_id`.

### 1.1 `drawing_views`: từng hình trong một phiên bản file

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| view_id | bigint PK | | |
| project_id | int FK projects CASCADE | không | |
| revision_id | bigint FK project_document_revisions CASCADE | không | |
| view_key | varchar(64) | không | khóa ổn định trong lần đọc, ví dụ `plan:3`, `section:A-A` |
| kind | varchar(24) | không | CHECK in (`mat_bang`, `mat_cat`, `mat_dung`, `chi_tiet`, `bang_thong_ke`, `toan_bo`, `khac`). Mã chi tiết theo `data/rules/loai_ban_ve.csv` |
| sheet_type | varchar(64) | có | mã loại bản vẽ trong `loai_ban_ve.csv` |
| title_raw | text | có | tiêu đề nguyên văn (sau khi đổi mã TCVN3/VNI) |
| title | varchar(255) | có | tiêu đề đã chuẩn hóa |
| bbox_wcs | jsonb | không | `[xmin, ymin, xmax, ymax]` theo mm WCS |
| scale_display | numeric(10,3) | có | mẫu số tỷ lệ in, ví dụ 100 cho 1:100 |
| scale_measure | numeric(12,6) | có | hệ số đổi đơn vị vẽ ra mm của hình (`dimensions.py`) |
| scale_source | char(1) | có | A/B/C/D |
| scope | varchar(16) | không | CHECK in (`tinh`, `tham_khao`, `ban_sao`, `chua_xac_nhan`), mặc định `chua_xac_nhan` |
| parser_version | varchar(32) | không | phiên bản bộ đọc, để đọc lại có đối chiếu |
| created_at | timestamptz | không | |

UNIQUE (`revision_id`, `view_key`, `parser_version`) · INDEX (`project_id`)

### 1.2 `building_levels`: tầng của công trình

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| level_id | bigint PK | | |
| project_id | int FK CASCADE | không | |
| profile_version | int | không | phiên bản hồ sơ công trình lúc xác định (`project_profile_revisions.version`) |
| code | varchar(32) | không | `TRET`, `LUNG`, `L1`…`L4`, `ST`, `MAI` |
| name | varchar(128) | không | |
| seq | smallint | không | thứ tự từ dưới lên, CHECK 0–10 (giới hạn nhà 5 tầng cộng lửng, tum, mái) |
| elevation_mm | numeric(10,1) | có | cao độ sàn hoàn thiện |
| height_mm | numeric(10,1) | có | CHECK > 0 và ≤ 10000 |
| height_status | char(1) | không | A/B/C/D. D khi `height_mm` null |
| height_evidence_id | bigint FK evidence_sources SET NULL | có | |

UNIQUE (`project_id`, `profile_version`, `code`) · CHECK (`height_mm IS NOT NULL OR height_status = 'D'`)

Bảng nối `view_levels(view_id, level_id)`, PK kép: một mặt cắt có thể thuộc nhiều tầng.

### 1.3 `drawing_entities`: chỉ những đối tượng CAD được dùng làm bằng chứng

Không lưu toàn bộ file: riêng `banve1` đã có hơn 231.000 nét. File gốc trong `project_document_revisions` không bao giờ đổi, nên khi cần có thể đọc lại đúng đối tượng theo `handle`.

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| entity_id | bigint PK | | |
| revision_id | bigint FK CASCADE | không | |
| view_id | bigint FK drawing_views SET NULL | có | |
| handle | varchar(32) | không | handle DXF; với đối tượng trong block là đường dẫn `INSERT/…/handle` |
| block_path | text | có | chuỗi tên block, ví dụ `MBTRET NHON/*U12` |
| dxftype | varchar(24) | không | LINE, LWPOLYLINE, TEXT, MTEXT, DIMENSION, INSERT, HATCH… |
| layer | varchar(255) | không | |
| geom_wcs | jsonb | có | hình học đã đổi sang WCS (mm), gọn: điểm, đoạn, bbox |
| text_raw | text | có | chữ nguyên văn |
| text_norm | text | có | chữ sau khi đổi mã và giãn viết tắt |
| attribs | jsonb | không | thuộc tính block hoặc DIMENSION, mặc định `{}` |

UNIQUE (`revision_id`, `handle`) · INDEX (`view_id`), (`layer`)

## 2. Cấu kiện và số đo

### 2.1 `building_elements`: một cấu kiện thực, gặp ở bao nhiêu hình vẫn là một dòng

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| element_id | bigint PK | | |
| project_id | int FK CASCADE | không | |
| level_id | bigint FK building_levels SET NULL | có | |
| code | varchar(32) | không | mã trên bản vẽ hoặc mã hệ thống: W5, C1, D2, M1, O3 |
| kind | varchar(24) | không | CHECK in (`tuong`, `cot`, `dam`, `san`, `mong`, `giang`, `lanh_to`, `thang`, `mai`, `lo_mo`, `nen`, `khac`) |
| subtype | varchar(32) | có | ví dụ `bao_che`, `ngan`, `cua_di`, `cua_so`, `dam_chinh` |
| geom_norm | jsonb | có | hình học chuẩn hóa (trục tim, mm, hệ tọa độ công trình) |
| design_material_text | text | có | ghi chú vật liệu theo thiết kế, nguyên văn. **Không có cột `material_id` ở bảng này** |
| recog_status | varchar(16) | không | CHECK in (`tu_dong`, `nguoi_sua`, `nguoi_them`, `da_loai`) |
| recog_confidence | numeric(4,3) | có | CHECK 0–1 |
| removed_reason | text | có | bắt buộc khi `recog_status = 'da_loai'` (CHECK) |
| first_seen_takeoff_id | bigint FK takeoff_results SET NULL | có | |
| created_at, updated_at | timestamptz | không | |

UNIQUE (`project_id`, `level_id`, `kind`, `code`) · INDEX (`project_id`, `kind`)

### 2.2 `element_occurrences`: các lần cấu kiện xuất hiện trên hình

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| occurrence_id | bigint PK | | |
| element_id | bigint FK CASCADE | không | |
| view_id | bigint FK drawing_views CASCADE | không | |
| role | varchar(16) | không | CHECK in (`hinh_chinh`, `mat_cat`, `chi_tiet`, `bang_thong_ke`, `ky_hieu`) |
| entity_ids | bigint[] | không | các `drawing_entities` tạo nên lần xuất hiện này |
| local_geom | jsonb | có | hình học trong hệ tọa độ của hình |

UNIQUE (`element_id`, `view_id`, `role`)

### 2.3 `element_measurements`: số đo, giữ mọi giá trị ứng viên

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| measurement_id | bigint PK | | |
| element_id | bigint FK CASCADE | không | |
| quantity_kind | varchar(24) | không | CHECK in (`dai`, `rong`, `cao`, `day`, `tiet_dien_b`, `tiet_dien_h`, `dien_tich`, `the_tich`, `so_luong`, `cao_do`, `ham_luong_thep`, `duong_kinh`) |
| value | numeric(14,4) | có | null khi thiếu (D) |
| unit | varchar(8) | không | CHECK khớp `quantity_kind`: mm / m2 / m3 / cai / kg_m3 |
| method | varchar(24) | không | CHECK in (`hinh_hoc`, `dimension`, `ghi_chu`, `bang_thong_ke`, `mat_cat`, `quy_tac`, `nguoi_nhap`, `thong_so_du_an`, `suy_luan`) |
| status | char(1) | không | A/B/C/D. CHECK (`value IS NOT NULL OR status = 'D'`) |
| selected | boolean | không | đúng **một** ứng viên được chọn cho mỗi (`element_id`, `quantity_kind`, `variant`) |
| variant | varchar(32) | không | mặc định `''`; tách nhiều số cùng loại, ví dụ dày trát `mat_trong` / `mat_ngoai` |
| supersedes_id | bigint FK element_measurements SET NULL | có | ứng viên mà dòng này thay khi người dùng sửa |
| note | text | có | lý do khi chọn hoặc khi thiếu |
| created_by | int FK users SET NULL | có | null khi do hệ thống tạo |
| created_at | timestamptz | không | |

UNIQUE INDEX một phần (`element_id`, `quantity_kind`, `variant`) WHERE `selected`. Ví dụ dài 3.950 (`hinh_hoc`, B) và 4.000 (`dimension`, A) là hai dòng; chỉ một dòng có `selected = true`.

### 2.4 `element_relations`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| relation_id | bigint PK | | |
| from_element_id | bigint FK CASCADE | không | |
| to_element_id | bigint FK CASCADE | không | CHECK khác `from_element_id` |
| kind | varchar(24) | không | CHECK in (`thuoc_tuong`, `goi_len`, `noi_voi`, `cung_chi_tiet`, `trung_voi`, `nam_trong`) |
| status | char(1) | không | A/B/C/D |
| evidence_id | bigint FK evidence_sources SET NULL | có | |

UNIQUE (`from_element_id`, `to_element_id`, `kind`)

## 3. Bằng chứng và kiểm tra

### 3.1 `evidence_sources`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| evidence_id | bigint PK | | |
| project_id | int FK CASCADE | không | |
| kind | varchar(24) | không | CHECK in (`chu`, `kich_thuoc`, `bang_thong_ke`, `vung_ban_ve`, `hatch`, `block`, `tai_lieu`, `nguoi_nhap`, `thong_so_du_an`, `dinh_muc`) |
| revision_id | bigint FK project_document_revisions SET NULL | có | bắt buộc khi kind thuộc nhóm bản vẽ (CHECK) |
| view_id | bigint FK drawing_views SET NULL | có | |
| entity_ids | bigint[] | không | mặc định `{}` |
| raw_content | text | không | **nội dung nguyên gốc**, ví dụ `- VỮA XIMĂNG a = 15 MÁC 75` |
| interpreted | jsonb | không | **giá trị đã diễn giải**, ví dụ `{"day_trat": 15, "unit": "mm", "mac_vua": "M75"}` |
| rule_code | varchar(64) | có | quy tắc đã áp, ví dụ mã trong `material_notes.csv` hoặc `nguong_nhan_dien.csv` |
| page_ref | varchar(128) | có | trang hoặc bảng, cho tài liệu ngoài |
| user_id | int FK users SET NULL | có | cho `nguoi_nhap` |
| created_at | timestamptz | không | |

### 3.2 `measurement_evidence`

PK (`measurement_id`, `evidence_id`) · `role` varchar(16) CHECK in (`chinh`, `doi_chieu`, `mau_thuan`)

### 3.3 `review_issues`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| issue_id | bigint PK | | |
| project_id | int FK CASCADE | không | |
| takeoff_id | bigint FK takeoff_results SET NULL | có | |
| kind | varchar(24) | không | CHECK in (`thieu_so`, `mau_thuan`, `nghi_trung`, `chua_ro`, `ngoai_khoang`, `thieu_ban_ve`) |
| severity | varchar(8) | không | CHECK in (`chan`, `canh_bao`, `ghi_chu`) |
| element_id | bigint FK SET NULL | có | |
| measurement_id | bigint FK SET NULL | có | |
| view_id | bigint FK SET NULL | có | |
| message | text | không | câu tiếng Việt hiển thị cho người dùng |
| check_code | varchar(32) | có | ví dụ `KH05` trong `khoang_hop_ly.csv` |
| state | varchar(12) | không | CHECK in (`mo`, `da_xu_ly`, `chap_nhan`, `bo_qua`), mặc định `mo` |
| resolution | text | có | bắt buộc khi state khác `mo` |
| resolved_by | int FK users SET NULL | có | |
| resolved_at | timestamptz | có | |

INDEX (`project_id`, `state`). `audit_logs` giữ nguyên; `detail` ghi thêm `{table, id, before, after}`.

## 4. Khối lượng

### 4.1 `takeoff_results`: thêm cột, không đổi cột cũ

| Cột thêm | Kiểu | Null | Ghi chú |
|---|---|---|---|
| profile_version | int | có | |
| input_revisions | jsonb | không | `[{file_id, revision_id, sha256, role}]`, mặc định `[]` |
| params_snapshot | jsonb | không | `ProjectParams` lúc tính |
| engine_version | varchar(32) | có | phiên bản mã của `compute_rough` hoặc `review.py` |
| request_sha256 | char(64) | có | lấy từ `analysis_receipt` |
| response_sha256 | char(64) | có | |
| client_analysis_id | uuid | có | token của lượt trên trang (F10) |
| state | varchar(12) | không | CHECK in (`tam`, `xac_nhan`, `huy`), mặc định `tam`; giữ `confirmed_at` cũ |
| superseded_by | bigint FK takeoff_results SET NULL | có | |

`result` (JSONB) giữ nguyên để không gãy API cũ. Các bảng 4.2–4.3 là **bản chuẩn hóa** của `result.works`; ghi trong cùng một giao dịch.

### 4.2 `takeoff_items`: một dòng cho mỗi `WorkItem`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| item_id | bigint PK | | |
| takeoff_id | bigint FK CASCADE | không | |
| work_code | varchar(32) | không | khóa của `WORKS` (XAY, TRAT, SAN, COT_THEP…) |
| level_id | bigint FK SET NULL | có | |
| element_id | bigint FK SET NULL | có | null khi công tác gộp nhiều cấu kiện |
| element_label | varchar(255) | có | = `WorkItem.element` |
| variant | varchar(64) | có | |
| unit | varchar(8) | không | |
| quantity | numeric(14,4) | có | null khi chưa tính được |
| quantity_known | numeric(14,4) | có | phần đã tính được khi `status = 'D'` một phần |
| formula | text | không | công thức đã thay số |
| basis | varchar(24) | có | `bang_thong_ke`, `ham_luong`, `not_supported` |
| wall_system_id | varchar(64) FK wall_systems SET NULL | có | |
| stage | varchar(16) | có | `WORK_STAGE` |
| status | char(1) | không | A/B/C/D |
| missing | text[] | không | mặc định `{}` |
| source | varchar(8) | không | CHECK in (`auto`, `manual`) |
| seq | int | không | thứ tự trong `result.works` |

UNIQUE (`takeoff_id`, `seq`) · INDEX (`takeoff_id`, `work_code`)

### 4.3 `takeoff_item_inputs`: đầu vào đã dùng, chụp giá trị lúc tính

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| item_id | bigint FK CASCADE | không | |
| seq | smallint | không | |
| input_kind | varchar(16) | không | CHECK in (`so_do`, `thong_so`, `dinh_muc`, `ket_qua_trung_gian`) |
| measurement_id | bigint FK SET NULL | có | |
| rough_norm_id | int FK rough_norms SET NULL | có | |
| label | varchar(128) | không | ví dụ `chiều dày sàn` |
| value_snapshot | numeric(14,4) | có | **giá trị tại thời điểm tính**, không đổi khi số đo bị sửa sau này |
| unit | varchar(8) | có | |
| status | char(1) | không | A/B/C/D |

PK (`item_id`, `seq`)

## 5. Phương án vật liệu

### 5.1 `material_scenarios`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| scenario_id | bigint PK | | |
| takeoff_id | bigint FK takeoff_results CASCADE | không | |
| name | varchar(128) | không | `Phương án A`, `Theo thiết kế`… |
| origin | varchar(16) | không | CHECK in (`thiet_ke`, `nguoi_dung`, `de_xuat_ai`, `toi_uu`) |
| run_id | int FK optimization_runs SET NULL | có | khi phương án đến từ NSGA-II |
| is_selected | boolean | không | UNIQUE INDEX một phần (`takeoff_id`) WHERE `is_selected` |
| created_by | int FK users SET NULL | có | |
| created_at | timestamptz | không | |

### 5.2 `material_assignments`

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| assignment_id | bigint PK | | |
| scenario_id | bigint FK CASCADE | không | |
| item_id | bigint FK takeoff_items CASCADE | có | gán theo công tác… |
| element_id | bigint FK building_elements CASCADE | có | …hoặc theo cấu kiện. CHECK (`item_id IS NOT NULL OR element_id IS NOT NULL`) |
| material_id | varchar(64) FK materials RESTRICT | có | để trống được |
| wall_system_id | varchar(64) FK wall_systems RESTRICT | có | |
| source | varchar(16) | không | CHECK in (`thiet_ke`, `nguoi_dung`, `de_xuat_ai`, `toi_uu`) |
| evidence_id | bigint FK evidence_sources SET NULL | có | ghi chú thiết kế, hoặc câu trả lời AI đã qua bộ kiểm |
| status | char(1) | không | A/B/C/D |

UNIQUE (`scenario_id`, `item_id`, `element_id`) NULLS NOT DISTINCT (PostgreSQL ≥ 15)

### 5.3 `material_requirements`: một dòng cho mỗi `MaterialLine` của từng phương án

| Cột | Kiểu | Null | Ghi chú |
|---|---|---|---|
| requirement_id | bigint PK | | |
| scenario_id | bigint FK CASCADE | không | |
| material_id | varchar(64) FK materials RESTRICT | có | trống khi danh mục chưa có mã (giữ `name`) |
| name | varchar(255) | không | |
| unit | varchar(16) | không | |
| quantity | numeric(14,4) | có | phần đã tính |
| complete | boolean | không | |
| waste_pct | numeric(6,3) | có | null: chưa có hao hụt (không tự cộng) |
| quantity_with_waste | numeric(14,4) | có | |
| quantity_min, quantity_max | numeric(14,4) | có | |
| confirmation | varchar(16) | có | `nguon`, `tinh`, `kinh_nghiem` |
| status | char(1) | không | A/B/C/D |
| missing | text[] | không | |
| group_id, raw_class | varchar(32) | có | |
| weight_kg | numeric(14,3) | có | |

Bảng nối `requirement_sources(requirement_id, item_id, rough_norm_id, quantity_part)` cho biết vật liệu này đến từ công tác nào và định mức nào (= `MaterialLine.uses`).

**Không lưu giá trong các bảng này.** Giá lấy từ `price_records` theo `optimization_runs.price_snapshot_date`, để không trộn khối lượng với giá dự đoán.

## 6. Thứ tự triển khai

| Đợt | Bảng | Điều kiện để sang đợt sau |
|---|---|---|
| 1 | `drawing_views`, `building_levels`, `view_levels`, `drawing_entities`, `evidence_sources` | Đọc lại một bản vẽ build cho ra đúng hình, tầng và bằng chứng |
| 2 | `building_elements`, `element_occurrences`, `element_measurements`, `measurement_evidence`, `element_relations`, `review_issues` | Một cấu kiện vẽ ở ba hình chỉ ra một dòng; giữ được hai ứng viên số đo |
| 3 | thêm cột `takeoff_results`, `takeoff_items`, `takeoff_item_inputs` | Bảng chuẩn hóa khớp `result.works` từng dòng trên cùng một lần tính |
| 4 | `material_scenarios`, `material_assignments`, `material_requirements`, `requirement_sources` | So hai phương án trên cùng khối lượng mà không phải tính lại khối lượng |

Mỗi đợt: sửa `db/models.py`, chạy `scripts/export_sql.py` và `scripts/build_upgrade_sql.py`, kiểm migration trên database thử nghiệm riêng (`OPTIMAT_TEST_DATABASE_URL`). Sau đó chạy truy vấn kiểm tra ở cuối `04_upgrade.sql`, kết quả phải rỗng.

## 7. Còn để ngỏ

- `geom_wcs` / `geom_norm`: lưu JSONB đơn giản hay dùng PostGIS. Đề xuất JSONB cho MVP, vì máy chạy hiện chưa có PostGIS.
- Đồng bộ mã cấu kiện giữa KT và KC (C1 trên mặt bằng kiến trúc ≡ C1 trên bản kết cấu): dùng `element_relations.kind = 'trung_voi'` hay gộp thẳng. Cần ca thật để quyết.
- Giới hạn số dòng `drawing_entities` cho mỗi phiên bản (đề xuất ≤ 50.000), để tránh lưu nhầm cả file.
