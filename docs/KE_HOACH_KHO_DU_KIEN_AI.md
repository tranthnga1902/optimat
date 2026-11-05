# Kế hoạch cải tiến đọc – nhận dạng có OpenAI API hỗ trợ (KD01–KD08)

Ngày lập: 05/11/2026 (bản 2, thay bản 1 cùng ngày). Trạng thái: **đề xuất, chưa triển khai**. KD01 đụng schema → phiên
điều phối duyệt trước.

## Trạng thái 05/11/2026

KD01–KD07 đã có mã, giao diện và test (`tests/test_facts_kd.py`, `tests/test_input_kd07.py`, `tests/test_analysis_cache.py`;
AI kiểm bằng phản hồi giả, **chưa chạy với OpenAI thật** — mã model `gpt-5.6-luna` chưa xác nhận). KD08 đã tách nguyên nhân,
chưa sửa mã nhận diện (`docs/review/KD08_HINH_HOC_XAY_DAM_COP_PHA.md`). Bật AI: tick "Cho phép AI" ở trang hồ sơ dự án
(gửi `allow_ai`), cần `LLM_PROVIDER=openai` + `OPENAI_API_KEY`. Duyệt đề xuất: trang /quy-tac, mục "Đề xuất AI chờ duyệt".

## 1. Số đo làm căn cứ (bộ build, sơ bộ)

Nguồn: `reports/batch/tong_hop.xlsx` (batch 02/11/2026, sheet `Ly_do_trong`, có lẫn file mẫu/test → chỉ là số sơ bộ) và
`docs/C01_DUONG_CO_SO_BUILD.md` (bộ 46, đối chứng chưa xác nhận).

| Nguyên nhân công tác bị trống | Lượt | Tỷ lệ | Ví dụ |
|---|---|---|---|
| Thiếu thông số thường **ghi bằng chữ/bảng** trên bản vẽ | 613 | 80 % | chiều dày trát (110), chiều dày sàn (69×2+19), cao dầm (50×2), phương án tường (55), bảng thống kê thép (≈89), lanh tô (≈70), cán nền (22), rộng dầm (24), kích thước móng (9) |
| Thông số người dùng / định mức | 87 | 11 % | hàm lượng thép kg/m³ |
| Trống kéo theo | 64 | 8 % | khối lượng bê tông của cấu kiện đã thiếu số |

Cảnh báo cấp bản vẽ hay gặp: "Không tìm thấy mặt bằng tầng kiến trúc" (16 bản vẽ), "Chưa xác định tầng trệt" (13),
"tường bao chưa khép kín" (12).

Sai số hình học (C01, bộ 46): XAY −16,6 %, DAM −19 %, cốp pha dầm −31,5 %, cốp pha sàn −28,1 %.

**Kết luận:** nút thắt lớn nhất là **đọc chữ ra thông số**, không phải hình học → AI đọc chữ là hướng đáng đầu tư nhất.
Hình học cần sprint riêng không dùng AI (KD08).

### Khảo sát chữ trên 9 bản vẽ build (`evaluate.survey`, 05/11/2026)

| Tín hiệu | Giá trị khác nhau | Chưa có quy tắc |
|---|---|---|
| Ghi chú vật liệu (TEXT) | 188 | **179 (95 %)** |
| Layer | 238 | 121 (51 %) |
| Hatch | 35 | 31 |
| Block | 990 | 984 (phần lớn không liên quan vật liệu) |

Ghi chú chưa có quy tắc **chứa đúng thông số đang thiếu**, ví dụ: "lớp vữa trát trần #75 dày 15", "lớp vữa tạo phẳng nền
50# dày 40", "lót vữa xm mác 75 dày 20", "bê tông B20 (M250)" (47 lần), "bê tông lót B7.5 (M100)" (42), "lớp bê tông gạch vỡ
dày 100", "lớp bê tông bảo vệ cốt thép dày", "thống kê thép xây dựng cho tổng cấu kiện" (37). Nhiều dòng còn lẫn mã chữ hỏng
("LớP VữA TạO PHẳNG") → AI đọc tốt hơn regex ở chỗ này, nhưng số vẫn phải kiểm bằng excerpt.

Layer chưa nhận phần lớn tên vô nghĩa ("0", "1", "3", "5L", "LAYER8") → **AI đọc tên layer không giúp được**; layer phải nhận
bằng hình học (KD08). KD05 chỉ áp cho tiêu đề tờ/tầng và ký hiệu cấu kiện.

### Đếm từ khóa thông số theo từng bản vẽ (regex thô, có thể đếm thiếu)

| Bản vẽ | sàn dày | trát dày | lanh tô | mác BT | vữa mác | Ø thép |
|---|---|---|---|---|---|---|
| nha_sang_hai_duong KC / KT | 30 / 0 | 3 / 9 | 35 / 0 | 56 / 0 | 6 / 5 | 128 / 0 |
| nha_huong_hai_duong KC / KT | 14 / 0 | 2 / 10 | 32 / 0 | 36 / 0 | 5 / 3 | 127 / 0 |
| nha_pho | 0 | 2 | 0 | 9 | 8 | 15 |
| ket_cau, tan_binh_ket_cau | 0 | 0 | 0 | 0 | 0 | 682–684 |
| nha_dan, tan_binh_kien_truc | 0 | 0 | 0 | 0 | 0 | 0 |

