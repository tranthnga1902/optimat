# Rà giao diện OptiMat AI — phiên 17

Ngày 03/11/2026. Theo yêu cầu người dùng: lề thoáng, bảng kiểu Excel, kẻ dọc mờ giữa cột, STT nhỏ; AI hỗ trợ là một cửa sổ chat. Đây là lượt kiểm bố cục, không nghiệm thu công thức, dữ liệu giá hoặc quyền hồ sơ thật.

## Cách kiểm và giới hạn

- Rà source các route và khung Shell/ProjectBar/Sheet. Mở tab Chrome riêng tại `http://127.0.0.1:3000`, phiên đăng nhập hiện có; không upload, chạy phân tích, gửi AI, sửa DB hoặc đổi dự án.
- Đã đọc DOM/layout của 20 route ở viewport 2048 px và 18 route ở 390×844 px. Chỉ đọc các trạng thái sẵn có; một số bảng đang tải ở thời điểm lấy mẫu. Không coi bảng chưa xuất hiện là lỗi mất dữ liệu hoặc kiểm dữ liệu hoàn tất.
- Đã xem ảnh màn hình trang Dự án của tôi và Kiểm soát dữ liệu ở desktop. Hai ảnh trung gian khác còn ở trạng thái kiểm tra đăng nhập, không dùng làm bằng chứng trang đã tải xong. Chưa lưu ảnh để làm gói QA.
- Kết nối Chrome mất khi chờ `/co-so-du-lieu` ở mobile. `/co-so-du-lieu` và `/dang-nhap` chưa hoàn tất lượt mobile. Đã thử trả viewport mặc định nhưng kết nối không còn; cần kiểm lại kích thước khi mở tiếp.
- Chưa kiểm mọi tab con, modal, trang phân trang, trạng thái 401/403/500, hồ sơ rỗng và CAD preview. Không có bằng chứng E2E upload–lưu–mở lại–phân tích.

## Các vấn đề cần xử lý

| Ưu tiên | Phát hiện | Bằng chứng | Vùng sửa đề xuất / chủ phối hợp |
|---|---|---|---|
| P1 | Ba trang tràn ngang toàn trang ở 390 px | `document.documentElement.scrollWidth > innerWidth` tại `/du-an-cua-toi`, `/phan-tho`, `/dieu-chinh`; desktop không tràn trong mẫu đã xem | 02 rà `ProjectBar.tsx`, vùng nút/form và host bảng; giới hạn overflow trong bảng, không giấu toàn trang bằng overflow-x:hidden |
| P1 | Dự án của tôi chưa đáp ứng hồ sơ trước phân tích | Trang thực vẫn chỉ có mô tả và link “Tiếp: bóc tách bản vẽ”; `ProjectBar` vẫn dùng dialog và chuyển tới `/do-boc` khi mở/tạo | 02 host/form inline; 06 API user/tệp/phiên bản; 17 đã cung cấp component riêng |
| P2 | Bảng Excel thiếu kẻ dọc mờ ở các trang dùng Sheet | DOM mẫu bảng đầu `/phan-tho`, bảng Sheet tại `/dieu-chinh`, `/gia`, `/danh-muc`: ô đầu có `borderRightStyle: none`. Source `globals.css` có `.xl th,.xl td { border:0; border-bottom:... }` | 02 sở hữu Sheet/global: bổ sung kẻ cột scoped, giữ focus/chọn ô; 17 đã làm riêng trong ProjectFilesPanel |
| P2 | Tên menu người dùng bị cắt, khó phân biệt đầy đủ | Ảnh desktop và AX: “Kiểm tra côn...”, “Vật liệu v...” do nhãn `.truncate`; title chỉ đặt khi menu collapsed trong Shell | 02 cân nhắc title cho nhãn đầy đủ khi expanded, hoặc cách bố trí badge không chiếm quá nhiều chỗ |
| P2 | AI hỗ trợ cần chuyển thành cửa sổ chat thống nhất theo yêu cầu mới | `/toi-uu/Proposal.tsx` đang nhúng `MaterialAdvisor`; cần chốt giao diện hội thoại riêng thay vì các hộp hỏi rời | 02/04/12 giữ logic; 17 đề xuất bố cục cửa sổ chat bên dưới |

