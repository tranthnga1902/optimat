"""Chuyển đổi giao dịch: kiểm kê, chuyển dữ liệu, đối chiếu tất cả view rồi commit.

CLI phải tạo pg_dump trước khi gọi migrate(). Không dùng --reset cho database người dùng.
"""
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import inspect, text, select, func

from .schema20 import metadata, legacy, NAMES, KEPT, RENAMED, RULE_KINDS, COST_KINDS
from .compat20 import quote, create_schema


def _json(value):
    return json.dumps(value, ensure_ascii=False, default=lambda x: x.isoformat() if isinstance(x, (date, datetime)) else float(x) if isinstance(x, Decimal) else str(x))


def _rows(conn, name):
    return conn.execute(text(f'SELECT to_jsonb(t) FROM {quote(name)} t')).scalars().all()


def _canonical(rows, columns):
    return sorted(_json({c: r.get(c) for c in columns}) for r in rows)


def physical_tables(conn):
    return set(inspect(conn).get_table_names(schema='public'))


def _grants(conn):
    return conn.execute(text("""SELECT c.relname,CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE r.rolname END AS grantee,
        a.privilege_type,a.is_grantable FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL aclexplode(c.relacl) a LEFT JOIN pg_roles r ON r.oid=a.grantee
        WHERE n.nspname='public' AND c.relkind IN ('r','v') AND a.grantee<>c.relowner"""
    )).mappings().all()


def _restore_grants(conn, rows, have, reporting):
    allowed={'SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'}
    grants={}
    for r in rows:
        if r['privilege_type'] in allowed:
            grants.setdefault(r['relname'],{}).setdefault(r['grantee'],{})[r['privilege_type']]=r['is_grantable']
    def apply(name,role,privileges,view=False):
        role_sql='PUBLIC' if role=='PUBLIC' else quote(role)
        for privilege,option in privileges.items():
            if view and privilege not in {'SELECT','INSERT','UPDATE','DELETE'}:continue
            conn.exec_driver_sql(f'GRANT {privilege} ON {quote(name)} TO {role_sql}'+(' WITH GRANT OPTION' if option else ''))
    def target(old):
        if old in RULE_KINDS:return 'rule_sets'
        if old in COST_KINDS:return 'cost_parameters'
        if old in ('project_files','project_document_revisions'):return 'document_revisions'
        if old=='project_profile_revisions':return 'projects'
        return RENAMED.get(old,old)
    physical={}
    for name in NAMES:
        parents=[n for n in have if target(n)==name]
        if not parents:parents=['takeoff_results'] if 'takeoff_results' in have else []
        roles=set.intersection(*(set(grants.get(n,{})) for n in parents)) if parents else set()
        for role in roles:
            common=set.intersection(*(set(grants[n][role]) for n in parents))
            privileges={p:all(grants[n][role][p] for n in parents) for p in common}
            apply(name,role,privileges)
            physical.setdefault(name,{})[role]=privileges
    for name,roles in grants.items():
        if name not in NAMES:
            for role,privileges in roles.items():apply(name,role,privileges,view=True)
    # Các sequence mới phải dùng được với quyền INSERT đã phục hồi.
    sequence_roles={}
    for name,roles in physical.items():
        for c in metadata.tables[name].primary_key:
            seq=conn.execute(text('SELECT pg_get_serial_sequence(:t,:c)'),{'t':name,'c':c.name}).scalar()
            if seq:
                sequence_roles.setdefault(seq,set()).update(r for r,p in roles.items() if 'INSERT' in p)
    for name in (*RULE_KINDS,*COST_KINDS):
        for c in legacy.tables[name].primary_key:
            if c.type.__class__.__name__ in ('Integer','BigInteger'):
                seq=f'compat_{name}_{c.name}_seq'
                sequence_roles.setdefault(seq,set()).update(r for r,p in grants.get(name,{}).items() if 'INSERT' in p)
    for name,seq in [('project_files','compat_file_id_seq'),('project_document_revisions','compat_revision_id_seq'),('project_profile_revisions','compat_profile_revision_id_seq')]:
        sequence_roles.setdefault(seq,set()).update(r for r,p in grants.get(name,{}).items() if 'INSERT' in p)
    for seq,roles in sequence_roles.items():
        for role in roles:
            role_sql='PUBLIC' if role=='PUBLIC' else quote(role)
            # pg_get_serial_sequence trả qualified name đã được PostgreSQL quote.
            conn.exec_driver_sql(f'GRANT USAGE, SELECT ON SEQUENCE {seq} TO {role_sql}')
    return sum(len(v) for v in physical.values())


def _insert_legacy(conn, name, row):
    columns = list(legacy.tables[name].columns.keys())
    fields = ','.join(quote(c) for c in columns)
    # jsonb_populate_record chuyển ngày/giờ và kiểu số theo row type của bảng/view.
    conn.execute(text(f'INSERT INTO {quote(name)} ({fields}) SELECT {fields} FROM jsonb_populate_record(NULL::{quote(name)}, CAST(:body AS jsonb))'), {'body': _json(row)})


