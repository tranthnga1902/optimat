"""Hợp đồng 20 bảng và các ca toàn vẹn trên database thử nghiệm riêng."""
import os
import uuid

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from optimat.db.schema20 import metadata, NAMES
from optimat.db.compat20 import schema_sql
from optimat.db.migrate20 import migrate, physical_tables


def test_exact_twenty_storage_tables():
    assert NAMES == {
        'users','projects','document_revisions','analysis_runs','building_elements',
        'element_measurements','evidence_sources','takeoff_items','materials','wall_systems',
        'material_relations','work_norms','suppliers','supplier_materials','price_records',
        'cost_parameters','material_scenarios','optimization_runs','rule_sets','audit_logs'}
    assert schema_sql().count('CREATE TABLE ')==20
    assert 'CREATE VIEW "takeoff_results"' in schema_sql()


@pytest.fixture
def db20():
    raw=os.environ.get('OPTIMAT_TEST_DATABASE_URL')
    if not raw:
        pytest.skip('Chưa đặt database thử nghiệm riêng.')
    url=make_url(raw)
    if not (url.database or '').startswith('optimat_test_schema20_') or url.host not in ('localhost','127.0.0.1','::1'):
        pytest.skip('Ca schema20 chỉ chạy trên database thử nghiệm có tên riêng của đợt chuyển đổi.')
    engine=create_engine(url,hide_parameters=True)
    with engine.connect() as conn:
        tx=conn.begin()
        try:
            assert physical_tables(conn)==NAMES
            uid=conn.execute(metadata.tables['users'].insert().values(email=f'{uuid.uuid4()}@example.test',password_hash='test').returning(metadata.tables['users'].c.user_id)).scalar_one()
            pid=conn.execute(metadata.tables['projects'].insert().values(user_id=uid,name='Kiểm thử 20 bảng').returning(metadata.tables['projects'].c.project_id)).scalar_one()
            a=metadata.tables['analysis_runs']
            ids=[conn.execute(a.insert().values(project_id=pid,result={'kind':'rough','works':[],'input':{}}).returning(a.c.takeoff_id)).scalar_one() for _ in range(2)]
            yield conn,pid,ids
        finally:
            tx.rollback()
    engine.dispose()


def test_migration_rerun_is_noop(db20):
    conn,_,_=db20
    assert migrate(conn)['changed'] is False
    assert physical_tables(conn)==NAMES


def test_legacy_view_write_keeps_twenty_tables(db20):
    conn,pid,_=db20
    fid=conn.execute(text("INSERT INTO project_files(project_id,filename,file_type,stored_path) VALUES(:p,'mẫu.dxf','dxf','/sample') RETURNING file_id"),{'p':pid}).scalar_one()
    conn.execute(text("INSERT INTO project_document_revisions(file_id,version,sha256,stored_path,size_bytes,format,role) VALUES(:f,1,:hash,'/sample',10,'dxf','KT')"),{'f':fid,'hash':'a'*64})
    assert conn.execute(text('SELECT count(*) FROM document_revisions WHERE project_id=:p'),{'p':pid}).scalar_one()==2
    assert physical_tables(conn)==NAMES


def test_file_revision_is_immutable(db20):
    conn,pid,_=db20
    fid=conn.execute(text("INSERT INTO project_files(project_id,filename,file_type,stored_path) VALUES(:p,'mẫu.dxf','dxf','/sample') RETURNING file_id"),{'p':pid}).scalar_one()
    rid=conn.execute(text("INSERT INTO project_document_revisions(file_id,version,sha256,stored_path,size_bytes,format,role) VALUES(:f,1,:hash,'/sample',10,'dxf','KT') RETURNING revision_id"),{'f':fid,'hash':'a'*64}).scalar_one()
    with pytest.raises(IntegrityError), conn.begin_nested():
        conn.execute(text("UPDATE document_revisions SET role='KC' WHERE revision_id=:r"),{'r':rid})


def test_measurement_rejects_foreign_analysis_evidence(db20):
    conn,_,ids=db20
    e=metadata.tables['building_elements'];s=metadata.tables['evidence_sources'];m=metadata.tables['element_measurements']
    eid=conn.execute(e.insert().values(analysis_id=ids[0],element_key='W1',kind='wall').returning(e.c.element_id)).scalar_one()
    source=conn.execute(s.insert().values(analysis_id=ids[1],kind='snapshot',raw_content={}).returning(s.c.evidence_id)).scalar_one()
    with pytest.raises(IntegrityError), conn.begin_nested():
        conn.execute(m.insert().values(element_id=eid,property_code='length',value=5000,unit='mm',status='B',method='snapshot',evidence_ids=[source]))


