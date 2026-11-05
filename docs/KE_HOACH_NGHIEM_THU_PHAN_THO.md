# Kế hoạch giao việc Claude: phần thô và giá vật tư thực tế

**Điều chỉnh luồng 03/11/2026:** thêm bước bắt buộc “Kiểm tra công tác và khối lượng” trước chọn vật liệu.
Dùng `/phan-tho` trước `/dieu-chinh`, bỏ điều kiện phải chọn vật liệu mới được kiểm khối lượng.
Đặc tả và ca nghiệm thu bổ sung cho P01/P02: [Kiểm tra công tác và khối lượng](KIEM_TRA_CONG_TAC_KHOI_LUONG.md).
Điều chỉnh này chưa phải xác nhận đã triển khai.

Ngày lập: 03/11/2026. Chủ đồ án yêu cầu Codex làm BA và reviewer chính; Claude triển khai.
Trạng thái ban đầu: mọi đầu việc bên dưới đều CHƯA NGHIỆM THU. Đây là kế hoạch, không phải xác nhận chức năng đã đạt.

## 1. Mục tiêu và ranh giới

Hoàn thiện luồng đang có: bản vẽ → cấu kiện → công tác → vật tư → nhóm/loại → báo giá so sánh được.
Người dùng kiểm tra và nhập bổ sung có nguồn là một phần của quy trình; không yêu cầu tự động hóa 95%.
Giữ compute_rough là công thức chốt; tái sử dụng evaluate_rough.py, compare_estimate.py, bộ định mức và BOQ đang có.
Nhà ở riêng lẻ xây mới ≤5 tầng, kiến trúc + kết cấu phần thô. Không lập dự toán xây dựng, không thiết kế/kiểm tra chịu lực,
không thêm điện nước, hoàn thiện hoặc biện pháp thi công. So chi phí vật tư không được gọi là tổng dự toán công trình.

Phạm vi M01 đã được chủ đồ án duyệt ngày 03/11/2026 tại mục 5A: bổ sung các dạng phần thô được ghi IN; mái khung và thang cốn/xoắn OUT khỏi đồ án và mẫu số. Quét nước xi măng chỉ IN khi là lớp cấu tạo cần thiết đã xác định. Chức năng chưa triển khai vẫn báo thiếu/chưa hỗ trợ, không coi là đã hoàn thành.
Không loại hạng mục khó khỏi mẫu số sau khi thấy kết quả. Hồ sơ ngoài phạm vi phải được ghi vào danh sách loại và lý do.

### Thước đo nghiệm thu đề xuất (chốt trước thực nghiệm tại M01/D01)

| Chỉ tiêu | Mẫu số và cách tính | Mục tiêu |
|---|---|---|
| Hoàn tất công tác | Dòng công tác trong đáp án phần thô đã khóa; tử số là dòng có khối lượng hoàn chỉnh, nguồn và quy tắc được người kiểm xác nhận | ≥95%; nhập tay có nguồn được tính, chỉ cảnh báo thì không |
| Đủ quy cách vật tư | Dòng vật tư cần mua trong đáp án; tử số đủ loại/quy cách/đơn vị/lượng | ≥95% |
| Có giá sử dụng được | Dòng vật tư cần mua trong đáp án; tử số có báo giá ACTUAL còn hiệu lực, đúng quy cách, địa bàn và lượng mua | ≥95%; thiếu giá/hết hạn KHÔNG tính đạt |
| Có giá để so | Dòng vật tư cần mua trong đáp án; tử số có ≥2 nhà cung cấp độc lập, cùng điều kiện so sánh | ≥90%; báo cả số dòng và số nhà cung cấp |
| Sai số khối lượng | ACTUAL–test, cùng phạm vi/đơn vị, có đáp án độc lập; báo từng cấu kiện, A/B và C tách riêng | Mục tiêu ≤10% mỗi nhóm đủ điều kiện; báo số dòng đạt/tổng và số không tính được |
| Không mất phần thiếu | Toàn bộ hạng mục mong đợi nhưng thiếu/không hỗ trợ phải có lý do | 100% |
| Nhất quán | Cùng yêu cầu: API, trang, BOQ; cùng đại lượng/đơn vị và quy tắc làm tròn | Chênh không quá một đơn vị làm tròn cuối |

