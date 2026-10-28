# Kế hoạch chi tiết OptiMat AI

Đồ án 15 tuần, 05/10/2026 đến 17/01/2027. Bản này điều chỉnh ngày 12/10/2026 theo ba quyết định:

1. **Thu hẹp giả định đầu vào (góp ý của giảng viên hướng dẫn):** chỉ cam kết sai số đo bóc dưới 10% trên bản vẽ đạt bộ quy ước, với 20–30 mặt bằng kiểm tra có đáp án đo tay.
2. **Hai tầng đánh giá:** tầng 1 là cam kết trên bản vẽ đạt quy ước; tầng 2 là báo cáo số liệu trên 10–15 bản vẽ gốc, không hứa ngưỡng.
3. **Mô hình ngôn ngữ:** mô hình của OpenAI gọi qua API thay cho Qwen 4B, điều hướng agent bằng gọi công cụ. XGBoost vẫn huấn luyện trên máy.

4. **Kiến trúc agent (12/10/2026):** một agent điều phối (Orchestrator, mô hình của OpenAI) và sáu công cụ chuyên trách:
   Takeoff, Data, Price (XGBoost), Optimize (NSGA-II), Compare, Procurement. Không có agent viết báo cáo; biểu đồ là
   thành phần giao diện. Không dùng kho dữ liệu riêng.
5. **Đại lý và giá ba mức:** đại lý thu thập tay từ Google Maps (mẫu `OptiMat AI - Thu thap dai ly.xlsx`); giá đại lý,
   giá dự đoán, hoặc loại khỏi tối ưu khi không có giá.

Chi tiết nằm trong Charter, PRD (mục 3.6 đến 3.9, 4.2, 5.7) và tài liệu cơ sở dữ liệu. Bảng kế hoạch nộp Khoa chia 7 giai đoạn:
tuần 1, 2, 3–4, 5–7, 8–9, 10–12, 13–15; danh sách việc theo tuần dưới đây chi tiết hơn và còn điều chỉnh.

## Tổng quan theo tuần

| Tuần | Thời gian | Nội dung chính | Kết quả bàn giao |
|---|---|---|---|
| 1 | 05/10–11/10 | Mã nền, lược đồ 19 bảng, bóc tách bằng quy tắc, dữ liệu 75 vật liệu, PRD | Đã xong |
| 2 | 12/10–18/10 | Chốt phạm vi với giảng viên; chạy agent với API thật; nạp danh mục; bắt đầu thu bản vẽ | Phạm vi đã duyệt |
| 3–4 | 19/10–01/11 | Chuẩn hóa bản vẽ, đo tay đáp án; lấp định mức và hao hụt; bắt đầu thu giá | Bộ bản vẽ có đáp án |
| 5 | 02/11–08/11 | Sửa module bản vẽ, bước kiểm tra quy ước, chỉnh quy tắc trên nhóm build | Module sẵn sàng cho bộ test |
| 6 | 09/11–15/11 | Chạy bộ test tầng 1; U nhiều lớp; tối ưu dùng `wall_systems` | Số liệu đo bóc tầng 1 |
| 7 | 16/11–22/11 | Huấn luyện XGBoost với giá thật | Mô hình giá và bảng so sánh |
| 8 | 23/11–29/11 | Endpoint agent, ghi cơ sở dữ liệu, đăng nhập, đánh giá agent | Luồng đầy đủ qua API |
| 9–10 | 30/11–13/12 | Giao diện React, bản đồ | Ứng dụng web |
| 11 | 14/12–20/12 | Hạng mục mở rộng chờ chốt | Theo lựa chọn |
| 12 | 21/12–27/12 | Thực nghiệm so sánh thuật toán, độ nhạy, tầng 2 | Bảng và biểu đồ thực nghiệm |
| 13 | 28/12–03/01 | Nghiên cứu tình huống, chốt số liệu | Chương thực nghiệm |
| 14 | 04/01–10/01 | Viết báo cáo, slide, video demo dự phòng | Bản thảo báo cáo |
| 15 | 11/01–17/01 | Sửa theo góp ý, nộp, tập bảo vệ | Hồ sơ nộp |

