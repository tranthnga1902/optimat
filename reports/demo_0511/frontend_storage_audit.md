# Rà lưu phiên CAD sau thay đổi luồng giao diện

Chỉ đọc source và mô phỏng localStorage bằng fixture tổng hợp trong reports/demo_0511/frontend_regression.cjs. Không đọc browser storage thật, không sửa source, không gọi backend trong lúc kiểm hồi quy đang chạy.

## Luồng hiện tại

/do-boc xác nhận kích thước/khối lượng từng mặt bằng -> /dieu-chinh (Review adjustment) khôi phục optimat-review, chọn vật liệu và phần thô -> /vat-lieu -> /toi-uu. Gate mở bản vẽ yêu cầu optimat-project-name và optimat-project-info. Thay đổi mới do phiên giao diện khác thực hiện, không hoàn tác.

## Bằng chứng trong source

- Review.tsx lưu optimat-review bằng JSON.stringify({data,states,planP,confirmed,pi,structural}). data bao gồm CAD SVG của từng mặt bằng và overview, segs/walls/openings/labels cùng dữ liệu nhận dạng.
- Autosave thực hiện mỗi khi thay đổi data/states/planP/confirmed/pi/structural, trên localStorage đồng bộ; chưa loại CAD hoặc kiểm dung lượng trước ghi. Bản vẽ lớn có thể vượt quota lưu trữ. Không giả định mọi browser đều có cùng ngưỡng5MB; chưa đo dung lượng thực tế trong browser.
- Autosave catch hiện cảnh báo giữ trang mở. sendConfirm đã gọi API, setConfirmed và remember(optimat-confirmed) trước lần ghi optimat-review cuối để chuyển bước.
- Nếu lần ghi đó lỗi quota: router.push tự động không chạy (bị catch), nhưng state confirmed mới vẫn có. Link Tiếp: điều chỉnh vật liệu chỉ xét mọi confirmed[i], không xét saveError. Người dùng vẫn có thể sang /dieu-chinh và khôi phục snapshot cũ.
- Nếu chưa từng lưu snapshot thành công thì /dieu-chinh không có dữ liệu để khôi phục. Nếu có snapshot cũ thì số ở optimat-confirmed mới có thể khác states/confirmed cũ của optimat-review.

## Probe đã chạy

Trong harness, chỉ setItem('optimat-review',...) bị ném Error('QuotaExceededError'), store confirmed và input đang mở vẫn hoạt động. Sửa chiều cao thành3800 và xác nhận:

1. Warning autosave có hiển thị.
2. Tự chuyển trang không chạy.
3. optimat-confirmed nhận height3800.
4. optimat-review giữ chiều cao cũ.
5. Link /dieu-chinh vẫn hiển thị.

Probe là quan sát rủi ro tái hiện, không đánh PASS sản phẩm cho nhánh quota này. Không kết luận bản vẽ thật đã chạm quota. Các kiểm hồi quy stale-response/height/multiple-stairs/transition bình thường đều tiếp tục PASS.

## Đề xuất sửa tối thiểu xin cấp lượt riêng

Chỉ Review.tsx và harness báo cáo, không engine/IndexedDB/backend:

- Lỗi ghi phiên phải đặt cùng cảnh báo saveError ở cả autosave và sendConfirm.
- Chỉ cho chuyển /dieu-chinh (tự động và Link) khi snapshot hiện tại đã ghi thành công; nếu thất bại giữ nguyên state/input/confirmed đang mở, báo đã xác nhận nhưng chưa lưu phiên chuyển bước, không nói API xác nhận thất bại.
- Không xóa optimat-confirmed hoặc draft để giải phóng chỗ một cách âm thầm; không điều hướng sang snapshot cũ.
- Nếu cần dữ liệu lớn: tách phần CAD nặng khỏi snapshot hoặc dùng cùng phiên in-memory khi điều hướng phải là quyết định riêng, có QA refresh/back; không thêm IndexedDB trong bản sửa khẩn cấp.

## QA sau khi được sửa

- Fixture quota: không còn nextLink hoạt động khi snapshot bị từ chối, input và confirmed vẫn giữ, thông báo đúng hai kết quả xác nhận/lưu phiên.
- Browser thực tế: bản CAD nhỏ và KT46, kiểm dung lượng snapshot theo dữ liệu file/API đã nhận hoặc thao tác UI được cấp phép; refresh, quay lại, /do-boc -> /dieu-chinh -> /phan-tho; không dùng thao tác script đọc toàn localStorage.
- Mô phỏng quota trong harness không thay browserQA. Giao diện thực tế còn CHỜ kiểm.
