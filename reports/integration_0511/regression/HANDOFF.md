# Full baseline tích hợp không DB - 03/11/2026

Lượt kiểm độc quyền được điều phối cấp cho baseline A01/Q01/BOQ/P0 API worker/N02-a. Chạy toàn suite đúng một lần bằng pytest thường, **không --runxfail**. Không tự nghiệm thu nghiệp vụ hoặc coi N02-b đã hoàn tất.

```text
517 collected
501 passed, 15 skipped, 1 xfailed in 502.95s (0:08:22)
failed=0; errors=0; xpassed=0
pytest exit=0; collector/session exit=0
```

**Đạt lượt hồi quy không DB trên snapshot đã khóa.** Handle 4318 kết thúc; launcher PID41660 được collector đợi thoát. Kết thúc 17:37:31 giờ Việt Nam (10:37:31 UTC). Pytest 502,95 giây, tổng collector 506,47 giây. Không failure/error traceback; tracebacks.log ghi rõ không có phần lỗi.

## Môi trường và phạm vi

- Python venv 3.13.0, pytest 9.1.1; require_escalated được auto-review cho phép vì asyncio/TestClient cần loopback ngoài sandbox đã được chẩn đoán ở lượt trước.
- Child bỏ DATABASE_URL và OPTIMAT_TEST_DATABASE_URL; OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1, overlay test data/sample/catalog. Collector UTF-8.
- Lệnh trong environment.json/process.json: `pytest -ra -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=<reports/integration_0511/regression/pytest_temp>`.
- Không DB/test DB/reset/check_data, không sửa code/data/docs chung, không restart hoặc tự chạy lại. Không can thiệp tiến trình demo.

## Snapshot

- **207 file** trước/sau: src/scripts/tests Python; catalog/rules CSV; ground_truth CSV/JSON (normalized/d02/cases khi có).
- hash_diff.json: **changed=[], added=[], removed=[]**. Không có thay đổi trong phạm vi hash trong lượt chạy.
- Frontend và SQL historical theo điều phối nằm ngoài hash, được phép tiếp diễn; docs/reports khác cũng ngoài phạm vi. Không kết luận toàn repo bất biến hoặc UI/SQL đã được kiểm bởi suite này.

## Giới hạn kết quả

- **15 skipped** vì chưa đặt OPTIMAT_TEST_DATABASE_URL: không chứng minh đường PostgreSQL, schema hoặc dữ liệu DB vận hành đã đạt.
- **1 xfailed**: `tests/test_rough_secondary.py::test_overlapping_ties_deduct_masonry_once` - hai giằng cùng đoạn trừ khối xây hai lần (N03). Không coi lỗi này đã được giải quyết.
- Không còn xfail N02 trong summary pytest thường của lượt này. Đây là bằng chứng kiểm baseline hiện tại, không thay review/đáp án đầy đủ của N02-b.
- API concurrency dùng event health/cleanup/mock CAD trong test; chưa phải smoke KT46 thật hoặc chứng minh hiệu năng đọc bản vẽ ngoài thực tế. Suite có các bài bản vẽ khác nhưng không thay cổng demo/end-to-end và xác nhận người kiểm.
- Không tự đổi nhãn da_kiem/KPI hoặc đánh nghiệm thu A01/Q01/BOQ/J04/J05/N02. Điều phối quyết định cổng tiếp theo theo bằng chứng và giới hạn trên.

## File bàn giao

pytest_full.log, tracebacks.log, result.json, environment.json, process.json, hash_before.json, hash_after.json, hash_diff.json và HANDOFF.md. pytest_temp là dữ liệu tạm test. Chỉ ghi trong reports/integration_0511/regression; không ghi đè các log lịch sử khác.
