-- Phép thử DDL v2 (04/11/2026). Chạy trên database TRỐNG đã áp: sql hiện có -> migration_dot0 -> ddl_de_xuat.
-- Ca hỏng phải bị chặn đúng tên ràng buộc/trigger (cho phép "a|b" khi hai FK cùng bắt được); ca hợp lệ phải được nhận.
CREATE TEMP TABLE _ket_qua (stt serial, nhom text, ca text, mong_doi text, thuc_te text, dat boolean);

CREATE OR REPLACE FUNCTION pg_temp.ok(nhom text, ca text, q text) RETURNS void AS $$
BEGIN
  EXECUTE q; INSERT INTO _ket_qua (nhom, ca, mong_doi, thuc_te, dat) VALUES (nhom, ca, 'nhận', 'nhận', true);
EXCEPTION WHEN others THEN INSERT INTO _ket_qua (nhom, ca, mong_doi, thuc_te, dat) VALUES (nhom, ca, 'nhận', SQLERRM, false);
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION pg_temp.fail(nhom text, ca text, q text, rang_buoc text) RETURNS void AS $$
DECLARE c text;
BEGIN
  EXECUTE q; INSERT INTO _ket_qua (nhom, ca, mong_doi, thuc_te, dat) VALUES (nhom, ca, 'chặn ' || rang_buoc, 'nhận (SAI)', false);
EXCEPTION WHEN others THEN
  GET STACKED DIAGNOSTICS c = CONSTRAINT_NAME;
  INSERT INTO _ket_qua (nhom, ca, mong_doi, thuc_te, dat) VALUES (nhom, ca, 'chặn ' || rang_buoc, coalesce(nullif(c,''), SQLERRM), coalesce(c,'') ~ ('^(' || rang_buoc || ')$'));
END $$ LANGUAGE plpgsql;

-- ---------- dữ liệu nền: hai công trình A (23) và B (24) ----------
SELECT pg_temp.ok('nền', 'danh mục, người dùng, 2 dự án, tệp, phiên bản, hồ sơ, lần nhận dạng, lần bóc', $q$
  INSERT INTO material_groups VALUES ('G1', 1, 'Vật liệu xây', 'gạch, vữa');
  INSERT INTO materials (material_id, name, "group", unit, data_kind) VALUES ('AAC01','Gạch AAC','G1','m3','ACTUAL'), ('GN01','Gạch đặc','G1','viên','ACTUAL');
  INSERT INTO wall_systems (wall_system_id, material_id, data_kind) VALUES ('W-AAC01-100','AAC01','ACTUAL'), ('W-GN01-220','GN01','ACTUAL');
  INSERT INTO rough_norms (id, work_code, qty, qty_unit, norm_code, source) VALUES (101, 'TRAT', 0.017, 'm3/m2', 'AK.21224', 'TT 38/2026 PL VII');
  INSERT INTO price_records (id, date, material_id, province, quantity, unit, unit_price, source, data_kind, price_level)
    VALUES (101, '2026-01-15', 'AAC01', 'Hà Nội', 1, 'm3', 1250000, 'CBG 02.01/2026 trang 14', 'ACTUAL', 'BULLETIN');
  INSERT INTO users (user_id, email, full_name, password_hash) VALUES (101, 'qa@example.test', 'QA', 'x');
  INSERT INTO projects (project_id, user_id, name, address) VALUES (23, 101, 'A', ''), (24, 101, 'B', '');
  INSERT INTO project_files (file_id, project_id, filename, file_type, stored_path) VALUES (127, 23, 'sample_floor.dxf', 'dxf', '/a'), (200, 24, 'b.dxf', 'dxf', '/b');
  INSERT INTO project_document_revisions (revision_id, project_id, file_id, version, sha256, stored_path, size_bytes, format, role) OVERRIDING SYSTEM VALUE
    VALUES (101, 23, 127, 1, repeat('f',64), '/a', 18229, 'dxf', 'KT'), (102, 24, 200, 1, repeat('b',64), '/b', 1000, 'dxf', 'KT');
  INSERT INTO project_profile_revisions (project_id, version, payload) VALUES (23, 3, '{}'), (24, 1, '{}');
  INSERT INTO recognition_runs (recog_run_id, project_id, profile_version, parser_version, rules_sha256) OVERRIDING SYSTEM VALUE
    VALUES (101, 23, 3, '2026.11', repeat('1',64)), (102, 24, 1, '2026.11', repeat('1',64)), (103, 23, 3, '2026.12', repeat('2',64));
  INSERT INTO recognition_run_inputs VALUES (101, 23, 101), (102, 24, 102), (103, 23, 101);
  INSERT INTO takeoff_results (takeoff_id, project_id, file_id, result, kind, data_kind, recog_run_id, profile_version)
    VALUES (101, 23, 127, '{}', 'takeoff', 'SAMPLE', 101, 3), (102, 24, 200, '{}', 'takeoff', 'SAMPLE', 102, 1);
  INSERT INTO optimization_runs (run_id, project_id, takeoff_id, method, solutions) VALUES (102, 24, 102, 'nsga2', '[]');
$q$);