Không cộng các chỉ tiêu thành một điểm “chính xác 95%”. Không đổi dòng, tách nhỏ dòng hoặc thu hẹp phạm vi để tăng tỷ lệ.
Nhập tay đủ nguồn có thể hoàn tất nghiệp vụ nhưng vẫn mang C; phải báo riêng phần tự nhận, suy và nhập tay.
Mục tiêu chỉ được công bố khi có dữ liệu nghiệm thu; chưa đủ dữ liệu thì kết luận “chưa đủ bằng chứng”.

## 2. Phân vai và cách giao việc

- Chủ đồ án: chốt phạm vi, cung cấp/cho phép sử dụng dữ liệu thật; duyệt thay đổi lược đồ PostgreSQL theo quy định kho.
- Codex BA: xác định đầu vào, đầu ra, ca đúng/sai/thiếu, phụ thuộc và tiêu chí cho từng đầu việc.
- Claude dev: đọc CLAUDE.md, kiểm lại mã hiện tại, triển khai đúng một đầu việc mỗi lượt, tự kiểm và gửi gói bàn giao.
- Codex reviewer: đọc diff và luồng liên quan, kiểm bằng chứng; trả ĐẠT / CẦN SỬA / CHỜ DỮ LIỆU, kèm vấn đề cụ thể.
- Claude tự kiểm xong ghi “chờ review”; chỉ đánh ✅ sau khi review đạt. Không suy từ việc có file/test sang việc đã nghiệm thu.

Mỗi đầu việc dưới đây là một sprint nhỏ/một PR hoặc một diff độc lập. Ước lượng 0,5–1 ngày dev cho đầu việc mã;
đầu việc dữ liệu không có cam kết ngày khi chưa có nguồn. Nếu vượt một ngày do thêm loại dữ liệu/luồng mới, tách trước khi làm.
Phần mở rộng cấu kiện bắt buộc tách BA → công thức → nối luồng, không gộp cả một loại kết cấu vào một lượt.
Không yêu cầu xin lại phép cho sửa nhỏ đã nằm trong đầu việc. Đổi trường/cách gộp nhóm phải báo trước; đổi DB cần chủ đồ án duyệt.

### Quy tắc nghiệm thu chung

1. Mã thay đổi có test hành vi phù hợp; lỗi phải có ca tái hiện. Sprint chỉ tài liệu/dữ liệu không ép tạo test giả.
2. Chạy test trọng tâm và toàn bộ pytest, ghi chính xác passed/skipped/xfail/failed. Không cố định kỳ vọng 336 bài.
   Không được còn xfail che chính lỗi đang xử lý. Không chạy đồng thời các bộ test cùng DB kiểm thử.
3. Đụng data/: check_data 0 lỗi trên DB kiểm thử có cùng phiên bản dữ liệu, ghi hash/phiên bản CSV và cách nạp.
   Script hiện yêu cầu PostgreSQL; không báo đã kiểm CSV chỉ vì kiểm DB thật đạt. Không tự nạp đè DB thật.
4. Quy tắc vào CSV; thiếu nguồn/số thì trống + lý do; ACTUAL/SAMPLE/SYNTHETIC tách rõ, chỉ chỉnh trên build.
5. Mỗi sprint có diff, tên test/lệnh/kết quả, ví dụ trước–sau, giới hạn, file dữ liệu dùng và một dòng NHAT_KY.md.
6. Sprint giao diện cần thao tác thật trên một hồ sơ build và ảnh; giữ dữ liệu qua request/response, không chỉ tsc.
7. File dùng chung sửa từng đoạn nhỏ. Không viết lại takeoff/models/API hoặc thêm engine tính song song.

## 3. Backlog nhỏ theo thứ tự thực hiện

Tên test bên dưới là đề xuất cho hành vi cần chứng minh; được đặt theo quy ước test hiện có.
Mỗi bảng gồm vị trí dự kiến, Claude phải xác minh lại trước khi sửa, không coi là yêu cầu tạo module mới.

### A. Khóa phạm vi, dữ liệu và đường cơ sở

