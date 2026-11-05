# Kế hoạch trợ lý hỏi đáp theo dòng công tác

> THAY PHẠM VI: chỉ đạo mới nhất 03/11/2026 là trợ lý vật liệu TOÀN PHẦN THÔ. Xem MATERIAL_CONTRACT.md và MATERIAL_CASES.md. Phần hỏi dòng bên dưới là lịch sử chuẩn bị, không phải điều kiện demo. Đã mở staging tmp/row_assistant_12, chưa apply source/live vì freeze/full 225.

Ngày 03/11/2026 — phiên 12. Trạng thái: chuẩn bị chỉ đọc theo điều phối 01; chưa triển khai, chưa chạy mock/live, chưa nghiệm thu UI. Chỉ ghi PLAN.md và CASES.md trong thư mục này. Không sửa source/test/API/UI/DB; không gọi OpenAI, không mở full, không đọc .env/khóa và không vượt gate upload đã từ chối.

## 1. Mục tiêu và bằng chứng hiện trạng

Nút **Hỏi về dòng này** trong chi tiết công tác: trả lời tiếng Việt về công thức, khoản trừ, dữ liệu thiếu và bước kiểm tra. Giữ dòng gốc để đối chiếu; trả lời không thay đổi số, trạng thái kiểm hay lựa chọn vật tư.

Đã đọc: docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md, docs/PHAN_VAI_CAC_PHIEN.md; agent/llm.py, orchestrator.py, pipeline.py; api/main.py, auth.py; db/models.py; frontend/src/lib/{work-review,review-session,projects}.ts và do-boc/WorkReview.tsx. Đường dẫn Python tương đối với src/optimat/.

- llm.chat_openai dùng requests + config.OPENAI_URL (Chat Completions), OPENAI_MODEL, timeout; khóa chỉ lấy từ môi trường backend. Tái dùng transport, không đổi model, SDK hoặc migration API vì tính năng này.
- orchestrator.run_agent có công cụ chạy lại đo bóc/tối ưu, không phù hợp cho giải thích chỉ đọc một dòng. Chỉ tái dùng transport và mẫu xử lý lỗi; không gọi agent có công cụ từ nút hỏi.
- /api/agent/run nhận tệp, chạy toàn luồng; chưa nhận binding projectUid/drawingId/reviewId/row. Route này không phải bằng chứng kiểm quyền dòng.
- WorkVersion = projectUid + drawingId + file + reviewId. WorkSnapshot có request/result/at/materialRevision; WorkReceipt có checked/partial/confirmed. sameWorkVersion là kiểm tra client, không phải xác thực máy chủ.
- WorkReview chọn dòng bằng chỉ số gốc trong snapshot.result.works. Không dùng vị trí sau lọc làm định danh. Hiện chưa thấy rowId ổn định trong contract đã đọc.
- Dự án đang mở/bản kiểm được lưu localStorage. require_user trả None khi không có DATABASE_URL. Không được dùng điều đó để tuyên bố đã kiểm quyền dự án cục bộ.
- DB có projects.user_id, project_files.project_id và takeoff_results.project_id/file_id/result. Chưa chứng minh chúng lưu ánh xạ WorkVersion của UI hoặc revision hiện hành; cần thiết kế binding trước khi release.

## 2. Phân biệt hai mức xác minh

**Mức hồ sơ có server state:** backend kiểm người dùng, quyền trên project, file thuộc project, snapshot thuộc file và revision, dòng thuộc snapshot. Dùng predicate ownership trong truy vấn, không chỉ kiểm user đã đăng nhập. Backend tự lấy dòng; không tin dòng client gửi. ID không tồn tại/không thuộc quyền trả lỗi chung, không tiết lộ tên hay sự tồn tại hồ sơ khác. Mọi kiểm tra phải diễn ra trước outbound OpenAI.

**Mức dự án chỉ ở trình duyệt:** projectUid/reviewId và hash do client tự khai chỉ chứng minh tính nhất quán của payload, không chứng minh sở hữu, nguồn bản vẽ hay bản mới nhất. Echo các ID, ký lại hash client hoặc gắn nhãn verified không khắc phục được điều này.

Đề xuất mặc định: chưa có server binding thì khóa hỏi theo hồ sơ, vẫn xem dòng gốc và thông báo “Bản kiểm này chưa được liên kết với phiên trên máy chủ”. Không lặng lẽ gọi endpoint công khai bằng khóa backend.

Phương án demo cục bộ nếu 01/00 chọn: server phát phiên demo có phạm vi, cookie HttpOnly/token không chứa khóa OpenAI, hết hạn và giới hạn lượt; server giữ snapshot demo tối thiểu cùng revision và dòng, chỉ cho phiên đó truy cập. Snapshot phải là fixture SYNTHETIC/SAMPLE được phép. Có thể không cần DB, nhưng phải có server state; restart làm phiên hết hiệu lực, không tuyên bố bền vững. Nếu đăng ký snapshot do trình duyệt cung cấp, nhãn là “Nội dung người dùng cung cấp”, không phải “đã đối chiếu bản vẽ”. Không tự mở cổng đăng ký hồ sơ thật để né quyền upload.

