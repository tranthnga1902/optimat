# G8 — đề xuất exporter staging và manifest hunk 09

Ngày 03/11/2026. Trạng thái: ĐỀ XUẤT, chưa release canonical, chưa tạo hoặc nghiệm thu workbook.
Đã đọc `CONTRACT_DE_XUAT.md`, `staging/M1_AF11110_REFERENCE.json`, DTO staging của03,
`docs/review/G8_M1_AF11110_EVIDENCE.json` và QA15. Không sửa `src/optimat/rough/boq.py`.
Hai điều kiện validator của03 vẫn chờ01/03 chốt; tài liệu này không thay thế validator.

## Phạm vi hunk xin mở sau khi hợp đồng được release

| File | Hunk dự kiến | Ranh giới |
|---|---|---|
| `src/optimat/rough/boq.py` | Thêm hàm ghi sheet chi tiết và đối soát; gọi từ `boq_workbook` | Chỉ consume `WorkItem.quantity_detail` thuộc cùng result snapshot; không gọi producer, resolver, pricing hoặc parse formula |
| `tests/test_rough_boq_detail.py` mới | Kiểm tra serialization workbook và tương thích legacy | Không HTTP, DB, full suite hoặc UI |
| `reports/g8_detail/staging/exporter_preview_09.py` mới, nếu01 giao lượt | Adapter riêng fixture M1 và preview workbook | Không import vào product; không giả fixture là snapshot sản phẩm đã kiểm |
| `reports/g8_detail/staging/test_exporter_preview_09.py` mới, nếu01 giao lượt | Assertion riêng fixture và precision | Chạy focused theo slot01; không lấy kết quả làm nghiệm thu Excel/UI |

Không sửa CLI, producer, catalog, optimizer, vật tư legacy hoặc các sheet legacy trong mảnh đầu.
Không hardcode AF.11110 hay số liệu M1 trong source. File staging M1 chỉ phục vụ đối chiếu riêng.

## Layout workbook dự kiến

Giữ các sheet hiện có. Thêm `Tiên lượng chi tiết` và `Đối soát chi tiết`.
Workbook staging riêng M1 thêm `VT tham chiếu M1`; sheet này không được tự đưa vào export sản phẩm.

`Tiên lượng chi tiết`: phần đầu ghi định danh result/revision đã được luồng hiện có cấp,
phạm vi và trạng thái snapshot thực tế. Không tự thêm `reviewed=true`, không coi hash là phê duyệt.
Nếu hợp đồng chưa cấp định danh, để trạng thái chưa liên kết snapshot và chưa qua gate UI/export.

Cây hiển thị: hạng mục → công tác/cấu tạo/đơn vị tương thích → plan/vị trí → nhóm → dòng.
Các hàng tiêu đề nhóm không có lượng đóng góp, không nằm trong SUM. Không gộp khác mác,
variant hoặc đơn vị theo cùng code. Các ordinal chỉ định danh trong snapshot hiện tại.

| Cột | Nội dung |
|---|---|
| A–E | work_key, row_id, hạng mục, công tác/cấu tạo, plan/vị trí |
| F–J | nhóm, nhãn cấu kiện, role, dấu (+1/−1), đơn vị |
| K–N | số lượng cấu kiện, số lần lặp, kích thước/cơ sở hình học, quy đổi và nguồn |
| O–R | hệ số phụ và nguồn, phương pháp, expression diễn giải, nguồn/evidence |
| S–W | lượng tuyệt đối dạng số khi biểu diễn được; lượng có dấu dạng số khi biểu diễn được; raw text tuyệt đối; signed raw text; lý do thiếu/giới hạn precision |

`raw_quantity` là lượng đã tính đầy đủ: exporter không nhân lại count, repetitions,
conversion hoặc factors. Expression luôn là text, không thực thi công thức XLSX hay suy ra lượng.
Nguồn/nhãn/expression bắt đầu bằng ký tự công thức phải ghi kiểu text để không bị Excel thực thi.
Role reference có thể hiển thị raw geometry nhưng cột lượng đóng góp để trống.
Khoản trừ giữ sign=−1; không clamp tổng âm. Giá trị0 giữ là số0, None để trống và ghi missing.
Hệ số nguồn trống vẫn trống; không biến thành xác nhận hệ số1 hoặc0.

`Đối soát chi tiết`: work_key, đơn vị, detail_level, known_part_raw, total_raw,
complete, legacy_quantity, legacy_delta và nguồn snapshot. Mỗi số raw có cột text chính xác.
Partial: hiện phần biết, total để trống; không đổi partial thành tổng đủ. Detail None:
ghi “Chưa có diễn giải chi tiết”, không dựng contribution từ dimensions hoặc formula.