| ID / S13 tương ứng | Phạm vi một lượt | File/vùng dự kiến | Bằng chứng xong | Phụ thuộc |
|---|---|---|---|---|
| M01 / m | BA lập ma trận hạng mục; chủ đồ án chốt dạng móng, bể/vách/ô văng, bậc xây, mái; chốt mẫu số và xử lý thiếu | docs/, ho_tro_cau_kien.csv; chưa đổi code/DB | Mỗi hạng mục có in/out, auto/manual/unsupported, dữ liệu cần; quyết định được ghi rõ. **03/11/2026: 5A chủ đồ án đã duyệt, 5B Codex đã chốt:** [M01](M01_PHAM_VI_PHAN_THO.md); **M01 ✅ 03/11/2026: Codex nghiệm thu tài liệu BA (sau vòng sửa 2, mục 13)**; được tiếp tục D01 theo [prompt](review/CLAUDE_M01_D01_PROMPT.md); CSV vận hành chưa sửa | — |
| D01 / f,g | Lập manifest hồ sơ/phiên bản, data_kind, split và quyền dùng; không di chuyển test sang build âm thầm | ground_truth/du_toan/cases.csv, README, data_check.py | Chặn thiếu metadata, công trình trùng phiên bản ở hai tập, SAMPLE/SYNTHETIC vào chỉ tiêu chính. **D01 ✅ 03/11/2026: Codex nghiệm thu (sau sửa vòng 1: kien_truc trống/thư mục bị chặn ở cổng; --out luôn ghi lần chạy mới)** — manifest 14 cột, `data_check.check_cases`/`select_cases`, cổng `evaluate_rough.py --muc-dich`, `tests/test_ground_truth_manifest.py`; diff `docs/review/D01_diff.patch` | M01 |
| D02 / f,h | Lập mẫu đáp án công tác và vật tư; nhận một hồ sơ build đã kiểm tay | ground_truth/, docs/ | Có tầng/cấu kiện/công thức/đơn vị/nguồn; phân biệt thép lắp đặt và lượng mua; người kiểm xác nhận. **03/11/2026: D02: các bản sửa đã qua Codex review; chờ kiểm hồi quy toàn bộ và xác nhận đáp án thực** (pytest toàn bộ trong khung yên tĩnh: 395 đạt, 3 xfail, mã thoát 0; log + hash ở docs/review/D02_*) (chưa có người kiểm, 0 dòng da_kiem) — [D02](D02_DAC_TA_DAP_AN.md), `ground_truth/du_toan/d02/`, `data_check.check_answer_set`, `tests/test_ground_truth_d02.py` | D01 |
| C01 / c | Đường cơ sở trên build; tái dùng script có sẵn, đo bao phủ trước khi sửa thuật toán | evaluate_rough.py, compare_estimate.py, tests tương ứng | **03/11/2026: ĐẠT mốc kỹ thuật baseline phát triển** sau sửa bốn lỗi; [kết luận và giới hạn](review/C01_NGHIEM_THU_KY_THUAT.md). Hồi quy không DB:401 passed,15 skipped,3 xfailed,pytest exit0; hash204 file không đổi, reports/c01_regression_outside/. Cho mở N01. Chưa nghiệm thu dữ liệu thực/độ chính xác/đối chiếu vật tư đầy đủ hoặc PostgreSQL; vật tư thiếu liên kết phạm vi/cơ sở lượng được giữ số và lý do, không tính chênh. Chủ đồ án cùng Codex chốt nghiệp vụ từng quyết định có nguồn, chưa phê duyệt hàng loạt | D01,D02 |

### B. Sửa lỗi tính trước khi mở rộng

