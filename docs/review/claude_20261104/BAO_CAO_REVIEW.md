# OptiMat AI · Bàn giao cho Claude review · 04/11/2026

**Quyết định cần review:** Có thể trình diễn đến bước nào, phần nào đủ căn cứ cho người dùng kiểm khối lượng và phần nào còn chặn việc đề xuất, so giá hoặc đặt mua vật tư? Đọc theo đúng môi trường và phiên bản. Báo cáo tổng hợp biên bản hiện có và cuộc demo dự án 23. Không chạy lại toàn bộ test trong lượt lập báo cáo.

Phạm vi sản phẩm là nhà ở riêng lẻ xây mới tối đa 5 tầng. Luồng đích đi từ hồ sơ gốc → bóc bản vẽ → kiểm công tác và khối lượng → phương án vật liệu phần thô → so giá theo điều kiện giao → tối ưu → bảng mua. Mốc MVP 22/11/2026, đồ án 17/01/2027. Hiện chưa đủ bằng chứng để công bố 80% hoàn thành hoặc sai số trên nhà thực. Git HEAD khi lập báo cáo là `a315602`, nhánh `phan-tho-quy-uoc-csdl-vat-lieu`. Các phiên còn làm việc trên checkout. Khi tái hiện, đối chiếu hash và build trong từng biên nhận thay vì coi riêng HEAD là bản demo.

## Những phần đã làm và giới hạn của từng kết quả

