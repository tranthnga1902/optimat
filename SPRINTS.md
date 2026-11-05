# Sprint triển khai: bóc phần thô, đọc bản vẽ theo quy ước, cơ sở dữ liệu vật liệu

Hiện hành chốt [20 bảng vật lý](docs/schema/CSDL_20_BANG.md). Các mục đã hoàn thành phía dưới là lịch sử; kế hoạch dữ liệu mới ở [đây](docs/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md).

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
| S3b | Sàn, cán nền, nền, chống thấm | Sàn trừ ô trống, cán nền theo diện tích sử dụng, nền trệt theo lớp, chống thấm WC + cổ tường, ban công nhập tay | Test cho tầng trệt và tầng trên; đường bao hở thì báo và cho nhập tay diện tích | ✅ (28/10: hở thì khép theo bao lồi tường bao + cảnh báo kiểm tra, nhập tay vẫn thắng) |
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
| S12 | Trạng thái A/B/C/D và đầu ra cho bộ tối ưu (đặc tả 30/10) | `rough/status.py` gán `status`, `inputs`, `stage` cho công tác; vật liệu kế thừa xấu nhất; `dinh_muc_phan_tho.csv` thêm mức xác nhận / khoảng / ngày tra (cấp phối M250 từ cem.gov.vn, C); `MaterialLine.group_id`, `weight_kg`; `RoughResult.by_group` (5 nhóm, ngoài phạm vi vẫn liệt kê), `envelope_by_orientation` (`north_deg`); `min_opening_m2`; `rough/checks.py` + `khoang_hop_ly.csv`; BOQ thêm cột trạng thái, giai đoạn, sheet Theo nhóm | Nhà mẫu đủ 4 trạng thái; hệ số tham khảo → C + cảnh báo; check_data 0 lỗi; pytest đạt | ✅ 30/10 (không đổi lược đồ DB; không XGBoost phân loại; mẫu công tác giữ trong mã — ba điểm lệch đặc tả đã chốt) |
| S11 | Đọc vật liệu chính xác và nhanh hơn | Hatch bị phá dựng lại thành vùng đoán (`HatchItem.synthetic`, nguồn `hatch_doan`); từ viết tắt `viet_tat.csv`; ghép ghi chú nhiều dòng (`text_blocks.py`); cache quy tắc gộp theo danh mục + quy đổi phương án tường một lần mỗi cặp (họ, lớp dày); `batch_takeoff --jobs`; `benchmark_material_rules.py` | Tường có hatch bị phá có căn cứ H01; "gạch kg nung" khớp T07; ghi chú 2 dòng khớp T01; `apply_material_rules` 400 tường 2,2 s → 0,13 s; pytest đạt, check_data 0 lỗi | ✅ 30/10 (A1–A3, B1–B3; A4 báo cáo `unmatched` theo mẫu chưa làm) |

## Lộ trình DT01–DT07 – dự toán, tổng hợp, định mức – đơn giá, sai lệch (từ 05/11/2026, ưu tiên cao nhất)

Trọng tâm đề tài người dùng chốt 05/11/2026; luồng chính và tiêu chí chi tiết: [docs/LUONG_DU_TOAN_SAI_LECH.md](docs/LUONG_DU_TOAN_SAI_LECH.md).
Đã có (05/11): `rough/estimate_reader.py` (đọc thẳng file dự toán), `rough/estimate_check.py` (4 kiểm tra), `POST /api/estimate/check`, trang `/kiem-tra-sai-lech`.

