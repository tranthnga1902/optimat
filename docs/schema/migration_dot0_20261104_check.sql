-- Kiểm sau migration đợt 0 (đi cùng migration_dot0_20261104_tests.sql). Mỗi dòng phải có dat = true.
SELECT 'phân loại ' || takeoff_id AS ca,
       kind || '/' || data_kind || '/' || state AS thuc_te,
       CASE takeoff_id WHEN 1 THEN 'estimate_reference/ACTUAL/tam' WHEN 2 THEN 'estimate_comparison/ACTUAL/tam'
                       WHEN 5 THEN 'synthetic_housing/SYNTHETIC/tam' WHEN 25 THEN 'takeoff/SAMPLE/xac_nhan' WHEN 26 THEN 'rough/SAMPLE/xac_nhan' END AS mong_doi,
       kind || '/' || data_kind || '/' || state =
       CASE takeoff_id WHEN 1 THEN 'estimate_reference/ACTUAL/tam' WHEN 2 THEN 'estimate_comparison/ACTUAL/tam'
                       WHEN 5 THEN 'synthetic_housing/SYNTHETIC/tam' WHEN 25 THEN 'takeoff/SAMPLE/xac_nhan' WHEN 26 THEN 'rough/SAMPLE/xac_nhan' END AS dat
  FROM takeoff_results
UNION ALL
SELECT 'revision có project_id', project_id::text, '23', project_id = 23 FROM project_document_revisions
UNION ALL
SELECT 'tiền NUMERIC', data_type, 'numeric', data_type = 'numeric' FROM information_schema.columns WHERE table_name = 'price_records' AND column_name = 'unit_price'
UNION ALL
SELECT 'fk_material_notes_material đã VALIDATE', convalidated::text, 'true', convalidated FROM pg_constraint WHERE conname = 'fk_material_notes_material'
ORDER BY 1;
