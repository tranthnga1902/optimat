# M01 – Ma trận phạm vi phần thô và cách đo mức hoàn tất

Ngày lập: 03/11/2026; Codex cập nhật quyết định chủ đồ án cùng ngày. Người lập ban đầu: Claude (dev).
Trạng thái: **PHẠM VI ĐÃ DUYỆT; M01 ✅ — Codex nghiệm thu tài liệu BA ngày 03/11/2026 (sau vòng sửa 2, mục 13)**. ✅ là nghiệm thu tài liệu, không phải chức năng. Không đổi mã, CSV vận hành, schema/API hay DB trong M01.

Kế hoạch gốc: [KE_HOACH_NGHIEM_THU_PHAN_THO.md](KE_HOACH_NGHIEM_THU_PHAN_THO.md) (dòng M01, mục 1 thước đo).

## 0. Quy ước đọc tài liệu

Mỗi nhận định mang một nhãn nguồn:

| Nhãn | Nghĩa | Ai chịu trách nhiệm |
|---|---|---|
| **[HT]** | Hiện trạng đã kiểm bằng đọc mã/test (file:dòng ghi kèm). Không lấy từ mô tả trong tài liệu | Claude, Codex kiểm lại |
| **[ĐX]** | Đề xuất của Claude, chưa ai duyệt | Codex review, chủ đồ án quyết |
| **[QĐ]** | Quyết định đã có văn bản của chủ đồ án (nguồn ghi kèm) | Chủ đồ án |
| **CHỜ QĐ** | (Lịch sử vòng 1) Cần chủ đồ án quyết. Từ 03/11/2026 không còn mục phạm vi nào ở trạng thái này (5A) | Chủ đồ án |

[QĐ] Ranh giới chung: nhà ở riêng lẻ xây mới ≤5 tầng; kiến trúc + kết cấu phần thô; không điện nước, hoàn thiện,
biện pháp thi công, thiết kế/kiểm tra chịu lực hoặc lập dự toán. Quyết định chi tiết tại 5A đã được chủ đồ án duyệt ngày
03/11/2026 trong chat: “Đồng ý các đề xuất trên. Mái khung và thang cốn/xoắn loại khỏi phạm vi đồ án.”
Thông điệp này chấp thuận bảng đề xuất Codex trình bày ngay trước đó; QĐ-11 áp dụng theo bảng Codex (quét nước xi măng
chỉ tính khi là lớp cấu tạo cần thiết được xác định), thay cho đề xuất OUT toàn bộ trong bản Claude trước.
**Mái khung và thang cốn/xoắn là OUT/H5, không phải IN nhưng chưa hỗ trợ/H4.** Hạng mục IN chưa có mã/dữ liệu vẫn là thiếu,
không trở thành OUT. Duyệt phạm vi không đồng nghĩa chức năng đã triển khai hoặc mẫu số từng hồ sơ đã được khóa.

