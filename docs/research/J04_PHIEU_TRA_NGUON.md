# J04 - Bốn phiếu tra nguồn phần thô

Ngày tra: 03/11/2026. **Chuẩn bị nguồn, chờ Codex review; chưa nghiệm thu J04.**
**Cập nhật review 03/11/2026:** [Codex review](../review/J04_CODEX_REVIEW.md) chấp nhận phần chuẩn bị nguồn trong giới hạn nêu rõ; J04 gắn hồ sơ vẫn chờ dữ liệu/D02. Phân định làm ngay/chờ và quyền ghi song song tại review cùng ba prompt thay cho cách hiểu gộp ở mục 6 bên dưới. Không xác nhận J05 đã hoàn thành.
D02 đang thực hiện ở phiên khác; chưa có đáp án hồ sơ được xác nhận để áp số vào công trình.
Chỉ sửa tài liệu này, không triển khai J05, không cập nhật CSV/catalog/DB hoặc trạng thái hỗ trợ.
Theo xác nhận trong chat ngày 03/11/2026, chuẩn bị ba gói bàn giao song song cho Claude: ván ép, trát, phụ gia; cán 50 mm giữ chờ nguồn.

## 1. Nguồn và cách kiểm

- [Trang văn bản Chính phủ](https://vanban.chinhphu.vn/?docid=218632&pageid=27160&typegroupid=6): TT 38/2026/TT-BXD, ban hành 26/06/2026, hiệu lực 01/07/2026; có liên kết cả hai phụ lục dưới đây.
- **N2:** [Phụ lục II chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf), Định mức dự toán xây dựng công trình, 724 trang.
- **N7:** [Phụ lục VII chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf), Định mức sử dụng vật liệu xây dựng, 180 trang. Đã mở qua liên kết đính kèm trên trang văn bản, không suy URL làm bằng chứng.
- **S7:** [Bản sao Phụ lục VII đang lưu trong repo](https://cdn.thuvienphapluat.vn/phap-luat/2022-2/DTTM/29-6-2026/PL7-TT-38.pdf). Chỉ đối chiếu các đoạn dùng trong phiếu 4, không xác nhận toàn văn trùng N7.

Quy ước trang: ghi **trang PDF đếm từ 1 / số in trên trang**. Ví dụ PDF 589 / in 588. Các vị trí bên dưới đã kiểm nội dung PDF qua web; ảnh cục bộ N2 PDF 455 và 589 đã được render bằng Poppler và xem trực quan để kiểm hàng/cột, đơn vị, ghi chú. Không coi OCR/text trích riêng là đủ chứng minh bố cục.

Mốc dữ liệu cục bộ khi tra:

| Tệp | SHA-256 |
|---|---|
| `data/rules/dinh_muc_phan_tho.csv` | `11DD461E2C87591DA5A1018C6222EF8108A7A187A6B863FCBCBF2A40246000BA` |
| N2 lưu tại `data/van_ban/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf` | `454AD108280159D4B041753EFEF0E248A989BE02B26F8D1076EEA19C42DD44FB` |
| S7 lưu tại `data/van_ban/PL7-TT-38.pdf` | `8BA969A2B1478FCA5BB9706CBD7041F92F77C726E7140E5184B0F6BD72BEE52D` |

N7 được kiểm trên web, chưa lưu vào kho hoặc tính hash; README nguồn vẫn mô tả hiện trạng cũ, không sửa trong lượt này. Chưa đối chiếu Công văn 9947/BXD-VPB với từng bản phụ lục; không khẳng định đã xác minh lịch sử thay thế. [Bộ Xây dựng đang đăng dự thảo sửa đổi](https://moc.gov.vn/vn/Pages/chitietduthao.aspx?iDuThao=1111), thời gian lấy ý kiến 26/10-04/11/2026; không dùng dự thảo làm hệ số vận hành.

Đã đọc CLAUDE.md, kế hoạch J04/J05, M01 mục 5A/5B, CSV và README nguồn. Phạm vi IN không có nghĩa đã hỗ trợ; nhập có nguồn vẫn phải giữ cách tạo đầu vào và trạng thái riêng. D02 phải chốt dòng đáp án/mẫu số, không tách dòng để nâng tỷ lệ.

## 2. Phiếu 1 - Cán nền 50 mm

**Hiện trạng:** CSV `CAN_NEN,50,@VUA` để trống `qty`, chưa có `norm_code`; dòng 30 mm có 0,035 m³/m². `rough/materials.py` dùng biến thể chiều dày để tra; không có căn cứ điền 50 bằng số của 30.

**Bằng chứng:** [N2, PDF 599 / in 598, AK.41100](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=599). Bảng láng nền/sàn không đánh màu có cột 2 và 3 cm; vữa lần lượt 0,025 và 0,035 m³/1 m². Mã đầy đủ tương ứng AK.41110/AK.41120. Không có cột 5 cm ở bảng này.

**Đơn vị/điều kiện:** 50 mm = 5 cm chỉ là đổi chiều dài, không tạo ra định mức hao phí. Không ngoại suy, không nhân 50/30 và không cộng các lớp giả định. Diện tích × 0,05 m chỉ cho thể tích hình học, chưa phải lượng vữa mua có hao phí.

**Đủ/thiếu vật liệu:** chưa có lượng vữa 50 mm có nguồn; chưa thể tách xi măng/cát đầy đủ. Cần người dùng cung cấp cấu tạo lớp cán, mác và cách cấp vữa, diện tích/chiều dày, định mức hoặc cấp phối được phê duyệt và cơ sở hao hụt. Nếu dùng vữa đóng bao cần suất dùng/chiều dày của đúng sản phẩm.

**Ca đề xuất:** 10 m², 50 mm: vẫn hiện công tác và vật tư thiếu định mức; không trả 0,35 hoặc 0,583333 m³ như số đã đủ. Ca kiểm soát 10 m², 30 mm theo AK.41120: 0,35 m³ vữa, trước bước phân rã cấp phối. Đây là ca đề xuất, chưa chạy.

**Kết luận: GIỮ TRỐNG / CHỜ NGUỒN.** Chưa chứng minh không có nguồn nào khác; chỉ kết luận AK.41100 không cung cấp trực tiếp 50 mm. Không mở J05a để điền số khi chưa có căn cứ mới được review.

## 3. Phiếu 2 - Ván ép AF.83 theo cấu kiện và hệ khung/chống

**Hiện trạng:** CSV `COP_PHA,VAN_EP,CP01` trống. Ghi chú “PL II chỉ có gỗ/thép” không còn phù hợp với N2 đã tra. CP01 là ván phủ phim m²; CP04 chống/giáo tính bộ, CP05 phụ kiện tính bộ; chưa có ánh xạ xác minh cho khung nhôm kg. `materials.py` chỉ tra VAN_EP chung, trong khi nguồn phân theo cấu kiện; `formwork_of` hiện được dùng để tra GO theo cấu kiện.

**Bằng chứng:** [N2, PDF 455-457 / in 454-456, AF.83000-AF.83400](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=455). Hệ ván ép công nghiệp, khung xương nhôm và chống thép ống. Các số sau là **hao phí cho 100 m² ván khuôn**, cột chiều cao ≤28 m; không phải bộ vật tư huy động đồng thời trên công trường.

| Cấu kiện | Mã cột ≤28 m | PDF / in | Ván công nghiệp m² | Khung nhôm kg | Chống thép ống kg |
|---|---|---|---:|---:|---:|
| Sàn mái | AF.83111 | 455 / 454 | 21 | 12 | 36,15 |
| Tường | AF.83211 | 456 / 455 | 13,13 | 12,65 | 38,13 |
| Xà dầm, giằng | AF.83311 | 456 / 455 | 21 | 15,05 | 39,61 |
| Cột vuông/chữ nhật | AF.83411 | 457 / 456 | 13,13 | 13,73 | 38,13 |

**Quy đổi:** mỗi hệ số trong bảng chia 100 để dùng trên 1 m²; diện tích là diện tích ván khuôn đã xác định, không lấy diện tích sàn thay mọi cấu kiện. Nguồn còn có vật liệu khác 5% theo cơ sở chi phí; không đổi 5% thành kg hoặc số bộ phụ kiện. Nhân công/ca máy ngoài phạm vi vật tư theo M01.

**Điều kiện:** người dùng xác nhận cấu kiện, chiều cao thực tế (≤5 tầng không tự chứng minh ≤28 m), đúng hệ khung/chống và quy cách ván; không áp AF.83 cho mọi ván phủ phim đi với gỗ hoặc hệ khác. Chưa xác lập mã AF.83 phù hợp cho móng, cầu thang, lanh tô, sê nô; không lấy dầm/sàn thay các dạng này.

**Đủ/thiếu vật liệu:** có căn cứ ba hao phí chính, chưa đủ danh sách mua/thuê. Cần quy cách ván để đối chiếu CP01, mã khung nhôm, chống kg hoặc căn cứ kg/bộ, chi tiết phụ kiện và xử lý phần vật liệu khác. Cần phân biệt hao phí luân chuyển với lượng mua ban đầu/tồn kho/thuê, không tự nhân số lần sử dụng lần nữa. M01 loại biện pháp thi công; việc đưa lượng thiết bị huy động/thuê vào danh sách mua cần BA phân định, không mở rộng bằng phiếu này.

**Ca đề xuất:** 10 m² dầm theo AF.83311 → ván 2,1 m²; khung 1,505 kg; chống 3,961 kg. Cột cùng diện tích → 1,313 m²; 1,373 kg; 3,813 kg. Không gọi cả hệ là đủ khi chỉ có CP01; đổi kg sang CP04 bộ khi thiếu khối lượng/bộ phải giữ thiếu. Móng/thang/hệ gỗ không khớp phải báo thiếu, không dùng hệ số sàn. Chưa chạy các ca.

**Kết luận: ĐỦ CĂN CỨ BẢNG CHO BỐN CẤU KIỆN NÊU TRÊN; CHỜ DỮ LIỆU HỆ VẬT LIỆU VÀ REVIEW.** Không đánh dấu VAN_EP đã hỗ trợ, chưa giao J05b điền một dòng CP01 chung.

## 4. Phiếu 3 - Điều chỉnh vữa trát trên tường gạch rỗng

**Hiện trạng:** CSV TRAT 15/20 mm có 0,017/0,023 m³/m², ghi AK.21200; dòng 15 có ghi chú +10% chưa áp. `walls.py` tạo TRAT theo mặt/chiều dày nhưng chưa gắn `wall_system_id` vào dòng trát; `materials.py` tra chỉ theo chiều dày. Chưa có đường xác nhận nền trát để áp hệ số một cách có nguồn.

**Bằng chứng:** [N2, PDF 589 / in 588, AK.21100 và AK.21200](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=589), ghi chú dưới hai bảng điều chỉnh hao phí vữa gạch rỗng +10%. Cột 15/20 mm tương ứng AK.21120/21130 (ngoài), AK.21220/21230 (trong). Bảng còn có “vật liệu khác” 0,5%, không phải 0,5% thể tích vữa.

**Đơn vị/quy đổi:** m³ vữa/1 m² mặt trát; nhân lượng vữa nền với 1,10, không tăng diện tích và không cộng 10% hai lần sau phân rã xi măng/cát. 15 mm → 0,0187; 20 mm → 0,0253 m³/m². Hệ số này là điều chỉnh do nền trát, không phải hao hụt mua bổ sung.

**Điều kiện:** xác nhận loại gạch thực tế, mặt và diện tích trát, dày, loại/mác vữa, nguồn thiết kế và người xác nhận. Không suy “rỗng” từ hatch/chiều dày tường. Không mở rộng tự động sang AAC, bê tông nhẹ, gạch không nung hoặc trát cột/dầm/trần; các nhóm kế tiếp có mã và điều kiện riêng cần tra đúng. Nền chưa rõ không mặc định đặc để trình bày tổng đủ.

**Đủ/thiếu vật liệu:** đủ căn cứ lượng vữa điều chỉnh trong đúng phạm vi; để ra vật tư mua còn cần cấp phối/quan hệ COMPOSED_OF đúng mác, hoặc sản phẩm vữa và đơn vị quy đổi. Phần vật liệu khác chưa được định danh để coi toàn bộ danh sách đủ.

**Ca đề xuất:** 10 m² gạch rỗng, 15 mm → 0,187 m³; 20 mm → 0,253 m³. Tường đặc 15 mm → 0,170 m³. Hai mặt 10 m²/mặt chỉ nhân diện tích một lần; tổng 0,374 m³ ở 15 mm. Nền không rõ giữ cờ thiếu; trát trên AAC không nhận hệ số qua tên “gạch” chung. Ca trừ âm phải đảo đúng phần vữa đã tăng. Chưa chạy các ca.

**Kết luận: ĐỦ CĂN CỨ HỆ SỐ; CHỜ ÁNH XẠ NỀN TƯỜNG, D02 VÀ REVIEW.** Có thể ưu tiên chuẩn bị J05c độc lập; chưa nghiệm thu khả năng xuất đủ vật tư.

## 5. Phiếu 4 - Phụ gia của cấp phối M350/M400 đang dùng

**Hiện trạng:** CSV dùng 11.12325/11.12326, XM02/CA01/DA01; ghi nguồn S7 và chưa tính phụ gia. Hệ số xi măng đang dùng là 394,625/436,65 kg trên m³ kết cấu (385/426 ×1,025). PG01 là tên chung nhiều loại phụ gia, đơn vị lít, thiếu sản phẩm/liều/khối lượng riêng; PG02 phụ gia kết nối không tự thay thế phụ gia dẻo hóa.

**Bằng chứng:** [N7 PDF 15 / in 14, bảng 11.12300](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf#page=15), cấp phối độ sụt 6-8 cm, Dmax20; 11.12325/26 ghi dẻo hóa. [N7 PDF 4 / in 3, hướng dẫn mục 4-5](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf#page=4) cho khoảng liều dẻo hóa 0,5-0,8% khối lượng xi măng và yêu cầu thí nghiệm cấp phối theo điều kiện thực tế.

Đối chiếu S7 cùng hai trang: các dòng 11.12325/26 và khoảng liều trên khớp N7. Không xác nhận hai PDF giống toàn bộ: phần tương quan mác/cấp bền ở trang in 3 có khác chữ tham chiếu tiêu chuẩn; không dùng kết quả đối chiếu cục bộ để duyệt mọi số lấy từ S7.

**Đơn vị/ca số học đề xuất:** với đúng cơ sở 1,025 đang dùng, tính khoảng khối lượng phụ gia tham khảo bằng khối lượng xi măng × tỷ lệ; không tự lấy trung điểm làm liều thiết kế.

| Mác | Xi măng kg/m³ vữa | Phụ gia kg/m³ vữa ở 0,5-0,8% | Phụ gia kg/m³ kết cấu, nhân 1,025 một lần |
|---|---:|---:|---:|
| M350 | 385 | 1,925-3,080 | 1,973125-3,157000 |
| M400 | 426 | 2,130-3,408 | 2,183250-3,493200 |

Đây là phép kiểm tra khoảng, **không phải lượng mua được duyệt**. Muốn đổi lít: L = kg / khối lượng riêng (kg/L) của đúng sản phẩm; thiếu khối lượng riêng thì giữ trống lít, không dùng 1 kg = 1 L. Không nhân 1,025 lần nữa nếu đã tính trên xi măng quy đổi trong CSV. Căn cứ áp 1,025 phải được reviewer kiểm theo đúng công tác bê tông, không coi là hệ số chung cho mọi cấu kiện chỉ từ phiếu này.

**Đủ/thiếu vật liệu và điều kiện:** còn thiếu sản phẩm dẻo hóa cụ thể, liều và cấp phối thiết kế/thí nghiệm được xác nhận, TDS tương ứng, quy cách đóng gói, kg/L khi mua lít; cần xác nhận cách cấp bê tông và biến thể xi măng/cốt liệu. Khoảng tra bảng không cho phép tự chọn phụ gia chống thấm/siêu dẻo hoặc giảm nước thêm trên cấp phối đã có. CSV chưa có dòng nước; phạm vi vật tư nước và cách thể hiện phần thiếu cần đối chiếu D02. Bê tông thương phẩm không bóc thêm phụ gia tại chỗ nếu thiết kế không có yêu cầu riêng.

**Ca thiếu/âm tính đề xuất:** thiếu sản phẩm/liều → dòng phụ gia chưa hoàn chỉnh dù ba vật liệu chính có số; thiếu kg/L → không ra lít PG01; đổi sang siêu dẻo → không dùng khoảng dẻo hóa; thương phẩm → không cộng phụ gia cấp phối vào lượng bê tông mua. Các khoảng trong bảng đã tính số học, chưa chạy kiểm thử mã.

**Kết luận: ĐÃ ĐỐI CHIẾU ĐƯỢC NGUỒN CHÍNH THỨC CHO ĐOẠN ĐANG DÙNG; CHỜ DỮ LIỆU THIẾT KẾ/SẢN PHẨM.** Chưa đủ căn cứ chốt lượng phụ gia mua, chưa được tự chọn một liều để triển khai J05d.

## 6. Ba gói bàn giao song song cho Claude dev

Ba nhánh dưới đây là nội dung chuẩn bị bàn giao, chưa phải lệnh triển khai J05. Không để ba phiên đồng thời sửa CSV/catalog/materials.py. Nếu cần triển khai sau review, một phiên tích hợp các thay đổi dùng chung; mỗi phiếu là một sprint riêng theo kế hoạch. Không chỉnh dữ liệu test để ép kết quả.

| Gói | Việc Claude có thể chuẩn bị độc lập | Điều kiện trước khi sửa dữ liệu/mã | Kết quả cần bàn giao |
|---|---|---|---|
| Ván ép / J05b | Đối chiếu cấu kiện-hệ và lập danh sách mã/đơn vị còn thiếu; xác định hao phí so với mua/thuê | Codex duyệt phiếu, D02 có đáp án liên quan, hệ ván/khung/chống và danh mục đủ căn cứ; thay DB nếu có phải được duyệt | Ánh xạ từng thành phần, ca dầm/cột và ca không khớp/thiếu quy đổi; không báo đủ khi chỉ có ván |
| Trát / J05c | Đề xuất giữ nguồn loại nền từ tường tới công tác trát, xác định hành vi nền chưa rõ | Codex duyệt phiếu và hợp đồng đầu vào, D02 xác nhận nền/dày/mặt trát; không tự suy từ hatch | Công thức áp đúng một lần; ca 15/20 mm, đặc/rỗng/không rõ, hai mặt và trừ âm |
| Phụ gia / J05d | Lập danh sách thông tin cần thu về cấp phối/sản phẩm; đối chiếu kg với lít | Codex duyệt phiếu, D02 và cấp phối/liều/sản phẩm có nguồn; không chọn thay thiết kế | Ca khoảng tham khảo tách lượng mua, thiếu liều/kg-L, thương phẩm và chống nhân lặp 1,025 |

Khi giao chính thức: đọc lại file hiện hành vì D02/phiên khác đang sửa repo; không ghi đè thay đổi của phiên khác. Dev tự kiểm và ghi “chờ review”, Codex quyết định nghiệm thu. Các kiểm tra mã/dữ liệu của J05 phải chạy khi triển khai; tài liệu này không thay thế bằng chứng đó.

## 7. Giới hạn và trạng thái bàn giao

- Chỉ tạo tài liệu này; không sửa M01/D02, CLAUDE.md, SPRINTS.md, NHAT_KY.md, CSV/catalog/DB hoặc test.
- Chưa chạy pytest/check_data: không thay mã hoặc dữ liệu vận hành; không dùng kết quả tài liệu để tuyên bố chức năng đạt.
- Chưa có bản vẽ/cấp phối/TDS và xác nhận người kiểm cho bốn phiếu; chưa khóa mẫu số và chưa áp hệ số vào công trình.
- Chưa đối chiếu toàn văn N7-S7 hoặc lịch sử thay phụ lục; bảng AF.83 không cung cấp đầy đủ quy cách mua/thuê; cán 50 mm chưa có hệ số được chứng minh.
- **Bàn giao: chờ Codex review nguồn, phạm vi áp dụng và điều kiện mở từng J05.**
