# Prompt cho Codex: review kế hoạch Lộ trình S13 (hoàn thiện phần thô)

Dán nguyên phần dưới dòng `---` vào Codex, mở ở thư mục `optimat-ai/`.
Bản chi tiết 03/11/2026 (thay bản tóm tắt cùng ngày). Mọi "hiện trạng" dưới đây đã được Claude đối chiếu với mã lúc
12:20 03/11/2026, kèm file:dòng; mã có thể đã đổi tiếp vì nhiều phiên làm song song, nên **kiểm lại từng dòng**.

---

Bạn là reviewer cho dự án OptiMat AI (đồ án tốt nghiệp; Python 3.13, FastAPI, ezdxf, pandas, pydantic; frontend Next.js 16,
React 19). Đọc `CLAUDE.md` trước. Quy tắc bắt buộc liên quan trực tiếp tới lần review này:

- **B7 — không đoán**: thiếu số liệu (thông số công trình, định mức, kích thước) thì để trống + cảnh báo, không điền mặc định.
- **Quy tắc nằm trong CSV** (`data/rules/*.csv`), không viết cứng trong mã; không quy tắc nào khớp thì để trống, báo `unmatched`.
- **build / test**: chỉ chỉnh quy tắc theo bản vẽ `build`; bản vẽ `test` chỉ để báo cáo độ chính xác.
- **Dữ liệu**: mọi dòng có `data_kind` (ACTUAL / SAMPLE / SYNTHETIC); không báo độ chính xác bằng SAMPLE, SYNTHETIC.
- **Phạm vi**: nhà ở riêng lẻ xây mới ≤ 5 tầng, **chỉ phần thô** (kiến trúc + kết cấu). Điện nước, biện pháp thi công,
  hoàn thiện nằm ngoài phạm vi. Không lập dự toán, không kiểm tra chịu lực.
- **File dùng chung** (`rough/models.py`, `rough/takeoff.py`, `drawing/takeoff.py`, `api/main.py`, `CLAUDE.md`, `SPRINTS.md`):
  chỉ sửa từng đoạn nhỏ; đổi tên trường hay cách gộp nhóm phải báo trước.
- Chú thích, thông báo người dùng: tiếng Việt. Mỗi thay đổi giữ `pytest` đạt.

Trả lời bằng tiếng Việt. **Chỉ review, không sửa mã, không sửa kế hoạch**, trừ khi tôi đồng ý sau đó.

Lần này review **kế hoạch** (chưa có mã mới cho S13, trừ phần thang do phiên khác vừa làm — xem S13i). Mục đích:

1. Phần "hiện trạng" của từng sprint có đúng với mã thật không.
2. Việc cần làm có đủ, đúng chỗ (file, hàm), không phá luồng hiện có không.
3. Tiêu chí xong có đo được bằng số / bài test cụ thể không.
4. Thứ tự, phụ thuộc có hợp lý không; sprint nào nên tách, gộp, cắt.
5. Còn lỗ hổng nào của phần thô mà không sprint nào che.

Kế hoạch gốc: `SPRINTS.md`, mục "Lộ trình S13". Nhật ký: `NHAT_KY.md`. Đặc tả trạng thái A/B/C/D: `rough/status.py` (docstring).

## 1. Luồng phần thô (để đọc mã nhanh)

