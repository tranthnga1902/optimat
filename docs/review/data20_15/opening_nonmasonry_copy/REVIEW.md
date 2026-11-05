# QA15 — parent nonmasonry backend

05/11/2026 — **PASS focused: 22 passed in 7.31s, EXIT0**. Không phát hiện blocker logic mới trong incremental review.py đã giao. Receipt `receipt.json`, terminal `focused.log`.

Sao chép src/data từ snapshot opening đã dùng cho bbox; review base hash đúng `7a2ecd852e5196879bcfb5071da998db21a78217947b4566e6dbba9b21d66fd1`. Chỉ incremental review.py và test riêng. Test target `4f85177c...`, review target `c106399d...` giữ hash sau chạy; base không đổi. Không nạp conftest repo, dotenv/DB URLs tắt; không runtime/candidate/DB/CAD thật/full/TestClient.

Review và focused xác nhận ba trạng thái: masonry thiếu kích thước pending đúng nhóm; parent đang giữ không masonry không orphan, được giữ nguyên ReviewOpening trong outside_masonry_openings; parent thiếu hoặc bị loại vẫn pending. Bốn tổ hợp w/h (đủ, thiếu rộng, thiếu cao, thiếu cả hai) giữ ID/parent/keep/null qua model_dump; warning nêu rõ không áp dụng khối xây/chưa xét công tác khác. Mặt bằng T2 độc lập vẫn đủ. complete chỉ biểu diễn phạm vi xây ở review, không chứng minh công tác bê tông hoặc hoàn thiện khác đủ. Invalid dimensions bị ValidationError; chưa kiểm HTTP422/DB save/UI consumer.

Finding bàn giao newline: mặc định git apply --check không áp được dù base hash đúng. --ignore-space-change áp được, cho hash `a4eb6c9608ea9dc6985f6f306d310a1c0faf798077c35fd50d8980163e843f64`, khác target. Nội dung khớp target canonical sau chuẩn hóa CRLF/LF; đã kiểm canonical đúng hash manifest rồi copy exact bytes vào bản sao để chạy. Vì vậy PASS source/harness **không** là PASS patch byte reproduction. Cần recipe newline hoặc exact target overlay/hash khi tích hợp.

Chưa kiểm serializer lưu thực tế, frontend, optimizer/export hoặc browser. Không thay đổi source/candidate đang chạy. DIM giữ PREPARED/NOT_RUN; CAD frontend chuyển lượt sau receipt này theo điều phối.
