# Tiên lượng hai bộ nhà ở mới

Các file `*.estimate.json` giữ nguyên số liệu PDF phần thô, hoàn thiện và MEP; mỗi dòng có trang/bảng/dòng nguồn. Đây là tiên lượng nguồn, chưa phải đáp án được người kiểm chuyên môn duyệt.

| Công trình | Công tác nguồn | Phép tính kiểm lại | Cảnh báo số học |
| --- | ---: | ---: | ---: |
| nha_huong_hai_duong_7x12 | 215 | 252 | 3 |
| nha_sang_hai_duong_4x15 | 249 | 249 | 1 |

Tổng **464 dòng = 215 + 249**. Bốn cảnh báo số học là sai khác phép tính/độ làm tròn, chưa chứng minh sai hình học.

## Mốc nhập PostgreSQL trước lượt rà soát

`database_receipt.json` ghi nhận lần nhập trước lượt rà soát BM-2. Lệnh đã dùng: `python scripts/import_housing_estimates.py --database`.

- `project_id=1`: 215 công tác nguồn, 14 nhóm đối chiếu; `takeoff_id=1` (tiên lượng), `2` (đối chiếu).
- `project_id=2`: 249 công tác nguồn, 15 nhóm đối chiếu; `takeoff_id=3` (tiên lượng), `4` (đối chiếu).
- Tổng 26 liên kết file. Bảng sử dụng: `projects`, `project_files`, `takeoff_results` (JSONB với `kind=estimate_reference` và `kind=estimate_comparison`), `audit_logs`.
- Kết quả giữ `confirmed_at=NULL`, `verification_status=chua_kiem`. Lưu DB không phải duyệt đáp án. Không sửa dữ liệu Dĩ An hoặc Tân Bình.

**Chưa nạp JSON rà soát mới vào DB.** Biên nhận cũ không chứng minh DB đã chứa các đính chính hoặc nhãn bên dưới. `*.comparison.json` trên đĩa và importer đã được đính chính BM-2; đối chiếu trong DB vẫn thuộc mốc nhập cũ.

## JSON rà soát mới ngày 03/11/2026

**Cập nhật gate sau đối chiếu nội bộ bảng:** vẫn giữ 11 nhãn/46 ô làm bằng chứng; chỉ 9 nhãn có liên kết đối chứng phát triển ở mức bảng thống kê (chưa phải hình học đã duyệt). W005 Hương và W007 Sang bị cách ly với `quarantined_inconsistent_schedule`, `eligible_label_id=null`, do tổng KLCT khác ô tổng hợp. Tổng cách ly hiện là **455 dòng = 453 dòng thiếu đối chứng + 2 dòng mâu thuẫn bảng**. Các số đếm 453 trong mô tả lần xuất trước bên dưới chỉ là mốc trước sửa gate. Số nguồn và số ô nhãn được giữ nguyên để truy vết, không đổi thành số giả định mới. Xem `reports/review_housing_20261103/KIEM_TONG_BANG_THEP.md` và `BOC_TUNG_THANH_THEP_BE.md` cho bằng chứng và tính lại từng mã; chưa chốt tổng bể.

- `review_evidence.json`: vấn đề và nguồn đối chứng.
- `*.quality_review.json`: liệt kê điều kiện sử dụng của đủ 464 dòng; không có nghĩa đã bóc hình học đầy đủ 464 dòng.
- `*.verified_quantities.json`: **11 nhãn tổng hợp thép thiết kế**, gồm **46 ô đường kính/khối lượng** từ bảng thống kê CAD, kèm SHA-256, handle, layer, tọa độ và vị trí tiên lượng nguồn. Tổng cha bằng tổng các ô con; **không cộng cha và con vào cùng một tổng**.
- **453 dòng còn cách ly**, chưa đủ đối chứng theo phạm vi công tác để dùng làm đáp án chuẩn. Nhãn thống kê thép chưa được tính lại từng thanh từ hình học và còn chờ QS duyệt.

Các file mới giữ `human_approval=false`, `verification_status=chua_kiem`, `is_complete_ground_truth=false`. Khối lượng thiết kế và tiên lượng nguồn được lưu riêng; không áp hệ số 1,1 của nguồn vào nhãn thép thiết kế.

## Đính chính và việc chờ QS

- **BM-2 nhà Hương:** PDF kết cấu trang 8 (KC-01-02) và trang 10 (KC-01-04) giải thích chiều dài không giao: **7,29 − 3 × 0,80 = 4,89 m**. Cảnh báo cũ “4,89 m cần làm rõ so với 7,29 m” đã được giải quyết theo quy tắc trừ giao; không thay 4,89 thành 7,29.
- Hợp các hình chữ nhật cho diện tích đáy 47,172 m², bằng tổng phân bổ không đếm trùng giao; lớp đáy dày 0,25 m tương ứng 11,793 m³. Đây chỉ là kiểm tra lớp đáy, chưa xác nhận toàn bộ phần vát/giao theo cao độ hoặc tổng bê tông móng. QS cần duyệt quy tắc phân bổ chuyên môn.
- **BM-2 W006:** bản vẽ có đáy rộng 1,00 m nhưng diễn giải nguồn dùng 0,80 m; tiết diện tương ứng 0,4425 thay vì 0,3675 m². Chờ QS xác nhận bề rộng, phần giao và tổng khối lượng trước khi sửa tiên lượng. W002/W004 có dòng BM-5 dài 10,48 m tương ứng BM-4; giữ nguyên số nguồn và ghi chú lỗi tên.
- **Lanh tô nhà Hương W017:** bản vẽ dùng Ø16, 92,9 kg; nguồn ghi Phi12. Nhãn từ bản vẽ dùng Ø16, giữ nguyên nguồn riêng và chờ QS duyệt.
- **Thép móng/bể nhà Sang W007:** bảng thống kê bản vẽ cộng 2,9012 t, khác 2,952 t ở nguồn; các ô chênh lệch và handle được ghi trong JSON.
- **Cọc nhà Sang:** 34 × 10 m = 340 m khớp ghi chú thiết kế tạm tính, không phải chiều dài nghiệm thu sau ép thử. Cần làm rõ hệ số nguồn 1,1/1,3 trước nghiệm thu.

Bằng chứng ảnh, công thức và danh sách cần QS xác nhận nằm tại [bàn giao](../../../../reports/review_housing_20261103/BAN_GIAO.md). Tái lập JSON bằng `python scripts/review_housing_quantities.py`; chương trình này không kết nối DB.

## Kiểm tra đã thực hiện

Lượt rà soát: **7 test trọng tâm đạt**, thuộc `tests/test_review_housing_quantities.py` và `tests/test_import_housing_estimates.py`. Không chạy full suite hoặc test DB trong lượt này. Kết quả 17 test trích dữ liệu/mã hóa CAD là bằng chứng của lượt trước; bộ mở rộng đọc CAD thật từng được dừng, không có kết luận đầy đủ cho bộ đó.
