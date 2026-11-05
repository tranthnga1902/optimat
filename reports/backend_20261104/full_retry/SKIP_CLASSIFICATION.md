# Phân loại skipped của full backend retry — 04/11/2026

Chỉ đọc log/artifact và mã test; không collect lại, không chạy pytest, không kết nối DB. Kết quả gốc: **1096 passed, 19 skipped, 15 deselected**, exit 0. Phân loại dưới đây không thay đổi gate đã chạy.

## 19 skipped

Nodeid dùng đường dẫn tương đối từ gốc checkout `optimat-ai`. Cột dòng là vị trí log `-ra` ghi nhận; nodeid được đối chiếu tĩnh với hàm test trong file.

| # | Nodeid | Dòng log | Lý do / gate chưa có bằng chứng |
|---|---|---:|---|
| 1 | `tests/test_admin_db.py::test_edit_rule_tables_in_postgresql` | 44 | Thiếu OPTIMAT_TEST_DATABASE_URL; CRUD quy tắc, cache và audit trên PostgreSQL |
| 2 | `tests/test_admin_db.py::test_manage_dealers_in_postgresql` | 71 | Thiếu URL DB test; CRUD đại lý/giá, validation và cascade trên PostgreSQL |
| 3 | `tests/test_admin_project_file.py::test_symlink_escape` | 84 | OSError khi tạo symlink; chặn tải file qua symlink thoát thư mục lưu trữ chưa được thực thi trong môi trường này |
| 4 | `tests/test_auth_admin.py::test_roles_users_projects_in_postgresql` | 41 | Thiếu URL DB test; đăng nhập, phân quyền admin/user, khóa tài khoản, dự án và audit có DB |
| 5 | `tests/test_db.py::test_catalog_from_db_matches_csv` | 46 | Thiếu URL DB test; đối chiếu danh mục DB/CSV |
| 6 | `tests/test_db.py::test_optimize_same_result_from_db` | 57 | Thiếu URL DB test; kết quả tối ưu DB/CSV tương đương, dùng DXF mẫu |
| 7 | `tests/test_db.py::test_train_from_db` | 71 | Thiếu URL DB test; đọc lịch sử giá và huấn luyện mô hình giá cục bộ, không phải OpenAI |
| 8 | `tests/test_db.py::test_all_tables_created` | 79 | Thiếu URL DB test; tạo đủ bảng theo metadata/schema |
| 9 | `tests/test_db.py::test_rules_and_families_from_db` | 87 | Thiếu URL DB test; quy tắc/họ vật liệu/định mức DB bằng CSV, gồm bốn khóa TRAT J05c |
| 10 | `tests/test_db.py::test_project_flow_roundtrip` | 109 | Thiếu URL DB test; lưu/đọc dự án, kết quả bóc tách, tối ưu và JSON, dùng DXF mẫu |
| 11 | `tests/test_db.py::test_materials_sql_script_loads_and_reruns` | 145 | Thiếu URL DB test; nạp và chạy lại SQL vật liệu |
| 12 | `tests/test_db.py::test_upgrade_sql_fills_missing_and_reruns` | 180 | Thiếu URL DB test; SQL nâng cấp điền phần thiếu và chạy lại |
| 13 | `tests/test_db.py::test_confirm_saves_to_project` | 217 | Thiếu URL DB test; API xác nhận lưu kết quả vào dự án, dùng DXF mẫu |
| 14 | `tests/test_db.py::test_rough_saves_to_project` | 250 | Thiếu URL DB test; API phần thô lưu kết quả vào dự án, dùng DXF mẫu |
| 15 | `tests/test_db.py::test_takeoff_reads_project_params` | 281 | Thiếu URL DB test; bóc tách nhận thông số dự án, dùng dữ liệu dựng trong test |
| 16 | `tests/test_db.py::test_concepts_admin_crud` | 324 | Thiếu URL DB test; CRUD quy ước nhận diện và phân quyền quản trị |
| 17 | `tests/test_project_document_roles_db.py::test_roles_delta_and_guarded_rollback` | 19 | OPTIMAT_PROJECT_DB_TEST chưa bật (fixture isolated_db); delta role HO_SO và rollback có điều kiện trên PostgreSQL |
| 18 | `tests/test_project_documents_migration.py::test_project_documents_migration_isolated` | 13 | OPTIMAT_PROJECT_MIGRATION_TEST chưa bật; tạo hai bảng revision, uniqueness/role constraint và rollback trong schema tạm |
| 19 | `tests/test_project_files_db.py::test_owned_project_files_and_profile_route` | 86 | OPTIMAT_PROJECT_DB_TEST chưa bật (fixture isolated_db); ownership, upload/version/download/preview, profile concurrency, phân giải revision trên DB |

