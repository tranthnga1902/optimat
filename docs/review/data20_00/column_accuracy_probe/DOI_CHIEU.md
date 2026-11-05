# Kiểm độ chính xác khi bóc cột · 04/11/2026

## Nhận diện hình trong DXF thử

[Tệp DXF thử](column_outline_sample.dxf) có một đường bao cột chữ nhật 225 × 335 mm, một đường chéo rời và một nét chữ L hở. Cả ba đặt trên cùng layer. Cùng byte đầu vào và cùng chuỗi đọc DXF → nhận cột → tính công tác, với chiều cao tầng 3.600 mm và sàn 120 mm.

| Kết quả | Trước sửa | Sau sửa |
|---|---:|---:|
| Số cột | 3 | 1 |
| Tiết diện bộ đọc trả về | 220 × 340 mm | 225 × 335 mm |
| Bê tông trả về, làm tròn tới 0,001 m³ | 0,781 m³ | 0,262 m³ |

Đối chứng tay: 0,225 × 0,335 × (3,600 − 0,120) = 0,262305 m³. [Biên nhận trước](before.json) · [Biên nhận sau](after.json). Bản sửa còn giữ danh tính của polyline kín qua block để hai đường bao chung cạnh, chung góc, có nét nối hoặc khe 0,4 mm vẫn phân biệt được trong bốn ca kiểm. [Biên nhận bốn ca và hồi quy](../../data20_05/column_contour_fix/v2_receipt.json).

## Kiểm bằng tệp kết cấu VN002

Với DXF KC có SHA-256 `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`, lượt trước sửa không sinh bản ghi cột vật lý. Lượt đọc bằng mã sản phẩm sau sửa tách được C-2 ở 4/A và 4/B. Riêng tại 4/A, khoảng từ +3,150 đến +6,750 m có tiết diện 220 × 220 mm, dòng gross là 0,17424 m³ như đối chứng tay. Ghi chú sàn 120 mm mới là ứng viên; khi chưa nối chắc với vùng sàn tại nút, khoản trừ và lượng sau trừ để trống. Dữ liệu này là kết quả chạy bộ đọc và tính lượng trên DXF kết cấu, chưa là nghiệm thu UI, toàn nhà hoặc đáp án thi công đã duyệt.

[Đầu ra bộ đọc thực](../../data20_03/column_fix/reader_actual/final/reader.json) · [Đối chứng tay và tờ nguồn](../VN002_C2_A4.md)
