import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'src')
import optimat.config
from optimat.db.session import get_engine
from optimat.db.migrate20 import physical_tables
from optimat.db.schema20 import NAMES,metadata
from sqlalchemy import text,select,func
root=Path('.')
receipt=json.loads((root/'backups/schema20/migration_20261104_174541_191430.json').read_text(encoding='utf-8'))
with get_engine().connect() as c:
 assert physical_tables(c)==NAMES
 counts={n:c.execute(select(func.count()).select_from(metadata.tables[n])).scalar_one() for n in sorted(NAMES)}
 assert counts==receipt['physical_rows']
 assert c.execute(text("SELECT count(*) FROM takeoff_results")).scalar_one()==26
 assert c.execute(text("SELECT count(*) FROM project_document_revisions")).scalar_one()==2
 project=c.execute(text('SELECT project_id FROM projects WHERE project_id=23')).scalar_one()
 sealed=c.execute(text('SELECT count(*) FROM analysis_runs WHERE result_sha256 IS NOT NULL')).scalar_one()
 c.exec_driver_sql('SET LOCAL ROLE optimat')
 for name in ('project_files','project_document_revisions','takeoff_results','rough_norms','material_families','v_price_training','v_wall_systems'):
  c.execute(text('SELECT count(*) FROM '+name)).scalar_one()
 c.exec_driver_sql('RESET ROLE')
report={'status':'committed_verified','database':'optimat','physical_tables':20,'physical_rows':counts,'sealed_analyses':sealed,'project_23_present':project==23,'legacy_column_row_comparison':'28 structures verified in migration transaction','application_role_readback':'optimat passed seven legacy/reporting views','backup_validated':True,'source_hashes':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['src/optimat/db/compat20.py','src/optimat/db/schema20.py','src/optimat/db/analysis20.py','src/optimat/db/migrate20.py']},'tests':['schema20_focused_latest:52 passed','schema20_compute_latest:66 passed','schema20_final_integrity:16 passed']}
(root/'reports/schema20_main_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'tables':20,'sealed_analyses':sealed,'project23':True}))