SELECT pg_temp.ok('nền', 'chuỗi lần nhận dạng A: hình, đối tượng CAD, bằng chứng, tầng, cấu kiện W5, số đo', $q$
  INSERT INTO drawing_views (view_id, recog_run_id, revision_id, view_key, kind, bbox_wcs) OVERRIDING SYSTEM VALUE VALUES (101, 101, 101, 'plan:0', 'mat_bang', '[0,0,5000,12000]');
  INSERT INTO drawing_views (view_id, recog_run_id, revision_id, view_key, kind, bbox_wcs) OVERRIDING SYSTEM VALUE VALUES (102, 102, 102, 'plan:0', 'mat_bang', '[0,0,4000,15000]');
  INSERT INTO drawing_entities (entity_id, revision_id, handle, dxftype, layer, text_raw) OVERRIDING SYSTEM VALUE
    VALUES (101, 101, '2A1', 'TEXT', 'KICHTHUOC', 'Tường ngăn 110 xây gạch AAC'), (102, 101, '1F0', 'LINE', 'TUONG', NULL), (103, 102, '9B', 'LINE', 'TUONG', NULL);
  INSERT INTO evidence_sources (evidence_id, recog_run_id, kind, revision_id, view_id, raw_content, interpreted) OVERRIDING SYSTEM VALUE
    VALUES (101, 101, 'chu', 101, 101, 'Tường ngăn 110 xây gạch AAC', '{"material_id":"AAC01","day_mm":110}'),
           (102, 102, 'chu', 102, 102, 'Tường 220', '{"day_mm":220}');
  INSERT INTO evidence_entities VALUES (101, 101, 101, 101);
  INSERT INTO building_levels (level_id, recog_run_id, code, name, seq, height_status) OVERRIDING SYSTEM VALUE VALUES (101, 101, 'TRET', 'Tầng trệt', 0, 'D'), (102, 102, 'TRET', 'Tầng trệt', 0, 'D');
  INSERT INTO view_levels VALUES (101, 101, 101);
  INSERT INTO building_elements (element_id, recog_run_id, level_id, code, kind, subtype) OVERRIDING SYSTEM VALUE
    VALUES (101, 101, 101, 'W5', 'tuong', 'ngan'), (102, 102, 102, 'W1', 'tuong', 'bao_che');
  INSERT INTO element_occurrences (occurrence_id, recog_run_id, element_id, view_id, revision_id, role) OVERRIDING SYSTEM VALUE VALUES (101, 101, 101, 101, 101, 'hinh_chinh');
  INSERT INTO occurrence_entities VALUES (101, 101, 101, 102);
  INSERT INTO element_measurements (measurement_id, recog_run_id, element_id, quantity_kind, value, unit, method, status, selected) OVERRIDING SYSTEM VALUE
    VALUES (101, 101, 101, 'dai', 4560, 'mm', 'hinh_hoc', 'B', true), (102, 101, 101, 'dai', 4600, 'mm', 'dimension', 'A', false),
           (103, 102, 102, 'dai', 11780, 'mm', 'hinh_hoc', 'B', true);
  INSERT INTO measurement_evidence VALUES (101, 101, 101, 'chinh');
$q$);

