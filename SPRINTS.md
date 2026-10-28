# Sprint triển khai: bóc phần thô, đọc bản vẽ theo quy ước, cơ sở dữ liệu vật liệu

Mỗi sprint nhỏ, xong là chạy `pytest` và ghi một dòng vào `NHAT_KY.md`. Tiêu chí xong luôn gồm: pytest đạt, thiếu số thì
để trống kèm cảnh báo (Quy ước B7), không đổi lược đồ cơ sở dữ liệu nếu chưa hỏi nga.

Trạng thái: ✅ xong · 🔄 đang làm · ⬜ chưa làm

## Tổng quan

| Sprint | Mục tiêu | Việc cụ thể | Tiêu chí xong | Trạng thái |
|---|---|---|---|---|
| S0 | Nền sạch | Sửa bài test lỗi mã hóa trên Windows; tạo `NHAT_KY.md` | 64 bài đạt | ✅ |
| S1 | Chuỗi công tác → vật liệu | Gói `rough/`: thông số công trình B1, 14 công tác, `dinh_muc_phan_tho.csv`, cấp phối vữa từ `material_relations` | Gạch, xi măng, cát của tường W-GN01-220 đúng định mức; ô định mức trống báo "chưa tra" | ✅ |
| S2 | Xây, trát, lanh tô | `rough/walls.py`: trừ cửa, lanh tô, cột, dầm; trát 2 mặt, tường bao tách trong/ngoài | Test số học trên mặt bằng mẫu; chạy được trên 2 bản vẽ build | ✅ |
| S3a | Đường bao và phòng | `rough/areas.py`: tô tường lên lưới, đóng khe ở chỗ cột, tìm phòng; tên phòng theo `room_rules.csv` | Hộp mẫu sai số < 0,5%; nhận phòng WC | ✅ |
| S3b | Sàn, cán nền, nền, chống thấm | Sàn trừ ô trống, cán nền theo diện tích sử dụng, nền trệt theo lớp, chống thấm WC + cổ tường, ban công nhập tay | Test cho tầng trệt và tầng trên; đường bao hở thì báo và cho nhập tay diện tích | ✅ |
| S4a | Cột | Nhận cột trên mặt bằng (hatch đặc, ô chữ nhật nhỏ), tiết diện, chiều cao; m³, cốp pha; trừ cột trong tường | Test cột mẫu; đếm cột trên bản vẽ build | ✅ |
| S4b | Dầm | Đọc dầm từ bản vẽ kết cấu nếu có; không có thì suy theo tường và cột để người dùng duyệt; m³, cốp pha | Test dầm suy từ tường; cảnh báo khi phải suy | ✅ (21/10: đọc cả hình chi tiết móng, dầm) |
| S4c | Cầu thang | Vùng thang (đã loại khỏi tường), số bậc, bề rộng vế; m³ bản thang + bậc | Test thang mẫu | 🔄 còn nhận thang tự động |
| S4d | Cốp pha tổng | Cộng cốp pha lanh tô, cột, dầm, sàn, thang | Một dòng cốp pha mỗi cấu kiện, có công thức | ✅ |
| S5a | Cốt thép | Tấn thép = m³ bê tông × hàm lượng từng cấu kiện; dây buộc | Thiếu hàm lượng cấu kiện nào thì cấu kiện đó trống | ✅ |
| S5b | Móng, ca máy | Móng nhập tay (khối lượng hoặc kích thước); ca máy để trống chờ định mức | Móng nhập tay vào bảng vật liệu | ✅ |
| S6a | Gộp các tầng | `rough_takeoff(plans, params)`: nhận tầng trệt, cộng mọi mặt bằng ra một bảng | Chạy trên nhà dân, nhà phố | ✅ |
| S6b | API | `/api/takeoff/rough/auto`, `/api/takeoff/rough`; lưu trong JSON của `takeoff_results` | Test API | ✅ |
| S6c | Agent và kiểm soát dữ liệu | Công cụ phần thô cho agent, bước trong luồng cố định; `check_data` kiểm `dinh_muc_phan_tho.csv` | Agent chạy được khi tắt LLM | ✅ |
| S7a | Form thông số | Nhập thông số công trình và từng mặt bằng trên trang Kiểm tra bóc tách | Đổi thông số thì bảng tính lại | ✅ |
| S7b | Bảng phần thô | Bảng công tác + vật liệu mua về trên trang kiểm tra và `/app`, ô thiếu tô màu | Xem được trên 2 bản vẽ build | ✅ |
| S8 | Tài liệu | Cập nhật CLAUDE.md, PLAN.md, trạng thái trong `vat-lieu-phan-tho.md` | Tài liệu khớp mã | 🔄 còn file đặc tả ngoài kho mã |
| S9 | Đọc bản vẽ theo khái niệm của Quy ước v1.0 | `data/rules/quy_uoc.csv` (23 điều khoản QU), `data/rules/concepts.csv` (ký hiệu nhận dạng), kiểm tra quy ước (A4), gắn nguồn cho từng kết quả, trang quan sát định nghĩa và đối chiếu | Phân vai layer không đổi sau khi chuyển quy tắc sang CSV; mỗi điều khoản QU có kết quả đạt / vi phạm / chưa kiểm kèm bằng chứng; chạy được trên 3 bản vẽ build | ✅ |
| S10 | Cơ sở dữ liệu xác định vật liệu | Danh mục 93 vật liệu (thêm 18 vật liệu phần thô), bảng `material_notes`, `drawing_concepts`, `convention_clauses`, quy tắc so nguyên từ, file Excel đối chiếu | Nhận đúng vật liệu phần thô từ ghi chú bản vẽ; ≥ 90% đúng và 0 gán nhầm trên bản vẽ test | 🔄 chờ bản vẽ build, test |