| Hạng mục | Đã làm, đã kiểm ở đâu | Còn mở trước nghiệm thu | Bằng chứng |
|---|---|---|---|
| Phạm vi và dữ liệu | M01/D01 chốt phạm vi và manifest. C01 có đường cơ sở đánh giá cho phát triển. D02 đã cách ly nhãn mâu thuẫn. | Chưa có đủ đáp án đo bóc thật do người kiểm độc lập xác nhận. Mục tiêu 12 hồ sơ build + 8 test độc lập khác với 20 dự án tổng hợp có metadata. | [Tổng hợp các mốc](../TONG_HOP_NGHIEM_THU_20261103.md), [C01](../C01_NGHIEM_THU_KY_THUAT.md) |
| Hồ sơ và lưu lịch sử | Đã áp hai bảng được duyệt `project_document_revisions`, `project_profile_revisions`. Có API hồ sơ, tải nguyên bản, xem trước, bắt đầu phân tích. Đã kiểm dự án 23 trên web 3001/API 8001. | Kiểm tách người dùng, dữ liệu cũ và lỗi lưu ở đúng môi trường đích. Snapshot đối chiếu tại migration chỉ chứng minh những thuộc tính đã được đo. | [Nghiệm thu và các cập nhật theo ngày](../TONG_HOP_NGHIEM_THU_20261103.md), [QA luồng gốc](../qa_workflow_15/PROJECT_SOURCE_ACCEPTANCE.md) |
| PDF, Word, Excel | Có kiểm định tệp, chặn ZIP giả DOCX/XLSX. Backend đọc được XLS mẫu M1 gồm 56 sheet. Đã cập nhật ràng buộc vai trò hồ sơ, tiên lượng và tham khảo. | Chưa có demo đủ tải → xem → mở lại cho từng loại Office/PDF. DOC cũ, encoding và tệp không hợp lệ phải được phân biệt với định dạng hỗ trợ. | [Tổng hợp mixed-file](../TONG_HOP_NGHIEM_THU_20261103.md) |
| Đọc CAD, công tác và khối lượng | Có parser số N01, bảng lặp N02, xử lý giằng chồng N03, metadata kích thước cấu kiện và tổng một phần Q02. N03 đã đạt kỹ thuật sau review và hồi quy. `compute_rough` là nguồn công thức dùng chung. | Chưa nghiệm thu hình học trên hồ sơ thật. Kiểm giao thang–sàn, mái–sàn, dầm–cột–cốp pha, nguồn dầm từng tầng và các khoản trừ theo đúng baseline, nhất là khi thiếu căn cứ căn chỉnh KT/KC. | [Biên bản backend](../NGHIEM_THU_BACKEND_20261103_RETRY1.md), [ca kích thước](../qa_workflow_15/DIMENSIONS_CASES.md) |
| Bảng tiên lượng G8 và Excel | Có hợp đồng dữ liệu chi tiết, dòng lót móng và sàn/nền, quy tắc tổng, bộ xuất thử và ví dụ đối chiếu M1. Có kiểm HTTP JSON/Excel/optimizer bằng fixture tổng hợp. | Chưa đủ chi tiết cho tất cả P03–P07. Cần kiểm workbook thực mở trong Excel và so cùng một lượt từ giao diện đến BOQ, kể cả dòng thiếu. M1 là hồ sơ riêng. | [Bàn giao G8](../../../reports/g8_detail/BAN_GIAO.md), [kiểm Excel native](../qa_workflow_15/G8_PREVIEW_NATIVE.md) |
| AI chọn vật liệu toàn phần thô | Có tư vấn theo công tác và vật tư, kiểm mã/nguồn, giữ dòng thiếu. F01 giới hạn khối lượng theo phần đã kiểm. F02/F03 thể hiện phụ kiện, nguồn, điều kiện và nhãn giá tham khảo. Trên VN002, staging gọi OpenAI thật một lần với 52 dòng công tác, 7 dòng vật tư. Phản hồi bị chặn ở mã TH10 lúc đầu; sau sửa, phát lại nhận đúng 7 dòng và chặn 6 biến thể sai. | Sáu dòng chưa có mã phù hợp. TH10 chỉ là gợi ý dây buộc, thiếu báo giá. Cần ca giao diện dùng đúng lượng đã kiểm. Không gán lượt VN002 cho dự án 23 hoặc xem phát lại là lượt OpenAI mới. | [Lượt thật và phát lại](../../../reports/demo_0511/live_advisor_vn002/KIEM_TRA.md), [tiêu chí AI](../qa_workflow_15/AI_MATERIAL_ACCEPTANCE.md) |
| Giá, lượng mua, tối ưu | Có lịch sử giá có nguồn, chống nhập trùng, sửa khớp quy cách/mác và phân biệt lượng biết với phần thiếu. Có đầu vào optimizer và phép đối chiếu trên fixture. | Thiếu báo giá mua ACTUAL so cùng quy cách, VAT, ngày, địa bàn, lô mua và phí giao. Chưa đủ cơ sở cho kết luận XGBoost tốt hơn giá gần nhất/Ridge hoặc NSGA-II đạt trên ca thực. Chưa khép bảng mua nhiều đại lý và phí chuyến chỉ cộng một lần. | [Readiness giá](../price_model_16/READINESS.md), [chuỗi lượng đến giá](../qa_workflow_15/CHAIN_ACCEPTANCE_GAPS.md) |
| Hồi quy | Biên bản backend ngày 04/11 ghi **1.096 passed, 19 skipped, 15 deselected**, exit 0; 263 tệp trong manifest khớp trước/sau. Bản sửa giao diện có build và kiểm tra riêng. | Hồi quy này loại DB ứng dụng, OpenAI live, CAD thật và frontend. Đối chiếu phiên bản trước khi dùng kết quả cho thay đổi sau đó. | [Phạm vi và danh sách loại](../../../reports/backend_20261104/full_retry/HANDOFF.md) |

## Dự án 23 · các bước đã quan sát

