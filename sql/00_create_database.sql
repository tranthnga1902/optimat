-- Chạy MỘT LẦN trong DBeaver khi đang kết nối bằng tài khoản postgres (database postgres).
-- Đổi 'matkhau' thành mật khẩu của bạn. Chạy từng lệnh một (Ctrl+Enter), vì CREATE DATABASE
-- không chạy được trong cùng một giao dịch với lệnh khác.

CREATE USER optimat PASSWORD 'matkhau';

-- Bắt buộc mã hóa UTF8 vì dữ liệu có tiếng Việt.
CREATE DATABASE optimat OWNER optimat ENCODING 'UTF8' TEMPLATE template0;

-- Database riêng cho pytest (bài kiểm thử xóa và tạo lại toàn bộ bảng trong này).
CREATE DATABASE optimat_test OWNER optimat ENCODING 'UTF8' TEMPLATE template0;
