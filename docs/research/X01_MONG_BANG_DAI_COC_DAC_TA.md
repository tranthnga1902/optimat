# X01 — Đặc tả BA chuẩn bị móng băng, đài và vật tư cọc

Ngày lập: 03/11/2026. Trạng thái: **bản chuẩn bị để Codex review, CHỜ DỮ LIỆU; chưa nghiệm thu X01**.

## 1. Phạm vi và điều kiện sử dụng

Tài liệu chỉ đặc tả hai nhóm: móng băng; đài và vật tư cọc theo thiết kế. M01 và D01 đã nghiệm thu theo giao việc; D02 đang sửa validator và chờ người kiểm xác nhận. Không coi bộ nháp 46 là đáp án đã kiểm. Không triển khai X02/X03, không đổi mã, danh mục, dữ liệu hay trạng thái sprint trong lượt này.

Nguồn quyết định nội bộ: [M01 mục 5A/5B](../M01_PHAM_VI_PHAN_THO.md), QĐ-01/02/17/18 và QĐ-19, PP-20; [kế hoạch mục 1–2, 46–56 và X01/X02/X03](../KE_HOACH_NGHIEM_THU_PHAN_THO.md). Các số dòng mã dưới đây là ảnh chụp khi đọc ngày lập, không phải khóa phiên bản; dev phải kiểm lại vì có phiên khác sửa đồng thời.

- IN: đào, đắp, lót, bê tông, cốp pha, thép móng băng; đài và vật tư cọc BTCT theo thiết kế; cổ cột/cổ móng dưới ±0.000 chưa được tính ở nơi khác.
- OUT: dịch vụ/công tác ép, khoan, đập đầu cọc; nhân công, ca máy. Không suy sức chịu tải, số lượng/chiều dài cọc, tiết diện hay cấu tạo chịu lực. Mái khung, thang cốn và thang xoắn OUT.
- Một engine `compute_rough`; ưu tiên nhập và xác nhận trước, tự nhận sau. Có công thức khối không đồng nghĩa đủ nghiệp vụ hay đủ luồng trang/API/BOQ.
- Không dùng nguồn ngoài trong tài liệu này. Công thức dưới đây là đề xuất hình học và cách tổ chức dữ liệu, **không phải kết luận quy chuẩn đo bóc**. Người kiểm chuyên môn phải xác nhận điều kiện, ranh giới và phần trừ trước khi dùng cho công trình. Nếu cần căn cứ văn bản, phải bổ sung nguồn chính thức, trang/điều và điều kiện áp dụng; chưa có thì để mở.

### Các cổng trước khi nghiệm thu

1. X01 của từng dạng cần hồ sơ **build** được phép dùng, chi tiết và đáp án độc lập theo D02, người kiểm xác nhận công thức/phần giao/vật tư. Hiện chưa đủ; không lấy SYNTHETIC thay thế.
2. X02 chỉ bắt đầu sau khi BA của đúng dạng được duyệt; mỗi lượt một phạm vi ≤1 ngày dev. X03 theo sau X02 tương ứng. Nếu quá một ngày phải tách tiếp.
3. Theo kế hoạch: công tác mong đợi nhưng thiếu/không hỗ trợ phải có dòng và lý do; nhập tay có nguồn có thể hoàn tất K1 nhưng vẫn báo riêng C/cách tạo. Cách tạo từng đầu vào tách khỏi A/B/C/D, không nâng A chỉ vì người dùng bấm xác nhận.
4. Sprint mã sau này chạy test trọng tâm và toàn bộ pytest khi được điều phối DB; sprint UI thao tác thật trên build và có ảnh. Lượt tài liệu này không chạy pytest, không dùng DB, không mở/chạy hồ sơ banve1 test.

## 2. Hiện trạng có bằng chứng

Đường dẫn trong bảng tính từ gốc repo; cú pháp `file:hàm:dòng` cho điểm vào, không khẳng định đã chạy test.

