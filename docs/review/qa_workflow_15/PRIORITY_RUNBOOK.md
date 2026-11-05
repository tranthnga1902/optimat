# Kịch bản QA ưu tiên sau freeze

Luồng demo mới thay thứ tự tuyến tính cũ: sau kiểm/lưu tới thẳng `/toi-uu`, không chọn tay vật liệu; nhận nháp toàn phần thô và hỏi AI, xác nhận/lưu cả phương án. `/dieu-chinh`/xem giá tùy chọn. Dùng AI23–26 tại AI_MATERIAL_ACCEPTANCE.md để kiểm nhánh chính, không tường, thiếu căn cứ, override và restore. Những cổng receipt/version/invalidation bên dưới vẫn áp dụng, không đòi materials-ready thủ công chỉ để xem nháp.

Trạng thái: CHUẨN BỊ, chưa chạy. Chỉ tài liệu QA15. Không full/TestClient, không tự mở browser/API restart, không thử lại upload Tân Bình bằng bất kỳ đường nào. 01 giao lượt và nguồn freeze; 02 giữ browser/API restart, 05 sole full.

## Cổng nhận bàn giao

01 cung cấp phạm vi ca, hash freeze và owner thao tác; 02/03/04 cung cấp hợp đồng snapshot cuối cùng, ví dụ payload đã loại bí mật và lệnh focused được phép. Không chạy lệnh chỉ vì có trong bàn giao nếu ngoài lượt được cấp. Dùng dự án/fixture synthetic cô lập do owner cung cấp, không sửa localStorage dự án thật để thử quota hoặc race.

Mapping đã được 01 chốt theo implementation02: `projectUid` = projectSessionId; `drawingId` = documentRevision; `reviewId` và `materialRevision` giữ nguyên. `checked: number[]` biểu diễn phạm vi checkedWorkKeys **chỉ trên immutable reviewId và chính xác thứ tự works của snapshot đó**. Không yêu cầu đổi tên hoặc thêm field trùng. `partial`/`confirmed` gắn cùng receipt; draft không ready; legacy thiếu ID phải kiểm lại. Đây là hợp đồng nghiệm thu, chưa phải kết quả runtime và không xác nhận source freeze.

Oracle S09 bắt buộc: cùng file nhưng result array đổi thứ tự, recompute hoặc đổi scope phải vô hiệu receipt/index cũ; không áp index đã kiểm của dòng A sang dòng B tại cùng vị trí. `projectUid` bền qua restore dù `archive.id` đổi. Sau khi kiểm lại, receipt mới chỉ được áp lên đúng snapshot mới.

Đã đối chiếu schema bàn giao03 tại `reports/work_dimensions/CONTRACT.md` và manifest SOURCE_READY theo nhật ký01; oracle chi tiết tại `DIMENSIONS_CASES.md`. Chưa có freeze tích hợp/lượt QA15. Nếu schema sửa sau focused phải cập nhật lại trước chạy; không nhận source-ready là nghiệm thu.

## Các lượt ngắn, theo thứ tự

