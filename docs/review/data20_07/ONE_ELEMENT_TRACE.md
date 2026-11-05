# VN002 — truy đúng một hàng thép, chưa duyệt đáp án

ID `D20-07-VN002-WATER-DM1-BAR1`, BUILD `nha_sang_hai_duong_4x15`. Nguồn đã hash lại: KT `719ea17b22b856bb31363fbfc9bf218f312112958e9de4f6638e2ede1f1cf8d6`; KC `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`. Đường dẫn/hash PDF và tọa độ đầy đủ từng số tại [JSON](ONE_ELEMENT_TRACE.json).

## Vị trí tìm lại

PDF kết cấu trang18 **KC-01-12**, bảng **BỂ NƯỚC bên phải**, nhóm **DM-1 (SL:2), STT1**. Không phải bảng bể phốt bên trái. [Ảnh hàng](ONE_ELEMENT_ROW.png); ảnh gốc toàn trang `reports/review_housing_20261103/sang_be_page18.png`.

CAD KC: INSERT **1173553**, block`TK_9`, layer`TEXT_TK`, điểm chèn **x=-1345152.255989423, y=-1068252.078578262**, scale80. Scale80 là tỷ lệ biểu diễn ký hiệu bảng; không nhân vào số kích thước ghi bằngmm. Thuộc tính nằm dưới INSERT này; đường truy `1173553 → handle ATTRIB` trong JSON.

| Số/ý nghĩa | Giá trị gốc | Handle ATTRIB / tag |
| --- | ---: | --- |
| STT/mã thanh | 1 |1173554 / SH |
| Đoạn móc1 |200mm |1173555 / L1 |
| Đoạn giữa |2450mm |1173556 / L2 |
| Đoạn móc2 |200mm |1173557 / L3 |
| Đường kính |12mm |1173558 / DK |
| Chiều dài1thanh |2850mm |1173559 / DAI |
| Số thanh/1 cấu kiện |2 |117355A / SL1 |
| Số thanh toàn nhóm |4 |117355B / SLA |
| Tổng chiều dài |11,4m |117355C / DT |
| Khối lượng in |10,1kg |117355D / TL |

Nhãn nhóm DM-1: TEXT`1173581`; SL2: TEXT`1173582` trên cùng bảng. Mặt cắt DM-1 bể nước ở **trang17 KC-01-11**, phía trên phải, ghi2Ø12 cho lớp tương ứng và SL02; đây là liên kết theo mã/loại, chưa tách hai dầm vật lý. Tầng, trục và từng instance dầm **chưa xác định**, giữNULL; không khẳng định đã nối được vào kiến trúc chỉ vì có cặpKT/KC đúng hash.

Đơn trọng: **trang3 KC-00**, bảng3, dòngØ12 =**0,888kg/m**; [ảnh bảng đơn trọng](ONE_ELEMENT_UNIT_MASS.png). TEXT CAD **10FFADB**, x=-1730268.781144352,y=-1031517.590586386, ghi0.888; nhận diện dòngØ12 bằng bảng PDF, không chỉ tìm mọi chữ0.888. Đây là quy ước đơn trọng trong hồ sơ, không lấy hệ số ngoài hoặc tự suy7850 để thay.

## Phép tính một hàng

`L1thanh=(200+2450+200)/1000=2,850m`.

`N=2thanh/cấu kiện × 2cấu kiện=4thanh`, đã có sẵn trong SLA4.

`ΣL=4×2,850=11,4m`; `m=11,4×0,888=10,1232kg →10,1kg` khi làm tròn cuối đến0,1kg, khớp TL in của **hàng này**. Không nhânSL2 lần nữa sau khi đã dùng4; không dùng tổngØ12=36,9 hoặc tổng bể làm đầu vào.

## Giới hạn và kiểm đã làm

Chiều dài được cộng từ các đoạn hình dạng bảng, chưa đo độc lập đường tim/hình học hoặc giải quyết bán kính uốn/cover. Khớp một hàng không duyệt mọi hàng DM-1 hoặc cả bể. Bảng tổng bể vẫn mâu thuẫn; gate cũ giữ nguyên. PDF/CAD cùng thiết kế không phải hai chứng cứ thiết kế độc lập.

Đã đọc nhỏ một hàng INSERT/ATTRIB và một ô đơn trọng, hash cặp file, kiểm200+2450+200=2850, SLA4, phép tính và làm tròn. Ảnh là trích vùng từ trang PDF đã render có sẵn. Không chạy rough/CAD batch/full suite/DB, không sửa canonical, không gắn `da_kiem`; `human_approval=false`, `verification_status=chua_kiem`. Đề nghị00/01 trình kiểm đúng phạm vi hàng này.
