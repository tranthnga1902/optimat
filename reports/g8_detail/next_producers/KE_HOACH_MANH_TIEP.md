# G8 — manifest các producer còn lại, chỉ chuẩn bị

03/11/2026. 01 đã nhận mảnh lót móng: 142 test đạt, 3 HTTP chưa chạy, 231 hash không đổi, review14 khép. Bốn file mảnh lót đang HOLD cho 02/09 tích hợp. Tài liệu này **không mở quyền sửa source hoặc chạy suite**.

Manifest có cấu trúc: `PRODUCER_MANIFEST.json`. Mốc đọc 11 file rough: `BASE_READ_HASH.json`. Mốc lót đã nhận: `../lean_producer/FINAL_HASH.json`. Không đổi schema/quantity/status/owner/norm/catalog trong lượt lập kế hoạch.

## Thứ tự mở đề xuất

| Mảnh | Phạm vi source cần mở sau khi 01 duyệt | Đầu ra cần nghiệm thu |
|---|---|---|
| G8-P02 | areas.area_works + builder/helper + test riêng | Diện tích sàn/lỗ, cán nền, lớp nền, WC và ban công; phân biệt lót nền với lót móng đã có |
| G8-P03 | foundations emitter MONG/DAO/DAP/CP; _neg cần release riêng do dùng chung | Từng lớp hộp/vát hoặc lượng nhập nguồn; hố; các phần trừ đắp; phần hố giao là dòng âm riêng |
| G8-P04 | columns.column_works/schedule_column_works, beams.beam_works + helper/test | Cột theo đoạn cao độ, dầm theo owner O01, CP gross/cut/đầu dầm; không lấy raw map tính lại |
| G8-P05 | stairs.stair_works và riêng secondary.roof_works + helper/test | Bản/bậc/chiếu nghỉ/dầm thang; mái BT theo diện tích/dày; giữ phạm vi loại trừ M01 |
| G8-P06 | steel.schedule_works/steel_works + helper/test | Bảng thép, tấn nhập tay, hàm lượng; quy đổi có nguồn, giữ thứ tự ưu tiên và basis đầu vào legacy |
| G8-P07 | walls.wall_works + secondary L1/N03 emitter/mutation hooks, caller nếu cần + helper/test | Chỉ sau review vòng đời net/rounding: tường, trát, lanh tô, giằng hợp, sê nô và CP liên quan |

Đề xuất mở P02 tiếp theo sau consumer lót ổn. Không cần chờ P03 mới thiết kế P04/P05, nhưng mỗi file có một writer và mỗi mảnh được 01 mở rõ. P07 là cổng riêng, không ghép vào P05 chỉ vì cùng file secondary.py.

## 19 mã công tác chưa đồng nghĩa đủ 19 producer

Manifest đã đối chiếu đủ 19 khóa WORKS hiện hành, không thêm mã mới. Phải kiểm theo **nhánh emitter**, không chỉ kiểm code có detail:

- BE_TONG_LOT: lót móng đã có; lót nền trong areas chưa có.
- COP_PHA: 9 họ cha MONG/COT/DAM/SAN/CAU_THANG/GIANG_TUONG/SE_NO/MAI/LANH_TO. CP SAN còn dòng âm `_slab_form_deduction`; không coi xong diện tích sàn là đã xong CP SAN.
- COT: cột mặt bằng và bảng thống kê có hai nguồn/công thức riêng. Khi có bảng, cột KT không được tính thêm.
- COT_THEP: bảng kg, lượng tấn nhập và hàm lượng là ba basis riêng. Không dùng một hàng hàm lượng để chứng minh có diễn giải bảng Ø.
- DAO/DAP có cả dòng hố và dòng trừ giao; trường hợp thiếu vị trí phải ghi đúng giới hạn nguồn, không vẽ vị trí giả.
- O01 có dòng DAM/CP pending. Khi muốn phủ toàn bảng, cần release đúng hunk emitter pending để có dòng detail unknown, không đổi resolver hoặc gán quantity0.

Mức phủ cần báo số dòng thuộc snapshot có components / aggregate / unavailable / None, cộng riêng dòng thiếu/ngoài phạm vi. Không tính reference vào số dòng khối lượng hoặc tính mã có sẵn là đã tự nhận. Hạng mục mà engine hiện không sinh WorkItem không tự được coi là đã phủ; không thêm khối lượng để làm đẹp tỷ lệ.

## Nguồn và phép trừ phải giữ

