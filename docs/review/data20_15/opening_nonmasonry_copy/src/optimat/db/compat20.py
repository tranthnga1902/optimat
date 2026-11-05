"""View chuyển tiếp cho API/CSV cũ trên đúng 20 bảng vật lý."""
import re
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, CreateIndex

from .schema20 import metadata, legacy, KEPT, RENAMED, RULE_KINDS, COST_KINDS

DIALECT = postgresql.dialect()


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _expr(expr, columns):
    # Biểu thức từ metadata tin cậy; chỉ thay tên cột ngoài chuỗi SQL.
    parts = re.split(r"('(?:''|[^'])*')", expr)
    for i in range(0, len(parts), 2):
        for c in sorted(columns, key=lambda c: -len(c.name)):
            parts[i] = re.sub(r'(?<![\w.])' + re.escape(c.name) + r'(?![\w])', 'r.' + quote(c.name), parts[i])
    return ''.join(parts)


def json_view_sql(name, storage):
    t = legacy.tables[name]
    cols = list(t.columns)
    pk = list(t.primary_key.columns)
    fields = ', '.join(f'(payload ->> {literal(c.name)})::{c.type.compile(dialect=DIALECT)} AS {quote(c.name)}'
                       if str(c.type) != 'JSONB' else f'payload -> {literal(c.name)} AS {quote(c.name)}' for c in cols)
    statements = [f'CREATE VIEW {quote(name)} AS SELECT {fields} FROM {storage} WHERE kind = {literal(name)};']
    for c in cols:
        if c.primary_key and str(c.type) in ('INTEGER', 'BIGINT'):
            seq = f'compat_{name}_{c.name}_seq'
            statements += [f'CREATE SEQUENCE {quote(seq)};',
                           f'ALTER VIEW {quote(name)} ALTER COLUMN {quote(c.name)} SET DEFAULT nextval({literal(seq)});']
        elif c.server_default is not None:
            arg=c.server_default.arg
            default=literal(arg) if isinstance(arg,str) else str(arg.compile(dialect=DIALECT))
            statements.append(f'ALTER VIEW {quote(name)} ALTER COLUMN {quote(c.name)} SET DEFAULT {default};')
    checks = []
    for c in cols:
        if not c.nullable:
            checks.append(f"IF r.{quote(c.name)} IS NULL THEN RAISE EXCEPTION 'Cột {name}.{c.name} không được trống' USING ERRCODE='23502'; END IF;")
        for fk in c.foreign_keys:
            parent, field = fk.target_fullname.split('.')
            checks.append(f"IF r.{quote(c.name)} IS NOT NULL AND NOT EXISTS (SELECT 1 FROM {quote(parent)} WHERE {quote(field)} = r.{quote(c.name)}) THEN RAISE EXCEPTION 'Tham chiếu {name}.{c.name} không hợp lệ' USING ERRCODE='23503'; END IF;")
    for k in t.constraints:
        if isinstance(k, CheckConstraint):
            checks.append(f"IF ({_expr(str(k.sqltext), cols)}) IS FALSE THEN RAISE EXCEPTION 'Vi phạm {k.name}' USING ERRCODE='23514', CONSTRAINT={literal(k.name or 'compat_check')}; END IF;")
        if isinstance(k, UniqueConstraint):
            equal = ' AND '.join(f'v.{quote(c.name)} = r.{quote(c.name)}' for c in k.columns)
            not_same = ' OR '.join(f'v.{quote(c.name)} IS DISTINCT FROM r.{quote(c.name)}' for c in pk)
            checks.append(f"IF EXISTS (SELECT 1 FROM {quote(name)} v WHERE {equal} AND ({not_same})) THEN RAISE EXCEPTION 'Trùng khóa {name}' USING ERRCODE='23505', CONSTRAINT={literal(k.name or name+'_unique')}; END IF;")
    keys = ', '.join(f'r.{quote(c.name)}' for c in pk)
    statements.append(f'''CREATE FUNCTION compat_validate_{name}(body jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r {quote(name)}%ROWTYPE;
BEGIN
  SELECT * INTO r FROM jsonb_populate_record(NULL::{quote(name)}, body);
  {' '.join(checks)}
  RETURN to_jsonb(r);
END $$;''')
    newkey = ', '.join(f'NEW.{quote(c.name)}' for c in pk)
    oldkey = ', '.join(f'OLD.{quote(c.name)}' for c in pk)
    statements.append(f'''CREATE FUNCTION compat_write_{name}() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM {storage} WHERE kind={literal(name)} AND record_key=jsonb_build_array({oldkey})::text;
    RETURN OLD;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF jsonb_build_array({newkey}) IS DISTINCT FROM jsonb_build_array({oldkey}) THEN
      RAISE EXCEPTION 'Không đổi khóa của {name}' USING ERRCODE='23514';
    END IF;
    UPDATE {storage} SET payload=to_jsonb(NEW) WHERE kind={literal(name)} AND record_key=jsonb_build_array({oldkey})::text;
  ELSE
    INSERT INTO {storage}(kind,record_key,payload) VALUES ({literal(name)},jsonb_build_array({newkey})::text,to_jsonb(NEW));
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER compat_write INSTEAD OF INSERT OR UPDATE OR DELETE ON {quote(name)}
FOR EACH ROW EXECUTE FUNCTION compat_write_{name}();''')
    return statements


