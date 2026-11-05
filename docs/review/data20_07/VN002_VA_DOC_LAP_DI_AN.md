# Bổ sung07 cho BOARD01 — 04/11/2026

## VN002 — đề cử Pioneer BUILD, chưa chốt ground truth

[VN002_CONG_TAC_COVERAGE.csv](VN002_CONG_TAC_COVERAGE.csv) liệt kê **đủ249 công tác**, giữ số nguồn/đơn vị và vị trí PDF trang/bảng/dòng, SHA-256 PDF, gate/issue và trường reviewer trống. Đây là đánh giá nguồn hiện có, không phải đo lại249 dòng. Có5 liên kết nhãn thống kê DEV (W012 cột, W014 dầm, W016 sàn, W018 thang, W020 lanh tô);244 dòng cách ly gồm W007 mâu thuẫn nội bộ bảng bể và243 dòng thiếu đối chứng đủ phạm vi. Năm nhãn chỉ có nguồn bảng, chưa phải oracle hình học hoặc đáp án người thật duyệt. Không công tác nào có oracle độc lập đã xác nhận trong bộ đang đọc.

Tiên lượng249 dòng có cả phần ngoài phạm vi phần thô; không đưa toàn249 làm mẫu số chính thức. Mỗi công tác có nguồn tiên lượng không đồng nghĩa có nguồn mọi kích thước/giao trừ. Chờ06 xác minh cặp hồ sơ/khả năng mở/revision/quyền dùng; readiness D02–D04 chưa đủ để chốt Pioneer hoàn chỉnh. Giữ `chua_kiem`, quyền dùng `chua_ro`, người kiểm trống.

## Dĩ An / banve1 / VN003 — bằng chứng đã được sử dụng phát triển

**Không nên trình là holdout chưa từng được xem.** Không đổi split test đã đăng ký; đề nghị gắn lịch sử phơi lộ riêng sau01 duyệt:

1. `tests/test_rough_columns.py:28`, `test_columns_far_apart_do_not_need_one_huge_grid`: docstring ghi rõ tình huống từ **banve1,02/11/2026**, mô tả thay đổi từ lưới toàn file sang từng cụm. Test dùng hình tổng hợp tái hiện; đây là dấu vết điều chỉnh thuật toán theo tình huống quan sát từ hồ sơ test, không phải chỉ thấy tên file trong manifest.
2. `tests/test_drawing_io.py:186`, `test_declared_inch_but_dimensions_in_mm`: docstring ghi **bộ46,banve1,02/11/2026**, dùng tình huống `$INSUNITS` và DIM để kiểm quy tắc đọc đơn vị. Chứng minh hồ sơ test đã cung cấp tình huống cho phát triển; chưa chứng minh mọi đáp án khối lượng bị dùng để tuning.
3. `docs/M01_PHAM_VI_PHAN_THO.md:123,208,400` dùng dòng tiên lượng Dĩ An để phân tích đào gộp và lệch phạm vi CHONG_THAM. Đáp án đã được xem ở mức phạm vi/công tác, không thể xác nhận bảo mật toàn bộ đáp án.
4. Bằng chứng bảo vệ về sau vẫn có: `reports/c01_review_fix/build.log:3` ghi bỏ qua banve1 vì split test; tài liệu D02 và test manifest giữ split/không tạo bộ D02 banve1. Những cổng này ngăn lượt C01/D02 về sau, **không xóa lịch sử đã phơi lộ**.

Chưa audit toàn bộ lịch sử Git/chat hoặc mọi lần chạy nên không kết luận mức tuning từng chỉ tiêu. Kết luận đủ bằng chứng là **đã phơi lộ ít nhất tình huống đọc CAD/cột và phạm vi tiên lượng; tính độc lập nghiêm ngặt chưa đạt**. Nếu tiếp tục đánh giá Dĩ An, công bố như tập test đăng ký có lịch sử sử dụng, không lấy nó làm chứng cứ holdout chưa thấy. Cần chủ đồ án quyết định cách báo cáo, không tự chuyển nó sang build.