1. Mở được “QA hồ sơ bản gốc 03-11” trên trang Dự án của tôi. Người dùng chọn `sample_floor.dxf`. Một POST tải tệp trả 201. File 127, vai trò KT, bản vẽ v1, 18.229 byte. [Ảnh trước khi tải](optimat-project23-before-upload-20261104.jpg)
2. Sửa mô tả ngay trên trang, lưu thông tin từ v2 lên v3, rời trang và mở lại. Mô tả SAMPLE và bản vẽ v1 vẫn hiện. [Ảnh trạng thái lưu](optimat-demo-profile-v3-20261104.jpg)
3. Tải nguyên bản, đối chiếu SHA-256 khớp mẫu. Xem trước gọi đúng `/api/projects/23/files/127/revisions/1/preview`. Số lần tải lên và phân tích giữ nguyên trong bước xem. [Ảnh xem CAD](optimat-demo-original-preview-v1-20261104.jpg)
4. Bấm Bắt đầu phân tích, POST trả 200 và chuyển tới lượt `34a7ed70-b4ae-464c-8e2d-b2b3f915887c`. Tổng số upload vẫn là một. Có một lượt phân tích của người dùng trước demo. **Giới hạn kiểm toán:** log, ảnh và bộ kiểm phía client phù hợp với việc dùng lại bản vẽ. Chưa có request body/biên nhận máy chủ độc lập gắn đồng thời UUID này với file 127/v1 và profile v3. [Ảnh sau Start](optimat-demo-analysis-started-20261104.jpg) · [Biên nhận](optimat_project23_demo_receipt_20261104.json)
5. Ảnh sau Start cho thấy vùng CAD bị bảng Khối lượng ép hẹp. 02 sửa bố cục theo chiều rộng còn lại sau menu. Khi module còn tối đa 950 px, công cụ, CAD, hướng dẫn và bảng có vị trí riêng. TypeScript, ESLint và build đạt. Build `oWnM3ZoBlYORzZeEWnOtz` đã được 01 đưa lên 3001. Kết quả thao tác sau khi thay build được ghi riêng dưới đây. [Biên nhận build](../../../reports/module_ui_qa_20261103/viewer_responsive_candidate_20261104.json) · [Diff](../../../reports/module_ui_qa_20261103/viewer_responsive_20261104.patch)

## Một công tác có thể tính độc lập để đối chiếu màn hình

Chọn **xây tường ngăn 110 mm**. Mẫu có một đoạn giữa hai mặt trong của tường bao. Đây là phép tính đối chứng từ hồ sơ SAMPLE, trước các khoản trừ, nếu có. Bảng dưới không thay cho kết quả giao diện.

| Số đoạn | Dài | Dày | Cao | Diện tích một mặt | Thể tích hình học trước khoản trừ khác |
|---:|---:|---:|---:|---:|---:|
| 1 | 4,56 m | 0,110 m | 3,30 m (giả thiết QA) | 4,56 × 3,30 = 15,048 m² | 15,048 × 0,110 = 1,65528 m³ |

Chiều dài từ hai đầu đoạn ở x = 220 và 4.780 mm. Hai nét tường cách nhau 110 mm. D1 và S1 trong mẫu đặt ở tường bao. Chiều cao 3,30 m đến từ bộ đáp án build. Ghi chú CAD nêu AAC, đáp án mẫu dùng mã AAC01. Đây là hai nguồn để Claude kiểm lời tư vấn. Số viên/block, vữa chuyên dụng, hao hụt, quy cách mua, nhà cung cấp và giá cần nguồn riêng. Chỉ ghi “AI đề xuất” khi truy được câu trả lời thực cho đúng công tác. [Mã sinh mẫu](../../../scripts/make_sample_dxf.py) · [Giả thiết chiều cao](../../../data/ground_truth/index.csv) · [Đáp án nhóm tường](../../../data/ground_truth/walls.csv)

**Đối chiếu trên trình duyệt.** Ảnh sau sửa ở kích thước từng lỗi cho thấy thanh công cụ nằm phía trên và CAD chiếm chiều ngang còn lại sau menu. Trên màn xác nhận, 01 đặt giả thiết SAMPLE một tầng cao 3,30 m, bổ sung hai lỗ mở từ bộ đáp án. Giao diện hiển thị 5 đoạn tường, 2 lỗ mở. Tường ngăn dài 4,56 m, diện tích 15,05 m², khớp phép tính làm tròn ở trên. Tường bao dài 33,12 m, khấu trừ 3,66 m², còn 105,64 m². Tổng giao diện 120,68 m² tính trước khi làm tròn từng nhóm. Ảnh là màn trước khi lưu bản kiểm, không chứng minh phản hồi máy chủ hoặc đầu ra AI. [Trước sửa 892 px](optimat-viewer-before-892x857.jpg) · [Sau sửa 892 px](optimat-viewer-after-892x857.jpg) · [Số đo trên màn xác nhận](optimat-sample-review-inputs-20261104.jpg)

