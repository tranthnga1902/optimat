"""Extract the two downloaded PDF estimates, compare with CAD, and optionally import into PostgreSQL.

Run without --database first; database import uses the saved, reviewable JSON artifacts.
"""
import argparse
import ast
import hashlib
import json
import operator
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from import_estimate import classify, text

OUT = ROOT / 'data/ground_truth/du_toan/normalized_20261103'


def number(value):
    """These PDFs use decimal dots and comma thousands separators, including quantities like 4,802.780."""
    raw = str(value or '').strip().replace(' ', '')
    if not re.fullmatch(r'-?\d[\d,]*(?:\.\d+)?', raw):
        return None
    return float(raw.replace(',', ''))


def formula_value(label):
    expr = label.rsplit(':', 1)[-1].strip().replace(',', '.').replace('×', '*')
    if not re.fullmatch(r'[\d.\s()+*/−-]+', expr) or not any(c in expr for c in '*+/'):
        return None
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
    def calc(node):
        if isinstance(node, ast.Constant) and type(node.value) in (float, int):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](calc(node.left), calc(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return (-1 if isinstance(node.op, ast.USub) else 1) * calc(node.operand)
        raise ValueError('Unsupported arithmetic')
    try:
        return float(calc(ast.parse(expr.replace('−', '-'), mode='eval').body))
    except (ValueError, SyntaxError, ZeroDivisionError):
        return None


def parse_rows(pages, case_id):
    works, raw_rows = [], []
    current = None
    section = ''
    for page_no, tables in pages:
        for table_no, table in enumerate(tables, 1):
            for row_no, row in enumerate(table, 1):
                cells = [str(c or '').strip() for c in row]
                raw_rows.append(dict(page=page_no, table=table_no, row=row_no, cells=cells))
                if len(cells) not in (7, 8):
                    continue
                stt, code, label, unit, qty, price, amount = cells[:7]
                q = number(qty)
                location = dict(page=page_no, table=table_no, row=row_no)
                if stt.isdigit() and code in ('TT', '') and q is not None and unit:
                    name = text(label.replace('\n', ' '))
                    mc, ck = classify(name)
                    current = dict(id=f'{case_id}-W{len(works)+1:03}', stt_goc=int(stt), section=section,
                                   ma_dinh_muc=code, ten_cong_tac=name, ten_goc=label,
                                   don_vi=unit, khoi_luong=q, khoi_luong_goc=qty,
                                   don_gia=number(price), thanh_tien=number(amount),
                                   ma_cong_tac=mc, cau_kien=ck, source=location,
                                   ghi_chu=cells[7] if len(cells)==8 else '', details=[],
                                   verification_status='chua_kiem')
                    works.append(current)
                elif code == 'TC':
                    current = None
                elif not stt and not code and label and not unit and q is None and re.match(r'(?i)^[a-z0-9]+[.\-]\s', label):
                    section = text(label)
                    current = None
                elif current and not stt and not code and label:
                    detail = dict(text=text(label.replace('\n', ' ')), text_goc=label,
                                  quantity=q, quantity_goc=qty, source=location)
                    v = formula_value(detail['text'])
                    if v is not None:
                        detail['formula_result'] = v
                        if q is not None:
                            detail['arithmetic_difference'] = round(v-q, 6)
                            decimals=len(qty.rsplit('.',1)[1]) if '.' in qty else 0
                            detail['rounding_tolerance']=.5*10**(-decimals)+1e-9
                            detail['arithmetic_match'] = abs(v-q) <= detail['rounding_tolerance']
                    current['details'].append(detail)
    return works, raw_rows


def extract(case):
    import pdfplumber
    pdf = ROOT / case['du_toan']
    with pdfplumber.open(pdf) as doc:
        # First two pages are cost summaries, not the itemized quantity schedule.
        pages = [(i+1, p.extract_tables()) for i, p in enumerate(doc.pages) if i >= 2]
        page_count = len(doc.pages)
    works, rows = parse_rows(pages, case['cong_trinh_id'])
    assert len(works) > 30 and all(w['khoi_luong'] >= 0 for w in works)
    payload = dict(schema_version=1, kind='estimate_reference', cong_trinh_id=case['cong_trinh_id'],
                   data_kind='ACTUAL', source_url=case['source_url'], source_pdf=case['du_toan'],
                   source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(), pages=page_count,
                   extraction='pdf_vector_tables', verification_status='chua_kiem',
                   warnings=['Số gốc của người lập dự toán, chưa phải đáp án đo tay đã duyệt.',
                             'Dòng chi tiết có thể gồm cả tổng nhóm và dòng con; không cộng mù tất cả chi tiết.'],
                   works=works, raw_rows=rows)
    return payload


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def reconcile(estimate, cad_works):
    from optimat.rough.models import WORKS
    from compare_estimate import compare
    import pandas as pd
    comparable, excluded, by_row = [], [], []
    for w in estimate['works']:
        code=w['ma_cong_tac']; name=w['ten_cong_tac'].lower()
        # Mixed work scopes cannot be compared with a single model work code.
        mixed=(('móng' in name and ('giằng' in name or 'bể' in name)) or
               (code=='TRAT' and any(x in name for x in ['cột','dầm','sàn','cầu thang'])) or
               (code=='CHONG_THAM' and ('trát' in name or 'láng' in name)))
        reason=('chưa ánh xạ công tác' if not code else 'dòng gộp nhiều cấu kiện/công tác' if mixed else
                'đơn vị không khớp với công tác hệ thống' if w['don_vi']!=WORKS[code][1] else None)
        if reason:
            excluded.append(dict(work_id=w['id'],reason=reason))
            by_row.append(dict(work_id=w['id'],status='chua_doi_chieu_duoc',reason=reason))
        else:
            comparable.append(w)
            by_row.append(dict(work_id=w['id'],status='doi_chieu_theo_nhom_chua_kiem_tay',
                               group=[code,w['cau_kien']]))
    table=compare(pd.DataFrame(comparable),cad_works)
    groups=json.loads(table.to_json(orient='records',force_ascii=False))
    for group in groups:
        group['reference_work_ids']=[w['id'] for w in comparable if (w['ma_cong_tac'],w['cau_kien'])==(group['ma_cong_tac'],group['cau_kien'])]
        group['verification_status']='chua_kiem'
        if group['status'] not in ('A','B'):
            group['diagnostic_difference_pct']=group['lech_pct']
            group['lech_pct']=None
            group['comparison_limitation']='Thiếu dữ liệu hoặc có giả định; không dùng làm sai số chính thức.'
    return dict(comparison=groups,
                excluded_from_group_comparison=excluded,row_comparisons=by_row)


def compare_cad(case, estimate):
    from optimat.catalog.repository import Catalog
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.rough.models import ProjectParams
    from optimat.rough.takeoff import rough_from_drawing, compute_rough
    from compare_estimate import compare
    import pandas as pd
    architecture, structural = [ROOT/p for p in case['drawings']]
    cat = Catalog.load()
    # Independent CAD takeoff: never copy PDF quantities or coefficients into the model's inputs.
    req = rough_from_drawing(read_drawing(str(architecture)), ProjectParams(), None, cat, architecture.name,
                             structural=[read_drawing(str(structural))])
    result = compute_rough(req, cat)
    reconciled = reconcile(estimate, result.works)
    return dict(kind='estimate_comparison', cong_trinh_id=case['cong_trinh_id'],
                verification_status='chua_kiem', method='independent_CAD_takeoff_grouped_by_work_code',
                source_drawings=[dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                                 for p in (architecture, structural)],
                warnings=['Đối chứng tự động, không thay xác nhận của người kiểm.',
                          'Hạng mục thiếu đầu vào hoặc chưa nhận diện không được coi là khớp.'],
                **reconciled, cad_request=req.model_dump(mode='json'),
                cad_result=result.model_dump(mode='json'))


def import_database(cases):
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from optimat.api.auth import hash_password
    from optimat.db.models import User, Project, ProjectFile, TakeoffResultRow, AuditLog
    from optimat.db.session import get_engine
    counts=[]
    with Session(get_engine()) as s, s.begin():
        owner = s.scalar(select(User).where(User.email=='housing-dataset@import.invalid'))
        if owner is None:
            owner=User(email='housing-dataset@import.invalid',full_name='Kho hồ sơ nhà ở tham khảo',
                       role='user',is_active=False,password_hash=hash_password(secrets.token_urlsafe(48)))
            s.add(owner); s.flush()
        for case in cases:
            cid=case['cong_trinh_id']
            estimate=json.loads((OUT/f'{cid}.estimate.json').read_text(encoding='utf-8'))
            comparison=json.loads((OUT/f'{cid}.comparison.json').read_text(encoding='utf-8'))
            from optimat.rough.models import WorkItem
            comparison.update(reconcile(estimate,[WorkItem(**w) for w in comparison['cad_result']['works']]))
            comparison['warnings'].append('Bộ đọc CAD báo có ACAD_PROXY_OBJECT bị bỏ qua; kết quả nhận diện có thể thiếu cấu kiện.')
            if cid=='nha_sang_hai_duong_4x15':
                comparison['visual_spot_checks']=[
                    dict(work_ids=[f'{cid}-W002',f'{cid}-W003'],method='assistant_visual_spotcheck',
                         source='PDF kết cấu trang 7 KC-01-01 và trang 8 KC-01-02; PDF tiên lượng trang 3-4',
                         finding='Bản vẽ ghi 34 cọc, mỗi cọc tạm tính 10 m gồm 2 đoạn 5 m, tiết diện 200×200 mm.',
                         calculation='34 * (5 + 5) = 340 m; 34 đầu cọc',result='khop_so_nguon_tam_tinh',
                         limitation='Chiều dài cọc còn phụ thuộc ép thử/thực tế; không phải xác nhận thi công hoặc duyệt đáp án.')]
            else:
                comparison['visual_spot_checks']=[
                    dict(work_ids=[f'{cid}-W002'],method='assistant_visual_spotcheck',
                         source='PDF kết cấu trang 8 KC-01-02 và trang 10 KC-01-04; PDF tiên lượng trang 3',
                         finding='Chi tiết BM-1 ghi L=7290 mm, SL=02; phù hợp 2*7,29 trong diễn giải đào móng.',
                         calculation='2 * 7.29 * 1 * 1.15 * 1.3 = 21.7971 m³',result='khop_mot_phan_kich_thuoc',
                         limitation='Chỉ kiểm chiều dài và số lượng BM-1; chưa xác nhận hệ số đào mở rộng hay tổng đào móng.'),
                    dict(work_ids=[f'{cid}-W002'],method='CAD_text_and_PDF_formula_crosscheck',
                         source='PDF tiên lượng trang 3 dòng BM-2; CAD kết cấu handle 1002DDD, layer LS-TEXT',
                         finding='BM-2 dài tổng 7,29 m; trừ ba băng giao rộng 0,80 m còn 4,89 m.',
                         calculation='7.29 - 3 * 0.80 = 4.89',
                         estimate_length_m=4.89,drawing_length_m=7.29,result='resolved_measurement_convention',
                         limitation='Chỉ giải quyết chiều dài không giao; chưa xác nhận hệ số đào hoặc tổng bê tông móng.')]
            evidence_path=OUT/'drawing_spotcheck_evidence.json'
            if evidence_path.exists():
                evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
                comparison['drawing_text_evidence']=[e for e in evidence if cid in e['file']]
            checks=[d for w in estimate['works'] for d in w['details'] if 'arithmetic_match' in d]
            estimate['arithmetic_summary']={'checked':len(checks),'within_printed_rounding':sum(d['arithmetic_match'] for d in checks),
                                            'needs_review':sum(not d['arithmetic_match'] for d in checks)}
            write_json(OUT/f'{cid}.estimate.json',estimate)
            write_json(OUT/f'{cid}.comparison.json',comparison)
            name=f'[DATA:{cid}] Hồ sơ nhà ở tham khảo'
            project=s.scalar(select(Project).where(Project.user_id==owner.user_id,Project.name==name))
            if project is None:
                project=Project(user_id=owner.user_id,name=name,address='Hải Dương',excluded_materials=[])
                s.add(project); s.flush()
            paths=[f['path'] for f in case['files']]+case['drawings']
            paths += [str((OUT/f'{cid}.{kind}.json').relative_to(ROOT)) for kind in ['estimate','comparison']]
            for path in paths:
                assert (ROOT/path).is_file(),path
                pf=s.scalar(select(ProjectFile).where(ProjectFile.project_id==project.project_id,ProjectFile.stored_path==path))
                if pf is None:
                    s.add(ProjectFile(project_id=project.project_id,filename=Path(path).name,
                                      file_type=Path(path).suffix.lstrip('.'),stored_path=path))
            s.flush()
            result_ids=[]
            for payload in (estimate,comparison):
                source_path=case['du_toan'] if payload['kind']=='estimate_reference' else case['drawings'][0]
                source_file=s.scalar(select(ProjectFile).where(ProjectFile.project_id==project.project_id,ProjectFile.stored_path==source_path))
                row=s.scalar(select(TakeoffResultRow).where(TakeoffResultRow.project_id==project.project_id,
                          TakeoffResultRow.result['kind'].astext==payload['kind']))
                if row is None:
                    row=TakeoffResultRow(project_id=project.project_id,file_id=source_file.file_id,result=payload,layer_overrides={},confirmed_at=None)
                    s.add(row); s.flush()
                else:
                    assert row.confirmed_at is None,'Do not overwrite a confirmed result'
                    row.result=payload
                    row.file_id=source_file.file_id
                result_ids.append(row.takeoff_id)
            counts.append(dict(cong_trinh_id=cid,project_id=project.project_id,result_ids=result_ids,
                               works=len(estimate['works']),files=len(paths)))
        s.add(AuditLog(action='IMPORT_HOUSING_ESTIMATES',detail={'records':counts,'confirmed':False}))
    # Verify persisted JSON after commit through a new transaction.
    with Session(get_engine()) as s:
        for row in counts:
            stored=s.get(TakeoffResultRow,row['result_ids'][0])
            assert len(stored.result['works'])==row['works'] and stored.confirmed_at is None
    write_json(OUT/'database_receipt.json',counts)
    incoming_path=ROOT/'data/ground_truth/du_toan/incoming_20261103.json'
    incoming=json.loads(incoming_path.read_text(encoding='utf-8'))
    by_id={r['cong_trinh_id']:r for r in counts}
    for record in incoming['records']:
        if record['cong_trinh_id'] in by_id:
            saved=by_id[record['cong_trinh_id']]
            record.update(status='database_imported_pending_review',database_project_id=saved['project_id'],
                          normalized_estimate=str((OUT/f"{record['cong_trinh_id']}.estimate.json").relative_to(ROOT)),
                          comparison=str((OUT/f"{record['cong_trinh_id']}.comparison.json").relative_to(ROOT)))
    write_json(incoming_path,incoming)
    print(json.dumps(counts,ensure_ascii=False),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--database',action='store_true')
    ap.add_argument('--extract-only',action='store_true')
    ap.add_argument('--compare-only',action='store_true')
    args=ap.parse_args()
    incoming=json.loads((ROOT/'data/ground_truth/du_toan/incoming_20261103.json').read_text(encoding='utf-8'))
    cases=[c for c in incoming['records'] if c['existing_case'] is None]
    if args.database:
        import_database(cases)
        return
    for case in cases:
        cid=case['cong_trinh_id']; path=OUT/f'{cid}.estimate.json'
        if args.compare_only:
            estimate=json.loads(path.read_text(encoding='utf-8'))
            assert estimate['source_sha256']==hashlib.sha256((ROOT/case['du_toan']).read_bytes()).hexdigest()
        else:
            estimate=extract(case)
            write_json(path,estimate)
        print(cid,'extracted',len(estimate['works']),'works',flush=True)
        if not args.extract_only:
            comparison=compare_cad(case,estimate)
            write_json(OUT/f'{cid}.comparison.json',comparison)
            print(cid,'CAD compared',len(comparison['comparison']),'groups',flush=True)


if __name__=='__main__':
    main()
