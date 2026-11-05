# Kế hoạch hoàn thiện dữ liệu OptiMat AI theo lược đồ 20 bảng

Ngày lập: 04/11/2026. Thời lượng đề xuất: 6 tuần kể từ khi bắt đầu; không tự gán ngày kết thúc khi chưa chốt nhân lực. Các chỉ tiêu thu thập dưới đây là mục tiêu của đợt đầu, không phải số liệu đã hoàn thành.

## 1. Mục tiêu và phạm vi

Hoàn thiện dữ liệu cho chuỗi hồ sơ DWG/DXF → nhận dạng cấu kiện → số đo có nguồn → khối lượng phần thô → phương án vật liệu → nhu cầu mua → tra giá và tối ưu. Khi bản vẽ chưa chỉ định vật liệu, vẫn lưu và kiểm tra khối lượng hình học; không ép gán mã vật liệu.

Kế hoạch tham khảo cách chia tuần, gói dữ liệu, ground truth, kiểm tra chất lượng và bàn giao của tài liệu người dùng cung cấp. Không kế thừa 16 bảng DWH, các dự án bất động sản, 28 kịch bản kinh doanh hay số liệu mô phỏng của tài liệu đó. Hệ thống OptiMat giữ đúng 20 bảng vật lý, không tạo kho dữ liệu hoặc bảng kiểm thử mới.

Đầu ra gồm dữ liệu có nguồn, manifest phiên bản, bộ đáp án được kiểm độc lập, kịch bản kiểm thử, báo cáo chất lượng và hướng dẫn cập nhật. File lớn lưu ngoài database; các bảng lưu định danh, đường dẫn, hash và dữ liệu nghiệp vụ. Bộ kiểm chứng lưu dưới thư mục data/ground_truth, có phiên bản và tách công trình phát triển/nghiệm thu.

## 2. Hiện trạng cần xử lý

Kiểm kê chỉ đọc ngày 04/11/2026 trên database trước chuyển đổi ghi nhận: 98 vật liệu, 22 phương án tường, 31 dòng định mức phần thô, 15 quan hệ vật liệu; 2.867 nhà cung cấp nhưng chỉ 13 cặp cung ứng–vật liệu; 63 quan sát giá; 128 file, 2 phiên bản file và 4 phiên bản thông số; 26 kết quả lưu, trong đó phần lớn là hồ sơ mô phỏng/tham chiếu. Số dòng không chứng minh dữ liệu đầy đủ hoặc đã kiểm chứng.

Theo tài liệu kiểm kê tham chiếu, 63 quan sát giá hiện tại là công bố giá, còn dữ liệu cung ứng mẫu phải tách khỏi số thực. Phải kiểm lại các nhãn này ở Tuần 1 trước khi lập tập giá sử dụng chính thức. Dữ liệu ground truth hiện có phải được người có chuyên môn đối chiếu lại, không tự chuyển thành trạng thái đã kiểm.

Ưu tiên là chất lượng và liên kết nguồn, không thu thêm hàng nghìn dòng nhà cung cấp hoặc bản vẽ mà không có nhãn/đáp án.

## 3. Mười gói dữ liệu phải hoàn thiện

| Mã | Gói dữ liệu | Trường/nội dung tối thiểu | Nơi lưu trong 20 bảng | Điều kiện sẵn sàng |
|---|---|---|---|---|
| D01 | Hồ sơ thực tế | Mã công trình, file kiến trúc/kết cấu, vai trò, phiên bản, SHA-256, nguồn và quyền dùng; danh sách file thiếu | projects, document_revisions | File mở được, đúng cặp hồ sơ; hash kiểm lại được; thiếu được ghi rõ |
| D02 | Hình vẽ và cấu kiện | Vùng hình, tầng, tỷ lệ/biến đổi, loại và mã cấu kiện, đối tượng CAD, lần xuất hiện, cấu kiện trùng | analysis_runs, building_elements | Nhận dạng được đối tượng và đối tượng dễ nhầm; liên kết đúng tầng/hình; không đếm mỗi hình thành cấu kiện mới |
| D03 | Số đo và bằng chứng | Đại lượng, giá trị gốc/chuẩn, đơn vị, nguồn, handle/đường dẫn INSERT hoặc vị trí bảng, phương pháp, trạng thái A/B/C/D | element_measurements, evidence_sources | Số đo truy về đúng cấu kiện và nguồn; giữ các ứng viên mâu thuẫn; không dùng 0 thay thiếu |
| D04 | Đáp án khối lượng | Danh mục cấu kiện phải tìm thấy, công tác, số đo, công thức, cộng/trừ/giao nhau, đơn vị, người kiểm, ngày kiểm | File ground truth; analysis_runs/takeoff_items chỉ lưu các lần chạy được đánh giá | Có kiểm độc lập; cùng công trình không nằm ở cả build và test; mẫu số và phần chưa đánh giá được công bố |
| D05 | Danh mục vật liệu | Mã, tên, nhóm/họ, quy cách, đơn vị chuẩn/mua, chiều quy đổi, khối lượng riêng, hao hụt và nguồn | materials; dữ liệu tham chiếu trong rule_sets | Mã duy nhất; đơn vị/quy đổi có nguồn; thuộc tính thiếu để NULL; phân biệt ACTUAL/SAMPLE/SYNTHETIC |
| D06 | Định mức và cấp phối | Công tác, quy cách, hệ số, đơn vị, mã/phiên bản nguồn, vật liệu thành phần, phạm vi áp dụng, hao hụt đã bao gồm hay chưa | work_norms, wall_systems, material_relations | Mỗi hệ số có căn cứ; đúng quy cách; không cộng hao hụt hai lần; token vật liệu theo vai trò được giải nghĩa |
| D07 | Nhà cung cấp và cung ứng | Mã, vị trí đã kiểm, vật liệu cụ thể, tên/đơn vị bán, hệ số đổi, thời gian giao, tối thiểu đặt hàng, nguồn/ngày xác minh | suppliers, supplier_materials | Có ít nhất một phương án mua đủ điều kiện cho mỗi vật liệu của luồng demo; chưa xác minh không coi là sẵn sàng |
| D08 | Giá và chi phí | Mã vật liệu/nhà cung cấp, đơn vị, ngày, địa phương, lượng áp dụng, loại giá, VAT/vận chuyển, nguồn; công lao động và biểu phí xe | price_records, cost_parameters | Giá so sánh cùng cơ sở; không dùng giá công bố như báo giá mua; dự đoán gắn nhãn riêng |
| D09 | Quy tắc nhận dạng | Loại quy tắc, mã, thứ tự/độ ưu tiên, payload đúng cấu trúc, nguồn, phiên bản, ca dương/âm | rule_sets | Nạp/đọc khớp CSV; không tạo quy tắc đặc biệt cho hồ sơ test; có ngưỡng và giới hạn công bố |
| D10 | Phương án và lịch sử chạy | Lựa chọn vật liệu, lượng mua, nguồn công tác/định mức, cấu hình, snapshot giá, mô hình và hash, seed, trạng thái xác nhận | material_scenarios, optimization_runs, audit_logs | Tái giải thích được kết quả cũ khi danh mục/giá thay đổi; không biến đề xuất thành chỉ định thiết kế |

