# Hợp đồng staging — trợ lý vật liệu toàn phần thô

Theo phạm vi mới nhất của chủ đồ án qua 00/01: điểm hỏi chính tại `/toi-uu`, đi thẳng từ bản công tác đã kiểm; `/dieu-chinh` và xem giá là tùy chọn. Không phụ thuộc wall_groups/NSGA-II/manual dropdown. 01 đã release và 12 áp đúng 4 file backend/test canonical; main/UI vẫn thuộc02. Xem HANDOFF.md cho hash/terminal. Full backend225 không bao phủ mã AI mới.

## File và điểm nối cho 01/02

- `tmp/row_assistant_12/agent/material_advisor.py` → dự kiến `src/optimat/agent/material_advisor.py`.
- `tmp/row_assistant_12/api/material_advisor.py` → dự kiến `src/optimat/api/material_advisor.py`.
- `tmp/row_assistant_12/frontend/MaterialAdvisor.tsx` → dự kiến `frontend/src/components/MaterialAdvisor.tsx`.
- `tmp/row_assistant_12/tests/` là harness staging. Chưa sửa llm/orchestrator/pipeline/catalog/pricing/rough/main/UI chung.
- Hunk main.py tương lai do owner 02 áp: `from .material_advisor import router as material_advisor_router` và `app.include_router(material_advisor_router)`.
- UI `/dieu-chinh`: props `{context: MaterialAdvisorContext, onPropose?: (selection) => void}`. Selection trả binding/contextHash/lineId/materialId/needsDesignReview/needsGeometryReview sau chọn và xác nhận. Callback chỉ tạo đề xuất chờ kiểm, không gán approved/ready/purchase hoặc đầu vào tối ưu. Caller giữ bảng gốc luôn đọc được.

## Context tối thiểu

MaterialAdvisorContext: binding `{projectUid,drawingId,reviewId,materialRevision?}`, partial, scope, works, materials, intermediates, proposedMaterialIds. Advisory cho phép bỏ materialRevision hoặc null; khi có phải nonempty. Response normalize về null; client so `(revision ?? null)`. Product caller vẫn giữ approvedWork/receipt gate; diagnostic04 checked=false/partial=true không phải nghiệm thu. Purchase mode giữ materialRevision/provenance riêng.

- works: rowIndex gốc, code, plan, element, quantity, unit, status, basis, checked, missing. Giữ cả dòng thiếu/ngoài hỗ trợ; không gửi CAD hoặc request/result toàn bộ.
- materials: lineId ổn định trong revision, material_id hoặc null, name, raw_class, unit, quantity, quantity_with_waste, complete, missing, sources, uses `{work,plan,quantity,via}`.
- intermediates: name, quantity, unit, complete. Chỉ đối chiếu vữa/bê tông trung gian, không cộng lại nguyên liệu sau tách.
- proposedMaterialIds là mã muốn tra thêm, không phải đã duyệt thay thế và không bắt người dùng chọn trước. Backend tự resolve tên/quy cách+đơn vị+raw_class trùng DUY NHẤT trong catalog, ghi resolution_source; không dùng cùng raw_class để tự bù mác/cấp thép. Không resolve được thì gợi ý điều kiện/nhóm dữ kiện còn thiếu, không ép người dùng chọn từng dòng.
- Giới hạn: 300 công tác, 100 dòng vật tư, 40 trung gian, 30 mã tra; UTF-8 context tối đa 60 KB, câu hỏi 1500 ký tự. Vượt giới hạn báo chia phạm vi, không âm thầm bỏ dòng. Không gửi tên chủ nhà/địa chỉ/cookie/key.
- Backend tra mã/quy cách/nguồn/giá từ catalog. Lượng và trạng thái kiểm local snapshot là dữ liệu client cung cấp, không xác minh độc lập. Khác mã cùng raw_class chỉ là đề xuất tra cứu cần kiểm, không có nghĩa tương đương kỹ thuật.

## Wire và ranh giới phiên

POST `/api/assistant/material-session` với `{question,contextJson,contextHash,requestId}`. contextJson = JSON.stringify(context); contextHash = SHA-256 UTF-8 chuỗi nguyên. Backend kiểm schema/byte size/hash, cấp cookie HttpOnly/SameSite strict và lưu binding/hash/principal/TTL. Hash không chứng minh nguồn hay quyền dự án.