| Sprint | Mục tiêu | Phụ thuộc | Tiêu chí xong | Trạng thái |
|---|---|---|---|---|
| DT01 | Một bộ đọc + một bộ gắn mã (`cong_tac_du_toan.csv`, gộp với KD07); quy cách từ tên (mác, phương án tường, dày trát) qua CSV; chốt XM02/XM03 | — | Bộ 46, banve1 có định mức xi măng, cát, đá, gạch, vữa | ⬜ |
| DT02 | Cổng duyệt gắn mã trên trang, lưu theo hash file, đề xuất quy tắc qua KD06 | DT01 | Sửa mã → kết quả đổi; mở lại giữ bản duyệt | ⬜ |
| DT03 | Tổng hợp khối lượng dự toán theo hạng mục × quy cách; tỷ lệ hợp lý; mức phát hiện + ngưỡng từng loại | DT01 | Tab tổng hợp + sheet Excel; test gộp | ⬜ |
| DT04 | Đo độ chính xác phát hiện: cài lỗi có kiểm soát, precision/recall theo loại | DT01 | `reports/estimate_check/` có bảng số | ⬜ |
| DT05 | Giá tham chiếu theo ngày + tỉnh lập dự toán: tra bảng gần nhất và XGBoost có khoảng | dữ liệu giá nhiều kỳ | Bộ 46 so với giá 2016; bảng XGBoost vs tra bảng | ⏸ |
| DT06 | NSGA-II cho vật liệu thô (bê tông, thép, xi măng, cát, đá, gạch) từ dự toán đã duyệt | DT01, DT05 | Bộ 46 ra phương án khả thi; vét cạn khớp bài nhỏ | ⬜ |
| DT07 | Lưu kết quả theo dự án, lịch sử, so hai phiên bản dự toán | DT02 | Lịch sử trên trang dự án; test so phiên bản | ⬜ |

Thứ tự: DT01 → DT02 + DT03 → DT04 → DT05 → DT06 → DT07.

## Lộ trình S13 – hoàn thiện phần thô so với mục tiêu ban đầu (từ 02/11/2026)

**Kế hoạch giao Claude theo sprint nhỏ (03/11/2026):** [BA, backlog, dữ liệu và nghiệm thu](docs/KE_HOACH_NGHIEM_THU_PHAN_THO.md).
Codex làm BA/reviewer chính, Claude triển khai từng đầu việc; hoàn tất dev ghi “chờ review”, chỉ đánh ✅ khi review đạt.
Các mã nhỏ trong tài liệu ánh xạ về S13 bên dưới, không phải triển khai lặp. Khi giao việc, dùng tiêu chí chi tiết trong tài liệu mới:
không tự suy diện tích lỗ thang từ rộng vế/chiếu nghỉ; tổng nhóm chỉ so cùng đại lượng/đơn vị; thiếu giá không tính vào tỷ lệ có giá.
Mục tiêu 95% là các chỉ tiêu hoàn tất nghiệp vụ trên tập hồ sơ đã chốt, không phải 95% tự động hoặc độ chính xác đã chứng minh.

Ước lượng chức năng ~85–90% và bằng chứng độ chính xác ~20–30% ở lượt đối chiếu đặc tả 30/10 chỉ là nhận định lịch sử, không phải số đo tiến độ hoặc chỉ tiêu nghiệm thu hiện tại. Trạng thái mới theo [kế hoạch nghiệm thu](docs/KE_HOACH_NGHIEM_THU_PHAN_THO.md) và [hồi quy tích hợp](docs/review/NGHIEM_THU_KY_THUAT_TICH_HOP_0511.md).
Viết lại chi tiết 03/11/2026 sau khi rà `src/optimat/rough/` và `data/rules/ho_tro_cau_kien.csv`.

**Cách kiểm soát một sprint**: chỉ đánh ✅ khi có đủ 4 bằng chứng — (1) tên bài test mới trong `tests/` chạy đạt,
(2) `pytest` toàn bộ đạt (ghi số bài), (3) `python scripts/check_data.py` 0 lỗi nếu đụng `data/`, (4) một dòng `NHAT_KY.md`
ghi file đã sửa. Sprint đổi khả năng nhận cấu kiện thì sửa luôn dòng tương ứng trong `ho_tro_cau_kien.csv`.
Ký hiệu thêm: 🔍 mã đã có, chưa đủ bằng chứng · ⏸ chờ dữ liệu người dùng · ❓ chờ quyết định.

