# Bàn giao dữ kiện cho trợ lý chọn vật liệu phần thô

Phiên 04 gửi 12, 02 và 15. Điểm vào chính của trợ lý là Phương án tối ưu ngay sau khi kiểm khối lượng. Bước chọn tay và trang xem giá là tùy chọn. [Kế hoạch của chủ đồ án](../../docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md)

## Đầu vào và phạm vi

Tư vấn bắt đầu từ bản kiểm công tác đã lưu và yêu cầu tiếng Việt. Dùng `approvedWork` của phiên 02, cùng `projectUid, drawingId, file, reviewId`. Có thể tư vấn **trước** khi lưu lựa chọn vật liệu. Khi áp vào bảng mua hoặc chạy tối ưu, phải kiểm thêm `materialRevision` của lần lưu thành công. Đề xuất của trợ lý chưa phải lựa chọn đã duyệt.

| Dữ kiện trả về cho trợ lý | Nguồn xác định và cách sử dụng |
|---|---|
| Công tác và lượng lắp đặt | Từng `WorkSnapshot.result.works[i]` cùng `plan, code, element, unit, quantity, basis, status, missing, evidence`. Dùng chỉ số dòng trong phạm vi đúng `reviewId`. Trình bày lượng đã biết và lý do thiếu riêng. |
| Vật tư phát sinh | `result.materials` và `uses`. Mỗi phần góp có `work, plan, quantity, via, stage, status`. Hiện chỉ truy trực tiếp đến mã công tác và mặt bằng. Khi nhiều cấu kiện cùng tầng và mã, ghi phạm vi gộp. Chỉ tách riêng nếu truy được đúng dòng đầu vào cùng bộ định mức; không chia đều theo số cấu kiện. |
| Mác và cấp phối | `snapshot.request.params`, cấu tạo và định mức, `Catalog.materials`, `Catalog.relations`, `result.intermediates`. Bê tông/vữa trung gian trộn tại chỗ chỉ xuất tiền mua một lần qua các thành phần; giữ loại, mác và phương pháp cấp đã duyệt. |
| Lượng vật tư và lượng mua | Dùng `quantity, quantity_with_waste, complete, unit, missing`. Tách số công tác, nhu cầu vật tư theo định mức và quy cách đặt mua. Tấn thép chưa tự đổi thành số cây; m² cốp pha chưa tự đổi thành số tấm. Chỉ quy đổi nếu có quy cách, hệ số và nguồn áp dụng. Dòng D có thể còn phần lượng đã biết. |
| Phương án kỹ thuật | Mỗi ứng viên có mã danh mục thật, đơn vị/quy cách thiết kế, căn cứ phù hợp và phần chưa rõ. Quy cách hoặc cấp kỹ thuật chưa chứng minh tương đương thì cần người phụ trách thiết kế quyết định. So chi phí hoặc lịch giao sau bước lọc kỹ thuật. |
| Giá và giao hàng | Dùng `price_offers` và `select_best_offer(actual_only=True)` cho mã vật tư. Giữ nguyên đơn vị, nhà cung cấp, nguồn, ngày giá, hạn theo nguồn, VAT, cước và lý do loại. Thiếu hạn ghi “chưa rõ hiệu lực”. Giá lịch sử/công bố chỉ để tham khảo. Nếu chưa có nguồn về giao hàng thì để trống thời gian. |
| Phương án tường | Dùng `wall_groups` cuối cùng, `Catalog.wall_view()` và bộ tối ưu hiện có khi đủ điều kiện. Hệ số U và thời gian, cước dự tính được gắn đúng phương án tường. Không yêu cầu các nhóm khác phải có U hay phải chờ bộ tối ưu tường trả nghiệm. |

## Nhóm phải xét khi phát sinh

| Nhóm | Ràng buộc kỹ thuật cần giữ | Khi thiếu căn cứ |
|---|---|---|
| Bê tông móng, cột, dầm, sàn, thang, mái và cấu kiện phụ | Đúng mác và vị trí; tách bê tông lót, bê tông kết cấu, trộn tại chỗ, thương phẩm. | Giữ m³ công tác; nêu thiếu mác, phương pháp cấp hoặc cấp phối. |
| Thép và phụ kiện | Đối chiếu bảng thống kê, đường kính, cấp thép và quy cách bán. Dây buộc, vật liệu phụ chỉ tính khi định mức có căn cứ. | Nêu khối lượng theo hàm lượng nếu có; để trống mã/quy cách cây, cuộn hoặc phụ kiện còn thiếu. |
| Cốp pha | Đúng cấu kiện, diện tích tiếp xúc và hệ ván khuôn. Nhu cầu mua/thuê phụ thuộc quy cách, cách sử dụng lại. | Giữ diện tích công tác; nêu loại ván, kích thước tấm hoặc căn cứ luân chuyển còn thiếu. |
| Xây, trát | Đúng bề dày, vai trò tường, kích thước gạch, loại/mác vữa, nền trát và chiều dày lớp. | Đổi vật liệu ảnh hưởng hình học thì giữ dưới dạng chờ kiểm. Thiếu giá không làm mất cấu tạo kỹ thuật phù hợp. |
| Nền, chống thấm | Đúng từng lớp, dày lớp, diện tích/phạm vi, vật liệu và định mức phủ. | Giữ m² hoặc m³ đã kiểm; không tự chọn số lớp, quy cách bao/thùng/cuộn. |
| Công tác khác trong phạm vi M01 | Với hạng mục không phát sinh mua, ghi căn cứ đã xác định. Với hạng mục chưa hỗ trợ, giữ dòng và nêu giới hạn. | Danh sách ứng viên rỗng chưa chứng minh công tác không cần mua. |

## Nghiệm thu tư vấn

- Nhiều ứng viên cùng quy cách. Nêu từng mã thật, so các điều kiện có thể so và mô tả dữ liệu còn thiếu. Giá giao tận nơi và giá tại kho hiển thị riêng.
- Một ứng viên hợp lệ. Giải thích lý do phù hợp và trình người dùng chọn. Nhiều nhà cung cấp của cùng mã vẫn là một vật liệu.
- Không có ứng viên, hoặc có ứng viên kỹ thuật nhưng thiếu giá/giao hàng. Trả đúng trạng thái cho từng nhóm và tiếp tục tư vấn các nhóm còn lại.
- Có ít nhất một ca phi tường, một ca thiếu quy cách mua, một ca đề xuất làm đổi hình học và một ca kết quả đến muộn sau khi đổi bản kiểm. Ghi nguồn chính xác của lần giải thích là OpenAI, mẫu, hoặc bộ tách quy tắc.
- Kiểm OpenAI thật là một lượt riêng trên dữ liệu được phép. Tài liệu này chưa phải bằng chứng đã gọi API, đã triển khai trợ lý hoặc nghiệm thu trên công trình thật.