def test_null_selected_measurement_is_rejected(db20):
    conn,_,ids=db20
    e=metadata.tables['building_elements'];m=metadata.tables['element_measurements']
    eid=conn.execute(e.insert().values(analysis_id=ids[0],element_key='W1',kind='wall').returning(e.c.element_id)).scalar_one()
    with pytest.raises(IntegrityError),conn.begin_nested():
        conn.execute(m.insert().values(element_id=eid,property_code='height',value=None,unit='mm',status='D',method='snapshot',selected=True))


def test_complete_requirement_must_have_quantity(db20):
    conn,_,ids=db20
    with pytest.raises(IntegrityError),conn.begin_nested():
        conn.execute(metadata.tables['material_scenarios'].insert().values(analysis_id=ids[0],name='Thiếu lượng',origin='user',requirements=[{'complete':True,'quantity':None}]))


def test_work_cannot_reference_another_analysis(db20):
    conn,_,ids=db20
    e=metadata.tables['building_elements']
    eid=conn.execute(e.insert().values(analysis_id=ids[0],element_key='W1',kind='wall').returning(e.c.element_id)).scalar_one()
    with pytest.raises(IntegrityError),conn.begin_nested():
        conn.execute(metadata.tables['takeoff_items'].insert().values(analysis_id=ids[1],seq=1,work_code='XAY',unit='m³',quantity=1,status='B',element_id=eid,payload={}))


def test_store_details_is_idempotent_and_preserves_unknown_material(db20):
    from optimat.db.analysis20 import store_details
    conn,_,ids=db20
    a=metadata.tables['analysis_runs']
    result={'kind':'rough','input':{'plans':[{'name':'Tầng 1','height_mm':3000,'walls':[{'id':'W1','x1':0,'y1':0,'x2':5000,'y2':0,'mat':None}]}]},
            'works':[{'code':'XAY','unit':'m³','quantity':None,'status':'D','missing':['Chưa biết chiều dày'],'formula':''}]}
    conn.execute(a.update().where(a.c.takeoff_id==ids[0]).values(result=result))
    store_details(conn,ids[0]);store_details(conn,ids[0])
    assert len(conn.execute(select(metadata.tables['building_elements']).where(metadata.tables['building_elements'].c.analysis_id==ids[0])).all())==1
    item=conn.execute(select(metadata.tables['takeoff_items']).where(metadata.tables['takeoff_items'].c.analysis_id==ids[0])).mappings().one()
    assert item['quantity'] is None and item['status']=='D'
    assert conn.execute(select(metadata.tables['material_scenarios']).where(metadata.tables['material_scenarios'].c.analysis_id==ids[0])).first() is None
    with pytest.raises(IntegrityError),conn.begin_nested():
        conn.execute(a.update().where(a.c.takeoff_id==ids[0]).values(result={}))
    with pytest.raises(IntegrityError),conn.begin_nested():
        conn.execute(a.update().where(a.c.takeoff_id==ids[0]).values(result_sha256=None))


def test_root_walls_path_and_unverified_catalog(db20):
    from optimat.db.analysis20 import store_details
    conn,_,ids=db20
    a=metadata.tables['analysis_runs']
    body={'input':{'plan':'Tầng 1','walls':[{'id':'W1','x1':0,'y1':0,'x2':1000,'y2':0}]},'works':[]}
    conn.execute(a.update().where(a.c.takeoff_id==ids[0]).values(result=body))
    store_details(conn,ids[0])
    ev=conn.execute(select(metadata.tables['evidence_sources'].c.source_ref).where(metadata.tables['evidence_sources'].c.analysis_id==ids[0])).scalar_one()
    assert ev['path']=='input.walls[0]'
    snapshot=conn.execute(select(a.c.input_snapshot).where(a.c.takeoff_id==ids[0])).scalar_one()
    assert snapshot['catalog_is_historical_input'] is False
    assert snapshot['catalog_capture_kind']=='database_at_save_unverified'


def test_catalog_snapshot_is_the_supplied_compute_input(db20):
    from optimat.db.analysis20 import store_details
    conn,_,ids=db20
    store_details(conn,ids[0],catalog_snapshot={'materials':[{'material_id':'snapshot-only'}]})
    a=metadata.tables['analysis_runs']
    snapshot=conn.execute(select(a.c.input_snapshot).where(a.c.takeoff_id==ids[0])).scalar_one()
    assert snapshot['catalog']=={'materials':[{'material_id':'snapshot-only'}]}
    assert snapshot['catalog_is_historical_input'] is True
    assert snapshot['rules_input_verified'] is False