### Sắp lại theo Codex review (03/11/2026)

Kết luận review (`docs/review/S13_codex_review_prompt.md`): luồng bản vẽ → công tác → vật liệu → nhóm đã chạy; ưu tiên là
**làm đúng và minh bạch phần đã bóc được**, rồi mới tăng tự động hóa. Không viết lại luồng, không mở nhiều cấu kiện cùng lúc.
Đã kiểm lại trên mã: 3 bài xfail (strict) đúng là 3 lỗi Codex nêu; trang chỉ giữ thang đầu tiên (`model.ts` `st0`); thang auto
gắn B không xét dày bản (C) (`status.py:103`); hao hụt tính "tất cả hoặc không" theo dòng (`materials.py:268`).

| Bước | Sprint | Mục tiêu | Tiêu chí xong | Trạng thái |
|---|---|---|---|---|
| 1 Sửa lỗi đã biết | S13n | N01 số trong bảng; N02 bảng lặp; N03 giằng chồng có cao độ | N01/N02/N03 đạt kỹ thuật đúng phạm vi | ✅ N03 review2/probe và full824passed16skip0fail0xfail exit0,225hash ổn; [biên bản](docs/review/NGHIEM_THU_BACKEND_20261103_RETRY1.md), chưa đáp án thực/DB/O01 |
| | S13a | Hao hụt theo **từng phần góp**: phần từ định mức có mã không cộng, phần không mã cộng `waste_pct` (thiếu thì báo chỉ phần đó) | Test dòng XM02 góp từ bê tông TT 38 + nguồn không mã: `quantity_with_waste` = phần có mã + phần không mã × (1 + %) | ✅ A01 đạt kỹ thuật 03/11/2026, hồi quy 501 passed, 15 skipped, 1 xfailed; không xác nhận đáp án vật tư thực |
| 2 Chống tính trùng | S13o | Thang ↔ sàn (lỗ thang trừ khỏi sàn khi chưa nhập ô trống), mái ↔ sàn tầng trên, dầm ↔ cột ↔ cốp pha (trừ đáy sàn gắn đúng từng sàn), chọn nguồn dầm theo **từng tầng** (kết cấu / nhập tay / suy) thay vì tắt suy toàn nhà | Mỗi cặp một test; tầng thiếu bản vẽ kết cấu vẫn suy dầm | ⬜ |
| | S13b | Cốp pha DAM/MONG/CAU_THANG, unknown, âm và None | Kiểm riêng và hồi quy tích hợp | ✅ B01 đạt kỹ thuật03/11/2026; không duyệt định mức mới |
| 3 Đồng bộ đầu ra | S13p | API → trang /do-boc → BOQ → tổng nhóm/loại khớp nhau sau lọc loại, trừ, hao hụt; trang hiển thị bảng theo nhóm như BOQ; trang giữ **nhiều thang** | Test tổng nhóm = tổng dòng; kiểm trang thật (gộp S13e) có ảnh chụp | ⬜ |
| 4 Trạng thái minh bạch | S13q | Trạng thái thang và phần đã biết/phần thiếu | Backend giữ missing/D và đầu ra HTTP nhất quán | 🔄 Q01/Q02 backend đạt kỹ thuật; P01/P02 giao diện chưa nghiệm thu toàn luồng |
| 5 Chốt phạm vi | S13m | Ma trận `ho_tro_cau_kien.csv` khớp mã (thang tự nhận, móng băng nhập tay…); chốt bể ngầm/bể phốt, vách BTCT, ô văng, chống thấm mái, bậc xây vs bậc bê tông: hỗ trợ hay ngoài phạm vi, **ghi rõ trên BOQ, không biến mất âm thầm** | Ma trận được nga duyệt; BOQ có mục "chưa bóc" | ❓ |
| | S13j | Định mức: giữ trống CAN_NEN 50, ván ép tới khi có căn cứ; lót móng / lót nền **chọn cấu tạo theo thông số**, không mặc định đá 4×6; phụ gia M350/M400; cấp phối / cách cung cấp bê tông theo cấu kiện (móng thương phẩm, lanh tô trộn tay) | Mỗi việc một test; check_data 0 lỗi; đổi `ProjectParams` thì báo trước | ⬜ |
| 6 Tăng tự động | S13i | Thang: tầng vẽ dở, nhiều thang, tum, sân thượng | Test từng trường hợp; ma trận → conditional | 🔄 phiên khác (phần nối mã) |
| | S13k | Giằng kết cấu gắn tầng + căn tọa độ KT–KC, trừ khối xây | Test trừ đúng, không trùng giằng nhập tay | ⬜ |
| | S13l | Mái: diện tích + dày từ bản vẽ mái | Test mặt bằng mái giả; nhập tay thắng | ⬜ |
| Kiểm chứng | S13d, S13c | Dầm bộ 46 lệch ~30%; báo cáo sai số cấu kiện × trạng thái (bộ 46 là build, không làm số báo cáo) | Như chi tiết dưới | ⬜ |
| | S13f, S13g, S13h | Đáp án bóc tay, 20–30 bản vẽ build/test, thép theo Ø (cả dây buộc theo Ø) | — | ⏸ |

