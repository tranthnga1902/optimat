# Bàn giao dự án OptiMat AI (09/10/2026)

Tài liệu này tóm tắt toàn bộ những gì đã chốt và đã làm, để tiếp tục trong Claude Code mà không cần
đọc lại cuộc trao đổi cũ. Quy tắc làm việc ngắn gọn nằm trong `CLAUDE.md`, danh sách việc theo tuần nằm trong `PLAN.md`.

## 0. Cập nhật 13/10/2026: hệ thống đã nối thông một bộ mã vật liệu

Luồng đầy đủ đang chạy được (58 bài kiểm thử; 66 bài khi có PostgreSQL):

```
bản vẽ -> tách mặt bằng -> nhận tường, lỗ mở -> vật liệu ghi trên bản vẽ (ghi chú, hatch, layer, 240 tên gọi khác)
       -> quy về mã danh mục (GN01...) + phương án tường (W-GN01-220) theo loại tường
       -> trang Kiểm tra bóc tách (/ui/takeoff): sửa, bổ sung, chọn vật liệu từ danh mục -> Xác nhận
       -> máy chủ chốt khối lượng + bảng vật liệu (gạch, vữa) + giá có trong DB; lưu takeoff_results nếu ?project=<id>
       -> Tối ưu (có thể giữ vật liệu thiết kế, chỉ chọn đại lý và xe) -> giải thích
```

- API mới: `/api/catalog/wall-materials`, `/api/price/bill`, `/api/agent/run`; `/api/takeoff/confirm` trả `bill`, `takeoff_id`;
  `Constraints.keep_design_material`.
- Agent: bước `step_bill` trong luồng cố định, công cụ `tra_gia_theo_thiet_ke` cho agent gọi công cụ.
- Mã mẫu MAT_* đã bỏ khỏi mã nguồn và dữ liệu đi kèm. `data/catalog/materials.csv`, `wall_systems.csv`,
  `material_aliases.csv` sinh từ `materials_master.xlsx` cùng lúc với `sql/03_materials.sql`.
- Danh mục thật còn thiếu số: chỉ W-GN01-110/220 đủ để tối ưu (xem `GET /api/catalog/wall-materials`, trường `missing`).
  Kiểm thử dùng thêm số MẪU trong `data/sample/catalog` qua biến `OPTIMAT_CATALOG_OVERLAY`.
- Database đã có: chạy `sql/04_upgrade.sql` rồi `sql/03_materials.sql`; dòng giá mẫu cũ mang mã MAT_* xóa bằng phần
  dọn dẹp cuối file 04.

Bổ sung cùng ngày: giao diện chung `/app` (theo mockup, hai vai trò, nối trang kiểm tra → vật liệu và giá → tối ưu),
kiểm soát dữ liệu (`scripts/check_data.py`, `/api/data/check`, hook pre-commit), thư mục `docs/` (đề cương, mẫu thu thập,
mockup), bản vẽ thật trong `data/drawings/build/`, kho git có sẵn lịch sử. Quy trình: `docs/QUY_TRINH_DU_LIEU.md`.

Các mục bên dưới là bản bàn giao 09/10, giữ để tra cứu; chỗ nào khác với mục 0 thì theo mục 0.
Đã lỗi thời (21/10/2026), theo `CLAUDE.md`: mô hình ngôn ngữ là OpenAI qua API (không phải Qwen/Ollama), 26 bảng (không phải 19),
phạm vi bóc toàn bộ phần thô; số bài kiểm thử và câu lệnh mở đầu ở mục 4, 9 không còn đúng. Tiến độ: `SPRINTS.md`, `NHAT_KY.md`.

## 1. Đề tài

**Nghiên cứu và xây dựng hệ thống AI Agent hỗ trợ tối ưu lựa chọn giải pháp sử dụng vật liệu xây dựng
cho công trình nhà ở ứng dụng mô hình XGBoost và thuật toán NSGA-II** (tên hệ thống: OptiMat AI).

- Đồ án tốt nghiệp kỹ sư CNTT, Trường ĐH Kiến trúc Hà Nội, Khoa CNTT.
- Thời gian: 15 tuần, 05/10/2026 đến 17/01/2027.
- Còn thiếu trong hồ sơ: tên GVHD, họ tên sinh viên, MSSV, lớp (đang để trống, tô vàng trong các file .docx).

## 2. Các quyết định đã chốt (không đổi nếu người dùng không yêu cầu)

