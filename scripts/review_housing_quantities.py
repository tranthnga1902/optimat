"""Build drawing-backed labels and a conservative audit; never writes to the database."""
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/ground_truth/du_toan/normalized_20261103'
REPORT = ROOT / 'reports/review_housing_20261103'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def steel_cell(entity):
    match = re.fullmatch(r'\s*%%c\s*(\d+)\s*:\s*([\d.,]+)\s*', entity['raw'], re.I)
    if not match:
        raise ValueError(f"Not a steel summary cell: {entity['handle']}")
    return int(match[1]), float(match[2].replace(',', '.'))


def blocking_issues(issues):
    return [i for i in issues if i.get('issue_type') == 'internal_schedule_arithmetic_conflict'
            and i.get('status') == 'reviewed_unresolved']


def foundation_overlap():
    # Coordinates in metres, reconstructed from KC-01-02 / KC-01-04.
    rectangles = [(-.4, .4, -.4, 6.89), (10.88, 11.68, -.4, 6.89),
                  (3.26, 4.26, -.4, 6.89), (6.28, 7.28, -.4, 6.89),
                  (-.4, 11.89, 6.09, 6.89), (-.4, 11.68, 2.66, 3.46),
                  (-.4, 12.19, -.4, .4)]
    # Independent grid union: each small cell is counted once even at crossings.
    xs = sorted({v for r in rectangles for v in r[:2]})
    ys = sorted({v for r in rectangles for v in r[2:]})
    union = sum((b-a)*(d-c) for a,b in zip(xs,xs[1:]) for c,d in zip(ys,ys[1:])
                if any(x0 <= (a+b)/2 <= x1 and y0 <= (c+d)/2 <= y1
                       for x0,x1,y0,y1 in rectangles))
    allocated = 2*7.29*.8 + 2*(7.29-3*.8) + (10.69+10.48+10.99)*.8
    assert abs(union-allocated) < 1e-9
    return dict(rectangles_m=rectangles, union_area_m2=round(union, 6),
                allocated_area_m2=round(allocated, 6), bm2_net_length_m=4.89,
                bm2_profile_area_m2=.4425, bottom_layer_volume_m3=round(union*.25, 6),
                limitation='Chỉ đáy chữ nhật dày 0,25 m; chưa xác nhận tổng bê tông móng và phần vát giao nhau.')


def build():
    evidence = read(OUT / 'review_evidence.json')
    receipts = []
    for cid, case in evidence['cases'].items():
        estimate = read(OUT / f'{cid}.estimate.json')
        dump = REPORT / f'{cid}_ket_cau_text.json'
        entities = {e['handle']: e for e in read(dump)}
        dxf = ROOT / f'data/drawings/build/{cid}_ket_cau.dxf'
        dxf_hash = hashlib.sha256(dxf.read_bytes()).hexdigest()
        works = {w['id']: w for w in estimate['works']}
        labels = []
        reviewed = {}
        for item in case['steel']:
            work_id = f"{cid}-{item['work']}"
            components = []
            for group in item['groups']:
                for handle in group['handles']:
                    entity = entities[handle]
                    diameter, kg = steel_cell(entity)
                    components.append(dict(group=group['name'], diameter_mm=diameter, quantity=kg,
                                           unit='kg', evidence=dict(handle=handle, text=entity['raw'],
                                           layer=entity['layer'], position=entity['position'])))
            quantity = round(sum(c['quantity'] for c in components)/1000, 6)
            labels.append(dict(id=work_id+'-drawing-steel', source_work_id=work_id,
                               scope='steel_schedule_mass', quantity=quantity, unit='t',
                               components=components, aggregation='parent_equals_sum_components; do_not_sum_parent_with_children',
                               source_quantity=works[work_id]['khoi_luong'],
                               source_unit=works[work_id]['don_vi'], source_estimate_location=works[work_id]['source'],
                               quantity_basis='net_design_schedule; no estimate coefficient applied',
                               drawing=str(dxf.relative_to(ROOT)), drawing_sha256=dxf_hash))
            blockers = blocking_issues([i for i in case['issues'] if work_id.endswith('-'+i['work'])])
            labels[-1].update(eligible_for_development_comparison=not blockers,
                              arithmetic_status='inconsistent_schedule' if blockers else 'not_independently_certified',
                              blocking_issue_ids=[i['id'] for i in blockers])
            if not blockers:
                reviewed[work_id] = labels[-1]['id']
        audit = []
        for work in estimate['works']:
            issues = [i for i in case['issues'] if work['id'].endswith('-'+i['work'])]
            blockers = blocking_issues(issues)
            audit.append(dict(work_id=work['id'], source=work['source'],
                              source_quantity=work['khoi_luong'], source_unit=work['don_vi'],
                              status='quarantined_inconsistent_schedule' if blockers else 'drawing_schedule_label_available' if work['id'] in reviewed else 'quarantined_pending_drawing_takeoff',
                              eligible_label_id=reviewed.get(work['id']), issues=issues,
                              arithmetic_status='inconsistent_schedule' if blockers else 'not_independently_certified',
                              blocking_issue_ids=[i['id'] for i in blockers],
                              arithmetic_alerts=[d for d in work['details'] if d.get('arithmetic_match') is False],
                              reason='Mâu thuẫn nội bộ bảng thống kê; giữ nhãn làm bằng chứng, không dùng làm đáp án.' if blockers else 'Có nhãn thép thiết kế tách riêng hệ số nguồn.' if work['id'] in reviewed else
                              'Chưa đủ đối chứng hình học/số lượng theo phạm vi công tác; không dùng làm đáp án chuẩn.'))
        common = dict(schema_version=1, cong_trinh_id=cid, reviewer='Codex', human_approval=False,
                      verification_status='chua_kiem', is_complete_ground_truth=False)
        dataset = dict(**common, kind='verified_quantity_dataset', labels=labels,
                       limitation='Đối chứng bảng thống kê thép thiết kế, chưa tính lại từng thanh từ hình học; cần QS duyệt trước nghiệm thu.')
        review = dict(**common, kind='estimate_quality_review', rows=audit, issues=case['issues'],
                      checked_work_count=len(audit), eligible_schedule_work_count=len(reviewed),
                      quarantined_work_count=len(audit)-len(reviewed))
        if 'huong' in cid:
            review['foundation_overlap_check'] = foundation_overlap()
        write(OUT / f'{cid}.verified_quantities.json', dataset)
        write(OUT / f'{cid}.quality_review.json', review)
        comparison_path = OUT / f'{cid}.comparison.json'
        comparison = read(comparison_path)
        comparison['detailed_review'] = dict(path=os.path.relpath(OUT/f'{cid}.quality_review.json', ROOT), issues=case['issues'])
        for spot in comparison.get('visual_spot_checks', []):
            if spot.get('estimate_length_m') == 4.89:
                spot.update(result='resolved_measurement_convention',
                            finding='BM-2 dài tổng 7,29 m; trừ ba băng giao rộng 0,80 m còn 4,89 m.',
                            calculation='7.29 - 3 * 0.80 = 4.89',
                            limitation='Không xác nhận tổng đào, hệ số 1,3 hay tổng bê tông móng.')
        write(comparison_path, comparison)
        receipts.append(dict(case=cid, works=len(audit), schedule_labels=len(labels),
                             steel_cells=sum(len(x['components']) for x in labels),
                             eligible_schedule_labels=len(reviewed),
                             quarantined=len(audit)-len(reviewed), database_updated=False))
    write(REPORT / 'review_receipt.json', receipts)
    return receipts


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
