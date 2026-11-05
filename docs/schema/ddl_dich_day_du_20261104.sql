-- OptiMat AI · DDL ĐÍCH ĐẦY ĐỦ (45 bảng) = sql hiện có + docs/schema/ddl_de_xuat_20261104.sql
-- Sinh bằng pg_dump --schema-only từ PostgreSQL 17 tạm ngày 04/11/2026 sau khi áp và chạy 41/41 phép thử.
\restrict whjdxsK6tTe14PWtxRZGwmJBHvjExLqKBTQcJlqn22yMprCugonGYQFbBvw9S6l
CREATE TABLE audit_logs (
    log_id bigint NOT NULL,
    user_id integer,
    action character varying(64) NOT NULL,
    detail jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE SEQUENCE audit_logs_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE audit_logs_log_id_seq OWNED BY audit_logs.log_id;
CREATE TABLE building_elements (
    element_id bigint NOT NULL,
    project_id integer NOT NULL,
    level_id bigint,
    code character varying(32) NOT NULL,
    kind character varying(24) NOT NULL,
    subtype character varying(32),
    geom_norm jsonb,
    design_material_text text,
    recog_status character varying(16) DEFAULT 'tu_dong'::character varying NOT NULL,
    recog_confidence numeric(4,3),
    removed_reason text,
    first_seen_takeoff_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_elements_conf CHECK (((recog_confidence IS NULL) OR ((recog_confidence >= (0)::numeric) AND (recog_confidence <= (1)::numeric)))),
    CONSTRAINT ck_elements_kind CHECK (((kind)::text = ANY ((ARRAY['tuong'::character varying, 'cot'::character varying, 'dam'::character varying, 'san'::character varying, 'mong'::character varying, 'giang'::character varying, 'lanh_to'::character varying, 'thang'::character varying, 'mai'::character varying, 'lo_mo'::character varying, 'nen'::character varying, 'khac'::character varying])::text[]))),
    CONSTRAINT ck_elements_removed_reason CHECK ((((recog_status)::text <> 'da_loai'::text) OR (removed_reason IS NOT NULL))),
    CONSTRAINT ck_elements_status CHECK (((recog_status)::text = ANY ((ARRAY['tu_dong'::character varying, 'nguoi_sua'::character varying, 'nguoi_them'::character varying, 'da_loai'::character varying])::text[])))
);
ALTER TABLE building_elements ALTER COLUMN element_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME building_elements_element_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE building_levels (
    level_id bigint NOT NULL,
    project_id integer NOT NULL,
    profile_version integer NOT NULL,
    code character varying(32) NOT NULL,
    name character varying(128) NOT NULL,
    seq smallint NOT NULL,
    elevation_mm numeric(10,1),
    height_mm numeric(10,1),
    height_status character(1) NOT NULL,
    height_evidence_id bigint,
    CONSTRAINT ck_levels_height CHECK (((height_mm IS NULL) OR ((height_mm > (0)::numeric) AND (height_mm <= (10000)::numeric)))),
    CONSTRAINT ck_levels_missing_is_d CHECK (((height_mm IS NOT NULL) OR (height_status = 'D'::bpchar))),
    CONSTRAINT ck_levels_seq CHECK (((seq >= 0) AND (seq <= 10))),
    CONSTRAINT ck_levels_status CHECK ((height_status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar])))
);
ALTER TABLE building_levels ALTER COLUMN level_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME building_levels_level_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE convention_clauses (
    id integer NOT NULL,
    ma character varying(16) NOT NULL,
    nhom character varying(64) NOT NULL,
    dieu_khoan text NOT NULL,
    muc character varying(1) NOT NULL,
    cach_kiem text,
    CONSTRAINT ck_convention_clauses_muc CHECK (((muc)::text = ANY ((ARRAY['B'::character varying, 'K'::character varying])::text[])))
);
CREATE SEQUENCE convention_clauses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE convention_clauses_id_seq OWNED BY convention_clauses.id;
CREATE TABLE drawing_concepts (
    id integer NOT NULL,
    ma character varying(16) NOT NULL,
    khai_niem character varying(64) NOT NULL,
    qu character varying(16),
    tin_hieu character varying(16) NOT NULL,
    mau character varying(128) NOT NULL,
    vai_tro character varying(16) NOT NULL,
    rong_mm double precision,
    cao_mm double precision,
    ghi_chu text,
    CONSTRAINT ck_drawing_concepts_signal CHECK (((tin_hieu)::text = ANY ((ARRAY['layer'::character varying, 'block'::character varying])::text[])))
);
CREATE SEQUENCE drawing_concepts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE drawing_concepts_id_seq OWNED BY drawing_concepts.id;
CREATE TABLE drawing_entities (
    entity_id bigint NOT NULL,
    revision_id bigint NOT NULL,
    view_id bigint,
    handle character varying(255) NOT NULL,
    block_path text,
    dxftype character varying(24) NOT NULL,
    layer character varying(255) NOT NULL,
    geom_wcs jsonb,
    text_raw text,
    text_norm text,
    attribs jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT ck_entities_text CHECK ((((dxftype)::text <> ALL ((ARRAY['TEXT'::character varying, 'MTEXT'::character varying, 'ATTRIB'::character varying])::text[])) OR (text_raw IS NOT NULL)))
);
ALTER TABLE drawing_entities ALTER COLUMN entity_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME drawing_entities_entity_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE drawing_views (
    view_id bigint NOT NULL,
    project_id integer NOT NULL,
    revision_id bigint NOT NULL,
    view_key character varying(64) NOT NULL,
    kind character varying(24) NOT NULL,
    sheet_type character varying(64),
    title_raw text,
    title character varying(255),
    bbox_wcs jsonb NOT NULL,
    scale_display numeric(10,3),
    scale_measure numeric(12,6),
    scale_status character(1),
    scope character varying(16) DEFAULT 'chua_xac_nhan'::character varying NOT NULL,
    parser_version character varying(32) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_drawing_views_bbox CHECK (((jsonb_typeof(bbox_wcs) = 'array'::text) AND (jsonb_array_length(bbox_wcs) = 4))),
    CONSTRAINT ck_drawing_views_kind CHECK (((kind)::text = ANY ((ARRAY['mat_bang'::character varying, 'mat_cat'::character varying, 'mat_dung'::character varying, 'chi_tiet'::character varying, 'bang_thong_ke'::character varying, 'toan_bo'::character varying, 'khac'::character varying])::text[]))),
    CONSTRAINT ck_drawing_views_scale CHECK ((((scale_display IS NULL) OR (scale_display > (0)::numeric)) AND ((scale_measure IS NULL) OR (scale_measure > (0)::numeric)))),
    CONSTRAINT ck_drawing_views_scale_status CHECK (((scale_status IS NULL) OR (scale_status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar])))),
    CONSTRAINT ck_drawing_views_scope CHECK (((scope)::text = ANY ((ARRAY['tinh'::character varying, 'tham_khao'::character varying, 'ban_sao'::character varying, 'chua_xac_nhan'::character varying])::text[])))
);
ALTER TABLE drawing_views ALTER COLUMN view_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME drawing_views_view_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE element_measurements (
    measurement_id bigint NOT NULL,
    element_id bigint NOT NULL,
    quantity_kind character varying(24) NOT NULL,
    variant character varying(32) DEFAULT ''::character varying NOT NULL,
    value numeric(14,4),
    unit character varying(8) NOT NULL,
    method character varying(24) NOT NULL,
    status character(1) NOT NULL,
    selected boolean DEFAULT false NOT NULL,
    supersedes_id bigint,
    note text,
    created_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_meas_kind CHECK (((quantity_kind)::text = ANY ((ARRAY['dai'::character varying, 'rong'::character varying, 'cao'::character varying, 'day'::character varying, 'tiet_dien_b'::character varying, 'tiet_dien_h'::character varying, 'dien_tich'::character varying, 'the_tich'::character varying, 'so_luong'::character varying, 'cao_do'::character varying, 'ham_luong_thep'::character varying, 'duong_kinh'::character varying])::text[]))),
    CONSTRAINT ck_meas_method CHECK (((method)::text = ANY ((ARRAY['hinh_hoc'::character varying, 'dimension'::character varying, 'ghi_chu'::character varying, 'bang_thong_ke'::character varying, 'mat_cat'::character varying, 'quy_tac'::character varying, 'nguoi_nhap'::character varying, 'thong_so_du_an'::character varying, 'suy_luan'::character varying])::text[]))),
    CONSTRAINT ck_meas_missing_is_d CHECK (((value IS NOT NULL) OR (status = 'D'::bpchar))),
    CONSTRAINT ck_meas_no_self CHECK (((supersedes_id IS NULL) OR (supersedes_id <> measurement_id))),
    CONSTRAINT ck_meas_positive CHECK (((value IS NULL) OR ((quantity_kind)::text = 'cao_do'::text) OR (value >= (0)::numeric))),
    CONSTRAINT ck_meas_status CHECK ((status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar]))),
    CONSTRAINT ck_meas_unit CHECK (((((quantity_kind)::text = ANY ((ARRAY['dai'::character varying, 'rong'::character varying, 'cao'::character varying, 'day'::character varying, 'tiet_dien_b'::character varying, 'tiet_dien_h'::character varying, 'cao_do'::character varying, 'duong_kinh'::character varying])::text[])) AND ((unit)::text = 'mm'::text)) OR (((quantity_kind)::text = 'dien_tich'::text) AND ((unit)::text = 'm2'::text)) OR (((quantity_kind)::text = 'the_tich'::text) AND ((unit)::text = 'm3'::text)) OR (((quantity_kind)::text = 'so_luong'::text) AND ((unit)::text = 'cai'::text)) OR (((quantity_kind)::text = 'ham_luong_thep'::text) AND ((unit)::text = 'kg_m3'::text)))),
    CONSTRAINT ck_meas_user_is_c CHECK ((((method)::text <> 'nguoi_nhap'::text) OR (status = ANY (ARRAY['C'::bpchar, 'D'::bpchar]))))
);
ALTER TABLE element_measurements ALTER COLUMN measurement_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME element_measurements_measurement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE element_occurrences (
    occurrence_id bigint NOT NULL,
    element_id bigint NOT NULL,
    view_id bigint NOT NULL,
    role character varying(16) NOT NULL,
    entity_ids bigint[] DEFAULT '{}'::bigint[] NOT NULL,
    local_geom jsonb,
    CONSTRAINT ck_occurrences_role CHECK (((role)::text = ANY ((ARRAY['hinh_chinh'::character varying, 'mat_cat'::character varying, 'chi_tiet'::character varying, 'bang_thong_ke'::character varying, 'ky_hieu'::character varying])::text[])))
);
ALTER TABLE element_occurrences ALTER COLUMN occurrence_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME element_occurrences_occurrence_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE element_relations (
    relation_id bigint NOT NULL,
    from_element_id bigint NOT NULL,
    to_element_id bigint NOT NULL,
    kind character varying(24) NOT NULL,
    status character(1) NOT NULL,
    evidence_id bigint,
    CONSTRAINT ck_relations_kind CHECK (((kind)::text = ANY ((ARRAY['thuoc_tuong'::character varying, 'goi_len'::character varying, 'noi_voi'::character varying, 'cung_chi_tiet'::character varying, 'trung_voi'::character varying, 'nam_trong'::character varying])::text[]))),
    CONSTRAINT ck_relations_no_self CHECK ((from_element_id <> to_element_id)),
    CONSTRAINT ck_relations_status CHECK ((status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar])))
);
ALTER TABLE element_relations ALTER COLUMN relation_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME element_relations_relation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE evidence_sources (
    evidence_id bigint NOT NULL,
    project_id integer NOT NULL,
    kind character varying(24) NOT NULL,
    revision_id bigint,
    view_id bigint,
    entity_ids bigint[] DEFAULT '{}'::bigint[] NOT NULL,
    raw_content text NOT NULL,
    interpreted jsonb NOT NULL,
    rule_code character varying(64),
    page_ref character varying(128),
    user_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_evidence_drawing_has_revision CHECK ((((kind)::text <> ALL ((ARRAY['chu'::character varying, 'kich_thuoc'::character varying, 'bang_thong_ke'::character varying, 'vung_ban_ve'::character varying, 'hatch'::character varying, 'block'::character varying])::text[])) OR (revision_id IS NOT NULL))),
    CONSTRAINT ck_evidence_interpreted_object CHECK ((jsonb_typeof(interpreted) = 'object'::text)),
    CONSTRAINT ck_evidence_kind CHECK (((kind)::text = ANY ((ARRAY['chu'::character varying, 'kich_thuoc'::character varying, 'bang_thong_ke'::character varying, 'vung_ban_ve'::character varying, 'hatch'::character varying, 'block'::character varying, 'tai_lieu'::character varying, 'nguoi_nhap'::character varying, 'thong_so_du_an'::character varying, 'dinh_muc'::character varying])::text[]))),
    CONSTRAINT ck_evidence_user_input CHECK ((((kind)::text <> 'nguoi_nhap'::text) OR (user_id IS NOT NULL)))
);
ALTER TABLE evidence_sources ALTER COLUMN evidence_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME evidence_sources_evidence_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE labor_rates (
    id integer NOT NULL,
    province character varying(64) NOT NULL,
    grade character varying(32) NOT NULL,
    rate_per_day numeric(12,2) NOT NULL,
    valid_from date,
    source character varying(1024) DEFAULT ''::character varying NOT NULL,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    CONSTRAINT ck_labor_rates_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[])))
);
CREATE SEQUENCE labor_rates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE labor_rates_id_seq OWNED BY labor_rates.id;
CREATE TABLE material_aliases (
    id integer NOT NULL,
    alias character varying(255) NOT NULL,
    material_id character varying(64) NOT NULL,
    source character varying(255) DEFAULT ''::character varying NOT NULL
);
CREATE SEQUENCE material_aliases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE material_aliases_id_seq OWNED BY material_aliases.id;
CREATE TABLE material_assignments (
    assignment_id bigint NOT NULL,
    scenario_id bigint NOT NULL,
    item_id bigint,
    element_id bigint,
    material_id character varying(64),
    wall_system_id character varying(64),
    source character varying(16) NOT NULL,
    evidence_id bigint,
    status character(1) NOT NULL,
    CONSTRAINT ck_assign_ai_has_evidence CHECK ((((source)::text <> 'de_xuat_ai'::text) OR (evidence_id IS NOT NULL))),
    CONSTRAINT ck_assign_empty_is_d CHECK (((material_id IS NOT NULL) OR (wall_system_id IS NOT NULL) OR (status = 'D'::bpchar))),
    CONSTRAINT ck_assign_source CHECK (((source)::text = ANY ((ARRAY['thiet_ke'::character varying, 'nguoi_dung'::character varying, 'de_xuat_ai'::character varying, 'toi_uu'::character varying])::text[]))),
    CONSTRAINT ck_assign_status CHECK ((status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar]))),
    CONSTRAINT ck_assign_target CHECK (((item_id IS NOT NULL) OR (element_id IS NOT NULL)))
);
ALTER TABLE material_assignments ALTER COLUMN assignment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME material_assignments_assignment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE material_families (
    family_id character varying(32) NOT NULL,
    name character varying(255) NOT NULL,
    sort_order integer NOT NULL,
    is_wall boolean DEFAULT false NOT NULL
);
CREATE TABLE material_groups (
    group_id character varying(64) NOT NULL,
    sort_order integer NOT NULL,
    name character varying(255) NOT NULL,
    description text DEFAULT ''::text NOT NULL
);
CREATE TABLE material_notes (
    id integer NOT NULL,
    rule_id character varying(32) NOT NULL,
    pattern character varying(255) NOT NULL,
    material_id character varying(32) NOT NULL,
    ten character varying(255),
    nguon character varying(32),
    kiem_chung character varying(32),
    ghi_chu text
);
CREATE SEQUENCE material_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE material_notes_id_seq OWNED BY material_notes.id;
CREATE TABLE material_relations (
    id integer NOT NULL,
    material_id character varying(64) NOT NULL,
    relation_type character varying(16) NOT NULL,
    related_material_id character varying(64) NOT NULL,
    quantity double precision,
    quantity_unit character varying(64),
    source character varying(255),
    note text,
    CONSTRAINT ck_material_relations_type CHECK (((relation_type)::text = ANY ((ARRAY['REQUIRES'::character varying, 'COMPOSED_OF'::character varying])::text[])))
);
CREATE SEQUENCE material_relations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE material_relations_id_seq OWNED BY material_relations.id;
CREATE TABLE material_requirements (
    requirement_id bigint NOT NULL,
    scenario_id bigint NOT NULL,
    material_id character varying(64),
    name character varying(255) NOT NULL,
    unit character varying(16) NOT NULL,
    quantity numeric(14,4),
    complete boolean NOT NULL,
    waste_pct numeric(6,3),
    quantity_with_waste numeric(14,4),
    quantity_min numeric(14,4),
    quantity_max numeric(14,4),
    confirmation character varying(16),
    status character(1) NOT NULL,
    missing text[] DEFAULT '{}'::text[] NOT NULL,
    group_id character varying(64),
    raw_class character varying(32),
    weight_kg numeric(14,3),
    CONSTRAINT ck_req_confirm CHECK (((confirmation IS NULL) OR ((confirmation)::text = ANY ((ARRAY['nguon'::character varying, 'tinh'::character varying, 'kinh_nghiem'::character varying])::text[])))),
    CONSTRAINT ck_req_incomplete_is_d CHECK ((complete OR (status = 'D'::bpchar))),
    CONSTRAINT ck_req_range CHECK (((quantity_min IS NULL) OR (quantity_max IS NULL) OR (quantity_min <= quantity_max))),
    CONSTRAINT ck_req_status CHECK ((status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar]))),
    CONSTRAINT ck_req_waste CHECK (((waste_pct IS NULL) OR ((waste_pct >= (0)::numeric) AND (waste_pct < (100)::numeric)))),
    CONSTRAINT ck_req_waste_needs_pct CHECK (((quantity_with_waste IS NULL) OR (waste_pct IS NOT NULL)))
);
ALTER TABLE material_requirements ALTER COLUMN requirement_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME material_requirements_requirement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE material_rules (
    id integer NOT NULL,
    rule_id character varying(32) NOT NULL,
    signal character varying(16) NOT NULL,
    pattern character varying(255) NOT NULL,
    target character varying(255),
    element character varying(32),
    width_mm double precision,
    height_mm double precision,
    priority integer DEFAULT 0 NOT NULL,
    note text,
    CONSTRAINT ck_material_rules_signal CHECK (((signal)::text = ANY ((ARRAY['text'::character varying, 'hatch'::character varying, 'layer'::character varying, 'block'::character varying])::text[])))
);
CREATE SEQUENCE material_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE material_rules_id_seq OWNED BY material_rules.id;
CREATE TABLE material_scenarios (
    scenario_id bigint NOT NULL,
    takeoff_id integer NOT NULL,
    name character varying(128) NOT NULL,
    origin character varying(16) NOT NULL,
    run_id integer,
    is_selected boolean DEFAULT false NOT NULL,
    created_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_scenarios_origin CHECK (((origin)::text = ANY ((ARRAY['thiet_ke'::character varying, 'nguoi_dung'::character varying, 'de_xuat_ai'::character varying, 'toi_uu'::character varying])::text[]))),
    CONSTRAINT ck_scenarios_run CHECK ((((origin)::text <> 'toi_uu'::text) OR (run_id IS NOT NULL)))
);
ALTER TABLE material_scenarios ALTER COLUMN scenario_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME material_scenarios_scenario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE material_standards (
    material_id character varying(64) NOT NULL,
    standard_id integer NOT NULL,
    note character varying(255) DEFAULT ''::character varying NOT NULL
);
CREATE TABLE materials (
    material_id character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    "group" character varying(64) NOT NULL,
    thickness_mm double precision,
    unit character varying(16) NOT NULL,
    qty_per_m2 double precision,
    weight_kg_per_m2 double precision,
    lambda_w_mk double precision,
    labor_days_per_m2 double precision,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    subgroup character varying(128),
    family character varying(32),
    usage_text character varying(255),
    usage_role character varying(128),
    tier integer,
    purchase_unit character varying(32),
    unit_conversion double precision,
    length_mm double precision,
    width_mm double precision,
    height_mm double precision,
    price_priority character varying(4),
    needs_lambda boolean,
    lambda_source character varying(255),
    unit_weight_kg double precision,
    weight_source character varying(255),
    transport_volume_m3 double precision,
    waste_pct double precision,
    waste_source character varying(255),
    standards_text text,
    reference_brands text,
    tech_notes text,
    data_note text,
    raw_class character varying(32),
    CONSTRAINT ck_materials_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[])))
);
CREATE TABLE measurement_evidence (
    measurement_id bigint NOT NULL,
    evidence_id bigint NOT NULL,
    role character varying(16) DEFAULT 'chinh'::character varying NOT NULL,
    CONSTRAINT ck_meas_evidence_role CHECK (((role)::text = ANY ((ARRAY['chinh'::character varying, 'doi_chieu'::character varying, 'mau_thuan'::character varying])::text[])))
);
CREATE TABLE model_versions (
    version character varying(32) NOT NULL,
    target character varying(32) NOT NULL,
    trained_at timestamp with time zone DEFAULT now() NOT NULL,
    data_rows integer NOT NULL,
    contains_synthetic boolean DEFAULT false NOT NULL,
    metrics jsonb NOT NULL,
    file_path character varying(1024) NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_model_versions_target CHECK (((target)::text = ANY ((ARRAY['material_price'::character varying, 'transport_cost'::character varying])::text[])))
);
CREATE TABLE optimization_runs (
    run_id integer NOT NULL,
    project_id integer NOT NULL,
    takeoff_id integer,
    model_version character varying(32),
    method character varying(16) NOT NULL,
    config jsonb DEFAULT '{}'::jsonb NOT NULL,
    solutions jsonb NOT NULL,
    chosen_index integer,
    price_snapshot_date date,
    llm_model character varying(64),
    tool_calls jsonb DEFAULT '[]'::jsonb NOT NULL,
    excluded_materials jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_optimization_chosen CHECK (((chosen_index IS NULL) OR (chosen_index >= 0))),
    CONSTRAINT ck_optimization_method CHECK (((method)::text = ANY ((ARRAY['nsga2'::character varying, 'brute'::character varying])::text[])))
);
CREATE SEQUENCE optimization_runs_run_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE optimization_runs_run_id_seq OWNED BY optimization_runs.run_id;
CREATE TABLE price_records (
    id bigint NOT NULL,
    date date NOT NULL,
    material_id character varying(64) NOT NULL,
    supplier_id character varying(64),
    province character varying(64) NOT NULL,
    quantity double precision NOT NULL,
    unit character varying(16) NOT NULL,
    unit_price numeric(14,2) NOT NULL,
    vat_included character varying(8) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    transport_included character varying(8) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    source character varying(1024) DEFAULT ''::character varying NOT NULL,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    price_level character varying(16) DEFAULT 'DEALER'::character varying NOT NULL,
    CONSTRAINT ck_price_records_basis CHECK ((((vat_included)::text = ANY ((ARRAY['YES'::character varying, 'NO'::character varying, 'UNKNOWN'::character varying])::text[])) AND ((transport_included)::text = ANY ((ARRAY['YES'::character varying, 'NO'::character varying, 'UNKNOWN'::character varying])::text[])))),
    CONSTRAINT ck_price_records_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[]))),
    CONSTRAINT ck_price_records_positive CHECK (((unit_price)::double precision > (0)::double precision)),
    CONSTRAINT ck_price_records_price_level CHECK (((price_level)::text = ANY ((ARRAY['DEALER'::character varying, 'QUOTE'::character varying, 'BULLETIN'::character varying])::text[]))),
    CONSTRAINT ck_price_records_supplier CHECK (((supplier_id IS NOT NULL) OR ((price_level)::text = 'BULLETIN'::text)))
);
CREATE SEQUENCE price_records_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE price_records_id_seq OWNED BY price_records.id;
CREATE TABLE project_document_revisions (
    revision_id bigint NOT NULL,
    file_id integer NOT NULL,
    version integer NOT NULL,
    sha256 character varying(64) NOT NULL,
    stored_path text NOT NULL,
    size_bytes bigint NOT NULL,
    format character varying(16) NOT NULL,
    role character varying(16) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_document_role CHECK (((role)::text = ANY ((ARRAY['KT'::character varying, 'KC'::character varying, 'HO_SO'::character varying, 'TIEN_LUONG'::character varying, 'THAM_KHAO'::character varying])::text[]))),
    CONSTRAINT ck_document_version_size CHECK (((version > 0) AND (size_bytes > 0)))
);
CREATE SEQUENCE project_document_revisions_revision_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE project_document_revisions_revision_id_seq OWNED BY project_document_revisions.revision_id;
CREATE TABLE project_files (
    file_id integer NOT NULL,
    project_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    file_type character varying(16) NOT NULL,
    stored_path character varying(1024) NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_project_files_type CHECK (((file_type)::text = ANY ((ARRAY['dwg'::character varying, 'dxf'::character varying, 'pdf'::character varying, 'xlsx'::character varying, 'xls'::character varying, 'docx'::character varying, 'doc'::character varying, 'csv'::character varying, 'json'::character varying, 'md'::character varying])::text[])))
);
CREATE SEQUENCE project_files_file_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE project_files_file_id_seq OWNED BY project_files.file_id;
CREATE TABLE project_profile_revisions (
    revision_id bigint NOT NULL,
    project_id integer NOT NULL,
    version integer NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_project_profile_version CHECK ((version > 0))
);
CREATE SEQUENCE project_profile_revisions_revision_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE project_profile_revisions_revision_id_seq OWNED BY project_profile_revisions.revision_id;
CREATE TABLE projects (
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(255) NOT NULL,
    address character varying(512) DEFAULT ''::character varying NOT NULL,
    site_lat double precision,
    site_lon double precision,
    floor_height_mm double precision,
    door_width_mm double precision,
    door_height_mm double precision,
    window_width_mm double precision,
    window_height_mm double precision,
    budget numeric(16,2),
    deadline_days double precision,
    max_vehicle_ton double precision,
    excluded_materials jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_projects_dims_positive CHECK (((COALESCE(floor_height_mm, (1)::double precision) > (0)::double precision) AND (COALESCE(door_width_mm, (1)::double precision) > (0)::double precision) AND (COALESCE(door_height_mm, (1)::double precision) > (0)::double precision) AND (COALESCE(window_width_mm, (1)::double precision) > (0)::double precision) AND (COALESCE(window_height_mm, (1)::double precision) > (0)::double precision))),
    CONSTRAINT ck_projects_latlon CHECK ((((site_lat IS NULL) OR ((site_lat >= ('-90'::integer)::double precision) AND (site_lat <= (90)::double precision))) AND ((site_lon IS NULL) OR ((site_lon >= ('-180'::integer)::double precision) AND (site_lon <= (180)::double precision)))))
);
CREATE SEQUENCE projects_project_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE projects_project_id_seq OWNED BY projects.project_id;
CREATE TABLE requirement_sources (
    requirement_id bigint NOT NULL,
    item_id bigint NOT NULL,
    rough_norm_id integer,
    quantity_part numeric(14,4)
);
CREATE TABLE review_issues (
    issue_id bigint NOT NULL,
    project_id integer NOT NULL,
    takeoff_id integer,
    kind character varying(24) NOT NULL,
    severity character varying(8) NOT NULL,
    element_id bigint,
    measurement_id bigint,
    view_id bigint,
    message text NOT NULL,
    check_code character varying(32),
    state character varying(12) DEFAULT 'mo'::character varying NOT NULL,
    resolution text,
    resolved_by integer,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_issues_kind CHECK (((kind)::text = ANY ((ARRAY['thieu_so'::character varying, 'mau_thuan'::character varying, 'nghi_trung'::character varying, 'chua_ro'::character varying, 'ngoai_khoang'::character varying, 'thieu_ban_ve'::character varying])::text[]))),
    CONSTRAINT ck_issues_resolved CHECK ((((state)::text = 'mo'::text) OR ((resolution IS NOT NULL) AND (resolved_at IS NOT NULL)))),
    CONSTRAINT ck_issues_severity CHECK (((severity)::text = ANY ((ARRAY['chan'::character varying, 'canh_bao'::character varying, 'ghi_chu'::character varying])::text[]))),
    CONSTRAINT ck_issues_state CHECK (((state)::text = ANY ((ARRAY['mo'::character varying, 'da_xu_ly'::character varying, 'chap_nhan'::character varying, 'bo_qua'::character varying])::text[])))
);
ALTER TABLE review_issues ALTER COLUMN issue_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME review_issues_issue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE room_rules (
    id integer NOT NULL,
    rule_id character varying(32) NOT NULL,
    pattern character varying(255) NOT NULL,
    kind character varying(16) NOT NULL,
    note text,
    CONSTRAINT ck_room_rules_kind CHECK (((kind)::text = ANY ((ARRAY['WET'::character varying, 'BALCONY'::character varying])::text[])))
);
CREATE SEQUENCE room_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE room_rules_id_seq OWNED BY room_rules.id;
CREATE TABLE rough_norms (
    id integer NOT NULL,
    work_code character varying(32) NOT NULL,
    variant character varying(32),
    material_id character varying(64),
    material_name character varying(255),
    qty double precision,
    qty_unit character varying(64),
    qty_min double precision,
    qty_max double precision,
    muc_xac_nhan character varying(16),
    ngay_tra character varying(10),
    norm_code character varying(64),
    source character varying(255),
    note text,
    CONSTRAINT ck_rough_norms_confirm CHECK (((muc_xac_nhan IS NULL) OR ((muc_xac_nhan)::text = ANY ((ARRAY['nguon'::character varying, 'tinh'::character varying, 'kinh_nghiem'::character varying])::text[])))),
    CONSTRAINT ck_rough_norms_range CHECK (((qty_min IS NULL) OR (qty_max IS NULL) OR (qty_min <= qty_max)))
);
CREATE SEQUENCE rough_norms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE rough_norms_id_seq OWNED BY rough_norms.id;
CREATE TABLE standards (
    standard_id integer NOT NULL,
    code character varying(64) NOT NULL,
    title text NOT NULL,
    kind character varying(32) DEFAULT ''::character varying NOT NULL,
    status character varying(32) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    valid_from date,
    valid_to date,
    source_url character varying(1024) DEFAULT ''::character varying NOT NULL,
    CONSTRAINT ck_standards_kind CHECK (((kind)::text = ANY ((ARRAY['TCVN'::character varying, 'QCVN'::character varying, 'THONG_TU'::character varying, 'KHAC'::character varying])::text[]))),
    CONSTRAINT ck_standards_period CHECK (((valid_to IS NULL) OR (valid_from IS NULL) OR (valid_to >= valid_from))),
    CONSTRAINT ck_standards_status CHECK (((status)::text = ANY ((ARRAY['CON_HIEU_LUC'::character varying, 'HET_HIEU_LUC'::character varying, 'UNKNOWN'::character varying])::text[])))
);
CREATE SEQUENCE standards_standard_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE standards_standard_id_seq OWNED BY standards.standard_id;
CREATE TABLE supplier_materials (
    id integer NOT NULL,
    supplier_id character varying(64) NOT NULL,
    material_id character varying(64) NOT NULL,
    base_price numeric(14,2),
    product_url character varying(1024),
    collected_at date NOT NULL,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    dealer_product_name character varying(255),
    brand character varying(128),
    sale_unit character varying(32),
    unit_conversion double precision,
    price_level character varying(16),
    price_date date,
    vat_included character varying(8) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    transport_included character varying(8) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    in_stock boolean,
    note text,
    CONSTRAINT ck_supplier_materials_basis CHECK ((((vat_included)::text = ANY ((ARRAY['YES'::character varying, 'NO'::character varying, 'UNKNOWN'::character varying])::text[])) AND ((transport_included)::text = ANY ((ARRAY['YES'::character varying, 'NO'::character varying, 'UNKNOWN'::character varying])::text[])))),
    CONSTRAINT ck_supplier_materials_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[]))),
    CONSTRAINT ck_supplier_materials_price_complete CHECK (((base_price IS NULL) OR (((base_price)::double precision > (0)::double precision) AND (price_level IS NOT NULL) AND (price_date IS NOT NULL)))),
    CONSTRAINT ck_supplier_materials_price_level CHECK (((price_level IS NULL) OR ((price_level)::text = ANY ((ARRAY['DEALER'::character varying, 'QUOTE'::character varying])::text[]))))
);
CREATE SEQUENCE supplier_materials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE supplier_materials_id_seq OWNED BY supplier_materials.id;
CREATE TABLE suppliers (
    supplier_id character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    province character varying(64) NOT NULL,
    lat double precision,
    lon double precision,
    lead_time_days double precision,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    dealer_type character varying(64),
    brands text,
    address character varying(512),
    ward character varying(128),
    district character varying(128),
    maps_url character varying(1024),
    phone character varying(64),
    zalo character varying(64),
    email character varying(255),
    website character varying(1024),
    facebook character varying(1024),
    tax_code character varying(32),
    opening_hours character varying(255),
    delivers boolean,
    delivery_radius_km double precision,
    max_truck_ton double precision,
    min_order character varying(255),
    vat_invoice boolean,
    payment character varying(255),
    price_public character varying(8),
    price_page_url character varying(1024),
    verified boolean,
    collected_at date,
    collected_by character varying(128),
    source character varying(1024),
    note text,
    CONSTRAINT ck_suppliers_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[]))),
    CONSTRAINT ck_suppliers_latlon CHECK ((((lat >= ('-90'::integer)::double precision) AND (lat <= (90)::double precision)) AND ((lon >= ('-180'::integer)::double precision) AND (lon <= (180)::double precision)))),
    CONSTRAINT ck_suppliers_price_public CHECK (((price_public IS NULL) OR ((price_public)::text = ANY ((ARRAY['YES'::character varying, 'NO'::character varying, 'PARTIAL'::character varying])::text[]))))
);
CREATE TABLE takeoff_item_inputs (
    item_id bigint NOT NULL,
    seq smallint NOT NULL,
    input_kind character varying(20) NOT NULL,
    measurement_id bigint,
    rough_norm_id integer,
    label character varying(128) NOT NULL,
    value_snapshot numeric(14,4),
    unit character varying(16),
    status character(1) NOT NULL,
    CONSTRAINT ck_inputs_kind CHECK (((input_kind)::text = ANY ((ARRAY['so_do'::character varying, 'thong_so'::character varying, 'dinh_muc'::character varying, 'ket_qua_trung_gian'::character varying])::text[]))),
    CONSTRAINT ck_inputs_missing_is_d CHECK (((value_snapshot IS NOT NULL) OR (status = 'D'::bpchar))),
    CONSTRAINT ck_inputs_status CHECK ((status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar])))
);
CREATE TABLE takeoff_items (
    item_id bigint NOT NULL,
    takeoff_id integer NOT NULL,
    seq integer NOT NULL,
    work_code character varying(32) NOT NULL,
    level_id bigint,
    element_id bigint,
    element_label character varying(255),
    variant character varying(64),
    unit character varying(8) NOT NULL,
    quantity numeric(14,4),
    quantity_known numeric(14,4),
    formula text DEFAULT ''::text NOT NULL,
    basis character varying(24),
    wall_system_id character varying(64),
    stage character varying(16),
    status character(1) NOT NULL,
    missing text[] DEFAULT '{}'::text[] NOT NULL,
    source character varying(8) DEFAULT 'auto'::character varying NOT NULL,
    CONSTRAINT ck_items_basis CHECK (((basis IS NULL) OR ((basis)::text = ANY ((ARRAY['bang_thong_ke'::character varying, 'ham_luong'::character varying, 'not_supported'::character varying])::text[])))),
    CONSTRAINT ck_items_d_has_reason CHECK (((status <> 'D'::bpchar) OR (cardinality(missing) > 0))),
    CONSTRAINT ck_items_known_le_total CHECK (((quantity IS NULL) OR (quantity_known IS NULL) OR (quantity_known <= quantity))),
    CONSTRAINT ck_items_missing_is_d CHECK (((quantity IS NOT NULL) OR (status = 'D'::bpchar))),
    CONSTRAINT ck_items_source CHECK (((source)::text = ANY ((ARRAY['auto'::character varying, 'manual'::character varying])::text[]))),
    CONSTRAINT ck_items_status CHECK ((status = ANY (ARRAY['A'::bpchar, 'B'::bpchar, 'C'::bpchar, 'D'::bpchar])))
);
ALTER TABLE takeoff_items ALTER COLUMN item_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME takeoff_items_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
CREATE TABLE takeoff_results (
    takeoff_id integer NOT NULL,
    project_id integer NOT NULL,
    file_id integer,
    result jsonb NOT NULL,
    layer_overrides jsonb DEFAULT '{}'::jsonb NOT NULL,
    confirmed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    kind character varying(24) DEFAULT 'takeoff'::character varying NOT NULL,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    profile_version integer,
    input_revisions jsonb DEFAULT '[]'::jsonb NOT NULL,
    params_snapshot jsonb DEFAULT '{}'::jsonb NOT NULL,
    engine_version character varying(32),
    request_sha256 character(64),
    response_sha256 character(64),
    client_analysis_id uuid,
    state character varying(12) DEFAULT 'tam'::character varying NOT NULL,
    superseded_by integer,
    CONSTRAINT ck_takeoff_confirmed CHECK ((((state)::text <> 'xac_nhan'::text) OR (confirmed_at IS NOT NULL))),
    CONSTRAINT ck_takeoff_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[]))),
    CONSTRAINT ck_takeoff_inputs_array CHECK ((jsonb_typeof(input_revisions) = 'array'::text)),
    CONSTRAINT ck_takeoff_kind CHECK (((kind)::text = ANY ((ARRAY['takeoff'::character varying, 'rough'::character varying, 'estimate_reference'::character varying, 'estimate_comparison'::character varying, 'synthetic_housing'::character varying])::text[]))),
    CONSTRAINT ck_takeoff_no_self CHECK (((superseded_by IS NULL) OR (superseded_by <> takeoff_id))),
    CONSTRAINT ck_takeoff_state CHECK (((state)::text = ANY ((ARRAY['tam'::character varying, 'xac_nhan'::character varying, 'huy'::character varying])::text[]))),
    CONSTRAINT ck_takeoff_synthetic CHECK ((((kind)::text <> 'synthetic_housing'::text) OR ((data_kind)::text = 'SYNTHETIC'::text)))
);
CREATE SEQUENCE takeoff_results_takeoff_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE takeoff_results_takeoff_id_seq OWNED BY takeoff_results.takeoff_id;
CREATE TABLE users (
    user_id integer NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255) DEFAULT ''::character varying NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(16) DEFAULT 'user'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_users_role CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'user'::character varying])::text[])))
);
CREATE SEQUENCE users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE users_user_id_seq OWNED BY users.user_id;
CREATE TABLE vehicles (
    vehicle_id character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    payload_ton double precision NOT NULL,
    base_fee numeric(12,2) NOT NULL,
    fee_per_km numeric(12,2) NOT NULL,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    CONSTRAINT ck_vehicles_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[])))
);
CREATE TABLE view_levels (
    view_id bigint NOT NULL,
    level_id bigint NOT NULL
);
CREATE TABLE wall_systems (
    wall_system_id character varying(64) NOT NULL,
    material_id character varying(64) NOT NULL,
    wall_thickness_mm double precision,
    detect_class character varying(8),
    role character varying(16),
    masonry_thickness_mm double precision,
    norm_code character varying(32),
    units_per_m3 double precision,
    mortar_m3_per_m3 double precision,
    labor_day_per_m3 double precision,
    unit_factor double precision,
    mortar_material_id character varying(64),
    mortar_density double precision,
    r0_reference double precision,
    norm_source character varying(255),
    note text,
    data_kind character varying(16) DEFAULT 'ACTUAL'::character varying NOT NULL,
    CONSTRAINT ck_wall_systems_class CHECK (((detect_class IS NULL) OR ((detect_class)::text = ANY ((ARRAY['110'::character varying, '150'::character varying, '220'::character varying, '330'::character varying])::text[])))),
    CONSTRAINT ck_wall_systems_data_kind CHECK (((data_kind)::text = ANY ((ARRAY['ACTUAL'::character varying, 'SAMPLE'::character varying, 'SYNTHETIC'::character varying])::text[]))),
    CONSTRAINT ck_wall_systems_role CHECK (((role IS NULL) OR ((role)::text = ANY ((ARRAY['envelope'::character varying, 'partition'::character varying])::text[]))))
);
ALTER TABLE ONLY audit_logs ALTER COLUMN log_id SET DEFAULT nextval('audit_logs_log_id_seq'::regclass);
ALTER TABLE ONLY convention_clauses ALTER COLUMN id SET DEFAULT nextval('convention_clauses_id_seq'::regclass);
ALTER TABLE ONLY drawing_concepts ALTER COLUMN id SET DEFAULT nextval('drawing_concepts_id_seq'::regclass);
ALTER TABLE ONLY labor_rates ALTER COLUMN id SET DEFAULT nextval('labor_rates_id_seq'::regclass);
ALTER TABLE ONLY material_aliases ALTER COLUMN id SET DEFAULT nextval('material_aliases_id_seq'::regclass);
ALTER TABLE ONLY material_notes ALTER COLUMN id SET DEFAULT nextval('material_notes_id_seq'::regclass);
ALTER TABLE ONLY material_relations ALTER COLUMN id SET DEFAULT nextval('material_relations_id_seq'::regclass);
ALTER TABLE ONLY material_rules ALTER COLUMN id SET DEFAULT nextval('material_rules_id_seq'::regclass);
ALTER TABLE ONLY optimization_runs ALTER COLUMN run_id SET DEFAULT nextval('optimization_runs_run_id_seq'::regclass);
ALTER TABLE ONLY price_records ALTER COLUMN id SET DEFAULT nextval('price_records_id_seq'::regclass);
ALTER TABLE ONLY project_document_revisions ALTER COLUMN revision_id SET DEFAULT nextval('project_document_revisions_revision_id_seq'::regclass);
ALTER TABLE ONLY project_files ALTER COLUMN file_id SET DEFAULT nextval('project_files_file_id_seq'::regclass);
ALTER TABLE ONLY project_profile_revisions ALTER COLUMN revision_id SET DEFAULT nextval('project_profile_revisions_revision_id_seq'::regclass);
ALTER TABLE ONLY projects ALTER COLUMN project_id SET DEFAULT nextval('projects_project_id_seq'::regclass);
ALTER TABLE ONLY room_rules ALTER COLUMN id SET DEFAULT nextval('room_rules_id_seq'::regclass);
ALTER TABLE ONLY rough_norms ALTER COLUMN id SET DEFAULT nextval('rough_norms_id_seq'::regclass);
ALTER TABLE ONLY standards ALTER COLUMN standard_id SET DEFAULT nextval('standards_standard_id_seq'::regclass);
ALTER TABLE ONLY supplier_materials ALTER COLUMN id SET DEFAULT nextval('supplier_materials_id_seq'::regclass);
ALTER TABLE ONLY takeoff_results ALTER COLUMN takeoff_id SET DEFAULT nextval('takeoff_results_takeoff_id_seq'::regclass);
ALTER TABLE ONLY users ALTER COLUMN user_id SET DEFAULT nextval('users_user_id_seq'::regclass);
ALTER TABLE ONLY audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (log_id);
ALTER TABLE ONLY building_elements
    ADD CONSTRAINT building_elements_pkey PRIMARY KEY (element_id);
