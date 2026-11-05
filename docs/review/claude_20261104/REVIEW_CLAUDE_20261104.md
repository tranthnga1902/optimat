# Review độc lập · bàn giao 04/11/2026

Người review: Claude (Opus 5.5). Thời điểm: 04/11/2026, sau 14:41. Chỉ đọc biên bản, biên nhận và tính lại băm. Không chạy lại test. Không ghi gì vào dự án 23 hay DB.
Checkout lúc review: HEAD `a315602`, nhánh `phan-tho-quy-uoc-csdl-vat-lieu`, **326 đường dẫn bẩn hoặc chưa theo dõi**. Vì vậy không coi HEAD là bản demo.

## Kết luận

| Bước | Có thể trình diễn? | Căn cứ |
|---|---|---|
| Mở dự án → tải DXF → sửa hồ sơ v2→v3 → mở lại → tải nguyên bản → xem trước | **Có, với nhãn SAMPLE** | Biên nhận demo, SHA-256 tính lại khớp (mục 1) |
| Bắt đầu phân tích → màn hình đo bóc | **Có, chỉ để xem**. Không được nói lượt `34a7ed70…` chắc chắn đọc file 127/v1 và profile v3 | Thiếu biên nhận phía máy chủ (F2) |
| Người dùng kiểm khối lượng | **Chỉ với tường ngăn 110 của SAMPLE**, đối chiếu số tính tay. Chưa có căn cứ trên nhà thật | Mục 2, F4 |
| AI đề xuất vật liệu | **Không demo trên dự án 23**. Chỉ có thể kể lại lượt VN002 như một lượt kiểm logic | F5 |
| So giá, tối ưu, bảng mua | **Chặn**. Chưa có báo giá mua ACTUAL đủ điều kiện | F6 |

## 1. Những gì tôi xác minh lại được

- `data/sample/sample_floor.dxf` (đã commit, không sửa): 18.229 byte, SHA-256 `f88d3808…e721a0`. Bản tải về `Downloads/sample_floor (1).dxf` (14:28) có cùng băm. Khớp biên nhận.
- Tường ngăn 110 trong `scripts/make_sample_dxf.py`: hai nét ở y = 6000 và 6110, x từ 220 đến 4780. Vậy dài 4,56 m, dày 0,110 m. Chiều cao 3.300 mm có trong `data/ground_truth/index.csv` (split = build). `walls.csv` ghi 4,56 m / 15,05 m² / AAC01. `tests/test_takeoff.py:18,21` cũng kiểm các số này. Phép tính 4,56 × 3,30 = 15,048 m² và × 0,110 = 1,65528 m³ là đúng. Không có lỗ mở trên tường 110.
- Hồi quy backend (`reports/backend_20261104/full_retry/result.json`): 1.096 passed, 19 skipped, 15 deselected, exit 0, xong lúc 09:45 giờ VN. Manifest 263 tệp không đổi. Khớp bàn giao.
- `src/optimat/agent/material_advisor.py` hiện có SHA-256 `463E8F88…0210E`, đúng băm trong `replay_canonical.json`.
- Cổng 3001 đang phục vụ `static/chunks/240zypd2h7pof.css`. Chunk này chỉ có trong `.next-viewer-20261104`, không có trong `.next`. Vậy 3001 nhiều khả năng đang chạy build `oWnM3ZoBlYORzZeEWnOtz`.

## 2. Phát hiện