## 4. Quy mô đợt đầu và cách chọn mẫu

Mục tiêu khởi đầu là 5 hồ sơ nhà ở thực tế có kiến trúc và kết cấu tương ứng. Chọn đa dạng theo số tầng, loại móng, cách biểu diễn tường/cửa, bảng thép, đơn vị và tỷ lệ. Dùng một hồ sơ đầy đủ để hoàn thiện quy trình trước; sau đó mở rộng. Giữ nguyên split của hồ sơ đã đăng ký; các hồ sơ mới được phân build/test ngay lúc nhập. Có ít nhất 2 công trình test độc lập nếu thu thập được đủ 5 hồ sơ; nếu không đủ, báo thiếu và không công bố kết quả tổng quát.

Tạo thêm biến thể tổng hợp từ hồ sơ build để kiểm tra đổi tên layer/block, dịch chuyển, xoay, đơn vị, nhiều tỷ lệ và lỗi có chủ đích. Không đưa biến thể cùng công trình vào test độc lập. Không dùng biến thể làm bằng chứng về độ chính xác trên thực tế.

Chọn 3–5 phương án tường có đủ thông số để chạy toàn chuỗi; định mức phần thô phải phủ các công tác thật sự xuất hiện trong hồ sơ mẫu. Chọn 1 địa bàn cung ứng trước, xác minh khoảng 10 nhà cung cấp liên quan; phấn đấu có 2–3 báo giá cùng cơ sở cho mỗi vật liệu trọng tâm. Đây là mục tiêu thu thập, không được tạo số giả để đạt chỉ tiêu.

Mô hình dự đoán giá chỉ được nghiệm thu nếu tập quan sát đúng cơ sở và đủ cho phép chia tập theo thời gian/vật liệu. Không đặt số dòng tối thiểu tùy tiện hoặc nhân bản 63 dòng giá công bố để tạo tập huấn luyện lớn. Khi chưa đủ, dùng tra giá có nguồn và ghi rõ mô hình chưa đủ dữ liệu.

## 5. Phân công theo vai trò

| Vai trò | Trách nhiệm | Người kiểm chéo |
|---|---|---|
| Phụ trách database/backend | Schema 20 bảng, import, migration, transaction, snapshot, API và quyền | QA kiểm dữ liệu; người quản lý duyệt phạm vi |
| Phụ trách CAD | Hồ sơ, đơn vị/tỷ lệ, nhãn cấu kiện, nguồn số đo, biến thể | Chuyên môn đo bóc |
| Chuyên môn đo bóc | Công thức, phạm vi, giao/trừ, bảng thép, đáp án | Một người kiểm độc lập không tự duyệt toàn bộ đáp án mình lập |
| Phụ trách vật liệu/giá | Danh mục, định mức, cấp phối, xác minh nguồn cung và báo giá | Chuyên môn đo bóc + QA |
| QA dữ liệu | Manifest, phân tách build/test, kiểm chất lượng, benchmark và release | Người phụ trách hệ thống |

Đây là 5 luồng trách nhiệm, không mặc định có 5 người hoặc gán tên của nhóm trong tài liệu tham khảo. Nếu một người kiêm nhiệm, phải điều chỉnh thời lượng và giữ bước kiểm độc lập cho đáp án nghiệm thu.

## 6. Kế hoạch sáu tuần

### Tuần 1 — Chốt hợp đồng và kiểm kê

- Backend: đối chiếu đúng 20 bảng vật lý; kiểm tra view chuyển tiếp; xuất từ điển dữ liệu và ánh xạ dữ liệu cũ–mới.
- CAD: kiểm kê toàn bộ file, vai trò, phiên bản, hash, khả năng mở và mức đầy đủ của từng hồ sơ.
- Đo bóc: chốt danh mục công tác trong phạm vi; mẫu nhãn cấu kiện/số đo; quy tắc cộng/trừ và cách ghi trường hợp không đủ dữ liệu.
- Vật liệu/giá: lập ma trận thiếu theo mã vật liệu, quy cách, định mức, nguồn cung và cơ sở giá; xác minh phân loại giá/dữ liệu mẫu hiện có.
- QA: chốt 28 tình huống kiểm chứng ở mục 7; tiêu chí nghiệm thu, split và manifest.

Đầu ra M1: từ điển dữ liệu 20 bảng; danh sách hồ sơ và khoảng trống; biểu mẫu nhập; bộ kiểm chất lượng chạy được. Không đóng băng các giá trị chưa có nguồn.

### Tuần 2 — Hoàn thiện một gói hồ sơ mẫu

- Chọn một công trình build đủ kiến trúc/kết cấu; hoàn thiện phiên bản hồ sơ, vùng hình, tầng, tỷ lệ và danh mục cấu kiện.
- Gắn nguồn từng số đo; liên kết mặt bằng–chi tiết–bảng thống kê; kiểm tra handle/INSERT và cửa chủ.
- Lập đáp án nháp theo cấu kiện và công tác; người thứ hai kiểm các phần đã lập.
- Hoàn thiện danh mục/định mức của các công tác trong hồ sơ này; lập danh sách báo giá cần lấy.
- Backend nạp thử toàn bộ qua pipeline thật; QA đối chiếu số dòng và snapshot với file nguồn.

