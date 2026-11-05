# G8 — hợp đồng chi tiết đề xuất, chờ 01 duyệt

03/11/2026. Chỉ thiết kế/staging; không sửa baseline O01. Mục tiêu: UI và Excel đọc cùng chi tiết từ kết quả đã kiểm, không tự bóc lại hoặc parse chuỗi formula.

## 1. Dữ liệu thêm nhỏ nhất

Đề xuất `WorkItem.quantity_detail: WorkQuantityDetail | None = None`. Payload cũ vẫn đọc được; không có detail phải ghi “Chưa có diễn giải chi tiết”, không chuyển dimensions thành dòng đóng góp giả.

`WorkQuantityDetail`:

| Trường | Ý nghĩa |
|---|---|
| unit | Đúng đơn vị WorkItem, không đổi unit engine |
| rows | Danh sách dòng cộng/trừ và tham khảo có nguồn |
| detail_level | components / aggregate / unavailable; có tổng không chứng minh đã có diễn giải từng cấu kiện |
| known_part_raw | Tổng các contribution đã biết, chuỗi Decimal; None khi chưa biết dòng nào; 0 là số 0 đã biết |
| total_raw | Chỉ có khi toàn phạm vi đủ; còn pending thì None |
| complete | Đủ toàn phạm vi, gồm dependency/scope của công tác; không chỉ nhìn các dòng đang có số |
| scope_complete | Producer xác định phạm vi/dependency đủ; không suy từ việc rows đang có số |
| legacy_quantity | Bản sao số WorkItem.quantity hiện hành để đối chiếu, không ghi đè |
| legacy_delta | known_part_raw − legacy_quantity nếu cả hai có số; chỉ giải thích chênh, không “bù” vào dòng cuối |

Mỗi `QuantityDetailRow`: row_id, label, group, role, sign, unit, raw_quantity, method, dimensions, conversion, factors, expression, sources, missing. `raw_quantity` là **trị tuyệt đối sau khi đã tính count/lặp/hệ số/quy đổi**, chuỗi Decimal hoặc None; `sign` chỉ +1/-1. Consumer không nhân lần nữa. Khoản trừ dùng sign=-1, số 0 không bị coi là trống. Không clamp tổng âm thành 0 để làm khớp.

- role=contribution mới vào tổng. role=reference giữ căn cứ/raw geometry nhưng không cộng. N03 hai giằng raw/reference + một đoạn hợp/union chỉ đoạn hợp góp lượng; không nhân chồng raw và union.
- method mô tả cách producer đã tính: box, area, perimeter, count, prismoid, union, steel, ratio, source_quantity. expression chỉ để giải thích, không thực thi/parse; không tạo DSL/công cụ tính thứ hai.
- dimensions tái dùng ý nghĩa WorkDimensions: không áp dụng khác thiếu, count khác repetitions, cao toàn tiết diện khác cao tính BT, dài gross/net/cut rõ. Bản staging đã tái dùng WorkDimensions có kiểu; không thêm bộ dimension song song.
- conversion ghi from_unit, to_unit, factor và source; to_unit phải là unit dòng. Đây là quy đổi vật lý chính xác, khác hệ số phụ/hao hụt. Tái dùng quy tắc quy đổi hiện có khi phù hợp, không import data_check vào engine hoặc tạo registry đơn vị tổng quát.
- factors ghi tên, giá trị, nguồn, phần áp dụng; [] nghĩa không áp dụng hệ số phụ, không tự biến ô hệ số nguồn trống thành “đã xác nhận hệ số1”. Count/repetitions là dữ liệu riêng, không lặp vào factors.
- raw_quantity thiếu phải có missing. Lỗ cửa chưa biết cao không được nhập quantity0 hoặc bỏ dòng. Thép theo hàm lượng có method ratio, không giả đường kính/chiều dài; thép theo bảng giữ nguồn và quy đổi kg/tấn.

## 2. Snapshot, khóa và cây nhóm

