# Hợp đồng review độc lập WorkDimensions — phiên14

Ngày: 03/11/2026. Trạng thái: đề xuất nghiệm thu, chưa phải API đã triển khai hoặc được chốt. Phiên03 là sole writer backend dimensions; phiên14 chỉ đọc source và ghi báo cáo tại thư mục này. Không nhận N03/O01 hoặc quyền sửa công thức compute.

Đã đọc AGENTS.md, PLAN.md, phiếu điều chỉnh luồng, đặc tả kiểm công tác, WORK_DIMENSIONS_REVIEW_20261103.md và manifest bàn giao. Luồng áp dụng: `/do-boc` → `/phan-tho` → `/dieu-chinh` → `/vat-lieu` → `/toi-uu`.

## Bất biến

- `dimensions` là đầu vào có nguồn theo từng cấu kiện/lớp, không phải công thức tính khối lượng thay thế. Giữ nguyên `quantity`, `missing`, `status`, `inputs`, `evidence`, `masonry_geometry` cuối pipeline làm căn cứ về lượng và độ đủ.
- Payload cũ thiếu field nhận danh sách rỗng; không tự xác nhận đã kiểm. Thêm metadata không đổi số BT/CP/XAY, quy tắc A/B/C/D, schema DB hay điều kiện tối ưu.
- Dài/rộng/cao/dày dùng m; diện tích m²; count là số cấu kiện/thanh, không có đơn vị chiều dài. Không suy kích thước từ quantity, diện tích hoặc parse formula/note.
- Mỗi phần tử giữ label và nguồn; nhóm khác kích thước giữ đủ từng phần tử. Không chọn một kích thước đại diện rồi gán cho toàn nhóm. Cấu kiện trùng ID cần thêm ngữ cảnh tầng/view hoặc vị trí thực, không tạo tọa độ giả.
- `None` là chưa biết hoặc không áp dụng nhưng phải phân biệt được hai nghĩa khi hiển thị. `0` có chủ đích không được đổi sang mặc định bằng `or`; giá trị không hợp lệ phải được báo thiếu/lỗi theo miền đầu vào. Không chấp nhận NaN/±inf trong bất cứ field số nào, kể cả quantity đang None; không thay số lỗi bằng 0, không nới JSON serializer.
- Nguồn dimensions không nâng trạng thái. Nguồn cần chỉ rõ trường lấy từ bản vẽ, tham số, nhập tay hay suy luận; nguồn trộn không chỉ ghi “bản vẽ hoặc thông số”. Không có nguồn/vị trí thì ghi rõ giới hạn.

## Nghĩa hình học phải giữ

| Nhóm | Ý nghĩa bắt buộc và giới hạn |
|---|---|
| Tường/trát/lanh tô | Dài đoạn; dày khối xây; cao tầng riêng với cao xây sau trừ dầm. Kích thước raw trước cửa/cột/giằng không được gọi là net sau N03. Lanh tô dài cửa + hai gối, cao và gối thiếu giữ None. Trát còn cần số mặt và khoản trừ; cùng dimensions tường không đại diện đầy đủ quantity trát. |
| Dầm | Phân biệt dài trục, khoản trừ giao và dài net; `length_m` hiện là net. `height_m` hiện là cao toàn tiết diện, không phải web dưới sàn. Giằng móng không trừ sàn. CP có framed/hole riêng, không suy từ tích metadata. |
| Cột | Hai cạnh tiết diện và cao đoạn; cột mặt bằng cao sau trừ sàn, thiếu dày sàn phải ghi đang dùng cao tầng. Cột bảng giữ hai cao độ có dấu, count đúng một lần; cao độ âm hợp lệ khác với chiều cao âm. CP đầu dầm là khoản trừ riêng. |
| Móng/lót/đất | Mỗi lớp/bậc giữ đáy, đỉnh lớp vát và cao dưới dạng số có cấu trúc. Chỉ biết thể tích không sinh hình hộp. Thể tích nhập trực tiếp phải được ghi là cơ sở ưu tiên nếu vẫn có kích thước tham khảo. Lót giữ footprint và dày thực; hố đào giữ đáy, sâu, taluy/cao độ. Kích thước hố đi kèm đắp chỉ là tham chiếu, không gọi là kích thước khối đắp. |
| Sàn/mái/nền/chống thấm | Diện tích gộp, lỗ mở và sau trừ phân biệt; không ép thành chữ nhật. Dày theo từng lớp; lỗ mở None khác 0 xác nhận không có lỗ. Dài ở chống thấm là chu vi, cao là cổ tường; không dùng làm dài/cao phòng. |
| Thang | Từng thang/vế, số bậc, rộng bậc, cao bậc, tổng chạy ngang, dài nghiêng, rộng vế, dày bản và chiếu nghỉ; dầm thang là phần riêng. Không suy lỗ sàn từ diện tích thang. Không nhận thang chưa hỗ trợ là đủ vì metadata có số. |
| Giằng/sê nô | Các đoạn trục raw trước hợp đoạn giữ riêng; khối lượng dùng đoạn hợp. Hai raw giằng chồng nhau không chứng minh có hai thể tích. Khoản trừ không hiển thị thành cấu kiện cộng mới. |
| Thép | Bảng: dài cắt một thanh, số thanh, đường kính và nguồn bảng/dòng; quantity công tác là tấn lắp đặt. Theo hàm lượng: bê tông × kg/m³, không có hình học thanh độc lập. Tấn nhập tay không giả dài/số thanh. Không gọi lượng lắp đặt là lượng mua. |
| Lặp tầng | Giữ kích thước một cấu kiện; count hoặc multiplicity thể hiện số lần lặp đúng một lần. Không đồng thời nhân dài và count. Count None không tự đổi thành 1 nếu chưa xác định nghĩa; count 0 không tự thành n. |

