-- =============================================================================
-- OptiMat AI · MIGRATION ĐỢT 0 (04/11/2026) — sửa 28 bảng hiện có, chuyển dữ liệu cũ
-- Chạy trong MỘT giao dịch: psql -v ON_ERROR_STOP=1 -1 -f migration_dot0_20261104.sql
-- Sao lưu trước. Script tự dừng (RAISE) nếu còn dòng chưa phân loại được, không gán mặc định.
-- Phiên bản tài liệu cho 126 tệp cũ KHÔNG làm ở đây: cần đọc tệp trên đĩa và người duyệt vai trò
-- -> scripts/backfill_document_revisions.py (dry-run ra CSV, duyệt, rồi --apply).
-- =============================================================================

-- 0.1 Tiền tệ: FLOAT -> NUMERIC
ALTER TABLE price_records      ALTER COLUMN unit_price   TYPE NUMERIC(14,2);
ALTER TABLE supplier_materials ALTER COLUMN base_price   TYPE NUMERIC(14,2);
ALTER TABLE labor_rates        ALTER COLUMN rate_per_day TYPE NUMERIC(12,2);
ALTER TABLE vehicles           ALTER COLUMN base_fee     TYPE NUMERIC(12,2),
                               ALTER COLUMN fee_per_km   TYPE NUMERIC(12,2);
ALTER TABLE projects           ALTER COLUMN budget       TYPE NUMERIC(16,2);

-- 0.2 Miền giá trị (đã kiểm 04/11 trên CSDL đang chạy: 0 dòng vi phạm)
ALTER TABLE room_rules        ADD CONSTRAINT ck_room_rules_kind        CHECK (kind IN ('WET','BALCONY'));
ALTER TABLE wall_systems      ADD CONSTRAINT ck_wall_systems_role      CHECK (role IS NULL OR role IN ('envelope','partition'));
ALTER TABLE wall_systems      ADD CONSTRAINT ck_wall_systems_class     CHECK (detect_class IS NULL OR detect_class IN ('110','150','220','330'));
ALTER TABLE standards         ADD CONSTRAINT ck_standards_kind         CHECK (kind IN ('TCVN','QCVN','THONG_TU','KHAC'));
ALTER TABLE standards         ADD CONSTRAINT ck_standards_status       CHECK (status IN ('CON_HIEU_LUC','HET_HIEU_LUC','UNKNOWN'));
ALTER TABLE standards         ADD CONSTRAINT ck_standards_period       CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from);
ALTER TABLE model_versions    ADD CONSTRAINT ck_model_versions_target  CHECK (target IN ('material_price','transport_cost'));
ALTER TABLE optimization_runs ADD CONSTRAINT ck_optimization_method    CHECK (method IN ('nsga2','brute'));
ALTER TABLE optimization_runs ADD CONSTRAINT ck_optimization_chosen    CHECK (chosen_index IS NULL OR chosen_index >= 0);
ALTER TABLE rough_norms       ADD CONSTRAINT ck_rough_norms_confirm    CHECK (muc_xac_nhan IS NULL OR muc_xac_nhan IN ('nguon','tinh','kinh_nghiem'));
ALTER TABLE rough_norms       ADD CONSTRAINT ck_rough_norms_range      CHECK (qty_min IS NULL OR qty_max IS NULL OR qty_min <= qty_max);
ALTER TABLE project_files     ADD CONSTRAINT ck_project_files_type     CHECK (file_type IN ('dwg','dxf','pdf','xlsx','xls','docx','doc','csv','json','md'));
ALTER TABLE projects          ADD CONSTRAINT ck_projects_latlon        CHECK ((site_lat IS NULL OR site_lat BETWEEN -90 AND 90) AND (site_lon IS NULL OR site_lon BETWEEN -180 AND 180));
ALTER TABLE projects          ADD CONSTRAINT ck_projects_dims_positive CHECK (COALESCE(floor_height_mm,1) > 0 AND COALESCE(door_width_mm,1) > 0 AND COALESCE(door_height_mm,1) > 0
                                                                              AND COALESCE(window_width_mm,1) > 0 AND COALESCE(window_height_mm,1) > 0);

-- 0.3 Khóa ngoại thiếu: thêm NOT VALID rồi VALIDATE ngay (0 dòng vi phạm); lỗi thì cả giao dịch dừng
ALTER TABLE material_notes ADD CONSTRAINT fk_material_notes_material FOREIGN KEY (material_id) REFERENCES materials(material_id) NOT VALID;
ALTER TABLE material_notes VALIDATE CONSTRAINT fk_material_notes_material;

-- 0.4 Khóa ghép để các bảng mới kiểm được "cùng dự án / cùng lần bóc" (review điểm 1)
ALTER TABLE project_files     ADD CONSTRAINT uq_project_files_project UNIQUE (project_id, file_id);
ALTER TABLE wall_systems      ADD CONSTRAINT uq_wall_systems_material UNIQUE (wall_system_id, material_id);
ALTER TABLE optimization_runs ADD CONSTRAINT uq_optimization_takeoff  UNIQUE (run_id, takeoff_id);

-- 0.5 project_document_revisions: thêm project_id (suy từ project_files), khóa ghép, chỉ cho thêm
ALTER TABLE project_document_revisions ADD COLUMN project_id INTEGER;
UPDATE project_document_revisions r SET project_id = f.project_id FROM project_files f WHERE f.file_id = r.file_id;
ALTER TABLE project_document_revisions ALTER COLUMN project_id SET NOT NULL,
    ADD CONSTRAINT fk_document_file_project FOREIGN KEY (project_id, file_id) REFERENCES project_files(project_id, file_id) ON DELETE CASCADE,
    ADD CONSTRAINT uq_document_project_revision UNIQUE (project_id, revision_id);

