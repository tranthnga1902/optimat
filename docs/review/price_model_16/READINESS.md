# Readiness mô hình giá — phiên 16

Ngày rà soát: 03/11/2026. Phạm vi: chỉ đọc mã và tệp cục bộ; không kết nối DB, không train, không sửa source/data/models. Báo cáo riêng này không release quyền ghi. Phiên 01 giữ quyền release/freeze/full; owner04 vẫn giữ pricing/optimizer.

## Kết luận

**CHƯA ĐỦ dữ liệu ACTUAL có nguồn để huấn luyện và báo cáo độ chính xác đồ án.** Có dấu vết công bố giá thật nhưng chưa có chuỗi ít nhất sáu tháng cho đúng vật liệu MVP, cùng địa bàn và cơ sở giá. Không thể suy trạng thái DB hiện tại từ bản dump hoặc PLAN.md. Không dùng dự đoán để lấp yêu cầu báo giá mua thật.

Luồng giữ nguyên: `/do-boc` → `/phan-tho` → `/dieu-chinh` → `/vat-lieu` → `/toi-uu`. Dự đoán giá chỉ tiêu thụ vật liệu/khối lượng của snapshot đã kiểm và lựa chọn sau đó; không làm điều kiện để kiểm khối lượng, không tự nâng nguồn hoặc biến giá dự đoán thành báo giá ACTUAL.

## Bằng chứng cục bộ

| Nguồn | Quan sát | Giá trị sử dụng |
|---|---|---|
| `data/sample/prices_sample.csv` | 1.248 dòng, toàn bộ nhãn SYNTHETIC; 24 kỳ tháng 11/2024–10/2026; `Ha Noi`; AAC01, AAC03, GK02, GK03, GN01 | Chỉ kiểm mã, không phải kết quả thực nghiệm thật |
| `data/cong_bo_gia/02.01_2026_CBGVL-SXD.csv` | 6.974 dòng trích xuất; 59 dòng có material_id, 26 mã; có trang, nhà cung cấp, điều kiện, quy tắc và giá đã đổi đơn vị | Bảng duyệt ứng viên ACTUAL, chưa phải CSV đầu vào train |
| `scripts/import_price_bulletin.py` | Gán ACTUAL/BULLETIN; địa bàn mặc định Hà Nội; ngày từ tham số hoặc chữ ký PDF; lượng 1; đơn vị lấy từ catalog khi nạp DB | Cần kiểm ngày hiệu lực so với ngày ký và chứng từ gốc, không mặc nhiên coi giá công bố là báo giá giao hàng |
| `PLAN.md` | Ghi nhận trước đây 59 price_records ACTUAL/26 mã, thiếu GN01/VU02; yêu cầu ≥6 tháng và ≥3 đại lý/vật liệu MVP | Chỉ là nhật ký, chưa xác minh DB hiện tại |
| `models/material_price_metrics.json` | train/val/test 832/208/208; test 01/07–01/10/2026; contains_synthetic=true | Không dùng làm số liệu độ chính xác đồ án |

26 mã ghép trong bảng công bố: AAC01, AAC02, AAC03, CA01, CA03, CT02, CT04, CT05, CT06, DA01, DA02, DA03, DA04, GK01, MA02, PG02, TH01, TH02, TH03, TH05, TH07, TH08, VU03, XM01, XM02, XM03. Không có GN01/VU02. CSV này không chứa date/province/source/data_kind theo schema train; tên tệp không chứng minh ngày hiệu lực. Chưa xác minh PDF gốc hay nguồn trực tuyến trong lượt này; địa bàn Hà Nội chỉ được hỗ trợ bởi cấu hình importer và tên bãi, chưa đủ để xác nhận mọi dòng.

Metrics mô phỏng hiện có:

| Mô hình | MAE | RMSE | R² | MAPE (%) |
|---|---:|---:|---:|---:|
| XGBoost | 36.105,30 | 66.220,06 | 0,99465 | 4,4720 |
| Giá gần nhất | 23.005,73 | 43.532,29 | 0,99769 | 3,3180 |
| Ridge | 27.186,16 | 47.811,52 | 0,99721 | 2,4911 |

Ngay trên mô phỏng, XGBoost thua giá gần nhất ở MAE/RMSE/MAPE; không suy điều này sang giá thật. MAE/RMSE gộp nhiều đơn vị có giới hạn diễn giải, cần báo riêng từng vật liệu/đơn vị.

## Rà mã và rủi ro đánh giá

