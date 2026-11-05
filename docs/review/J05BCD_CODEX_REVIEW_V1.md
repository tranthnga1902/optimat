# Codex review J05c/J05b/J05d - vòng 1, 03/11/2026

Ba tài liệu mô tả thay đổi dự kiến, chưa có mã/dữ liệu được áp. Review này chốt hợp đồng và lỗi trong bản vá đề xuất; không nghiệm thu chức năng hoặc hồ sơ thực.

## Kết luận

| Gói | Kết luận chuẩn bị | Quyền tiếp tục |
|---|---|---|
| J05c | Chấp thuận hợp đồng có các yêu cầu dưới đây | Được triển khai trước, không đợi D02 để chạy test SYNTHETIC; áp hồ sơ/KPI vẫn chờ người kiểm |
| J05b | Cần sửa thiết kế hệ được chọn, phân loại dòng thiếu và biểu diễn phần còn thiếu | Sửa tài liệu riêng; chưa áp 15 dòng CSV hoặc sửa UI/materials |
| J05d | Chấp thuận ý tưởng giai đoạn 1 giữ phụ gia thiếu; bản vá thông báo/phân loại cần sửa | Sửa tài liệu riêng; tích hợp giai đoạn 1 sau J05c, không mở trường liều giai đoạn 2 |

## Phải sửa trước khi áp bản vá

### 1. Dòng chưa có mã bị phân loại sai và lọc mất (J05b, J05d)

- **Hiện trạng:** `materials.py::_Bill.result` gán `raw_class` theo `RAW_CLASS_BY_NAME` khi không có mã; bảng này chỉ nhận tên chứa thép/gạch/bê tông/vữa, còn lại là `khac`. `takeoff.py::compute_rough` sau đó lọc theo `params.material_classes`.
- **Ca lỗi:** “Ván ép công nghiệp”, “Khung xương nhôm” và “Phụ gia dẻo hóa” không có mã → `khac`; “Cột chống thép ống” → `thep`. Chọn `cop_pha` hoặc `phu_gia` sẽ làm các dòng mong đợi biến mất. Việc dòng có D và có mặt trong BOQ trực tiếp không chứng minh nó còn sau lọc.
- **Sửa:** đề xuất cách truyền loại vật tư đúng ngay cả khi chưa có mã, tận dụng metadata/luồng hiện có nếu được; nếu cần trường mới, trình hợp đồng trước. Không gán cả mọi dòng từ công tác bê tông thành `phu_gia`, không đánh tất cả dòng có chữ thép thành cốp pha. Tránh chữa bằng đổi tên để tình cờ khớp chuỗi. Không bỏ bộ lọc của người dùng.
- **Test bắt buộc khi triển khai:** gọi qua `compute_rough` với lọc `cop_pha`/`phu_gia`, kiểm dòng có số/thiếu vẫn còn đúng lớp và đi vào optimizer `missing`. Kiểm hồi quy thép cốt và các vật tư bê tông. Với lọc chủ động loại nhóm thì hành vi loại phải đúng phạm vi đã chọn.

### 2. Chọn “ván ép” chưa chứng minh đã chọn đúng hệ AF.83 (J05b)

- **Hiện trạng:** trường `formwork_type=van_ep` đang mô tả tấm ván; không có bằng chứng riêng rằng công trình chọn khung nhôm và chống thép ống. Đổi nhãn UI không tự xác nhận lựa chọn cũ/API cũ.
- **Ca lỗi:** hồ sơ dùng ván ép với đà/chống gỗ nhưng gửi `van_ep` sẽ được tính hao phí khung nhôm và chống thép của AF.83, dù ba dòng vẫn D vì thiếu mã.
- **Sửa:** chốt một lựa chọn hệ rõ nghĩa, có nguồn/xác nhận; giữ `van_ep` cũ ở trạng thái chưa xác định hệ, không tự nâng thành AF.83. Có thể đề xuất biến thể lựa chọn nhỏ nhất thay vì thêm nhiều trường; ghi đường tương thích API và dữ liệu lưu. Hệ hỗn hợp theo cấu kiện vẫn chưa mở trong lượt này.
- **Chiều cao:** chấp thuận nhận xét các cột đã tra có cùng hao phí vật liệu. Được ghi mã nhóm cùng bằng chứng các cột, không giả ghi mã ≤28 khi thiếu chiều cao. Chỉ kết luận số vật liệu trùng **trong miền các bảng đã tra**, không suy cho chiều cao ngoài miền. Không lấy chiều cao làm yêu cầu quyết định số khi đã chứng minh các cột cùng số.
- **Ánh xạ:** SAN/DAM/GIANG_TUONG/COT chữ nhật theo hệ được xác nhận có thể đề xuất tiếp; MAI chỉ chốt mái bằng BTCT trong đợt này. Mái nghiêng chưa được tự động áp chung chỉ vì mã MAI. Móng/thang/lanh tô/sê nô và tường/vách chưa có đường công tác giữ thiếu/chưa hỗ trợ. Thông báo không bảo người dùng đổi sang gỗ hoặc “nhập tay” như cách thoát thiếu khi chưa có cấu tạo và đường nhập được hỗ trợ.

