# Nguồn giá ứng viên cho demo 05/11 — rà ngày 03/11/2026

Đã dùng một batch bốn truy vấn rồi mở các nguồn mạnh nhất. Không gọi hoặc nhắn nhà cung cấp, không gửi form, không đăng nhập. Chỉ lưu báo cáo và bằng chứng trong reports/demo_0511; chưa ghi DB, CSV danh mục hoặc ACTUAL row vào dữ liệu vận hành.

**Có bốn dòng giá xi măng lịch sử mới từ nguồn chính thức, đã kiểm trực quan cột VAT. Chưa tìm được báo giá mua hiện hành đủ điều kiện cho cả gạch GN01, vữa và giao hàng.** Ngày quan sát 03/11 không thay ngày giá hoặc thời hạn hiệu lực.

## 1. Phải khớp đúng danh mục

| Mã | Quy cách và đơn vị danh mục | Không được thay bằng |
|---|---|---|
| GN01 | Gạch đặc nung 220×105×60 mm; viên | Gạch đinh 190×90×55 hoặc gạch bê tông cùng cỡ |
| XM01 | PCB30 bao 50 kg; tấn | PC30 hoặc xi măng xây trát theo ASTM khác |
| XM02 | PCB40 bao 50 kg; tấn | PCB40 rời hoặc PC40 |
| CA01 | Cát vàng hạt to đổ bê tông; m³ | Mọi loại cát vàng chung, cát xây tô hoặc san lấp |
| VU02 | Vữa xây/trát M75 trộn tại chỗ; m³ | Vữa khô đóng bao hoặc vữa trộn sẵn |

Nguồn nội bộ: data/catalog/materials.csv. VU02 đang có cấp phối 307 kg XM01 + 1,13 m³ CA02 trên một m³ vữa; CA02 không phải CA01. Lượt này không tự tính giá VU02 từ giá CA01 hoặc giả định nhân công/hao hụt.

## 2. Bốn dòng lịch sử có thể trình review để nhập