| Nhóm | Nguồn đầu vào | Phép tính/khấu trừ phải diễn giải |
|---|---|---|
| Sàn/nền | PlanParams nhập, PlanGeometry suy, nguồn kín/bao lồi; void và lớp nền | outline−void; diện tích×dày; chưa có void phải unknown, không chứng nhận legacy đang dùng0 là net đủ |
| Chống thấm | Phòng WET, diện tích/chu vi, cao cổ; diện tích ban công nhập | Diện tích đáy + chu vi×cao cổ là hai contribution cùng m²; không đổi sang thể tích |
| Móng | FoundationItem count, tiers/top_*, volume override, source | Volume nhập thắng geometry: geometry reference; hộp/vát tính theo công thức đang có, không đoán L/W/H từ V |
| Đất | pit, cao độ tự nhiên/đáy/lót, margin, slope, neck, positions | Đắp=hố−lót−móng−cổ; trừ overlap riêng; tích phân SLICES200 giữ nguyên |
| Cột | Column hình học hoặc ColumnSpan count/b/h/z_from/z_to | BT và CP theo chiều cao hiệu lực; đầu dầm trừ CP có nguồn; giữ đoạn cao độ âm |
| Dầm | Chỉ argument beam_works đã qua O01 và beam_joints | gross/net/cut, web height, framed area; tuple nguồn của Beam thật, không gán mã đối tác chưa có |
| Thang | Số bậc, mặt bậc, rộng vế, cao tầng, dày bản, chiếu nghỉ/dầm | Bản+bậc+chiếu nghỉ+dầm; CP từng phần. Không biến dimensions thành contribution rồi cộng lại tổng cùng lúc |
| Mái | Roof area/thickness/source/replaces_slab_of | Thay mái loại SAN/CP cũ cùng object/detail, không để hàng detail mồ côi |
| Thép | RebarRow.kg/evidence hoặc tấn nhập; hàm lượng và WorkItem BT được chọn | kg→tấn một lần; kg đã là tổng không nhân total_bars lần nữa; không giả Ø cho ratio/manual |
| Tường/lanh tô | ReviewWall/Opening, system thickness, column overlap, cao xây | Gross−cửa−lanh tô−cột; L1 đổi đồng thời XAY/LANH_TO/CP; N03 trừ hợp hoặc treo net D |
| Giằng/sê nô | LinearMember/source/context/z, normalize union, support gate | Raw giằng reference không cộng thêm union. CP đáy chưa chứng minh vẫn D, không dùng0 |

## Cổng khó: raw, rounding và net cùng số legacy

1. **Raw là lượng của phép tính hiện hành trước lần round đang xét.** Không hứa mọi nguồn trung gian đều chưa làm tròn. `steel_works` hàm lượng hiện dùng WorkItem.quantity BT legacy đã round; detail phải ghi basis này, không thay bằng raw BT mới vì sẽ đổi vật tư.
2. L1 hiện round từng lần trừ/hoàn trả; N03 lấy XAY.quantity đã round làm đầu vào. Vì vậy không được lấy gross geometry raw rồi gọi kết quả trừ đó là chính chuỗi net legacy mà không nêu ranh giới làm tròn.
3. **BA01 đã chốt:** P06/P07 dùng source_quantity có nhãn “đã round từ bước trước”, geometry chỉ reference. Không mở thay đổi precision engine và không thêm residual bù vào dòng cuối để ép khớp.
4. Finalizer hiện phát hiện quantity/unit thay đổi so capture và hạ scope D/missing. Nó **không phát hiện raw net đổi nhưng cùng round3**. Fixture bắt buộc ở P07: raw0,32254 trừ0,00003 thành0,32251 trong khi cả hai legacy vẫn0,323. Hook mutation phải rebuild detail theo dữ liệu thật dù quantity legacy không đổi; thiếu hook thì test phải thất bại.
5. Không bật validate_assignment toàn WorkItem, không sửa assign_status/N03 để né lỗi. Finalize từ dump/constructor vẫn nằm sau net/status/scope. DTO khớp số chưa chứng minh đúng nguồn hoặc đã được người kiểm xác nhận.
6. Từng lớp/cấu kiện chia một group có thể có sai khác float do thứ tự nhân/cộng. Giữ nguồn và phân biệt sai khác biểu diễn với rounding nghiệp vụ; cần policy/tolerance được duyệt, không chia scalar tổng theo tỷ lệ để giả từng cấu kiện.

## Những hunk chung phải xin riêng