-- ---------- 1. Liên kết chéo công trình / lần nhận dạng / lần bóc ----------
SELECT pg_temp.fail('1 chéo', 'lần nhận dạng A dùng phiên bản tệp của B', $q$INSERT INTO recognition_run_inputs VALUES (101, 23, 102)$q$, 'fk_run_inputs_revision');
SELECT pg_temp.fail('1 chéo', 'hình của lần A trỏ phiên bản tệp của B', $q$INSERT INTO drawing_views (recog_run_id, revision_id, view_key, kind, bbox_wcs) VALUES (101, 102, 'plan:9', 'mat_bang', '[0,0,1,1]')$q$, 'fk_views_run_input');
SELECT pg_temp.fail('1 chéo', 'lần bóc của A gắn lần nhận dạng của B', $q$INSERT INTO takeoff_results (project_id, result, kind, data_kind, recog_run_id) VALUES (23, '{}', 'takeoff', 'SAMPLE', 102)$q$, 'fk_takeoff_recog_run');
SELECT pg_temp.fail('1 chéo', 'lần bóc trỏ phiên bản hồ sơ không có của dự án', $q$INSERT INTO takeoff_results (project_id, result, kind, data_kind, profile_version) VALUES (23, '{}', 'takeoff', 'SAMPLE', 1)$q$, 'fk_takeoff_profile');
SELECT pg_temp.fail('1 chéo', 'bằng chứng lần A gắn đối tượng CAD của tệp B', $q$INSERT INTO evidence_entities VALUES (101, 101, 102, 103)$q$, 'fk_evidence_entities_evidence|fk_evidence_entities_entity');
SELECT pg_temp.fail('1 chéo', 'lần xuất hiện gắn đối tượng CAD khác phiên bản', $q$INSERT INTO occurrence_entities VALUES (101, 101, 102, 103)$q$, 'fk_occ_entities_occ|fk_occ_entities_entity');
SELECT pg_temp.fail('1 chéo', 'số đo lần A nối bằng chứng lần B', $q$INSERT INTO measurement_evidence VALUES (101, 101, 102, 'chinh')$q$, 'fk_meas_ev_evidence');
SELECT pg_temp.fail('1 chéo', 'cấu kiện lần A gắn tầng lần B', $q$INSERT INTO building_elements (recog_run_id, level_id, code, kind) VALUES (101, 102, 'W9', 'tuong')$q$, 'fk_elements_level');
SELECT pg_temp.ok  ('1 chéo', 'công tác lần bóc A (nháp) cho W5, và công tác lần bóc B', $q$
  INSERT INTO takeoff_items (item_id, takeoff_id, recog_run_id, seq, work_code, element_id, unit, quantity, formula, wall_system_id, status) OVERRIDING SYSTEM VALUE
    VALUES (101, 101, 101, 1, 'XAY', 101, 'm3', 1.6553, '4,56 × 3,30 × 0,110', 'W-AAC01-100', 'C'),
           (102, 102, 102, 1, 'XAY', 102, 'm3', 8.55, '…', 'W-GN01-220', 'C')$q$);
SELECT pg_temp.fail('1 chéo', 'công tác lần bóc A dùng cấu kiện của lần nhận dạng B', $q$INSERT INTO takeoff_items (takeoff_id, recog_run_id, seq, work_code, element_id, unit, quantity, status) VALUES (101, 101, 9, 'XAY', 102, 'm3', 1, 'C')$q$, 'fk_items_element');
SELECT pg_temp.fail('1 chéo', 'công tác khai lần nhận dạng khác lần bóc', $q$INSERT INTO takeoff_items (takeoff_id, recog_run_id, seq, work_code, unit, quantity, status) VALUES (101, 102, 9, 'XAY', 'm3', 1, 'C')$q$, 'fk_items_takeoff');

