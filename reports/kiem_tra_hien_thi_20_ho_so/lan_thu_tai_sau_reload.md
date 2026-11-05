# Thử tải sau khi API được nạp lại

- Trang quản trị với phiên đã đăng nhập hiển thị dự án P01, năm nút tải và kết quả Nhà giả lập chưa xác nhận.
- Bấm `Tải P01_ban_ve.pdf`. Giao diện không hiển thị lỗi; công cụ chờ sự kiện download trong 20 giây nhưng hết thời gian, không nhận được đường dẫn tệp tải. Không thấy tệp tương ứng trong thư mục Downloads khi kiểm tra sau đó.
- Do chưa xác nhận được tệp đầu tiên và công cụ không cung cấp status, header hoặc bytes của yêu cầu từ nút tải, **chưa chạy hoặc nghiệm thu 100 lượt HTTP**. Không coi giao diện không báo lỗi hay SHA-256 tệp gốc trên đĩa là bằng chứng byte HTTP.
- Chưa xác minh bằng thử nghiệm này các trường content-type, Content-Disposition, độ dài hoặc SHA-256 qua Next; chưa có kết luận xác định rằng backend lỗi. Không thay đổi database, tài khoản, dịch vụ hoặc nhập lại hồ sơ.
- Bổ sung đối chiếu log do tiến trình API ghi: `reports/module_ui_qa_20261103/api_reload_20261103_224823.log` có `GET /api/admin/projects/3/files/28 HTTP/1.1` trả `200 OK` tại backend. Đây là bằng chứng backend xử lý yêu cầu tệp P01 PDF, nhưng log không chứa headers hoặc bytes; chưa đủ đối chiếu SHA-256 hay kết luận tệp đã được trình duyệt lưu. Không có 100 kết quả HTTP.
- Giới hạn quan sát: API trình duyệt công bố thao tác `waitForEvent('download')` và `download.path()`, nhưng lần click tạo tải qua blob không phát sự kiện quan sát được; `playwright.evaluate` chỉ cho đọc DOM, không phải API bắt HTTP/response body. Không trích cookie, tạo token hoặc chuyển phiên xác thực sang công cụ khác.
