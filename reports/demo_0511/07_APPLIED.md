# Gói07 đã nhập — xi măng lịch sử ACTUAL

Ngày03/11/2026. Bản review, PDF, stagingJSON và các nguồn băm trong manifest giữ nguyên sau khi khóa; trạng thái DB mới được ghi riêng ở đây, không sửa `07_cement_review.md` hoặc `cement_historical_proposed.json`.

**Đã thêm 1 nhà cung cấp và 4 bản ghi giá lịch sử vào database optimat. Chạy lại không thêm trùng.** Đây không phải báo giá mua còn hiệu lực ngày05/11.

| Lượt | Giờ Việt Nam / UTC | Kết quả |
|---|---|---|
| Apply thành công đầu |03/11/2026 17:27:14 /10:27:14UTC | COMMITTED; suppliers2866→2867; price_records59→63 |
| Apply kiểm chống trùng |03/11/2026 17:27:45 /10:27:45UTC | COMMITTED no-op;0NCC/0giá mới; counts giữ2867/63 |

Biên nhận đầy đủ:

- `07_cement_historical_actual_first_apply_receipt.json`: supplier `CBG-991233626E`, priceIDs **1426,1427,1428,1429**, cùng ngày/quantity/source thực sự RETURNING.
- `07_cement_historical_actual_apply_receipt.json`: lần chạy lại0/0; không ghi đè biên nhận đầu.
- `07_cement_historical_actual_preflight.json`: kiểm trước nhập.
- SQL chuẩn: `sql/07_cement_historical_actual.sql`; SHA256 `ce9b7eea9f287dee2239c78b204c64f70fc74e56106569e07901c0b2a7224e09`.

Lưu ý băm: giá trị `ce9b...` trong manifest/receipt là băm nội dungUTF-8 sau chuẩn hóa xuốngdòngLF, đúng cách runnerđọc. File trênWindows lưuCRLF nên rawbyteSHA256 là `110d7d5e554a410a14f781c3f42dcfa90af8de1df7d1516ca6e3480fd590afd8`. Bảnreports vàcanonical byte-identical, khôngBOM; khácrawhashvớimanifest ởđây làquyước newline, khôngphảithaySQL. Đãđọckiểm toànbộsourcehashes trongmanifest, khôngcónguồnthayđổi.

Nguồn chính thức [CEMIA — kê khai xi măng tháng3/2026](https://cemia.gov.vn/UploadedFiles/UploadedFiles/tiep%20nhan/20260403035144_Ke%20khai%20gia%20Xi%20mang%20thang%203.2026.pdf), trang13/14. Giữ ngày17/03/2026, HàNội, baoKPK50kg, giáđồng/tấn trực tiếp, **đãVAT**, vận chuyểnUNKNOWN; bốn biến thể PCB30/PCB40 cao cấp/đa dụng trongsource, không quy đổi bao hoặc tính ngược thuế.

Lượt thử ban đầu gặp psycopg diễn giải ký tự `%20` trong URL như placeholder và **đã rollback**, không phải lần nhập thành công. Phiên chính sửa runner dùng `no_parameters=True` cho câu SQLliteral, sau đó mới có hai receipt thành công trên. Không dùng lỗi lần thử để kết luận giá trị dữ liệu sai; không thực thi dump nguồn.

Gói06 cũng đã apply lại no-op0/0 theo `db_apply_receipt.json` lúc17:16:28 ViệtNam; đó là59giá cũ ngày20/06/2026, không phải59giá mới. Gói07 làm tổng lịch sử thành63dòng.

Không cóIDthêm ở các lượt no-op. Nếu cần rollback gói07 phải căn cứ đúng4priceIDs+supplier thực thêm của **firstreceipt**, kiểm phụ thuộc phát sinh sau đó; không xóa mọi dòng ứng viên hoặc nhầm giữreceiptno-oplàm biên nhận đầu. Lượt này chỉ lập báo cáo, không chạy rollback/DB.

Giới hạn còn nguyên: chưa có báo giá mua, xe hoặc nhân công ACTUAL trong các bảng tương ứng;13offers/4xe/1nhân công SAMPLE tồn tại từtrước không được dùng lấp thiếu theo lựa chọnuserACTUAL-only. Lịch sử hai mốc tháng3/tháng6 chưa phải chuỗi6tháng giá thật hoặc nguồn cung hiện hành.

Phiên chính báo74testtrọng tâm đạt, gồm13caAPIview/structural; source ổn định đang chờ toànsuite. Trình duyệt chưa khép doHMR/xửlýCADdài; không gọi toànbộdemođãsẵn.