Không gán nguyên nhân tràn ngang chỉ từ một phép đo; cần xác định phần tử vượt biên trước khi vá. Không sửa các tệp chung hoặc logic của chủ phiên khác trong lượt này.

## Ma trận trang đã mở

“Không thấy tràn” chỉ là kết quả mẫu bố cục đang hiển thị, không đồng nghĩa toàn bộ chức năng đã đạt.

| Route | Desktop 2048 px | Mobile 390 px |
|---|---|---|
| `/du-an-cua-toi` | Có lề 30 px; chưa có hồ sơ inline | Tràn ngang toàn trang |
| `/do-boc` | Khung canvas không dùng lề chung; có bảng hiện tại | Không thấy tràn ngang |
| `/phan-tho` | Có lề; Sheet 15 cột, STT khoảng 33 px | Tràn ngang toàn trang |
| `/dieu-chinh` | Có lề; bảng chính STT khoảng 38 px | Tràn ngang toàn trang |
| `/vat-lieu` | Có lề; bảng vật tư phần thô hiện tại | Không thấy tràn ngang, bảng nằm trong vùng cuộn |
| `/toi-uu` | Có phương án nháp và vùng AI hiện tại | Không thấy tràn ngang |
| `/tiep-nhan` | Mở được form ban đầu; chưa upload | Không thấy tràn ngang ở form ban đầu |
| `/mapping` | Mở được trạng thái sẵn có; chưa gửi hồ sơ | Không thấy tràn ngang ở trạng thái sẵn có |
| `/tong-quan` | Mở được trang; dữ liệu đang tải trong mẫu DOM | Không thấy tràn ngang trong mẫu DOM |
| `/kiem-soat` | Ảnh thực có kết quả và danh sách cảnh báo | Không thấy tràn ngang trong mẫu DOM, chưa kiểm hết danh sách |
| `/du-an` | Mở được bảng 22 dòng dự án hiện tại | Không thấy tràn ngang toàn trang |
| `/nguoi-dung` | Mở được bảng 3 dòng hiện tại | Không thấy tràn ngang toàn trang |
| `/nhan-dien` | Mở được trang 112 ký hiệu, chưa thao tác thử CAD | Không thấy tràn ngang ở trạng thái ban đầu |
| `/quy-tac` | Mở được bảng 6 dòng hiện tại | Không thấy tràn ngang toàn trang |
| `/danh-muc` | Mở được trang; bảng chưa có trong mẫu đầu | Bảng 22 dòng; STT khoảng 33 px, thiếu kẻ dọc |
| `/dai-ly` | Mở được trang; chưa thao tác tìm kiếm/bản đồ | Không thấy tràn ngang ở trạng thái ban đầu |
| `/gia` | Bảng 13 dòng, 10 cột; STT khoảng 30 px | Không thấy tràn ngang toàn trang; thiếu kẻ dọc |
| `/mo-hinh` | Mở được bảng chỉ số và cấu hình | Không thấy tràn ngang toàn trang |
| `/co-so-du-lieu` | Mở được 5 bảng nhóm dữ liệu | Chưa hoàn tất do mất kết nối Chrome |
| `/dang-nhap` | Mở được trạng thái “Đã đăng nhập”; không đăng xuất | Chưa kiểm |

`/` là route chuyển hướng, không phải màn độc lập. Trang lỗi/404 được rà source nhưng chưa kích hoạt lỗi thật trong trình duyệt.

## Thiết kế AI hỗ trợ theo yêu cầu mới

