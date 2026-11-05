# Lưu/mở lại lỗ thủ công — QUEUED / NOT_RUN

05/11/2026 — tiêu chí do 01 chuyển từ yêu cầu người dùng qua 00. Chưa giao lượt chạy; chờ exact contract, manifest/freeze và phạm vi lệnh.

Owner02: snapshot frontend theo project/bản vẽ trước khi đổi file. Owner06: DTO giữ x/y hữu hạn, optional; null khác 0. Không thêm bảng, không cập nhật project26. Gói tách khỏi CAD/input/nonmasonry; không dùng receipt các gói đó để đóng ca restore.

| Ca | Fixture / oracle chờ chốt |
|---|---|
| MOR01 | N1–N5 có ID/parent/x/y/dimensions; đổi drawing rồi mở lại phải giữ đủ danh tính, vị trí và kích thước. |
| MOR02 | Vị trí (0,0) hợp lệ, không bị coi thiếu hoặc thay bằng tọa độ khác. |
| MOR03 | Dữ liệu cũ thiếu x/y hiển thị thiếu; không mặc định thành (0,0), không bịa vị trí. |
| MOR04 | Khác project/revision không trộn snapshot, ID, parent hoặc tọa độ; quay lại chỉ restore đúng identity. |
| MOR05 | Quota fail không làm mất snapshot trước; không báo lưu thành công khi chưa lưu được. |

Expected về lúc persist/restore, khóa identity, DTO null/omitted và lỗi validation phải lấy từ contract cuối. Chưa có fixture/harness được giao, chưa thực thi hoặc sửa production. Không DB/project26/upload thật/browser live/full/TestClient, không thử lại upload Tân Bình. DIM tiếp tục PREPARED/NOT_RUN.
