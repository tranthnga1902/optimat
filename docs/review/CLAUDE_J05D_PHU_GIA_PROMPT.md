# Prompt Claude - J05d phụ gia M350/M400

Bạn là Claude dev của OptiMat AI. Codex là BA/reviewer. Chỉ chuẩn bị hợp đồng và cách xử lý phụ gia của cấp phối M350/M400 đang dùng; không chọn sản phẩm/liều thay thiết kế, không mở J01/J02 hoặc sửa bê tông thương phẩm ngoài ca không cộng phụ gia trùng.
Gốc repo: `C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai`.

## Đọc trước

Đọc CLAUDE.md, AGENTS.md áp dụng, kế hoạch J04/J05/quy tắc nghiệm thu, M01 5A/5B, `docs/research/J04_PHIEU_TRA_NGUON.md` mục 1/5/6/7, `docs/review/J04_CODEX_REVIEW.md`, trạng thái và giới hạn D02. Kiểm workspace và giữ thay đổi của phiên khác.
Khảo sát `rough/materials.py::_Bill.concrete/norm_line`, `norms.py::Norm.value`, models/status/BOQ và caller, CSV BE_TONG_TRON, PG01/PG02 trong danh mục gốc và test vật liệu. Chưa sửa các file khảo sát trong đợt này.

## Làm ngay - đợt chuẩn bị song song

Chỉ tạo/cập nhật `docs/research/J05D_PHU_GIA_THIET_KE.md`; không sửa mã, dữ liệu vận hành/test thực, SQL/DB, J04/D02, CLAUDE.md, SPRINTS.md hoặc NHAT_KY.md. Quyền ghi giới hạn này để tránh xung đột với nhánh trát; ghi kết quả trong tài liệu riêng. Chưa áp bản vá kể cả khi tự tìm được sản phẩm hợp lý trên web.