## Chứng từ mua và mẫu bàn giao của 04/16

Phiên 16 đã đối chiếu với 04 và bàn giao workbook sáu sheet, giữ 63 dòng giá tham khảo và 22 liên kết Maps. Bốn PDF xi măng chứng minh nguồn lịch sử; 59 dòng CSV còn chờ PDF gốc. Hai bảng trống mới dành cho đối chiếu đơn mua với phiên bản thiết kế/vật liệu và ghi phí giao, bơm, dịch vụ đúng đơn hoặc chuyến. Phiên 16 đã kiểm lại công thức, liên kết, ô lỗi và ảnh render. Excel native và nhập vào ứng dụng còn chờ kiểm. Không có dòng nào được nâng thành báo giá mua. [Workbook bàn giao, checklist ở Hướng dẫn A41:B45](Bao_gia_MVP_dieu_kien_04_20261104.xlsx)

Để mở một ca giá mua thật, chủ đồ án cần cung cấp một lần các dữ liệu sau khi có:

1. Địa chỉ/tọa độ, tỉnh, ngày đặt và ngày giao, hạn chế xe và bốc dỡ.
2. Một dòng bê tông và một nhóm tường đã kiểm, kèm lượng mua, quy cách và phiên bản.
3. Chứng từ nhà bán, bậc số lượng hoặc đơn tối thiểu, hiệu lực tại ngày đặt, VAT và giao đúng địa chỉ.
4. Thời gian cung ứng và cách tính từng khoản giao, bơm, bốc dỡ, chờ; ghi khoản đã gồm trong giá.
5. Bê tông đúng mác và cách cấp. Tường đúng cặp gạch/vữa. Với VU02 cần xi măng và cát CA02 theo cấp phối. Để trống điều kiện nhà bán chưa xác nhận.

## Yêu cầu review độc lập

**Phản hồi của 00 sau review Claude.** [Bản review gốc, giữ nguyên](REVIEW_CLAUDE_20261104.md). Các cập nhật dưới đây bổ sung bằng chứng phát sinh sau mốc đọc của Claude.

