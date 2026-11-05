# Trạng thái API và nguồn CAD C-2 tại 4/A

## Baseline thực tế

Một lần kết nối để POST tệp KC tới `127.0.0.1:8001/api/takeoff/structural` thất bại trước khi gửi request: sandbox báo `WinError 10013`; không có HTTP status, body, hash response hay số dòng. [Trạng thái máy đọc được](C2_BASELINE_STATUS.json). `netstat` trong sandbox không thấy listener, nhưng không có quyền quan sát đầy đủ nên không chứng minh dịch vụ ngừng. Theo thông tin 01 cung cấp, tiến trình có quyền đã xác minh staging proxy tới `8001/openapi.json` trả 200; 01 đảm nhiệm POST baseline thực. Không tạo response thay thế, không gọi lại, không khởi động dịch vụ.

**Baseline thực do 01 thực hiện sau đó:** HTTP 200, 76,02 giây, không có project ID hay lưu DB theo receipt. Đã đọc [receipt](C:/Users/Admin/.codex/visualizations/2026/11/03/01a1a0af-a01f-7af3-bf7d-34ef9a0c5576/c2-runtime-baseline/receipt.json) và tự tính SHA-256 [response](C:/Users/Admin/.codex/visualizations/2026/11/03/01a1a0af-a01f-7af3-bf7d-34ef9a0c5576/c2-runtime-baseline/structural.response.json): `bf2082f99470fa63c8f7f17083803c08c1a595c61e4f9a7c1a46ef16fbd1acf3`, khớp receipt. JSON thực **không có trường** `structural_columns`; `column_schedule` là mảng rỗng. Đây là baseline runtime trước reader mới, không phải kết quả candidate. Thông tin không lưu DB dựa trên receipt, không được xác minh bằng truy vấn DB.

## Nguồn cho reader

[Bàn giao nguồn CAD của 07](../data20_07/C2_A4_CAD_SOURCE_HANDOFF.md), [JSON entity](../data20_07/C2_A4_CAD_SOURCE.json) SHA-256 `ef19c2c01f62d41ac0f81c5bb8bba6d2205d41c118e3de2799a2b2066e3b779`; nguồn KC `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`. Ba cửa sổ chứa mặt bằng định vị, chi tiết cột và sàn tầng 3; chúng là bbox trích thủ công, không phải phạm vi view đã nhận dạng. Trong đó có text, leader, hatch, DIMENSION và INSERT cùng block liên quan: reader phải xử lý phép biến đổi block, trục, vùng và quan hệ trước khi gán một instance. Không chép locator hay đáp án từ fixture/oracle vào production. INSUNITS KC bằng 0: chưa mặc định đơn vị hình học.

[Bàn giao block và vật liệu](../data20_07/C2_A4_BLOCK_AND_MATERIAL_HANDOFF.md) và [nguồn block](../data20_07/C2_A4_CAD_BLOCK_SOURCE.json), SHA-256 `9a388082d25b8a59f422c24a6cc91af629c198ec0307e0468204f0745c5bc48c`, bổ sung một INSERT có gốc ở xa nhưng hình học sau transform nằm trong vùng mặt bằng. Do vậy gói cửa sổ đầu thiếu INSERT không phải bằng chứng bản vẽ thiếu hình hoặc trục. Dùng raw cộng transform **hoặc** world entity để tránh đếm đôi; giữ đường dẫn source handle. Bằng chứng bố trí thép và mác vật liệu chưa phải khối lượng mua hoặc mã catalog.

## API mapping hiện tại

`project_analysis._events` đã truyền từng tệp KC vào bộ đọc và giữ nguồn theo đường dẫn đọc hoặc tên tệp; `_column_sources` chỉ gắn file ID/revision/hash vào evidence của instance nếu xác định duy nhất nguồn. Khi nhiều nguồn không rõ, giữ nguyên instance và cảnh báo. Mapping hiện không điền trục, cao độ, tiết diện hay matched ID. Lần rà này sửa thêm trường hợp reader trả đường dẫn tệp lưu trữ thay cho tên tệp gốc; kiểm thử 5 ca đạt, một test route không chạy do trước đó bị treo trong môi trường này.

Tại thời điểm báo cáo ban đầu, reader chưa suy nối an toàn trục, tiết diện, cao độ và sàn từ hình học thực của fixture; chưa có bằng chứng C-2 thực được đọc đầy đủ. Hash lịch sử khi đó: `project_analysis.py` `e6347f21ce3ceb9ecfcaa1852c6c2cb6aa6ceaeac41ba67830f99ca0fb142e89`; `structural_column_instances.py` `fdab0bba6d02b8f5b583402283d4cc5f4fbb58775922e101e656a295679fb4d9`. Mã đang phát triển có thể tiếp tục thay đổi; hash không phải bằng chứng đã nạp runtime.

**Freeze API mới:** xem hash hiện hành trong [manifest](C2_API_MANIFEST.json), thay các hash lịch sử của đoạn trước. Đã kiểm `source_sha256`, `missing`, `top_slab_candidates` đi qua encoder/stream nguyên vẹn; candidate chưa được gán vào `top_slab_thickness_mm`/`top_slab_source`. Nếu hash reader khác hash revision đã chọn thì không gắn bằng chứng revision đó và phát cảnh báo. Sáu test focused đạt, một test route loại khỏi lượt chạy vì trước đó bị treo; chưa kiểm runtime candidate hay round-trip qua frontend/rough API.

**Bản freeze C-2:** [C2_FROZEN_project_analysis.py](C2_FROZEN_project_analysis.py), byte SHA-256 `ecf631350200ce1050ffbb774ff1a0aca1a5c300da1ad84ba7dc3ec6e574948e`, khớp manifest. Bản sao dựng từ file canonical bằng cách bỏ duy nhất import `document_candidates` và endpoint `/candidates`; canonical đang phát triển tài liệu được giữ nguyên. Bản sao không tự thay đổi runtime.