def compatibility_sql():
    sql = []
    for old, new in RENAMED.items():
        columns = ','.join(quote(c.name) for c in legacy.tables[old].columns)
        sql.append(f'CREATE VIEW {quote(old)} AS SELECT {columns} FROM {quote(new)};')
    # Tạo hết view trước: bộ kiểm tra FK có thể tham chiếu view tạo sau.
    bodies = []
    for name in (*RULE_KINDS, *COST_KINDS):
        parts = json_view_sql(name, 'rule_sets' if name in RULE_KINDS else 'cost_parameters')
        sql.extend(x for x in parts if not x.startswith('CREATE FUNCTION'))
        bodies.extend(x for x in parts if x.startswith('CREATE FUNCTION'))
    sql.extend(bodies)
    for storage, kinds in [('rule_sets', RULE_KINDS), ('cost_parameters', COST_KINDS)]:
        cases = ' '.join(f"WHEN {literal(n)} THEN NEW.payload := compat_validate_{n}(NEW.payload); expected_key := jsonb_build_array({', '.join('(NEW.payload->'+literal(c.name)+')' for c in legacy.tables[n].primary_key.columns)})::text;" for n in kinds)
        version_update="IF TG_OP='UPDATE' THEN NEW.version := OLD.version + CASE WHEN NEW.payload IS DISTINCT FROM OLD.payload THEN 1 ELSE 0 END; NEW.updated_at:=now(); END IF;" if storage=='rule_sets' else ''
        sql.append(f'''CREATE FUNCTION validate_{storage}() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected_key text;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended({literal(storage)} || NEW.kind,20));
  IF TG_OP='UPDATE' AND (NEW.kind IS DISTINCT FROM OLD.kind OR NEW.record_key IS DISTINCT FROM OLD.record_key) THEN
    RAISE EXCEPTION 'Không đổi khóa hoặc loại dữ liệu' USING ERRCODE='23514';
  END IF;
  CASE NEW.kind {cases} ELSE RAISE EXCEPTION 'Loại dữ liệu không được hỗ trợ: %', NEW.kind USING ERRCODE='23514'; END CASE;
  IF NEW.record_key <> expected_key THEN RAISE EXCEPTION 'Khóa dữ liệu không khớp nội dung' USING ERRCODE='23514'; END IF;
  {version_update}
  RETURN NEW;
END $$;
CREATE TRIGGER validate_payload BEFORE INSERT OR UPDATE ON {storage} FOR EACH ROW EXECUTE FUNCTION validate_{storage}();''')
    sql.extend(DOCUMENT_SQL)
    sql.extend(INTEGRITY_SQL)
    result='\n\n'.join(sql).replace('CREATE FUNCTION ', 'CREATE OR REPLACE FUNCTION ').replace('CREATE SEQUENCE ', 'CREATE SEQUENCE IF NOT EXISTS ')
    # View đã kiểm quyền DML trước khi gọi trigger; definer chỉ ghi phần dữ liệu của view.
    # search_path cố định tránh đối tượng tạm do caller tạo che khuất bảng ứng dụng.
    return result.replace('RETURNS trigger LANGUAGE plpgsql AS $$',
                          'RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$')


