# N02-b3 - Probe parity HTTP JSON/Excel/optimizer

03/11/2026. Probe được điều phối giao bổ sung, chỉ chạy **sau** full session93390 terminal và lưu hash_after. Không chạy pytest/full lần hai, không sửa src/tests/scripts/CSV/DB hoặc can thiệp workerUI20288.

**Kết quả: 4/4 fixture PASS; 12/12 HTTP response200; script/collector exit0.** Thời gian script10,11giây. Handle14135 kết thúc; launcher PID26300 được collector đợi thoát. Không traceback lỗi.

## Luồng thật và dữ liệu thay trong RAM

- TestClient với app thật; main.compute_rough là đúng takeoff.compute_rough thật (kiểm identity trước probe). Không mock compute, save_rough, BOQ hoặc export_for_optimizer.
- Cùng một RoughRequest được POST tới `/api/takeoff/rough`, `/api/takeoff/rough/excel`, `/api/takeoff/rough/optimizer` cho mỗi fixture. project_id=None, không DB/.env nên save_rough thật không ghi DB.
- Lấy rows_for bằng runpy từ tests/test_rough_partial.py, không gọi test/pytest. Chỉ patch takeoff.default_catalog trả Catalog.from_csv(None) copyRAM với TH10 waste_pct=0; patch pricing.price_offers trả QUOTE100/kg, data_kind=SYNTHETIC. Không nạp dữ liệu giá thật.
- Python venv3.13.0, child bỏ hai biến DB, OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8. Outside sandbox được auto-review cho phép do TestClient/socketpair cần loopback đã xác minh; không chỉnh chính sách hệ thống.

## Kết quả theo fixture

| Fixture | COT_THEP tấn / đủ | TH10 kg / trạng thái / đủ | Giá fixture / est_cost | Optimizer TH10 |
|---|---|---|---|---|
| Pending hai bảng | 0,063 / false | 0,753 / D / false | 100 / null | missing.known_part=0,753, giữ reason, không có trong materials |
| Pending + manual0,0632 | 0,063 / false | 0,753 / D / false | 100 / null | như trên |
| Resolved cùng scope | 0,032 / true | 0,383 / C / true | 100 / 38 | materials.quantity=0,383, không còn trong missing |
| Resolved hai tầng | 0,063 / true | 0,753 / C / true | 100 / 75 | materials.quantity=0,753, không còn trong missing |

TH10 resolved là C theo hệ số tham khảo/khoảng dây buộc hiện hành, không ép thành A. Không đòi tổng RoughResult là A hoặc đủ vì thép chính vẫn chưa có mã vật liệu cụ thể.

## Kiểm parity đã thực hiện

- Parse bytes HTTP Excel bằng openpyxl, không gọi boq_workbook trực tiếp để thay endpoint.
- COT_THEP: số tổng và complete JSON khớp “Khối lượng”/“Đủ số” ở sheet Tổng hợp; trạng thái khớp. missing của công tác thép khớp missing_reason ở Theo tầng.
- TH10: lượng đã biết, complete, status, lý do thiếu khớp JSON với sheet Vật liệu; pending không sinh est_cost dù còn best_price100/price_source SYNTHETIC. Resolved cost đúng 38/75 theo lượng đã làm tròn và giá fixture. Sheet Vật liệu hiện không có cột est_cost; kiểm chi phí trên JSON, không tuyên bố đã có cột chi phí Excel.
- Optimizer pending giữ known_part/reason đúng JSON, không xuất lượng TH10 vào materials; resolved xuất lượng/status đúng và không còn TH10 trong missing.
- “Đủ kg” sheet Theo nhóm khớp JSON weight_complete: pending dùng **“chưa đủ dữ liệu khối lượng”**, không nhãn cũ “thiếu khối lượng riêng”; resolved nhóm TH10 trong fixture dùng “có”.

## Hash và file tái lập

- hash_before/after probe: **212 file** (src/scripts/tests Python; catalog/rules CSV; ground_truth CSV/JSON); hash_diff changed/added/removed đều rỗng.
- Snapshot probe khác mốc full trước đó vì full đã ghi nhận thêm scripts/import_synthetic_housing.py (211→212). Probe không xóa ngoại lệ full hoặc chứng minh lại toàn suite cho file thêm đó.
- Frontend/SQL/docs/reports ngoài hash; không claim whole repo bất biến.
- runtime_probe.py là script tái lập, chỉ ở thư mục báo cáo được giao; environment.json/process.json lưu lệnh và patch RAM, collector_result.json/report.json lưu exit/các assertion. runtime.log/tracebacks.log không có lỗi.
- Bốn *_request.json; tám JSON response (rough/optimizer); bốn *.xlsx từ endpoint thật. Tệp response đủ để kiểm lại các dòng targeted; không phải hồ sơ nghiệm thu thực.

Chỉ chứng minh parity HTTP/JSON/Excel/optimizer trên fixture **SYNTHETIC**. Không QAUI, không giá thật, không hình học CAD, không kiểm PostgreSQL hoặc xác nhận D02/người kiểm. Chờ điều phối đánh giá cùng ngoại lệ hash của full; không tự nghiệm thu N02.