→ Hai bộ Hải Dương ghi nhiều thông số bằng chữ: KD03 có lợi lớn. Bộ cũ (ket_cau, tan_binh, nha_dan) gần như chỉ có bảng thép
(Ø): KD04 có lợi, KD03 ít; thông số còn lại vẫn phải hỏi người dùng hoặc lấy từ DOCX/XLSX tùy chọn.

Chưa đếm: bao nhiêu trong 613 lượt trống có ghi chú tương ứng trên **đúng** bản vẽ đó — đo ở đầu KD03.

## 2. Ràng buộc đã chốt

| # | Ràng buộc |
|---|---|
| R1 | Chỉ DWG/DXF, XLSX/XLS, DOCX, biểu mẫu. Không PDF, scan, ảnh, OCR. |
| R2 | Bắt buộc chỉ bản vẽ CAD; XLSX dự toán, DOCX thuyết minh/yêu cầu, vị trí là tùy chọn. |
| R3 | AI **không sinh số**: chỉ chọn nhãn trong danh mục đóng và chỉ ra nguồn (handle/ô/đoạn) + trích đoạn; số do mã đọc từ trích đoạn. |
| R4 | Dữ kiện AI tối đa mức **B**, không ghi đè A hoặc số người nhập; quy tắc CSV thắng AI. |
| R5 | `LLM_PROVIDER=none` vẫn chạy đủ như hiện nay. |
| R6 | Không điền mặc định (B7); thiếu → danh sách câu hỏi. |
| R7 | Chỉnh prompt/quy tắc theo **build**; **test** chỉ báo cáo. |
| R8 | Dự án đánh dấu "không gửi ra ngoài" → không gọi OpenAI (chỉ Ollama hoặc tắt). |
| R9 | Chỉ phần thô. |

## 3. Cách dùng OpenAI API

| Hạng mục | Cách làm |
|---|---|
| Gọi API | Mở rộng `agent/llm.chat_openai`: thêm `response_format = {"type":"json_schema","json_schema":{..., "strict": true}}` (hiện chỉ có `json_object`). Model từ `OPENAI_MODEL`; mã `gpt-5.6-luna` **chưa xác nhận** trên trang OpenAI → kiểm trước KD03. |
| Đầu vào gửi đi | Chỉ chữ: đoạn ghi chú (`drawing/text_blocks.py`), tiêu đề tờ, tên layer/block, ô bảng đã dựng lưới (có id). Không gửi hình, không gửi tọa độ thừa. |
| Đầu ra | JSON theo schema: `[{ref, field, label, excerpt}]`; `field`, `label` là enum đóng sinh từ CSV/danh mục. Không có trường số. |
| Đọc số | Mã tách số từ `excerpt` bằng regex hiện có (`encoding`, `dimensions`), đổi đơn vị; không tách được → loại. |
| Gom lô | Một lần gọi / một tờ bản vẽ (hoặc ≤ N đoạn); song song có giới hạn. |
| Cache | Khóa = SHA-256 nội dung gửi + phiên bản prompt + model. Chạy lại cùng hồ sơ: không gọi API. |
| Lỗi mạng / timeout | Bỏ qua bước AI cho tờ đó, ghi cảnh báo; luồng quy tắc vẫn chạy (R5). |
| Chi phí | Ghi token vào log theo lần phân tích; trần token/hồ sơ trong `config`. |
| Bảo mật | Khóa chỉ ở `.env`; cờ dự án `cho_phep_ai_ngoai` (R8); không ghi nội dung gửi đi ra log công khai. |

## 4. Bốn chốt chống bịa (mã kiểm)

1. Nhãn/field thuộc enum đóng; ngoài → loại.
2. `excerpt` là chuỗi con (sau chuẩn hóa dấu, TCVN3/VNI) của đúng nguồn `ref`; số rút ra phải nằm trong `excerpt`.
3. Không lấn quyền: AI ≤ B; mâu thuẫn với quy tắc/A → giữ nguồn mạnh, gắn cờ.
4. Truy vết: lưu prompt, model, excerpt, kết quả kiểm cho từng dữ kiện; cache tái lập được.

## 5. Sprint (ưu tiên theo số đo)

