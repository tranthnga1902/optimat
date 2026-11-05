# Gói đề xuất áp delta vai trò — 04/11/2026

**Trạng thái:** chuẩn bị để duyệt; delta chưa áp vào database ứng dụng. Không khởi động lại API, sửa source hoặc chạy thêm test trong bước lập gói. Kết quả trước đó: kiểm thử XLS tập trung 46/46 và delta trong schema tạm `optimat_test` 1/1; không coi đó là nghiệm thu runtime.

## Đích và thay đổi

- Database ứng dụng **được cấu hình**: PostgreSQL local, `optimat`, schema `public`, bảng `project_document_revisions`. Kiểm tra metadata ngày 04/11 cho thấy `project_document_revisions` có 0 dòng, `project_profile_revisions` có 1 dòng; bảng `projects`, `project_files`, `takeoff_results` lần lượt 23, 126, 24 dòng. Đây là snapshot tại thời điểm kiểm tra, không phải số cố định.
- Constraint `ck_document_role` đang validated, kiểm `role` thuộc `KT`, `KC`, `THAM_KHAO`. Delta thay bằng check cho `KT`, `KC`, `HO_SO`, `TIEN_LUONG`, `THAM_KHAO`. Delta không sửa hàng, blob, owner, lịch sử hay bảng khác.
- File delta `scripts/db/project_document_roles.sql`: SHA-256 `547b8b44bc2154fe97c4e236f7239283ea55abca5a3e12397e21e4acfaed9a6d`.
- File rollback `scripts/db/project_document_roles_rollback.sql`: SHA-256 `0c547c4ddd73e73ddc655c60cd86d47eaa42c4a73be5985aa583472276adc5f2`.
- Migration lịch sử `scripts/db/project_documents.sql` giữ nguyên; SHA-256 `6d322334a36dc8a09d72be1352469661123f85f46d238fd34fb9f49d73467575`.

Biên bản metadata và hash không chứa mật khẩu: `tmp/roles_app_preflight_20261104.json`. Trước khi áp, phải kiểm lại tại thời điểm thực thi: kết nối đúng database ứng dụng đã xác nhận, schema/table/constraint hiện tại đúng dự kiến, hash file đúng, backup hoặc snapshot phù hợp với chính sách vận hành, và ghi số đếm/định nghĩa constraint để đối chiếu. Không áp nếu thiếu bảng, constraint đã đổi, hash khác hoặc đích chưa chắc chắn.

## Thực thi và dừng an toàn

Delta là một giao dịch: `ALTER TABLE ... DROP CONSTRAINT`, rồi `ADD CONSTRAINT ... CHECK`, rồi commit. `ALTER TABLE` cần khóa bảng mạnh và có thể chờ truy cập khác; cần chọn cửa sổ thực thi phù hợp. Không thay file SQL để chèn timeout. Runner có thể thực thi `BEGIN`, sau đó trong **cùng kết nối và giao dịch** đặt `SET LOCAL lock_timeout = '3s'` và `SET LOCAL statement_timeout = '30s'`, rồi chạy lần lượt đúng hai câu ALTER trong file đã kiểm hash và `COMMIT`. Các giá trị này là đề xuất để review; nếu không phù hợp tải thực tế, chốt lại trước khi chạy. Không chạy nguyên file có `BEGIN/COMMIT` lồng trong giao dịch ngoài hoặc đặt `SET LOCAL` ngoài giao dịch.

Trước ALTER, trong cùng giao dịch lấy khóa thích hợp trên bảng và kiểm lại constraint/target dưới khóa. Nếu khóa chờ quá hạn, lệnh lỗi, điều kiện kiểm tra sai hoặc xác minh trong giao dịch không đạt: rollback toàn bộ và báo lỗi đã lọc bí mật; không thử lại mù quáng. Nếu commit báo lỗi/đứt kết nối, trạng thái commit có thể không rõ: dừng và kiểm metadata chỉ đọc trước bất kỳ lần thử lại nào.

Rollback riêng chỉ được thực hiện theo phương án được duyệt: khóa bảng, kiểm không có revision `HO_SO` hoặc `TIEN_LUONG`, rồi thu hẹp check trong cùng giao dịch. Nếu có một trong hai role mới thì **dừng**, giữ dữ liệu và lịch sử; không xóa hay đổi role để ép rollback. Script rollback đã chứa guard này. Không tự xóa hai bảng revision.

## Xác minh sau áp

Trong giao dịch và sau commit, đọc lại `current_database`, tên/namespace bảng, `ck_document_role`, `convalidated`, định nghĩa đầy đủ và tập 5 role; đối chiếu với SQL đã duyệt. Ghi số dòng và thống kê role của bảng revision/profile, số dòng các bảng dự án/tệp/kết quả trước và sau. Khi ứng dụng còn ghi đồng thời, thay đổi count có thể do hoạt động hợp lệ khác: không suy diễn nguyên nhân, điều tra trước khi tuyên bố bảo toàn. DDL không yêu cầu đọc nội dung hồ sơ hoặc dữ liệu cá nhân. Biên bản ghi thời điểm, hash, kết quả commit/xác minh và tình trạng lỗi, không lưu URL/mật khẩu. Nếu cần chứng minh dữ liệu byte/hàng bất biến vượt quá số đếm thì cần phương án fingerprint/snapshot phù hợp và riêng tư được duyệt; số đếm đơn thuần không chứng minh nội dung bất biến.

## Chưa chứng minh database của API đang chạy

`runtime_target_verified=false`: kiểm tra trước chỉ xác nhận `DATABASE_URL` của tiến trình preflight và `current_database()` trên kết nối đó. Chưa chứng minh PID API `10060` dùng cùng đích; health PostgreSQL hay tên biến cấu hình không đủ.

Một hướng chứng minh chỉ đọc, nếu hệ thống cho phép: xác minh PID và thời điểm khởi động còn đúng, quan sát cặp cổng kết nối TCP của PID tới PostgreSQL, rồi đối chiếu `client_port`, `datname`, địa chỉ và thời điểm trong `pg_stat_activity` trên server. Chỉ thu metadata cần thiết, không đọc environment tiến trình, connection URL, mật khẩu hoặc câu SQL nhạy cảm. Phải phân biệt cổng/tiến trình tái sử dụng; nếu không có kết nối hiện hữu, thiếu quyền xem metadata, PID đã đổi hoặc tương quan không đủ rõ thì **không kết luận được**. Cần bằng chứng vận hành tương đương được chủ môi trường cung cấp trước khi tuyên bố API đang dùng đích này.
