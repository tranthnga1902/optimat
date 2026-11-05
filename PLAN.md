# Kế hoạch chi tiết OptiMat AI

**Quyết định ngày 04/11/2026:** đúng [20 bảng vật lý](docs/schema/CSDL_20_BANG.md); [kế hoạch dữ liệu sáu tuần](docs/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md). Các số bảng trong mốc lịch sử không mở lại phạm vi schema.

**Ưu tiên mới theo chủ đồ án:** hoàn thiện sớm luồng lõi, sát thực tế, chỉn chu và không bịa số.
Thứ tự triển khai tại [kế hoạch ưu tiên](docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md);
owner/ID tại [danh bạ phiên](docs/PHAN_VAI_CAC_PHIEN.md). Các mục lịch cũ bên dưới không tự mở rộng phạm vi.

## Điều chỉnh luồng nghiệp vụ 03/11/2026: kiểm khối lượng trước vật liệu

Phân vai mới: chat kế hoạch chỉ cố vấn và điều phối yêu cầu; các phiên phụ trách triển khai theo
[phiếu điều chỉnh và bàn giao WIP](docs/DIEU_CHINH_LUONG_KIEM_KHOI_LUONG_20261103.md).

Luồng ưu tiên mới: **Dự án → Bóc tách bản vẽ → Kiểm tra công tác và khối lượng → Nhận phương án vật liệu tại Tối ưu → So sánh với AI → Áp dụng phương án / xuất bảng mua**. Người dùng có thể chỉnh vật liệu và xem giá chi tiết khi cần. Tính sẵn các dòng có căn cứ và mang phần thiếu sang bước phương án theo [quy tắc tự đề xuất](docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md).
Bước kiểm công tác là điều kiện MVP, thực hiện trước các đầu việc chọn vật liệu và so giá. Dùng lại `/phan-tho`
cho bước này, đặt trước `/dieu-chinh`; không tạo bộ máy tính khối lượng thứ hai.
Đặc tả giao diện, phụ thuộc và nghiệm thu: [Kiểm tra công tác và khối lượng](docs/KIEM_TRA_CONG_TAC_KHOI_LUONG.md).
Đây là điều chỉnh kế hoạch, chưa xác nhận giao diện đã triển khai. Các lịch/luồng cũ bên dưới đọc theo điều chỉnh này.

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

## MVP (chốt 02/11/2026, hạn demo 22/11/2026)

**Phạm vi (người dùng chốt 03/11/2026): chỉ phần thô xây dựng.** Bản vẽ đầu vào là kiến trúc + kết cấu; không làm điện
nước, biện pháp thi công, hoàn thiện.

**Một câu:** người dùng mở 1 bộ bản vẽ thật (kiến trúc + kết cấu) trên web → bóc phần thô (tường, cột, dầm, sàn, móng,
thang, thép, cốp pha), sửa, xác nhận → bảng vật liệu thô có giá thật → NSGA-II trả 3–5 phương án tường (chi phí, thời gian
cung ứng, U) kèm đại lý từ database → lời giải thích.

**Xong** = chạy trọn luồng trên `/do-boc` → `/toi-uu` với PostgreSQL và dữ liệu `ACTUAL`, quay video lại. pytest đạt là
điều kiện cần, không phải tiêu chí xong.

**Đóng băng đến khi MVP xong:** quản trị AD-02..06, `/tiep-nhan`, `/mapping`, công bố giá. Phần thô chỉ sửa lỗi và đo
sai số với dự toán thật, không thêm cấu kiện mới. Mã đã có giữ nguyên, chỉ sửa khi chặn luồng MVP.

### Dữ liệu (người dùng làm, không viết mã thay được)

- [ ] Giảng viên duyệt phạm vi MVP ở trên (gửi kèm danh sách đóng băng).
- [ ] Chọn 3–4 phương án tường cho MVP (ví dụ W-GN01-110, W-GN01-220, 1 AAC, 1 gạch bê tông); điền đủ định mức, khối lượng
      tường, λ, hao hụt trong `materials_master.xlsx`, có nguồn; sinh lại SQL. Kiểm: `GET /api/catalog/wall-materials` → các
      phương án này nằm trong `ready`.
- [ ] Giá thật cho mọi vật liệu của các phương án trên (gạch + xi măng + cát + vữa AAC nếu có): mỗi vật liệu ≥ 3 đại lý
      có tọa độ và `lead_time_days`, nạp `supplier_materials` (`ACTUAL`).
- [ ] Ít nhất 6 tháng giá theo thời gian (công bố giá Sở XD hoặc đại lý) cho các vật liệu trên, để XGBoost huấn luyện
      và so với mốc "tra bảng giá gần nhất".
- [ ] Đo tay tường của 5 mặt bằng thật (2 lần, lệch < 2%), nhập `data/ground_truth/` (3 build, 2 test).
- [ ] `labor_rates` thật cho Hà Nội (hoặc ghi rõ MVP không tính nhân công).

### Mã (chỉ những việc chặn luồng)

