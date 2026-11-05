# Cơ sở dữ liệu OptiMat AI theo 20 bảng

Ngày cập nhật: 04/11/2026. Đây là đặc tả hiện hành, thay thiết kế 45 bảng và các kiểm kê 23/26/28 bảng cũ. Số bảng vật lý lấy từ `db/schema20.py`; không đếm view thành bảng lưu dữ liệu.

## 1. Danh sách đã chốt

| Nhóm | Bảng vật lý | Số lượng |
|---|---|---|
| Tài khoản và hồ sơ | users, projects, document_revisions | 3 |
| Nhận dạng và bóc tách | analysis_runs, building_elements, element_measurements, evidence_sources, takeoff_items | 5 |
| Vật liệu và định mức | materials, wall_systems, material_relations, work_norms | 4 |
| Nguồn cung và chi phí | suppliers, supplier_materials, price_records, cost_parameters | 4 |
| Phương án và vận hành | material_scenarios, optimization_runs, rule_sets, audit_logs | 4 |

Đúng 20 bảng vật lý, không có bảng hồ sơ/ngưỡng/quy tắc ẩn ở schema khác. File gốc, mô hình và bộ đáp án nằm ngoài DB; database lưu đường dẫn và snapshot. Một số tên cũ được giữ bằng view để không phá API và CSV đang sử dụng; view không lưu bản sao dữ liệu.

## 2. Nguồn schema và cách khởi tạo

- `src/optimat/db/schema20.py`: metadata của 20 bảng và các FK/CHECK/index vật lý.
- `src/optimat/db/compat20.py`: view có thể ghi và trigger kiểm tra dữ liệu gộp; khởi tạo schema mới.
- `src/optimat/db/models.py`, `project_documents.py`: ánh xạ tương thích của các luồng cũ; không gọi `Base.metadata.create_all` để khởi tạo database mới.
- `scripts/export_sql.py`: sinh `sql/01_schema.sql` gồm 20 bảng và view/trigger tương thích, cùng seed và quy tắc.
- `scripts/build_upgrade_sql.py`: sinh `sql/04_upgrade.sql`, bổ sung cấu trúc thiếu của schema 20. Script từ chối database còn bảng vật lý cũ; không tự chuyển dữ liệu bằng ALTER rời rạc.

Database mới: cấu hình DATABASE_URL riêng rồi chạy `python scripts/init_db.py`. Chỉ dùng `--reset` trên database thử nghiệm hoặc khi chủ ý xóa toàn bộ dữ liệu ứng dụng. Danh mục đầy đủ và các view tính giá/định mức được nạp bằng `sql/03_materials.sql`, `sql/04_upgrade.sql`, `sql/05_rules.sql` theo nhu cầu.

Database đang dùng: chạy `python scripts/migrate_schema20.py` để kiểm kê; `python scripts/migrate_schema20.py --apply` để sao lưu rồi chuyển đổi. Không dùng `--reset` cho chuyển đổi dữ liệu.

## 3. Grain và nơi lưu

| Bảng | Một dòng đại diện cho |
|---|---|
| users | Một tài khoản và vai trò |
| projects | Một công trình; profile_revisions giữ các phiên bản thông số bất biến được API bổ sung |
| document_revisions | Một bản ghi tệp logic hoặc một phiên bản tệp; record_type phân biệt file/revision; bản ghi revision có hash, vai trò, phiên bản và kích thước |
| analysis_runs | Một snapshot nhận dạng/bóc tách; khóa takeoff_id được giữ để tương thích; result/input_snapshot chứa đầy đủ đầu vào, kết quả, hình/tầng, vấn đề và nguồn |
| building_elements | Một cấu kiện trong đúng một lần phân tích; không gộp các lần chạy vào cùng cấu kiện có thể sửa |
| element_measurements | Một ứng viên số đo; chỉ một giá trị được chọn cho từng thông số của cấu kiện |
| evidence_sources | Một bằng chứng trong một lần phân tích, có vị trí và nội dung nguồn |
| takeoff_items | Một dòng công tác hoặc khấu trừ trong snapshot; không tự tính lại công thức |
| materials | Một mã vật liệu; giữ đơn vị chuẩn, quy cách, thuộc tính kỹ thuật và nguồn |
| wall_systems | Một phương án tường, vật liệu chính và định mức theo quy cách |
| material_relations | Một quan hệ cấp phối/vật liệu đi kèm giữa hai vật liệu |
| work_norms | Một hệ số định mức theo công tác và biến thể; giữ token vai trò @VUA theo logic hiện có |
| suppliers | Một nhà cung cấp/địa điểm cung ứng |
| supplier_materials | Một cặp nhà cung cấp–vật liệu với giá hiện hành và điều kiện mua |
| price_records | Một quan sát giá theo ngày, nguồn, vật liệu, nhà cung cấp và cơ sở giá |
| cost_parameters | Một bản ghi phương tiện hoặc đơn giá nhân công; kind + record_key định danh; payload kiểm tra theo cấu trúc cũ |
| material_scenarios | Một phương án trên một snapshot; assignments/requirements/catalog_snapshot lưu lựa chọn, nhu cầu, đầu vào và nguồn |
| optimization_runs | Một lần tối ưu có cấu hình, tập phương án và snapshot các đầu vào thực dùng |
| rule_sets | Một bản ghi quy tắc/danh mục tham chiếu/metadata mô hình; kind + record_key duy nhất, payload được kiểm theo từng loại |
| audit_logs | Một sự kiện có người thực hiện nếu xác định được và chi tiết thao tác |