## Lộ trình S01–S08 (từ 21/10/2026, mã yêu cầu `S02-01`…)

Đánh số hai chữ số, khác lộ trình S0–S10 ở trên (S04 ≠ S4). Đặc tả, review nằm trong `docs/`.

| Sprint | Nội dung | Tài liệu | Trạng thái |
|---|---|---|---|
| S01 | (chưa có ghi chép trong kho) | | ⬜ cần bổ sung |
| S02 | Tiếp nhận hồ sơ CAD: kiểm file, hash/phiên bản, DWG→DXF có log, inventory JSON, trang `/tiep-nhan` | `docs/review/S02_codex_review_prompt*.md` | 🔄 chờ Codex review vòng 2 |
| S03 | Hồ sơ chuẩn hóa: ComponentRegistry + EvidenceRef, mapping kiến trúc–kết cấu, trang `/mapping` | `docs/review/S03_codex_review_prompt.md` | ✅ |
| S04 | Tường + lỗ mở: `length_rule` tim/thông thủy, cửa trừ một lần | `docs/review/S04_codex_review_prompt.md` | ✅ đã sửa theo Codex review (21/10) |
| S05–S06 | Móng, đất, cột, dầm, sàn | `docs/boc-mong-cot-dam-san.md`, `docs/codex-review-S05-S06.md` | ✅ |
| S07–S08 | Cốt thép theo bảng thống kê, BOQ Excel, cấu kiện phụ | `docs/S07_S08_thep_BOQ_cau_kien_phu.md`, `docs/codex_review_S07_S08.md` | ✅ |

## Lộ trình Admin AD-01–AD-06 (từ 22/10/2026, 6 sprint × 2 tuần)

Kế hoạch quản trị OptiMat AI v2.0, mã yêu cầu `AD01-01`…; giao diện mẫu tham khảo `OptiMat_Admin_UI_Demo.html` (ngoài kho, số liệu minh họa).

| Sprint | Nội dung | Trạng thái |
|---|---|---|
| AD-01 | Nền tảng admin: menu nhóm + thu gọn, 403/404/lỗi, đăng nhập và phân quyền (`api/auth.py`), người dùng, dự án, tổng quan, phân trang, audit log (`api/admin_ops.py`; trang `/tong-quan`, `/nguoi-dung`, `/du-an`) | ✅ 23/10 (chưa có toast chung; API người dùng thường chưa bắt đăng nhập) |
| AD-02 | Hồ sơ CAD theo dự án và phiên bản, mapping layer, phiên bản hóa + kiểm thử quy tắc, đối tượng chưa khớp | ⬜ cần thêm bảng phiên bản quy tắc |
| AD-03 | Vật liệu, định mức (bản nháp → phát hành), BOQ theo dự án, duyệt và hiệu chỉnh tách khỏi kết quả gốc, xuất Excel | ⬜ trái với quyết định "danh mục chỉ sửa ở materials_master.xlsx": cần chốt lại |
| AD-04 | Nhà cung cấp, giá theo ngày/khu vực/nguồn, import CSV có kiểm tra, lịch sử giá | ⬜ (đã có CRUD `suppliers`, `supplier_materials`) |
| AD-05 | XGBoost (phiên bản, kích hoạt, rollback), cấu hình NSGA-II, giám sát và trace Agent, chi phí API | ⬜ cần ghi `optimization_runs`, chi phí LLM |
| AD-06 | Báo cáo, audit log có lọc, kiểm thử E2E, tài liệu, nghiệm thu | ⬜ |