ALTER TABLE ONLY building_levels
    ADD CONSTRAINT building_levels_pkey PRIMARY KEY (level_id);
ALTER TABLE ONLY convention_clauses
    ADD CONSTRAINT convention_clauses_ma_key UNIQUE (ma);
ALTER TABLE ONLY convention_clauses
    ADD CONSTRAINT convention_clauses_pkey PRIMARY KEY (id);
ALTER TABLE ONLY drawing_concepts
    ADD CONSTRAINT drawing_concepts_ma_key UNIQUE (ma);
ALTER TABLE ONLY drawing_concepts
    ADD CONSTRAINT drawing_concepts_pkey PRIMARY KEY (id);
ALTER TABLE ONLY drawing_entities
    ADD CONSTRAINT drawing_entities_pkey PRIMARY KEY (entity_id);
ALTER TABLE ONLY drawing_views
    ADD CONSTRAINT drawing_views_pkey PRIMARY KEY (view_id);
ALTER TABLE ONLY element_measurements
    ADD CONSTRAINT element_measurements_pkey PRIMARY KEY (measurement_id);
ALTER TABLE ONLY element_occurrences
    ADD CONSTRAINT element_occurrences_pkey PRIMARY KEY (occurrence_id);
ALTER TABLE ONLY element_relations
    ADD CONSTRAINT element_relations_pkey PRIMARY KEY (relation_id);
