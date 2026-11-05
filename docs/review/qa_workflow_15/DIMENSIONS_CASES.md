# Ca kích thước chờ chốt schema cuối

Trạng thái: PREPARED / NOT_RUN bởi QA15. Đã nhận diện bàn giao schema SOURCE_READY của 03 tại `reports/work_dimensions/CONTRACT.md` và manifest `SOURCE_READY_HASH.json`, được ghi nhận trong nhật ký điều phối 01. Model hash `ea57ec73e239d73b6fd60ae7c4f8d0c5bc1e2994ba3e6f1401d5984e2b270a92` khớp mốc đã đọc. Đây là hợp đồng bàn giao để hoàn thiện ca, **chưa là freeze tích hợp hoặc release QA15**. Nếu có bàn giao sửa tiếp phải cập nhật theo 01.

Đã đọc kết quả owner tại `reports/work_dimensions/result.json`: exit1, 227 passed/1 failed, 228 collected, 224 hash trước/sau không đổi. Không phải QA15 tự chạy; chưa dùng kết quả này để nghiệm thu. Chưa phân tích nguyên nhân fail trong lượt docs này, chờ owner/01 bàn giao sửa và terminal cuối.

01 xác nhận schema bàn giao trên vẫn WIP, có thể thay đổi sau terminal: 14 đã đối chiếu 11 hash và báo `_neg` trong foundations chưa có dimension deduction như contract/test yêu cầu; 03 đang xử lý theo điều phối. Đây là blocker bàn giao do 01 cung cấp, không phải phát hiện runtime của QA15. DIM05 phải đối chiếu riêng dòng trừ foundations sau sửa, nhận manifest/patch/terminal mới trước đánh giá. Giữ `protected_N03.json` và `backend_dimensions.patch` làm tài liệu đối chiếu của owner, không tự áp patch.

Không import model/probe/TestClient/full/browser/API; không upload Tân Bình. Chỉ hoàn thiện và chạy ca khi 01 giao lượt sau freeze. Phiên 05 sole full; 02 giữ browser/API restart.

## Cập nhật bàn giao được đọc ngày 05/11/2026

QA15 đã đọc `reports/work_dimensions/BAN_GIAO.md`, `CONTRACT.md` và `FINAL_HASH.json`. Bàn giao cuối của owner thay trạng thái WIP nêu trên: attempt1 vẫn giữ 227 passed/1 failed; attempt2 được owner ghi nhận 231 passed/EXIT0, 224 dependency không đổi. Review14 theo bàn giao đã đối chiếu 11/11 hash và khép hai finding `_neg`/nguồn chiều cao. QA15 chưa tự thực thi hoặc xác minh checkout hiện tại khớp manifest; không dùng `result.json` ở thư mục gốc (attempt1) làm kết quả cuối.

- DIM05: kiểm `_neg` có record `basis=deduction`, không có cạnh hình hộp giả; đối chiếu quantity âm vốn có, không cộng lại reference/union/deduction.
- DIM03/DIM06: kiểm nguồn chiều cao tường từ Beam manual/structural thực dùng, cùng explicit params depth=0; nhánh fallback `req.structural_beams` chưa có assert riêng theo owner, cần ghi giới hạn coverage.
- DIM06: ví dụ dầm trục 4 m, trừ 0,2 m, net 3,8 m; height 0,4 m và concrete_height 0,3 m; quantity BT 0,228 m³ chỉ là oracle fixture bàn giao, không làm đáp án hồ sơ thật.
- Trước chạy vẫn cần 01 xác nhận freeze tích hợp, manifest áp dụng và chính xác lượt/lệnh QA15. Mốc FINAL của backend không tự cấp quyền chạy. Trạng thái QA15 giữ PREPARED / NOT_RUN; không full/TestClient, browser/API restart hoặc retry upload Tân Bình.

## Schema quan sát để đối chiếu với bàn giao cuối

- `basis`: input/reference/union/deduction; `repetitions` integer >=1, mặc định 1; `count` riêng cho một lần.
- Trường số optional: count, length_m, gross_length_m, deducted_length_m, width_m, height_m, floor_height_m, bottom_level_m, top_level_m, slope_ratio, faces, concrete_height_m, thickness_m, top_length_m, top_width_m, slope_length_m, diameter_m, area_m2, opening_area_m2, net_area_m2.
- `source`, `field_sources`, `missing_fields`, `not_applicable_fields`, `label`, `note`; model khai báo không nhận inf/nan.
- Validator hiện phân loại field truyền None là thiếu, field số không truyền là không áp dụng khi không có hai danh sách explicit; khi có danh sách thì giữ chúng qua round-trip. Nguồn chung được dùng làm fallback trước nguồn theo field. Đây là hành vi source đã đọc, chưa chứng minh producer/API/UI tuân thủ.

## Ca sẵn sàng triển khai sau release

**Cập nhật ưu tiên mới:** yêu cầu UI/Excel Tiên lượng G8 đã thay tiêu chí BOQ MVP (a) cũ trong tài liệu này. Ca G8_M1_ACCEPTANCE.md là cổng riêng bắt buộc; DIM10 và ghi chú cũ không miễn kiểm9 dòng/bốn vật tư/UI+Excel mở lại. Schema detail rows/precision chờ03/01 chốt; không tự sửa exporter (09 sở hữu).

Tất cả dữ liệu ví dụ là SYNTHETIC, không làm đáp án công trình. Expected cuối cần đối chiếu hợp đồng 01 chốt, không mặc định mọi hành vi WIP đều đúng.