Đầu ra M2: một Data Pack đọc được từ CAD đến khối lượng và phương án vật liệu. Phần chưa có giá/định mức vẫn hiển thị thiếu; không điền mẫu thay thật.

### Tuần 3 — Mở rộng hồ sơ và hoàn thiện ground truth

- Thu thập/chuẩn hóa các hồ sơ còn lại; giữ tập test độc lập và giới hạn quyền xem đáp án khi điều chỉnh quy tắc.
- Kiểm nhãn cấu kiện và số đo cho các loại móng, cột, dầm, sàn, tường, cửa, cầu thang và thép trong phạm vi.
- Ghi rõ công tác ngoài phạm vi/chưa hỗ trợ; không bỏ khỏi mẫu số mà không giải thích.
- Hoàn thành đáp án đã kiểm cho các hồ sơ có đủ căn cứ; ghi người kiểm và hash nguồn.
- Hoàn thiện quy cách vật liệu, cấp phối và báo giá trọng tâm; xác minh thời gian cung ứng.

Đầu ra M3: danh sách gói hồ sơ phát triển/nghiệm thu; đáp án có nguồn và trạng thái kiểm; báo cáo phần chưa đủ để đánh giá.

### Tuần 4 — Hợp nhất và chạy cổng chất lượng

- Nạp các gói vào database thử nghiệm 20 bảng, không thay schema để chạy riêng từng hồ sơ.
- Kiểm trùng mã/phiên bản, quan hệ chéo dự án, số đo khác đơn vị, ID trong JSONB, giá sai cơ sở và định mức thiếu nguồn.
- Kiểm không đếm trùng cấu kiện xuất hiện ở nhiều hình; kiểm dòng khấu trừ và cộng theo đơn vị.
- Chạy hai phương án vật liệu trên cùng snapshot khi hình học không đổi. Thay chiều dày ảnh hưởng thiết kế phải tạo lần tính mới.
- Chạy 28 ca chức năng; công bố danh sách đạt, sai và chưa đánh giá được, không chỉ phần đã ra số.

Đầu ra M4: bản dữ liệu ứng viên; lỗi toàn vẹn và sai nhãn không còn ở phần được công bố sẵn sàng; các phần thiếu có danh sách riêng.

### Tuần 5 — Đánh giá độc lập và sửa đúng nguyên nhân

- Đóng băng phiên bản engine, quy tắc, danh mục và bộ test trước đánh giá.
- Đo nhận dạng cấu kiện, liên kết số đo, sai số khối lượng, độ phủ nguồn và khả năng phát hiện thiếu/mâu thuẫn.
- Kiểm báo giá và tối ưu bằng phương án đối chứng nhỏ có thể tính tay hoặc vét cạn.
- Phân lỗi thành dữ liệu nguồn/nhãn, thuật toán, định mức/đơn vị, benchmark; sửa đúng lớp gây lỗi.
- Nếu cần nhìn vào test để sửa, ghi nhận tập đã bị sử dụng phát triển và chuẩn bị tập test mới; không tiếp tục gọi kết quả đó là độc lập.

Đầu ra M5: báo cáo benchmark có mẫu số, số hồ sơ, phiên bản, sai số và giới hạn; ledger lỗi và vòng sửa dữ liệu đầu tiên.

### Tuần 6 — Hồi quy và bàn giao

- Chạy lại cổng chất lượng, ca nghiệp vụ, hồi quy API và tính nhất quán snapshot.
- Kiểm phục hồi database kèm file CAD/mô hình; đối chiếu hash và mở lại nguồn.
- Chốt release manifest: file, phiên bản, số dòng, hash, split, engine/config và người kiểm.
- Xuất từ điển dữ liệu, ERD, báo cáo chất lượng, gói đáp án, hướng dẫn cập nhật và biên bản phần còn thiếu.
- Chỉ phát hành dữ liệu đã đạt; phần chưa đủ giữ nhãn chưa sẵn sàng và chủ thể chịu trách nhiệm bổ sung.

Đầu ra M6: gói dữ liệu có phiên bản có thể khôi phục và kiểm chứng. Không dùng câu “nhận diện mọi bản vẽ” hoặc “độ chính xác 100%” khi dữ liệu chưa chứng minh.

## 7. Bộ 28 tình huống kiểm chứng dành cho OptiMat

| Mã | Tình huống | Kết quả phải kiểm |
|---|---|---|
| TC01 | CAD hợp lệ, đơn vị mm | Mở file, xác định đúng đơn vị và hình |
| TC02 | Đơn vị m/cm hoặc khai báo sai | Quy đổi đúng khi đủ căn cứ; chưa rõ thì báo thiếu |
| TC03 | Nhiều tỷ lệ cùng file | Không áp một tỷ lệ cho tất cả hình |
| TC04 | Đổi tên layer/block | Kết quả không phụ thuộc tên của hồ sơ mẫu duy nhất |
| TC05 | Dịch chuyển/xoay hình | Khối lượng bất biến khi thiết kế không đổi |
| TC06 | Block lồng và INSERT lặp | Định vị đúng nguồn, phân biệt lần chèn |
| TC07 | Một cấu kiện trên nhiều hình | Không nhân số lượng cấu kiện |
| TC08 | Mặt bằng và chi tiết cùng mã | Liên kết đúng cấu kiện/tầng |
| TC09 | DIMENSION khác hình học | Giữ hai giá trị và báo mâu thuẫn |
| TC10 | Thiếu chiều cao/dày/tiết diện | Không tự điền; chỉ rõ công tác thiếu |
| TC11 | Hai ứng viên cùng được chọn | CSDL/transaction từ chối |
| TC12 | Cửa thuộc tường | Trừ đúng cửa và đúng tường chủ |
| TC13 | Cửa thiếu kích thước | Không âm thầm coi diện tích cửa bằng 0 |
| TC14 | Giao cột–dầm–sàn–tường | Áp đúng quy tắc trừ và nguồn |
| TC15 | Móng và bê tông lót | Đúng kích thước, đơn vị và số lượng |
| TC16 | Bảng thép theo một cấu kiện/toàn nhóm | Không nhân lặp sai; đúng chiều dài/khối lượng |
| TC17 | Thép thiếu bảng thống kê | Phân biệt chưa xác định và giả định được công bố |
| TC18 | Hồ sơ chưa biết vật liệu | Vẫn lưu số đo/khối lượng; nhu cầu vật liệu chưa xác định |
| TC19 | Hai phương án cùng hình học | Đúng định mức và lượng mua riêng từng phương án |
| TC20 | Phương án đổi chiều dày | Bắt buộc tính lại phần chịu ảnh hưởng |
| TC21 | Thiếu định mức hoặc cấp phối | Giữ phần đã biết và lý do thiếu |
| TC22 | Quy đổi kg/tấn/bao/viên/m³ | Đúng chiều hệ số và không cộng khác đơn vị |
| TC23 | Hao hụt đã gồm trong định mức | Không cộng hao hụt hai lần |
| TC24 | Giá công bố, báo giá và giá dự đoán | Phân biệt nguồn và phạm vi sử dụng |
| TC25 | Giá khác VAT/vận chuyển/ngày | Không so sánh trực tiếp khi chưa chuẩn hóa |
| TC26 | Quan hệ chéo dự án/phiên bản | Bị từ chối trước khi lưu |
| TC27 | Đổi giá/quy tắc sau lần chạy | Snapshot cũ vẫn giải thích được |
| TC28 | Sao lưu/khôi phục và chạy lại | Nguồn đúng hash; kết quả tái lập trong điều kiện đã công bố |

