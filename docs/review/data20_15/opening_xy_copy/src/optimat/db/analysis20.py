"""Lưu cấu kiện/số đo/công tác cùng snapshot, không tính lại công thức đo bóc."""
import hashlib
import json
import math

from sqlalchemy import select, update

from .schema20 import metadata

T=metadata.tables


def _json(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,default=str,separators=(',',':'))


def capture_catalog(catalog):
    names={'materials':'materials','wall_systems':'wall_systems','material_relations':'relations',
           'suppliers':'suppliers','supplier_materials':'supplier_materials','vehicles':'vehicles',
           'labor_rates':'labor_rates','material_groups':'material_groups','material_families':'families','material_aliases':'aliases'}
    return {name:json.loads(getattr(catalog,attr).to_json(orient='records',date_format='iso')) for name,attr in names.items()}


def store_details(conn, analysis_id, historical=False, catalog_snapshot=None):
    row=conn.execute(select(T['analysis_runs']).where(T['analysis_runs'].c.takeoff_id==analysis_id)).mappings().one()
    if row['result_sha256']:
        return
    result=row['result']
    request=result.get('input') or {}
    has_plans=bool(request.get('plans'))
    plans=request.get('plans') or ([request] if request.get('walls') else [])
    elements={}
    for pi,plan in enumerate(plans):
        level=plan.get('name') or plan.get('plan') or str(pi+1)
        for collection,kind in [('walls','wall'),('openings','opening'),('columns','column'),('beams','beam'),('stairs','stair')]:
            for ei,element in enumerate(plan.get(collection) or []):
                if not isinstance(element,dict) or element.get('keep') is False:
                    continue
                key=f'{level}:{collection}:{element.get("id",ei+1)}'
                source_path=f'input.plans[{pi}].{collection}[{ei}]' if has_plans else f'input.{collection}[{ei}]'
                eid=conn.execute(T['building_elements'].insert().values(analysis_id=analysis_id,element_key=key,
                    kind=kind,level_code=level,geometry={k:element[k] for k in ('x1','y1','x2','y2','points','bbox') if k in element},
                    occurrences=[{'plan':level,'input_path':source_path}],payload=element)
                    .returning(T['building_elements'].c.element_id)).scalar_one()
                elements[(level,str(element.get('id',ei+1)))]=eid
                evidence=conn.execute(T['evidence_sources'].insert().values(analysis_id=analysis_id,kind='input_snapshot',
                    source_ref={'path':source_path,'note':'Tham chiếu snapshot, chưa xác minh handle CAD.'},
                    raw_content=element).returning(T['evidence_sources'].c.evidence_id)).scalar_one()
                manual=element.get('src')=='manual' or element.get('source')=='manual' or element.get('edited',False)
                status='C' if manual else 'B'
                values={}
                for prop,fields in [('width',('w','b_mm','width_mm')),('height',('h','h_mm','height_mm')),('length',('length_mm',)),('thickness',('thickness_mm',))]:
                    for f in fields:
                        if isinstance(element.get(f),(int,float)) and not isinstance(element[f],bool):
                            values[prop]=element[f];break
                if all(isinstance(element.get(k),(int,float)) for k in ('x1','y1','x2','y2')):
                    values['length']=math.hypot(element['x2']-element['x1'],element['y2']-element['y1'])
                if kind=='wall' and plan.get('height_mm') is not None:
                    values['height']=plan['height_mm']
                for prop,value in values.items():
                    if not math.isfinite(float(value)):
                        raise ValueError('Số đo không hữu hạn trong snapshot.')
                    conn.execute(T['element_measurements'].insert().values(element_id=eid,property_code=prop,value=value,
                        unit='mm',status=status,selected=True,method='user_input' if manual else 'snapshot',evidence_ids=[evidence]))
    for seq,work in enumerate(result.get('works') or [],1):
        if not isinstance(work,dict):
            continue
        quantity=work.get('quantity')
        status=work.get('status') or ('D' if quantity is None else 'C')
        if quantity is None:status='D'
        detail=work.get('quantity_detail') or {}
        conn.execute(T['takeoff_items'].insert().values(analysis_id=analysis_id,seq=seq,
            work_code=work.get('code') or 'UNKNOWN',unit=work.get('unit') or '',quantity=quantity,
            known_part=detail.get('known_part_raw',quantity),status=status,
            element_id=elements.get((work.get('plan'),str(work.get('element')))),
            formula=work.get('formula') or '',input_snapshot={'dimensions':work.get('dimensions'),'quantity_detail':detail},payload=work))
    materials=result.get('materials') or []
    snapshot={**row['input_snapshot'],'request':request,'source':'legacy_snapshot' if not row['input_snapshot'] else 'snapshot',
              'catalog_is_historical_input':catalog_snapshot is not None and not historical,
              'catalog_capture_kind':'compute_input' if catalog_snapshot is not None and not historical else 'database_at_save_unverified',
              'rules_input_verified':False,
              'catalog':catalog_snapshot if catalog_snapshot is not None else {name:[dict(x) for x in conn.execute(select(T[name])).mappings()] for name in ('materials','wall_systems','material_relations','work_norms','rule_sets','cost_parameters')}}
    # Chuẩn hóa RowMapping/Decimal/date trước khi gửi JSONB, không làm tròn công tác.
    snapshot=json.loads(_json(snapshot))
    if materials:
        conn.execute(T['material_scenarios'].insert().values(analysis_id=analysis_id,name='Vật liệu của snapshot bóc tách',
            origin='proposed',selected=False,requirements=materials,catalog_snapshot={'schema_version':1,'catalog':snapshot['catalog'],
              'catalog_is_historical_input':snapshot['catalog_is_historical_input'],'capture_kind':snapshot['catalog_capture_kind']}))
    conn.execute(update(T['analysis_runs']).where(T['analysis_runs'].c.takeoff_id==analysis_id).values(
        input_snapshot=snapshot,result_sha256=hashlib.sha256(_json(result).encode('utf-8')).hexdigest()))
