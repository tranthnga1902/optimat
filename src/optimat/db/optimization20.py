"""Chụp đầu vào và giá đã dùng khi lưu một lần tối ưu gắn dự án."""
import hashlib
import json

from .session import get_engine
from .schema20 import metadata
from .. import config
from ..schemas import WallGroup


def assert_groups_match(saved_result, groups):
    expected=saved_result.get('wall_groups')
    if expected is None:expected=saved_result.get('groups')
    if expected is None:
        raise ValueError('Kết quả đã lưu chưa có nhóm tường để đối chiếu; cần tính và lưu lại.')
    encode=lambda values:sorted(json.dumps(WallGroup.model_validate(v).model_dump(mode='json'),sort_keys=True,ensure_ascii=False) for v in values)
    if encode(expected)!=encode(groups):
        raise ValueError('Nhóm tường gửi tối ưu khác khối lượng đã lưu; cần lưu bản bóc mới.')


def save_optimization(request, result, catalog, model):
    def records(df):
        return json.loads(df.to_json(orient='records',date_format='iso'))
    snapshot={name:records(getattr(catalog,name)) for name in
              ('materials','wall_systems','relations','suppliers','supplier_materials','vehicles','labor_rates')}
    spec=getattr(model,'spec',None)
    model_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in config.MODELS_DIR.glob('material_price*') if p.is_file()} if model else {}
    with get_engine().begin() as conn:
        from sqlalchemy import select
        analysis=metadata.tables['analysis_runs']
        saved=conn.execute(select(analysis.c.result).where(analysis.c.takeoff_id==request.takeoff_id,
            analysis.c.project_id==request.project_id).with_for_update()).scalar_one()
        assert_groups_match(saved,request.groups)
        run=metadata.tables['optimization_runs']
        run_id=conn.execute(run.insert().values(project_id=request.project_id,takeoff_id=request.takeoff_id,
            method=result.execution.get('algorithm') or request.method,config={'schema_version':20,'request':request.model_dump(mode='json'),
                'catalog_snapshot':snapshot,'model_spec':spec,'model_files':model_files,
                'execution':result.execution,'n_evaluated':result.n_evaluated,'notes':result.notes,
                'price_snapshot_scope':'Giá và chi phí thực dùng nằm trong từng choice của solutions.'},
            solutions=[s.model_dump(mode='json') for s in result.solutions])
            .returning(run.c.run_id)).scalar_one()
        for i,solution in enumerate(result.solutions,1):
            requirements=[]
            for index,choice in enumerate(solution.choices):
                for prefix in ('','mortar_'):
                    mid=getattr(choice,prefix+'material_id',None)
                    if not mid:continue
                    qty=getattr(choice,prefix+'quantity',None)
                    unit=getattr(choice,prefix+'unit',None)
                    requirements.append({'material_id':mid,'name':getattr(choice,prefix+'material_name',None),
                        'unit':unit,'quantity':qty,'complete':qty is not None,'status':'C' if qty is not None else 'D',
                        'quantity_basis':'as_returned_by_optimizer','missing':[] if qty is not None else ['Chưa có lượng'],
                        'uses':[{'analysis_id':request.takeoff_id,'assignment_index':index,'wall_type':choice.wall_type}],
                        'source_scope':'nhom_tuong; chua_anh_xa_tung_item','commercially_confirmed':False})
            conn.execute(metadata.tables['material_scenarios'].insert().values(analysis_id=request.takeoff_id,
                name=f'Phương án tối ưu {i}',origin='optimized',run_id=run_id,
                assignments=[c.model_dump(mode='json') for c in solution.choices],requirements=requirements,
                catalog_snapshot={'schema_version':1,'catalog':snapshot,'model_files':model_files,
                  'catalog_is_historical_input':True,'capture_kind':'optimizer_input','model_hash_scope':'files_at_save'}))
        return run_id
