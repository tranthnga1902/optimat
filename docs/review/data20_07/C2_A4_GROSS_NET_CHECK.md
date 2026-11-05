# Kiểm07 — một đoạn C-2 tại4/A, VN002

Đã đọc đề nghị00 `docs/review/data20_00/VN002_C2_A4.md`, xem ảnhchi tiết trang22 và sàn trang24, đối chiếu mã nguồn chỉ đọc. Không lặp đoCAD hoặc tạo lần chạy ứng dụng.

- Ảnhchi tiết cộtC-2 cho hai cạnh220mm, cao độ+3,150/+6,750: chênh3600mm. Ảnhsàn tầng3 tại nút4/A ghiH120mm và+6,750. Trong phạm vi nguồn này, phép tính gross **1×0,22×0,22×3,6=0,174240m³** đúng số học.
- `src/optimat/rough/columns.py:242` lấy `hc=(height_mm−slab)/1000`; nhánh cột mặt bằng dùng thể tích theohc. Nếu áp đúng nhánh/quy ước này, net **1×0,22×0,22×(3,6−0,12)=0,168432m³**, khoản phân bổ lớp sàn **0,005808m³**. GiữN=1 dù chi tiết loạiC-2 ghiSL02; không nhân cột4/B hoặc tầng khác.
- Nhánh công tác dầm có cơ chế chặn chiều dài theo vùngcột tại `beams.py:106` trở đi; chiều cao bê tông dầm thường trừ dày sàn. Phải kiểm lần chạy thực có ranh sàn/đầu dầm tương ứng để bảo đảm nút không đếm trùng; đọc mã không chứng minh geometry snapshot đã đúng.
- **Không trừ thêm400mm của dầm** khi đã chọn quy ước cột đến đáy sàn và dầm chặn tại cột. Trừ thêm sẽ thay quy tắc phân bổ nút; cần một phương án giao cột–dầm–sàn nhất quán riêng nếu muốn dùng cách đó.

Kết luận cho01/00: đồng ý phép tính gross/net **trong phạm vi quy ước nhánh cột mặt bằng đã nêu**, chưa xác nhận lượng thanh toán hoặc toànBOQ. Hai số là hai cơ sở lượng của cùng đoạn, không cộng với nhau. Nguồn cao độ/tiết diện/sàn có trong ảnhđã xem; liên kết vị tríC-2 tại4/A dựa trên ảnhtrang19 và truy vết00, lượt07 chưa đo lạiCAD vị trí. Chưa có biên nhận một dòng qua ứng dụng hoặc reviewer người thật; giữchua_kiem. Không DB/source/canonical/test hoặc thay schema20bảng.