| ID / S13 | Phạm vi một lượt | File/vùng dự kiến | Ca nghiệm thu | Phụ thuộc |
|---|---|---|---|---|
| N01 / n | Số trong bảng thép | rough/rebar.py::_num, test_rough_rebar.py | **ĐẠT kỹ thuật03/11/2026**, [kết luận](review/N01_NGHIEM_THU.md). Hai dạng mixed đúng1200.5, giữ quyước một dấu cũ, nhóm saiNone/evidence/missing, bỏ đúngxfailN01. Hồi quy427passed15skip2xfail0fail,exit0,hash204filekhôngđổi (reports/n01/regression). Chưa nghiệmthuDB/hìnhhọc/đápánthực | C01 |
| N02 / n | Bảng thép lặp | read_rebar_schedules, test_rough_rebar.py | **ĐẠT kỹ thuật03/11/2026**, gồm reader, nguồn/manifest, mapping qua upload và partial tới tổng/vật tư/giá. Full605passed15skip1xfail(N03),exit0; probe4fixture/12HTTP200,hash212khôngđổi. Ngoại lệ full thêm CLI synthetic độc lập được ghi rõ; [biên bản và giới hạn](review/N02_NGHIEM_THU_KY_THUAT.md). Chưa nghiệm thu đáp án thực/UI/DB | N01 |
| N03 / n | Giằng chồng cùng cao độ | secondary/takeoff, test_rough_secondary.py | **ĐẠT kỹ thuật03/11/2026** sau review2/focused162/probe root và full824passed16skip0fail0xfail,exit0,225hash không đổi. [Biên bản](review/NGHIEM_THU_BACKEND_20261103_RETRY1.md). Chưa nghiệm thu hình học/đáp án thật/DB | C01, Q02 backend; O01 vẫn riêng |
| A01 / a | Hao hụt theo phần góp | materials._Bill.result, test_rough_materials.py | **ĐẠT kỹ thuật 03/11/2026**: 10 đã gồm +10 chưa gồm, 3,5% →20,350; thiếu % giữ lượng biết nhưng mua chưa hoàn chỉnh/D, giữ dấu trừ và trường hợp triệt tiêu. Hồi quy tích hợp 501 passed, 15 skipped, 1 xfailed, exit0, hash207 không đổi; [kết luận](review/NGHIEM_THU_KY_THUAT_TICH_HOP_0511.md). Không thay Q02/P02 hoặc xác nhận vật tư thực | C01 |
| Q01 / q | Đầu vào quyết định trạng thái thang/giằng | status.py, stairs.py, secondary.py, test_rough_status.py | **ĐẠT kỹ thuật 03/11/2026**: auto thang+dày nhập tay →C; thiếu dày/nguồn cao tầng →D; giằng/sê nô giữ structural/manual qua nhóm nguồn và công tác. [Hồi quy và giới hạn](review/NGHIEM_THU_KY_THUAT_TICH_HOP_0511.md): 501 passed, 15 skipped, 1 xfailed, hash207 không đổi; không đồng nghĩa mọi numeric+missing của Q02 đã hoàn tất | C01 |
| Q02 / q | Phần đã biết và phần thiếu | models/takeoff/boq, tests rough_takeoff/boq | **ĐẠT kỹ thuật backend trong N02-b3**, giữ lượng biết và missing/D qua công tác/tổng/vật tư/intermediate/nhóm/giá; JSON/Excel/optimizer đã kiểm HTTP cùng input. [Biên bản](review/N02_NGHIEM_THU_KY_THUAT.md), full605passed15skip1xfail(N03),exit0. Chưa thay nghiệm thu giao diện P01/P02 | Q01 |
| B01 / b | Vật liệu cốp pha theo cấu kiện | materials.py, tests/test_rough_formwork_materials.py | **ĐẠT kỹ thuật03/11/2026** sau12ca trọng tâm và full605passed15skip1xfail(N03),exit0; [biên bản](review/N02_NGHIEM_THU_KY_THUAT.md). 10 m² DAM →CP03 0,194 m³, CP06 1,429 kg; MONG/CAU_THANG; unknown GO_ trống; âm/None đúng. Không thay/duyệt định mức mới | A01 |

### C. Giao cấu kiện và tính nhất quán

