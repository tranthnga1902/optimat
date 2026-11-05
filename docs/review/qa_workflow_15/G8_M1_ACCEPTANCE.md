# QA tiên lượng G8 — tham chiếu riêng M1

Trạng thái: PREPARED / NOT_RUN. Nhiệm vụ15 là QA độc lập; chỉ ghi thư mục QA15, chờ01 điều phối lượt chạy. Không hardcode số M1 vào sản phẩm/catalog; không dùng chúng xác nhận bản vẽ khác. Không full/TestClient hoặc thử lại upload Tân Bình.

01 xác nhận tiêu chí BOQ cũ đã được thay thế: **Excel Tiên lượng G8 là deliverable bắt buộc**, không chỉ parity tổng lượng. Owner03 chuẩn bị contract server detail rows/precision, 09 sole exporter+tests staging, 02 UI; full225 source HOLD nên QA chỉ chuẩn bị. Chưa có rounding rule cuối từ01. Bằng chứng đọc dưới là cached values từ BIFF/OLE, không trích formula và không chứng minh Excel đã recalculate. Phải tách raw/cached/published/hiển thị và quy tắc rounding được chốt khi nghiệm thu.

## Nguồn và expected nhận bàn giao

Đã đọc local chỉ đọc bằng xlrd (Python -B), không sửa workbook: `C:/Users/Admin/Downloads/2._G8-20261003T022634Z-1-001/2. G8/1. Ho so mau OFFICE/DU TOAN M1.xls`. SHA256 thực đọc khớp `9312133C01B959194447ED90B8FDB0B889B98FB7BB5CC4A078A6DA2FFE0F1CED`. Đây là xác minh dữ liệu nguồn lưu trong file, không phải chạy UI/Excel hoặc tính lại công thức Excel.

`Tien luong!J36` = 3,2515; hàng37/41/46 là tiêu đề nhóm theo bàn giao, không đưa vào 9 dòng. Dữ liệu B, D:I đọc được:

| Hàng | Tên B | Số CK D | Dài E | Rộng F | Cao G | H | Lượng I (m³) |
|---|---|---|---|---|---|---|---|
| 38 | DC-1 | 2 | 0,75 | 2,15 | 0,1 | trống | 0,3225 |
| 39 | DC-2 | 4 | 0,75 | 2,25 | 0,1 | trống | 0,675 |
| 40 | DC-3 | 2 | 0,75 | 1,5 | 0,1 | trống | 0,225 |
| 42 | GM-1 | 2 | 9,93 | 0,5 | 0,1 | trống | 0,993 |
| 43 | GM-2 | 1 | 3,67 | 0,5 | 0,1 | trống | 0,1835 |
| 44 | GM-3 | 2 | 3,67 | 0,5 | 0,1 | trống | 0,367 |
| 45 | GM-4 | 1 | 3,67 | 0,5 | 0,1 | trống | 0,1835 |
| 47 | DT-01 (có khoảng trắng cuối trong ô gốc) | 1 | 5,35 | 0,4 | 0,1 | trống | 0,214 |
| 48 | DT-02 | 2 | 1,1 | 0,4 | 0,1 | trống | 0,088 |

Tổng Decimal của 9 giá trị I = 3,2515, khớp J36. E42 lưu float 9.930000000000001, E43:E45 lưu 3.6699999999999995; bảng trên biểu diễn gọn, không sửa nguồn. H trống không tự coi là dữ liệu thiếu hoặc 0; cần owner giữ đúng ngữ nghĩa hệ số tùy chọn.

`Phân tích VT!B58:E58` thực đọc: AF.11110 / “Bê tông lót móng SX bằng máy trộn, đổ bằng thủ công, M100, đá 4x6, PCB30” / m3 / 3,2515. B60:B63 lần lượt A24.0797A, A24.0180, A24.0010, A24.0524; D đơn vị, E mức dùng, F lượng. Không coi mã M1 là mã catalog OptiMat nếu chưa có mapping được duyệt.

| Vật tư | Định mức cho 1 m³ | Tổng theo sheet được bàn giao | Cơ sở |
|---|---|---|---|
| Xi măng PCB30 | 197,825 kg | 643,228 kg | Riêng AF.11110/M1 |
| Cát vàng | 0,572975 m³ | 1,863 m³ | Riêng AF.11110/M1 |
| Đá 4×6 | 0,92865 m³ | 3,0195 m³ | Riêng AF.11110/M1 |
| Nước | 166,05 lít | 539,9116 lít | Riêng AF.11110/M1 |

