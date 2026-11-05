# Inventory cho /quy-tac — ưu tiên cột và giao cấu kiện

Ngày 04/11/2026. Chỉ đọc source và ghi báo cáo, không sửa source đã freeze, không test/build/CAD/DB/runtime. Đối tượng sử dụng: root01 và chủ module17.

`QUY_TAC_PHAN_THO_INVENTORY.csv` có 25 quy tắc, mỗi dòng có consumer file/hàm/dòng/hash, điều kiện, công thức, đơn vị, phép cộng/trừ/giao/gom, xử lý thiếu và giới hạn. ID là ID tài liệu để tra cứu, **không phải khóa cấu hình engine đang đọc**. Không phải inventory toàn bộ công thức phần thô; tập trung nhánh cột và các consumer liên quan theo ưu tiên được giao.

## Trạng thái phải hiển thị

- source_new_frozen_not_integrated: nhánh structural_columns mới đã có consumer trong source nhưng chưa tích hợp runtime. Focused đã bàn giao riêng; lượt inventory này không chạy lại.
- source_legacy_runtime_unverified: mã legacy đã triển khai trong source, chưa xác minh process runtime hiện tại sử dụng đúng hash này.
- Đề xuất chưa có consumer: tự nối trục–leader–section–span–slab region từ CAD VN002; mapping ô sàn tầng trên chính xác cho khoản trừ CP; sửa mô tả quy tắc làm đổi engine. Không được hiển thị các mục này là đang hoạt động.

## Giới hạn quan trọng

1. Cột KT legacy thiếu slab vẫn lấy H và cảnh báo; nhánh instance mới giữ gross và net NULL khi thiếu nguồn khoản trừ. Không gộp hai hành vi thành “hệ thống luôn để NULL”.
2. Cốp pha instance mới luôn pending vì chưa kiểm quan hệ giao; legacy schedule tính chu vi đủ và chưa trừ đầu dầm. Không ghi cả hai là đã xử lý mọi giao cột–dầm.
3. _slab_form_deduction còn shortcut gán theo plan dầm/cột; chưa chứng minh đúng ô sàn tầng trên. Khoản trừ này không phải tính lại bê tông COT.
4. Aggregate schedule là số theo loại/đoạn, không phải physical instance. Cùng mã khác trục phải phân biệt; unknown scope giữ pending thay cộng đôi.
5. Reader VN002 chưa đạt end-to-end. Thuộc tính block explicit mới là một nhánh đọc generic, không phải bằng chứng VN002 dùng các thuộc tính đó. Không dùng fixture nhập tay hoặc số oracle làm cấu hình production.
6. Phạm vi nghiệp vụ chỉ nhà ở riêng lẻ xây mới ≤5 tầng. Inventory không tìm thấy cổng chung trong các consumer đã đọc để tự chứng minh loại công trình/số tầng; cần căn cứ hồ sơ và eligibility bên ngoài phép tính. Không mô tả giới hạn phạm vi như một validator đã có.

## Cách tích hợp an toàn cho 17

Đưa công thức, nguồn consumer, trạng thái source/runtime và hạn chế lên /quy-tac dưới dạng thông tin. Trường chỉnh sửa chỉ có tác dụng thực thi khi tồn tại consumer/config thực sự được engine dùng và có luồng ghi/kiểm/phiên bản đã được giao. Không hứa sửa lời mô tả làm đổi công thức. Giữ đúng 20 bảng; inventory này không đề nghị hoặc cấp quyền thêm bảng.

Các số liệu riêng C-2 nằm ở tài liệu kiểm nguồn/test trước, không được nhúng vào rule production. Giữ quyền ghi code module /quy-tac cho17;03 không sửa UI/API hoặc ledger chung.