- `train.py/load_prices_from_db` đọc toàn bộ price_records; `load_prices` không lọc ACTUAL hoặc xác thực source/price_level. Cảnh báo báo cáo chỉ xét SYNTHETIC, chưa chặn SAMPLE/UNKNOWN. Không chạy `--from-db` với trạng thái hiện tại để tạo kết quả đồ án.
- `time_split` chia các ngày duy nhất 70/15/15; không trộn cùng ngày giữa tập. `build_spec` chỉ fit train, tốt cho tránh rò rỉ chuẩn hóa. Với ít kỳ, tập rỗng hoặc chỉ số R² không đủ quan sát; dữ liệu rỗng có thể lỗi trước kiểm tra. Sáu tháng là mức thu thập tối thiểu của kế hoạch, chưa bảo đảm tập test đủ mạnh.
- Phải dùng thời điểm giá thực sự được biết trước cutoff. Ngày hiệu lực được nhập hồi tố, ngày ký PDF, các bản sửa công bố và cùng báo giá sao chép nhiều nguồn có thể gây rò rỉ dù chia theo date. Giữ nhóm chứng từ/phiên bản, khử trùng trước split, tuyệt đối không dùng test chọn tham số.
- Baseline gần nhất lấy train+validation theo `(material_id, supplier_id)`, fallback median theo vật liệu; chưa tách tỉnh, đơn vị, VAT, vận chuyển, price_level. Chỉ đánh giá các dòng có lookup, trong khi XGBoost/Ridge đánh giá toàn test: cần báo coverage và so trên cùng mask. Nếu không có dòng được phủ, evaluate hiện có thể lỗi.
- Ridge fit train+validation; XGBoost fit train và dùng validation dừng sớm. Đây là giao thức cần công khai, chưa phải cùng lượng dữ liệu fit. Cần chốt giao thức trước test và ghi rõ cố định cửa sổ hay rolling forecast; baseline hiện không cập nhật bằng quan sát trong test.
- `features.py`: phân loại material/supplier/province; số tháng, tháng trong năm, log lượng tương đối theo đơn vị. Chưa dùng VAT, vận chuyển, price_level hay source làm phân tầng. Lượng <=0/NaN/vô hạn và đơn vị không nhất quán cần chặn trước log; load hiện chỉ lọc unit_price >0 và thiếu REQUIRED_COLS.
- `cost_model.py`: load chỉ cần model/spec, chưa kiểm provenance metrics; `knows` chỉ xét vật liệu và supplier xuất hiện độc lập, không chứng minh đúng cặp, địa bàn, thời gian hay đơn vị đã học. Predict chưa tự chặn ngoài miền. Không thay owner04 trong nhiệm vụ này; bàn giao rủi ro để 01 phân công.

## Dữ liệu còn thiếu và tiêu chí trước train

1. Chốt danh sách vật liệu MVP từ các phương án tường đã chọn: gạch, xi măng, cát, vữa AAC nếu có; mapping mã/đơn vị có người duyệt. Không lấy 26 mã hiện có làm đại diện mọi vật liệu phần thô.
2. Thu ít nhất sáu tháng giá ACTUAL có chứng từ gốc và kỳ hiệu lực; ưu tiên thêm kỳ để có validation/test độc lập. Mỗi dòng lưu source/trang, địa bàn, nhà cung cấp, ngày được biết, price_level, đơn vị, quantity, VAT/vận chuyển; phân biệt giá công bố và báo giá đại lý. Với đầu vào mua thật, vẫn cần ≥3 đại lý/vật liệu có tọa độ và lead time theo PLAN.
3. Có export CSV ACTUAL được duyệt, truy xuất nguồn và kiểm trùng, giá/lượng hữu hạn dương; không tự sinh ACTUAL, không trộn SAMPLE/SYNTHETIC. Bảng count theo vật liệu × địa bàn × tháng, số nguồn và khoảng thời gian phải đi kèm. Không truy vấn DB thật trong phạm vi phiên này.
4. Phiên 01 release riêng cho owner phù hợp để khép validation, lọc dữ liệu, baseline theo cùng cơ sở giá, coverage/cùng mask, và protocol thời gian. Chốt cutoff, giữ test kín; báo MAE/RMSE/MAPE theo nhóm, số dòng, missing coverage và baseline Ridge/giá gần nhất. Không yêu cầu XGBoost phải thắng, báo đúng nếu thua.
5. Trước train ghi hash nguồn/CSV, phiên bản thư viện, seed, cấu hình, cutoff, số dòng bị loại; output mới không trùng thư mục có sẵn, không thay models dùng runtime. Sau train đọc metrics để xác nhận ACTUAL-only và có kiểm tra tái lập. Chỉ chạy focused/full theo quyền 01.

## Lệnh đề xuất — CHƯA CHẠY

Chỉ sau khi 01 cho phép chạy train và dữ liệu/protocol ở trên được duyệt; CSV phải được owner chuẩn bị ngoài lượt này. Chọn hậu tố run mới mỗi lần, không tái sử dụng output đã tồn tại:

```powershell
python -m optimat.predict.train --data docs/review/price_model_16/input/prices_actual_approved.csv --out docs/review/price_model_16/runs/actual_20261103_r01
```

Đây là cú pháp CLI đang có, không phải xác nhận đường dẫn input đã tồn tại hoặc mã đã đạt tiêu chí. Không đề xuất `--from-db` cho lượt đánh giá đầu vì hiện chưa lọc data_kind và phiên này không được đọc DB. CLI mặc định thử thêm LightGBM/CatBoost nếu cài; phải ghi đúng các model thực sự chạy và dependency. Không nạp output này vào runtime nếu chưa qua review riêng.

## Giới hạn xác minh

Đã đọc AGENTS.md, PLAN.md, hai đặc tả luồng, train/features/cost_model, metrics, schema price_records, importer công bố và CSV liên quan. Chỉ đếm CSV bằng PowerShell; không import module ứng dụng, không chạy test/full/huấn luyện, không đọc .env hay DSN. Không xác nhận chứng từ gốc, độ đúng mapping hay dữ liệu DB hiện thời. Báo cáo chỉ sửa trong `docs/review/price_model_16/`.
