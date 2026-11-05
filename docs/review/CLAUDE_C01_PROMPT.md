# Giao Claude C01 — Báo cáo đường cơ sở phần thô trên build

Bạn là Claude dev; Codex là BA và reviewer chính. Chủ đồ án yêu cầu tiếp tục sau D02.
Repo: `C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai`.
Các đường dẫn dưới đây tương đối với repo.

## 1. Điều kiện bắt đầu

M01/D01 đã nghiệm thu. Codex chấp nhận các bản sửa và bằng chứng hồi quy phần kỹ thuật D02:
log toàn bộ 395 passed, 3 xfail, EXIT=0; importer thay đổi được kiểm bổ sung 4/4 trên bản cuối.
Phần đáp án thực D02 vẫn chờ người có chuyên môn xác nhận, 0 dòng da_kiem; mẫu số34 chỉ dự kiến.
Không đánh ✅ toàn D02, không điền người kiểm thay người thật, không biến đối chứng build thành chỉ tiêu nghiệm thu.
Được làm C01 ở chế độ phát triển trên bản nháp để phát hiện thiếu/sai và chuẩn bị báo cáo; chưa chạy nghiệm thu test.

## 2. Đọc trước

- CLAUDE.md, AGENTS.md áp dụng nếu có; NHAT_KY.md các mục M01/D01/D02; SPRINTS.md phần S13.
- docs/KE_HOACH_NGHIEM_THU_PHAN_THO.md: C01, quy tắc nghiệm thu, V01/V03.
- docs/M01_PHAM_VI_PHAN_THO.md: PTxx, trạng thái H0–H6, K1–K7, quyết định5A/5B.
- docs/D02_DAC_TA_DAP_AN.md: schema, cha–con, nguồn và các câu hỏi chưa xác nhận.
- data/ground_truth/du_toan/README.md, cases.csv.
- Bộ d02/46_nha_tan_binh gồm bốn CSV; 46_nha_tan_binh.csv, 46_thong_so.json, 46_vat_tu.csv.
- src/optimat/data_check.py: check_cases/select_cases/check_answer_set/denominator_ids/material_totals.
- scripts/evaluate_rough.py, scripts/compare_estimate.py; rough/takeoff.py, models.py, status.py, materials.py, boq.py.
- tests/test_ground_truth_manifest.py, test_ground_truth_d02.py, test_evaluate_rough.py, test_compare_estimate.py.

Đọc callers trước sửa. Không viết engine bóc tách hoặc framework báo cáo mới.

## 3. Phạm vi C01

Tái dùng script đánh giá để xuất một báo cáo đường cơ sở trên hồ sơ build46. Mục đích là trả lời:
1. Những hạng mục/công tác nào có trong nguồn và nằm trong phạm vi?
2. Hệ thống nhận/tính được gì, chưa ánh xạ/thiếu/chưa hỗ trợ gì?
3. Chỗ nào đủ điều kiện so khối lượng, chỗ nào chỉ có số đối chứng chưa xác nhận?
4. Vật tư/nhóm nào có kết quả, phần nào chưa có nguồn tương đương để so?

Không sửa các thuật toán nhận dạng, công thức, định mức hoặc số đáp án để làm kết quả đẹp.
Không triển khai sửa lỗi N01/N02/N03 hay Q01/Q02 trong lượt này. Phát hiện thì ghi ca và sprint.
Không chạy banve1 hoặc dữ liệu test; chỉ đọc manifest để giữ bảo vệ build/test.

## 4. Việc cần làm

### A. Khóa ảnh chụp đầu vào cho một lần báo cáo

- Đi qua select_cases với mục đích phat_trien, chỉ build. Không glob toàn thư mục CSV.
- Bộ D02 có lỗi validator thì không chạy case đó, ghi lý do. Cảnh báo được giữ trong báo cáo.
- Ghi nguồn đối chứng, phiên bản/hash mã/quy tắc/dữ liệu liên quan, data_kind/split và trạng thái kiểm.
- Thiếu bản vẽ/không đọc được thì xuất trạng thái thiếu, không giữ báo cáo cũ.
- Không sửa cases.csv hay nâng da_kiem chỉ để cổng bao_cao chạy được.