- [ ] Chạy luồng bằng tay trên `nha_pho.dxf`, ghi mọi chỗ gãy vào mục "Lỗi chặn MVP" bên dưới; chỉ sửa các lỗi đó.
- [ ] Nhận tường trên 3 mặt bằng build đủ dùng: sai số diện tích tường < 10% so với đáp án đo tay (`evaluate_takeoff.py`).
- [ ] Huấn luyện XGBoost `--from-db` trên giá `ACTUAL`; ghi bảng so sánh với mốc tra bảng (được phép thua mốc, ghi rõ).
- [ ] Tối ưu dùng giá thật, không cần `OPTIMAT_CATALOG_OVERLAY`; ghi lần chạy vào `optimization_runs`.
- [ ] Agent chạy được khi `LLM_PROVIDER=none`; chạy thử 1 lần với khóa OpenAI thật, ghi mã mô hình và chi phí.
- [ ] Chạy 2 mặt bằng test một lần, ghi sai số vào `NHAT_KY.md`.

### Demo

- [ ] Kịch bản demo 5 phút, video dự phòng khi mất mạng.

### Lỗi chặn MVP

(ghi khi chạy luồng bằng tay: bước, lỗi, đã sửa chưa)

Chạy 03/11/2026 qua API (PostgreSQL thật, `nha_pho.dxf`, cao tầng 3300, agent `use_llm=false`):

| # | Bước | Kết quả | Loại | Trạng thái |
|---|---|---|---|---|
| 1 | Đo bóc (`/api/takeoff/plans`, 28 s) | 4 mặt bằng, 9 nhóm tường. Không nhóm nào nhận được vật liệu từ bản vẽ (hatch bị phá, chỉ biết "khối xây") → người dùng phải chọn phương án trên `/do-boc` | Dự kiến | — |
| 2 | Tách mặt bằng | "mặt bằng tầng 3 (+6.60)" xuất hiện 2 lần (bản thứ 2 có hậu tố "(2)"): cần xem là trùng hay là tầng 4/mái đặt sai tiêu đề | Mã | ⬜ |
| 3 | Nhóm tường lạ | Có nhóm 330 (3,3 m²) và 150 trên nhà phố, chưa có phương án nào cho hai lớp này → dòng trống trong bảng vật liệu | Mã + dữ liệu | ⬜ |
| 4 | Bảng vật liệu (đã chọn W-GN01-110/220) | Ra số lượng gạch GN01 và vữa VU02, nhưng **không có giá** và thiếu hao hụt | Dữ liệu | ⬜ |
| 5 | Tối ưu (`/api/optimize`) | **422 "Không có loại xe nào thỏa tải trọng"**: bảng `vehicles` = 0 dòng. Luồng dừng tại đây, agent cũng báo "không có phương án" | Dữ liệu | ⬜ chặn |
| 6 | Dữ liệu trong DB | `supplier_materials` 0, `vehicles` 0, `labor_rates` 0, `price_records` 59 dòng ACTUAL cho 26 mã (không có GN01, VU02), `projects` 0. 5 phương án `ready`: W-GN01-110/220, W-GN03-105/150, W-GK01-110 | Dữ liệu | ⬜ |

Chưa chạy trên giao diện `/do-boc` → `/toi-uu`: API dừng ở bước 5 nên giao diện cũng không đi qua được.

03/11/2026: `sql/optimat_day_du.sql` (pg_dump database thật + khối SỐ MẪU xe, nhân công, 3 đại lý, giá gạch) nạp vào
database trống chạy được; tối ưu qua được bước 5 và trả phương án khi chỉ có nhóm 110/220 (số MẪU, không báo cáo). Lỗi mới:

