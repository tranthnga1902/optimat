"""Chuẩn hóa hồ sơ nhà giả lập thành JSONL có thể kiểm tra trước khi nhập."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'outputs' / 'nha_o_20_moi'
DEST = ROOT / 'data' / 'ground_truth' / 'du_toan' / 'synthetic_20_normalized.jsonl'


def main():
    report = json.loads((SOURCE / 'validation_report.json').read_text(encoding='utf-8'))
    passed = {r['id'] for r in report['houses'] if r['status'] == 'PASS'}
    records = []
    for path in sorted(SOURCE.glob('P*/P*_data.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        cid = data['house_id']
        if cid not in passed or data.get('synthetic') is not True:
            raise ValueError(f'{cid}: không đạt kiểm tra hoặc thiếu nhãn giả lập')
        elements = {e['id'] for e in data['elements']}
        sheets = {s['id'] for s in data['sheets']}
        for row in data['quantities']:
            if row['element_id'] not in elements or row['drawing'] not in sheets:
                raise ValueError(f'{cid}: không tìm thấy cấu kiện hoặc trang bản vẽ')
            expected = row['n'] * row['a'] * row['b'] * row['c'] - row['deduct']
            if not math.isfinite(row['value']) or abs(expected - row['value']) > 1e-7:
                raise ValueError(f'{cid}: sai công thức dòng {row["id"]}')
        files = []
        for suffix in ('ban_ve.dxf', 'ban_ve.pdf', 'tien_luong.xlsx', 'data.json', 'vat_lieu_dai_ly.md'):
            item = path.parent / f'{cid}_{suffix}'
            if not item.is_file():
                raise FileNotFoundError(item)
            files.append({'path': str(item.relative_to(ROOT.parent)), 'sha256': hashlib.sha256(item.read_bytes()).hexdigest()})
        records.append({'schema_version': 1, 'kind': 'synthetic_housing', 'data_kind': 'SYNTHETIC',
                        'verification_status': 'automated_geometry_checks_only', 'house_id': cid,
                        'files': files, 'data': data})
    if len(records) != 20:
        raise ValueError(f'Cần 20 hồ sơ; tìm thấy {len(records)}')
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in records), encoding='utf-8')
    print(f'Đã chuẩn hóa {len(records)} hồ sơ vào {DEST}')


if __name__ == '__main__':
    main()
