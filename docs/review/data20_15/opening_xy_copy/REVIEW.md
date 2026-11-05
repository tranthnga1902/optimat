# QA15 — DTO tọa độ backend

05/11/2026 — **PASS focused: 34 passed in 7.58s / EXIT0** trên bản sao. Source target `d00762ab...`, coordinates test `7db4f432...` và incomplete test `4f85177c...` đúng manifest, giữ hash; base `c106399d...` không đổi. Receipt `receipt.json`; terminal `focused.log`.

DTO thêm riêng optional strict finite x/y. Test xác nhận confirm ReviewPlan và rough RoughRequest JSON dump/restore giữ âm/0, null legacy không thành 0; thiếu một trục được chấp nhận; NaN/±Inf/chuỗi bị từ chối. 22 ca incomplete cũ giữ pending ID và outside_masonry. Probe `check_outside.py` bổ sung ba tổ hợp 0/0, âm/null, null/âm qua outside_masonry_openings JSON restore, giữ ID/parent/w null. Probe lần đầu hoàn tất assert nhưng lỗi in tiếng Việt do console cp1252; chạy lại với PYTHONIOENCODING=utf-8 đạt, không sửa logic để che lỗi.

Finding bàn giao newline tiếp tục: default apply check lỗi dù exact base; ignore-space-change áp được nhưng hash `250cfa6f...` khác target. Nội dung chuẩn hóa CRLF/LF khớp canonical đúng target hash; copy exact canonical bytes để kiểm. Chưa PASS patch byte reproduction; không sửa candidate/runtime.

Chỉ dữ liệu synthetic trong bộ nhớ và local catalog; không DB/API/save thực tế/browser/full/TestClient. Không chứng minh N1–N5 mở lại trên ứng dụng. Frontend serializer/checkpoint và Board guard chờ freeze/lượt riêng; DIM vẫn PREPARED/NOT_RUN.
