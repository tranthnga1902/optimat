-- OptiMat AI: đúng 20 bảng vật lý; các tên cũ là view tương thích.


CREATE TABLE cost_parameters (
	parameter_id BIGSERIAL NOT NULL, 
	kind VARCHAR(24) NOT NULL, 
	record_key TEXT NOT NULL, 
	payload JSONB NOT NULL, 
	PRIMARY KEY (parameter_id), 
	CONSTRAINT uq_cost_record UNIQUE (kind, record_key), 
	CONSTRAINT ck_cost_payload CHECK (kind IN ('vehicles','labor_rates') AND jsonb_typeof(payload) = 'object')
)

;


CREATE TABLE materials (
	material_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	"group" VARCHAR(64) NOT NULL, 
	thickness_mm FLOAT, 
	unit VARCHAR(16) NOT NULL, 
	qty_per_m2 FLOAT, 
	weight_kg_per_m2 FLOAT, 
	lambda_w_mk FLOAT, 
	labor_days_per_m2 FLOAT, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	subgroup VARCHAR(128), 
	family VARCHAR(32), 
	usage_text VARCHAR(255), 
	usage_role VARCHAR(128), 
	tier INTEGER, 
	purchase_unit VARCHAR(32), 
	unit_conversion FLOAT, 
	length_mm FLOAT, 
	width_mm FLOAT, 
	height_mm FLOAT, 
	price_priority VARCHAR(4), 
	needs_lambda BOOLEAN, 
	lambda_source VARCHAR(255), 
	unit_weight_kg FLOAT, 
	weight_source VARCHAR(255), 
	transport_volume_m3 FLOAT, 
	waste_pct FLOAT, 
	waste_source VARCHAR(255), 
	standards_text TEXT, 
	reference_brands TEXT, 
	tech_notes TEXT, 
	data_note TEXT, 
	raw_class VARCHAR(32), 
	catalog_metadata JSONB DEFAULT '{}' NOT NULL, 
	PRIMARY KEY (material_id), 
	CONSTRAINT ck_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC'))
)

;


CREATE TABLE rule_sets (
	set_id BIGSERIAL NOT NULL, 
	kind VARCHAR(48) NOT NULL, 
	record_key TEXT NOT NULL, 
	payload JSONB NOT NULL, 
	version INTEGER DEFAULT '1' NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (set_id), 
	CONSTRAINT uq_rule_record UNIQUE (kind, record_key), 
	CONSTRAINT ck_rule_payload CHECK (jsonb_typeof(payload) = 'object' AND version > 0)
)

;


CREATE TABLE suppliers (
	supplier_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	province VARCHAR(64) NOT NULL, 
	lat FLOAT, 
	lon FLOAT, 
	lead_time_days FLOAT, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	dealer_type VARCHAR(64), 
	brands TEXT, 
	address VARCHAR(512), 
	ward VARCHAR(128), 
	district VARCHAR(128), 
	maps_url VARCHAR(1024), 
	phone VARCHAR(64), 
	zalo VARCHAR(64), 
	email VARCHAR(255), 
	website VARCHAR(1024), 
	facebook VARCHAR(1024), 
	tax_code VARCHAR(32), 
	opening_hours VARCHAR(255), 
	delivers BOOLEAN, 
	delivery_radius_km FLOAT, 
	max_truck_ton FLOAT, 
	min_order VARCHAR(255), 
	vat_invoice BOOLEAN, 
	payment VARCHAR(255), 
	price_public VARCHAR(8), 
	price_page_url VARCHAR(1024), 
	verified BOOLEAN, 
	collected_at DATE, 
	collected_by VARCHAR(128), 
	source VARCHAR(1024), 
	note TEXT, 
	linked_supplier_id VARCHAR(64), 
	PRIMARY KEY (supplier_id), 
	CONSTRAINT ck_suppliers_price_public CHECK (price_public IS NULL OR price_public IN ('YES', 'NO', 'PARTIAL')), 
	CONSTRAINT ck_suppliers_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_suppliers_latlon CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180), 
	FOREIGN KEY(linked_supplier_id) REFERENCES suppliers (supplier_id) ON DELETE SET NULL
)

;


CREATE TABLE users (
	user_id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255) DEFAULT '' NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(16) DEFAULT 'user' NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT ck_users_role CHECK (role IN ('admin', 'user')), 
	CONSTRAINT users_email_key UNIQUE (email)
)

;


CREATE TABLE work_norms (
	id SERIAL NOT NULL, 
	work_code VARCHAR(32) NOT NULL, 
	variant VARCHAR(32), 
	material_id VARCHAR(64), 
	material_name VARCHAR(255), 
	qty FLOAT, 
	qty_unit VARCHAR(64), 
	qty_min FLOAT, 
	qty_max FLOAT, 
	muc_xac_nhan VARCHAR(16), 
	ngay_tra VARCHAR(10), 
	norm_code VARCHAR(64), 
	source VARCHAR(255), 
	note TEXT, 
	PRIMARY KEY (id)
)

;

CREATE INDEX ix_rough_norms_work_code ON work_norms (work_code);


CREATE TABLE audit_logs (
	log_id BIGSERIAL NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(64) NOT NULL, 
	detail JSONB DEFAULT '{}' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE SET NULL
)

;

CREATE INDEX ix_audit_logs_action ON audit_logs (action);


CREATE TABLE material_relations (
	id SERIAL NOT NULL, 
	material_id VARCHAR(64) NOT NULL, 
	relation_type VARCHAR(16) NOT NULL, 
	related_material_id VARCHAR(64) NOT NULL, 
	quantity FLOAT, 
	quantity_unit VARCHAR(64), 
	source VARCHAR(255), 
	note TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT material_relations_material_id_related_material_id_rela_f54c UNIQUE (material_id, related_material_id, relation_type), 
	CONSTRAINT ck_material_relations_type CHECK (relation_type IN ('REQUIRES', 'COMPOSED_OF')), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE, 
	FOREIGN KEY(related_material_id) REFERENCES materials (material_id) ON DELETE CASCADE
)

;

CREATE INDEX ix_material_relations_material_id ON material_relations (material_id);


CREATE TABLE price_records (
	id BIGSERIAL NOT NULL, 
	date DATE NOT NULL, 
	material_id VARCHAR(64) NOT NULL, 
	supplier_id VARCHAR(64), 
	province VARCHAR(64) NOT NULL, 
	quantity FLOAT NOT NULL, 
	unit VARCHAR(16) NOT NULL, 
	unit_price FLOAT NOT NULL, 
	vat_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL, 
	transport_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL, 
	source VARCHAR(1024) DEFAULT '' NOT NULL, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	price_level VARCHAR(16) DEFAULT 'DEALER' NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_price_records_price_level CHECK (price_level IN ('DEALER', 'QUOTE', 'BULLETIN')), 
	CONSTRAINT ck_price_records_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')), 
	CONSTRAINT ck_price_records_positive CHECK (unit_price > 0), 
	CONSTRAINT ck_price_records_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_price_records_supplier CHECK (supplier_id IS NOT NULL OR price_level = 'BULLETIN'), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (supplier_id)
)

;

CREATE INDEX ix_price_records_lookup ON price_records (material_id, supplier_id, date);

CREATE UNIQUE INDEX uq_price_records_dedup ON price_records (material_id, COALESCE(supplier_id, ''), date, quantity, source);