```
DXF kiến trúc ──► drawing/takeoff.takeoff_plans()      tách mặt bằng tầng, tường, cửa, chiều cao
                  rough/takeoff.rough_from_drawing()   (takeoff.py:442) dựng RoughRequest:
                     ├─ detect_columns(sub)             cột (rough/columns.py)
                     ├─ building_stairs(subs, names)    thang tự nhận (takeoff.py:456, mới — xem S13i)
                     ├─ rough_parts(sub)                vai trò thấy theo layer/block (chỉ để nhắc nhập)
                     ├─ room_labels(sub)                tên phòng (WC, ban công…) cho chống thấm
                     └─ structural_parts([kiến trúc] + kết cấu)   (takeoff.py:469)
                           ├─ read_rebar_schedules      bảng thống kê thép (rough/rebar.py)
                           ├─ read_secondary            giằng GT…, sê nô SN…, cao lanh tô LT…, loại mái (secondary.py:194)
                           └─ read_structural           dầm D…/ĐK…, móng M…, bảng cột (rough/structural.py)
Trang /do-boc (người dùng sửa) ──► RoughRequest
rough/takeoff.compute_rough()  (takeoff.py:168) — CÔNG THỨC CHỐT DUY NHẤT:
   mỗi mặt bằng: wall_works, column_works, stair_works, lintel_under_beam (L1), deduct_ties (L2), linear_works,
                 beam_works, area_works (sàn, cán nền, nền, chống thấm), _slab_form_deduction
   toàn nhà:     dầm kết cấu × số tầng, schedule_column_works, linear_works(kết cấu), roof_works,
                 drop_slab_under_roof (L3), foundation_works, steel_works, cross_checks
   ──► rough/materials.materials_for_works()  (materials.py:280): công tác → vữa/bê tông → vật liệu mua về
   ──► trạng thái A/B/C/D (rough/status.py), nhóm, loại vật liệu thô, BOQ (rough/boq.py)
```

Dữ liệu quy tắc: `data/rules/dinh_muc_phan_tho.csv` (định mức TT 38/2026), `data/catalog/material_relations.csv` (cấp phối vữa
COMPOSED_OF), `data/rules/ho_tro_cau_kien.csv` (ma trận khả năng: supported / conditional / not_supported),
`data/rules/ky_hieu_cau_kien.csv` (ký hiệu D, ĐK, M, GT, SN, LT…), `data/rules/loai_mai.csv`.
Đáp án thật: `data/ground_truth/du_toan/` — `46_nha_tan_binh.csv` (dự toán 64 công tác, split build), `46_thong_so.json`,
`46_vat_tu.csv`, `banve1_nha_pho_di_an.csv`, `banve1_vat_tu.csv`, `cases.csv`; so bằng `scripts/compare_estimate.py`.

## 2. Hiện trạng đã đối chiếu (cần bạn xác nhận / bác bỏ)

### 2.1 Cấu kiện

| Cấu kiện | Cách có số | Trạng thái A/B/C/D | Bằng chứng | Ma trận `ho_tro_cau_kien.csv` |
|---|---|---|---|---|
| Tường xây, trát, lanh tô theo cửa | Cặp nét trên mặt bằng kiến trúc | theo nguồn | `rough/walls.py`, `tests/test_rough_walls.py` | supported |
| Cột | Vùng tô đặc / layer cột; hoặc bảng thống kê cột | B / A | `columns.py` `detect_columns`, `schedule_column_works` | supported |
| Sàn, cán nền, nền trệt, chống thấm | Đường bao phòng trên lưới 10 mm | B (bao lồi + cảnh báo nếu hở) | `areas.py` `plan_geometry`, `area_works` | supported |
| Dầm, đà kiềng | D…/ĐK… + cặp nét trên mặt bằng kết cấu; không có thì suy từ tường + cột | A / B | `structural.py` `measure_beams`; `beams.py` `infer_beams` | supported / conditional |
| Móng đơn | M… + hình chi tiết (khối hộp, bậc, vát) | A / C | `structural.py` `footing_detail_sizes`, `foundations.py` | conditional |
| Thép | Bảng thống kê TEXT/MTEXT; không có thì hàm lượng kg/m³ | A / C | `rebar.py`, `steel.py` | supported / conditional |
| Giằng tường, sê nô | GT…/SN… + cặp nét trên mặt bằng kết cấu; hoặc nhập vào mặt bằng kiến trúc | B / C | `secondary.py` `read_secondary`, `linear_works`, `deduct_ties` | conditional / supported |
| Cầu thang bản | Tự nhận nét mũi bậc (mới) hoặc nhập tay | B / C | `stairs.py` `detect_stairs`, `building_stairs`; `status.py:103` | **vẫn ghi `not_supported` cho "Tự nhận" (dòng 11) — lệch mã** |
| Mái bê tông | Nhập diện tích + dày (`ProjectParams.roofs`) | C | `secondary.py:155` `roof_works` | supported |
| Loại mái | Tiêu đề bản vẽ mái → `loai_mai.csv` | chỉ cảnh báo | `secondary.py` cuối `read_secondary` | — |
| Móng băng, móng cọc, thang cốn/xoắn, mái khung | — | not_supported | `roof_works` (khung), `Stair.kind` | not_supported |