| # | Mức | Phát hiện | Tái hiện / vị trí | Kết quả thực | Mong đợi | Bằng chứng còn thiếu |
|---|---|---|---|---|---|---|
| F1 | Cao (độ tin của biên bản) | Bàn giao bước 5 viết “kết quả thao tác sau khi thay build được ghi riêng dưới đây”, nhưng không có phần đó. Biên nhận build ghi `"status": "candidate_verified_not_deployed"` và `"browserQA": "pending on the existing project 23 tab"`. Trong khi đó 3001 có vẻ đã chạy build mới (mục 1). | `reports/module_ui_qa_20261103/viewer_responsive_candidate_20261104.json` | Biên nhận cũ, bố cục chưa được kiểm trên trình duyệt | Một biên nhận deploy riêng: build id, giờ, viewport CSS, menu mở, Vừa khung, mở bảng Kiểm tra, có ảnh | Ảnh và viewport sau khi deploy; ghi chú cách đưa build lên 3001 |
| F2 | Cao (truy vết) | Lượt `34a7ed70…` chưa được gắn với file 127/v1 và profile v3 bằng dữ liệu phía máy chủ. Biên nhận chỉ có số đếm phía client, và `log` trỏ vào thư mục Temp ngoài kho. | `optimat_project23_demo_receipt_20261104.json` → `analysis`, `log` | Suy ra từ upload_count không đổi | Bản ghi analysis trên API/DB có `file_id`, `revision`, `profile_revision` | Phản hồi GET của lượt phân tích, hoặc dòng log đã chép vào kho |
| F3 | Trung bình | Bước 1 ghi “một POST tải tệp trả 201”, nhưng biên nhận không có trường nào cho POST đó. Biên nhận chỉ ghi `upload_count_before: 1` và “No new file upload by agent”. | Biên nhận demo | Không xác định được giờ và người tải | Ghi request id/giờ của POST 201, hoặc sửa câu chữ thành “file đã có sẵn” | Request/response của lần tải |
| F4 | Trung bình | `quantity_confirmation_performed: false`. Chưa ai đối chiếu số tường 110 trên màn hình với 4,56 m / 15,048 m² / 1,655 m³. Đây là bước rẻ nhất để chứng minh luồng kiểm khối lượng. | Mở `/do-boc?analysis=34a7ed70…`, tìm dòng tường 110 | Chưa có | Màn hình, API và Excel cùng ra 4,56 m, 15,05 m² (sai lệch ≤ 0,02 như test) | Ảnh, JSON API và ô Excel của cùng lượt phân tích |
| F5 | Cao (AI) | Lời tư vấn AI duy nhất có thật là lượt OpenAI VN002 lúc 23:11 ngày 03/11. Lượt này gọi thẳng hàm Python, không qua HTTP (“API trên cổng demo chưa có tuyến trợ lý toàn phần thô”). Các lượt sau chỉ phát lại. Trên dự án 23 chưa có POST trợ lý nào (`assistant_posts: 0`). Không có lời tư vấn nào cho AAC01 / tường 110. | `reports/demo_0511/live_advisor_vn002/KIEM_TRA.md` | AI chưa được kiểm qua giao diện | Một lượt qua UI → API cho đúng dòng tường 110, ghi nguồn AAC01 | Biên nhận UI/HTTP của lượt tư vấn |
| F6 | Chặn (giá/mua) | `price_model_16/READINESS.md` ghi “CHƯA ĐỦ dữ liệu ACTUAL”. Có 59 dòng công bố giá / 26 mã. AAC01 có trong danh sách nhưng đó là giá công bố, không phải báo giá giao hàng. Không có GN01/VU02. Còn thiếu chuỗi 6 tháng và ≥ 3 đại lý cho mỗi vật liệu. `load_prices` không lọc ACTUAL. | READINESS.md dòng 7, 18, 21, 35 | — | Báo giá ACTUAL cùng quy cách, VAT, ngày, địa bàn, lô và phí giao | Bộ CSV ACTUAL đã duyệt |
| F7 | Trung bình (tái lập) | `material_advisor.py` **chưa được git theo dõi** (`??`). Bản “mã chính” chỉ tồn tại trong cây làm việc. Các phiên khác có thể sửa hoặc xoá nó mà không để lại lịch sử. | `git status src/optimat/agent/material_advisor.py` | Băm hiện còn khớp | Commit, hoặc lưu bản sao cùng băm vào thư mục biên nhận | Commit hash |
| F8 | Trung bình (phạm vi hồi quy) | 19 test bị bỏ qua chính là các test DB cho hồ sơ/lịch sử: `test_project_documents_migration`, `test_project_files_db`, `test_project_document_roles_db`, `test_db` (13 ca, thiếu `OPTIMAT_TEST_DATABASE_URL`). Vì vậy hai bảng revision mới **chưa có hồi quy tự động trên DB**. Hồi quy chạy lúc 09:45, trước khi CSS đổi lúc 14:38 (CSS vốn ngoài phạm vi). | `reports/backend_20261104/full_retry/pytest_full.log` | — | Chạy riêng nhóm test DB trên DB thử nghiệm | Log của nhóm đó |
| F9 | Thấp (dữ liệu mẫu) | Đáp án dùng cửa sổ S1 rộng 1.200 mm (`index.csv`, `test_takeoff.py:5`), nhưng block S1 trong DXF chỉ là một nét dài 900 mm, giống D1. Không ảnh hưởng tường 110. Có ảnh hưởng nếu demo khoản trừ trên tường 220. | `scripts/make_sample_dxf.py`, khối `for name in ("D1", "S1")` | Hình học 900 ≠ đáp án 1.200 | Hoặc block có kích thước đúng, hoặc ghi rõ kích thước lấy từ bảng cửa | — |