ALTER TABLE ONLY evidence_sources
    ADD CONSTRAINT evidence_sources_pkey PRIMARY KEY (evidence_id);
ALTER TABLE ONLY labor_rates
    ADD CONSTRAINT labor_rates_pkey PRIMARY KEY (id);
ALTER TABLE ONLY material_aliases
    ADD CONSTRAINT material_aliases_alias_material_id_key UNIQUE (alias, material_id);
ALTER TABLE ONLY material_aliases
    ADD CONSTRAINT material_aliases_pkey PRIMARY KEY (id);
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_pkey PRIMARY KEY (assignment_id);
ALTER TABLE ONLY material_families
    ADD CONSTRAINT material_families_pkey PRIMARY KEY (family_id);
ALTER TABLE ONLY material_groups
    ADD CONSTRAINT material_groups_pkey PRIMARY KEY (group_id);
ALTER TABLE ONLY material_notes
    ADD CONSTRAINT material_notes_pkey PRIMARY KEY (id);
ALTER TABLE ONLY material_notes
    ADD CONSTRAINT material_notes_rule_id_key UNIQUE (rule_id);
ALTER TABLE ONLY material_relations
    ADD CONSTRAINT material_relations_material_id_related_material_id_rela_f54c UNIQUE (material_id, related_material_id, relation_type);