### 3. Không được để “vật liệu khác” chỉ ở tài liệu rồi mất trên đầu ra (J05b)

- **Hiện trạng:** thiết kế mục 7 ưu tiên chỉ ghi note như AF.81. Khi ba mã chính được bổ sung về sau, không còn dòng nào chứng minh phần hệ còn thiếu, và note chưa chắc hiện ở đầu ra.
- **Ca lỗi:** ánh xạ xong ván/khung/chống, BOQ hiển thị ba dòng đủ dù phụ kiện/phần vật liệu khác chưa xác định. Lỗi đang có ở AF.81 không phải lý do lặp lại cho AF.83.
- **Sửa:** đề xuất biểu diễn phần vật liệu khác chưa quy thành lượng hoặc một cảnh báo nguồn gắn rõ công tác/hệ, được giữ qua API/BOQ và phân loại đúng. Không sinh 5% thành kg/bộ hoặc tự chọn CP05. Chứng minh khi ba dòng chính đã có mã, hệ vẫn không bị trình bày là danh sách mua ban đầu đầy đủ. Không sửa toàn bộ Q02.
- **Cơ sở luân chuyển:** ghi hao phí định mức khác lượng huy động/mua ban đầu là đúng. Tuy nhiên suy “21/100 nghĩa là mỗi tấm dùng nhiều lần” không đủ chứng minh chi tiết chế độ luân chuyển; ghi nguồn thuyết minh nếu khẳng định đã gồm và không tự suy số lần dùng.

### 4. Thông báo thiếu liều không được áp cho mọi định mức trống (J05d)

- **Hiện trạng:** bản vá `norm_line` đổi mọi dòng có norm_code nhưng thiếu value sang “chưa có liều/sản phẩm thiết kế”.
- **Ca lỗi:** dòng vật liệu khác AF.83 trống lượng có mã nguồn sẽ bị báo thiếu liều phụ gia, dù không phải phụ gia.
- **Sửa:** dùng thông báo chung đúng bản chất “đã có nguồn ...; chưa xác định lượng/điều kiện áp dụng”, đồng thời giữ lý do riêng phụ gia ở ngữ cảnh/metadata phù hợp và đầu ra thực sự hiển thị. Không dùng toàn bộ note thành mã thực thi. Giữ các dòng trống chưa có nguồn có thông báo phù hợp; không thay `Norm.value`.

## Chốt hợp đồng J05c để triển khai

1. Chấp thuận TRAT mang `WorkItem.wall_system_id` sẵn có, giữ `variant` đầu ra là chiều dày; khóa tra nội bộ `<dày>/<family>`, bốn dòng dữ liệu 15/20 mm SOLID/HOLLOW như đề xuất. Giữ CAN_NEN nguyên. Không thêm bảng/trường DB. Số đã điều chỉnh trong CSV, không nhân 1,10 ở Python.
2. Dùng family từ vật liệu chính của phương án tường, không hardcode GNxx trong Python. Danh mục hiện gọi GN02 là gạch nung 2 lỗ, GN03 6 lỗ, GO01 ống 4 lỗ, cùng CLAY_HOLLOW; **chấp thuận ánh xạ danh mục này cho luồng kỹ thuật**, không cần đợi người kiểm để viết test tổng hợp. Vật liệu thực tế của hồ sơ vẫn cần xác nhận đúng phương án. Không dùng việc hiện có family làm chứng nhận sản phẩm cụ thể.
3. [VSQI, TCVN 1450:2009](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+1450%3A2009) xác nhận phạm vi gạch rỗng đất sét nung, nhưng còn nêu ngoại lệ khối lượng thể tích >1600 kg/m³ được xem như gạch đặc. Không tuyên bố mọi viên có lỗ đều tự động là rỗng theo chuẩn trong mọi trường hợp. Có mâu thuẫn hồ sơ/sản phẩm với family thì giữ chờ xác nhận, không tự đổi hệ số từ số lỗ. Không thêm yêu cầu mật độ mặc định cho mọi test/catalog chỉ để giải quyết ngoại lệ chưa có hồ sơ cụ thể.
4. **Chấp thuận cách đọc +10% cho AK.211 và AK.212**: ghi chú đặt sau hai bảng dưới AK.210, không giới hạn trong/ngoài. Đây là kết luận đọc phạm vi của BA, không phải đã có công văn giải thích. Giữ nguồn chung AK.211/212 và ghi rõ hai mặt cùng hệ số; đừng hiển thị AK.212 như mã chính xác của mặt ngoài. Không cần mở thêm trường mặt chỉ để nhân một hệ số giống nhau trong sprint này.
5. Đã xem ảnh N2 PDF 590 và 591 / in 589 và 590. AK.213/214 dùng vữa trát bê tông nhẹ; AK.215/216 dùng vữa thông thường cho gạch không nung. Số 0,017 cho 15 mm cũng có ở AK.215/216: lỗi hiện tại là **chưa chọn đúng phạm vi/mã và loại vữa**, không đủ chứng cứ nói mọi lượng 0,017 trên AAC đều sai số học. Trong J05c cho AAC/CMU/CLC/panel/chưa rõ ra thiếu định mức phù hợp, chưa mở tra các bảng này. CMU_HOLLOW là gạch không nung theo danh mục: không áp CLAY_HOLLOW +10%; không còn chờ quyết định nhóm cho sprint này.
6. Truyền evidence lựa chọn theo `wall_systems_by_class` sang TRAT như đề xuất; giữ C khi nguồn nhập tay. Thiếu nền là thiếu bước vật tư, không xóa diện tích công tác đã biết hoặc tự ép WorkItem thành thiếu hình học. Sửa comment/serializer cần thiết; không mở refactor status tổng quát.
7. Pseudodiff có rủi ro `fam` chưa gán khi TRAT thiếu variant. Khởi tạo an toàn và kiểm riêng thiếu dày, thiếu mác, phương án không tồn tại/family trống; không chỉ test đường có variant.
8. Số tính tay là giá trị chưa làm tròn; hiện intermediate/result làm tròn 3 chữ số, MaterialUse 4. Ca 0,0374 m³ âm và số xi măng kg phải kiểm đúng đơn vị thật (XM01 là tấn) và đúng giai đoạn làm tròn; không yêu cầu đầu ra giữ toàn bộ chữ số nếu hợp đồng hiện tại làm tròn. Không gọi `MaterialUse.quantity` của xi măng là lượng vữa; kiểm intermediate hoặc công thức/uses đúng vật liệu.
9. Triển khai trước các ca đề xuất cộng thêm: rỗng mặt ngoài, thiếu dày, family trống, hai nền cùng mác không tăng toàn tổng; hồi quy test cũ cần đổi sang có phương án rõ. Giữ một ca chưa có phương án thực sự thiếu, không chỉ sửa hết fixtures để che đổi hành vi. Không cần DB migration; nạp/check dữ liệu trên DB kiểm thử theo quy trình, không DB thật.

