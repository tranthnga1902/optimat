# Danh bạ phiên OptiMat AI

Cập nhật 03/11/2026 theo yêu cầu chủ đồ án đổi tên và thêm vai trò song song. ID giữ nguyên khi đổi tên.
Bảng này không mở rộng quyền sửa đang được phiên01 điều phối. Phiên00 chỉ kế hoạch, không tự dev.

**Đầu mối giao tiếp chủ đồ án:** theo chỉ đạo mới, chủ đồ án trao đổi chính với00. Phiên00 tiếp nhận yêu cầu,
chốt đặc tả/ưu tiên, phân việc và tổng hợp kết quả. Phiên01 điều phối kỹ thuật nội bộ: quyền ghi, phụ thuộc,
freeze và lịch kiểm thử. Các phiên chuyên môn báo kết quả/blocker cho01; câu hỏi sản phẩm/phạm vi/dữ liệu cần
chủ đồ án quyết định được gom về00, không buộc chủ đồ án theo dõi hoặc trả lời lặp ở nhiều chat.
Không dồn yêu cầu phê duyệt bắt buộc của công cụ sang phiên khác để vượt giới hạn;00 trình rõ hành động cần người dùng xử lý.

## Phiên đã đổi tên

| Tên mới | Tên cũ | ID | Vai trò và quyền |
|---|---|---|---|
| 00 · Cố vấn — Kế hoạch và phân vai | Xem kế hoạch hiện tại | `01a1a1ee-cbe0-7ce3-a0de-22f89aab7fbd` | Chỉ kế hoạch, đặc tả, phân vai; không source |
| 01 · Điều phối — Tiến độ và nghiệm thu | Kiểm tra tiến độ dự án | `01a1a0af-a01f-7af3-bf7d-34ef9a0c5576` | Điều phối duy nhất quyền ghi, freeze, nghiệm thu |
| 02 · Giao diện — Bóc tách và kiểm khối lượng | Đề xuất chọn nguyên liệu tự động | `01a1a0e8-3a59-7c32-a9cd-42c3311818f7` | Sole UI theo release của01; giữ preview bản vẽ |
| 03 · Review — Công thức phần thô và S13 | Review lộ trình S13 phần thô | `01a1a027-c69b-7b40-b18e-f5729b520957` | Sole backend dimensions theo release của01; review/N03/O01 theo phạm vi đã giao |
| 04 · Tích hợp — Vật tư, giá và tối ưu | Xem toàn bộ kế hoạch hệ thống | `01a1a0d1-640e-77a3-b92f-2e03fb857aad` | Pricing/optimizer/wall_groups; audit glue trước edit theo01 |
| 05 · J04 — Định mức và hồi quy tích hợp | J04 — Rà nguồn định mức phần thô | `01a1a06c-ecea-7930-b9b7-b6980c8f43f5` | Định mức theo nhiệm vụ hiện có; sole full theo lịch01 |
| 06 · Hồ sơ — Dữ liệu mẫu và quản lý tệp | Tạo 5 bộ bản vẽ nhà ở | `01a1a0e0-4565-78e1-941c-db246a84cf95` | Hồ sơ mẫu/admin/tải tệp theo phạm vi01 |
| 07 · Dữ liệu thật — Bản vẽ và đáp án | Tìm 10 bộ bản vẽ bóc tách | `01a1a042-3924-7ea0-847f-c734b584b9ea` | Chỉ dữ liệu thật/nguồn/đáp án; không tự phê duyệt số mâu thuẫn |
| 08 · X01 — Phạm vi móng băng và đài cọc | X01 — Đặc tả móng băng và đài/cọc | `01a1a08a-fed3-7ab0-90b2-6e32d6dacd2a` | Đặc tả phạm vi cấu kiện, chưa mở source mới |
| 09 · Báo cáo — Tiếng Việt và nhãn dữ liệu | Hỗ trợ xử lý tiếng Việt có dấu | `01a1a0e7-3ef4-7bb0-a8f6-765ce54b230d` | Nhãn/báo cáo tiếng Việt; HOLD source tới release |
| 10 · Triển khai — Đọc CAD và Render | Tìm cách thay thế đọc file khi deploy | `01a1a055-6c9a-7f43-b286-e7d1db210fbc` | Đọc CAD/deploy; không tự triển khai dịch vụ |
| 11 · Nghiệp vụ — Đầu vào và lượng mua | Liệt kê tài liệu cần bổ sung | `01a1a0f3-e582-7953-9942-800df41a13cb` | Nghiệp vụ đầu vào, lượng lắp đặt/lượng mua |
| 12 · Trợ lý OpenAI — Tư vấn chọn vật liệu | Cập nhật tiến độ bóc tách | `01a1a02b-b865-7c11-8995-e20d0814ddf6` | Đề xuất, so sánh và hỗ trợ chọn vật liệu tại /dieu-chinh. Phối hợp 02 về giao diện, 04 về danh mục/giá/tối ưu và 15 về nghiệm thu. |
| 13 · Tham khảo — Hash và phiên bản nguồn | Giải thích hash trạng thái | `01a1a09b-1a46-7571-8d21-ac60c1f205cd` | Tham khảo phiên bản/hash, không mở test trùng |

## Phiên mới đã khởi động

| Tên | ID | Phạm vi ngay lúc tạo |
|---|---|---|
| 14 · Review độc lập — Kích thước công tác | `01a1a206-e2ce-7720-92a7-47234ea0fc35` | Đọc source, chỉ ghi docs/review/backend_dimensions_14; không writer backend |
| 15 · QA — Luồng kiểm khối lượng | `01a1a206-ef50-7c91-a195-fab84cf8f77d` | Ma trận QA tại docs/review/qa_workflow_15; không full/Chrome/upload trước release |
| 16 · Mô hình giá — Dữ liệu và XGBoost | `01a1a207-0d6b-7120-b459-4ebbd2497138` | Readiness tại docs/review/price_model_16; không train/DB/models/data trước release |

## Làm song song và bàn giao

Phiên **17 · Giao diện — Bố cục và trình bày** (`01a1a20f-1fac-7271-ab92-7d2ad9a4f62b`) phụ trách chỉnh bố cục, bảng dữ liệu và hiển thị trên màn hình nhỏ. Việc đầu tiên là rà trang Vật liệu và giá. Phiên 01 phân tệp để phiên 17 thực hiện song song với phiên 02 và 04.

- 02 làm UI và03 làm backend sau release;14 review độc lập,15 chuẩn bị QA,16 rà dữ liệu giá song song ở thư mục riêng.
- 01 chốt hợp đồng và phiên bản, giải quyết caller chung, xếp focused/full. Mỗi vùng source một writer; không đồng thời chạy suite/CAD nặng.
- 04 rà glue giá/tối ưu,06 giữ hồ sơ/tải tệp,07 xác minh dữ liệu thật. Không đổi nhiệm vụ các phiên đang chạy chỉ vì đổi tên.
- Mọi gói bàn giao có đường dẫn, phiên bản/hash, test terminal và giới hạn; có mã không đồng nghĩa nghiệm thu.
- QA ACTUAL-build vẫn chờ người dùng tự chọn file/cấp lại quyền upload. Không vượt gate đã từ chối bằng native/API/browser khác.

