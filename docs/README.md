# Tài liệu đi kèm

Hiện hành: [CSDL 20 bảng](schema/CSDL_20_BANG.md) và [kế hoạch dữ liệu sáu tuần](KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md). Các bản 19/23/26/28/45 bảng được giữ để đối chiếu lịch sử, không dùng làm schema triển khai.

| Thư mục | Nội dung | Ai sửa, sửa thế nào |
|---|---|---|
| `de-cuong/` | Đề cương, đề cương chi tiết, bảng kế hoạch (Word) | Sửa trực tiếp bằng Word |
| `du-lieu/` | Mẫu thu thập đại lý; sổ quản lý cơ sở dữ liệu (từ điển dữ liệu bản cũ 19 bảng; lược đồ hiện tại 26 bảng xem `TONG_HOP_DU_LIEU.md`) | Điền đại lý vào mẫu, rồi nạp vào `suppliers`, `supplier_materials` |
| `luu-tru/` | Bản cũ đã được thay thế, giữ để đối chiếu | Không sửa |
| `QUY_TRINH_DU_LIEU.md` | Quy trình vừa phát triển vừa kiểm soát dữ liệu | |
| `schema/CSDL_20_BANG.md` | Schema hiện hành, 20 bảng và ánh xạ view | Đối chiếu schema20.py và compat20.py |
| `KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md` | Dữ liệu, sáu tuần và tiêu chí nghiệm thu | Cập nhật theo nguồn đã xác minh |
| `TONG_HOP_DU_LIEU.md` | Kiểm kê lịch sử và định nghĩa dữ liệu đầu vào | Tra cùng đặc tả 20 bảng |

Nguồn dữ liệu vật liệu duy nhất là `data/catalog/materials_master.xlsx` (không nằm trong thư mục này).