| Hạng mục | Quyết định |
|---|---|
| Phạm vi công trình | Nhà ở riêng lẻ xây mới, đến 5 tầng, miền Bắc |
| Nhóm vật liệu | Giữ nguyên 5 nhóm: (1) bê tông cốt thép; (2) thi công phần thô; (3) hoàn thiện; (4) khác và khung pháp lý; (5) kết cấu thép và bao che |
| Làm sâu | Tường bao che và tường ngăn. Bê tông cốt thép chỉ tối ưu nguồn cung, khối lượng lấy từ dự toán |
| Mục tiêu tối ưu | 3 mục tiêu: tổng chi phí, thời gian cung ứng, hệ số truyền nhiệt U |
| Học máy | XGBoost dự đoán đơn giá vật liệu. Bắt buộc có huấn luyện, huấn luyện trên máy người dùng (không dùng Colab) |
| Tối ưu | NSGA-II (pymoo); tự chuyển sang vét cạn khi không quá 20.000 tổ hợp |
| LLM | Qwen 4B qua Ollama (`qwen3:4b`), chỉ trích ràng buộc và viết lời giải thích; có dự phòng bằng regex |
| Đọc bản vẽ | Hệ luật (không phải học máy). Phân loại đối tượng bằng học máy là phương án 2, để sau |
| Không dùng | API AI trả phí; RAG làm lõi |
| Cơ sở dữ liệu | PostgreSQL, xem và sửa bằng DBeaver, mã hóa UTF-8, 19 bảng |
| Nhà cung cấp | Kết quả phải dẫn liên kết tới trang của nhà phân phối cụ thể, lấy từ cơ sở dữ liệu |
| Đặt tên | Tên bảng, cột, biến bằng tiếng Anh không dấu; nội dung và thông báo bằng tiếng Việt |
| Số liệu báo cáo | Không dùng dữ liệu mẫu hay mô phỏng để báo cáo độ chính xác |
| Máy người dùng | Windows, Ryzen 5 6600HS, 16 GB RAM, GPU 6 GB |

## 3. Luồng xử lý

Bản vẽ DWG/DXF -> đọc và phân loại layer -> nhận diện tường -> bóc tách vật liệu bằng quy tắc -> đo bóc khối lượng
-> tìm nguồn cung -> dự đoán giá (XGBoost) -> tối ưu (NSGA-II) -> giải thích (Qwen).

| Thành phần | Loại | Có huấn luyện |
|---|---|---|
| Nhận diện tường, bóc tách bằng quy tắc | Thuật toán hình học và hệ luật | Không |
| XGBoost | Học máy | Có |
| NSGA-II | Thuật toán tối ưu tiến hóa | Không |
| Qwen 4B | Mô hình ngôn ngữ có sẵn | Không |

## 4. Hiện trạng mã nguồn

`pytest`: 28 bài đạt; thêm 6 bài khi đặt `OPTIMAT_TEST_DATABASE_URL`.

**Đã có và có kiểm thử**

- Đọc DXF bằng ezdxf; DWG qua ODA File Converter (mới kiểm thử giả lập, chưa chạy ODA thật).
- Phân loại layer theo tên tiếng Việt, cho phép người dùng ghi đè vai trò layer.
- Chuyển mã TCVN3 sang Unicode (chưa thử trên file thật).
- Nhận diện tường bằng ghép cặp nét song song, lớp chiều dày 110/220/330; trừ lỗ cửa theo block.
- Bóc tách bằng quy tắc: ghi chú, hatch, layer, block -> vật liệu. Quy tắc trong `data/rules/material_rules.csv` (22 quy tắc).
- Công cụ khảo sát (`scripts/survey_drawings.py`) và chấm điểm (`scripts/evaluate_takeoff.py`) theo nhóm build/test.
- PostgreSQL 19 bảng (SQLAlchemy 2 + psycopg3), script tạo bảng và nạp dữ liệu, bản SQL cho DBeaver.
- Huấn luyện XGBoost: mục tiêu log, chia theo thời gian 70/15/15, đối chứng "tra bảng giá gần nhất" và Ridge.
- NSGA-II và vét cạn, lọc Pareto.
- Trích ràng buộc bằng regex; luồng agent cố định thứ tự bước; API FastAPI
  (`/api/health`, `/api/takeoff`, `/api/constraints/parse`, `/api/optimize`).

**Chưa có**

- Đăng nhập, phân quyền; API ghi vào các bảng `users`, `projects`, `project_files`, `takeoff_results`, `optimization_runs`.
- Trình thu thập giá; OSRM và bản đồ; LangGraph; đối chiếu dự toán Excel.
- Dữ liệu thật: mọi dữ liệu đi kèm đều là mẫu (`SAMPLE`) hoặc mô phỏng (`SYNTHETIC`).

**Vấn đề đã biết**