CREATE TABLE projects (
	project_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	address VARCHAR(512) DEFAULT '' NOT NULL, 
	site_lat FLOAT, 
	site_lon FLOAT, 
	floor_height_mm FLOAT, 
	door_width_mm FLOAT, 
	door_height_mm FLOAT, 
	window_width_mm FLOAT, 
	window_height_mm FLOAT, 
	budget FLOAT, 
	deadline_days FLOAT, 
	max_vehicle_ton FLOAT, 
	excluded_materials JSONB DEFAULT '[]' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	profile_revisions JSONB DEFAULT '[]' NOT NULL, 
	PRIMARY KEY (project_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
)

;

CREATE INDEX ix_projects_user_id ON projects (user_id);


CREATE TABLE supplier_materials (
	id SERIAL NOT NULL, 
	supplier_id VARCHAR(64) NOT NULL, 
	material_id VARCHAR(64) NOT NULL, 
	base_price FLOAT, 
	product_url VARCHAR(1024), 
	collected_at DATE NOT NULL, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	dealer_product_name VARCHAR(255), 
	brand VARCHAR(128), 
	sale_unit VARCHAR(32), 
	unit_conversion FLOAT, 
	price_level VARCHAR(16), 
	price_date DATE, 
	vat_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL, 
	transport_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL, 
	in_stock BOOLEAN, 
	note TEXT, 
	quote_reference VARCHAR(1024), 
	valid_until DATE, 
	lead_time_days FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_supplier_materials_price_level CHECK (price_level IS NULL OR price_level IN ('DEALER', 'QUOTE')), 
	CONSTRAINT ck_supplier_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_supplier_materials_price_complete CHECK (base_price IS NULL OR (base_price > 0 AND price_level IS NOT NULL AND price_date IS NOT NULL)), 
	CONSTRAINT supplier_materials_supplier_id_material_id_key UNIQUE (supplier_id, material_id), 
	CONSTRAINT ck_supplier_materials_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (supplier_id) ON DELETE CASCADE, 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE
)

;


CREATE TABLE wall_systems (
	wall_system_id VARCHAR(64) NOT NULL, 
	material_id VARCHAR(64) NOT NULL, 
	wall_thickness_mm FLOAT, 
	detect_class VARCHAR(8), 
	role VARCHAR(16), 
	masonry_thickness_mm FLOAT, 
	norm_code VARCHAR(32), 
	units_per_m3 FLOAT, 
	mortar_m3_per_m3 FLOAT, 
	labor_day_per_m3 FLOAT, 
	unit_factor FLOAT, 
	mortar_material_id VARCHAR(64), 
	mortar_density FLOAT, 
	r0_reference FLOAT, 
	norm_source VARCHAR(255), 
	note TEXT, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	PRIMARY KEY (wall_system_id), 
	CONSTRAINT ck_wall_systems_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE, 
	FOREIGN KEY(mortar_material_id) REFERENCES materials (material_id)
)

;

CREATE INDEX ix_wall_systems_material_id ON wall_systems (material_id);


CREATE TABLE analysis_runs (
	takeoff_id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	file_id INTEGER, 
	result JSONB NOT NULL, 
	layer_overrides JSONB DEFAULT '{}' NOT NULL, 
	confirmed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	kind VARCHAR(32) DEFAULT 'takeoff' NOT NULL, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	input_snapshot JSONB DEFAULT '{}' NOT NULL, 
	schema_version INTEGER DEFAULT '1' NOT NULL, 
	result_sha256 VARCHAR(64), 
	PRIMARY KEY (takeoff_id), 
	FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE, 
	CONSTRAINT uq_analysis_project_id UNIQUE (project_id, takeoff_id), 
	CONSTRAINT ck_analysis_data_kind CHECK (data_kind IN ('ACTUAL','SAMPLE','SYNTHETIC')), 
	CONSTRAINT ck_analysis_synthetic CHECK (kind <> 'synthetic_housing' OR data_kind = 'SYNTHETIC')
)

;

CREATE INDEX ix_takeoff_results_project_id ON analysis_runs (project_id);


CREATE TABLE document_revisions (
	document_id BIGSERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	record_type VARCHAR(12) NOT NULL, 
	file_id INTEGER NOT NULL, 
	revision_id BIGINT, 
	version INTEGER, 
	filename VARCHAR(255) NOT NULL, 
	format VARCHAR(16) NOT NULL, 
	stored_path TEXT NOT NULL, 
	sha256 VARCHAR(64), 
	size_bytes BIGINT, 
	role VARCHAR(16), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (document_id), 
	CONSTRAINT uq_document_revision_id UNIQUE (revision_id), 
	CONSTRAINT uq_document_file_version UNIQUE (file_id, version), 
	CONSTRAINT ck_document_record_type CHECK (record_type IN ('file','revision')), 
	CONSTRAINT ck_document_revision_required CHECK (record_type <> 'revision' OR (revision_id IS NOT NULL AND version IS NOT NULL AND version > 0 AND sha256 IS NOT NULL AND size_bytes IS NOT NULL AND size_bytes > 0 AND role IS NOT NULL AND role IN ('KT','KC','HO_SO','TIEN_LUONG','THAM_KHAO'))), 
	FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE
)

;

CREATE INDEX ix_document_revisions_project_id ON document_revisions (project_id);

CREATE UNIQUE INDEX uq_document_file_record ON document_revisions (file_id) WHERE record_type = 'file';


CREATE TABLE building_elements (
	element_id BIGSERIAL NOT NULL, 
	analysis_id INTEGER NOT NULL, 
	element_key VARCHAR(255) NOT NULL, 
	kind VARCHAR(32) NOT NULL, 
	level_code VARCHAR(128), 
	geometry JSONB DEFAULT '{}' NOT NULL, 
	occurrences JSONB DEFAULT '[]' NOT NULL, 
	relations JSONB DEFAULT '[]' NOT NULL, 
	payload JSONB DEFAULT '{}' NOT NULL, 
	PRIMARY KEY (element_id), 
	CONSTRAINT uq_element_analysis_key UNIQUE (analysis_id, element_key), 
	FOREIGN KEY(analysis_id) REFERENCES analysis_runs (takeoff_id) ON DELETE CASCADE
)

;

CREATE INDEX ix_building_elements_analysis_id ON building_elements (analysis_id);


CREATE TABLE evidence_sources (
	evidence_id BIGSERIAL NOT NULL, 
	analysis_id INTEGER NOT NULL, 
	kind VARCHAR(32) NOT NULL, 
	revision_id BIGINT, 
	source_ref JSONB DEFAULT '{}' NOT NULL, 
	raw_content JSONB NOT NULL, 
	created_by INTEGER, 
	PRIMARY KEY (evidence_id), 
	FOREIGN KEY(analysis_id) REFERENCES analysis_runs (takeoff_id) ON DELETE CASCADE, 
	FOREIGN KEY(revision_id) REFERENCES document_revisions (revision_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE SET NULL
)

;

CREATE INDEX ix_evidence_sources_analysis_id ON evidence_sources (analysis_id);


CREATE TABLE optimization_runs (
	run_id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	takeoff_id INTEGER, 
	model_version VARCHAR(32), 
	method VARCHAR(16) NOT NULL, 
	config JSONB DEFAULT '{}' NOT NULL, 
	solutions JSONB NOT NULL, 
	chosen_index INTEGER, 
	price_snapshot_date DATE, 
	llm_model VARCHAR(64), 
	tool_calls JSONB DEFAULT '[]' NOT NULL, 
	excluded_materials JSONB DEFAULT '[]' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (run_id), 
	FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE, 
	FOREIGN KEY(takeoff_id) REFERENCES analysis_runs (takeoff_id) ON DELETE SET NULL
)

;

CREATE INDEX ix_optimization_runs_project_id ON optimization_runs (project_id);


CREATE TABLE element_measurements (
	measurement_id BIGSERIAL NOT NULL, 
	element_id BIGINT NOT NULL, 
	property_code VARCHAR(64) NOT NULL, 
	value NUMERIC(20, 6), 
	unit VARCHAR(24) NOT NULL, 
	status VARCHAR(1) NOT NULL, 
	selected BOOLEAN DEFAULT 'false' NOT NULL, 
	method VARCHAR(24) NOT NULL, 
	evidence_ids JSONB DEFAULT '[]' NOT NULL, 
	PRIMARY KEY (measurement_id), 
	CONSTRAINT ck_measurement_status CHECK (status IN ('A','B','C','D') AND (value IS NOT NULL OR status = 'D')), 
	CONSTRAINT ck_measurement_selected CHECK (NOT selected OR value IS NOT NULL), 
	CONSTRAINT ck_measurement_user CHECK (method <> 'user_input' OR status IN ('C','D')), 
	FOREIGN KEY(element_id) REFERENCES building_elements (element_id) ON DELETE CASCADE
)

;

CREATE INDEX ix_element_measurements_element_id ON element_measurements (element_id);

CREATE UNIQUE INDEX uq_measurement_selected ON element_measurements (element_id, property_code) WHERE selected;


CREATE TABLE material_scenarios (
	scenario_id BIGSERIAL NOT NULL, 
	analysis_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	origin VARCHAR(24) NOT NULL, 
	selected BOOLEAN DEFAULT 'false' NOT NULL, 
	assignments JSONB DEFAULT '[]' NOT NULL, 
	requirements JSONB DEFAULT '[]' NOT NULL, 
	catalog_snapshot JSONB DEFAULT '{}' NOT NULL, 
	run_id INTEGER, 
	PRIMARY KEY (scenario_id), 
	CONSTRAINT ck_scenario_origin CHECK (origin IN ('design','user','proposed','optimized')), 
	CONSTRAINT ck_scenario_run CHECK (origin <> 'optimized' OR run_id IS NOT NULL), 
	FOREIGN KEY(analysis_id) REFERENCES analysis_runs (takeoff_id) ON DELETE CASCADE, 
	FOREIGN KEY(run_id) REFERENCES optimization_runs (run_id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_material_scenarios_analysis_id ON material_scenarios (analysis_id);

CREATE UNIQUE INDEX uq_scenario_selected ON material_scenarios (analysis_id) WHERE selected;


CREATE TABLE takeoff_items (
	item_id BIGSERIAL NOT NULL, 
	analysis_id INTEGER NOT NULL, 
	seq INTEGER NOT NULL, 
	work_code VARCHAR(64) NOT NULL, 
	element_id BIGINT, 
	unit VARCHAR(24) NOT NULL, 
	quantity NUMERIC(20, 6), 
	known_part NUMERIC(20, 6), 
	status VARCHAR(1) NOT NULL, 
	formula TEXT DEFAULT '' NOT NULL, 
	input_snapshot JSONB DEFAULT '{}' NOT NULL, 
	payload JSONB NOT NULL, 
	PRIMARY KEY (item_id), 
	CONSTRAINT uq_takeoff_item_seq UNIQUE (analysis_id, seq), 
	CONSTRAINT ck_item_status CHECK (status IN ('A','B','C','D') AND (quantity IS NOT NULL OR status = 'D')), 
	FOREIGN KEY(analysis_id) REFERENCES analysis_runs (takeoff_id) ON DELETE CASCADE, 
	FOREIGN KEY(element_id) REFERENCES building_elements (element_id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_takeoff_items_analysis_id ON takeoff_items (analysis_id);

CREATE VIEW "rough_norms" AS SELECT "id","work_code","variant","material_id","material_name","qty","qty_unit","qty_min","qty_max","muc_xac_nhan","ngay_tra","norm_code","source","note" FROM "work_norms";

CREATE VIEW "takeoff_results" AS SELECT "takeoff_id","project_id","file_id","result","layer_overrides","confirmed_at","created_at" FROM "analysis_runs";

CREATE VIEW "material_groups" AS SELECT (payload ->> 'group_id')::VARCHAR(64) AS "group_id", (payload ->> 'sort_order')::INTEGER AS "sort_order", (payload ->> 'name')::VARCHAR(255) AS "name", (payload ->> 'description')::TEXT AS "description" FROM rule_sets WHERE kind = 'material_groups';

ALTER VIEW "material_groups" ALTER COLUMN "description" SET DEFAULT '';

CREATE VIEW "material_families" AS SELECT (payload ->> 'family_id')::VARCHAR(32) AS "family_id", (payload ->> 'name')::VARCHAR(255) AS "name", (payload ->> 'sort_order')::INTEGER AS "sort_order", (payload ->> 'is_wall')::BOOLEAN AS "is_wall" FROM rule_sets WHERE kind = 'material_families';

ALTER VIEW "material_families" ALTER COLUMN "is_wall" SET DEFAULT 'false';

CREATE VIEW "material_aliases" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'alias')::VARCHAR(255) AS "alias", (payload ->> 'material_id')::VARCHAR(64) AS "material_id", (payload ->> 'source')::VARCHAR(255) AS "source" FROM rule_sets WHERE kind = 'material_aliases';

CREATE SEQUENCE IF NOT EXISTS "compat_material_aliases_id_seq";

ALTER VIEW "material_aliases" ALTER COLUMN "id" SET DEFAULT nextval('compat_material_aliases_id_seq');

ALTER VIEW "material_aliases" ALTER COLUMN "source" SET DEFAULT '';

CREATE VIEW "standards" AS SELECT (payload ->> 'standard_id')::INTEGER AS "standard_id", (payload ->> 'code')::VARCHAR(64) AS "code", (payload ->> 'title')::TEXT AS "title", (payload ->> 'kind')::VARCHAR(32) AS "kind", (payload ->> 'status')::VARCHAR(32) AS "status", (payload ->> 'valid_from')::DATE AS "valid_from", (payload ->> 'valid_to')::DATE AS "valid_to", (payload ->> 'source_url')::VARCHAR(1024) AS "source_url" FROM rule_sets WHERE kind = 'standards';

CREATE SEQUENCE IF NOT EXISTS "compat_standards_standard_id_seq";

ALTER VIEW "standards" ALTER COLUMN "standard_id" SET DEFAULT nextval('compat_standards_standard_id_seq');

ALTER VIEW "standards" ALTER COLUMN "kind" SET DEFAULT '';

ALTER VIEW "standards" ALTER COLUMN "status" SET DEFAULT 'UNKNOWN';

ALTER VIEW "standards" ALTER COLUMN "source_url" SET DEFAULT '';

CREATE VIEW "material_standards" AS SELECT (payload ->> 'material_id')::VARCHAR(64) AS "material_id", (payload ->> 'standard_id')::INTEGER AS "standard_id", (payload ->> 'note')::VARCHAR(255) AS "note" FROM rule_sets WHERE kind = 'material_standards';

CREATE SEQUENCE IF NOT EXISTS "compat_material_standards_standard_id_seq";

ALTER VIEW "material_standards" ALTER COLUMN "standard_id" SET DEFAULT nextval('compat_material_standards_standard_id_seq');

ALTER VIEW "material_standards" ALTER COLUMN "note" SET DEFAULT '';

CREATE VIEW "material_rules" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'rule_id')::VARCHAR(32) AS "rule_id", (payload ->> 'signal')::VARCHAR(16) AS "signal", (payload ->> 'pattern')::VARCHAR(255) AS "pattern", (payload ->> 'target')::VARCHAR(255) AS "target", (payload ->> 'element')::VARCHAR(32) AS "element", (payload ->> 'width_mm')::FLOAT AS "width_mm", (payload ->> 'height_mm')::FLOAT AS "height_mm", (payload ->> 'priority')::INTEGER AS "priority", (payload ->> 'note')::TEXT AS "note" FROM rule_sets WHERE kind = 'material_rules';

CREATE SEQUENCE IF NOT EXISTS "compat_material_rules_id_seq";

ALTER VIEW "material_rules" ALTER COLUMN "id" SET DEFAULT nextval('compat_material_rules_id_seq');

ALTER VIEW "material_rules" ALTER COLUMN "priority" SET DEFAULT '0';

CREATE VIEW "room_rules" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'rule_id')::VARCHAR(32) AS "rule_id", (payload ->> 'pattern')::VARCHAR(255) AS "pattern", (payload ->> 'kind')::VARCHAR(16) AS "kind", (payload ->> 'note')::TEXT AS "note" FROM rule_sets WHERE kind = 'room_rules';

CREATE SEQUENCE IF NOT EXISTS "compat_room_rules_id_seq";

ALTER VIEW "room_rules" ALTER COLUMN "id" SET DEFAULT nextval('compat_room_rules_id_seq');

CREATE VIEW "material_notes" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'rule_id')::VARCHAR(32) AS "rule_id", (payload ->> 'pattern')::VARCHAR(255) AS "pattern", (payload ->> 'material_id')::VARCHAR(32) AS "material_id", (payload ->> 'ten')::VARCHAR(255) AS "ten", (payload ->> 'nguon')::VARCHAR(32) AS "nguon", (payload ->> 'kiem_chung')::VARCHAR(32) AS "kiem_chung", (payload ->> 'ghi_chu')::TEXT AS "ghi_chu" FROM rule_sets WHERE kind = 'material_notes';

CREATE SEQUENCE IF NOT EXISTS "compat_material_notes_id_seq";

ALTER VIEW "material_notes" ALTER COLUMN "id" SET DEFAULT nextval('compat_material_notes_id_seq');

CREATE VIEW "drawing_concepts" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'ma')::VARCHAR(16) AS "ma", (payload ->> 'khai_niem')::VARCHAR(64) AS "khai_niem", (payload ->> 'qu')::VARCHAR(16) AS "qu", (payload ->> 'tin_hieu')::VARCHAR(16) AS "tin_hieu", (payload ->> 'mau')::VARCHAR(128) AS "mau", (payload ->> 'vai_tro')::VARCHAR(16) AS "vai_tro", (payload ->> 'rong_mm')::FLOAT AS "rong_mm", (payload ->> 'cao_mm')::FLOAT AS "cao_mm", (payload ->> 'ghi_chu')::TEXT AS "ghi_chu" FROM rule_sets WHERE kind = 'drawing_concepts';

CREATE SEQUENCE IF NOT EXISTS "compat_drawing_concepts_id_seq";

ALTER VIEW "drawing_concepts" ALTER COLUMN "id" SET DEFAULT nextval('compat_drawing_concepts_id_seq');

CREATE VIEW "convention_clauses" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'ma')::VARCHAR(16) AS "ma", (payload ->> 'nhom')::VARCHAR(64) AS "nhom", (payload ->> 'dieu_khoan')::TEXT AS "dieu_khoan", (payload ->> 'muc')::VARCHAR(1) AS "muc", (payload ->> 'cach_kiem')::TEXT AS "cach_kiem" FROM rule_sets WHERE kind = 'convention_clauses';

