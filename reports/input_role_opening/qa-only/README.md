# Trang QA vai trò bản vẽ

Áp gói `input-role.patch` dành cho đúng cổng vào bản sao QA. Sao chép thư mục `qa-only/3001/src/app/qa-input-roles` hoặc `qa-only/3002/src/app/qa-input-roles` tương ứng vào `src/app` của bản sao, rồi mở `/qa-input-roles`.

Trang dùng `ProjectFilesPanel` của bản ứng viên. Chọn một trong bảy ca để kiểm nút Bắt đầu phân tích và lý do cho phép/chặn. Có thể bỏ chọn phiên bản trùng hoặc tài liệu ngoài CAD đã được chọn từ trước. Dòng trạng thái phía trên bảng hiển thị các ID đang chọn.

Ca **Chọn vai trò trước khi tải** dùng bản sao đúng `ProjectDossier` của cổng, thay bộ gọi API, lưu phiên, chuyển trang và tải nguyên bản bằng mô phỏng. Chọn tệp thử: bộ đếm vẫn bằng 0 trước khi chọn vai trò và bấm tải. Khi bấm tải, bộ đếm hiển thị tên tệp và vai trò đã chuyển vào bộ nhận giả lập. Nội dung tệp không được đọc hoặc gửi. Đổi ca để đặt lại bộ đếm.

`check-fixture.cjs` kiểm render và bộ nhận giả lập. Việc gửi tệp đến backend và lưu bản vẽ thật nằm ngoài ca kiểm này.