### 2.2 Vật liệu (đường đi từ công tác ra vật liệu, `materials.py`)

| Công tác | Vật liệu | Định mức / nguồn | Ghi chú |
|---|---|---|---|
| XAY | gạch theo `wall_systems` + vữa xây | AE… TT 38 | `waste_included` khi mã AE (materials.py:342) |
| TRAT 15, 20 | vữa → XM01 + CA02 | AK.21200 | — |
| CAN_NEN 30 | vữa | AK.41100 | **CAN_NEN 50 trống số, không mã** |
| Vữa M50 / M75 / M100 | XM01 + CA02 | COMPOSED_OF (TT 38 PL VII) | không dùng CA05 (cát mịn) |
| Bê tông kết cấu (`CONCRETE_WORKS`: LANH_TO, COT, DAM, SAN, CAU_THANG, GIANG_TUONG, SE_NO, MAI, MONG) | trộn tại chỗ: XM01/XM02 + CA01 + DA01; thương phẩm: giữ m³ | BE_TONG_TRON M100–M400, mọi dòng có mã 11.1xxxx | `params.concrete_grade` + **một** `concrete_supply` cho mọi cấu kiện |
| BE_TONG_LOT (lót móng) | như trên với `lean_concrete_grade` | BE_TONG_TRON M100 → **DA01 (đá 1×2)** | materials.py:305; thực tế lót thường đá 4×6 (DA03) |
| NEN_DEM_CAT | CA03 1,22 m³/m³ | AB.13410 | — |
| COT_THEP | thép (tấn) + dây buộc TH10 | TH10 chỉ có khoảng 7,85–16,07 kg/tấn, `tinh`, không mã → C | test `test_steel_and_tie_wire` |
| COP_PHA gỗ | CP03 (ván, đà nẹp, chống) + CP06 đinh | AF.81120–81160 cho MONG, COT, DAM, GIANG_TUONG, SAN, MAI, LANH_TO, **SE_NO, CAU_THANG** | `formwork_type = go` |
| COP_PHA ván ép | CP01 | **trống số, không mã** | test khẳng định trống |
| CHONG_THAM | CT01 1,128 (tinh); CT02 3–4, CT03 1,5–2 kg/m² (chỉ khoảng) | không mã TT 38 → C | — |
| Chưa định mức nào dùng | DA02 (2×4), DA03 (4×6), DA04 (mạt), DA05 (hộc), CA04 (nghiền), CA05 (mịn) | — | có trong `materials.csv` |

Hao hụt (materials.py:264–273): dòng vật liệu mà **mọi** phần góp (`uses`) đều từ định mức có `norm_code` thì
`quantity_with_waste = quantity`; ngược lại cần `materials.waste_pct`, thiếu thì `missing` += "hao hụt thi công (%)".

### 2.3 Kiểm thử đã có (liên quan S13)

- Hao hụt: `tests/test_rough_materials.py:35–38` (AE.222 không cộng hao hụt), `:57` (thương phẩm vẫn báo thiếu).
- Cốp pha gỗ: `tests/test_rough_materials.py:101` `test_formwork_materials_by_type_and_element` (cột, sàn; ván ép trống).
- Dây buộc: `tests/test_rough_materials.py:74` `test_steel_and_tie_wire`.
- Thang: `tests/test_rough_stairs.py` (công thức), `tests/test_rough_stairs_detect.py` (2 vế có chiếu nghỉ; lưới gạch không
  phải thang; thang vẽ dở lấy thang đủ nhất nhà), `tests/test_rough_secondary.py:103, 112`.
- Giằng, mái: `tests/test_rough_secondary.py:53, 63, 71` (giằng trừ khối xây, chồng nhau trừ một lần), `:85, 94` (mái thay sàn, mái khung).
- Bản vẽ thật: `tests/test_rough_build_drawings.py`.
- pytest chạy 12:30 03/11/2026 (cả thay đổi thang của phiên khác): 333 đạt, 3 xfail.