Số tổng sheet là expected tham chiếu được cung cấp, không mặc định là tích của các số đã làm tròn hiển thị. Khi mở workbook phải lấy giá trị ô thực/formula và quy tắc làm tròn trước khi kết luận lệch. Lượng vật tư cấp phối không được cộng thêm bê tông trung gian lần nữa.

Đối chiếu số lưu thực đọc (tích Decimal của J36 × E, không khẳng định là công thức gốc):

| Hàng VT | Tích chưa làm tròn | F lưu trong sheet | Tích − F |
|---|---|---|---|
| 60 PCB30 | 643,2279875 kg | 643,228 kg | −0,0000125 kg |
| 61 Cát | 1,8630282125 m³ | 1,863 m³ | +0,0000282125 m³ |
| 62 Đá | 3,019505475 m³ | 3,0195 m³ | +0,000005475 m³ |
| 63 Nước | 539,911575 lít | 539,9116 lít | −0,000025 lít |

Các F tương thích với làm tròn tích theo số chữ số đang lưu (3/3/4/4), nhưng chưa xác minh formula/format hoặc recalculation native. Không dùng nhận xét này như dung sai tự cấp cho sản phẩm.

## Ca nghiệm thu

| ID | Thao tác sau khi được giao lượt | Oracle / bằng chứng |
|---|---|---|
| G8-01 P0 | Đọc 9 dòng gốc và input/formula/đơn vị/nguồn từng dòng; đối chiếu bảng UI | Đủ đúng 9 dòng, đúng đài/giằng/dầm tường và phạm vi M1, không gom mất chi tiết hoặc đếm dòng tổng hai lần; lưu ô nguồn và giá trị từng dòng |
| G8-02 P0 | Tính tổng bằng cơ sở từng dòng gốc và đối chiếu kết quả đã kiểm | Tổng 3,2515 m³ theo M1; ghi riêng số đầy đủ và số hiển thị, không sửa lượng để ép khớp |
| G8-03 P0 | Đối chiếu bốn vật tư theo cùng bản khối lượng/định mức M1 | Đúng mã/loại, đơn vị, cơ sở 1m³ và bốn tổng sheet; không lấy định mức catalog khác làm cùng nguồn; không đổi kg thành số bao khi thiếu quy cách |
| G8-04 P0 | Export Excel từ snapshot đã kiểm rồi mở lại; đối chiếu UI/Excel | Cùng projectUid/drawingId/reviewId và lựa chọn đã xác nhận; đủ 9 dòng/tổng/bốn vật tư trong phạm vi được owner triển khai, không xuất draft hoặc revision cũ; không coi file tạo được là mở lại đạt |
| G8-05 P0 | Dùng bản synthetic thiếu nguồn/định mức/quy cách hoặc chỉ có tổng không có chi tiết | Hiện thiếu và phạm vi phần biết; không tự điền M1 hoặc tạo 9 dòng giả; không đánh đã kiểm/đủ từ nguồn không liên kết |
| G8-06 P0 | Sửa một input, tính/lưu và export lại; quay lại/reload | Invalidation đúng snapshot; UI/Excel mới cùng cơ sở; file cũ không bị trình bày như bản mới |
| G8-07 P1 | Đối chiếu precision từng dòng, tổng trước/sau làm tròn, tích định mức và số sheet | Ghi chênh absolute có đơn vị và nguyên nhân đã chứng minh; không tự đặt dung sai để pass; nếu chưa rõ quy tắc làm tròn ghi BLOCKED/khác biệt cần owner giải thích |

## Phiếu đối chiếu khi có dữ liệu

Mỗi dòng: ô nguồn → giá trị đầy đủ/formula → UI đầy đủ/hiển thị → ô Excel xuất/giá trị mở lại → chênh có đơn vị → nguyên nhân/căn cứ → PASS/FAIL/BLOCKED. Tổng hợp đủ 9 dòng, 1 tổng bê tông và 4 vật tư; đính kèm hash workbook nguồn/xuất, ảnh UI/Excel mở lại, revision và terminal nếu lượt được giao có chạy focused.

Chờ01 xác định owner UI/Excel, phạm vi được release và quy tắc số học. QA15 đã xác minh hash/giá trị lưu và tổng nguồn bằng đọc chỉ đọc; chưa kiểm formula native/render hoặc chạy sản phẩm. Các ca G8-01–07 vẫn NOT_RUN đối với UI/Excel sản phẩm. Ca này không thay nghiệm thu AI đa nhóm hoặc QA ACTUAL-build.
