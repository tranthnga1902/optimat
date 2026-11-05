# Đề xuất mở tệp dự án

- Trang quản trị `du-an` dùng `GET /api/admin/projects/{project_id}` qua proxy Next. Router này yêu cầu quyền quản trị và trả metadata `project_files`; bảng hiện chỉ hiển thị tên, loại và thời điểm.
- Rà mã `src/optimat`: chưa thấy route trả nội dung từ `project_files.stored_path`. `FileResponse` hiện chỉ dùng cho hình minh họa ký hiệu, không phải tệp dự án. Không có HTTP status hay content-type của nội dung 100 tệp để báo cáo.
- Đề xuất thêm route GET quản trị theo cặp `project_id` và `file_id`, xác nhận tệp thuộc dự án; giữ `require_admin`, từ chối ID không thuộc dự án. Giải quyết đường dẫn theo gốc lưu trữ cho phép, kiểm tra `resolve()` không thoát gốc, không cho đường dẫn tùy ý, kiểm tra tồn tại và tệp thường; chọn content type và Content-Disposition an toàn. Tránh cho phép truy cập theo tên hoặc đường dẫn do client cung cấp.
- Tại bảng chi tiết quản trị, thêm nút tải theo file ID, hiển thị trạng thái lỗi và tên phù hợp; đổi nhãn “Hồ sơ CAD” thành “Tệp dự án”, hiển thị `synthetic_housing` đúng loại. Không thay quyền sở hữu hoặc kích hoạt tài khoản kỹ thuật.
- Kiểm thử: tài khoản quản trị được tải đúng byte và SHA-256; người chưa đăng nhập/người dùng thường bị từ chối; ID sai, khác dự án, thiếu tệp, đường dẫn vượt gốc bị từ chối; kiểm cả DXF, PDF, XLSX, JSON, MD. Sau triển khai cần chạy 100 lượt HTTP và so hash.

Trang “Dự án của tôi” là lịch sử trong trình duyệt; không tự đồng bộ danh sách dự án quản trị. Tách bài toán hiển thị cho người dùng thực với quyết định phân quyền và chủ sở hữu; không ép ghi localStorage hoặc thay owner.