## 8. Tiêu chí nghiệm thu

Các cổng bắt buộc: đúng 20 bảng vật lý; không có FK mồ côi hoặc liên kết chéo dự án trong dữ liệu phát hành; mọi số đo được dùng có nguồn hoặc giả định được ghi rõ; mọi hệ số quy đổi/định mức được dùng có đơn vị và nguồn; dữ liệu mẫu không xuất hiện như dữ liệu thật; file trong manifest mở được và đúng hash; thiếu dữ liệu không biến thành 0.

Với công thức xác định trên dữ liệu tổng hợp kiểm soát được, kết quả phải khớp đáp án tính độc lập trong dung sai số học đã công bố; không dùng sai số này để đại diện sai số nhận dạng CAD. Với hồ sơ thực, báo cáo riêng precision/recall cấu kiện, tỷ lệ gán số đo đúng, sai số từng công tác và độ phủ; ngưỡng chấp nhận do người phụ trách nghiệp vụ chốt ở Tuần 1 sau khi xem khả năng đo kiểm, không tự đặt ngưỡng “100% toàn hệ thống”.

Mỗi báo cáo có danh sách công trình, data_kind, split, trạng thái đáp án, người kiểm, phần ngoài phạm vi, phiên bản engine/quy tắc và số lượng mẫu. Một benchmark chạy hết không đồng nghĩa benchmark đạt chất lượng.

## 9. Phụ thuộc và rủi ro

- Thiếu hồ sơ đủ cặp kiến trúc/kết cấu hoặc quyền dùng: lập danh sách thiếu, không thay bằng dữ liệu giả rồi báo thực tế.
- Thiếu người kiểm đo bóc: vẫn hoàn thiện pipeline và nhãn nháp, nhưng chưa nghiệm thu độ chính xác.
- Dữ liệu giá ít hoặc khác cơ sở: chỉ tra nguồn có căn cứ, chưa nghiệm thu dự đoán giá.
- Gộp dữ liệu vào JSONB: phải có schema và kiểm tra lúc ghi; không coi mọi liên kết đã được FK bảo vệ.
- Quy tắc tối ưu theo hồ sơ mẫu: giữ tập test độc lập, dùng biến thể và ca âm; không cài đáp án vào quy tắc.
- Thiếu nhân lực cho sáu tuần: ưu tiên D01–D06 và một luồng end-to-end có nguồn, công bố rõ phạm vi D07–D10 chưa hoàn thiện.

## 10. Gói bàn giao và cơ chế cập nhật

Mỗi release gồm manifest.json, danh sách file/hash, từ điển dữ liệu 20 bảng, schema SQL, ánh xạ nhập, dữ liệu đã chuẩn hóa, ground truth, báo cáo 28 ca và benchmark hồ sơ thực, danh sách thiếu, hướng dẫn backup/restore và cập nhật. Không đưa mật khẩu hoặc thông tin kết nối vào gói bàn giao.

Khi có hồ sơ/giá/định mức mới: lưu nguồn → tạo phiên bản → chuẩn hóa → kiểm chất lượng → kiểm chéo → chạy hồi quy phần bị ảnh hưởng → phát hành manifest mới. Không sửa ngược snapshot đã xác nhận.

## 11. Checklist xử lý gốc đọc bản vẽ và hoàn thiện dữ liệu

Cập nhật 04/11/2026 theo yêu cầu chủ đồ án. **Ưu tiên làm rõ một hồ sơ đang có trước khi mua, tìm hoặc tải thêm bộ mới.** Chọn VN002 nhà Sang làm hồ sơ BUILD để hoàn thiện, chưa gọi là hồ sơ hoàn chỉnh. Dùng cặp DXF KT/KC và PDF/DWG nguồn đã được kiểm kê trong [báo cáo06](review/data20_06/README.md); không sửa bản gốc. Việc có tệp hoặc chạy ra số không đủ để đánh dấu đạt.

Cách đọc: `[x]` chỉ phần đã được đối chiếu và có biên nhận đúng phạm vi; `[ ]` là còn mở. **THIẾU** = chưa đủ đầu vào/nhãn/đáp án; **CHƯA KIỂM** = có mã/tài liệu nhưng chưa có kiểm chứng đúng ca; **ĐẠT** chỉ có hiệu lực với bằng chứng ghi ở dòng đó. A/B/C/D không thay trạng thái người kiểm. Bảng này là checklist, không tự cấp quyền chạy CAD, sửa canonical, DB, build, upload hoặc gọi AI. Quyền ghi và lượt kiểm theo [BOARD01](review/data20_01/BOARD.md); S20 giữ schema/migration/glue và một lượt suite/DB tại một thời điểm.

### 11.1. P0 — đóng chuỗi đọc bản vẽ đến khối lượng trên Pioneer