| # | Bước | Kết quả | Loại | Trạng thái |
|---|---|---|---|---|
| 7 | Tối ưu cả nhà | Một nhóm tường không có phương án (330) làm **cả lần tối ưu trả 422**, thay vì bỏ nhóm đó và ghi vào notes | Mã | ✅ 03/11: bỏ nhóm + ghi chú "tổng chi phí chưa gồm nhóm này" (`optimize/problem.py`, test `test_group_without_option_is_skipped`) |
| 8 | Kết quả tối ưu | `lead_time_days` trống trong phương án dù đại lý MẪU có `lead_time_days` | — | ✅ không phải lỗi: trường tên `supply_days` (3–4 ngày) |
| 9 | Agent (`/api/agent/run`, `use_llm=false`) | Chạy hết luồng, nhưng tổng **233,3 triệu** so với **83,9 triệu** khi tối ưu theo từng mặt bằng (`/api/takeoff/plans`); tường 110 cần 8–12 chuyến xe 8 tấn. Nghi agent đo cả file như một mặt bằng (đếm trùng các tầng/hình chi tiết) | Mã | ✅ 03/11: đúng nguyên nhân (cả file 1.163 m², từng mặt bằng 320 m²); agent dùng `takeoff_building_from_file` (gộp từng mặt bằng), nay ra 83,9 triệu |
| 11 | Agent trên 16 bản vẽ (`data/drawings`, cả DWG) | Một tầng vẽ nhiều hình (kích thước, kí hiệu cửa, vật dụng, bản chép "(2)") bị cộng nhiều lần; file điện không tách được mặt bằng bị đo cả file (3.300 m² tường) | Mã | ✅ 03/11: `merge_plans` giữ 1 hình mỗi tầng (nhiều tường nhất, có cảnh báo); file nhiều hình mà không tách được mặt bằng thì không đo cả file |
| 12 | Bộ 46 Tân Bình so dự toán | Tường 10 cm: 823 m² so với ~1.034 m² (103,4 m³ / 0,1) = 80%; tường 20 cm: 412 so với ~450 m² (90,1 m³ / 0,2) = 91%. Trước sửa #11: 130% và 128% | Đo | ⬜ còn thiếu ~20% tường 110 |
| 13 | banve1 (nhóm test, cả DXF và DWG) | Tách được mặt bằng nhưng **không nhận được tường nào** trên mọi mặt bằng. Không chỉnh quy tắc trên nhóm test: cần bản vẽ build cùng kiểu trình bày (S13g) | Dữ liệu | ⬜ chặn |
| 14 | nha_pho | Sau #11, "mặt bằng tầng 3 (+6.60) (2)" bị coi là bản chép của tầng 3 và bỏ (tổng 320 → 269 m²). Cần mở bản vẽ xem đó là tầng 4/tum ghi sai tiêu đề hay bản chép thật | Dữ liệu | ⬜ |
| 15 | Bản vẽ không phải kiến trúc | `Dien nuoc.dwg` vẫn đo ra 176 m² (mặt bằng điện nước dùng nền kiến trúc), `BIEN PHAP THI CONG.dwg` 1.305 m²: agent nên chỉ nhận file kiến trúc (`drawing/sheets.py` đã nhận loại bản vẽ) | — | ➖ ngoài phạm vi: điện nước, biện pháp thi công đã bỏ (03/11), người dùng chỉ đưa bản vẽ kiến trúc |
| 16 | Phần thô bộ 46 so dự toán (03/11, `compare_estimate.py` + `46_thong_so.json`) | Lệch: lót −8%, móng −12%, cột +9%, dầm −19%, sàn −11%, cốp pha móng 0% / cột −5% / dầm −32% / sàn −35%, thép móng 0% / cột +27% / dầm −33% / sàn +11%, xây −18%, trát −28%. **Chưa có:** đào đắp đất, cầu thang, lanh tô (D) | Đo | ⬜ |
| 17 | Agent | Chỉ bóc phần thô khi gửi `rough_params`; không gửi thì agent chỉ đo tường | Mã | ✅ 03/11: luôn bóc phần thô (thiếu thông số thì để trống, B7); `/api/agent/run` nhận `structural_file`. Bộ 46 không thông số: 12 công tác, có số xây, trát, cột, cán nền; dầm, sàn, móng, thép trống chờ thông số |
| 18 | Trang `/do-boc` | Phần thô trên web không dùng bản vẽ kết cấu (dầm suy, móng không có); chưa có ô cốt đất, mở rộng hố, taluy | Mã | ✅ 03/11: nút "Mở bản vẽ kết cấu…" (`/api/takeoff/structural`), nhóm "Móng, đào đất". Bộ 46: dầm 15,3 → 30,2 m³, cột 10,5 → 18,6 m³. Chưa thử bằng tay trên trình duyệt (cần đăng nhập) |
| 19 | Giá vật liệu phần thô | Bảng vật liệu phần thô không có giá | Mã | ✅ 03/11: đơn giá thấp nhất cùng đơn vị + thành tiền (`attach_prices`). Bộ 46 có giá công bố XM01, XM02, CA01, DA01; thiếu giá CA02, TH10, thép (chưa chia đường kính), gạch (chưa chọn phương án) |
| 20 | Cầu thang | Chỉ nhập tay theo từng mặt bằng (số bậc, rộng vế...); chưa tự nhận trên bản vẽ (S4c) | Mã | ✅ 03/11: `rough/stairs.detect_stairs` + `building_stairs` (nét mũi bậc; tầng vẽ dở lấy thang đủ nhất trong nhà; bỏ sân thượng); trang `/do-boc` điền sẵn ô thang (B). Bộ 46: bê tông thang 5,59 / 5,85 m³ (−4%), thép +4%, cốp pha −23% |
| 21 | Cầu thang nhà phố, nhà dân | Chỉ nhận 7–8 bậc/tầng (một vế; vế kia có thể là bậc rẻ quạt hoặc vẽ khác): có cảnh báo cao bậc > 220 mm, chưa sửa | Mã | ⬜ |
| 10 | Kết quả agent | Mỗi tầng là một nhóm riêng nên câu trả lời lặp "Tường 110" nhiều dòng và số chuyến xe tính riêng từng tầng (chưa gộp chuyến) | Mã | ⬜ |

03/11/2026, database `optimat` đã nạp `optimat_day_du.sql`: tối ưu cả nhà phố trả 2 phương án (NSGA-II, nhóm 330 và 150 bị bỏ kèm ghi chú). Luồng API chạy hết bằng số MẪU.

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
