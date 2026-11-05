# Bước kiểm tra công tác và khối lượng

## Bảng tiên lượng công tác theo hồ sơ G8 M1 — yêu cầu bổ sung

Chủ đồ án cung cấp `DU TOAN M1.xls` làm mẫu về mức chi tiết nghiệp vụ. Sheet `Tien luong` hàng 5–6 định nghĩa STT, tên công tác/diễn giải, đơn vị, số cấu kiện, dài, rộng, cao, hệ số phụ, khối lượng cấu kiện và tổng công tác. Sheet `Công trình` hàng 4–5 bổ sung ký hiệu bản vẽ, mã định mức, mã vữa, mã công tác, tổng dài và diện tích. Các mã chỉ ghi khi đã đối chiếu được nguồn. Đơn vị, quy cách, cấp/mác và phương pháp đã xác định phải đi cùng dòng công tác, phân biệt trường chưa biết với không áp dụng.

**Đầu ra bắt buộc trên giao diện và Excel** là hạng mục → công tác → nhóm vị trí/tầng → dòng diễn giải từng cấu kiện hoặc nhóm đồng nhất. Mỗi dòng phải giải được đóng góp vào tổng theo đúng đại lượng và đơn vị, kể cả khoản trừ. Ghi số lần lặp một lần, giữ độ chính xác tính trước làm tròn, ghi riêng quy đổi đơn vị và căn cứ của hệ số phụ. Cho phép công thức theo diện tích, chu vi, số lượng, khối lượng thép hoặc thể tích có nguồn khi tích dài × rộng × cao không thích hợp. Thiếu dữ liệu vẫn hiện dòng với lý do; đối chiếu cùng bản khối lượng đã kiểm. Lựa chọn sheet mới hoặc mở rộng sheet chi tiết do phiên 01 điều phối, giữ tương thích với BOQ cũ. Yêu cầu này thay tiêu chí Excel trước đây chỉ yêu cầu khớp tổng/nguồn.

**Ca đối chiếu từ mẫu:** `Tien luong` hàng 36–48, công tác bê tông lót móng M100 đá 4×6 PCB30. Dòng 38 đài DC-1 có 2 × 0,75 × 2,15 × 0,10 = 0,3225 m³; tổng các dòng cấu kiện là 3,2515 m³. Hàng 9–12 cho ví dụ 22 cọc × 14 m = 308 m dài; công tác ép ghi 3,08 đơn vị 100 m. Dùng để kiểm diễn giải, phân biệt công tác và quy đổi đơn vị. M1 là mẫu cấu trúc và ca đối chiếu, không chứng minh độ chính xác trên bản vẽ khác; phần hoàn thiện ngoài nhà, chi phí và quyết toán trong workbook nằm ngoài phạm vi hiện tại. Trợ lý chọn vật liệu phải bám đúng đặc tính thiết kế và lượng của các công tác đã kiểm.

## Yêu cầu 1 — Tỷ lệ trong màn hình Bóc tách bản vẽ

Khi hiển thị, giữ đúng tương quan hình học theo kích thước thiết kế, ghi rõ đơn vị và nguồn đo. Chỉ đối chiếu với kích thước hiện trường khi có số đo độc lập của cùng cấu kiện, cùng phương và cùng đơn vị. Nếu chỉ có bản vẽ, ghi “Theo thiết kế”. Phóng/thu trên màn hình không thay đổi kích thước tính toán. Yêu cầu này chưa chốt chức năng hiệu chỉnh phép đo bằng hai điểm.

Trên `/do-boc`, cạnh vùng bản vẽ, hiển thị tỷ lệ ghi trên bản vẽ (ví dụ **1:100**) khi có ghi chú nhận diện được và gắn được với đúng hình. Khi chưa xác định, hiển thị “Chưa xác định” và cho người dùng nhập tỷ lệ tham chiếu cho hình đang xem, có nhãn nguồn. Không lấy tỷ lệ in của khung tên áp cho mọi hình chi tiết.

Thêm thanh trượt có thể kéo bằng chuột hoặc điều khiển bằng bàn phím để đổi mức phóng của hình đang xem. Đồng bộ thanh trượt, lăn chuột, nút Vừa khung và thước khoảng cách. Kéo nền vẫn di chuyển hình. Ghi tỷ lệ in và mức phóng ở hai nhãn riêng. Nghiệm thu bằng hình có/thiếu tỷ lệ và hồ sơ có nhiều hình khác tỷ lệ; phóng hay di chuyển không đổi chiều dài tường, diện tích hoặc khối lượng đã xác nhận. Hiệu chỉnh kích thước đo theo hai điểm chuẩn là một nghiệp vụ riêng cần chủ đồ án chốt.