ALTER TABLE ONLY material_relations
    ADD CONSTRAINT material_relations_pkey PRIMARY KEY (id);
ALTER TABLE ONLY material_requirements
    ADD CONSTRAINT material_requirements_pkey PRIMARY KEY (requirement_id);
ALTER TABLE ONLY material_rules
    ADD CONSTRAINT material_rules_pkey PRIMARY KEY (id);
ALTER TABLE ONLY material_rules
    ADD CONSTRAINT material_rules_rule_id_key UNIQUE (rule_id);
ALTER TABLE ONLY material_scenarios
    ADD CONSTRAINT material_scenarios_pkey PRIMARY KEY (scenario_id);
ALTER TABLE ONLY material_standards
    ADD CONSTRAINT material_standards_pkey PRIMARY KEY (material_id, standard_id);
ALTER TABLE ONLY materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (material_id);
ALTER TABLE ONLY measurement_evidence
    ADD CONSTRAINT measurement_evidence_pkey PRIMARY KEY (measurement_id, evidence_id);
ALTER TABLE ONLY model_versions
    ADD CONSTRAINT model_versions_pkey PRIMARY KEY (version);
ALTER TABLE ONLY optimization_runs
    ADD CONSTRAINT optimization_runs_pkey PRIMARY KEY (run_id);
