-- =============================================================================
-- OptiMat AI · DDL ĐỀ XUẤT v2 (04/11/2026, sau review) — bảng mới cho chuỗi bóc tách
-- PostgreSQL 15+. Chạy SAU sql/01..05 hiện có và migration_dot0_20261104.sql.
-- Thay đổi so với v1 (theo review):
--  1. Khóa ghép: mọi bảng con mang khóa của phạm vi cha (dự án / lần nhận dạng / lần bóc / phương án),
--     nên không thể nối dữ liệu của hai công trình hay hai lần bóc.
--  2. Lịch sử bất biến bằng trigger: lần nhận dạng 'khoa', lần bóc 'xac_nhan', phương án 'khoa' thì
--     dữ liệu con không sửa/xóa được; số đo không sửa giá trị (sửa = ứng viên mới).
--  3. recognition_runs: định danh một lần nhận dạng (các phiên bản tệp, parser, băm bộ quy tắc, cấu hình).
--  4. Bảng nối thay mảng ID: recognition_run_inputs, evidence_entities, occurrence_entities.
--  5. Snapshot: đầu vào, định mức và giá thực dùng được chép lại giá trị (ID chỉ để tra).
--  6. CHECK sửa theo các ca review; FK ghép (wall_system_id, material_id).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- A. LẦN NHẬN DẠNG
-- ---------------------------------------------------------------------------
CREATE TABLE recognition_runs (
    recog_run_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    profile_version INTEGER NOT NULL,
    parser_version  VARCHAR(32) NOT NULL,
    rules_sha256    CHAR(64)    NOT NULL,
    config          JSONB       NOT NULL DEFAULT '{}',
    state           VARCHAR(8)  NOT NULL DEFAULT 'nhap',
    created_by      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_at       TIMESTAMPTZ,
    CONSTRAINT uq_recog_runs_project UNIQUE (project_id, recog_run_id),
    CONSTRAINT fk_recog_runs_profile FOREIGN KEY (project_id, profile_version) REFERENCES project_profile_revisions(project_id, version),
    CONSTRAINT ck_recog_runs_state  CHECK (state IN ('nhap','khoa','huy')),
    CONSTRAINT ck_recog_runs_locked CHECK ((state = 'khoa') = (locked_at IS NOT NULL) OR state = 'huy'),
    CONSTRAINT ck_recog_runs_config CHECK (jsonb_typeof(config) = 'object')
);

CREATE TABLE recognition_run_inputs (
    recog_run_id BIGINT  NOT NULL,
    project_id   INTEGER NOT NULL,
    revision_id  BIGINT  NOT NULL,
    PRIMARY KEY (recog_run_id, revision_id),
    CONSTRAINT fk_run_inputs_run      FOREIGN KEY (project_id, recog_run_id) REFERENCES recognition_runs(project_id, recog_run_id) ON DELETE CASCADE,
    CONSTRAINT fk_run_inputs_revision FOREIGN KEY (project_id, revision_id)  REFERENCES project_document_revisions(project_id, revision_id)
);

-- takeoff_results gắn với lần nhận dạng cùng dự án
ALTER TABLE takeoff_results
    ADD COLUMN recog_run_id BIGINT,
    ADD CONSTRAINT fk_takeoff_recog_run FOREIGN KEY (project_id, recog_run_id) REFERENCES recognition_runs(project_id, recog_run_id),
    ADD CONSTRAINT uq_takeoff_recog_run UNIQUE (recog_run_id, takeoff_id);

-- ---------------------------------------------------------------------------
-- B. BẢN VẼ VÀ BẰNG CHỨNG
-- ---------------------------------------------------------------------------
CREATE TABLE drawing_views (
    view_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id  BIGINT NOT NULL,
    revision_id   BIGINT NOT NULL,
    view_key      VARCHAR(64) NOT NULL,
    kind          VARCHAR(24) NOT NULL,
    sheet_type    VARCHAR(64),
    title_raw     TEXT,
    title         VARCHAR(255),
    bbox_wcs      JSONB NOT NULL,
    scale_display NUMERIC(10,3),
    scale_measure NUMERIC(12,6),
    scale_status  CHAR(1),
    scope         VARCHAR(16) NOT NULL DEFAULT 'chua_xac_nhan',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_views_run_input FOREIGN KEY (recog_run_id, revision_id) REFERENCES recognition_run_inputs(recog_run_id, revision_id) ON DELETE CASCADE,
    CONSTRAINT uq_views_key      UNIQUE (recog_run_id, revision_id, view_key),
    CONSTRAINT uq_views_run      UNIQUE (recog_run_id, view_id),
    CONSTRAINT uq_views_run_rev  UNIQUE (recog_run_id, view_id, revision_id),
    CONSTRAINT ck_views_kind  CHECK (kind IN ('mat_bang','mat_cat','mat_dung','chi_tiet','bang_thong_ke','toan_bo','khac')),
    CONSTRAINT ck_views_scope CHECK (scope IN ('tinh','tham_khao','ban_sao','chua_xac_nhan')),
    CONSTRAINT ck_views_scale_status CHECK (scale_status IS NULL OR scale_status IN ('A','B','C','D')),
    CONSTRAINT ck_views_scale CHECK ((scale_display IS NULL OR scale_display > 0) AND (scale_measure IS NULL OR scale_measure > 0)),
    CONSTRAINT ck_views_bbox  CHECK (jsonb_typeof(bbox_wcs) = 'array' AND jsonb_array_length(bbox_wcs) = 4)
);

