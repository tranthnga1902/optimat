"""Lược đồ lưu trữ chính thức 20 bảng; models.py mô tả thêm các view tương thích.

Các view không lưu bản sao dữ liệu. Không gọi Base.metadata.create_all cho schema mới.
"""
from sqlalchemy import (MetaData, Table, Column, Integer, BigInteger, String, Text, Boolean,
                        Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index, func, text)
from sqlalchemy.dialects.postgresql import JSONB

from .models import Base as CompatibilityBase
from . import project_documents  # đăng ký đủ 28 cấu trúc cũ

metadata = MetaData()
legacy = CompatibilityBase.metadata
RENAMED = {"rough_norms": "work_norms", "takeoff_results": "analysis_runs"}
KEPT = ("users", "projects", "materials", "wall_systems", "material_relations", "suppliers",
        "supplier_materials", "price_records", "optimization_runs", "audit_logs")
RULE_KINDS = ("material_groups", "material_families", "material_aliases", "standards", "material_standards",
              "material_rules", "room_rules", "material_notes", "drawing_concepts", "convention_clauses", "model_versions")
COST_KINDS = ("vehicles", "labor_rates")
TITLES = {}


def _copy_table(old_name, new_name):
    old = legacy.tables[old_name]
    cols = []
    for c in old.columns:
        fks = []
        for f in c.foreign_keys:
            parent, field = f.target_fullname.split('.')
            if parent in KEPT or parent in RENAMED:
                fks.append(ForeignKey(f"{RENAMED.get(parent, parent)}.{field}", ondelete=f.ondelete))
        cols.append(Column(c.name, c.type, *fks, primary_key=c.primary_key, nullable=c.nullable,
                           server_default=c.server_default, autoincrement=c.autoincrement, comment=c.comment))
    constraints = []
    for k in old.constraints:
        if isinstance(k, CheckConstraint):
            constraints.append(CheckConstraint(str(k.sqltext), name=k.name))
        elif isinstance(k, UniqueConstraint):
            constraints.append(UniqueConstraint(*(c.name for c in k.columns), name=k.name))
    t = Table(new_name, metadata, *cols, *constraints, comment=old.comment, info=dict(old.info))
    for idx in old.indexes:
        expressions = [t.c[e.name] if getattr(e, 'name', None) and e.name in t.c else text(str(e)) for e in idx.expressions]
        Index(idx.name, *expressions, unique=idx.unique)
    return t


for _name in KEPT:
    _copy_table(_name, _name)
for _old, _new in RENAMED.items():
    _copy_table(_old, _new)

metadata.tables['projects'].append_column(Column('profile_revisions', JSONB, nullable=False, server_default='[]'))
metadata.tables['materials'].append_column(Column('catalog_metadata', JSONB, nullable=False, server_default='{}'))
analysis = metadata.tables['analysis_runs']
analysis.append_column(Column('kind', String(32), nullable=False, server_default='takeoff'))
analysis.append_column(Column('data_kind', String(16), nullable=False, server_default='ACTUAL'))
analysis.append_column(Column('input_snapshot', JSONB, nullable=False, server_default='{}'))
analysis.append_column(Column('schema_version', Integer, nullable=False, server_default='1'))
analysis.append_column(Column('result_sha256', String(64)))
analysis.append_constraint(UniqueConstraint('project_id', 'takeoff_id', name='uq_analysis_project_id'))
analysis.append_constraint(CheckConstraint("data_kind IN ('ACTUAL','SAMPLE','SYNTHETIC')", name='ck_analysis_data_kind'))
analysis.append_constraint(CheckConstraint("kind <> 'synthetic_housing' OR data_kind = 'SYNTHETIC'", name='ck_analysis_synthetic'))

Table('document_revisions', metadata,
      Column('document_id', BigInteger, primary_key=True),
      Column('project_id', Integer, ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False, index=True),
      Column('record_type', String(12), nullable=False),
      Column('file_id', Integer, nullable=False),
      Column('revision_id', BigInteger),
      Column('version', Integer), Column('filename', String(255), nullable=False),
      Column('format', String(16), nullable=False), Column('stored_path', Text, nullable=False),
      Column('sha256', String(64)), Column('size_bytes', BigInteger), Column('role', String(16)),
      Column('created_at', DateTime(timezone=True), nullable=False, server_default=func.now()),
      UniqueConstraint('revision_id', name='uq_document_revision_id'),
      UniqueConstraint('file_id', 'version', name='uq_document_file_version'),
      CheckConstraint("record_type IN ('file','revision')", name='ck_document_record_type'),
      CheckConstraint("record_type <> 'revision' OR (revision_id IS NOT NULL AND version IS NOT NULL AND version > 0 AND sha256 IS NOT NULL AND size_bytes IS NOT NULL AND size_bytes > 0 AND role IS NOT NULL AND role IN ('KT','KC','HO_SO','TIEN_LUONG','THAM_KHAO'))", name='ck_document_revision_required'))
Index('uq_document_file_record', metadata.tables['document_revisions'].c.file_id,
      unique=True, postgresql_where=text("record_type = 'file'"))

Table('rule_sets', metadata,
      Column('set_id', BigInteger, primary_key=True),
      Column('kind', String(48), nullable=False), Column('record_key', Text, nullable=False),
      Column('payload', JSONB, nullable=False),
      Column('version', Integer, nullable=False, server_default='1'),
      Column('updated_at', DateTime(timezone=True), nullable=False, server_default=func.now()),
      UniqueConstraint('kind', 'record_key', name='uq_rule_record'),
      CheckConstraint("jsonb_typeof(payload) = 'object' AND version > 0", name='ck_rule_payload'))
