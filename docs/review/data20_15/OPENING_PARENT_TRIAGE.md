# Opening parent nonmasonry — PENDING triage

Nguồn: điều phối 01, ngày 05/11/2026. Chưa giao lượt chạy; QA15 chưa xác minh bằng thực thi và chưa kết luận lỗi.

01 quan sát khác biệt: `compute_review` dùng tập ID masonry giữ lại nên opening có parent concrete có thể bị coi unassigned và pending toàn bộ; rough dùng `all_kept_ids` nên coi đã có parent và không pending. Frontend compute có cách dùng ID masonry tương tự, cần đối chiếu tính nhất quán nếu hợp đồng được chốt.

06 đang rà hợp đồng/case trên bản sao theo quyền read-only; không thay freeze. Trước QA cần 01 cung cấp quyết định về parent hợp lệ theo vật liệu, phạm vi pending (toàn bộ hay từng plan), manifest cuối và lượt/lệnh được giao. Ca dự kiến phải phân biệt parent masonry, concrete, parent thực sự không tồn tại và parent thuộc plan khác; expected chờ hợp đồng, không mặc định một nhánh hiện tại là oracle.

01 cập nhật sau triage06: finding đã CONFIRMED; hợp đồng ba trạng thái là masonry pending / nonmasonry kept không phải orphan / true orphan pending toàn bộ. Owner06 sửa review.py/test; owner02 sửa frontend model compute/helper. QA15 chờ manifest incremental và lượt riêng, chưa chạy trên hợp đồng mới. Runtime 8003/8004 giữ freeze theo 01.

Trạng thái: **CONFIRMED triage / NOT_RUN QA15**. Không sửa production/frontend, không chạy test mới, không full/TestClient/DB/CAD thật, không thử lại upload Tân Bình. Bbox đã hoàn tất riêng tại `overlay_bbox_copy/receipt.json`; không lặp lại.
