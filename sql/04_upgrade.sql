-- Sinh từ scripts/build_upgrade_sql.py. Không tạo lại 28 bảng cũ.
-- Database cũ: python scripts/migrate_schema20.py --apply (backup bắt buộc).
BEGIN;
DO $$
DECLARE actual text[];
BEGIN
  SELECT array_agg(table_name::text ORDER BY table_name) INTO actual FROM information_schema.tables
  WHERE table_schema='public' AND table_type='BASE TABLE';
  IF actual IS NULL OR NOT actual <@ ARRAY['analysis_runs','audit_logs','building_elements','cost_parameters','document_revisions','element_measurements','evidence_sources','material_relations','material_scenarios','materials','optimization_runs','price_records','projects','rule_sets','supplier_materials','suppliers','takeoff_items','users','wall_systems','work_norms']::text[] THEN
    RAISE EXCEPTION 'Database chưa đúng 20 bảng. Chạy scripts/migrate_schema20.py --apply trước.';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS cost_parameters (
	parameter_id BIGSERIAL NOT NULL, 
	kind VARCHAR(24) NOT NULL, 
	record_key TEXT NOT NULL, 
	payload JSONB NOT NULL, 
	PRIMARY KEY (parameter_id), 
	CONSTRAINT uq_cost_record UNIQUE (kind, record_key), 
	CONSTRAINT ck_cost_payload CHECK (kind IN ('vehicles','labor_rates') AND jsonb_typeof(payload) = 'object')
)

;
ALTER TABLE "cost_parameters" ADD COLUMN IF NOT EXISTS parameter_id BIGSERIAL NOT NULL;
ALTER TABLE "cost_parameters" ADD COLUMN IF NOT EXISTS kind VARCHAR(24) NOT NULL;
ALTER TABLE "cost_parameters" ADD COLUMN IF NOT EXISTS record_key TEXT NOT NULL;
ALTER TABLE "cost_parameters" ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='cost_parameters'::regclass AND conname='ck_cost_payload') THEN ALTER TABLE cost_parameters ADD CONSTRAINT ck_cost_payload CHECK (kind IN ('vehicles','labor_rates') AND jsonb_typeof(payload) = 'object'); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='cost_parameters'::regclass AND conname='uq_cost_record') THEN ALTER TABLE cost_parameters ADD CONSTRAINT uq_cost_record UNIQUE (kind, record_key); END IF; END $$;

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
	raw_class VARCHAR(32), 
	catalog_metadata JSONB DEFAULT '{}' NOT NULL, 
	PRIMARY KEY (material_id), 
	CONSTRAINT ck_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC'))
)

;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) NOT NULL;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS "group" VARCHAR(64) NOT NULL;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS thickness_mm FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS unit VARCHAR(16) NOT NULL;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS qty_per_m2 FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS weight_kg_per_m2 FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS lambda_w_mk FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS labor_days_per_m2 FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS subgroup VARCHAR(128);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS family VARCHAR(32);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS usage_text VARCHAR(255);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS usage_role VARCHAR(128);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS tier INTEGER;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS purchase_unit VARCHAR(32);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS unit_conversion FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS length_mm FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS width_mm FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS height_mm FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS price_priority VARCHAR(4);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS needs_lambda BOOLEAN;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS lambda_source VARCHAR(255);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS unit_weight_kg FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS weight_source VARCHAR(255);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS transport_volume_m3 FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS waste_pct FLOAT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS waste_source VARCHAR(255);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS standards_text TEXT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS reference_brands TEXT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS tech_notes TEXT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS data_note TEXT;
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS raw_class VARCHAR(32);
ALTER TABLE "materials" ADD COLUMN IF NOT EXISTS catalog_metadata JSONB DEFAULT '{}' NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='materials'::regclass AND conname='ck_materials_data_kind') THEN ALTER TABLE materials ADD CONSTRAINT ck_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')); END IF; END $$;