## ID delta đề xuất cho01 — chưa sửa canonical

Ledger cụ thể: [DI_AN_EXPOSURE_LEDGER.csv](DI_AN_EXPOSURE_LEDGER.csv). Đặt `contaminated` cho phạm vi tình huống đọc đơn vị/cụm cột đã có test ghi nguồn banve1 và hành vi thay đổi; các bằng chứng tham khảo phạm vi tiên lượng chỉ ghi `not_proven` cho tính độc lập, chưa chứng minh sửa số để khớp. Ngày02/11/2026 lấy từ docstring, không phải ngày commit đã xác minh; các đoạn M01 chưa xác minh ngày thì để trống. Tổng thể Dĩ An không còn đủ cơ sở làm holdout chưa thấy; không khẳng định mọi phép tính đã bị tuning. Các cờ chỉ ở ledger báo cáo, không thêm cột/đổi split cases.csv.

**Test thay thế:** chưa có công trình cụ thể nào trong các file đã kiểm đủ bằng chứng vừa độc lập, đủ quyền, đủ cặp KT/KC và có đáp án người thật kiểm. Không đề cử Hương/Sang/Tân Bình vì đều build đã dùng phát triển; VN003/VN004 là alias, không phải ứng viên mới. Đề xuất06 thu identity mới `TEST_CANDIDATE_01` và `TEST_CANDIDATE_02` như mã yêu cầu thu, **không phải công trình thực đã có**: nhà ở Việt Nam có quyền dùng, cặpKT/KC cùng revision/hash, thiết kế khác bốn identity cũ; lập đáp án riêng trước khi mở cho người chỉnh quy tắc, khóa lịch sử tiếp cận, người lập/người kiểm và phạm vi. Chưa có thì báo thiếu2 holdout đủ điều kiện, không điền công trình giả để đủ5.

| Delta | Đường dẫn/ID liên quan | Đề xuất và người xử lý |
| --- | --- | --- |
| D20-07-VN002-W001…W249 | CSV coverage mới; canonical `normalized_20261103/nha_sang_hai_duong_4x15.*` |01/06 chốt revision và phạm vi Pioneer;07 chỉ bổ sung nhãn theo công tác được cấp lượt, không điền thiếu bằng tổng nguồn. ID là đề xuất, chưa phải revision DB. |
| D20-07-TEST-EXPOSURE-DIAN | `cases.csv` ID `di_an_banve1`; incoming ID `VN003_nha_pho_3_tang` |15/01 lập ledger exposure riêng theo bốn nguồn trên; giữ split test và identity alias; chưa sửa cờ độc lập ở canonical. |
| D20-07-NEW-TEST-GAP | Manifest toàn dự án |06/00 tìm quyền/hồ sơ mới khi được giao; tối thiểu mục tiêu5 công trình cần thêm1 identity, nhưng để có2 holdout chưa phơi lộ có thể phải thêm2 identity test mới, thành6 nếu giữ cả4 cũ. Không đếm VN003/VN004 hoặc biến thể làm công trình mới. Chưa có nguồn mới đủ quyền/đáp án được xác nhận trong lượt này. |

Người kiểm thực của VN002/Dĩ An chưa có trong dữ liệu được rà.01/00 cần chốt ai lập/ai kiểm đáp án và tiêu chí trước benchmark; không tự bổ sung tên/ngày hoặc `da_kiem`. Không tự đặt ngưỡng hoặc công bố KPI từ5 nhãnDEV.

Lượt này chỉ đọc và thêm hai tệp trong thư mục07. Không sửa nguồn/canonical/split/approval, không chạy CAD/test/DB, không thu thêm hồ sơ để đủ số. Coverage dùng các JSON audit đã có, giữ nguyên source_quantity.