## 2b. Đối chiếu tường 110 (bổ sung 04/11, sau F4)

**Không còn đọc lại được lượt `34a7ed70…`.** `POST /api/projects/{id}/analysis` (`src/optimat/api/project_analysis.py`) chỉ tính rồi stream kết quả, không lưu vào DB và không có route GET. Token chỉ dùng một lần và bị xoá khỏi `sessionStorage` (`Review.tsx:427-429`). Vì vậy số trên màn hình của lượt đó chỉ tồn tại trong tab đã đóng.

Dòng cuối stream có `analysis_receipt` do máy chủ sinh. Receipt chứa `client_analysis_id`, `files`, `profile_version`, `request_sha256` và `response_sha256`, tức đúng chứng cứ F2 còn thiếu. Nhưng receipt này không được lưu lại. Đề nghị: từ nay chép receipt này vào biên nhận demo.

**Chạy offline đúng chuỗi hàm của route** (`read_drawing` → `takeoff_plans(h = 3300, openings = None)` → `view_payload`) trên `data/sample/sample_floor.dxf`. Băm khớp file 127. Python `.venv`, không DB, không gọi máy chủ:

| Đại lượng | Tính tay | Backend | Khớp |
|---|---:|---:|---|
| Dài | 4,56 m | 4,56 m | ✓ |
| Diện tích gộp | 15,048 m² | 15,05 m² | ✓ (làm tròn 2 chữ số) |
| Lỗ mở | 0 | 0,0 m² | ✓ |
| Diện tích thực | 15,048 m² | 15,05 m² | ✓ |
| Thể tích | 1,65528 m³ | không có trong `groups` (15,05 × 0,110 = 1,6555) | — |
| Vật liệu thiết kế | AAC01 (ghi chú CAD, đáp án) | `AAC01`, độ tin 1,0 | ✓ |
| Phương án tường | — | `W-AAC01-100` | cần xem lại: tường 110 trên bản vẽ được gán phương án 100 mm |

Giới hạn: chiều cao 3.300 lấy từ `index.csv`, không phải hồ sơ v3 trong DB. Lượt chạy dùng `openings = None`, nên tường 220 ra lỗ mở = 0 (109,3 m² thay vì 105,64). Tường 110 không bị ảnh hưởng. Đây là cùng mã và cùng tệp, **không phải** ảnh màn hình của lượt `34a7ed70`.

## 2c. Lượt phân tích mới trên giao diện (04/11, sau 15:00)

Biên nhận: [optimat_project23_wall110_receipt_20261104.json](optimat_project23_wall110_receipt_20261104.json) · Ảnh: [optimat-project23-wall110-h330-20261104.jpg](optimat-project23-wall110-h330-20261104.jpg)

Lượt chạy: dự án 23, hồ sơ v3, file 127/v1, bấm Bắt đầu phân tích. Token phía client `88307123-58b0-4fb6-a7d3-ba7c11935c2c`. Web 3001 chạy build `oWnM3ZoBlYORzZeEWnOtz`, viewport CSS 849×833. Request và response được bắt bằng bộ chặn fetch trong trang. Không bấm Xác nhận, không sửa hồ sơ hay tệp.

**Kết quả tường 110 (W5):** màn hình và API đều ra 4,56 m, dày 110, AAC01, `W-AAC01-100`. Sau khi nhập tạm chiều cao 3,30 m trên trang, diện tích ra **15,05 m²**, khớp số tính tay. Tổng diện tích tường thực 124,34 m², chưa trừ cửa.

**Phát hiện mới:**