| Bằng chứng đọc mã/test | Có gì | Chưa đủ nghiệp vụ ở đâu |
|---|---|---|
| `src/optimat/rough/models.py:FoundationItem:90`, `FootingTier:81`, `ProjectParams:119` | Khối hộp/bậc/vát, thể tích trực tiếp; `kind=don/bang`; vị trí, mặt bằng, nguồn; thông số đất, thép, cấp phối | `kind` không được rẽ nhánh trong `foundation_works`, nhưng chú thích trường đã định nghĩa `kind="bang"`: dài = chiều dài băng **đã trừ phần giao** (net) — đây là hợp đồng hiện có của request cũ, không phải lựa chọn mở. Mỗi `FoundationItem` là một **loại** (count + positions), không phải một instance; chưa có cọc, hướng băng, ranh giới giao và nguồn/xác nhận từng đầu vào |
| `src/optimat/rough/foundations.py:tiers_of:28`, `_prismoid:36`, `tier_volume_m3:41` | Thể tích khối với cạnh hai đáy thay đổi tuyến tính; mm³ → m³ | Không tự biểu diễn mạng băng giao nhau hay hình dạng đài bất kỳ; không dùng prismoid cho mọi hình vát |
| `src/optimat/rough/foundations.py:tier_formwork_m2:46`, `foundation_works:123` | Chu vi × cao cho bậc thẳng; bỏ toàn bộ bậc có trường mặt trên; `volume_m3` thắng `tiers`, rồi kích thước | Chưa phân biệt mặt tiếp đất/mặt phải ghép ván, mặt giao, đầu băng. Bỏ mặt vát là hành vi mã, chưa là quy tắc được người kiểm xác nhận |
| `src/optimat/rough/foundations.py:pit:57`, `pit_volume_m3:81` | Cần đất tự nhiên, mở rộng, taluy, đáy móng, dày lót và kích thước; hố chữ nhật với taluy tuyến tính | Đáy hố lấy cạnh bậc dưới + mở rộng; chưa có kích thước lót riêng. Không có dữ liệu đất thì chỉ cảnh báo, không sinh dòng đào/đắp (`foundation_works:161,209`) |
| `src/optimat/rough/foundations.py:pit_overlap_m3:100`, `foundation_works:190` | Tích phân lát để trừ hố chồng lấn khi có đủ vị trí; khung song song trục | Không giải bê tông/lót chung; không đại diện móng xoay, đào chung tự do, cao độ đất khác nhau. Thiếu vị trí chỉ cảnh báo, tổng vẫn có số; phải làm rõ partial |
| `src/optimat/rough/foundations.py:foundation_works:130,173` | Bỏ bản ghi sau nếu trùng tên; trừ thể tích cổ chôn trong đất đắp | Khóa chống trùng là tên loại (đúng với mô hình item = loại); muốn khóa theo instance thì phải đổi nghĩa `count` (O7). Cổ chỉ là phần trừ đất bằng `neck_b/h × phần chôn`, **không sinh thêm bê tông/cốp pha/thép cổ**, và có thể lệch với đoạn cổ z âm trong bảng cột (hai nguồn hình học cho cùng một cổ) |
| `src/optimat/rough/foundations.py:footing_rects:214`; `src/optimat/rough/beams.py:beam_joints:106`; `src/optimat/rough/takeoff.py:compute_rough:268` | Cắt chiều dài giằng qua khung bậc trên móng, trước `beam_works` | Chỉ khung 2D, cạnh dài theo x; chưa chứng minh cùng cao độ, giao một phần chiều cao, băng xiên, giao băng–sườn. Không tái dùng vô điều kiện |
| `src/optimat/rough/structural.py:footing_detail_sizes:153`, `read_structural:448` | Đếm ký hiệu FOUNDATION trên BV04, bỏ ký hiệu trùng chỗ; ghép kích thước dài/rộng/cao/lót từ BV05 và mặt cắt | Không xác định `kind`, không trả đáy móng/tiers/cọc; không phân biệt móng đơn với đài cọc. M1–M4 bộ 46 **có thể là đài cọc** là câu hỏi cần xác minh, không kết luận từ tên M |
| `src/optimat/rough/structural.py:read_column_schedule:210`; `src/optimat/rough/columns.py:schedule_column_works:260`; `src/optimat/rough/takeoff.py:compute_rough:279` | Đoạn cột theo z đầu/cuối có thể gồm cao độ âm; sinh bê tông và cốp pha | Phải kiểm đoạn cổ đã nằm trong bảng, không cộng lại. Cốp pha bảng cột chưa trừ đầu dầm; chưa chứng minh quy tắc cổ đài |
| `src/optimat/rough/steel.py:steel_works:38`, `schedule_works:15`; `src/optimat/rough/rebar.py:RebarRow:39`, `read_table:133` | Ưu tiên tổng tấn nhập theo bảng > bảng đọc > hàm lượng; bảng có Ø/chiều dài cắt/số thanh/kg/m; thiếu thì có missing | Ưu tiên theo **mã cấu kiện** (`scheduled` gom theo `element_code`): chỉ một dòng bảng MONG đã chặn hàm lượng cho cả nhóm móng; `steel_schedule_t[MONG]` nhập tay lại thắng cả bảng. Cần khóa phạm vi bao phủ ổn định theo phương án O7; phạm vi có thể là loại móng hoặc từng instance, chưa buộc đổi item thành instance. `schedule_works` gom mất Ø ở WorkItem; J03 xử lý, không làm trùng |
| `src/optimat/rough/materials.py:materials_for_works:280` | MONG dùng nhánh bê tông chung; lót dùng mác riêng; thép, dây buộc, cốp pha có đường quy đổi | Thép mua hiện một tên chung, bảng thiếu quy cách không thành đủ vật tư. Không có nhánh vật tư cọc; không được coi bê tông đúc sẵn là bê tông trộn tại công trường |
| `src/optimat/rough/takeoff.py:compute_rough:168,286,307,318`, `save_rough:498` | Gọi móng rồi thép, gán trạng thái, quy đổi vật tư; tổng có `complete`; lưu input + result JSON | Dòng bị bỏ hẳn không làm tổng incomplete; không thể dùng tổng hiện tại làm bằng chứng đủ phạm vi. JSON đủ chỗ mở rộng, chưa cần DB mới |
| `src/optimat/rough/status.py:_inputs:50`, `assign_status:109`; `src/optimat/rough/boq.py:_row:36`, `boq_workbook:54` | Missing → D; BOQ có công thức/evidence/lý do thiếu; vật tư có complete | Móng đang mang nguồn manual/C kể cả lấy từ KC; cần phối hợp Q01, không đổi định nghĩa trạng thái cục bộ trong X02 |
| `src/optimat/api/main.py:takeoff_rough:231`, `takeoff_rough_excel:245`; `src/optimat/rough/takeoff.py:RoughRequest:79` | API JSON và Excel dùng RoughRequest, `params.foundations` đã có | Chưa chứng minh trang có đường nhập/sửa đủ móng/cọc. API đủ số chưa chứng minh X03 hoàn tất UI (QĐ-19) |

### Test hiện có và giới hạn bằng chứng

| File:test:dòng | Hành vi đang được mô tả trong test |
|---|---|
| `tests/test_rough_foundations.py:test_stepped_and_sloped_tiers:24` | Khối bậc/vát, lót tách riêng, cốp pha bậc đứng |
| `tests/test_rough_foundations.py:test_footing_without_detail_stays_blank:37` | Thiếu chi tiết giữ trống |
| `tests/test_rough_foundations.py:test_excavation_and_backfill:44`, `test_earthworks_need_confirmed_inputs:57`, `test_insufficient_elevation:64`, `test_negative_backfill_blocked:71` | Số đào/đắp, thiếu đầu vào/cổ, cao độ và đắp âm |
| `tests/test_rough_foundations.py:test_duplicate_footing_counted_once:80`, `test_overlapping_pits_counted_once:85` | Trùng tên; hố chồng với taluy 0; không chứng minh bê tông băng giao nhau |
| `tests/test_rough_foundations.py:test_tie_beam_through_footing_not_double_counted:94`, `test_footing_center_from_plan_rectangle:107` | Giằng xuyên khối chữ nhật; tìm tâm khung |
| `tests/test_rough_joints.py:test_column_beam_slab_node_no_double_count:18`, `test_crossing_beams_main_continuous:31`, `test_t_junction_and_duplicate_beam:43`, `test_missing_section_blocked:79` | Cơ chế giao khung, tính lại không trừ thêm, trùng và thiếu tiết diện; **không phải** nghiệm thu móng băng/cọc |
| `tests/test_rough_structural.py:test_read_structural_beams_and_foundations:59`, `test_structural_scale_and_rough_bill:71`, `test_read_details_footing_and_beam_section:99`, `test_rough_bill_uses_detail_sizes:111` | Ký hiệu, tỷ lệ, ghép DIM, khối móng khi có chi tiết; không chứng minh phân loại đài |
| `tests/test_rough_structural.py:test_column_schedule_reads_grid:182`, `test_column_schedule_replaces_plan_columns:191` | Bảng cột và không cộng cột mặt bằng khi có bảng; cần thêm ca cổ cao độ âm/giao đài |
| `tests/test_rough_steel.py:test_steel_by_ratio_per_element:13`, `test_steel_schedule_wins:24`, `test_foundation_manual:29` | Hàm lượng, ưu tiên bảng, móng tay; chưa phân bao phủ từng đài/băng |
| `tests/test_rough_materials.py:test_concrete_ready_mix_and_site_mix:53`, `test_steel_and_tie_wire:78`, `test_formwork_materials_by_type_and_element:105` | Quy đổi vật tư chung; không có ca mua đoạn cọc/đầu nối |