def reset_sequences(conn):
    for t in metadata.tables.values():
        for c in t.primary_key:
            if c.type.__class__.__name__ in ('Integer', 'BigInteger'):
                seq = conn.execute(text('SELECT pg_get_serial_sequence(:t,:c)'), {'t': t.name, 'c': c.name}).scalar()
                if seq:
                    maximum = conn.exec_driver_sql(f'SELECT max({quote(c.name)}) FROM {quote(t.name)}').scalar()
                    conn.execute(text('SELECT setval(CAST(:seq AS regclass),:n,:called)'), {'seq':seq,'n':maximum or 1,'called':maximum is not None})
    pairs = [('project_files','file_id','compat_file_id_seq'),
             ('project_document_revisions','revision_id','compat_revision_id_seq'),
             ('project_profile_revisions','revision_id','compat_profile_revision_id_seq')]
    for name in (*RULE_KINDS,*COST_KINDS):
        for c in legacy.tables[name].primary_key:
            if c.type.__class__.__name__ in ('Integer','BigInteger'):
                pairs.append((name,c.name,f'compat_{name}_{c.name}_seq'))
    for table,col,seq in pairs:
        maximum=conn.exec_driver_sql(f'SELECT max({quote(col)}) FROM {quote(table)}').scalar()
        conn.execute(text('SELECT setval(CAST(:seq AS regclass),:n,:called)'),{'seq':seq,'n':maximum or 1,'called':maximum is not None})


def migrate(conn):
    """Gọi trong engine.begin(); lỗi bất kỳ phải rollback toàn bộ giao dịch."""
    conn.exec_driver_sql("SELECT pg_advisory_xact_lock(2041104,20)")
    have = physical_tables(conn)
    if have == NAMES:
        return {'changed':False,'tables':20,'message':'Database đã dùng lược đồ 20 bảng.'}
    unknown = have - set(legacy.tables)
    if unknown:
        raise ValueError('Có bảng ngoài lược đồ đã biết; chưa chuyển đổi: '+', '.join(sorted(unknown)))
    if not have:
        create_schema(conn)
        return {'changed':True,'tables':20,'legacy_rows':{}}
    # Không xóa bảng mà metadata chưa mô tả đủ cột; không bỏ dữ liệu mở rộng âm thầm.
    inspector=inspect(conn)
    custom=conn.execute(text("""SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
       WHERE n.nspname='public' AND c.relkind='r' AND
       (c.relrowsecurity OR c.relforcerowsecurity OR pg_get_userbyid(c.relowner)<>current_user)""")).scalars().all()
    triggers=conn.execute(text("""SELECT t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
       JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal""")).scalars().all()
    if custom or triggers:
        raise ValueError('Có RLS, owner khác hoặc trigger tùy chỉnh; cần hợp đồng chuyển quyền/chuyển logic riêng trước khi đổi schema.')
    for name in have:
        actual={c['name'] for c in inspector.get_columns(name)}
        expected=set(legacy.tables[name].columns.keys())
        if actual != expected:
            raise ValueError(f'Cột của {name} khác metadata; cần đối chiếu trước khi chuyển đổi.')
    conn.exec_driver_sql('LOCK TABLE '+','.join(quote(n) for n in sorted(have))+' IN ACCESS EXCLUSIVE MODE')
    before={n:_rows(conn,n) for n in have}
    grants=_grants(conn)
    # View ngoài ứng dụng có thể chứa nghiệp vụ riêng; không xóa ngầm.
    unknown_views=set(inspector.get_view_names())-{'v_price_training','v_wall_systems'}
    if unknown_views:
        raise ValueError('Có view ngoài lược đồ cần xử lý trước: '+', '.join(sorted(unknown_views)))
    reporting={name:conn.execute(text('SELECT pg_get_viewdef(CAST(:n AS regclass),true)'),{'n':name}).scalar_one()
               for name in inspector.get_view_names()}
    reporting_before={name:_rows(conn,name) for name in reporting}
    for name in ('v_price_training','v_wall_systems'):
        conn.exec_driver_sql(f'DROP VIEW IF EXISTS {quote(name)}')
    # Chỉ các bảng đã khóa/đọc và đối chiếu. Giao dịch bảo đảm rollback DDL + dữ liệu.
    conn.exec_driver_sql('DROP TABLE '+','.join(quote(n) for n in sorted(have))+' CASCADE')
    create_schema(conn)
    for t in legacy.sorted_tables:
        for row in before.get(t.name,[]):
            _insert_legacy(conn,t.name,row)
    for name,definition in reporting.items():
        conn.exec_driver_sql(f'CREATE VIEW {quote(name)} AS {definition}')
    grant_count=_restore_grants(conn,grants,have,reporting)
    reset_sequences(conn)
    differences=[]
    for name,rows in before.items():
        cols=list(legacy.tables[name].columns.keys())
        if _canonical(rows,cols) != _canonical(_rows(conn,name),cols):
            differences.append(name)
    if differences:
        raise ValueError('Dữ liệu sau chuyển đổi khác nguồn: '+', '.join(differences))
    for name,rows in reporting_before.items():
        columns=list(rows[0]) if rows else []
        if _canonical(rows,columns)!=_canonical(_rows(conn,name),columns):
            raise ValueError('View báo cáo khác dữ liệu nguồn: '+name)
    from .analysis20 import store_details
    for row in before.get('takeoff_results',[]):
        store_details(conn,row['takeoff_id'],historical=True)
    if physical_tables(conn)!=NAMES:
        raise ValueError('Database sau chuyển đổi chưa đúng 20 bảng.')
    counts={n:len(r) for n,r in before.items()}
    conn.execute(metadata.tables['audit_logs'].insert().values(action='schema20_migration',detail={'legacy_rows':counts,'physical_tables':20,'verification':'full_row_comparison'}))
    physical_rows={n:conn.execute(select(func.count()).select_from(metadata.tables[n])).scalar_one() for n in sorted(NAMES)}
    return {'changed':True,'tables':20,'legacy_rows':counts,'physical_rows':physical_rows,'grants_restored':grant_count,
            'reporting_views_restored':list(reporting),'verified':'Đối chiếu đầy đủ từng cột/dòng và view báo cáo; bảo toàn quyền qua view và quyền chung của bảng gộp; thêm một sự kiện nhật ký chuyển đổi.'}
