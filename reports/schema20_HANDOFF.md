# Bàn giao cập nhật checklist và database ngày 04 tháng 11 năm 2026

Kế hoạch hiện hành: docs/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md, mục11. Word: docs/schema/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.docx (14 trang, đã xuất và kiểm bố cục).

18 mục C00–C17: C00 hoàn thành kiểm kê; 17 mục còn mở tại thời điểm lập checklist. Mỗi mục có hiện trạng, bằng chứng đã có, việc bổ sung, phụ trách, điều kiện hoàn thành và thông tin cần chủ đồ án chốt. Các biên nhận mới dưới đây không tự đánh dấu đạt toàn chuỗi CAD.

Ưu tiên dùng VN002 đang có: khóa hồ sơ/phiên bản; kiểm đơn vị và từng vùng hình; truy từng occurrence/instance; gắn số đo; tính gross/trừ/net; đối chiếu đáp án độc lập. Vật liệu chưa biết giữ chưa xác định. Giá/NCC và dự đoán giá làm sau.

## Bằng chứng nhỏ đã có

Đọc docs/review/data20_07/ONE_ELEMENT_TRACE.md: hàng thép DM-1/STT1, bể nước, KC-01-12 trang18 có handle từng ATTRIB. (200+2450+200)/1000 = 2,85m; 4 thanh ×2,85×0,888 =10,1232kg, làm tròn10,1kg khớp hàng in. Chưa xác định đủ instance/tầng/trục, chưa có người kiểm độc lập; không coi là cả bể hoặc reader đã nghiệm thu.

## Database chính

Đã chuyển trong giao dịch, backup bắt buộc trước chuyển. reports/schema20_main_receipt.json: committed_verified, đúng20 bảng vật lý,26 analysis được đóng snapshot, dự án23 còn. Migration đối chiếu đầy đủ từng cột/dòng của28 cấu trúc cũ, bảo toàn quyền và2 view báo cáo. Bản sao restore/migrate riêng đã kiểm trước main. Không reset dữ liệu.

Kiểm tập trung:52 passed trước sửa guard INSERT/NEW;66 passed phần compute/review/rough;16 passed sau sửa guard cuối, gồm ACL, liên kết nguồn, revision và6 thao tác thêm/chuyển dữ liệu vào snapshot đã đóng. Đây là các lượt riêng, không gọi là một full suite sạch.

Kiểm dữ liệu sau chuyển:0 lỗi,1916 cảnh báo,2 ghi chú. Xem reports/schema20_data_check/data_check.md; các cảnh báo là khoảng trống cần rà soát, không đổi thành dữ liệu thật hoặc tự coi đã hoàn thiện.

API đã quiesce để chuyển;01 được giao restart đúng3 cổng8001/8002/8765 và đọc khói, không tiếp tục W5/demo/AI. Biên nhận runtime do01 cập nhật riêng.

## Phạm vi nghiệm thu hồ sơ VN002

Mẫu nghiệm thu chỉ gồm phần thô của nhà ở riêng lẻ xây mới có tối đa 5 tầng. Khi chọn mẫu, ghi bằng chứng cho loại công trình, tính chất xây mới và số tầng. Hồ sơ chưa đủ căn cứ giữ ở trạng thái chờ xác minh. Hồ sơ ngoài phạm vi ghi lý do loại và không tính vào mẫu số.

Với VN002, khung tên KC-01-05 ghi “Nhà ở gia đình”. Hồ sơ kiến trúc PDF trang 3–4 có các mặt bằng ghi tầng 1, 2, 3 và 4; trang 5 thể hiện mặt bằng mái. Đây là bằng chứng về các tầng được vẽ ngoài thông tin tên gói “4 tầng”. Cần đối chiếu hồ sơ pháp lý hoặc thuyết minh để xác nhận nhà ở riêng lẻ xây mới và cách tính số tầng thiết kế trước khi đưa vào mẫu nghiệm thu. Trong thời gian đó, vẫn có thể dùng bộ bản vẽ để kiểm nội bộ.

Ca DM-1 chỉ xét hai dầm móng và cốt thép của bể nước thuộc căn nhà VN002. Tờ cấp nước hỗ trợ định vị gara tầng 1. Công trình được đếm một lần theo hồ sơ nhà ở khi đủ điều kiện.