| ID / S13 | Phạm vi một lượt | File/vùng dự kiến | Ca nghiệm thu | Phụ thuộc |
|---|---|---|---|---|
| O01 / o | Nguồn dầm theo từng tầng | takeoff.compute_rough, _floor_key, test_rough_structural | Tầng có KC không cộng thêm manual/suy chưa chọn; tầng thiếu KC vẫn cho suy; nhóm tầng chồng một phần không nhân lặp | Q02 |
| O02 / o | Trừ cốp pha đúng ô sàn/tầng | _slab_form_deduction, beams/columns, test_rough_joints | Có sơ đồ sàn–dầm–cột được BA chốt; không chuyển khoản trừ sang tầng khác, không âm; thiếu mapping không trừ đoán | O01,B01 |
| O03 / o,i | Lỗ thang và chiếu nghỉ | areas.PlanParams/area_works, stairs, tests areas/stairs | Sàn 50 m², lỗ xác nhận 5 m², dày100 →4,5 m³ và 45 m² cốp pha trước trừ dầm; không trừ lỗ hai lần | Q02 |
| O04 / o,l | Mái thay sàn | secondary.drop_slab_under_roof, test_rough_secondary | Mái 50×0,1 →5 m³; liên kết rõ chỉ bỏ đúng sàn; thiếu/không rõ liên kết không tự bỏ; mái thiếu số không làm mất lượng đã biết | O02,Q02 |
| P01 / p | Trang giữ đủ dữ liệu cấu kiện | do-boc/model.ts, viewer.py, test API/frontend hiện có | Hai thang vẫn còn hai sau gửi; giữ height_source; sửa tay đổi nguồn; dữ liệu thiếu không tự biến thành 0 | Q01,O03 |
| P02 / p,e | Nhóm/loại trên API, trang và BOQ | takeoff.py, boq.py, Rough.tsx | Tổng nhóm kg khớp dòng kg có cùng cơ sở; thiếu khối lượng riêng báo chưa đủ; không cộng tấn+viên+m³; quantity và quantity_with_waste đối chiếu riêng | A01,Q02,P01 |
| D03 / d | Chẩn đoán dầm bộ 46 | compare_estimate.py, structural/beams, tests | Tách bê tông/cốp pha/chiều dài; giải thích mọi thay đổi lớn; không thêm hệ số để khớp tổng dự toán | O01,O02,C01 |

Không suy lỗ sàn từ rộng vế/chiếu nghỉ đơn thuần. O03 trước hết dùng polygon/diện tích lỗ được đo hoặc xác nhận; chưa có thì
giữ thiếu + cảnh báo và thể hiện kết quả chưa trừ là tạm tính, không tự cho một diện tích lỗ mặc định.

### D. Công tác ra vật tư đủ quy cách

| ID / S13 | Phạm vi một lượt | File/vùng dự kiến | Ca nghiệm thu | Phụ thuộc |
|---|---|---|---|---|
| J01 / j8 | Ghi đè cách cung cấp/mác theo cấu kiện | ProjectParams, materials.concrete, frontend form | Móng thương phẩm và lanh tô trộn tại chỗ trong cùng nhà; lựa chọn rõ thắng cấu hình chung; không chọn thì báo thiếu | P02; báo hợp đồng trường trước |
| J02 / j1,j5 | Chọn biến thể cấp phối lót/cốt liệu | CSV định mức, norms/materials, form | DA01/DA03 theo lựa chọn và nguồn; đúng cả M100/M150; yêu cầu biến thể không có thì trống, không thay bằng cấp phối khác | J01, nguồn cấp phối |
| J03 / h,j3 | Giữ Ø từ bảng thép tới danh sách vật tư | rebar/steel/models/materials/boq | D8,D16,D20 giữ ba quy cách và tổng kg; dòng thiếu Ø vẫn chưa chia; dây buộc đúng nhóm có nguồn, không cộng thêm thép đã gồm | N01,N02,D02 |
| J04 / j2,j4,j6,j7 | Rà nguồn và lập bốn phiếu định mức riêng: cán50; ván ép AF.83; trát nền gạch rỗng; phụ gia | docs/nguồn, catalog master, rules | Mỗi phiếu ghi phạm vi, đơn vị, số nguồn hoặc lý do giữ trống; không đánh dấu đã hỗ trợ khi mới có nguồn | D02 |
| J05a–d / j | Mỗi phiếu J04 đủ dữ liệu thành MỘT sprint triển khai riêng | CSV + loader/materials + test đúng phiếu | Test số học, âm tính/thiếu nguồn; ván ép gồm đúng hệ vật liệu, không chỉ CP01; không bắt BOQ hết trống để đạt | J04, dữ liệu phiếu tương ứng |
| I01 / i,j9 | Phân biệt cấu tạo bậc xây và bậc bê tông | Stair, stair_works, materials, form | Cùng hình học: bản BTCT+bậc xây không ra bê tông bậc; bậc BT không ra gạch; chưa rõ cấu tạo không tự chọn | O03,J01, chi tiết thang thật |