Thứ tự: S13n → S13a → S13o → S13b → S13p → S13q → S13m → S13j → S13i → S13k → S13l; S13d, S13c xen khi rảnh; S13f/g/h khi có dữ liệu.
S13e gộp vào S13p.

### Chi tiết

**S13n Sửa 3 lỗi xfail** ⬜ (Codex review, bước 1)
- `tests/test_rough_secondary.py:70` hai giằng cùng đoạn trừ khối xây hai lần → `secondary.deduct_ties`: gộp khoảng chồng theo tường trước khi trừ.
- `tests/test_rough_rebar.py:47` ô số "1.234,5" / "1,234.5" đọc thành None → `rebar._num`.
- `tests/test_rough_rebar.py:52` bảng thép lặp không số hiệu cộng hai lần → `rebar.read_rebar_schedules`: khử bảng trùng nội dung.
- Xong khi: bỏ ba dấu `xfail`, pytest đạt (hiện 333 đạt, 3 xfail → 336 đạt).

**S13a Hao hụt theo từng phần góp** ⬜
- Hiện trạng: `rough/materials.py:268` không cộng hao hụt chỉ khi **mọi** `uses` có `waste_included`; dòng hỗn hợp thì cộng % lên
  cả dòng (cộng thừa phần TT 38) hoặc báo thiếu cả dòng.
- Test đã có: `tests/test_rough_materials.py:35–38` (AE.222 không cộng hao hụt), `:57` (thương phẩm vẫn báo thiếu).
- Việc: `quantity_with_waste` = Σ phần có mã + Σ phần không mã × (1 + waste_pct/100); thiếu `waste_pct` chỉ khi còn phần không mã.
- Xong khi: test dòng hỗn hợp đạt, ghi nhật ký.

**S13o Chống tính trùng** ⬜ (bước 2)
- o1 Lỗ thang ↔ sàn: thang tự nhận / nhập có kích thước vế, chiếu nghỉ → trừ ô thang khỏi sàn tầng trên khi người dùng chưa nhập `void_area_m2`; cảnh báo.
- o2 Mái ↔ sàn: mái bê tông không có `replaces_slab_of` mà trùng mặt bằng trên cùng → cảnh báo (không tự bỏ sàn).
- o3 Trừ cốp pha đáy sàn trên dầm/cột (`takeoff._slab_form_deduction`) gắn đúng sàn của từng mặt bằng.
- o4 Nguồn dầm theo từng tầng: tầng có dầm kết cấu → không suy; tầng không có → vẫn suy (hiện `req.structural_beams` tắt suy toàn nhà, takeoff.py:229).
- Xong khi: mỗi việc một test tái hiện lỗi trước khi sửa.

