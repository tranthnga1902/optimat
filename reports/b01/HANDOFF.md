# B01 - Test vật liệu cốp pha theo cấu kiện

03/11/2026. **Đạt lượt test trọng tâm; chờ Codex/điều phối review.** Chỉ thêm `tests/test_rough_formwork_materials.py` và báo cáo tại reports/b01. Không sửa materials.py, models.py, norms.py, test_rough_materials.py, CSV/catalog/DB hoặc tài liệu chung; không chạy full suite.

## Kết quả

```text
pytest tests/test_rough_formwork_materials.py -ra -p no:cacheprovider --basetemp=<reports/b01/pytest_temp>
12 collected; 12 passed in 2.85s
failed=0; errors=0; skipped=0; xfailed=0; xpassed=0
pytest/collector exit=0
```

Python venv 3.13.0, pytest 9.1.1, chạy sandbox bình thường vì chỉ gọi pure materials. Child bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8; không TestClient/CAD/asyncio hoặc DB. Catalog.from_csv(None) lấy catalog gốc, load_norms có đường dẫn CSV rõ ràng. Không cần escalation, không chạy lại.

## Đã đọc và phạm vi hành vi

- `materials_for_works` nhánh COP_PHA chọn GO_<formwork_of>; `norm_line` đổi đơn vị/cộng các thành phần; `_Bill.result` làm tròn 3 số lẻ và giữ hao hụt đã gồm.
- `norms_for` chọn variant, `load_norms`/unit_factor; WorkItem và ProjectParams; caller dầm/móng/thang tạo formwork_of DAM/MONG/CAU_THANG.
- CSV AF.81120/81140/81160 hiện có. Không sửa định mức hoặc bổ sung nguồn mới; các diện tích là fixture kỹ thuật SYNTHETIC, không phải hồ sơ thật hoặc nghiệm thu định mức.

## Kỳ vọng tính riêng, không tính từ loader trong assertion

| Ca | Số kiểm |
|---|---|
| DAM 10 m² | CP03 = (0,794 + 0,189 + 0,957)/100 ×10 = 0,194 m³; CP06 =14,29/100 ×10 =1,429 kg |
| MONG 100 m² | CP03 =0,794+0,210+0,335 =1,339 m³; CP06 =15 kg |
| CAU_THANG 100 m² | CP03 =0,794+0,981 =1,775 m³; CP06 =11,45 kg |
| Ba cấu kiện trên cộng chung | CP03=3,308 m³; CP06=27,879 kg, không dùng hệ số của một cấu kiện cho cả tổng |
| Ba ca âm tương ứng | Đảo dấu đúng CP03/CP06; không bỏ phần âm |
| DAM +10 và −2 m² | Tổng chưa làm tròn 0,1552 m³/1,1432 kg; đầu ra 0,155 m³/1,143 kg |
| GO_KHONG_CO | Một dòng quantity=None, D/incomplete và lý do định mức/cấu kiện; không dùng hệ số chung |
| quantity=None với DAM/MONG/CAU_THANG | CP03/CP06 đều trống lượng và lượng mua, D/incomplete; có cảnh báo thiếu khối lượng, không số 0 |

Ca có số còn kiểm đơn vị, complete và quantity_with_waste bằng quantity vì định mức đã gồm hao phí theo metadata hiện có; không cộng thêm hao hụt. Không khẳng định đủ khối lượng riêng/vận chuyển/giá hoặc thiết bị huy động ngoài phạm vi phép kiểm.

## Hash/diff và giới hạn

- hash_before.json lưu trước khi thêm test; hash_after.json sau chạy: **16 tệp được bảo vệ không đổi** gồm materials.py/models.py/norms.py, các CSV catalog dùng và CSV dinh_muc_phan_tho. hash_diff.json: changed=[]; không có tệp được bảo vệ bị mất trong lần hash sau.
- Test mới SHA-256: `f7d9be73f346f9cc8bf3e7d7dac3c39fded18f06fa57dae504773f412e6eb8bf` (environment.json và result.json ghi trước/sau).
- B01_tests.diff là diff thêm tệp từ /dev/null, không chứa diff workspace của phiên khác.
- N02-b1 đang được phép sửa rebar; frontend và các file khác không thuộc phạm vi hash B01. **Không kết luận toàn repo bất biến.**
- Không phát hiện lỗi trong 12 ca này nên không sửa source. Không kiểm hình học CAD/API/BOQ/DB/full suite hoặc xác nhận định mức mới.

## File bàn giao

Test mới; reports/b01/B01_tests.diff, pytest_focused.log, tracebacks.log (không có failure/error), result.json, environment.json, process.json, hash_before.json, hash_after.json, hash_diff.json và HANDOFF.md. pytest_temp là dữ liệu tạm test.

Chờ điều phối review B01 và cấp lượt khác nếu cần; không tự đánh nghiệm thu hoặc mở phần sửa materials của writer b3.
