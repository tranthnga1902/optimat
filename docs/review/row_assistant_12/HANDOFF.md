# Bàn giao backend trợ lý vật liệu — phiên 12

Đã áp đúng 4 file mới theo release01. Trước apply: cả bốn canonical file chưa tồn tại (kiểm Test-Path, từ chối overwrite nếu tồn tại). Sau apply: agent/API trùng byte với staging; hai tests đổi import harness sang canonical. Không sửa main.py, UI/source/shared store/rough/catalog/DB hoặc các file của02/03/04. Chưa tự mount router.

| Canonical file | SHA-256 |
|---|---|
| src/optimat/agent/material_advisor.py | 463E8F88B2C92958B6217CDE60EA419ECDBB345EF2569E912094D2ADB300210E |
| src/optimat/api/material_advisor.py | 285BCC1C885C3D2F0CB82F19C08E3FFE16F3FB674B47831453E726800A47293C |
| tests/test_material_advisor.py | 087304A58167992694B974E8454E0F0D527DF25C8D662CE1061854B0AC54C4B5 |
| tests/test_material_advisor_api.py | DA8774E7D0C5CAD03673E8532A3955A7480F335C0CD52BAFACE9E425AF26E53E |

## Hàm / contract / điểm nối

`MaterialRequest(question,contextJson,contextHash,requestId).context()` kiểm schema/hash.

`material_facts(context: MaterialContext, question: str, catalog: Catalog) -> dict` chỉ đọc lượng + catalog/quotes, không chạy lại định mức/U.

`advise_materials(req: MaterialRequest, catalog: Catalog, chat=None) -> dict`: chat mặc định chat_openai cũ; mock/replay có thể inject. Model/config không đổi.

Router mới prefix `/api/assistant`; POST `/material-session` rồi `/materials`. 02 sole main hook: import router từ `.material_advisor`, include_router. Contract chi tiết MATERIAL_CONTRACT.md.

Props delta cho02: materialRevision optional nullable ở Binding, normalize null khi so binding. Product `/toi-uu` cần approvedWork/receipt, không chặn bởi chưa qua chọn vật liệu. Callback onPropose chỉ tạo đề xuất chờ kiểm, không approved/ready/purchase. Staging UI tại tmp/row_assistant_12/frontend/MaterialAdvisor.tsx, canonical UI thuộc02, không copy đè.

## Terminal thật đã có

- Canonical: `.venv/Scripts/python.exe -m pytest tests/test_material_advisor.py -q -p no:cacheprovider` → **26 passed in 4.17s, exit0**. Bao gồm guard nguyên mã đúng dòng/summary, sai dòng/prefix/suffix, số mới, signed work/use, known-part âm, không chia vật tư theo element, toàn nhóm phần thô, exact autoresolve, reference price, materialRevision nullable. Không chạy lại 26 nếu không thay mã.
- Staging phiên trước optional revision: combined logic+HTTP mock **31 passed in 3.98s, exit0**. Đây không là canonical HTTP mới có test nullable.
- TypeScript staging component: `node frontend/node_modules/typescript/bin/tsc -p tmp/row_assistant_12/tsconfig.json` → exit0, trước delta optional nullable nhỏ; chưa gọi là QA canonical UI.
- ACTUAL context-only: `.venv/Scripts/python.exe reports/demo_0511/live_advisor_vn002/check_advisor.py --context-only` → **Input accepted, exit0**, sau sửa signed quantity.

**Canonical HTTP mock đã có terminal trên CHÍNH action chờ quyền:** `.venv/Scripts/python.exe -m pytest tests/test_material_advisor_api.py -q -p no:cacheprovider -o faulthandler_timeout=20` → **7 passed in 3.13s, exit0**. Tool exec_command require_escalated chạy mock ngoài sandbox vì Windows TestClient/socketpair bị treo trong sandbox (stack socket.accept/_fallback_socketpair). Không OpenAI/CAD/DB/full; không nhờ actor khác chạy hộ. Không có auto-review rejection. Bảy ca gồm no-cookie, cross-snapshot, principal, noDB opt-in/Origin, expiry/hash, key/network sanitized, lượt và materialRevision nullable/stale. Cộng với logic là 33 focused tests mới đạt; đây không phải suite tích hợp/full.

## API thật và replay — phân biệt bằng chứng

04 sole actor đã gọi đúng một lần OpenAI thật trên ACTUAL diagnostic tối thiểu, không nguyên CAD: HTTP200, gpt-5.6-luna, 52 work/7 material, checked=false/partial=true. Kết quả live ban đầu **bị guard cũ từ chối** vì TH10 hợp lệ; không gọi live lần hai.

Nguồn bất biến: reports/demo_0511/live_advisor_vn002/context.local.json SHA e1dde8db29d9697677d206f09ccd96fbcfdc48c7a1734c35fe2d82131752ee51; response content SHA 64968be309996a2d2cf60cf9cc9886a5ee3a094295156a13520df20999d08876. reply.openai.json và live_receipt.json giữ nguyên.

04 replay độc lập canonical đã có: `reports/demo_0511/live_advisor_vn002/replay_canonical.json`, source hash463E8F88…0210E khớp manifest, **7 accepted, TH10 chỉ m5, 6 dòng không ứng viên, 0 giá mua, 6 biến thể bị chặn, 0 call mới**, exit0 và hash trước/sau ổn định. Cùng context/response hash gốc, dùng catalog cục bộ, 0 DB. Đây là replay response đã gọi thật, không phải live mới hoặc production E2E.

## Giới hạn cần giữ khi demo

client_snapshot không xác minh độc lập sở hữu/nguồn CAD/approved receipt/bản mới nhất. Session hash chỉ bind payload, local demo opt-in + Origin/loopback, RAM một worker. DB mode không nhận/lookup artifact DB; muốn claim DB ownership cần thêm luồng server snapshot đúng quyền.

Các mã khác raw_class chỉ tra thêm cần kiểm thiết kế, không chứng minh tương đương. Tự resolve hiện chỉ exact tên/quy cách/đơn vị/loại duy nhất. Thiếu mác/cấp thép không tự bù; TH10 là dây buộc, không thay thép chịu lực. quantity_with_waste chưa là lượng mua; purchase null tới khi đủ quy cách/kho/hàng đã đặt.

Chưa QA giao diện/whole-plan confirmation hoặc budget/supply/U có nguồn. HTTP canonical mock đã đạt, chưa phải HTTP production hoặc UI E2E. AI văn xuôi có thể sai ngữ nghĩa dù guard mã/số đạt. Không ghi full225 bao phủ AI, không ghi LIVE_STAGING là production E2E. Ca M1/G8 giữ nguồn riêng, không hardcode cấp phối M1 vào catalog chung.
