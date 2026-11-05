# Backend trên Render: DXF và DWG

DXF được đọc trực tiếp bằng ezdxf. DWG được chuyển sang DXF bằng LibreDWG
(`dwg2dxf`), không cần ODA hay giao diện đồ họa. DWF/DWFx chưa đọc trực tiếp:
người dùng cần chuyển sang DXF trước, không chỉ đổi đuôi file.

## Cách nhanh: Blueprint (`render.yaml`)

`render.yaml` ở gốc repository khai 3 phần: `optimat-api` (Docker), `optimat-web` (Next.js), `optimat-db` (PostgreSQL 16).

1. Push repository lên GitHub, rồi trên Render chọn **New > Blueprint** và chọn repository đó.
2. Render hỏi các biến `sync: false`: điền `OPENAI_API_KEY` (để trống nếu không dùng trợ lý AI); `OPTIMAT_API` để
   trống ở lần đầu.
3. Khi `optimat-api` chạy xong, chép URL của nó (vd. `https://optimat-api.onrender.com`) vào biến `OPTIMAT_API` của
   `optimat-web`, rồi **Manual Deploy**. Rewrite `/api` được đọc lúc build, nên đổi biến này thì phải build lại.
4. Tạo bảng và nạp danh mục từ máy cá nhân, dùng **External Database URL** của `optimat-db`:
   ```powershell
   $env:DATABASE_URL = "<External Database URL>"
   .venv\Scripts\python.exe scripts\init_db.py
   .venv\Scripts\python.exe scripts\create_admin.py --email <email>
   ```
   Tạo admin ngay: khi database chưa có admin, ai mở `/dang-nhap` cũng tạo được admin.

`DATABASE_URL` của Render có dạng `postgresql://...`; `db/session.py` tự đổi sang `postgresql+psycopg://`.
Mọi thành phần đang ở gói **free** (không cần thẻ):
- Web service ngủ sau 15 phút không có truy cập, lần mở sau chờ khoảng 1 phút; 512 MB RAM, hết bộ nhớ khi đọc
  bản vẽ lớn hoặc chạy NSGA-II thì nâng `optimat-api` lên Starter/Standard.
- PostgreSQL free bị Render **xóa sau 30 ngày**. Muốn giữ lâu: tạo database miễn phí ở https://neon.tech, xóa
  khối `databases:` và đổi `DATABASE_URL` trong `render.yaml` thành `sync: false`, rồi dán URL của Neon.

## Cấu hình Render thủ công

1. Tạo Web Service từ repository. Nếu repository chứa thư mục `optimat-ai`,
   đặt Root Directory là `optimat-ai`; nếu đây đã là gốc repository thì để trống.
2. Chọn Language **Docker**, Dockerfile Path **./Dockerfile**.
   Dockerfile này chỉ chạy backend; frontend Next.js triển khai riêng và trỏ
   `OPTIMAT_API` về URL backend trước khi build (theo cấu hình proxy hiện có).
3. Để Docker Command trống, dùng CMD trong Dockerfile với cổng `$PORT`.
4. Đặt Health Check Path `/api/health`. JSON phải có
   `dwg_converter_available: true` sau khi deploy.
5. Khai báo `DATABASE_URL` và các biến môi trường ứng dụng cần dùng trên Render.
   Không đưa `.env` từ máy cá nhân vào image. Nếu cần giữ file tải lên qua các lần
   deploy, cấu hình lưu trữ bền vững riêng; filesystem mặc định không giữ dữ liệu.

Docker build biên dịch LibreDWG 0.13.3 từ bản phát hành GNU và kiểm tra binary bằng
`dwg2dxf --version`. Không cài LibreDWG qua pip.

## Máy cá nhân

Cài `dwg2dxf` vào PATH hoặc đặt `LIBREDWG_CONVERTER_PATH` trỏ tới executable.
Hệ thống ưu tiên LibreDWG; ODA vẫn dùng được khi không tìm thấy LibreDWG.

## Kiểm tra trước khi dùng kết quả

Tải DXF mẫu, rồi DWG thực tế và đối chiếu layer, block, kích thước và khối lượng
với bản DXF xuất từ CAD. Chuyển đổi thành công không bảo đảm mọi đối tượng CAD
đều được giữ nguyên. DWF chưa có bộ chuyển đổi tự động trong phiên bản này.

Tài liệu: https://render.com/docs/docker
và https://www.gnu.org/software/libredwg/manual/html_node/Programs.html
