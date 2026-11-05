# Kiểm riêng vị trí bể nước trang11 — VN002

## Kết luận trực tiếp từ nguồn

[Ảnh toàn trang11](WATER_LOCATION_PAGE11.png) giữ đủ khung tên **KC-01-05 — MẶT BẰNG XÂY TƯỜNG MÓNG**, trục1/2/3/4 vàA/B. [Phóng vùng bể và DIM](WATER_LOCATION_DIMS.png) cho thấy chữ **BỂ NƯỚC** trong ô **1–2/A–B**, kích thước ngang2500, đứng2000; mép phải cách trục2 **890mm**, mép dưới cách trụcA **390mm**.

Đọc độc lập DIM CAD trên KC đúng hash `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`, không chỉ chép kết luận00. [JSON DIM có các điểm định nghĩa](WATER_LOCATION_DIM_ENTITIES.json) lưu cả các DIM lân cận để nhận diện đúng vùng, không dùngDIM của bể phốt bên phải.

| Nguồn | Handle | Nội dung/điểm CAD |
| --- | --- | --- |
| Tiêu đề hình | TEXT1169EF0 | Mặt bằng xây tường móng, x=−1694546,616832;y=−1056256,090979 |
| Chữ trong vùng bể | TEXT116C7C4 | Bể nước, x=−1696830,008452;y=−1061723,787001 |
| Ngang bể | DIM116C817 |2500; hai mốcx=−1697171,086111 và−1694671,086111 |
| Mép phải→trục2 | DIM116C824 |890; mốcx=−1694671,086111 và−1693781,086111 |
| Chiều đứng bể | DIM116C831 |2000; hai mốcy=−1061260,847574 và−1063260,847574 |
| **Mép dưới→trụcA** | **DIM116C83E** | **390**; mốcy=−1063260,847574 và−1063650,847574 |

BốnDIM nêu trên có text rỗng (không có override), measurement lần lượt2500/890/2000/390. Đơn vịmm đọc trên kích thước hồ sơ và quy ước kích thước; tọa độ là CAD modelspace, không phải tọa độ thi công. Đầu mốcDIM đối chiếu vị trí đường dóng/trục trên ảnh, không gọi defpoint là tim dầm.

Trang11 có các nhãnTM/BT cho công tác móng, nhưng vùng bể nước không cho thấy nhãnDM-1 gắn trực tiếp từng cạnh. Chưa đủ căn cứ gắn một cạnh mặt bằng tổng thể với một ID dầmDM-1 chỉ từ kích thước.

## Suy luận có điều kiện, không phải liên kết đã duyệt

Trang17 KC-01-11 ghi **CHI TIẾT BỂ NƯỚC**, phủ bì2500 theo phương đứng và2000 theo phương ngang; trang11 là2500 ngang/2000 đứng. Hai hình phù hợp về kích thước nếu đổi phương (ứng viên phép xoay±90°, và vẫn cần loại khả năng đối xứng). ChữBỂ NƯỚC/kích thước hỗ trợ quan hệ cùng loại chi tiết, chưa xác định duy nhất chiều xoay hoặc ánh xạ từng cạnh.

Không lấy “cạnh dọc trái/phải trang17” tự đổi thành “cạnh gần trụcA/B trang11”. Hai tênA/B trong báo cáo [haiDM-1](TWO_DM1_WATER_POSITIONS.md) là **mã định vị kiểm**, hoàn toàn khác trụcA/B công trình ở trang11. Khi trình tiếp nên gọi rõ **DM1-vị trí trái hình17** và **DM1-vị trí phải hình17** để tránh nhầm.

## Phần còn thiếu giữNULL

- Ánh xạ `DM1-trái-hình17 → cạnh cụ thể hình11` và `DM1-phải-hình17 → cạnh cụ thể hình11`: **NULL**, cần mốc chung có hướng (tuyến mặt cắt/lỗ cửa thăm/đặc điểm không đối xứng hoặc nhãn dẫn chi tiết) xác định được trên cả hai hình.
- ID hai dầm vật lý, tầng/tênlevel và transform hình17→hình11: **NULL**. Chỉ xác định được vùngbể trên mặt bằng móng; không suy tên tầng từ cao độ cục bộ.
- Tuyến1–1/2–2 là tuyến mặt cắt ở hình17, không đổi thành trục công trình. Bản thânSL02 không định vị hai cạnh.

Có thể trình chủ đồ án xác nhận hẹp: vị trí vùngbể ô1–2/A–B và bốn kích thước trên. Không gộp xác nhận này thành phê duyệt ánh xạ haiDM-1/tổng thép/bể. Giữ `chua_kiem`; không sửa filegốc/canonical hoặc truy vết cũ. Lượt này chỉ render1trangPDF và đọc cácDIM vùng nhỏ; không rough/full/DB/demo/AI.