| Lượt / ca | Chuẩn bị | Trình tự | Oracle và điều kiện dừng |
|---|---|---|---|
| 1 — S07/S09 | Hai dự án synthetic A/B; A có ít nhất hai dòng phân biệt được và một dòng thiếu; snapshot/receipt cùng revision | Kiểm riêng dòng thứ nhất, chấp nhận partial, lưu; reload; A→B→A hai vòng qua history; ghi định danh mỗi vòng | Định danh A ổn định dù archive mới; B riêng biệt; đúng dòng đã kiểm và partial phục hồi. Nếu mất/trộn dữ liệu: FAIL, giữ bằng chứng rồi dừng nhánh phụ thuộc |
| 2 — S08/S10/F03 | Một bản hợp lệ, bản legacy thiếu liên kết, bản draft; bản sao synthetic có một revision lệch | Mở từng bản; thử đi bước sau; tính/lưu đúng bản rồi thử lại | Legacy/lệch/draft không ready; không nhận receipt của bản khác; bản hợp lệ đi tiếp chỉ sau kiểm/lưu thành công. Chốt mapping hợp đồng trước đánh giá |
| 3 — S02/S04 | Owner cung cấp harness fault injection có thể khôi phục, không DB thật | Lần lượt lỗi trước ghi, giữa các khóa, và khi rollback; quota lúc lưu kiểm, lưu vật liệu và đổi dự án | Không báo lưu thành công, không trộn snapshot/ready, giữ bản trước hoặc báo lỗi phục hồi rõ; ghi riêng rollback lỗi. Không lặp fault trên dự án thật |
| 4 — S05/S06 | Hai response synthetic có identity và dữ liệu khác; owner hỗ trợ điều khiển thứ tự | Gửi R1 rồi R2; trả R2 trước R1; lặp với đổi dự án/file/tầng giữa chờ | R1 không ghi đè R2 hoặc dự án mới; cờ kiểm/kết quả cũ hết hiệu lực đúng phạm vi; ghi timeline và payload identity |
| 5 — D01–D03/F02/F04 | Payload có hai cấu kiện khác kích thước, cao tầng khác cao xây, null/0/không áp dụng, nguồn A/B/C/D | Mở bảng/chi tiết; kiểm/bỏ kiểm; sửa cao, tính/lưu; đối chiếu phép tính đã được owner chốt | Không suy kích thước từ formula; đổi mm→m đúng; thiếu không thành 0; nguồn không nâng cấp do kiểm; subtotal/missing còn nguyên |
| 6 — D08 | Bộ fixture N03/Q02 cuối do 03/14 bàn giao, có expected trước/sau | Chỉ chạy ca focused được 01 giao hoặc đọc terminal owner; đối chiếu JSON cùng hash | Raw/net, giao tiết diện và CP thiếu không thành đủ; không dùng kết quả hash cũ làm đạt cho freeze mới |
| 7 — M01/M02/M03/G01 | Snapshot đã kiểm và lựa chọn vật liệu synthetic; có bản đổi cấu tạo và bản không đổi | Tạo vật tư/kết quả; sửa lượng; chọn vật liệu đổi dày; quay lại/reload; lặp với lựa chọn không đổi hình học | Lượng/cấu tạo đổi buộc kiểm lại, vô hiệu vật tư/giá/tối ưu cũ; lựa chọn không đổi không mất lượng; phân biệt giá tham khảo/báo giá/dự đoán và thiếu quy cách |

Nếu owner chưa có harness hỗ trợ một fault/race, ghi BLOCKED và yêu cầu owner bổ sung trong phạm vi 01 giao; QA15 không tự sửa tests/scripts hoặc mở TestClient. Không dùng response giả để kết luận độ chính xác bản vẽ thật.

## Phiếu ghi kết quả cho mỗi ca

Sao chép mẫu này trong thư mục QA15 khi có lượt thực thi:

```text
Ca / lượt được 01 giao:
Trạng thái: NOT_RUN | PASS | FAIL | BLOCKED | SKIPPED
Nguồn freeze / hash trước / hash sau:
Hợp đồng định danh và revision được chốt:
Fixture: SYNTHETIC | SAMPLE | ACTUAL-build; tên/hash:
Điều kiện ban đầu / bước thao tác:
Expected / actual:
Snapshot trước/sau đã loại bí mật:
Ảnh / timeline / API / BOQ / terminal và exit code:
Giới hạn bằng chứng:
Blocker / owner / bước tiếp theo:
```

Hash thay đổi ngoài delta được giao: dừng kết luận trên nguồn đó, báo 01 để freeze lại. Ca synthetic đạt chỉ đóng ca kỹ thuật tương ứng; A01 ACTUAL-build giữ BLOCKED do quyền upload cho đến khi người dùng tự chọn hoặc cấp lại quyền. Không dự báo giờ hoàn tất khi chưa có release và dữ liệu.