### E. Bổ sung hạng mục theo thiết kế, tự động hóa làm sau

| ID / S13 | Phạm vi một lượt | File/vùng dự kiến | Ca nghiệm thu | Phụ thuộc |
|---|---|---|---|---|
| X01 / m | BA từng dạng còn thiếu: móng băng; đài/cọc; bể; vách; ô văng; chống thấm mái | docs/, ma trận hỗ trợ | Mỗi dạng có chi tiết build + đáp án + công thức + giao cấu kiện + vật tư + ảnh hưởng trường/DB; thiếu dữ liệu thì chờ | M01,D02 |
| X02-{dạng} / m | Chỉ công thức cho MỘT dạng X01 được duyệt | foundations/secondary hoặc vùng phù hợp; WORKS/status nếu cần | Một case số học được người kiểm xác nhận + thiếu kích thước + giao nhau; chưa nối UI trong lượt này | X01 của đúng dạng; duyệt DB nếu cần |
| X03-{dạng} / m | Nối nhập/xác nhận dạng đã tính vào luồng và BOQ | models/takeoff/form/boq | Sửa qua trang, API cùng số; vật tư có nguồn; unsupported khác vẫn hiện; không nhận tự động khi chưa làm | X02 của đúng dạng |
| K01 / k | Giữ nguồn file/view/tầng của giằng | LinearMember, read_secondary, structural_parts | Không mất nguồn; mặt bằng dùng hai tầng có hai đích rõ; tầng chưa khớp giữ pending | N03,O01; báo trường trước |
| K02 / k | Căn chỉnh KT–KC có xác nhận | registry/mapping, takeoff, form tối thiểu | Ca tịnh tiến+tỷ lệ và ca xoay nếu cho hỗ trợ; không dùng góc bbox làm điểm neo vật lý; thiếu/không khớp thì không trừ | K01, điểm neo/biến đổi có nguồn |
| K03 / k | Dùng giằng đã căn chỉnh, chọn nguồn và trừ tường | secondary/takeoff | Một giằng xuất hiện ở KC+manual chỉ tính một; chưa căn chỉnh không trừ; tách cao độ | K02,N03 |
| I02 / i | Nhận thang có giới hạn, quy tắc ra CSV | stairs.py, rules, tests detect | Không chép mẫu cả nhà khi chưa đủ bằng chứng; ca nhiều thang/tum/khác mẫu/lưới gạch; thiếu thì nhập | I01,P01, bộ build có đáp án |
| L01 / l | Mái bằng: nhận diện tích/dày khi có căn cứ | secondary/areas/takeoff, rules | Đường bao khác diện tích sàn không bị ép bằng; thiếu dày trống; nhập tay thắng; mái dốc chưa đủ dữ liệu không tính | O04, bản mái build có đáp án |

X02/X03 là các mẫu đầu việc phải nhân bản theo từng dạng đã duyệt, không phải một sprint gom mọi cấu kiện.
Móng/cọc chỉ bóc thiết kế đã có, không suy chiều dài cọc, sức chịu tải hoặc cấu tạo kết cấu.

### F. Báo giá và thao tác mua vật tư

