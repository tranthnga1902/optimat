# Đối chiếu chỉ đọc contract AI — frontend hiện hành

Ngày 04/11/2026, phiên 12 theo giao01. Chỉ đọc source và ghi tài liệu trong vùng docs12. Không sửa source/test/DB/runtime, không chạy test/browser hoặc gọi OpenAI. Các tình huống dưới đây là phân tích nhánh mã, không phải ca ACTUAL đã thao tác hay nghiệm thu mới.

## Kết luận

Request/response chính khớp contract canonical: envelope, SHA-256 chuỗi contextJson, binding dự án/bản vẽ/review và materialRevision nullable, hai POST, facts tách AI, applied=false. Luồng /toi-uu nhận bản kiểm qua approvedWork và mở Proposal độc lập với nghiệm tường. Có ba điểm lệch cần owner frontend xử lý sau release: mất known-part trong context một phần; thiếu chi tiết phụ kiện có điều kiện ở response UI; giá BULLETIN chưa được diễn giải rõ là tham khảo.

Chưa đủ căn cứ để kết luận runtime đã nạp hoặc chưa nạp bản này: chỉ thấy source main đã include router. Không kiểm runtime trong lượt đọc này. Không dùng 26+7 tests/replay để tuyên bố UI E2E, WebUI80 hoặc ownership server đã đạt.

## Sai lệch cụ thể và sửa nhỏ nhất

### F01 — P2: context cả dự án có thể xóa phần lượng đã biết khi có use chưa kiểm

- Vị trí: `frontend/src/app/(user)/dieu-chinh/advice-scope.ts:28`–`:39`, đặc biệt `:33`, `:35`, `:38`, `:39`.
- `exact` yêu cầu mọi use đều map tới các dòng đã checked. Một vật tư có phần góp đã biết từ công tác đã kiểm và một use thuộc công tác còn thiếu/chưa kiểm làm exact=false. Ngay cả selected=null (đang hỏi cả dự án), quantity và quantity_with_waste bị thay null, mọi quantity/via của uses bị thay null/rỗng, sources=[]; complete=false là đúng nhưng known-part và nguồn biết được không còn đi tới backend.
- Backend `agent/material_advisor.py:185`–`:188` chỉ trả đúng demand client gửi, không thể khôi phục phần đã biết. `Proposal.tsx:57`–`:60` cũng dùng context đã mất số để hiển thị “Chưa đủ dữ liệu”. Đây là lệch với nguyên tắc giữ known-part và nguồn thay vì làm mất toàn bộ số biết được.
- Sửa nhỏ nhất đề xuất: nhánh selected=null giữ lượng tổng phần đã biết và nguồn với nhãn rõ “phần đã tính trong toàn phạm vi, còn phần chưa kiểm”; giữ complete=false và missing, không gọi đó là lượng đã duyệt hay lượng mua. Nhánh chọn riêng một element mà lineage chưa đủ vẫn để lượng phân bổ riêng null, không chia đều. Nếu cần thể hiện cả lượng đã kiểm và phần nguồn chưa kiểm thì tách trường minh bạch, không tái sử dụng một trường để che khác phạm vi.
- Owner: 02 (advice-scope/Proposal), 01 điều phối. Không tự sửa backend để gán lại lượng bị client xóa. Chưa chạy ca tái hiện trong lượt này.

### F02 — P2: UI bỏ chi tiết accessories dù backend đã trả mã/nguồn/điều kiện

- Backend: `src/optimat/agent/material_advisor.py:173`–`:178`, `:188` trả `accessories[]` gồm material_id/source/note/state=needs_conditions_and_quantity. Không cộng số lượng hoặc mặc nhiên coi REQUIRES áp dụng.
- Frontend: `frontend/src/components/MaterialAdvisor.tsx:19`–`:24` không khai báo accessories trong facts.materials; render `:104`–`:122` không đọc accessories. Chỉ hiện generic missing “Có phụ kiện…” nên người dùng không thấy phụ kiện nào, căn cứ nào và điều kiện gì để kiểm.
- Sửa nhỏ nhất: thêm kiểu accessories và danh sách mở rộng trong từng dòng, hiện mã, nguồn, ghi chú và nhãn “cần xác nhận điều kiện/lượng”; không tạo quantity, không biến thành đã chọn/mua. Có thể dùng nhãn từ catalog đã trả, không nhờ LLM bịa thêm.
- Owner: 02 phối hợp17 nếu chạm tệp UI đang frozen; 01 release. Không cần sửa contract backend.

### F03 — P2: offer tham khảo và offer mua dùng chung nhãn UI

- Backend: `agent/material_advisor.py:155` tái dùng select_best_offer; offer có `is_reference`, price_level, điều kiện và nguồn. `:261` đã loại is_reference khi tạo has_eligible_price cho model.
- Frontend: `MaterialAdvisor.tsx:15`–`:16` bỏ `is_reference` trong type Offer; `:114` hiển thị mọi offer bằng cùng nhãn “Đơn giá nguồn … BULLETIN …”. Người dùng chỉ thấy mã mức giá, chưa có diễn giải trực tiếp “Giá công bố tham khảo, chưa phải báo giá mua/giao”.
- Sửa nhỏ nhất: thêm is_reference vào type, phân nhãn BULLETIN/is_reference thành “Giá công bố tham khảo”; commercial thì giữ điều kiện VAT/cước/ngày/nguồn. Không dùng presence của offer để coi là đã có giá mua hoặc đủ ngân sách. Chưa có bằng chứng UI đã dùng giá tham khảo đặt hàng; finding là thiếu phân biệt ở trình bày.
- Owner: 02/17 theo release01. Không đổi bộ chọn giá backend hoặc gọi live mới.