CREATE SEQUENCE IF NOT EXISTS "compat_convention_clauses_id_seq";

ALTER VIEW "convention_clauses" ALTER COLUMN "id" SET DEFAULT nextval('compat_convention_clauses_id_seq');

CREATE VIEW "model_versions" AS SELECT (payload ->> 'version')::VARCHAR(32) AS "version", (payload ->> 'target')::VARCHAR(32) AS "target", (payload ->> 'trained_at')::TIMESTAMP WITH TIME ZONE AS "trained_at", (payload ->> 'data_rows')::INTEGER AS "data_rows", (payload ->> 'contains_synthetic')::BOOLEAN AS "contains_synthetic", payload -> 'metrics' AS "metrics", (payload ->> 'file_path')::VARCHAR(1024) AS "file_path", (payload ->> 'is_active')::BOOLEAN AS "is_active" FROM rule_sets WHERE kind = 'model_versions';

ALTER VIEW "model_versions" ALTER COLUMN "trained_at" SET DEFAULT now();

ALTER VIEW "model_versions" ALTER COLUMN "contains_synthetic" SET DEFAULT 'false';

ALTER VIEW "model_versions" ALTER COLUMN "is_active" SET DEFAULT 'false';

CREATE VIEW "vehicles" AS SELECT (payload ->> 'vehicle_id')::VARCHAR(64) AS "vehicle_id", (payload ->> 'name')::VARCHAR(255) AS "name", (payload ->> 'payload_ton')::FLOAT AS "payload_ton", (payload ->> 'base_fee')::FLOAT AS "base_fee", (payload ->> 'fee_per_km')::FLOAT AS "fee_per_km", (payload ->> 'data_kind')::VARCHAR(16) AS "data_kind" FROM cost_parameters WHERE kind = 'vehicles';

