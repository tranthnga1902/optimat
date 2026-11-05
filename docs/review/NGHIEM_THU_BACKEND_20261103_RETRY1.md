# Nghiệm thu kỹ thuật backend — hồi quy retry1 ngày 03/11/2026

**ĐẠT trong phạm vi backend đã kiểm.** Điều phối 01 đã trực tiếp đọc kết quả terminal, log, preflight, hash trước/sau và các bàn giao/review tương ứng. Đây là mốc nguồn trước triển khai O01, tiên lượng G8 và trợ lý AI mới.

## Bằng chứng hồi quy

- `reports/integration_next/retry1/result.json`: 840 bài được thu; **824 passed, 16 skipped, 0 failed, 0 xfailed/xpassed**, exit0.
- Pytest 548,14 giây; runner 551,25 giây. Kết thúc 15:59:37 UTC ngày 03/11/2026, tức 22:59:37 tại Việt Nam. Session77098 terminal, process32372/child39124 đã được xác minh sống trong lúc chạy; không khởi chạy lại do timeout quan sát.
- `preflight.json`: hai snapshot cách3 giây không thay đổi, không có pytest khác lúc kiểm; noDB, ngoài sandbox cho TestClient, không `--runxfail`.
- `hash_before.json`, `hash_after.json`, `hash_diff.json`: **225 tệp trong phạm vi src/tests/scripts/catalog không sửa, thêm hoặc mất trong lượt chạy**. Root còn đối chiếu độc lập snapshot giữa lượt, không thấy thay đổi.
- 16 ca bỏ qua:15 PostgreSQL chưa có OPTIMAT_TEST_DATABASE_URL và1 symlink Windows không có quyền tạo trong môi trường kiểm. Không ép chạy trên DB thật đang dùng, không thay quyền máy để làm xanh.
- Frontend, SQL, tài liệu, báo cáo và code AI đang staging ngoài phạm vi hash. Full này không bao phủ các phần đó.

## Phần được tiếp nhận kỹ thuật

| Phần | Kết luận và bằng chứng riêng |
|---|---|
| N03 giằng | Đạt kỹ thuật sau review2/focused162, probe root độc lập và full này. Hợp cùng trục/cao độ đúng phạm vi; khác cao độ giữ riêng; giao tiết diện chưa hỗ trợ giữ thiếu; trừ xây theo phần giao bề rộng; cốp pha đáy thiếu căn cứ giữ None/D độc lập với gate cửa/cột. BT/phần biết không bị xóa. `reports/n03/review2/`, `N03_REVIEW_20261103.md`. |
| Metadata WorkDimensions | Đạt kỹ thuật API/producers trong phạm vi đã giao: focused231 passed, review14 khớp11file FINAL; source/protected_N03 giữ sáu hàm tính/khấu trừ cốt lõi. Dài/rộng/cao/dày/diện tích/cao độ/Ø có nguồn, finite/None/0/không áp dụng, count/repetitions và basis raw/reference/union/deduction được phân biệt. Không dùng metadata tái tạo net hoặc nâng D. `reports/work_dimensions/`. |
| Nguồn giá phần thô | Đạt kỹ thuật hunk attach_prices: focused95 passed, review14 khớp2file FINAL và phần ngoài function như base metadata. Reset tiền cũ trước chọn lại, giữ đúng nguồn/VAT/cước/hạn theo nguồn hoặc chưa rõ, không tính tiền dòng D, không đổi lượng hay tự quy đổi thuế/cước. `reports/rough_price_source/`. |
| Chính sách giá/đơn vị | Gói pricing/optimizer hiện có được chạy qua full; focused41 của báo giá/VAT/cước và110 production trước đó là bằng chứng riêng. Giá khác đơn vị/thiếu nguồn không được suy thành giá mua; BULLETIN/lịch sử/dự đoán giữ đúng vai trò. Chưa chứng minh dữ liệu giá thật đủ để mua. |
| JSON/NDJSON xem bản vẽ | Lỗi NaN từ detect_class trống được sửa ở nguồn bảng tra; HTTP mặc định và progressive đã qua focused rồi full. Vật liệu thiếu lớp vẫn ở danh sách lựa chọn. Preview không tự xác nhận lượng. |
| Route tải tệp quản trị | Đạt kỹ thuật backend kiểm quyền, project/file, đường dẫn, byte/header/Unicode theo các fixture; symlink case Windows còn skip. Chưa nghiệm thu tải100tệp thực qua ứng dụng vì quan sát download chưa hoàn tất. |
| N02/Q02/B01/A01/Q01 đã nghiệm thu trước | Full mới không có failure ở hồi quy tương ứng. Giữ mốc và giới hạn cũ; không đổi thành xác nhận độ chính xác trên hồ sơ thật. |

## Các cổng còn mở

1. **O01 chưa triển khai:** nguồn dầm từng tầng và vùng KC chồng một phần vẫn là đầu việc P0 đã có BA/DTO. Gói full này không tuyên bố sửa O01, O02/O03/O04 hoặc mọi dạng cấu kiện.
2. **G8 M1 là yêu cầu mới bắt buộc UI+Excel:** chi tiết dòng tiên lượng, hệ số có nguồn, quy đổi đơn vị, raw trước làm tròn, tổng đối soát và bốn vật tư AF.11110. Bản BOQ cũ chỉ parity tổng chưa đáp ứng yêu cầu mới. M1 là nguồn fixture riêng, không thay catalog chung hoặc làm đáp án bản vẽ khác.
3. **AI tư vấn toàn bộ phần thô** đang staging theo chỉ đạo mới, chưa trong full. Rowchat hoặc tư vấn chỉ tường không đủ phạm vi. Lượt OpenAI thật trên một hồ sơ thật đã được user ủy quyền cho04 nhưng cần khép adapter/contract trước; không gửi nguyên CAD, không giả snapshot đã kiểm.
4. **UI/consumer/Excel/browser:** các harness và QA P20 là bằng chứng kỹ thuật riêng; cần parity đúng source/API mới và phạm vi mới. QA ACTUAL-build Tân Bình còn gate upload user declined, không vòng qua native/API/browser khác.
5. **Đáp án và giá thật:** D02 Hương/Sang chưa có phê duyệt độc lập; tổng móng/bể mâu thuẫn giữ chờ. Thiếu nguồn/quy cách/giá/điều kiện không được bịa để khép bảng hoặc huấn luyện XGBoost. DB chưa được nghiệm thu qua các ca skip.

Mọi sửa sau snapshot225 phải có diff/hash và kiểm tương ứng; không dùng biên bản này bao phủ source mới. Quyền ghi/freeze/full do01 điều phối,00 gom ưu tiên và quyết định sản phẩm với chủ đồ án.
