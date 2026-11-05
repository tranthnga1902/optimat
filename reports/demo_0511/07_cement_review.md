# Review nguồn gói07 — xi măng lịch sử ACTUAL

Ngày03/11/2026. Agent dữ liệu tải PDF chính thức sau khi auto-review cho phép, render trang13/14 bằng Poppler và xem PNG. Phiên chính đã xem độc lập cả hai ảnh, xác nhận và cho phép chuẩn bị gói nhập trong phạm vi user yêu cầu ACTUAL có nguồn; không tuyên bố báo giá mua hiện hành.

Đã xác nhận trên ảnh: ngày văn bản17/03/2026;1228/XMTĐ-XNTT;Hà Nội;Công ty Xi măng Vicem Tam Điệp;baoKPK50kg;đơn vịTấn. STT1/2 trang13:PCB30cao cấp1.150.000,PCB40cao cấp1.200.000;STT3/4 trang14:PCB30đa dụng1.070.000,PCB40đa dụng1.130.000. Cả bốn số thuộc cột **Giá(đã cóVAT)**, cột giá trướcVAT trống. Ghi chú vận chuyển trống nên transport_includedUNKNOWN; không suy thuế suất hoặc giá trướcVAT.

Kiểm currency bổ sung từ PDF gốc bằng pdfplumber: trang1 có dòng **Đơn vị tính: VNĐ**. Đây là currency của bảng tổng hợp, không suy từ giá hoặc tên domain. Đã kiểm catalogXM01/XM02:ACTUAL,unit=tấn; nguồn báo giá/tấn nên không quy đổi50kg→tấn. Tên biến thể phải giữ trongsource vì mã danh mục là nhóm chung.

Nguồn: https://cemia.gov.vn/UploadedFiles/UploadedFiles/tiep%20nhan/20260403035144_Ke%20khai%20gia%20Xi%20mang%20thang%203.2026.pdf

PDF: reports/demo_0511/cemia_ximang_thang3_2026.pdf;PNG:cemia_price_page-13.png/-14.png. Stagingcement_historical_proposed.json giữPROPOSED_NOT_APPLIED và không sửa sau khi khóa manifest; trạng thái áp dụngDB phải đọcreceipt riêng.

Gói:1supplier ứng viên,4price_recordsACTUAL/BULLETIN. Không supplier_materialsDEALER,không xe/nhân công,coords/leadNULL,verifiedFALSE. Chưa có thời hạnhiệu lực,đơn hàng tối thiểu,phígiao hoặcleadtime; không lấp thiếu. Dữ liệu lịch sử03/2026 không chứng minh còn hiệu lực05/11.

Lệnh tái sinh, chỉ sau khi kết thúc khung apply và được cấp lượt:

```powershell
Set-Location -LiteralPath 'C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai'
$env:PYTHONIOENCODING='utf-8'
$env:OPTIMAT_NO_DOTENV='1'
.venv/Scripts/python.exe reports/demo_0511/build_cement_historical_sql.py
```

Generator tái dùng render_sql hiện có; không import engine/DB. ScriptSQL BEGIN/INSERTONCONFLICTDONOTHINGRETURNING/COMMIT; xung đột giữ nguyênDB. Phiên chính preflight/hash/review rồi mớiapply, lưureceipt riêng theo gói. Rollback chỉ theoIDthực sự thêm của receipt, không xóa mọi khóa ứng viên.