-- ---------- 3. Phiên bản nhận dạng ----------
SELECT pg_temp.ok  ('3 phiên bản', 'đọc lại cùng hồ sơ bằng bộ quy tắc mới: W5 ở lần 103 không đè W5 của lần 101', $q$INSERT INTO building_elements (recog_run_id, code, kind) VALUES (103, 'W5', 'tuong')$q$);
SELECT pg_temp.fail('3 phiên bản', 'trùng W5 trong cùng lần nhận dạng, cùng tầng', $q$INSERT INTO building_elements (recog_run_id, level_id, code, kind) VALUES (101, 101, 'W5', 'tuong')$q$, 'uq_elements_code');

-- ---------- 6. CHECK theo ca review ----------
SELECT pg_temp.fail('6 CHECK', 'chọn ứng viên số đo không có giá trị (D)', $q$INSERT INTO element_measurements (recog_run_id, element_id, quantity_kind, unit, method, status, selected) VALUES (101, 101, 'cao', 'mm', 'thong_so_du_an', 'D', true)$q$, 'ck_meas_selected_has_value');
SELECT pg_temp.fail('6 CHECK', 'số đo có giá trị mà gắn D', $q$INSERT INTO element_measurements (recog_run_id, element_id, quantity_kind, value, unit, method, status) VALUES (101, 101, 'cao', 3300, 'mm', 'thong_so_du_an', 'D')$q$, 'ck_meas_missing_is_d');
SELECT pg_temp.fail('6 CHECK', 'người nhập mà gắn A', $q$INSERT INTO element_measurements (recog_run_id, element_id, quantity_kind, value, unit, method, status) VALUES (101, 101, 'cao', 3300, 'mm', 'nguoi_nhap', 'A')$q$, 'ck_meas_user_is_c');
SELECT pg_temp.fail('6 CHECK', 'chiều dài ghi m2', $q$INSERT INTO element_measurements (recog_run_id, element_id, quantity_kind, value, unit, method, status) VALUES (101, 101, 'dai', 4.56, 'm2', 'hinh_hoc', 'B')$q$, 'ck_meas_unit');
SELECT pg_temp.ok  ('6 CHECK', 'dòng khấu trừ cốp pha −0,194 m2 đánh dấu khấu trừ', $q$INSERT INTO takeoff_items (takeoff_id, recog_run_id, seq, work_code, unit, is_deduction, quantity, quantity_known, formula, status) VALUES (101, 101, 2, 'COP_PHA', 'm2', true, -0.194, -0.194, 'trừ lỗ sàn', 'B')$q$);
SELECT pg_temp.fail('6 CHECK', 'số âm mà không đánh dấu khấu trừ', $q$INSERT INTO takeoff_items (takeoff_id, recog_run_id, seq, work_code, unit, quantity, status) VALUES (101, 101, 3, 'COP_PHA', 'm2', -0.29, 'B')$q$, 'ck_items_sign');
SELECT pg_temp.fail('6 CHECK', 'phần đã biết vượt tổng', $q$INSERT INTO takeoff_items (takeoff_id, recog_run_id, seq, work_code, unit, quantity, quantity_known, status, missing) VALUES (101, 101, 4, 'TRAT', 'm2', 10, 12, 'D', '{"dày trát mặt ngoài"}')$q$, 'ck_items_known');
SELECT pg_temp.fail('6 CHECK', 'công tác D không ghi thiếu gì', $q$INSERT INTO takeoff_items (takeoff_id, recog_run_id, seq, work_code, unit, status) VALUES (101, 101, 5, 'SAN', 'm3', 'D')$q$, 'ck_items_d_has_reason');

-- ---------- 5. Snapshot đầu vào và định mức ----------
SELECT pg_temp.ok  ('5 snapshot', 'chụp đầu vào số đo và định mức kèm nguồn', $q$
  INSERT INTO takeoff_item_inputs (item_id, recog_run_id, seq, input_kind, measurement_id, label, value_snapshot, unit, status) VALUES (101, 101, 1, 'so_do', 101, 'chiều dài', 4560, 'mm', 'B');
  INSERT INTO takeoff_item_inputs (item_id, recog_run_id, seq, input_kind, rough_norm_id, label, value_snapshot, unit, status, norm_code, confirmation, source_snapshot)
    VALUES (101, 101, 2, 'dinh_muc', 101, 'vữa trát / m2', 0.017, 'm3/m2', 'A', 'AK.21224', 'nguon', 'TT 38/2026 PL VII')$q$);