- Detail được sinh tại producer và gắn vào chính WorkItem trước khi lưu/xác nhận. UI/Excel nhận cùng payload đã kiểm; không chạy producer lại lúc export hoặc chọn vật liệu.
- work_key/row_id chỉ ổn định trong **một result snapshot**: dùng index công tác/dòng hoặc ID nguồn có sẵn, kèm định danh kết quả lưu/phiên bản kiểm hiện có. Không tuyên bố ID ordinal tồn tại qua sửa file, đổi tầng hoặc tính lại.
- 02/01 chốt định danh result đã kiểm đang có; không tự thêm “reviewed=true” hoặc coi hash là phê duyệt của người kiểm. Backend chỉ phát dữ liệu chi tiết; trạng thái xác nhận giữ hợp đồng luồng hiện tại.
- Cây: hạng mục theo WorkItem.stage → công tác (code, variant/cấu tạo/đơn vị phải tương thích) → plan/vị trí → row.group/label. Không cộng m²/m³/tấn; không nhập hai mác/định mức khác nhau chỉ vì cùng code.
- Raw geometry maps O01 không phải nguồn khối lượng hiệu lực. Dùng WorkItem đã được resolver chọn, cùng evidence view → tầng; không lặp raw map để sinh thêm hàng.

## 3. Precision và tương thích

- Producer truyền **chính giá trị q trước `_work` round3**, không suy ngược từ quantity đã round hoặc formula. Đưa q ra ngoài biến rồi dùng cùng q cho công thức legacy và detail; không sửa phép tính engine để ép mẫu M1.
- Giữ WorkItem.quantity, totals, vật tư, pricing và optimizer legacy trong gói G8 đầu. Ledger có tổng raw riêng và chênh legacy; đổi nền precision/vật tư là quyết định tính toán riêng cần 01 duyệt, không ghép im lặng vào metadata.
- Decimal string là dữ liệu API chuẩn của detail. Phần tổng detail cộng chuỗi Decimal ở backend. UI chỉ format hiển thị; Excel đọc đúng giá trị, không cộng các giá trị đã format. Excel có giới hạn chữ số số học, 09 cần giữ raw string truy vết khi vượt khả năng số của Excel.
- Producer hiện dùng float: chuyển `str(q)` giữ giá trị tính thực tế, không hứa đã phục hồi số thập phân thiết kế gốc. Sai khác float nhỏ và làm tròn hiển thị phải báo riêng, không sửa raw cell hoặc dùng residual giả.
- Sửa net sau `_work` (N03 deduct_ties, L1 lintel, các khoản _neg, drop slab/roof) phải cập nhật ledger cùng giao dịch tính; nếu chưa có hook hợp lệ thì đánh detail unavailable/aggregate, không giữ ledger gross như net đúng.

## 4. Ca M1 có nguồn, không hardcode sản phẩm

Nguồn read-only `DU TOAN M1.xls`, SHA256 `9312133c01b959194447ed90b8fdb0b889b98fb7bb5cc4a078a6da2ffe0f1ced`; đã kiểm file local khớp hash. Fixture riêng: `staging/M1_AF11110_REFERENCE.json`, từ evidence đã trích tại `docs/review/G8_M1_AF11110_EVIDENCE.json`.

- Tien luong I38/I39/I40/I42/I43/I44/I45/I47/I48 = 9 contribution, tổng **3.2515m³**, khớp J36. Các hàng37/41/46 là nhóm, không phải lượng.
- I38 = 0.3225m³, diễn giải 2×0.75×2.15×0.10. H trống giữ trống; không gán hệ số phụ đã duyệt.
- E42 và E43–45 có floating artifact trong số ô lưu. Fixture giữ raw cell, lấy I làm lượng nguồn có method source_quantity. Chưa trích công thức XLS, không gọi đây là audit công thức hoặc suy “E đã được làm tròn là số gốc”.
- Minh họa khác biệt: round3 từng 9 lượng I bằng Python hiện hành rồi cộng = **3.251**; cộng raw3.2515 rồi round3 = **3.252**. Cả hai đều phải phân biệt raw **3.2515**; không thêm dòng bù.

| Vật tư M1 | Mức dùng / m³ | Tích raw3.2515 | Số lưu workbook |
|---|---:|---:|---:|
| PCB30 kg | 197.825 | 643.2279875 | 643.228 |
| Cát vàng m³ | 0.572975 | 1.8630282125 | 1.863 |
| Đá4×6 m³ | 0.92865 | 3.019505475 | 3.0195 |
| Nước lít | 166.05 | 539.911575 | 539.9116 |