## J05d: phạm vi được chốt và chưa chốt

- Chấp thuận giai đoạn 1 thêm dòng phụ gia không có số/khoảng/mã sản phẩm cho M350/M400, giữ ba lượng đã biết. Phải giải quyết phân loại/lọc và thông báo ở mục 1/4 trước tích hợp. Chưa thêm số nước hoặc chốt hao hụt chỉ trong gói này.
- Không coi ba vật liệu complete=True là chứng minh toàn bộ cấp phối hoàn chỉnh; dòng thiếu phải còn ở API/BOQ/optimizer đúng bộ lọc.
- Giai đoạn 2 **chưa duyệt trường mới**. Đề xuất đang gọi “một trường” nhưng chưa định nghĩa tên, kiểu container/cardinality cho nhiều mác. Cần chỉ rõ `%` nghĩa 0,6 hay 0,006, điều kiện số hữu hạn/dương, đơn vị/mật độ >0, nguồn/ngày xác nhận, cách thay dòng thiếu và từ chối mix_code/kind không khớp. Không lấy khoảng TT38 làm giới hạn liều thiết kế cứng khi chưa có căn cứ sản phẩm.
- Hợp đồng cấp phối thiết kế khác bảng vẫn ngoài lượt này. Bản sao và N7 chỉ được đối chiếu các đoạn đã đọc; không viết “khác duy nhất” cho toàn văn.

## Thứ tự giao Claude tiếp theo

1. **J05c:** sửa mô tả theo quyết định trên rồi triển khai/test trong luồng hiện có; bàn giao diff, lệnh/kết quả và giới hạn. Được sửa trường có sẵn theo hợp đồng đã chốt, không hỏi lại các quyết định đó. Chưa áp hồ sơ/KPI trước D02.
2. **J05b và J05d:** mỗi gói cập nhật tài liệu riêng để xử lý findings, không sửa mã dùng chung khi J05c đang chạy. J05b trình hệ/lọc/phần thiếu; J05d trình lọc/thông báo giai đoạn 1. Codex chốt bản sửa rồi mới tích hợp lần lượt.
3. Không sửa D02/cases/đáp án thực, không cập nhật trạng thái hoàn tất J05/J04. Trong đợt song song giữ nhật ký bàn giao trong tài liệu riêng, phiên tích hợp cập nhật file tổng hợp sau. Mã/dữ liệu sửa mới chạy test trọng tâm, toàn pytest và check_data đúng DB kiểm thử; không chạy đồng thời chung DB.

## Kiểm tra và giới hạn review

Đã đọc ba tài liệu, đường add/result/filter, Norm.value, trạng thái TRAT và export BOQ/optimizer; đối chiếu danh mục family và xem hai trang PDF bổ sung nêu trên. Không chạy pytest/check_data vì chưa áp mã/dữ liệu. Không kiểm chứng các số dòng mã được Claude ghi là ổn định; dev phải tìm lại theo symbol. Chưa kiểm chữ ký số, toàn văn N7-S7, lịch sử thay phụ lục hoặc dữ liệu hồ sơ thực. Các kết luận trên là review thiết kế, không chứng minh tính năng đã hoạt động.
