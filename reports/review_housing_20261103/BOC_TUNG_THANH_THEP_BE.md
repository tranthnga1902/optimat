# Bóc lại từng mã thanh thép bể Hương và Sang — 03/11/2026

Đã tính lại **42 mã thanh** từ chiều dài hình dạng và số thanh × số cấu kiện, không dùng ô trọng lượng/KLCT/tổng hợp làm đầu vào phép tính. Kết quả chi tiết tại [JSON từng thanh](be_tung_thanh_recalculation.json). **Chưa chốt tổng bể làm đáp án chuẩn:** số thanh bố trí, một số quy tắc uốn và nắp cửa thăm còn mâu thuẫn/thiếu căn cứ. Không sửa dữ liệu normalized, mã, trạng thái duyệt hay DB.

## Cách tính

`L_toàn_bộ = L_một_thanh × số_thanh_mỗi_cấu_kiện × số_cấu_kiện`; `m = L_toàn_bộ × π/4 × (d/1000)² × 7850` kg. Khối lượng riêng 7850 kg/m³ là giả thiết tính khối lượng lý thuyết được khai báo, không phải xác nhận tiêu chuẩn/hợp đồng. Không cộng hệ số 1,1, không làm tròn từng dòng trước khi cộng. JSON có phương án phụ dùng bảng kg/m đã khai báo (Ø6 .222, Ø8 .395, Ø10 .617, Ø12 .888) để thấy ảnh hưởng quy ước trọng lượng; không trộn hai cách.

Các thanh thẳng/U góc: cộng kích thước các đoạn ghi trên hình dạng, theo quy ước chiều dài triển khai hồ sơ; chưa hiệu chỉnh riêng bán kính uốn. Đai Ø6: `2×(170+250)+2×60=960 mm`, khớp hình và chiều dài ghi. Thanh cong Ø8 mã3 tấm đan có đoạn150/150/70/70 và cung có ký hiệu60; tạm giữ chiều dài triển khai ghi628 mm, **chưa coi là chiều dài tính độc lập hoàn toàn** vì chưa xác định chắc quy ước bán kính/đường tim. Mọi dòng như vậy được đánh dấu riêng trong JSON.

## Nguồn và kiểm bố trí

- Hương chi tiết: [PDF trang13 KC-01-07](huong_be_page13.png); hình dạng thanh: [PDF trang14 KC-01-08](huong_be_page14.png), [phóng to các mã thanh](huong_be_bar_shapes.png).
- Sang bể phốt: [trang16 KC-01-10](sang_be_page16.png); bể nước: [trang17 KC-01-11](sang_be_page17.png); hình dạng và bảng thanh: [trang18 KC-01-12](sang_be_page18.png).
- Số lượng DM-1/DM-2 đều2 cấu kiện; thanh chủ trên/dưới mỗi mã2 thanh/cấu kiện, đối chiếu mặt cắt. Hương tấm đan TĐ-1/TĐ-2 mỗi loại4 tấm, mỗi tấm6 thanh dọc; Sang bể phốt cũng4 tấm mỗi loại, mỗi tấm6 thanh dọc. Những số này có căn cứ hình chi tiết, không chỉ ô tổng.
- Số đai, số thanh theo a150 và a600 phải xác định mép bắt đầu/kết thúc và phủ bì/lớp bảo vệ trước khi duyệt số lượng. JSON giữ số thanh bảng và gắn trạng thái chờ đối chiếu bố trí, không mặc nhiên công nhận.

## Các số có thể xác định trong phạm vi hẹp

**Thép chủ Ø12 dầm bể**: số lượng2+2 thanh/mặt cắt và2 dầm/mỗi loại có trên chi tiết; chiều dài đoạn thẳng và móc có trên hình dạng thanh. Hương: `(3,35+3,45+2,85+2,95)×4=50,4 m`, lý thuyết **44,745830 kg**. Sang mỗi bể: `(2,85+2,95+2,35+2,45)×4=42,4 m`, lý thuyết **37,643317 kg**. Nếu trình đến0,1kg theo cách tính này: Hương44,7kg, Sang37,6kg; khác với việc cộng số mỗi dòng đã làm tròn. Không chọn ô tổng43,6kg Hương hoặc36,9kg bể nước Sang làm khối lượng chủ Ø12 theo các chi tiết này. Còn chờ thống nhất quy ước chiều dài uốn và đơn trọng trước ghi nhãn chuẩn.