Mã AF.11110 và mã vật tư chỉ của fixture M1 có địa chỉ ô; không thay mã BE_TONG_LOT/catalog toàn cục. Chưa suy ra hao hụt hoặc hệ số1.025 nếu chưa có bằng chứng ô/công thức. 22×14=308m→3.08 đơn vị100m chỉ là ca quy đổi tham khảo, không đưa công tác ép cọc ngoài M01 vào product.

## 5. File/hunk dự kiến, chưa được sửa canonical

| File | Hunk cần mở | Điều giữ nguyên |
|---|---|---|
| rough/models.py | DTO detail và WorkItem.quantity_detail optional | WorkDimensions/status/quantity cũ |
| rough/quantity_details.py mới nếu 01 duyệt | Validation/sum contribution/provenance nhỏ, không engine mới | Không parse formula, không dependency mới |
| rough/walls.py | _work capture pre-round; wall/opening/column/lintel rows, CP lintel | Công thức, clamp/round legacy, nguồn chọn |
| rough/foundations.py | Lớp móng/hộp/vát/lót/hố/đắp và _neg | Không đổi tích phân hố hoặc CSV |
| rough/columns.py, beams.py | Các đoạn, net/gross/cut và CP/đầu dầm có hàng trừ riêng | Không đổi công thức giao |
| rough/areas.py, stairs.py | Diện tích/lỗ/lớp; vế/bậc/chiếu nghỉ/CP | Không tự suy lỗ sàn hoặc cấu tạo thiếu |
| rough/secondary.py | Chỉ hook detail tại emitter và hậu xử lý L1/N03 | normalize/deduct/support geometry/gate N03 giữ; cần 01/14 kiểm riêng |
| rough/steel.py | Bảng/hàm lượng và quy đổi exact có nguồn | Không đổi lựa chọn nguồn thép |
| rough/takeoff.py | Chỉ finalize/bind snapshot của detail sau mọi net mutation | O01 DTO/resolver/price_source giữ nguyên; chưa mở quyền ghi |
| tests/test_rough_quantity_details.py mới | Scalar/unknown0/negative deduction/unit/repetition/union/precision/roundtrip | Chờ slot test, không full/DB/HTTP ngoài quyền |

09 sole exporter rough/boq.py + export tests. 02 sole UI/TypeScript consumer và kiểm cùng snapshot. 03 không sửa hai vùng đó. Nên tích hợp theo 2 mảnh: DTO + _work + lót/M1 và đối soát raw; sau đó hook từng producer/net mutation. Không được gọi mảnh đầu là toàn phần thô đã có chi tiết đủ.

## 6. Bàn giao staging và cổng tiếp

`staging/quantity_details_proposed.py`: model/sum và hook lót nhận raw q, chưa import/nối vào source. `staging/M1_AF11110_REFERENCE.json`: 9 dòng, nhóm, số ô, lượng raw, 4 vật tư nguồn. **Đã kiểm staging thuần Python: 33 passed, EXIT0**, không HTTP/CAD/DB; 226 file canonical trước/sau không đổi hash. Chưa nối source, chưa phát API/Excel thật. Staging test và snapshot không chứng minh đã bao phủ toàn producer phần thô.

Đề nghị01/02/09 phản hồi tên DTO, Decimal string, row role/sign, snapshot identity, hierarchy và scope hai mảnh. Chỉ sau01 mở file/hunk mới chạm source; không đổi hash O01 đang chờ HTTP/tích hợp. Không chạy lại HTTP outside đã bị automatic approval review từ chối.

Validation đã khép: conversion finite/positive/nonempty; DetailFactor typed name/value/unit/meaning/source; WorkQuantityDetail tự kiểm signed sum/unit/known_part/total/complete/scope/delta ngay cả khi khởi tạo trực tiếp, extra keys bị chặn. Sum/delta dùng cùng localcontext đủ chữ số đầu vào, có test số thập phân dài hơn28 chữ số và round-trip.
