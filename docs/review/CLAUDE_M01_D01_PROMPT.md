# Giao Claude hoàn tất M01 rồi triển khai D01

Bạn là Claude dev; Codex làm BA và reviewer chính. Chủ đồ án đã yêu cầu thực hiện liên tiếp hai phần dưới đây.
Không dừng để hỏi lại phạm vi đã duyệt. M01 và D01 bàn giao thành hai diff/nhóm thay đổi riêng để review.

## 1. Đọc trước

Gốc dự án: `C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai`.
Các đường dẫn dưới đây tương đối với gốc dự án; kiểm trạng thái workspace, giữ thay đổi của phiên khác.

1. `CLAUDE.md` và AGENTS.md áp dụng nếu có.
2. `docs/KE_HOACH_NGHIEM_THU_PHAN_THO.md`: quy tắc nghiệm thu, dòng M01/D01, danh mục dữ liệu.
3. `docs/M01_PHAM_VI_PHAN_THO.md`: đọc hết, đặc biệt 5A/5B và cập nhật mục12.
4. `SPRINTS.md`: phần S13; `NHAT_KY.md`: các mục mới nhất.
5. `data/ground_truth/du_toan/README.md`, `cases.csv` và header các file đáp án được tham chiếu.
6. `src/optimat/data_check.py`, `scripts/check_data.py`, `scripts/evaluate_rough.py`, `scripts/compare_estimate.py`.
7. `tests/conftest.py`, `tests/test_evaluate_rough.py`, `tests/test_compare_estimate.py`,
   các test hiện có của data_check và loader tìm được qua rg.
8. Để đóng review M01: `frontend/src/app/(user)/do-boc/Review.tsx`, `model.ts`, `Rough.tsx`,
   `src/optimat/rough/takeoff.py::structural_parts`, `rough/status.py`.

## 2. Quyết định đã có hiệu lực

Nguồn: chủ đồ án xác nhận ngày 03/11/2026 trong chat, đã được Codex ghi tại M01 mục5A.

- IN: móng băng và đào/đắp/lót/bê tông/cốp pha/thép; đài và vật tư cọc theo thiết kế;
  bể nước ngầm/bể phốt phần đào/lót/kết cấu/xây/trát/chống thấm; vách; ô văng/mái hắt;
  sê nô xây; chống thấm mái/sê nô/ô văng khi thiết kế yêu cầu; bậc xây/bê tông và tam cấp;
  tường chắn mái/lan can xây; trát cột/dầm/trần; mái dốc BTCT đủ hình học; cổ cột/cổ móng theo thiết kế.
- Quét nước xi măng chỉ IN khi là lớp cấu tạo cần thiết được xác định, không tự gộp mặc định.
- OUT: mái khung thép/gỗ và hệ tôn/ngói; thang cốn/xoắn. Đây là H5 ngoài phạm vi, không phải H4 chờ hỗ trợ.
- OUT công tác/dịch vụ ép, khoan, đập đầu cọc; thiết bị/ống; nhân công/ca máy; các phần ngoài ranh giới chung.
  Không vì vậy mà loại vật tư cọc hoặc lượng bê tông/thép thuộc thiết kế.
- Phí giao vật tư thuộc so báo giá G05, không thêm thành công tác WORKS.
- IN không đồng nghĩa mã đã làm được; thiếu đầu vào/định mức thì để trống + lý do.
- 5B đã chốt: BULLETIN tham khảo không vào K3; micro+từng hồ sơ+trung bình theo hồ sơ+thấp nhất;
  không sinh vật tư giả cho công tác không có vật tư; nhập API có nguồn/người xác nhận có thể đạt K1 nhưng
  không chứng minh hoàn tất qua giao diện; cách tạo dữ liệu ghi từng đầu vào, tách khỏi A/B/C/D.

## 3. Phần A — Hoàn tất tài liệu M01

Chỉ sửa tài liệu, không sửa chức năng để đóng hai điểm review:

1. Trang cột chỉ bỏ/giữ qua toggleCol, chưa có đường sửa tiết diện/tọa độ hoặc thêm cột.
   Sửa câu “cột sửa được”, PT12 và phần liên quan thành mô tả đúng. Theo định nghĩa T/T- đang dùng,
   cột nhận sai kích thước không sửa được là T-. Gắn phần thiếu vào P01, không thực hiện P01 ở lượt này.
2. Bỏ câu “Thông số công trình luôn là nhập tay”. `structural_parts()` có thể bổ sung móng/cao lanh tô vào
   ProjectParams. Ghi nguồn theo cách tạo giá trị thực tế; không suy nguồn từ tên model hoặc nhãn C hiện tại.

Rà nhất quán toàn tài liệu sau cập nhật của Codex:
- Các CHỜ/ĐX/H4 cũ liên quan 5A phải phù hợp quyết định đã duyệt; phần lịch sử phải ghi rõ là lịch sử.
- Ma trận, mô tả, danh sách sửa CSV, ví dụ và dữ liệu cần không còn yêu cầu chốt lại 5A/5B.
- Không ghi columns.py tính sai cao độ âm: công thức nhận đoạn âm, chưa chứng minh sai số nghiệp vụ.
- Phạm vi đã chốt chưa đủ để khóa mẫu số: còn manifest và ánh xạ/đáp án được kiểm ở D01/D02.

Thêm phản hồi review vòng2, ghi chính xác phần chưa kiểm. Cập nhật kế hoạch/nhật ký thành
“M01 hoàn tất sửa tài liệu, chờ Codex xác nhận cuối”; không tự đánh ✅.
Theo yêu cầu chủ đồ án, tiếp tục D01 ngay sau phần A, không cần dừng chờ một lượt chat khác.

## 4. Phần B — Triển khai D01: manifest và bảo vệ dữ liệu đánh giá

### Phạm vi

Lập manifest hồ sơ/phiên bản, data_kind, split và nguồn/quyền dùng; thêm kiểm tra và nối với nơi dùng để đánh giá.
Tái dùng cases.csv và đường kiểm dữ liệu hiện có; chọn thay đổi nhỏ nhất, không dựng hệ quản trị dữ liệu mới.

### Việc phải làm

1. Kiểm metadata thực có, đề xuất rồi áp dụng cấu trúc tối thiểu có mô tả:
   - ID công trình ổn định, ID/phiên bản hồ sơ, ten/case_id;
   - data_kind, split;
   - đường dẫn KT/KC/đáp án/thông số (trường tùy chọn phải được ghi rõ);
   - nguồn tài liệu và tình trạng quyền dùng;
   - trạng thái người kiểm/đáp án nếu cần để phân biệt chưa đủ điều kiện đánh giá.
   Có thể dùng tên trường theo quy ước repo; ghi ảnh hưởng callers trước sửa.
2. Chỉ điền giá trị có bằng chứng. Nguồn tải công khai không đồng nghĩa được phép tái phân phối.
   Chưa biết quyền/ngày/phiên bản/người kiểm: ghi unknown/pending hoặc để trống theo schema, có cảnh báo;
   không bịa hash/phiên bản/người xác nhận. Thiếu metadata định danh bắt buộc thì lỗi/pending, không mặc định hợp lệ.
3. Giữ nguyên split hiện có: bộ46 build, banve1 test. Không đọc hình học/chạy đánh giá banve1 để sửa quy tắc.
   Được đọc metadata và cấu trúc file phục vụ kiểm tra; không sửa khối lượng đáp án hay suy đáp án mới từ test.
4. Chặn cùng công trình nằm ở cả build/test, kể cả khác phiên bản/tên/đường dẫn.
   Kiểm trùng ID và tham chiếu nguồn trùng nếu có căn cứ; không coi hai file cùng basename là cùng công trình.
5. Kiểm enum, cột bắt buộc, tham chiếu file/đáp án, tính nhất quán metadata. Chỉ kiểm file CAD tùy chọn
   khi đường dẫn có khai báo; khi bản vẽ không được phân phối cùng repo, báo rõ thiếu file cục bộ và
   chặn chạy case đó, không làm các test CI không cần bản vẽ thật thất bại vô điều kiện.