CREATE TABLE IF NOT EXISTS rule_sets (
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
ALTER TABLE "rule_sets" ADD COLUMN IF NOT EXISTS set_id BIGSERIAL NOT NULL;
ALTER TABLE "rule_sets" ADD COLUMN IF NOT EXISTS kind VARCHAR(48) NOT NULL;
ALTER TABLE "rule_sets" ADD COLUMN IF NOT EXISTS record_key TEXT NOT NULL;
ALTER TABLE "rule_sets" ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL;
ALTER TABLE "rule_sets" ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT '1' NOT NULL;
ALTER TABLE "rule_sets" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='rule_sets'::regclass AND conname='uq_rule_record') THEN ALTER TABLE rule_sets ADD CONSTRAINT uq_rule_record UNIQUE (kind, record_key); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='rule_sets'::regclass AND conname='ck_rule_payload') THEN ALTER TABLE rule_sets ADD CONSTRAINT ck_rule_payload CHECK (jsonb_typeof(payload) = 'object' AND version > 0); END IF; END $$;

CREATE TABLE IF NOT EXISTS suppliers (
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
	CONSTRAINT ck_suppliers_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_suppliers_price_public CHECK (price_public IS NULL OR price_public IN ('YES', 'NO', 'PARTIAL')), 
	CONSTRAINT ck_suppliers_latlon CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180), 
	FOREIGN KEY(linked_supplier_id) REFERENCES suppliers (supplier_id) ON DELETE SET NULL
)

;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(64) NOT NULL;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS province VARCHAR(64) NOT NULL;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS lat FLOAT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS lon FLOAT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS lead_time_days FLOAT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS dealer_type VARCHAR(64);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS brands TEXT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS address VARCHAR(512);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS ward VARCHAR(128);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS district VARCHAR(128);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS maps_url VARCHAR(1024);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS phone VARCHAR(64);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS zalo VARCHAR(64);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS website VARCHAR(1024);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS facebook VARCHAR(1024);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS tax_code VARCHAR(32);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS opening_hours VARCHAR(255);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS delivers BOOLEAN;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS delivery_radius_km FLOAT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS max_truck_ton FLOAT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS min_order VARCHAR(255);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS vat_invoice BOOLEAN;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS payment VARCHAR(255);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS price_public VARCHAR(8);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS price_page_url VARCHAR(1024);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS verified BOOLEAN;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS collected_at DATE;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS collected_by VARCHAR(128);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS source VARCHAR(1024);
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE "suppliers" ADD COLUMN IF NOT EXISTS linked_supplier_id VARCHAR(64);
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='suppliers'::regclass AND conname='ck_suppliers_latlon') THEN ALTER TABLE suppliers ADD CONSTRAINT ck_suppliers_latlon CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='suppliers'::regclass AND conname='ck_suppliers_data_kind') THEN ALTER TABLE suppliers ADD CONSTRAINT ck_suppliers_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='suppliers'::regclass AND conname='ck_suppliers_price_public') THEN ALTER TABLE suppliers ADD CONSTRAINT ck_suppliers_price_public CHECK (price_public IS NULL OR price_public IN ('YES', 'NO', 'PARTIAL')); END IF; END $$;

CREATE TABLE IF NOT EXISTS users (
	user_id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255) DEFAULT '' NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(16) DEFAULT 'user' NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT users_email_key UNIQUE (email), 
	CONSTRAINT ck_users_role CHECK (role IN ('admin', 'user'))
)

;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS user_id SERIAL NOT NULL;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS email VARCHAR(255) NOT NULL;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS full_name VARCHAR(255) DEFAULT '' NOT NULL;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NOT NULL;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS role VARCHAR(16) DEFAULT 'user' NOT NULL;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT 'true' NOT NULL;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='users'::regclass AND conname='ck_users_role') THEN ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN ('admin', 'user')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='users'::regclass AND conname='users_email_key') THEN ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email); END IF; END $$;

