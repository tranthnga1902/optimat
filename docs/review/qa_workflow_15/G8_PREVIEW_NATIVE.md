# QA native Excel — workbook tham chiếu G8

**Kết quả: NOT_RUN — gate truy cập ứng dụng timeout.**

Phạm vi01 release: chỉ mở/đọc workbook `reports/g8_detail/exporter_preview_09/M1_AF11110_THAM_CHIEU.xlsx` bằng Microsoft Excel native; không sửa/lưu, không đóng workbook khác. Chưa producer/UI parity hoặc actual accuracy.

## Đã thực hiện

- Đọc skill computer-use cùng guidance/API/confirmations; dùng node_repl + @oai/sky đúng runtime.
- Hash trước: `75641444766379ada63ef584d608304be4bde4a1d33ee96f71c1e2653ba9a981`, khớp mốc01.
- `sky.list_apps()` tìm thấy Excel đang chạy, app `Microsoft.Office.EXCEL.EXE.15`, window ID69830, title `DU TOAN M1  [Protected View] - Excel` (workbook khác đang mở). Chưa gửi phím/click hoặc lệnh mở file.
- Lượt lấy window/state của Excel trả **`Computer Use app approval timed out`**. Không có screenshot hoặc accessibility state của Excel để kiểm. Dừng, không retry qua công cụ khác/COM/automation khác hoặc vượt Protected View.
- Hash sau: `75641444766379ada63ef584d608304be4bde4a1d33ee96f71c1e2653ba9a981`, không đổi.

## Các mục chưa chạy

| Mục01 giao | Trạng thái |
|---|---|
| Mở đúng workbook tham chiếu bằng Excel | NOT_RUN |
| Tiên lượng12 cột,9 contribution + nhóm không cộng,3,2515m³ | NOT_RUN |
| Sheet Truy vết/Đối soát/VT nguồn,4 vật tư cached/raw tách riêng | NOT_RUN |
| Raw text/links/Unicode/layout/không cắt chữ ở zoom hợp lý | NOT_RUN |
| Print preview A3 nếu hỗ trợ | NOT_RUN |
| Ảnh thật native | Không có — không capture được qua gate |

26 serialization tests do owner bàn giao không thay bằng chứng native. Không dùng thư viện đọc XLSX để gọi native pass. Không CAD/upload/API/DB/full/app demo hoặc chỉnh source; không thay đổi/đóng workbook của người dùng.

Blocker: quyền Computer Use Excel chưa hoàn tất trong thời hạn công cụ. Bước tiếp theo:01 xếp lại lượt khi quyền/môi trường native sẵn sàng; QA15 không tự thử lại hoặc đổi đường để vượt gate. Không có kết luận về lỗi layout/dữ liệu workbook vì chưa quan sát được.