## Tuần 1: Khởi động (05/10–11/10), đã xong

- [x] Mã nền: đọc DXF/DWG, nhận diện tường, đo bóc, XGBoost, NSGA-II, API.
- [x] Bóc tách vật liệu bằng quy tắc (`drawing/material_rules.py`, `data/rules/material_rules.csv`).
- [x] Lược đồ 19 bảng; `sql/03_materials.sql` nạp 75 vật liệu, 20 phương án tường, 13 quan hệ.
- [x] PRD, đề cương, bảng kế hoạch.
- [x] Agent gọi công cụ qua API của OpenAI (`agent/orchestrator.py`), mới kiểm thử bằng mô hình giả.

## Tuần 2: Chốt phạm vi (12/10–18/10)

- [ ] Gửi giảng viên: bộ quy ước bản vẽ, hai tầng đánh giá, giới hạn tính U, việc đổi sang mô hình OpenAI.
- [ ] Chốt hạng mục mở rộng: nguồn cung cả công trình từ dự toán Excel, xuất hồ sơ.
- [ ] Sửa đề cương ở các chỗ ghi "miễn phí", "chạy cục bộ", "Qwen 4B".
- [ ] Tạo khóa API, xác nhận mã mô hình trên trang OpenAI, chạy `run_agent` với API thật, ghi chi phí mỗi lần chạy.
- [ ] Chạy `sql/03_materials.sql` trên database của máy.
- [ ] Tải Thông tư 38/2026/TT-BXD (định mức dự toán và phụ lục định mức sử dụng vật liệu).
- [ ] Bắt đầu tìm 7–10 bộ bản vẽ nhà ở riêng lẻ có đủ mặt bằng các tầng.
- [ ] Bắt đầu thu thập đại lý cho 16 vật liệu tường theo mẫu thu thập (mỗi vật liệu 3–5 đại lý).
- [ ] Tìm và đánh giá công bố giá của Sở Xây dựng Hà Nội và các tỉnh lân cận (vật liệu nào, từ năm nào, định dạng).
- [ ] Viết bộ 30–50 câu hỏi đánh giá agent có đáp án.

### Phần thô (17/10/2026, theo hướng nga chốt)

Bóc toàn bộ phần thô ra công tác và vật liệu mua về, chia 17 sprint nhỏ trong `SPRINTS.md`, nhật ký trong `NHAT_KY.md`.

- [x] S0–S7: chuỗi công tác → vật liệu, xây, trát, lanh tô, sàn, cán nền, nền, chống thấm, cột, dầm (suy), thang (nhập tay),
  cốp pha, cốt thép theo hàm lượng, móng nhập tay, gộp tầng, API, agent, kiểm soát định mức, tab "Phần thô".
- [ ] Tra TT 38/2026 điền `data/rules/dinh_muc_phan_tho.csv` (22 dòng đang trống) và hao hụt trong `materials_master.xlsx`.
- [ ] Thêm 4 mã còn thiếu vào danh mục (dây thép buộc, đinh, con kê, gỗ xẻ) khi nga đồng ý.
- [x] Đọc dầm từ bản vẽ kết cấu (S4b.5, 21/10; cả hình chi tiết móng, dầm).
- [ ] Nhận thang và đếm bậc tự động (S4c.1–2).
- Từ 21/10 làm theo lộ trình S01–S08 (bảng trong `SPRINTS.md`).
- [ ] Giảng viên duyệt: trừ dầm khỏi chiều cao tường, công thức thang, cốp pha sàn có trừ đáy dầm hay không.

## Tuần 3–4: Bản vẽ và dữ liệu (19/10–01/11)

Đây là hai tuần quyết định: mọi số liệu đo bóc phụ thuộc vào bộ bản vẽ này.