Tổng: **15 thiếu URL DB test + 3 opt-in PostgreSQL chưa bật + 1 symlink = 19**. Cả 18 ca DB đều phụ thuộc PostgreSQL; ba ca opt-in còn yêu cầu URL DB test local riêng hợp lệ. Lý do skip trực tiếp của ba ca là opt-in chưa bật, không gộp nhầm thành lỗi kết nối.

Không ca skipped nào cần network OpenAI hoặc CAD thật. Các DXF ở nhóm DB là fixture mẫu/tự dựng; route project-files mock bộ đọc/preview và cấm gọi phân tích/LLM/lưu kết quả. Ca symlink dùng mock DB/storage và file text tạm, không cần PostgreSQL/OpenAI/CAD.

Các ca DB cũ dùng `init_db.py --reset` ở fixture hoặc thân test. Ba ca opt-in dùng transaction/schema tạm, rollback và kiểm tra public không đổi; tên DB/opt-in không tự chứng minh target đã cô lập. Đây là phân loại phụ thuộc, không phải chỉ dẫn bật/chạy chúng hoặc xác nhận migration đã áp.

## 15 deselected — tách khỏi skipped

`process.json` lưu năm prefix được 01 duyệt loại vì phạm vi full không CAD thật:

1. `tests/test_drawing_io.py::test_real_drawing_read_in_world_coords` (mọi tham số)
2. `tests/test_rough_build_drawings.py::test_nha_dan_columns_and_rough`
3. `tests/test_rough_build_drawings.py::test_nha_pho_columns`
4. `tests/test_registry.py::test_ket_cau_build_drawing`
5. `tests/test_rough_structural.py::test_ket_cau_build_drawing`

Log xác nhận **15 ca**, không phải 5 ca. Log không ghi từng parameter nodeid bị deselect; không suy dựng danh sách tham số từ filesystem hiện tại thành bằng chứng của lượt chạy. Phần chưa được kiểm là đọc/WCS, nhận diện kết cấu và bóc phần thô trên các CAD thật thuộc năm prefix này; không phải skip DB/OpenAI.

## Ý nghĩa nghiệm thu và điểm cần theo dõi

- Gate hồi quy backend không DB/OpenAI/CAD thật giữ kết quả đạt 1096 ca; 19 skipped và 15 deselected không được tính vào passed.
- Chưa thể dùng lượt này nghiệm thu PostgreSQL persistence/CRUD/auth, DB–CSV parity của J05c, SQL migration/rollback, project revisions/profile concurrency với DB, hay symlink escape trên Windows.
- OpenAI thật và CAD thật vẫn ngoài phạm vi bằng chứng của lượt này; không phải toàn bộ phần ngoài phạm vi đều biểu hiện bằng một skipped test.
- **Quan sát tĩnh có thể gây fail khi mở gate DB:** `tests/test_db.py::test_all_tables_created` vẫn chứa `len(Base.metadata.tables) == 26` (dòng 84), trong khi fix contract đã nhận ở `test_admin_db.py` là 28 bảng. Ca này đang skipped nên full xanh không xác minh assertion đó. Chưa chạy DB để chứng minh failure và chưa sửa test/source theo yêu cầu chỉ đọc.

## Bằng chứng tái kiểm không chạy test

Tất cả đường dưới tương đối với thư mục chứa báo cáo này:

- `pytest_full.log`: short test summary ghi đủ 19 vị trí/lý do skip; collection/summary ghi 15 deselected.
- `result.json`: exit/counts, thời điểm kết thúc, 263 hash trước/sau không đổi.
- `environment.json`: không có DATABASE_URL, URL DB test, OPENAI_API_KEY; hai opt-in false; LLM_PROVIDER=none; bỏ dotenv.
- `process.json`: command chính xác với năm --deselect, PID và thời điểm bắt đầu.
- `hash_before.json`, `hash_after.json`, `hash_diff.json`: baseline của mã đã chạy.
- `HANDOFF.md`: phạm vi gate và giới hạn của full retry đã bàn giao.

Để tái kiểm phân loại, đọc phần cuối `pytest_full.log`, đối chiếu vị trí skip với định nghĩa hàm trong các file test nêu trên và fixture `isolated_db` ở `tests/test_project_files_db.py`. Không cần import/collect test hoặc đọc .env. Báo cáo này chỉ bổ sung artifact, không sửa log gốc, source, test hay DB.
