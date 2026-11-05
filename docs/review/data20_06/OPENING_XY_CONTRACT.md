# DTO tọa độ lỗ mở — contract cho serializer

`ReviewOpening.x` và `.y` là số hữu hạn tùy chọn theo hệ tọa độ dữ liệu đầu vào, cho phép âm hoặc 0. Thiếu/trống JSON biểu diễn bằng `null`; bản cũ không có trường vẫn đọc là `null`. Không suy vị trí từ parent và không đổi null thành 0. NaN, ±Inf và chuỗi bị từ chối. `id`, `wall`, `w`, `h`, `keep`, `src`, `ev` giữ ý nghĩa cũ.

`ReviewPlan.openings` (confirm) và `PlanInput.openings` (rough) dùng cùng DTO. Khi serializer thực sự gửi `x/y`, `model_dump(mode='json')` bảo toàn tọa độ và `save_review`/`save_rough` hiện đưa input dump vào JSON result; chưa thực hiện ghi DB hoặc xác nhận mở lại qua ứng dụng. Kết quả partial `pending_openings`/`outside_masonry_openings` cũng giữ `x/y`. Frontend cần truyền nguyên giá trị trong cả hai payload, không lọc lỗ thiếu kích thước và không dùng `x || 0`/`y || 0`; bản cũ thiếu tiếp tục hiển thị chưa có tọa độ.

Đã kiểm test DTO và dump/restore trong bộ nhớ: 34 passed cùng các ca incomplete, tọa độ 0/âm/null và giá trị không hợp lệ. Không chứng minh database đang lưu/mở lại được. [Patch tăng dần](OPENING_XY.patch), [manifest](OPENING_XY_MANIFEST.json) dựa trên nonmasonry freeze hash `c106399d612dc40c9687956b879a8edd09902c5b94cedc2d59215609c03a67a5`; `git apply --check` thành công trên bản sao base. Không cập nhật dữ liệu cũ, không thêm bảng, chưa triển khai.
