# C-2 4/A — rà luồng dữ liệu đầu vào (chưa chạy)

Phạm vi: đọc mã và đối chiếu chứng cứ [C2_A4_DOI_CHIEU.md](C2_A4_DOI_CHIEU.md). Chưa chạy hồ sơ, sửa code, database hoặc ứng dụng; các điểm sau là khả năng và thiếu hụt từ mã, không khẳng định lỗi runtime đã tái hiện.

## Luồng và điểm thiếu

1. `src/optimat/api/project_analysis.py:_events`: từng tệp KC được đọc và đưa vào `structural_parts`; provenance đầy đủ nằm ở kết quả tổng thể, còn `source_revision` hiện gắn từng plan KT. Kết quả `structural` gồm tên file nối chuỗi và các phần kết cấu gộp, không gắn trực tiếp file/revision/hash KC vào từng cột hay đoạn.
2. `src/optimat/rough/takeoff.py:structural_parts`: gộp `column_sections` bằng `update` và nối `column_schedule` giữa các bản KC, không giữ nguồn theo phần tử. Tên loại cột trùng giữa tệp có thể bị ghi đè ở bảng tiết diện; không thể coi tên hay mã loại là định danh vật lý duy nhất.
3. `src/optimat/rough/structural.py:ColumnSpan` và `read_column_schedule`: mỗi đoạn có `code`, `count`, `z_from_mm`, `z_to_mm`, `b_mm`, `h_mm`; không có trục, định danh cột vật lý, tờ hay nguồn tệp. Bộ đọc được viết cho bảng có tiêu đề “thống kê cột” và cột `SL: n`; không mặc nhiên chứng minh chi tiết C-2 trên KC-02-04 sẽ tạo ra một span. `SL=02` không xác định riêng 4/A.
4. `frontend/src/app/(user)/do-boc/model.ts:roughRequest`: các trường kết cấu được spread vào request, nhưng danh sách `columns` lấy từ `pp.cols` của mặt bằng KT và chỉ giữ `id,x,y,b_mm,h_mm,keep,source`. Không truyền `role` của cột, `level_m`/`source_revision` của plan hoặc liên kết trục, KC và khoảng cao độ. `Review.tsx` lưu structural và request trong snapshot; không bù các liên kết còn thiếu.
5. `src/optimat/rough/takeoff.py:compute_rough`: chỉ cần `column_schedule` khác rỗng là bỏ `column_works` cho **mọi** plan, rồi `schedule_column_works` tính tất cả span. Điều này không kiểm phạm vi theo cột/tầng/plan; một bảng không đầy đủ có thể làm mất các cột plan khác, còn span ngoài phạm vi plan chọn vẫn được tính. `schedule_column_works` tính count × tiết diện × chênh cao độ đầy đủ, khác quy ước nhánh plan lấy cao tầng trừ dày sàn. Hai phương pháp không được cộng trùng hoặc tự coi tương đương.

## Hợp đồng đề xuất để 01/03 thống nhất trước khi sửa

- Giữ nguồn KC ưu tiên khi chứng cứ đủ: project/profile revision, file ID/revision/hash, tờ và định danh vùng; mỗi instance phải có mã C-2 **và** trục 4/A, tách khỏi C-2 4/B. Liên kết theo trục cần nguồn và xác nhận; không ghép theo kích thước gần giống hay dùng `SL=02` làm một instance.
- Mỗi đoạn giữ cao độ đáy/đỉnh và nguồn, tiết diện, số lượng instance đã chọn cùng trạng thái thiếu/xung đột; tờ KC-02-01, KC-02-04, KC-03-01/02 và hash PDF có bằng chứng trong biên bản, nhưng PDF–DXF cùng revision chưa xác minh. Nếu không nối được instance/đoạn an toàn, đánh dấu chưa đủ thay vì phát sinh lượng như thể xác định.
- Lựa chọn phạm vi phải áp cho từng instance và đoạn; nguồn KC và phương án KT thay thế chỉ loại trừ nhau theo phạm vi thực sự đã đối chiếu. Quy ước khối lượng cột–dầm–sàn và phần giao phải nói rõ và kiểm không đếm hai lần; chênh hình học 0,174240 m³ so với nhánh trừ dày sàn 0,168432 m³ không phải bằng chứng hai nhánh có thể cộng.
- Những điểm có thể cần thay đổi: `project_analysis.py` (provenance từng nguồn), `structural.py`/`takeoff.py` (mô hình và phạm vi), `columns.py` (kết quả từng instance/đoạn), `model.ts`/`Review.tsx` (truyền, lưu, xác nhận). Chỉ sửa file cụ thể sau khi 01 phân công; kiểm focused một cột 4/A, hai cột cùng mã 4/A–4/B, bảng một phần, phạm vi tầng, nguồn không khớp và thiếu cao độ.
