# Đối chiếu hồ sơ incoming — 03/11/2026

Trạng thái: **CHỜ NGƯỜI KIỂM / CHỜ DỮ LIỆU**. Không nạp DB trong lượt điều phối này. Không sửa đáp án D02, cases.csv, nhật ký hoặc kế hoạch chung.

## Kết quả có bằng chứng

**Cập nhật sau cấp lượt sửa gate:** generator dùng issue metadata `internal_schedule_arithmetic_conflict` / `reviewed_unresolved` để giữ bằng chứng nhãn nhưng cách ly W005 Hương và W007 Sang (`quarantined_inconsistent_schedule`, `eligible_label_id=null`). Có 9 nhãn liên kết đối chứng phát triển mức bảng, chưa duyệt hình học; 455 dòng cách ly gồm453 dòng cũ+2 dòng mâu thuẫn. Đã tái sinh JSON, không thay số nguồn hoặc số nhãn; DB chưa cập nhật. Snapshot/diff/hash/test tại `gate_fix/`. Tính lại42 mã thanh bể được lưu riêng tại [bóc từng thanh](BOC_TUNG_THANH_THEP_BE.md); tổng bể chưa chốt vì số thanh bố trí, cửa thăm và quy ước uốn còn cần làm rõ. Các đoạn “chưa sửa JSON” và số453 phía dưới ghi nhận mốc bàn giao trước lượt sửa gate này.

**Bổ sung kiểm lại Sang trang 18:** W007 chưa đủ điều kiện sử dụng nhãn 2,9012 t. Khung tên trang này ghi **KC-01-12**, đính chính dẫn chiếu KC-02-03 trước đây. Bể nước DM-1 Ø12 có 10,1+10,5=20,6 kg (KLCT handle `11735D2`); DM-2 có 8,3+8,7=17,0 kg (`11735B6`). Tổng chi tiết 37,6 kg khác ô tổng hợp 36,9 kg (`11735E0`), chênh 0,7 kg. Chưa có dòng trừ hoặc lời giải thích trên bảng; không tự dùng hệ số hoặc quy về làm tròn thông thường. Bể nước theo ô tổng hợp là 219 kg; theo chi tiết Ø12 là 219,7 kg. Giữ các phần khác thì W007 tương ứng 2,9012/2,9019 t: **hai ứng viên số học, chưa chốt số thay thế**. Xem [ảnh trang 18](sang_be_page18.png) và [phiếu mục 3](PHIEU_CHOT_CHU_DO_AN.md). Chưa ai duyệt cả ba quyết định.

Lượt bổ sung chỉ sửa phiếu và bàn giao, không sửa JSON/mã/DB khi đang khóa kiểm thử. W007 trong JSON hiện còn số 2,9012 t từ ô tổng hợp, chưa phản ánh phát hiện mới và chưa đủ điều kiện làm đáp án chuẩn. **11 nhãn/46 ô là số sản phẩm đã xuất, không chứng nhận tất cả nhất quán nội bộ; W007 cần chặn sử dụng đến khi đối chiếu xong.**

- Hương, kết cấu PDF trang 8 KC-01-02 và trang 10 KC-01-04: BM-2 dài tổng 7,29 m, phần không giao ba băng ngang rộng 0,80 m là **4,89 m**. Cảnh báo chênh lệch chiều dài trước đây đã được sửa trong comparison và importer. Không đổi 4,89 thành 7,29.
- Kiểm tra độc lập bằng hợp các hình chữ nhật: diện tích đáy 47,172 m² bằng tổng phân bổ không trùng giao; lớp đáy dày 0,25 m có thể tích 11,793 m³. Đây không phải toàn bộ bê tông móng.
- Hương W006: đáy BM-2 rộng 1,00 m trên mặt cắt nhưng diễn giải nguồn dùng 0,80 m. Tiết diện tương ứng 0,4425 thay vì 0,3675 m². Cần QS kiểm phần vát, giao và cao độ trước khi sửa tổng công tác.
- Hương W002/W004: dòng BM-5 dài 10,48 m thực chất tương ứng BM-4; dòng 10,99 m mới tương ứng BM-5. Giữ nguyên dòng nguồn, ghi chú lỗi tên riêng.
- Hương W017: tổng hợp CAD handle 10190F7 và chi tiết/thống kê PDF trang 30–31 dùng Ø16, 92,9 kg; tiên lượng ghi Phi12. Nhãn từ bản vẽ dùng Ø16.
- Sang W007: các ô tổng hợp móng 2491 kg, bể phốt 191,2 kg, bể nước 219 kg cộng thành **2,9012 t**, khác 2,952 t ở nguồn. Tuy nhiên tổng hợp Ø12 bể nước mâu thuẫn các dòng chi tiết trên PDF trang 18 **KC-01-12**, như bổ sung trên; chưa xác nhận tổng W007 nhất quán hoặc số nào là số đúng.
- Sang cọc: 34 × 10 m = 340 m là chiều dài thiết kế tạm tính; không dùng như số nghiệm thu thực tế. Phân loại thép cho công tác cọc trong bộ trích nguồn không dùng làm nhãn thép khối lượng.