Chỉ đọc test, không chạy; chưa thu bằng chứng công trình hay xác nhận chuyên môn. Không nâng hỗ trợ dựa trên docstring hoặc số test.

## 3. Đầu vào tối thiểu và hành vi thiếu

Mỗi số cần giá trị + đơn vị + vị trí nguồn (file/phiên bản, sheet/chi tiết/dòng/đối tượng) + cách tạo + người/ngày xác nhận khi chốt. Dữ liệu có thể đọc trực tiếp bên dưới là **khả năng cung cấp**, không khẳng định bộ tự nhận hiện đã đọc được.

| Đầu vào | Đơn vị/nguồn cần | Bắt buộc cho | Thiếu thì D/partial; lựa chọn người dùng |
|---|---|---|---|
| Loại thực: băng/đài; mã và instance, mặt bằng, số khối | mã, số nguyên; MB móng + chi tiết | Mọi dòng của dạng | Chưa rõ loại thì D, không suy đài từ M…; người kiểm chọn loại. Count >0; không nhân count khi danh sách đã chứa từng instance |
| Dài/rộng/cao hoặc các bậc; hình dạng mặt trên | mm; DIM/chi tiết | Bê tông | Thiếu phần nào thì dòng tương ứng D; có thể nhập thể tích đã bóc kèm công thức/nguồn thay thế, nhưng không suy được cốp pha/lót/đào từ thể tích |
| Băng: đoạn tim/biên, hướng, điểm đầu/cuối, cao độ, quy ước chiều dài gross hay net | mm; MB + mặt cắt | Giao băng và diện tích tiếp xúc | Chọn `net đã bóc` có nguồn hoặc `gross cần xử lý giao`; chưa biết thì không báo tổng hoàn chỉnh. Đoạn net không được cắt lần nữa |
| Sườn/đà kiềng và liên kết tới băng/đài | mm, mã liên kết; chi tiết nút và cao độ | Giao bê tông/cốp pha/thép | Không có quan hệ cao độ thì chỉ có số phần rời nếu rõ, tổng partial; không cắt theo 2D rồi coi đủ |
| Đài: mặt bằng/tiers, đáy/đỉnh, vị trí cọc và cao độ đầu cọc | mm; chi tiết đài + bảng cọc | Đài, phần giao cọc | Thiếu ngàm/ranh giới thì đài gross có thể hiển thị tạm, kết quả net D/partial theo quyết định người kiểm |
| Cổ: tiết diện, số lượng, z đầu/cuối, mã cột và đoạn bảng đã bao phủ | mm; bảng cột/chi tiết | Bê tông, cốp pha, thép cổ và đắp | Thiếu không tự lấy chiều cao tới đất tự nhiên làm cổ kết cấu; chọn đã nằm trong bảng / nhập đoạn còn thiếu / xác nhận không có; chưa rõ giữ D |
| Lót: biên riêng, dày, cao độ, có/không, nhóm vùng chung | mm; cấu tạo/mặt cắt | Lót, đào, đắp | Không mặc định lót bằng mép móng cho đường mới. Mã hiện lấy lót theo bậc dưới cùng (`test_stepped_and_sloped_tiers` dựa vào đó): đề xuất thêm trường biên lót riêng (O10). Ngoại lệ tương thích: request cũ thiếu biên lót riêng nhưng đủ kích thước bậc dưới và dày lót thì giữ số cũ, trạng thái không tốt hơn C + cảnh báo "lót lấy theo mép móng, chưa xác nhận". Ngoài ngoại lệ này, thiếu biên hoặc dày cần để tính thì lót D; ngoại lệ không được ghi đè D do thiếu đầu vào khác. `không có` phải có xác nhận, không dùng null hay 0 thay thế |
| Đất tự nhiên, đáy đào hoặc đáy lót; biên đào, mở rộng/taluy; nhóm hố chung | mm; hồ sơ/biện pháp được người kiểm cung cấp | Đào | Không tự chọn taluy/mở rộng. Chọn hố riêng/hố chung hoặc khối lượng bóc được xác nhận; thiếu thì có dòng D, không chỉ cảnh báo |
| Cốt đắp hoàn trả, thể tích kết cấu nằm trong vùng đắp, lớp thay đất/đệm | mm/m³; mặt cắt + phạm vi hoàn trả | Đắp | Đào có số vẫn đắp D nếu chưa đủ. Không đồng nhất cốt hoàn trả với đất tự nhiên; không suy đất mua từ m³ hình học |
| Mặt cần cốp pha, mặt tiếp đất, mặt giao, có đáy/vát hay không | m² hoặc biên/mm; cấu tạo/biện pháp | Cốp pha | Người kiểm chọn diện tiếp xúc hoặc nhập m² có bảng bóc. Thiếu thì D, không mặc định tất cả mặt bên đều ghép ván |
| Bảng thép: phạm vi cấu kiện/instance, thanh, Ø/cấp thép, chiều dài cắt, số thanh, kg/m có nguồn | mm, thanh, kg/m, t; bảng thiết kế | Thép lắp đặt theo bảng | Tổng t có nguồn dùng được cho công tác nhưng vật tư mua thiếu quy cách vẫn D/partial; bảng thiếu hàng không coi đủ cả nhóm MONG |
| Hàm lượng từng phạm vi chưa có bảng và người chấp nhận | kg/m³; người nhập + căn cứ | Thép tạm theo hàm lượng | Thiếu cả hai đường thì D. Người dùng chọn bảng/hàm lượng theo phạm vi không giao nhau; không tự lấy hàm lượng tiêu chuẩn |
| Cọc: loại đúc sẵn/đổ tại chỗ, mã/quy cách, số cọc, cấu hình từng đoạn, chiều dài thiết kế, ngàm, nguồn | mm/m, cái; bảng cọc + chi tiết | Lượng thiết kế/lắp đặt và mua | Không lấy chiều dài từ tải trọng. Tổng mét không suy ra số đoạn mua. Cọc đổ tại chỗ chưa có BA vật tư riêng thì báo chưa hỗ trợ, không quy đổi như cọc đúc sẵn |
| Đoạn cọc, đầu/mũi, bản nối/phụ kiện, số/vị trí mối nối, BOM có bao gồm chưa | cái/bộ/m/kg; thiết kế + quy cách sản phẩm | Vật tư mua cọc | Chỉ xuất khi thiết kế có; thiếu cấu hình thì lượng mua D, không mặc định n đoạn → n−1 nối cho mọi sản phẩm |
| Mác/cấp bê tông, hình thức cung cấp, quy cách thép, loại cốp pha, định mức/hao hụt | theo danh mục/nguồn | Vật tư mua | Tính hình học vẫn giữ; vật tư liên quan incomplete và lý do. Cọc mua nguyên sản phẩm không tách xi măng/thép lần nữa |