- `_neg`: capture sau khi tạo số âm hiện hành, sign=-1 với trị tuyệt đối; không gắn ledger legacy0 rồi model_copy quantity âm mà để stale detail. Caller hố giao và CP SAN phải có regression riêng.
- `_slab_form_deduction`: nguồn dầm/cột thật của chính scope; không mượn geometry KC chưa căn chỉnh để trừ sàn KT. O02/alignment vẫn ngoài G8.
- `drop_slab_under_roof`: loại cả work/detail; không tự gộp dữ liệu hai nguồn hoặc phục hồi hàng sàn đã bị loại.
- `lintel_under_beam`, `deduct_ties`: phải mở cùng emitter tường và giữ các hàm normalize/axis/support/gate N03 bất biến; chỉ trace/rebuild detail đúng bước được duyệt.
- `walls._work`: chưa cần mở generic capture cho mọi code. Khi producer chưa có receipt, để None/aggregate có nguồn; không dùng quantity legacy làm raw để giả hoàn thành.
- `takeoff`: không sửa owner O01 hoặc price_source; nếu cần bind/finalize thêm hook thì diff phải chứng minh đúng hunk và giữ consumer snapshot.

## Dữ liệu/kiểm thử cần cho từng mảnh

- P02: diện tích gộp, lỗ None/0/đã đo, nền nhiều lớp, WC đủ/thiếu cao cổ, chu vi thật; mái thay sàn, ban công0 theo đúng nhánh legacy. Không tự sửa các nhánh hiện dùng truthiness trong metadata.
- P03: lớp hộp/vát, volume override, âm/0/thiếu, cổ móng dưới đất; vị trí đủ/thiếu/mismatch, hai hố giao và không giao.
- P04: hai nguồn cột; cao độ qua±0; dầm net/cut/framed; 1/2 view O01 chồng tầng có owner và pending; CP không đủ nguồn vẫn partial.
- P05: nhiều vế/thang, landing0, dầm thang thiếu tiết diện, mái BT thay sàn; mái khung và thang cốn/xoắn tiếp tục ngoài M01.
- P06: dòng thép kg biết/thiếu, Ø rõ/không rõ, tấn nhập, ratio0/thiếu; có parent D và known part. Giữ dữ liệu chưa được người kiểm xác nhận, không đổi da_kiem.
- P07: cửa/cột/giằng kết hợp, b100/b220/b300, support đủ/thiếu, union cùng trục/lệch trục/ngữ cảnh, L1 nhiều lỗ và raw-net-cùng-round. Giữ hồi quy N03 đã đạt.

Mỗi mảnh: snapshot/diff/exact manifest trước focused, log/mã thoát/hash trước-sau, source/status/totals/materials legacy parity, JSON round-trip cùng payload. Chỉ xếp focused theo 01; không full, CAD/DB hoặc HTTP outside đã bị từ chối. Consumer UI/Excel và ACTUAL có cổng riêng, không dùng synthetic để thay người kiểm chuyên môn.

## Bàn giao lượt chuẩn bị

Không sửa source hoặc chạy test ở lượt này. Đã lập manifest đủ19WORKS và các nhánh CP/shared mutation; source lót đang giữ nguyên cho 02/09. Đề nghị01 mở từng hunk sau consumer lót; policy đầu vào legacy cho P06/P07 đã được BA chốt như trên. Cần review cụ thể lifecycle/rebuild trước P07, không coi quyết định policy là release source. Các mảnh còn lại chỉ là đề xuất, chưa code-ready hoặc nghiệm thu.


## Bổ sung G8-SUM — tổng raw/coverage backend cùng snapshot

Theo01, thêm một mảnh backend ngang sáu mảnh producer: [hợp đồng tổng raw](../raw_group_contract/CONTRACT.md). Đây là mảnh thứ7 trong kế hoạch triển khai, không phải producer thứ7 hoặc mã công tác mới. Đề xuất bố trí sau gate consumer lót và trước mở rộng P02;01 quyết định lịch/hunk.

Grouper đọc finalized WorkItems của cùng snapshot, partition theo stage/code/variant/unit/source/basis tương thích cùng parent/spec cần thiết; không đủ quy cách thì cô lập work, không đoán để gộp. Mỗi detail.known_part_raw góp một lần; total_raw chỉ khi mọi thành viên đủ. Không lấy tổng legacy làm raw, không cộng reference hoặc nhân count/repetitions lại.

Coverage tách components/aggregate/unavailable/no_detail và rows biết/thiếu/reference; row_id scoped trong work+snapshot, không khử trùng r1 giữa hai công tác. UI/Excel nhận summary backend gắn cùng payload đã kiểm, không tự cộng số đã format/round. ParentC vẫn có thể ledgerpartial ở P02 voidNone; consumer phải hiện đúng điều đó, không đánh dấu enginecomplete đã được sửa.

Cần source release riêng: DTO summary/group/count + builder/hash + parent binding trong takeoff/RoughResult + pure tests, sau đó02/09consumer. Chưa sửa source ở bước chuẩn bị này. Tổng raw/coverage cũng không thay KPI hồ sơ thật hoặc chứng nhận vật tư legacy chạy từraw.