1. Chiều dài tường hụt khoảng một chiều dày ở mỗi góc (`drawing/walls.py`); trên bản vẽ mẫu là −2,75% với tường 220.
2. Chưa tách tầng: file có nhiều mặt bằng sẽ bị cộng gộp.
3. Chưa có bảng mã VNI; ghi chú VNI không khớp quy tắc.
4. Quy tắc hatch (ANSI31 = gạch xây, SOLID = bê tông) là giả định, chưa kiểm trên bản vẽ thật.
5. Trên dữ liệu mô phỏng, mốc tra bảng nhỉnh hơn XGBoost; cần thêm đặc trưng giá kỳ trước.
6. Đường gọi Ollama trong `agent/llm.py` chưa chạy với Ollama thật.
7. Bảng `standards` còn trống (người dùng có 123 bản ghi chưa cung cấp).
8. Chưa có bản vẽ nào thuộc nhóm test, nên chưa có số liệu độ chính xác dùng được.

## 5. Cấu trúc thư mục

```
src/optimat/
  config.py, schemas.py
  drawing/    encoding, dwg_convert, layer_classifier, dxf_reader, walls, material_rules, takeoff, evaluate
  catalog/    repository (đọc từ PostgreSQL hoặc CSV)
  db/         session, models (19 bảng)
  predict/    features (nguồn đặc trưng duy nhất), train, cost_model
  optimize/   problem (NSGA-II, vét cạn)
  agent/      llm (regex, Ollama), pipeline
  api/        main (FastAPI)
scripts/      init_db, export_sql, make_sample_data, make_sample_dxf, survey_drawings, evaluate_takeoff
data/         catalog (CSV mẫu), sample, rules, ground_truth
sql/          00_create_database, 01_schema, 02_seed_sample (sinh tự động, không sửa tay)
tests/        8 file kiểm thử
```

Nơi lưu dữ liệu: dữ liệu có cấu trúc trong PostgreSQL; bản vẽ trong `data/drawings/`, mô hình trong `models/`,
file gốc thu thập trong `data/raw/` (database chỉ lưu đường dẫn); quy tắc và đáp án đo tay là CSV trong dự án.

## 6. Cài đặt trên Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest

# PostgreSQL: tạo database optimat (UTF-8) rồi
$env:DATABASE_URL = "postgresql+psycopg://postgres:<mật khẩu>@localhost:5432/optimat"
python scripts/init_db.py --reset

# Huấn luyện thử và chạy API
$env:PYTHONPATH = "src"
python -m optimat.predict.train --data data/sample/prices_sample.csv --out models
uvicorn optimat.api.main:app --reload --app-dir src
```

Cần cài thêm khi dùng: ODA File Converter (đọc DWG), Ollama và `ollama pull qwen3:4b` (lời giải thích).

## 7. Việc tiếp theo, theo thứ tự

1. Lấy 3–5 bộ bản vẽ thật vào `data/drawings/build/`, chạy `survey_drawings.py`, bổ sung quy tắc cho các dòng "CHUA CO QUY TAC".
2. Sửa lỗi hụt chiều dài ở góc tường và thêm tách tầng.
3. Thêm bảng mã VNI; thử TCVN3 và ODA trên file thật.
4. Nhập đáp án đo tay (build 3–5 bộ, test 5–10 bộ), chạy `evaluate_takeoff.py`. Chỉ chỉnh quy tắc theo nhóm build.
5. Thu thập giá thật vào `price_records`, nạp 123 tiêu chuẩn, thêm đặc trưng giá kỳ trước, huấn luyện lại.
6. API ghi dự án và kết quả vào database; đăng nhập và phân quyền.
7. Bản đồ quãng đường (OSRM) trên giao diện Next.js (`frontend/`).
8. Chạy thử Ollama thật; chuyển luồng agent sang LangGraph.
9. Thực nghiệm, viết báo cáo.

## 8. Tài liệu đã làm (nằm ngoài thư mục mã)

- `De cuong DATN - OptiMat AI.docx`, `De cuong chi tiet DATN - OptiMat AI.docx`, `Bang ke hoach DATN - OptiMat AI.docx`
- `OptiMat AI - Quan ly co so du lieu.xlsx` (21 sheet, chú thích từng bảng và cột)
- Mockup giao diện 2 vai trò: https://claude.ai/artifact/61gv8j4or8PMGGFjERcsS7

## 9. Câu lệnh mở đầu gợi ý cho Claude Code

> Đọc CLAUDE.md, HANDOFF.md và PLAN.md. Chạy pytest để xác nhận 28 bài đạt. Sau đó làm việc số 1 ở mục 7 của
> HANDOFF.md với các bản vẽ trong data/drawings/build. Trả lời bằng tiếng Việt.