Các giá trị kích thước/DIM, ký hiệu, bảng thép, bảng cọc, cao độ, ghi chú vật liệu có thể lấy trực tiếp nếu hồ sơ có; hình học đo/suy cần lưu cách tạo riêng. Người dùng phải chọn loại cấu kiện, phạm vi bảng, vùng giao, phương thức cung cấp và xác nhận thông tin chưa tự nhận. Không ép nhập lại số đã có nguồn tốt; cho sửa và giữ dấu vết.

### Quy tắc số và phần thiếu đề xuất

- Chặn số NaN/Infinity; kích thước/chiều dài/số lượng dương, count nguyên; taluy/mở rộng không âm; cao độ có thể âm; đơn vị nhập phải rõ và đổi đúng một lần. Bậc vát phải đủ mô tả, không tự điền cạnh thiếu. Quy tắc hình dạng ngoài miền hỗ trợ trả lý do, không xấp xỉ im lặng.
- `null` là chưa biết; 0 chỉ là bằng 0 đã xác nhận trong miền hợp lệ. Thiếu khác không tồn tại và khác OUT. Nhập rỗng không được làm biến mất dòng mong đợi.
- Thành phần độc lập đủ số có thể hiện; tổng nhóm chỉ là phần đã tính và `complete=False` khi còn thiếu. Dòng có số tạm không được che missing hoặc được tính hoàn tất K1. Tái dùng `missing/status/complete` hiện có, phối hợp Q01/Q02 để thống nhất mô tả partial.
- Chỉ có thể tích trực tiếp: cho MONG có số, cốp pha/lót/đào/đắp/thép ghi thiếu theo dữ liệu thực; không coi toàn bộ cấu kiện hoàn tất.
- Có vị trí thiếu/không khớp count, chưa xử lý chồng lấn, hoặc chưa xác nhận quy tắc giao: tổng net chưa hoàn chỉnh. Không để cảnh báo thuần túy đi kèm nhãn hoàn tất.

## 4. Công thức dự kiến và sổ phần giao

Đơn vị nội bộ kích thước mm; công thức minh họa dùng m. Không làm tròn từng giao trước tổng; thống nhất làm tròn cuối theo engine/BOQ. Mỗi phần giao cần hai đối tượng, vùng/cao độ, lượng gross, phần trừ, bên sở hữu, nguồn và quyết định người kiểm. Không cộng hai lựa chọn dưới đây đồng thời.

| Đối tượng | Đề xuất hình học khi đủ dữ liệu | Điều phải chốt trước code |
|---|---|---|
| Băng/đài hộp hoặc bậc | `Vgross = count × Σ(L×B×H)`; lớp có cạnh biến thiên tuyến tính dùng `H/6 × (Ađáy+4Agiữa+Ađỉnh)` | Phạm vi hình vát được hỗ trợ, mặt cắt nào là kích thước thật; volume nhập là mỗi khối hay tổng (giữ nghĩa hiện tại: mỗi khối) |
| Băng–băng | Với cùng vùng cao độ: `Vhợp = ΣV − phần đếm lặp`; giao ≥3 dùng hợp vùng, không chỉ trừ cặp khiến trừ quá | Ưu tiên bản đầu: người kiểm nhập chiều dài/thể tích **net đã loại giao** có bảng bóc — trùng hợp đồng hiện có của `kind="bang"`, nên request cũ không bị trừ giao lần nữa; gross là đường mới cần cờ rõ. Tự hợp hình học là sprint riêng, không mặc nhiên dùng pit_overlap cho bê tông |
| Băng–sườn/đà kiềng | Có thể giao phần sườn trong thân băng, hoặc sườn chỉ từ mặt trên băng: tính theo ranh giới thiết kế; thể tích giao chỉ khi giao cả xy và z | Ai sở hữu nút, sườn đã nằm trong tiers hay DAM; cắt chiều dài toàn tiết diện chỉ đúng khi giao phủ đủ tiết diện theo quy tắc được xác nhận |
| Đài–cọc ngàm | `Vđài gross` và `Σ(Acọc × lngàm)` ghi riêng nếu mô hình cho phép; số net theo quy tắc người kiểm xác nhận | Chưa chốt có trừ vật chiếm chỗ khỏi bê tông đài hay không, quy tắc đo bóc nào áp dụng, ngàm bao nhiêu theo thiết kế. Không lấy chiều dài ngàm mặc định; không cắt bớt chiều dài cọc mua vì đã trừ thể tích giao |
| Cổ cột–đài/băng | `V = n×b×h×(zcuối−zđầu)` cho đoạn **chưa** thuộc đài/băng/bảng cột; hợp các khoảng theo cùng instance | Đỉnh đài/mặt băng, chân cổ, điểm chuyển sang cột; thép neo có thể đã nằm chiều dài cắt, không thêm lần nữa. Phần trừ cổ khi đắp phải lấy từ **cùng nguồn** với bê tông cổ (bảng cột hoặc nhập cổ), không dùng song song `neck_b/h`. Không tự trừ khỏi cột khác chỉ vì cùng tên |
| Lót chung | `V = diện tích hợp của từng vùng lót theo cao độ × dày`, hoặc bảng bóc net đã duyệt | Mép lót và vùng băng/đài chung; khác dày/cao độ phải chia vùng; không Σ lót từng móng nếu đã có lót chung |
| Đào chung | Hố chữ nhật taluy tuyến tính: prismoid như trên; nhóm hố chung dùng thể tích vùng hợp theo z hoặc lượng net do người kiểm cung cấp | Biên/mái theo hồ sơ, cốt đất chung hay riêng, sai số tích phân, móng xoay; không tự coi hố riêng là phương án thi công bắt buộc |
| Đắp | `Vhoàn trả = Vvùng hoàn trả − Vhợp kết cấu/lót/lớp khác nằm trong vùng đó` | Cốt hoàn trả, phạm vi cọc trong vùng, sườn/cổ đã trừ ở đâu; m³ đắp hình học không phải m³ đất rời vận chuyển/mua. Âm → D và yêu cầu kiểm, không clamp 0 |
| Cốp pha | Tổng diện tích mặt thực cần khuôn, trừ mặt giao/tiếp xúc theo quy tắc đã duyệt; đầu băng chỉ ở đầu tự do | Mặt đất có dùng ván không, mặt vát/đáy, tiếp xúc cổ/dầm/cọc; không lấy chu vi toàn mạng nhân cao và không tự bỏ mặt vát |
| Thép bảng | `t = Σ(nthanh × Lcắt[m] × kg/m)/1000` | Số cấu kiện đã nhân trong bảng chưa; bao gồm neo/nối/uốn chưa; bảng theo từng instance hay loại. Trọng lượng bảng ghi chỉ đối chiếu khi khác số tính |
| Thép hàm lượng | `t tạm = Vbê tông thuộc phạm vi chưa có bảng × k[kg/m³]/1000` | k và cách lấy thể tích sau xử lý giao do người kiểm chấp nhận; không dùng cho chọn tiết diện/cấu tạo |
| Cọc/đoạn/phụ kiện | `Lm thiết kế = Σ số lượng × chiều dài thiết kế`; lượng đoạn mua theo cấu hình được chỉ định; đầu nối theo BOM/thiết kế | Chiều dài tính từ đâu tới đâu, phần cắt bỏ và ngàm đã nằm trong đoạn mua; không suy tổ hợp đoạn tối ưu hoặc số mối nối khi chỉ có tổng mét |