CREATE OR REPLACE FUNCTION optimat_insert_only() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'Bảng % chỉ cho thêm dòng: không sửa dòng đã lưu (tạo phiên bản mới).', TG_TABLE_NAME
    USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_' || TG_TABLE_NAME || '_insert_only';
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_project_document_revisions_insert_only BEFORE UPDATE ON project_document_revisions
    FOR EACH ROW EXECUTE FUNCTION optimat_insert_only();
CREATE TRIGGER trg_project_profile_revisions_insert_only BEFORE UPDATE ON project_profile_revisions
    FOR EACH ROW EXECUTE FUNCTION optimat_insert_only();

-- 0.6 takeoff_results: cột mới + phân loại dòng cũ theo căn cứ có trong result, không theo mặc định
ALTER TABLE takeoff_results
    ADD COLUMN kind               VARCHAR(24),
    ADD COLUMN data_kind          VARCHAR(16),
    ADD COLUMN profile_version    INTEGER,
    ADD COLUMN params_snapshot    JSONB,
    ADD COLUMN engine_version     VARCHAR(32),
    ADD COLUMN request_sha256     CHAR(64),
    ADD COLUMN response_sha256    CHAR(64),
    ADD COLUMN client_analysis_id UUID,
    ADD COLUMN state              VARCHAR(12),
    ADD COLUMN superseded_by      INTEGER REFERENCES takeoff_results(takeoff_id) ON DELETE SET NULL;

-- quy tắc 1: kind lấy từ result.kind; kết quả xác nhận của trang kiểm tra (có walls_kept) là 'takeoff'
UPDATE takeoff_results SET kind = COALESCE(result->>'kind', CASE WHEN result ? 'walls_kept' THEN 'takeoff' END);
-- quy tắc 2: data_kind ghi sẵn trong result
UPDATE takeoff_results SET data_kind = result->>'data_kind' WHERE result->>'data_kind' IN ('ACTUAL','SAMPLE','SYNTHETIC');
-- quy tắc 3: đầu vào là bản vẽ mẫu tự tạo data/sample/sample_floor.dxf -> SAMPLE
UPDATE takeoff_results SET data_kind = 'SAMPLE'
 WHERE data_kind IS NULL AND (result->>'file' = 'sample_floor.dxf' OR result->'input'->>'file' = 'sample_floor.dxf');
-- quy tắc 4: so sánh dự toán theo loại dữ liệu của dự toán tham chiếu cùng dự án
UPDATE takeoff_results c SET data_kind = r.data_kind
  FROM takeoff_results r
 WHERE c.data_kind IS NULL AND c.kind = 'estimate_comparison'
   AND r.project_id = c.project_id AND r.kind = 'estimate_reference' AND r.data_kind IS NOT NULL;
-- quy tắc 5: trạng thái theo confirmed_at
UPDATE takeoff_results SET state = CASE WHEN confirmed_at IS NOT NULL THEN 'xac_nhan' ELSE 'tam' END,
                           params_snapshot = COALESCE(params_snapshot, '{}');

DO $$
DECLARE n int; ids text;
BEGIN
  SELECT count(*), string_agg(takeoff_id::text, ', ') INTO n, ids FROM takeoff_results WHERE kind IS NULL OR data_kind IS NULL;
  IF n > 0 THEN
    RAISE EXCEPTION 'Còn % dòng takeoff_results chưa phân loại được (takeoff_id: %). Bổ sung quy tắc có căn cứ rồi chạy lại.', n, ids;
  END IF;
END $$;

ALTER TABLE takeoff_results
    ALTER COLUMN kind SET NOT NULL,
    ALTER COLUMN data_kind SET NOT NULL,
    ALTER COLUMN state SET NOT NULL, ALTER COLUMN state SET DEFAULT 'tam',
    ALTER COLUMN params_snapshot SET NOT NULL, ALTER COLUMN params_snapshot SET DEFAULT '{}',
    ADD CONSTRAINT ck_takeoff_kind      CHECK (kind IN ('takeoff','rough','estimate_reference','estimate_comparison','synthetic_housing')),
    ADD CONSTRAINT ck_takeoff_data_kind CHECK (data_kind IN ('ACTUAL','SAMPLE','SYNTHETIC')),
    ADD CONSTRAINT ck_takeoff_synthetic CHECK (kind <> 'synthetic_housing' OR data_kind = 'SYNTHETIC'),
    ADD CONSTRAINT ck_takeoff_state     CHECK (state IN ('tam','xac_nhan','huy')),
    ADD CONSTRAINT ck_takeoff_confirmed CHECK (state <> 'xac_nhan' OR confirmed_at IS NOT NULL),
    ADD CONSTRAINT ck_takeoff_no_self   CHECK (superseded_by IS NULL OR superseded_by <> takeoff_id),
    ADD CONSTRAINT fk_takeoff_profile   FOREIGN KEY (project_id, profile_version)
        REFERENCES project_profile_revisions(project_id, version);
CREATE INDEX ix_takeoff_results_kind ON takeoff_results (project_id, kind, state);

-- Kiểm cuối: rỗng là đạt
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM project_document_revisions WHERE project_id IS NULL) THEN RAISE EXCEPTION 'revision thiếu project_id'; END IF;
  IF EXISTS (SELECT 1 FROM takeoff_results WHERE kind = 'synthetic_housing' AND data_kind <> 'SYNTHETIC') THEN RAISE EXCEPTION 'mô phỏng sai loại'; END IF;
END $$;