## 3. Cách kiểm soát sprint (đề xuất)

Chỉ đánh ✅ khi đủ 4 bằng chứng: (1) bài test mới có tên, chạy đạt; (2) `pytest` toàn bộ đạt, ghi số bài; (3)
`python scripts/check_data.py` 0 lỗi nếu đụng `data/`; (4) một dòng `NHAT_KY.md` ghi file đã sửa. Sprint đổi khả năng nhận
cấu kiện thì sửa dòng tương ứng trong `ho_tro_cau_kien.csv`.
Ký hiệu: ✅ xong · 🔄 đang làm · ⬜ chưa làm · 🔍 mã có, chưa đủ bằng chứng · ⏸ chờ dữ liệu · ❓ chờ quyết định.

## 4. Các sprint (chi tiết)

Thứ tự đề xuất: S13a → S13b → S13i → S13j → S13k → S13l → S13d → S13e → S13c → (S13f, S13g, S13h khi có dữ liệu). S13m quyết bất kỳ lúc nào.

### S13a — Hao hụt không báo thiếu sai · đề xuất ✅ (chờ xác nhận)
- **Hiện trạng**: đã làm (materials.py:264–273, `waste_included` gán ở `norm_line`, `mortar`, `_masonry`); test `test_rough_materials.py:35–38, 57`.
- **Còn lại**: chỉ cần xác nhận. Trường hợp chưa có test: một dòng vật liệu nhận phần góp từ cả định mức có mã lẫn không mã
  (vd. XM02 từ bê tông trộn tại chỗ có mã + vữa tham khảo không mã) → phải báo cần hao hụt cho **toàn dòng** hay chỉ phần không mã?
- **Câu hỏi cho reviewer**: cách "tất cả hoặc không" có làm cộng thiếu / thừa hao hụt không? Nên tách `quantity_with_waste` theo phần góp?

### S13b — Vật liệu cốp pha gỗ theo cấu kiện · đề xuất ✅ (chờ xác nhận)
- **Hiện trạng**: `dinh_muc_phan_tho.csv` có GO_ cho 9 cấu kiện (cả SE_NO, CAU_THANG); `materials.py:312–320` tra `GO_{formwork_of}`;
  test `test_formwork_materials_by_type_and_element` (cột, sàn, ván ép trống).
- **Còn lại**: test cho DAM, MONG, CAU_THANG (bộ 3 dòng thay vì 4), công tác cốp pha **âm** (`_slab_form_deduction` trừ đáy sàn
  trên dầm/cột, takeoff.py:419) có trừ đúng gỗ/đinh không; `formwork_of` không có dòng GO_ → trống + lý do.
- **Tiêu chí**: 10 m² cốp pha dầm → CP03 = 10 × (0,00794 + 0,00189 + 0,00957) = 0,194 m³, CP06 = 1,429 kg.

### S13i — Cầu thang tự nhận · 🔄 phiên khác đang làm (mã sửa 11:48–11:57 03/11, chưa ghi nhật ký)
- **Hiện trạng mới**: `rough_from_drawing` gọi `building_stairs` (takeoff.py:456), `drawing/viewer.py:89–99` điền sẵn ô thang;
  frontend `do-boc/model.ts:195–243` điền ô thang, `stairSource` → "auto" nếu người dùng không sửa, ngược lại "manual";
  `status.py:103`: thang auto = B, manual = C. Test `test_rough_stairs_detect.py` (3 bài).
- **Còn lại**: (1) dòng 11 `ho_tro_cau_kien.csv` còn `not_supported` → đổi `conditional`, điều kiện "chỉ thang bản; số bậc, vế,
  bậc suy từ nét mũi bậc"; (2) chạy trên bản vẽ build có thang (bộ 46: dự toán ghi bản thang `2,5 × 3,6 × 0,1`) so số bậc,
  rộng vế với hình vẽ; (3) nhật ký.
- **Câu hỏi**: `building_stairs` áp "thang đủ nhất nhà" cho tầng vẽ dở — có nguy cơ gán thang cho tầng không có thang (tầng
  mái, tum) hoặc đếm thang hai lần (tầng dưới vẽ đầu dưới, tầng trên vẽ đầu trên của cùng một thang)? Ô thang có nằm trong
  đường bao sàn (`area_works`) → sàn bị tính cả lỗ thang? Cốp pha thang AF.81160 có trùng cốp pha sàn?