- [ ] Chuẩn hóa 5 mặt bằng nhóm build theo bộ quy ước; ghi lại từng thao tác sửa.
- [ ] Chuẩn hóa 20–30 mặt bằng nhóm test (7–10 căn nhà); giữ bản gốc trong `data/drawings/raw/`.
- [ ] Đo tay diện tích từng nhóm tường; đo hai lần độc lập, lệch dưới 2% mới nhận.
- [ ] Nhập đáp án vào `data/ground_truth/index.csv` và `walls.csv`.
- [ ] Giữ riêng 10–15 mặt bằng gốc chưa sửa cho tầng 2.
- [ ] Lấp định mức xây và hao hụt còn trống trong `data/catalog/materials_master.xlsx`, ghi nguồn; sinh lại SQL.
- [ ] Chốt với giảng viên: định mức cho gạch 2 lỗ, λ của gạch rỗng và gạch bê tông.
- [ ] Bắt đầu thu thập giá và nhà cung cấp cho 32 vật liệu ưu tiên (kéo dài tới tuần 7); nạp 123 tiêu chuẩn.

## Tuần 5: Module bản vẽ (02/11–08/11)

- [x] Sửa lỗi hụt chiều dài ở góc tường (`drawing/walls.py`, nối góc L tới giao trục tim).
- [x] Thêm lớp chiều dày 150.
- [ ] Viết bước kiểm tra bản vẽ theo bộ quy ước, trả danh sách vi phạm.
- [ ] Chạy `scripts/survey_drawings.py` trên nhóm build, bổ sung quy tắc. Không xem nhóm test.
- [x] Chiều cao tầng nhập riêng cho từng mặt bằng (tách mặt bằng, đọc cao độ; trang Kiểm tra bóc tách).

## Tuần 6: Đo bóc tầng 1, U và tối ưu (09/11–15/11)

- [ ] Chạy `scripts/evaluate_takeoff.py` trên nhóm test, một lần; ghi sai số theo từng bản vẽ và từng loại nhà.
- [ ] Tính U cho tường nhiều lớp; so R0 với tường mẫu Phụ lục 6 của QCVN 09:2017/BXD.
- [x] Một bộ mã vật liệu xuyên suốt: bóc tách, kiểm tra, tối ưu, tra giá đều theo `materials`/`wall_systems` (13/10).
- [x] Bảng vật liệu theo thiết kế: gạch + vữa theo định mức phương án, giá từ `supplier_materials`/`price_records` (`catalog/pricing.py`).
- [ ] Công cụ Data: cộng vật liệu đi kèm khác (`material_relations`: lưới, neo, keo); cấp phối vữa ra xi măng, cát.
- [ ] Mở rộng bảng `suppliers`, `supplier_materials`, `price_records` theo mục 9 tài liệu cơ sở dữ liệu; nạp đại lý đã thu thập.
- [x] Loại phương án thiếu thông số khỏi tối ưu, kèm lý do (`Catalog.wall_view().missing`).

## Tuần 7: Mô hình giá (16/11–22/11)

- [ ] Làm sạch giá theo cổng kiểm tra (đơn vị, thuế, ngày, trùng, ngoại lai).
- [ ] Thêm đặc trưng giá kỳ trước; huấn luyện XGBoost; chia theo thời gian 70/15/15.
- [ ] So với mốc "tra bảng giá gần nhất" và Ridge. Tập kiểm tra chỉ chạy một lần.

## Tuần 8: Agent và API (23/11–29/11)

- [x] Endpoint `/api/agent/run`; kết quả đo bóc đã xác nhận lưu vào `takeoff_results` khi gắn dự án.
- [ ] Ghi lần tối ưu (kèm công cụ đã gọi, ngày bảng giá) vào `optimization_runs`.
- [ ] Công cụ Compare: so vật liệu, phương án, đại lý trên cùng diện tích tường.
- [ ] Đăng nhập và hai vai trò.
- [ ] Bộ 30–50 câu yêu cầu tiếng Việt có đáp án; đo tỷ lệ trích đúng ràng buộc của mô hình so với regex, tỷ lệ câu trả lời bị chặn vì có số lạ.
- [ ] Ghi mã mô hình, ngày chạy, lưu toàn bộ câu trả lời.

