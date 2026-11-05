# Kiểm trình duyệt demo 05/11

Đây là ghi nhận từng bước, chưa phải nghiệm thu trọn luồng.

## Đã quan sát

- Backend và Next.js khởi chạy cục bộ ở 127.0.0.1:8000/3000; log riêng trong thư mục này. Không mở Internet.
- Phiên admin đã đăng nhập được và vào `/do-boc`. Không đổi mật khẩu hay tạo tài khoản bằng agent.
- Đã chọn `data/drawings/build/tan_binh_kien_truc.dxf` qua file chooser trên trình duyệt.
- Backend ghi POST `/api/takeoff/view` trả 200. Trang quan sát vẫn hiện “Đang đọc” trong lượt có Fast Refresh; chưa kết luận nguyên nhân. Không dùng HTTP 200 làm bằng chứng UI đã hiện kết quả.
- Hai mẫu của đúng backend PID40384: CPU161,88s/RAM1.129.054.208bytes và CPU233,84375s/RAM1.123.143.680bytes. CPU tăng, không có bằng chứng deadlock. Số CPU không phải thời gian wall-clock riêng của một request.
- GET `/api/health` ngoài sandbox có timeout5s trong lúc CAD xử lý. Đọc mã thấy route async gọi chuỗi CAD đồng bộ trên event loop; đã giao bản sửa worker riêng cho view/structural.
- Ảnh quan sát: `browser_waiting.jpg`. Chưa có ảnh kết quả bóc hoàn chỉnh.

## Kiểm tự động đã chạy lại độc lập

- `node reports/demo_0511/frontend_regression.cjs`: PASS, exit0.
- `node reports/demo_0511/frontend_rough_regression.cjs`: PASS, exit0.
- Các kiểm này mô phỏng hành vi frontend; không thay chứng minh giao diện hoặc số đo trên bản vẽ thật.

## Bổ sung sau nạp SQL07

- Backend đã nạp bản worker mới, PID20288, launcher37596; chỉ restart đúng backend của phiên này sau xác minh parent/cmd/CPU, không còn tác vụ CAD quan sát đang chạy. Phiên admin vẫn hoạt động.
- Trình duyệt `/co-so-du-lieu` hiển thị `price_records`63dòng. Đã mở bảng, lọc `CBG-991233626E`, xác nhận4dòng ID1426–1429, ngày17/03/2026, XM01/XM02, tấn, VATYES, vận chuyểnUNKNOWN, ACTUAL/BULLETIN và nguồn từng biến thể.
- Ảnh bằng chứng: `db_prices_verified.jpg`. Đây là QA phần nạp dữ liệu, không phải QA toàn luồng đo bóc.
- User giao luồng mới ở chat khác: `/do-boc` chỉ chốt kích thước/khối lượng, tiếp `/dieu-chinh`, rồi giá/tối ưu. Đã giữ nguyên thay đổi này. Snapshot nguồn quan sát ở `frontend_external_changes/`.
- Hai harness đã được thích ứng luồng mới và báo PASS. Có rủi ro quota localStorage được tái hiện ở `frontend_storage_audit.md`; chưa sửa vì writer giao diện đang hoàn thiện yêu cầu thông tin dự án bắt buộc.
- Worker KT/KC đã qua13ca trong lượt focused74passed. Full suite do chat điều phối giữ tại `reports/integration_0511/regression/`; chưa dùng kết quả chạy dở làm bằng chứng đạt. Chờ full và bàn giao frontend ổn định trước lần CAD thật tiếp theo.

## Kết quả chạy bộ 46 sau hồi quy, ngày 03/11/2026

Mốc hồi quy tích hợp đã đóng với 501 bài đạt, 15 bỏ qua, 1 xfail N03 và 0 lỗi. Kiểm trực tiếp trên worker 20288 qua localhost, lần lượt gửi một tệp kiến trúc rồi một tệp kết cấu. Tiến trình kiểm 13789 kết thúc với mã 0. Số liệu dưới đây thuộc phiên bản đã nạp vào worker đó.

| Đầu vào | Kết quả xử lý | Thời gian người gọi | CPU tăng trong tiến trình | RAM cao nhất quan sát |
|---|---|---:|---:|---:|
| Kiến trúc bộ 46 | HTTP 200, 11 vùng, phản hồi 13.191.738 byte | 85,744 giây | 79,47 giây | 616,4 MiB |
| Kết cấu bộ 46 | HTTP 200, 15 bản vẽ thành phần, 4 móng và 34 dòng bảng cột | 38,022 giây | 37,53 giây | 556,1 MiB |

Danh sách kiến trúc có vùng cùng tên tầng mang hậu tố (2) và một vùng có 0 tường. Kết cấu trả danh sách bảng thép rỗng. Cần đối chiếu riêng theo bản vẽ trước khi dùng làm khối lượng nghiệm thu.

Trong 7 lần đo khi upload còn chạy, `/api/auth/me` trả 200 cả 7, từ 0,032 đến 0,617 giây. `/api/health` trả trong 5 giây ở 2 lần, 5 lần vượt thời hạn chờ của máy khách. Sau khi kết thúc CAD, hai lượt health trả 200 sau 14,787 và 12,282 giây. Các mẫu này cho thấy health chậm cả lúc không có tác vụ CAD của phiên kiểm. Trong tiến trình Python chẩn đoán riêng, hai lượt nạp mô hình mất 0,141–0,151 giây, tìm bộ chuyển DWG mất 0,108–0,112 giây, đọc cấu hình DB dưới 1 mili giây. Nguyên nhân độ trễ trong tiến trình phục vụ HTTP còn chưa xác định.

Trên trình duyệt, tên và mô tả hợp lệ đã mở được dự án kiểm tra. Hủy thao tác tạo mới vẫn giữ nguyên dự án. Tạo dự án kiểm tra thứ hai rồi chọn bộ 46 trong lịch sử đã khôi phục đúng tên dự án và nút mở bản vẽ. Ảnh bước này ở `ui46_project_open.jpg`.

Lượt tải tệp qua giao diện chưa được xác nhận. Hộp chọn tệp trả lỗi mất liên kết với phần tử, lần thử lại bị ngắt. Trạng thái trang quan sát được sau lượt đầu vẫn yêu cầu mở bản vẽ. Log backend có POST của các phiên dùng chung nên không đủ để gán cho thao tác trên tab này. Cổng QA còn mở gồm tải thực tế qua trình duyệt, giữ dữ liệu khi sang trang điều chỉnh và xuất kết quả từ đúng phiên đó.

Bằng chứng máy đọc được nằm trong `runtime46_20261103T104021Z/result.json`, `idle_probes.json` và `health_components.json` cùng thư mục lần chạy.

## Cần khép

1. Sau khi chọn được bộ 46 trên web, xác minh màn hình hiện đúng bản vẽ, dữ liệu qua bước xác nhận và trang điều chỉnh, rồi kiểm bảng xuất của cùng dự án.
2. Kiểm trên trình duyệt việc khôi phục kết quả khi bộ nhớ hạn chế. Lưu ảnh từng bước thành công hoặc thông báo lỗi cụ thể.
3. Xác định nguyên nhân độ trễ của health trong tiến trình phục vụ HTTP. Giữ số đo đã thu làm mốc đối chiếu.
4. Phần tối ưu mua thực tế còn cần báo giá nhà cung cấp và điều kiện giao hàng phù hợp với vật tư đã chọn.
