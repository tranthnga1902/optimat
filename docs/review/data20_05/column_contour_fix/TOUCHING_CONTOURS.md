# Vòng 2: hai contour chạm nhau — đã kiểm SYNTHETIC

**Cập nhật cuối:** 00 đã xác nhận03 không giữ dxf_reader.py/columns.py và cho phép05 triển khai hunk metadata tối thiểu. Nội dung chờ ownership bên dưới là lịch sử trước quyền này. Reader và consumer nay đã được sửa; bốn ca ban đầu fail đã chạy tới terminal **4passed**. Bằng chứng mới ở `v2_receipt.json`, `touch_final.log`, `v2_regression.log`, `converter_retry.log`, `signal_columns_v2.patch`. Log vòng1 không đại diện source hiện tại.

Reader thêm trường tùy chọn cuối Segment `contour_id: int | None = None`. Chỉ polyline kín toàn cạnh LINE được gán nhóm; ID lấy chỉ số đầu trong danh sách segment của lần đọc, vì thế các INSERT của cùng block có ID khác nhau. Giữ nguyên source block và mọi hunk khác trong reader. ID này không là handle/FK hoặc định danh bền vững giữa các lần đọc. `crop` giữ Segment và ID; test mới xác nhận block lặp chung cạnh sau crop vẫn ra2cột225×335. Nét rời có đường chia xuyên khung giữ chưa nhận, không tự khẳng định2cột từ hình học mơ hồ.

Kiểm cuối: **74 ca khác nhau đạt qua hai lượt**. Lượt hồi quy chính72passed/2failed/11deselected;2failure là TemporaryDirectory converter không có quyền trong Temp của sandbox. Chạy lại riêng2ca với TMP/TEMP/TMPDIR trong workspace:2passed/exit0. Không gọi lượt chính exit1 thành exit0 hoặc báo74pass trong một lượt.11deselected là các tham số CAD thật trong test_drawing_io, giữ ngoài phạm vi. Các ca contour mới gồm chung cạnh/góc/nét nối/khe0,4mm, block lặp/crop và đường vào rough; tổng22ca contour. Có chỉnh assertion khe0,4mm dùng dung sai1e-7 cho sai số225−epsilon của float, không làm tròn kích thước production.

Chưa kiểm CAD thật/full suite/DB/runtime. Chờ00/15review độc lập trước phát hành. Những nhận định “chưa hoàn thành reader” dưới đây chỉ mô tả thời điểm trước cập nhật này.

Theo phản hồi QA15/00, đã tái hiện bằng 4 test DXF SYNTHETIC (hai LWPOLYLINE kín riêng biệt): chung cạnh, chung góc, nối bằng LINE, cách nhau0,4mm. Cả4 fail trước vòng sửa này; log `touch_before.log`. Không dùng CAD thật hoặc DB.

## Phần đã sửa trong scope05

`signal_columns` giữ từng `contour_id` nếu có, không union các contour đó theo đầu mút. Với nét rời chưa có danh tính, trường hợp khung ngoài có đường chia xuyên khung bị giữ chưa nhận: không tự gộp thành một cột ngoài và không tự chia thành hai cột khi không có căn cứ. Không thay đổi hatch/detect_columns.

Đã thêm2 test hợp đồng: hai nhóm Segment mang ID riêng chung cạnh vẫn giữ2cột; cùng các nét nhưng không có ID thì giữ chưa nhận. Lượt consumer/columns: **23passed,4deselected,exit0**, log `consumer.log`. Bốn deselected chính là test reader mới còn chờ metadata; không coi đây là full pass của vòng2 hoặc regression56 đã chạy lại sau thay đổi này.

## Hunk reader cần owner01/03 xác nhận trước sửa

`src/optimat/drawing/dxf_reader.py` đang có uncommitted diff của phiên khác.05 đã gửi câu hỏi ownership bằng công cụ hỏi người dùng và chưa sửa file này. Đề nghị owner reader bổ sung hợp đồng nhỏ sau, không thêm schema DB hoặc provenance giả:

1. Thêm trường tùy chọn cuối `Segment`: `contour_id: int | None = None`. Đây chỉ là danh tính nhóm contour trong **một Drawing đọc được**, không phải entity handle/FK/revision hoặc bằng chứng đã duyệt.
2. Trong `_Collector.polyline`, sau khi đọc `closed/parts`, cấp một ID riêng cho mỗi lần thu closed polyline toàn LINE (ví dụ chỉ số bắt đầu trong `self.segments`, không dùng tên block/handle đơn lẻ vì INSERT lặp cần nhóm riêng).
3. Khi append mỗi cạnh polyline, gắn cùng ID đó lên Segment vừa thêm. Nét rời/đường nối vẫn None. Polyline hở hoặc có cung không được coi là contour chữ nhật kín từ tập LINE thiếu cung.
4. Giữ ID khi crop/rescale/copy nếu các nhánh ấy tạo Segment mới. Không thay `source` tên block thành contour ID: source đang có consumer khác.

05 consumer dùng `getattr(seg, 'contour_id', None)` nên tương thích Segment cũ; khi reader truyền metadata,4test reader phải chạy thật qua read_drawing và pass, không mock ID ở4ca này. Cần thêm case INSERT lặp để xác nhận không trùng ID giữa occurrence. Sau đó chạy lại nguyên bộ hồi quy56 +6ca mới, ghi source/testhash mới và nhờ15review. Không phát hành bản consumer-only như đã giải quyết reader.

## Giới hạn hiện tại

Vòng2 đang **chờ ownership/metadata reader**, chưa chốt. Các test reader mới cố ý giữ kỳ vọng2contour và vẫn là tái hiện lỗi; không xfail/skip để che thiếu. Hai LINE rectangle chung cạnh có cùng hình học như một rectangle chia ô: khi không có identity/entity kín, không thể khẳng định số cột chỉ từ các đoạn. Các nét kéo ra ngoài và contour xoay vẫn chưa được suy đoán. Log/receipt vòng1 giữ lịch sử, không đại diện hash mới. Không sửa DB/schema/runtime, không chạy full suite.