| # | Mức | Phát hiện | Thực tế | Mong đợi |
|---|---|---|---|---|
| F10 | Cao | **Bản đang chạy không gửi và không trả biên nhận lượt phân tích.** Request body không có `client_analysis_id`, dù `Review.tsx` trong checkout có gửi. Stream kết thúc ở `complete`, không có dòng `receipt`, dù `project_analysis.py` trong checkout có sinh. Vậy API 8001 và/hoặc frontend 3001 cũ hơn mã nguồn trong checkout. Token trong URL chỉ tồn tại ở client. | Không thể gắn UUID lượt với file/profile ở phía máy chủ (F2 không khắc phục được trên bản đang chạy) | Deploy API và frontend có receipt, rồi chạy lại |
| F11 | Trung bình | **Hồ sơ v3 không có chiều cao tầng.** Vì vậy `height_mm = null` và `groups = []`. Đây là hành vi đúng theo B7. Nhưng giao diện hiện ô chiều cao là `0.00` và mỗi tường là `0,00 m²`, tức hiển thị giá trị thiếu như thể bằng 0. Người dùng có thể hiểu nhầm là diện tích bằng 0. | `0,00 m²` | Ô trống hoặc “chưa tính”, kèm lý do. Nguồn: `Review.tsx:654` dùng `(S.height_mm/1000).toFixed(2)` khi `height_mm` null |
| F12 | Trung bình | **Cảnh báo và danh sách lỗ mở mâu thuẫn nhau.** Cảnh báo ghi D1, S1 “vẫn có trong danh sách để nhập chiều cao”. Nhưng `openings = []`, tab Lỗ mở hiện 0, và trang không có chỗ để nhập kích thước cửa. Tường 220 vì thế ra 109,28 m² thay vì 105,64 m². | Không trừ được cửa trên giao diện | Hiện D1, S1 với kích thước trống để nhập, hoặc sửa câu cảnh báo |
| F13 | Thấp | Viewport 849 px: danh sách tường nằm dưới CAD, phải cuộn trang mới thấy. Không bị đè, chỉ ghi nhận. | — | — |

**Cập nhật F11/F12 (04/11, sau review):** đã sửa trong mã nguồn, **chưa build/deploy** lên 3001/8001.

- `drawing/takeoff.py`: block cửa không có kích thước vẫn vào `openings`. Nó được gắn với tường gần nhất, để rộng và cao trống, và không bị trừ diện tích. Câu cảnh báo nay ghi “vẫn có trong danh sách lỗ mở để nhập kích thước”.
- `schemas.OpeningItem.width_mm` được để trống (Optional). `ReviewOpening.w` khi xác nhận vẫn bắt buộc. Frontend chỉ gửi những lỗ mở đã có rộng.
- Frontend do-boc: ô chiều cao để trống thay vì `0.00`; diện tích tường hiện “chưa tính”; lỗ mở có ô “nhập rộng” và hiện “chưa trừ”.
- Kiểm tra: thêm test `test_block_openings_without_size_listed_not_subtracted`. pytest tập trung (drawing/rough/review/api): 707 đạt. eslint `do-boc` và `tsc --noEmit` sạch.

**F10 vẫn mở:** API và web đang chạy cũ hơn mã nguồn trong checkout. Bản đang chạy không gửi `client_analysis_id` và không trả receipt.

**Cập nhật F1/F7:** thư mục này đã có thêm `viewer_deploy_receipt.json` do phiên khác tạo, ghi `status: verified`, build `oWnM3…`, 14:42. Cũng có `material_advisor_463e8f88.py.txt`, băm khớp `463E8F88…`. Tôi chỉ kiểm băm và trường status, chưa kiểm phần còn lại.

## 3. Đối chiếu mục tiêu độc lập

Hiện chưa tính được độ phủ, sai số, số báo giá ACTUAL, số nhà cung cấp hay độ nhất quán làm tròn. Lý do: mẫu số đủ điều kiện bằng 0. Chỉ có 1 bản vẽ SAMPLE (split = build), chưa có bản test nào, và chưa có hồ sơ thật do người kiểm độc lập xác nhận (mục tiêu là 12 hồ sơ build + 8 hồ sơ test). Không được dùng 20 dự án tổng hợp làm mẫu số. Như bàn giao đã nêu, chưa được công bố 80% hay sai số.

## 4. Thứ tự đề nghị trước khi demo

1. F4: chụp màn hình dòng tường 110 cùng API và Excel của lượt `34a7ed70…`. Không tốn tải mới và không đụng bản gốc.
2. F1: viết biên nhận deploy và kiểm bố cục với menu mở.
3. F2/F3: chép log máy chủ của lượt phân tích và lần POST vào kho.
4. F7: commit `material_advisor.py`.
5. Chỉ demo AI và giá khi xong F5 và F6.

Không kiểm: chưa xem nội dung 4 ảnh JPG, chưa mở giao diện, chưa đọc G8 / CHAIN_ACCEPTANCE_GAPS / C01 từng dòng, chưa kiểm hồ sơ Office/PDF.
