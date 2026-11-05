# Rà bàn giao tái lập AI và entry W5 — chỉ đọc

04/11/2026, theo yêu cầu01/00. Không git add/commit, sửa source, test, live/API, DB, runtime hay browser. Chỉ đọc Git/source/hash/bằng chứng cũ và xuất inventory/tài liệu này.

## Kết luận chính

1. **Đúng: cả bốn tệp AI/test vẫn untracked (`??`).** Một checkout từ commit hiện tại không tự có backend AI và kiểm thử này. Router trong main.py là thay đổi tracked chưa commit (` M`). File tồn tại trong workspace và mock từng đạt không đồng nghĩa đã có gói phát hành tái lập.
2. Đã lập `REPRO_MANIFEST_20261104.json`: 22 tệp Python theo static import closure, 13 CSV danh mục/config (superset), setup và bằng chứng replay. Mỗi tệp có SHA-256, tracked/status/existence. AST chỉ đọc, không import/chạy source; đây là inventory bảo thủ, không là một lần tái lập đã chạy.
3. VN002 là **một live call tới OpenAI qua hàm staging**, HTTP200 rồi bị validator cũ từ chối. Canonical replay sau đó nhận đúng phản hồi đã lưu, không gọi thêm. Chưa có bằng chứng browser E2E hoặc tư vấn từ receipt đã được người dùng kiểm.
4. **Chưa có entry W5 tư vấn chưa kiểm ở `/phan-tho` theo source đã đọc.** Trang đang render Review roughOnly → WorkReview; hai nút chuyển chọn vật liệu/tối ưu bị canConfirmWork chặn tới khi kiểm/xác nhận. Giữ gate; diagnostic staging checked=false không thể dùng để tuyên bố entry W5 đã có.

## Bộ tệp cần đưa vào gói/track

### A. Delta AI bắt buộc, hiện đều `??`

| Tệp | SHA-256 hiện tại |
|---|---|
| src/optimat/agent/material_advisor.py | 463E8F88B2C92958B6217CDE60EA419ECDBB345EF2569E912094D2ADB300210E |
| src/optimat/api/material_advisor.py | 3873672E507B0F30B029A9F1A9A4D8E4659C833B67CF813009C0611C7F14901D |
| tests/test_material_advisor.py | 087304A58167992694B974E8454E0F0D527DF25C8D662CE1061854B0AC54C4B5 |
| tests/test_material_advisor_api.py | EEF33C6213829F704F36243FDD9742183D70D5A74588979DDFD995018FDC22CD |

Không chỉ track material_advisor.py đơn lẻ. API test import helper `request` từ test_material_advisor; thiếu tệp helper/test logic cũng làm hỏng việc thu thập test.

### B. Baseline Python/setup cần giữ đúng phiên bản

Danh sách đầy đủ 22 file nằm trong manifest (role=static_import_closure). Ngoài bốn file A gồm package `__init__.py` và:

- src/optimat/agent/llm.py; api/auth.py;
- catalog/pricing.py, catalog/repository.py;
- config.py; db/models.py, db/session.py;
- drawing/encoding.py; rough/models.py; schemas.py;
- tests/conftest.py.

Trong closure hiện có thay đổi tracked chưa commit tại pricing.py, repository.py, db/models.py, drawing/encoding.py, rough/models.py, schemas.py. Đóng gói bốn file mới nhưng bỏ những baseline đang dùng này không bảo đảm chạy cùng code như workspace. Không tự gom hoặc commit thay owner; 01 chốt release tích hợp có baseline cụ thể.

`tests/conftest.py` là bắt buộc: đặt OPTIMAT_NO_DOTENV=1, bỏ DATABASE_URL, UTF-8 và overlay kiểm thử; không bỏ file này rồi cho test đọc .env thật. `pytest.ini` đặt pythonpath=src. `requirements.txt` có pytest/httpx/FastAPI/Pydantic/requests/pandas/SQLAlchemy và các phụ thuộc import hiện có. Cần giữ ba file setup này; requirements.txt hiện ` M`.