def test_used_evidence_cannot_disappear_or_move(db20):
    conn,_,ids=db20
    e=metadata.tables['building_elements'];s=metadata.tables['evidence_sources'];m=metadata.tables['element_measurements']
    eid=conn.execute(e.insert().values(analysis_id=ids[0],element_key='W1',kind='wall').returning(e.c.element_id)).scalar_one()
    source=conn.execute(s.insert().values(analysis_id=ids[0],kind='snapshot',raw_content={}).returning(s.c.evidence_id)).scalar_one()
    conn.execute(m.insert().values(element_id=eid,property_code='length',value=1000,unit='mm',status='B',method='snapshot',evidence_ids=[str(source)]))
    for statement in (s.delete().where(s.c.evidence_id==source),s.update().where(s.c.evidence_id==source).values(analysis_id=ids[1])):
        with pytest.raises(IntegrityError),conn.begin_nested():conn.execute(statement)


def test_revision_null_required_fields_are_rejected(db20):
    conn,pid,_=db20
    fid=conn.execute(text("INSERT INTO project_files(project_id,filename,file_type,stored_path) VALUES(:p,'mẫu.dxf','dxf','/sample') RETURNING file_id"),{'p':pid}).scalar_one()
    d=metadata.tables['document_revisions']
    with pytest.raises(IntegrityError),conn.begin_nested():
        conn.execute(d.insert().values(project_id=pid,record_type='revision',file_id=fid,revision_id=987654321,
            filename='mẫu.dxf',format='dxf',stored_path='/sample',sha256='a'*64,version=None,size_bytes=None,role=None))


def test_optimizer_groups_must_match_saved_quantities():
    from optimat.db.optimization20 import assert_groups_match
    group={'wall_type':'110','role':'partition','length_m':5,'gross_area_m2':15,'opening_area_m2':0,'net_area_m2':15}
    assert_groups_match({'groups':[group]},[group])
    with pytest.raises(ValueError):assert_groups_match({'groups':[group]},[{**group,'net_area_m2':150}])


def test_restored_application_role_can_read_and_write_views(db20):
    conn,pid,_=db20
    has_role=conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='optimat')")).scalar_one()
    allowed=conn.execute(text("SELECT has_table_privilege('optimat','document_revisions','INSERT')")).scalar_one() if has_role else False
    if not allowed:pytest.skip('Ca ACL chỉ áp dụng cho bản sao có GRANT ứng dụng từ nguồn.')
    conn.exec_driver_sql('SET LOCAL ROLE optimat')
    try:
        assert conn.execute(text('SELECT count(*) FROM rule_sets')).scalar_one()>=0
        conn.execute(text("INSERT INTO project_files(project_id,filename,file_type,stored_path) VALUES(:p,'acl.dxf','dxf','/sample')"),{'p':pid})
    finally:
        conn.exec_driver_sql('RESET ROLE')

def test_sealed_analysis_rejects_new_or_moved_children(db20):
    conn,_,ids=db20
    a=metadata.tables['analysis_runs'];e=metadata.tables['building_elements'];m=metadata.tables['element_measurements'];w=metadata.tables['takeoff_items']
    ea=conn.execute(e.insert().values(analysis_id=ids[0],element_key='A',kind='wall').returning(e.c.element_id)).scalar_one()
    eb=conn.execute(e.insert().values(analysis_id=ids[1],element_key='B',kind='wall').returning(e.c.element_id)).scalar_one()
    mid=conn.execute(m.insert().values(element_id=eb,property_code='length',unit='mm',status='D',method='snapshot').returning(m.c.measurement_id)).scalar_one()
    wid=conn.execute(w.insert().values(analysis_id=ids[1],seq=1,work_code='X',unit='m',status='D',payload={}).returning(w.c.item_id)).scalar_one()
    conn.execute(a.update().where(a.c.takeoff_id==ids[0]).values(result_sha256='a'*64))
    statements=[e.insert().values(analysis_id=ids[0],element_key='new',kind='wall'),e.update().where(e.c.element_id==eb).values(analysis_id=ids[0]),m.insert().values(element_id=ea,property_code='length',unit='mm',status='D',method='snapshot'),m.update().where(m.c.measurement_id==mid).values(element_id=ea),w.insert().values(analysis_id=ids[0],seq=1,work_code='X',unit='m',status='D',payload={}),w.update().where(w.c.item_id==wid).values(analysis_id=ids[0])]
    for statement in statements:
        with pytest.raises(IntegrityError),conn.begin_nested():conn.execute(statement)
    conn.execute(e.update().where(e.c.element_id==eb).values(kind='beam'))