**S13p Đồng bộ API → trang → BOQ → nhóm** ⬜ (bước 3, gộp S13e)
- Tổng `by_group`, `by_class` = tổng dòng vật liệu sau lọc `material_classes`, sau trừ, sau hao hụt (test).
- Trang /do-boc: bảng theo nhóm như BOQ; giữ nhiều thang mỗi mặt bằng (hiện `model.ts` chỉ lấy `stairs[0]`).
- Kiểm trang thật trên 1 bản vẽ build, ảnh chụp từng mục (danh sách ở S13e).

**S13q Trạng thái minh bạch** ⬜ (bước 4)
- Thang auto: trạng thái = yếu nhất(B nhận nét, C dày bản / cao tầng nhập tay) — sửa `status.py:103`.
- Công tác, nhóm, tổng có phần D: gắn cờ "một phần" (không trình bày như tổng đủ) trên API, trang, BOQ.
- Xong khi: test hai trường hợp; BOQ có cột / ghi chú "một phần".

**S13b Vật liệu cốp pha** 🔍
- Hiện trạng: `dinh_muc_phan_tho.csv` đã có COP_PHA GO_MONG/COT/DAM/GIANG_TUONG/SAN/MAI/LANH_TO (AF.81: CP03 gỗ ván, đà nẹp, chống;
  CP06 đinh); `materials.py` tra `GO_{formwork_of}`.
  Có cả GO_SE_NO, GO_CAU_THANG (9 cấu kiện). Test đã có: `test_formwork_materials_by_type_and_element` (cột, sàn, ván ép trống).
- Còn làm: test 10 m² cốp pha dầm ra CP03 = 0,194 m³ (0,0794 + 0,0189 + 0,0957), CP06 = 1,429 kg; MONG, CAU_THANG;
  cốp pha âm (`_slab_form_deduction`) trừ đúng gỗ / đinh.
- Xong khi: test đạt; xác nhận trên BOQ của một bản vẽ build.

**S13c Báo cáo sai số theo cấu kiện × trạng thái** ⬜
- Việc: script gộp mọi file `data/ground_truth/du_toan/*.csv` (qua `compare_estimate.py`), mỗi dòng = cấu kiện × trạng thái A/B/C/D,
  cột: khối lượng hệ thống, dự toán, sai số %. Chỉ tiêu chỉ tính trên A/B; C/D liệt kê riêng.
- Xong khi: ra `reports/sai_so_phan_tho.xlsx`; số khớp tay với một dự toán chọn ngẫu nhiên.

**S13d Dầm bộ 46 lệch ~30%** ⬜
- Việc: so từng dầm (dài, b, h) với dự toán; phân loại lỗi: thiếu dầm, trùng tầng, tiết diện, tỷ lệ mặt bằng, giao cột.
- Xong khi: sửa gốc kèm test tái hiện, hoặc ghi lý do không sửa được vào `NHAT_KY.md`; sai số mới ghi vào báo cáo S13c.

**S13e Kiểm trang /do-boc** ⬜
- Việc: mở trang thật trên 1 bản vẽ build: chọn loại vật liệu (`material_classes`), cột trạng thái A/B/C/D, cột loại, bảng theo nhóm,
  dòng cốp pha gỗ, cát / đá / xi măng tách từ bê tông trộn tại chỗ.
- Xong khi: ảnh chụp từng mục; lỗi tìm thấy sửa xong hoặc ghi thành việc mới.

