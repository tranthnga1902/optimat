# Prompt Claude - J05b ván ép AF.83

Bạn là Claude dev của OptiMat AI. Codex là BA/reviewer. Làm đúng gói ván ép này; không kiêm trát, phụ gia, cán 50 mm hoặc D02.
Gốc repo: `C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai`.

## Đọc trước

Đọc `CLAUDE.md`, AGENTS.md áp dụng, kế hoạch J04/J05 và quy tắc nghiệm thu, M01 mục 5A/5B, `docs/research/J04_PHIEU_TRA_NGUON.md` mục 1/3/6/7, `docs/review/J04_CODEX_REVIEW.md`, `docs/D02_DAC_TA_DAP_AN.md` phần trạng thái/giới hạn. Kiểm trạng thái workspace; không hoàn nguyên thay đổi của phiên khác.
Khảo sát `rough/materials.py`, `norms.py`, `models.py`, `boq.py`, các nơi tạo COP_PHA/formwork_of, catalog repository, `data/rules/dinh_muc_phan_tho.csv`, `data/catalog/materials_master.xlsx`, CSV danh mục và test cốp pha hiện có. Đọc có mục tiêu, không sửa các file này ở đợt đầu.

## Quyền làm ngay - đợt chuẩn bị song song

Chỉ tạo/cập nhật `docs/research/J05B_VAN_EP_THIET_KE.md`. Không sửa mã, CSV/catalog/SQL/DB, D02, J04, CLAUDE.md, SPRINTS.md hoặc NHAT_KY.md. Quyền ghi giới hạn này ưu tiên quy ước cập nhật nhật ký của phiên thông thường để tránh xung đột; ghi bàn giao ngay trong tài liệu riêng.
Nhánh trát là bên duy nhất được sửa mã dùng chung trong đợt đầu sau khi hợp đồng trường đã được chốt. Bạn không áp bản vá trực tiếp hoặc tự chuyển sang triển khai khi nhánh khác đang chạy.

Làm ngay đến hết các việc sau, không dừng chỉ vì D02 chưa có người kiểm:

1. Kiểm nguồn chính thức [N2 PDF 455-457](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=455), dùng skill PDF; ghi mã cột/đơn vị/điều kiện và ca số học. Không lấy việc có bảng làm bằng chứng đủ lượng mua.
2. Lập ma trận cấu kiện hệ thống thực sự tạo được → mã AF.83 → ván/khung nhôm/chống thép/phần khác → mã danh mục hoặc “chưa có”. Phân biệt SÀN/MÁI, DẦM/GIẰNG, CỘT vuông/chữ nhật, TƯỜNG; chưa có đường tạo công tác cho vách thì giữ chưa hỗ trợ, không mở X01. MÓNG/THANG/LANH_TÔ/SÊ_NÔ không tự ánh xạ sang dầm/sàn.
3. Phân định hao phí định mức và số tấm/bộ phải mua ban đầu hoặc thuê; đề xuất chính xác nhãn đầu ra và phần dữ liệu cần người dùng xác nhận. Không thiết kế biện pháp thi công.
4. Nêu đề xuất nhỏ nhất để chọn đúng hệ và cấu kiện, giữ nguồn chiều cao/quy cách; liệt kê từng file/đoạn dự kiến sửa, trường có sẵn/tận dụng được, trường mới thực sự cần. Nếu ảnh hưởng DB: chỉ đề xuất lược đồ/migration/rollback, không thực hiện. Danh mục gốc là XLSX; không sửa CSV sinh ra làm nguồn riêng.
5. Chỉ rõ cách giữ phần thiếu ở API/BOQ khi biết ván nhưng chưa có khung/chống/quy đổi/phụ kiện; dòng biết có thể giữ số nhưng không gọi toàn hệ đủ. Không dùng 0 cho thiếu và không nhân 5% chi phí thành kg/bộ.
6. Viết ca nghiệm thu và bảng thông tin còn cần thu, phân biệt cái thiếu ở D02 với dữ liệu sản phẩm/hệ cốp pha. Có thể ghi diff đề xuất dưới code fence trong tài liệu; chưa áp vào repo.

## Căn cứ số học tối thiểu

Nguồn tính cho 100 m². Cột ≤28 m: AF.83111 sàn mái (21 m²; 12 kg; 36,15 kg), AF.83211 tường (13,13; 12,65; 38,13), AF.83311 dầm/giằng (21; 15,05; 39,61), AF.83411 cột (13,13; 13,73; 38,13). Ba thành phần theo thứ tự ván/khung/chống. Xác minh lại trước khi dùng. Chiều cao phải có nguồn; ≤5 tầng không tự chứng minh ≤28 m.

Ca SYNTHETIC dự kiến: 10 m² dầm → 2,1 m² ván, 1,505 kg khung, 3,961 kg chống; 10 m² cột → 1,313 m², 1,373 kg, 3,813 kg. Thêm sàn/tường, phần trừ âm, thiếu diện tích/chiều cao/hệ, hệ ván ép đi với gỗ, chưa có kg/bộ, cấu kiện không được ánh xạ. Không tự nhân số lần luân chuyển hoặc cộng hao hụt lần hai.

## Phải chờ

- **Chờ Codex chốt hợp đồng và lịch tích hợp:** trước khi sửa mô hình trường, loader/materials, XLSX/CSV/SQL hoặc API/UI. Không ghi đè CP04 “bộ” thành “kg” cho tiện và không tự tạo mã vật liệu thật có số bịa.
- **Chờ dữ liệu hệ:** quy cách ván, hệ khung/chống được chọn, nguồn kg/bộ nếu cần, phụ kiện và cơ sở mua/thuê. Không hứa hoàn tất toàn hệ khi chưa có.
- **Chờ D02 có dòng liên quan được người kiểm xác nhận:** trước áp cho hồ sơ thật/so đáp án hoặc công bố chỉ tiêu. Bộ 46 dự toán gỗ cũ không tự thành đáp án AF.83; không sửa đáp án để khớp TT38.

## Kiểm tra khi được giao triển khai tiếp

Tái dùng luồng `compute_rough → materials_for_works → BOQ`; không tạo engine riêng. Quy tắc/hệ số có nguồn vào dữ liệu, không hardcode trong nhánh Python. Kiểm cả CSV và đường PostgreSQL theo quy trình dự án, trên DB kiểm thử có cùng dữ liệu; không nạp DB thật. Chạy test trọng tâm rồi toàn bộ pytest một lần khi hoàn tất, không chạy đồng thời với phiên dùng chung DB. Thay UI cần thao tác thật có bằng chứng; test tổng hợp không thay D02.

## Bàn giao đợt này

Tài liệu thiết kế phải có bảng đủ/thiếu từng thành phần, hợp đồng đề xuất, file dự kiến sửa, ca số học, giới hạn và danh sách dữ liệu cần bổ sung. Báo “chuẩn bị kỹ thuật xong, chờ Codex review”, không đánh J05b hoặc J04 hoàn tất. Ghi đúng kiểm tra đã làm; tài liệu thuần túy không ép chạy pytest hoặc tạo test giả.