| Phát hiện | Kết quả đối chiếu |
|---|---|
| Build và upload | Có biên nhận triển khai lúc 14:42:39, build khớp, có hash HTML/CSS đang phục vụ. Đã đưa vào gói các ảnh trước/sau và trích nguyên các dòng access log cho upload 201, preview 200, Start 200. Biên nhận candidate vẫn giữ nguyên. [Biên nhận triển khai](viewer_deploy_receipt.json) · [Trích log](project23_access_excerpt.log) |
| Kết quả 26 trên dự án 23 | Sau mốc biên nhận ban đầu ghi `quantity_confirmation_performed: false`, 01 xác nhận đầu vào mặt bằng SAMPLE rồi bấm tính một lần tại /phan-tho. UI báo lưu kết quả 26 lúc 14:56:32 ngày 04/11. Bảng có 12 dòng, 2 đủ dữ liệu, 10 cần bổ sung, 12 chưa được đánh đã kiểm. Bản ghi lượng mới chưa bổ sung được provenance còn thiếu của lần Start trước đó. [Ảnh màn Kiểm tra công tác](optimat-sample-work-detail-20261104.jpg) |
| W5: chiều dày nào đi vào công tác? | 15,048 m² khớp diện tích hình học. **1,65528 m³** là phép nhân theo bề dày danh nghĩa 0,110 m. **1,5048 m³**, hiển thị **1,505 m³**, là công tác phần thô 01 đọc trên UI: 1 × 4,56 × 3,30 × 0,100 cho lõi cấu tạo W-AAC01-100, lỗ mở của W5 bằng 0. Hai giá trị trả lời hai câu hỏi khác nhau. Oracle walls.csv so diện tích, không có cột thể tích. Cần xác minh cấu tạo lõi theo thiết kế, chiều cao thực, trừ dầm và truy vị trí W5 trước khi dùng để mua. |
| Tư vấn W5 | Theo thao tác của 01, màn /phan-tho chưa có nút tư vấn riêng W5, hai lối sang Chọn vật liệu và Tối ưu bị chặn khi còn chưa kiểm. Gợi ý có điều kiện của 00 là đối chiếu block AAC có lõi 100 mm và vữa/keo tương thích với hồ sơ hệ tường. Chưa có phản hồi OpenAI hay lượng đặt mua trên dự án này. |
| QA và tái hiện | 19 skip trong full gồm 15 PostgreSQL cũ, 3 DB opt-in và 1 symlink Windows. Các kiểm DB cho revision không chạy trong lượt full này. material_advisor.py còn untracked khi kiểm lại, hash 463E8F88…D300210E khớp replay. Đã kèm bản mã đúng hash để review; lịch sử Git vẫn là việc mở. [Mã trợ lý tại lúc đóng gói](material_advisor_463e8f88.py.txt) |
| Các giới hạn còn nguyên | Lượt OpenAI thật thuộc VN002. Chưa có giá giao cho AAC01 hay đủ mẫu số ACTUAL. Nét block S1 dài 900 mm khác chiều rộng giả thiết QA 1.200 mm. 01 đã bổ sung lỗ theo nguồn QA; S1 nằm trên tường bao, không khấu trừ W5. Với viewer mới, sau đổi kích thước còn trường hợp cần bấm Vừa khung để chọn đúng nét. |

00 đã mở và kiểm ảnh W5 mới sau khi 01 dùng “Tải phiên hiện tại”. Ảnh thấy công thức 1,505 m³, nguồn hình học A và chiều cao C, chưa có vị trí liên kết bản vẽ, 10 dòng còn thiếu, các nút chuyển bước bị khóa. Dòng W5 vẫn ghi “Cần bổ sung: Không” dù còn giới hạn bằng chứng. Claude có thể kiểm xem người dùng có phân biệt được “đủ đầu vào để tính” với “đủ căn cứ để duyệt” trên màn này hay không. [Ảnh chi tiết W5 đã đối chiếu](optimat-w5-detail-verified-20261104-v2.jpg)

- Đối chiếu từng kích thước và khoản trừ với cấu kiện, tầng, đơn vị, nguồn và phiên bản. Khi một phần chưa có số, kiểm cả lượng đã biết lẫn lý do thiếu qua giao diện, API, Excel và dữ liệu tư vấn.
- Kiểm lại ở kích thước từng gặp lỗi với menu mở. Thử Vừa khung, giữ mặt bằng khi đổi bố cục và mở bảng Kiểm tra công tác và khối lượng. Ghi ảnh, viewport CSS, build và đúng lượt phân tích.
- Truy vết một dòng từ kích thước đến lượng lắp đặt, định mức và lượng mua. Khi chỉ có chỉ định thiết kế, giá lịch sử hay giá dự đoán, kiểm cách hệ thống ghi nguồn và chặn kết luận mua. Kiểm AI không gán lượng gộp cho các dòng chưa xác nhận.
- Đối chiếu mục tiêu độc lập về độ phủ, sai số, báo giá ACTUAL, số nhà cung cấp và nhất quán làm tròn với mẫu số đủ điều kiện. Tách những ca không tính được. Mỗi phát hiện cần mức ảnh hưởng, tệp/dòng hoặc bước tái hiện, kết quả thực, kết quả mong đợi và bằng chứng còn thiếu.
- Có thể bắt đầu bằng các tài liệu liên kết và biên nhận. Bảo toàn dự án 23 cùng bản gốc. Hồ sơ Tân Bình không được phép dùng cho lượt demo.