**S13i Cầu thang tự nhận** 🔄 (gộp S4c.1–S4c.2; phiên khác sửa mã 11:48–11:57 03/11, chưa ghi nhật ký)
- Hiện trạng (sửa 12:20 03/11): `rough_from_drawing` đã gọi `building_stairs` (takeoff.py:456), `drawing/viewer.py` điền sẵn
  ô thang, `do-boc/model.ts` gửi nguồn auto/manual, `status.py` thang auto = B; test `test_rough_stairs_detect.py`.
  Còn: dòng "Cầu thang, Tự nhận" trong `ho_tro_cau_kien.csv` vẫn not_supported; chưa kiểm trên bản vẽ build. Phần dưới là kế hoạch gốc.
- Việc: gọi `building_stairs` trong `rough_from_drawing` (`rough/takeoff.py`, sửa từng đoạn nhỏ) → `PlanInput.stairs` nguồn "suy";
  trang /do-boc điền sẵn ô thang, người dùng sửa được; nhập tay luôn thắng; thiếu cao bậc / dày bản thì trống + cảnh báo.
- Xong khi: test bản vẽ giả 2 vế 1 chiếu nghỉ ra đúng số bậc; chạy trên bản vẽ build không sập, số bậc đúng ≥ 1 thang;
  đổi dòng "Cầu thang, Tự nhận trên bản vẽ" trong `ho_tro_cau_kien.csv` sang conditional.

**S13j Định mức cốt liệu còn thiếu** ⬜
Việc tách nhỏ, mỗi dòng có nguồn TT 38 hoặc ghi `muc_xac_nhan` + khoảng (Quy ước B7):
- j1 Bê tông lót móng / lót nền: chọn cấu tạo theo thông số (đá 1×2, 4×6…), **không mặc định đá 4×6** (Codex review); chưa chọn thì giữ như hiện tại + cảnh báo.
- j7 Phụ gia cho cấp phối M350/M400 (hiện chỉ xi măng, cát, đá).
- j8 Cấp phối và cách cung cấp bê tông theo cấu kiện (hiện một `concrete_grade`, một `concrete_supply` cho mọi cấu kiện) — đổi `ProjectParams`, báo trước.
- j9 Bậc thang xây gạch vs bậc bê tông: tách vật liệu (cùng thể tích, khác vật liệu).
- j2 `CAN_NEN 50`: điền định mức vữa cán nền dày 5 cm (đang trống).
- j3 `COT_THEP` dây thép buộc TH10: hiện chỉ có khoảng 7,85–16,07 kg/tấn (tinh, C); tra TT 38 theo nhóm Ø (phụ thuộc S13h).
- j4 `COP_PHA VAN_EP` (CP01) m² / m² (đang trống).
- j5 Cát mịn CA05: quy tắc khi nào vữa dùng CA05 thay CA02 (theo mác vữa / thông số); không có căn cứ thì giữ CA02 và ghi rõ.
- j6 Trát tường gạch rỗng tăng 10% vữa (ghi chú AK.21 chưa áp).
- Xong khi: mỗi việc có test số học; `check_data` 0 lỗi; BOQ mẫu không còn dòng trống tương ứng.

**S13k Giằng tường kết cấu gắn tầng** ⬜
- Hiện trạng: giằng GT… đọc từ mặt bằng kết cấu nhưng chưa gắn tầng kiến trúc → chưa trừ khỏi khối xây (cảnh báo).
- Việc: gắn mặt bằng kết cấu ↔ tầng kiến trúc (dùng cách ghép tầng của dầm, `registry.floors_of`), rồi `deduct_ties` như giằng nhập tay.
- Xong khi: test giằng kết cấu trừ đúng dài chồng × cao × dày; dòng ma trận giằng kết cấu sang supported.

**S13l Diện tích mái bê tông từ bản vẽ** ⬜
- Hiện trạng: bản vẽ mái chỉ được nhận loại (`roof_kind`), diện tích + dày nhập tay.
- Việc: mái bê tông → diện tích theo đường bao mặt bằng mái (`plan_geometry`), dày từ chữ ghi; người dùng duyệt (B).
- Xong khi: test mặt bằng mái giả; nhập tay vẫn thắng.