| Kiểm / ID | Vấn đề gốc | Bằng chứng/tài liệu đã có | Hiện trạng | Việc bổ sung cụ thể | Owner | Điều kiện đóng | Chủ đồ án cần cung cấp/chốt |
|---|---|---|---|---|---|---|---|
| [x] C00 · P0 | Chưa biết dữ liệu hiện có thiếu ở đâu | 01 đã đọc report06/07/05/04/16/14/15, đối chiếu CSV:458 đường dẫn,4 identity,249 công tác nguồn VN002,28 dòng ma trận; ghi trong BOARD | **ĐẠT phần kiểm kê**; chưa đạt đọc CAD | Giữ gap ledger và cập nhật theo receipt mới; không đếm số file thành số công trình | 01 | Có báo cáo và đối chiếu cấu trúc/giới hạn; không đóng các dòng CAD phía dưới | Chưa cần mua/tải hồ sơ mới |
| [ ] C01 · P0 | Chưa chứng minh KT/KC cùng thiết kế, đúng revision và mở được | 06 có hash cặp DXF, PDF/DWG/tiên lượng; 28/28 file metadata có mặt/khớp theo report06 | **THIẾU** revision thiết kế/quyền; **CHƯA KIỂM** mở cặp đợt này | Lập manifest VN002: vai trò, hash, lineage DWG→DXF, phiên bản, nguồn/quyền; kiểm mở đúng hai file trong lượt được giao, ghi lỗi/proxy/bỏ qua | 06; S20 khi nhập thử | Đọc được cặp, xác định cùng công trình/revision, hash truy lại và manifest không giả metadata | Xác nhận bộ nguồn/phiên bản nếu biết; quyền dùng nội bộ/huấn luyện/chia sẻ; bản thay thế chỉ khi chứng minh tệp hiện có hỏng/thiếu |
| [ ] C02 · P0 | Đơn vị CAD và tỷ lệ riêng từng hình có thể bị trộn | dxf_reader.py có declared_insunits/_check_units; dimensions.py có unit_ratios/view_scale; registry.py ghi issue khi thiếu tỷ lệ nhưng có nhánh scale or1.0; TC02–03 | **CHƯA KIỂM** trên từng hình VN002 | Chọn một mặt bằng và chi tiết liên quan; ghi đơn vị gốc/hệ số chuẩn/tỷ lệ hình cùng DIM kiểm chéo. Giữ tỷ lệ in, đơn vị và zoom là ba khái niệm riêng; không lấy khung tên áp mọi hình | 03 quy tắc;06 hồ sơ;07 nhãn;15 QA | Hai hình khác tỷ lệ về cùng kích thước thiết kế khi đủ nguồn; trường hợp không đủ phải báo chưa xác định và không xuất lượng như chắc chắn | Chỉ cần chỉ rõ kích thước/đơn vị thiết kế khi bản gốc mâu thuẫn; không nhập một tỷ lệ chung để che thiếu |
| [ ] C03 · P0 | Block lồng/INSERT lặp/xoay/scale làm sai tọa độ hoặc mất nguồn | _Collector.insert dùng virtual_entities/multi_insert, giới hạn độ sâu và cảnh báo; TC05–06; báo cáo07 còn thiếu INSERT path | **CHƯA KIỂM** trace từng occurrence VN002 | Chọn block thật đang có; đối chiếu tọa độ trước/sau, xoay/scale/phản chiếu nếu xuất hiện; lưu handle + đầy đủ đường dẫn lần chèn. Ghi entity không hỗ trợ/không mở được | 03;07;15 | Về đúng vị trí/đơn vị; nhận đúng số instance; truy đúng block nguồn; vượt giới hạn không âm thầm mất cấu kiện | Chưa cần bộ mới; cung cấp/xác nhận XREF/font/bản gốc nếu reader báo thiếu tài nguyên |
| [ ] C04 · P0 | Trộn mặt bằng, mặt cắt, chi tiết hoặc bảng thép thành cùng vùng | plans.py/find_plans, sheets.py, registry.py có phân vùng theo tiêu đề/khung; report07 thiếu vùng/tầng/transform | **THIẾU** nhãn vùng đủ | Lập danh sách vùng hình VN002 có bbox, loại hình, tầng, tỷ lệ, quan hệ; kiểm vùng sát nhau/không có tiêu đề và lưu đối tượng chưa phân loại | 07 nhãn;03 quy tắc | Khớp nhãn vùng đã kiểm; không dùng mặt đứng/chi tiết làm mặt bằng mới; có mẫu số cả vùng bỏ sót/sai | Xác nhận tên tầng/vùng không rõ trên nguồn; không tự suy từ thứ tự trang |
| [ ] C05 · P0 | Nhận chữ/mã chưa chứng minh nhận đúng hình học cấu kiện | registry.py có Component/Occurrence/EvidenceRef; walls.py và rough có bộ tính theo cấu kiện;07 mới có2 nhóm nháp,không phải2 instance vật lý hoàn chỉnh | **THIẾU** danh sách instance chuẩn | Chọn phạm vi nhỏ của VN002; đánh nhãn tường/cửa và cột/dầm liên quan, rồi mở rộng móng/sàn/thang. Mỗi instance có hình học, tầng/vùng, loại/mã và dấu vết nguồn; ghi nhận nhầm/bỏ sót | 07;03 thuật toán sau phân quyền | Đếm được đúng từng instance trong phạm vi đã khóa; precision/recall có mẫu số, không lấy số nhóm thống kê làm số cấu kiện | Người có chuyên môn kiểm danh sách/loại; chốt phần thô nằm trong demo |
| [ ] C06 · P0 | DIM/chữ số đo có thể gắn nhầm cấu kiện, phương hoặc đơn vị | dimensions.py đọc DIM thẳng ngang/đứng ở modelspace; bỏ chữ không thuần số như Ø6a200/2x100.07 có4 ứng viên đọc chữ,selected=false | **THIẾU** liên kết số đo hình học; có giới hạn reader | Giữ số hiển thị, số đo hình học, điểm gióng/phương, đơn vị và ứng viên. Gắn theo cấu kiện/vùng/nguồn, không chỉ chữ gần nhất. Liệt kê DIM trong block, nghiêng, text phức hợp chưa hỗ trợ | 03;07;15 | Mỗi số dùng tính truy về đúng thuộc tính/instance; ca DIM khác nét giữ cả hai và issue; không chuyển khối lượng bảng thành chiều dài | Chọn giá trị đúng khi nguồn thiết kế mâu thuẫn; không cần nhập lại mọi kích thước có nguồn |
| [ ] C07 · P0 | Cùng mã trên nhiều tầng/chi tiết dễ ghép nhầm hoặc nhân lặp | registry.py ghép symbol/floors/details và báo hình dùng nhiều tầng; C01 yêu cầu cùng phạm vi;TC07–08/16 | **ĐẠT MỘT PHẦN**: đã định vị hai dầm DM-1 bể nước trên mặt bằng móng dưới gara tầng 1 (mục 11.5). Còn thiếu xác nhận độc lập và liên kết từng dầm với đối tượng CAD | Tách identity cấu kiện vật lý khỏi occurrence trên hình/bảng; ghi quy tắc mã+tầng+trục/quan hệ chi tiết. Kiểm chi tiết điển hình, mã lặp và bảng thép theo một cấu kiện/toàn nhóm | 07;03 | Ghép đúng mặt bằng↔chi tiết↔thống kê; số lần lặp chỉ một lần; không mặc định mỗi hình là cấu kiện mới | Chốt phạm vi áp dụng chi tiết/bảng điển hình khi nguồn không nói rõ |
| [ ] C08 · P0 | Trừ cửa/giao cột–dầm–sàn–tường và chống trùng chưa có đối chứng đủ | TC12–16, drawing/takeoff.py, rough; docs/KIEM_TRA_CONG_TAC_KHOI_LUONG.md yêu cầu lượng gộp/trừ/net;07 có xung đột bảng bể | **THIẾU** oracle giao/trừ | Trên vùng Pioneer đã nhãn, xác định tường chủ của cửa, số đo lỗ, miền giao, gross/deduction/net và nguồn từng khoản. Kiểm cửa thiếu kích thước, cha/con, hình lặp, thang/mái/bể riêng | 07 nhãn;03 tính;15 kiểm | Tính tay độc lập cùng phạm vi/đơn vị; không trừ hai lần, không cộng cha+con; thiếu giữ missing, không coi cửa thiếu là0 | Người kiểm chốt quy tắc đo/giao/trừ và cấu kiện chủ không rõ |
| [ ] C09 · P0 | Thiếu/mâu thuẫn có thể bị biến thành số0/giả định chắc chắn |07 giữ20,6/17,0/36,9kg ở tầng con/tổng khác nhau; W007 chưa có oracle;TC09–11/13/17 | **THIẾU** quyết định nguồn, **CHƯA KIỂM** toàn chuỗi | Lập issue mỗi thuộc tính/công tác; giữ NULL khác0 và không áp dụng; tách A/B/C/D với approval; số nhập bổ sung là giả định có nguồn, không nâng A | 07;03;S20 kiểm lưu;15 | UI/API/snapshot/BOQ cùng lý do thiếu; chưa đủ không ra tổng đầy đủ; không chọn36,9 hoặc37,6 để che xung đột | Cung cấp chi tiết/bảng sửa đổi hoặc xác nhận giả định cụ thể; không duyệt tổng khi chỉ kiểm một ô |
| [ ] C10 · P0 | Chưa có nhãn và đáp án độc lập để biết reader sai ở bước nào |07 coverage249 dòng,5 DEV/244 cách ly;0 oracle độc lập đã xác nhận. C01 chỉ BUILD,0da_kiem; số móng/thép bộ46 từng lấy từ chính dự toán | **THIẾU** đáp án/người kiểm | Khóa phạm vi Pioneer trước; lập nhãn vùng/instance/số đo/công thức có hash/nguồn, một người lập và người thứ hai kiểm. Giữ tiên lượng là tài liệu tham chiếu; không lấy output engine làm oracle | 07;15;00 | Bộ expected đã kiểm riêng; mẫu số gồm cả bỏ sót/không hỗ trợ; dung sai/đơn vị được chốt trước chạy | Chọn người lập/người kiểm thực và tiêu chí; cung cấp số đo độc lập chỉ nơi tài liệu hiện có không đủ |
| [ ] C11 · P0 | Có tổng nhưng chưa lần được cấu kiện→công thức→tổng khối lượng | docs/KIEM_TRA_CONG_TAC_KHOI_LUONG.md, M1; C01 bản gốc có cảnh báo cũ, phải xem reports/c01_review_fix/HUONG_DAN_BAN_SUA.md và BAN_GIAO.md | **CHƯA KIỂM** VN002 theo diễn giải mới | Xuất một công tác đủ và một công tác partial: cấu kiện/tầng, số lượng, kích thước, hệ số, lượng gốc, trừ/net, raw trước làm tròn, nguồn từng đầu vào. Khớp API/web/BOQ cùng snapshot; không suy chiều từ chuỗi công thức | 03 producer;owner UI/BOQ khi01 cấp;15 QA | Cộng từng dòng khớp tổng cùng đơn vị; lặp một lần; số thiếu vẫn thấy; có bằng chứng nguồn mở lại được | Chốt công tác/vùng nghiệm thu đầu tiên; chưa cần chọn gạch/NCC để tính hình học |
| [ ] C12 · P0 | Snapshot/nguồn lưu có thể sai dù đọc CAD đúng |14 nêu hash có thể gỡ khóa,catalog lúc save,path rootwalls,evidence orphan,revisionNULL;15mappingTC26–28;S20 giữ solewriter | **CHƯA KIỂM** bản sửa sau review | S20 xử lý finding và kiểm clone: khóa hash/result/input,đúng path/analysis/revision;catalog thực dùng hoặc cờ chưa xác minh;rollback/restore/ACL. Không sửa main trước gate | S20;14 review;15 evidence | Có diff/hash và terminal đúng ca; bản cũ mở lại đúng nguồn; không coi counts backfill là CAD verified | Quyết định main migration riêng sau gói chứng cứ; không cần mật khẩu/DSN qua chat |
| [ ] C13 · P0 | Tập TEST đăng ký không còn chắc độc lập |07 DI_AN_EXPOSURE_LEDGER: banve1 đã cung cấp ca đơn vị/cụm cột và phạm vi M01; C01 về sau bỏ qua không xóa lịch sử này | **THIẾU** holdout đạt tính độc lập | Giữ cases.csv TEST/aliasVN003, ghi exposure phạm vi cụ thể; không dùng làm “chưa từng xem”. Hoàn thiện BUILD trước; lập yêu cầu hai holdout mới sau khi rõ thiếu, không tự mua/tải/đổi split | 07;15;06;00 | Có split theo identity/lịch sử tiếp cận,expected độc lập/hash khóa trước mở; chưa đủ thì báo chưa đánh giá | Chốt cách công bố Dĩ An đã phơi lộ; sau Pioneer mới quyết định nguồn/quyền test bổ sung |