Ở giai đoạn nhập net, sổ phần giao có thể là bảng bóc người kiểm cung cấp thay vì engine hình học mới. Cần cảnh báo xung đột nếu đồng thời có dữ liệu gross, net và phần trừ; chỉ một đường là đường có hiệu lực, dữ liệu còn lại để đối chiếu. Tính lại cùng request không làm trừ thêm; thứ tự bản ghi không làm thay đổi tổng.

## 5. Vật tư phải xuất và ranh giới lượng

| Nhóm | Lượng hình học/công tác | Lượng lắp đặt/thiết kế | Lượng mua và phần thiếu cần hiện |
|---|---|---|---|
| Bê tông băng/đài/cổ | m³ kết cấu, tách lót | Theo ranh giới công tác đã xác nhận | Thương phẩm: m³ đặt có nguồn hệ số; trộn tại chỗ: xi măng/cát/đá/nước/phụ gia nếu có định mức phù hợp. Không dùng chung mác toàn dự án nếu thiết kế khác mà chưa chấp thuận |
| Lót | m³ lót theo vùng net | Lớp cấu tạo | Vật liệu theo mác/cung cấp riêng; thiếu định mức giữ incomplete |
| Cốt thép | Thể tích bê tông chỉ là cơ sở hàm lượng | t/kg theo bảng từng Ø/cấp thép, hoặc t tạm theo hàm lượng | Quy cách mua, đơn vị, chiều dài cây/cuộn nếu có; hao hụt/cắt uốn có nguồn. Tổng t đủ K1 chưa đủ quy cách mua; không tự chia Ø từ hàm lượng. Dây buộc theo định mức đúng và không nhân đôi hao hụt |
| Cốp pha | m² tiếp xúc | Mặt khuôn cần thi công | Gỗ/ván ép/phụ kiện theo định mức đúng cấu kiện, điều kiện luân chuyển/hao hụt; không đồng nhất m² tiếp xúc với m² ván mua. Phối hợp J04/J05, không tự điền định mức |
| Cọc đúc sẵn mua nguyên | Số cọc, mét theo thiết kế | Từng vị trí và cấu hình đoạn | Cái/đoạn theo mã/quy cách/chiều dài; mũi/đầu nối/bản nối nếu thiết kế yêu cầu và chưa gồm trong sản phẩm. Không cộng bê tông/thép bên trong vào vật tư rời nữa |
| Cọc tự chế tạo theo thiết kế (nếu được chọn) | Khối cọc và bảng thép/phụ kiện thiết kế | Từng đoạn | Chỉ bóc vật liệu rời sau BA riêng về phương thức cung cấp/BOM và nguồn; không xuất đồng thời cọc mua nguyên. Không coi đường này sẵn hỗ trợ |
| Đất đắp/đệm | m³ hình học từng lớp | Phạm vi hoàn trả | Nếu cần mua, phải biết loại, nguồn đất tận dụng/đất mua, hệ số quy đổi có nguồn; không tạo vật tư giả cho đào không sinh vật tư mua |

Giữ riêng `quantity`, `quantity_with_waste`, `complete`, `missing`, `uses`, `waste_included`. Không nhân hao hụt lần hai khi định mức đã bao gồm; thiếu hệ số không tự đặt 0%. Catalog chưa có đúng quy cách thì không gán mã gần đúng; lượng đã biết vẫn giữ kèm thiếu mã/giá. Công tác không sinh vật tư vẫn ở K1, không tạo dòng giả K2–K4 (QĐ-16). Giá, vận chuyển vật tư mua thuộc luồng G; không lập tổng dự toán hay thêm nhân công/ca máy.

## 6. Hợp đồng trường/API/BOQ tối thiểu đề xuất

Đây là danh sách yêu cầu cho review, **không phải schema đã chốt**. Trước đổi trường/cách gộp phải báo phiên điều phối; thay lược đồ PostgreSQL cần chủ đồ án duyệt. Không mở bảng DB chỉ vì thêm cấu kiện; `save_rough` đã lưu request/result trong JSON.

