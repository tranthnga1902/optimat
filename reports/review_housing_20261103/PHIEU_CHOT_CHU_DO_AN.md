# Phiếu trình chủ đồ án — 03/11/2026

**Trạng thái: CHỜ CHỦ ĐỒ ÁN CHỌN TỪNG QUYẾT ĐỊNH. Chưa ký hoặc ghi nhận đồng ý thay người dùng.**

Mục đích là thống nhất cách dùng bằng chứng trong dữ liệu đối chứng phát triển. Đồng ý các mục dưới đây không phải nghiệm thu sai số độc lập, không xác nhận toàn bộ hồ sơ hoặc thay xác nhận chuyên môn. Câu “bạn và tôi thống nhất luôn cho phù hợp” là căn cứ trình từng quyết định, chưa phải phê duyệt cả ba mục.

Chỉ tạo phiếu này; chưa thay CSV, JSON, `human_approval`, `verification_status`, `cases` hoặc DB. Các trường dưới đây là **dự kiến sau khi có đồng ý cụ thể**, chưa được ghi vào dữ liệu. Không đề xuất tự đổi thành `da_kiem`.

## Quyết định 1 — BM-2 nhà Hương: phân biệt chiều dài tổng và chiều dài không giao

**Điều cần chủ đồ án đồng ý:** trong đối chứng phát triển, giữ 4,89 m là chiều dài không giao của BM-2 theo quy tắc trừ ba băng ngang; không coi 4,89 m và 7,29 m là hai số đo cùng phạm vi. Không thay chiều dài nguồn thành 7,29 m.

| Trước khi đính chính cảnh báo | Đề nghị chốt |
| --- | --- |
| Cảnh báo nguồn 4,89 m khác CAD 7,29 m, chưa giải thích | CAD dài tổng 7,29 m; chiều dài không giao 7,29 − 3 × 0,80 = **4,89 m** |
| Dòng nguồn `2*4,89*1*1,15*1,3`, kết quả 14,621 m³ | Giữ nguyên dòng và số nguồn; chỉ giải quyết cảnh báo chiều dài |

Nguồn truy được:

- Công tác `nha_huong_hai_duong_7x12-W002`, PDF tiên lượng trang 3, bảng 1, dòng 14; xem [JSON nguồn](../../data/ground_truth/du_toan/normalized_20261103/nha_huong_hai_duong_7x12.estimate.json).
- PDF kết cấu trang 8 KC-01-02 và trang 10 KC-01-04. Ảnh [mặt bằng móng](huong_kc_page_8.png) và [mặt cắt móng](huong_kc_page_10.png).
- CAD kết cấu handle `1002DDD`, layer `LS-TEXT`, ghi BM-2 dài 7290 mm, số lượng 02; tìm handle trong [bản trích chữ CAD](nha_huong_hai_duong_7x12_ket_cau_text.json). Ba băng ngang rộng 0,80 m đối chiếu trên hai ảnh trên.
- Kiểm tra phân bổ diện tích lớp đáy không đếm trùng được lưu tại `foundation_overlap_check` trong [quality review](../../data/ground_truth/du_toan/normalized_20261103/nha_huong_hai_duong_7x12.quality_review.json); không mở rộng kết luận sang toàn tiết diện.

**Không chứng minh:** bề rộng đào/lót, hệ số 1,3 hoặc 1,1, tổng đào 104,101 m³, tổng bê tông móng, cách phân bổ phần vát/giao theo cao độ. Bề rộng đáy BM-2 nguồn 0,80 m so bản vẽ 1,00 m và xử lý giao đầy đủ vẫn chưa chốt.

Trường dự kiến ghi nhận riêng sau duyệt: `decision_id=BM2_NET_LENGTH`, `owner_decision=agreed_for_development_comparison`, `gross_length_m=7.29`, `net_length_m=4.89`, `scope=length_excluding_three_crossings`. Giữ nguyên khối lượng nguồn và trạng thái chuyên môn; chỉ lưu lời đồng ý thực tế của chủ đồ án khi nhận được.

Lựa chọn để điều phối trình: **Đồng ý phạm vi trên / Cần xem lại / Chưa chốt**. Kết quả hiện tại: **chưa có lựa chọn**.

## Quyết định 2 — Lanh tô nhà Hương: Ø16, 92,9 kg trong nhãn từ bản vẽ

**Điều cần chủ đồ án đồng ý:** dùng **Ø16, 92,9 kg** cho ô nhãn thống kê lanh tô theo bản vẽ; giữ nguyên “Phi12” của tiên lượng trong trường nguồn để truy vết.