ALTER TABLE ONLY price_records
    ADD CONSTRAINT price_records_pkey PRIMARY KEY (id);
ALTER TABLE ONLY project_document_revisions
    ADD CONSTRAINT project_document_revisions_pkey PRIMARY KEY (revision_id);
ALTER TABLE ONLY project_files
    ADD CONSTRAINT project_files_pkey PRIMARY KEY (file_id);
ALTER TABLE ONLY project_profile_revisions
    ADD CONSTRAINT project_profile_revisions_pkey PRIMARY KEY (revision_id);
ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (project_id);
ALTER TABLE ONLY requirement_sources
    ADD CONSTRAINT requirement_sources_pkey PRIMARY KEY (requirement_id, item_id);
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_pkey PRIMARY KEY (issue_id);
ALTER TABLE ONLY room_rules
    ADD CONSTRAINT room_rules_pkey PRIMARY KEY (id);
ALTER TABLE ONLY room_rules
    ADD CONSTRAINT room_rules_rule_id_key UNIQUE (rule_id);
ALTER TABLE ONLY rough_norms
    ADD CONSTRAINT rough_norms_pkey PRIMARY KEY (id);
ALTER TABLE ONLY standards
    ADD CONSTRAINT standards_code_key UNIQUE (code);
ALTER TABLE ONLY standards
    ADD CONSTRAINT standards_pkey PRIMARY KEY (standard_id);