Table('cost_parameters', metadata,
      Column('parameter_id', BigInteger, primary_key=True),
      Column('kind', String(24), nullable=False), Column('record_key', Text, nullable=False),
      Column('payload', JSONB, nullable=False),
      UniqueConstraint('kind', 'record_key', name='uq_cost_record'),
      CheckConstraint("kind IN ('vehicles','labor_rates') AND jsonb_typeof(payload) = 'object'", name='ck_cost_payload'))

Table('building_elements', metadata,
      Column('element_id', BigInteger, primary_key=True),
      Column('analysis_id', Integer, ForeignKey('analysis_runs.takeoff_id', ondelete='CASCADE'), nullable=False, index=True),
      Column('element_key', String(255), nullable=False), Column('kind', String(32), nullable=False),
      Column('level_code', String(128)), Column('geometry', JSONB, nullable=False, server_default='{}'),
      Column('occurrences', JSONB, nullable=False, server_default='[]'),
      Column('relations', JSONB, nullable=False, server_default='[]'),
      Column('payload', JSONB, nullable=False, server_default='{}'),
      UniqueConstraint('analysis_id', 'element_key', name='uq_element_analysis_key'))
Table('evidence_sources', metadata,
      Column('evidence_id', BigInteger, primary_key=True),
      Column('analysis_id', Integer, ForeignKey('analysis_runs.takeoff_id', ondelete='CASCADE'), nullable=False, index=True),
      Column('kind', String(32), nullable=False),
      Column('revision_id', BigInteger, ForeignKey('document_revisions.revision_id', ondelete='RESTRICT')),
      Column('source_ref', JSONB, nullable=False, server_default='{}'),
      Column('raw_content', JSONB, nullable=False),
      Column('created_by', Integer, ForeignKey('users.user_id', ondelete='SET NULL')))
Table('element_measurements', metadata,
      Column('measurement_id', BigInteger, primary_key=True),
      Column('element_id', BigInteger, ForeignKey('building_elements.element_id', ondelete='CASCADE'), nullable=False, index=True),
      Column('property_code', String(64), nullable=False), Column('value', Numeric(20, 6)),
      Column('unit', String(24), nullable=False), Column('status', String(1), nullable=False),
      Column('selected', Boolean, nullable=False, server_default='false'),
      Column('method', String(24), nullable=False),
      Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
      CheckConstraint("status IN ('A','B','C','D') AND (value IS NOT NULL OR status = 'D')", name='ck_measurement_status'),
      CheckConstraint('NOT selected OR value IS NOT NULL', name='ck_measurement_selected'),
      CheckConstraint("method <> 'user_input' OR status IN ('C','D')", name='ck_measurement_user'))
Index('uq_measurement_selected', metadata.tables['element_measurements'].c.element_id,
      metadata.tables['element_measurements'].c.property_code, unique=True, postgresql_where=text('selected'))
Table('takeoff_items', metadata,
      Column('item_id', BigInteger, primary_key=True),
      Column('analysis_id', Integer, ForeignKey('analysis_runs.takeoff_id', ondelete='CASCADE'), nullable=False, index=True),
      Column('seq', Integer, nullable=False), Column('work_code', String(64), nullable=False),
      Column('element_id', BigInteger, ForeignKey('building_elements.element_id', ondelete='RESTRICT')),
      Column('unit', String(24), nullable=False), Column('quantity', Numeric(20, 6)),
      Column('known_part', Numeric(20, 6)), Column('status', String(1), nullable=False),
      Column('formula', Text, nullable=False, server_default=''),
      Column('input_snapshot', JSONB, nullable=False, server_default='{}'),
      Column('payload', JSONB, nullable=False),
      UniqueConstraint('analysis_id', 'seq', name='uq_takeoff_item_seq'),
      CheckConstraint("status IN ('A','B','C','D') AND (quantity IS NOT NULL OR status = 'D')", name='ck_item_status'))
Table('material_scenarios', metadata,
      Column('scenario_id', BigInteger, primary_key=True),
      Column('analysis_id', Integer, ForeignKey('analysis_runs.takeoff_id', ondelete='CASCADE'), nullable=False, index=True),
      Column('name', String(255), nullable=False), Column('origin', String(24), nullable=False),
      Column('selected', Boolean, nullable=False, server_default='false'),
      Column('assignments', JSONB, nullable=False, server_default='[]'),
      Column('requirements', JSONB, nullable=False, server_default='[]'),
      Column('catalog_snapshot', JSONB, nullable=False, server_default='{}'),
      Column('run_id', Integer, ForeignKey('optimization_runs.run_id', ondelete='RESTRICT')),
      CheckConstraint("origin IN ('design','user','proposed','optimized')", name='ck_scenario_origin'),
      CheckConstraint("origin <> 'optimized' OR run_id IS NOT NULL", name='ck_scenario_run'))
Index('uq_scenario_selected', metadata.tables['material_scenarios'].c.analysis_id,
      unique=True, postgresql_where=text('selected'))

NAMES = frozenset(metadata.tables)
assert len(NAMES) == 20, NAMES
for _name, _title in {
    'document_revisions': 'Hồ sơ và phiên bản tệp', 'analysis_runs': 'Lần nhận dạng và bóc tách',
    'building_elements': 'Cấu kiện', 'element_measurements': 'Số đo cấu kiện',
    'evidence_sources': 'Bằng chứng số đo', 'takeoff_items': 'Dòng khối lượng',
    'work_norms': 'Định mức công tác', 'cost_parameters': 'Thông số chi phí',
    'rule_sets': 'Quy tắc và dữ liệu tham chiếu', 'material_scenarios': 'Phương án và nhu cầu vật liệu',
}.items():
    metadata.tables[_name].info['title'] = _title