### 11.2. P1/P2 — sau khi có hình học/công tác đủ nguồn

| Kiểm / ID | Vấn đề gốc | Bằng chứng/tài liệu đã có | Hiện trạng | Việc bổ sung cụ thể | Owner | Điều kiện đóng | Chủ đồ án cần cung cấp/chốt |
|---|---|---|---|---|---|---|---|
| [ ] C14 · P1 | Danh mục/định mức chưa khớp quy cách Pioneer |05 GAP_DINH_MUC: DB31/CSV68, GN01 cao60/65,TRAT gộp,CAN_NEN mã nhóm;15quan hệ và22hệ tường đang có | **THIẾU** nguồn/phạm vi được kiểm | Rà C05-01/03/08 trên đúng quy cách,đơn vị/hao hụt;không chia đôi tường110 thành55,không dùng định mức tường cho mọi mặt;chưa đủ giữ lượng hình học | 05;07 phạm vi | Hệ số có mã/trang/đơn vị/cơ sở;không hao hụt hai lần;thay dày buộc tính lại | Xác nhận quy cách/mác/hệ thiết kế khi nguồn thiếu;không phải chọn tùy ý để hợp engine |
| [ ] C15 · P1 | Phương án/nhu cầu có thể mất liên kết với bản bóc |04 SCENARIO_CONTRACT 6ca;req.groups chưa so takeoff,requirements=[] vàsnapshot/config còn gap | **CHƯA KIỂM** bản sửa | S20 giữ binding/cấu hình/snapshot version;không biến proposal thành chỉ định hoặc selected thành duyệt mua;không bắt vật liệu trước đọc hình học | S20;04;15 | Đọc lại và nối được analysis→work→assignment→requirement;giữ phần thiếu;thay cấu tạo ảnh hưởng hình học tạo lần tính mới | Quyết định vật liệu sau khi hiểu khối lượng và ảnh hưởng thiết kế |
| [ ] C16 · P2 | Giá/NCC chưa đủ điều kiện mua hoặc so tối ưu |04:98 mã rà,13cặpSAMPLE/0CSVchính;16:63BULLETIN+15gap,chưaquotemua đúngđơn | **THIẾU** chứng từ thương mại | Sau Pioneer,chọn vật tư thực cần mua/địa bàn;thu đúngSKU/đơn vị/lượng/hiệu lực/VAT/cước/leadtime;không đổi thiết kế để tận dụng mã có giá | 04;16 | Có báo giá cùng cơ sở và snapshot chứng từ;thiếu giá vẫn cho xem hình học/phương án có điều kiện | Nơi/ngày giao,lượng đã kiểm và chứng từ NCC khi đến bước mua;chưa cần thu45giá trước giải gốcCAD |
| [ ] C17 · P2 | Chưa đủ dữ liệu để đánh giá mô hình dự đoán giá |16 READINESS_20:1.248SYNTHETIC không làACTUAL;360=15×24tháng chỉmục tiêu | **THIẾU** tập giá đủ nguồn/split | Dùng tra giá có nguồn;chỉ mở train khi dữ liệu đủ chia thời gian/vật liệu,baseline,cơ sở giá vàprotocol được duyệt | 16;00;01 | Có tập train/val/test thật,coverage/metrics trên cùng tập;không nhân bản63dòng hoặc lấy dữ liệu mẫu làm thật | Chưa cần đầu tư thêm dữ liệu giá để kiểm reader;quyết định thu giá sau phạm vi Pioneer |