ALTER TABLE ONLY supplier_materials
    ADD CONSTRAINT supplier_materials_pkey PRIMARY KEY (id);
ALTER TABLE ONLY supplier_materials
    ADD CONSTRAINT supplier_materials_supplier_id_material_id_key UNIQUE (supplier_id, material_id);
ALTER TABLE ONLY suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (supplier_id);
ALTER TABLE ONLY takeoff_item_inputs
    ADD CONSTRAINT takeoff_item_inputs_pkey PRIMARY KEY (item_id, seq);
ALTER TABLE ONLY takeoff_items
    ADD CONSTRAINT takeoff_items_pkey PRIMARY KEY (item_id);
ALTER TABLE ONLY takeoff_results
    ADD CONSTRAINT takeoff_results_pkey PRIMARY KEY (takeoff_id);
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT uq_assignments UNIQUE NULLS NOT DISTINCT (scenario_id, item_id, element_id);
ALTER TABLE ONLY building_elements
    ADD CONSTRAINT uq_building_elements UNIQUE NULLS NOT DISTINCT (project_id, level_id, kind, code);
ALTER TABLE ONLY building_levels
    ADD CONSTRAINT uq_building_levels UNIQUE (project_id, profile_version, code);
ALTER TABLE ONLY project_document_revisions
    ADD CONSTRAINT uq_document_file_version UNIQUE (file_id, version);
