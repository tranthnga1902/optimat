-- Lược đồ OptiMat AI (19 bảng). Sinh tự động từ src/optimat/db/models.py, không sửa tay.
-- Chạy trong DBeaver khi đang kết nối tới database optimat bằng tài khoản optimat.

CREATE TABLE labor_rates (
	id SERIAL NOT NULL, 
	province VARCHAR(64) NOT NULL, 
	grade VARCHAR(32) NOT NULL, 
	rate_per_day FLOAT NOT NULL, 
	valid_from DATE, 
	source VARCHAR(1024) DEFAULT '' NOT NULL, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_labor_rates_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC'))
);

CREATE INDEX ix_labor_rates_province ON labor_rates (province);

CREATE TABLE material_groups (
	group_id VARCHAR(64) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT DEFAULT '' NOT NULL, 
	PRIMARY KEY (group_id)
);

CREATE TABLE model_versions (
	version VARCHAR(32) NOT NULL, 
	target VARCHAR(32) NOT NULL, 
	trained_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	data_rows INTEGER NOT NULL, 
	contains_synthetic BOOLEAN DEFAULT 'false' NOT NULL, 
	metrics JSONB NOT NULL, 
	file_path VARCHAR(1024) NOT NULL, 
	is_active BOOLEAN DEFAULT 'false' NOT NULL, 
	PRIMARY KEY (version)
);

CREATE TABLE standards (
	standard_id SERIAL NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	title TEXT NOT NULL, 
	kind VARCHAR(32) DEFAULT '' NOT NULL, 
	status VARCHAR(32) DEFAULT 'UNKNOWN' NOT NULL, 
	valid_from DATE, 
	valid_to DATE, 
	source_url VARCHAR(1024) DEFAULT '' NOT NULL, 
	PRIMARY KEY (standard_id), 
	CONSTRAINT standards_code_key UNIQUE (code)
);

CREATE TABLE suppliers (
	supplier_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	province VARCHAR(64) NOT NULL, 
	lat FLOAT NOT NULL, 
	lon FLOAT NOT NULL, 
	lead_time_days FLOAT NOT NULL, 
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
	PRIMARY KEY (supplier_id), 
	CONSTRAINT ck_suppliers_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_suppliers_price_public CHECK (price_public IS NULL OR price_public IN ('YES', 'NO', 'PARTIAL')), 
	CONSTRAINT ck_suppliers_latlon CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180)
);

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
);

CREATE TABLE vehicles (
	vehicle_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	payload_ton FLOAT NOT NULL, 
	base_fee FLOAT NOT NULL, 
	fee_per_km FLOAT NOT NULL, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	PRIMARY KEY (vehicle_id), 
	CONSTRAINT ck_vehicles_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC'))
);

CREATE TABLE audit_logs (
	log_id BIGSERIAL NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(64) NOT NULL, 
	detail JSONB DEFAULT '{}' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE SET NULL
);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

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
	PRIMARY KEY (material_id), 
	CONSTRAINT ck_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	FOREIGN KEY("group") REFERENCES material_groups (group_id)
);

CREATE TABLE projects (
	project_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	address VARCHAR(512) DEFAULT '' NOT NULL, 
	site_lat FLOAT, 
	site_lon FLOAT, 
	floor_height_mm FLOAT, 
	budget FLOAT, 
	deadline_days FLOAT, 
	max_vehicle_ton FLOAT, 
	excluded_materials JSONB DEFAULT '[]' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (project_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_projects_user_id ON projects (user_id);

CREATE TABLE material_aliases (
	id SERIAL NOT NULL, 
	alias VARCHAR(255) NOT NULL, 
	material_id VARCHAR(64) NOT NULL, 
	source VARCHAR(255) DEFAULT '' NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT material_aliases_alias_material_id_key UNIQUE (alias, material_id), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE
);

CREATE INDEX ix_material_aliases_alias ON material_aliases (alias);

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
);

CREATE INDEX ix_material_relations_material_id ON material_relations (material_id);

CREATE TABLE material_standards (
	material_id VARCHAR(64) NOT NULL, 
	standard_id INTEGER NOT NULL, 
	note VARCHAR(255) DEFAULT '' NOT NULL, 
	PRIMARY KEY (material_id, standard_id), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE, 
	FOREIGN KEY(standard_id) REFERENCES standards (standard_id) ON DELETE CASCADE
);

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
	CONSTRAINT ck_price_records_positive CHECK (unit_price > 0), 
	CONSTRAINT ck_price_records_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_price_records_price_level CHECK (price_level IN ('DEALER', 'QUOTE', 'BULLETIN')), 
	CONSTRAINT ck_price_records_supplier CHECK (supplier_id IS NOT NULL OR price_level = 'BULLETIN'), 
	CONSTRAINT ck_price_records_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (supplier_id)
);

CREATE INDEX ix_price_records_lookup ON price_records (material_id, supplier_id, date);

CREATE UNIQUE INDEX uq_price_records_dedup ON price_records (material_id, COALESCE(supplier_id, ''), date, quantity, source);

CREATE TABLE project_files (
	file_id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	file_type VARCHAR(16) NOT NULL, 
	stored_path VARCHAR(1024) NOT NULL, 
	uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (file_id), 
	FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

CREATE INDEX ix_project_files_project_id ON project_files (project_id);

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
	PRIMARY KEY (id), 
	CONSTRAINT supplier_materials_supplier_id_material_id_key UNIQUE (supplier_id, material_id), 
	CONSTRAINT ck_supplier_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_supplier_materials_price_level CHECK (price_level IS NULL OR price_level IN ('DEALER', 'QUOTE')), 
	CONSTRAINT ck_supplier_materials_price_complete CHECK (base_price IS NULL OR (base_price > 0 AND price_level IS NOT NULL AND price_date IS NOT NULL)), 
	CONSTRAINT ck_supplier_materials_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (supplier_id) ON DELETE CASCADE, 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE
);

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
);

CREATE INDEX ix_wall_systems_material_id ON wall_systems (material_id);

CREATE TABLE takeoff_results (
	takeoff_id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	file_id INTEGER, 
	result JSONB NOT NULL, 
	layer_overrides JSONB DEFAULT '{}' NOT NULL, 
	confirmed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (takeoff_id), 
	FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE, 
	FOREIGN KEY(file_id) REFERENCES project_files (file_id) ON DELETE SET NULL
);

CREATE INDEX ix_takeoff_results_project_id ON takeoff_results (project_id);

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
	FOREIGN KEY(takeoff_id) REFERENCES takeoff_results (takeoff_id) ON DELETE SET NULL, 
	FOREIGN KEY(model_version) REFERENCES model_versions (version) ON DELETE SET NULL
);

CREATE INDEX ix_optimization_runs_project_id ON optimization_runs (project_id);
