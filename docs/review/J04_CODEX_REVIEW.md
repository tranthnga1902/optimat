# Review J04 - Codex, 03/11/2026

J04 lập căn cứ nguồn và ca số học cho bốn nhóm vật tư còn thiếu. Đây là review tài liệu/khả năng triển khai, không phải nghiệm thu J05 hoặc đáp án D02.

**Kết luận: ĐẠT phần chuẩn bị nguồn trong giới hạn đã nêu; CHỜ DỮ LIỆU để nghiệm thu J04 gắn hồ sơ.** Được giao ba nhánh chuẩn bị kỹ thuật ngay theo prompt riêng bên dưới. Không mở toàn bộ J05 chỉ vì đã có bảng nguồn.

## Bằng chứng đã kiểm

- Đọc J04, kế hoạch J04/J05, M01 5A/5B, đặc tả D02 và các phần mã liên quan: `rough/materials.py`, `norms.py`, `models.py`, `walls.py`, danh mục/CSV định mức và test vật liệu hiện có.
- Mở lại [N2 chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf): AF.83 PDF 455-457; AK.211/212 PDF 589; AK.411 PDF 599. Số và đơn vị trong J04 phù hợp các bảng đã tra. Lần lập phiếu đã render/xem trực quan PDF 455 và 589. Review này không tuyên bố đã kiểm chữ ký số hay toàn bộ phụ lục.
- Mở lại [N7 chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf): PDF 4 mục 4-5 và PDF 15 dòng 11.12325/26. Phép tính khoảng phụ gia trong J04 đúng với giả thiết nhân 1,025 một lần. Khoảng đó không phải liều mua được phê duyệt.
- D02 hiện có mẫu/validator/bộ nháp, phần kỹ thuật chờ review; **0 dòng được người kiểm xác nhận**, chưa khóa mẫu số. J04 ghi “D02 đang thực hiện” cần đọc theo hiện trạng này, không coi D02 đã xong dữ liệu.

## Các điểm phải xử lý trong bàn giao

1. **Khoảng phụ gia có thể bị biến thành liều chính thức nếu dùng loader hiện tại.**
   - Hiện trạng: `Norm.value` trong `rough/norms.py` lấy trung điểm khi chỉ có min/max; `materials.py::_Bill.norm_line` dùng giá trị này để sinh lượng.
   - Trường hợp lỗi: nhập khoảng 0,5-0,8% vào định mức có `norm_code` sẽ tạo một lượng đại diện dù người dùng chưa chọn liều; chỉ có mã nguồn không chứng minh đã đủ thiết kế.
   - Cách xử lý: prompt phụ gia cấm đưa khoảng vào đường sinh lượng mua hiện tại. Chưa có liều/sản phẩm thì phải giữ thiếu; thay hành vi khoảng phải có thiết kế riêng, không đổi toàn bộ `Norm.value` và gây hồi quy các định mức khoảng đang có.
   - Nếu bỏ qua: BOQ có thể xuất số phụ gia nhìn như lượng mua đã chốt.

2. **Cảnh báo bằng lời không bảo đảm giữ đủ phần vật tư còn thiếu.**
   - Hiện trạng: `concrete()` chỉ duyệt các dòng CSV đã có; M350/M400 có xi măng/cát/đá nhưng không có dòng phụ gia. Nhánh cốp pha có thể trả các vật liệu được tra mà không biết phần hệ còn thiếu.
   - Trường hợp lỗi: chỉ thêm CP01 cho AF.83, hoặc giữ ba vật liệu bê tông rồi ghi thiếu phụ gia ở tài liệu, sẽ không bảo đảm đầu ra API/BOQ giữ phần thiếu cần thiết.
   - Cách xử lý: mọi thiết kế J05 phải chỉ rõ dòng thiếu, lý do, nguồn và trạng thái thể hiện ở đâu; không thêm 5% vật liệu khác thành số kg/bộ. Không xóa lượng đã biết để che phần thiếu. Không hứa đã giải quyết cơ chế known_part tổng quát của Q02 trong các sprint này.
   - Nếu bỏ qua: người đọc có thể hiểu phần vật tư đã biết là danh sách mua hoàn chỉnh.

3. **Phụ thuộc D02 và quyền ghi song song cần tách theo loại công việc.**
   - Hiện trạng: mục 6 J04 có thể bị hiểu rằng phải đợi D02 rồi mới làm mọi việc hoặc cả ba nhánh đều có thể sửa mã sau cùng một điều kiện.
   - Trường hợp lỗi: trì hoãn cả việc đối chiếu nguồn/test tổng hợp, hoặc ba phiên cùng sửa `materials.py`, CSV và file tổng hợp sẽ tạo xung đột.
   - Cách xử lý: cho làm ngay khảo sát, hợp đồng đầu vào, ca SYNTHETIC và bản vá đề xuất; áp nguồn vào hồ sơ, đo chỉ tiêu và nghiệm thu vẫn chờ D02 xác nhận. Đợt đầu chỉ nhánh trát được sửa mã dùng chung sau khi hợp đồng trường cần thiết đã được Codex chốt; hai nhánh khác chỉ ghi tài liệu riêng.
   - Nếu bỏ qua: thay đổi có thể mất nhau hoặc bộ nháp D02 bị dùng làm đáp án đã kiểm.

Ba prompt đã đưa các điểm trên thành yêu cầu cụ thể; không cần sửa số nguồn trong phiếu J04. Không thay ghi chú lịch sử thành xác nhận chức năng hoàn thiện.

## Quyết định theo phiếu

| Phiếu | Làm ngay | Chờ trước khi vận hành/áp hồ sơ |
|---|---|---|
| Cán 50 mm | Giữ trống và lý do | Định mức/cấp phối có nguồn được review; không nội suy |
| Ván ép | Ma trận hệ/cấu kiện/mã/đơn vị, đề xuất bản vá và ca số học | Đủ quy cách hệ, ánh xạ danh mục, phân định hao phí với mua/thuê; D02 xác nhận phần liên quan; lịch tích hợp |
| Trát gạch rỗng | Truy nguồn nền trát, hợp đồng trường và test tổng hợp; triển khai phạm vi được chốt, không tự thêm trường | Hợp đồng đầu vào mới nếu cần; nền/vữa/diện tích hồ sơ do người kiểm xác nhận; D02 cho nghiệm thu thực |
| Phụ gia | Hợp đồng liều/sản phẩm/đơn vị và đề xuất biểu diễn thiếu | Cấp phối/liều/sản phẩm/TDS, kg/L khi cần; D02 xác nhận; lịch tích hợp |

## Prompt giao riêng

- [Ván ép AF.83](CLAUDE_J05B_VAN_EP_PROMPT.md).
- [Trát gạch rỗng](CLAUDE_J05C_TRAT_GACH_RONG_PROMPT.md).
- [Phụ gia M350/M400](CLAUDE_J05D_PHU_GIA_PROMPT.md).

Đọc review này cùng J04; phân định làm ngay/chờ ở đây thay cho cách hiểu gộp tại mục 6 J04. Ba prompt độc lập về nhiệm vụ, không cho phép ba phiên ghi chung một file.

Không chạy pytest/check_data trong lượt review này vì chỉ tạo Markdown. Chưa kiểm thao tác UI, dữ liệu PostgreSQL, bản vẽ build hoặc hiệu quả trên hồ sơ thực. Không nghiệm thu D02 trong lượt này. Chưa kiểm lịch sử thay thế phụ lục và mức 1,025 cho từng cấu kiện; đây vẫn là giới hạn của phiếu phụ gia.
