# Ca nghiệm thu trợ lý vật liệu toàn phần thô

03/11/2026. Thay MVP tường/hỏi dòng. Chưa có live/UI nghiệm thu; terminal mock ghi riêng khi có kết quả thật.

| Ca | Dữ liệu/nhu cầu | Điều kiện đạt |
|---|---|---|
| M01 | SYN bê tông/cấp phối, thép, cốp pha, xây/trát, nền/chống thấm, phụ kiện | Mọi work có coverage/lý do; không cần wall_groups/NSGA-II |
| M02 | Hai cấu kiện cùng code+plan, một MaterialUse tổng | Không chia đều hoặc gán tổng cho riêng cấu kiện |
| M03 | Vữa/bê tông trung gian đã tách nguyên liệu | Hiện riêng, không cộng lại vật tư mua |
| M04 | Thép có known-part nhưng thiếu đường kính/cấp/chiều dài cây | Giữ lượng/đơn vị, purchase null, không tự ra số cây |
| M05 | Thiết kế bê tông một mác, yêu cầu rẻ | Không hạ mác/đổi supply; mã tra khác proposed cần kiểm thiết kế |
| M06 | Một/nhiều/không mã tra phi tường | Giữ lý do; nhiều NCC không là nhiều cấu tạo; chưa chứng minh tương đương |
| M07 | Thiếu giá/sai đơn vị/hết hạn/thiếu nguồn | Không bịa giá, không kết luận rẻ nhất/đạt ngân sách; BULLETIN chỉ tham khảo |
| M08 | Đổi ưu tiên ngân sách/lịch/loại trừ | Ghi parse source regex; không hiểu hết hoặc thiếu dữ kiện thì nói chưa kết luận |
| M09 | Chống thấm/cốp pha/REQUIRES thiếu điều kiện | Hiện missing, không tự định mức hoặc đếm bao/bộ/tấm |
| M10 | Đào/đắp không phát sinh vs công tác chưa map | Hai trạng thái riêng; đất mua ngoài cần khai báo |
| M11 | AI mã/dòng lạ, duplicate/thiếu advice, số mới/refusal | Reject, không sửa facts/approval |
| M12 | Cookie hết hạn/sai hash/binding/principal | Reject trước transport; không gọi local ownership đã verified |
| M13 | NoDB chưa opt-in/Origin lạ | Reject trước OpenAI, không mở công khai khóa backend |
| M14 | Thiếu key/network/API/schema lỗi | Thông báo sạch, không raw exception/secret, bảng gốc vẫn xem được |
| M15 | Đổi project/drawing/review/materialRevision/hủy/response trễ | Không hiện answer cũ/khóa nút vĩnh viễn; không hứa hủy phí |
| M16 | Chọn/xác nhận đề xuất | Chỉ callback chờ kiểm, không sửa design/quantity/receipt/ready/purchase |
| M17 | Payload quá lớn/extra CAD/key | Reject, không cắt phạm vi âm thầm |

Live sau release: một call SYN tối thiểu đa nhóm gồm phi tường, dòng thiếu, công tác đất và trung gian. Không đọc .env/key/đổi model/upload hồ sơ thật. Ghi hash, terminal mock, requestId, model, thời gian, payload redacted, response/ảnh UI; không cookie/Authorization. QA15 độc lập sau hook;05 sole full. Tường-only chưa đạt demo toàn phần thô.
