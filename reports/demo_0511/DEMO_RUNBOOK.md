# Kịch bản demo đợt 1 — 05/11/2026

Kịch bản theo kế hoạch ngày 03/11/2026. Bản nghiệm thu cần một hồ sơ kiến trúc và kết cấu có nguồn, bản khối lượng đã kiểm, lựa chọn vật liệu đã lưu và kết quả vật tư tương ứng. Luồng này đang chờ tổng duyệt. [Phiếu điều chỉnh](../../docs/DIEU_CHINH_LUONG_KIEM_KHOI_LUONG_20261103.md) · [Bảng việc ưu tiên](SPRINT_BOARD.md)

## 1. Demo Dự án của tôi trên dự án 23

Dùng [trang Dự án của tôi](http://127.0.0.1:3001/du-an-cua-toi?ho-so=1). Ngày 04/11, bản mới trên cổng 3001 đã trả HTTP 200 và Chrome chuyển đến màn đăng nhập. Cổng 3000 còn phục vụ bản cũ và trả 404. Chủ đồ án đăng nhập trực tiếp bằng tài khoản đã tạo dự án. Phiên 01 kiểm tra trước khi báo chọn tệp.

1. Mở **QA hồ sơ bản gốc 03-11**, kiểm mã 23 và mục **Hồ sơ gốc**, chụp ảnh trước tải.
2. Chủ đồ án bấm **Tải bản vẽ gốc** và tự chọn `C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai\data\sample\sample_floor.dxf`. Chụp khi tên tệp và phiên bản xuất hiện.
3. Nhập, lưu thông tin ngay trên trang. Rời trang rồi mở lại đúng dự án, đối chiếu giá trị đã lưu.
4. Mở bản gốc, ghi nhận tên tệp và phiên bản đã chọn. Kiểm việc xem trước chưa khởi chạy phân tích.
5. Bấm **Bắt đầu phân tích**. Đối chiếu phiên bản nhận ở bước bóc tách với bước 4 và kiểm không có lượt tải tệp thứ hai. Gửi ảnh theo thứ tự về chat 00.

## 2. Giới hạn bằng chứng

Tệp mẫu chỉ dùng để kiểm luồng và phiên bản. Không tải bộ Tân Bình. Các mục 3–7 là kế hoạch tổng duyệt nghiệp vụ riêng, cần hồ sơ KT/KC thực đã được phép sử dụng. Số kiểm thử backend và kết quả trên tệp mẫu không thay cho bằng chứng nghiệm thu các sprint.

## 3. Chuẩn bị trước giờ trình diễn

1. Dùng một trình duyệt/profile cố định; kiểm không còn mặt bằng xác nhận của công trình khác trong `/vat-lieu`. Chỉ xóa kết quả tạm qua nút UI sau khi đã giữ bản cần thiết; không xóa DB.
2. Ghi mã dự án thực tế tương ứng với hồ sơ đã được phép dùng cho tổng duyệt.
3. Chạy trọn một lượt từ file gốc; ghi số tầng, diện tích tường, số dòng công tác/vật tư, số dòng thiếu và nguồn giá. Giữ ảnh từng bước; không dùng số đã nhớ từ mã cũ như kết quả hiện tại.
4. Lưu CSV/JSON từ `/do-boc` bằng chức năng hiện có. BOQ Excel chỉ đưa vào kịch bản khi bản xuất cùng đầu vào đã được kiểm khớp.
5. Quay video5phút cùng bản mã, cấu hình và dữ liệu đã tổng duyệt; mở thử video. Trước khi có video, workbook cũ chỉ là dự phòng bằng chứng baseline.
6. Kiểm quay lại và tải lại cả 5 trang. Thử hai dự án có file trùng tên, sửa vật liệu cùng bề dày, sửa cấu tạo làm đổi bề dày và giả lập lỗi lưu giữa các bước trên dữ liệu kiểm thử. Chỉ xác nhận nghiệm thu khi giá, tối ưu và BOQ đọc đúng phiên còn hiệu lực.

## 4. Kịch bản nói và thao tác trong 5 phút

| Thời điểm | Trang / thao tác | Lời trình bày và điểm cần chứng minh |
|---|---|---|
| 00:00–00:25 | Mở dự án và hồ sơ đã chuẩn bị | Nêu nguồn kiến trúc, kết cấu, phiên bản bản vẽ và mục tiêu so sánh phương án tường. |
| 00:25–01:15 | `/do-boc` · kiểm các hình, tường, lỗ mở | Chỉ ra một hình được tính và một hình tham khảo. Chốt phạm vi tầng. |
| 01:15–02:20 | `/phan-tho` · kiểm công tác và khối lượng | Mở một cấu kiện, đối chiếu kích thước, đơn vị, nguồn, khoản trừ và lượng cuối. Mở một dòng còn thiếu, cho thấy phần đã biết, lưu rõ phạm vi đã kiểm. |
| 02:20–03:00 | Mở thẳng `/toi-uu` và xem phương án nháp | Dùng hồ sơ chưa chọn tay từng vật liệu. Chỉ một mã có căn cứ được điền sẵn, một dòng chưa đủ dữ liệu và một nhóm phi tường đang phát sinh. |
| 03:00–03:35 | Hỏi AI ngay trong phương án | Hỏi nhóm nào chỉ có một mã và có thể đặt mua chưa. Đối chiếu mã, lý do thiếu giá và quy cách với dữ kiện. Ghi rõ trạng thái phản hồi thật hoặc lỗi xác thực nếu có. |
| 03:35–04:30 | Xem phần thiếu và xác nhận cả phương án | Nếu cần, mở chi tiết giá hoặc điều chỉnh vật liệu. Lưu phạm vi đã chọn, chỉ công tác phải kiểm lại nếu đổi bề dày. Bộ so sánh tường chỉ dùng khi có đủ dữ liệu tường. |
| 04:30–04:45 | Đối chiếu BOQ | So một dòng có cùng dự án, phiên khối lượng, vật liệu, đơn vị và quy tắc làm tròn với giao diện. |
| 04:45–05:00 | Mở lại dự án và nêu giới hạn | Chỉ bằng chứng đã tổng duyệt. Nêu công tác còn thiếu hoặc cần kiểm trước mốc 22/11. |

Nếu mở file/đọc hình học vượt thời lượng, chuẩn bị bản đã mở sẵn trong lượt tổng duyệt và quay thao tác tải đầu vào ở video. Nói rõ bước tải đã chuẩn bị, không giả là mới xử lý tức thời.

## 5. Nhánh khi chưa đủ giá hoặc không có nghiệm

- Không có giá: giữ dòng thiếu, hiển thị tỷ lệ có giá thực đo. Không đổi dữ liệu SAMPLE thành ACTUAL, không coi giá thiếu bằng0 hoặc gọi tổng một phần là tổng đủ.
- DB có13giá mua/4xe/1nhân công SAMPLE từ trước: **không dùng để lấp thiếu theo lựa chọn ACTUAL-only**. Không xóa/đổi nhãn chúng trong demo; cần kiểm bộ tối ưu có thực sự lọc nguồn trước chạy.
- Có59giá công bố ngày20/06/2026 theo biên nhận nhập cũ: gọi là BULLETIN tham khảo theo ngày/điều kiện nguồn; không suy tháng01 từ số văn bản02.01, không khẳng định còn hiệu lực đến05/11 hoặc gồm giao hàng. PDF gốc chưa được kiểm lại trong lượt này.
- Đã thêm4giá xi măngCEMIA ngày17/03/2026:XM01/XM02 cao cấp/đa dụng,đồng/tấn,đãVAT,vận chuyểnUNKNOWN; PDFđãkiểm ảnh. Tổng63giá lịch sửkhông phải63báogiámuahiệnhành hoặc chuỗi6tháng. Cóthể chỉsource/page/biếnthể ở `07_APPLIED.md`, không gọi làgiágiao tận côngtrình.
- Tối ưu không có nghiệm: kiểm dữ liệu và ràng buộc; chỉ nới ràng buộc khi giải thích công khai. Nếu thiếu xe/báo giá/leadtime ACTUAL thì trình bày nguyên nhân; không dùng ảnh/video SAMPLE như lần chạy ACTUAL hoặc dựng nghiệm.
- Ghi nguồn phản hồi thực tế. Khi dùng mẫu hoặc bộ tách quy tắc, giới thiệu đúng chế độ đó. Lượt nghiệm thu OpenAI thật cần dữ liệu được phép và biên nhận riêng. [Bàn giao trợ lý cho toàn bộ phần thô](AI_CHON_VAT_LIEU_PHAN_THO.md)
- XGBoost: artifacts hiện tại ghi SYNTHETIC. Có thể giới thiệu module đã có; chưa dùng chỉ số của nó làm chất lượng giá thật hoặc lấp KPI báo giá.

## 6. Checklist nghiệm thu bản demo

Đánh dấu sau khi thực hiện và kèm đường dẫn bằng chứng. Các mốc DB/static đã có không tự đóng các bước tích hợp.

| Điều kiện | Kết quả / bằng chứng |
|---|---|
| Health xác nhận đúng backend/danh mục và đăng nhập được | Đã đọc metadata DB cấu hình. Chrome trên cổng 3001 đang chờ người dùng đăng nhập. |
| Mở đúng hồ sơ KT/KC thực và kiểm số tầng/ánh xạ | Chờ hồ sơ thực được phép và kết quả QA riêng. |
| Không lẫn kết quả công trình khác; ID dự án đúng nếu lưu DB | CHƯA KIỂM UI/DB |
| Kiểm và lưu ở `/phan-tho` trước khi chọn ở `/dieu-chinh` | Chờ kiểm UI, gồm dòng đủ dữ liệu và xác nhận phạm vi còn thiếu. |
| Trợ lý tư vấn toàn bộ phần thô | Chờ kiểm ca nhiều, một, không có phương án hoặc thiếu giá; có ca phi tường, nguồn dữ kiện và bước người dùng xác nhận. Tối ưu tường là công cụ riêng. |
| Cùng dự án, Back/Forward giữ đúng xác nhận và điều chỉnh | CHƯA KIỂM luồng mới; không coi harness của bản cũ là đạt |
| Lỗi lưu, phản hồi về muộn, hai dự án trùng tên file | Chờ chứng minh kết quả cũ mất hiệu lực và các trang sau không nhận trạng thái lưu dở. |
| Tính phần thô không lỗi; công tác thiếu không biến0 | CHƯA KIỂM UI |
| Khối lượng đối chiếu cùng phạm vi; chênh lớn có giải thích | Có baseline phát triển; CHƯA XÁC NHẬN lần chạy demo |
| API, web và BOQ khớp trên đúng phiên | 110 ca backend và 4 bộ kiểm giao diện thuộc luồng trước. Cần đối chiếu lại sau thay đổi kích thước và lưu bản kiểm. |
| Giá có loại/nguồn/ngày; phần thiếu và tổng một phần rõ | DB63ACTUAL/BULLETIN saugói07;1NCC/4giá mới,repeat0/0. Chưa báogiámua/xe/nhân côngACTUAL; UIcò nkiểm |
| Tối ưu có nghiệm hợp lệ hoặc thông báo thiếu/ràng buộc trung thực | CHƯA KIỂM lần chạy demo |
| Không hứa tổng cả công trình khi chỉ tính tối ưu tường | YÊU CẦU kịch bản |
| Mở lại đúng bản giao diện và chạy lại thành công | CHƯA KIỂM |
| Video/ảnh/Excel dự phòng mở được, đúng phiên bản | Workbook baseline hiện có; video CHƯA CÓ BẰNG CHỨNG |

## 7. Nguồn bằng chứng để người trình diễn tra nhanh

- `reports/demo_0511/data_audit.md`: số đếm CSV, dữ liệu thiếu và phạm vi mô hình.
- `data/ground_truth/du_toan/cases.csv`, `README.md`: split, nguồn và thông số46; banve1 vẫn là test.
- `reports/c01_review_fix/BAN_GIAO.md`: baseline64 dòng gốc,47 hạng mục,25 nhóm/17 nhóm so được;24 vật tư/0 đủ căn cứ so. Đây là mốc phát triển, không KPI.
- `docs/review/C01_NGHIEM_THU_KY_THUAT.md`: mốc kỹ thuật C01, không nâng xác nhận nghiệp vụ/DB.
- `models/material_price_metrics.json`: chỉ số hiện có trên SYNTHETIC.
- [Hợp đồng kích thước và phạm vi](../../docs/KIEM_TRA_CONG_TAC_KHOI_LUONG.md) và [phiếu điều chỉnh](../../docs/DIEU_CHINH_LUONG_KIEM_KHOI_LUONG_20261103.md) ghi điều kiện nghiệm thu luồng hiện tại.

DBsnapshotcũ ởdb_readiness.json;06no-opreceiptvà07first/repeatreceiptsghi rõnguồn vàsốmới. SQLchuẩn:sql/06_demo_actual.sql,sql/07_cement_historical_actual.sql. Xem07_APPLIED.md cho17:27:14/17:27:45giờViệtNam,IDs1426–1429 vàsupplierCBG-991233626E. Lượt07thửđầu vìURL%20đãrollback;runnerno_parameters=True sửa xongmớicóreceiptCOMMIT. Chưa khépUI/hiệu lực thịtrường/khối lượngđộclập; khôngchethiếu bằngSAMPLE.