CREATE TABLE IF NOT EXISTS work_norms (
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
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS id SERIAL NOT NULL;
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS work_code VARCHAR(32) NOT NULL;
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS variant VARCHAR(32);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS material_id VARCHAR(64);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS material_name VARCHAR(255);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS qty FLOAT;
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS qty_unit VARCHAR(64);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS qty_min FLOAT;
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS qty_max FLOAT;
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS muc_xac_nhan VARCHAR(16);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS ngay_tra VARCHAR(10);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS norm_code VARCHAR(64);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS source VARCHAR(255);
ALTER TABLE "work_norms" ADD COLUMN IF NOT EXISTS note TEXT;
CREATE INDEX IF NOT EXISTS ix_rough_norms_work_code ON work_norms (work_code);

CREATE TABLE IF NOT EXISTS audit_logs (
	log_id BIGSERIAL NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(64) NOT NULL, 
	detail JSONB DEFAULT '{}' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE SET NULL
)

;
ALTER TABLE "audit_logs" ADD COLUMN IF NOT EXISTS log_id BIGSERIAL NOT NULL;
ALTER TABLE "audit_logs" ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE "audit_logs" ADD COLUMN IF NOT EXISTS action VARCHAR(64) NOT NULL;
ALTER TABLE "audit_logs" ADD COLUMN IF NOT EXISTS detail JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "audit_logs" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);

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
)

;
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS id SERIAL NOT NULL;
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) NOT NULL;
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS relation_type VARCHAR(16) NOT NULL;
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS related_material_id VARCHAR(64) NOT NULL;
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS quantity FLOAT;
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS quantity_unit VARCHAR(64);
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS source VARCHAR(255);
ALTER TABLE "material_relations" ADD COLUMN IF NOT EXISTS note TEXT;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='material_relations'::regclass AND conname='ck_material_relations_type') THEN ALTER TABLE material_relations ADD CONSTRAINT ck_material_relations_type CHECK (relation_type IN ('REQUIRES', 'COMPOSED_OF')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='material_relations'::regclass AND conname='material_relations_material_id_related_material_id_rela_f54c') THEN ALTER TABLE material_relations ADD CONSTRAINT material_relations_material_id_related_material_id_rela_f54c UNIQUE (material_id, related_material_id, relation_type); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_material_relations_material_id ON material_relations (material_id);

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
	CONSTRAINT ck_price_records_supplier CHECK (supplier_id IS NOT NULL OR price_level = 'BULLETIN'), 
	CONSTRAINT ck_price_records_price_level CHECK (price_level IN ('DEALER', 'QUOTE', 'BULLETIN')), 
	CONSTRAINT ck_price_records_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')), 
	CONSTRAINT ck_price_records_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_price_records_positive CHECK (unit_price > 0), 
	FOREIGN KEY(material_id) REFERENCES materials (material_id), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (supplier_id)
)

;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS id BIGSERIAL NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS date DATE NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(64);
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS province VARCHAR(64) NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS quantity FLOAT NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS unit VARCHAR(16) NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS unit_price FLOAT NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS vat_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS transport_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS source VARCHAR(1024) DEFAULT '' NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE "price_records" ADD COLUMN IF NOT EXISTS price_level VARCHAR(16) DEFAULT 'DEALER' NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='price_records'::regclass AND conname='ck_price_records_basis') THEN ALTER TABLE price_records ADD CONSTRAINT ck_price_records_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='price_records'::regclass AND conname='ck_price_records_supplier') THEN ALTER TABLE price_records ADD CONSTRAINT ck_price_records_supplier CHECK (supplier_id IS NOT NULL OR price_level = 'BULLETIN'); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='price_records'::regclass AND conname='ck_price_records_data_kind') THEN ALTER TABLE price_records ADD CONSTRAINT ck_price_records_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='price_records'::regclass AND conname='ck_price_records_price_level') THEN ALTER TABLE price_records ADD CONSTRAINT ck_price_records_price_level CHECK (price_level IN ('DEALER', 'QUOTE', 'BULLETIN')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='price_records'::regclass AND conname='ck_price_records_positive') THEN ALTER TABLE price_records ADD CONSTRAINT ck_price_records_positive CHECK (unit_price > 0); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_price_records_lookup ON price_records (material_id, supplier_id, date);
CREATE UNIQUE INDEX IF NOT EXISTS uq_price_records_dedup ON price_records (material_id, COALESCE(supplier_id, ''), date, quantity, source);