Tổng công bố lấy từ payload đã được validator kiểm. Exporter không tạo bộ tính thứ hai;
test có thể cộng Decimal contribution độc lập để kiểm parity. Không dùng SUM các ô đã format
hoặc công thức Excel làm số có thẩm quyền; không tạo dòng bù chênh lệch.

## Precision Excel

Decimal string là dữ liệu chuẩn. Luôn ghi raw string vào cột text, cả khi ô số dùng được.
Chỉ ghi bản số nếu hữu hạn, trong phạm vi Excel và không vượt15 chữ số có nghĩa theo kiểm tra
bảo thủ; trường hợp không an toàn thì để ô số trống, ghi “Xem raw text; vượt precision Excel”.
Format chỉ ảnh hưởng hiển thị, không quantize payload, không sửa floating artifact.
Kích thước như9.930000000000001 và3.6699999999999995 giữ nguyên trong raw text/evidence.
Kiểm tra roundtrip qua thư viện không được gọi là kiểm Excel native recalculate.

## Oracle staging M1

9 contribution từ `Tien luong!I38/I39/I40/I42/I43/I44/I45/I47/I48`:
0.3225;0.675;0.225;0.993;0.1835;0.367;0.1835;0.214;0.088m³.
Tổng Decimal=3.2515m³, đối chiếu J36. Nhóm37/41/46 không cộng.
DC-1 giữ count2, kích thước0.75×2.15×0.10, H38 trống; I38 là source_quantity.
Chưa có formula text XLS, không gọi đây là audit công thức.

Minh họa legacy phải gắn nhãn riêng: cộng round3 từng9 dòng theo Python hiện hành=3.251;
round3 sau tổng=3.252. Chênh raw−hai minh họa lần lượt+0.0005 và−0.0005m³.
Hai minh họa không phải `WorkItem.quantity` sản phẩm; legacy_quantity thật chỉ lấy từ payload
engine, không gán một trong hai số này cho engine khi chưa có bằng chứng.

| Vật tư | Tích theo raw3.2515 | Cached nguồn | Tích−cached |
|---|---:|---:|---:|
| PCB30 kg | 643.2279875 | 643.228 | −0.0000125 |
| Cát vàng m³ | 1.8630282125 | 1.863 | +0.0000282125 |
| Đá4×6 m³ | 3.019505475 | 3.0195 | +0.000005475 |
| Nước lít | 539.911575 | 539.9116 | −0.000025 |

Ghi kèm mức dùng, mã vật tư nguồn và `Phân tích VT!B60:F63`; không đồng nhất vật tư fixture
với catalog hoặc kết quả materials legacy. Không áp1.025, không suy hao hụt. Cached evidence
không phải công thức hoặc kết quả native recalculate. Không tự cấp dung sai để pass.

## Manifest kiểm thử dự kiến và gate

1. **Cấu trúc:** đúng9 contribution và3 nhóm; giữ thứ tự/row_id/đơn vị/nguồn; nhóm không cộng.
2. **Ngữ nghĩa:** sign−1, tổng âm, reference/union không cộng đôi, zero khác None,
   pending contribution có missing, partial không giả total, detail None không tạo dòng giả.
3. **Precision:** raw3.2515, hai minh họa round3 và chênh có dấu; count/lặp/hệ số không nhân lại;
   số lớn, số rất nhỏ, hơn15 chữ số giữ nguyên raw text; không để expression thành Excel formula.
4. **Vật tư tham chiếu:** đủ4 dòng, tích và cached nguồn tách riêng; không đổi legacy materials/catalog.
5. **Tương thích:** cùng payload cũ vẫn export; các ô số/sheet legacy và optimizer output giữ nguyên.
6. **Serialization:** save rồi `openpyxl.load_workbook` kiểm kiểu ô/text/giá trị và không formula bất ngờ.
   Đây là kiểm file bằng thư viện, không thay gate mở Excel thật.
7. **Sau tích hợp, owner01/02/QA15 cấp lượt riêng:** cùng snapshot UI/Excel, sửa input làm hết hiệu lực
   snapshot cũ, mở lại workbook bằng Excel thật, kiểm hiển thị/nguồn/9 dòng/4 vật tư. Chưa chạy.

Chưa chạy staging code, chưa tạo XLSX, chưa chạy focused test lượt này; chưa kiểm HTTP/full/UI/Excel.
Chỉ sau01 release hunk và03 chốt validator mới nối DTO canonical vào exporter.