Phần lớn requirements dùng lower bound, chưa là lock phiên bản đầy đủ cho môi trường 8 mock. Các environment.json đã có của full backend ghi Python3.13.0/Windows, nhưng không phải freeze package của chính action8 và không được dùng thay bằng chứng đó. Vì vậy hiện xác nhận được source hash và terminal cũ, **chưa bảo đảm tái lập bit-for-bit trên máy sạch**; gói release nên thêm lock/package inventory do owner phát hành khi được giao, không tạo mới bằng pip trong lượt chỉ đọc này.

### C. Dữ liệu cần đóng gói cho logic và canonical replay

Giữ toàn bộ CSV `data/catalog/*.csv` theo manifest (13 mục tổng cộng khi cộng `data/rules/nguong_nhan_dien.csv`). Đây là superset an toàn: Catalog.from_csv đọc các bảng material_groups/material_families/materials/wall_systems/material_aliases/material_relations/suppliers/supplier_materials/vehicles/labor_rates hiện có; config đọc nguong_nhan_dien.csv. Hai CSV standards/material_standards được liệt kê thêm để không lẫn baseline danh mục khi release, không khẳng định đều được hai test trực tiếp dùng.

material_aliases/material_relations/materials/wall_systems/nguong_nhan_dien hiện ` M`; standards/material_standards hiện `??`. `materials_master.xlsx` là nguồn soạn dữ liệu, không được Catalog.from_csv đọc để chạy hai focused suites; có thể giữ trong gói tác giả riêng, không cần gửi CAD hoặc XLS để replay response.

Tồn kho DB, khóa API và .env **không cần** cho focused mock/canonical replay offline. Không đóng gói `.env`, credential, cookie, venv, node_modules, __pycache__ hoặc ép chép CAD thật vào gói test AI tối thiểu.

### D. Gói replay và chứng cứ phải giữ cùng nhau

Hiện các artifact sau đều untracked, nên cần được chủ dự án quyết định track hoặc đưa vào archive chứng cứ có manifest (không chỉ dẫn link tới một máy cá nhân):

- reports/demo_0511/live_advisor_vn002/check_advisor.py;
- context.local.json; reply.openai.json; live_receipt.json; live_attempt.json; provenance.json;
- replay_canonical.json và KIEM_TRA.md;
- docs/review/row_assistant_12/ORIGIN_3001_HTTP.log, ORIGIN_3001_RECEIPT.json, ORIGIN_3001_BEFORE.json, ORIGIN_3001_AFTER.json, ORIGIN_3001.patch, ORIGIN_3001_HANDOFF.md;
- HANDOFF.md và contract/ma trận hiện hành để đọc đúng giới hạn.

`check_advisor.py --replay --canonical` chọn src canonical, yêu cầu DATABASE_URL tắt, đọc Catalog.from_csv, đối chiếu context/reply hash và facts với live receipt, inject chat từ response đã lưu. Đây là đường replay không cần tmp/staging. Không dùng `--live`, không cần OpenAI key. `--replay` không có `--canonical` vẫn trỏ staging/DB, không phải lệnh tái lập offline đúng phạm vi.