## Các phần đã khớp khi đọc source

| Nội dung | Căn cứ frontend | Căn cứ backend / kết luận |
|---|---|---|
| Wire envelope/hash | MaterialAdvisor.tsx:68–79 | MaterialRequest/context():96–109; cùng raw UTF-8 contextJson, không hash object normalize khác |
| Nullable revision | MaterialAdvisor.tsx:6,35–36; advice-scope.ts:43 | Binding:21–25 nullable/defaultNone; omission/null được sameBinding normalize; nonempty nếu có |
| Đúng phiên, bỏ answer cũ | MaterialAdvisor.tsx:45–79 | Cookie bind hash + binding + principal; stale input 409. Đây không là proof server biết bản mới nhất localStorage |
| Đầu vào cả phần thô | advice-scope.ts:12–15,23–46 | Các dòng theo code/plan + raw_class, không phụ thuộc wall_groups |
| Product gate có kiểm | purchase-session.ts:7–23; work-review.ts:22–25 | Proposal chỉ hiện qua optimize.tsx:102–105 khi reviewed/receipt/draftKey hợp lệ theo client |
| Không bắt chọn vật liệu trước tư vấn | purchase-session.ts:21–23 phân draftKey với key | Advisory nhận revision null; purchase key vẫn cần ready + materialRevision |
| Không bị NSGA-II tường chặn | optimize.tsx:103–105,109 | proposal vẫn render khi groups không có hoặc issues; tối ưu tường là phần riêng |
| Lineage không chia bình quân | advice-scope.ts:17–39 | backend coverage:190–205 ghi mapped_aggregate theo work+plan, không tự gán cho element |
| Trung gian không cộng lại | advice-scope.ts:45–46; MaterialAdvisor.tsx:102–103 | facts.intermediates tách và có intermediate_note. Khi chưa kiểm toàn bộ, client gửi intermediates=[]; không được đọc mảng rỗng là không có vữa/bê tông trong hồ sơ |
| AI proposal chưa tự ghi | MaterialAdvisor.tsx:116–120; Proposal.tsx:71–83 | onPropose chỉ setEdits; applied=false từ backend; có bước confirm riêng |
| Lưu cả phương án vẫn phân điều kiện | review-session.ts:24–42 | disposition proposed nếu khác mã/needsReview, conditional nếu receipt.partial/unresolved/proposed; conditional làm materials-ready=false và optimization=null |
| Không tự nâng ready | review-session.ts:33–35 | ready cần không conditional và cờ trước đó true; save proposal không tự biến advice thành purchase-ready |

## Phân biệt ba mức bằng chứng

1. **Lời tư vấn:** output model + facts theo context client, IDs bound candidate, không thay số. Cảnh báo client_snapshot nằm trong facts.warnings và được UI render `MaterialAdvisor.tsx:99`.
2. **Saved whole plan:** saveReviewedProposal kiểm lại WorkVersion/materialRevision/receipt/project localStorage rồi lưu choices, scopedChoices, unresolved, status và thời điểm. Đây là xác nhận/lưu cục bộ theo bản kiểm, không phải nghiệm thu mua hàng hoặc xác thực quyền dự án phía server.
3. **Server verified ownership:** chưa có trong API này. api/material_advisor.py:50–57,69–76 chỉ bind hash/binding/principal trong RAM; không lookup owner của artifact DB và không chứng minh receipt client thật. require_user ở DB mode là đăng nhập, không tự nâng thành ownership của projectUid.

## Hash snapshot nguồn đã đọc

| File | SHA-256 |
|---|---|
| frontend/src/components/MaterialAdvisor.tsx | 3ADDAE2C22886B9DD5EFEB67CA2F38FDDCF453C8E6F0BADEB5787CA9731F76CE |
| frontend/src/app/(user)/toi-uu/Proposal.tsx | C8BF841B7699C431BB356F6C5EAD18DA2FD6A8BE0D6287DD783290A3CE1CD7AA |
| frontend/src/app/(user)/dieu-chinh/advice-scope.ts | 43F864851636141CFAEDACD1916B4D1C3DEC4AA708D6A15F3CF6152992958734 |
| frontend/src/lib/review-session.ts | 1DB96FC93D21492F52AA0D721D645DA8B7976E7A79ACEB7634A3432620B6BB6C |
| frontend/src/lib/purchase-session.ts | F4C637C0D9EAF61DFED97F27A8D3280C230DF03584AE09688C036FB8EADAF2DE |
| frontend/src/lib/work-review.ts | D1D9F724A9949A8426D9102DA8CFD005014C18E5CB67F02AF40C9AB3B3655B29 |
| frontend/src/app/(user)/toi-uu/optimize.tsx | 6D7777BFAD6677023EBC1EF1B22C0D02F5FE941E0BA8C72D87F32D2496E4C850 |
| src/optimat/agent/material_advisor.py | 463E8F88B2C92958B6217CDE60EA419ECDBB345EF2569E912094D2ADB300210E |
| src/optimat/api/material_advisor.py | 285BCC1C885C3D2F0CB82F19C08E3FFE16F3FB674B47831453E726800A47293C |

Source có thể được owner khác cập nhật sau snapshot này; cần so hash trước áp finding. 12 không ghi đè tệp frozen.

## Bằng chứng tái dùng, không chạy lại

HANDOFF.md: canonical logic26 passed/4.17s, HTTPmock7 passed/3.13s. replay_canonical.json: source463E, 7 advice/6 biến thể bị chặn, 0 call mới, checked=false/partial=true của diagnostic. Những kết quả đó không kiểm adapter/frontend hash mới này, không chứng minh ACTUAL human-approved và không đóng gate browser/runtime.