1. Tái dùng `ProjectParams.foundations`, `FoundationItem` và `FootingTier` cho băng/đài có hình học tương thích. Giữ `count`, thứ tự ưu tiên `volume_m3 > tiers > kích thước` và nghĩa thể tích mỗi khối cho request cũ. Chỉ mở rộng `kind` cho đài sau review; request cũ không có kind không được tự gán đài/băng từ tên. Với kiểu mới phải chọn rõ loại trước tính đầy đủ.
2. Tái dùng các mã có đúng đại lượng: MONG cho bê tông băng/đài; BE_TONG_LOT, DAO_DAT, DAP_DAT; COP_PHA với `formwork_of=MONG`; COT cho đoạn cổ chưa tính; DAM chỉ cho sườn/đà kiềng được định nghĩa là dầm riêng; COT_THEP với `steel_element` đúng. Tên/mã instance phân biệt loại trong `element/evidence`, không tạo MONG_BANG/DAI chỉ để đổi nhãn. Chỉ thêm mã vật tư/công tác cọc khi xác định đơn vị/luồng hiện có không chứa đúng nghĩa; không nhét mét/cái cọc vào m³ MONG.
3. Cần định danh ổn định theo instance/mặt bằng, phạm vi gross/net và nhóm đào/lót chung; quan hệ cổ–cột/đài, băng–sườn; phạm vi bảng thép. Trước tiên xem dữ liệu đang có đáp ứng được không; chỉ bổ sung trường thực sự cần sau ca nghiệm thu. `name` không đủ làm khóa chống trùng; `source` chuỗi không đủ thay chứng cứ nguồn từng số. Không mã hóa số liệu cần tính bằng cách phân tích lại chuỗi `formula`.
4. Cọc cần danh sách thiết kế/vật tư đoạn với quan hệ tới đài, phương thức mua nguyên hay chế tạo, quy cách/đơn vị/số lượng/chiều dài và BOM đã bao gồm. Tái dùng MaterialLine/MaterialUse để xuất mua, RebarRow cho bảng thép phù hợp; không tạo một hệ thống BOQ cọc song song. Lượng mua theo cái/m khác nhau không gộp cùng dòng nếu chưa có quy đổi rõ.
5. `WorkItem` đã có formula/evidence/missing/source/basis/status/inputs; tổng/vật tư đã có complete. Bổ sung truy vết giá trị/nguồn/người xác nhận và phần thiếu theo hợp đồng chung Q01/Q02/P01, tránh tạo một kiểu trạng thái riêng cho móng. Dòng tạm/partial phải tồn tại trong API và BOQ, kể cả chưa có số. Người kiểm cần phân biệt phần không tồn tại, chưa biết và OUT; không dựa vào việc vắng dòng để suy không có.
6. Giữ `/api/takeoff/rough` và `/api/takeoff/rough/excel` với cùng RoughRequest; nhập/xác nhận trên trang gửi dữ liệu về `compute_rough`, không tính chốt trong frontend. Auto/structural chỉ đề xuất đầu vào, không ghi đè giá trị đã xác nhận. API phải trả lý do trường không hợp lệ, giữ đầu vào chưa đủ và round-trip qua lưu JSON. Không cần endpoint tính móng riêng ở bản tối thiểu.
7. BOQ tái dùng sheet công tác/vật tư/bảng thép/phạm vi hỗ trợ: thêm nhận diện băng/đài/cọc và quan hệ phần trừ bằng các cột sẵn có khi đọc được; chỉ thêm cột khi thiếu nghĩa. Phải thấy gross/net, đại lượng và đơn vị, công thức, nguồn, người xác nhận, phần chưa bóc và lượng mua theo quy cách. Tổng MONG gộp được nhưng vẫn truy ngược từng instance; không đổi mẫu số nghiệm thu bằng cách gộp dòng.
8. Khi thêm mã mới có lý do: rà WORKS/CONCRETE_WORKS/STEEL_ELEMENTS/WORK_STAGE, status, materials, boq, API và frontend, support matrix cùng tests. Cọc mua nguyên không tự vào CONCRETE_WORKS/STEEL_ELEMENTS. J03 phụ trách giữ Ø tới vật tư; X02 không làm bản chia thép khác.

## 7. Các lát dev sau khi qua cổng dữ liệu và BA

Ước lượng mỗi dòng là ngày dev (không gồm chờ người kiểm/nguồn); đây là đề xuất, không tự đưa vào SPRINTS.md. Các ID con chỉ là nhãn bàn giao trong tài liệu. Test số học dưới đây ở mục 8 là **SYNTHETIC**; vẫn cần một ca ACTUAL–build được người kiểm xác nhận cho mỗi dạng để nghiệm thu X02.

| Lượt | Phạm vi tối thiểu | Ước lượng | Phụ thuộc và ca nghiệm thu |
|---|---|---|---|
| X02-B1 | Băng thẳng/bậc theo bảng net đã xác nhận; tái dùng MONG, thiếu chiều dài/rộng/cao có dòng D; không tự hợp mạng | 0,5–1 | X01-băng duyệt + D02 có đáp án; S1, S2, S3; request cũ không đổi số |
| X02-B2 | Sổ giao băng–băng và băng–sườn theo phần trừ nhập có nguồn, chống trừ hai lần; chưa tính hình học tự động | 1 | B1 + quy tắc giao đã chốt; S2, S4, S5, trùng ba băng phải dùng net đã kiểm hoặc D |
| X02-B3 | Lót/đào/đắp vùng chung được nhập net; cốp pha diện tiếp xúc nhập/khối đơn đúng điều kiện | 1 | B1/B2 + cốt hoàn trả/biên được kiểm; S6, S7; thiếu dữ liệu không mất dòng |
| X02-D1 | Đài hộp/bậc + cổ chưa có trong bảng cột; giữ các đoạn đã bao phủ | 1 | X01-đài duyệt + D02; S8, S9; không bổ sung thiết kế cổ |
| X02-D2 | Giao đài–cọc theo quy tắc được người kiểm chọn và vùng ngàm đã biết; phần chưa rõ D/partial | 0,5–1 | D1 + xác nhận có/không trừ ngàm; S8; không mặc định quy tắc |
| X02-C1 | Vật tư cọc đúc sẵn theo cấu hình đoạn/BOM nhập; tách lượng thiết kế và mua | 1 | X01-cọc duyệt + D02 + hợp đồng quy cách được review; S10, S11; không tối ưu tổ hợp cọc |
| X02-T1 | Áp bảng thép theo phạm vi băng/đài/cổ và hàm lượng phần chưa có bảng; không mất Ø | 1 | B1/D1 + O7 đã chốt khóa phạm vi bao phủ + J03/hợp đồng phạm vi; S12, bảng thiếu hàng; tránh dùng MONG tổng chặn mọi phần chưa có bảng |
| X03-B1 | Nhập/sửa băng net, nguồn/xác nhận và phần giao qua trang/API/lưu request | 1 | X02-B1/B2 + P01/Q01/Q02; S1–S5 round-trip, thao tác build có ảnh |
| X03-B2 | Nối vùng lót/đào/đắp/cốp pha vào trang và BOQ, hiện phần thiếu | 1 | X02-B3 + B1 UI; S6/S7, API/trang/BOQ cùng số, thiếu vẫn hiện |
| X03-D1 | Nhập đài, cổ, liên kết và ngàm; đối chiếu đoạn bảng cột, BOQ | 1 | X02-D1/D2; S8/S9 round-trip, không tự nhận đài |
| X03-C1 | Nhập cọc/đoạn/phụ kiện, lượng mua có quy cách và BOQ | 1 | X02-C1 + G/J03 liên quan; S10/S11 round-trip, mua nguyên không cộng lại vật liệu rời |
| X03-T1 | Trình bày phạm vi thép, bảng/hàm lượng, chứng cứ và vật tư chưa đủ | 0,5–1 | X02-T1 + các UI cấu kiện; S12, thép có công tác nhưng thiếu Ø vẫn chưa đủ mua |

Tự nhận mạng băng/đài/cọc không nằm trong các lát tối thiểu này. Nếu sau này cần, lập sprint riêng sau khi đường nhập đã nghiệm thu. Không khởi động các lượt trên chỉ vì tài liệu này đã tồn tại; Codex gốc quyết định cổng X01 từng dạng sau dữ liệu D02.

## 8. Bộ ca kiểm đề xuất — tất cả SYNTHETIC