Ba trục tách riêng, không suy trục này từ trục kia (sửa theo review vòng 1, vấn đề #1, #2, #5):

- **Nhận – cách tạo dữ liệu** của từng đầu vào (bản vẽ → đầu vào): `TN` tự nhận đọc trực tiếp · `SL` suy luận theo quy tắc ·
  `NT` nhập tay hoặc người dùng sửa · `KH` không có đường nào. Đây **không** phải trạng thái A/B/C/D: A/B/C/D là độ tin cậy yếu nhất
  của mọi đầu vào một dòng (`status.py`), nên sàn có diện tích tự đo nhưng dày sàn nhập tay vẫn mang C dù diện tích không nhập tay.
- **Luồng** (đầu vào → công tác → vật tư → API/trang/BOQ), xét từng đầu vào **bắt buộc**:
  `T` theo mã, mọi đầu vào bắt buộc có đường cung cấp qua trang /do-boc (đọc tự động hiển thị + sửa được, hoặc ô nhập)
  · `T-` công thức có, nhưng ít nhất một đầu vào bắt buộc chỉ có qua bộ đọc tự động không sửa được, hoặc không có đường nào trên trang
  (ghi đầu vào thiếu) · `API` chỉ đưa vào được qua JSON `/api/takeoff/rough` · `CT` công thức có nhưng sai/hở nghiệp vụ
  · `NS` dòng "Not supported" hiện rõ, không ra số · `—` không có dòng nào, hạng mục **biến mất**.
  **Không dòng nào được đánh "đủ luồng":** `T` chỉ là kết luận đọc mã; chưa có thao tác thật trên trang (P01/P02, quy tắc nghiệm thu 6) nên mọi `T` là **chưa xác minh thao tác**.
- **Thiếu ở bước** (cho hạng mục chưa đạt), đánh theo thứ tự luồng, dừng ở bước đầu tiên thiếu:
  `S1` dạng cấu kiện/công thức · `S2` đầu vào (trường mô hình hoặc bộ đọc) · `S3` nối luồng (trang, BOQ) · `S4` vật tư/định mức
  · `MÃ` thực sự cần mã công tác mới (chỉ khi mã có sẵn không chứa được về đơn vị, cốp pha, thép hoặc định mức). Không mặc định mở `WORKS` mới.

"Không tự nhận" ≠ "không tính được khi nhập tay". "Có công thức" ≠ "đã đủ luồng". "Chưa có chức năng riêng" ≠ "không có mã công tác".

Đường cung cấp đầu vào trên trang /do-boc [HT, đọc mã, chưa thao tác]: `roughFields`/`PP` (`do-boc/model.ts:170-191`) và `roughRequest`
(`model.ts:231-250`) gửi: tường, cửa (rộng, cao), cột (chỉ bỏ/giữ: `toggleCol` `Review.tsx:248-250`; không sửa tiết diện/tọa độ, không thêm cột), chiều cao tầng, ô trống, ban công, diện tích nhập tay, **một** thang
(số bậc, rộng vế, rộng bậc, chiếu nghỉ), thông số công trình (mác, vữa, dày trát/cán/sàn/bản thang, rộng/cao dầm chung, lanh tô, loại
ván, cốt tự nhiên, mở rộng hố, taluy, lớp nền, cổ tường + vật liệu chống thấm, hàm lượng thép, loại vật liệu). Phần đọc kết cấu
(`foundations`, `structural_beams`, `members`, `rebar`, `column_schedule`) được **chuyển nguyên**, trang chỉ hiện số loại móng, số mặt
bằng dầm (`Rough.tsx:72`). Trang **không** gửi: `PlanInput.beams`, `PlanInput.members`, `params.roofs`, móng nhập/sửa, cao độ đáy móng,
cổ móng, dầm thang, `Stair.kind`, thang thứ hai, nhãn phòng thêm/sửa, `steel_schedule_t`, `wall_systems_by_class`.

## 1. Ma trận tổng (một dòng một hạng mục)

Phạm vi: `IN` trong phạm vi ([QĐ chung] hoặc [QĐ 5A]) · `OUT` ngoài phạm vi ([QĐ chung] hoặc [QĐ 5A]). Không còn hạng mục `CHỜ` (bản vòng 1 có; đã thay theo 5A).
Chi tiết từng mã (đầu vào, công tác, vật tư, giao trùng, hành vi thiếu, bằng chứng) ở mục 2.

| Mã | Hạng mục / dạng cấu tạo | Phạm vi | Nhận (cách tạo đầu vào) | Luồng | Thiếu ở bước | Sprint kế | Quyết định |
|---|---|---|---|---|---|---|---|
| PT01 | Đào đất hố móng đơn | IN | NT (cốt tự nhiên, mở rộng, taluy); KH cao độ đáy móng, cổ móng | T- (thiếu `bottom_level_mm`: bộ đọc không trả, trang không có ô) | S2, S3 | P01/X03 (đầu vào móng), C01 | — |
| PT02 | Đắp đất hố móng đơn | IN | như PT01 + KH tiết diện cổ móng | T- (như PT01) | S2, S3 | như PT01 | — |
| PT03 | Đào/đắp móng băng, đài, bể, đào chung hố | IN [QĐ 5A] | KH | — | S1 (công thức hố không phải hộp), S2; mã `DAO_DAT`/`DAP_DAT` dùng lại được | X01 | QĐ-01/02/03 |
| PT04 | Bê tông lót móng (đơn) | IN | TN dày lót + kích thước (bộ đọc chi tiết) | T- (đọc được thì có, không sửa/nhập trên trang) | S3 | P01/X03 | — |
| PT05 | Nền trệt: đệm cát, bê tông lót nền | IN | TN/NT diện tích + NT lớp | T | — (chưa xác minh thao tác) | J02 | — |
| PT06 | Móng đơn hộp/bậc/vát | IN | TN đếm M… + kích thước chi tiết; nhãn trạng thái sai thành C | T- (không sửa/thêm móng trên trang) | S3; nhãn: Q01 | Q01, P01/X03 | — |
| PT07 | Móng băng | IN [QĐ 5A] | KH | API (tính như hộp; `kind` bị bỏ qua) | S1 (giao băng–băng, sườn), S2, S3; mã `MONG` dùng lại được | X01→X02/X03 | QĐ-01 |
| PT08 | Đài cọc | IN [QĐ 5A] | KH | API một phần: khối bê tông đài nhập như móng hộp ra số | S1 (đài–cọc, đầu cọc ngàm), S2, S3; mã `MONG` dùng được cho bê tông đài | X01 | QĐ-02 |
| PT09 | Cọc BTCT (vật tư cọc; ép/khoan, đập đầu cọc) | IN vật tư; OUT dịch vụ ép/khoan/đập đầu [QĐ-02] | KH | — | S1, S2, S4; vật tư cọc có thể cần dòng vật tư/mã mới (loại `coc_san` đã có) | X01 | QĐ-02 |
| PT10 | Đà kiềng, giằng móng | IN | TN (ĐK… KC) + tiết diện chữ/chi tiết hoặc NT rộng/cao dầm chung | T- (không sửa từng dầm) | S3 | O01, D03, P01 | — |
| PT11 | Cổ cột dưới ±0.000 | IN [QĐ-17] | TN khi có bảng thống kê cột có đoạn cao độ âm; KH khi không có bảng | T- (có bảng: tính; không bảng: không có đường) | S1 (khi thiếu bảng), S2 | X01 | QĐ-17 |
| PT12 | Cột BTCT | IN | TN (tô đặc; bảng cột) + SL/NT cao tầng; người dùng chỉ bỏ/giữ cột | T- (cột nhận sai tiết diện/vị trí hoặc sót cột không sửa/thêm được trên trang; bảng cột không sửa) | S3 | P01, O02 | — |
| PT13 | Dầm BTCT | IN | TN (KC) / SL (suy) | T- (không nhập/sửa dầm trên trang; `beams` không gửi) | S3 | O01, D03, P01 | — |
| PT14 | Giằng tường | IN | TN (GT… KC, chưa gắn tầng) / NT qua API | API (tay) / CT (KC: không trừ xây) | S3; KC: S2 (gắn tầng) | N03, K01–K03, Q01 | — |
| PT15 | Vách BTCT | IN [QĐ 5A] | KH | — | S1, S2, S3; mã: cần quyết định dùng mã có sẵn hay mã mới (cốp pha/thép riêng) | X01 | QĐ-05 |
| PT16 | Lanh tô theo lỗ cửa | IN | TN/NT lỗ cửa + NT cao, gối (hoặc TN cao từ LT…) | T | — (chưa xác minh) | — | — |
| PT17 | Sàn BTCT | IN | SL đường bao / NT diện tích + NT dày | T, nhưng thiếu ô trống vẫn ra như đủ (CT) | Q02 (cờ một phần) | Q02, O03 | — |
| PT18 | Lỗ sàn (lỗ thang, giếng trời) | IN | NT (`void_area_m2`) | T | — | O03 | — |
| PT19 | Thang bản BTCT (bản, chiếu nghỉ, dầm thang) | IN | SL (nét mũi bậc) / NT | T- (một thang/mặt bằng, không có dầm thang) | S3 | Q01, P01, I02 | — |
| PT20 | Bậc thang xây gạch vs bậc bê tông | IN [QĐ 5A] | KH | CT sai: bậc luôn tính bê tông | S1, S2 (trường cấu tạo bậc); mã `XAY` dùng được cho bậc xây | I01 | QĐ-09 |
| PT21 | Tam cấp | IN [QĐ 5A] | KH | — | S1, S2, S3; mã có sẵn (`XAY`, bê tông) dùng được | X01 | QĐ-09 |
| PT22 | Thang cốn, thang xoắn | OUT [QĐ-13] | KH | NS chỉ qua API (trang không có ô `kind`) | — (OUT; chỉ cần hiển thị H5 rõ) | Không triển khai; hiển thị ngoài phạm vi | QĐ-13 |
| PT23 | Mái bằng BTCT | IN | NT qua API | API | S3 | O04, L01 | — |
| PT24 | Mái dốc BTCT | IN [QĐ 5A] | KH | API (tính như mái bằng nếu nhập diện tích nghiêng) | S1 (tiêu chí), S3 | L01 | QĐ-12 |
| PT25 | Mái khung (vì kèo, xà gồ, tôn, ngói) | OUT [QĐ-12] | KH | NS | — (OUT; chỉ cần hiển thị H5 rõ) | Không triển khai; hiển thị ngoài phạm vi | QĐ-12 |
| PT26 | Tường chắn mái, lan can xây | IN [QĐ 5A] | TN tường trên MB sân thượng/mái (chưa xác minh) | CT rủi ro: dùng cao tầng | S2 (cao lan can); mã `XAY`, `TRAT` dùng được | X01 | QĐ-10 |
| PT27 | Sê nô bê tông | IN | TN (SN… KC) / NT qua API | T- (đọc KC không sửa) / API (tay); CT (chữ nhật quy ước) | S3 | K01 | — |
| PT28 | Sê nô xây | IN [QĐ 5A] | KH | — | S1, S2, S3; mã `XAY`, `TRAT`, `CHONG_THAM` dùng được | X01 | QĐ-07 |
| PT29 | Ô văng, mái hắt BTCT | IN [QĐ 5A] | KH | — | S2, S3; công thức khối = dài × rộng × dày như sê nô; định mức cốp pha AF.81150 đã ghi "mái hắt"; mã: chọn dùng lại hay tách | X01 | QĐ-06 |
| PT30 | Bể nước ngầm: kết cấu, xây, chống thấm | IN [QĐ 5A] | KH | — | S1, S2, S3; công tác dùng lại `MONG`/`SAN`/`XAY`/`TRAT`/`CHONG_THAM`/`DAO_DAT` cần quyết định | X01 | QĐ-03 |
| PT31 | Bể phốt/hầm phân: kết cấu, xây, chống thấm | IN [QĐ 5A] | KH | — | như PT30 | X01 | QĐ-04 |
| PT32 | Tường xây gạch | IN | TN cặp nét (sửa, vẽ thêm được) + SL/NT cao tầng + TN/NT vật liệu | T | — (chưa xác minh) | — | — |
| PT33 | Trát tường | IN | như PT32 + NT dày | T | S4 gạch rỗng +10% | J05 | — |
| PT34 | Trát cột, dầm, trần, quét nước xi măng | IN có điều kiện [QĐ-11] | KH | — | S1 (diện tích trát từ cột/dầm/sàn đã có), S4 (định mức); mã `TRAT` dùng được | J04, X01 | QĐ-11 |
| PT35 | Cán nền | IN | SL/NT diện tích + NT dày | T | S4 dày 50 chưa định mức | J04/J05 | — |
| PT36 | Chống thấm WC | IN | SL tên phòng + NT cổ tường, vật liệu | T- (không thêm/sửa nhãn phòng WC trên trang) | S3 | P01 | — |
| PT37 | Chống thấm ban công | IN | NT diện tích | T | — | — | — |
| PT38 | Chống thấm mái, sê nô, ô văng | IN [QĐ 5A] | KH | — | S2 (diện tích + vật liệu cho mái/sê nô), S3; **mã `CHONG_THAM` và định mức CT01–CT03 đã có** | X01 | QĐ-08 |
| PT39 | Cốt thép theo bảng thống kê | IN | TN | T- (đọc, không sửa; `steel_schedule_t` không có ô) | S4 (mất Ø, J03); 2 lỗi xfail | N01, N02, J03 | — |
| PT40 | Cốt thép theo hàm lượng | IN | NT | T | — | — | — |
| PT41 | Dây buộc | IN | hệ số CSV (khoảng, C) | T | S4 theo Ø | J03 | — |
| PT42 | Cốp pha gỗ AF.81 / ván ép | IN | NT loại ván | T gỗ; ván ép trống | S4 | B01, J04/J05 | — |
| PT43 | Bê tông: mác, cách cung cấp, cấp phối lót, phụ gia | IN | NT | T một mác/cách cho cả nhà | S2 (theo cấu kiện), S4 (phụ gia, lót) | J01, J02, J05 | — |
| PT44 | Vữa xây/trát/cán, gạch, hao hụt | IN | NT + danh mục | T; hao hụt tất cả-hoặc-không (CT) | S4 | A01 | — |
| PT45 | Ca máy, nhân công | OUT [QĐ-18] | — | Cảnh báo "chưa tính" | — | — | QĐ-18 |
| PT46 | Điện nước, hoàn thiện (lát, ốp, sơn, bả, trần, cửa, lan can sắt) | OUT [QĐ chung] | — | — | — | — | — |
| PT47 | Biện pháp thi công: dàn giáo, chuẩn bị mặt bằng, vận chuyển trong công trường, bốc xếp/vận chuyển lên cao, vận chuyển đất thải | OUT [QĐ chung] | — | — | — | — | — |
| PT48 | Phí giao vật tư đến công trình theo báo giá | IN cho chỉ tiêu giá (G05), **không phải công tác** | Từ báo giá (DL08) | Chưa có (G05) | Không thêm vào `WORKS`; thuộc dữ liệu giá | G05 | — |

## 2. Chi tiết theo nhóm

Cột "Thiếu/chưa hỗ trợ" mô tả **hành vi hiện tại [HT]** và **hành vi phải có [ĐX]** theo mục 3.

### 2.1 Đất, lót, móng

**PT01–PT02 Đào, đắp hố móng đơn**
- Đầu vào bắt buộc: kích thước lớp dưới móng; dày lót; cao độ đáy móng; cốt đất tự nhiên; mở rộng đáy hố; hệ số taluy; tiết diện cổ móng khi mặt móng thấp hơn cốt tự nhiên. Nguồn chấp nhận: chi tiết móng + mặt cắt địa hình/hồ sơ thiết kế; nhập tay có ghi nguồn.
- Công tác: `DAO_DAT`, `DAP_DAT` (m³), dòng trừ âm phần hố chồng lấn. Vật tư: không có (công tác không mua vật tư).
- Giao trùng: hố chồng lấn trừ một lần khi có vị trí từng khối `foundations.py:200-208`; hố của móng băng/bể/đài chưa có (PT03).
- Thiếu: [HT] thiếu bất kỳ cao độ nào → dòng trống + `missing` (`foundations.py:57-65,165-168`); chưa nhập cả ba thông số đất thì không sinh dòng đào/đắp, chỉ cảnh báo (`foundations.py:126,209-210`) → **dòng biến mất**. [ĐX] vẫn sinh dòng D "chưa có cao độ đất".
- **Luồng [HT, sửa theo review #2]: T-, không đủ luồng.** `pit()` bắt buộc `bottom_level_mm` (`foundations.py:60-63`), nhưng bộ đọc chi tiết móng chỉ trả dài, rộng, cao, dày lót (`structural.py:153-177`) và trang không có ô nhập/sửa móng (chỉ cốt tự nhiên, mở rộng, taluy: `model.ts:179`). Qua trang, đào/đắp luôn ra D (nếu đã nhập ba thông số đất) hoặc không có dòng. Chỉ API JSON cung cấp đủ. Cổ móng (`neck_b/h_mm`) cũng không có đường qua trang.
- Thiếu ở bước: S2 (bộ đọc cao độ đáy, cổ móng) và S3 (ô nhập/sửa móng). Giao việc: bổ sung đầu vào móng trong P01/X03; đọc cao độ đáy từ mặt cắt là việc riêng sau khi có bản vẽ build có ghi cao độ.
- Bằng chứng: `rough/foundations.py:57-79,123-211`; test `test_rough_foundations.py::test_excavation_and_backfill`, `::test_earthworks_need_confirmed_inputs`, `::test_insufficient_elevation`, `::test_negative_backfill_blocked`, `::test_overlapping_pits_counted_once` (đều nhập `bottom_level_mm` trực tiếp, không đi qua bộ đọc hay trang).

**PT03 Đào đắp móng băng, đài, bể, đào chung hố** — IN theo QĐ-01/02/03 đã duyệt. [HT] không có mã. Dự toán thật gộp đào móng + hầm phân + bể nước ngầm vào một dòng (`banve1_nha_pho_di_an.csv` stt 2) → mẫu số phải ghi rõ dòng đáp án này chứa phần hệ thống chưa hỗ trợ (xem 3.1 luật 4).

**PT04 Bê tông lót móng**: [HT] `foundations.py:147-151` = n × dài × rộng lớp dưới × dày lót; vật tư qua `lean_concrete_grade` + `concrete_supply` (`materials.py:305-306`). Cấp phối lót chưa chọn được đá 1×2/4×6 (J02). Thiếu dày lót: **không sinh dòng** (điều kiện `if f.lean_thickness_mm is not None`) → [ĐX] sinh dòng D. Luồng T-: dày lót chỉ có khi bộ đọc lấy được (`structural.py:172-175`), trang không sửa/nhập được.

**PT05 Nền trệt**: [HT] `areas.py:231-238`: chưa nhập lớp nền → hai dòng D `NEN_DEM_CAT`, `BE_TONG_LOT` "cấu tạo nền"; có lớp → diện tích sử dụng × dày. Giao trùng: lót nền và lót móng cùng mã `BE_TONG_LOT`, phân biệt bằng `plan`/`element`. Test: `test_rough_areas.py` (trường hợp tầng trệt). Đắp/tôn nền ngoài đệm cát: chưa có mã (gộp IN theo QĐ-01 đã duyệt nếu cần).

**PT06 Móng đơn**
- Nhận: [HT] đếm theo ký hiệu M… trên MB móng, kích thước từ mặt cắt chi tiết (`structural.py:515-521`), nối vào `params.foundations` khi người dùng chưa nhập (`takeoff.py:492-493`).
- Tính: `foundations.py:137-160` khối hộp/bậc/vát, cốp pha thành đứng (mặt vát không tính).
- Vật tư: bê tông theo mác chung; cốp pha `GO_MONG`; thép theo hàm lượng `MONG` hoặc bảng thép.
- Giao trùng: móng nhập hai lần cùng tên bỏ dòng sau (`foundations.py:131-133`); đà kiềng xuyên qua móng không tính trùng (`test_tie_beam_through_footing_not_double_counted`).
- Thiếu: kích thước → `MONG` trống + cảnh báo chưa tính cốp pha (`foundations.py:143-158`).
- **Lệch [HT]**: mọi dòng móng gắn `source="manual"` (`foundations.py:143`) và `status.py:100-101` luôn cho C, trong khi docstring `status.py:13` ghi "đọc bản vẽ kết cấu: A". Móng đọc từ KC bị báo là nhập tay: sai cả nhãn độ tin cậy lẫn cách tạo dữ liệu (`source`). Sprint Q01.
- Trang: [HT] chỉ hiện số loại móng đọc được (`Rough.tsx:72`), không có ô sửa kích thước/thêm móng tay → nhập tay móng chỉ qua API JSON. Sprint P01/X03.
- Test: `test_rough_foundations.py::test_stepped_and_sloped_tiers`, `::test_footing_without_detail_stays_blank`, `::test_duplicate_footing_counted_once`; ma trận CSV dòng "Móng đơn" = conditional, không có test tham chiếu.

**PT07 Móng băng** — IN theo QĐ-01 đã duyệt.
- [HT] `models.py:94` có `kind: "don" | "bang"`, docstring `foundations.py:5-6` mô tả móng băng = hộp với dài đã trừ giao. Nhưng **không chỗ nào đọc `kind`** (grep `src/`, `tests/`, `frontend/`: chỉ khai báo) và không có test. Kết luận: nhập JSON một "móng" dài × rộng × cao vẫn ra số, song không trừ giao băng–băng, không có cốp pha băng giật cấp, không có đào băng (PT03), trang không có ô nhập.
- Ma trận CSV ghi "Móng băng, móng cọc: not_supported" — đúng về nghiệp vụ; lệch với mô tả docstring. [ĐX] giữ not_supported tới khi X01 chốt; ghi chú trong CSV rằng `kind` chưa dùng.
- Đầu vào cần: tim băng theo trục, tiết diện (bản + sườn/dầm móng), giao nhau, cao độ, lót; nguồn: MB móng + mặt cắt băng.
- Giao dễ trùng: băng–băng tại nút; băng–đà kiềng; dầm móng (sườn) với `DAM`; cổ cột.

**PT08–PT09 Đài cọc, cọc** — IN theo QĐ-02 đã duyệt. [HT, sửa theo review #5] Bê tông, cốp pha, lót của **đài** tính được một phần bằng công thức khối `FoundationItem` + mã `MONG` đã có (nhập qua API); phần thiếu là dạng cấu kiện (S1: liên kết đài–cọc, phần đầu cọc ngàm vào đài, đào hố đài) và đầu vào trang (S3). Không cần mã công tác mới cho bê tông đài. **Cọc** chưa có gì: vật tư cọc (loại `coc_san`) chưa có đường sinh (S1, S2, S4; có thể cần dòng vật tư/mã mới — quyết định ở X01). Ép/khoan, đập đầu cọc: công tác/dịch vụ thi công OUT theo QĐ-02 đã duyệt; vật tư cọc vẫn IN. Bộ 46 có "ép trước cọc BTCT 25×25" (m) và "đập đầu cọc" (cọc) đang để trống mã (`46_nha_tan_binh.csv` dòng 1, 4). `RAW_CLASSES` đã có loại `coc_san` (`models.py` mục RAW_CLASSES) nhưng không công tác nào sinh. Ranh giới [QĐ chung]: chỉ bóc theo thiết kế, không suy chiều dài/sức chịu tải.

**PT10 Đà kiềng/giằng móng**: [HT] đọc ký hiệu ĐK… như dầm trên MB kết cấu, nhận bằng `is_tie_beam`, ra công tác `DAM` (không có mã riêng), không trừ đáy sàn (`takeoff.py:422-423`). Test `test_rough_structural.py::test_read_structural_beams_and_foundations`.

**PT11 Cổ cột dưới ±0.000** — [QĐ-17] trong phạm vi, đã duyệt. [HT, sửa theo review #3]
- **Có bảng thống kê cột**: `read_column_schedule()` nhận cả đoạn cao độ âm (`structural.py:210-251`, `ColumnSpan.z_from_mm/z_to_mm`); `schedule_column_works()` tính bê tông + cốp pha theo `z_to − z_from` của từng đoạn, không loại đoạn âm (`columns.py:260-266`) → cổ cột **được tính** nếu bảng có đoạn đó. Có bảng thì cột kiến trúc không tính bê tông (`takeoff.py:238-239`).
- **Không có bảng**: cột tính theo chiều cao tầng của mặt bằng kiến trúc (`columns.column_works`); `neck_b/h_mm` chỉ dùng trừ đất đắp (`foundations.py:173-180`) → chưa có đường tính cổ cột (S1: công thức từ mặt móng tới cốt nền; S2: tiết diện cổ không đọc được, trang không có ô).
- Sprint mới **phải tránh cộng thêm cổ cột đã nằm trong bảng cột** (chỉ sinh cổ cột khi không có `column_schedule` hoặc bảng không có đoạn âm của cột đó). Mã `COT` dùng được; không cần mã mới.

### 2.2 Khung bê tông

**PT12 Cột**: [HT] tô đặc trên MB kiến trúc (A) hoặc bảng thống kê cột (A, thắng, `takeoff.py:238-239`); chiều cao theo tầng (B/C). Luồng T- [sửa theo review vòng 2]: trang chỉ bỏ/giữ cột (`Review.tsx:248-250`, `Board.tsx:138-142` bấm để bỏ/giữ); `roughRequest` gửi nguyên `x, y, b_mm, h_mm` đã nhận (`model.ts:231-250`) → cột nhận sai kích thước/vị trí hoặc cột bị sót không sửa/thêm được trên trang (P01; không làm ở M01). Test theo CSV: `test_rough_columns.py::test_detect_columns_from_solid_fills`, `::test_manual_and_removed_columns`. Giao trùng: trừ khối xây tại cột (`column_overlaps`), trừ cốp pha sàn tại đỉnh cột (`_slab_form_deduction`, gắn sai tầng — O02).

**PT13 Dầm**: [HT] KC (A) / nhập tay (C) / suy từ tường+cột (B). Có dầm KC ở bất kỳ tầng nào thì tắt suy dầm cả nhà (`takeoff.py:229`) → tầng thiếu MB dầm mất dầm (O01). Một MB dầm dùng nhiều tầng nhân hệ số (`takeoff.py:273-276`). Bộ 46 lệch ~30% (D03). Luồng T-: trang không gửi `PlanInput.beams` (grep `do-boc/*.ts*`: chỉ `structural_beams` chuyển nguyên) → không sửa/xóa/thêm dầm; tiết diện chỉ sửa được qua rộng/cao dầm chung (thông số C cho mọi dầm).

**PT14 Giằng tường**
- Nhập tay vào `PlanInput.members` → khối lượng + trừ khối xây (`secondary.py:59-117`); test `test_tie_deducted_from_masonry`, `test_tie_without_depth_left_blank`; lỗi xfail trừ hai lần khi hai giằng chồng (`test_rough_secondary.py:70`, N03). Trang không có ô nhập giằng → **API**.
- Đọc KC (GT…): tính ở mặt bằng "bản vẽ kết cấu" (`takeoff.py:280`), không trừ xây (`secondary.py:226-228`). Nhập thêm tay cùng giằng → **tính hai lần** (K03).
- **Lệch [HT]**: `linear_works` không truyền `source` (`secondary.py:72`) → `WorkItem.source="auto"`, `status.py:104-105` gắn C với chữ "(nhập tay)" cho cả giằng/sê nô đọc từ KC. Sprint Q01/K01.

**PT15 Vách BTCT** — IN theo QĐ-05 đã duyệt. [HT] không có dạng cấu kiện, ký hiệu, đầu vào hay dòng ma trận → vách trên bản vẽ (nếu nhận thành tường) có thể bị tính thành **tường xây** hoặc biến mất. Chưa kiểm trên bản vẽ build. Thiếu ở bước: S1, S2, S3. Mã: công thức khối (dài × cao × dày) đơn giản, nhưng cốp pha hai mặt, định mức ván khuôn tường và hàm lượng thép cần khóa cấu kiện riêng (`STEEL_ELEMENTS`, `GO_*`) → quyết định dùng mã có sẵn hay mã mới thuộc X01, không mặc định.

**PT16 Lanh tô**: [HT] `walls.py:65-123` theo lỗ cửa: Σ (rộng + 2 gối) × dày tường × cao lanh tô; L1 bỏ lanh tô khi cửa sát đáy dầm (`secondary.py:120-152`). Thiếu cao/gối: dòng D + cảnh báo khối xây chưa trừ lanh tô (`walls.py:103,116`). Phụ thuộc chiều cao cửa (bộ 46 không có → để trống, README du_toan). Dòng dự toán bộ 46 "lanh tô, mái hắt, máng nước, tấm đan, ô văng" gộp cả PT29 → ánh xạ 1 dòng đáp án : nhiều hạng mục (3.1 luật 4).

**PT17–PT18 Sàn, lỗ sàn**
- [HT] `areas.py:211-225`: sàn = (diện tích trong tim tường bao − ô trống) × dày; không tính tầng trệt; tường bao hở → bao lồi + cảnh báo.
- **Lệch nguyên tắc [HT]**: `void_area_m2` trống → cảnh báo nhưng công tác sàn vẫn có số và không có `missing` (`areas.py:213-222`) → trạng thái không xuống D, tổng sàn hiện như đủ. Cùng lỗi với cốp pha sàn. Sprint Q02/O03.
- Không được suy lỗ thang từ rộng vế/chiếu nghỉ ([QĐ] kế hoạch mục C). [HT] mã hiện không suy (đúng).
- Trang có ô "Ô trống trên sàn" (`model.ts:189`). Giao trùng: thang–sàn (O03), mái–sàn (`drop_slab_under_roof`, `secondary.py:174-180`), đáy dầm/cột (`_slab_form_deduction`).

**PT19 Thang bản**
- Nhập tay: `stairs.py:140-179` (bản nghiêng, bậc, chiếu nghỉ, dầm thang); test `test_rough_stairs.py::test_two_flight_stair`, `::test_stair_missing_inputs`, `test_rough_secondary.py::test_stair_legacy_dimensions_not_summed` (05/11: thang kiểu cũ không tự cộng).
- Tự nhận: `detect_stairs`/`building_stairs` (`stairs.py:90-137`) **được gọi** trong `rough_from_drawing` (`takeoff.py:456`); test `test_rough_stairs_detect.py` (3 bài). → **Ma trận CSV lệch**: dòng "Cầu thang, Tự nhận trên bản vẽ, not_supported". CLAUDE.md cũng ghi "thang (nhập tay)". [ĐX] đổi CSV sang conditional **sau** review S13i/Q01.
- **Lệch [HT]**: thang auto gắn B (`status.py:103`) dù dày bản luôn là thông số C (`stairs.py:142`) → Q01.
- Trang: chỉ giữ thang đầu tiên mỗi mặt bằng (`model.ts:195` `st0`), không có ô dày-bản-riêng/dầm thang/`kind` → P01.
- Thiếu: số bậc/rộng vế/rộng bậc/dày bản → `CAU_THANG`, `COP_PHA` trống + `missing` (`stairs.py:144-157`).

**PT20–PT21 Bậc xây vs bậc bê tông, tam cấp** — IN theo QĐ-09 đã duyệt. [HT] bậc luôn cộng vào bê tông cầu thang (`stairs.py:165,170`) → thang bản + bậc xây gạch sẽ ra thừa bê tông, thiếu gạch. Bộ 46 có dòng "Xây các bộ phận kết cấu phức tạp khác gạch thẻ" (không gắn mã) — khả năng là bậc/tam cấp, **chưa xác minh**. Tam cấp: không có mã.

**PT22 Thang cốn/xoắn** [QĐ-13: OUT, H5]: [HT] `kind != "ban"` → dòng `CAU_THANG` trống, `basis="not_supported"`, không sinh vật tư (`stairs.py:148-151`, `materials.py:287-288`); test `test_stair_con_not_supported`. Trang không có ô chọn `kind` → người dùng trang không khai báo được thang cốn: thang cốn trên bản vẽ sẽ bị nhận/nhập như thang bản. [QĐ-13] ngoài phạm vi đồ án (H5); không triển khai công thức, cần ghi rõ giới hạn trong đầu ra.

### 2.3 Mái, sê nô, ô văng, tường mái

**PT23–PT25 Mái**: [HT] `secondary.py:155-180`: bê tông = diện tích × dày, cốp pha = diện tích; `replaces_slab_of` bỏ sàn của mặt bằng đó; mái khung → dòng NS + cảnh báo. Bản vẽ mái chỉ nhận loại theo tiêu đề (`secondary.py:229-235`). `RoofItem` không có trên trang (grep `frontend/src`: không có `roofs`) → **API**. Mái dốc BTCT: nhập diện tích nghiêng thì công thức vẫn dùng được, nhưng chưa có ca/tiêu chí → IN theo QĐ-12 đã duyệt, chờ triển khai; mái khung OUT theo cùng quyết định. Thiếu dày: `MAI` trống, cốp pha vẫn có số (`secondary.py:163-170`) → "một phần".

**PT26 Tường chắn mái, lan can xây** — IN theo QĐ-10 đã duyệt. [HT chưa kiểm trên bản vẽ] tường trên mặt bằng sân thượng/mái nếu được tách thành mặt bằng và có chiều cao sẽ tính xây với **chiều cao tầng**, không có thông số cao lan can → rủi ro thừa khối lượng. `building_stairs` đã bỏ thang ở sân thượng/mái (`stairs.py:126`) chứng tỏ các mặt bằng này có trong danh sách.

**PT27 Sê nô bê tông**: [HT] KC SN… hoặc nhập tay; tiết diện chữ nhật + cảnh báo chữ U (`secondary.py:59-81`); test `test_gutter_rectangular_with_warning`. Cùng lỗi nhãn C "(nhập tay)" như PT14.
**PT28 Sê nô xây**, **PT29 Ô văng/mái hắt** — IN theo QĐ-07, QĐ-06 đã duyệt. [HT] không có dạng cấu kiện/đầu vào → biến mất. Mã có sẵn chứa được: sê nô xây = `XAY` + `TRAT` + `CHONG_THAM` (thiếu S1 hình học thành sê nô, S2 đầu vào); ô văng = khối dài × rộng × dày như `SE_NO`/`LANH_TO`, định mức cốp pha `GO_LANH_TO`/`GO_SE_NO` (AF.81150) đã ghi "lanh tô liền mái hắt, máng nước" (thiếu S2 danh sách ô văng, S3 nối luồng). Tách mã riêng chỉ khi cần báo cáo riêng ô văng — quyết định tại X01.

### 2.4 Bể (chỉ kết cấu, xây, chống thấm)

**PT30 Bể nước ngầm, PT31 Bể phốt** — IN theo QĐ-03/04 đã duyệt. [HT] không có dạng cấu kiện bể; các phần của bể (đào, lót, đáy, thành BTCT hoặc xây, nắp, trát, chống thấm) có thể đi qua mã có sẵn `DAO_DAT`, `BE_TONG_LOT`, `MONG`/`SAN`, `XAY`, `TRAT`, `CHONG_THAM`; thiếu S1 (dạng bể và phép trừ giao), S2, S3. Mã mới chỉ khi báo cáo cần tách bể khỏi nhà — quyết định tại X01. Bộ 46 có "Xây tường gạch ống … BNN" và "Trát tường trong … BNN" để trống mã; README du_toan ghi trống = "không phải bộ phận nhà (dòng BNN)". [HT] Cách phân loại OUT cũ trong README không còn phù hợp quyết định mới → phải phân loại IN theo QĐ-03/04 đã duyệt (D01/D02). Thiết bị, ống, bơm luôn OUT [QĐ chung].
Đầu vào cần: kích thước trong/ngoài, dày đáy/thành/nắp, cấu tạo thành (BTCT hay xây), lót, chống thấm, cao độ; nguồn: chi tiết bể.
Giao trùng: đào chung hố với móng; lót bể với lót móng; nắp bể với sàn trệt/nền.

### 2.5 Tường, trát, nền, chống thấm

**PT32 Tường xây**: [HT] `walls.py:41-123`; trừ cửa, lanh tô, cột, dầm, giằng; thiếu phương án tường → `XAY` trống. Test theo CSV: `test_rough_walls.py::test_full_params`, `::test_missing_params_warn_not_guess`.
**PT33 Trát tường**: [HT] chỉ mặt tường xây (`walls.py:106-109`); trát gạch rỗng +10% chưa áp (J05).
**PT34 Trát cột, dầm, trần; quét nước xi măng** — IN có điều kiện theo QĐ-11 đã duyệt. (Lịch sử: kế hoạch ghi "trát trong phạm vi đã có", vòng 1 hiểu là chỉ trát tường.) Theo QĐ-11, trát cột/dầm/trần IN; quét nước xi măng chỉ IN khi là lớp cấu tạo cần thiết được xác định. [HT] chưa có công thức/định mức (S1, S4). Cả hai dự toán đều có các dòng này (để trống mã).
**PT35 Cán nền**: [HT] `areas.py:227-230`; định mức dày 50 trống (`dinh_muc_phan_tho.csv` dòng CAN_NEN,50).
**PT36–PT37 Chống thấm WC, ban công**: [HT] `areas.py:239-255`; WC theo tên phòng (`room_rules.csv`) → B; cổ tường, vật liệu → C; ban công nhập diện tích; tên phòng WC nằm ngoài phòng khép kín → cảnh báo, **không có dòng** (biến mất). Luồng WC: T- — nhãn phòng chuyển nguyên từ bản vẽ (`model.ts` gửi `labels: p.labels`), trang không thêm/sửa được phòng WC.
**PT38 Chống thấm mái, sê nô, ô văng** — IN theo QĐ-08 đã duyệt. [HT, sửa theo review #5] **Mã `CHONG_THAM` và định mức CT01–CT03 đã có** (`materials.py` nhánh CHONG_THAM, `dinh_muc_phan_tho.csv`); thiếu đối tượng/đầu vào sinh công tác cho mái, sê nô, ô văng (S2: diện tích + vật liệu; `RoofItem` không có trường chống thấm) và nối luồng (S3). Không cần mã mới. **Lệch đáp án**: `banve1_nha_pho_di_an.csv` gắn mã `CHONG_THAM` cho dòng "Quét flinkote chống thấm mái, sê nô, ô văng" trong khi `CHONG_THAM` của hệ thống là WC/ban công → so sai đối tượng (D02).

### 2.6 Vật tư

| Mã | Hiện trạng [HT] | Hở / sprint |
|---|---|---|
| PT39 Thép bảng thống kê | `rebar.py` đọc bảng TEXT/MTEXT, A; vật tư một dòng `STEEL_NAME` (tấn), không giữ Ø (`materials.py:307-311`) | 2 xfail `test_rough_rebar.py:47,52` (N01, N02); Ø → J03; ACAD_TABLE not_supported |
| PT40 Thép hàm lượng | C; kế thừa trạng thái cấu kiện (`status.py:123-133`) | — |
| PT41 Dây buộc | TH10 khoảng 7,85–16,07 kg/tấn, `tinh` (C) | theo Ø: J03 |
| PT42 Cốp pha | `formwork_type` bắt buộc; gỗ AF.81 theo 9 cấu kiện; ván ép trống (`dinh_muc_phan_tho.csv` COP_PHA,VAN_EP) | B01, J04/J05 |
| PT43 Bê tông | một `concrete_grade` + `concrete_supply` cho mọi cấu kiện (`models.py:121-123`); trộn tại chỗ M100–M400 có cấp phối TT 38; M350/M400 bảng ghi phụ gia nhưng chưa có dòng phụ gia | J01, J02, J05 |
| PT44 Vữa, gạch, hao hụt | gạch theo `wall_systems`; vữa theo quan hệ COMPOSED_OF; hao hụt chỉ đúng khi mọi phần góp cùng loại (`materials.py:268-273`) | A01 |

## 3. Định nghĩa phần thiếu và mức hoàn tất [ĐX]

### 3.1 Sáu trạng thái hoàn tất của một hạng mục mong đợi

Đơn vị: một **dòng hạng mục mong đợi** = (hồ sơ, tầng/vị trí, mã PTxx, công tác) có trong đáp án đã khóa hoặc sổ hạng mục của hồ sơ.

| Mã | Tên | Điều kiện | Thể hiện bắt buộc trên API, trang, BOQ |
|---|---|---|---|
| H1 | Có, tính đủ | Mọi phần có số; không còn `missing`; mọi phép trừ giao nhau đã áp; nguồn + quy tắc được người kiểm xác nhận | Số + trạng thái A/B/C + nguồn |
| H2 | Có, tính một phần | Có phần đã biết nhưng còn phần D hoặc phép trừ chưa áp được (vd. sàn chưa trừ ô trống chưa nhập; mái có cốp pha nhưng thiếu bê tông) | Hiện "phần đã biết", gắn nhãn **một phần**, không cộng vào tổng như tổng đủ |
| H3 | Có, thiếu đầu vào | Hạng mục được hỗ trợ nhưng thiếu số → không ra số | Dòng trống (D) + danh sách đầu vào thiếu |
| H4 | Có, hệ thống chưa hỗ trợ | Trong phạm vi (IN theo 5A), chưa có công thức/luồng. Mái khung, thang cốn/xoắn **không** là H4 mà là H5 | Dòng "chưa hỗ trợ" + mã PTxx + lý do; không số; không vật tư |
| H5 | Ngoài phạm vi đã duyệt | Có mã quyết định QĐ-xx ký trước khi chạy đánh giá | Liệt kê ở mục "ngoài phạm vi" kèm mã quyết định; không vào mẫu số |
| H6 | Chưa xác định có hay không | Hồ sơ thiếu loại bản vẽ cần để biết (vd. không có MB móng, không có chi tiết bể) và chưa ai xác nhận | Dòng "chưa xác định" + loại bản vẽ thiếu; không số |

Thêm trạng thái ngoài mẫu số: **H0 Không có (đã xác nhận)** — người kiểm ghi rõ hồ sơ không có hạng mục, có căn cứ (vd. "nhà không có tầng hầm, MB móng KC-01 không có bể"). Chỉ H0 được hiện số 0 hoặc bỏ dòng.

Luật:
1. Không phát hiện ≠ không có. Hệ thống không thấy → H6 (hoặc H4 nếu chưa hỗ trợ), không bao giờ H0.
2. Không sinh khối lượng 0 cho hạng mục chưa xác định. [HT] `_work` kẹp số âm về 0 (`walls.py:30`); dòng trừ âm đi qua `_neg` — giữ nguyên, nhưng không dùng 0 thay "chưa có".
3. Không suy diện tích lỗ thang từ rộng vế/chiếu nghỉ; thiếu → sàn ở H2, không phải H1.
4. Một dòng đáp án gộp nhiều hạng mục (vd. bê tông lanh tô + ô văng) chỉ đạt H1 khi **mọi** hạng mục con đạt H1.

### 3.2 Hiện trạng ánh xạ sang sáu trạng thái [HT]

| Trạng thái | Mã hiện có | Hở |
|---|---|---|
| H1 | `quantity` có số, `missing` rỗng | Sàn thiếu ô trống vẫn rơi vào đây (`areas.py:213-222`) |
| H2 | `WorkTotal.complete=False` ở tổng (`takeoff.py:322-325`), `MaterialLine.complete=False` | Từng công tác không có cờ "một phần"; tổng vẫn hiện số phần biết (Q02) |
| H3 | `quantity=None` + `missing` → D (`status.py:116-118`) | Một số trường hợp không sinh dòng: lót móng thiếu dày, đào đắp khi chưa nhập cả ba thông số đất, WC ngoài phòng kín |
| H4 | `basis="not_supported"`: chỉ thang cốn/xoắn, mái khung — theo 5A hai dạng này là H5 (OUT), nên dòng NS hiện có cần trình bày là "ngoài phạm vi" (P02/X03) | Cọc, vách, ô văng, sê nô xây, bể, chống thấm mái/sê nô, tam cấp, trát cột/dầm/trần, cổ cột khi không có bảng cột **không có dòng nào**; móng băng, đài chỉ ra số khi người dùng tự nhập như móng hộp qua API (không có dòng báo phần chưa hỗ trợ); bậc xây ra **sai** thành bê tông → vi phạm chỉ tiêu "Không mất phần thiếu" |
| H5 | Nhóm vật liệu ngoài phạm vi liệt kê `in_scope=False` (`takeoff.py:380`) | Không có danh sách hạng mục ngoài phạm vi theo quyết định |
| H6 | Cảnh báo chung "Chưa có loại bản vẽ…" (`takeoff.py:184-187`), gợi ý `FOUND_HINT` | Không gắn được với hạng mục cụ thể |
| H0 | — | Không có |

BOQ đã có sheet "Phạm vi hỗ trợ" in nguyên `ho_tro_cau_kien.csv` (`boq.py:91`) — đây là ma trận năng lực, **không** phải danh sách hạng mục của hồ sơ đang bóc. [ĐX] cần một danh sách "hạng mục chưa bóc" theo hồ sơ (mục 6).

## 4. Cách đo các chỉ tiêu [các điểm ở 5B đã chốt; phần còn lại là đề xuất dùng cho V01]

### 4.1 Nguyên tắc chung (áp cho mọi chỉ tiêu)

- **Khóa trước khi chạy**: đáp án công tác, đáp án vật tư, sổ hạng mục, danh sách H5 (mã QĐ) và phiên bản quy tắc được ghi hash trước lần chạy tính chỉ tiêu. Đổi sau khi thấy kết quả → phiên bản mới, báo cả hai số.
- **Mẫu số đến từ đáp án, không từ đầu ra hệ thống.** Hệ thống tách một dòng đáp án thành nhiều dòng không làm tăng mẫu số; ánh xạ nhiều dòng hệ thống → một dòng đáp án; dòng đáp án đạt khi tổng các phần ánh xạ đạt.
- Dòng đáp án hệ thống không ánh xạ được → không đạt, liệt kê. Dòng hệ thống không có trong đáp án → báo riêng ("thừa"), không cộng vào tử số.
- **Chỉ ACTUAL, split test** cho số công bố. Build: báo cáo phát triển, ghi rõ "build". SAMPLE/SYNTHETIC: chỉ kiểm script tính (fixture), không vào bảng chỉ tiêu.
- **Gộp**: số chính = gộp mọi dòng của mọi hồ sơ test (micro); kèm từng hồ sơ, trung bình theo hồ sơ và hồ sơ thấp nhất, luôn có mẫu số (QĐ-15). Trung bình theo hồ sơ không thay số micro.
- **Không cộng các chỉ tiêu thành một số.** Mỗi chỉ tiêu một bảng; bao phủ, tự động hóa và độ chính xác báo riêng.
- **Hai trục báo riêng, không suy trục này từ trục kia** (sửa theo review #1):
  - *Độ tin cậy* A/B/C/D = trạng thái yếu nhất của mọi đầu vào (`status.py`). Dùng cho K5 (bảng A/B và bảng C) và để cảnh báo; **không** dùng để nói dòng được tự nhận hay nhập tay.
  - *Cách tạo dữ liệu* ghi theo **từng đầu vào bắt buộc** của dòng đáp án, chia theo vai trò: (i) hình học/số lượng (dài, diện tích, số khối, số bậc), (ii) tiết diện/chiều dày, (iii) thông số thiết kế (mác, cấu tạo, loại vật liệu), (iv) hệ số định mức. Mỗi đầu vào: tự nhận / suy luận / nhập tay hoặc sửa tay / thiếu.
  - Báo cáo: với mỗi vai trò, số dòng đạt K1 có đầu vào vai trò đó tự nhận, suy, nhập tay. **Không** tính một "tỷ lệ tự động" chung và **không** dùng công thức "tự động = A + B".
  - [HT] Hệ thống mới ghi cách tạo dữ liệu ở một số đầu vào: `ReviewWall.src/edited`, `Column.source`, `Stair.source` (trang đổi auto → manual khi người dùng sửa, `model.ts:225-229`), `Beam.source`, `WorkItem.source`; `WorkItem.inputs` chỉ ghi độ tin cậy dạng chữ. Giá trị trong `ProjectParams` **không** luôn là nhập tay; nguồn thực tế theo cách tạo giá trị (sửa theo review vòng 2): (a) biểu mẫu trang (`roughValues` → `projectParams`, `model.ts:205-217`) hoặc JSON API/file thông số (`compare_estimate.py`, `batch_takeoff --params`): nhập tay/từ file; (b) `structural_parts()` điền `foundations` từ bộ đọc kết cấu khi chưa có (`takeoff.py:492-493`) và `lintel_height_mm` từ chữ LT… khi chưa nhập và chỉ có một giá trị (`takeoff.py:482-485`): tự nhận; trên trang, `roughRequest` gán `foundations` đọc được và `lintel_height_mm` khi ô trống (`model.ts:236-239`); (c) `compute_rough` dùng cao dầm duy nhất của dầm đã có để trừ tường khi `beam_depth_mm` trống (`takeoff.py:234-236`): suy luận, không ghi lại vào params. Nhãn độ tin cậy hiện gắn C cho mọi giá trị params (`status.py` `_param`) bất kể cách tạo — không suy cách tạo từ tên model hay nhãn C. Đến khi có trường riêng (mục 9), người kiểm ghi cách tạo dữ liệu vào đáp án/phiếu nghiệm thu.

### 4.2 Bảng định nghĩa

| Chỉ tiêu | Đơn vị | Mẫu số | Tử số (điều kiện đạt) | Thiếu (H2/H3/H6) | Chưa hỗ trợ (H4) | Ngoài phạm vi (H5) / H0 |
|---|---|---|---|---|---|---|
| K1 Hoàn tất công tác | dòng công tác đáp án | Mọi dòng IN (QĐ chung + 5A) | H1: số hoàn chỉnh, có nguồn, quy tắc được người kiểm xác nhận. Nhập tay có nguồn đạt (mang C). Chỉ có cảnh báo không đạt | Ở mẫu số, không đạt | Ở mẫu số, không đạt | Loại khỏi mẫu số, liệt kê kèm mã QĐ |
| K2 Đủ quy cách vật tư | dòng vật tư cần mua trong đáp án | Mọi dòng vật tư thuộc công tác IN | Đúng mã/loại + quy cách (mác, Ø, cỡ gạch, loại ván) + đơn vị + lượng hoàn chỉnh (`complete=True`; hao hụt đã biết hoặc đã gồm trong định mức) | Không đạt | Không đạt | Loại, liệt kê |
| K3 Có giá sử dụng được | như K2 | như K2 | Đạt K2 **và** có giá ACTUAL còn hiệu lực ở ngày đánh giá, đúng quy cách, đơn vị (không tự đổi), địa bàn, mức lượng áp dụng. Giá dự đoán, SAMPLE, hết hạn: không đạt. BULLETIN: không tính K3, báo riêng theo QĐ-14 | Không đạt | Không đạt | Loại |
| K4 Có giá để so | như K2 | như K2 | Đạt K3 với ≥ 2 nhà cung cấp độc lập cùng điều kiện (VAT, giao hàng). Báo kèm số NCC | Không đạt | Không đạt | Loại |
| K5 Sai số khối lượng | nhóm cấu kiện × công tác × hồ sơ | Dòng ACTUAL–test có cả số hệ thống lẫn đáp án độc lập, cùng phạm vi/đơn vị | \|hệ thống − đáp án\| / đáp án ≤ 10% | Không vào phép chia; đếm riêng "không tính được" | Như thiếu | Loại |
| K6 Không mất phần thiếu | dòng hạng mục mong đợi không đạt H1 | Mọi dòng H2, H3, H4, H6 (theo đáp án + sổ hạng mục) | Có dòng hiện trên API **và** BOQ, đúng trạng thái, có lý do | (thuộc mẫu số) | (thuộc mẫu số) | Không thuộc |
| K7 Nhất quán | cặp (đại lượng, đơn vị) giữa API–trang–BOQ | Mọi tổng công tác, dòng vật tư, tổng nhóm của một yêu cầu | Chênh ≤ một đơn vị làm tròn cuối; không cộng khác đơn vị | — | — | — |

Ghi chú:
- K1 không đòi sai số ≤ 10% (đó là K5). Một dòng có thể đạt K1 mà sai K5.
- K5 báo A/B và C thành hai bảng; D không có số nên chỉ đếm.
- Công tác không sinh vật tư (đào, đắp) không có dòng K2–K4 (QĐ-16). Ép/khoan/đập đầu cọc là OUT (QĐ-02), không thuộc K1.
- Nhập qua JSON API không có trên trang: theo QĐ-19, tính K1 nếu lưu giá trị, nguồn và người xác nhận; báo riêng hạn chế luồng giao diện.

### 4.3 Chặn tăng tỷ lệ giả

1. Danh sách H5 chỉ thêm được bằng mã QĐ có ngày trước lần chạy; dòng loại sau khi thấy kết quả bị đưa lại mẫu số.
2. Hạng mục khó IN theo 5A (móng băng, bể, vách…) luôn ở mẫu số; chưa làm được thì là H4, không chuyển sang H5.
3. Tách nhỏ dòng hệ thống không đổi mẫu số (4.1). Tách nhỏ dòng đáp án sau khóa = phiên bản đáp án mới.
4. Thiếu giá không bao giờ đạt K3; giá MẪU/dự đoán không đạt.
5. Không đổi tử số bằng cách giảm điều kiện xác nhận người kiểm.

### 4.4 Ví dụ kiểm cách tính (số nhỏ, giả định, không phải dữ liệu thật)

**Ví dụ 1 – Hồ sơ có đủ, thiếu, chưa hỗ trợ.** Đáp án hồ sơ X: 10 dòng công tác IN.
- 6 dòng H1: tường tầng 1, tường tầng 2, cột tầng 1, sàn tầng 3, móng M1, thép móng.
- 1 dòng H2: sàn tầng 2 chưa nhập ô trống.
- 2 dòng H3: thang thiếu dày bản; lanh tô thiếu cao lanh tô.
- 1 dòng H4: vách BTCT.
- K1 = 6/10 = **60%**.
- Cách tạo dữ liệu, vai trò (i) hình học/số lượng của 6 dòng đạt: tự nhận 3 (tường T1, tường T2, cột T1), suy 1 (đường bao sàn T3), nhập tay 2 (kích thước móng M1, tấn thép móng). Các vai trò (ii)–(iv) ghi tương tự theo phiếu; không gộp thành một tỷ lệ tự động.
- Độ tin cậy cùng 6 dòng (giả định): A 0; B 2 (hai dòng tường: cao tầng suy từ cao độ, không nhập cao dầm); C 4 (cột và sàn vì dày sàn là thông số C; móng; thép nhập tay). Nếu dùng sai công thức "tự động = A + B" sẽ ra 2/10, trong khi 4 dòng có hình học tự nhận/suy — đây là lý do bỏ công thức đó.
- K6 mẫu số = 4 dòng không đạt. Hiện trạng mã: sàn H2 hiện như H1 (không có cờ), vách không có dòng → chỉ 2 dòng H3 hiện đúng → K6 = **2/4 = 50%** (mục tiêu 100%).

**Ví dụ 2 – Dòng ngoài phạm vi được xác nhận.** Đáp án hồ sơ Y: 12 dòng.
- 2 dòng mái khung/thang xoắn, có QĐ-12/13 = OUT duyệt trước lần chạy → H5, mẫu số còn 10.
- 1 dòng vách BTCT: IN theo QĐ-05, hệ thống chưa hỗ trợ → ở mẫu số dạng H4.
- 8 dòng H1 → K1 = 8/10 = **80%**; liệt kê 2 dòng H5 kèm QĐ-12/13.
- Sai cách: loại thêm dòng vách BTCT sau khi thấy kết quả → 8/9 = 88,9% — **không hợp lệ**, phải báo 80%.

**Ví dụ 3 – Hoàn tất bằng nhập tay vẫn mang C; tách dòng không tăng mẫu số.**
- Đáp án: "Bê tông móng M1–M4, 14 khối, 11,76 m³" (1 dòng). Người dùng nhập kích thước từ chi tiết móng (nguồn: bản vẽ KC, hình MC1), người kiểm xác nhận. Hệ thống sinh 4 dòng (M1…M4), tổng 11,76.
- K1: 1/1 đạt (bốn dòng hệ thống ánh xạ một dòng đáp án, mẫu số vẫn 1). Cách tạo dữ liệu: hình học và kích thước nhập tay (có nguồn). Độ tin cậy: C. K5: vào bảng C, không vào bảng A/B.
- Nếu cùng dòng đó do bộ đọc chi tiết móng tự lấy kích thước: cách tạo dữ liệu = tự nhận; độ tin cậy hiện **vẫn bị gắn C** do lỗi L3 (Q01) — ví dụ cho thấy hai trục phải ghi riêng.
- Nếu M3 thiếu kích thước: tổng phần biết có số nhưng dòng đáp án là H2 → K1 = 0/1.

**Ví dụ 4 – Vật tư và giá.** Đáp án vật tư: xi măng PCB40, cát vàng, đá 1×2, thép D10, thép D16 (5 dòng).
- Hệ thống: xi măng, cát, đá đủ quy cách + lượng (hao hụt TT 38 đã gồm); thép một dòng không chia Ø → D10, D16 không đạt.
- K2 = 3/5 = **60%**.
- Giá: xi măng có 2 báo giá đại lý ACTUAL còn hạn; cát chỉ có công bố giá BULLETIN; đá chỉ có giá SAMPLE.
- K3 = 1/5 = **20%** (cát có BULLETIN được báo riêng, không nâng K3 lên 40%). K4 = 1/5 = **20%**, xi măng 2 NCC.

## 5. Quyết định đã có hiệu lực (5A chủ đồ án duyệt, 5B Codex chốt)

Phạm vi 5A do chủ đồ án duyệt; cách đo 5B do Codex chốt với vai trò BA/reviewer. D01 được triển khai ngay sau khi
Claude hoàn tất hai điểm tài liệu còn lại. D01 không tự khóa đáp án/mẫu số và không chạy đánh giá bản vẽ test.

### 5A. Quyết định phạm vi – ĐÃ DUYỆT ngày 03/11/2026

Nguồn: xác nhận của chủ đồ án trong chat nêu ở mục 0. Bảng này thay thế các đề xuất CHỜ ở bản vòng 1, không thay đổi lịch sử review.
IN = phải có đường bóc và xuất vật tư theo thiết kế, có thể nhập/xác nhận trước, tự nhận sau; chưa đủ dữ liệu thì chờ dữ liệu.

| Mã | Quyết định đã duyệt | Ranh giới và dữ liệu cần | Sprint phụ thuộc |
|---|---|---|---|
| QĐ-01 | IN móng băng, gồm đào/đắp/lót/bê tông/cốp pha/thép | Trục, tiết diện, giao băng và cao độ từ thiết kế; nhập trước, tự nhận sau | X01, X02/X03-bang |
| QĐ-02 | IN đài và vật tư cọc BTCT theo thiết kế; OUT công tác/dịch vụ ép, khoan, đập đầu cọc | Không suy chiều dài hoặc sức chịu tải; cần chi tiết đài và bảng cọc. Không loại lượng bê tông/thép/cọc phải mua nếu thuộc thiết kế | X01 |
| QĐ-03 | IN bể nước ngầm: đào/lót/kết cấu/xây/trát/chống thấm | Thiết bị, đường ống OUT; cần chi tiết bể, kiểm giao móng và nền | X01 |
| QĐ-04 | IN bể phốt/hầm phân, cùng ranh giới QĐ-03 | Chi tiết kết cấu/xây/chống thấm và đào chung | X01 |
| QĐ-05 | IN vách BTCT: bê tông/cốp pha/thép | Theo thiết kế; kiểm trùng tường; không thiết kế chịu lực | X01 |
| QĐ-06 | IN ô văng/mái hắt BTCT | Tách giao lanh tô/mái khi đối chiếu và tính | X01 |
| QĐ-07 | IN sê nô xây, trát và chống thấm | Đúng cấu tạo/tiết diện, không mặc định là sê nô bê tông | X01 |
| QĐ-08 | IN chống thấm mái/sê nô/ô văng khi thiết kế yêu cầu | Cấu tạo/vật liệu/diện tích có nguồn; định mức phù hợp, không chọn tự động | X01, D02 |
| QĐ-09 | IN bậc xây gạch, bậc bê tông và tam cấp | Chọn cấu tạo tường minh; không cộng đồng thời gạch và bê tông cho cùng bậc | I01, X01 |
| QĐ-10 | IN tường chắn mái và lan can xây | Chiều cao riêng theo thiết kế, không dùng cao tầng | X01 |
| QĐ-11 | IN trát cột/dầm/trần; quét nước xi măng IN có điều kiện | Quét chỉ khi là lớp cấu tạo cần thiết đã xác định; không gộp mặc định. Sơn/bả/hoàn thiện khác OUT | J04, X01 |
| QĐ-12 | IN mái dốc BTCT khi đủ hình học; OUT mái khung thép/gỗ và hệ tôn/ngói | Mái khung H5, loại khỏi mẫu số; mái dốc thiếu hình học vẫn thiếu, không suy góc | L01 |
| QĐ-13 | OUT thang cốn và thang xoắn | H5, loại khỏi mẫu số, công bố rõ giới hạn; không triển khai công thức | Hiển thị phạm vi khi cần |
| QĐ-17 | IN cổ cột/cổ móng dưới ±0.000 theo thiết kế | Không cộng thêm đoạn đã có trong bảng thống kê cột; chưa có bảng thì bổ sung đường nhập | X01 |
| QĐ-18 | OUT nhân công và ca máy | Không tính trong chỉ tiêu vật tư; vẫn bóc lượng công tác thuộc phạm vi, không lập tổng dự toán | — |

### 5B. Phương pháp đo – Codex BA chốt ngày 03/11/2026

Nguồn: kết luận review Codex vòng sửa 1 trong chat; không cần xin lại quyết định phạm vi.

| Mã | Quyết định BA | Áp dụng |
|---|---|---|
| QĐ-14 | BULLETIN chỉ là tham khảo, không tính K3 có báo giá mua sử dụng được | G04, V01 |
| QĐ-15 | Báo micro theo dòng, từng hồ sơ, trung bình theo hồ sơ và hồ sơ thấp nhất; luôn có mẫu số | V01 |
| QĐ-16 | Công tác không sinh vật tư thuộc phạm vi vẫn ở K1; không tạo dòng giả K2–K4 | V01 |
| QĐ-19 | Nhập API có lưu đủ giá trị, nguồn và người xác nhận được tính hoàn tất khối lượng K1; không chứng minh hoàn tất qua giao diện | P01, X03, V01 |
| PP-20 | Cách tạo ghi theo từng đầu vào, cho phép nhiều cách trong một công tác; tách khỏi A/B/C/D | Q01, V01 |

## 6. Đề xuất sửa `ho_tro_cau_kien.csv` (chưa sửa – chờ review)

[HT] test `test_rough_secondary.py::test_support_matrix_backed_by_tests` chỉ cho `trang_thai` ∈ {supported, conditional, not_supported}
và bắt dòng supported có ≥ 2 test tồn tại.

| Dòng hiện tại | Đề xuất | Lý do |
|---|---|---|
| Cầu thang, Tự nhận trên bản vẽ, not_supported | conditional; điều kiện "thang bản ≥ 5 nét mũi bậc; nhiều thang/tum/sân thượng chưa kiểm; người dùng duyệt"; test `test_rough_stairs_detect.py::*` — **chỉ sau** review S13i và Q01 | Mã đã gọi `building_stairs` (`takeoff.py:456`) |
| "Móng băng, móng cọc", not_supported, "Chưa có quy ước" | Tách 3 dòng: Móng băng / Đài cọc / Vật tư cọc; vẫn not_supported (chưa làm), `pham_vi` = IN (QĐ-01, QĐ-02); ghi "FoundationItem.kind có khai báo nhưng chưa dùng" | Gỡ lệch docstring; IN không nâng năng lực |
| Móng đơn, conditional | Thêm điều kiện "khối lượng đọc KC đang gắn C (Q01)"; thêm test tham chiếu | Nhãn trạng thái sai |
| Giằng tường (KC), conditional | Thêm "tính riêng ở 'bản vẽ kết cấu', không trừ xây; nhập tay cùng giằng sẽ trùng (K03)" | Rủi ro trùng |
| Mái bê tông, Giằng tường nhập tay: supported | Thêm điều kiện "chỉ qua API JSON, trang chưa có ô nhập" | Phân biệt có công thức và đủ luồng |
| Sàn, supported | Thêm "ô trống nhập tay; chưa nhập thì sàn chưa trừ (H2, Q02)" | |
| (chưa có) | Thêm dòng not_supported: Vách BTCT, Ô văng/mái hắt, Sê nô xây, Bể nước ngầm, Bể phốt, Tam cấp, Bậc xây gạch, Tường chắn mái/lan can xây, Chống thấm mái/sê nô, Trát cột/dầm/trần | Để BOQ "Phạm vi hỗ trợ" không im lặng |
| (chưa có) | Thêm dòng conditional "Cổ cột dưới ±0.000": tính khi bảng thống kê cột có đoạn cao độ âm (`columns.py:260-266`); không có bảng thì chưa tính | Sửa theo review #3 |
| (chưa có) | Thêm dòng conditional "Đào, đắp hố móng đơn": công thức có; cần cao độ đáy móng — bộ đọc chưa trả, trang chưa có ô | Sửa theo review #2 |
| "Cầu thang cốn, xoắn", "Mái khung …": not_supported | Giữ not_supported (năng lực), thêm `pham_vi` = OUT, ghi QĐ-13/QĐ-12 | 5A: H5, không phải H4 |
| (cấu trúc) | Thêm cột `pham_vi` (IN / OUT theo 5A) và `ma_pt` (PTxx) — phải sửa test ma trận cùng lúc | Tách năng lực khỏi phạm vi |

## 7. Điểm tài liệu/ma trận đang lệch mã [HT]

| # | Tài liệu nói | Mã thực tế | Sprint |
|---|---|---|---|
| L1 | CSV: thang tự nhận not_supported; CLAUDE.md: "stairs.py thang (nhập tay)", "chưa đọc … cầu thang" | `takeoff.py:456` gọi `building_stairs`; test `test_rough_stairs_detect.py` | S13i/Q01, cập nhật CSV |
| L2 | Docstring `foundations.py:5-6`, `models.py:94`: móng băng | `kind` không được đọc ở đâu; không test | X01 |
| L3 | Docstring `status.py`: móng đọc KC là A | `foundations.py:143` `source="manual"`, `status.py:100-101` luôn C | Q01 |
| L4 | Giằng/sê nô KC là nguồn "structural" | `secondary.py:72` không truyền `source`; nhãn "C (nhập tay)" (`status.py:104-105`) | Q01, K01 |
| L5 | Kế hoạch: không trình bày tạm tính như đủ | Sàn thiếu `void_area_m2` có số, không `missing` (`areas.py:213-222`) | Q02, O03 |
| L6 | Kế hoạch: không mất phần thiếu | Hạng mục chưa hỗ trợ ngoài thang cốn/mái khung không sinh dòng; lót móng thiếu dày, đào đắp chưa nhập đất, WC ngoài phòng kín không sinh dòng | Q02 + X03 |
| L7 | README du_toan: mã trống = ngoài phạm vi | Trống gồm cả ép cọc, đập đầu cọc, xây/trát BNN, xây kết cấu phức tạp, trát dầm/cột/trần — phải đối chiếu quyết định 5A: phần kết cấu/vật tư IN, dịch vụ thi công và phần loại rõ OUT | D01, D02 |
| L8 | `banve1` gắn `CHONG_THAM` cho chống thấm mái/sê nô/ô văng | `CHONG_THAM` của hệ thống là WC + ban công | D02 |
| L9 | Bộ 46 dòng `LANH_TO` gồm ô văng, máng nước, tấm đan | Hệ thống chỉ lanh tô theo lỗ cửa | D02 |
| L10 | CSV: mái bê tông, giằng nhập tay "supported" | Trang không có ô nhập `roofs`, `members`, móng tay, `kind` thang; chỉ giữ thang đầu (`model.ts:195`) | P01, X03 |
| L11 | Bậc thang | Luôn bê tông (`stairs.py:165`) | I01 |
| L12 | CLAUDE.md lệnh pytest "303 bài"; SPRINTS S13n "333 đạt, 3 xfail" | Không chạy lại trong M01 | — |
| L13 | (Bản M01 vòng đầu) đào/đắp "đủ luồng" | `pit()` cần `bottom_level_mm` (`foundations.py:60-63`); `footing_detail_sizes` không trả (`structural.py:153-177`); trang không có ô (`model.ts:179`) | P01/X03 |
| L14 | (Bản M01 vòng đầu) cổ cột không có khối lượng | Có khi bảng cột có đoạn âm (`structural.py:210-251`, `columns.py:260-266`) | X01 (chống cộng trùng) |
| L15 | (Bản M01 vòng đầu) loại mọi vận chuyển | Phí giao vật tư đến công trình là dữ liệu giá của G05; chỉ vận chuyển/bốc xếp thi công là biện pháp (PT47, PT48) | G05 |

## 8. Dữ liệu cần bổ sung (theo mức ưu tiên)

| Ưu tiên | Dữ liệu | Dùng cho |
|---|---|---|
| P1 | Phạm vi 5A đã duyệt, phương pháp 5B do Codex chốt; lập ánh xạ từng dòng đáp án theo quyết định, xác nhận dữ liệu trước khi khóa | D01/D02, chốt mẫu số từng hồ sơ |
| P1 | Rà dòng đáp án mã trống: D01 ghi quy tắc và metadata; D02 ánh xạ IN/OUT theo 5A và tồn tại có/không/chưa rõ. Chưa phân loại không tự coi OUT | D01, D02 |
| P1 | Một hồ sơ build có đáp án công tác do người kiểm khóa (DL03) kèm sổ hạng mục PTxx | D02, C01 |
| P2 | Chi tiết thật cho từng dạng IN đã duyệt nhưng còn thiếu dữ liệu: móng băng, đài + bảng cọc, bể, vách, ô văng, sê nô xây, chống thấm mái, bậc xây, lan can mái (DL01/DL02) | X01 |
| P2 | Thông số liên kết: diện tích lỗ sàn đo/ xác nhận, dày bản thang, cấu tạo bậc, cao lan can (DL02) | O03, I01 |
| P3 | Định mức trát cột/dầm/trần, cán 50, ván ép, phụ gia (DL05) | J04, J05 |
| P3 | Báo giá ACTUAL + quy cách (DL06, DL07) | G01–G04 |

## 9. Ảnh hưởng trường/API/DB có thể phát sinh (chưa triển khai)

- `WorkItem`: cờ mức hoàn tất (H1–H4) hoặc tái dùng `basis` + thêm giá trị; `RoughResult`: danh sách hạng mục của hồ sơ `{ma_pt, trang_thai H0–H6, ly_do, ma_qd}` → API, trang, BOQ sheet "Chưa bóc". Đổi trường dùng chung: báo phiên điều phối trước.
- `WORKS`/`CONCRETE_WORKS`/`STEEL_ELEMENTS`/`WORK_STAGE` (`models.py`): **chỉ** thêm mã khi X01 xác định bước thiếu là `MÃ` (mã có sẵn không chứa được đơn vị, cốp pha, thép hoặc định mức). Theo mục 1, phần lớn hạng mục thiếu ở S1–S3 và dùng lại được mã có sẵn; ứng viên cần cân nhắc mã/khóa cấu kiện riêng: vách (cốp pha, thép), vật tư cọc. Thêm mã kéo theo `status._inputs`, `boq._component`, `dinh_muc_phan_tho.csv` (GO_xxx), frontend.
- Cách tạo dữ liệu theo đầu vào (review #1): trường riêng tách khỏi `status`, ví dụ `WorkItem.provenance` {vai trò: tự nhận | suy | nhập tay | thiếu}, gom từ `src/edited/source` đã có. Đổi trường dùng chung: báo phiên điều phối trước (Q01/V01).
- Đầu vào móng trên trang (review #2): ô nhập/sửa `FoundationItem` gồm cao độ đáy, dày lót, cổ móng (P01/X03); không đổi lược đồ DB.
- Phí giao hàng (review #4): thuộc dữ liệu giá G05, không thêm vào `WORKS`.
- `ProjectParams`/`FoundationItem`: dùng `kind`; thêm cấu tạo bậc thang, cao lan can, bê tông theo cấu kiện (J01); danh sách vách/ô văng/bể nhập tay.
- `ho_tro_cau_kien.csv`: thêm cột `pham_vi`, `ma_pt` + sửa test ma trận. CSV này chưa có bảng PostgreSQL; nếu đưa vào DB cần chủ đồ án duyệt.
- `data/ground_truth/du_toan/cases.csv`: thêm `data_kind`, phiên bản, quyền dùng (D01); file đáp án thêm `ma_pt`, `ton_tai`, `pham_vi`, người kiểm.
- `takeoff_results.result` là JSON: lưu thêm danh sách hạng mục không cần đổi lược đồ.
- Không đề xuất đổi DB trong M01.

## 10. Kiểm tra đã làm và chưa làm

Đã làm: đọc `CLAUDE.md`, kế hoạch, `SPRINTS.md` (S13), 12 dòng cuối `NHAT_KY.md`, `ho_tro_cau_kien.csv`, README + `cases.csv` + hai CSV dự toán;
đọc `rough/models.py`, `takeoff.py`, `status.py`, `foundations.py`, `stairs.py`, `secondary.py`, phần chính `areas.py`, `walls.py`,
`materials.py`, `boq.py`; grep `structural.py`, `api/main.py`, `frontend/src/app/(user)/do-boc/model.ts`, `Rough.tsx`, `phan-tho/rough.tsx`; tên test `tests/test_rough_*.py`.

Vòng sửa M01 cuối (review vòng 2): đọc `Review.tsx:248-250,387` (`toggleCol`), grep `cols` trong `do-boc/*.tsx` (`Board.tsx:138-142`, `Rough.tsx:60,110`), `model.ts:205-239` (`projectParams`, gán móng/cao lanh tô), `takeoff.py:233-236,469-495` (`structural_parts`, cao dầm suy).

Vòng 1 (sau review): đọc `structural.footing_detail_sizes` (`structural.py:153-177`), `read_column_schedule`/`ColumnSpan` (`structural.py:193-251`), `columns.schedule_column_works` (`columns.py:260-266`), `do-boc/model.ts:165-250` (biểu mẫu và `roughRequest`); grep `beams`, `members`, `roofs`, `labels`, `kind` trong `do-boc/*.ts*`.

Chưa làm: không chạy pytest (chỉ đổi Markdown); **không thao tác trang thật**, nên mọi nhãn `T` là kết luận đọc mã, chưa xác minh; không chạy hệ thống trên bản vẽ build nên PT15 (vách nhận thành tường?), PT26 (tường trên MB sân thượng), bảng cột của bản vẽ build có đoạn cổ cột hay không, và dòng "xây kết cấu phức tạp" của bộ 46 **chưa xác minh**; chưa đọc hết `Rough.tsx`, `Review.tsx`, `viewer.py`; chưa kiểm `test_rough_build_drawings.py`.

## 11. Phản hồi review Codex vòng 1

| # | Vấn đề | Đoạn đã sửa | Bằng chứng |
|---|---|---|---|
| 1 | A/B/C bị dùng để phân loại tự nhận/suy/nhập tay; công thức "tự động = A + B" | Mục 0 (ba trục: cách tạo dữ liệu tách khỏi độ tin cậy); ma trận cột "Nhận (cách tạo đầu vào)"; 4.1 (bỏ công thức, báo theo vai trò đầu vào); ví dụ 1, 3; 5B PP-20; mục 9 (trường `provenance`) | `status.py:116-133` (status = yếu nhất của đầu vào); `areas.py:211-222` + `status.py` nhánh SAN: diện tích B nhưng dày sàn C; `model.ts:225-229` (`Stair.source`) |
| 2 | PT01–02 đánh đủ luồng dù thiếu cao độ đáy móng | Mục 0 (định nghĩa `T`/`T-`, không dòng nào "đủ luồng"); ma trận PT01, PT02, PT04, PT06, PT10, PT13, PT19, PT27, PT36, PT39 sang `T-`; chi tiết PT01–02, PT04, PT13, PT36; 7-L13; mục 6 dòng đào đắp | `foundations.py:60-63`; `structural.py:153-177`; `model.ts:179`, `model.ts:231-250` (không gửi móng/dầm/mái/giằng); `Rough.tsx:72` |
| 3 | Cổ cột bị mô tả không có khối lượng | Ma trận PT11; chi tiết PT11 (có bảng: tính; không bảng: chưa có đường; chống cộng trùng); 3.2 H4; 5A QĐ-17; mục 6; 7-L14 | `structural.py:193-251`; `columns.py:260-266`; `takeoff.py:238-239` |
| 4 | PT47 loại mọi vận chuyển, mâu thuẫn G05 | PT47 chỉ còn biện pháp/vận chuyển thi công; thêm PT48 phí giao vật tư (dữ liệu giá, không phải công tác); mục 9; 7-L15 | Kế hoạch mục F, dòng G05 |
| 5 | Đồng nhất "chưa có chức năng" với "không có mã" | Mục 0 (cột "Thiếu ở bước" S1–S4/MÃ); ma trận cột mới; chi tiết PT08–09, PT15, PT28–29, PT30–31, PT38; 5A cột "Thiếu ở bước"; mục 9 (chỉ thêm mã ở bước MÃ) | `materials.py` nhánh `CHONG_THAM` + `dinh_muc_phan_tho.csv` CT01–CT03; `foundations.py:137-160` (khối dùng cho đài); `dinh_muc_phan_tho.csv` GO_LANH_TO/GO_SE_NO ghi "mái hắt, máng nước" |
| — | Rà mọi nhãn Đ | Không còn nhãn `Đ`; `T` = theo mã có đường qua trang, chưa xác minh thao tác | Mục 0, đoạn "Đường cung cấp đầu vào trên trang" |
| — | Tách quyết định phạm vi khỏi đề xuất kỹ thuật | Mục 5A (chủ đồ án), 5B (Codex BA/reviewer); D01 làm metadata được, chưa khóa mẫu số | Yêu cầu review |

Trạng thái cập nhật: **5A đã được chủ đồ án duyệt; 5B đã được Codex chốt**. M01 chưa đánh ✅: Claude cần hoàn tất hai điểm
review còn lại (khả năng sửa cột trên trang; nguồn thực tế của giá trị trong ProjectParams), đồng bộ các câu mô tả lịch sử với
quyết định hiện hành và bàn giao diff. D01 được triển khai tiếp theo yêu cầu chủ đồ án, không phải đợi hỏi lại phạm vi.

## 12. Cập nhật quyết định và giao việc ngày 03/11/2026

Codex ghi quyết định chủ đồ án và phương pháp BA vào 5A/5B; đồng bộ phạm vi trong ma trận và ví dụ. Không nâng trạng thái hỗ trợ
hoặc thay CSV vận hành chỉ vì phạm vi đã duyệt. Claude hoàn tất hai điểm review còn lại, rà các tham chiếu đề xuất cũ và cập nhật
mục11 bằng chứng vòng2, sau đó triển khai D01. Prompt: [CLAUDE_M01_D01_PROMPT.md](review/CLAUDE_M01_D01_PROMPT.md).
Chưa khóa mẫu số từng hồ sơ: còn cần manifest/ánh xạ và đáp án được người kiểm xác nhận ở D01/D02.

## 13. Phản hồi review Codex vòng 2 (hoàn tất M01)

| # | Điểm review | Đoạn đã sửa | Bằng chứng |
|---|---|---|---|
| 1 | Trang chỉ bỏ/giữ cột, không sửa tiết diện/tọa độ hay thêm cột | Mục 0 đoạn "Đường cung cấp đầu vào"; ma trận PT12 → `T-`, S3, P01; chi tiết PT12 | `Review.tsx:248-250` (`toggleCol` chỉ đổi `keep`), `Review.tsx:387`; `Board.tsx:138-142` (bấm để bỏ/giữ); `model.ts:231-250` gửi nguyên `x, y, b_mm, h_mm` |
| 2 | Bỏ câu "thông số công trình luôn là nhập tay"; ghi nguồn thực tế | 4.1 đoạn [HT] về cách tạo dữ liệu: biểu mẫu/JSON/file (nhập tay), `structural_parts` (tự nhận móng, cao lanh tô), cao dầm suy trong `compute_rough` | `takeoff.py:482-485,492-493`, `takeoff.py:234-236`, `model.ts:205-217,236-239`, `status.py` `_param` (luôn C) |
| — | Đồng bộ với 5A/5B | Mục 0 (CHỜ QĐ là lịch sử), chú thích phạm vi mục 1, PT22/PT25 bước thiếu "— (OUT)", PT07/PT30 "đầu vào cần", PT34 theo QĐ-11, 3.1/3.2 H4 vs H5, tiêu đề mục 4, 4.1 gộp theo QĐ-15, 4.2 mẫu số K1/K2 chỉ IN, ghi chú ép cọc OUT, 4.3 mục 2, tiêu đề mục 5, mục 6 (`pham_vi` IN/OUT; mái khung/thang cốn OUT) | 5A, 5B |
| — | Không ghi `columns.py` tính sai cao độ âm | Giữ mô tả trung tính: công thức nhận đoạn âm (`columns.py:260-266`); chưa có bằng chứng sai số nghiệp vụ | — |
| — | Phạm vi đã chốt chưa đủ khóa mẫu số | Giữ ở mục 5 và 12: cần manifest (D01) và ánh xạ/đáp án được kiểm (D02) | — |

Chưa kiểm (giữ nguyên từ mục 10): chưa thao tác trang thật, mọi `T`/`T-` là kết luận đọc mã; chưa chạy bản vẽ build cho PT15, PT26,
cổ cột trong bảng cột của bản vẽ build, dòng "xây kết cấu phức tạp" bộ 46; chưa đọc `viewer.py`, `test_rough_build_drawings.py`.
Trạng thái: **M01 hoàn tất sửa tài liệu, chờ Codex xác nhận cuối**; chưa đánh ✅.