### 11.3. Thứ tự làm ngay và đầu ra phải nhìn thấy

1. **Khóa đầu vào VN002 (C01)** và chọn một phạm vi nhỏ trong cặp KT/KC hiện có: mặt bằng + chi tiết/mặt cắt liên quan. Xác định tầng từ nguồn, không tự đoán. 06/07 chỉ ra đúng file/hash/vùng/công tác; không bắt đầu bằng nạp thêm hàng loạt hồ sơ.
2. **Theo dấu đọc (C02–C07):** file/entity/INSERT→vùng/tầng/tỷ lệ→instance→số đo. Lập một bảng expected/actual cho từng bước, lưu vị trí nguồn và danh sách đối tượng bỏ sót/nhầm. Ưu tiên bóc tường/cửa và cấu kiện kết cấu liên quan có đủ bằng chứng; mục nào chưa đủ hiện issue.
3. **Tính và đối chiếu (C08–C11):** làm rõ gross/trừ/net và một lần lặp; so tay độc lập; từ số sai truy về lỗi vùng/hình học/liên kết số đo/phạm vi/công thức. Không chỉnh hệ số để tổng khớp tiên lượng.
4. **Giữ nguồn khi lưu và mở lại (C12):** kiểm trên clone theo quyền S20; kết quả26/W5 và runtime cũ không tự tiếp tục trong checklist này. Chưa có receipt thì giữ ô trống.
5. **Chỉ sau đó** mở định mức/vật liệu C14–C15; giá và dự đoán C16–C17 là cổng sau. Công trình chưa chỉ định vật liệu vẫn phải lưu/xem được hình học và khối lượng có nguồn (TC18).

**Chủ đồ án cần giải quyết trước mắt:** xác nhận bộ VN002/phiên bản/quyền sử dụng, chọn người kiểm độc lập và phạm vi công tác đầu tiên; chỉ bổ sung trang/chi tiết/số đo cụ thể khi nhóm chỉ ra đúng chỗ thiếu. Chưa có lý do yêu cầu mua một bộ dữ liệu khác trước bước xác minh này.

