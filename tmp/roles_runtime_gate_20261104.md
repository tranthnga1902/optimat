# Kiểm tra điều kiện áp delta vai trò

- Kết quả: **dừng trước khi áp delta**.
- Kiểm tra chỉ đọc `Get-Process -Id 10060` không tìm thấy tiến trình có PID 10060. Vì vậy không thể đối chiếu kết nối TCP của PID này với `pg_stat_activity` hoặc xác nhận database runtime.
- SHA-256 delta `project_document_roles.sql`: `547b8b44bc2154fe97c4e236f7239283ea55abca5a3e12397e21e4acfaed9a6d`.
- SHA-256 rollback `project_document_roles_rollback.sql`: `0c547c4ddd73e73ddc655c60cd86d47eaa42c4a73be5985aa583472276adc5f2`.
- Không thực thi delta hay rollback; chưa thay đổi database, dữ liệu hoặc runtime.
