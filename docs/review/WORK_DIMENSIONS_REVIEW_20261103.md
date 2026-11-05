# Review delta WorkDimensions — 03/11/2026

Codex, **chỉ đọc** bốn file và callers; không sửa source/test, không chạy import/probe/test/CAD/DB trong lúc UI xử lý NaN. O01 vẫn HOLD.

**Kết luận:** delta bốn file là thêm metadata, chưa thấy đổi công thức BT/CP/XAY hoặc quy tắc status. **Chưa nghiệm thu metadata**: có nhãn chiều dài dầm sai đã xác định, chưa có test trực tiếp cho dimensions và cần kiểm dữ liệu không hữu hạn/None cùng các callers mới. Không có căn cứ quy lỗi NaN của full cho delta này; không xác định tác giả không cho phép rollback.

## Base xác thực và hash

Base có đủ cả bốn file tại `C:/Users/Admin/Downloads/optimat-ai_6/tmp/wall-basis-integration/src/optimat/rough/`. Tôi đã tự đối chiếu SHA256 byte từng file với `reports/integration_next/full/hash_before.json`: **4/4 khớp**. Không dùng HEAD xa hơn để dựng lịch sử của lượt drift.

| File | SHA256 base khớp hash_before full | SHA256 checkout lúc review |
|---|---|---|
| models.py | e3845ae56e5fe5774773d8c47f7efbe28a963d274d5d03551fa8f7bc06d61730 | b497c7f8e84fcb33feb7ddba59f418f90d02afc798a8c46ba6deb387d847d1b3 |
| beams.py | cc55396c30e86c2119f4159b5d38d1a00f6500e8840bda4cd42fe0222fe0b24f | e74b0a48564cae5fcfb941a96c9b610a1d709a11406ce983a735872cdc4f1150 |
| columns.py | c37412834c6a8fc1638912bb8dd3cb67bd6f2e89411e0b569744e25ad81f5a7d | ba17eb75bc08c636156f2fbd95abe0ce6829fb8433de7534b37190229008361f |
| walls.py | dec7879087408a7b9fec7eeb32e608e3dbb35eea5f5e6440ae902b1c3ede39f1 | 89471e0d34af2e7f311b93cc51bed43a3c3827940ae65204bbcb7aa97fb649ad |

Không dùng timestamp để khẳng định ai ghi file; hash base được đọc trực tiếp từ byte staging và khớp hash_before của full.

Đã so diff sau chuẩn hóa xuống dòng và AST chỉ đọc: bỏ riêng class WorkDimensions, field WorkItem.dimensions, các assignment tạo dimensions/lintel_dimensions, lời gọi extend metadata và keyword dimensions của _work thì AST checkout **bằng AST base ở cả bốn file**. Điều này xác định các biểu thức công thức, nhánh nhận dạng cột, missing/status và phép tính số cũ không bị đổi trong delta; không chứng minh phần metadata mới không thể lỗi khi thực thi.

## Delta và đơn vị/None/source

- models.py:176–204 thêm WorkDimensions, các float optional defaultNone, label/source bắt buộc, note default rỗng; WorkItem.dimensions default_factory=list giữ payload cũ không cần field. Số lượng count không có đơn vị, dài/rộng/cao/dày theo m, diện tích theo m². Model hiện không có ràng buộc hữu hạn cho các float.
- beams.py:186–199: mỗi Beam giữ count1, length_m từ Beam.length_mm/1000, width_m/height_m từ tiết diện đã chọn chia1000. Height là **toàn tiết diện**, còn quantity dùng web=depth−slab (giằng móng không trừ slab); note nêu rõ web. Cùng metadata đầu vào gắn DAM và CP, không phải khai triển đầy đủ phép trừ framed/hole của CP. Source ghi plan/id/Beam.source và “tiết diện bản vẽ hoặc thông số công trình”, chưa chỉ rõ riêng trường nào thắng khi trộn nguồn.
- columns.py:252–276: cột plan dùng hai cạnh tiết diện h/b chia1000, height_m=hc sau trừ sàn; note nói rõ nếu slab thiếu đang lấy chiều cao tầng. Cột bảng dùng count và chiều cao (z_to−z_from)/1000, source giữ hai cao độ. Không suy cạnh tiết diện từ thể tích. BT/CP vẫn dùng công thức cũ, metadata không bao gồm mọi khoản trừ đầu dầm khỏi CP.
- walls.py:107–140: kích thước từng tường từ tọa độ, thickness t và h_wall; XAY/TRAT dùng chung thông tin đầu vào. Lanh tô lấy rộng cửa +2gối, dày tường và cao từ params; None của gối/cao được giữ. Đây là đầu vào trước trừ cửa/cột/giằng, không phải kích thước của net XAY sau N03. Không có phép đọc ngược formula hoặc quantity trong các assignment mới.