Máy chủ không tự biết người dùng đang mở snapshot localStorage mới nào. Server chỉ phát hiện stale so với revision server đang quản lý; UI phải loại phản hồi nếu snapshot đang xem đã đổi. Công bố giới hạn này thay vì nói đã kiểm stale toàn cục.

## 3. Hợp đồng đề xuất để 01/02 chốt

Tên route dưới đây là đề xuất, chưa có mã: POST /api/assistant/row.

- Request: question; projectUid, drawingId, reviewId; định danh serverSnapshotId/revision do server phát; rowIndex gốc và rowFingerprint do server tính từ snapshot; requestId. file chỉ là nhãn hiển thị, không là đường dẫn để mở tệp.
- project_id/takeoff_id/file_id: nếu dùng DB phải được resolve và đối chiếu server-side; không coi projectUid là project_id hoặc tự ép chuỗi sang số.
- Có scope máy chủ: mặt bằng được chọn, phạm vi còn thiếu, xác nhận phạm vi, receipt partial và trạng thái kiểm nếu được lưu. confirmed/checked/partial do client khai không phải phê duyệt server. Thiếu trạng thái thì ghi chưa xác minh.
- RowFingerprint phục vụ so phiên bản, không thay kiểm quyền. Bind token/lookup với principal hoặc phiên demo + project + drawing + snapshot + revision; không dùng hash công khai làm quyền truy cập.
- Response: requestId + binding do backend xác định + verificationMode + facts + explanation + generalGuidance + missing + checks + warnings. Không có patch/update/actions/tool_calls.
- facts là dữ liệu dựng từ row allowlist ở backend; model không được viết lại facts hoặc tự cấp nguồn. Câu giải thích riêng hồ sơ phải tham chiếu field ID hợp lệ; backend kiểm reference.
- Hợp đồng cần khóa rõ revision khi công thức/evidence/source/status/partial đổi, kể cả khi quantity giữ nguyên. materialRevision riêng không mặc nhiên đại diện revision đo bóc.

## 4. Context tối thiểu và ranh giới nội dung

Backend chỉ chọn một dòng: code/name/element/plan/unit/quantity/status/basis/formula, dimensions cần thiết và field_sources, inputs/evidence/missing; dữ liệu khoản trừ/raw-net hiện có của dòng. Thêm scope/partial và trạng thái xác minh ở mức tối thiểu. Cắt theo ngân sách kích thước đã định; nếu phải cắt mất căn cứ thì báo context thiếu, không kết luận chắc chắn.

Không gửi nguyên CAD/PDF/request/result của nhà, ảnh bản vẽ, địa chỉ, tên chủ nhà, khóa, cookie, đường dẫn lưu tệp, bảng giá hoặc lịch sử dự án khác. IDs kiểm quyền giữ ở backend; OpenAI chỉ cần nhãn tham chiếu mờ của dòng, không cần UID người dùng/project. Câu hỏi cũng là dữ liệu gửi ra ngoài: giới hạn độ dài, UI nhắc không nhập thông tin nhạy cảm; không log nguyên câu hỏi/context mặc định.

Tách hiển thị:

1. **Căn cứ của dòng đang xem:** facts nguyên nguồn, gắn mức xác minh; bằng chứng dạng chữ không đồng nghĩa đã mở và kiểm bản vẽ.
2. **Giải thích theo dữ liệu đã có:** liên kết tới trường/công thức. Nếu không có khoản trừ chi tiết, nói không xác định được khoản trừ từ context.
3. **Hướng dẫn chung:** gợi ý kiểm mặt bằng/mặt cắt/biện pháp; không khẳng định hồ sơ này có cấu kiện, kích thước, mác hoặc đơn giá chưa được cung cấp.
4. **Còn thiếu và bước kiểm:** liệt kê rõ, không tự điền số, không suy cạnh từ diện tích/thể tích.

Nếu nguồn mâu thuẫn/sai đơn vị: nêu mâu thuẫn, yêu cầu kiểm nguồn; không chọn nguồn thắng hoặc đổi số âm thầm. Nếu người dùng yêu cầu sửa, hướng dẫn sửa qua luồng kiểm công tác hiện hữu. Không có công cụ ghi, SQL, truy cập tệp hoặc tự tìm giá trong lần hỏi.

Prompt injection trong question/formula/evidence đều là nội dung không tin cậy, không phải lệnh hệ thống. Prompt chỉ là một lớp; backend vẫn khóa allowlist, references, không có công cụ và không nhận mutation từ output. Kiểm tra con số đơn thuần không đủ chứng minh nội dung đúng; một số có sẵn vẫn có thể bị gán sai ý nghĩa.

## 5. OpenAI và định dạng trả lời

Đã tìm và mở tài liệu chính thức ngày 03/11/2026: [Structured model outputs, Chat Completions](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).

