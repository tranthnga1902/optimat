# Prompt Claude - J05c trát tường gạch rỗng

Bạn là Claude dev của OptiMat AI. Codex là BA/reviewer. Chỉ xử lý điều chỉnh lượng vữa trát do nền tường gạch rỗng; không mở trát cột/dầm/trần, ván ép, phụ gia hoặc cán 50 mm.
Gốc repo: `C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai`.

## Đọc trước

Đọc CLAUDE.md, AGENTS.md áp dụng, kế hoạch J05c/quy tắc nghiệm thu, M01 5A/5B, `docs/research/J04_PHIEU_TRA_NGUON.md` mục 1/4/6/7 và `docs/review/J04_CODEX_REVIEW.md`. Đọc trạng thái D02 trong `docs/D02_DAC_TA_DAP_AN.md`: có bộ nháp nhưng 0 dòng đã được người kiểm xác nhận, chưa khóa mẫu số.
Kiểm `rough/walls.py` nơi tạo TRAT, `models.py::WorkItem`, `materials.py` nhánh TRAT/CAN_NEN và mortar, `norms.py::norms_for`, `status.py`, các caller/serializer/BOQ; danh mục vật liệu/phương án tường và test hiện có. Không suy loại nền chỉ từ tên lớp hoặc chiều dày.

## Làm được ngay

Bạn là nhánh duy nhất được sửa mã dùng chung trong đợt đầu; hai nhánh ván ép/phụ gia chỉ chuẩn bị tài liệu riêng. Không tự nhận quyền ghi nếu thực tế có phiên khác đang sửa đúng đoạn: đọc diff, báo vùng xung đột và giữ bản vá đề xuất trong tài liệu của mình, không ghi đè.

1. Tạo `docs/research/J05C_TRAT_THIET_KE.md`: truy vết nền tường từ phương án vật liệu/đầu vào xác nhận tới từng mặt trát; phân biệt “đặc”, “rỗng đúng phạm vi AK.211/212”, “ngoài phạm vi bảng”, “chưa rõ”. Tận dụng `wall_system_id` có sẵn nếu thích hợp; chứng minh nó được giữ tới dòng TRAT. Một mã phương án không tự chứng minh nền đặc/rỗng nếu danh mục thiếu nguồn.
2. Nêu hợp đồng nhỏ nhất: dữ liệu nào có sẵn, dữ liệu nào mới cần thêm, ai cung cấp/xác nhận, ưu tiên khi người dùng sửa, cách giữ nguồn và trạng thái; phạm vi đường CSV/PostgreSQL, API/BOQ và UI nếu có ảnh hưởng. Gửi hợp đồng trường mới cho Codex review trước khi đổi trường/cách gộp nhóm, theo quy định kho. Chưa chốt thì hoàn thiện tài liệu và ca dự kiến, không tạo mô hình mới theo phỏng đoán.
3. Nếu không cần trường mới hoặc đã có hợp đồng được Codex chốt trong phiên: triển khai sửa nhỏ trong luồng sẵn có, cùng test hành vi SYNTHETIC. Không phải đợi D02 để kiểm công thức tổng hợp. Hệ số/ánh xạ là dữ liệu có nguồn, không hardcode danh sách mã vật liệu hoặc 1,10 trong logic Python.
4. Giữ hệ số nền là một điều chỉnh lượng vữa trước phân rã xi măng/cát, không tăng diện tích trát và không tăng thêm lần nữa ở vật liệu mua. Tách CAN_NEN khỏi điều chỉnh TRAT. Dòng nền chưa rõ/ngoài phạm vi bảng phải hiện thiếu/chưa có định mức phù hợp; không mặc định đặc và không tự dùng hệ số AAC.

## Nguồn và ca nghiệm thu

[N2 PDF 589 / in 588](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=589), AK.211/212, ghi chú tăng hao phí vữa gạch rỗng 10%. Dùng skill PDF khi đối chiếu. Mức nền 15/20 mm = 0,017/0,023 m³/m²; mã cột trong AK.21220/30, ngoài AK.21120/30. Không đổi cả bảng thành một biến thể “rỗng” nếu làm mất nguồn nền của từng tường.

Viết test hành vi phù hợp trong bộ test hiện có, thêm tệp riêng khi cần để tránh sửa một tệp quá rộng:

- 10 m² gạch rỗng đúng phạm vi: 15 mm → 0,187 m³, 20 mm → 0,253 m³ vữa trung gian; vật tư tách ra khớp cấp phối đã chọn, chỉ áp hệ số một lần.
- 10 m² đặc đã xác nhận, 15 mm → 0,170 m³; hai mặt mỗi mặt 10 m² gạch rỗng → 0,374 m³; không nhân hai mặt lần hai.
- Hai tường cùng dày nhưng nền khác nhau giữ riêng nguồn/điều chỉnh, không nhân toàn bộ tổng vữa 1,10.
- Chưa rõ nền, chưa chọn mác/cấp phối, thiếu khối lượng hoặc dày không có bảng: có lý do thiếu cụ thể; không số 0 hoặc số nền đặc giả làm tổng đủ.
- AAC/gạch không nung/loại ngoài nhóm đã tra không tự nhận 1,10; dòng CAN_NEN không bị ảnh hưởng.
- Ca trừ âm đảo đúng phần góp đã điều chỉnh; nếu test đi tới gộp phần biết/thiếu, ghi rõ giới hạn Q02 thay vì âm thầm sửa cả cơ chế tổng hợp.
- Có nguồn trên đầu ra; nhập tay vẫn phản ánh C theo quy tắc hiện hành, không nâng thành A chỉ do hệ số có norm_code.

## Giới hạn quyền sửa

Được sửa tối thiểu nhánh walls/materials/norms và test liên quan trong hợp đồng đã chốt. File models/takeoff/API/boq chỉ sửa đoạn thực sự cần và sau thông báo hợp đồng; không tạo engine khác. Nếu cần dữ liệu ánh xạ mới: đề xuất vị trí/nguồn và cách nạp DB nhất quán trước khi thêm bảng/trường. Thay lược đồ DB phải được chủ đồ án duyệt; không chạy migration/nạp đè DB thật. Danh mục XLSX là nguồn, không chỉnh CSV sinh ra như nguồn độc lập.

Không sửa J04, D02, cases/đáp án build hoặc dữ liệu test thực để làm đẹp số. Không cập nhật CLAUDE.md/SPRINTS.md/NHAT_KY.md trong đợt chạy song song; ghi mọi thay đổi/lệnh/kết quả ở tài liệu bàn giao riêng để phiên tích hợp cập nhật một lần. Không mở UI riêng nếu hợp đồng đầu vào chưa chốt; phần API-only phải ghi đúng là API-only.

## Phải chờ D02 hoặc dữ liệu

- D02/người kiểm xác nhận đúng loại nền, mặt trát, chiều dày/diện tích, mác và cấp phối hoặc vữa sản phẩm của hồ sơ trước khi áp vào công trình/so đáp án/đo KPI. Có bảng nguồn và test SYNTHETIC không thay bước này.
- Chưa có loại nền đáng tin trong danh mục: giữ thiếu, lập bảng cần bổ sung; không gán tất cả phương án GNxx theo tên gọi chung.
- Vật liệu khác 0,5% trong nguồn là cơ sở chi phí, không sinh kg/bộ/viên. Thiếu thành phần này không cho phép tuyên bố toàn bộ vật tư mua đã đủ.

## Kiểm và bàn giao

Nếu chỉ thiết kế: không cần pytest giả, bàn giao hợp đồng + ca số học + phần chờ. Nếu đổi mã: chạy test trọng tâm và toàn bộ pytest sau cùng, báo đúng passed/skipped/xfail/failed. Nếu đổi data: check_data trên DB kiểm thử nạp đúng phiên bản, ghi hash/cách nạp; không có DB thì báo chưa kiểm, không coi CSV đã qua. Không chạy test đồng thời trên cùng DB với D02/phiên khác. Nếu sửa UI, kiểm thao tác thật một hồ sơ build và giữ dữ liệu qua request/response.

Bàn giao diff/file, ví dụ trước-sau, kiểm tra đã chạy, dữ liệu dùng, phần làm ngay đã xong và phần chờ riêng. Ghi “chờ Codex review”; không tự nghiệm thu J05c/J04 hoặc công bố đạt trên hồ sơ thật.