ALTER VIEW "vehicles" ALTER COLUMN "data_kind" SET DEFAULT 'ACTUAL';

CREATE VIEW "labor_rates" AS SELECT (payload ->> 'id')::INTEGER AS "id", (payload ->> 'province')::VARCHAR(64) AS "province", (payload ->> 'grade')::VARCHAR(32) AS "grade", (payload ->> 'rate_per_day')::FLOAT AS "rate_per_day", (payload ->> 'valid_from')::DATE AS "valid_from", (payload ->> 'source')::VARCHAR(1024) AS "source", (payload ->> 'data_kind')::VARCHAR(16) AS "data_kind" FROM cost_parameters WHERE kind = 'labor_rates';

CREATE SEQUENCE IF NOT EXISTS "compat_labor_rates_id_seq";

ALTER VIEW "labor_rates" ALTER COLUMN "id" SET DEFAULT nextval('compat_labor_rates_id_seq');

ALTER VIEW "labor_rates" ALTER COLUMN "source" SET DEFAULT '';

ALTER VIEW "labor_rates" ALTER COLUMN "data_kind" SET DEFAULT 'ACTUAL';

CREATE OR REPLACE FUNCTION compat_validate_material_groups(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "material_groups"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"material_groups", body);
  IF r."group_id" IS NULL THEN RAISE EXCEPTION 'Cột material_groups.group_id không được trống' USING ERRCODE='23502'; END IF; IF r."sort_order" IS NULL THEN RAISE EXCEPTION 'Cột material_groups.sort_order không được trống' USING ERRCODE='23502'; END IF; IF r."name" IS NULL THEN RAISE EXCEPTION 'Cột material_groups.name không được trống' USING ERRCODE='23502'; END IF; IF r."description" IS NULL THEN RAISE EXCEPTION 'Cột material_groups.description không được trống' USING ERRCODE='23502'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_material_groups() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='material_groups' AND record_key=jsonb_build_array(OLD."group_id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."group_id") IS DISTINCT FROM jsonb_build_array(OLD."group_id") THEN
      RAISE EXCEPTION 'Không đổi khóa của material_groups' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='material_groups' AND record_key=jsonb_build_array(OLD."group_id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('material_groups',jsonb_build_array(NEW."group_id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "material_groups"
FOR EACH ROW EXECUTE FUNCTION compat_write_material_groups();

CREATE OR REPLACE FUNCTION compat_validate_material_families(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "material_families"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"material_families", body);
  IF r."family_id" IS NULL THEN RAISE EXCEPTION 'Cột material_families.family_id không được trống' USING ERRCODE='23502'; END IF; IF r."name" IS NULL THEN RAISE EXCEPTION 'Cột material_families.name không được trống' USING ERRCODE='23502'; END IF; IF r."sort_order" IS NULL THEN RAISE EXCEPTION 'Cột material_families.sort_order không được trống' USING ERRCODE='23502'; END IF; IF r."is_wall" IS NULL THEN RAISE EXCEPTION 'Cột material_families.is_wall không được trống' USING ERRCODE='23502'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_material_families() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='material_families' AND record_key=jsonb_build_array(OLD."family_id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."family_id") IS DISTINCT FROM jsonb_build_array(OLD."family_id") THEN
      RAISE EXCEPTION 'Không đổi khóa của material_families' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='material_families' AND record_key=jsonb_build_array(OLD."family_id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('material_families',jsonb_build_array(NEW."family_id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "material_families"
FOR EACH ROW EXECUTE FUNCTION compat_write_material_families();

CREATE OR REPLACE FUNCTION compat_validate_material_aliases(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "material_aliases"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"material_aliases", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột material_aliases.id không được trống' USING ERRCODE='23502'; END IF; IF r."alias" IS NULL THEN RAISE EXCEPTION 'Cột material_aliases.alias không được trống' USING ERRCODE='23502'; END IF; IF r."material_id" IS NULL THEN RAISE EXCEPTION 'Cột material_aliases.material_id không được trống' USING ERRCODE='23502'; END IF; IF r."material_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM "materials" WHERE "material_id" = r."material_id") THEN RAISE EXCEPTION 'Tham chiếu material_aliases.material_id không hợp lệ' USING ERRCODE='23503'; END IF; IF r."source" IS NULL THEN RAISE EXCEPTION 'Cột material_aliases.source không được trống' USING ERRCODE='23502'; END IF; IF EXISTS (SELECT 1 FROM "material_aliases" v WHERE v."alias" = r."alias" AND v."material_id" = r."material_id" AND (v."id" IS DISTINCT FROM r."id")) THEN RAISE EXCEPTION 'Trùng khóa material_aliases' USING ERRCODE='23505', CONSTRAINT='material_aliases_alias_material_id_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_material_aliases() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='material_aliases' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của material_aliases' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='material_aliases' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('material_aliases',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "material_aliases"
FOR EACH ROW EXECUTE FUNCTION compat_write_material_aliases();

CREATE OR REPLACE FUNCTION compat_validate_standards(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "standards"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"standards", body);
  IF r."standard_id" IS NULL THEN RAISE EXCEPTION 'Cột standards.standard_id không được trống' USING ERRCODE='23502'; END IF; IF r."code" IS NULL THEN RAISE EXCEPTION 'Cột standards.code không được trống' USING ERRCODE='23502'; END IF; IF r."title" IS NULL THEN RAISE EXCEPTION 'Cột standards.title không được trống' USING ERRCODE='23502'; END IF; IF r."kind" IS NULL THEN RAISE EXCEPTION 'Cột standards.kind không được trống' USING ERRCODE='23502'; END IF; IF r."status" IS NULL THEN RAISE EXCEPTION 'Cột standards.status không được trống' USING ERRCODE='23502'; END IF; IF r."source_url" IS NULL THEN RAISE EXCEPTION 'Cột standards.source_url không được trống' USING ERRCODE='23502'; END IF; IF EXISTS (SELECT 1 FROM "standards" v WHERE v."code" = r."code" AND (v."standard_id" IS DISTINCT FROM r."standard_id")) THEN RAISE EXCEPTION 'Trùng khóa standards' USING ERRCODE='23505', CONSTRAINT='standards_code_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_standards() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='standards' AND record_key=jsonb_build_array(OLD."standard_id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."standard_id") IS DISTINCT FROM jsonb_build_array(OLD."standard_id") THEN
      RAISE EXCEPTION 'Không đổi khóa của standards' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='standards' AND record_key=jsonb_build_array(OLD."standard_id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('standards',jsonb_build_array(NEW."standard_id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "standards"
FOR EACH ROW EXECUTE FUNCTION compat_write_standards();

CREATE OR REPLACE FUNCTION compat_validate_material_standards(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "material_standards"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"material_standards", body);
  IF r."material_id" IS NULL THEN RAISE EXCEPTION 'Cột material_standards.material_id không được trống' USING ERRCODE='23502'; END IF; IF r."material_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM "materials" WHERE "material_id" = r."material_id") THEN RAISE EXCEPTION 'Tham chiếu material_standards.material_id không hợp lệ' USING ERRCODE='23503'; END IF; IF r."standard_id" IS NULL THEN RAISE EXCEPTION 'Cột material_standards.standard_id không được trống' USING ERRCODE='23502'; END IF; IF r."standard_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM "standards" WHERE "standard_id" = r."standard_id") THEN RAISE EXCEPTION 'Tham chiếu material_standards.standard_id không hợp lệ' USING ERRCODE='23503'; END IF; IF r."note" IS NULL THEN RAISE EXCEPTION 'Cột material_standards.note không được trống' USING ERRCODE='23502'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_material_standards() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='material_standards' AND record_key=jsonb_build_array(OLD."material_id", OLD."standard_id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."material_id", NEW."standard_id") IS DISTINCT FROM jsonb_build_array(OLD."material_id", OLD."standard_id") THEN
      RAISE EXCEPTION 'Không đổi khóa của material_standards' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='material_standards' AND record_key=jsonb_build_array(OLD."material_id", OLD."standard_id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('material_standards',jsonb_build_array(NEW."material_id", NEW."standard_id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "material_standards"
FOR EACH ROW EXECUTE FUNCTION compat_write_material_standards();

CREATE OR REPLACE FUNCTION compat_validate_material_rules(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "material_rules"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"material_rules", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột material_rules.id không được trống' USING ERRCODE='23502'; END IF; IF r."rule_id" IS NULL THEN RAISE EXCEPTION 'Cột material_rules.rule_id không được trống' USING ERRCODE='23502'; END IF; IF r."signal" IS NULL THEN RAISE EXCEPTION 'Cột material_rules.signal không được trống' USING ERRCODE='23502'; END IF; IF r."pattern" IS NULL THEN RAISE EXCEPTION 'Cột material_rules.pattern không được trống' USING ERRCODE='23502'; END IF; IF r."priority" IS NULL THEN RAISE EXCEPTION 'Cột material_rules.priority không được trống' USING ERRCODE='23502'; END IF; IF (r."signal" IN ('text', 'hatch', 'layer', 'block')) IS FALSE THEN RAISE EXCEPTION 'Vi phạm ck_material_rules_signal' USING ERRCODE='23514', CONSTRAINT='ck_material_rules_signal'; END IF; IF EXISTS (SELECT 1 FROM "material_rules" v WHERE v."rule_id" = r."rule_id" AND (v."id" IS DISTINCT FROM r."id")) THEN RAISE EXCEPTION 'Trùng khóa material_rules' USING ERRCODE='23505', CONSTRAINT='material_rules_rule_id_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_material_rules() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='material_rules' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của material_rules' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='material_rules' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('material_rules',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "material_rules"
FOR EACH ROW EXECUTE FUNCTION compat_write_material_rules();

CREATE OR REPLACE FUNCTION compat_validate_room_rules(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "room_rules"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"room_rules", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột room_rules.id không được trống' USING ERRCODE='23502'; END IF; IF r."rule_id" IS NULL THEN RAISE EXCEPTION 'Cột room_rules.rule_id không được trống' USING ERRCODE='23502'; END IF; IF r."pattern" IS NULL THEN RAISE EXCEPTION 'Cột room_rules.pattern không được trống' USING ERRCODE='23502'; END IF; IF r."kind" IS NULL THEN RAISE EXCEPTION 'Cột room_rules.kind không được trống' USING ERRCODE='23502'; END IF; IF EXISTS (SELECT 1 FROM "room_rules" v WHERE v."rule_id" = r."rule_id" AND (v."id" IS DISTINCT FROM r."id")) THEN RAISE EXCEPTION 'Trùng khóa room_rules' USING ERRCODE='23505', CONSTRAINT='room_rules_rule_id_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_room_rules() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='room_rules' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của room_rules' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='room_rules' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('room_rules',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "room_rules"
FOR EACH ROW EXECUTE FUNCTION compat_write_room_rules();

CREATE OR REPLACE FUNCTION compat_validate_material_notes(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "material_notes"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"material_notes", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột material_notes.id không được trống' USING ERRCODE='23502'; END IF; IF r."rule_id" IS NULL THEN RAISE EXCEPTION 'Cột material_notes.rule_id không được trống' USING ERRCODE='23502'; END IF; IF r."pattern" IS NULL THEN RAISE EXCEPTION 'Cột material_notes.pattern không được trống' USING ERRCODE='23502'; END IF; IF r."material_id" IS NULL THEN RAISE EXCEPTION 'Cột material_notes.material_id không được trống' USING ERRCODE='23502'; END IF; IF EXISTS (SELECT 1 FROM "material_notes" v WHERE v."rule_id" = r."rule_id" AND (v."id" IS DISTINCT FROM r."id")) THEN RAISE EXCEPTION 'Trùng khóa material_notes' USING ERRCODE='23505', CONSTRAINT='material_notes_rule_id_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_material_notes() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='material_notes' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của material_notes' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='material_notes' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('material_notes',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "material_notes"
FOR EACH ROW EXECUTE FUNCTION compat_write_material_notes();

CREATE OR REPLACE FUNCTION compat_validate_drawing_concepts(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "drawing_concepts"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"drawing_concepts", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột drawing_concepts.id không được trống' USING ERRCODE='23502'; END IF; IF r."ma" IS NULL THEN RAISE EXCEPTION 'Cột drawing_concepts.ma không được trống' USING ERRCODE='23502'; END IF; IF r."khai_niem" IS NULL THEN RAISE EXCEPTION 'Cột drawing_concepts.khai_niem không được trống' USING ERRCODE='23502'; END IF; IF r."tin_hieu" IS NULL THEN RAISE EXCEPTION 'Cột drawing_concepts.tin_hieu không được trống' USING ERRCODE='23502'; END IF; IF r."mau" IS NULL THEN RAISE EXCEPTION 'Cột drawing_concepts.mau không được trống' USING ERRCODE='23502'; END IF; IF r."vai_tro" IS NULL THEN RAISE EXCEPTION 'Cột drawing_concepts.vai_tro không được trống' USING ERRCODE='23502'; END IF; IF (r."tin_hieu" IN ('layer', 'block')) IS FALSE THEN RAISE EXCEPTION 'Vi phạm ck_drawing_concepts_signal' USING ERRCODE='23514', CONSTRAINT='ck_drawing_concepts_signal'; END IF; IF EXISTS (SELECT 1 FROM "drawing_concepts" v WHERE v."ma" = r."ma" AND (v."id" IS DISTINCT FROM r."id")) THEN RAISE EXCEPTION 'Trùng khóa drawing_concepts' USING ERRCODE='23505', CONSTRAINT='drawing_concepts_ma_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_drawing_concepts() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='drawing_concepts' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của drawing_concepts' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='drawing_concepts' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('drawing_concepts',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "drawing_concepts"
FOR EACH ROW EXECUTE FUNCTION compat_write_drawing_concepts();

CREATE OR REPLACE FUNCTION compat_validate_convention_clauses(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "convention_clauses"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"convention_clauses", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột convention_clauses.id không được trống' USING ERRCODE='23502'; END IF; IF r."ma" IS NULL THEN RAISE EXCEPTION 'Cột convention_clauses.ma không được trống' USING ERRCODE='23502'; END IF; IF r."nhom" IS NULL THEN RAISE EXCEPTION 'Cột convention_clauses.nhom không được trống' USING ERRCODE='23502'; END IF; IF r."dieu_khoan" IS NULL THEN RAISE EXCEPTION 'Cột convention_clauses.dieu_khoan không được trống' USING ERRCODE='23502'; END IF; IF r."muc" IS NULL THEN RAISE EXCEPTION 'Cột convention_clauses.muc không được trống' USING ERRCODE='23502'; END IF; IF (r."muc" IN ('B', 'K')) IS FALSE THEN RAISE EXCEPTION 'Vi phạm ck_convention_clauses_muc' USING ERRCODE='23514', CONSTRAINT='ck_convention_clauses_muc'; END IF; IF EXISTS (SELECT 1 FROM "convention_clauses" v WHERE v."ma" = r."ma" AND (v."id" IS DISTINCT FROM r."id")) THEN RAISE EXCEPTION 'Trùng khóa convention_clauses' USING ERRCODE='23505', CONSTRAINT='convention_clauses_ma_key'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_convention_clauses() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='convention_clauses' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của convention_clauses' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='convention_clauses' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('convention_clauses',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "convention_clauses"
FOR EACH ROW EXECUTE FUNCTION compat_write_convention_clauses();

CREATE OR REPLACE FUNCTION compat_validate_model_versions(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "model_versions"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"model_versions", body);
  IF r."version" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.version không được trống' USING ERRCODE='23502'; END IF; IF r."target" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.target không được trống' USING ERRCODE='23502'; END IF; IF r."trained_at" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.trained_at không được trống' USING ERRCODE='23502'; END IF; IF r."data_rows" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.data_rows không được trống' USING ERRCODE='23502'; END IF; IF r."contains_synthetic" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.contains_synthetic không được trống' USING ERRCODE='23502'; END IF; IF r."metrics" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.metrics không được trống' USING ERRCODE='23502'; END IF; IF r."file_path" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.file_path không được trống' USING ERRCODE='23502'; END IF; IF r."is_active" IS NULL THEN RAISE EXCEPTION 'Cột model_versions.is_active không được trống' USING ERRCODE='23502'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_model_versions() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM rule_sets WHERE kind='model_versions' AND record_key=jsonb_build_array(OLD."version")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."version") IS DISTINCT FROM jsonb_build_array(OLD."version") THEN
      RAISE EXCEPTION 'Không đổi khóa của model_versions' USING ERRCODE='23514';
    END IF;
    UPDATE rule_sets SET payload=to_jsonb(NEW) WHERE kind='model_versions' AND record_key=jsonb_build_array(OLD."version")::text;
  ELSE
    INSERT INTO rule_sets(kind,record_key,payload) VALUES ('model_versions',jsonb_build_array(NEW."version")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "model_versions"
FOR EACH ROW EXECUTE FUNCTION compat_write_model_versions();

CREATE OR REPLACE FUNCTION compat_validate_vehicles(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "vehicles"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"vehicles", body);
  IF r."vehicle_id" IS NULL THEN RAISE EXCEPTION 'Cột vehicles.vehicle_id không được trống' USING ERRCODE='23502'; END IF; IF r."name" IS NULL THEN RAISE EXCEPTION 'Cột vehicles.name không được trống' USING ERRCODE='23502'; END IF; IF r."payload_ton" IS NULL THEN RAISE EXCEPTION 'Cột vehicles.payload_ton không được trống' USING ERRCODE='23502'; END IF; IF r."base_fee" IS NULL THEN RAISE EXCEPTION 'Cột vehicles.base_fee không được trống' USING ERRCODE='23502'; END IF; IF r."fee_per_km" IS NULL THEN RAISE EXCEPTION 'Cột vehicles.fee_per_km không được trống' USING ERRCODE='23502'; END IF; IF r."data_kind" IS NULL THEN RAISE EXCEPTION 'Cột vehicles.data_kind không được trống' USING ERRCODE='23502'; END IF; IF (r."data_kind" IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')) IS FALSE THEN RAISE EXCEPTION 'Vi phạm ck_vehicles_data_kind' USING ERRCODE='23514', CONSTRAINT='ck_vehicles_data_kind'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_vehicles() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM cost_parameters WHERE kind='vehicles' AND record_key=jsonb_build_array(OLD."vehicle_id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."vehicle_id") IS DISTINCT FROM jsonb_build_array(OLD."vehicle_id") THEN
      RAISE EXCEPTION 'Không đổi khóa của vehicles' USING ERRCODE='23514';
    END IF;
    UPDATE cost_parameters SET payload=to_jsonb(NEW) WHERE kind='vehicles' AND record_key=jsonb_build_array(OLD."vehicle_id")::text;
  ELSE
    INSERT INTO cost_parameters(kind,record_key,payload) VALUES ('vehicles',jsonb_build_array(NEW."vehicle_id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "vehicles"
FOR EACH ROW EXECUTE FUNCTION compat_write_vehicles();

CREATE OR REPLACE FUNCTION compat_validate_labor_rates(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r "labor_rates"%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::"labor_rates", body);
  IF r."id" IS NULL THEN RAISE EXCEPTION 'Cột labor_rates.id không được trống' USING ERRCODE='23502'; END IF; IF r."province" IS NULL THEN RAISE EXCEPTION 'Cột labor_rates.province không được trống' USING ERRCODE='23502'; END IF; IF r."grade" IS NULL THEN RAISE EXCEPTION 'Cột labor_rates.grade không được trống' USING ERRCODE='23502'; END IF; IF r."rate_per_day" IS NULL THEN RAISE EXCEPTION 'Cột labor_rates.rate_per_day không được trống' USING ERRCODE='23502'; END IF; IF r."source" IS NULL THEN RAISE EXCEPTION 'Cột labor_rates.source không được trống' USING ERRCODE='23502'; END IF; IF r."data_kind" IS NULL THEN RAISE EXCEPTION 'Cột labor_rates.data_kind không được trống' USING ERRCODE='23502'; END IF; IF (r."data_kind" IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')) IS FALSE THEN RAISE EXCEPTION 'Vi phạm ck_labor_rates_data_kind' USING ERRCODE='23514', CONSTRAINT='ck_labor_rates_data_kind'; END IF;
  RETURN to_jsonb(r);
END $$;

CREATE OR REPLACE FUNCTION compat_write_labor_rates() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM cost_parameters WHERE kind='labor_rates' AND record_key=jsonb_build_array(OLD."id")::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array(NEW."id") IS DISTINCT FROM jsonb_build_array(OLD."id") THEN
      RAISE EXCEPTION 'Không đổi khóa của labor_rates' USING ERRCODE='23514';
    END IF;
    UPDATE cost_parameters SET payload=to_jsonb(NEW) WHERE kind='labor_rates' AND record_key=jsonb_build_array(OLD."id")::text;
  ELSE
    INSERT INTO cost_parameters(kind,record_key,payload) VALUES ('labor_rates',jsonb_build_array(NEW."id")::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "labor_rates"
FOR EACH ROW EXECUTE FUNCTION compat_write_labor_rates();

CREATE OR REPLACE FUNCTION validate_rule_sets() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE expected_key text;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('rule_sets' || NEW.kind,20));
  IF TG_OP='UPDATE' AND (NEW.kind IS DISTINCT FROM OLD.kind OR NEW.record_key IS DISTINCT FROM OLD.record_key) THEN
    RAISE EXCEPTION 'Không đổi khóa hoặc loại dữ liệu' USING ERRCODE='23514';
  END IF;
  CASE NEW.kind WHEN 'material_groups' THEN NEW.payload := compat_validate_material_groups(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'group_id'))::text; WHEN 'material_families' THEN NEW.payload := compat_validate_material_families(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'family_id'))::text; WHEN 'material_aliases' THEN NEW.payload := compat_validate_material_aliases(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; WHEN 'standards' THEN NEW.payload := compat_validate_standards(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'standard_id'))::text; WHEN 'material_standards' THEN NEW.payload := compat_validate_material_standards(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'material_id'), (NEW.payload->'standard_id'))::text; WHEN 'material_rules' THEN NEW.payload := compat_validate_material_rules(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; WHEN 'room_rules' THEN NEW.payload := compat_validate_room_rules(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; WHEN 'material_notes' THEN NEW.payload := compat_validate_material_notes(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; WHEN 'drawing_concepts' THEN NEW.payload := compat_validate_drawing_concepts(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; WHEN 'convention_clauses' THEN NEW.payload := compat_validate_convention_clauses(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; WHEN 'model_versions' THEN NEW.payload := compat_validate_model_versions(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'version'))::text; ELSE RAISE EXCEPTION 'Loại dữ liệu không được hỗ trợ: %', NEW.kind USING ERRCODE='23514'; END CASE;
  IF NEW.record_key <> expected_key THEN RAISE EXCEPTION 'Khóa dữ liệu không khớp nội dung' USING ERRCODE='23514'; END IF;
  IF TG_OP='UPDATE' THEN NEW.version := OLD.version + CASE WHEN NEW.payload IS DISTINCT FROM OLD.payload THEN 1 ELSE 0 END; NEW.updated_at:=now(); END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER validate_payload BEFORE INSERT OR UPDATE ON rule_sets FOR EACH ROW EXECUTE FUNCTION validate_rule_sets();

CREATE OR REPLACE FUNCTION validate_cost_parameters() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE expected_key text;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('cost_parameters' || NEW.kind,20));
  IF TG_OP='UPDATE' AND (NEW.kind IS DISTINCT FROM OLD.kind OR NEW.record_key IS DISTINCT FROM OLD.record_key) THEN
    RAISE EXCEPTION 'Không đổi khóa hoặc loại dữ liệu' USING ERRCODE='23514';
  END IF;
  CASE NEW.kind WHEN 'vehicles' THEN NEW.payload := compat_validate_vehicles(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'vehicle_id'))::text; WHEN 'labor_rates' THEN NEW.payload := compat_validate_labor_rates(NEW.payload); expected_key := jsonb_build_array((NEW.payload->'id'))::text; ELSE RAISE EXCEPTION 'Loại dữ liệu không được hỗ trợ: %', NEW.kind USING ERRCODE='23514'; END CASE;
  IF NEW.record_key <> expected_key THEN RAISE EXCEPTION 'Khóa dữ liệu không khớp nội dung' USING ERRCODE='23514'; END IF;
  
  RETURN NEW;
END $$;
CREATE TRIGGER validate_payload BEFORE INSERT OR UPDATE ON cost_parameters FOR EACH ROW EXECUTE FUNCTION validate_cost_parameters();


CREATE SEQUENCE IF NOT EXISTS compat_file_id_seq;
CREATE SEQUENCE IF NOT EXISTS compat_revision_id_seq;
CREATE SEQUENCE IF NOT EXISTS compat_profile_revision_id_seq;
CREATE VIEW project_files AS SELECT file_id,project_id,filename,format AS file_type,stored_path,created_at AS uploaded_at
  FROM document_revisions WHERE record_type='file';
ALTER VIEW project_files ALTER COLUMN file_id SET DEFAULT nextval('compat_file_id_seq');
ALTER VIEW project_files ALTER COLUMN uploaded_at SET DEFAULT now();
CREATE VIEW project_document_revisions AS SELECT revision_id,file_id,version,sha256,stored_path,size_bytes,format,role,created_at
  FROM document_revisions WHERE record_type='revision';
ALTER VIEW project_document_revisions ALTER COLUMN revision_id SET DEFAULT nextval('compat_revision_id_seq');
ALTER VIEW project_document_revisions ALTER COLUMN created_at SET DEFAULT now();
CREATE VIEW project_profile_revisions AS SELECT r.revision_id,p.project_id,r.version,r.payload,r.created_at
  FROM projects p CROSS JOIN LATERAL jsonb_to_recordset(p.profile_revisions)
  AS r(revision_id bigint,version integer,payload jsonb,created_at timestamptz);
ALTER VIEW project_profile_revisions ALTER COLUMN revision_id SET DEFAULT nextval('compat_profile_revision_id_seq');
ALTER VIEW project_profile_revisions ALTER COLUMN created_at SET DEFAULT now();



CREATE OR REPLACE FUNCTION compat_write_file() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP='INSERT' THEN
    INSERT INTO document_revisions(project_id,record_type,file_id,filename,format,stored_path,created_at)
    VALUES(NEW.project_id,'file',NEW.file_id,NEW.filename,NEW.file_type,NEW.stored_path,NEW.uploaded_at);
    RETURN NEW;
  ELSIF TG_OP='UPDATE' THEN
    IF NEW.file_id<>OLD.file_id OR NEW.project_id<>OLD.project_id THEN RAISE EXCEPTION 'Không chuyển tệp sang dự án khác'; END IF;
    UPDATE document_revisions SET filename=NEW.filename,format=NEW.file_type,stored_path=NEW.stored_path
      WHERE record_type='file' AND file_id=OLD.file_id;
    RETURN NEW;
  ELSE
    DELETE FROM document_revisions WHERE file_id=OLD.file_id;
    RETURN OLD;
  END IF;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON project_files FOR EACH ROW EXECUTE FUNCTION compat_write_file();
CREATE OR REPLACE FUNCTION compat_write_revision() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE f project_files%ROWTYPE;
BEGIN
  IF TG_OP='UPDATE' THEN RAISE EXCEPTION 'Phiên bản hồ sơ bất biến; hãy tạo phiên bản mới' USING ERRCODE='23514'; END IF;
  IF TG_OP='DELETE' THEN
    DELETE FROM document_revisions WHERE revision_id=OLD.revision_id;
    RETURN OLD;
  END IF;
  SELECT * INTO STRICT f FROM project_files WHERE file_id=NEW.file_id;
  INSERT INTO document_revisions(project_id,record_type,file_id,revision_id,version,filename,format,stored_path,sha256,size_bytes,role,created_at)
  VALUES(f.project_id,'revision',NEW.file_id,NEW.revision_id,NEW.version,f.filename,NEW.format,NEW.stored_path,NEW.sha256,NEW.size_bytes,NEW.role,NEW.created_at);
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON project_document_revisions FOR EACH ROW EXECUTE FUNCTION compat_write_revision();
CREATE OR REPLACE FUNCTION compat_write_profile() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE existing jsonb;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Phiên bản thông số bất biến; hãy tạo phiên bản mới' USING ERRCODE='23514'; END IF;
  IF NEW.version IS NULL OR NEW.version<=0 OR NEW.payload IS NULL THEN RAISE EXCEPTION 'Phiên bản thông số không hợp lệ' USING ERRCODE='23514'; END IF;
  SELECT profile_revisions INTO STRICT existing FROM projects WHERE project_id=NEW.project_id FOR UPDATE;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(existing) r WHERE (r->>'version')::integer=NEW.version) THEN
    RAISE EXCEPTION 'Trùng phiên bản thông số' USING ERRCODE='23505',CONSTRAINT='uq_project_profile_version';
  END IF;
  UPDATE projects SET profile_revisions=existing || jsonb_build_array(to_jsonb(NEW)) WHERE project_id=NEW.project_id;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON project_profile_revisions FOR EACH ROW EXECUTE FUNCTION compat_write_profile();



CREATE OR REPLACE FUNCTION validate_material20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP='DELETE' THEN
    DELETE FROM rule_sets WHERE kind IN ('material_aliases','material_standards') AND payload->>'material_id'=OLD.material_id;
    RETURN OLD;
  END IF;
  IF NOT EXISTS(SELECT 1 FROM material_groups WHERE group_id=NEW."group") THEN
    RAISE EXCEPTION 'Nhóm vật liệu không tồn tại' USING ERRCODE='23503';
  END IF;
  IF NEW.family IS NOT NULL AND NOT EXISTS(SELECT 1 FROM material_families WHERE family_id=NEW.family) THEN
    RAISE EXCEPTION 'Họ vật liệu không tồn tại' USING ERRCODE='23503';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER validate_material BEFORE INSERT OR UPDATE OR DELETE ON materials FOR EACH ROW EXECUTE FUNCTION validate_material20();
CREATE OR REPLACE FUNCTION protect_reference20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF OLD.kind='material_groups' AND EXISTS(SELECT 1 FROM materials WHERE "group"=OLD.payload->>'group_id') THEN
    RAISE EXCEPTION 'Nhóm đang có vật liệu tham chiếu' USING ERRCODE='23503';
  END IF;
  IF OLD.kind='material_families' AND EXISTS(SELECT 1 FROM materials WHERE family=OLD.payload->>'family_id') THEN
    RAISE EXCEPTION 'Họ đang có vật liệu tham chiếu' USING ERRCODE='23503';
  END IF;
  IF OLD.kind='standards' THEN
    DELETE FROM rule_sets WHERE kind='material_standards' AND payload->>'standard_id'=OLD.payload->>'standard_id';
  END IF;
  IF OLD.kind='model_versions' THEN
    UPDATE optimization_runs SET model_version=NULL WHERE model_version=OLD.payload->>'version';
  END IF;
  RETURN OLD;
END $$;
CREATE TRIGGER protect_reference BEFORE DELETE ON rule_sets FOR EACH ROW EXECUTE FUNCTION protect_reference20();
CREATE OR REPLACE FUNCTION validate_analysis20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF NEW.file_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM project_files WHERE file_id=NEW.file_id AND project_id=NEW.project_id) THEN
    RAISE EXCEPTION 'Tệp không thuộc dự án của lần bóc' USING ERRCODE='23503';
  END IF;
  NEW.kind := COALESCE(NEW.result->>'kind',NEW.kind,'takeoff');
  IF NEW.kind='synthetic_housing' THEN NEW.data_kind := 'SYNTHETIC'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER validate_analysis BEFORE INSERT OR UPDATE ON analysis_runs FOR EACH ROW EXECUTE FUNCTION validate_analysis20();
CREATE OR REPLACE FUNCTION protect_snapshot20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF OLD.result_sha256 IS NOT NULL AND (NEW.result_sha256 IS DISTINCT FROM OLD.result_sha256 OR NEW.result IS DISTINCT FROM OLD.result OR NEW.input_snapshot IS DISTINCT FROM OLD.input_snapshot
    OR NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.file_id IS DISTINCT FROM OLD.file_id) THEN
    RAISE EXCEPTION 'Snapshot đã lưu; hãy tạo lần phân tích mới' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER protect_snapshot BEFORE UPDATE ON analysis_runs FOR EACH ROW EXECUTE FUNCTION protect_snapshot20();
CREATE OR REPLACE FUNCTION validate_document20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP='UPDATE' AND OLD.record_type='revision' AND NEW IS DISTINCT FROM OLD THEN
    RAISE EXCEPTION 'Phiên bản tệp bất biến' USING ERRCODE='23514';
  END IF;
  IF NEW.record_type='revision' AND NOT EXISTS(SELECT 1 FROM document_revisions d WHERE d.record_type='file'
    AND d.file_id=NEW.file_id AND d.project_id=NEW.project_id) THEN
    RAISE EXCEPTION 'Phiên bản không thuộc tệp của dự án' USING ERRCODE='23503';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER validate_document BEFORE INSERT OR UPDATE ON document_revisions FOR EACH ROW EXECUTE FUNCTION validate_document20();
CREATE OR REPLACE FUNCTION protect_evidence20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF EXISTS(SELECT 1 FROM analysis_runs WHERE takeoff_id=OLD.analysis_id) AND
     EXISTS(SELECT 1 FROM element_measurements WHERE evidence_ids @> jsonb_build_array(OLD.evidence_id)) THEN
    IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Bằng chứng đang được số đo tham chiếu' USING ERRCODE='23503'; END IF;
    IF NEW.evidence_id IS DISTINCT FROM OLD.evidence_id OR NEW.analysis_id IS DISTINCT FROM OLD.analysis_id
      OR NEW.source_ref IS DISTINCT FROM OLD.source_ref OR NEW.raw_content IS DISTINCT FROM OLD.raw_content
      OR NEW.revision_id IS DISTINCT FROM OLD.revision_id THEN
      RAISE EXCEPTION 'Không thay nguồn bằng chứng đang được sử dụng' USING ERRCODE='23503';
    END IF;
  END IF;
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER protect_evidence BEFORE UPDATE OR DELETE ON evidence_sources FOR EACH ROW EXECUTE FUNCTION protect_evidence20();
CREATE OR REPLACE FUNCTION protect_analysis_child20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE aid integer; digest text;
BEGIN
  IF TG_OP<>'INSERT' THEN
    IF TG_TABLE_NAME='element_measurements' THEN
      SELECT analysis_id INTO aid FROM building_elements WHERE element_id=OLD.element_id;
    ELSE aid:=OLD.analysis_id;
    END IF;
    SELECT result_sha256 INTO digest FROM analysis_runs WHERE takeoff_id=aid;
    IF digest IS NOT NULL THEN
      RAISE EXCEPTION 'Chi tiết thuộc snapshot đã đóng; hãy tạo lần phân tích mới' USING ERRCODE='23514';
    END IF;
  END IF;
  IF TG_OP<>'DELETE' THEN
    IF TG_TABLE_NAME='element_measurements' THEN
      SELECT analysis_id INTO aid FROM building_elements WHERE element_id=NEW.element_id;
    ELSE aid:=NEW.analysis_id;
    END IF;
    SELECT result_sha256 INTO digest FROM analysis_runs WHERE takeoff_id=aid FOR UPDATE;
    IF digest IS NOT NULL THEN
      RAISE EXCEPTION 'Chi tiết thuộc snapshot đã đóng; hãy tạo lần phân tích mới' USING ERRCODE='23514';
    END IF;
  END IF;
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER protect_frozen BEFORE INSERT OR UPDATE OR DELETE ON building_elements FOR EACH ROW EXECUTE FUNCTION protect_analysis_child20();
CREATE TRIGGER protect_frozen BEFORE INSERT OR UPDATE OR DELETE ON element_measurements FOR EACH ROW EXECUTE FUNCTION protect_analysis_child20();
CREATE TRIGGER protect_frozen BEFORE INSERT OR UPDATE OR DELETE ON takeoff_items FOR EACH ROW EXECUTE FUNCTION protect_analysis_child20();
CREATE OR REPLACE FUNCTION validate_links20() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE parent_analysis integer; other_analysis integer; project integer; entry jsonb;
BEGIN
  IF TG_TABLE_NAME='optimization_runs' THEN
    IF NEW.takeoff_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM analysis_runs WHERE takeoff_id=NEW.takeoff_id AND project_id=NEW.project_id) THEN
      RAISE EXCEPTION 'Lần tối ưu và lần bóc khác dự án' USING ERRCODE='23503';
    END IF;
  ELSIF TG_TABLE_NAME='takeoff_items' THEN
    IF NEW.element_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM building_elements WHERE element_id=NEW.element_id AND analysis_id=NEW.analysis_id) THEN
      RAISE EXCEPTION 'Công tác và cấu kiện khác lần nhận dạng' USING ERRCODE='23503';
    END IF;
  ELSIF TG_TABLE_NAME='element_measurements' THEN
    SELECT analysis_id INTO parent_analysis FROM building_elements WHERE element_id=NEW.element_id;
    IF jsonb_typeof(NEW.evidence_ids)<>'array' THEN RAISE EXCEPTION 'Bằng chứng phải là danh sách' USING ERRCODE='23514'; END IF;
    SELECT COALESCE(jsonb_agg(value::bigint),'[]'::jsonb) INTO NEW.evidence_ids FROM jsonb_array_elements_text(NEW.evidence_ids);
    IF EXISTS(SELECT 1 FROM jsonb_array_elements_text(NEW.evidence_ids) id WHERE NOT EXISTS
      (SELECT 1 FROM evidence_sources e WHERE e.evidence_id=id::bigint AND e.analysis_id=parent_analysis)) THEN
      RAISE EXCEPTION 'Bằng chứng không thuộc lần nhận dạng' USING ERRCODE='23503';
    END IF;
  ELSIF TG_TABLE_NAME='evidence_sources' THEN
    IF NEW.revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM document_revisions d JOIN analysis_runs a ON a.project_id=d.project_id
      WHERE d.revision_id=NEW.revision_id AND a.takeoff_id=NEW.analysis_id) THEN
      RAISE EXCEPTION 'Bằng chứng và hồ sơ khác dự án' USING ERRCODE='23503';
    END IF;
  ELSIF TG_TABLE_NAME='material_scenarios' THEN
    IF NEW.run_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM optimization_runs r WHERE r.run_id=NEW.run_id AND r.takeoff_id=NEW.analysis_id) THEN
      RAISE EXCEPTION 'Phương án không thuộc lần tối ưu này' USING ERRCODE='23503';
    END IF;
    IF jsonb_typeof(NEW.assignments)<>'array' OR jsonb_typeof(NEW.requirements)<>'array' THEN
      RAISE EXCEPTION 'Phương án phải chứa danh sách vật liệu' USING ERRCODE='23514';
    END IF;
    FOR entry IN SELECT value FROM jsonb_array_elements(NEW.assignments) LOOP
      IF jsonb_typeof(entry)<>'object' THEN RAISE EXCEPTION 'Gán vật liệu phải là object' USING ERRCODE='23514'; END IF;
      IF entry->>'material_id' IS NOT NULL AND NOT EXISTS(SELECT 1 FROM materials WHERE material_id=entry->>'material_id') THEN
        RAISE EXCEPTION 'Mã vật liệu không tồn tại' USING ERRCODE='23503';
      END IF;
      IF entry->>'wall_system_id' IS NOT NULL AND NOT EXISTS(SELECT 1 FROM wall_systems WHERE wall_system_id=entry->>'wall_system_id'
        AND (entry->>'material_id' IS NULL OR material_id=entry->>'material_id')) THEN
        RAISE EXCEPTION 'Phương án tường không khớp vật liệu' USING ERRCODE='23503';
      END IF;
      IF entry->>'item_id' IS NOT NULL AND NOT EXISTS(SELECT 1 FROM takeoff_items WHERE item_id=(entry->>'item_id')::bigint AND analysis_id=NEW.analysis_id) THEN
        RAISE EXCEPTION 'Gán vật liệu khác lần bóc' USING ERRCODE='23503';
      END IF;
    END LOOP;
    FOR entry IN SELECT value FROM jsonb_array_elements(NEW.requirements) LOOP
      IF jsonb_typeof(entry)<>'object' THEN RAISE EXCEPTION 'Nhu cầu vật liệu phải là object' USING ERRCODE='23514'; END IF;
      IF entry->>'material_id' IS NOT NULL AND NOT EXISTS(SELECT 1 FROM materials WHERE material_id=entry->>'material_id') THEN
        RAISE EXCEPTION 'Mã vật liệu nhu cầu không tồn tại' USING ERRCODE='23503';
      END IF;
      IF entry->>'complete'='true' AND entry->>'quantity' IS NULL THEN
        RAISE EXCEPTION 'Nhu cầu hoàn chỉnh phải có lượng' USING ERRCODE='23514';
      END IF;
      IF entry->>'quantity_with_waste' IS NOT NULL AND entry->>'waste_pct' IS NULL AND NOT
        (jsonb_array_length(COALESCE(entry->'uses','[]'::jsonb))>0 AND NOT EXISTS
          (SELECT 1 FROM jsonb_array_elements(entry->'uses') u WHERE NOT COALESCE((u->>'waste_included')::boolean,false))) THEN
        RAISE EXCEPTION 'Lượng sau hao hụt thiếu tỷ lệ' USING ERRCODE='23514';
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER validate_links BEFORE INSERT OR UPDATE ON optimization_runs FOR EACH ROW EXECUTE FUNCTION validate_links20();
CREATE TRIGGER validate_links BEFORE INSERT OR UPDATE ON takeoff_items FOR EACH ROW EXECUTE FUNCTION validate_links20();
CREATE TRIGGER validate_links BEFORE INSERT OR UPDATE ON element_measurements FOR EACH ROW EXECUTE FUNCTION validate_links20();
CREATE TRIGGER validate_links BEFORE INSERT OR UPDATE ON evidence_sources FOR EACH ROW EXECUTE FUNCTION validate_links20();
CREATE TRIGGER validate_links BEFORE INSERT OR UPDATE ON material_scenarios FOR EACH ROW EXECUTE FUNCTION validate_links20();