CREATE TABLE IF NOT EXISTS projects (
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
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS project_id SERIAL NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS user_id INTEGER NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS address VARCHAR(512) DEFAULT '' NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS site_lat FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS site_lon FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS floor_height_mm FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS door_width_mm FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS door_height_mm FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS window_width_mm FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS window_height_mm FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS budget FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS deadline_days FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS max_vehicle_ton FLOAT;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS excluded_materials JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE "projects" ADD COLUMN IF NOT EXISTS profile_revisions JSONB DEFAULT '[]' NOT NULL;
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id);

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
	quote_reference VARCHAR(1024), 
	valid_until DATE, 
	lead_time_days FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT supplier_materials_supplier_id_material_id_key UNIQUE (supplier_id, material_id), 
	CONSTRAINT ck_supplier_materials_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')), 
	CONSTRAINT ck_supplier_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')), 
	CONSTRAINT ck_supplier_materials_price_level CHECK (price_level IS NULL OR price_level IN ('DEALER', 'QUOTE')), 
	CONSTRAINT ck_supplier_materials_price_complete CHECK (base_price IS NULL OR (base_price > 0 AND price_level IS NOT NULL AND price_date IS NOT NULL)), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (supplier_id) ON DELETE CASCADE, 
	FOREIGN KEY(material_id) REFERENCES materials (material_id) ON DELETE CASCADE
)

;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS id SERIAL NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(64) NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS base_price FLOAT;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS product_url VARCHAR(1024);
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS collected_at DATE NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS dealer_product_name VARCHAR(255);
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS brand VARCHAR(128);
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS sale_unit VARCHAR(32);
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS unit_conversion FLOAT;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS price_level VARCHAR(16);
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS price_date DATE;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS vat_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS transport_included VARCHAR(8) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS in_stock BOOLEAN;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS quote_reference VARCHAR(1024);
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS valid_until DATE;
ALTER TABLE "supplier_materials" ADD COLUMN IF NOT EXISTS lead_time_days FLOAT;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='supplier_materials'::regclass AND conname='ck_supplier_materials_basis') THEN ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_basis CHECK (vat_included IN ('YES', 'NO', 'UNKNOWN') AND transport_included IN ('YES', 'NO', 'UNKNOWN')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='supplier_materials'::regclass AND conname='ck_supplier_materials_price_level') THEN ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_price_level CHECK (price_level IS NULL OR price_level IN ('DEALER', 'QUOTE')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='supplier_materials'::regclass AND conname='ck_supplier_materials_price_complete') THEN ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_price_complete CHECK (base_price IS NULL OR (base_price > 0 AND price_level IS NOT NULL AND price_date IS NOT NULL)); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='supplier_materials'::regclass AND conname='supplier_materials_supplier_id_material_id_key') THEN ALTER TABLE supplier_materials ADD CONSTRAINT supplier_materials_supplier_id_material_id_key UNIQUE (supplier_id, material_id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='supplier_materials'::regclass AND conname='ck_supplier_materials_data_kind') THEN ALTER TABLE supplier_materials ADD CONSTRAINT ck_supplier_materials_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')); END IF; END $$;

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
)

;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS wall_system_id VARCHAR(64) NOT NULL;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS material_id VARCHAR(64) NOT NULL;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS wall_thickness_mm FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS detect_class VARCHAR(8);
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS role VARCHAR(16);
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS masonry_thickness_mm FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS norm_code VARCHAR(32);
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS units_per_m3 FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS mortar_m3_per_m3 FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS labor_day_per_m3 FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS unit_factor FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS mortar_material_id VARCHAR(64);
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS mortar_density FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS r0_reference FLOAT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS norm_source VARCHAR(255);
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE "wall_systems" ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='wall_systems'::regclass AND conname='ck_wall_systems_data_kind') THEN ALTER TABLE wall_systems ADD CONSTRAINT ck_wall_systems_data_kind CHECK (data_kind IN ('ACTUAL', 'SAMPLE', 'SYNTHETIC')); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_wall_systems_material_id ON wall_systems (material_id);

