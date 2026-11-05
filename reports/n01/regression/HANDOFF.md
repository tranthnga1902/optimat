# N01 - Hồi quy toàn bộ không DB, ngoài sandbox

03/11/2026. Lượt kiểm độc quyền do điều phối cấp; chạy toàn suite đúng một lần, không sửa mã/dữ liệu và không mở N02.

## Kết quả

```text
444 collected
427 passed, 15 skipped, 2 xfailed in 558.65s (0:09:18)
0 failed; 0 errors
pytest exit 0; collector/session exit 0
```

Handle 63522 đã kết thúc, launcher PID5392 được collector đợi thoát. Kết thúc 17:08:35 giờ Việt Nam (10:08:35 UTC). Thời gian pytest 558,65 giây; tổng collector 562,5 giây. Collector dùng UTF-8 và in log thành công, không còn lỗi UnicodeEncodeError như lượt trước.

## Môi trường

- Python venv 3.13.0, pytest 9.1.1, require_escalated được auto-review cho phép dựa trên chẩn đoán socketpair/TestClient trước đây.
- Child không có DATABASE_URL hoặc OPTIMAT_TEST_DATABASE_URL; OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1; overlay test data/sample/catalog.
- `pytest -ra -o faulthandler_timeout=120 -p no:cacheprovider --basetemp=<reports/n01/regression/pytest_temp>`; lệnh chính xác/environment chỉ cờ không nhạy cảm trong environment.json và process.json.
- Không DB/reset/check_data, không ca khác song song, không restart do timeout.

## Hash và ngoại lệ phạm vi

- hash_before.json/hash_after.json: **204 file**, cùng phạm vi src/scripts/tests Python; catalog/rules CSV; ground_truth CSV/JSON, gồm normalized/d02/cases khi có.
- hash_diff.json: **changed=[], added=[], removed=[]**. Snapshot đã khóa không thay trong thời gian chạy.
- Điều phối cho phép frontend sửa riêng song song (Review/model, /vat-lieu, /toi-uu). Frontend **không nằm trong 204 file**, nên không kết luận toàn repo bất biến hoặc giao diện đã được kiểm. Các tài liệu ngoài phạm vi hash cũng không thuộc kết luận bất biến này.

## Skip/xfail và giới hạn

- **15 skip**: chưa đặt OPTIMAT_TEST_DATABASE_URL; không chứng minh PostgreSQL đã đạt.
- **2 xfail còn lại**: test_duplicate_table_without_mark_counted_once (bảng thép lặp thiếu số hiệu) và test_overlapping_ties_deduct_masonry_once (giằng chồng trừ khối xây hai lần).
- Xfail phân cách số Việt Nam của N01 không còn trong danh sách xfail lần này. Không coi hai xfail còn lại là lỗi đã được sửa.
- Không có failure traceback. Không dùng kết quả để tự nghiệm thu N01, nâng trạng thái dữ liệu/người kiểm hoặc công bố KPI nghiệp vụ. Điều phối quyết định nghiệm thu; không mở N02 từ lượt kiểm này.

## Bàn giao

- pytest_full.log: log đầy đủ, thống kê và lý do skip/xfail.
- result.json: exit, thời gian, summary và hash diff; environment.json/process.json: lệnh/cờ/PID.
- hash_before.json, hash_after.json, hash_diff.json: bằng chứng snapshot.
- HANDOFF.md này; pytest_temp là thư mục tạm test.

Chỉ tạo báo cáo/basetemp trong reports/n01/regression; không sửa source, CSV/JSON nguồn, tài liệu chung, NHAT_KY hoặc SPRINTS. Chờ điều phối đọc và quyết định bước tiếp.