Đây là kết quả từng thanh theo chi tiết hiện có, không xác nhận toàn bộ bể hoặc sai số độc lập. CAD/PDF cùng thiết kế không phải hai nguồn độc lập.

## Bảng từng mã thanh

Các số lượng có dấu sao trong cột căn cứ vẫn lấy từ bảng thanh, cần kiểm bố trí; không chốt tổng từ chúng. Chiều dài các đoạn và số cấu kiện ở các hàng khác đã đối chiếu chi tiết như trên.

### huong — be_phot

| Nhóm-mã | Ø mm | Cộng đoạn / L mm | Thanh/CK × CK | Tổng m | Lý thuyết kg | Căn cứ còn thiếu |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| day-1 | 10 | 110+2950+110 | 26 × 1 | 82.42000 | 50.815026 | * Kiểm số thanh theo bố trí |
| day-2 | 10 | 110+2450+110 | 40 × 1 | 106.80000 | 65.846211 | * Kiểm số thanh theo bố trí |
| day-3 | 10 | 200+100+200+100+200 | 20 × 1 | 16.00000 | 9.864601 | * Kiểm số thanh theo bố trí |
| DM1-1 | 12 | 200+2950+200 | 2 × 2 | 13.40000 | 11.896709 | Quy ước triển khai uốn nếu có |
| DM1-2 | 12 | 250+2950+250 | 2 × 2 | 13.80000 | 12.251834 | Quy ước triển khai uốn nếu có |
| DM1-3 | 6 | 170+250+170+250+60+60 | 21 × 2 | 40.32000 | 8.949166 | * Kiểm đầu/cuối đai |
| DM2-1 | 12 | 200+2450+200 | 2 × 2 | 11.40000 | 10.121081 | Quy ước triển khai uốn nếu có |
| DM2-2 | 12 | 250+2450+250 | 2 × 2 | 11.80000 | 10.476206 | Quy ước triển khai uốn nếu có |
| DM2-3 | 6 | 170+250+170+250+60+60 | 18 × 2 | 34.56000 | 7.670714 | * Kiểm đầu/cuối đai |
| TD1-1 | 10 | 1470 | 6 × 4 | 35.28000 | 21.751445 | Quy ước triển khai uốn nếu có |
| TD1-2 | 8 | 80+520+80 | 11 × 4 | 29.92000 | 11.805954 | * Kiểm phân bố thanh/đường cong |
| TD1-3 | 8 | 628 ghi trên hình, cung chưa chốt | 3 × 4 | 7.53600 | 2.973585 | * Kiểm phân bố thanh/đường cong |
| TD2-1 | 10 | 1230 | 6 × 4 | 29.52000 | 18.200189 | Quy ước triển khai uốn nếu có |
| TD2-2 | 8 | 80+520+80 | 9 × 4 | 24.48000 | 9.659417 | * Kiểm phân bố thanh/đường cong |
| TD2-3 | 8 | 628 ghi trên hình, cung chưa chốt | 3 × 4 | 7.53600 | 2.973585 | * Kiểm phân bố thanh/đường cong |

Tổng có điều kiện theo số thanh trong bảng: **255.255723 kg** lý thuyết; **255.422340 kg** theo bảng đơn trọng phụ. Đây **không phải tổng bể đã chốt**.

### sang — be_phot