## Cần sửa — [P2] Nhãn dầm in khoản trừ thành chiều dài sau trừ

Vùng `beams.py:186–190`. `Beam.length_mm` (`:44–45`) đã là max(0, chiều dài trục−cut_mm). Do đó **length_m đúng là net**, nhưng note “Dài sau trừ giao {b.cut_mm/1000} m” lại in số của khoản trừ.

Ca tính tay từ code, chưa chạy: trục4.000 mm, cut_mm200 → length_m3,800 m; note hiện nói “Dài sau trừ giao0,2 m”. Người kiểm nhận hai chiều dài net mâu thuẫn dù quantity BT vẫn dùng3,8 đúng. Sửa nhỏ nhất: đổi note thành “Đã trừ giao0,2 m” (hoặc ghi cả dài trục/khoản trừ/net bằng đúng nguồn), không đổi length_m hoặc quantity để khớp nhãn. Thêm ca cut0 và cut>0 sau khi được cấp test.

## Các cổng chưa được focused chứng minh

1. **Hữu hạn/strict JSON:** WorkDimensions hiện dùng float không có allow_inf_nan=False hoặc validator. Cần kiểm trường mới không mang NaN/inf vào response ngay cả khi quantity cũ đã None. Ca phân tích nhánh: width của Beam là NaN nhưng depth/slab thiếu → quantity có thể None vì missing, trong khi width_m mới vẫn NaN. Đây là rủi ro của field mới cần probe sau release; **không khẳng định đây là exact NaN ở test_review_api**, route full lỗi là /api/takeoff/view và UI owner đang điều tra riêng. Không cho serializer chấp nhận NaN để lấp lỗi.
2. **Nguồn trộn:** width lấy params, depth từ Beam hoặc ngược lại phải có cách hiểu nguồn đúng; câu “hoặc” hiện chưa truy chính xác mỗi trường. Không dùng dimensions.source để tự nâng A hay xóa prior C/D. Cần ca metadata đi cùng inputs/evidence/status hiện có.
3. **None khác không áp dụng/0:** các optional giữ None, UI chung hiển thị “— chưa có hoặc không áp dụng”. Cần ca thiếu d/gối/dày sàn, count0 nếu hợp đồng cho phép và phần trừ âm; không dùng `or` đổi0 thành số mặc định. Metadata raw không có số không được đổi quantity hoặc missing đang có.
4. **Sau sửa hình học:** N03 có thể đổi XAY về None/D hoặc trừ giằng; L1 có thể bỏ lanh tô. Dimensions vẫn là raw đầu vào; không dùng tích dài×rộng×cao để tái tạo net hoặc chứng minh dòng đã đủ. UI phải đọc quantity/missing/status cuối cùng, không đánh đủ vì dimensions có số.

## Callers và ảnh hưởng N03/Q02