| ID | Phạm vi một lượt | File/vùng dự kiến | Ca nghiệm thu | Phụ thuộc |
|---|---|---|---|---|
| G01 | BA mẫu báo giá và danh sách vật tư cần hỏi | docs/, mẫu dữ liệu giá | Đủ quy cách/đơn vị/nhà cung cấp/ngày/hiệu lực/VAT/giao hàng/lượng áp dụng/nguồn/data_kind; chưa giả định trường thiếu | D02,J03 |
| G02 | Đối chiếu mẫu với DB, đề xuất thay đổi tối thiểu | db/models.py chỉ khảo sát; docs thiết kế | Bảng trường đã có/chưa có, cách tương thích dữ liệu cũ, migration/rollback đề xuất; chưa tự đổi DB | G01 |
| G03 | Nhập một báo giá có nguồn và chống nhập lặp | catalog/pricing/repository, API import hiện có, tests | Nhập hai lần không nhân bản; giữ bản gốc, giá mới không xóa lịch sử; mã chưa khớp pending | G02, chủ đồ án duyệt thay đổi DB nếu có |
| G04 | Chuẩn hóa và lọc báo giá đủ điều kiện | pricing.py, tests | Cùng quy cách; kg/tấn/bao đổi khi có căn cứ; khác VAT chưa rõ thì không xếp chung; hết hạn/SAMPLE không thành giá mua thật | G03 |
| G05 | Chi phí giao đến công trình theo báo giá | pricing + lớp dữ liệu giao hàng đã duyệt | Phí chuyến chỉ cộng một lần mỗi đơn/nhà cung cấp; thiếu phí không coi bằng0; không so giá kho với giá giao như cùng điều kiện | G04, báo giá vận chuyển thật |
| G06 | Trang so giá và xuất bảng hỏi mua | frontend giá/vật liệu đang có, API/boq | So ≥2 nhà cung cấp cùng điều kiện, thấy ngày/nguồn/phần thiếu; xuất đủ quy cách; không gán là tổng dự toán | G05,P02 |

Giá dự đoán phải tách khỏi báo giá ACTUAL và không dùng để lấp KPI có giá thực tế. Chưa có số lượng mua hoàn chỉnh thì chi phí
phải ghi là một phần. Không bắt phát triển tuyến đường/OSRM nếu báo giá đã có phí giao hàng xác nhận.

### G. Dữ liệu thật và nghiệm thu cuối

| ID | Phạm vi | Đầu ra và tiêu chí | Phụ thuộc |
|---|---|---|---|
| T01 / f,g,h | Thu hồ sơ/đáp án độc lập | Mục tiêu chuẩn bị 20 hồ sơ (12 build/8 test); tám test có người kiểm, đủ dạng đã chốt; số lượng là mục tiêu thu, không bảo đảm đại diện thị trường | D01,D02; làm song song |
| T02 | Thu báo giá thực tế | Một địa bàn trước; mục tiêu ≥3 NCC mỗi nhóm vật liệu chính, ≥3 đợt giá; đo tỷ lệ thực có, không tự sinh dòng ACTUAL | G01; làm song song |
| V01 / c | Chốt script tính chỉ tiêu và phiên bản quy tắc trước test | Fixture tổng hợp kiểm mẫu số/thiếu/giá hết hạn; báo theo công trình và cấu kiện, lỗi lớn nhất, A/B/C/D, auto/manual; không cộng đơn vị khác nhau | C01,G06, X03 cần thiết |
| V02 | Người dùng thử quy trình trên build | 3–5 người, có người biết bóc; ghi thời gian, số chỉnh sửa, lỗi dữ liệu mất; sửa lỗi trọng yếu trước khi khóa phiên bản | P02,G06 |
| V03 | Nghiệm thu test đã khóa | Hash code/rules/data; chạy script ổn định đã kiểm trên build; không chỉnh theo test; báo đầy đủ chỉ tiêu mục1, không đạt hoặc thiếu nguồn thì ghi thẳng | T01,T02,V01,V02 |

Sau V03 nếu dùng kết quả test để phát triển, bộ đó trở thành dữ liệu phát triển và phải có bộ test độc lập mới trước tuyên bố tiếp.

## 4. Phiếu dữ liệu cần chủ đồ án/Claude chuẩn bị

