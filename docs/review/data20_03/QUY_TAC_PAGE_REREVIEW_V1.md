# Review lại /quy-tac — vòng sửa 1

Ngày 04/11/2026. **Đóng cả 6 finding của bản đầu: 2 P1 và 4 P2.** Đây là kết luận về nội dung mô tả sau đối chiếu source, không phải nghiệm thu runtime, giao diện hoặc reader VN002.

Bản được đọc: `frontend/src/app/(admin)/quy-tac/page.tsx`, SHA-256 `70fd4b69625804252d84de36dc4fed4957730adeb80b2df0361574351b74c2c8`. Giữ báo cáo vòng đầu tại QUY_TAC_PAGE_REVIEW.md, không xóa lịch sử.

| Finding cũ | Kết luận | Bằng chứng sửa trong page | Consumer đối chiếu |
|---|---|---|---|
| 1 — P1 điều kiện đủ | ĐÓNG | Dòng18 yêu cầu phạm vi xác định, mọi đóng góp có lượng, không còn thiếu; D giữ phần biết và tổng trống | quantity_details.py:16,60; quantity_summary.py::_quantity_complete/build_quantity_summary |
| 2 — P1 source mới bị hiểu là runtime | ĐÓNG | Dòng10 nêu nhánh mới chưa xác minh trên bản chạy; dòng25 nói mô tả thuật toán, phải kiểm phiên bản runtime theo hồ sơ; dòng32 bỏ lời tự áp dụng, thay bằng xem input/kết quả | takeoff.py::compute_rough; đối chiếu trạng thái freeze/chưa tích hợp do01 xác nhận |
| 3 — P2 thiếu nhánh cột instance | ĐÓNG | Dòng13 tách bảng không tự trừ sàn, mặt bằng thiếu slab lấy H có cảnh báo, instance theo trục/gross/slab riêng/net trống khi thiếu; không suy reader VN002 đã nối từ phép tính fixture | columns.py::column_works/schedule_column_works; structural_column_instances.py:57–110 |
| 4 — P2 CP sàn đúng tầng/ô | ĐÓNG | Dòng15 nêu khoản trừ theo mặt bằng đang xét, phải kiểm tầng/ô vì chưa tự dò giao sàn tầng trên | takeoff.py::_slab_form_deduction:705 và shortcut trong hàm |
| 5 — P2 ô trống/gross sàn | ĐÓNG | Dòng15 ghi outline−void rồi nhân dày; thiếu void chỉ biết gross, 0 chỉ khi xác nhận không có ô trống | areas.py:216–228 và detail khoản trừ void |
| 6 — P2 mái thay sàn phải có mapping | ĐÓNG | Dòng15 chỉ bỏ SAN/CP SAN khi mái bê tông chỉ rõ replaces_slab_of | secondary.py:424–430, lọc kind=be_tong và plan tương ứng |

## Giới hạn kết luận

Không chạy test/build/DB/browser hoặc sửa page/core. Không kết luận link hoạt động, bố cục đạt hoặc engine runtime đã cập nhật. Reader VN002 vẫn chưa đạt end-to-end; phép tính từ input có nguồn không thay cho nhận dạng trục/section/slab tự động. Giữ đúng20bảng và phạm vi nhà ở riêng lẻ xây mới≤5tầng. Không phát hiện finding còn mở trong sáu điểm được giao kiểm lại.