| Nhóm-mã | Ø mm | Cộng đoạn / L mm | Thanh/CK × CK | Tổng m | Lý thuyết kg | Căn cứ còn thiếu |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| day-1 | 10 | 110+2450+110 | 22 × 1 | 58.74000 | 36.215416 | * Kiểm số thanh theo bố trí |
| day-2 | 10 | 110+1950+110 | 30 × 1 | 65.10000 | 40.136595 | * Kiểm số thanh theo bố trí |
| day-3 | 10 | 200+100+200+100+200 | 16 × 1 | 12.80000 | 7.891681 | * Kiểm số thanh theo bố trí |
| DM1-1 | 12 | 200+2450+200 | 2 × 2 | 11.40000 | 10.121081 | Quy ước triển khai uốn nếu có |
| DM1-2 | 12 | 250+2450+250 | 2 × 2 | 11.80000 | 10.476206 | Quy ước triển khai uốn nếu có |
| DM1-3 | 6 | 170+250+170+250+60+60 | 18 × 2 | 34.56000 | 7.670714 | * Kiểm đầu/cuối đai |
| DM2-1 | 12 | 200+1950+200 | 2 × 2 | 9.40000 | 8.345452 | Quy ước triển khai uốn nếu có |
| DM2-2 | 12 | 250+1950+250 | 2 × 2 | 9.80000 | 8.700578 | Quy ước triển khai uốn nếu có |
| DM2-3 | 6 | 170+250+170+250+60+60 | 14 × 2 | 26.88000 | 5.966111 | * Kiểm đầu/cuối đai |
| TD1-1 | 10 | 1270 | 6 × 4 | 30.48000 | 18.792065 | Quy ước triển khai uốn nếu có |
| TD1-2 | 8 | 80+380+80 | 11 × 4 | 23.76000 | 9.375317 | * Kiểm phân bố thanh/đường cong |
| TD1-3 | 8 | 628 ghi trên hình, cung chưa chốt | 3 × 4 | 7.53600 | 2.973585 | * Kiểm phân bố thanh/đường cong |
| TD2-1 | 10 | 930 | 6 × 4 | 22.32000 | 13.761118 | Quy ước triển khai uốn nếu có |
| TD2-2 | 8 | 80+380+80 | 9 × 4 | 19.44000 | 7.670714 | * Kiểm phân bố thanh/đường cong |
| TD2-3 | 8 | 628 ghi trên hình, cung chưa chốt | 3 × 4 | 7.53600 | 2.973585 | * Kiểm phân bố thanh/đường cong |

Tổng có điều kiện theo số thanh trong bảng: **191.070218 kg** lý thuyết; **191.192800 kg** theo bảng đơn trọng phụ. Đây **không phải tổng bể đã chốt**.

### sang — be_nuoc

| Nhóm-mã | Ø mm | Cộng đoạn / L mm | Thanh/CK × CK | Tổng m | Lý thuyết kg | Căn cứ còn thiếu |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| day-1 | 10 | 110+2450+110 | 22 × 1 | 58.74000 | 36.215416 | * Kiểm số thanh theo bố trí |
| day-2 | 10 | 110+1950+110 | 30 × 1 | 65.10000 | 40.136595 | * Kiểm số thanh theo bố trí |
| day-3 | 10 | 200+100+200+100+200 | 16 × 1 | 12.80000 | 7.891681 | * Kiểm số thanh theo bố trí |
| DM1-1 | 12 | 200+2450+200 | 2 × 2 | 11.40000 | 10.121081 | Quy ước triển khai uốn nếu có |
| DM1-2 | 12 | 250+2450+250 | 2 × 2 | 11.80000 | 10.476206 | Quy ước triển khai uốn nếu có |
| DM1-3 | 6 | 170+250+170+250+60+60 | 18 × 2 | 34.56000 | 7.670714 | * Kiểm đầu/cuối đai |
| DM2-1 | 12 | 200+1950+200 | 2 × 2 | 9.40000 | 8.345452 | Quy ước triển khai uốn nếu có |
| DM2-2 | 12 | 250+1950+250 | 2 × 2 | 9.80000 | 8.700578 | Quy ước triển khai uốn nếu có |
| DM2-3 | 6 | 170+250+170+250+60+60 | 14 × 2 | 26.88000 | 5.966111 | * Kiểm đầu/cuối đai |
| nap-1 | 10 | 110+2450+110 | 22 × 1 | 58.74000 | 36.215416 | * Kiểm số thanh theo bố trí |
| nap-2 | 10 | 110+1950+110 | 30 × 1 | 65.10000 | 40.136595 | * Kiểm số thanh theo bố trí |
| nap-3 | 10 | 200+100+200+100+200 | 16 × 1 | 12.80000 | 7.891681 | * Kiểm số thanh theo bố trí |

