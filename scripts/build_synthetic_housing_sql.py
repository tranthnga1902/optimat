"""Sinh SQL tự chứa từ JSONL, không cần máy chủ PostgreSQL đọc tệp cục bộ."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'data/ground_truth/du_toan/synthetic_20_normalized.jsonl'
target = root / 'sql/nhap_20_ho_so_gia_lap.sql'
records = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line]
assert len(records) == 20 and len({r['house_id'] for r in records}) == 20
assert all(r['data_kind'] == 'SYNTHETIC' for r in records)
payload = json.dumps(records, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
assert '$housing_payload$' not in payload
sql = '''-- PostgreSQL: chạy toàn bộ tệp trên database optimat đã có schema ứng dụng.
-- Nguồn tệp chỉ được lưu làm metadata trong JSON; SQL không sao chép tệp vào máy chủ.
-- Các dự án thuộc tài khoản kỹ thuật vô hiệu hóa; dữ liệu chưa được người dùng xác nhận.
BEGIN;
DO $housing_import$
DECLARE
  payload jsonb := $housing_payload$''' + payload + '''$housing_payload$::jsonb;
  r jsonb;
  owner_id integer;
  project_id_value integer;
  result_id integer;
  project_count integer;
  result_count integer;
  project_name text;
  existing_result jsonb;
  existing_confirmed timestamptz;
BEGIN
  IF jsonb_array_length(payload) <> 20 OR
     (SELECT count(DISTINCT item->>'house_id') FROM jsonb_array_elements(payload) item) <> 20 OR
     EXISTS (SELECT 1 FROM jsonb_array_elements(payload) item WHERE item->>'data_kind' IS DISTINCT FROM 'SYNTHETIC') THEN
    RAISE EXCEPTION 'Bộ dữ liệu không hợp lệ';
  END IF;
  SELECT user_id INTO owner_id FROM users WHERE email = 'synthetic-housing@import.invalid';
  IF owner_id IS NULL THEN
    INSERT INTO users(email, full_name, role, is_active, password_hash)
      VALUES ('synthetic-housing@import.invalid', 'Kho nhà giả lập', 'user', false, '!disabled')
      RETURNING user_id INTO owner_id;
  ELSIF EXISTS (SELECT 1 FROM users WHERE user_id=owner_id AND is_active) THEN
    RAISE EXCEPTION 'Tài khoản nhập dữ liệu đang hoạt động; dừng để kiểm tra';
  END IF;
  FOR r IN SELECT value FROM jsonb_array_elements(payload) LOOP
    project_name := '[SYNTHETIC:' || (r->>'house_id') || '] Hồ sơ nhà ở giả lập';
    SELECT count(*), min(project_id) INTO project_count, project_id_value FROM projects
      WHERE user_id=owner_id AND name=project_name;
    IF project_count > 1 THEN RAISE EXCEPTION 'Dự án trùng: %', project_name; END IF;
    IF project_count = 0 THEN
      INSERT INTO projects(user_id,name,address,excluded_materials)
        VALUES(owner_id,project_name,COALESCE(r#>>'{data,project,address}',''), '[]'::jsonb)
        RETURNING project_id INTO project_id_value;
    END IF;
    SELECT count(*), min(takeoff_id) INTO result_count, result_id FROM takeoff_results
      WHERE project_id=project_id_value AND result->>'kind'='synthetic_housing';
    IF result_count > 1 THEN RAISE EXCEPTION 'Kết quả trùng: %', project_name; END IF;
    IF result_count = 0 THEN
      INSERT INTO takeoff_results(project_id,file_id,result,layer_overrides,confirmed_at)
        VALUES(project_id_value,NULL,r,'{}'::jsonb,NULL)
        RETURNING takeoff_id INTO result_id;
    ELSE
      SELECT result, confirmed_at INTO existing_result, existing_confirmed FROM takeoff_results WHERE takeoff_id=result_id;
      IF existing_confirmed IS NOT NULL OR existing_result IS DISTINCT FROM r THEN
        RAISE EXCEPTION 'Kết quả đã được xác nhận hoặc khác dữ liệu nguồn: %', project_name;
      END IF;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM takeoff_results WHERE takeoff_id=result_id AND result=r AND confirmed_at IS NULL) THEN
      RAISE EXCEPTION 'Không kiểm tra được kết quả: %', project_name;
    END IF;
  END LOOP;
  INSERT INTO audit_logs(action,detail) VALUES ('IMPORT_SYNTHETIC_HOUSING_SQL',
    jsonb_build_object('count',20,'data_kind','SYNTHETIC','file_links','metadata_only'));
END $housing_import$;
-- Xem số dòng và số lượng chi tiết trước COMMIT; lỗi ở trên sẽ hủy giao dịch.
SELECT p.name, t.result->>'data_kind' AS data_kind,
       jsonb_array_length(t.result#>'{data,quantities}') AS so_dong_tien_luong,
       jsonb_array_length(t.result->'files') AS so_tep_tham_chieu,
       t.confirmed_at
FROM projects p JOIN users u ON u.user_id=p.user_id
JOIN takeoff_results t ON t.project_id=p.project_id
WHERE u.email='synthetic-housing@import.invalid' AND t.result->>'kind'='synthetic_housing'
ORDER BY p.name;
COMMIT;
'''
target.write_text(sql, encoding='utf-8')
print('SQL:', target, 'records:', len(records), 'bytes:', target.stat().st_size)