| Mã | Dữ liệu | Nội dung bắt buộc | Dùng cho |
|---|---|---|---|
| DL01 | Hồ sơ CAD đồng bộ | Mã công trình, số tầng, KT/KC/chi tiết, phiên bản, đơn vị, nguồn và quyền dùng | D01,T01 |
| DL02 | Thông số và liên kết | Cao độ, dày sàn/thang, cấu tạo bậc/nền/mái, mác/cấp phối/supply, lỗ sàn, tầng và điểm neo KT–KC | Q/O/J/K/L |
| DL03 | Đáp án công tác | Mỗi dòng có tầng/cấu kiện/kích thước/số lượng/công thức/phần trừ/đơn vị/người kiểm | D02,C01,V01 |
| DL04 | Đáp án vật tư | Liên kết công tác, hệ số/nguồn/quy cách/đơn vị, đã gồm hao hụt/nối thép/luân chuyển chưa | J/B/V |
| DL05 | Định mức còn thiếu | Trang nguồn + điều kiện áp dụng, loại vật liệu, qty/min/max, đơn vị, norm_code hoặc xác nhận/ngày tra | J02,J04,J05 |
| DL06 | Quy cách hàng hóa | Mã/hãng/tiêu chuẩn/mác/Ø/kích thước/đóng gói; quy đổi đơn vị có nguồn | J03,G01,G04 |
| DL07 | Báo giá gốc | NCC, quy cách, giá, đơn vị, lượng áp dụng, ngày/hiệu lực, VAT, nơi giao, chứng cứ | G03,T02 |
| DL08 | Điều kiện giao hàng | Địa chỉ công trình, phí chuyến/phí theo lượng, bốc dỡ, tối thiểu đơn, ngày giao; chưa biết để trống | G05 |

Các dòng dữ liệu phải có data_kind; ACTUAL là dữ liệu thật có nguồn, không có nghĩa là tự động đúng hoặc đủ để nghiệm thu.
Khóa người kiểm, phạm vi và phiên bản cho đáp án. Không lấy tổng vật tư cả hoàn thiện làm đáp án cho vật tư phần thô.

## 5. Thứ tự giao ngay và phần được hoãn

Giao lượt đầu: M01 → D01 → D02 → C01. Sau đó B và C; dữ liệu T01/T02 thu song song theo mẫu đã chốt.
Luồng trọng tâm: B → C → D → các X cần cho bao phủ → F → V. E tự động hóa sau khi luồng nhập/xác nhận đã đúng.
Không để C01/V01 đến cuối mới phát hiện không có mẫu số hoặc đầu ra đánh giá.

Nếu thiếu thời gian: hoãn mái dốc, căn chỉnh tự động tổng quát, nhận dạng mọi kiểu bản vẽ, dự đoán giá mới và tối ưu logistics.
Không hoãn sửa lỗi tính, hiện thiếu số, quy cách vật tư, dữ liệu giá thật hoặc kiểm chứng độc lập rồi vẫn tuyên bố đạt95%.
Không hứa thời hạn hoàn thành toàn lộ trình trước khi biết X nào mở rộng và dữ liệu T01/T02 đã có bao nhiêu.

## 6. Mẫu giao một sprint cho Claude

```text
Vai trò: Claude dev; Codex là BA/reviewer chính.
Đọc CLAUDE.md, SPRINTS.md và docs/KE_HOACH_NGHIEM_THU_PHAN_THO.md.
Lượt này chỉ làm: <ID và tên>.
Phụ thuộc đã đạt: <ID + bằng chứng>; dữ liệu: <đường dẫn/phiên bản/data_kind/split>.
Trước sửa: kiểm lại hiện trạng và callers; liệt kê file định sửa và ảnh hưởng hợp đồng trường/cách gộp/DB.
Thực hiện đúng phạm vi và ca nghiệm thu trong kế hoạch; thiếu dữ liệu thì ghi thiếu, tiếp tục phần độc lập làm được.
Không thay quy tắc theo test; không mặc định kích thước/định mức/giá; không viết lại engine.
Đổi DB phải có duyệt theo quy định; đổi trường/cách gộp phải báo trước.
Bàn giao: diff/file, ca trước–sau, test/lệnh/kết quả thật, dữ liệu dùng, giới hạn,
ảnh thao tác nếu có UI, dòng nhật ký. Đánh “chờ review”, chưa tự đánh nghiệm thu✅.
```

Codex review mỗi lượt: kiểm logic và caller → số học và giao cấu kiện → B7/nguồn/trạng thái → hồi quy → dữ liệu/đầu ra.
Kết luận ngắn, lỗi xếp theo tác động và chỉ rõ ca tái hiện. Reviewer không xác nhận thay cho người kiểm chuyên môn xây dựng
khi công thức nghiệp vụ hoặc đáp án chưa được xác nhận.