DOCUMENT_SQL = [r'''
CREATE SEQUENCE compat_file_id_seq;
CREATE SEQUENCE compat_revision_id_seq;
CREATE SEQUENCE compat_profile_revision_id_seq;
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
''', r'''
CREATE FUNCTION compat_write_file() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION compat_write_revision() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION compat_write_profile() RETURNS trigger LANGUAGE plpgsql AS $$
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
''']

INTEGRITY_SQL = [r'''
CREATE FUNCTION validate_material20() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION protect_reference20() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION validate_analysis20() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.file_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM project_files WHERE file_id=NEW.file_id AND project_id=NEW.project_id) THEN
    RAISE EXCEPTION 'Tệp không thuộc dự án của lần bóc' USING ERRCODE='23503';
  END IF;
  NEW.kind := COALESCE(NEW.result->>'kind',NEW.kind,'takeoff');
  IF NEW.kind='synthetic_housing' THEN NEW.data_kind := 'SYNTHETIC'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER validate_analysis BEFORE INSERT OR UPDATE ON analysis_runs FOR EACH ROW EXECUTE FUNCTION validate_analysis20();
CREATE FUNCTION protect_snapshot20() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.result_sha256 IS NOT NULL AND (NEW.result_sha256 IS DISTINCT FROM OLD.result_sha256 OR NEW.result IS DISTINCT FROM OLD.result OR NEW.input_snapshot IS DISTINCT FROM OLD.input_snapshot
    OR NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.file_id IS DISTINCT FROM OLD.file_id) THEN
    RAISE EXCEPTION 'Snapshot đã lưu; hãy tạo lần phân tích mới' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER protect_snapshot BEFORE UPDATE ON analysis_runs FOR EACH ROW EXECUTE FUNCTION protect_snapshot20();
CREATE FUNCTION validate_document20() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION protect_evidence20() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION protect_analysis_child20() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE FUNCTION validate_links20() RETURNS trigger LANGUAGE plpgsql AS $$
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
''']


def schema_sql():
    chunks = ['-- OptiMat AI: đúng 20 bảng vật lý; các tên cũ là view tương thích.']
    for t in metadata.sorted_tables:
        chunks.append(str(CreateTable(t).compile(dialect=DIALECT)) + ';')
        chunks.extend(str(CreateIndex(i).compile(dialect=DIALECT)) + ';' for i in sorted(t.indexes, key=lambda i:i.name))
    return '\n\n'.join(chunks) + '\n\n' + compatibility_sql()


def create_schema(conn):
    metadata.create_all(conn)
    with conn.connection.driver_connection.cursor() as cursor:
        cursor.execute(compatibility_sql())


def initialize_database(engine, reset=False):
    """Khởi tạo mới hoặc reset có chủ ý; không tự chuyển đổi database có dữ liệu."""
    from sqlalchemy import inspect
    from .schema20 import NAMES
    with engine.begin() as conn:
        have=set(inspect(conn).get_table_names())
        if reset:
            unknown=have-set(legacy.tables)-NAMES
            if unknown:
                raise ValueError('Không reset database có bảng ngoài ứng dụng: '+', '.join(sorted(unknown)))
            for name in inspect(conn).get_view_names():
                conn.exec_driver_sql(f'DROP VIEW IF EXISTS {quote(name)} CASCADE')
            if have:
                conn.exec_driver_sql('DROP TABLE '+','.join(quote(n) for n in sorted(have))+' CASCADE')
            have=set()
        if not have:
            create_schema(conn)
        elif have != NAMES:
            raise ValueError('Database chưa dùng 20 bảng. Chạy scripts/migrate_schema20.py --apply để sao lưu và chuyển dữ liệu trước.')