SELECT pg_temp.fail('5 snapshot', 'định mức có số mà không chụp nguồn', $q$INSERT INTO takeoff_item_inputs (item_id, recog_run_id, seq, input_kind, rough_norm_id, label, value_snapshot, unit, status) VALUES (101, 101, 3, 'dinh_muc', 101, 'vữa', 0.017, 'm3/m2', 'A')$q$, 'ck_inputs_norm_snapshot');
SELECT pg_temp.fail('5 snapshot', 'đầu vào lấy số đo của lần nhận dạng khác', $q$INSERT INTO takeoff_item_inputs (item_id, recog_run_id, seq, input_kind, measurement_id, label, value_snapshot, unit, status) VALUES (101, 101, 4, 'so_do', 103, 'chiều dài', 11780, 'mm', 'B')$q$, 'fk_inputs_meas');

-- ---------- 2. Khóa lịch sử ----------
SELECT pg_temp.fail('2 bất biến', 'sửa giá trị số đo đã lưu', $q$UPDATE element_measurements SET value = 4580 WHERE measurement_id = 101$q$, 'trg_measurement_value_fixed');
SELECT pg_temp.ok  ('2 bất biến', 'đổi ứng viên được chọn khi lần nhận dạng còn nháp', $q$UPDATE element_measurements SET selected = false WHERE measurement_id = 101; UPDATE element_measurements SET selected = true WHERE measurement_id = 102$q$);
SELECT pg_temp.fail('2 bất biến', 'sửa đối tượng CAD', $q$UPDATE drawing_entities SET layer = 'X' WHERE entity_id = 102$q$, 'trg_drawing_entities_insert_only');
SELECT pg_temp.fail('2 bất biến', 'sửa phiên bản tệp đã lưu', $q$UPDATE project_document_revisions SET sha256 = repeat('0',64) WHERE revision_id = 101$q$, 'trg_project_document_revisions_insert_only');
SELECT pg_temp.fail('2 bất biến', 'xác nhận lần bóc khi lần nhận dạng còn nháp', $q$UPDATE takeoff_results SET state = 'xac_nhan', confirmed_at = now() WHERE takeoff_id = 102$q$, 'trg_takeoff_needs_locked_run');
SELECT pg_temp.ok  ('2 bất biến', 'khóa lần nhận dạng A rồi xác nhận lần bóc A', $q$UPDATE recognition_runs SET state = 'khoa', locked_at = now() WHERE recog_run_id = 101; UPDATE takeoff_results SET state = 'xac_nhan', confirmed_at = now() WHERE takeoff_id = 101$q$);
SELECT pg_temp.fail('2 bất biến', 'thêm hình vào lần nhận dạng đã khóa', $q$INSERT INTO drawing_views (recog_run_id, revision_id, view_key, kind, bbox_wcs) VALUES (101, 101, 'plan:1', 'mat_bang', '[0,0,1,1]')$q$, 'trg_recog_run_locked');
SELECT pg_temp.fail('2 bất biến', 'đổi ứng viên được chọn sau khi khóa', $q$UPDATE element_measurements SET selected = false WHERE measurement_id = 102$q$, 'trg_recog_run_locked');
SELECT pg_temp.fail('2 bất biến', 'xóa số đo của lần đã khóa', $q$DELETE FROM element_measurements WHERE measurement_id = 101$q$, 'trg_recog_run_locked');
SELECT pg_temp.fail('2 bất biến', 'mở khóa lần nhận dạng', $q$UPDATE recognition_runs SET state = 'nhap', locked_at = NULL WHERE recog_run_id = 101$q$, 'trg_recog_run_locked');
SELECT pg_temp.fail('2 bất biến', 'sửa công tác của lần bóc đã xác nhận', $q$UPDATE takeoff_items SET quantity = 2 WHERE item_id = 101$q$, 'trg_takeoff_locked');
SELECT pg_temp.fail('2 bất biến', 'sửa nội dung lần bóc đã xác nhận', $q$UPDATE takeoff_results SET result = '{"x":1}' WHERE takeoff_id = 101$q$, 'trg_takeoff_locked');