6. Chặn SAMPLE/SYNTHETIC hoặc metadata không hợp lệ lọt vào chỉ tiêu chính ACTUAL–test.
   Build và fixture vẫn được chạy trong chế độ phát triển, ghi nhãn rõ. Bộ lọc phải được dùng tại lối vào
   báo cáo, không chỉ viết hàm kiểm mà evaluator không gọi. Không đổi công thức tính KPI của C01/V01 ở lượt này.
7. README: mã công tác trống nghĩa là chưa ánh xạ/chưa phân loại, KHÔNG tự đồng nghĩa OUT.
   Ghi quyết định 5A mới và đường cần phân loại theo từng dòng. D01 không phải D02:
   chưa ánh xạ hàng loạt dòng đáp án, chưa khóa mẫu số, chưa sửa ma_cong_tac/cau_kien hoặc CSV vận hành.

### Test hành vi tối thiểu

- Manifest hợp lệ giữ đúng 46=build, banve1=test.
- Thiếu cột/ID bắt buộc; split/data_kind sai → lỗi có vị trí, không tự sửa.
- Hai phiên bản của cùng công trình nằm hai split → chặn.
- Case trùng/tham chiếu đáp án khai báo không tồn tại → báo đúng.
- Quyền dùng chưa rõ → cảnh báo/pending, không được tự ghi là có quyền phân phối.
- Bản vẽ thật thiếu trên máy → case không chạy được có lý do; test validator dùng fixture tạm.
- Đường báo cáo chính từ chối/loại có lý do SAMPLE/SYNTHETIC và metadata chưa hợp lệ;
  chế độ phát triển vẫn dùng được fixture, không âm thầm đổi split/data_kind.
- Loader/evaluator cũ không bị lỗi KeyError bởi thay đổi cột; số công thức không đổi ở fixture hợp lệ.

Tên test theo quy ước repo; không cần mỗi gạch đầu dòng thành một file riêng.

### Giới hạn

- Không triển khai D02, C01, Q01/Q02, chức năng cấu kiện, giá hoặc giao diện trong D01.
- Không đổi schema/PostgreSQL, không nạp đè DB thật; thay DB phải được duyệt riêng.
- Không đụng ngưỡng nhận dạng hoặc điều chỉnh theo test.
- Không tuyên bố đạt95% hoặc độ chính xác từ manifest. ACTUAL không thay cho đáp án đã kiểm độc lập.

## 5. Kiểm tra và bàn giao

Phần A: kiểm Markdown/link/tham chiếu, không cần pytest riêng.
Phần B: chạy test trọng tâm, pytest toàn bộ và check_data theo quy định repo; ghi chính xác số passed/skipped/xfail/failed.
check_data hiện cần PostgreSQL; kiểm validator bằng fixture không được phụ thuộc DB thật. Nếu thiếu DB kiểm thử hoặc
quyền truy cập, ghi chưa chạy/đang chờ và kết quả độc lập đã có, không tự dùng DB thật để nạp dữ liệu.

Bàn giao hai phần riêng:

1. M01: file/diff, bảng trả lời hai điểm review, quyết định 5A/5B đã đồng bộ, phần chưa kiểm.
2. D01: schema manifest trước–sau, giá trị có nguồn và giá trị pending, file/callers đã sửa;
   bảng ca test → tên test → kết quả; bằng chứng chặn dữ liệu sai tại lối vào evaluator;
   lệnh kiểm/kết quả thật; cách chạy lại; giới hạn và dữ liệu chủ đồ án còn cần cung cấp.
3. Nhật ký và kế hoạch mỗi phần ghi “chờ Codex review”, không tự nghiệm thu✅; chưa bắt đầu D02.

Nếu phiên điều phối cũ trong CLAUDE.md không còn tồn tại, ghi rõ không gửi được; không tạo phiên thay thế hoặc
để việc này chặn công việc đã được chủ đồ án giao. Vẫn sửa file dùng chung từng đoạn và báo ảnh hưởng hợp đồng trước sửa.
