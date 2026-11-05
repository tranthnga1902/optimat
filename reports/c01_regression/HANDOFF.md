# Hồi quy sau C01 - lượt không DB, 03/11/2026

**Kết quả: INCOMPLETE, chưa chứng minh hồi quy đạt.** Chạy toàn suite đúng một lần. Không có thống kê cuối passed/skipped/xfail/failed; các trường này để null trong result.json, không dùng 0 thay kết quả chưa có.

## Môi trường và phạm vi

- Python venv 3.13.0, pytest 9.1.1; môi trường chi tiết ở environment.json, chỉ cờ không nhạy cảm.
- Bỏ DATABASE_URL và OPTIMAT_TEST_DATABASE_URL trước khi tạo subprocess; OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8; overlay test data/sample/catalog; tắt cacheprovider, basetemp riêng.
- Không chạy DB test/reset/nạp DB/check_data. Không sửa source, CSV, docs chung hoặc restart suite.
- Hash 173 file: src/scripts/tests Python và CSV trong data/catalog,data/rules; trước/sau suite và sau chẩn đoán đều không changed/added/removed.

## Lượt toàn suite

- Handle 10603; launcher PID20984, Python con PID27556, chuỗi parent lưu ở process_observation_1.json.
- Bắt đầu 2026-11-03 09:34:13 UTC (16:34:13 giờ Việt Nam). Thu thập **417 items**.
- Log dừng tại tests/test_admin_db.py, chưa có ký hiệu kết quả bài đầu tiên. Hai mẫu lúc 16:37:16 và 16:38:13: CPU launcher 0,03125s, child 10,546875s không đổi; log 333 byte, last-write 16:34:29. Threads ở trạng thái chờ; chỉ các dữ kiện này chưa chứng minh deadlock hoặc nguyên nhân.
- Theo chỉ dẫn điều phối, ngắt mềm đúng session. Session trả exit 1; không thu được mã thoát pytest riêng hoặc traceback cuối. Không gán exit 1 của session thành “1 test failed”. Xác nhận bốn PID của cây chạy đã vắng mặt trước khi chạy chẩn đoán.
- process.json/result.json và process_after_interrupt.json lưu bằng chứng; pytest_full.log giữ nguyên, không ghi đè.

## Một ca chẩn đoán, không chạy song song

- Sau khi cây suite đã thoát, chỉ chạy tests/test_admin_db.py::test_overview_and_rows_from_csv với --full-trace, faulthandler_timeout=60, môi trường không DB như trên, basetemp/log riêng.
- Handle 35803, launcher PID32240. Thu thập **1 item**; sau 60 giây có stack dump trong pytest_diagnostic.log.
- Stack chứng minh thread portal đang tạo asyncio event loop qua windows_events/proactor_events, socket._fallback_socketpair rồi socket.accept. Thread chính đang chờ concurrent Future từ anyio.start_blocking_portal, qua Starlette TestClient; call site tests/test_admin_db.py:19 là client.get('/api/admin/db').
- Chưa thấy endpoint nghiệp vụ hoặc truy vấn DB trên stack. **Điểm chờ đã xác định; nguyên nhân gốc chưa chứng minh.** Có thể cần điều tra runtime/socketpair/môi trường Windows riêng; không suy chắc do sandbox hoặc do source dự án chỉ từ stack này.
- Sau khi lưu stack, ngắt mềm session chẩn đoán; session exit 1, pytest exit riêng không có, không thống kê pass/fail. Xác nhận launcher/child đã thoát, lưu diagnostic_after_interrupt.json. Không còn session test chạy nền của lượt này.

## File bàn giao

- hash_before.json, hash_after.json, hash_diff.json; hash_after_diagnostic.json, hash_diff_after_diagnostic.json.
- environment.json, process.json, process_observation_1.json, process_observation_2.json, process_after_interrupt.json, result.json.
- pytest_full.log; diagnostic_process.json, pytest_diagnostic.log, diagnostic_after_interrupt.json, diagnostic_result.json.
- HANDOFF.md này. Thư mục pytest_temp/diagnostic_temp là basetemp của hai lần chạy, không phải dữ liệu nghiệm thu.

## Đề xuất cho điều phối

Lượt hồi quy không DB chưa hoàn tất; không dùng số test lịch sử để thay kết quả. Bằng chứng đủ để chuyển sang điều tra điểm tạo event loop/socketpair trước khi cấp lượt full suite khác. Không sửa/restart tự động. Chưa có căn cứ sửa endpoint hoặc source J05c/C01; không nghiệm thu nghiệp vụ.

## Bổ sung đối chiếu môi trường theo điều phối

- Sau khi xác nhận hai cây test trước đã thoát, chạy riêng hai probe trong sandbox, mỗi probe là subprocess có timeout 10 giây: `socket.socketpair()` và `asyncio.new_event_loop()` đều timeout; subprocess probe tương ứng được kết thúc/đợi thoát bởi subprocess.run, không chạy song song. Kết quả ở runtime_probes_sandbox.json; handle 67223 đã exit 0 (đó là exit của bộ thu thập, không phải probe đạt).
- Auto-review cho phép exec_command require_escalated đối chiếu runtime và đúng một ca TestClient. Ngoài sandbox, hai probe đều exit 0, stdout OK; runtime_probes_outside.json.
- Ca ngoài sandbox: tests/test_admin_db.py::test_overview_and_rows_from_csv, `--full-trace`, faulthandler_timeout=60, không cacheprovider, basetemp riêng; vẫn loại DATABASE_URL và OPTIMAT_TEST_DATABASE_URL, OPTIMAT_NO_DOTENV=1 và PYTHONIOENCODING=utf-8. **1 passed in 7.54s, pytest exit 0**. Handle 22233 đã kết thúc; launcher PID17468 được bộ thu thập đợi kết thúc. Log pytest_testclient_outside.log, metadata testclient_outside_process.json, kết quả testclient_outside_result.json.
- Đối chiếu cho thấy điểm chờ socketpair/asyncio và ca TestClient phụ thuộc môi trường sandbox so với ngoài sandbox. Chưa phân định cơ chế chính sách/socket Windows sâu hơn; không đổi chính sách hệ thống hoặc source ứng dụng/tests để né.
- **Chưa chạy full suite ngoài sandbox.** Điều phối yêu cầu đợi bàn giao gate dữ liệu nhãn mâu thuẫn và khóa hash nguồn mới rồi mới cấp lượt. Kết quả ca đơn không thay trạng thái INCOMPLETE của suite 417 bài.
- Không còn ca test chạy nền thuộc lượt này; không sửa source/data. Các file bổ sung chỉ ở reports/c01_regression.
