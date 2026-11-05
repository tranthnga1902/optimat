# Full backend retry sau fix contract28 - 04/11/2026

**Đạt gate hồi quy backend trong phạm vi đã được user/01 duyệt.** Không bao gồm CAD thật, DB app/migration, network OpenAI, native hoặc QA frontend/ACTUAL. Không tự nâng thành nghiệm thu nghiệp vụ toàn hệ thống.

```text
collected 1130 items / 15 deselected / 1115 selected
1096 passed, 19 skipped, 15 deselected in 146.16s (0:02:26)
failed=0; errors=0; xfailed=0; xpassed=0
pytest exit=0; collector/session exit=0
```

Session **23185** đã poll trực tiếp bằng write_stdin tới terminal; launcher **PID25920** được collector đợi thoát. Kết thúc09:45:04 giờ Việt Nam (02:45:04 UTC). Pytest146,16giây, collector150,14giây. Không failure/error traceback; tracebacks.log xác nhận không có phần lỗi.

## Preflight và phiên bản

- User approval full không DB/OpenAI/CAD thật được01 xác nhận;01 mở slot retry sau frontend clean build kết thúc. Không tự chạy lại attempt0; đây là lượt retry riêng được cấp sau focused fix contract28 đạt.
- Hai snapshot cách3giây ổn định. Baseline khớp hash sau fix đã được01 nhận; delta so attempt0 chỉ tests/test_admin_db.py như authorized_edit_diff/test_fix.diff đã bàn giao ở admin_metadata_fix.
- **263 file** hash trước/sau hoàn toàn khớp; hash_diff changed/added/removed đều rỗng. Profile giữ nguyên attempt0: reference manifest sau concrete-grade cộng src/scripts/tests Python, catalog/rules CSV, ground_truth/sample CSV+JSON, synthetic sample DXF, docs/schema JSON và pytest/config/requirements.
- Không so263 với225 hoặc frontmanifest92 cũ. Frontend/build config hiện hành ngoài acceptance; không claim toànrepo bất biến hoặc giao diện đã kiểm. Không có source/test edit trong lúc chạy.
- Ca metadata CSV 28bảng đã chạy đạt trong full này; bổ sung focused trước đó kiểm rõ hai revision model readonly/fallback rỗng. Không suy model metadata thành schema DB đã áp hoặc dữ liệu thật đã có.

## Các ca bị loại/skip đúng quyền

Giữ nguyên năm prefix được01 duyệt, không sửa marker/test và không đọc CAD thật để bù:

1. tests/test_drawing_io.py::test_real_drawing_read_in_world_coords (mọi tham số)
2. tests/test_rough_build_drawings.py::test_nha_dan_columns_and_rough
3. tests/test_rough_build_drawings.py::test_nha_pho_columns
4. tests/test_registry.py::test_ket_cau_build_drawing
5. tests/test_rough_structural.py::test_ket_cau_build_drawing

**15ca thực tế deselected**, lý do “user full không CAD thật”; không gọi đó là chỉ5case. Các test unit/API/synthetic/sample khác được giữ.

**19skip:** 15PostgreSQL cũ thiếu OPTIMAT_TEST_DATABASE_URL;3route/roles/migration opt-in DB chưa bật;1symlink Windows không tạo được trong môi trường. Không nới permission, bật DBtest, reset/migrate hoặc query DB runtime trong suite.

## Môi trường/lệnh

- Python venv3.13.0 đúng nested checkout optimat-ai, pytest9.1.1, pytest thường không --runxfail.
- Child bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPENAI_API_KEY và hai opt-in projectDB/migration; OPTIMAT_NO_DOTENV=1, LLM_PROVIDER=none, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1, overlay test data/sample/catalog. Cờ lưu chỉ boolean/giá trị không nhạy cảm.
- `-ra -p no:cacheprovider -o faulthandler_timeout=120`, basetemp riêng trong workspace. Lệnh chính xác ở environment.json/process.json; chỉ đổi đường basetemp sang full_retry so command_plan cũ.
- require_escalated được auto-review cho phép theo user approval và nhu cầu TestClient/socketpair ngoài sandbox đã xác minh. Không thay actor/chính sách hệ thống, restart service, networkOpenAI hoặc browser upload.

## Bàn giao/giới hạn

preflight.json, hash_preflight_1.json/hash_preflight_2.json, hash_before.json/hash_after.json/hash_diff.json, environment.json/process.json/result.json, pytest_full.log/tracebacks.log và HANDOFF.md. pytest_temp là dữ liệu tạm test.

Giữ nguyên full_run attempt0exit1 và admin_metadata_fix focused/log/diff. Lượt này chỉ tạo artifacts full_retry, không sửa source/schema/DB để ép pass. Chờ01 chốt gate tích hợp đúng phạm vi; ACTUAL/UI/native/DBapp/OpenAI thật còn cần bằng chứng riêng.
