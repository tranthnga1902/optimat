-- Phép thử migration đợt 0: chạy trên database có lược đồ hiện có (TRƯỚC migration).
-- Bước 1 (file này, phần nạp): tạo các dòng cũ giống 26 dòng thật của takeoff_results theo từng loại.
-- Bước 2: chạy migration_dot0_20261104.sql.  Bước 3: chạy phần kiểm ở cuối file migration_dot0_20261104_check.sql.
INSERT INTO users (user_id, email, full_name, password_hash) VALUES (1, 'qa@example.test', 'QA', 'x');
INSERT INTO projects (project_id, user_id, name, address) VALUES (1, 1, 'VN001', ''), (3, 1, 'mô phỏng', ''), (23, 1, 'QA', '');
INSERT INTO project_files (file_id, project_id, filename, file_type, stored_path) VALUES (4, 1, 'dt.pdf', 'pdf', '/x'), (10, 1, 'kt.dxf', 'dxf', '/y'), (127, 23, 'sample_floor.dxf', 'dxf', '/s');
INSERT INTO project_document_revisions (file_id, version, sha256, stored_path, size_bytes, format, role) VALUES (127, 1, repeat('f',64), '/s', 18229, 'dxf', 'KT');
INSERT INTO project_profile_revisions (project_id, version, payload) VALUES (23, 3, '{}');
INSERT INTO takeoff_results (takeoff_id, project_id, file_id, result, confirmed_at) VALUES
  (1, 1, 4,  '{"kind":"estimate_reference","data_kind":"ACTUAL"}', NULL),
  (2, 1, 10, '{"kind":"estimate_comparison","verification_status":"chua_kiem"}', NULL),
  (5, 3, NULL, '{"kind":"synthetic_housing","data_kind":"SYNTHETIC"}', NULL),
  (25, 23, NULL, '{"file":"sample_floor.dxf","walls_kept":5}', now()),
  (26, 23, NULL, '{"kind":"rough","input":{"file":"sample_floor.dxf"}}', now());