ALTER TABLE ONLY drawing_entities
    ADD CONSTRAINT uq_drawing_entities UNIQUE (revision_id, handle);
ALTER TABLE ONLY drawing_views
    ADD CONSTRAINT uq_drawing_views UNIQUE (revision_id, view_key, parser_version);
ALTER TABLE ONLY element_occurrences
    ADD CONSTRAINT uq_element_occurrences UNIQUE (element_id, view_id, role);
ALTER TABLE ONLY element_relations
    ADD CONSTRAINT uq_element_relations UNIQUE (from_element_id, to_element_id, kind);
ALTER TABLE ONLY project_profile_revisions
    ADD CONSTRAINT uq_project_profile_version UNIQUE (project_id, version);
ALTER TABLE ONLY takeoff_items
    ADD CONSTRAINT uq_takeoff_items UNIQUE (takeoff_id, seq);
ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);
ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);
ALTER TABLE ONLY vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (vehicle_id);
ALTER TABLE ONLY view_levels
    ADD CONSTRAINT view_levels_pkey PRIMARY KEY (view_id, level_id);
ALTER TABLE ONLY wall_systems
    ADD CONSTRAINT wall_systems_pkey PRIMARY KEY (wall_system_id);
CREATE INDEX ix_audit_logs_action ON audit_logs USING btree (action);
CREATE INDEX ix_building_elements_kind ON building_elements USING btree (project_id, kind);
CREATE INDEX ix_drawing_entities_view ON drawing_entities USING btree (view_id);
CREATE INDEX ix_drawing_views_project ON drawing_views USING btree (project_id);
CREATE INDEX ix_evidence_project ON evidence_sources USING btree (project_id, kind);
CREATE INDEX ix_labor_rates_province ON labor_rates USING btree (province);
CREATE INDEX ix_material_aliases_alias ON material_aliases USING btree (alias);
CREATE INDEX ix_material_notes_material_id ON material_notes USING btree (material_id);
CREATE INDEX ix_material_relations_material_id ON material_relations USING btree (material_id);
CREATE INDEX ix_material_requirements_scenario ON material_requirements USING btree (scenario_id, material_id);
CREATE INDEX ix_optimization_runs_project_id ON optimization_runs USING btree (project_id);
CREATE INDEX ix_price_records_lookup ON price_records USING btree (material_id, supplier_id, date);
CREATE INDEX ix_project_document_revisions_file_id ON project_document_revisions USING btree (file_id);
CREATE INDEX ix_project_files_project_id ON project_files USING btree (project_id);
CREATE INDEX ix_project_profile_revisions_project_id ON project_profile_revisions USING btree (project_id);
CREATE INDEX ix_projects_user_id ON projects USING btree (user_id);
CREATE INDEX ix_review_issues_open ON review_issues USING btree (project_id, state);
CREATE INDEX ix_rough_norms_work_code ON rough_norms USING btree (work_code);
CREATE INDEX ix_takeoff_items_work ON takeoff_items USING btree (takeoff_id, work_code);
CREATE INDEX ix_takeoff_results_kind ON takeoff_results USING btree (project_id, kind, state);
CREATE INDEX ix_takeoff_results_project_id ON takeoff_results USING btree (project_id);
CREATE INDEX ix_wall_systems_material_id ON wall_systems USING btree (material_id);
CREATE UNIQUE INDEX uq_meas_one_selected ON element_measurements USING btree (element_id, quantity_kind, variant) WHERE selected;
CREATE UNIQUE INDEX uq_price_records_dedup ON price_records USING btree (material_id, COALESCE(supplier_id, ''::character varying), date, quantity, source);
CREATE UNIQUE INDEX uq_scenarios_one_selected ON material_scenarios USING btree (takeoff_id) WHERE is_selected;
ALTER TABLE ONLY audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE ONLY building_elements
    ADD CONSTRAINT building_elements_first_seen_takeoff_id_fkey FOREIGN KEY (first_seen_takeoff_id) REFERENCES takeoff_results(takeoff_id) ON DELETE SET NULL;
ALTER TABLE ONLY building_elements
    ADD CONSTRAINT building_elements_level_id_fkey FOREIGN KEY (level_id) REFERENCES building_levels(level_id) ON DELETE SET NULL;
ALTER TABLE ONLY building_elements
    ADD CONSTRAINT building_elements_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY building_levels
    ADD CONSTRAINT building_levels_height_evidence_id_fkey FOREIGN KEY (height_evidence_id) REFERENCES evidence_sources(evidence_id) ON DELETE SET NULL;
ALTER TABLE ONLY building_levels
    ADD CONSTRAINT building_levels_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY drawing_entities
    ADD CONSTRAINT drawing_entities_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES project_document_revisions(revision_id) ON DELETE CASCADE;
ALTER TABLE ONLY drawing_entities
    ADD CONSTRAINT drawing_entities_view_id_fkey FOREIGN KEY (view_id) REFERENCES drawing_views(view_id) ON DELETE SET NULL;
ALTER TABLE ONLY drawing_views
    ADD CONSTRAINT drawing_views_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY drawing_views
    ADD CONSTRAINT drawing_views_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES project_document_revisions(revision_id) ON DELETE CASCADE;
ALTER TABLE ONLY element_measurements
    ADD CONSTRAINT element_measurements_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE ONLY element_measurements
    ADD CONSTRAINT element_measurements_element_id_fkey FOREIGN KEY (element_id) REFERENCES building_elements(element_id) ON DELETE CASCADE;
ALTER TABLE ONLY element_measurements
    ADD CONSTRAINT element_measurements_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES element_measurements(measurement_id) ON DELETE SET NULL;
ALTER TABLE ONLY element_occurrences
    ADD CONSTRAINT element_occurrences_element_id_fkey FOREIGN KEY (element_id) REFERENCES building_elements(element_id) ON DELETE CASCADE;
ALTER TABLE ONLY element_occurrences
    ADD CONSTRAINT element_occurrences_view_id_fkey FOREIGN KEY (view_id) REFERENCES drawing_views(view_id) ON DELETE CASCADE;
ALTER TABLE ONLY element_relations
    ADD CONSTRAINT element_relations_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES evidence_sources(evidence_id) ON DELETE SET NULL;
ALTER TABLE ONLY element_relations
    ADD CONSTRAINT element_relations_from_element_id_fkey FOREIGN KEY (from_element_id) REFERENCES building_elements(element_id) ON DELETE CASCADE;
ALTER TABLE ONLY element_relations
    ADD CONSTRAINT element_relations_to_element_id_fkey FOREIGN KEY (to_element_id) REFERENCES building_elements(element_id) ON DELETE CASCADE;
ALTER TABLE ONLY evidence_sources
    ADD CONSTRAINT evidence_sources_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY evidence_sources
    ADD CONSTRAINT evidence_sources_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES project_document_revisions(revision_id) ON DELETE SET NULL;
ALTER TABLE ONLY evidence_sources
    ADD CONSTRAINT evidence_sources_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE ONLY evidence_sources
    ADD CONSTRAINT evidence_sources_view_id_fkey FOREIGN KEY (view_id) REFERENCES drawing_views(view_id) ON DELETE SET NULL;