-- ---------- 5–6. Phương án vật liệu, giá ----------
SELECT pg_temp.ok  ('5 phương án', 'phương án theo thiết kế trên lần bóc A', $q$INSERT INTO material_scenarios (scenario_id, takeoff_id, name, origin, price_basis_date) OVERRIDING SYSTEM VALUE VALUES (101, 101, 'Theo thiết kế', 'thiet_ke', '2026-01-15')$q$);
SELECT pg_temp.fail('1 chéo', 'phương án lần bóc A dùng lượt tối ưu của lần bóc B', $q$INSERT INTO material_scenarios (takeoff_id, name, origin, run_id) VALUES (101, 'PA tối ưu', 'toi_uu', 102)$q$, 'fk_scen_opt_run');
SELECT pg_temp.fail('1 chéo', 'phương án lần bóc A gán công tác của lần bóc B', $q$INSERT INTO material_assignments (scenario_id, takeoff_id, recog_run_id, item_id, material_id, source, status) VALUES (101, 101, 101, 102, 'AAC01', 'nguoi_dung', 'C')$q$, 'fk_assign_item');
SELECT pg_temp.fail('6 CHECK', 'vật liệu và phương án tường không khớp', $q$INSERT INTO material_assignments (scenario_id, takeoff_id, recog_run_id, item_id, material_id, wall_system_id, source, status) VALUES (101, 101, 101, 101, 'GN01', 'W-AAC01-100', 'nguoi_dung', 'C')$q$, 'fk_assign_wall_material');
SELECT pg_temp.fail('6 CHECK', 'gán AI không bằng chứng', $q$INSERT INTO material_assignments (scenario_id, takeoff_id, recog_run_id, item_id, material_id, source, status) VALUES (101, 101, 101, 101, 'AAC01', 'de_xuat_ai', 'B')$q$, 'ck_assign_ai_has_evidence');
SELECT pg_temp.ok  ('5 phương án', 'gán theo thiết kế có bằng chứng, khớp phương án tường', $q$INSERT INTO material_assignments (scenario_id, takeoff_id, recog_run_id, item_id, material_id, wall_system_id, source, evidence_id, status) VALUES (101, 101, 101, 101, 'AAC01', 'W-AAC01-100', 'thiet_ke', 101, 'A')$q$);
SELECT pg_temp.fail('6 CHECK', 'đủ (complete) mà không có số, gắn A', $q$INSERT INTO material_requirements (scenario_id, takeoff_id, name, unit, complete, status) VALUES (101, 101, 'Gạch AAC', 'm3', true, 'A')$q$, 'ck_req_complete');
SELECT pg_temp.fail('6 CHECK', 'thiếu phần mà không gắn D', $q$INSERT INTO material_requirements (scenario_id, takeoff_id, name, unit, quantity, complete, status) VALUES (101, 101, 'Vữa AAC', 'tấn', 0.1, false, 'C')$q$, 'ck_req_complete');
SELECT pg_temp.fail('5 snapshot', 'có lượng hao hụt mà không chụp % và nguồn', $q$INSERT INTO material_requirements (scenario_id, takeoff_id, name, unit, quantity, complete, quantity_with_waste, status) VALUES (101, 101, 'Gạch AAC', 'm3', 1.6553, true, 1.7, 'C')$q$, 'ck_req_waste_snapshot');
SELECT pg_temp.ok  ('5 snapshot', 'nhu cầu gạch AAC + nguồn định mức đã chụp', $q$
  INSERT INTO material_requirements (requirement_id, scenario_id, takeoff_id, material_id, name, unit, quantity, complete, status) OVERRIDING SYSTEM VALUE VALUES (101, 101, 101, 'AAC01', 'Gạch AAC', 'm3', 1.6553, true, 'C');
  INSERT INTO requirement_sources (requirement_id, takeoff_id, item_id, wall_system_id, norm_qty, norm_unit, norm_source, confirmation, quantity_part) VALUES (101, 101, 101, 'W-AAC01-100', 1.0, 'm3/m3', 'wall_systems W-AAC01-100', 'tinh', 1.6553)$q$);
