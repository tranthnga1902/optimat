# Mục tiêu, ràng buộc tối ưu theo từng đối tượng và quyền quyết định (đặc tả 05/11/2026)

Bổ sung cho bước B6 / sprint DT06 của [luồng dự toán](LUONG_DU_TOAN_SAI_LECH.md). Trạng thái: **đặc tả, chưa triển khai**.
Mã hiện tại (`optimize/problem.py`) dùng ba mục tiêu chung cho mọi nhóm: tổng chi phí, `supply_days`, U. Tài liệu này thay
bằng mục tiêu riêng cho từng đối tượng, theo nghiệp vụ mua vật tư thật.

## 1. Bối cảnh nghiệp vụ được chọn

- Người dùng: chủ nhà hoặc kỹ sư giám sát của nhà ở riêng lẻ, hợp đồng **khoán nhân công**, chủ nhà **tự mua vật tư**.
  Với hợp đồng trọn gói, chỉ dùng phần kiểm khối lượng, kiểm sai lệch, không dùng bước chọn đại lý.
- Mác, quy cách, chủng loại do **thiết kế** chốt. Tối ưu chủ yếu chọn **nguồn cung, hãng, cách cấp, đợt mua**, không chọn vật liệu
  khác thiết kế. Ngoại lệ duy nhất là phương án tường, và phải được kỹ sư xác nhận.
- Mua **theo giai đoạn thi công** (`stage`: đất móng → khung từng tầng → tường → chống thấm), không mua một lần cho cả nhà.

## 2. Ai làm gì

| Vai | Được làm | Không được làm |
|---|---|---|
| **Hệ thống (mã)** | Lọc ràng buộc cứng; quy đổi ra đơn vị bán; tính mục tiêu từ số có nguồn; NSGA-II hoặc vét cạn; trả 3–5 phương án kèm nhãn (rẻ nhất, ít đại lý nhất, cân bằng) | Tự chọn thay người dùng; điền giá, ngày giao không có nguồn |
| **AI (mô hình ngôn ngữ)** | Trích ưu tiên từ câu tiếng Việt thành ràng buộc; giải thích đánh đổi giữa các phương án bằng số của công cụ; gắn nhãn **“Đề xuất”**; nhắc việc cần xác minh | Chọn phương án; đổi mác, quy cách, phương án tường; đưa số không có trong kết quả công cụ (bị thay bằng dữ kiện gốc) |
| **Người dùng** | Chọn một phương án hoặc giữ thiết kế; sửa ràng buộc rồi chạy lại; bấm **Áp dụng** để chốt | — |
| **Kỹ sư thiết kế** | Duyệt danh sách phương án tường thay thế (`approved_wall_system_ids`), xác nhận khi đổi khác thiết kế | — |

Mỗi lần chốt lưu: người chốt, thời điểm, phương án, phiên bản khối lượng, phiên bản báo giá, ý kiến AI đã hiện (để truy vết
“AI đề xuất gì, người dùng chọn gì”). Phương án AI đề xuất **không bao giờ** tự áp dụng.

## 3. Ràng buộc chung (mọi đối tượng)

| Mã | Ràng buộc | Nguồn dữ liệu |
|---|---|---|
| RC1 | Đúng mã, mác, quy cách thiết kế (trừ tường đã được duyệt thay) | Khối lượng đã kiểm, cấu tạo đã duyệt |
| RC2 | Báo giá ACTUAL: có VAT rõ, ngày báo giá, còn hiệu lực tại ngày đặt, cùng đơn vị bán | `supplier_materials` / `price_offers` |
| RC3 | Giao trước **ngày cần** của giai đoạn | Người dùng nhập ngày bắt đầu từng giai đoạn |
| RC4 | Xe vào được công trình: tải trọng tối đa, chiều dài xe (thép), xe bồn/bơm có vào được | Người dùng nhập điều kiện đường vào |
| RC5 | Đơn tối thiểu, bậc số lượng của đại lý | Báo giá đại lý |
| RC6 | Ngân sách (nếu nhập) chỉ so với các dòng **đủ giá**; thiếu giá thì phương án ghi “chưa đủ để so ngân sách” | Kết quả tính |

Mục tiêu chung cho phần chọn nguồn cung:
- **f_tiền**: tiền giao tận công trình = vật tư + vận chuyển + bốc dỡ/bơm, phí chuyến cộng **một lần** cho mỗi chuyến gộp.
- **f_đại lý**: số đại lý phải làm việc (ít hơn thì dễ gộp chuyến, theo dõi công nợ, đổi trả).

`supply_days` chuyển từ mục tiêu thành **ràng buộc RC3**: vật liệu phổ thông thường giao trong ngày, nên tối thiểu hóa
không tạo khác biệt; quan trọng là có kịp ngày cần hay không.

## 4. Theo từng đối tượng

