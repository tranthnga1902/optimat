# Nghiệm thu kỹ thuật N02, partial Q02 và B01

Ngày 03/11/2026. Codex điều phối/reviewer: **ĐẠT kỹ thuật trong phạm vi dưới đây**. Chưa nghiệm thu dữ liệu thực, độ chính xác hình học, PostgreSQL, toàn luồng giao diện hoặc các sprint còn lại.

## N02 — bảng thép lặp và xác nhận phạm vi

Đã đối chiếu ma trận T1–T14 trong [giao việc N02](N02_GIAO_DEV.md), mã hiện tại, test reader/API/partial và các gói bàn giao:

- Chỉ bỏ bản sao nguyên bảng cùng phạm vi có căn cứ; giữ bội số dòng, hai tầng độc lập, ô gốc và phần chưa đọc được. Không so chỉ bằng tổng kg hoặc khử trùng xuyên file.
- Có pipeline collect → manifest trước dedup → validate toàn bộ mapping → resolve; giữ wrapper/caller cũ. Hash nguồn từ byte upload gốc, kiểm revision/table/content, xung đột nhóm và lý do override; sai trả422 trước khi áp dở. DWG giữ hash gốc và trace chuyển đổi hiện có.
- JSON-only giữ metadata/rows, không tự áp mapping, dedup hoặc xóa missing. Áp/thay mapping phải gửi lại nguồn. Người/ngày/chứng cứ là dấu vết nghiệp vụ, không xác thực chuyên môn người khai.
- Numeric + missing giữ lượng đã biết nhưng D/chưa đủ qua công tác, tổng, vật tư phụ thuộc và giá; tổng nhập tay không tự xóa vấn đề phạm vi nguồn.

Bằng chứng: [reader sau review](../../reports/n02/b1/review_fix/HANDOFF.md), [upload/round-trip](../../reports/n02/b2/HANDOFF.md), [partial](../../reports/n02/b3/HANDOFF.md). Ca mapping cột trên bảng dầm do điều phối phát hiện đã được sửa và kiểm lại; không bỏ qua xung đột chỉ vì có override_reason.

## Q02 — partial backend và đầu ra

Đạt phần backend được triển khai cùng N02-b3: trạng thái/inputs giữ phụ thuộc yếu nhất; subtotal công tác/cốp pha chưa complete nếu còn con thiếu; missing/D truyền tới dây buộc và vật tư khác của chính công tác, intermediate và cờ trọng lượng nhóm/loại. Giữ A01, dấu âm, số0, None và số thô trước làm tròn. Vật tư độc lập không bị hạ trạng thái theo nhóm không liên quan.

Giữ giá tham khảo nhưng est_cost=None khi lượng chưa đủ; optimizer đưa dòng D vào missing.known_part. BOQ giữ lý do chi tiết và dùng nhãn nhóm/loại “chưa đủ dữ liệu khối lượng”. Đây chưa phải nghiệm thu P01/P02 trên giao diện hoặc mọi cách lọc/gộp đầu ra.

Điều phối kiểm độc lập các ca pending có/không tổng nhập tay với TH10 waste_pct=0 chỉ trong bản sao RAM: giữ0,063t và0,753kg, D/missing/chưa đủ/không chi phí hoàn chỉnh. [Kết quả sau sửa](../../reports/partial_review_20261103/after_b3.json).

## B01 — vật liệu cốp pha

Đạt kỹ thuật tra định mức hiện có theo DAM/MONG/CAU_THANG, cộng phần âm/trừ, nhóm khác cấu kiện, loại chưa có định mức và khối lượng None. Ca10m²DAM cho CP03=0,194m³ và CP06=1,429kg. Chỉ bổ sung kiểm hành vi, không thay hoặc nghiệm thu nguồn định mức mới. [Bàn giao12 ca](../../reports/b01/HANDOFF.md).

## Hồi quy và đồng bộ HTTP

- Full thường, không --runxfail: **605 passed, 15 skipped, 1 xfailed, 0 failed/errors, exit0**;621 collected,589,49giây.15skip là kiểm DB chưa cấu hình; xfail còn lại N03. Session93390 đã terminal. [Kết quả và log](../../reports/n02/full_regression/HANDOFF.md).
- Hash full:211→212; không sửa/xóa tệp có từ đầu, chỉ thêm `scripts/import_synthetic_housing.py`. Điều phối đã kiểm đây là CLI độc lập có __main__, không được src/tests gọi, thuộc yêu cầu nhập20SYNTHETIC ở chat khác. **Không tuyên bố toàn snapshot bất biến hoặc nghiệm thu script nhập này từ full.**
- Sau full, probe app thật qua TestClient, compute/BOQ/export thật: **4/4 fixture PASS,12/12 HTTP200,exit0**, session14135 terminal. JSON ↔ bytes Excel ↔ optimizer khớp COT_THEP/TH10 trên pending, pending+manual, resolved cùng scope và hai tầng. Giá100/kg là fixtureSYNTHETIC; không là giá mua thật. [Bằng chứng và artifact](../../reports/n02/api_output_parity/HANDOFF.md).
- Hash probe212 tệp trước/sau không đổi. Frontend/SQL/docs/reports ngoài phạm vi hash; không suy toàn repo bất biến.

N02 không còn xfail che lỗi đã xử lý. Cho mở N03 theo BA đã chốt và phân quyền riêng; xfail N03 hiện tại vẫn giữ tới khi có bản sửa và bằng chứng tương ứng.
