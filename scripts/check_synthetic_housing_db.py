"""Kiểm tra trạng thái nhập hồ sơ giả lập, không thay đổi cơ sở dữ liệu."""
import json
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import optimat.config
from sqlalchemy import text
from optimat.db.session import get_engine

with get_engine().connect() as conn:
    rows = conn.execute(text("""SELECT p.name, t.result->>'data_kind' AS data_kind,
        t.confirmed_at, jsonb_array_length(t.result#>'{data,quantities}') AS quantities
        FROM users u JOIN projects p ON p.user_id=u.user_id
        JOIN takeoff_results t ON t.project_id=p.project_id
        WHERE u.email='synthetic-housing@import.invalid'
          AND t.result->>'kind'='synthetic_housing' ORDER BY p.name""")).mappings().all()
    print(json.dumps({'database': conn.execute(text('SELECT current_database()')).scalar(),
                      'results': len(rows), 'synthetic': sum(r['data_kind']=='SYNTHETIC' for r in rows),
                      'confirmed': sum(r['confirmed_at'] is not None for r in rows),
                      'quantity_rows': sum(r['quantities'] for r in rows)}, ensure_ascii=False))
    root = Path(__file__).resolve().parents[1]
    source = [json.loads(line) for line in (root / 'data/ground_truth/du_toan/synthetic_20_normalized.jsonl').read_text(encoding='utf-8').splitlines() if line]
    results = conn.execute(text("""SELECT p.project_id, t.result FROM users u
        JOIN projects p ON p.user_id=u.user_id JOIN takeoff_results t ON t.project_id=p.project_id
        WHERE u.email='synthetic-housing@import.invalid' AND t.result->>'kind'='synthetic_housing'""")).mappings().all()
    expected = {r['house_id']: r for r in source}
    assert len(results) == len(expected) == 20
    file_count = 0
    for item in results:
        payload = item['result']; original = expected[payload['house_id']]
        assert payload['data'] == original['data'] and payload['data_kind'] == 'SYNTHETIC'
        registered = conn.execute(text('SELECT stored_path FROM project_files WHERE project_id=:pid'), {'pid': item['project_id']}).scalars().all()
        if len(registered) != 5:
            print(json.dumps({'house_id':payload['house_id'],'registered_files':len(registered),'payload_file_paths':[f.get('stored_path') for f in payload['files']]},ensure_ascii=False))
            continue
        assert len(payload['files']) == 5
        for f in payload['files']:
            path = root / f['stored_path']
            assert f['stored_path'] in registered and path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == f['sha256']
            file_count += 1
    print(json.dumps({'source_data_compared':len(results),'verified_registered_files':file_count},ensure_ascii=False))