CREATE TABLE IF NOT EXISTS analysis_runs (
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
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS takeoff_id SERIAL NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS project_id INTEGER NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS file_id INTEGER;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS result JSONB NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS layer_overrides JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS kind VARCHAR(32) DEFAULT 'takeoff' NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS data_kind VARCHAR(16) DEFAULT 'ACTUAL' NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS input_snapshot JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS schema_version INTEGER DEFAULT '1' NOT NULL;
ALTER TABLE "analysis_runs" ADD COLUMN IF NOT EXISTS result_sha256 VARCHAR(64);
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='analysis_runs'::regclass AND conname='ck_analysis_synthetic') THEN ALTER TABLE analysis_runs ADD CONSTRAINT ck_analysis_synthetic CHECK (kind <> 'synthetic_housing' OR data_kind = 'SYNTHETIC'); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='analysis_runs'::regclass AND conname='ck_analysis_data_kind') THEN ALTER TABLE analysis_runs ADD CONSTRAINT ck_analysis_data_kind CHECK (data_kind IN ('ACTUAL','SAMPLE','SYNTHETIC')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='analysis_runs'::regclass AND conname='uq_analysis_project_id') THEN ALTER TABLE analysis_runs ADD CONSTRAINT uq_analysis_project_id UNIQUE (project_id, takeoff_id); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_takeoff_results_project_id ON analysis_runs (project_id);

