-- Nâng cấp database optimat lên lược đồ hiện tại (19 bảng). Sinh tự động bởi scripts/build_upgrade_sql.py,
-- không sửa tay. Không xóa bảng hay dữ liệu; chạy lại nhiều lần được.
-- DBeaver: kết nối database optimat, mở file này, chạy cả script bằng Alt+X.
-- Sau file này chạy sql/03_materials.sql để nạp hoặc cập nhật danh mục 75 vật liệu.

SET client_encoding = 'UTF8';
SET client_min_messages = warning;   -- ẩn thông báo 'đã có, bỏ qua'; chỉ hiện cảnh báo cần xử lý

-- ===================== 1. Bảng còn thiếu =====================

CREATE TABLE IF NOT EXISTS labor_rates (
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

CREATE TABLE IF NOT EXISTS material_groups (
	group_id VARCHAR(64) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT DEFAULT '' NOT NULL, 
	PRIMARY KEY (group_id)
);

CREATE TABLE IF NOT EXISTS model_versions (
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

CREATE TABLE IF NOT EXISTS standards (
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

CREATE TABLE IF NOT EXISTS suppliers (
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

CREATE TABLE IF NOT EXISTS users (
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

CREATE TABLE IF NOT EXISTS vehicles (
	vehicle_id VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	payload_ton FLOAT NOT NULL, 
	base_fee FLOAT NOT NULL, 
	fee_per_km FLOAT NOT NULL, 
	data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL, 
	PRIMARY KEY (vehicle_id), 
	CONSTRAINT ck_vehicles_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC'))
);

CREATE TABLE IF NOT EXISTS audit_logs (
	log_id BIGSERIAL NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(64) NOT NULL, 
	detail JSONB DEFAULT '{}' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS materials (
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

CREATE TABLE IF NOT EXISTS projects (
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

CREATE TABLE IF NOT EXISTS material_aliases (
	id SERIAL NOT NULL, 
	alias VARCHAR(255) NOT NULL, 
	material_id VARCHAR(64) NOT NULL, 
	source VARCHAR(255) DEFAULT '' NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT material_aliases_alias_material_id_key UNIQUE (alias, material_id), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS material_relations (
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

CREATE TABLE IF NOT EXISTS material_standards (
	material_id VARCHAR(64) NOT NULL, 
	standard_id INTEGER NOT NULL, 
	note VARCHAR(255) DEFAULT '' NOT NULL, 
	PRIMARY KEY (material_id, standard_id), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE, 
	FOREIGN KEY(standard_id) REFERENCES standards (standard_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_records (
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

CREATE TABLE IF NOT EXISTS project_files (
	file_id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	file_type VARCHAR(16) NOT NULL, 
	stored_path VARCHAR(1024) NOT NULL, 
	uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (file_id), 
	FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS supplier_materials (
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

CREATE TABLE IF NOT EXISTS wall_systems (
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

CREATE TABLE IF NOT EXISTS takeoff_results (
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

CREATE TABLE IF NOT EXISTS optimization_runs (
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

-- ===================== 2. Cột còn thiếu =====================

-- labor_rates
ALTER TABLE labor_rates ADD COLUMN IF NOT EXISTS province VARCHAR(64);
ALTER TABLE labor_rates ADD COLUMN IF NOT EXISTS grade VARCHAR(32);
ALTER TABLE labor_rates ADD COLUMN IF NOT EXISTS rate_per_day FLOAT;
ALTER TABLE labor_rates ADD COLUMN IF NOT EXISTS valid_from DATE;
ALTER TABLE labor_rates ADD COLUMN IF NOT EXISTS source VARCHAR(1024) DEFAULT '' NOT NULL;
ALTER TABLE labor_rates ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;

-- material_groups
ALTER TABLE material_groups ADD COLUMN IF NOT EXISTS sort_order INTEGER;
ALTER TABLE material_groups ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE material_groups ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '' NOT NULL;

-- model_versions
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS target VARCHAR(32);
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS trained_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS data_rows INTEGER;
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS contains_synthetic BOOLEAN DEFAULT 'false' NOT NULL;
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS metrics JSONB;
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS file_path VARCHAR(1024);
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT 'false' NOT NULL;

-- standards
ALTER TABLE standards ADD COLUMN IF NOT EXISTS code VARCHAR(64);
ALTER TABLE standards ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE standards ADD COLUMN IF NOT EXISTS kind VARCHAR(32) DEFAULT '' NOT NULL;
ALTER TABLE standards ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE standards ADD COLUMN IF NOT EXISTS valid_from DATE;
ALTER TABLE standards ADD COLUMN IF NOT EXISTS valid_to DATE;
ALTER TABLE standards ADD COLUMN IF NOT EXISTS source_url VARCHAR(1024) DEFAULT '' NOT NULL;

-- suppliers
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS province VARCHAR(64);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS lat FLOAT;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS lon FLOAT;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS lead_time_days FLOAT;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS dealer_type VARCHAR(64);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS brands TEXT;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS address VARCHAR(512);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS ward VARCHAR(128);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS district VARCHAR(128);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS maps_url VARCHAR(1024);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS phone VARCHAR(64);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS zalo VARCHAR(64);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS website VARCHAR(1024);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS facebook VARCHAR(1024);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS tax_code VARCHAR(32);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS opening_hours VARCHAR(255);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS delivers BOOLEAN;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS delivery_radius_km FLOAT;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS max_truck_ton FLOAT;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS min_order VARCHAR(255);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS vat_invoice BOOLEAN;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS payment VARCHAR(255);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS price_public VARCHAR(8);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS price_page_url VARCHAR(1024);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS verified BOOLEAN;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS collected_at DATE;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS collected_by VARCHAR(128);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS source VARCHAR(1024);
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS note TEXT;

-- users
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255) DEFAULT '' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(16) DEFAULT 'user' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT 'true' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- vehicles
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS payload_ton FLOAT;
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS base_fee FLOAT;
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS fee_per_km FLOAT;
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;

-- audit_logs
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users (user_id) ON DELETE SET NULL;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(64);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS detail JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- materials
ALTER TABLE materials ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS "group" VARCHAR(64) REFERENCES material_groups (group_id);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS thickness_mm FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS unit VARCHAR(16);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS qty_per_m2 FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS weight_kg_per_m2 FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS lambda_w_mk FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS labor_days_per_m2 FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS subgroup VARCHAR(128);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS family VARCHAR(32);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS usage_text VARCHAR(255);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS usage_role VARCHAR(128);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS tier INTEGER;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS purchase_unit VARCHAR(32);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS unit_conversion FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS length_mm FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS width_mm FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS height_mm FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS price_priority VARCHAR(4);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS needs_lambda BOOLEAN;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS lambda_source VARCHAR(255);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS unit_weight_kg FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS weight_source VARCHAR(255);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS transport_volume_m3 FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS waste_pct FLOAT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS waste_source VARCHAR(255);
ALTER TABLE materials ADD COLUMN IF NOT EXISTS standards_text TEXT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS reference_brands TEXT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS tech_notes TEXT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS data_note TEXT;

-- projects
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users (user_id) ON DELETE CASCADE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS address VARCHAR(512) DEFAULT '' NOT NULL;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS site_lat FLOAT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS site_lon FLOAT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS floor_height_mm FLOAT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget FLOAT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS deadline_days FLOAT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS max_vehicle_ton FLOAT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS excluded_materials JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- material_aliases
ALTER TABLE material_aliases ADD COLUMN IF NOT EXISTS alias VARCHAR(255);
ALTER TABLE material_aliases ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) REFERENCES materials (material_id) ON DELETE CASCADE;
ALTER TABLE material_aliases ADD COLUMN IF NOT EXISTS source VARCHAR(255) DEFAULT '' NOT NULL;

-- material_relations
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) REFERENCES materials (material_id) ON DELETE CASCADE;
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS relation_type VARCHAR(16);
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS related_material_id VARCHAR(64) REFERENCES materials (material_id) ON DELETE CASCADE;
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS quantity FLOAT;
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS quantity_unit VARCHAR(64);
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS source VARCHAR(255);
ALTER TABLE material_relations ADD COLUMN IF NOT EXISTS note TEXT;

-- material_standards
ALTER TABLE material_standards ADD COLUMN IF NOT EXISTS note VARCHAR(255) DEFAULT '' NOT NULL;

-- price_records
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS date DATE;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) REFERENCES materials (material_id);
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(64) REFERENCES suppliers (supplier_id);
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS province VARCHAR(64);
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS quantity FLOAT;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS unit VARCHAR(16);
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS unit_price FLOAT;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS vat_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS transport_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS source VARCHAR(1024) DEFAULT '' NOT NULL;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE price_records ADD COLUMN IF NOT EXISTS price_level VARCHAR(16) DEFAULT 'DEALER' NOT NULL;

-- project_files
ALTER TABLE project_files ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects (project_id) ON DELETE CASCADE;
ALTER TABLE project_files ADD COLUMN IF NOT EXISTS filename VARCHAR(255);
ALTER TABLE project_files ADD COLUMN IF NOT EXISTS file_type VARCHAR(16);
ALTER TABLE project_files ADD COLUMN IF NOT EXISTS stored_path VARCHAR(1024);
ALTER TABLE project_files ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- supplier_materials
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(64) REFERENCES suppliers (supplier_id) ON DELETE CASCADE;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) REFERENCES materials (material_id) ON DELETE CASCADE;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS base_price FLOAT;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS product_url VARCHAR(1024);
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS collected_at DATE;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS dealer_product_name VARCHAR(255);
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS brand VARCHAR(128);
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS sale_unit VARCHAR(32);
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS unit_conversion FLOAT;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS price_level VARCHAR(16);
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS price_date DATE;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS vat_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS transport_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS in_stock BOOLEAN;
ALTER TABLE supplier_materials ADD COLUMN IF NOT EXISTS note TEXT;

-- wall_systems
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) REFERENCES materials (material_id) ON DELETE CASCADE;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS wall_thickness_mm FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS detect_class VARCHAR(8);
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS role VARCHAR(16);
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS masonry_thickness_mm FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS norm_code VARCHAR(32);
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS units_per_m3 FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS mortar_m3_per_m3 FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS labor_day_per_m3 FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS unit_factor FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS mortar_material_id VARCHAR(64) REFERENCES materials (material_id);
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS mortar_density FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS r0_reference FLOAT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS norm_source VARCHAR(255);
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE wall_systems ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;

-- takeoff_results
ALTER TABLE takeoff_results ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects (project_id) ON DELETE CASCADE;
ALTER TABLE takeoff_results ADD COLUMN IF NOT EXISTS file_id INTEGER REFERENCES project_files (file_id) ON DELETE SET NULL;
ALTER TABLE takeoff_results ADD COLUMN IF NOT EXISTS result JSONB;
ALTER TABLE takeoff_results ADD COLUMN IF NOT EXISTS layer_overrides JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE takeoff_results ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE takeoff_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- optimization_runs
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects (project_id) ON DELETE CASCADE;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS takeoff_id INTEGER REFERENCES takeoff_results (takeoff_id) ON DELETE SET NULL;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS model_version VARCHAR(32) REFERENCES model_versions (version) ON DELETE SET NULL;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS method VARCHAR(16);
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS solutions JSONB;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS chosen_index INTEGER;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS price_snapshot_date DATE;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS llm_model VARCHAR(64);
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS tool_calls JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS excluded_materials JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- ===================== 3. Cột được phép để trống =====================

ALTER TABLE labor_rates ALTER COLUMN valid_from DROP NOT NULL;
ALTER TABLE standards ALTER COLUMN valid_from DROP NOT NULL;
ALTER TABLE standards ALTER COLUMN valid_to DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN dealer_type DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN brands DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN address DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN ward DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN district DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN maps_url DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN phone DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN zalo DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN email DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN website DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN facebook DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN tax_code DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN opening_hours DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN delivers DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN delivery_radius_km DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN max_truck_ton DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN min_order DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN vat_invoice DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN payment DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN price_public DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN price_page_url DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN verified DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN collected_at DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN collected_by DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN source DROP NOT NULL;
ALTER TABLE suppliers ALTER COLUMN note DROP NOT NULL;
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN thickness_mm DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN qty_per_m2 DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN weight_kg_per_m2 DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN lambda_w_mk DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN labor_days_per_m2 DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN subgroup DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN family DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN usage_text DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN usage_role DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN tier DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN purchase_unit DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN unit_conversion DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN length_mm DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN width_mm DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN height_mm DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN price_priority DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN needs_lambda DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN lambda_source DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN unit_weight_kg DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN weight_source DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN transport_volume_m3 DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN waste_pct DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN waste_source DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN standards_text DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN reference_brands DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN tech_notes DROP NOT NULL;
ALTER TABLE materials ALTER COLUMN data_note DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN site_lat DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN site_lon DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN floor_height_mm DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN budget DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN deadline_days DROP NOT NULL;
ALTER TABLE projects ALTER COLUMN max_vehicle_ton DROP NOT NULL;
ALTER TABLE material_relations ALTER COLUMN quantity DROP NOT NULL;
ALTER TABLE material_relations ALTER COLUMN quantity_unit DROP NOT NULL;
ALTER TABLE material_relations ALTER COLUMN source DROP NOT NULL;
ALTER TABLE material_relations ALTER COLUMN note DROP NOT NULL;
ALTER TABLE price_records ALTER COLUMN supplier_id DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN base_price DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN product_url DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN dealer_product_name DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN brand DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN sale_unit DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN unit_conversion DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN price_level DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN price_date DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN in_stock DROP NOT NULL;
ALTER TABLE supplier_materials ALTER COLUMN note DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN wall_thickness_mm DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN detect_class DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN role DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN masonry_thickness_mm DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN norm_code DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN units_per_m3 DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN mortar_m3_per_m3 DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN labor_day_per_m3 DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN unit_factor DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN mortar_material_id DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN mortar_density DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN r0_reference DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN norm_source DROP NOT NULL;
ALTER TABLE wall_systems ALTER COLUMN note DROP NOT NULL;
ALTER TABLE takeoff_results ALTER COLUMN file_id DROP NOT NULL;
ALTER TABLE takeoff_results ALTER COLUMN confirmed_at DROP NOT NULL;
ALTER TABLE optimization_runs ALTER COLUMN takeoff_id DROP NOT NULL;
ALTER TABLE optimization_runs ALTER COLUMN model_version DROP NOT NULL;
ALTER TABLE optimization_runs ALTER COLUMN chosen_index DROP NOT NULL;
ALTER TABLE optimization_runs ALTER COLUMN price_snapshot_date DROP NOT NULL;
ALTER TABLE optimization_runs ALTER COLUMN llm_model DROP NOT NULL;

-- ===================== 4. Bổ sung giá trị cho dữ liệu cũ =====================

-- Giá đã có trong supplier_materials trước khi có cột mức giá: coi là giá đại lý, ngày của giá = ngày thu thập.
UPDATE supplier_materials SET price_level = 'DEALER' WHERE base_price IS NOT NULL AND price_level IS NULL;
UPDATE supplier_materials SET price_date = collected_at WHERE base_price IS NOT NULL AND price_date IS NULL;
-- Chuẩn hóa giá trị cờ thuế, vận chuyển về YES / NO / UNKNOWN.
UPDATE supplier_materials SET vat_included = 'UNKNOWN' WHERE vat_included IS NULL OR vat_included NOT IN ('YES', 'NO', 'UNKNOWN');
UPDATE supplier_materials SET transport_included = 'UNKNOWN' WHERE transport_included IS NULL OR transport_included NOT IN ('YES', 'NO', 'UNKNOWN');
UPDATE price_records SET vat_included = 'UNKNOWN' WHERE vat_included IS NULL OR vat_included NOT IN ('YES', 'NO', 'UNKNOWN');
UPDATE price_records SET transport_included = 'UNKNOWN' WHERE transport_included IS NULL OR transport_included NOT IN ('YES', 'NO', 'UNKNOWN');

-- ===================== 5. Ràng buộc =====================

DO $$ BEGIN
  EXECUTE 'ALTER TABLE labor_rates ADD CONSTRAINT ck_labor_rates_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_labor_rates_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE standards ADD CONSTRAINT standards_code_key UNIQUE (code)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN unique_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc standards_code_key: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE suppliers ADD CONSTRAINT ck_suppliers_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_suppliers_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE suppliers ADD CONSTRAINT ck_suppliers_latlon CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_suppliers_latlon: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE suppliers ADD CONSTRAINT ck_suppliers_price_public CHECK (price_public IS NULL OR price_public IN (''YES'', ''NO'', ''PARTIAL''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_suppliers_price_public: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN (''admin'', ''user''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_users_role: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN unique_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc users_email_key: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE vehicles ADD CONSTRAINT ck_vehicles_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_vehicles_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE materials ADD CONSTRAINT ck_materials_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_materials_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE material_aliases ADD CONSTRAINT material_aliases_alias_material_id_key UNIQUE (alias, material_id)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN unique_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc material_aliases_alias_material_id_key: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE material_relations ADD CONSTRAINT ck_material_relations_type CHECK (relation_type IN (''REQUIRES'', ''COMPOSED_OF''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_material_relations_type: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE material_relations ADD CONSTRAINT material_relations_material_id_related_material_id_rela_f54c UNIQUE (material_id, related_material_id, relation_type)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN unique_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc material_relations_material_id_related_material_id_rela_f54c: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE price_records ADD CONSTRAINT ck_price_records_basis CHECK (vat_included IN (''YES'', ''NO'', ''UNKNOWN'') AND transport_included IN (''YES'', ''NO'', ''UNKNOWN''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_price_records_basis: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE price_records ADD CONSTRAINT ck_price_records_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_price_records_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE price_records ADD CONSTRAINT ck_price_records_positive CHECK (unit_price > 0)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_price_records_positive: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE price_records ADD CONSTRAINT ck_price_records_price_level CHECK (price_level IN (''DEALER'', ''QUOTE'', ''BULLETIN''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_price_records_price_level: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE price_records ADD CONSTRAINT ck_price_records_supplier CHECK (supplier_id IS NOT NULL OR price_level = ''BULLETIN'')';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_price_records_supplier: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_basis CHECK (vat_included IN (''YES'', ''NO'', ''UNKNOWN'') AND transport_included IN (''YES'', ''NO'', ''UNKNOWN''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_supplier_materials_basis: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_supplier_materials_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_price_complete CHECK (base_price IS NULL OR (base_price > 0 AND price_level IS NOT NULL AND price_date IS NOT NULL))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_supplier_materials_price_complete: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_price_level CHECK (price_level IS NULL OR price_level IN (''DEALER'', ''QUOTE''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_supplier_materials_price_level: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE supplier_materials ADD CONSTRAINT supplier_materials_supplier_id_material_id_key UNIQUE (supplier_id, material_id)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN unique_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc supplier_materials_supplier_id_material_id_key: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
DO $$ BEGIN
  EXECUTE 'ALTER TABLE wall_systems ADD CONSTRAINT ck_wall_systems_data_kind CHECK (data_kind IN (''ACTUAL'', ''SAMPLE'', ''SYNTHETIC''))';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN check_violation THEN RAISE WARNING 'Chưa thêm được ràng buộc ck_wall_systems_data_kind: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;

-- ===================== 6. Chỉ mục =====================

CREATE INDEX IF NOT EXISTS ix_labor_rates_province ON labor_rates (province);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id);
CREATE INDEX IF NOT EXISTS ix_material_aliases_alias ON material_aliases (alias);
CREATE INDEX IF NOT EXISTS ix_material_relations_material_id ON material_relations (material_id);
CREATE INDEX IF NOT EXISTS ix_price_records_lookup ON price_records (material_id, supplier_id, date);
DO $$ BEGIN
  EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS uq_price_records_dedup ON price_records (material_id, COALESCE(supplier_id, ''''), date, quantity, source)';
EXCEPTION
  WHEN duplicate_object OR duplicate_table THEN NULL;
  WHEN unique_violation THEN RAISE WARNING 'Chưa thêm được chỉ mục uq_price_records_dedup: dữ liệu cũ vi phạm, sửa dữ liệu rồi chạy lại';
END $$;
CREATE INDEX IF NOT EXISTS ix_project_files_project_id ON project_files (project_id);
CREATE INDEX IF NOT EXISTS ix_wall_systems_material_id ON wall_systems (material_id);
CREATE INDEX IF NOT EXISTS ix_takeoff_results_project_id ON takeoff_results (project_id);
CREATE INDEX IF NOT EXISTS ix_optimization_runs_project_id ON optimization_runs (project_id);

-- ===================== 7. View =====================

-- View đặc trưng cho huấn luyện mô hình giá: chỉ lấy dữ liệu thật (ACTUAL), nối thông tin vật liệu và đại lý.
-- Công cụ Price đọc dữ liệu huấn luyện từ một chỗ duy nhất này.
DROP VIEW IF EXISTS v_price_training;
CREATE VIEW v_price_training AS
SELECT p.id, p.date, p.material_id, p.supplier_id, p.province, p.quantity, p.unit, p.unit_price,
       p.vat_included, p.transport_included, p.price_level, p.source,
       m.name AS material_name, m."group" AS material_group, m.family, m.tier, m.unit AS material_unit,
       s.district AS supplier_district, s.dealer_type, s.lat AS supplier_lat, s.lon AS supplier_lon
FROM price_records p
JOIN materials m ON m.material_id = p.material_id
LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id
WHERE p.data_kind = 'ACTUAL';


-- ===================== Khi có cảnh báo "Chưa thêm được ..." =====================
-- uq_price_records_dedup: tìm dòng giá trùng, xóa bớt rồi chạy lại file này.
-- SELECT material_id, supplier_id, date, quantity, source, count(*) FROM price_records
--   GROUP BY 1, 2, 3, 4, 5 HAVING count(*) > 1;
-- ck_supplier_materials_price_complete: dòng có giá nhưng thiếu mức giá hoặc ngày của giá.
-- SELECT * FROM supplier_materials WHERE base_price IS NOT NULL AND (price_level IS NULL OR price_date IS NULL);
-- ===================== TÙY CHỌN: dọn dữ liệu mẫu (bỏ dấu -- để chạy) =====================
-- Chỉ chạy khi đã có dữ liệu thật. Xóa vật liệu mẫu MAT_..., đại lý mẫu và toàn bộ dòng SAMPLE / SYNTHETIC.
-- DELETE FROM price_records WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM supplier_materials WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM suppliers WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM vehicles WHERE data_kind IN ('SAMPLE', 'SYNTHETIC');
-- DELETE FROM materials WHERE material_id LIKE 'MAT\_%' AND data_kind = 'SAMPLE';

-- ===================== 8. Kiểm tra: kết quả rỗng nghĩa là database đã đủ =====================
WITH expected(table_name, column_name, udt_name) AS (VALUES
  ('labor_rates', 'id', 'int4'),
  ('labor_rates', 'province', 'varchar'),
  ('labor_rates', 'grade', 'varchar'),
  ('labor_rates', 'rate_per_day', 'float8'),
  ('labor_rates', 'valid_from', 'date'),
  ('labor_rates', 'source', 'varchar'),
  ('labor_rates', 'data_kind', 'varchar'),
  ('material_groups', 'group_id', 'varchar'),
  ('material_groups', 'sort_order', 'int4'),
  ('material_groups', 'name', 'varchar'),
  ('material_groups', 'description', 'text'),
  ('model_versions', 'version', 'varchar'),
  ('model_versions', 'target', 'varchar'),
  ('model_versions', 'trained_at', 'timestamptz'),
  ('model_versions', 'data_rows', 'int4'),
  ('model_versions', 'contains_synthetic', 'bool'),
  ('model_versions', 'metrics', 'jsonb'),
  ('model_versions', 'file_path', 'varchar'),
  ('model_versions', 'is_active', 'bool'),
  ('standards', 'standard_id', 'int4'),
  ('standards', 'code', 'varchar'),
  ('standards', 'title', 'text'),
  ('standards', 'kind', 'varchar'),
  ('standards', 'status', 'varchar'),
  ('standards', 'valid_from', 'date'),
  ('standards', 'valid_to', 'date'),
  ('standards', 'source_url', 'varchar'),
  ('suppliers', 'supplier_id', 'varchar'),
  ('suppliers', 'name', 'varchar'),
  ('suppliers', 'province', 'varchar'),
  ('suppliers', 'lat', 'float8'),
  ('suppliers', 'lon', 'float8'),
  ('suppliers', 'lead_time_days', 'float8'),
  ('suppliers', 'data_kind', 'varchar'),
  ('suppliers', 'dealer_type', 'varchar'),
  ('suppliers', 'brands', 'text'),
  ('suppliers', 'address', 'varchar'),
  ('suppliers', 'ward', 'varchar'),
  ('suppliers', 'district', 'varchar'),
  ('suppliers', 'maps_url', 'varchar'),
  ('suppliers', 'phone', 'varchar'),
  ('suppliers', 'zalo', 'varchar'),
  ('suppliers', 'email', 'varchar'),
  ('suppliers', 'website', 'varchar'),
  ('suppliers', 'facebook', 'varchar'),
  ('suppliers', 'tax_code', 'varchar'),
  ('suppliers', 'opening_hours', 'varchar'),
  ('suppliers', 'delivers', 'bool'),
  ('suppliers', 'delivery_radius_km', 'float8'),
  ('suppliers', 'max_truck_ton', 'float8'),
  ('suppliers', 'min_order', 'varchar'),
  ('suppliers', 'vat_invoice', 'bool'),
  ('suppliers', 'payment', 'varchar'),
  ('suppliers', 'price_public', 'varchar'),
  ('suppliers', 'price_page_url', 'varchar'),
  ('suppliers', 'verified', 'bool'),
  ('suppliers', 'collected_at', 'date'),
  ('suppliers', 'collected_by', 'varchar'),
  ('suppliers', 'source', 'varchar'),
  ('suppliers', 'note', 'text'),
  ('users', 'user_id', 'int4'),
  ('users', 'email', 'varchar'),
  ('users', 'full_name', 'varchar'),
  ('users', 'password_hash', 'varchar'),
  ('users', 'role', 'varchar'),
  ('users', 'is_active', 'bool'),
  ('users', 'created_at', 'timestamptz'),
  ('vehicles', 'vehicle_id', 'varchar'),
  ('vehicles', 'name', 'varchar'),
  ('vehicles', 'payload_ton', 'float8'),
  ('vehicles', 'base_fee', 'float8'),
  ('vehicles', 'fee_per_km', 'float8'),
  ('vehicles', 'data_kind', 'varchar'),
  ('audit_logs', 'log_id', 'int8'),
  ('audit_logs', 'user_id', 'int4'),
  ('audit_logs', 'action', 'varchar'),
  ('audit_logs', 'detail', 'jsonb'),
  ('audit_logs', 'created_at', 'timestamptz'),
  ('materials', 'material_id', 'varchar'),
  ('materials', 'name', 'varchar'),
  ('materials', 'group', 'varchar'),
  ('materials', 'thickness_mm', 'float8'),
  ('materials', 'unit', 'varchar'),
  ('materials', 'qty_per_m2', 'float8'),
  ('materials', 'weight_kg_per_m2', 'float8'),
  ('materials', 'lambda_w_mk', 'float8'),
  ('materials', 'labor_days_per_m2', 'float8'),
  ('materials', 'data_kind', 'varchar'),
  ('materials', 'subgroup', 'varchar'),
  ('materials', 'family', 'varchar'),
  ('materials', 'usage_text', 'varchar'),
  ('materials', 'usage_role', 'varchar'),
  ('materials', 'tier', 'int4'),
  ('materials', 'purchase_unit', 'varchar'),
  ('materials', 'unit_conversion', 'float8'),
  ('materials', 'length_mm', 'float8'),
  ('materials', 'width_mm', 'float8'),
  ('materials', 'height_mm', 'float8'),
  ('materials', 'price_priority', 'varchar'),
  ('materials', 'needs_lambda', 'bool'),
  ('materials', 'lambda_source', 'varchar'),
  ('materials', 'unit_weight_kg', 'float8'),
  ('materials', 'weight_source', 'varchar'),
  ('materials', 'transport_volume_m3', 'float8'),
  ('materials', 'waste_pct', 'float8'),
  ('materials', 'waste_source', 'varchar'),
  ('materials', 'standards_text', 'text'),
  ('materials', 'reference_brands', 'text'),
  ('materials', 'tech_notes', 'text'),
  ('materials', 'data_note', 'text'),
  ('projects', 'project_id', 'int4'),
  ('projects', 'user_id', 'int4'),
  ('projects', 'name', 'varchar'),
  ('projects', 'address', 'varchar'),
  ('projects', 'site_lat', 'float8'),
  ('projects', 'site_lon', 'float8'),
  ('projects', 'floor_height_mm', 'float8'),
  ('projects', 'budget', 'float8'),
  ('projects', 'deadline_days', 'float8'),
  ('projects', 'max_vehicle_ton', 'float8'),
  ('projects', 'excluded_materials', 'jsonb'),
  ('projects', 'created_at', 'timestamptz'),
  ('projects', 'updated_at', 'timestamptz'),
  ('material_aliases', 'id', 'int4'),
  ('material_aliases', 'alias', 'varchar'),
  ('material_aliases', 'material_id', 'varchar'),
  ('material_aliases', 'source', 'varchar'),
  ('material_relations', 'id', 'int4'),
  ('material_relations', 'material_id', 'varchar'),
  ('material_relations', 'relation_type', 'varchar'),
  ('material_relations', 'related_material_id', 'varchar'),
  ('material_relations', 'quantity', 'float8'),
  ('material_relations', 'quantity_unit', 'varchar'),
  ('material_relations', 'source', 'varchar'),
  ('material_relations', 'note', 'text'),
  ('material_standards', 'material_id', 'varchar'),
  ('material_standards', 'standard_id', 'int4'),
  ('material_standards', 'note', 'varchar'),
  ('price_records', 'id', 'int8'),
  ('price_records', 'date', 'date'),
  ('price_records', 'material_id', 'varchar'),
  ('price_records', 'supplier_id', 'varchar'),
  ('price_records', 'province', 'varchar'),
  ('price_records', 'quantity', 'float8'),
  ('price_records', 'unit', 'varchar'),
  ('price_records', 'unit_price', 'float8'),
  ('price_records', 'vat_included', 'varchar'),
  ('price_records', 'transport_included', 'varchar'),
  ('price_records', 'source', 'varchar'),
  ('price_records', 'data_kind', 'varchar'),
  ('price_records', 'price_level', 'varchar'),
  ('project_files', 'file_id', 'int4'),
  ('project_files', 'project_id', 'int4'),
  ('project_files', 'filename', 'varchar'),
  ('project_files', 'file_type', 'varchar'),
  ('project_files', 'stored_path', 'varchar'),
  ('project_files', 'uploaded_at', 'timestamptz'),
  ('supplier_materials', 'id', 'int4'),
  ('supplier_materials', 'supplier_id', 'varchar'),
  ('supplier_materials', 'material_id', 'varchar'),
  ('supplier_materials', 'base_price', 'float8'),
  ('supplier_materials', 'product_url', 'varchar'),
  ('supplier_materials', 'collected_at', 'date'),
  ('supplier_materials', 'data_kind', 'varchar'),
  ('supplier_materials', 'dealer_product_name', 'varchar'),
  ('supplier_materials', 'brand', 'varchar'),
  ('supplier_materials', 'sale_unit', 'varchar'),
  ('supplier_materials', 'unit_conversion', 'float8'),
  ('supplier_materials', 'price_level', 'varchar'),
  ('supplier_materials', 'price_date', 'date'),
  ('supplier_materials', 'vat_included', 'varchar'),
  ('supplier_materials', 'transport_included', 'varchar'),
  ('supplier_materials', 'in_stock', 'bool'),
  ('supplier_materials', 'note', 'text'),
  ('wall_systems', 'wall_system_id', 'varchar'),
  ('wall_systems', 'material_id', 'varchar'),
  ('wall_systems', 'wall_thickness_mm', 'float8'),
  ('wall_systems', 'detect_class', 'varchar'),
  ('wall_systems', 'role', 'varchar'),
  ('wall_systems', 'masonry_thickness_mm', 'float8'),
  ('wall_systems', 'norm_code', 'varchar'),
  ('wall_systems', 'units_per_m3', 'float8'),
  ('wall_systems', 'mortar_m3_per_m3', 'float8'),
  ('wall_systems', 'labor_day_per_m3', 'float8'),
  ('wall_systems', 'unit_factor', 'float8'),
  ('wall_systems', 'mortar_material_id', 'varchar'),
  ('wall_systems', 'mortar_density', 'float8'),
  ('wall_systems', 'r0_reference', 'float8'),
  ('wall_systems', 'norm_source', 'varchar'),
  ('wall_systems', 'note', 'text'),
  ('wall_systems', 'data_kind', 'varchar'),
  ('takeoff_results', 'takeoff_id', 'int4'),
  ('takeoff_results', 'project_id', 'int4'),
  ('takeoff_results', 'file_id', 'int4'),
  ('takeoff_results', 'result', 'jsonb'),
  ('takeoff_results', 'layer_overrides', 'jsonb'),
  ('takeoff_results', 'confirmed_at', 'timestamptz'),
  ('takeoff_results', 'created_at', 'timestamptz'),
  ('optimization_runs', 'run_id', 'int4'),
  ('optimization_runs', 'project_id', 'int4'),
  ('optimization_runs', 'takeoff_id', 'int4'),
  ('optimization_runs', 'model_version', 'varchar'),
  ('optimization_runs', 'method', 'varchar'),
  ('optimization_runs', 'config', 'jsonb'),
  ('optimization_runs', 'solutions', 'jsonb'),
  ('optimization_runs', 'chosen_index', 'int4'),
  ('optimization_runs', 'price_snapshot_date', 'date'),
  ('optimization_runs', 'llm_model', 'varchar'),
  ('optimization_runs', 'tool_calls', 'jsonb'),
  ('optimization_runs', 'excluded_materials', 'jsonb'),
  ('optimization_runs', 'created_at', 'timestamptz')),
expected_con(table_name, con_name) AS (VALUES ('labor_rates', 'ck_labor_rates_data_kind'), ('standards', 'standards_code_key'), ('suppliers', 'ck_suppliers_data_kind'), ('suppliers', 'ck_suppliers_latlon'), ('suppliers', 'ck_suppliers_price_public'), ('users', 'ck_users_role'), ('users', 'users_email_key'), ('vehicles', 'ck_vehicles_data_kind'), ('materials', 'ck_materials_data_kind'), ('material_aliases', 'material_aliases_alias_material_id_key'), ('material_relations', 'ck_material_relations_type'), ('material_relations', 'material_relations_material_id_related_material_id_rela_f54c'), ('price_records', 'ck_price_records_basis'), ('price_records', 'ck_price_records_data_kind'), ('price_records', 'ck_price_records_positive'), ('price_records', 'ck_price_records_price_level'), ('price_records', 'ck_price_records_supplier'), ('supplier_materials', 'ck_supplier_materials_basis'), ('supplier_materials', 'ck_supplier_materials_data_kind'), ('supplier_materials', 'ck_supplier_materials_price_complete'), ('supplier_materials', 'ck_supplier_materials_price_level'), ('supplier_materials', 'supplier_materials_supplier_id_material_id_key'), ('wall_systems', 'ck_wall_systems_data_kind'), ('labor_rates', 'ix_labor_rates_province'), ('audit_logs', 'ix_audit_logs_action'), ('projects', 'ix_projects_user_id'), ('material_aliases', 'ix_material_aliases_alias'), ('material_relations', 'ix_material_relations_material_id'), ('price_records', 'ix_price_records_lookup'), ('price_records', 'uq_price_records_dedup'), ('project_files', 'ix_project_files_project_id'), ('wall_systems', 'ix_wall_systems_material_id'), ('takeoff_results', 'ix_takeoff_results_project_id'), ('optimization_runs', 'ix_optimization_runs_project_id'))
SELECT 'THIEU COT' AS van_de, e.table_name, e.column_name AS ten, e.udt_name AS can_co, NULL AS dang_co
FROM expected e LEFT JOIN information_schema.columns c
  ON c.table_schema = 'public' AND c.table_name = e.table_name AND c.column_name = e.column_name
WHERE c.column_name IS NULL
UNION ALL
SELECT 'SAI KIEU', e.table_name, e.column_name, e.udt_name, c.udt_name
FROM expected e JOIN information_schema.columns c
  ON c.table_schema = 'public' AND c.table_name = e.table_name AND c.column_name = e.column_name
WHERE c.udt_name <> e.udt_name
UNION ALL
SELECT 'THIEU RANG BUOC', x.table_name, x.con_name, NULL, NULL FROM expected_con x
WHERE NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = x.con_name)
  AND NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = x.con_name)
ORDER BY 1, 2, 3;

-- Số dòng của từng bảng
SELECT table_name AS bang,
       (xpath('/row/n/text()', query_to_xml(format('SELECT count(*) AS n FROM %I', table_name), false, true, '')))[1]::text::int AS so_dong
FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1;