- `_work` trong walls.py tạo WorkItem từ kwargs; Beam/Column/wall producers gắn metadata ở đây. Đầu ra JSON/model_dump của RoughResult sẽ chứa field mới; lưu rough qua save_rough cũng giữ JSON field theo model_dump, chưa đổi schema DB quan hệ.
- `takeoff.compute_rough` gọi wall_works/column_works/beam_works/schedule_column_works. Caller mới tại takeoff:305–306 nhân dimensions.count khi view KC lặp nhiều tầng, thêm note “lặp n tầng”; không đổi dài/rộng/cao để giả một cấu kiện dài hơn. Biểu thức `(d.count or 1)*n` cần ca None và0 riêng; không suy count0 thành1 nếu miền đầu vào cho phép0. Caller này ngoài bốn delta đang audit, không coi đã review xong toàn bộ lịch sử của nó.
- Các producers ngoài bốn file hiện cũng gắn dimensions: areas/foundations/stairs/steel/secondary. Đây là phạm vi metadata khác cần chủ writer bàn giao, chưa được kiểm bằng kết luận AST bốn file. Đặc biệt secondary hiện thêm raw kích thước giằng trong _work; không được hiểu raw hai giằng trùng như đã cộng thành BT hai lần.
- N03 dùng _TieGroup/normalize_ties/deduct_ties rồi assign_status; không đọc dimensions để quyết định giao hoặc mức đủ. Q02/materials/totals/wall_groups/optimizer hiện đọc quantity/status/missing/masonry_geometry; không thấy caller tính lại net từ dimensions. Delta bốn file không trực tiếp đổi BT/CP/XAY/status theo AST.
- `boq.py` vẫn xuất quantity/formula/inputs/evidence/missing; chưa xuất bảng dimensions riêng. Không gọi metadata là đã có đầy đủ trong Excel. Optimizer không lấy dimensions làm lượng mua.
- Frontend `do-boc/model.ts:264–266` thêm type; `WorkReview.tsx:7–20` đọc field để hiển thị summary/detail, không parse formula để tìm kích thước; `:29–30` vẫn xác định thiếu từ quantity/missing/status. Summary nhìn thấy giá trị nhưng không đại diện toàn bộ cùng kích thước; source/note phải đọc ở detail.
- Các bản sao model_copy dùng giữ nguyên dimensions khi thay quantity; phải hiểu đây là raw chứ không net. Không thấy logic dimensions làm complete=True hoặc nâng status trong bốn file.

## Ma trận focused đề nghị sau khi root cấp lượt

Chưa chạy các ca này trong audit, không tạo/sửa file test:

| Ca | Cần chứng minh |
|---|---|
| Payload WorkItem cũ không dimensions | Nhận được [], lượng/status/missing như cũ |
| Dầm trục4 m, cut0,2 m | length_m3,8; note khoản trừ0,2; BT/CP vẫn theo công thức net trước delta |
| Dầm depth400/slab100; giằng móng depth400 | height_m0,4 toàn tiết diện; web0,3 hoặc0,4 được phân biệt bằng note; không lấy height metadata tái tính sai |
| Thiếu width/depth/slab, lót/thang/giằng legacy | None và D/missing còn nguyên; field metadata không làm quantity đủ |
| NaN/±inf trong field metadata khi quantity None | Strict JSON không nhận NaN; input bị chặn hoặc xử lý thiếu có chủ đích, không zero hóa |
| Cột bảng có cao độ âm, nhiều count | Mỗi cạnh chuyển mm→m đúng, hc theo hai cao độ, count không nhân hai lần; giữ hồi quy N01 |
| Tường có cửa/lanh tô/giằng hoặc N03 pending | Dimensions raw còn nhưng net/status/missing cuối đúng; raw không dùng để mở tối ưu khi D |
| CP cột có hole/CP dầm có framed | Metadata đầu vào không bị trình bày là đủ khai triển quantity CP; số cũ không đổi |
| KC lặp3 tầng | Count metadata×3 đúng một lần, BT/CP theo cơ sở cũ; None/0 không tự trở thành count1 trái hợp đồng |
| API JSON + WorkReview + BOQ | Dấu tiếng Việt/đơn vị/source/None rõ; lượng giữ đúng, không chỉ test có key dimensions |

## Cổng bàn giao

Kết luận này chỉ thuộc hash bốn file đã ghi. Cần sửa nhãn đã xác định, chốt xử lý hữu hạn và focused metadata/callers trên snapshot freeze trước full kế tiếp. Chủ UI đang sửa exact NaN riêng; không chạy test trùng hoặc tự mở sửa file. Chưa xác định tác giả thì giữ thay đổi và phân quyền writer, không rollback. N03 đã đạt review trọng tâm nhưng full trước có1failure/8hashdrift; audit này không tự nâng N03 hoặc toàn bộ backend thành nghiệm thu cuối.