## Khoảng trống của model hiện tại cần owner chốt

`models.py:176–192` hiện chỉ có các scalar chung và source/note. Chưa có trường số riêng cho khoản trừ/chiều dài trục, cao tầng/web, đỉnh lớp vát, cao độ, dài nghiêng/cao bậc/chiếu nghỉ, đường kính hoặc trạng thái áp dụng từng ô. Không coi chuỗi note là hoàn thành yêu cầu có cấu trúc. Phiên03 đề xuất phần mở rộng bổ sung tương thích nhỏ nhất theo phạm vi release; phiên01 chốt nếu cần mở rộng API/UI. Reviewer không ấn định tên field mới hoặc viết patch thay owner.

## Callers và giới hạn bằng chứng

- `takeoff.py:268–274,338–340`: khấu trừ L1/N03 rồi assign_status. Dimensions raw không chứng minh net đúng hoặc mở khóa dòng D. Không thay normalize/deduct/formula trong nhiệm vụ metadata.
- `takeoff.py:301–306`: nhân quantity và count khi view KC lặp tầng; phải đối chiếu cả hai, không nhân đôi trong UI/export.
- `api/main.py:318–341`: response_model RoughResult và export BOQ; cần kiểm strict JSON thực sau release. Route rough/auto tại dòng207 cũng cần cùng hợp đồng.
- `takeoff.py:538–555`: save_rough lưu model_dump JSON vào takeoff_results; không cần đổi schema quan hệ. Chưa kiểm round-trip DB trong lượt này.
- `boq.py:35–38,57–77`: bảng công tác chưa xuất dimensions riêng; sheet Cốt thép có bảng thanh từ req.rebar. Chưa thể tuyên bố Excel đủ toàn bộ metadata kích thước.
- `frontend/.../do-boc/model.ts:264–266`, `WorkReview.tsx:9–19,45`: đọc metadata để hiển thị; không được tái tính net. Kiểu mới cần owner UI nhận sau backend chốt. `dieu-chinh/materials.tsx:79–87` tính lại rồi lưu material session; việc vô hiệu xác nhận/snapshot là phụ thuộc UI, không được metadata tự coi đã xử lý.

Đây là review tĩnh trên checkout đang có nhiều writer; số dòng và nội dung có thể dịch chuyển. Manifest cũ là dấu mốc, không phải chứng minh snapshot hiện tại ổn định. Không xác định tác giả bằng timestamp hoặc git diff so HEAD.

## Cập nhật theo gói03 và quyết định01/00

Gói03 tại `reports/work_dimensions/CONTRACT.md` đã bổ sung schema có cấu trúc cho gross/deducted/web, đỉnh vát, cao độ, run/slope/đường kính, nguồn theo field, phân loại None và repetitions riêng count. Phần mô tả “model hiện tại” ở trên là mốc review trước bàn giao; đối chiếu gap và findings trên hash mới nằm ở phần cuối PLAN.md cùng thư mục, không đọc các gap cũ như kết luận mới.

01 truyền chốt00: MVP yêu cầu BOQ parity quantity/source/status/missing cùng snapshot; **không yêu cầu sheet WorkDimensions riêng**, không lấy thiếu sheet này làm blocker MVP. API/UI vẫn phải giữ metadata từng cấu kiện có nguồn. Gói SOURCE_READY_HASH là mốc trước focused, chưa là nghiệm thu cuối; lượt focused03 được14 đọc có1failure/227passed, không đạt toàn bộ.

Sau sửa v2, reviewer14 đã đọc terminal attempt2 của03:231passed/exit0,224dependency khôngdrift;11/11hash v2 khớp hash_after và checkout. Hai finding `_neg`/nguồn cao tường đã khép trong phạm vi này; xem PLAN.md phần v2 để biết hash và giới hạn. Kết quả v1 ở trên giữ làm lịch sử, không phải trạng thái v2. Không nâng kết luận thành nghiệm thu UI/full/hồ sơ thật.
