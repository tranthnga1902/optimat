# Hồi quy sau gate dữ liệu/C01 - ngoài sandbox, không DB

Ngày 03/11/2026. Điều phối cấp lượt toàn suite duy nhất, sole test owner. **ĐẠT lượt hồi quy không DB trên snapshot đã khóa; không nghiệm thu nghiệp vụ hoặc đường PostgreSQL.**

## Kết quả thật

```text
collected 419 items
401 passed, 15 skipped, 3 xfailed in 549.74s (0:09:09)
pytest exit: 0
failed: 0; errors: 0
```

Lượt kết thúc lúc 16:54:11 giờ Việt Nam (09:54:11 UTC). Bộ thu thập tính 553,7 giây gồm khởi động/ghi báo cáo; thời gian pytest là 549,74 giây.

**Phân biệt exit:** pytest subprocess đã exit 0, result.json và toàn bộ hash sau chạy được lưu. Sau đó bộ thu thập lỗi UnicodeEncodeError của cp1252 khi in đuôi log tiếng Việt ra console, nên session exec trả exit 1. Đây là lỗi xuất console sau kiểm, không phải lỗi pytest. Đã bổ sung `collector_session_exit_code` và mô tả vào result.json; không chạy lại suite để sửa báo cáo.

## Phạm vi/môi trường

- Python venv 3.13.0, pytest 9.1.1; lệnh trong environment.json/process.json: `python -m pytest -ra -o faulthandler_timeout=120 -p no:cacheprovider --basetemp=<reports/c01_regression_outside/pytest_temp>`.
- require_escalated được auto-review cho phép. Lý do: sandbox timeout ở socketpair/asyncio; hai probe và đúng ca TestClient ngoài sandbox đã đạt ở lượt chẩn đoán trước. Không thay đổi chính sách hệ thống hoặc sửa app/test để né lỗi môi trường.
- Child pytest bỏ DATABASE_URL và OPTIMAT_TEST_DATABASE_URL, OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1. Overlay test dùng data/sample/catalog theo quy ước conftest. Không in secret/URL.
- Không DB/reset/check_data, không chạy ca khác đồng thời, không restart do timeout. Handle 27573 đã kết thúc; launcher PID29492 được bộ thu thập đợi thoát.

## Khóa nguồn

- Snapshot mới **204 file**: src/scripts/tests `*.py`; data/catalog và data/rules `*.csv`; data/ground_truth toàn bộ `*.csv`/`*.json` (gồm normalized/d02/cases khi có).
- hash_before.json và hash_after.json: **không changed, added hoặc removed**; hash_diff.json xác nhận ba danh sách rỗng. Đây là bằng chứng phạm vi file đã khóa không thay trong lượt kiểm, không bao gồm mọi file khác của workspace.
- Không chỉnh source/code/data/docs chung. Chỉ ghi báo cáo và basetemp trong thư mục lượt này; không ghi đè log INCOMPLETE ở c01_regression.

## Giới hạn còn giữ

- 15 bài skip vì chưa đặt OPTIMAT_TEST_DATABASE_URL; không chứng minh đường DB đã đạt.
- 3 xfail hiện hữu: phân cách số Việt Nam trong bảng thép; bảng thép lặp thiếu số hiệu; giằng chồng trừ khối xây hai lần. Không coi xfail là chức năng đã sửa.
- Không có failure traceback trong lần này. Full log có lý do skip/xfail cụ thể; không dùng kết quả để nâng nhãn nguồn/da_kiem hay KPI hồ sơ thực.
- Lượt sandbox trước vẫn INCOMPLETE, không sửa lịch sử kết quả đó. Lượt này là lần được cấp riêng trên snapshot sau sửa gate.

## File bàn giao

- pytest_full.log: toàn bộ log, summary và lý do skip/xfail.
- result.json: counts, pytest exit 0, collector exit 1 và nguyên nhân tách riêng.
- environment.json/process.json: môi trường không nhạy cảm, lệnh, PID/mốc bắt đầu.
- hash_before.json, hash_after.json, hash_diff.json: 204 hash và đối chiếu.
- HANDOFF.md này; pytest_temp là dữ liệu tạm của test.

Điều phối có thể dùng kết quả này làm bằng chứng hồi quy không DB cho đúng snapshot. DB và xác nhận nghiệp vụ D02/J05 vẫn có cổng riêng; không tự nạp DB thật hoặc đánh nghiệm thu.