## 4. Ánh xạ từ lược đồ cũ

| Dữ liệu cũ | Nơi lưu vật lý mới | Truy cập tương thích |
|---|---|---|
| material_groups, material_families, material_aliases, standards, material_standards | rule_sets theo kind; tham chiếu danh mục được bảo toàn, không xóa vì gộp bảng | View cùng tên, kiểu cột cũ |
| material_rules, material_notes, room_rules, drawing_concepts, convention_clauses | rule_sets theo kind | View cùng tên; CRUD quản trị cũ vẫn hoạt động |
| model_versions | rule_sets kind=model_versions | View model_versions; cấu hình/hash mô hình thực dùng chụp trong lần tối ưu |
| vehicles, labor_rates | cost_parameters | View cùng tên |
| rough_norms | work_norms | View rough_norms |
| takeoff_results | analysis_runs | View takeoff_results |
| project_files, project_document_revisions | document_revisions | Hai view phân loại file/revision |
| project_profile_revisions | projects.profile_revisions | View trải các phiên bản trong JSONB; INSERT kiểm phiên bản và khóa dự án |

Các bảng còn tên không đổi được giữ dữ liệu và định danh cũ. Việc giữ view là chủ ý tương thích, không phải còn 28 bảng vật lý. `INSERT ... ON CONFLICT` theo khóa của view không được PostgreSQL hỗ trợ; các generator danh mục đã đổi sang UPDATE/INSERT có điều kiện. Các import dùng ON CONFLICT trên bảng vật lý như suppliers/price_records tiếp tục được giữ.

## 5. Quy tắc dữ liệu

### Hồ sơ và nguồn

Mỗi revision gắn đúng file/project; cập nhật revision bị từ chối, sửa là thêm phiên bản. Phiên bản thông số được append qua API có khóa dự án. Không tạo hash, vai trò hay người kiểm giả cho file cũ chưa có thông tin.

Một số đo có phương pháp, đơn vị, trạng thái A/B/C/D và danh sách evidence_id. Trigger kiểm các ID bằng chứng tồn tại và thuộc đúng lần phân tích. Không cho chọn số đo NULL; không cho hai số đo cùng được chọn cho một thuộc tính. Số đo do người dùng nhập không gắn A.

### Bóc tách và vật liệu

`analysis_runs` giữ snapshot gốc, `takeoff_items` giữ dòng công tác đã tính, `building_elements` giữ cấu kiện của chính snapshot đó. Công tác không được nối cấu kiện thuộc lần phân tích khác. Thiếu số đo giữ NULL; dòng trừ được phép âm, không áp bất đẳng thức phần đã biết/tổng cho mọi đại lượng có dấu.

Chưa có chỉ định vật liệu thì cấu kiện vẫn tồn tại. Chỉ tạo lượng mua khi có lựa chọn và định mức đủ căn cứ. Mỗi scenario có thể chứa các gán chưa xác định; không tự đánh dấu chọn vì hệ thống đã đề xuất. Thay đổi phương án ảnh hưởng chiều dày/hình học phải tính lại phần chịu ảnh hưởng.