CREATE TABLE IF NOT EXISTS document_revisions (
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
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS document_id BIGSERIAL NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS project_id INTEGER NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS record_type VARCHAR(12) NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS file_id INTEGER NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS revision_id BIGINT;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS version INTEGER;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS filename VARCHAR(255) NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS format VARCHAR(16) NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS stored_path TEXT NOT NULL;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS sha256 VARCHAR(64);
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS size_bytes BIGINT;
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS role VARCHAR(16);
ALTER TABLE "document_revisions" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='document_revisions'::regclass AND conname='ck_document_record_type') THEN ALTER TABLE document_revisions ADD CONSTRAINT ck_document_record_type CHECK (record_type IN ('file','revision')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='document_revisions'::regclass AND conname='uq_document_revision_id') THEN ALTER TABLE document_revisions ADD CONSTRAINT uq_document_revision_id UNIQUE (revision_id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='document_revisions'::regclass AND conname='ck_document_revision_required') THEN ALTER TABLE document_revisions ADD CONSTRAINT ck_document_revision_required CHECK (record_type <> 'revision' OR (revision_id IS NOT NULL AND version IS NOT NULL AND version > 0 AND sha256 IS NOT NULL AND size_bytes IS NOT NULL AND size_bytes > 0 AND role IS NOT NULL AND role IN ('KT','KC','HO_SO','TIEN_LUONG','THAM_KHAO'))); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='document_revisions'::regclass AND conname='uq_document_file_version') THEN ALTER TABLE document_revisions ADD CONSTRAINT uq_document_file_version UNIQUE (file_id, version); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_document_revisions_project_id ON document_revisions (project_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_document_file_record ON document_revisions (file_id) WHERE record_type = 'file';

CREATE TABLE IF NOT EXISTS building_elements (
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
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS element_id BIGSERIAL NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS analysis_id INTEGER NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS element_key VARCHAR(255) NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS kind VARCHAR(32) NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS level_code VARCHAR(128);
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS geometry JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS occurrences JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS relations JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "building_elements" ADD COLUMN IF NOT EXISTS payload JSONB DEFAULT '{}' NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='building_elements'::regclass AND conname='uq_element_analysis_key') THEN ALTER TABLE building_elements ADD CONSTRAINT uq_element_analysis_key UNIQUE (analysis_id, element_key); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_building_elements_analysis_id ON building_elements (analysis_id);

CREATE TABLE IF NOT EXISTS evidence_sources (
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
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS evidence_id BIGSERIAL NOT NULL;
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS analysis_id INTEGER NOT NULL;
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS kind VARCHAR(32) NOT NULL;
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS revision_id BIGINT;
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS source_ref JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS raw_content JSONB NOT NULL;
ALTER TABLE "evidence_sources" ADD COLUMN IF NOT EXISTS created_by INTEGER;
CREATE INDEX IF NOT EXISTS ix_evidence_sources_analysis_id ON evidence_sources (analysis_id);

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
	FOREIGN KEY(takeoff_id) REFERENCES analysis_runs (takeoff_id) ON DELETE SET NULL
)

;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS run_id SERIAL NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS project_id INTEGER NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS takeoff_id INTEGER;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS model_version VARCHAR(32);
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS method VARCHAR(16) NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS solutions JSONB NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS chosen_index INTEGER;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS price_snapshot_date DATE;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS llm_model VARCHAR(64);
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS tool_calls JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS excluded_materials JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "optimization_runs" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;
CREATE INDEX IF NOT EXISTS ix_optimization_runs_project_id ON optimization_runs (project_id);

CREATE TABLE IF NOT EXISTS element_measurements (
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
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS measurement_id BIGSERIAL NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS element_id BIGINT NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS property_code VARCHAR(64) NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS value NUMERIC(20, 6);
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS unit VARCHAR(24) NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS status VARCHAR(1) NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS selected BOOLEAN DEFAULT 'false' NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS method VARCHAR(24) NOT NULL;
ALTER TABLE "element_measurements" ADD COLUMN IF NOT EXISTS evidence_ids JSONB DEFAULT '[]' NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='element_measurements'::regclass AND conname='ck_measurement_status') THEN ALTER TABLE element_measurements ADD CONSTRAINT ck_measurement_status CHECK (status IN ('A','B','C','D') AND (value IS NOT NULL OR status = 'D')); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='element_measurements'::regclass AND conname='ck_measurement_selected') THEN ALTER TABLE element_measurements ADD CONSTRAINT ck_measurement_selected CHECK (NOT selected OR value IS NOT NULL); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='element_measurements'::regclass AND conname='ck_measurement_user') THEN ALTER TABLE element_measurements ADD CONSTRAINT ck_measurement_user CHECK (method <> 'user_input' OR status IN ('C','D')); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_element_measurements_element_id ON element_measurements (element_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_measurement_selected ON element_measurements (element_id, property_code) WHERE selected;

CREATE TABLE IF NOT EXISTS material_scenarios (
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
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS scenario_id BIGSERIAL NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS analysis_id INTEGER NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS origin VARCHAR(24) NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS selected BOOLEAN DEFAULT 'false' NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS assignments JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS requirements JSONB DEFAULT '[]' NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS catalog_snapshot JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "material_scenarios" ADD COLUMN IF NOT EXISTS run_id INTEGER;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='material_scenarios'::regclass AND conname='ck_scenario_run') THEN ALTER TABLE material_scenarios ADD CONSTRAINT ck_scenario_run CHECK (origin <> 'optimized' OR run_id IS NOT NULL); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='material_scenarios'::regclass AND conname='ck_scenario_origin') THEN ALTER TABLE material_scenarios ADD CONSTRAINT ck_scenario_origin CHECK (origin IN ('design','user','proposed','optimized')); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_material_scenarios_analysis_id ON material_scenarios (analysis_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_scenario_selected ON material_scenarios (analysis_id) WHERE selected;

CREATE TABLE IF NOT EXISTS takeoff_items (
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
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS item_id BIGSERIAL NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS analysis_id INTEGER NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS seq INTEGER NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS work_code VARCHAR(64) NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS element_id BIGINT;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS unit VARCHAR(24) NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS quantity NUMERIC(20, 6);
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS known_part NUMERIC(20, 6);
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS status VARCHAR(1) NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS formula TEXT DEFAULT '' NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS input_snapshot JSONB DEFAULT '{}' NOT NULL;
ALTER TABLE "takeoff_items" ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='takeoff_items'::regclass AND conname='uq_takeoff_item_seq') THEN ALTER TABLE takeoff_items ADD CONSTRAINT uq_takeoff_item_seq UNIQUE (analysis_id, seq); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='takeoff_items'::regclass AND conname='ck_item_status') THEN ALTER TABLE takeoff_items ADD CONSTRAINT ck_item_status CHECK (status IN ('A','B','C','D') AND (quantity IS NOT NULL OR status = 'D')); END IF; END $$;
CREATE INDEX IF NOT EXISTS ix_takeoff_items_analysis_id ON takeoff_items (analysis_id);

CREATE OR REPLACE VIEW v_price_training AS
SELECT p.id,p.date,p.material_id,p.supplier_id,p.province,p.quantity,p.unit,p.unit_price,
       p.vat_included,p.transport_included,p.price_level,p.source,
       m.name AS material_name,m."group" AS material_group,m.family,m.tier,m.unit AS material_unit,
       s.district AS supplier_district,s.dealer_type,s.lat AS supplier_lat,s.lon AS supplier_lon
FROM price_records p JOIN materials m ON m.material_id=p.material_id
LEFT JOIN suppliers s ON s.supplier_id=p.supplier_id WHERE p.data_kind='ACTUAL';

COMMIT;
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;