## Bổ sung sau bàn giao · VN002

Theo bàn giao của 01, một số dòng vật tư tổng hợp VN002 có 21 hoặc 22 lý do thiếu. Trường MaterialFact.missing chỉ nhận tối đa 12 mục nên từ chối dữ liệu trước bước tư vấn. 04 đang sửa điều kiện nhận dữ liệu, bổ sung kiểm thử giữ đủ lý do và chỉnh cách báo thiếu giá trên giao diện phương án. 12 rà soát ở chế độ chỉ đọc. Chờ đối chiếu diff, hash và kết quả kiểm thử với đúng dòng VN002. Kiểm backend, kiểm giao diện và chạy tư vấn thực tế là ba kết quả cần ghi riêng. Tình trạng này chưa được tái hiện bởi 00.

## Khả năng tái lập AI tại bản trước sửa của 04

### Kết quả mới của 04 và QA độc lập của 15

Trong lần xử lý VN002 mới, 04 báo cáo đã đọc hai DXF thành 61 công tác và 8 dòng vật tư, chưa có công tác nào được đánh đã kiểm. Đây là lần khác với ca cũ 52/7. Có một lần gọi OpenAI mới cho VN002 qua hàm sản phẩm. Phản hồi tám dòng bị bộ kiểm từ chối vì trường việc cần kiểm mang kiểu chuỗi. Sau khi chuẩn hóa một câu thành danh sách một phần tử, 04 phát lại nguyên phản hồi và nhận đủ tám dòng. Chỉ dòng dây buộc có gợi ý TH10, chưa có báo giá mua. Chưa phải demo W5 hoặc nghiệm thu giao diện.

15 đã kiểm từng phần tử độc lập trên hai dòng. Với **m5 – cốt thép**, 21 lý do ở nguồn + 1 lý do phạm vi thành 22, giữ đủ 22 khi lập dữ kiện tư vấn. Với **m6 – dây thép buộc TH10**, 20 + 1 thành 21, giữ đủ 21. Hai danh sách giữ đúng nguyên văn và thứ tự trước khi bộ tư vấn thêm lần lượt 4 và 3 lý do khác. Mốc này xác minh nguồn → ngữ cảnh → dữ kiện. Log lần gọi thật chỉ lưu hash của request. [Đối chiếu QA](../qa_workflow_15/VN002_MISSING_REVIEW.md) · [Biên nhận từng phần tử](../qa_workflow_15/VN002_MISSING_RECEIPT.json)

15 đã kiểm tiếp nội dung **user message** do đường tư vấn thực tạo ra qua mock transport sau sửa. Cả 26/26 và 24/24 mục ở dữ kiện có mặt nguyên văn, đúng thứ tự trong payload. Hash của phần user message khớp biên nhận lần live, gồm cả lý do thứ 22/21. System prompt đã thay đổi. Không suy ra toàn bộ request lịch sử giống hệt. Bộ kiểm tập trung của 04 ghi 34 passed. [Đối chiếu bản sửa và capture mới](../../../reports/demo_0511/vn002_drawings_to_proposal/verification.json)

01 và 12 đã đối chiếu bốn tệp AI/test chưa được Git theo dõi và phần gắn router trong main.py chưa commit. Danh mục phụ thuộc ghi nhận 22 tệp Python, 13 CSV, cấu hình và bằng chứng phát lại. Cần đối chiếu cả bản phát hành frontend. Phiên bản thư viện chưa khóa và chưa có lần dựng trên máy sạch. Hash 463E8F88…D300210E chỉ nhận diện bản trước sửa. Lượt OpenAI VN002 có HTTP 200 nhưng bộ kiểm cũ từ chối phản hồi; 7 dòng được nhận ở lần phát lại riêng. [Biên bản kiểm tra](../row_assistant_12/REPRO_AUDIT_20261104.md) · [Danh mục và hash](../row_assistant_12/REPRO_MANIFEST_20261104.json)