### B. Lập ánh xạ đối chiếu minh bạch

- Tái dùng WORKS và compare() cho tổng theo công tác/cấu kiện đang có; ghi đây là mức gộp.
- Tạo danh sách tất cả64 dòng gốc bộ46, kể cả OUT/chưa phân loại/không có mã; giữ id và nguồn D02.
- Không cộng cha và con; không tính con như mẫu số bổ sung. Phần chưa phân loại vẫn hiện.
- Một tổng hệ thống không được gán lặp cho nhiều dòng đáp án như thể từng dòng đã khớp độc lập.
- Chỉ so ở mức hai phía cùng phạm vi/đơn vị/cơ sở; nếu hệ thống chỉ có tổng mà đáp án chia tầng,
  có thể so tổng nhóm có căn cứ, nhưng không phân bổ ngược theo tỷ lệ hoặc tự suy khối lượng từng dòng.
- Dòng gộp có phần chưa hỗ trợ/chưa rõ không được đánh hoàn tất chỉ vì tổng cùng mã có số.
- Ánh xạ đề xuất phải có quy tắc/nguồn và trạng thái; chưa đủ căn cứ ghi chua_anh_xa, không mặc định OUT.
- Không suy tồn tại hạng mục từ việc engine không sinh dòng; dùng sổ D02 với co/khong/chua_ro.

### C. Báo đủ, thiếu và sai số đúng điều kiện

- Tách: có kết quả đầy đủ theo dữ liệu đã biết; một phần; thiếu đầu vào; chưa hỗ trợ;
  ngoài phạm vi; chưa xác định tồn tại; chưa ánh xạ.
- Không coi quantity có số là đã đủ. Kiểm complete/missing/warnings và hở đã ghi trong M01.
  Nếu chưa đủ căn cứ xác nhận H1, ghi trạng thái đề xuất/chưa xác nhận, không nâng lên hoàn tất.
- Giữ số đã biết và lý do thiếu riêng; không biến None thành0.
- Sai lệch đối chứng build có thể hiển thị nếu hai phía cùng phạm vi/đơn vị và đủ lượng,
  nhưng gắn nhãn nguồn chưa kiểm; không gọi đó là độ chính xác nghiệm thu.
- A/B và C xuất riêng; D/không có số đếm riêng. Tổng chính không trộn C/D vào chỉ tiêu A/B.
- Đáp án bằng0: phần trăm không xác định; báo chênh tuyệt đối và lý do, không chia0.
- Mẫu số dự kiến34, các dòng chờ phân loại và sự thiếu người kiểm phải hiện rõ.
  Không xuất một tỷ lệ hoàn tất95% hoặc khóa mẫu số khi D02 chưa đủ xác nhận.
- Báo phần thừa của hệ thống nếu xác định được cùng phạm vi; không bỏ vì nguồn không có dòng khớp.

### D. Vật tư và nhóm/loại

- Dùng kết quả materials/by_group/by_class hiện có; truy được về uses/công tác khi mã hỗ trợ.
- Vật tư dự toán lẫn hoàn thiện hoặc dung_lam_dap_an=khong không vào phép so; cho_kiem chỉ đối chứng tạm có nhãn.
- Thiếu nguồn vật tư cùng phạm vi thì ghi chưa đủ điều kiện so, không tự chia tổng xi măng/cát theo tỷ lệ.
- Không trộn lap_dat với mua; giữ nhóm Ø >10 chưa xác định riêng, không gộp thành ≤18.
- Chỉ cộng cùng đại lượng/đơn vị; tổng nhóm kg không so với tổng m³/viên/tấn chưa quy đổi.
- Nếu engine không thể cung cấp chi tiết đủ để đối chiếu, báo giới hạn; không đổi schema sản phẩm chỉ để lấp báo cáo.

### E. File báo cáo và hướng dẫn