| Nguồn tiên lượng | Nhãn đối chứng đề nghị |
| --- | --- |
| `Phi 12 : 92,9/1000*1,1`, hiển thị 0,102 t sau hệ số/làm tròn | `diameter_mm=16`, `quantity=92.9`, `unit=kg`, cơ sở bảng thống kê thiết kế, chưa áp hệ số nguồn |

Nguồn truy được:

- Công tác `nha_huong_hai_duong_7x12-W017`, PDF tiên lượng trang 12, bảng 1, dòng 16; tổng công tác ở dòng 13 là 0,217 t. Xem [JSON nguồn](../../data/ground_truth/du_toan/normalized_20261103/nha_huong_hai_duong_7x12.estimate.json).
- CAD handle `10190F7` ghi `%%c16 : 92.9`; tìm handle trong [bản trích CAD](nha_huong_hai_duong_7x12_ket_cau_text.json). Nhãn cùng layer, tọa độ và SHA-256 tại công tác W017 trong [JSON nhãn](../../data/ground_truth/du_toan/normalized_20261103/nha_huong_hai_duong_7x12.verified_quantities.json).
- Chi tiết và thống kê lanh tô PDF kết cấu trang 30–31, KC-06-03/KC-06-04; xem hai trang cuối trong [ảnh ghép trang 26–31](nha_huong_hai_duong_7x12_last_sheets.png).

**Không chứng minh:** tính lại từng thanh từ hình học, khối lượng thi công thực tế hoặc căn cứ hệ số 1,1. Không thay tổng nguồn 0,217 t bằng riêng ô 92,9 kg. Tổng nhãn lanh tô 197,4 kg gồm các ô Ø6, Ø10 và Ø16; không cộng tổng cha lần nữa với các ô con.

Trường dự kiến sau duyệt: `decision_id=HUONG_LINTEL_DIAMETER`, `owner_decision=agreed_for_development_comparison`, ô nhãn `diameter_mm=16`, `quantity=92.9`, `unit=kg`; giữ nguyên `text_goc` của nguồn và cơ sở `net_design_schedule`. Chưa xác nhận `human_approval` hoặc `da_kiem` cho cả công tác.

Lựa chọn để điều phối trình: **Đồng ý phạm vi trên / Cần xem lại / Chưa chốt**. Kết quả hiện tại: **chưa có lựa chọn**.

## Quyết định 3 — Thép móng/bể nhà Sang: CẦN ĐỐI CHIẾU tổng hàng với tổng hợp

**Tạm dừng đề nghị duyệt 2,9012 t.** Kiểm lại PDF/CAD phát hiện mâu thuẫn nội bộ ở Ø12 bể nước. Điều cần chủ đồ án xem xét hiện tại chỉ là giữ nguyên nguồn **2,952 t**, giữ W007 ở trạng thái chờ đối chiếu; chưa chọn 2,9012 t hoặc 2,9019 t làm đáp án. Chưa có đồng ý cho mục này hoặc hai mục trước.

| Thành phần | Tiên lượng nguồn | Bảng thống kê bản vẽ |
| --- | ---: | ---: |
| Bể phốt Ø10 | 133,5 kg | 116,8 kg, handle `11735D8` |
| Bể phốt Ø12 | 39,4 kg | 37,6 kg, handle `11735D9` |
| Bể nước Ø10 | 200 kg | 168,4 kg, handle `11735DF` |
| Bể nước Ø12 | 36,9 kg | Dòng tổng hợp 36,9 kg (`11735E0`), nhưng DM-1 + DM-2 = **37,6 kg** |
| Tổng công tác theo dòng tổng hợp | 2,952 t | (2491 + 191,2 + 219) / 1000 = **2,9012 t**, chưa xác minh nhất quán nội bộ |
| Tổng theo các dòng chi tiết bể nước, giữ nguyên các phần khác | Không sửa nguồn | (2491 + 191,2 + 219,7) / 1000 = **2,9019 t**, chỉ là phương án số học để đối chiếu, chưa chốt |

Nguồn truy được:

- Công tác `nha_sang_hai_duong_4x15-W007`: tổng nguồn PDF tiên lượng trang 5, bảng 1, dòng 9. Bể phốt Ø10/Ø12 ở trang 5 dòng 20/21; bể nước Ø10 ở trang 6 dòng 4. Xem [JSON nguồn](../../data/ground_truth/du_toan/normalized_20261103/nha_sang_hai_duong_4x15.estimate.json).
- Bảng thống kê bể ở PDF kết cấu trang 18; **khung tên trên trang ghi KC-01-12**, đính chính dẫn chiếu KC-02-03 trước đây. Xem [ảnh riêng trang 18](sang_be_page18.png), bảng bể nước bên phải; hoặc trang cuối [ảnh ghép trang 13–18](sang_foundation_tanks.png). Nguồn phần móng được liệt kê trong review evidence tại KC-01-08/KC-01-09; lượt này chưa kiểm lại toàn bộ phần móng.
- Tổng móng 2491 kg từ handles `118F2E7`–`118F2EC`; bể phốt 191,2 kg từ `11735D6`–`11735D9`; bể nước 219 kg từ `11735DE`–`11735E0`. Tra từng handle trong [bản trích CAD](nha_sang_hai_duong_4x15_ket_cau_text.json); giá trị, layer, tọa độ và SHA-256 tại W007 trong [JSON nhãn](../../data/ground_truth/du_toan/normalized_20261103/nha_sang_hai_duong_4x15.verified_quantities.json).

Chi tiết mâu thuẫn xác nhận trên PDF trang 18 và chữ CAD:

- Bể nước DM-1, SL=2: hai dòng Ø12 có khối lượng in **10,1 + 10,5 = 20,6 kg**; dòng KLCT handle `11735D2` ghi `%%c12: 20.6`. Nhãn DM-1 handle `1173581`.
- Bể nước DM-2, SL=2: hai dòng Ø12 có khối lượng in **8,3 + 8,7 = 17,0 kg**; dòng KLCT handle `11735B6` ghi `%%c12: 17,0`. Nhãn DM-2 handle `11735B7`.
- Hai KLCT đã khớp các dòng in của chính nhóm mình: **20,6 + 17,0 = 37,6 kg**, nhưng tổng cuối bảng handle `11735E0` ghi **36,9 kg**. Chênh **0,7 kg** nằm giữa tổng các dòng Ø12 và ô tổng hợp Ø12; chưa xác định được nguyên nhân hay dòng nào cần sửa. Trên bảng bể nước này không thấy dòng Ø12 khác hoặc dòng trừ 0,7 kg.
- Các dòng tổng hợp còn lại của bể nước là Ø6 = 13,7 kg (`11735DE`) và Ø10 = 168,4 kg (`11735DF`); vì vậy 219 kg là phép cộng các ô tổng hợp, còn 219,7 kg là phép cộng thay riêng Ø12 bằng tổng chi tiết. Không suy ra hệ số để hòa hai số. Chênh 0,7 kg không được giải thích chỉ bởi làm tròn bốn dòng khối lượng đến 0,1 kg (sai khác làm tròn thông thường của bốn dòng tối đa khoảng 0,2 kg trước bước làm tròn tổng).

**Không chứng minh:** bảng thống kê đã được kiểm lại từng thanh từ hình học, số tổng hay số chi tiết là bản sửa đúng, phiên bản nào là hồ sơ thi công cuối cùng, hoặc khối lượng nghiệm thu. 2,9019 t chưa phải số thay thế được duyệt; phần móng và các nhóm khác vẫn cần kiểm tra nội bộ nếu dùng tổng toàn công tác. Không lấy các chênh lệch làm sai số hình học đã nghiệm thu. Tổng cha và các ô thành phần không cộng chung.

Trường dự kiến sau quyết định giữ chờ: `decision_id=SANG_FOUNDATION_TANK_STEEL`, `owner_decision=pending_internal_schedule_reconciliation`, `source_quantity=2.952`; ghi riêng hai phép cộng 2,9012/2,9019 t là số ứng viên kèm căn cứ, **chưa đặt số thay thế được duyệt**. Các trường này chưa ghi vào JSON; nhãn W007 đang có 2,9012 t trên đĩa cần được coi là chưa đủ điều kiện sử dụng do phát hiện mới. Chưa xác nhận `human_approval` hoặc `da_kiem` cho công tác.

Lựa chọn để điều phối trình: **Giữ chờ đối chiếu / Yêu cầu thêm bằng chứng**. Kết quả hiện tại: **chưa có lựa chọn; không trình duyệt số 2,9012 t**.

## Bàn giao điều phối

Chỉ thêm file phiếu này, dựa trên [bàn giao bằng chứng](BAN_GIAO.md) và JSON có sẵn. Ba quyết định không duyệt thay 11 nhãn/46 ô hoặc 453 dòng còn cách ly, không mở thêm phạm vi bóc. Điều phối trình chủ đồ án từng mục, ghi nguyên lời chọn và phạm vi được đồng ý trước khi giao lượt cập nhật dữ liệu. Không chạy DB hoặc toàn bộ test cho thay đổi tài liệu này.