Theo tài liệu, JSON mode bảo đảm JSON hợp lệ nhưng không bảo đảm đúng schema; Structured Outputs hỗ trợ schema khi model tương thích. Đây là bảo đảm hình dạng, không bảo đảm facts nghiệp vụ. Phải xử lý refusal, output thiếu/sai và kiểm Pydantic ở backend.

Transport hiện có hỗ trợ json_mode, chưa có tham số schema. Khi mở source: giữ chat_openai; nếu cần mở rộng phải tương thích caller cũ và được giao riêng llm.py. Không tự đổi OPENAI_MODEL để có schema. Nếu model cấu hình chưa xác nhận hỗ trợ, dùng JSON mode + Pydantic và trả lỗi khi không hợp lệ; không retry âm thầm bằng model khác, không coi fallback theo mẫu là trả lời API thật.

Đề xuất output model nhỏ: explanation (text + field references), generalGuidance, checks, warnings; facts/binding/missing chuẩn do backend cung cấp. Không cho model tự trả verificationMode, URL nguồn mới hoặc số thay thế.

Lỗi API phải được ánh xạ thông báo cố định, không trả raw exception/response/request headers. Thiếu khóa: “Trợ lý chưa được cấu hình trên máy chủ”; không hỏi người dùng gửi khóa qua chat. Mất mạng/timeout/hết hạn mức/refusal/schema invalid không làm mất bản kiểm. Không tự retry vì request có thể đã tính phí. Limit câu hỏi, đầu ra, đồng thời và lượt theo phiên; tránh gọi lặp do double-click.

## 6. UI và điều kiện bỏ phản hồi cũ

Nút ở aside chi tiết WorkReview; component độc lập dự kiến RowAssistant.tsx. Hiện 02 là sole UI: 12 không sửa WorkReview hoặc lib/work-review khi chưa được phân file.

UI có ô câu hỏi, gợi ý câu hỏi, đang trả lời, hủy và lỗi/thử lại. Đọc dòng gốc luôn được, không khóa bảng. Hiển thị hai phần căn cứ hồ sơ/hướng dẫn chung. Không có nút áp dụng số hoặc tự tick đã kiểm.

Mỗi request chụp binding + requestId; khi chọn dòng/dự án/bản vẽ/review mới, hủy fetch và xóa câu trả lời đang gắn dòng cũ. Chỉ nhận response khớp binding hiện tại và requestId mới nhất, kể cả khi cùng số dòng nhưng đổi source/công thức. Abort trên trình duyệt không bảo đảm đã dừng request tới OpenAI hoặc không phát sinh phí.

## 7. Gói triển khai khi được mở quyền

1. 01/02 chốt server binding, nguồn scope/partial, revision và nhánh local; đây là phụ thuộc chặn tích hợp, không giả định contract hiện tại đã giải quyết.
2. 12 dự kiến nhận module độc lập agent/row_assistant.py + api/row_assistant.py, focused tests riêng; 01 giao writer include_router trong main.py và thay đổi transport nếu có. Không chạm vùng đang freeze.
3. 02 nhận component/điểm nối UI theo release; thỏa thuận rõ ai tạo RowAssistant.tsx để không hai writer. 12 cung cấp schema/messages/contract mock trước.
4. Kiểm mock theo CASES.md, focused terminal theo lịch 01. Không chạy CAD/full. Mỗi test chéo quyền/stale phải assert transport không được gọi.
5. Sau release live riêng: chỉ demo được phép, chỉ kiểm key-present boolean nếu cần, không đọc/print .env/khóa. Giữ nguyên model/URL cấu hình. Một lượt demo gồm ca đủ và thiếu dữ liệu; thông thường cần hai câu hỏi/API calls, không gọi gộp rồi nhận là đã kiểm hai lượt UI. 01 chốt ngân sách/phạm vi trước chạy.
6. Bàn giao 15 QA độc lập khi tích hợp: hash file, terminal focused, ảnh/UI thao tác, requestId/redacted payload, trạng thái từng ca. 05 giữ sole full theo lịch 01.

## 8. Blocker và giới hạn hiện tại

- Chưa được cấp vùng source/live, nên chưa có chức năng hay bằng chứng runtime mới.
- Chưa có mapping server cho WorkVersion và dòng từ dự án local; chưa thể nhận cross-project/stale server đã bảo vệ.
- Chưa kiểm model hỗ trợ schema, khóa, kết nối API hoặc quyền tài khoản; không suy ra từ tên model trong config.
- Chưa có phân quyền API mới, test mock, demo thật hoặc QA độc lập. Tài liệu này chỉ là kế hoạch có đối chiếu source.
- Chưa gửi thông điệp sang chat khác từ phiên này: chỉ nhận chỉ đạo qua chat, chưa có ủy quyền trực tiếp rõ ràng cho công cụ gửi liên chat. Gói bàn giao sẵn ở hai tệp này để điều phối đọc; không nhờ phiên khác vượt quyền công cụ.
