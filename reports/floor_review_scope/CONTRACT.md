# Phạm vi kiểm theo tầng

- Hai màn hình dùng cùng bộ chọn. Người dùng có thể đổi lựa chọn ngay ở bước 3, kể cả với hồ sơ cũ còn hình chưa phân loại.
- `reviewSelection` là các hình thuộc những tầng đang đánh dấu. `reviewScope` là phạm vi đã mở bằng nút Kiểm tra. Cả hai lưu theo phiên bản dự án và bản vẽ. Số trên nút đếm nhóm tầng. Khi bỏ tất cả, nút tắt và lần kiểm trước vẫn còn.
- Chọn một tầng đưa tất cả hình của tầng đó vào danh sách xem. Chỉ hình do người dùng chọn tính mới được gửi xác nhận. Nhiều hình tính cùng tầng phải được giải quyết trước khi cộng. Hình hỗn hợp hoặc không rõ không tự tách tầng. Cảnh báo theo hình giữ ở đúng nhóm.
- `confirmationGuide`, khôi phục, tính phần thô và chọn vật liệu dùng cùng danh sách chỉ mục gốc. Dữ liệu ngoài nhóm vẫn có trong phiên, không tự đổi sang tham khảo. Tổng và công tác ở bước 3 mang nhãn phạm vi đã chọn. Nguồn kết cấu toàn nhà chưa có liên kết tầng không được dùng như số liệu riêng của tập con.
- Khi đổi phạm vi, kết quả phần thô, biên nhận kiểm và bản nháp vật liệu của nhóm trước được lưu riêng. Giao dịch ghi phiên và các dữ liệu đang dùng phải thành công trước khi mở nhóm mới. Khôi phục kết quả yêu cầu cùng phiên bản bản vẽ.
- Gói giao diện độc lập với bản sửa kích thước lỗ mở. Trạng thái nghiệm thu của từng cổng được ghi trong biên bản kiểm thử sau khi hoàn tất.