Tổng có điều kiện theo số thanh trong bảng: **219.767525 kg** lý thuyết; **219.904640 kg** theo bảng đơn trọng phụ. Đây **không phải tổng bể đã chốt**.

## Vì sao chưa thể chốt tổng bể từ bản vẽ này

1. **Số thanh đáy/nắp theo a150 chưa thống nhất với bảng**: Hương đáy ghi hai lớp Ø10 a150, bảng mã1 có26 thanh, mã2 có40. Sang đáy có22/30; nắp bể nước cũng22/30. Các chiều phủ bì Hương3000×2500, Sang2500×2000 và chiều đoạn thẳng tương ứng2950/2450 hoặc2450/1950 không tự giải thích được mọi số thanh này theo cùng quy tắc mép. Ví dụ lấy chính đoạn thẳng2450 mm làm khoảng rải, `floor(2450/150)+1=17` vị trí/lớp (34 cho hai lớp), không phải26 hoặc22. **Đây chỉ là kiểm phát hiện mâu thuẫn, chưa khẳng định34 là đáp án**: cần chỉ rõ miền rải, lớp bảo vệ, thanh mép, có/không rải lên dầm và lỗ mở. Không tự chọn floor/ceil để khớp bảng.
2. **Chân chó Ø10**: hình dạng800 mm có thể cộng200+100+200+100+200, nhưng số20 Hương/16 Sang phải kiểm bố trí a600×600 và vùng rải; chưa có sơ đồ đếm từng vị trí đủ rõ. Nắp bể nước không tự động sao số chân chó đáy khi có lỗ mở.
3. **Nắp cửa thăm bể nước Sang**: trang17 có chi tiết nắp riêng, Ø8 a200 hai phương và một Ø10 (mã3), kích thước700/800, chênh mép50 và chiều dày80; bảng trang18 không có nhóm nắp cửa thăm riêng. Cần xác định số nắp, chiều dài/móc, đếm thanh, và thanh sàn bị cắt qua lỗ; chưa cộng bù một lượng đoán vào tổng.
4. **Bảng Hương tự mâu thuẫn ở nhiều tầng**: riêng mã đáy10-1/2/3 phải tính từ L và N; ba số khối lượng in50,8+65,8+9,9=126,5 khác KLCT124,8. Tính mới từng thanh cho nhóm đáy không dùng cả hai số này; tổng bể theo số thanh bảng vì thế cũng khác phép cộng KLCT253,7 hoặc ô tổng250,6.
5. **Thanh cong tấm đan và đai**: chưa chốt quy tắc đường tim/bán kính uốn, lớp bảo vệ và điểm bắt đầu/kết thúc rải. Không có căn cứ để đổi chiều dài/móc hay tăng giảm số lượng nhằm ép khớp tổng.

## Kết quả bàn giao

Đã bóc lại 42 mã theo từng thanh và tách rõ căn cứ từ chi tiết/số lấy bảng; đã tự kiểm tổng chiều dài, số thanh×số cấu kiện, tổng theo đường kính, và phép tính độc lập nhómØ12. Không chạy suite, không DB. Số44,745830kg Hương và37,643317kg mỗi bể Sang là kết quả hẹp của các mã thép chủØ12 theo chiều dài triển khai hiện có. Tổng toàn bể vẫn chưa chốt; cần quyết định miền rải/số thanh, cửa thăm và quy ước uốn trước khi chuyển JSON này thành đáp án chuẩn. Không phê duyệt thay chủ đồ án.