- Một cửa sổ chat có tiêu đề “AI hỗ trợ”, hiển thị tên dự án và bản kiểm/phương án đang dùng. Có nút thu gọn/đóng; mở lại giữ hội thoại thuộc đúng dự án và phiên bản.
- Desktop đặt bên phải trong phạm vi màn hình, chừa lề 16–24 px; mobile dùng chiều rộng khả dụng với lề 12–16 px. Ô nhập và nút gửi luôn nhìn thấy, lịch sử hội thoại cuộn riêng.
- Người dùng hỏi và AI trả lời trong cùng lịch sử; có trạng thái đang trả lời, lỗi và thử lại. Không gửi API chỉ vì mở cửa sổ.
- Căn cứ, phần thiếu và phương án đề xuất nằm trong tin nhắn; hành động áp dụng/xác nhận riêng, không tự thay thiết kế hay số lượng.
- Cần chuyển focus khi mở, trả focus khi đóng, hỗ trợ Escape, nhãn nút rõ và không dùng màu làm dấu hiệu duy nhất.

Đây là đặc tả trình bày để owner ghép; chưa có cửa sổ chat mới đang chạy hoặc bằng chứng gọi AI thật trong lượt này.

## Bàn giao ProjectFilesPanel

01 đã release đúng hai tệp `frontend/src/components/ProjectFilesPanel.tsx` và `ProjectFilesPanel.module.css`; 17 sole writer. Đã áp source, không sửa host/page/store/ProjectBar/router/backend.

- DTO `ProjectFileRevision` giữ snake_case: `project_id`, `file_id`, `revision_id`, `version`, `sha256`, `name`, `original_format`, `size_bytes`, `role`, `uploaded_at`; metadata legacy được để null. `analysis_status` nếu có phải là nhãn tiếng Việt do host cung cấp.
- Props controlled: `projectId`, `files`, `selectedRevisionIds`, `viewingRevisionId`, `preview`; slot `projectInfo`, `sourceContext`, `analysisContext`, `uploadControls`; callback `onView(file)`, `onDownload(file)`, `onSelectionChange(ids)`, `onStartAnalysis()`.
- `projectInfo` nhận form chung inline của 02. Component không tạo dialog, không fetch, không đọc/ghi store và không tự gọi phân tích.
- Chỉ hiện preview khi `revision_id` khớp phiên bản đang xem thuộc dự án hiện tại. Trạng thái loading/unsupported/forbidden/error được hiển thị riêng. Host phải kiểm request stale và quan hệ server; component không thay kiểm quyền.
- Chặn Start khi lựa chọn rỗng/stale/trùng, SHA không đúng 64 ký tự hex, version không phải số nguyên dương an toàn, thiếu role hoặc chỉ có THAM_KHAO. Host vẫn kiểm toàn bộ điều kiện backend.
- Bảng tái dùng Sheet, kẻ dọc mờ `--rule2`, STT width 1%/đệm ngang 6 px; card đệm 24 px desktop,16 px mobile. Vùng ngoài nhận lề Shell 30/16 px.
- Kiểm: ESLint riêng component exit0; TypeScript toàn frontend `tsc --noEmit --incremental false` exit0. Harness `node tmp/ui17/check.cjs optimat-ai/frontend/src/components/ProjectFilesPanel.tsx` exit0: preview đúng/sai revision, tách project, không autoanalysis, CTA chủ động, stale/incomplete/duplicate/ref-only/hash/version/role, callback mở đúng revision. Fixture chỉ trong test, không gửi API hoặc tạo dữ liệu demo.
- Chưa ghép host, chưa xem panel trong browser, chưa QA upload–persist–preview–analysis hoặc ACTUAL.

Hash SHA256 sau bàn giao:

| Tệp | SHA256 |
|---|---|
| ProjectFilesPanel.tsx | `34febe30c483781223a171937d30e9f6f95f67ea0458cdcd04ad05155070380c` |
| ProjectFilesPanel.module.css | `5b1b2a035f3a78f34877722f9cd3d87bab5dc7e22bf50b327888097937d1ca5f` |

Lần gửi trước bị bộ duyệt tự động dừng do hết hạn mức duyệt. Sau thông báo01 về hạn mức được khôi phục,17 đã trực tiếp kiểm công cụ usage: ordinaryUsageAllowed=true, usedPercent=4. Đã gửi thành công bàn giao props/paths/hash/check tới02 và01 qua công cụ nhắn cùng dự án. Theo01, giữ ổn định hai tệp component và không mở sửa các trang khác trong lượt tích hợp;02 ghép host inline,06 triển khai API/migration,01/15 sắp demo khi runtime đủ.
