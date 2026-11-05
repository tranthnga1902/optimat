# Rà soát và hợp đồng đề xuất: hồ sơ trước phân tích

Phạm vi: đọc mã hiện tại ngày 03/11/2026; chưa triển khai, chưa kiểm thử chạy thực tế. Không tải hoặc gửi hồ sơ công trình thực.

## Hiện trạng có bằng chứng

- `frontend/src/components/ProjectBar.tsx` và `frontend/src/lib/projects.ts` dùng localStorage cho lịch sử và thông tin dự án của người dùng. Đây không phải danh sách `projects` của PostgreSQL; chưa có định danh DB chủ dự án bền vững cho mỗi hồ sơ trong luồng đó.
- `project_files` có `file_id`, `project_id`, tên, loại, đường dẫn và thời gian tải; chưa có vai trò KT/KC/tham khảo, SHA-256, dung lượng hay mã phiên bản. Dùng nguyên các cột hiện tại không đáp ứng yêu cầu phân biệt phiên bản và chứng minh byte.
- `POST /api/ingest` gọi `ingest_file` và `store_upload` vào `data/uploads`; kiểm định đầu vào và hash có sẵn. Manifest phiên bản theo tên là toàn cục, không gắn dự án, khóa chỉ có hiệu lực một tiến trình, không có giao dịch chung với PostgreSQL. Đây là công cụ tiền xử lý, chưa phải API quản lý hồ sơ thuộc chủ dự án.
- `GET /api/admin/projects/{project_id}/files/{file_id}` trong source chỉ phục vụ quản trị, chỉ cho `data/drawings`, không phải quyền chủ dự án và không đọc tệp mới tại `data/uploads`.
- `POST /api/takeoff/view` nhận multipart bytes và không chỉ preview: cả nhánh thường và progressive đều gọi pipeline nhận dạng/đo bóc. Không gọi endpoint này khi người dùng chỉ mở xem. `drawing.view_progress.line_preview` là ứng viên hiển thị nét từ `read_drawing`, nhưng cần đo khả năng chuyển DWG, hiệu năng và lỗi riêng.
- Các API đo bóc hiện tại nhận upload bytes. Chưa có hợp đồng đầu vào gắn `project_id + file_id + revision + role` để phân tích đúng phiên bản đã lưu.

## Hợp đồng đề xuất để điều phối duyệt

1. Dự án DB thuộc người đăng nhập, không lấy `project_id`/owner từ localStorage làm bằng chứng sở hữu. Cần cơ chế tạo, liệt kê, đọc và mở lại dự án của người dùng; bảo toàn lịch sử local cũ, không tự nhập hoặc đổi chủ sở hữu.
2. Tải lên tệp CAD với `project_id`, tên gốc và vai trò do người dùng chọn (`KT`, `KC`, `THAM_KHAO`); kiểm kích thước, loại và chữ ký tệp theo `check_upload`. Tạo định danh tệp/phiên bản bất biến theo từng dự án và SHA-256 của byte gốc; tên hiển thị giữ nguyên an toàn. Nội dung trùng có thể chia sẻ lưu trữ nhưng liên kết, vai trò và lịch sử vẫn thuộc dự án. Không coi hash/tên trùng toàn cục là cùng phiên bản dự án.
3. Metadata tối thiểu: file ID, revision ID hoặc số phiên bản trong dự án, tên gốc, định dạng gốc, dung lượng, SHA-256, thời điểm, vai trò, trạng thái lưu và preview, đường dẫn xử lý nội bộ. Không lộ đường dẫn hệ thống cho client. Metadata hoặc bảng phiên bản cần migration/schema do 01 quyết định; không nhét vào `result` và không giả vờ có sẵn.
4. `GET` danh sách và metadata theo dự án; `GET` tải bytes gốc theo ID phiên bản và chủ sở hữu, trả attachment, nosniff và private/no-store. Kiểm dự án thuộc người dùng, phiên bản thuộc dự án; không nhận đường dẫn từ client. Đường dẫn kiểm containment và symlink theo chính sách lưu trữ. Không cấp quyền chủ dự án bằng route admin; quản trị riêng theo chính sách hiện hành.
5. Preview là một hành động độc lập, không chạy `takeoff`, không tạo kết quả xác nhận, không đụng bản bóc tách. Đề xuất endpoint preview theo ID phiên bản: đọc byte gốc đã lưu, với DXF dùng `read_drawing` và `line_preview`; với DWG chuyển bản sao trong thư mục tạm và giữ nguyên DWG gốc. Ghi định dạng nguồn, cảnh báo cắt giảm/giới hạn nét hoặc lý do không xem được; không chuyển lỗi thành bản vẽ rỗng. Cần xác minh `read_drawing` và converter không chạy nhận dạng ngoài mục tiêu preview trước khi chốt triển khai.
6. Nút phân tích chủ động gửi `project_id` cùng danh sách `{file_id, revision_id, sha256, role}` đã chọn. Server kiểm quyền, quan hệ dự án, hash và loại; phân biệt KT/KC/tham khảo, không tự coi tham khảo là KT/KC. Trả lỗi nếu phiên bản thay đổi/mất hoặc vai trò chưa rõ. `/do-boc` gọi backend bằng các ID được chọn, server đọc byte đã lưu; không yêu cầu upload lại và không tin nội dung/đường dẫn do client tự khai.
7. Lưu tệp và DB có hai miền giao dịch: ghi tệp tạm và kiểm hash trước, atomically đưa vào kho theo chính sách; giao dịch DB tạo liên kết/phiên bản; thất bại phải có cơ chế thu gom tệp mồ côi an toàn, không xóa tệp được dự án khác dùng. Đồng thời kiểm concurrency, giới hạn tệp và tránh đè cùng tên. Không tự khôi phục schema/reset DB.

## Kiểm thử bắt buộc trước nghiệm thu

- Quyền: chủ A truy cập hồ sơ A, chủ B/ẩn danh không đọc, tải, preview hay phân tích hồ sơ A; ID tệp dự án khác, ID không tồn tại và path traversal/symlink bị từ chối.
- Vòng đời: tải hai phiên bản cùng tên khác byte, đổi vai trò, tải lại trang/mở lại dự án, chọn đúng phiên bản và tải nguyên bản khớp byte/SHA; tệp nguồn không bị converter sửa.
- Preview: DXF/DWG thành công hoặc báo lỗi rõ; máy thiếu converter, tệp hỏng/giới hạn kích thước/preview thiếu; đo bằng spy rằng không gọi pipeline takeoff và không tạo `takeoff_results` khi chỉ tải lên/xem.
- Phân tích: chỉ chạy sau nút chủ động, không multipart upload lại, server nhận đúng file/revision/role/hash; reject revision cũ hoặc thiếu KT/KC thay vì đoán. Kiểm đồng thời hai dự án không lẫn trạng thái.
- Khả dụng: kiểm giới hạn xử lý tệp lớn và timeout, log trạng thái lỗi không lộ đường dẫn hoặc bí mật; kiểm rollback DB và tệp mồ côi; nghiệm thu chỉ dùng hồ sơ được phép tải lên. Gate từ chối upload Tân Bình vẫn có hiệu lực.

## Cần 01 phân vùng và chốt

Chọn mô hình bảng phiên bản/migration và nguồn định danh dự án giữa frontend local và PostgreSQL; thống nhất hợp đồng preview/analysis và route với các owner UI/backend. Chưa có số liệu, ảnh preview hay kết quả chạy để nhận là hoàn thành.
