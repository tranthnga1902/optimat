# Rà hợp đồng đầu vào kiến trúc/kết cấu — chỉ đọc mã

## Đường dự án đang có

- `api/project_files.py:resolve_analysis_files`: kiểm chủ dự án, profile version mới nhất, không trùng revision/file, vai trò KT/KC, loại CAD, tập lựa chọn khớp profile và hash byte nguồn; **bắt buộc có ít nhất một KT**. Profile lưu lựa chọn cũng chỉ nhận revision CAD phân tích. Preview và tải bản gốc là đường đọc riêng.
- `api/project_analysis.py:_events`: KT đi qua `takeoff_plans` → `view_payload`/viewer để nhận tường, lỗ và mặt bằng; KC đi vào `structural_parts`, **không gọi nhận tường KT cho KC trong đường này**. Cột KC có thể giữ revision qua `_column_sources` khi nhận diện được duy nhất nguồn. Receipt gắn project/profile/files và hash request/response, không tự xác nhận đúng loại tờ hay độ chính xác khối lượng.
- `frontend/src/lib/project-records.ts` cũng chặn tập chọn thiếu KT; `Review.tsx:readFile` yêu cầu `body.view.plans` và chạy luồng review mặt bằng. Nới riêng validator backend cho KC-only sẽ không đủ: `_events` hiện truy cập `views[0]` khi không có KT, và UI không có model/màn hình kết quả KC-only.
- `ProjectFilesPanel.tsx` là phạm vi 00 đang phụ trách. Thông báo trước Start nên nói rõ: KT cần để bóc kiến trúc/tường; KC tùy chọn để bổ sung cấu kiện; chọn KC đơn lẻ không thể bắt đầu đường hiện hành. Không tải lại bản đã lưu.

## Đường KC riêng và ranh giới

`api/main.py:/api/takeoff/structural` là đường đọc KC độc lập bằng **multipart upload**, gọi `structural_parts([drawing])`; bản thân route không mang project ID, revision hoặc receipt hồ sơ. `Review.tsx:onStructural` dùng `File` do người dùng chọn và gọi đường đó. Không đồng nhất đường này với xử lý revision KC đã lưu hoặc kết luận rằng nó gắn được đúng hồ sơ. Route dự án phải dùng `_project`, `_revision`, `_check_selection(..., verify_bytes=True)` và kiểm profile, không dùng lại upload khi đã có file lưu.

Đường upload chung `Review.tsx:upload` gọi `/api/takeoff/view` không kèm vai trò phân biệt KT/KC; nếu người dùng chọn file KC làm bản chính, không có hợp đồng vai trò ở đường này để ngăn đưa nó qua reader mặt bằng/tường. Cần chỉ dẫn/chọn vai trò rõ và guard server tương ứng trước khi gọi; không dùng tên tệp hoặc layer làm chứng cứ tuyệt đối.

## Tờ/mặt cắt và giới hạn

`rough/structural.py:read_structural` nhận view/tờ, mặt cắt và kích thước theo bộ nhận dạng; `rough/takeoff.py:structural_parts` hiện gộp nhiều file, `beams.update`/`column_sections.update` và ghép `sheets` theo thứ tự. Mã trùng hoặc tờ thiếu/khác thứ tự có thể gây mơ hồ/ghi đè; không suy liên kết tờ–mặt cắt–cấu kiện chỉ từ tên mã, tọa độ gần hay có mặt cùng một file. Cần giữ định danh tệp/revision/hash, sheet/view, locator/handle và bằng chứng ghép; mơ hồ hoặc thiếu giữ pending. Bộ viewer/nguồn đang do 03 xử lý: không sửa chồng.

## Đề xuất hunk trước khi ghi

1. **Hiện hành, không đổi backend:** 00 sửa `ProjectFilesPanel.tsx` để chặn KC-only, cho biết vai trò, phạm vi và phần thiếu trước Start. Các guard `project-records.ts` và `project_files.py` giữ nhất quán; test trường hợp KT-only, KT+KC, KC-only, file/hash/revision sai, tham khảo không thay KT.
2. **Nếu sau này cần KC-only thật:** thiết kế response loại `structural_only`, UI và trạng thái partial riêng; sửa có phối hợp `project_files.py:resolve_analysis_files`, `project_analysis.py:_events` (không truy cập `views[0]`, không gọi tường), `Review.tsx:readFile`/`project-records.ts` và test/receipt. Kiểm owner/profile/hash như cũ; không tạo kiến trúc/khối xây bằng 0 để vượt validator. Chưa cấp hunk, chưa chạy.
3. **Nối file KC đã lưu trong bước thô:** endpoint theo project/file/revision đã xác thực và đọc nội bộ; gắn provenance cho từng fact, tránh upload lại. Tránh sửa `api/main.py` khi 17/nhánh khác sở hữu. Đây là đề xuất, không phải capability đã có.
4. **Đối chiếu cấu kiện:** thay gộp map theo tên bằng danh tính nguồn/tờ và quan hệ có căn cứ; cho phép nhiều ứng viên, thiếu/mâu thuẫn giữ null. Thống nhất 03 trước thay `structural.py`/`takeoff.py` và viewer, bổ sung test file trùng mã/tờ, scale/đơn vị chưa rõ, KT/KC khác revision, không chéo dự án và không chạy nhận tường cho KC.

Chưa chạy API, UI hoặc database; không thay mã, schema, bốn tệp width đã freeze, Office hay AI.