-- Đối tượng CAD thuộc nội dung tệp (bất biến), dùng chung cho mọi lần nhận dạng của cùng phiên bản
CREATE TABLE drawing_entities (
    entity_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    revision_id BIGINT NOT NULL REFERENCES project_document_revisions(revision_id) ON DELETE CASCADE,
    handle      VARCHAR(255) NOT NULL,
    block_path  TEXT,
    dxftype     VARCHAR(24)  NOT NULL,
    layer       VARCHAR(255) NOT NULL,
    geom_wcs    JSONB,
    text_raw    TEXT,
    text_norm   TEXT,
    attribs     JSONB NOT NULL DEFAULT '{}',
    CONSTRAINT uq_entities_handle UNIQUE (revision_id, handle),
    CONSTRAINT uq_entities_rev    UNIQUE (revision_id, entity_id),
    CONSTRAINT ck_entities_text CHECK (dxftype NOT IN ('TEXT','MTEXT','ATTRIB') OR text_raw IS NOT NULL)
);

CREATE TABLE evidence_sources (
    evidence_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id BIGINT NOT NULL,
    kind         VARCHAR(24) NOT NULL,
    revision_id  BIGINT,
    view_id      BIGINT,
    raw_content  TEXT  NOT NULL,
    interpreted  JSONB NOT NULL,
    rule_code    VARCHAR(64),
    page_ref     VARCHAR(128),
    user_id      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_evidence_run      FOREIGN KEY (recog_run_id) REFERENCES recognition_runs(recog_run_id) ON DELETE CASCADE,
    CONSTRAINT fk_evidence_revision FOREIGN KEY (recog_run_id, revision_id) REFERENCES recognition_run_inputs(recog_run_id, revision_id),
    CONSTRAINT fk_evidence_view     FOREIGN KEY (recog_run_id, view_id, revision_id) REFERENCES drawing_views(recog_run_id, view_id, revision_id),
    CONSTRAINT uq_evidence_run      UNIQUE (recog_run_id, evidence_id),
    CONSTRAINT uq_evidence_run_rev  UNIQUE (recog_run_id, evidence_id, revision_id),
    CONSTRAINT ck_evidence_kind CHECK (kind IN ('chu','kich_thuoc','bang_thong_ke','vung_ban_ve','hatch','block','tai_lieu','nguoi_nhap','thong_so_du_an','dinh_muc')),
    CONSTRAINT ck_evidence_drawing_has_revision CHECK (kind NOT IN ('chu','kich_thuoc','bang_thong_ke','vung_ban_ve','hatch','block') OR revision_id IS NOT NULL),
    CONSTRAINT ck_evidence_view_needs_revision CHECK (view_id IS NULL OR revision_id IS NOT NULL),
    CONSTRAINT ck_evidence_user_input CHECK (kind <> 'nguoi_nhap' OR user_id IS NOT NULL),
    CONSTRAINT ck_evidence_interpreted_object CHECK (jsonb_typeof(interpreted) = 'object')
);

CREATE TABLE evidence_entities (
    recog_run_id BIGINT NOT NULL,
    evidence_id  BIGINT NOT NULL,
    revision_id  BIGINT NOT NULL,
    entity_id    BIGINT NOT NULL,
    PRIMARY KEY (evidence_id, entity_id),
    CONSTRAINT fk_evidence_entities_evidence FOREIGN KEY (recog_run_id, evidence_id, revision_id) REFERENCES evidence_sources(recog_run_id, evidence_id, revision_id) ON DELETE CASCADE,
    CONSTRAINT fk_evidence_entities_entity   FOREIGN KEY (revision_id, entity_id) REFERENCES drawing_entities(revision_id, entity_id)
);

CREATE TABLE building_levels (
    level_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id       BIGINT NOT NULL REFERENCES recognition_runs(recog_run_id) ON DELETE CASCADE,
    code               VARCHAR(32)  NOT NULL,
    name               VARCHAR(128) NOT NULL,
    seq                SMALLINT     NOT NULL,
    elevation_mm       NUMERIC(10,1),
    height_mm          NUMERIC(10,1),
    height_status      CHAR(1) NOT NULL,
    height_evidence_id BIGINT,
    CONSTRAINT uq_levels_run_code UNIQUE (recog_run_id, code),
    CONSTRAINT uq_levels_run      UNIQUE (recog_run_id, level_id),
    CONSTRAINT fk_levels_evidence FOREIGN KEY (recog_run_id, height_evidence_id) REFERENCES evidence_sources(recog_run_id, evidence_id),
    CONSTRAINT ck_levels_seq    CHECK (seq BETWEEN 0 AND 10),
    CONSTRAINT ck_levels_height CHECK (height_mm IS NULL OR (height_mm > 0 AND height_mm <= 10000)),
    CONSTRAINT ck_levels_status CHECK (height_status IN ('A','B','C','D')),
    CONSTRAINT ck_levels_missing_is_d CHECK ((height_mm IS NULL) = (height_status = 'D'))
);

