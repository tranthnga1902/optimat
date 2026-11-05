# D09 — Kiểm kê quy tắc DATA20

Ngày 04/11/2026. Phạm vi chỉ đọc nguồn và ghi ba tài liệu trong thư mục này. Không chạy test/CAD/DB/browser, không sửa dữ liệu chuẩn hoặc kế hoạch chung, không xác nhận dữ liệu thực.

Inventory gồm 22 CSV, 989 bản ghi. Một dòng là một bản ghi; ordinal là thứ tự bản ghi, không phải số dòng vật lý. rule_key chỉ để tra cứu, không phải record_key DB và có thể lặp. payload_json giữ dữ liệu dạng chữ; __extra_cells__ giữ các ô vượt header để không âm thầm bỏ mất. Hash tệp tính theo byte gốc, hash dòng theo JSON sắp khóa. Nhãn nguồn/xác minh được chép từ CSV, không phải xác nhận reviewer. Test_ref là nơi đối chiếu, không chứng minh từng quy tắc có ca dương/âm hoặc test đã đạt.

Sáu bộ trong scripts/init_db.py gồm rough_norms → work_norms và năm bộ → rule_sets. rule_sets còn chứa danh mục tham chiếu và model_versions. Không đọc DB nên chưa kiểm phiên bản/số dòng/model đang dùng, hoặc tương đương CSV–DB.

Đã kiểm tệp, header, hash và mã/test được dẫn. Chưa kiểm thực thi toàn bộ regex, chuyên môn, cache, hình học thực, quyền dùng hoặc đáp án VN002/Pioneer. Ưu tiên đối chiếu hai hồ sơ này trước khi tìm hồ sơ mới. Không đặt chỉ tiêu số dòng hoặc suy tỷ lệ hoàn thiện.

Bất thường cấu trúc cần chủ dữ liệu kiểm, chưa tự sửa:

- data/rules/viet_tat.csv bản ghi 4: ô dư sau header
- data/rules/viet_tat.csv bản ghi 5: ô dư sau header
- data/rules/viet_tat.csv bản ghi 6: ô dư sau header
- data/rules/viet_tat.csv bản ghi 7: ô dư sau header
- data/rules/viet_tat.csv bản ghi 8: ô dư sau header
- data/rules/viet_tat.csv bản ghi 9: ô dư sau header
- data/rules/viet_tat.csv bản ghi 10: ô dư sau header

## Ràng buộc phạm vi hồ sơ

Chỉ phần thô nhà ở riêng lẻ xây mới không quá 5 tầng. Khi chọn hồ sơ hoặc ca kiểm phải ghi căn cứ loại công trình và số tầng. Chưa rõ thì chờ xác minh; ngoài phạm vi thì loại khỏi mẫu số và ghi lý do, không loại tùy kết quả.

Không tính công trình bể độc lập, cấp thoát nước hoặc nhà công nghiệp thành hồ sơ nhà ở. DM-1 VN002 chỉ xét dầm/cốt thép bể thuộc căn nhà. Theo thông tin điều phối, khung tên VN002 ghi “Nhà ở gia đình”; thông tin 4 tầng hiện theo manifest/tên gói, chưa thay cho số tầng thiết kế đã kiểm. Phiên D09 chưa mở bản vẽ để xác nhận các thông tin này. Pioneer cũng phải có căn cứ phạm vi trước khi dùng cho nghiệm thu.

Giữ đúng 20 bảng vật lý. Nếu thực sự cần thêm bảng, trình lý do/phương án và chờ chủ đồ án duyệt trước khi triển khai. Báo cáo D09 không cấp quyền thay schema hoặc mở lại công việc đã dừng.