| Mã | Việc | File chính (dự kiến) | Tiêu chí xong | Phụ thuộc |
|---|---|---|---|---|
| **KD01** | Kho dữ kiện + cache theo hash, chưa bật AI; quy tắc hiện có ghi vào kho. **05/11: phần cache xong** (`src/optimat/analysis_cache.py`, JSON theo khóa băm, không đổi schema; đo 57,8 s → 0,28 s). Phần bảng dữ kiện dời sang KD02/KD03 (chưa có nơi đọc). | `db/schema20.py` hoặc JSON theo revision (điều phối chọn), mới `facts/store.py`, `api/project_analysis.py` | Lần chạy 2 cùng hồ sơ không đọc lại DXF; tiên lượng trùng luồng cũ trên build; pytest đạt | Điều phối duyệt |
| **KD02** | Bộ kiểm chứng 4 chốt + client OpenAI có `json_schema` strict, cache, timeout, đếm token. Test bằng phản hồi giả (đúng / nhãn lạ / excerpt bịa / số bịa). | mới `facts/verify.py`, `agent/llm.py` | 100 % ca bịa bị loại; ca đúng được nhận; không gọi mạng trong pytest | KD01 |
| **KD03** | **Trích thông số từ ghi chú** (ưu tiên số 1, ~80 % lượt trống): chiều dày sàn, trát, cán nền, cao/rộng dầm theo ký hiệu, lanh tô (cao, gối), cấu tạo nền, kích thước móng theo ký hiệu, mác bê tông/vữa, phương án tường. Kết quả vào `ProjectParams`/cấu kiện ở mức B. | mới `facts/ai_params.py`, `drawing/text_blocks.py`, `rough/takeoff.py` (chỉ đọc kho) | Trên build: đếm lượt trống trước/sau; độ chính xác từng field so với dự toán bộ 46 + soát tay; chỉ bật field đạt ngưỡng (đề xuất ≥ 95 %) | KD02 |
| **KD04** | **Bảng thống kê** (thép, cột, cửa): mã dựng lưới ô từ TEXT theo tọa độ; AI chỉ gán ô tiêu đề → cột chuẩn (Ø, số lượng, chiều dài, khối lượng…); mã đọc số theo cột. | `rough/rebar.py`, `rough/structural_column_instances.py`, mới `facts/ai_tables.py` | Bảng thống kê thép build đọc ra đủ cột; tổng kg khớp tổng ghi trên bảng | KD02 |
| **KD05** | **Gắn nhãn tờ / tầng / ký hiệu** chưa khớp quy tắc (không gồm layer: tên layer build phần lớn vô nghĩa) (sửa "không tìm thấy mặt bằng tầng", "chưa xác định tầng trệt"). | `drawing/sheets.py`, `drawing/plans.py`, `layer_classifier.py`, `ky_hieu_cau_kien.csv` | Số bản vẽ có cảnh báo tách tờ/tầng giảm trên build; không tăng nhận nhầm | KD02 |
| **KD06** | Hàng chờ duyệt: đề xuất AI → người duyệt → dòng CSV quy tắc (lần sau không gọi AI). | trang `/quy-tac`, `api/admin_db.py`, `data/rules/*.csv` | Duyệt 1 đề xuất → chạy lại khớp bằng quy tắc, 0 lần gọi API | KD03–KD05 |
| **KD07** | **05/11 đã xong phần input:** gỡ PDF tải lên mới, DOCX đọc theo đoạn có id, `RoughResult.missing_inputs` + bảng trên /phan-tho. Còn lại: ánh xạ dự toán. Tài liệu hỗ trợ tùy chọn: XLSX dự toán → cột đối chiếu (AI ánh xạ tên công tác → mã); DOCX → thông số (cùng cơ chế KD03); danh sách câu hỏi thiếu gom một lần; gỡ PDF khỏi luồng nhận hồ sơ (R1). | `api/document_candidates.py`, `api/project_document_io.py:53`, `api/project_files.py:294`, `ProjectDossier.tsx` | Có/không tài liệu hỗ trợ đều ra đủ bảng; lệch > `khoang_hop_ly` có cờ; `.pdf` bị từ chối rõ | KD02 |
| **KD08** | Hình học (không AI): tường −16,6 %, dầm/cốp pha; dùng chênh dự toán để chỉ chỗ cần kiểm. | `drawing/walls.py`, `rough/beams.py` | Có phân tích nguyên nhân XAY −16,6 % theo tầng; sprint sửa riêng | — |

Thứ tự: **KD01 → KD02 → KD03** (giá trị lớn nhất) → KD04, KD05 song song → KD06; KD07, KD08 xen khi rảnh.

## 6. Đo và nghiệm thu

- Thước đo chính: **số lượt công tác trống** và **số dòng mức D** trên build, trước/sau từng sprint (batch_takeoff).
- Độ chính xác từng field AI: soát tay một mẫu + đối chiếu dự toán bộ 46 (lưu ý: bộ 46 chưa xác nhận, thông số móng/thép lấy từ chính dự toán).
- Báo cáo cuối chạy **một lần** trên test (banve1); không chỉnh theo test.
- So với mốc "chỉ quy tắc" (LLM tắt) ở mọi báo cáo.

## 7. Rủi ro

- Bản vẽ có thể **không ghi** thông số bằng chữ → AI không cứu được; đo trước ở KD03.
- Gửi chữ bản vẽ lên OpenAI = dữ liệu ra khỏi máy (R8); hồ sơ hạn chế quyền dùng (Tân Bình) phải tắt.
- Mã model chưa xác nhận; chi phí/độ trễ chưa đo.
- KD01 đụng schema 20 bảng và file dùng chung → báo phiên điều phối.