**S13m Chốt cấu kiện không hỗ trợ** ❓
- Cần nga quyết: móng băng, móng cọc, thang cốn / xoắn, mái khung (vì kèo, xà gồ, tôn, ngói) — giữ Not supported (báo rõ trên BOQ)
  hay mở sprint riêng. Mặc định: giữ Not supported.
- Thêm theo Codex: bể ngầm / bể phốt, vách BTCT, ô văng, chống thấm mái — hỗ trợ hay ngoài phạm vi; BOQ có mục "chưa bóc" liệt kê.
- Ma trận `ho_tro_cau_kien.csv` phải khớp mã: thang tự nhận (đang not_supported), móng băng nhập tay (Codex báo lệch, cần kiểm).

**S13f / S13g / S13h** ⏸ chờ dữ liệu
- S13f: người dùng gửi đáp án bóc tay ≥ 5 bản vẽ → đo sai số tường theo đặc tả (A, B, bộ test cố định).
- S13g: 20–30 bản vẽ chia build / test → chỉnh nhận tường cho kiểu trình bày như banve1; chỉ chỉnh trên build.
- S13h: bản vẽ có bảng thống kê thép (theo Ø), bảng cửa (QU-15, lanh tô theo cửa thật).

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

### KD Kho dữ kiện đầu vào có AI hỗ trợ (05/11/2026) 🔄

Kế hoạch: `docs/KE_HOACH_KHO_DU_KIEN_AI.md` (KD01–KD08).

- ✅ KD01 (phần cache) Cache kết quả `/api/projects/{id}/analysis` theo hash tệp + thông số + mã/quy tắc/danh mục (`analysis_cache.py`, không đổi schema; bản vẽ build 7×12: 57,8 s → 0,28 s)
- ✅ KD01 (phần dữ kiện) `facts.Fact`/`FactReport` (nguồn, ref, trích đoạn, cách lấy, A–D); phân tích hồ sơ trả `input_facts` (cache cùng kết quả)
- ✅ KD02 `facts/verify.py` (nhãn trong danh mục, trích đoạn có thật) + `facts/ai.py` (OpenAI json_schema strict, cache, allow_ai mặc định tắt, lỗi mạng không chặn)
- ✅ KD03 `facts/params.py` + `data/rules/ghi_chu_thong_so.csv`: quy tắc trước, AI sau, mã đọc số; gợi ý B + xung đột; tab Phần thô "Thông số gợi ý từ hồ sơ"; DOCX qua endpoint candidates
- ✅ KD04 tiêu đề cột bảng thép chưa khớp → AI → duyệt thêm `bang_thep.csv` · ✅ KD05 tiêu đề tờ/mặt bằng tầng (`tieu_de_mat_bang.csv` mới, plans.py đọc) + ký hiệu cấu kiện
- ✅ KD06 hàng chờ `data/ai_de_xuat/queue.jsonl`, API `/api/admin/ai-proposals`, mục duyệt trên /quy-tac; duyệt = dòng CSV + xóa cache bộ đọc quy tắc
- ✅ KD07 gỡ PDF; DOCX theo đoạn; `missing_inputs`; dự toán XLSX → mã công tác (`cong_tac_du_toan.csv` + AI), `estimate.compare()`
- 🔄 KD08 đã tách nguyên nhân (scripts/kd08_tach_chenh_xay.py, docs/review/KD08_HINH_HOC_XAY_DAM_COP_PHA.md); **chưa sửa mã nhận diện**: cần đáp án hình học xác nhận (thiếu tường T1–T5, chọn bản trùng tầng ở sân thượng)

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
04/11/2026 · Luồng SAMPLE dự án 23 đã đến Kiểm tra công tác và khối lượng (kết quả 26). Tư vấn W5 trên web, chứng từ mua ACTUAL và gắn UUID phân tích với bản vẽ/hồ sơ trên máy chủ còn mở. Xem docs/review/claude_20261104/BAO_CAO_REVIEW.md.