JSONB của scenario phải là danh sách object. Mã vật liệu, phương án tường và công tác tham chiếu được kiểm tồn tại/khớp ngữ cảnh. Một dòng nhu cầu complete=true phải có quantity. Nếu có quantity_with_waste nhưng thiếu waste_pct, chỉ chấp nhận khi mọi nguồn uses đều công bố waste_included=true; đây là trường hợp định mức đã gồm hao hụt.

### Snapshot và giới hạn

Sau khi store_details ghi result_sha256, database chặn sửa result/input_snapshot/project/file của snapshot đó. Bổ sung/sửa hồ sơ tạo lần phân tích mới. Không coi dữ liệu A/B/C/D là trạng thái người kiểm đã duyệt.

Khi chuyển dữ liệu cũ, bản JSON gốc được giữ nguyên. Số đo chỉ có tham chiếu input snapshot được ghi là loại input_snapshot, không tự nâng thành bằng chứng CAD đã kiểm. Danh mục chụp lúc chuyển đổi được gắn catalog_is_historical_input=false; không tuyên bố đó là đúng bộ danh mục được dùng ở một lần tính trong quá khứ.

Các quan hệ nằm trong occurrences/relations và một số payload JSONB vẫn cần kiểm ở tầng ứng dụng. Không tuyên bố mọi liên kết được khóa ngoại bảo vệ. Dữ liệu CAD gốc phải giữ nguyên để truy lại handle/đường dẫn INSERT.

## 6. Luồng ghi/đọc hiện hành

1. Hồ sơ dự án qua API giữ nguyên hợp đồng file_id/revision_id; view ghi vào document_revisions.
2. Thông số dự án append vào projects.profile_revisions; API giữ kiểm nguồn và selected_revisions.
3. save_review/save_rough thêm analysis_runs qua view, gọi store_details trong cùng giao dịch để lưu cấu kiện, bằng chứng, số đo, dòng công tác và scenario hiện có, sau đó đóng snapshot.
4. Trang quản trị liệt kê đúng 20 bảng vật lý. Các API quy tắc cũ vẫn truy cập view để giữ chức năng chỉnh quy tắc; view không được liệt kê là bảng vật lý bổ sung.
5. Tối ưu không gắn dự án vẫn chạy như trước. Khi gửi đồng thời project_id/takeoff_id, API kiểm quyền và cùng dự án, lưu optimization_runs cùng material_scenarios, trả run_id. Frontend gửi ngữ cảnh khi snapshot đã có hai ID.
6. CSV vẫn phục vụ chế độ không kết nối database. Không gọi dữ liệu CSV là dữ liệu DB đã nhập; nguồn thực dùng phải được phân biệt.

## 7. Chuyển đổi, đối chiếu và phục hồi

CLI chuyển đổi tạo pg_dump định dạng custom và kiểm pg_restore --list trước khi thay đổi. Trong một giao dịch: khóa các bảng nguồn, đọc đầy đủ cột/dòng, từ chối bảng/view lạ hoặc cột khác metadata, thay cấu trúc, nạp dữ liệu, khôi phục sequence, đối chiếu từng cột/dòng qua view tương thích, backfill chi tiết có căn cứ và kiểm đúng 20 bảng. Bất kỳ lỗi nào rollback cả DDL và dữ liệu.

File backup có dữ liệu nhạy cảm nên nằm trong backups/ đã loại khỏi Git. Không đưa test_url.txt hoặc thông tin đăng nhập vào báo cáo/Word. Kiểm thử phục hồi phải dùng database riêng; không restore đè database người dùng để thử.

Trước chuyển đổi đã thử bản sao từ database nguồn và kiểm đủ 28 cấu trúc cũ. Kết quả kiểm thử cụ thể và tình trạng áp dụng chính thức được ghi trong báo cáo bàn giao, không suy ra từ việc có script hoặc tài liệu.

## 8. Giới hạn và công việc dữ liệu tiếp theo

Schema không làm hệ thống tự nhận mọi bản vẽ. Cần hồ sơ thực tế, nhãn cấu kiện/số đo, đáp án đã kiểm, định mức có nguồn và báo giá cùng cơ sở. Xem `../KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md` cho kế hoạch sáu tuần và 28 tình huống kiểm chứng.

Tài liệu 45 bảng và SQL đề xuất cũ chỉ để tham chiếu lịch sử, không dùng để nâng cấp hệ thống 20 bảng. Không chạy docs/schema/ddl_de_xuat_20261104.sql hoặc ddl_dich_day_du_20261104.sql trên schema hiện hành.