Xuất `reports/c01_duong_co_so_build.xlsx` hoặc tên tương đương ghi rõ build.
Các bảng cần có (được gộp/tách sheet hợp lý):
- Trang_thai: PHÁT TRIỂN/ĐỐI CHỨNG BUILD, nguồn chưa xác nhận, trạng thái dữ liệu, hash, thời điểm, case chạy/bỏ.
- Bao_phu: các số lượng được định nghĩa rõ, kèm dòng chưa phân loại/chưa ánh xạ; mẫu số chỉ dự kiến.
- Doi_chieu_cong_tac: dòng nguồn, ánh xạ/mức gộp, hệ thống/đối chứng/đơn vị/status/điều kiện so/lý do không so.
- Theo_trang_thai: A/B, C, D tách riêng, không gộp sai số toàn bộ thành KPI A/B.
- Vat_tu_nhom: kết quả và giới hạn đối chứng, đơn vị/cơ sở lượng, phần thiếu.
- Can_kiem, Bo_qua: đủ danh sách có lý do, không cắt mất hạng mục không có số.

Giữ tính năng D01 ghi trạng thái mới kể cả không có case. Không làm hỏng đường bao_cao:
khi chưa có ACTUAL–test được xác nhận thì vẫn không chạy và không phát sinh chỉ tiêu chính.
Tạo docs/C01_DUONG_CO_SO_BUILD.md: cách chạy lại, quy tắc ánh xạ, cơ sở tổng, kết luận và việc cần sửa sau.

## 5. Test hành vi

Dùng fixture SYNTHETIC tạm, không báo độ chính xác từ chúng:
- OUT, chưa phân loại, không mã và thiếu số vẫn hiện trong báo cáo.
- Tách cha–con không tăng mẫu số, không cộng cha với con.
- Hai dòng đáp án không được nhận lặp cùng một tổng hệ thống để tự đánh khớp.
- Dòng gộp còn phần thiếu không được ghi đủ.
- Nhóm không cùng phạm vi/đơn vị/cơ sở lượng bị loại khỏi phép tính lệch nhưng giữ lý do.
- A/B và C/D không trộn KPI; đáp án0 không chia0; None không thành0.
- D02 chưa da_kiem vẫn chạy được đối chứng build, nhưng không thành nghiệm thu/bao_cao.
- Vật tư bị loại, nhóm Ø chưa rõ và mua/lắp đặt không bị gộp sai.
- Không case hoặc không đủ điều kiện: đầu ra mới có trạng thái/lý do, không giữ số cũ.
- D01/D02 và evaluator cũ không hồi quy.

## 6. Thực hiện và bàn giao

Ưu tiên một diff nhỏ theo phạm vi trên. Nếu phải đổi hợp đồng đầu ra compare() hoặc schema dùng chung, báo ảnh hưởng
và callers trước; giữ tương thích hoặc thêm đường báo cáo riêng tối thiểu. Không đổi DB, không nạp DB thật.
Trước test toàn bộ thống nhất khung không sửa file/DB kiểm thử với các phiên khác; lưu log/exit và hash cần thiết.

Bàn giao:
1. File/diff, sơ đồ dữ liệu vào → ánh xạ → các bảng báo cáo.
2. Lệnh chạy thật bộ46, file Excel và tài liệu; dữ liệu thiếu nếu chưa chạy được.
3. Đối chiếu tay ít nhất ba nhóm: công tác độc lập; dòng gộp; vật tư mua/lắp đặt hoặc lý do chưa so được.
4. Bảng thống kê giải thích được tổng số dòng, OUT/IN/chờ phân loại/không ánh xạ, không khẳng định95%.
5. Các sai lệch/thiếu quan trọng có nguồn và gắn sprint, không sửa thuật toán tiện trong C01.
6. Test trọng tâm, pytest toàn bộ, kiểm dữ liệu với môi trường thật được ghi rõ; không suy nguyên nhân lỗi từ timestamp.
7. Cập nhật kế hoạch/nhật ký: C01 chờ Codex review; D02 kỹ thuật đã chấp nhận nhưng dữ liệu thực vẫn chờ xác nhận.

Không tự nghiệm thu C01 hoặc D02 dữ liệu, không chạy V03, không bắt đầu sửa các sprint tiếp theo.