POST `/api/assistant/materials` với cùng envelope và cookie. So hash/binding/người dùng/TTL/lượt/busy trước OpenAI. Local noDB mặc định tắt, chỉ demo khi env OPTIMAT_ASSISTANT_LOCAL_DEMO=1 + peer loopback + Origin localhost. Không tự bật env. DB mode require_user, không nhận DB artifact IDs/lookup dữ liệu dự án; không suy projectUid thành project_id. Muốn hỗ trợ hồ sơ DB thật phải bổ sung owner check + server snapshot trước lookup; chưa có nhánh này.

Đây là **client_snapshot**: server chỉ chứng minh nội dung trong phiên không đổi, không xác minh bản vẽ/ownership localStorage/bản mới nhất/receipt đã kiểm. UI phải loại response khi revision đổi. Session RAM cho demo một worker, restart mất phiên; chưa là auth/rate limit production. Không nói đã bảo vệ cross-project ownership độc lập chỉ vì có echo/hash.

## Facts, đề xuất và hạn chế

Response `{requestId,contextHash,binding,provenance:'client_snapshot',facts,ai,applied:false}`.

- coverage giữ mọi work: mapped_aggregate/missing/unsupported/no_purchase_material. MaterialUse không có element_id: chỉ map code+plan và nói tổng phạm vi, không chia đều/gán tổng cho một cấu kiện. Chưa gọi lại materials_for_works để truy riêng.
- work.quantity và uses.quantity giữ signed finite, kể cả khoản TRỪ âm; coverage ghi quantity_role=deduction. Known-part demand âm giữ raw và missing issue, không clamp0/abs/đổi dấu; purchase_quantity vẫn null, không sinh lượng mua âm. quantity_with_waste không là số bao/cây/tấm.
- Options từ mã hiện tại/tự tra duy nhất và mã muốn tra thêm cùng raw_class. Mã hiện tại là current_lookup, không gọi current_design đã được user duyệt. Khác mã luôn proposed, canApply false và needsDesignReview/needsGeometryReview; chưa có bộ chứng minh tương đương mác/cấp/cấu tạo. Không tự hạ cấp để giảm giá. has_eligible_price trong prompt chỉ true khi offer có và !is_reference; BULLETIN/lịch sử không là giá mua.
- Tái dùng price_offers/select_best_offer; BULLETIN phân biệt tham khảo. Không tính lại vật tư/U/tổng tiền/cước. Supply/U chưa có công cụ/nguồn thích hợp giữ null. Không áp U cho thép/bê tông; thiếu giá không xóa cấu tạo.
- REQUIRES hiện phụ kiện cần xác nhận điều kiện/lượng, không tự cộng. Đào/đắp không vật tư mua khác thiếu mapping; đất đắp mua ngoài cần khai báo.
- AI JSON summary/advice theo đúng lineId; IDs chỉ thuộc options của dòng. reason/checks được nhắc nguyên mã của chính dòng; summary union mã trong facts. Guard chặn TH100/X-TH10/TH10-A/sai dòng/giá hoặc ngày mới, không cấm mù mọi chữ số. Không nhận patch/approval/nguồn/giá mới. Schema/kiểm số không chứng minh hết sai ngữ nghĩa hay tên riêng bịa; QA và nhãn hướng dẫn chung vẫn bắt buộc.
- Prompt rút gọn không UID/CAD/toàn bộ hồ sơ; tên/nguồn/câu hỏi là dữ liệu không tin cậy. Không có tool ghi hay tự tìm nguồn mới.

## UI và API

Component pending/error/hủy, giữ dữ liệu gốc; AbortController + sequence + context guard gồm materialRevision. Hủy UI không bảo đảm upstream ngừng/tính phí. Không tự ghi store/history/receipt.

Giữ chat_openai/config model/URL, không dependency/migration/model mới. JSON mode + Pydantic; lỗi/refusal/key/network thông báo cố định không raw exception/fake AI fallback. Session giới hạn 6 lượt/10 phút, chặn đồng thời. Transport cũ chưa có output-token cap riêng; còn hạn chế chi phí trước production.

## Lịch và bằng chứng

12 không gọi live. 04 đã dùng DUY NHẤT một call ACTUAL diagnostic deidentified, HTTP200; validator cũ từ chối mã TH10. Guard đã sửa bằng replay chính response, không gọi thêm. Đường dẫn/nhãn LIVE_STAGING và hash trong HANDOFF.md; checked=false/partial=true chưa là production E2E hoặc tư vấn từ bản đã kiểm. 02 hook/15 QA tiếp; không chạy full/DB/train ở12.

Đã mở [OpenAI Structured Outputs, Chat Completions](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat) ngày 03/11/2026: JSON mode không bảo đảm schema, schema không chứng minh facts. Đã đọc Next cục bộ `frontend/node_modules/next/dist/docs/01-app/03-api-reference/01-directives/use-client.md` trước viết component.
