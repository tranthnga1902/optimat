# Hợp đồng đề xuất: hồ sơ của chủ dự án trước phân tích

Trạng thái: **đề xuất để 01/02/17 chốt**, không phải API đã triển khai. Không sửa source, DB hoặc chủ sở hữu dữ liệu hiện có. Ngày rà mã 03/11/2026.

## Phân định hiện trạng

- `Project.user_id` là quan hệ chủ sở hữu trong PostgreSQL. `/du-an-cua-toi` hiện dùng lịch sử localStorage riêng; chuỗi định danh local không chứng minh quyền và không được tự ghép sang project DB.
- `ProjectFile` hiện chưa có version, SHA-256, size, role. Manifest `data/uploads/manifest.jsonl` đánh số theo tên toàn cục, khóa trong một tiến trình; không đại diện lịch sử của dự án và không phải nguồn định danh revision an toàn khi nhiều worker chạy.
- `require_user` khi không có DATABASE_URL có thể trả `None`; endpoint hồ sơ mới phải bắt buộc DB và user thực, không hiểu `None` là được phép truy cập. Truy vấn ownership phải kiểm `projects.user_id == current_user.user_id` ở server. Không dùng endpoint admin cho user.
- `read_drawing` đọc DXF và chuyển DWG trong thư mục tạm; `line_preview` chỉ xuất nét có giới hạn. Đây là ứng viên kỹ thuật, chưa có phép kiểm runtime xác nhận toàn bộ nhánh preview không gọi phân tích.
- `POST /api/takeoff/view` nhận multipart và dựng kết quả nhận dạng/takeoff, kể cả chế độ progressive. Không dùng nó làm preview hoặc yêu cầu client tải lại byte đã lưu.

## Định danh và DTO đề xuất

Tất cả ID và version do server cấp; chưa chốt implementation schema. `project_id` là DB ID thực; `file_id` nhận diện hồ sơ logic trong dự án; `revision_id` bất biến nhận diện một lần lưu bytes; `sha256` là digest tính trên bytes gốc tại server; `role` do người dùng chọn trong `KT | KC | THAM_KHAO`. Bản cũ không tự có role/version/hash: để `null`/chưa xác định cho đến khi có migration/backfill được kiểm chứng, không suy diễn từ tên.

```json
{
  "project_id": 101,
  "file_id": 201,
  "revision_id": 301,
  "version": 2,
  "sha256": "<64 ký tự hex do server tính>",
  "name": "ban-ve-kien-truc.dwg",
  "original_format": "dwg",
  "size_bytes": 12345,
  "role": "KT",
  "uploaded_at": "2026-11-03T12:00:00Z",
  "preview_status": "not_requested",
  "source": "user_upload"
}
```

Ví dụ ID/số liệu chỉ minh họa, không là dự án thực. Metadata không trả đường dẫn hệ thống. Dự án và file/revision/role là quan hệ được server kiểm; `revision_id` không tái sử dụng cho bytes khác. Vai trò có thể thay nhưng phải có lịch sử phiên chọn và không làm thay đổi hash bytes. Quy tắc tên logic để đánh version, dedup và cách migrate cần 01 quyết định, không sao chép quy tắc manifest toàn cục một cách mù quáng.

## Route dự kiến

| Route | Đầu vào và kết quả | Điều kiện |
|---|---|---|
| `GET /api/projects` | Danh sách dự án thuộc user | Chỉ chủ sở hữu, DB và phiên hợp lệ |
| `POST /api/projects` | Tên, thông tin dự án do user nhập; trả ID DB | Tạo mới theo user đang đăng nhập |
| `GET /api/projects/{project_id}/files` | Metadata các tệp và revision của dự án | Ownership; trạng thái preview không đồng nghĩa phân tích |
| `POST /api/projects/{project_id}/files` | Multipart tệp CAD + role; trả DTO revision | Đây là lần upload duy nhất, giữ byte gốc, kiểm `check_upload`, bảo đảm hash và quyền |
| `GET /api/projects/{project_id}/files/{file_id}/revisions/{revision_id}/original` | Attachment byte gốc, content type an toàn, `nosniff`, `private, no-store` | Ownership + quan hệ tệp/revision; không nhận đường dẫn từ client |
| `GET /api/projects/{project_id}/files/{file_id}/revisions/{revision_id}/preview` | Nét, bbox/size, tổng/số nét hiển thị, định dạng gốc, trạng thái và cảnh báo | Chỉ đọc CAD/convert tạm để dựng hình; không `takeoff_plans`, `compute`, lưu kết quả hoặc LLM |
| `POST /api/projects/{project_id}/analysis` | JSON danh sách revision đã chọn, options và hash; trả tiến độ/kết quả theo cơ chế thống nhất với 02/03 | Chỉ sau nút chủ động; server đọc bytes đã lưu, không multipart/reupload |