- **Tiêu chí đề xuất**: trên bộ 46, số bậc mỗi tầng lệch ≤ 1 bậc, rộng vế lệch ≤ 50 mm so với đo tay trên hình; m³ bản thang
  lệch ≤ 10% so với dự toán.

### S13j — Định mức cốt liệu còn trống / chưa dùng · ⬜
Mỗi việc nhỏ, có test số học; số phải có `norm_code` TT 38 hoặc `muc_xac_nhan` + `qty_min/qty_max` + `ngay_tra` (check_data bắt).
- **j1 Bê tông lót đá 4×6**: hiện BE_TONG_LOT dùng chung BE_TONG_TRON M100 (DA01). Thêm biến thể cấp phối lót (DA03) trong CSV,
  `materials.py:305` chọn biến thể lót; không có dòng thì giữ DA01 + cảnh báo? Hay để trống (B7)?
- **j2 CAN_NEN 50**: tra AK.41xxx dày 5 cm; không có thì giữ trống.
- **j3 Dây buộc**: hiện chỉ có khoảng 7,85–16,07 kg/tấn (C). Tra định mức TT 38 theo nhóm đường kính (≤ 10, ≤ 18, > 18) → cần
  thép chia Ø (phụ thuộc S13h) — hay giữ khoảng?
- **j4 Ván ép CP01**: tra AF.82 (ván khuôn ván ép / phủ phim) m²/m² và số lần luân chuyển; không có thì giữ trống.
- **j5 Cát mịn CA05 / cát nghiền CA04**: chỉ dùng khi thông số chọn; không có căn cứ thì giữ CA02, ghi rõ.
- **j6 Trát tường gạch rỗng +10% vữa** (ghi chú AK.21): áp theo `wall_systems` (gạch rỗng) — cần cột phân biệt gạch đặc / rỗng.
- **j7 (mới)** DA05 đá hộc: chỉ cần nếu có móng xây đá hộc — phụ thuộc S13m.
- **Câu hỏi**: j1, j5 có vi phạm B7 không (chọn vật liệu thay người dùng)? Có nên đưa thành thông số `ProjectParams` (vd.
  `lean_concrete_aggregate`) thay vì quy tắc ngầm? Có cần tách `concrete_supply` theo cấu kiện (móng thương phẩm, lanh tô trộn
  tay là phổ biến)?

### S13k — Giằng tường đọc từ kết cấu gắn tầng, trừ khối xây · ⬜
- **Hiện trạng**: `structural_parts` gom `members` từ mọi file vào `RoughRequest.members` (takeoff.py:469–495), tính ở
  `linear_works("bản vẽ kết cấu", req.members)` — **không** gắn mặt bằng kiến trúc nên `deduct_ties` (chạy theo `p.members`) không trừ.
  `read_secondary` cảnh báo chuyện này.
- **Việc**: ghép mặt bằng kết cấu ↔ tầng kiến trúc (`drawing/registry.py:170` `floors_of`, như dầm dùng `_floor_key`),
  đổi tọa độ (hai bản vẽ khác gốc tọa độ, khác tỷ lệ — `structural_scale`), đưa giằng vào `p.members` rồi `deduct_ties`.
- **Rủi ro**: lệch gốc tọa độ giữa file kiến trúc và kết cấu (chưa có bước căn chỉnh nào); giằng người dùng nhập tay trùng giằng
  kết cấu → trừ hai lần (test `test_overlapping_ties_deduct_masonry_once` chỉ cho giằng cùng nguồn).
- **Câu hỏi**: căn chỉnh tọa độ hai bản vẽ đã có ở đâu chưa (S03 mapping `/mapping`)? Nếu chưa, sprint này có quá lớn?

### S13l — Diện tích mái bê tông từ bản vẽ mái · ⬜
- **Hiện trạng**: `roof_works` (secondary.py:155) chỉ dùng `ProjectParams.roofs` nhập tay; `read_secondary` nhận loại mái theo tiêu đề.
- **Việc**: mặt bằng mái kiểu bê tông → diện tích theo đường bao (`plan_geometry`) hoặc mép sàn mái, dày từ chữ ghi; trạng thái B;
  nhập tay thắng; mái dốc: diện tích nghiêng = bằng / cos(góc) — góc lấy ở đâu?