CREATE TABLE view_levels (
    recog_run_id BIGINT NOT NULL,
    view_id      BIGINT NOT NULL,
    level_id     BIGINT NOT NULL,
    PRIMARY KEY (view_id, level_id),
    CONSTRAINT fk_view_levels_view  FOREIGN KEY (recog_run_id, view_id)  REFERENCES drawing_views(recog_run_id, view_id) ON DELETE CASCADE,
    CONSTRAINT fk_view_levels_level FOREIGN KEY (recog_run_id, level_id) REFERENCES building_levels(recog_run_id, level_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- C. CẤU KIỆN VÀ SỐ ĐO (theo lần nhận dạng: đọc lại = lần mới, mã W5 không đè nhau)
-- ---------------------------------------------------------------------------
CREATE TABLE building_elements (
    element_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id         BIGINT NOT NULL REFERENCES recognition_runs(recog_run_id) ON DELETE CASCADE,
    level_id             BIGINT,
    code                 VARCHAR(32) NOT NULL,
    kind                 VARCHAR(24) NOT NULL,
    subtype              VARCHAR(32),
    geom_norm            JSONB,
    design_material_text TEXT,
    recog_status         VARCHAR(16) NOT NULL DEFAULT 'tu_dong',
    recog_confidence     NUMERIC(4,3),
    removed_reason       TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_elements_level FOREIGN KEY (recog_run_id, level_id) REFERENCES building_levels(recog_run_id, level_id),
    CONSTRAINT uq_elements_code  UNIQUE NULLS NOT DISTINCT (recog_run_id, level_id, kind, code),
    CONSTRAINT uq_elements_run   UNIQUE (recog_run_id, element_id),
    CONSTRAINT ck_elements_kind   CHECK (kind IN ('tuong','cot','dam','san','mong','giang','lanh_to','thang','mai','lo_mo','nen','khac')),
    CONSTRAINT ck_elements_status CHECK (recog_status IN ('tu_dong','nguoi_sua','nguoi_them','da_loai')),
    CONSTRAINT ck_elements_conf   CHECK (recog_confidence IS NULL OR recog_confidence BETWEEN 0 AND 1),
    CONSTRAINT ck_elements_removed_reason CHECK (recog_status <> 'da_loai' OR removed_reason IS NOT NULL)
);
CREATE INDEX ix_elements_kind ON building_elements (recog_run_id, kind);

CREATE TABLE element_occurrences (
    occurrence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id  BIGINT NOT NULL,
    element_id    BIGINT NOT NULL,
    view_id       BIGINT NOT NULL,
    revision_id   BIGINT NOT NULL,
    role          VARCHAR(16) NOT NULL,
    local_geom    JSONB,
    CONSTRAINT fk_occ_element FOREIGN KEY (recog_run_id, element_id) REFERENCES building_elements(recog_run_id, element_id) ON DELETE CASCADE,
    CONSTRAINT fk_occ_view    FOREIGN KEY (recog_run_id, view_id, revision_id) REFERENCES drawing_views(recog_run_id, view_id, revision_id) ON DELETE CASCADE,
    CONSTRAINT uq_occ         UNIQUE (element_id, view_id, role),
    CONSTRAINT uq_occ_run_rev UNIQUE (recog_run_id, occurrence_id, revision_id),
    CONSTRAINT ck_occ_role CHECK (role IN ('hinh_chinh','mat_cat','chi_tiet','bang_thong_ke','ky_hieu'))
);

CREATE TABLE occurrence_entities (
    recog_run_id  BIGINT NOT NULL,
    occurrence_id BIGINT NOT NULL,
    revision_id   BIGINT NOT NULL,
    entity_id     BIGINT NOT NULL,
    PRIMARY KEY (occurrence_id, entity_id),
    CONSTRAINT fk_occ_entities_occ    FOREIGN KEY (recog_run_id, occurrence_id, revision_id) REFERENCES element_occurrences(recog_run_id, occurrence_id, revision_id) ON DELETE CASCADE,
    CONSTRAINT fk_occ_entities_entity FOREIGN KEY (revision_id, entity_id) REFERENCES drawing_entities(revision_id, entity_id)
);

CREATE TABLE element_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id   BIGINT NOT NULL,
    element_id     BIGINT NOT NULL,
    quantity_kind  VARCHAR(24) NOT NULL,
    variant        VARCHAR(32) NOT NULL DEFAULT '',
    value          NUMERIC(14,4),
    unit           VARCHAR(8)  NOT NULL,
    method         VARCHAR(24) NOT NULL,
    status         CHAR(1)     NOT NULL,
    selected       BOOLEAN     NOT NULL DEFAULT FALSE,
    supersedes_id  BIGINT,
    note           TEXT,
    created_by     INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_meas_element    FOREIGN KEY (recog_run_id, element_id) REFERENCES building_elements(recog_run_id, element_id) ON DELETE CASCADE,
    CONSTRAINT fk_meas_supersedes FOREIGN KEY (recog_run_id, supersedes_id) REFERENCES element_measurements(recog_run_id, measurement_id),
    CONSTRAINT uq_meas_run UNIQUE (recog_run_id, measurement_id),
    CONSTRAINT ck_meas_kind CHECK (quantity_kind IN ('dai','rong','cao','day','tiet_dien_b','tiet_dien_h','dien_tich','the_tich','so_luong','cao_do','ham_luong_thep','duong_kinh')),
    CONSTRAINT ck_meas_unit CHECK (
        (quantity_kind IN ('dai','rong','cao','day','tiet_dien_b','tiet_dien_h','cao_do','duong_kinh') AND unit = 'mm')
     OR (quantity_kind = 'dien_tich' AND unit = 'm2')
     OR (quantity_kind = 'the_tich'  AND unit = 'm3')
     OR (quantity_kind = 'so_luong'  AND unit = 'cai')
     OR (quantity_kind = 'ham_luong_thep' AND unit = 'kg_m3')),
    CONSTRAINT ck_meas_method CHECK (method IN ('hinh_hoc','dimension','ghi_chu','bang_thong_ke','mat_cat','quy_tac','nguoi_nhap','thong_so_du_an','suy_luan')),
    CONSTRAINT ck_meas_status CHECK (status IN ('A','B','C','D')),
    CONSTRAINT ck_meas_missing_is_d CHECK ((value IS NULL) = (status = 'D')),
    CONSTRAINT ck_meas_selected_has_value CHECK (NOT selected OR value IS NOT NULL),
    CONSTRAINT ck_meas_positive CHECK (value IS NULL OR quantity_kind = 'cao_do' OR value >= 0),
    CONSTRAINT ck_meas_user_is_c CHECK (method <> 'nguoi_nhap' OR status IN ('C','D')),
    CONSTRAINT ck_meas_no_self CHECK (supersedes_id IS NULL OR supersedes_id <> measurement_id)
);
CREATE UNIQUE INDEX uq_meas_one_selected ON element_measurements (element_id, quantity_kind, variant) WHERE selected;

CREATE TABLE measurement_evidence (
    recog_run_id   BIGINT NOT NULL,
    measurement_id BIGINT NOT NULL,
    evidence_id    BIGINT NOT NULL,
    role           VARCHAR(16) NOT NULL DEFAULT 'chinh',
    PRIMARY KEY (measurement_id, evidence_id),
    CONSTRAINT fk_meas_ev_meas     FOREIGN KEY (recog_run_id, measurement_id) REFERENCES element_measurements(recog_run_id, measurement_id) ON DELETE CASCADE,
    CONSTRAINT fk_meas_ev_evidence FOREIGN KEY (recog_run_id, evidence_id)    REFERENCES evidence_sources(recog_run_id, evidence_id) ON DELETE CASCADE,
    CONSTRAINT ck_meas_evidence_role CHECK (role IN ('chinh','doi_chieu','mau_thuan'))
);

CREATE TABLE element_relations (
    relation_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id    BIGINT NOT NULL,
    from_element_id BIGINT NOT NULL,
    to_element_id   BIGINT NOT NULL,
    kind            VARCHAR(24) NOT NULL,
    status          CHAR(1) NOT NULL,
    evidence_id     BIGINT,
    CONSTRAINT fk_rel_from     FOREIGN KEY (recog_run_id, from_element_id) REFERENCES building_elements(recog_run_id, element_id) ON DELETE CASCADE,
    CONSTRAINT fk_rel_to       FOREIGN KEY (recog_run_id, to_element_id)   REFERENCES building_elements(recog_run_id, element_id) ON DELETE CASCADE,
    CONSTRAINT fk_rel_evidence FOREIGN KEY (recog_run_id, evidence_id)     REFERENCES evidence_sources(recog_run_id, evidence_id),
    CONSTRAINT uq_rel UNIQUE (from_element_id, to_element_id, kind),
    CONSTRAINT ck_rel_kind   CHECK (kind IN ('thuoc_tuong','goi_len','noi_voi','cung_chi_tiet','trung_voi','nam_trong')),
    CONSTRAINT ck_rel_status CHECK (status IN ('A','B','C','D')),
    CONSTRAINT ck_rel_no_self CHECK (from_element_id <> to_element_id)
);

CREATE TABLE review_issues (
    issue_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recog_run_id   BIGINT NOT NULL REFERENCES recognition_runs(recog_run_id) ON DELETE CASCADE,
    takeoff_id     INTEGER,
    kind           VARCHAR(24) NOT NULL,
    severity       VARCHAR(8)  NOT NULL,
    element_id     BIGINT,
    measurement_id BIGINT,
    view_id        BIGINT,
    message        TEXT NOT NULL,
    check_code     VARCHAR(32),
    state          VARCHAR(12) NOT NULL DEFAULT 'mo',
    resolution     TEXT,
    resolved_by    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    resolved_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_issue_takeoff FOREIGN KEY (recog_run_id, takeoff_id)     REFERENCES takeoff_results(recog_run_id, takeoff_id),
    CONSTRAINT fk_issue_element FOREIGN KEY (recog_run_id, element_id)     REFERENCES building_elements(recog_run_id, element_id),
    CONSTRAINT fk_issue_meas    FOREIGN KEY (recog_run_id, measurement_id) REFERENCES element_measurements(recog_run_id, measurement_id),
    CONSTRAINT fk_issue_view    FOREIGN KEY (recog_run_id, view_id)        REFERENCES drawing_views(recog_run_id, view_id),
    CONSTRAINT ck_issues_kind     CHECK (kind IN ('thieu_so','mau_thuan','nghi_trung','chua_ro','ngoai_khoang','thieu_ban_ve')),
    CONSTRAINT ck_issues_severity CHECK (severity IN ('chan','canh_bao','ghi_chu')),
    CONSTRAINT ck_issues_state    CHECK (state IN ('mo','da_xu_ly','chap_nhan','bo_qua')),
    CONSTRAINT ck_issues_resolved CHECK ((state = 'mo') = (resolution IS NULL AND resolved_at IS NULL))
);
CREATE INDEX ix_review_issues_open ON review_issues (recog_run_id, state);

-- ---------------------------------------------------------------------------
-- D. KHỐI LƯỢNG
-- ---------------------------------------------------------------------------
CREATE TABLE takeoff_items (
    item_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    takeoff_id     INTEGER NOT NULL,
    recog_run_id   BIGINT  NOT NULL,
    seq            INTEGER NOT NULL,
    work_code      VARCHAR(32) NOT NULL,
    level_id       BIGINT,
    element_id     BIGINT,
    element_label  VARCHAR(255),
    variant        VARCHAR(64),
    unit           VARCHAR(8) NOT NULL,
    is_deduction   BOOLEAN NOT NULL DEFAULT FALSE,
    quantity       NUMERIC(14,4),
    quantity_known NUMERIC(14,4),
    formula        TEXT NOT NULL DEFAULT '',
    basis          VARCHAR(24),
    wall_system_id VARCHAR(64) REFERENCES wall_systems(wall_system_id) ON DELETE RESTRICT,
    stage          VARCHAR(16),
    status         CHAR(1) NOT NULL,
    missing        TEXT[] NOT NULL DEFAULT '{}',
    source         VARCHAR(8) NOT NULL DEFAULT 'auto',
    CONSTRAINT fk_items_takeoff FOREIGN KEY (recog_run_id, takeoff_id) REFERENCES takeoff_results(recog_run_id, takeoff_id) ON DELETE CASCADE,
    CONSTRAINT fk_items_level   FOREIGN KEY (recog_run_id, level_id)   REFERENCES building_levels(recog_run_id, level_id),
    CONSTRAINT fk_items_element FOREIGN KEY (recog_run_id, element_id) REFERENCES building_elements(recog_run_id, element_id),
    CONSTRAINT uq_items_seq      UNIQUE (takeoff_id, seq),
    CONSTRAINT uq_items_takeoff  UNIQUE (takeoff_id, item_id),
    CONSTRAINT uq_items_run      UNIQUE (item_id, recog_run_id),
    CONSTRAINT ck_items_status  CHECK (status IN ('A','B','C','D')),
    CONSTRAINT ck_items_source  CHECK (source IN ('auto','manual')),
    CONSTRAINT ck_items_basis   CHECK (basis IS NULL OR basis IN ('bang_thong_ke','ham_luong','not_supported')),
    CONSTRAINT ck_items_missing_is_d  CHECK (quantity IS NOT NULL OR status = 'D'),
    CONSTRAINT ck_items_d_has_reason  CHECK (status <> 'D' OR cardinality(missing) > 0),
    -- khấu trừ mang dấu âm, công tác thường dấu dương; phần đã biết cùng dấu và không vượt độ lớn tổng
    CONSTRAINT ck_items_sign  CHECK (quantity IS NULL OR (is_deduction AND quantity <= 0) OR (NOT is_deduction AND quantity >= 0)),
    CONSTRAINT ck_items_known CHECK (quantity_known IS NULL OR quantity IS NULL
                                     OR (sign(quantity_known) * sign(quantity) >= 0 AND abs(quantity_known) <= abs(quantity))),
    CONSTRAINT ck_items_known_sign CHECK (quantity_known IS NULL OR (is_deduction AND quantity_known <= 0) OR (NOT is_deduction AND quantity_known >= 0))
);
CREATE INDEX ix_items_work ON takeoff_items (takeoff_id, work_code);

CREATE TABLE takeoff_item_inputs (
    item_id         BIGINT NOT NULL,
    recog_run_id    BIGINT NOT NULL,
    seq             SMALLINT NOT NULL,
    input_kind      VARCHAR(20) NOT NULL,
    measurement_id  BIGINT,
    rough_norm_id   INTEGER REFERENCES rough_norms(id) ON DELETE SET NULL,
    label           VARCHAR(128) NOT NULL,
    value_snapshot  NUMERIC(14,6),
    unit            VARCHAR(16),
    status          CHAR(1) NOT NULL,
    norm_code       VARCHAR(64),
    confirmation    VARCHAR(16),
    source_snapshot TEXT,
    PRIMARY KEY (item_id, seq),
    CONSTRAINT fk_inputs_item FOREIGN KEY (item_id, recog_run_id) REFERENCES takeoff_items(item_id, recog_run_id) ON DELETE CASCADE,
    CONSTRAINT fk_inputs_meas FOREIGN KEY (recog_run_id, measurement_id) REFERENCES element_measurements(recog_run_id, measurement_id),
    CONSTRAINT ck_inputs_kind   CHECK (input_kind IN ('so_do','thong_so','dinh_muc','ket_qua_trung_gian')),
    CONSTRAINT ck_inputs_status CHECK (status IN ('A','B','C','D')),
    CONSTRAINT ck_inputs_missing_is_d CHECK ((value_snapshot IS NULL) = (status = 'D')),
    CONSTRAINT ck_inputs_unit_with_value CHECK (value_snapshot IS NULL OR unit IS NOT NULL),
    CONSTRAINT ck_inputs_norm_snapshot CHECK (input_kind <> 'dinh_muc' OR value_snapshot IS NULL OR source_snapshot IS NOT NULL),
    CONSTRAINT ck_inputs_confirm CHECK (confirmation IS NULL OR confirmation IN ('nguon','tinh','kinh_nghiem'))
);

-- ---------------------------------------------------------------------------
-- E. PHƯƠNG ÁN VẬT LIỆU (cùng hình học và quy tắc đo; đổi chiều dày tường = lần bóc mới)
-- ---------------------------------------------------------------------------
CREATE TABLE material_scenarios (
    scenario_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    takeoff_id  INTEGER NOT NULL REFERENCES takeoff_results(takeoff_id) ON DELETE CASCADE,
    name        VARCHAR(128) NOT NULL,
    origin      VARCHAR(16)  NOT NULL,
    run_id      INTEGER,
    state       VARCHAR(8) NOT NULL DEFAULT 'nhap',
    is_selected BOOLEAN NOT NULL DEFAULT FALSE,
    price_basis_date DATE,
    created_by  INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_scen_opt_run   FOREIGN KEY (run_id, takeoff_id) REFERENCES optimization_runs(run_id, takeoff_id),
    CONSTRAINT uq_scen_takeoff   UNIQUE (takeoff_id, scenario_id),
    CONSTRAINT ck_scen_origin CHECK (origin IN ('thiet_ke','nguoi_dung','de_xuat_ai','toi_uu')),
    CONSTRAINT ck_scen_run    CHECK (origin <> 'toi_uu' OR run_id IS NOT NULL),
    CONSTRAINT ck_scen_state  CHECK (state IN ('nhap','khoa')),
    CONSTRAINT ck_scen_selected_locked CHECK (NOT is_selected OR state = 'khoa')
);
CREATE UNIQUE INDEX uq_scen_one_selected ON material_scenarios (takeoff_id) WHERE is_selected;

CREATE TABLE material_assignments (
    assignment_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id    BIGINT  NOT NULL,
    takeoff_id     INTEGER NOT NULL,
    recog_run_id   BIGINT  NOT NULL,
    item_id        BIGINT,
    element_id     BIGINT,
    material_id    VARCHAR(64) REFERENCES materials(material_id) ON DELETE RESTRICT,
    wall_system_id VARCHAR(64) REFERENCES wall_systems(wall_system_id) ON DELETE RESTRICT,
    source         VARCHAR(16) NOT NULL,
    evidence_id    BIGINT,
    status         CHAR(1) NOT NULL,
    CONSTRAINT fk_assign_scenario FOREIGN KEY (takeoff_id, scenario_id) REFERENCES material_scenarios(takeoff_id, scenario_id) ON DELETE CASCADE,
    CONSTRAINT fk_assign_takeoff  FOREIGN KEY (recog_run_id, takeoff_id) REFERENCES takeoff_results(recog_run_id, takeoff_id),
    CONSTRAINT fk_assign_item     FOREIGN KEY (takeoff_id, item_id)     REFERENCES takeoff_items(takeoff_id, item_id) ON DELETE CASCADE,
    CONSTRAINT fk_assign_element  FOREIGN KEY (recog_run_id, element_id) REFERENCES building_elements(recog_run_id, element_id),
    CONSTRAINT fk_assign_evidence FOREIGN KEY (recog_run_id, evidence_id) REFERENCES evidence_sources(recog_run_id, evidence_id),
    CONSTRAINT fk_assign_wall_material FOREIGN KEY (wall_system_id, material_id) REFERENCES wall_systems(wall_system_id, material_id),
    CONSTRAINT uq_assign UNIQUE NULLS NOT DISTINCT (scenario_id, item_id, element_id),
    CONSTRAINT ck_assign_target CHECK (item_id IS NOT NULL OR element_id IS NOT NULL),
    CONSTRAINT ck_assign_source CHECK (source IN ('thiet_ke','nguoi_dung','de_xuat_ai','toi_uu')),
    CONSTRAINT ck_assign_status CHECK (status IN ('A','B','C','D')),
    CONSTRAINT ck_assign_empty_is_d CHECK ((material_id IS NULL AND wall_system_id IS NULL) = (status = 'D')),
    CONSTRAINT ck_assign_ai_has_evidence CHECK (source <> 'de_xuat_ai' OR evidence_id IS NOT NULL)
);

CREATE TABLE material_requirements (
    requirement_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id         BIGINT  NOT NULL,
    takeoff_id          INTEGER NOT NULL,
    material_id         VARCHAR(64) REFERENCES materials(material_id) ON DELETE RESTRICT,
    name                VARCHAR(255) NOT NULL,
    unit                VARCHAR(16)  NOT NULL,
    quantity            NUMERIC(14,4),
    complete            BOOLEAN NOT NULL,
    waste_pct           NUMERIC(6,3),
    waste_source        VARCHAR(255),
    quantity_with_waste NUMERIC(14,4),
    quantity_min        NUMERIC(14,4),
    quantity_max        NUMERIC(14,4),
    confirmation        VARCHAR(16),
    status              CHAR(1) NOT NULL,
    missing             TEXT[] NOT NULL DEFAULT '{}',
    group_id            VARCHAR(64),
    raw_class           VARCHAR(32),
    unit_weight_kg      NUMERIC(12,4),
    weight_kg           NUMERIC(14,3),
    CONSTRAINT fk_req_scenario FOREIGN KEY (takeoff_id, scenario_id) REFERENCES material_scenarios(takeoff_id, scenario_id) ON DELETE CASCADE,
    CONSTRAINT uq_req_takeoff  UNIQUE (requirement_id, takeoff_id),
    CONSTRAINT ck_req_status  CHECK (status IN ('A','B','C','D')),
    CONSTRAINT ck_req_confirm CHECK (confirmation IS NULL OR confirmation IN ('nguon','tinh','kinh_nghiem')),
    CONSTRAINT ck_req_waste   CHECK (waste_pct IS NULL OR (waste_pct >= 0 AND waste_pct < 100)),
    CONSTRAINT ck_req_waste_snapshot CHECK ((quantity_with_waste IS NULL) OR (waste_pct IS NOT NULL AND waste_source IS NOT NULL AND quantity IS NOT NULL)),
    CONSTRAINT ck_req_range   CHECK (quantity_min IS NULL OR quantity_max IS NULL OR quantity_min <= quantity_max),
    -- đủ = có số và không D; thiếu = D (có thể có phần đã tính)
    CONSTRAINT ck_req_complete CHECK ((complete AND quantity IS NOT NULL AND status <> 'D') OR (NOT complete AND status = 'D')),
    CONSTRAINT ck_req_d_has_reason CHECK (status <> 'D' OR cardinality(missing) > 0),
    CONSTRAINT ck_req_weight CHECK (weight_kg IS NULL OR unit_weight_kg IS NOT NULL)
);
CREATE INDEX ix_req_scenario ON material_requirements (scenario_id, material_id);

CREATE TABLE requirement_sources (
    requirement_id  BIGINT  NOT NULL,
    takeoff_id      INTEGER NOT NULL,
    item_id         BIGINT  NOT NULL,
    rough_norm_id   INTEGER REFERENCES rough_norms(id) ON DELETE SET NULL,
    wall_system_id  VARCHAR(64) REFERENCES wall_systems(wall_system_id) ON DELETE RESTRICT,
    norm_qty        NUMERIC(14,6),
    norm_unit       VARCHAR(64),
    norm_code       VARCHAR(64),
    norm_source     TEXT,
    confirmation    VARCHAR(16),
    quantity_part   NUMERIC(14,4),
    PRIMARY KEY (requirement_id, item_id),
    CONSTRAINT fk_reqsrc_req  FOREIGN KEY (requirement_id, takeoff_id) REFERENCES material_requirements(requirement_id, takeoff_id) ON DELETE CASCADE,
    CONSTRAINT fk_reqsrc_item FOREIGN KEY (takeoff_id, item_id)        REFERENCES takeoff_items(takeoff_id, item_id) ON DELETE CASCADE,
    CONSTRAINT ck_reqsrc_norm_snapshot CHECK (norm_qty IS NULL OR (norm_unit IS NOT NULL AND norm_source IS NOT NULL)),
    CONSTRAINT ck_reqsrc_part_needs_norm CHECK (quantity_part IS NULL OR norm_qty IS NOT NULL),
    CONSTRAINT ck_reqsrc_confirm CHECK (confirmation IS NULL OR confirmation IN ('nguon','tinh','kinh_nghiem'))
);

-- Giá thực dùng cho phương án: chép lại giá trị, đơn vị, cơ sở VAT/vận chuyển, quy đổi và nguồn
CREATE TABLE scenario_price_lines (
    price_line_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id          BIGINT  NOT NULL,
    takeoff_id           INTEGER NOT NULL,
    material_id          VARCHAR(64) NOT NULL REFERENCES materials(material_id) ON DELETE RESTRICT,
    supplier_id          VARCHAR(64) REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    price_record_id      BIGINT  REFERENCES price_records(id) ON DELETE SET NULL,
    supplier_material_id INTEGER REFERENCES supplier_materials(id) ON DELETE SET NULL,
    price_level          VARCHAR(16) NOT NULL,
    data_kind            VARCHAR(16) NOT NULL,
    unit_price           NUMERIC(14,2) NOT NULL,
    price_unit           VARCHAR(32)  NOT NULL,
    unit_conversion      NUMERIC(14,6) NOT NULL DEFAULT 1,
    vat_included         VARCHAR(8) NOT NULL,
    transport_included   VARCHAR(8) NOT NULL,
    price_date           DATE NOT NULL,
    province             VARCHAR(64),
    source               TEXT NOT NULL,
    is_predicted         BOOLEAN NOT NULL DEFAULT FALSE,
    model_version        VARCHAR(32) REFERENCES model_versions(version) ON DELETE SET NULL,
    CONSTRAINT fk_price_scenario FOREIGN KEY (takeoff_id, scenario_id) REFERENCES material_scenarios(takeoff_id, scenario_id) ON DELETE CASCADE,
    CONSTRAINT uq_price_line UNIQUE NULLS NOT DISTINCT (scenario_id, material_id, supplier_id),
    CONSTRAINT ck_price_level CHECK (price_level IN ('DEALER','QUOTE','BULLETIN','PREDICTED')),
    CONSTRAINT ck_price_data_kind CHECK (data_kind IN ('ACTUAL','SAMPLE','SYNTHETIC')),
    CONSTRAINT ck_price_positive CHECK (unit_price > 0 AND unit_conversion > 0),
    CONSTRAINT ck_price_basis CHECK (vat_included IN ('YES','NO','UNKNOWN') AND transport_included IN ('YES','NO','UNKNOWN')),
    -- giá dự đoán không bao giờ đóng vai giá thật
    CONSTRAINT ck_price_predicted CHECK (is_predicted = (price_level = 'PREDICTED') AND (NOT is_predicted OR model_version IS NOT NULL)),
    CONSTRAINT ck_price_has_origin CHECK (is_predicted OR price_record_id IS NOT NULL OR supplier_material_id IS NOT NULL)
);

-- ---------------------------------------------------------------------------
-- F. TRIGGER KHÓA LỊCH SỬ
-- ---------------------------------------------------------------------------
-- F1. Trạng thái chỉ đi một chiều
CREATE OR REPLACE FUNCTION optimat_run_state_guard() RETURNS trigger AS $$
BEGIN
  IF OLD.state <> 'nhap' THEN
    RAISE EXCEPTION 'Lần nhận dạng % đã %: không sửa được, tạo lần nhận dạng mới.', OLD.recog_run_id, OLD.state
      USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_recog_run_locked';
  END IF;
  IF NEW.project_id <> OLD.project_id OR NEW.profile_version <> OLD.profile_version OR NEW.parser_version <> OLD.parser_version
     OR NEW.rules_sha256 <> OLD.rules_sha256 OR NEW.config <> OLD.config THEN
    RAISE EXCEPTION 'Không đổi đầu vào của lần nhận dạng; tạo lần mới.' USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_recog_run_inputs_fixed';
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_recog_run_state BEFORE UPDATE ON recognition_runs FOR EACH ROW EXECUTE FUNCTION optimat_run_state_guard();

-- F2. Dữ liệu thuộc lần nhận dạng chỉ ghi khi lần đó còn 'nhap'
CREATE OR REPLACE FUNCTION optimat_run_scope_guard() RETURNS trigger AS $$
DECLARE rid bigint; st text;
BEGIN
  rid := CASE WHEN TG_OP = 'DELETE' THEN OLD.recog_run_id ELSE NEW.recog_run_id END;
  SELECT state INTO st FROM recognition_runs WHERE recog_run_id = rid;
  IF st IS NOT NULL AND st <> 'nhap' THEN
    RAISE EXCEPTION 'Lần nhận dạng % đã %: không % vào %.', rid, st, lower(TG_OP), TG_TABLE_NAME
      USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_recog_run_locked';
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$ LANGUAGE plpgsql;
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['recognition_run_inputs','drawing_views','evidence_sources','evidence_entities','building_levels','view_levels',
                           'building_elements','element_occurrences','occurrence_entities','element_measurements','measurement_evidence','element_relations']
  LOOP
    EXECUTE format('CREATE TRIGGER trg_%s_run_scope BEFORE INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION optimat_run_scope_guard()', t, t);
  END LOOP;
END $$;

-- F3. Đối tượng CAD và số đo: giá trị đã lưu không sửa (sửa số đo = thêm ứng viên, supersedes_id)
CREATE TRIGGER trg_drawing_entities_insert_only BEFORE UPDATE ON drawing_entities FOR EACH ROW EXECUTE FUNCTION optimat_insert_only();
CREATE TRIGGER trg_evidence_sources_insert_only BEFORE UPDATE ON evidence_sources FOR EACH ROW EXECUTE FUNCTION optimat_insert_only();
CREATE OR REPLACE FUNCTION optimat_measurement_guard() RETURNS trigger AS $$
BEGIN
  IF (NEW.element_id, NEW.quantity_kind, NEW.variant, NEW.value, NEW.unit, NEW.method, NEW.status, NEW.supersedes_id)
     IS DISTINCT FROM (OLD.element_id, OLD.quantity_kind, OLD.variant, OLD.value, OLD.unit, OLD.method, OLD.status, OLD.supersedes_id) THEN
    RAISE EXCEPTION 'Số đo % không sửa giá trị; thêm ứng viên mới với supersedes_id.', OLD.measurement_id
      USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_measurement_value_fixed';
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_measurement_value_fixed BEFORE UPDATE ON element_measurements FOR EACH ROW EXECUTE FUNCTION optimat_measurement_guard();

-- F4. Lần bóc: tam -> xac_nhan|huy, xac_nhan -> huy; xác nhận cần lần nhận dạng đã khóa; sau xác nhận không sửa nội dung
CREATE OR REPLACE FUNCTION optimat_takeoff_guard() RETURNS trigger AS $$
DECLARE st text;
BEGIN
  IF TG_OP = 'UPDATE' AND OLD.state IN ('xac_nhan','huy') THEN
    IF OLD.state = 'huy' OR NEW.state <> 'huy'
       OR (NEW.result, NEW.params_snapshot, NEW.recog_run_id, NEW.profile_version, NEW.confirmed_at)
          IS DISTINCT FROM (OLD.result, OLD.params_snapshot, OLD.recog_run_id, OLD.profile_version, OLD.confirmed_at) THEN
      RAISE EXCEPTION 'Lần bóc % đã %: chỉ được chuyển sang huy.', OLD.takeoff_id, OLD.state
        USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_takeoff_locked';
    END IF;
  END IF;
  IF NEW.state = 'xac_nhan' AND NEW.recog_run_id IS NOT NULL THEN
    SELECT state INTO st FROM recognition_runs WHERE recog_run_id = NEW.recog_run_id;
    IF st <> 'khoa' THEN
      RAISE EXCEPTION 'Chỉ xác nhận lần bóc khi lần nhận dạng % đã khóa.', NEW.recog_run_id
        USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_takeoff_needs_locked_run';
    END IF;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_takeoff_state BEFORE INSERT OR UPDATE ON takeoff_results FOR EACH ROW EXECUTE FUNCTION optimat_takeoff_guard();

CREATE OR REPLACE FUNCTION optimat_takeoff_scope_guard() RETURNS trigger AS $$
DECLARE tid int; st text;
BEGIN
  IF TG_TABLE_NAME = 'takeoff_item_inputs' THEN
    SELECT i.takeoff_id INTO tid FROM takeoff_items i WHERE i.item_id = CASE WHEN TG_OP = 'DELETE' THEN OLD.item_id ELSE NEW.item_id END;
  ELSE
    tid := CASE WHEN TG_OP = 'DELETE' THEN OLD.takeoff_id ELSE NEW.takeoff_id END;
  END IF;
  SELECT state INTO st FROM takeoff_results WHERE takeoff_id = tid;
  IF st IS NOT NULL AND st <> 'tam' THEN
    RAISE EXCEPTION 'Lần bóc % đã %: không sửa %.', tid, st, TG_TABLE_NAME
      USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_takeoff_locked';
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_takeoff_items_scope  BEFORE INSERT OR UPDATE OR DELETE ON takeoff_items       FOR EACH ROW EXECUTE FUNCTION optimat_takeoff_scope_guard();
CREATE TRIGGER trg_takeoff_inputs_scope BEFORE INSERT OR UPDATE OR DELETE ON takeoff_item_inputs FOR EACH ROW EXECUTE FUNCTION optimat_takeoff_scope_guard();

-- F5. Phương án 'khoa': nội dung cố định; chỉ được đổi is_selected
CREATE OR REPLACE FUNCTION optimat_scenario_guard() RETURNS trigger AS $$
BEGIN
  IF OLD.state = 'khoa' AND (NEW.name, NEW.origin, NEW.run_id, NEW.state, NEW.price_basis_date, NEW.takeoff_id)
       IS DISTINCT FROM (OLD.name, OLD.origin, OLD.run_id, OLD.state, OLD.price_basis_date, OLD.takeoff_id) THEN
    RAISE EXCEPTION 'Phương án % đã khóa.', OLD.scenario_id USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_scenario_locked';
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_scenario_state BEFORE UPDATE ON material_scenarios FOR EACH ROW EXECUTE FUNCTION optimat_scenario_guard();

CREATE OR REPLACE FUNCTION optimat_scenario_scope_guard() RETURNS trigger AS $$
DECLARE sid bigint; st text;
BEGIN
  IF TG_TABLE_NAME = 'requirement_sources' THEN
    SELECT r.scenario_id INTO sid FROM material_requirements r WHERE r.requirement_id = CASE WHEN TG_OP = 'DELETE' THEN OLD.requirement_id ELSE NEW.requirement_id END;
  ELSE
    sid := CASE WHEN TG_OP = 'DELETE' THEN OLD.scenario_id ELSE NEW.scenario_id END;
  END IF;
  SELECT state INTO st FROM material_scenarios WHERE scenario_id = sid;
  IF st = 'khoa' THEN
    RAISE EXCEPTION 'Phương án % đã khóa: không sửa %.', sid, TG_TABLE_NAME USING ERRCODE = 'integrity_constraint_violation', CONSTRAINT = 'trg_scenario_locked';
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$ LANGUAGE plpgsql;
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['material_assignments','material_requirements','requirement_sources','scenario_price_lines'] LOOP
    EXECUTE format('CREATE TRIGGER trg_%s_scenario_scope BEFORE INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION optimat_scenario_scope_guard()', t, t);
  END LOOP;
END $$;