Preview có thể tốn CPU và chuyển DWG: cần timeout/giới hạn và trả trạng thái lỗi/cắt nét rõ. Nếu muốn cache preview thì phải xác định key `(revision_id, sha256, phiên bản renderer)` và quyền; không ghi kết quả phân tích, không thay source. API GET không khẳng định không có cache nội bộ, nhưng không được tạo trạng thái xác nhận/công tác.

Ví dụ body phân tích:

```json
{"files":[{"file_id":201,"revision_id":301,"sha256":"<hash>","role":"KT"},{"file_id":202,"revision_id":302,"sha256":"<hash>","role":"KC"}],"options":{}}
```

Trước khi gọi pipeline, server kiểm ownership, cả quan hệ revision/project, hash thực của byte lưu, phiên bản/role khớp lựa chọn, kích thước và định dạng. Không tự dùng `THAM_KHAO` làm KT hoặc KC; file tham khảo chỉ được dùng theo phạm vi xác định. Khi version/hash không khớp trả lỗi 409, missing 404 theo chính sách không tiết lộ dự án khác; loại file sai 422/400; chưa đăng nhập 401, không có DB 503/409 theo thống nhất. Trả chi tiết tiếng Việt, không rò đường dẫn nội bộ. Pipeline hiện có có thể tái dùng hàm nhận đường dẫn/bytes nội bộ; adapter API phải do owner backend triển khai và kiểm test, không thông qua multipart HTTP do client gửi lại.

## Đồng bộ frontend và an toàn dữ liệu

02/17 có thể dựa vào DTO này để thiết kế UI, nhưng không coi route là đã tồn tại. `/du-an-cua-toi` tạo/chọn project DB có quyền, liệt kê metadata, tải và preview bản gốc. Lựa chọn phân tích gồm ID revision, hash, role và thuộc project; chuyển lựa chọn này sang `/do-boc` qua cơ chế do 02 chốt, tránh truyền bytes hoặc chỉ tên tệp. Trạng thái local lịch sử không được thay thế kiểm tra server.

Tệp lưu tạm được kiểm hash rồi đưa vào kho gốc theo cách không ghi đè; DB lưu liên kết trong giao dịch. Nếu DB rollback, tệp đã tạo không tự rollback: phải có cleanup theo tham chiếu và concurrency, không xóa tệp dùng chung. Phân biệt thất bại upload và phiên bản đã lưu; không hứa atomic cross-filesystem/DB. Thực thi migration, backfill hoặc quyền đọc tệp ngoài khu vực cho phép cần review riêng.

## Bổ sung: thông tin và nguồn do người dùng cung cấp

Rà `ProjectInfo` hiện chỉ gồm `location`, `buildingType`, `floors`, `note` trong localStorage; form `ProjectBar` hiện chỉ sửa tên và mô tả, khi tạo đặt các trường kia rỗng. `Project` DB có address, chiều cao tầng, kích thước cửa, ngân sách và hạn cung ứng nhưng không có đầy đủ mô tả, loại công trình, số tầng, thông số theo tầng, nhu cầu vật liệu hoặc liên kết bằng chứng. Không coi các trường local là đã lưu bền vững trên server.

Hợp đồng mở rộng để 01/02 thống nhất: tái dùng một giao diện `ProjectInfo`/`ProjectBar`, với các nhóm `design_facts` và `material_preferences` tách biệt. Trường tùy chọn có thể `null`/chưa biết. Bản ghi mỗi giá trị chọn để phân tích cần nguồn `manual`, `document`, hoặc `unknown`, kèm `value`, `unit` nếu có, thời điểm và phiên bản thay đổi; `manual` không được hiển thị là trích bản vẽ. Với `document`, tham chiếu gồm `project_id`, `file_id`, `revision_id`, SHA-256 và vị trí đã biết: `page`, `floor`, `table`/`cell` hoặc tọa độ CAD/handle. Các trường vị trí có thể rỗng; nếu chỉ biết tệp thì báo mức truy vết tệp, không bịa trang hoặc vị trí. Server phải kiểm quyền và quan hệ file/revision với đúng dự án trước khi lưu hoặc mở nguồn.