- **Rủi ro**: trùng sàn tầng trên cùng — đã có `drop_slab_under_roof` nhưng cần `replaces_slab_of`; mái tự nhận phải tự điền hoặc cảnh báo.

### S13d — Dầm bộ 46 lệch ~30% · ⬜
- **Việc**: chạy `compare_estimate.py` bộ 46, so từng dầm (dài, b, h) với dòng diễn giải dự toán; phân loại nguyên nhân: thiếu
  dầm, trùng tầng (`duplicate_plans`, `_floor_key`), nhân số tầng (`structural_floors`), tiết diện (dự toán 200 × 350 gồm sàn 100),
  tỷ lệ mặt bằng (`structural_scale`), trừ giao cột (`beam_joints`).
- **Tiêu chí**: sửa gốc kèm test tái hiện, hoặc ghi lý do; số mới vào báo cáo S13c. Mục tiêu đề xuất: lệch ≤ 10% (cần chốt).

### S13e — Kiểm trang /do-boc · ⬜
- **Việc**: mở trang thật (`cd frontend && npm run dev`, API `uvicorn`) với 1 bản vẽ build; kiểm: ô chọn loại vật liệu
  (`material_classes`), cột trạng thái A/B/C/D, cột Loại, bảng theo nhóm, cốp pha gỗ, cát / đá / xi măng tách từ bê tông,
  ô thang điền sẵn + nguồn auto/manual.
- **Tiêu chí**: ảnh chụp từng mục; lỗi sửa hoặc ghi thành việc mới. Câu hỏi: nên đưa S13e lên trước S13j để thấy lỗi giao diện sớm?

### S13c — Báo cáo sai số cấu kiện × trạng thái · ⬜
- **Việc**: script gộp mọi `data/ground_truth/du_toan/*.csv` (+ `*_vat_tu.csv` cho vật liệu: xi măng, cát, đá, thép), mỗi dòng
  = cấu kiện × trạng thái; cột: hệ thống, dự toán, lệch %. Chỉ tiêu chỉ tính A/B; C/D liệt kê riêng. Ra `reports/sai_so_phan_tho.xlsx`.
- **Lưu ý**: bộ 46 là `split = build` (đã dùng sửa mã) — không được dùng làm số báo cáo độ chính xác.
- **Câu hỏi**: với 1–2 dự toán build, báo cáo này có ý nghĩa gì? Có nên đợi S13f/S13g?

### S13m — Chốt cấu kiện không hỗ trợ · ❓ chờ chủ đồ án
Móng băng, móng cọc, thang cốn/xoắn, mái khung (vì kèo, xà gồ, tôn, ngói), móng xây đá hộc. Mặc định: giữ not_supported,
BOQ ghi rõ dòng không trả số. Câu hỏi: với nhà phố 3–5 tầng miền Bắc, móng băng / cọc rất phổ biến — để ngoài phạm vi có làm
kết quả "toàn bộ phần thô" mất ý nghĩa không?

### S13f, S13g, S13h · ⏸ chờ dữ liệu
- S13f: đáp án bóc tay ≥ 5 bản vẽ → đo sai số tường theo đặc tả (A, B, bộ test cố định).
- S13g: 20–30 bản vẽ chia build / test → chỉnh nhận tường cho kiểu trình bày như banve1; chỉ chỉnh trên build.
- S13h: bản vẽ có bảng thống kê thép theo Ø, bảng cửa (QU-15, lanh tô theo cửa thật).

## 5. Cần kiểm tra (trả lời từng mục)

1. **Hiện trạng §2 có đúng mã không** — mỗi dòng bảng 2.1, 2.2: Đúng / Sai / Một phần + file:dòng. Đặc biệt:
   `building_stairs` đã nối đủ (API `/api/takeoff/rough/auto`, trang, `batch_takeoff.py`)? Ma trận dòng 11 còn lệch?
   Còn định mức trống nào trong `dinh_muc_phan_tho.csv` mà §2.2 bỏ sót? `formwork_of` nào sinh ra mà không có dòng GO_?