ALTER TABLE ONLY material_notes
    ADD CONSTRAINT fk_material_notes_material FOREIGN KEY (material_id) REFERENCES materials(material_id) NOT VALID;
ALTER TABLE ONLY material_aliases
    ADD CONSTRAINT material_aliases_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_element_id_fkey FOREIGN KEY (element_id) REFERENCES building_elements(element_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES evidence_sources(evidence_id) ON DELETE SET NULL;
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_item_id_fkey FOREIGN KEY (item_id) REFERENCES takeoff_items(item_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE RESTRICT;
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES material_scenarios(scenario_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_assignments
    ADD CONSTRAINT material_assignments_wall_system_id_fkey FOREIGN KEY (wall_system_id) REFERENCES wall_systems(wall_system_id) ON DELETE RESTRICT;
ALTER TABLE ONLY material_relations
    ADD CONSTRAINT material_relations_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_relations
    ADD CONSTRAINT material_relations_related_material_id_fkey FOREIGN KEY (related_material_id) REFERENCES materials(material_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_requirements
    ADD CONSTRAINT material_requirements_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE RESTRICT;
ALTER TABLE ONLY material_requirements
    ADD CONSTRAINT material_requirements_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES material_scenarios(scenario_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_scenarios
    ADD CONSTRAINT material_scenarios_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE ONLY material_scenarios
    ADD CONSTRAINT material_scenarios_run_id_fkey FOREIGN KEY (run_id) REFERENCES optimization_runs(run_id) ON DELETE SET NULL;
ALTER TABLE ONLY material_scenarios
    ADD CONSTRAINT material_scenarios_takeoff_id_fkey FOREIGN KEY (takeoff_id) REFERENCES takeoff_results(takeoff_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_standards
    ADD CONSTRAINT material_standards_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE;
ALTER TABLE ONLY material_standards
    ADD CONSTRAINT material_standards_standard_id_fkey FOREIGN KEY (standard_id) REFERENCES standards(standard_id) ON DELETE CASCADE;
ALTER TABLE ONLY materials
    ADD CONSTRAINT materials_family_fkey FOREIGN KEY (family) REFERENCES material_families(family_id);
ALTER TABLE ONLY materials
    ADD CONSTRAINT materials_group_fkey FOREIGN KEY ("group") REFERENCES material_groups(group_id);
ALTER TABLE ONLY measurement_evidence
    ADD CONSTRAINT measurement_evidence_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES evidence_sources(evidence_id) ON DELETE CASCADE;
ALTER TABLE ONLY measurement_evidence
    ADD CONSTRAINT measurement_evidence_measurement_id_fkey FOREIGN KEY (measurement_id) REFERENCES element_measurements(measurement_id) ON DELETE CASCADE;
ALTER TABLE ONLY optimization_runs
    ADD CONSTRAINT optimization_runs_model_version_fkey FOREIGN KEY (model_version) REFERENCES model_versions(version) ON DELETE SET NULL;
ALTER TABLE ONLY optimization_runs
    ADD CONSTRAINT optimization_runs_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY optimization_runs
    ADD CONSTRAINT optimization_runs_takeoff_id_fkey FOREIGN KEY (takeoff_id) REFERENCES takeoff_results(takeoff_id) ON DELETE SET NULL;
ALTER TABLE ONLY price_records
    ADD CONSTRAINT price_records_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id);
ALTER TABLE ONLY price_records
    ADD CONSTRAINT price_records_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id);
ALTER TABLE ONLY project_document_revisions
    ADD CONSTRAINT project_document_revisions_file_id_fkey FOREIGN KEY (file_id) REFERENCES project_files(file_id) ON DELETE CASCADE;
ALTER TABLE ONLY project_files
    ADD CONSTRAINT project_files_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY project_profile_revisions
    ADD CONSTRAINT project_profile_revisions_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
ALTER TABLE ONLY requirement_sources
    ADD CONSTRAINT requirement_sources_item_id_fkey FOREIGN KEY (item_id) REFERENCES takeoff_items(item_id) ON DELETE CASCADE;
ALTER TABLE ONLY requirement_sources
    ADD CONSTRAINT requirement_sources_requirement_id_fkey FOREIGN KEY (requirement_id) REFERENCES material_requirements(requirement_id) ON DELETE CASCADE;
ALTER TABLE ONLY requirement_sources
    ADD CONSTRAINT requirement_sources_rough_norm_id_fkey FOREIGN KEY (rough_norm_id) REFERENCES rough_norms(id) ON DELETE SET NULL;
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_element_id_fkey FOREIGN KEY (element_id) REFERENCES building_elements(element_id) ON DELETE SET NULL;
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_measurement_id_fkey FOREIGN KEY (measurement_id) REFERENCES element_measurements(measurement_id) ON DELETE SET NULL;
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_takeoff_id_fkey FOREIGN KEY (takeoff_id) REFERENCES takeoff_results(takeoff_id) ON DELETE SET NULL;
ALTER TABLE ONLY review_issues
    ADD CONSTRAINT review_issues_view_id_fkey FOREIGN KEY (view_id) REFERENCES drawing_views(view_id) ON DELETE SET NULL;
ALTER TABLE ONLY supplier_materials
    ADD CONSTRAINT supplier_materials_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE;
ALTER TABLE ONLY supplier_materials
    ADD CONSTRAINT supplier_materials_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE CASCADE;
ALTER TABLE ONLY takeoff_item_inputs
    ADD CONSTRAINT takeoff_item_inputs_item_id_fkey FOREIGN KEY (item_id) REFERENCES takeoff_items(item_id) ON DELETE CASCADE;
ALTER TABLE ONLY takeoff_item_inputs
    ADD CONSTRAINT takeoff_item_inputs_measurement_id_fkey FOREIGN KEY (measurement_id) REFERENCES element_measurements(measurement_id) ON DELETE SET NULL;
ALTER TABLE ONLY takeoff_item_inputs
    ADD CONSTRAINT takeoff_item_inputs_rough_norm_id_fkey FOREIGN KEY (rough_norm_id) REFERENCES rough_norms(id) ON DELETE SET NULL;
ALTER TABLE ONLY takeoff_items
    ADD CONSTRAINT takeoff_items_element_id_fkey FOREIGN KEY (element_id) REFERENCES building_elements(element_id) ON DELETE SET NULL;
ALTER TABLE ONLY takeoff_items
    ADD CONSTRAINT takeoff_items_level_id_fkey FOREIGN KEY (level_id) REFERENCES building_levels(level_id) ON DELETE SET NULL;
ALTER TABLE ONLY takeoff_items
    ADD CONSTRAINT takeoff_items_takeoff_id_fkey FOREIGN KEY (takeoff_id) REFERENCES takeoff_results(takeoff_id) ON DELETE CASCADE;
ALTER TABLE ONLY takeoff_items
    ADD CONSTRAINT takeoff_items_wall_system_id_fkey FOREIGN KEY (wall_system_id) REFERENCES wall_systems(wall_system_id) ON DELETE SET NULL;
ALTER TABLE ONLY takeoff_results
    ADD CONSTRAINT takeoff_results_file_id_fkey FOREIGN KEY (file_id) REFERENCES project_files(file_id) ON DELETE SET NULL;
ALTER TABLE ONLY takeoff_results
    ADD CONSTRAINT takeoff_results_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;
ALTER TABLE ONLY takeoff_results
    ADD CONSTRAINT takeoff_results_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES takeoff_results(takeoff_id) ON DELETE SET NULL;
ALTER TABLE ONLY view_levels
    ADD CONSTRAINT view_levels_level_id_fkey FOREIGN KEY (level_id) REFERENCES building_levels(level_id) ON DELETE CASCADE;
ALTER TABLE ONLY view_levels
    ADD CONSTRAINT view_levels_view_id_fkey FOREIGN KEY (view_id) REFERENCES drawing_views(view_id) ON DELETE CASCADE;
ALTER TABLE ONLY wall_systems
    ADD CONSTRAINT wall_systems_material_id_fkey FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE;
ALTER TABLE ONLY wall_systems
    ADD CONSTRAINT wall_systems_mortar_material_id_fkey FOREIGN KEY (mortar_material_id) REFERENCES materials(material_id);
\unrestrict whjdxsK6tTe14PWtxRZGwmJBHvjExLqKBTQcJlqn22yMprCugonGYQFbBvw9S6l