Lệnh mô tả để owner tái lập sau này (không chạy trong lượt này):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_material_advisor.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests/test_material_advisor_api.py -q -p no:cacheprovider -o faulthandler_timeout=20
# Với OPTIMAT_NO_DOTENV=1, DATABASE_URL vắng và không bật --live:
.\.venv\Scripts\python.exe reports/demo_0511/live_advisor_vn002/check_advisor.py --replay --canonical
```

Windows TestClient trước cần quyền tạo socketpair ngoài sandbox; lần chạy mới vẫn phải tuân theo approval hiện hành, không đổi actor để vượt gate. Không ghi test mới đã đạt chỉ vì có các lệnh này.

`build_context.cjs` và comparison/source CAD là gói provenance đầu vào **tùy nhu cầu điều tra**, không bắt buộc để replay context đã lưu. Chạy lại build_context hiện dùng adapter frontend có thể đã đổi và sẽ ghi đè context/provenance; không chạy nó để tái dựng một cách giả định response cũ. Nếu muốn tái dựng từ CAD thật cần giữ đúng adapter hash thời tạo cùng comparison + drawing hashes và quyền dữ liệu, tách khỏi gói replay tối thiểu.

### E. Tích hợp sản phẩm là gói riêng, không suy từ focused mock

Để ứng dụng có route: cần cả `src/optimat/api/main.py` với hai dòng include/import router (hiện tracked ` M`, SHA A28A10E1D65E45411F38E026BB0FB79F5E2EDA2A0254D16A8F6C8B3F345531F9) và baseline ứng dụng đầy đủ; main không cần để hai focused suites tạo FastAPI app riêng.

Để có giao diện: owner02/17 cần release components/MaterialAdvisor.tsx, AssistantWindow cùng CSS, toi-uu/Proposal và optimize, dieu-chinh/advice-scope, lib/review-session/purchase-session/work-review/store, frontend/package.json/package-lock và các phụ thuộc UI hiện có. Bốn file backend không thể chứng minh gói web đủ. Những tệp frontend này không nằm trong manifest backend tối thiểu và chưa được đóng gói bởi12.

## Provenance đúng của live và replay

- provenance.json: ACTUAL, existing_cad_takeoff, human_approval=false, persisted_project=false, checked_work_count=0, 52 work/7 material.
- live_receipt.json: LIVE_STAGING, http_attempts=1, HTTP200, returned_model=gpt-5.6-luna, outcome=failed/error_type=ValueError. Lỗi ứng dụng cũ chặn TH10; không sửa outcome cũ thành pass.
- Context SHA e1dde8db29d9697677d206f09ccd96fbcfdc48c7a1734c35fe2d82131752ee51. Response **content** SHA 64968be309996a2d2cf60cf9cc9886a5ee3a094295156a13520df20999d08876; không nhầm với hash byte cả file reply.openai.json.
- replay_canonical.json: agent463E, cùng context/content hash; accepted=true, 7 advice, TH10 chỉ dòng dây buộc, 6 dòng chưa có mã, 0 giá mua, 6 biến thể sai bị chặn, 0 call mới. Không biến TH10 thành thép chịu lực hoặc nói toàn dự án chỉ cần một vật liệu.
- Nhãn được phép: “đã có một phản hồi OpenAI thật trên input thực đã bỏ thông tin nhận diện, sau đó kiểm lại offline bằng validator sửa”. **Chưa được phép:** browser E2E, user-approved work, server ownership verified, cả phương án mua đã chốt hoặc tái chạy API mới thành công.

## Entry W5 chưa kiểm ở /phan-tho

- `frontend/src/app/(user)/phan-tho/page.tsx:1`–`:3` import Review rồi render `<Review roughOnly />`. `phan-tho/rough.tsx` là màn cũ, không phải component route đang mount; không kết luận từ màn cũ.
- `do-boc/Review.tsx:597`–`:613`: nhánh roughOnly hiện WorkReview và RoughTab; không mount MaterialAdvisor hay callback tư vấn đọc-only chưa kiểm.
- `do-boc/WorkReview.tsx:116`–`:117`: hai nút “Xác nhận và chọn vật liệu”/“Xác nhận và xem phương án tối ưu” đều disabled khi !canConfirmWork. Chuyển route trong Review chỉ xảy ra khi next.confirmed + destination.
- `lib/work-review.ts:17`–`:25`: canConfirmWork/approvedWork kiểm các dòng có lượng, phạm vi và receipt xác nhận. API/hàm diagnostic vẫn có thể đọc checked=false nhưng không là điểm vào W5 trên UI.

**Kết luận chỉ đọc:** W5 chưa có entry riêng cho dữ liệu chưa kiểm; root giữ gate là phù hợp hiện trạng. Muốn thêm phải là yêu cầu/release UI riêng, ghi rõ advisory chưa kiểm, không tự set receipt.confirmed/checked/materials-ready hoặc coi saved proposal là xác thực server. Lượt này12 không thêm entry hoặc sửa gate.

Hash UI snapshot đã đọc: page.tsx=1D7231ABAD409CFABF75616A15858FD4513CA91368A7D8F393748AC24BD0DA38; Review.tsx=7B06E88AFE2C41B0C34CD7A3C763CA6DDC8C6837D9908F24824907F6C8138BE5; WorkReview.tsx=B3BE6381AD67381894FE2375820488D582D9A7218B2DBAD7C58F50E15FC8D3EB. Review/WorkReview có thể được owner khác cập nhật sau lượt đọc; source line cần đối chiếu snapshot trước dùng làm tiêu chí runtime.
