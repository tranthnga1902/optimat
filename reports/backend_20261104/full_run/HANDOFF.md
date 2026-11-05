# Full backend mặc định, không DB/OpenAI/CAD thật - 04/11/2026

User trực tiếp duyệt tại01 và01 mở slot sau frontend build kết thúc. **Kết quả: CẦN REVIEW một failure; không nghiệm thu full pass.** Chạy một lượt, không sửa hoặc chạy lại.

```text
collected 1130 items / 15 deselected / 1115 selected
1 failed, 1095 passed, 19 skipped, 15 deselected in 182.56s (0:03:02)
xfailed=0; xpassed=0; errors=0
pytest exit=1; collector/session exit=1
```

Session **77871** đã poll trực tiếp bằng write_stdin tới terminal, launcher **PID4240** được collector đợi thoát. Kết thúc09:31:20 giờ Việt Nam (02:31:20 UTC); pytest182,56giây, collector185,95giây. Không còn job full chạy nền của lượt này.

## Failure và expected/actual

Node **tests/test_admin_db.py::test_overview_and_rows_from_csv**, dòng21.

- Expected: GET `/api/admin/db` báo source CSV, connected=False và `len(tables)==26`.
- Actual: source='csv', connected=False, **len(tables)=28**. Assertion thất bại ở điều kiện đếm bảng; không phải lỗi kết nối DB.
- Traceback nguyên văn trong tracebacks.log, thứ tự suite và toàn output trong pytest_full.log.
- Chưa tự kết luận sửa test26→28 là đúng giải pháp:01/owner cần đối chiếu hai bảng metadata mới với hợp đồng route. Không sửa source/test, không thêm skip/xfail hoặc chạy node riêng sau failure.

## Cổng nguồn và profile hash

- Dùng manifest **sau concrete-grade** `tmp/package_01_post_concrete_20261104T020202Z/manifest.json` ở root ngoài nested checkout, không dùng package015156 trước fix. Cả **221 entry backend** khớp manifest lúc preflight; manifest path/SHA và drift rỗng lưu ở preflight.json.
- Process inventory chỉ đọc lúc09:27:28 không có pytest hoặc Next build khác. Python/venv đúng nested checkout; không can thiệp service/API/browser.
- Hai snapshot cách3giây ổn định. **263 file** hash trước/sau khớp, hash_diff changed/added/removed đều rỗng.
- Profile mở rộng: 221 entry reference cộng Python src/scripts/tests, catalog/rules CSV, ground_truth/sample CSV+JSON, sample DXF SYNTHETIC, docs/schema JSON và pytest/config/requirements. Không so263 với225 cũ vì khác profile.
- Static search trong tests không tìm reference frontend/package.json/next.config/.tsx; không bao hàm mọi phụ thuộc động. Frontend/config build hiện hành ngoài acceptance; không dựa frontmanifest92 cũ để claim UI. AI staging/network/DB thật/CAD thật không thuộc kết quả.

## CAD thật: loại có chủ ý theo chỉ đạo01

Preflight phát hiện các test thật chưa có opt-in; dừng trước chạy để báo01.01 chốt đúng năm prefix `--deselect`, giữ nguyên test/source:

1. tests/test_drawing_io.py::test_real_drawing_read_in_world_coords (mọi parametrization)
2. tests/test_rough_build_drawings.py::test_nha_dan_columns_and_rough
3. tests/test_rough_build_drawings.py::test_nha_pho_columns
4. tests/test_registry.py::test_ket_cau_build_drawing
5. tests/test_rough_structural.py::test_ket_cau_build_drawing

**15 ca thực tế deselected**, không gọi đó là chỉ5case. Lý do: user full không CAD thật. Không đọc Tân Bình hoặc chạy CAD thật để bù phần loại; còn các fixture CAD SYNTHETIC/sample và API/unit được chạy theo suite chọn.

## Skip và môi trường

- **19skip**: 15 bài PostgreSQL cũ thiếu OPTIMAT_TEST_DATABASE_URL;3 opt-in DB/project migration/roles chưa bật;1 symlink Windows không tạo được trong môi trường kiểm. Không bật opt-in hoặc nới quyền symlink.
- Child bỏ DATABASE_URL, OPTIMAT_TEST_DATABASE_URL, OPENAI_API_KEY, OPTIMAT_PROJECT_DB_TEST, OPTIMAT_PROJECT_MIGRATION_TEST; OPTIMAT_NO_DOTENV=1, LLM_PROVIDER=none, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1; overlay test data/sample/catalog.
- Python venv3.13.0, pytest9.1.1. Outside sandbox được auto-review cho phép theo approval mới của user và loopback/TestClient đã xác minh; không đổi actor/chính sách hệ thống.
- Pytest thường, không --runxfail; `-ra -p no:cacheprovider -o faulthandler_timeout=120`, basetemp riêng trong workspace. Lệnh đầy đủ ở environment.json/process.json; cờ lưu không có URL/secret.
- Không DB query/reset/migration/runtime, network OpenAI, upload/browser, source/test edit hoặc restart service.06 chỉ đọc metadata appDB theo quyền riêng, không được coi là testDB trong suite này.

## Bàn giao

preflight.json, hash_preflight_1.json/hash_preflight_2.json, hash_before.json/hash_after.json/hash_diff.json, environment.json/process.json/result.json, pytest_full.log/tracebacks.log và HANDOFF.md. pytest_temp là dữ liệu tạm test. Preflight/command plan trước lúc được mở slot ở reports/backend_20261104/full_preflight giữ nguyên lịch sử.

Chỉ ghi artifacts báo cáo; chưa có full pass để đóng gate tích hợp. Chờ01 phân failure/owner và lịch kiểm tiếp nếu cần; không tự mở rerun hoặc nghiệm thu ACTUAL/UI/native/DBapp.