## Việc còn mở

Mỗi bước làm xong trong một lần ngồi, có test riêng. Bước nào đụng tới lược đồ cơ sở dữ liệu thì dừng hỏi nga trước.

### S4b Dầm 🔄
- ✅ S4b.1 Mô hình `Beam` (trục, b, h, nguồn `ket_cau | suy | manual`, `keep`) và `beam_works`: m³, cốp pha đáy + 2 thành trừ dày sàn; test số học
- ✅ S4b.2 Suy dầm theo tường và cột: đoạn tường nối hai cột thành dầm chờ duyệt, tiết diện để trống kèm cảnh báo "dầm suy"
- ✅ S4b.3 Dầm tính tới mép cột (trừ phần giao cột–dầm)
- ✅ S4b.4 Nối cao dầm vào `wall_works`: trừ dầm khỏi khối xây, bỏ cảnh báo "chưa có cao dầm" khi đã có dầm
- ✅ S4b.5 Đọc dầm từ bản vẽ kết cấu: ký hiệu D…/ĐK… + cặp nét, tiết diện ghi chữ (`ĐK2 300X500`); test bản vẽ giả + ket_cau.dxf (21/10/2026); tiết diện dầm, kích thước móng từ hình chi tiết (`drawing/dimensions.py`)

### S4c Cầu thang 🔄
- ⬜ S4c.1 Lấy vùng thang đã loại khỏi tường lúc nhận dạng thành `StairRegion`
- 🔄 S4c.2 Đếm bậc theo nét song song, đo bề rộng vế (chưa); cho nhập tay số bậc, cao bậc, dày bản (xong)
- ✅ S4c.3 `stair_works`: m³ bản thang (dài nghiêng × rộng × dày), bậc (½ × rộng bậc × cao bậc × bề rộng vế × số bậc), chiếu nghỉ
- ✅ S4c.4 Test thang mẫu hai vế một chiếu nghỉ; thiếu số bậc thì trống kèm cảnh báo

### S8 Tài liệu
- ✅ S8.1 Cập nhật CLAUDE.md, PLAN.md theo mã
- ⬜ S8.2 Cập nhật trạng thái trong `vat-lieu-phan-tho.md` (thư mục dự án chung, ngoài kho mã)

### S10 Cơ sở dữ liệu xác định vật liệu (chốt 19/10/2026) 🔄

Mục tiêu: hệ thống nhận đúng vật liệu phần thô từ bản vẽ. Quyết định theo 10 câu hỏi định hình:

| # | Quyết định | Trạng thái |
|---|---|---|
| 1 | Tường nhận ở cấp **họ** vật liệu (bản vẽ hiếm ghi quy cách viên), quy ra mã qua `Catalog.resolve_wall`; bê tông, vữa, thép, chống thấm nhận thẳng **mã** (bản vẽ ghi mác, loại) | ✅ |
| 2 | 18 vật liệu phần thô còn thiếu vào danh mục chính thức (`materials_master.xlsx`, 75 → 93): TH09, TH10, LK01–03, BT06, PG01–02, VU05, CT04–06, PK04–05, CP03–06; thông số số chưa có nguồn để trống | ✅ |
| 3 | Quy tắc nhận dạng vào PostgreSQL: thêm bảng `material_notes`, `drawing_concepts`, `convention_clauses` (23 → 26 bảng); CSV vẫn là nguồn sửa bằng Excel, `init_db.py --reload-rules` / `sql/05_rules.sql` | ✅ chưa nạp thử vào PostgreSQL thật |
| 4 | Một ghi chú khớp nhiều vật liệu (xi măng bao → XM01, XM02): trả hết, người dùng chọn trên trang kiểm tra; không thêm cột ưu tiên | ✅ |
| 5 | Nhận loại gạch qua hatch (H02 AR-BRSTD, H03 AR-B816) là giả định, ngoài chỉ tiêu S10 cho tới khi có bản vẽ gốc AutoCAD | ✅ ghi trong `material_rules.csv` |
| 6 | Mẫu ghi chú có nguồn khi khớp ghi chú thật trên bản vẽ build (`kiem_chung = ban_ve_build`, hiện 8/206) hoặc được duyệt "Đồng ý" trong file Excel | ✅ |
| 7 | Chốt bộ quy tắc khi có ≥ 5 bản vẽ build từ nhiều nguồn + 2–3 bản vẽ test giữ riêng (hiện 2 kiến trúc + 1 kết cấu) | ⬜ chờ bản vẽ |
| 8 | Chỉ tiêu: trên bản vẽ test, ≥ 90% ghi chú vật liệu gán đúng và 0 dòng gán nhầm (sheet Tổng hợp, dòng "Chỉ tiêu S10") | ⬜ chờ bản vẽ test |
| 9 | S10 chỉ cần **nhận dạng đúng**; đủ số để tính khối lượng (hao hụt, định mức TT 38, khối lượng thể tích VU04) là sprint sau | ✅ |
| 10 | Quy tắc chữ, layer của `material_rules` so nguyên từ (hết khớp nhầm kiểu "thép trong", "ngói đồng"). Còn "TRẦN THẠCH CAO" khớp T14 vì "thạch cao" là từ trọn vẹn: cần quy tắc loại trừ trần, chưa làm | ✅ một phần |

## Lưu trữ: chi tiết các sprint đã xong

<details>
<summary>S4a, S4d, S5a, S5b, S6a–S6c, S7a, S7b, S9 (bấm để mở)</summary>

### S4a Cột ✅
- ✅ S4a.1 `detect_columns`: hatch SOLID tô lên lưới, gộp tam giác, lọc theo `COLUMN_SIDE_MM`, độ lấp đầy, tỉ lệ cạnh
- ✅ S4a.2 `column_works`: m³ và cốp pha theo nhóm tiết diện; thiếu dày sàn thì cảnh báo
- ✅ S4a.3 `column_overlaps` + trừ cột khỏi khối xây trong `wall_works`
- ✅ S4a.4 Cột nhập tay, bỏ cột (`source="manual"`, `keep=False`) qua `columns_from_dicts`; test giữ/bỏ
- ✅ S4a.5 Chạy trên 2 bản vẽ build, đếm cột, ghi số vào `test_rough_build_drawings.py` (bỏ qua khi không có file)

### S4d Cốp pha tổng ✅
- ✅ S4d.1 Cốp pha sàn (từ diện tích sàn S3b) và cốp pha thang
- ✅ S4d.2 `formwork_summary` (trường `formwork` của kết quả): mỗi cấu kiện một dòng có công thức; test không đếm trùng các dòng `COP_PHA` đã có

### S5a Cốt thép ✅
- ✅ S5a.1 Hàm lượng thép (kg/m³) từng cấu kiện: trường trong `ProjectParams`, mặc định trống
- ✅ S5a.2 `steel_works`: tấn thép = m³ × hàm lượng; thiếu hàm lượng cấu kiện nào thì cấu kiện đó trống
- ✅ S5a.3 Dây buộc theo định mức trên tấn thép (`dinh_muc_phan_tho.csv`)

### S5b Móng, ca máy ✅
- ✅ S5b.1 Móng nhập tay: khối lượng, hoặc dài × rộng × cao × số lượng; bê tông lót
- ✅ S5b.2 Đưa móng vào chuỗi vật liệu (bê tông, thép theo hàm lượng móng, cốp pha)
- ✅ S5b.3 Dòng ca máy để trống, cảnh báo "chờ định mức"

### S6a Gộp các tầng ✅
- ✅ S6a.1 Nhận tầng trệt (người dùng chọn; không thì theo cao độ thấp nhất, rồi theo tên mặt bằng)
- ✅ S6a.2 `compute_rough(RoughRequest)`: gọi tường, diện tích, cột, dầm, thang từng mặt bằng ra `RoughBill`
- ✅ S6a.3 Cộng vật liệu các tầng, giữ dòng theo tầng để truy vết
- ✅ S6a.4 Chạy trên nhà dân, nhà phố

