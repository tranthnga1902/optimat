# Đối chiếu D01 với schema 20 bảng

Ngày 04/11/2026. Đây là tài liệu ánh xạ đề xuất từ danh mục file, **không phải dữ liệu đã nhập**. Căn cứ là `docs/schema/CSDL_20_BANG.md`, `src/optimat/db/schema20.py` và `src/optimat/db/compat20.py`. Không đọc hoặc thay đổi database ứng dụng trong lượt này.

## Một tệp, một revision và một công trình

| Thông tin danh mục | Nơi lưu/kiểm tra dự kiến | Quy tắc cần giữ |
|---|---|---|
| `project_candidate` | `projects.project_id` | Chỉ là nhãn nhóm nghiên cứu, không phải ID DB. Trước khi nạp cần công trình và chủ sở hữu hợp lệ; kiểm đúng cùng công trình, không tạo liên kết theo tên một cách tự động. |
| Tệp logic | `document_revisions`, `record_type='file'` | Một `file_id` trong dự án; `filename`, `format`, `stored_path` theo hợp đồng lưu trữ. `project_files` là **view tương thích**, không tạo bảng vật lý thứ 21. |
| Revision tệp | `document_revisions`, `record_type='revision'` | `revision_id`, `file_id`, `project_id`, `version`, `sha256`, `size_bytes`, `format`, `role`, `stored_path`, `created_at`. Nghiệp vụ yêu cầu ID và hash có mặt, version/size dương, role hợp lệ; unique `(file_id,version)` và `revision_id`. **Khoảng trống snapshot:** CHECK hiện viết `version > 0`, `size_bytes > 0`, `role IN (...)` mà thiếu kiểm `IS NOT NULL`; SQL CHECK có thể chấp nhận NULL ở các trường này khi biểu thức cho UNKNOWN. Không coi DB hiện tại đã chặn ba trường hợp NULL; cần sửa và kiểm thử theo owner schema. `project_document_revisions` là view. |
| `version`, `version_status` | `document_revisions.version` sau khi kiểm chứng | Cột danh mục để trống: ngày/tên file và ngày tải không chứng minh revision thiết kế. Khi nhập file mới qua API, server cấp phiên bản lưu trữ; không biến nó thành bằng chứng phiên bản thiết kế gốc. |
| `sha256`, `bytes`, `format`, `path` | `document_revisions.sha256`, `size_bytes`, `format`, `stored_path` | Hash trên byte tệp được đọc, không coi trùng tên là trùng byte. `path` trong CSV tính từ gốc workspace, không phải `stored_path` đã được cấp quyền/lưu an toàn. Khi nhập phải kiểm lại và dùng kho được cấu hình; không lưu đường dẫn do client tùy ý cung cấp. |
| `role` | `document_revisions.role` | Các nhãn trong CSV là **gợi ý**, cần người phụ trách xác nhận một trong `KT`, `KC`, `HO_SO`, `TIEN_LUONG`, `THAM_KHAO`. Nhãn `KT+KC sơ đồ` thể hiện cùng một tệp chứa cả hai loại theo README; không tự biến thành role DB hợp lệ hoặc hai revision riêng. MEP và gói nén cần phân loại hợp đồng phù hợp trước khi nhập. |
| `source`, `usage_rights`, `pairing_evidence`, `read_status`, `signature_check`, `parser_open_status` | Manifest/hồ sơ kiểm chứng bên ngoài DB; liên kết bằng project/file/revision và hash sau khi được thiết kế | Schema hiện tại **không có cột riêng** cho toàn bộ nguồn, quyền, kết luận cặp và trạng thái kiểm. Không nhét các trường này vào `stored_path`, giả định metadata tồn tại trong DB, hoặc tạo bảng riêng chưa được duyệt. Cần thỏa thuận manifest có phiên bản và quyền truy cập. |
| `data_kind`, `kind_evidence` | `analysis_runs.data_kind` chỉ khi tạo snapshot phân tích phù hợp | CSV dùng `UNKNOWN` như nhãn **chưa xác minh**, không phải giá trị hợp lệ của CHECK DB (`ACTUAL`, `SAMPLE`, `SYNTHETIC`). Chặn nạp/phát hành hoặc chờ phân loại có bằng chứng; không thay `UNKNOWN` bằng `ACTUAL` hay `SAMPLE`. Bản giả lập giữ `SYNTHETIC`. |
| Thông số và nguồn đã kiểm | `projects.profile_revisions`; sau phân tích là `analysis_runs`, `evidence_sources`, `building_elements`, `element_measurements` | Cần locator thực (trang/sheet/handle/lần INSERT) và nguồn đúng revision. Có cùng tên/nhóm không chứng minh số đo hoặc đáp án. Không tự tạo evidence hay trạng thái đã kiểm. |

Schema 20 dùng hai loại bản ghi vật lý trong cùng `document_revisions`; trigger tương thích kiểm quan hệ và ngăn UPDATE revision. `project_profile_revisions` là view qua `projects.profile_revisions`. Tính duy nhất file/revision không thay thế kiểm nguồn, ownership và quan hệ cùng dự án ở luồng ghi. Các tham chiếu trong JSONB vẫn cần kiểm tại ứng dụng.

**Vấn đề mở theo review 14:** ràng buộc `ck_document_revision_required` trong snapshot được đọc chưa bảo đảm `version`, `size_bytes` và `role` khác NULL cho `record_type='revision'`. Phiên S20 là owner sửa và kiểm; tài liệu này không tuyên bố bản sửa đã có hoặc đã được áp vào DB. Các trường ID/hash được viết bằng `IS NOT NULL` trong biểu thức, nhưng không suy rộng kết quả đó cho ba trường còn lại.

## Kiểm tra trước khi đưa một gói vào môi trường thử nghiệm

1. Chốt quyền dùng cụ thể, phân biệt quyền nội bộ, huấn luyện và chia sẻ; ẩn danh khi cần. File tải miễn phí không đồng nghĩa được dùng huấn luyện.
2. Xác định đúng gói KT/KC cùng công trình và đúng phiên bản; ghi bằng chứng chuyển đổi DWG→DXF và hash cả đầu vào/đầu ra. Nêu phần thiếu và trường hợp chưa xác định.
3. Mở từng file bằng reader phù hợp trong lượt được phân công; kiểm đơn vị, vùng hình, tầng và trạng thái lỗi. Hash/đọc byte hoặc file magic không chứng minh mở CAD được.
4. Nhập một công trình qua luồng được phân quyền vào **database thử nghiệm 20 bảng** sau khi có lượt cho phép; đối chiếu file/revision/project, truy lại nguyên bản và hash. Không giả định database ứng dụng đã chuyển đổi.
5. Đáp án và công thức cần kiểm độc lập; không gọi tiên lượng nguồn là ground truth hoặc gán `ACTUAL` chỉ vì file có trên mạng.