Ngày chốt kế hoạch: 03/11/2026. Trạng thái: chưa triển khai/nghiệm thu.

Cập nhật: đã có mã WIP, **chưa nghiệm thu**; chat kế hoạch dừng ghi source, chuyển các phiên triển khai.
Phân công, hợp đồng kích thước và giới hạn bằng chứng nằm trong
[phiếu điều chỉnh 03/11](DIEU_CHINH_LUONG_KIEM_KHOI_LUONG_20261103.md).

## Mục tiêu và vị trí

Luồng: Dự án → Bóc tách bản vẽ → Kiểm tra công tác và khối lượng → Chọn vật liệu → Vật tư và giá → Tối ưu / xuất bảng mua.
Dùng lại `/phan-tho`, đổi tên màn hình và menu thành “Kiểm tra công tác và khối lượng”; `/dieu-chinh` là bước chọn vật liệu sau đó.
Không buộc có phương án vật liệu hoặc cờ materials-ready mới được xem/tính khối lượng. Bản vẽ kiến trúc và kết cấu
được tiếp nhận từ bước bóc tách; màn hình kiểm vẫn cho bổ sung/đổi kết cấu khi thiếu.

Tách xác nhận hình học/công tác khỏi chọn vật liệu. Dùng compute_rough hiện có; chưa có vật liệu/định mức
không được làm mất số khối lượng hình học đã tính. Những thông số ảnh hưởng hình học như dày sàn, dày lớp trát,
cấu tạo thang vẫn nhập tại bước này; loại gạch, phương án tường, mác/cấp phối, nhà cung cấp và giá ở bước sau.
Đổi lựa chọn vật liệu làm đổi chiều dày/cấu tạo thì bắt buộc tính và kiểm lại khối lượng bị ảnh hưởng.

## Bố cục màn hình

1. Đầu trang: tên dự án, file kiến trúc/kết cấu, phiên bản đang kiểm; các ô đếm “Đủ dữ liệu”, “Cần bổ sung”,
   “Chưa kiểm tra”, “Chưa hỗ trợ”. Không cộng m², m³ và tấn thành một tổng.
2. Cột trái: cây Cả công trình → tầng → nhóm công tác/cấu kiện. Lọc theo tầng, công tác, nguồn, trạng thái và phần thiếu.
3. Vùng giữa: bảng công tác, mỗi dòng là một cấu kiện hoặc nhóm đồng nhất cùng tầng. Cột: Đã kiểm, Tầng,
   Công tác/cấu kiện, Số lượng, Dài, Rộng/dày, Cao, Diện tích, Khối lượng, ĐVT, Nguồn, Tình trạng.
   Tiêu đề kích thước ghi đơn vị; dữ liệu mm trong API được đổi sang m để hiển thị. Ô không áp dụng dùng “—”,
   ô thiếu ghi “Chưa có”; không thay bằng 0. Không suy ngược kích thước từ chuỗi công thức.
4. Chọn dòng mở khung chi tiết bên phải: vị trí bản vẽ nếu có, kích thước đầu vào, công thức, lượng gộp,
   các khoản trừ, lượng sau trừ, nguồn từng đầu vào và thông tin thiếu. Nguồn có vị trí thì nút “Xem trên bản vẽ”
   tô sáng cấu kiện; chưa có liên kết thì ghi rõ, không tạo vị trí giả.
5. Cuối trang: “Lưu kiểm tra”, “Tính lại”, “Tiếp: chọn vật liệu”. Bảng vật tư mua về và giá chuyển về bước sau.

## Nội dung từng loại công tác

| Nhóm | Đầu vào cần nhìn/kiểm | Đầu ra |
|---|---|---|
| Tường, trát | Dài, cao tầng và cao xây, dày, cửa, lanh tô/cột/dầm/giằng bị trừ; số mặt trát | m² tường, m³ xây; m² trát |
| Cột, dầm, giằng, lanh tô | Số lượng, dài/rộng/cao từng đoạn, phần giao và nguồn theo tầng | m³ bê tông, m² cốp pha liên quan |
| Sàn, mái | Diện tích gộp, lỗ trống đã đo/xác nhận, diện tích sau trừ, chiều dày | m², m³ bê tông |
| Thang | Từng thang/vế, bậc, rộng vế, chiếu nghỉ, dày bản, cấu tạo bậc | m³ bê tông; m² cốp pha |
| Móng, đất, lót | Loại/số móng, từng lớp kích thước, cao độ, cấu tạo lót và thông số hố đào | m³ móng/lót/đào/đắp |
| Thép | Cấu kiện, bảng thống kê, đường kính và khối lượng; hàm lượng giả định nếu dùng | kg/tấn lắp đặt; chưa gọi là lượng mua |
| Nền, chống thấm | Diện tích, chiều dày lớp, chu vi và cao cổ tường khi áp dụng | m² hoặc m³ theo công tác |