1. Dùng skill PDF, kiểm lại nguồn chính thức [N7 PDF 4](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf#page=4) mục 4-5 và [PDF 15](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf#page=15) dòng 11.12325/26. Tách N7 khỏi bản sao S7, không ghi đã đối chiếu toàn văn. Ghi điều kiện xi măng/cốt liệu/độ sụt và cơ sở đơn vị; không lấy “M350” làm đủ thông tin cho mọi cấp phối.
2. Truy vết hiện trạng: ba vật liệu chính có số, chưa có dòng phụ gia → đầu ra có thể bỏ mất phần thiếu. Đề xuất điểm nhỏ nhất để giữ dòng thiếu có nguồn/lý do trong danh sách vật tư và BOQ mà vẫn giữ số xi măng/cát/đá đã biết. Không tự sửa cơ chế known_part toàn hệ thống của Q02.
3. Viết hợp đồng đầu vào: cấp phối/phiên bản/cách cấp bê tông; sản phẩm và loại phụ gia; liều cùng đơn vị/cơ sở khối lượng; nguồn thiết kế/thí nghiệm và xác nhận; khối lượng riêng kg/L khi cần; quy cách mua. Chỉ yêu cầu thông tin có tác dụng tính/kiểm, không thêm framework quản lý sản phẩm.
4. Mô tả ưu tiên cấp phối được xác nhận so với bảng tham khảo; thiếu sản phẩm/liều giữ thiếu, không tự chọn khoảng hay trung điểm. Có thể chỉ ra TDS chính thức để thu dữ liệu, nhưng đó là ứng viên chờ thiết kế chọn, không phải lựa chọn đã duyệt.
5. Đề xuất diff ở dạng văn bản trong tài liệu: file/đoạn, trường có sẵn/mới, đường CSV và PostgreSQL, cách chuyển đơn vị, provenance và trạng thái. Nếu cần DB chỉ trình lược đồ/migration/rollback; chưa thực thi. Không sửa tên/đơn vị PG01 chung để biến thành một sản phẩm cụ thể.
6. Lập bảng dữ liệu cần từ người dùng/người kiểm và ca nghiệm thu SYNTHETIC. Không chờ D02 để hoàn tất khảo sát và thiết kế.

## Các điều cấm để tránh ra số giả

- `Norm.value` hiện lấy trung điểm của min/max. Không đưa khoảng liều vào loader hiện tại rồi coi số giữa khoảng là lượng mua. Không đổi hành vi tất cả định mức khoảng chỉ để giải quyết phụ gia.
- Có norm_code không đồng nghĩa đủ sản phẩm/liều. Không dùng 1 kg = 1 lít; kg/L phải đúng sản phẩm. PG02 kết nối không thay PG01 dẻo hóa.
- Không chọn phụ gia chống thấm/siêu dẻo thay dẻo hóa của bảng; không giảm thêm nước trên cấp phối đang có theo phần trăm chung.
- Không nhân 1,025 hai lần. Số xi măng CSV đã quy đổi m³ kết cấu; căn cứ áp 1,025 theo từng công tác còn phải review, không hardcode thành hệ số cho mọi cấu kiện.
- Thương phẩm không bóc thêm phụ gia trộn tại chỗ khi không có yêu cầu riêng được xác nhận. Không đổi cả cách chọn supply theo cấu kiện (J01).
- Nước chưa có dòng trong CSV phải nêu giới hạn và đối chiếu D02, không tự coi đã đủ mọi thành phần.

## Ca nghiệm thu phải đề xuất

Với giả thiết nguồn/cấp phối đang dùng và 1,025 chỉ một lần: M350 xi măng 385 kg/m³ vữa; khoảng tham khảo phụ gia = 1,925-3,080 kg/m³ vữa hoặc 1,973125-3,157000 kg/m³ kết cấu. M400: 426 kg; tương ứng 2,130-3,408 và 2,183250-3,493200 kg. Đây là kiểm số học tham khảo, không tạo lượng mua mặc định.

Thiết kế test sau này phải có: chưa chọn liều/sản phẩm → quantity mua trống + lý do; liều đã xác nhận trên dữ liệu SYNTHETIC → tính đúng theo khối lượng xi măng/cơ sở đơn vị; thiếu kg/L không ra lít; sai loại phụ gia không dùng khoảng dẻo hóa; thương phẩm không cộng trùng; trừ âm theo phần góp; giữ dòng thiếu khi ba thành phần khác đã có số; nguồn nhập tay không nâng A. Nếu dùng số mật độ/liều giả cho test phải ghi rõ SYNTHETIC, không nạp danh mục ACTUAL hoặc đáp án hồ sơ thật.

## Phải chờ

- **Chờ dữ liệu thiết kế/sản phẩm:** cấp phối được xác nhận, loại/sản phẩm, liều, TDS phù hợp, kg/L khi cần. Không yêu cầu người dùng chọn một số giữa khoảng chỉ để BOQ hết trống.
- **Chờ Codex duyệt hợp đồng/lịch tích hợp:** trước sửa mô hình dữ liệu, loader/materials, XLSX/CSV/SQL/API/UI; DB cần chủ đồ án duyệt. Đợt này nhánh trát sở hữu mã dùng chung.
- **Chờ D02 có dòng đáp án liên quan được người kiểm xác nhận:** trước áp vào hồ sơ, so số thực hoặc nghiệm thu J05d/J04. D02 hiện có 0 dòng đã kiểm, không dùng bộ nháp làm đáp án chuẩn.

## Bàn giao và kiểm tra đợt triển khai sau

Đợt này bàn giao tài liệu có bảng đủ/thiếu, hợp đồng, bản vá đề xuất và ca số học; ghi “chờ Codex review, chưa triển khai”. Không ép chạy pytest cho tài liệu.
Khi được giao triển khai: tái dùng luồng tính hiện có, quy tắc có nguồn ở dữ liệu; chạy test trọng tâm rồi toàn bộ pytest, check_data với DB kiểm thử đúng phiên bản nếu sửa data. Không nạp DB thật, không chạy đồng thời test trên cùng DB, không báo hoàn tất UI nếu chỉ API. Báo diff, lệnh/kết quả, dữ liệu và giới hạn; chỉ Codex nghiệm thu.
