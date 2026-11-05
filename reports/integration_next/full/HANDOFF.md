# Full tích hợp sau N03/production/preview - 03/11/2026

**Kết quả: CẦN SỬA; full terminal exit1 và phạm vi nguồn thay đổi trong lúc chạy. Không phải baseline đạt trên snapshot bất biến.** Không sửa hoặc chạy lại.

```text
772 collected
1 failed, 756 passed, 15 skipped in 562.59s (0:09:22)
xfailed=0; xpassed=0; errors=0
pytest exit=1; collector/session exit=1
```

Handle **62154** đã được poll trực tiếp bằng write_stdin tới terminal; launcher PID38412 được collector đợi thoát. Kết thúc 22:18:11 giờ Việt Nam (15:18:11 UTC); pytest562,59giây, tổng collector565,62giây. Không suy trạng thái dừng từ PID bị ẩn trong sandbox. Không restart do timeout/log im lặng.

## Failure thật

- Nodeid: **tests/test_review.py::test_review_api**.
- Call site tests/test_review.py:50: TestClient POST `/api/takeoff/view`, upload `data/sample/sample_floor.dxf`, không progressive flag.
- Test kỳ vọng HTTP200 rồi đọc JSON có plans/materials/walls. Thực tế **POST ném ValueError trước assertion status_code**, chưa có HTTP response được test nhận.
- Exception: `ValueError: Out of range float values are not JSON compliant: nan`; stack đi qua FastAPI response/Starlette JSONResponse và json.encoder với allow_nan=False.
- Chưa chứng minh NaN ở field nào, do pollution theo thứ tự test hay regression độc lập. Không tự sửa catalog cache, app, serializer hoặc fixture để ép đạt. Không chạy node riêng hoặc ca khác sau full vì chưa được cấp lượt.
- Tracebacks.log giữ toàn bộ traceback/short summary nguyên văn; pytest_full.log giữ thứ tự các tệp trong full, môi trường/lệnh trong environment.json/process.json. Nhóm production focused đã từng đạt không thay thế bằng chứng failure full này.

## Hash: preflight ổn định, cuối lượt không còn ổn định

Trước chạy đã đọc xác nhận HOLD ở QA_6_MODULE_BROWSER_20261103.md và release của điều phối; kiểm process chỉ đọc ngoài sandbox lúc22:08:16 không có pytest khác. Hai snapshot cách3giây khớp222file, preflight.json/hash_preflight_1.json/hash_preflight_2.json lưu bằng chứng. Snapshot có main.py, drawing/view_progress.py, tests/test_view_progress.py.

Cuối lượt vẫn222file nhưng **8 tệp đổi hash**:

1. scripts/c01_duong_co_so.py
2. scripts/report_labels.py
3. src/optimat/rough/beams.py
4. src/optimat/rough/columns.py
5. src/optimat/rough/models.py
6. src/optimat/rough/walls.py
7. tests/test_evaluate_rough.py
8. tests/test_ground_truth_manifest.py

Không thêm/xóa. Hash trước/sau cụ thể ở hash_before.json/hash_after.json; danh sách ở hash_diff.json. Chưa xác định writer hoặc thời điểm đổi của từng tệp; không suy tất cả thay đổi này gây failure NaN. Cần điều phối chốt nguồn thực tế và ngoại lệ trước quyết định lần kiểm khác. Không che diff hoặc chỉ xét các tệp không đổi để tuyên bố full ổn định.

Phạm vi hash: src/scripts/tests Python; data/catalog,data/rules CSV; data/ground_truth CSV/JSON. Frontend/SQL/docs/reports ngoài phạm vi; không claim whole repo bất biến hoặc frontend đã được full pytest xác minh.

## Môi trường/lệnh và giới hạn

- Python venv3.13.0, pytest9.1.1, pytest thường **không --runxfail**.
- `-ra -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=<reports/integration_next/full/pytest_temp>`.
- Child bỏ DATABASE_URL và OPTIMAT_TEST_DATABASE_URL; OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1; overlay test data/sample/catalog, collector UTF-8.
- require_escalated được auto-review cho phép cho TestClient/socketpair ngoài sandbox như các lượt đã xác minh.
- 15skip vì không đặt OPTIMAT_TEST_DATABASE_URL; không DB test/reset/check_data hoặc ghi DB vận hành. Không có xfail trong summary lần này, nhưng failure và hash drift ngăn dùng nó như bằng chứng nghiệm thu N03/full tích hợp cuối.
- Chỉ ghi báo cáo/basetemp tại reports/integration_next/full. Không sửa source/tests/data/docs chung, không can thiệp workerUI hoặc restart tiến trình phiên khác. Không tự chạy full thứ hai.

## Bàn giao

preflight.json; hash_preflight_1.json/hash_preflight_2.json; hash_before.json/hash_after.json/hash_diff.json; environment.json/process.json/result.json; pytest_full.log/tracebacks.log; HANDOFF.md. pytest_temp là dữ liệu tạm.

Đề nghị điều phối: giữ log lỗi, chốt8file đổi và quyền writer, giao điều tra NaN/thứ tự test trên bản nguồn đã khóa trước khi cấp probe hoặc full mới. Lượt này không chứng minh parity UI/preview thật, giá thực, hình học hoặc xác nhận nghiệp vụ.