### S6b API ✅
- ✅ S6b.1 Lược đồ yêu cầu/trả về (pydantic)
- ✅ S6b.2 `POST /api/takeoff/rough/auto` và `POST /api/takeoff/rough`
- ✅ S6b.3 Lưu trong JSON có sẵn của `takeoff_results` (`kind = rough`), không đổi lược đồ. Phần thô là endpoint riêng vì cần mọi mặt bằng + thông số; `/api/takeoff/confirm` của tường giữ nguyên
- ✅ S6b.4 Test API

### S6c Agent và kiểm soát dữ liệu ✅
- ✅ S6c.1 Công cụ phần thô cho agent (`boc_phan_tho`)
- ✅ S6c.2 Bước phần thô trong luồng cố định (chạy khi tắt LLM, chỉ khi người dùng gửi thông số công trình)
- ✅ S6c.3 `check_data` kiểm `dinh_muc_phan_tho.csv`: mã công tác, đơn vị, liệt kê ô còn trống
- ✅ S6c.4 Test agent tắt LLM

### S7a Form thông số ✅
- ✅ S7a.1 Form thông số công trình (B1) trên trang Kiểm tra bóc tách
- ✅ S7a.2 Thông số từng mặt bằng: chiều cao tầng, tầng trệt, nhập tay diện tích khi đường bao hở
- ✅ S7a.3 Đổi thông số thì gọi lại API, bảng tính lại

### S7b Bảng phần thô ✅
- ✅ S7b.1 Bảng công tác: tầng, cấu kiện, công thức, khối lượng
- ✅ S7b.2 Bảng vật liệu mua về; ô thiếu tô màu, rê chuột xem cảnh báo
- ✅ S7b.3 Đưa hai bảng lên `/app`
- ✅ S7b.4 Xem trên 2 bản vẽ build (nhà dân, nhà phố; nhà phố có hai tiêu đề "tầng 3" trùng tên, đã tách)

### S9 Đọc bản vẽ theo khái niệm (Quy ước bản vẽ v1.0) ✅
Hướng đã chốt (17/10/2026): nhận theo ký hiệu của quy ước trước (độ tin cậy cao), không khớp mới đoán bằng hình học (gắn nhãn "đoán",
người dùng duyệt). Không dùng mô hình ngôn ngữ để nhận dạng.
- ✅ S9.1 `data/rules/quy_uoc.csv`: 23 điều khoản QU-01…QU-23 (nhóm, nội dung, mức B/K, cách kiểm) chép từ Quy ước v1.0
- ✅ S9.2 `data/rules/concepts.csv`: ký hiệu nhận dạng (tên layer, tiền tố block cửa + kích thước mặc định) chuyển ra khỏi mã
  (`layer_classifier._DEFAULT_RULES`, `config.OPENING_BLOCK_PREFIXES`); phân vai 122 layer và nhận dạng tường, cửa trên 3 bản vẽ build giống hệt HEAD.
  Kích thước cửa mặc định đã bỏ (phiên "Đợt 3": lấy từ block, quy tắc block hoặc thông số cửa của dự án). Nạp vào PostgreSQL:
  bảng `drawing_concepts`, `convention_clauses` (S10)
- ✅ S9.3 QU-05: hai tiêu đề mặt bằng trùng tên thì đánh số thêm ngay trong `find_plans` và báo vi phạm (sửa lỗi audit: xác nhận
  tầng trùng tên ghi đè tầng kia ở trang kiểm tra, `/app`, file đáp án)
- ✅ S9.4 `drawing/convention_check.py` `analyze`: mỗi điều khoản trả đạt / vi phạm / chưa kiểm + bằng chứng; bản vẽ có vi phạm
  mức B thì "ngoài quy ước" (A4)
- ✅ S9.5 Nguồn từng kết quả: tường, cửa, cột gắn nguồn `quy_uoc` (khớp ký hiệu, ghi mã QU) hoặc `hinh_hoc` (đoán) và mức tin cậy B4
- ✅ S9.6 Trang quan sát `scripts/concept_report.py <bản vẽ>` → `<tên>.khai_niem.html`: định nghĩa đặt cạnh kết quả đối chiếu,
  ký hiệu đã khớp, sơ đồ tường tô theo nguồn, so với đáp án đo tay khi có
- ✅ S9.7 Chạy trên nhà dân, nhà phố, kết cấu; ghi nhật ký
- ✅ S9.8 Đưa danh sách vi phạm QU lên tab Cảnh báo của trang kiểm tra (sau khi nga duyệt trang quan sát)

</details>
