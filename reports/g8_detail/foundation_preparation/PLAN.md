# G8-P03 — móng/đất: chuẩn bị, chưa mở canonical

04/11/2026. G8-SUM đã được01 nhận code/pure189/review14; sáu file SUM đang HOLD cho consumer. Mảnh P03 chưa có quyền ghi source hoặc chạy focused. BASE_READ_HASH.json ghi mốc đọc năm file liên quan; không sửa các file này trong lượt chuẩn bị.

## Phạm vi đề xuất nhỏ nhất

1. foundations.py: chỉ receipt/emit MONG, CP móng, DAO_DAT, DAP_DAT và hai caller trừ giao đất. Bảo toàn emitter lót đã nhận.
2. quantity_details.py: thêm builder móng/đất, giữ AST mọi helper lót/area/finalize/summarize đã có.
3. tests/test_rough_foundation_details.py mới; regression foundations/details/partial/SUM theo slot01 sau release.

**Không sửa `_neg` dùng chung trong P03a.** Chỉ bọc hai kết quả `_neg("DAO_DAT", extra)` và `_neg("DAP_DAT", extra)` tại caller đất bằng receipt extra đã tính. Như vậy raw/sign/legacy âm được capture sau khi `_neg` đã tạo lượng âm, không gắn detail legacy0 rồi model_copy số âm gây stale.

CP sàn âm từ takeoff._slab_form_deduction **vẫn quantity_detail=None**, là gap có chủ đích và SUM tiếp tục đếm no_detail/incomplete. Không mở takeoff, O01, N03, models, quantity_summary, price, norm/catalog hoặc BOQ để đóng gap này trong P03a. P03b nếu cần generic `_neg`/CP SAN phải xin scope riêng; không nhận toàn bộ CP đã đủ chỉ vì đã có CP móng.

## Capture q: đúng một lần, không tính lại geometry

| Dòng | Giá trị đang được engine dùng | Receipt/diễn giải đề xuất |
|---|---|---|
| MONG volume override | f.count × f.volume_m3 | Một contribution source_quantity; volume/count có nguồn. Tiers/LWH chỉ reference, không gọi lại volume geometry để khẳng định override |
| MONG tiers/hộp | f.count × sum(tier_volume_m3(t)) | Capture **giá trị return thực tế** từng tier trong chính lượt generator/sum cũ; mỗi geometry calculator gọi một lần |
| CP móng | f.count × sum(tier_formwork_m2(t)) | Capture từng face return trong chính lượt cũ. Mặt vát return0 theo quy tắc hiện hành, không tính lại chu vi để thay số0 đó |
| DAO | f.count × v_pit | v_pit là kết quả pit_volume_m3(p) đã có; ghi đáy/đỉnh/sâu/taluy nguồn, không tính thể tích lần hai từ dimensions |
| DAP đủ | f.count × fill; fill=v_pit−lean−one−neck | Tái dùng bốn scalar đang có, bốn contribution signed; không lấy Vhố và gán kích thước thành Vđắp |
| DAP thiếu/âm | quantity=None, missing giữ nguyên | Thành phần biết vẫn được giữ; phần thiếu unknown, totalNone. Giá trị âm là chẩn đoán, không gán0 hoặc sửa hố để làm dương |
| Trừ hố giao | extra=pit_overlap_m3(pits), rồi `_neg` | Capture extra có sẵn một lần; row sign−1, raw_quantity=abs(extra); không tích phân lại |

Receipt tiers cần giữ thứ tự đánh giá/sum và branch override. Cách nhỏ: wrapper trace gọi calculator cũ một lần, append giá trị nhận được rồi return chính giá trị đó vào sum. Không materialize lại một danh sách đã tính volume lần nữa; override không chạy volume calculator vốn bị bỏ qua ở nhánh cũ.

Khối lượng component có count được nhân đúng một lần từ receipt per-tier/per-pit; row.raw_quantity đã gồm count, dimensions.count chỉ hiển thị. Lượng aggregate thực tế trước `_work` luôn giữ ở reference như policy P02 nếu tách các thành phần có khác biểu diễn float. Tổng ledger dùng Decimal từ đóng góp; không residual, không dung sai giả hoặc sửa engineprecision. Chưa lấy WorkItem.quantity đã round3 làm raw.

Nguồn f.source giữ nguyên hoặc ghi rõ thông số người dùng nhập. Thông tin này không trở thành bằng chứng đã kiểm độc lập chỉ vì có chuỗi file/hình. Row_id scoped work/snapshot; không registry mới, không suy số móng từ positions khác count.

## Điều kiện nguồn cần giữ

