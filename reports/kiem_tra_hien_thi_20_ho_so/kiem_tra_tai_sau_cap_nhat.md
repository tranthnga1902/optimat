# Kiểm tra tải tệp sau cập nhật

- Trang quản trị tại `http://127.0.0.1:3000/du-an` hiển thị 20 dự án SYNTHETIC, mỗi dự án 5 tệp. Chi tiết P01 hiển thị 5 nút tải và kết quả “Nhà giả lập - Chưa xác nhận”.
- Nhấn nút tải `P01_ban_ve.pdf`: giao diện hiển thị `Not Found`; sự kiện tải về không xuất hiện trong 15 giây. Thử nút DXF cũng không quan sát được tệp tải về; không suy diễn kết quả 98 tệp còn lại.
- Điều hướng trực tiếp qua Next tới `/api/admin/projects/3/files/28`: nội dung phản hồi `{"detail":"Not Found"}`. Điều hướng trực tiếp backend port 8000 cùng route: nội dung phản hồi `{"detail":"Not Found"}`.
- Đọc `http://127.0.0.1:8000/openapi.json` trong phiên trình duyệt hiện tại: danh sách các route dự án quản trị chỉ gồm `/api/admin/projects` và `/api/admin/projects/{project_id}`; chưa có route tải tệp. Điều này phù hợp với lỗi `Not Found` quan sát được.
- Mã nguồn đã được áp route tải sau thời điểm tiến trình backend có thể đã khởi động. Vì vậy, kết quả OpenAPI chỉ chứng minh **phiên backend được kiểm tra chưa công bố route**, chưa chứng minh bản vá mã nguồn sai. Cần xác định phiên bản đang nạp và kiểm tra lại OpenAPI sau khi chủ sở hữu môi trường nạp lại API.
- Công cụ điều khiển trình duyệt không xuất status và response headers của các lần điều hướng này. Không khẳng định status HTTP cụ thể, content-type hoặc SHA của payload tải; đã kiểm 0/100 tệp tải thành công qua HTTP. Mã băm trên đĩa trong ma trận trước không phải kết quả HTTP.
- Không reset phiên, đổi owner, sửa database, khởi động lại dịch vụ hoặc nhập lại. Cần xác định đúng tiến trình backend mà Next proxy tới và nạp phiên bản đã có route; sau đó mới thực hiện lại đủ 100 lượt tải và so byte/header/SHA.