2. **Sót việc** so với "bóc toàn bộ phần thô ra vật liệu": đào đắp đất, bê tông lót nền, bể nước ngầm / bể phốt (dự toán bộ 46
   có dòng "BNN"), vách BTCT, ô văng, sê nô xây, bậc tam cấp xây, tường chắn mái / lan can xây, chống thấm sàn mái, gạch xây
   bậc thang, cốt thép chờ, mạch ngừng. Cái nào nên thành việc, gắn vào sprint nào?
3. **Tiêu chí đo được** — tiêu chí nào mơ hồ, đề xuất số. Có tiêu chí nào chỉ đo được trên bản vẽ test (vi phạm build/test)?
4. **B7 và trạng thái** — việc nào có nguy cơ điền mặc định (j1, j5, S13l dày mái, góc mái dốc, S13i thang đủ nhất nhà)?
   Dữ liệu suy (thang auto, mái theo đường bao, giằng gắn tầng) nên B hay C theo quy tắc trong `status.py`?
5. **Không cộng trùng** — thang ↔ sàn (lỗ thang) ↔ cốp pha; giằng kết cấu ↔ giằng nhập tay; mái tự nhận ↔ sàn tầng trên cùng;
   dầm kết cấu × số tầng ↔ dầm suy; lót móng ↔ nền trệt. Biện pháp hiện có (file:dòng) và còn thiếu.
6. **Hao hụt** — luật "mọi phần góp đều có mã thì không cộng" (§S13a) đúng với TT 38 PL II quy định chung chưa? Dòng trộn hai loại?
7. **Thứ tự, phụ thuộc, quy mô** — sprint nào quá lớn (S13k?), nên tách, gộp, cắt nếu thiếu thời gian đồ án.
8. **File dùng chung / lược đồ** — sprint nào phải đổi trường `ProjectParams`, `PlanInput`, `RoughRequest`, `WorkItem`
   hoặc bảng PostgreSQL (`rough_norms` có đủ cột cho biến thể mới?) — liệt kê để báo trước.
9. **Rủi ro lớn nhất** của cả lộ trình (dữ liệu đáp án ít, lệch gốc tọa độ KT–KC, thời gian) và đề xuất giảm thiểu.

## 6. Cách chạy

```powershell
$env:PYTHONIOENCODING = "utf8"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m pytest tests/test_rough_materials.py tests/test_rough_stairs.py tests/test_rough_stairs_detect.py tests/test_rough_secondary.py -q
.venv\Scripts\python scripts/check_data.py
$env:PYTHONPATH = "src"
.venv\Scripts\python scripts/compare_estimate.py data/ground_truth/du_toan/46_nha_tan_binh.csv <Kien_truc.dxf> --structural <Ket_cau.dxf>
.venv\Scripts\python scripts/batch_takeoff.py data/drawings/build --params data/sample/thong_so_mau.json
```

Tìm nhanh: `rg "building_stairs|detect_stairs"`, `rg "waste_included"`, `rg "formwork_of="`, `rg "BE_TONG_LOT|lean_concrete"`,
`rg "members" src/optimat/rough/takeoff.py`. Bản vẽ thật (nếu có trên máy): `data/drawings/build/`, `data/drawings/raw_20261102/`
(không vào Git).

## 7. Định dạng trả lời

1. **Bảng Hiện trạng**: mục §2, khẳng định, Đúng / Sai / Một phần, bằng chứng file:dòng.
2. **Bảng Vấn đề của kế hoạch**, xếp Nghiêm trọng / Trung bình / Nhỏ: sprint, vấn đề, hậu quả nếu làm theo kế hoạch hiện tại,
   đề xuất sửa (một câu).
3. **Việc còn sót**: mỗi việc một dòng, gắn sprint nào hoặc sprint mới, ưu tiên.
4. **Trả lời câu hỏi** trong từng sprint (§4) và 9 mục §5, ngắn gọn.
5. **Thứ tự đề xuất** sau review và sprint nên cắt nếu thiếu thời gian.

Không góp ý văn phong nếu không ảnh hưởng nội dung.
