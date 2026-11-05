# N01 — Bàn giao sửa số hỗn hợp trong bảng thép

03/11/2026 — **CHỜ REVIEW ĐỘC LẬP**, chưa tự nghiệm thu; C01 đã cho phép mở N01 theo `docs/review/C01_NGHIEM_THU_KY_THUAT.md`. Không mở N02/N03/A01.

## Thay đổi và trước–sau

- Chỉ sửa `src/optimat/rough/rebar.py::_num` và `tests/test_rough_rebar.py`; bằng chứng riêng trong thư mục này. Không sửa caller, evidence/missing, khử trùng, schema, locale, UI, CSV/DB hoặc tài liệu chung.
- Trước: `1.200,5` / `1,200.5` → None. Sau: cả hai → 1200.5; nhiều nhóm nghìn hợp lệ cũng được đọc. Chuỗi hai dấu sai nhóm `12.00,5` / `1,20.5`, thiếu phần thập phân hoặc dấu lặp sai → None. Kiểm nhóm trước khi chuẩn hóa, không đoán theo kích thước/khối lượng.
- Giữ quy ước một dấu: `5.000 → 5000`, `3.200 → 3200`, `1.200 → 1200`, `1,200 → 1.2`, `3.2 → 3.2`; giữ số nguyên, rỗng và Ø16. Không hỗ trợ mọi locale; đây là hợp đồng phần mềm theo BA đã chốt.
- Test tích hợp đọc bảng SYNTHETIC kiểm chiều dài mm/m, tổng số thanh và khối lượng bảng ghi; kg tính khớp 1896.79 hoặc 2370.00 theo ca. Với 1200.5 m, vẫn đổi sang mm rồi báo ngoài khoảng, không tự ép về chiều dài hợp lý. Chuỗi sai nhóm với Ø hợp lệ vẫn giữ dòng, evidence gốc và missing chiều dài.
- Bỏ duy nhất decorator xfail mixed separators **sau** lượt 17 ca mixed chạy đạt với `--runxfail`. Xfail bảng lặp N02 giữ nguyên; file/test N03 không sửa.

## Test và môi trường

Python `.venv/Scripts/python.exe`; mọi subprocess test đều bỏ `DATABASE_URL` và `OPTIMAT_TEST_DATABASE_URL`, đặt `OPTIMAT_NO_DOTENV=1`, `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1`, không cacheprovider và basetemp riêng ở reports/n01. Không nạp DB hoặc chạy full suite.

| Bằng chứng | Phạm vi và kết quả |
|---|---|
| `pytest_mixed.log`, `result_mixed.json` | `pytest tests/test_rough_rebar.py -k mixed --runxfail -q`: **17 passed, 17 deselected**, pytest exit 0; decorator N01 lúc đó còn giữ để xác minh trước khi bỏ |
| `pytest_focused.log`, `result_focused.json` | Sau bỏ xfail N01: `pytest tests/test_rough_rebar.py tests/test_rough_steel.py tests/test_rough_agent.py -k "not test_agent_api_rough_params" -q -ra`: **40 passed, 1 deselected, 1 xfailed**, pytest exit 0, 13.45s; xfail đúng N02 |
| `pytest_testclient.log`, `result_testclient.json` | `pytest tests/test_rough_agent.py::test_agent_api_rough_params -q -ra`: **1 passed**, pytest exit 0, 6.78s; chạy riêng ngoài sandbox bằng require_escalated được auto-review cho phép, theo bằng chứng socketpair/asyncio trong `reports/c01_regression/HANDOFF.md` |

Tổng phạm vi ba file sau sửa (hai lượt cuối, không cộng trùng lượt mixed): **41 passed, 1 xfailed, 0 failed, 0 errors, 0 skipped**. Mã thoát pytest lưu riêng trong JSON. Bộ thu thập lượt focused gặp cp1252 khi in lại log tiếng Việt sau khi đã lưu kết quả, nên shell session exit 1; **không phải pytest thất bại**. Đã đọc lại file UTF-8: pytest exit 0; không chạy lại vì lỗi in log.

## Snapshot/hash/diff và giới hạn

- `before/` và `after/`: snapshot nguyên hai file được phép sửa; `N01.diff`: diff so trực tiếp snapshot trước/sau, không dùng git HEAD vốn đã có sửa của phiên khác.
- `hash_before.json` / `hash_after.json`: SHA-256 cùng 204 đường dẫn code/test/CSV/JSON từ manifest hồi quy C01; `hash_diff.json` chỉ có **hai file N01**. 202 file khác không đổi trong khoảng chụp; không phát hiện writer khác trên tập được theo dõi. Đối chiếu source ngoài thân `_num` giữ nguyên. Manifest không bao phủ mọi file của workspace.
- `parser_before.json` / `parser_after.json`: tái hiện bằng cách lấy đúng AST hàm `_num` từ snapshot/nguồn, không import ứng dụng hay DB; là probe parser, không thay test tích hợp.
- SHA-256 source: trước `449fe02de5e64d1e7622fb81cc72468cdb412c4842d62ab88fb7610500b60817`; sau `3c5fb2ccd7126cc658b74027b010c97205d35e3b8eec372385155deb2fdcf918`.
- SHA-256 test: trước `a4ba9a949a265c68da8a2636e35c9877e171abc8647b956d4b04c753d08d1bb5`; sau `8846466d381d62b319933c77baf91db58906548339b35c0be31fbb98b5b5bdeb`.
- Không đổi cơ chế lấy token số đầu tiên/điều kiện dừng khi cả Ø và chiều dài không đọc được; không thiết kế parser locale tổng quát. N02/N03 vẫn chưa sửa. Chưa chạy full suite/DB; không có bằng chứng nghiệm thu đáp án D02 hoặc độ chính xác công trình từ test SYNTHETIC.

Việc tiếp: điều phối review diff và quy ước nhóm, xác minh độc lập test/hash, cấp lượt full khi phù hợp. Dòng nhật ký đề xuất: “03/11/2026 — N01 sửa mixed separators hợp lệ, giữ hợp đồng một dấu/callers; trọng tâm 41 passed, 1 xfailed (N02), hash204 chỉ đổi 2 file được giao; chờ review và lượt full, chưa DB/nghiệm thu.”

## Cập nhật điều phối — khóa mã chờ hồi quy

Theo thông báo điều phối ngày 03/11/2026: đã đọc `N01.diff`, `hash_diff.json`, kiểm parser/callers/test và chạy độc lập rebar + steel: **36 passed, 1 xfailed, pytest exit 0**; chưa thấy lỗi chặn trong phạm vi N01. Đây là kết quả do điều phối cung cấp, không phải lượt test bổ sung của phiên này.

Mã/tests khóa ở SHA-256 trong `hash_after.json`; không sửa thêm trong lúc J04 chạy full suite N01. Chỉ cập nhật HANDOFF này; giữ xfail N02/N03, chưa mở N02. Trạng thái: **review phạm vi chưa thấy lỗi chặn, CHỜ HỒI QUY J04 và quyết định nghiệm thu của điều phối**; chưa tự nghiệm thu N01.