## Phạm vi dữ liệu bàn giao

`review_evidence.json` lưu nguồn và vấn đề; hai file `*.quality_review.json` liệt kê đủ **464 dòng** để kiểm soát điều kiện sử dụng, không có nghĩa đã đo hình học đủ 464 dòng. **453 dòng còn cách ly** vì thiếu đối chứng đủ phạm vi. Có **11 nhãn tổng hợp thép thiết kế**, chứa **46 ô đường kính/khối lượng** đọc trực tiếp theo handle trong CAD. Tổng và các ô con là cùng một khối lượng, không cộng cả hai.

Hai file `*.verified_quantities.json` giữ số nguồn riêng với số theo thống kê bản vẽ; không áp hệ số 1,1 của tiên lượng vào nhãn khối lượng thiết kế. Thống kê thép chưa được tính lại từng thanh từ hình học, chưa phải đáp án nghiệm thu. Tất cả giữ `human_approval=false`, `verification_status=chua_kiem`, `is_complete_ground_truth=false`.

Nguồn CAD cùng SHA-256, handle/layer/toạ độ từng ô nằm trong JSON nhãn; vị trí dòng PDF tiên lượng nằm trong audit. Ảnh đối chứng tại thư mục báo cáo gồm `huong_kc_page_8.png`, `huong_kc_page_10.png`, `huong_steel_foundation.png`, `nha_huong_hai_duong_7x12_last_sheets.png`, `sang_foundation_tanks.png`.

## Việc cần QS xác nhận

1. Duyệt quy tắc phân bổ giao BM-1…BM-5 và tích phân tiết diện vát theo cao độ; sau đó mới thay tổng bê tông/đào/lót.
2. Xác nhận phiên bản hồ sơ, lỗi Ø12/Ø16, các ô thép bể Sang và mâu thuẫn Ø12 bể nước 37,6/36,9 kg; chưa duyệt 2,9012 hoặc 2,9019 t. Tính lại từ thống kê từng thanh nếu dùng làm ground truth hình học.
3. Làm rõ hệ số 1,1 và 1,3 theo phạm vi hợp đồng; không coi chúng là kích thước đo.
4. Bóc riêng xây/trát/hoàn thiện/MEP và hạng mục trọn gói trong 453 dòng còn lại; bốn cảnh báo số học chỉ là sai khác phép tính/độ làm tròn, chưa chứng minh sai hình học.
5. Điều phối cấp lượt DB sau duyệt; DB hiện vẫn là bản nhập trước lượt rà soát này.

## Tái lập và phạm vi sửa

Chạy `python scripts/review_housing_quantities.py` để dựng lại audit/nhãn từ các bản trích CAD đã lưu; công cụ không kết nối DB. Test trọng tâm: `tests/test_review_housing_quantities.py`, `tests/test_import_housing_estimates.py`. Không chạy full suite hoặc test DB.

File mã sửa/thêm: `scripts/review_housing_quantities.py`, `scripts/import_housing_estimates.py`, `tests/test_review_housing_quantities.py`; dữ liệu thuộc incoming/normalized và báo cáo thư mục này. Đề xuất nhật ký: “Rà BM-2 incoming, giải quyết chiều dài trừ giao; phát hiện sai bề rộng, quy cách lanh tô và thép bể; bàn giao 11 nhãn thống kê thép, 453 dòng cách ly, chờ QS và lượt DB.”