Bản kế hoạch này giữ 20 bảng và lịch sáu tuần đã nêu; checklist không đổi mục tiêu thu thập thành kết quả đã có. Nguồn bổ sung: [readiness/coverage07](review/data20_07/README.md), [QA28ca](review/data20_15/EVIDENCE_REQUIREMENTS.md), [review14](review/data20_14/REVIEW.md), D09: chờ owner03 bàn giao tại docs/review/data20_03/, [yêu cầu khối lượng](KIEM_TRA_CONG_TAC_KHOI_LUONG.md). Các file nguồn/code chỉ được đọc để chỉ ra khả năng/giới hạn; chưa chạy CAD hoặc kiểm thử mới trong lượt append checklist này.

### 11.4. Tận dụng ca và mã sẵn có, chưa coi là nghiệm thu Pioneer

03 đã bàn giao tóm tắt D09; 01 đối chiếu có các test đơn vị/biến đổi dưới đây trong mã. Đây là **danh sách kiểm sẽ dùng**, chưa chạy lại và chưa chứng minh VN002 đạt. Không viết lại reader hoặc thu thêm hồ sơ trước khi dùng ca hiện có để khoanh lỗi.

| Dòng checklist | Mã/ca có thể dùng lại | Khoảng trống phải lấp trên Pioneer |
|---|---|---|
| C02 | test_drawing_io.py::test_declared_inch_but_dimensions_in_mm, test_declared_units_kept_when_dimensions_agree_or_too_few; test_ingest.py::test_headerless_dxf_is_not_meters; dimensions.py::view_scale | Đơn vị thiếu/mâu thuẫn; nhiều hình khác tỷ lệ; DIM sửa chữ và DIM không nhất quán. Các ca có dấu vết banve1 không chứng minh test độc lập |
| C03 | test_drawing_io.py::test_every_transform_read_in_world_coords; dxf_reader.py::_Collector.insert, MAX_BLOCK_DEPTH=16 | Truy nguồn qua từng cấp; block thật, scale không đều, vượt độ sâu/bỏ qua; không chỉ kiểm tọa độ hình tổng hợp |
| C04/C07 | plans.py, sheets.py, registry.py, rough/structural.py; tests/test_encoding_plans.py | Ghép tên tầng KT/KC, mã giống khác tầng, mặt cắt/chi tiết không bị tính thành mặt bằng. Đối tượng REGION/không hỗ trợ phải có issue, chưa xác nhận ca REGION riêng |
| C06 | dimensions.py::_linear_dims/_shown; registry.py::build_registry/_resolve | Reader DIM hiện chỉ ngang/đứng modelspace; cần expected cho DIM block/nghiêng/chữ phức hợp, giữ chưa hỗ trợ khi chưa làm được |
| C07/C08 | rough/rebar.py và tests/test_rough_rebar.py có ca bản sao/cùng phạm vi/tầng độc lập/trùng một phần | Kiểm bảng thật VN002, không suy cùng tổng kg là cùng cấu kiện hoặc bản sao; giữ mâu thuẫn tiêu đề/cha-con |
| C12/D09 | rule_sets và các CSV/ngưỡng/ký hiệu/hằng số trong source thực đọc | Chốt manifest **toàn bộ đầu vào thực dùng**, thứ tự ưu tiên, phiên bản/hash; chỉ chụp rule_sets chưa chứng minh tái lập reader |


### 11.5. VN002 định vị hai dầm DM-1 của bể nước

**C04, C05, C07 — đã xác định trên hồ sơ.** N-01 (hồ sơ nước, trang 3) đặt bể nước dưới gara tầng 1. KC-01-05 (kết cấu, trang 11) định vị bể giữa trục 1 và 2, trong khoảng A–B. KC-01-11 (trang 17) chỉ hai nhãn DM-1 vào hai cạnh dài của đáy bể, ghi dài 2.500 mm, rộng 220 mm, số lượng 02 và cao độ đỉnh/đáy −1,200/−1,500 m. Cả hai là dầm móng bể, chạy theo phương từ trục 1 tới trục 2. Bể phốt trong ô 3–4 có mã dầm trùng và được thống kê riêng.

| Vị trí từng dầm trên mặt bằng công trình | Mép ngoài tính từ trục A về phía B | Tim suy ra từ bề rộng 220 mm |
|---|---|---|
| DM-1 phía A, sát cạnh dài gần trục A | 390 mm, kích thước ghi trên KC-01-05 | 500 mm từ A về B |
| DM-1 phía B, ở cạnh dài đối diện | 2.390 mm = 390 + 2.000 | 2.280 mm từ A về B |

**C02, C06 — cách đối chiếu.** KC-01-05 ghi bể dài 2.500 mm theo phương 1–2, rộng 2.000 mm theo phương A–B. Mép bể gần trục 2 cách trục 2 là 890 mm. Với nhịp 1–2 dài 6.020 mm, hai đầu dầm lần lượt cách trục 1 là 2.630 và 5.130 mm. Vị trí tim trong bảng là kết quả ghép kích thước bao với chi tiết dầm. Hai tên “phía A” và “phía B” là tên theo dõi do nhóm đặt. Có thể kiểm lại bằng cách mở trang 11 và 17 cạnh nhau rồi đối chiếu N-01 và N-06 (hồ sơ nước, trang 8).

**C08, C10 — còn thiếu.** Bảng thép KC-01-12 (trang 18, bảng bể nước bên phải) cho số thanh của cả nhóm hai dầm. Dòng STT 1 có tổng 4 thanh, khối lượng 10,1 kg sau làm tròn. Giữ số lượng này ở cấp nhóm. Cần người kiểm độc lập đối chiếu cách ghép và vị trí tim, xác nhận phiên bản thiết kế, và kiểm reader tự liên kết từng cạnh với hình học CAD cùng tầng và trục. Các mục nghiệm thu tổng thể tiếp tục mở.

**Dữ liệu đã rà.** Đã lập danh sách và tính SHA-256 cho 288 tệp trong cả 9 thư mục con của data. Tìm theo tên, nội dung văn bản và tệp trùng hash cho thấy 4 DWG tại uploads trùng bản nguồn VN002. Bằng chứng định vị lấy từ các tờ kết cấu và cấp thoát nước nêu trên. Danh mục theo tệp lưu tại reports/vn002_dm1/inventory.json.