## Tuần 9–10: Giao diện (30/11–13/12)

- [ ] Trang dự án, trang kết quả, trang quản trị theo mockup.
- [ ] Màn hình gán vai trò layer và hiển thị vi phạm quy ước.
- [ ] Bản đồ quãng đường tới nhà cung cấp (OSRM; dự phòng khoảng cách đường chim bay nhân hệ số).

## Tuần 11: Procurement và hạng mục mở rộng (14/12–20/12)

- [ ] Công cụ Procurement: bảng dự trù mua (cộng hao hụt, quy đổi đơn vị mua, vật liệu đi kèm, chia theo đại lý, số chuyến xe), xuất Excel và PDF.
- [ ] Liên kết chỉ đường Google Maps từ công trình tới đại lý.
- [ ] Nếu đã chốt: đọc khối lượng từ dự toán Excel, tối ưu nguồn cung cho cả 5 nhóm vật liệu.

## Tuần 12–13: Thực nghiệm (21/12–03/01)

- [ ] NSGA-II so với vét cạn và tổng có trọng số: hypervolume, thời gian chạy.
- [ ] Độ nhạy: giá tăng 10–20%, đổi vị trí công trường.
- [ ] Tầng 2: chạy trên 10–15 bản vẽ gốc, phân loại nguyên nhân lỗi.
- [ ] Nghiên cứu tình huống 2–3 căn nhà: so phương án đề xuất với thiết kế gốc.

## Tuần 14–15: Báo cáo và bảo vệ (04/01–17/01)

- [ ] Viết báo cáo; mỗi con số có nguồn và nhãn dữ liệu.
- [ ] Slide, video demo dự phòng cho trường hợp mất mạng.
- [ ] Sửa theo góp ý, nộp, tập bảo vệ.

## Thứ tự cắt giảm khi trễ

Cắt từ dưới lên; ba mục đầu không cắt.

1. Bộ test tầng 1 và module bản vẽ.
2. Mô hình giá với dữ liệu thật.
3. Tối ưu và U nhiều lớp.
4. Giao diện (có thể rút còn trang dự án và trang kết quả).
5. So sánh thuật toán và độ nhạy.
6. Nghiên cứu tình huống.
7. Tầng 2 trên bản vẽ gốc.
8. Hạng mục mở rộng tuần 11.

## PostgreSQL và DBeaver

DBeaver là công cụ xem và sửa dữ liệu; ứng dụng và DBeaver cùng nối tới một database.

Các lệnh dưới đây có sẵn trong `sql/00_create_database.sql`. Muốn tạo bảng bằng SQL thay cho
`init_db.py` thì chạy tiếp `sql/01_schema.sql` và `sql/02_seed_sample.sql` trong database `optimat`.

Tạo database (chạy trong SQL Editor của DBeaver, khi đang nối bằng tài khoản `postgres`):

```sql
CREATE USER optimat PASSWORD 'matkhau';
CREATE DATABASE optimat OWNER optimat ENCODING 'UTF8' TEMPLATE template0;
CREATE DATABASE optimat_test OWNER optimat ENCODING 'UTF8' TEMPLATE template0;
```

Thông số kết nối trong DBeaver (New Connection, chọn PostgreSQL):

| Trường | Giá trị |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| Database | `optimat` |
| Username | `optimat` |
| Password | mật khẩu đã đặt |

Cho ứng dụng dùng đúng database đó (PowerShell):

```powershell
$env:DATABASE_URL = "postgresql+psycopg://optimat:matkhau@localhost:5432/optimat"
python scripts/init_db.py --prices data/sample/prices_sample.csv
```

`optimat_test` chỉ dùng cho `pytest`, vì bài kiểm thử xóa và tạo lại toàn bộ bảng.

## Nhật ký tiến độ

| Tuần | Đã xong | Chưa xong | Ghi chú |
|---|---|---|---|
| 1 | | | |