Nguồn cấp một: [CEMIA — Bảng tổng hợp kê khai giá xi măng tháng 3/2026](https://cemia.gov.vn/UploadedFiles/UploadedFiles/tiep%20nhan/20260403035144_Ke%20khai%20gia%20Xi%20mang%20thang%203.2026.pdf).

PDF trang 13–14: Công ty Xi măng Vicem Tam Điệp, văn bản 1228/XMTĐ-XNTT, ngày 17/03/2026, Hà Nội; bao KPK 50 kg, TCVN 6260:2020. Đã tải bản gốc sau khi auto-review cho phép và render bằng Poppler; xem trực quan xác nhận cả bốn số nằm ở **cột Giá (đã có VAT)**. Cột trước VAT và ghi chú vận chuyển trống. Trích ngắn: “Đóng bao KPK 50kg”.

| Mã ứng viên | Biến thể nguồn | STT / trang PDF | Đồng/tấn, đã VAT |
|---|---|---|---:|
| XM01 | Vicem cao cấp PCB30 | 1 / 13 | 1.150.000 |
| XM02 | Vicem cao cấp PCB40 | 2 / 13 | 1.200.000 |
| XM01 | Đa dụng PCB30 | 3 / 14 | 1.070.000 |
| XM02 | Đa dụng PCB40 | 4 / 14 | 1.130.000 |

Khớp cao về mác, bao gói, đơn vị và địa bàn. Nguồn báo trực tiếp theo tấn, cùng đơn vị danh mục: **không cần quy đổi bao sang tấn**. Không tính ngược giá trước VAT hoặc suy thuế suất.

Gói đề xuất: `cement_historical_proposed.json`, status `PROPOSED_NOT_APPLIED`, bốn bản ghi ACTUAL/BULLETIN lịch sử, `vat_included=YES`, `transport_included=UNKNOWN`. Tên từng biến thể nằm trong source, cùng URL/trang/STT/văn bản. Supplier candidate `CBG-991233626E`; lat/lon/lead time trống, verified false. Không biến thành báo giá DEALER/supplier_materials.

Thiếu thời hạn hiệu lực, vận chuyển, lượng áp dụng, lead time, tọa độ và phí giao phải giữ thiếu. Mã XM01/XM02 là nhóm chung, không phải SKU thương hiệu: không coi bốn biến thể là một sản phẩm đồng nhất khi so giá. Ngày 17/03 là ngày văn bản, không phải xác nhận còn bán được giá đó ngày 05/11.

Bằng chứng cục bộ:

- `cemia_ximang_thang3_2026.pdf`, SHA256 `6ebfe2d3e432cb08f5319878e65463583350a96238b0ff62a6d17f02b1342c8d`.
- `cemia_price_page-13.png` và `cemia_price_page-14.png`: ảnh trang đã xem, header hai cột thuế rõ.
- `cement_historical_proposed.json`: giá trị, nguồn, unknowns, hash danh mục và giới hạn ánh xạ; chưa applied.

Web screenshot ban đầu có cache miss nên đã chuyển sang tải PDF chính thức và render. Không dựa vào search snippet để xác nhận giá/cột VAT.

## 3. Trang bán hàng Huy Đồng: đúng XM02 nhưng giá mâu thuẫn

[Trang sản phẩm Long Sơn PCB40](https://www.ximanghuydong.vn/xi-mang-long-son-pcb40) của nhà phân phối hiển thị 82.000 đồng, trọng lượng 50 kg. Trích ngắn: “Trọng lượng: 50Kg”. Không đọc được ngày công bố giá, thời hạn hoặc VAT.

[Trang danh mục cùng nhà bán](https://www.ximanghuydong.vn/xi-mang-long-son) lại hiển thị 73.000 đồng cho cùng tên. **PENDING, không lấy giá thấp hơn để nhập**; không tự quy đổi hoặc gắn ngày hiện tại làm ngày giá.

[Chính sách giao hàng](https://www.ximanghuydong.vn/chinh-sach-giao-hang) nói 1–2 ngày tùy khoảng cách và phí được xác nhận trước thanh toán. Trích ngắn: “tùy vào khoảng cách vận chuyển”. Địa chỉ nhà bán ở TP.HCM; đây không chứng minh giao Hà Nội trong một thời gian cố định. Không tự đặt lead_time_days hoặc phí bằng 0.

## 4. Marketplace và nguồn tổng hợp: chỉ ứng viên, không nhập

[Vật Liệu Số — Holcim PCB40 bao 50 kg](https://vatlieuso.com/vat-lieu/xi-mang-holcim-pcb40-bao-50kg/) hiển thị 98.000 đồng/bao, cập nhật 20/10/2026, kho TP.HCM; trang tự gọi “Giá tham khảo hiện tại”. Chưa xác minh nhà cung cấp chính chủ; tên PCB40 nhưng bảng tiêu chuẩn ghi TCVN2682, thiếu VAT/hiệu lực/đơn hàng. PENDING, không nhập DEALER; nhãn xác minh của website không thay xác minh của đồ án.

[Danh mục cát](https://vatlieuso.com/vat-lieu/vat-lieu-tho/cat-da-soi/) có cát bê tông hạt to 410.000 đồng/m³ ở Bình Dương. Cần kiểm trang sản phẩm, chủ thể bán, ngày và điều kiện đầy đủ; chưa phải giá Hà Nội. PENDING cho CA01.

[Danh mục gạch](https://vatlieuso.com/vat-lieu/vat-lieu-tho/gach-xay-block/) có gạch đặc nung 190×90×55 mm, khác GN01. Không nhập dù báo giá theo viên. Chưa có nguồn GN01 đúng cỡ trong lượt rà giới hạn.

[Cổng CEMIA bảng19492](https://cemia.gov.vn/tc/bang-gia-vat-lieu.html?bangGia=19492&loaiBangGia=T%E1%BA%A5t+c%E1%BA%A3&nam=&tinh=) có search snippet Long Sơn 85.000/bao nhưng trang mở thực tế là bảng Cà Mau tháng4, không trả record. Không nhập snippet hoặc gắn Hà Nội.

[Bài tổng hợp Hà Thành Home](https://hathanhhome.vn/tin-tuc/gia-vat-lieu-xay-dung-thang-5-nam-2026-tai-ha-noi) tự nêu chưa tra được số văn bản quýIII trên cổng Sở. Không dùng giá tổng hợp đó như báo giá trực tiếp của NCC. Dữ liệu quýII đã có trong DB không phải nguồn mới.

## 5. Cổng làm tiếp

1. Phiên chính review PDF/JSON bốn dòng xi măng rồi mới nhập gói BULLETIN lịch sử riêng. Giữ biến thể trong source, missing UNKNOWN; không gọi là báo giá mua còn hiệu lực.
2. GN01 cần nguồn nhà máy/đại lý đúng gạch đặc nung 220×105×60 mm, giá/ngày/điều kiện rõ. Hiện chưa có ứng viên đủ.
3. CA01 cần đúng cát bê tông hạt to, đúng địa bàn, đơn vị và điều kiện. Không dùng cát vàng chung hoặc source Bình Dương để giả giá Hà Nội.
4. VU02 giữ thiếu giá mua. Chỉ tính giá thành phần ở luồng có cấp phối/giá phù hợp; không cào vữa khô thay vữa tại chỗ.

Bốn truy vấn đã dùng: gạch đặc22010560 giá2026; Long SơnPCB40 giá2026 bao50kgVAT; cát vàng Hà Nội báo giá2026 VAT vận chuyển; vữaM75 trộn sẵn giá2026. Kết quả vữa trộn sẵn không được dùng cho VU02.

Chưa nhập dòng mới nào và chưa có báo giá mua hiện hành đủ điều kiện tối ưu trọn luồng. Bốn giá chính thức bổ sung được lịch sử thật nhưng không giải quyết thiếu GN01/VU02 hoặc xe/giao hàng.
