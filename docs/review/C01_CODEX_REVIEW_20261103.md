# Review C01 — 03/11/2026

Kết luận: **CẦN SỬA**, chưa mở N01/A01. Review bản đang triển khai, không thay thế review gói bàn giao cuối. Không sửa mã, dữ liệu, tài liệu chung hoặc chỉ thị cho dev khác.

C01 đã có bộ sinh báo cáo build và test riêng. Cách tách dòng gốc/con, giữ dòng OUT/chưa phân loại, nhãn đối chứng chưa xác nhận và ghi đè báo cáo là đúng hướng. Tuy nhiên còn các lỗi chặn dưới đây.

## 1. [P1] Vật tư cùng mã chưa chắc cùng phạm vi

Vùng sửa: `scripts/c01_duong_co_so.py:153–177`, test tương ứng.

`material_table` ghép theo material_id rồi lấy toàn bộ quantity_with_waste; không kiểm phạm vi công tác nguồn so với các uses của vật tư hệ thống. Tái hiện trong bộ nhớ: đáp án XM01 = 40 kg chỉ thuộc C_XAY; hệ thống XM01 = 100 kg gồm XAY 40 và TRAT 60. Hàm vẫn trả so_duoc=True, lệch 150%. Đây là so hai phạm vi khác nhau.

Sửa tối thiểu: chỉ bật so_duoc khi chứng minh cùng phạm vi/cơ sở lượng. Nếu không tách được đúng phần có hao hụt, giữ cả hai số để rà nhưng để chênh/% trống và nêu lý do. Thêm test trên, không tự phân bổ tổng nguồn.

## 2. [P1] Có số nhưng thiếu đầu vào vẫn bị coi là đầy đủ

Vùng sửa: `scripts/c01_duong_co_so.py:55–68`, `:111–115`, `:131–141`, test tương ứng.

complete hiện chỉ kiểm quantity khác None. Tái hiện: WorkItem XAY quantity=10, status=D, missing=['missing height']; đáp án 10. Kết quả he_thong_du=True, so_duoc=True, chenh=0. Hàng thiếu đầu vào vì vậy có thể xuất hiện như đã tính đủ.

Sửa tối thiểu: tách tổng phần đã biết khỏi mức hoàn tất; phản ánh missing và trạng thái D theo hợp đồng của engine. Nhóm chưa đủ không được so như tổng đầy đủ; vẫn giữ lượng phần biết và lý do thiếu. Thêm test numeric + missing/D.

## 3. [P2] Sổ hạng mục bị mất ở đầu ra

Vùng sửa: `scripts/c01_duong_co_so.py:72–150`, `:230–239`, danh sách sheet `:253`.

build_report nhận hm nhưng không dùng. main chỉ đếm hang_muc_chua_ro. Tái hiện: thêm hạng mục PT15 ton_tai=co vào hm, không có dòng dự toán tương ứng; không bảng trả về nào chứa PT15. Người đọc không thấy cấu kiện đã biết tồn tại nhưng chưa có đáp án/kết quả; các hạng mục chưa rõ cũng chỉ còn một con số tổng.

Sửa tối thiểu: xuất từng hạng mục, giữ tồn tại/phạm vi/nguồn/cảnh báo và liên kết dòng đáp án, chỉ rõ chưa có dòng tham chiếu hoặc chưa ánh xạ. Không suy không tồn tại từ việc engine không nhận ra. Thêm test hạng mục có/chưa rõ nhưng không có dòng công tác.

## 4. [P2] Ánh xạ theo PT bỏ qua mã công tác

Vùng sửa: `scripts/c01_duong_co_so.py:43–52`.

Ngoài COP_PHA và COT_THEP, leaf_key trả mã từ PT_WORK thay vì kiểm mã dòng. Tái hiện: ma_pt=PT05, ma_cong_tac=NEN_DEM_CAT trả BE_TONG_LOT. Hai công tác cùng đơn vị m³ sẽ bị ghép sai mà không bị cổng đơn vị chặn. Đây là fixture SYNTHETIC kiểm hợp đồng ánh xạ; không khẳng định bộ 46 hiện có dòng cát này.

Sửa tối thiểu: xác thực cặp PT/mã; chỉ nhận ánh xạ tương đương đã khai báo rõ. Cặp không tương thích phải giữ dòng và lý do, không tự đổi mã.

## Bằng chứng và giới hạn

- Đọc bộ sinh C01, thay đổi evaluator, test C01 và phân công điều phối.
- Chạy các ca tái hiện trực tiếp bằng `.venv/Scripts/python.exe`, chỉ gọi hàm trong bộ nhớ, mã thoát 0; không gọi main/Catalog.load/DB, không sinh lại Excel.
- Kết quả: numeric+D+missing vẫn so được; vật tư trộn phạm vi vẫn so được; PT15 không hiện; mã cát đổi thành bê tông lót.
- Không chạy pytest toàn bộ, DB test hoặc import DB; không xác minh tiến trình full suite/DB còn sống. Timestamp/file không đủ để kết luận tiến trình đang chạy.
- Chưa nghiệm thu workbook hoặc tài liệu C01 cuối; tại thời điểm rà chưa có `docs/C01_DUONG_CO_SO_BUILD.md`.
- Cần dev bàn giao bản cuối và test hồi quy bốn ca trên trước review lại. Không dùng kết quả build làm KPI nghiệm thu; D02 vẫn chờ người kiểm.

Dòng nhật ký đề xuất cho điều phối: “03/11/2026 — Codex review-only C01 đang triển khai: CẦN SỬA bốn điểm về phạm vi vật tư, mức hoàn tất công tác, hiển thị sổ hạng mục và xác thực ánh xạ PT/mã; tái hiện không DB, chưa chạy full suite, chưa mở N01/A01.”
