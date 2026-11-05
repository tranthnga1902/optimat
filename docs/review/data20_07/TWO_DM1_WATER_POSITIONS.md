# Hai vị trí DM-1 bể nước VN002 — chưa duyệt đáp án

Đúng fileKC `data/drawings/build/nha_sang_hai_duong_4x15_ket_cau.dxf`, SHA-256 `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`; cặpKT đã khóa `719ea17b22b856bb31363fbfc9bf218f312112958e9de4f6638e2ede1f1cf8d6`. Chi tiết số liệu trong [JSON truy vết](TWO_DM1_WATER_TRACE.json). Không sửa ONE_ELEMENT_TRACE cũ.

## Ngữ cảnh đúng bể

[Ảnh toàn trang17 KC-01-11](TWO_DM1_WATER_CONTEXT.png) có khung tên **CHI TIẾT BỂ NƯỚC**. [Ảnh mặt bằng đáy](TWO_DM1_WATER_PLAN.png) giữ tiêu đề **MẶT BẰNG THÉP ĐÁY BỂ NƯỚC**, hai nhãnDM-1 vàDM-2. Trang16 KC-01-10 là bể phốt, không dùng để xác định hai vị trí này. Tiêu đề mặt bằng CAD handle`11731F9`; khung tên`1172211`. Các chữ legacy được giữ nguyên raw trong JSON và đọc qua ảnhPDF, không sửa fileCAD.

**A/B là tên định vị trong báo cáo**, không phải trục hoặc mã thiết kế. Hai vị trí có bằng chứng nhãn và leader trực tiếp, không chỉ suy từSL2:

| Vị trí | Chữ nguồn / handle / layer | Tọa độ chữCAD x,y | Leader LS-DIM / điểm đầu tại cạnh dầm |
| --- | --- | --- | --- |
| A — cạnh dọc bên trái mặt bằng đáy | `dm-1`, TEXT`1173211`, LS-TEXT | −1413315,371113; −1067024,133381 | LEADER`1173210`; điểm đầu x=−1411995,937232,y=−1067085,711074 |
| B — cạnh dọc bên phải mặt bằng đáy | `dm-1`, TEXT`1173213`, LS-TEXT | −1403663,415263; −1067024,133381 | LEADER`1173212`; điểm đầu x=−1404626,366140,y=−1067085,711074 |

Đã đọc thực thểLEADER và chuỗi vertices trực tiếp; JSON lưu đầy đủ, không dùng vị trí chữ làm tim dầm. ẢnhPDF thể hiện chấm đầu leader ở hai cạnh dọc khác nhau. Hai nhãnDM-2 chỉ vào cạnh ngang trên/dưới, giúp phân biệt phương; không dùng chúng để tạo thêmDM-1. Các polylines thép gần hàng chữ được giữ dưới dạng ứng viên hình học, không tự nhận thành leader.

## Quan hệ với mặt cắt và bảng thống kê

Mặt cắt DM-1 ở trên phải cùng trang17: TEXT`11732A4` là tên mặt cắt; TEXT`11732A5` ghi **DM-1: L=2500mm; SL=02**. Hình mặt cắt ghi rộng220,cao300, cốt−1,200/−1,500; mặt bằng có kích thước bao2500×2000, lọt lòng2060×1560. Đây là kích thước/chữ đọc trên hình, chưa đo độc lập tim hoặc gắn mỗi kích thước với dầm vật lý trong một snapshot.

Trang18 KC-01-12, bảng **BỂ NƯỚC bên phải**, nhãn nhómDM-1 TEXT`1173581`, SL2 TEXT`1173582`; hàng1 INSERT`1173553` đã truy ở ONE_ELEMENT_TRACE. SL2 ở mặt cắt/bảng **hỗ trợ số lượng**, còn hai nhãn+leader trên mặt bằng là bằng chứng vị tríA/B. Không nhân2 vị trí×SL2 thành4 dầm; bảng có4 thanh cho2 dầm, không phải4dầm.

## Giới hạn cụ thể

- Tầng, trục công trình, vị trí bể trên mặt bằng nhà và ID hai dầm vật lý vẫn **NULL**. Tuyến **1–1/2–2 là tuyến mặt cắt**, không phải trục nhà. Cao độ cục bộ không tự suy ra tên tầng.
- Chưa nốiA/B vào kiến trúc hoặc mặt bằng móng tổng thể; cần nhãn bể/ranh/tuyến liên hệ tới mặt bằng nhà và hệ trục có nguồn để hoàn tất liên kết.
- Các tọa độ trên là tọa độ bản vẽ ở vị trí hình, không phải tọa độ thi công và không chứng minh cùng tỷ lệ với hình khác.
- Chỉ xác minh vị trí hai nhãnDM-1 của bể nước trên hình này và liên kết cùng loạiDM-1; không chốt tổng thép, lớp bảo vệ/uốn hoặc tổng bể, không duyệt mâu thuẫn36,9kg.

Lượt đọc nhỏ modelspace TEXT/LEADER gần vị trí đã biết và trích ảnh từ trang đã có; không CAD batch/rough/full/DB/demo. Chưa ai duyệt: giữ `human_approval=false`, `verification_status=chua_kiem`. Không đổi file gốc/canonical hoặc bộtruy một hàng trước.
