# Từ dòng công tác đến vật tư của đoạn cột C-2 tại 4/A

## Lỗi và bản sửa

Hai đoạn cột ở cùng tầng có các dòng công tác cùng mã `COT` hoặc `COP_PHA`. Bộ tính biết đang quy đổi cho dòng nào nhưng trước đây chỉ xuất mã công tác và tên tầng trong `MaterialUse`. Giao diện vì thế phải bỏ qua phần góp khi không thể phân biệt hai đoạn. Bản sửa ghi thêm `rowIndex` cho từng phần góp, theo thứ tự cuối cùng của `result.works` mà bộ tính nhận. Trong một snapshot, phần góp có `rowIndex=i` trỏ về đúng khóa `w:i`. Đổi bản bóc phải đọc lại các khóa. Bản lưu cũ thiếu chỉ số vẫn mở được và giữ phần mơ hồ chưa gán.

[Thay đổi backend](producer.patch) · [Ca trước sửa](red.log) · [Ca sau sửa](green.log) · [Biên nhận mã nguồn](receipt.json)

## Đường tính đã kiểm

Từ 24 instance trong đầu ra `final_v3` của bộ đọc DXF kết cấu, dùng `compute_rough` với danh mục CSV, không nhập mác/kích thước giả định. Phép kiểm chỉ sử dụng phần cột kết cấu, chưa ghép toàn bộ kiến trúc. Khóa trong bảng dưới đây thuộc riêng snapshot này.

| Đoạn từ +3,150 đến +6,750 m | Khóa bê tông | Khóa cốp pha | Kết quả tại đoạn |
|---|---|---|---|
| 4/A · `5336a248e7a9b93bfe770983` | `w:22` | `w:50` | Gross 0,17424 m³. Chưa chọn vùng sàn để tính net. Cốp pha chưa đủ mặt tiếp xúc. |
| 4/B · `bc82cfd24f38f91258e814d8` | `w:19` | `w:47` | Có phần góp riêng dù cùng mã loại, tầng và kích thước với 4/A. |

Bộ chọn công tác chưa kiểm của giao diện đã nhận đúng một dòng nhu cầu cho từng công tác trên. Với dữ liệu kiểu cũ bỏ `rowIndex`, cả bốn trường hợp có liên kết mơ hồ đều không trả lượng. Với dữ liệu mới, các dòng được giữ và lượng vẫn là NULL. Đây là kiểm hàm dùng trên giao diện, chưa phải lượt thao tác trên trình duyệt. [Đầu ra bộ tính](production.json) · [Đầu ra bộ chọn của UI](consumer.json)

Trong ca hồi quy có đủ lượng, khi chọn thương phẩm M250 chỉ phát dòng thành phẩm. Khi chọn trộn tại chỗ chỉ phát các thành phần cấp phối có nguồn và không cộng thêm hao hụt đã có trong định mức. Nhánh thiếu phương thức cấp giữ nhu cầu chưa định danh. Ghi chú B20 của cấu kiện khác không tự chọn BT03 khi chưa có mác đúng phạm vi. Chỉ số dòng không thay đổi đơn vị, quy tắc làm tròn hoặc tính lượng mua. Dòng theo định mức vẫn cần phân biệt với số lượng đặt hàng. [Các ca hồi quy độc lập](../../../../tests/test_column_material_binding.py)

### Hai cột cùng tầng, chỉ một cột đủ lượng

Ca âm riêng dùng **hai cột tổng hợp**, không thay bất kỳ thông số VN002 nào. Cột thử A thiếu nguồn sàn đỉnh nên net là NULL. Cột thử B có net 0,29 m³. Cả hai nhánh giao diện được gọi trực tiếp bằng `w:0` và `w:1` của bản thử. Nhánh thương phẩm trả BT03 bằng NULL cho A và 0,29 m³ cho B. Nhánh trộn tại chỗ chỉ trả xi măng/cát/đá; từng lượng của A vẫn là NULL, B có lượng thành phần riêng. Cả hai nhánh đều để trống lượng mua riêng đoạn.

Lần kiểm đầu tách đúng lượng nhưng phát hiện phần giải thích của dòng đã kiểm còn lẫn phạm vi. Khi chỉ chọn B, `adviceScope` hiển thị lý do “dày sàn đỉnh và căn cứ trừ sàn” của A vì dùng danh sách thiếu chung của vật tư. Nhánh `uncheckedRowAdvice` không mang lý do đó sang B. Ca này được theo dõi riêng với kết quả của producer đã đóng băng. Biên nhận tách `quantity_scope_passed` và `missing_scope_passed` để có thể đối chiếu lại sau khi sửa giao diện. [Biên nhận ca âm](mixed_scope.json) · [Phép kiểm chạy lại](check_mixed_scope.py)

## Mắt xích thép trên hồ sơ nguồn

Trên KC-02-04 trang 22, nhóm **C-2** có nhãn DXF `118CDEF`, số cấu kiện `118CDF0`. Hai dòng thanh số **3 và 4** là INSERT `118CDA7` và `118CDB3`. Mỗi dòng ghi Ø20, dài cắt 4.300 mm, 2 thanh/cấu kiện, 4 thanh toàn nhóm, 17,2 m và 42,4 kg toàn nhóm. Kết hợp hai số hiệu cho một cấu kiện được **17,20 m**. Đối chiếu 2,470 kg/m theo bảng 3 ở KC-00 trang 3 cho **42,484 kg**. Phân bổ hai lượng in theo mỗi cấu kiện cho **42,4 kg**, chênh **0,084 kg**. Hai giá trị có nguồn và cách tính khác nhau, cần giữ cả hai khi đối chiếu.

Ca âm quan trọng: C-1 có mark 3/4 trùng cả đường kính, dài cắt, số lượng và khối lượng in với C-2. C-1A cũng trùng số hiệu và chiều dài nhưng có 8 thanh toàn nhóm. Dòng đai số 7 của C-2 (`118CDD7`) ghi 77 thanh/cấu kiện, 154 thanh toàn nhóm, dài cắt 800 mm. Chưa có căn cứ phân 77 thanh cho riêng đoạn đang xét. [Thuộc tính CAD và tọa độ của ba nhóm](schedule_source.json) · [Bảng thép và hình dọc](../../data20_00/VN002_C2_BANG_THEP_3_4.png) · [Ghi chú phạm vi mặt cắt và cấp thép](../../data20_07/C2_A4_BLOCK_AND_MATERIAL_HANDOFF.md)

Các locators trên được đọc từ thực thể gốc bằng ezdxf để đối chứng. Phần này chưa chứng minh bộ đọc bảng thép sản phẩm tự nối được các thanh 3/4 với mặt cắt, đoạn cao độ và vị trí 4/A. Đã chuyển nguồn cho phiên phụ trách reader và bảng thép. Chỉ khi xuất hiện công tác thép có liên kết nguồn đủ mạnh cho đoạn, mới được dùng chỉ số dòng của công tác đó để quy đổi vật liệu. Hiện chưa gán tổng thép cột/toàn nhà, 42,484 kg hoặc 77 đai vào lượng mua của 4/A.