Tái dùng ma trận phạm vi M01. Có tên công tác trong danh mục không đồng nghĩa đã tự nhận được trên bản vẽ.
Hiện riêng dòng hạng mục mong đợi nhưng chưa hỗ trợ; không tạo khối lượng giả. Không suy diện tích lỗ thang từ rộng vế/chiếu nghỉ.

## Chỉnh sửa và xác nhận

- Cho sửa thông số đầu vào hoặc nhập khối lượng đo tay có đơn vị, nguồn và lý do. Giữ giá trị gốc, giá trị ghi đè;
  không sửa trực tiếp ô kết quả tính mà mất công thức. Nhập bổ sung giữ trạng thái C theo quy ước hiện tại.
- Trạng thái nguồn A/B/C/D độc lập với trạng thái kiểm “Chưa kiểm/Đã kiểm/Cần bổ sung/Chưa hỗ trợ”. Đã kiểm không đổi C/D thành A.
- Sửa đầu vào thì đánh dấu kết quả liên quan cần tính lại; chỉ xác nhận sau khi tính/lưu thành công. Thay file hoặc tầng
  làm mất hiệu lực xác nhận liên quan. Bỏ phản hồi API cũ đến muộn.
- Cho xác nhận một phần khi còn thiếu: hiện danh sách thiếu, người dùng xác nhận tiếp tục với phạm vi đó; không bỏ dòng D.
  Chặn chuyển khi chưa tính, còn thay đổi chưa lưu, lỗi tính/lưu, hoặc các dòng thuộc phạm vi tiếp tục chưa được kiểm.
- Bước vật liệu dùng đúng bản khối lượng đã xác nhận; thay đổi khối lượng làm bảng vật tư/giá/tối ưu cũ hết hiệu lực.

## Triển khai và nghiệm thu

**Phạm vi Excel của MVP.** Xuất BOQ từ cùng bản khối lượng đã kiểm. Đối chiếu công tác/cấu kiện/tầng, đơn vị, lượng, công thức/nguồn, trạng thái và lý do thiếu giữa API, giao diện và Excel, theo cùng quy tắc làm tròn. Ca nghiệm thu gồm một dòng đủ và một dòng chỉ tính được một phần. Kích thước chi tiết từng chiều và nguồn của từng chiều thuộc màn hình kiểm tra và API. Một sheet Excel riêng cho toàn bộ kích thước là đề xuất mở rộng sau MVP.

1. Sau khi khép lỗi tính N03/O, bỏ phụ thuộc chọn vật liệu khỏi tính khối lượng; bổ sung đầu vào kích thước có cấu trúc
   và nguồn cho những dòng còn chỉ có formula. Giữ trường API hiện có, bổ sung tương thích; không đổi DB trong đầu việc này.
2. Đổi thứ tự menu/Steps/guard: `/do-boc` → `/phan-tho` → `/dieu-chinh` → `/vat-lieu` → `/toi-uu`.
   Dùng lại bảng/kết quả và lưu phiên hiện có; snapshot cũ thiếu xác nhận mới phải được kiểm lại, không tự đánh đã kiểm.
3. Triển khai bảng và chi tiết; giữ nhiều tầng, nhiều thang; tổng một phần và lý do thiếu phải nhất quán API/UI/BOQ.
4. Kiểm thử: không chọn vật liệu vẫn xem được khối lượng; thiếu cao/dày/lỗ mở không thành 0; sửa và tính lại cập nhật
   đúng; ghi đè có nguồn; nhiều thang; phản hồi cũ; lưu lỗi/quota; xác nhận một phần; đổi file làm xác nhận hết hiệu lực;
   chọn vật liệu đổi hình học buộc kiểm lại. Không dùng dữ liệu tổng hợp để kết luận độ chính xác thực.
5. QA trình duyệt trên một hồ sơ build KT+KC: từ tải file tới chọn vật liệu, xem nguồn cấu kiện, sửa số, quay lại và tải lại trang;
   ảnh và kết quả đối chiếu API/BOQ là bằng chứng bắt buộc trước đánh dấu hoàn tất.
