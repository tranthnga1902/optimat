# A01/Q01/BOQ - Test trọng tâm không DB, 03/11/2026

**Kết quả: CẦN SỬA / chờ điều phối phân lỗi.** Chạy đúng một lượt sáu tệp đã giao; không tự sửa hoặc chạy lại.

```text
88 collected
1 failed, 87 passed in 37.31s
passed=87; skipped=0; xfailed=0; xpassed=0; failed=1; errors=0
pytest exit=1; collector/session exit=1
```

Handle 49873 đã kết thúc; launcher PID28940 đã được bộ thu thập đợi thoát. Kết thúc 17:12:45 giờ Việt Nam (10:12:45 UTC); pytest 37,31 giây, tổng collector 40,47 giây. Không full suite.

## Failure

`tests/test_rough_status.py::test_reference_factor_downgrades_material_to_c`, dòng 104: lượng XM02 đúng 4,151 tấn nhưng `xm.status` thực tế là **D**, test đòi **C**. Assertion dừng trước khi chứng minh các kiểm tra tiếp theo trong hàm.

Traceback đầy đủ được tách ở tracebacks.log; toàn log ở pytest_focused.log. Chưa có lỗi thứ hai trong lượt này.

Đọc mã sau test, không chạy thêm ca: `_Bill.result` hiện đặt `complete=False` khi phần lượng mua cần hao hụt nhưng tỷ lệ thiếu/không hợp lệ, rồi gán `status=D` khi không complete. Test dùng Norm tham khảo cho XM02, norm_code trống, nên phần góp không được đánh đã gồm hao hụt qua mã bảng. Điều phối cần phân định fixture thiếu dữ liệu hao hụt với lỗi triển khai trước khi sửa: kết quả test chứng minh xung đột kỳ vọng C/D, chưa cho phép hạ D xuống C chỉ để test đạt. Không sửa dữ liệu ACTUAL hoặc thêm xfail để che.

## Phạm vi và bằng chứng

- Lệnh: pytest sáu tệp test_rough_materials.py, test_rough_plaster.py, test_rough_status.py, test_export_boq_cli.py, test_rough_takeoff.py, test_rough_agent.py, `-ra -p no:cacheprovider`, faulthandler_timeout=120, basetemp riêng. Lệnh chính xác trong process.json/environment.json.
- Ngoài sandbox được auto-review cho phép do TestClient cần loopback đã kiểm ở lượt trước. Python venv 3.13.0, pytest 9.1.1; child bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, overlay data/sample/catalog, collector UTF-8.
- Snapshot **205 file** hiện có: src/scripts/tests Python; catalog/rules CSV; ground_truth CSV/JSON. Không ép số lượng về 204 của snapshot cũ. hash_before.json/hash_after.json khớp: changed/added/removed đều rỗng.
- Frontend và SQL được điều phối cho sửa ngoài phạm vi hash; không kết luận toàn repo không đổi. Các docs/reports khác cũng ngoài hash.
- Chỉ ghi báo cáo và basetemp dưới reports/a01_q01_boq/focused; không sửa code/data/docs chung, không DB/reset/check_data, không test lại.

## File bàn giao

pytest_focused.log, tracebacks.log, result.json, environment.json, process.json, hash_before.json, hash_after.json, hash_diff.json, HANDOFF.md. pytest_temp là thư mục tạm test.

Chờ điều phối giao lỗi status/fixture cho writer phù hợp; chưa có cổng để chạy lại/full suite hoặc nghiệm thu A01/Q01/BOQ từ lượt này.