| Đối tượng | Biến người dùng chọn | Ràng buộc cứng riêng | Mục tiêu tối ưu | Phương pháp | Người quyết định |
|---|---|---|---|---|---|
| **Tường xây** (bao che, ngăn) | Phương án tường trong danh sách được duyệt cùng lớp dày và vai trò; đại lý gạch + vữa | Tường chịu lực, khu ướt, tường ngăn cháy: giữ thiết kế; vữa đi đúng hệ tường; chỉ hệ đủ thông số (`wall_view().ready`) | f_tiền (gạch + vữa + nhân công xây); **U** (chỉ tường bao); **khối lượng tường kg/m²** (tải lên dầm, sàn) | **NSGA-II** 3 mục tiêu (không gian lớn, đánh đổi thật) | Người dùng chọn; đổi khác thiết kế cần kỹ sư xác nhận |
| **Bê tông kết cấu** (móng, cột, dầm, sàn, thang) | Cách cấp: thương phẩm + bơm hoặc trộn tại chỗ; trạm trộn | Đúng mác thiết kế; lượng mỗi đợt đổ ≥ đơn tối thiểu của trạm; xe bồn, bơm vào được (RC4); thời gian vận chuyển trong giới hạn trạm cam kết | f_tiền (thương phẩm: bê tông + bơm; trộn tay: xi + cát + đá + nhân công trộn); số đợt đổ | Vét cạn theo **từng đợt đổ** (ít biến) | Người dùng; AI nêu ưu nhược về kiểm soát chất lượng, không tự chọn |
| **Thép** | Hãng (trong danh sách thiết kế cho phép); đại lý | Đúng mác (ví dụ CB300, CB400) và Ø; mua theo cây 11,7 m (Ø ≥ 10) hoặc cuộn (Ø6, Ø8); xe chở thép dài vào được | f_tiền; f_đại lý | Gộp vào bài **phân bổ đại lý** (mục 5) | Người dùng chọn hãng |
| **Xi măng** | Loại, hãng đúng yêu cầu cấp phối; đại lý | Đúng loại xi trong cấp phối (ví dụ PCB30/PCB40); theo bao 50 kg; không trữ lâu: mua theo đợt | f_tiền; f_đại lý (gộp chuyến với cát, đá) | Phân bổ đại lý | Người dùng |
| **Cát, đá** | Bãi, đại lý | Đúng loại: cát vàng bê tông, cát xây trát, đá 1×2 / 4×6; mua theo khối xe; có chỗ tập kết | f_tiền; số chuyến | Phân bổ đại lý | Người dùng |
| **Gạch** (khi giữ đúng thiết kế) | Đại lý, hãng cùng quy cách | Cùng kích thước viên, mác gạch; theo đơn vị bán (viên, m³ khối AAC) | f_tiền; f_đại lý | Phân bổ đại lý | Người dùng |
| **Cốp pha** | Thuê hay mua; loại (gỗ ván ép, thép, nhựa) | Đủ diện tích cho một đợt đổ lớn nhất; thường thuộc phần nhà thầu nhân công, chỉ xét khi chủ nhà tự lo | f_tiền theo số lần luân chuyển | Vét cạn | Người dùng |
| **Chống thấm** | Sản phẩm cùng hệ thiết kế; đại lý | Đúng hệ (màng khò, quét gốc xi măng…), số lớp và định mức phủ của nhà sản xuất | f_tiền theo m² phủ | Vét cạn | Người dùng |

## 5. Bài toán phân bổ đại lý cho cả bảng mua

Sau khi các đối tượng đã chốt quy cách, hệ thống phân bổ từng dòng vật tư của một giai đoạn cho đại lý:

- Biến: dòng vật tư → đại lý (một dòng có thể tách nhiều đại lý nếu một nơi không đủ hàng).
- Mục tiêu: **min f_tiền**, **min f_đại lý** (hoặc số chuyến). Hai mục tiêu xung đột: gom về một đại lý đỡ chuyến nhưng có
  thể đắt hơn từng mặt hàng.
- Ràng buộc: RC1–RC6; mỗi chuyến không vượt tải trọng xe vào được.
- Phương pháp: **NSGA-II** 2 mục tiêu khi số tổ hợp lớn; vét cạn làm đối chứng trên bài nhỏ (như test hiện có).
- Đầu ra: 3–5 phương án Pareto, mỗi phương án là **bảng mua theo giai đoạn**: vật liệu, số lượng theo đơn vị bán, đơn giá,
  đại lý, chuyến xe, ngày giao, nguồn báo giá.

## 6. Dữ liệu người dùng phải nhập (không có thì để trống, phương án ghi điều kiện)

Địa chỉ hoặc tọa độ công trình; tải trọng xe tối đa, xe bồn/bơm có vào được; ngày bắt đầu từng giai đoạn; danh sách hãng
chấp nhận (thép, xi măng); ngân sách (tùy chọn); báo giá đại lý (nhập hoặc tải lên).

## 7. Thay đổi so với mã hiện tại (việc cho DT06)

1. Tách mục tiêu theo đối tượng: tường giữ NSGA-II (chi phí, U, kg/m²); vật tư khác dùng (f_tiền, f_đại lý).
2. `supply_days` từ mục tiêu thành ràng buộc ngày cần theo `stage`.
3. Gộp chuyến nhiều dòng cùng đại lý (hiện tính xe riêng từng nhóm).
4. Thêm biến cách cấp bê tông (thương phẩm / trộn tại chỗ) — **không** thêm biến mác.
5. API trả nhãn phương án và lưu lựa chọn người dùng tách khỏi đề xuất AI.