| ID / nối ma trận | Input hoặc thao tác dự kiến | Oracle cần chứng minh |
|---|---|---|
| DIM01 / D03 | Producer truyền height_m=None, bỏ width_m; bản khác height_m=0 | Phân biệt thiếu/không áp dụng/0 qua producer → JSON → UI; không đổi null thành 0; 0 chỉ hợp lệ theo miền của công tác |
| DIM02 / D03 | Serialize và restore cùng dimensions với danh sách missing/not-applicable explicit | Danh sách và giá trị giữ nguyên sau round-trip; không phân loại mọi null thành thiếu; field không đồng thời bị trình bày thiếu và không áp dụng |
| DIM03 / D01 | length từ bản vẽ, height nhập tay, thickness từ tham số; nguồn chung và override từng field | Nguồn đúng từng field, không ghi nguồn đo trực tiếp cho giả định; nguồn thiếu hiện rõ; không nâng trạng thái A/B/C/D |
| DIM04 / D07 | count=2 cho một lần, repetitions=3; hai cấu kiện khác kích thước | Giữ count=2 và repetitions=3 có nhãn; không nhân cả chiều dài và count/repetitions; quantity cuối do pipeline tính, không tái tạo từ metadata |
| DIM05 / D04,D08 | input/reference/union/deduction xuất hiện cùng dòng công tác có raw và net khác nhau | reference không thành lượng net; union/deduction không thành cấu kiện mới; quantity/status/missing cuối vẫn là căn cứ; không cộng raw lần nữa |
| DIM06 / D02,D04 | floor_height_m khác height_m; gross_length_m khác length_m và có deducted_length_m | Nhãn cao tầng/cao xây, dài gộp/net/khoản trừ đúng nghĩa; đối chiếu expected producer do 03/14 bàn giao, không suy công thức chung cho mọi loại |
| DIM07 / D05,D06 | bottom/top level có thể âm, móng vát top_length/top_width; thang có slope_length; sàn chỉ area/net/opening | Không cấm cao độ âm chỉ vì là số âm; không biến độ dốc/số mặt thành mét; không ép mặt bằng chữ nhật; trường thiếu không sinh kích thước giả |
| DIM08 / D03 | NaN/Infinity; repetitions=0/âm/phân số; basis ngoài enum | Producer/API không phát JSON không hợp lệ; từ chối input không hợp lệ theo hợp đồng, có lỗi rõ; không tự sửa thành số giả |
| DIM09 / D01,F02 | Legacy WorkItem không dimensions; dimensions rỗng; quantity có số nhưng missing/D | Giữ tương thích lượng/status; báo không có kích thước trực tiếp; không nâng đủ vì có số hoặc vì người dùng đã xem |
| DIM10 / A01 | API có dimensions nhưng BOQ chưa có sheet metadata tương ứng | Đối chiếu lượng/đơn vị/nguồn thực sự được export; ghi riêng metadata không xuất, không tuyên bố BOQ đủ dimensions chỉ từ API |

## Dữ liệu cần nhận từ 01/03/14 trước chạy

### Oracle đã cụ thể hóa theo CONTRACT của 03

- DIM04: count×repetitions khi áp dụng; count0/None không thành1; không nhân length.
- DIM05: không cộng reference+union; directvolume ưu tiên thì kích thước chỉ reference; deduction không cạnh giả. Lượng/status/missing lấy WorkItem cuối, không tái tính net từ metadata.
- DIM06: length_m dầm = net, gross_length_m = trục, deducted_length_m = khoản trừ; height_m = toàn tiết diện, concrete_height_m = cao tính BT. Nguồn phải đúng nhánh Beam/params thực dùng.
- DIM07: slope_ratio/faces/count/repetitions không đơn vị; các chiều dài/cao độ/Ø theo m. Cao độ có dấu; thang length_m ngang, slope_length_m nghiêng; thép hàm lượng/manual không có hình học thanh thì dimensions=[].
- DIM08: hợp đồng từ chối NaN/±inf, không đổi0; route compute dự kiến trả422 cho ValidationError. HTTP chỉ kiểm bởi owner/lượt được 01 giao, QA15 không mở TestClient.
- DIM10: 00/01 đã chốt BOQ MVP phạm vi (a): cùng snapshot đã kiểm, parity công tác/cấu kiện/tầng, lượng/đơn vị, công thức/nguồn, trạng thái/phần thiếu; ít nhất dòng đủ và partial. **Không yêu cầu sheet dimensions riêng**, không mở sửa boq.py chỉ vì chưa có metadata đầy đủ.
- Sàn chưa biết void: net_area_m2=None theo metadata; giới hạn engine về độ đủ của void chưa được đóng bởi gói dimensions. Ghi riêng cho 01 nếu nghiệm thu gặp, không nhận metadata thay công thức sửa lỗi.

1. Exact schema cuối và hash freeze; xác nhận ý nghĩa các trường nguồn/missing/not-applicable, đơn vị slope_ratio/faces, gross/net theo từng producer.
2. Payload chuẩn từng basis, ca lặp tầng và ca raw/net N03; expected quantity độc lập với tích dimensions.
3. Hợp đồng legacy/round-trip và hành vi invalid input; danh sách focused được phép, môi trường cô lập và người thao tác.
4. Ví dụ UI/BOQ được cam kết hỗ trợ; ghi rõ phần metadata chưa export thay vì suy ra đã đủ.

Khi nhận schema cuối: đối chiếu từng dòng trên, cập nhật expected và mốc hash, báo 01 các delta; chỉ ghi PASS khi có bằng chứng thực thi đúng lượt được giao.
