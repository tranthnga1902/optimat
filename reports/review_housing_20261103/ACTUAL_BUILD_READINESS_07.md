# 07 — Hồ sơ ACTUAL-build đề xuất để kiểm luồng

Theo kế hoạch ưu tiên và phân vai mới, đề xuất **nhà Hương Hải Dương7×12**, đã có KT+KC DXF, DWG gốc, PDF và tiên lượng nguồn. [Manifest](ACTUAL_BUILD_CANDIDATE.json) ghi đường dẫn, kích thước file và SHA-256 kiểm từ file thực có; không tải lên, không sửa split/registry, không chạy lại CAD nặng.

**Đủ chuẩn bị kiểm luồng, chưa đủ nghiệm thu sai số toàn công trình.** Có thể kiểm chọn hồ sơ→KT/KC→xem nguồn→sửa/xác nhận một phần→chọn vật liệu→xuất mà không đòi mọi dòng có đáp án. Việc chạy UI/upload do01 xếp lịch và chờ người dùng chọn hoặc cấp lại quyền; không vượt gate đã từ chối trên hồ sơ Tân Bình. Chưa thực hiện luồng trong lượt này.

Ví dụ đối chứng nhỏ có căn cứ: W010 thép cột, tổng KLCT CAD theoØ6/16/18 khớp95,6/556,5/107,9kg, tổng**0,760t**. Dòng tiên lượng trang9/bảng1/dòng12 là**0,836t**, gồm cơ sở hệ số1,1; không dùng0,836t làm đáp án lượng thép net0,760t. Handle và tọa độ nằm trong manifest. Đây chỉ là đối chứng bảng thống kê, chưa đo lại từng thanh hay kích thước cột, chưa có phê duyệt người dùng.

W005 móng/bể Hương và W007 Sang vẫn cách ly do bảng tự mâu thuẫn; W006 bê tông móng Hương còn sai bề rộng nguồn/phần giao chưa chốt. Không dùng số tổng làm đáp án cho phần thiếu. Mọi dòng khác đọc gate tương ứng, không suy “cả hồ sơ sạch” từ ví dụ W010. Báo cáo42 mã và DIEM_CAN_CHOT_THEP_BE.md là hồ sơ quyết định riêng, không chặn việc chuẩn bị kiểm luồng một phần.

Bàn giao01/15: dùng manifest để chọn file/phiên bản, kiểm UI giữ riêng lượng nguồn/lượng thiết kế/hệ số và phần thiếu. Chưa có nguồn kích thước hoặc chưa đủ quy cách vật tư thì giữ trống và lý do, không gán0 hoặc tự chọn giá/định mức để đủ bảng. Nếu chọn hồ sơ khác, manifest này chỉ là phương án dự phòng; không tự thay hồ sơ mà chủ đồ án đã chọn.

Lượt này chỉ bổ sung hai báo cáo/manifest; kiểm file tồn tại, SHA và phạm vi ví dụ. Không code/tests/normalized/DB, không tự duyệt hoặc tuyên bố full/QA đã đạt.