Các con số chỉ kiểm đại số/luồng, không phải kích thước công trình, không là đáp án bộ 46, không chứng minh quy tắc chuyên môn. Kết quả cốp pha/giao chỉ có hiệu lực với điều kiện giả định ghi ngay trong ca.

| Ca | Đầu vào/điều kiện | Kết quả cần kiểm |
|---|---|---|
| S1 băng rời | 1 băng hộp net 5×1×0,3 m, lót **được xác nhận riêng** 5×1,2×0,1 | MONG 1,5 m³; lót 0,6 m³; thiếu cao độ vẫn đào/đắp D; không lấy rộng lót=1 m. Cùng băng gửi theo request cũ (không có biên lót): lót 0,5 m³ như hiện nay, trạng thái C + cảnh báo |
| S2 giao chữ thập | Hai băng gross mỗi băng 4×1×0,3, giao 1×1×0,3, cùng cao độ; người kiểm giao nút một lần | Gross 2,4; trừ 0,3; net 2,1 m³. Dữ liệu chiều dài đã net thì không trừ tiếp |
| S3 thiếu | Băng có L=5 m, B trống; sau đó chỉ nhập V=1,5 m³ có nguồn | Lượt đầu MONG D; lượt sau MONG có số nhưng cốp pha/lót/đất không suy từ V, tổng nghiệp vụ chưa đủ |
| S4 băng–sườn | Băng 5×1×0,3; sườn cùng trục 5×0,2×0,5 tính từ đáy băng, giả định phần chung 5×0,2×0,3 | Net hợp 1,5+0,5−0,3=1,7 m³; nếu sườn bắt đầu từ đỉnh băng thì không dùng phép trừ này; thiếu z → chưa chốt net |
| S5 trùng/idempotent | Gửi lại S2, đảo thứ tự; cùng mã instance xuất hiện hai lần; cùng tên loại nhưng hai instance khác | Tổng không đổi khi tính lại/đảo thứ tự; bản trùng thật báo xung đột/bỏ có dấu vết theo hợp đồng; hai instance khác không bị bỏ chỉ vì cùng tên. Ca này chỉ áp dụng sau khi O7 chốt item = instance; nếu giữ item = loại thì hai instance là một item count=2 + positions |
| S6 đào/đắp rời | Vùng đào vách đứng 6×2×1=12; trong vùng hoàn trả có móng 1,5, lót 0,6, cổ 0,1 m³, không còn lớp khác theo xác nhận | Đắp 9,8 m³; thiếu cốt hoàn trả → đắp D dù đào đủ; không sinh 9,8 m³ đất mua mặc định |
| S7 vùng chung | Hai hố 2×2×1 m chồng 1×2×1, cùng cốt; lót chung 3×2×0,1; hoặc thiếu vị trí một hố | Đào hợp 6 m³, lót 0,6 m³; không cộng lót riêng thêm. Thiếu vị trí → số riêng chỉ partial, không chứng nhận hợp; đắp âm → D |
| S8 đài–cọc | Đài 2×2×0,5=2 m³; 4 cọc vuông 0,2×0,2, ngàm 0,1 m theo dữ liệu giả | V giao 0,016 m³. Nếu quy tắc duyệt trừ: net 1,984; nếu duyệt không trừ: 2,000; chưa chọn → chưa có net hoàn chỉnh. Lượng cọc mua giữ theo bảng đoạn |
| S9 cổ đã trong bảng | Cổ 0,2×0,3 từ −0,5 tới 0,0 m; bảng cột đã phủ −0,5 tới +3,0 cùng instance | Không thêm lại 0,03 m³ cổ; bảng chỉ phủ −0,2 trở lên thì đoạn thiếu 0,018 m³ cần xác nhận; thiếu ánh xạ instance → D, không tự đoán |
| S10 mua cọc | 3 cọc; thiết kế mỗi cọc 2 đoạn 4 m; BOM quy định 1 bộ nối/cọc và chưa nằm trong giá sản phẩm | 24 m thiết kế, 6 đoạn 4 m mua, 3 bộ nối; không xuất xi măng/thép bên trong. BOM xác nhận nối đã gồm thì không thêm dòng mua nối |
| S11 thiếu cấu hình | Chỉ có 3 cọc dài 8 m, chưa quy định đoạn; sau đó đoạn 4 m có nhưng Ø/tiết diện/mã quy cách chưa rõ | Có thể hiện 24 m thiết kế, lượng đoạn mua D; không tự chọn 6 đoạn. Thiếu quy cách vẫn incomplete, không gán giá loại gần nhất |
| S12 bảng + hàm lượng | Phạm vi A bảng đủ 10 thanh×2 m×1 kg/m; phạm vi B bê tông 1 m³ với k=100 kg/m³ do người nhập chấp nhận | A 0,020 t; B 0,100 t tạm; không chặn B vì có bảng MONG-A. Nếu bảng A thiếu Ø thì lượng công tác biết nhưng vật tư chia quy cách chưa đủ; không suy Ø từ kg/m trong ca |

Thêm biên kỹ thuật trong từng sprint: NaN/Infinity/số âm/count lẻ bị từ chối; null khác 0; hướng xoay ngoài miền hỗ trợ có lý do; mặt bằng khác không gộp; giao chạm biên bằng 0; phần trừ lớn hơn gross bị chặn; xóa dữ liệu đã xác nhận làm các dòng phụ thuộc thiếu; request cũ giữ số; API/trang/BOQ lệch không quá một đơn vị làm tròn cuối. Các ca này là đề xuất chưa chạy.

## 9. Phiếu dữ liệu gửi người kiểm

Không yêu cầu tự thiết kế thêm kích thước. Người cung cấp đánh dấu “không có/chưa biết” và chỉ tới nguồn thực; không bù số theo kinh nghiệm.