Giá trị nguồn (khi đã được ghi nhận có căn cứ) và giá trị đang chọn để phân tích là hai trường/phiên bản riêng; thay đổi thủ công không sửa byte tệp, không xóa dấu vết nguồn, không gộp các giá trị mâu thuẫn thành một số. Không tuyên bố nguồn document đã xác nhận nếu chưa có tài liệu và vị trí thực. Cần cơ chế lưu DB có version/concurrency và test mở lại sau refresh; schema hiện tại chưa đủ, nên cần migration và mapping được 01 chốt trước khi triển khai. Không chuyển localStorage sang DB bằng cách ngầm đoán project ownership.

Tài liệu tham khảo PDF/tiên lượng là nhóm tệp khác với bản vẽ dùng phân tích: kiểm định định dạng/dung lượng riêng và lưu revision gốc; whitelist hiện có trong `check_upload` chỉ nhận DXF/DWG, không tự mở rộng để nhận PDF/XLSX mà thiếu kiểm định và chính sách xem/tải. PDF có thể xem bằng cơ chế an toàn được chốt; XLSX hoặc định dạng chưa hỗ trợ thì tải bản gốc và hiện lý do không xem trước. Tài liệu tham khảo không tự đưa vào pipeline KT/KC.

Trước nút phân tích, màn hình cần trình bày snapshot các revision/role đã chọn, giá trị chọn và nguồn, nhu cầu vật liệu và các trường thiếu; server nhận snapshot/phiên bản và từ chối dữ liệu đã đổi theo hợp đồng nhất quán được 01/02/03 chốt. Nút xem nguồn mở đúng revision được phân quyền, và chỉ đánh dấu phạm vi trang/vị trí nếu biết thật.

Kiểm thử bổ sung: nhập và sửa một thông tin, lưu/mở lại dự án rồi so nguồn và giá trị; sửa giá trị đã có nguồn không thay bản gốc; hai nguồn mâu thuẫn vẫn giữ cả hai; xem nguồn theo revision/cross-project; file-only không sinh page giả; PDF/XLSX bị từ chối hoặc tải đúng theo whitelist đã duyệt; kiểm sở hữu dữ liệu đầu vào; xem hồ sơ không tạo kết quả đo bóc. Không tự kích hoạt upload hồ sơ Tân Bình đang bị từ chối.

## Tests chặn nghiệm thu

1. Ẩn danh, user B, revision thuộc project khác, file ID/revision ID giả, đường dẫn traversal/symlink, thiếu DB đều không được đọc/tải/preview/phân tích tệp của user A.
2. Hai dự án cùng tên file; cùng tên hai phiên bản khác byte; đồng thời upload; bản gốc được trả đúng byte/độ dài/hash; re-open/reload giữ lựa chọn chính xác, không trộn dự án.
3. Dùng spies chặn `takeoff_plans`, `compute_rough`, ghi `takeoff_results`, LLM: sau upload và preview số lượt gọi bằng 0; preview DXF/DWG, missing converter, hỏng, vượt giới hạn đều trả trạng thái rõ; DWG nguyên bản không thay đổi.
4. Sau click phân tích, chỉ IDs/hash/role qua JSON; không gửi lại multipart. Pipeline nhận đúng bytes/revision đã chọn; hash sai, file bị đổi, role mơ hồ bị chặn; tham khảo không tự được dùng như KT/KC.
5. Lỗi copy/DB rollback, xung đột version/concurrency, restart, stale hash và thu gom orphan; kiểm đúng dữ liệu được phép. Không thử upload Tân Bình khi gate từ chối còn hiệu lực.

## Điểm cần chốt trước release

01 phân vùng owner và quyết định migration/backfill, tạo/chọn project DB, metadata revision/role và quyền admin ngoại lệ; 02/17 chốt cách chuyển fileRef; 03 chốt adapter pipeline và định dạng kết quả/progress. Không có evidence test terminal hoặc 100 tải HTTP ở hợp đồng này.
