# Nguồn giá trên bảng phần thô và BOQ

Rà mã ngày 03/11/2026. Đề xuất dưới đây chờ phiên 01 cấp vùng ghi.

| Đầu ra | Kết quả đối chiếu |
|---|---|
| API phần thô | `rough/takeoff.py::attach_prices` nhận đúng `PriceOffer` đã chọn. Khi tạo `MaterialLine.price_source`, hàm giữ loại, tên nơi bán hoặc nguồn, ngày và loại dữ liệu. VAT và cước giao hàng dừng ở đối tượng báo giá. |
| Trang Vật tư và giá | Bảng vật tư phần thô hiển thị trực tiếp `MaterialLine.price_source`. Bổ sung thông tin vào chuỗi này sẽ hiện trên trang mà không cần thay kiểu phản hồi. Bảng gạch/vữa phía trên đọc `BillLine.best_offer` riêng. |
| BOQ Excel | `rough/boq.py::boq_bytes` xuất trang **Vật liệu** theo khối lượng. Trang này hiện chưa xuất đơn giá, thành tiền hoặc nguồn giá. Chỉ đổi `price_source` sẽ không thêm giá vào Excel. |

## Thay đổi nhỏ nhất đề xuất

1. Trong `attach_prices`, dùng các trường của chính báo giá được chọn để ghi loại giá, người bán, ngày, chứng từ hoặc trang giá, điều kiện VAT và cước vào `price_source`. Giữ nhãn tham khảo của giá công bố và nhãn SAMPLE/SYNTHETIC của kịch bản nếu có. Khi nguồn thiếu điều kiện, ghi rõ “chưa rõ VAT” hoặc “chưa rõ cước”. Không tính ngược giá trước thuế hoặc cước.
2. Giữ `best_price`, `price_source` và `est_cost` là tùy chọn. Nếu chạy lại trên cùng danh sách, xóa giá cũ trước khi chọn mới để báo giá đã mất hiệu lực không còn trên dòng. Giá thiếu để trống, dòng vật tư chưa đủ lượng vẫn giữ phần lượng đã biết và lý do thiếu. Không cần thêm trường API hoặc cột DB.
3. BOQ hiện chỉ dùng để đối chiếu khối lượng. Nếu 01 giao bổ sung giá vào Excel, nối các cột lượng dùng để tính tiền, đơn giá, thành tiền theo nguồn và nguồn/điều kiện vào **cuối** trang Vật liệu. Dùng dữ liệu của đúng bản đã lưu và các giá trị API đã tính. Không cộng các dòng khác cơ sở thành một tổng.

## Ca kiểm sau khi được cấp lượt

- Báo giá đã gồm VAT và chưa gồm cước hiển thị đúng cả hai điều kiện, nhà cung cấp, ngày và chứng từ.
- Giá công bố chưa rõ cước vẫn mang nhãn **tham khảo**. Đơn giá của báo giá mua thiếu điều kiện không được áp dụng.
- Có đơn giá nhưng khối lượng chưa đủ thì thành tiền để trống. Cập nhật lại với báo giá hết hạn xóa tiền cũ, giữ nguyên lượng và trạng thái thiếu.
- Nếu có yêu cầu xuất giá, so các ô của dòng vật tư giữa Excel và API của cùng bản. Kiểm ô thiếu còn trống và các cột hiện hữu giữ đúng thứ tự.