- `tiers_of`: tiers thắng L/W/H; không có đủ lớp/LWH thì unknown. Không suy L/W/H từ volume override.
- `positions`: chỉ đưa vào pits theo nhánh hiện có khi len(positions)==count. Thiếu/mismatch giữ cảnh báo và không giả vị trí/cặp giao. Dữ liệu receipt có thể giữ tên móng, chỉ số vị trí, x/y và nguồn đã dùng bên cạnh danh sách pits, **không thay tuple đầu vào hoặc thuật toán tích phân**.
- `SLICES=200`, SAME_SPOT_MM, hàm prismoid/union, cốt tự nhiên/đáy/lót và mở rộng/taluy giữ nguyên. Giá trị tích phân số chỉ là phép tính hiện hành, không gọi là giao hình học chính xác tuyệt đối hoặc chứng minh độ chính xác bản vẽ.
- Ngưỡng extra>1e-4 giữ nguyên; không tự thêm dòng trừ nhỏ hơn ngưỡng để “đóng raw”. P03 metadata không sửa thuật toán engine.
- Cổ móng: buried=0 thì neck=0 có căn cứ từ nhánh hiện hành dù chưa có b/h; không nhập kích thước giả bằng0. Buried>0 thiếu tiết diện thì phần cổ unknown, không dùng0 thay.
- Không có cấu hình earth thì engine hiện không emit DAO/DAP; P03 không tạo dòng/quantity mới để tăng coverage. Phạm vi inventory M01 là cổng riêng.
- Đất chưa có phân loại/biện pháp, SUM vẫn isolate theo work với compatibility_pending; điều này không làm quantity_known thành unknown. Không thêm mã/giá/định mức đất ở P03.

### Điểm cần01 chốt trước source: thiếu vị trí và net toàn phạm vi

Đề xuất khi có nhiều hố nhưng positions thiếu/mismatch: DAO/DAP giữ gross/phần tính được và cảnh báo legacy, song detail.scope_complete=False/totalNone vì chưa kiểm giao; không tạo WorkItem trừ giả hoặc phân bổ giao theo tỷ lệ. Có thể giữ reference unknown ghi lý do chung trong detail mỗi work, không coi đó là lượng0. Điều này giống P02 parentC nhưng ledgerpartial, không sửa trạng thái engine.

Không tự áp điều kiện này lên một hố duy nhất hoặc count0 khi không có khả năng giao; cần receipt số hố của đúng các foundation đã đi qua dedup và nhánh hiện hành. Đây là đề xuất metadata cầnBA duyệt, chưa triển khai hoặc chạy test, không dùng số lượng positions làm số lượng móng thay count.

## Thứ tự net/finalize

Emit receipts từ scalar gốc → gắn parent quantity legacy thực tế → thêm dòng giao âm riêng khi engine thật sự emit → assign_status/finalize hiện có → SUM hiện có.

Không mutate quantity sau capture mà giữ gross detail; nếu có bước mới làm raw thay đổi cùng legacy round thì phải rebuild từ receipt ở chính mutation. P03a dùng scalar net đã có trước emit, không mở L1/N03. Parent quantityNone/D/missing chỉ được known_part với totalNone; giữ nguyên quantity/status/missing/warnings legacy.

## Dữ liệu và regression bắt buộc khi được mở

- Móng hộp một lớp, nhiều lớp, lớp vát và lớp top bằng đáy nhưng fieldtop được khai báo (giữ cách tính CP cũ).
- volume override có/không tiers; thiếu chiều dài/rộng/cao; count0/âm theo nhánh legacy; f.source thật/để trống.
- Cốt tự nhiên/đáy/lót, margin/taluy, mặt móng qua cốt tự nhiên; neck0 có căn cứ và neck thiếu khi chôn dưới đất.
- Hai hố không giao, giao, trùng vị trí, thiếu positions, count mismatch; giữ SLICES200 và ngưỡng hiện hành.
- Dòng trừ DAO/DAP sign âm có q raw trước round; CP sàn âm vẫn no_detail ngoài scope.
- Decimal component vs float aggregate reference; không nhân count/repetition lại; quantityNone không được detailfull; coverage/SUM giữ phần biết, group đất isolate có lý do.
- So toàn payload legacy quantity/status/missing/warnings/totals/materials/giá trước/sau. AST calculator/helper lót/area/finalize/O01/N03/attach_prices không đổi ngoài receipt hunk đã được duyệt.

Trước focused: manifest/diff/exact hashes/source examples cho01/14; chỉ chạy slot pure được cấp, không HTTP/DB/CAD/full hoặc reload31112. Mã P03 chưa triển khai; các case trên là kế hoạch kiểm, không kết quả đã chạy.