| Phiếu | Nội dung cần điền/đính kèm | Chốt bởi |
|---|---|---|
| A — Hồ sơ | Mã công trình; ACTUAL/SAMPLE/SYNTHETIC; build/test theo D01; quyền dùng; file/phiên bản; sheet MB móng/chi tiết; người lập/người kiểm/ngày; không lấy test làm build | Chủ hồ sơ + người kiểm |
| B — Phân loại | Mỗi ký hiệu là móng đơn/băng/đài/chưa rõ; count và danh sách vị trí; M1–M4 bộ 46 có phải đài cọc không? Nguồn chi tiết nào chứng minh? | Người kiểm kết cấu/bóc khối lượng |
| C — Băng | Bảng đoạn và tiết diện/bậc; chiều dài tim/biên/net; cao độ; sườn/đà kiềng; nút L/T/+ và ba nhánh; bảng phần giao/ai sở hữu nút | Người kiểm |
| D — Đài/cổ | Biên/bậc/cao độ; quan hệ với cọc; ngàm thiết kế; cổ z đầu/cuối; đoạn bảng cột đã gồm; quy tắc có/không trừ giao và căn cứ nếu áp dụng văn bản | Người kiểm |
| E — Đất/lót/khuôn | Biên/dày lót; đào riêng/chung, cốt đất/đáy/mở rộng/taluy; cốt hoàn trả và vùng chiếm chỗ; diện cần khuôn; mặt vát/tiếp đất; nguồn biện pháp | Người kiểm và người cung cấp hồ sơ |
| F — Thép | Bảng gốc và phạm vi bao phủ; mã thanh/Ø/cấp/L cắt/số cấu kiện×số thanh/kg/m; neo/nối đã gồm; tổng lắp đặt; phần chỉ dùng hàm lượng và người chấp nhận | Người kiểm |
| G — Cọc mua | Loại/quy cách, số vị trí; chiều dài thiết kế; từng loại đoạn/chiều dài/số lượng; mũi/đầu nối/phụ kiện và BOM đã gồm; mua nguyên hay chế tạo; không cần đơn giá để kiểm lượng | Người kiểm + bên cung cấp quy cách |
| H — Đáp án | Mỗi công tác/vật tư: tầng/instance/đại lượng/đơn vị/gross/phần trừ/net/công thức/nguồn; phân lượng hình học–lắp đặt–mua; thiếu và OUT; người xác nhận, ngày, trạng thái theo D02 hiện hành | Người kiểm độc lập |

Tối thiểu một ca build băng và một ca build đài+cọc có đủ phần giao liên quan; nếu hồ sơ không có một dạng thì ghi không tồn tại, thu hồ sơ khác thay vì tạo kích thước để lấp. Phiếu chưa điền là danh sách thiếu dữ liệu, chưa phải đáp án khóa. Không chép/khóa hash dữ liệu D02 trong tài liệu này; dùng giao thức D02 sau khi phiên sửa bàn giao.

## 10. Quyết định còn mở trước code và bàn giao

| Mã mở | Cần quyết định | Người/đầu vào cần |
|---|---|---|
| O1 | Bản tối thiểu dùng net nhập đã bóc cho mạng băng (đã là hợp đồng hiện có của `kind="bang"`), hay thêm ngay đường gross tự hợp? Đề xuất giữ net, gross sau | Codex BA/reviewer + người kiểm bảng giao |
| O2 | Ranh giới băng–sườn–đà kiềng; sở hữu nút, phạm vi theo cao độ; quy tắc giao ≥3 | Người kiểm chuyên môn; chi tiết build |
| O3 | Đài có trừ phần cọc ngàm không; có áp dụng văn bản đo bóc nào và điều kiện nào? | Người kiểm, nguồn chính thức nếu viện dẫn |
| O4 | Cổ tính trong MONG hay COT theo đoạn, đối chiếu bảng cột và thép neo; mặt khuôn nào tính; phần trừ khi đắp dùng cùng nguồn cổ với bê tông | Người kiểm + Codex review hợp đồng; đề xuất COT cho đoạn độc lập đúng nghĩa |
| O5 | Quy ước lót/đào/đắp chung, cốt hoàn trả; lượng đất mua có thuộc phiếu vật tư và đủ nguồn quy đổi chưa | Người kiểm + hồ sơ/biện pháp |
| O6 | Cọc đúc sẵn mua nguyên là phạm vi đầu tiên? Cọc đổ tại chỗ/tự chế tạo cần BA tiếp theo, không tự gộp | Codex BA + chủ hồ sơ; phạm vi vật tư IN không bị biến thành OUT do chưa hỗ trợ |
| O7 | `FoundationItem` giữ nghĩa một loại (count + positions, khóa = tên) hay đổi thành một instance (đổi nghĩa `count` của request cũ); danh tính instance/phạm vi bảng thép, đơn vị mua cọc và giữ Ø; trường nào thật sự thiếu so với Q01/Q02/J03/P01 | Codex gốc/phiên điều phối trước sửa trường/gộp |
| O8 | Xác nhận kiểu nguồn/người xác nhận, hành vi partial và dòng chưa hỗ trợ dùng chung; tương thích request cũ không kind | Codex reviewer; không chốt lược đồ riêng tại X01 |
| O10 | Lót: thêm trường biên lót riêng và hạ C cho request cũ lấy theo mép móng (giữ số), hay đổi số và sửa test hiện có? Đề xuất giữ số + hạ C | Codex reviewer + người kiểm |
| O9 | Chọn ca ACTUAL–build, đáp án D02 đã kiểm cho từng dạng và tiêu chí số học/cốp pha/vật tư | Người kiểm độc lập; D02 hoàn tất validator và xác nhận |

Sau D02, dev có thể làm X02-B1 hoặc X02-D1/C1 **khi** đúng dạng qua X01 và các quyết định phụ thuộc đã được duyệt; không cần chờ tự nhận. Công việc độc lập hiện làm được là review hợp đồng, phiếu dữ liệu và các ca SYNTHETIC; không có bằng chứng để kết luận đủ X01 hay bắt đầu công thức công trình.

Điểm Codex gốc cần review trước: net/gross (net đã là hợp đồng của `kind="bang"`) và cổng partial; item = loại hay instance (O7); lót request cũ (O10); cổ đã nằm trong bảng cột; giao đài–cọc; phạm vi ưu tiên bảng thép theo MONG; đơn vị và vật tư cọc mua nguyên; chia lát ≤1 ngày và phối hợp J03/Q01/Q02/P01. Phạm vi đã duyệt không cần hỏi lại.

## 11. Tự kiểm lượt tài liệu

- Đã đọc CLAUDE.md, kế hoạch X01/X02/X03/quy tắc nghiệm thu, M01 5A/5B; đọc mã models/foundations/takeoff/structural/steel/materials và các điểm nối beams/columns/rebar/status/boq/API; đọc test liên quan. Đường dẫn output chưa tồn tại khi bắt đầu.
- Chỉ tạo tài liệu này. Repo có nhiều sửa đổi từ trước và phiên khác; không nhận các thay đổi ấy là của lượt này, không ghi đè hay hoàn tác. Không sửa SPRINTS.md/NHAT_KY.md theo giới hạn giao việc, dù quy tắc chung thường yêu cầu cập nhật.
- Không mở bản vẽ build/test, không chạy banve1, pytest, script dữ liệu hay DB; không đọc PDF/tra nguồn ngoài. Chưa xác minh UI thực, chưa kiểm công thức bằng người chuyên môn, chưa có đáp án công trình được khóa.
- Các tham chiếu file và điểm vào hàm/test được kiểm tồn tại khi bàn giao; cần kiểm lại dòng khi dev bắt đầu. Trạng thái cuối: **CHỜ CODEX REVIEW + DỮ LIỆU, không tự đánh hoàn thành X01**.
