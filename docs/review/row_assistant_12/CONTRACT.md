# Hợp đồng staging — AI hỗ trợ chọn vật liệu tường

> ĐÃ THAY THẾ bởi MATERIAL_CONTRACT.md: trợ lý toàn phần thô, không chỉ tường. Giữ bản này làm lịch sử; không tích hợp contract cũ.

03/11/2026, ưu tiên mới của 00 thay MVP hỏi dòng. PLAN.md/CASES.md về hỏi dòng là tài liệu chuẩn bị trước, không còn điều kiện demo chính. Chưa có quyền apply source/live; mã chuẩn bị ở tmp/row_assistant_12/. Chưa có mock terminal hoặc nghiệm thu.

## Điểm nối dự kiến cho 01/02

- Component: RowAssistant, props `{context: MaterialContext; onChoose?: (wallSystemId: string) => void}`. onChoose chỉ phát lựa chọn sau bấm xác nhận; caller kiểm geometry/version rồi áp qua luồng có sẵn, không tự lưu từ AI. Context chứa một nhóm tường đã kiểm, binding bất biến và phạm vi partial; không nguyên hồ sơ. Component đặt ở bước Chọn vật liệu, không bắt hỏi công thức trước.
- API: router độc lập src/optimat/api/row_assistant.py, prefix `/api/assistant`. Hunk main.py tương lai do 02/owner áp: `from .row_assistant import router as row_assistant_router` và `app.include_router(row_assistant_router)`.
- POST `/api/assistant/materials`: `{question, context, contextHash, requestId}`. Hash SHA-256 canonical JSON context chỉ bảo đảm payload nhất quán, không xác minh bản vẽ/quyền. Binding context: `{projectUid,drawingId,reviewId,rowIndex}`; mode local `client_snapshot`, không gọi đã được backend kiểm độc lập. Server không nhận catalog/giá/phương án do client tự gửi.
- MaterialContext: binding trên, `group` theo WallGroup hiện có, `checked: true`, `partial: boolean`, `scope: string`, `approvedWallSystemIds: string[]`. Đây là lời khai client; server trả rõ provenance. Không nhận địa chỉ/tệp/CAD hoặc request/result cả nhà.
- Backend dùng catalog để lọc cùng lớp, vai trò và bề dày khối xây với thiết kế; chỉ xét thiết kế và mã thay thế người dùng đã cho phép. Cho phép nhiều/một/không phương án; thiếu giá không xóa phương án kỹ thuật. Giữ nguồn và thiếu dữ liệu, không dựng giá. Khác hình học không được âm thầm đề xuất áp dụng.
- Output `{requestId,contextHash,binding,provenance,candidates,missing,warnings,ai}`. candidates/facts từ backend tất định; `ai` chỉ giải thích/gợi ý kiểm, tham chiếu mã có trong candidates, không tạo số/mã/giá. Không có mutation.
- MVP chi phí chỉ so phần vật tư chính có báo giá hợp lệ cùng đơn vị/điều kiện; ghi rõ chưa phải tổng chi phí tường, chưa gồm vữa/nhân công/vận chuyển. Không gọi rẻ nhất tổng thể khi thiếu thành phần. Cung ứng/U thiếu nguồn giữ null; U tính từ lớp xây chỉ ghi đúng phạm vi đó.
- Route không được coi require_user(None) ở noDB là auth. Nhánh demo local phải opt-in server, phiên HttpOnly và Origin/loopback phù hợp; nếu thiếu điều kiện thì từ chối trước OpenAI. Nhánh có DB ID phải kiểm owner trước lookup artifact, chưa có binding server trả chưa hỗ trợ thay vì echo giả verified. Tích hợp server state sẽ chốt cùng 01.
- Error: 401/403 quyền; 409 snapshot/binding; 422 payload; 503 thiếu khóa/mất mạng; 502 output invalid/refusal. Message cố định, không raw exceptions. Client AbortController + request sequence/context guard; dòng và bản gốc luôn đọc được.

## Phạm vi file

Staging dự kiến: agent/row_assistant.py; api/row_assistant.py; RowAssistant.tsx; test_material_assistant.py; test_material_assistant_api.py. Khi 01 mở apply mới copy vào file mới đã phân; chưa sửa llm/orchestrator/pipeline/main/WorkReview/store/rough/catalog/pricing. Focused mock độc lập trên staging theo lịch 01; không full/DB/train/live.

## Cần chốt trước hook

02 cung cấp đúng nhóm tường đã kiểm và revision khi thay đổi cấu tạo; cần tránh lấy nhóm tường nhận dạng sơ bộ thay cho final_wall_groups. Context group chỉ một nhóm, nếu partial phải hiện rõ. approvedWallSystemIds chỉ là cho phép so sánh, không thay xác nhận áp dụng. Backend chưa thể chứng minh checked/partial của localStorage. Tài liệu không tuyên bố đã giải quyết xác thực độc lập.
