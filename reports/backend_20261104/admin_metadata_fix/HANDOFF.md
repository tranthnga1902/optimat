# Fix contract metadata CSV - 04/11/2026

Theo01 xác nhận schema28bảng là thay đổi có chủ đích đã được user duyệt. Chỉ sửa `tests/test_admin_db.py`: docstring26→28 và function `test_overview_and_rows_from_csv`; không sửa API/model/SQL/DB.

## Thay đổi được phép

- Giữ assertion chính xác `source==csv`, `not connected`, **len(tables)==28**, không nới thành >= hoặc bỏ kiểm count.
- Kiểm đích danh `project_document_revisions` và `project_profile_revisions` được liệt kê, editable=False.
- GET CSV fallback từng bảng phải HTTP200, name/source đúng, rows=[], total=0, editable=False. Comment ghi rõ model metadata không chứng minh DB đã áp schema/có dữ liệu.
- Giữ nguyên tất cả assertions cũ về overview read-only, material_notes, CRUD, bảng không tồn tại, suppliers và dealers.

## Focused terminal

```text
tests/test_admin_db.py::test_overview_and_rows_from_csv PASSED
1 passed in 18.60s
failed/errors/skipped/xfail=0
pytest/collector/session exit=0
```

Session7011 terminal; launcher PID22088 đã được collector đợi thoát. Chỉ chạy node này một lần, không full retry. Không có failure traceback.

Child bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPENAI_API_KEY và hai opt-in projectDB/migration; OPTIMAT_NO_DOTENV=1, LLM_PROVIDER=none, PYTHONIOENCODING=utf-8, basetemp workspace riêng, no cacheprovider. Outside sandbox TestClient được auto-review cho phép. Không DB query/reset/migration hoặc CAD thật, không service restart.

## Hash/diff

- 263 tệp profile như full attempt0 được hash trước edit, lúc test bắt đầu và sau test.
- Thay đổi từ trước edit: **chỉ tests/test_admin_db.py**, đúng scope. Trong lúc test: **không file nào đổi**.
- `test_fix.diff` lưu đúng diff test; `test_admin_db.before.txt` là bản sao trước sửa để review, không dùng rollback source tự động.
- `hash_before.json`, `hash_test_start.json`, `hash_after.json`, `authorized_edit_diff.json`, `hash_diff.json` ghi bằng chứng. Test đã đổi hash so với manifest trước fix, nên lượt full sau phải khóa snapshot mới/ghi ngoại lệ được01chấp thuận, không giả toàn bộ manifest cũ còn khớp.

## Bàn giao và giới hạn

pytest_focused.log, tracebacks.log, environment.json/process.json/result.json, diff/hash và HANDOFF.md. Không đụng artifacts full attempt0exit1; không sửa source/test khác hoặc docs chung. Chờ01 mở slot full retry sau frontend build; focused pass không biến full cũ thành pass và không chứng minh DBapp/native/UI.