SELECT pg_temp.fail('5 snapshot', 'nguồn định mức có hệ số mà thiếu đơn vị và nguồn', $q$INSERT INTO requirement_sources (requirement_id, takeoff_id, item_id, norm_qty) VALUES (101, 101, 101, 1.0)$q$, 'ck_reqsrc_norm_snapshot|requirement_sources_pkey');
SELECT pg_temp.ok  ('5 snapshot', 'giá thực dùng: chép giá công bố kèm cơ sở VAT, vận chuyển, nguồn', $q$INSERT INTO scenario_price_lines (scenario_id, takeoff_id, material_id, price_record_id, price_level, data_kind, unit_price, price_unit, vat_included, transport_included, price_date, province, source) VALUES (101, 101, 'AAC01', 101, 'BULLETIN', 'ACTUAL', 1250000, 'm3', 'NO', 'UNKNOWN', '2026-01-15', 'Hà Nội', 'CBG 02.01/2026 trang 14')$q$);
SELECT pg_temp.fail('5 snapshot', 'giá không có nguồn gốc và không phải dự đoán', $q$INSERT INTO scenario_price_lines (scenario_id, takeoff_id, material_id, supplier_id, price_level, data_kind, unit_price, price_unit, vat_included, transport_included, price_date, source) VALUES (101, 101, 'GN01', NULL, 'DEALER', 'ACTUAL', 1200, 'viên', 'NO', 'NO', '2026-01-15', 'gõ tay')$q$, 'ck_price_has_origin');
SELECT pg_temp.fail('5 snapshot', 'giá dự đoán khai là giá đại lý', $q$INSERT INTO scenario_price_lines (scenario_id, takeoff_id, material_id, price_level, data_kind, unit_price, price_unit, vat_included, transport_included, price_date, source, is_predicted) VALUES (101, 101, 'GN01', 'DEALER', 'ACTUAL', 1200, 'viên', 'NO', 'NO', '2026-01-15', 'XGBoost', true)$q$, 'ck_price_predicted');
SELECT pg_temp.fail('2 bất biến', 'chọn phương án khi chưa khóa', $q$UPDATE material_scenarios SET is_selected = true WHERE scenario_id = 101$q$, 'ck_scen_selected_locked');
SELECT pg_temp.ok  ('2 bất biến', 'khóa rồi chọn phương án', $q$UPDATE material_scenarios SET state = 'khoa' WHERE scenario_id = 101; UPDATE material_scenarios SET is_selected = true WHERE scenario_id = 101$q$);
SELECT pg_temp.fail('2 bất biến', 'sửa nhu cầu vật liệu của phương án đã khóa', $q$UPDATE material_requirements SET quantity = 2 WHERE requirement_id = 101$q$, 'trg_scenario_locked');
SELECT pg_temp.fail('2 bất biến', 'đổi ngày bảng giá của phương án đã khóa', $q$UPDATE material_scenarios SET price_basis_date = '2026-02-01' WHERE scenario_id = 101$q$, 'trg_scenario_locked');
SELECT pg_temp.fail('2 bất biến', 'xóa vật liệu đang được gán', $q$DELETE FROM materials WHERE material_id = 'AAC01'$q$, '.*_fkey|fk_.*');

SELECT count(*) FILTER (WHERE dat) AS dat, count(*) AS tong FROM _ket_qua;
SELECT nhom, count(*) FILTER (WHERE dat) || '/' || count(*) AS ket_qua FROM _ket_qua GROUP BY nhom ORDER BY nhom;
SELECT stt, nhom, ca, mong_doi, thuc_te FROM _ket_qua WHERE NOT dat ORDER BY stt;
\copy (SELECT stt, nhom, ca, mong_doi, thuc_te, dat FROM _ket_qua ORDER BY stt) TO 'ket_qua_tests.csv' WITH CSV HEADER
