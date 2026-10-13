# OptiMat AI

Đồ án tốt nghiệp ngành CNTT: hệ thống AI Agent hỗ trợ tối ưu lựa chọn vật liệu xây tường cho nhà ở
riêng lẻ ở miền Bắc Việt Nam, dùng XGBoost để dự đoán giá và NSGA-II để tối ưu đa mục tiêu.
Kế hoạch 15 tuần và danh sách việc nằm trong `PLAN.md`. Trao đổi với người dùng bằng tiếng Việt.

## Lệnh

```powershell
pytest                                                        # 58 bài; 66 bài khi có OPTIMAT_TEST_DATABASE_URL
python scripts/check_data.py [--strict]                       # kiểm soát dữ liệu; 0 lỗi mới commit (hook .githooks/pre-commit)
python scripts/survey_drawings.py <thư mục hoặc file bản vẽ>     # thống kê layer, hatch, block, ghi chú chưa có quy tắc
python scripts/evaluate_takeoff.py                            # so kết quả bóc tách với data/ground_truth
python scripts/view_takeoff.py <file.dxf> --open             # trang Kiểm tra bóc tách tự chứa (--steps: trang 5 bước)
$env:PYTHONPATH = "src"
python -m optimat.predict.train --from-db --out models        # huấn luyện từ bảng price_records
python -m optimat.predict.train --data data/sample/prices_sample.csv --out models
python scripts/init_db.py [--reset] [--prices <f.csv>] [--standards <f.csv>]   # tạo 19 bảng, nạp dữ liệu
python scripts/export_sql.py                                  # sinh lại sql/01, 02 sau khi sửa db/models.py
python scripts/build_materials_sql.py                         # sinh lại sql/03_materials.sql và data/catalog/{materials,wall_systems,material_aliases}.csv từ materials_master.xlsx
python scripts/build_upgrade_sql.py                           # sinh lại sql/04_upgrade.sql (nâng cấp database đã có, không mất dữ liệu)
uvicorn optimat.api.main:app --reload --app-dir src           # giao diện chung /app, trang kiểm tra /ui/takeoff, tài liệu /docs
```

Biến môi trường: `DATABASE_URL` (PostgreSQL; không đặt thì đọc CSV trong `data/catalog`),
`OPTIMAT_TEST_DATABASE_URL` (database kiểm thử riêng, bị xóa bảng mỗi lần chạy),
`OPTIMAT_CATALOG_OVERLAY` (thư mục CSV đè lên data/catalog khi không có PostgreSQL; conftest đặt `data/sample/catalog` = số MẪU),
`OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_PROVIDER` (mô hình ngôn ngữ của agent),
`ODA_CONVERTER_PATH` (đường dẫn ODAFileConverter.exe nếu không cài ở thư mục mặc định).

## Kiến trúc

Luồng: bản vẽ DWG/DXF -> nhận diện tường -> đo bóc -> tìm nguồn cung -> dự đoán giá -> tối ưu -> giải thích.

- `src/optimat/drawing/`: đọc DXF/DWG, phân loại layer, chuyển mã TCVN3, ghép cặp nét song song thành tường, đo bóc.
  Bản vẽ thật: `dxf_reader.py` mở block, nhận hatch bị phá (nét song song cách đều), đọc cung cửa và chữ trong thuộc tính;
  `plans.py` tách các mặt bằng tầng theo tiêu đề và đọc cao độ sàn; `walls.py` tự nhận layer tường bằng hình học
  (cặp nét đúng chiều dày, ưu tiên cặp có hatch gạch chéo ở giữa), bỏ thành cầu thang, gộp tường trùng, nối góc L
  tới giao trục tim, nối khe cửa (cung cánh cửa, block, nét kính) rồi trừ lỗ mở; `takeoff.py` xác định tường bao che
  bằng tia dò ra ngoài nhà và có `takeoff_plans()` đo từng mặt bằng.
  `material_rules.py` gán vật liệu theo thiết kế từ ghi chú, hatch, layer, block; `evaluate.py` chấm điểm và khảo sát;
  `viewer.py` + `viewer_template.html` dựng trang xem từng bước (chỉ hiển thị kết quả đo bóc, không tính lại).
  Trang Kiểm tra bóc tách (`review_app.html`, `/ui/takeoff`): bản vẽ bên trái, danh sách nhận dạng bên phải; người dùng
  loại bỏ, sửa loại/vai trò/vật liệu, vẽ thêm tường, thêm/sửa cửa, sửa chiều cao rồi xác nhận. Trang chỉ tính tạm;
  `review.py` (`/api/takeoff/confirm`) là công thức chốt duy nhất; trả bảng vật liệu + giá, lưu `takeoff_results` khi
  gửi `project_id` (trang: `/ui/takeoff?project=<id>`) và có PostgreSQL. Sau xác nhận, trang gọi `/api/optimize`.
- **Một bộ mã vật liệu xuyên suốt** (13/10/2026): bóc tách, trang kiểm tra, tối ưu và tra giá đều dùng mã của danh mục
  thật (`materials.material_id` như GN01, AAC01; `wall_systems.wall_system_id` như W-GN01-220). Quy tắc trả họ
  (`family`) hoặc mã; `Catalog.resolve_wall()` quy đổi theo `detect_class`; một phương án thì chọn, nhiều thì để người dùng
  chọn (`material_candidates`), không có thì để trống kèm cảnh báo. Tên gọi khác (`material_aliases`) tự sinh quy tắc ghi chú.
  `catalog/pricing.py` lập bảng vật liệu (gạch + vữa theo định mức của phương án) và giá có trong `supplier_materials`
  / `price_records` (ACTUAL); xác nhận trên trang kiểm tra trả bảng này. Tối ưu chỉ dùng phương án đủ số liệu
  (`Catalog.wall_view().ready`), phương án thiếu số được liệt kê trong notes; `keep_design_material` giữ phương án thiết kế.
  Luồng agent có bước `step_bill` và công cụ `tra_gia_theo_thiet_ke`. API: `/api/catalog/wall-materials`, `/api/price/bill`,
  `/api/agent/run`.
- `data/rules/material_rules.csv`: bộ quy tắc, sửa bằng Excel. `data/ground_truth/`: đáp án đo tay (cột `split` = build hoặc test).
- `src/optimat/catalog/`: danh mục vật liệu, nhà cung cấp, phương tiện (PostgreSQL hoặc CSV).
- `src/optimat/db/`: lược đồ SQLAlchemy 19 bảng (danh mục, nguồn cung và giá, người dùng và dự án, vận hành) và kết nối.
- `data/catalog/materials_master.xlsx`: nguồn của danh mục 75 vật liệu, phương án tường (`wall_systems`), quan hệ (`material_relations`).
  Sửa số liệu ở đây rồi sinh lại SQL; mỗi thông số có mã nguồn, ô chưa có nguồn để trống.
- `sql/`: bản SQL sinh tự động, không sửa tay. Database mới: 00 → 01 → 02 (mẫu) → 03. Database đã có: 04 → 03;
  04 thêm bảng, cột, ràng buộc còn thiếu, cuối file có truy vấn kiểm tra (rỗng là đủ). Sửa `db/models.py` thì sinh lại 01, 02, 04.
- `src/optimat/predict/`: đặc trưng, huấn luyện, nạp mô hình.
- `src/optimat/optimize/`: bài toán 3 mục tiêu (tổng chi phí, thời gian cung ứng, hệ số truyền nhiệt), NSGA-II và vét cạn.
- `src/optimat/agent/`: trích ràng buộc từ câu tiếng Việt (Ollama, dự phòng bằng regex), luồng điều phối.
- `src/optimat/api/`: FastAPI. `src/optimat/web/app.html`: giao diện chung `/app` (theo `docs/mockup/`), không có bước build;
  người dùng: đo bóc (nhúng `/ui/takeoff`), vật liệu và giá, tối ưu + trợ lý; quản trị: kiểm soát dữ liệu, danh mục, giá, mô hình.
  Trang kiểm tra ghi mặt bằng đã chốt vào localStorage `optimat-confirmed` để `/app` gộp các tầng (bản chính thức: `takeoff_results`).
- `src/optimat/data_check.py` + `scripts/check_data.py` + `/api/data/check`: kiểm soát dữ liệu (lỗi chặn commit, cảnh báo, ghi chú).
  Quy trình: `docs/QUY_TRINH_DU_LIEU.md`. Tài liệu, mẫu thu thập, mockup: `docs/`. Bản vẽ thật: `data/drawings/build/` (không vào git).

## Quy tắc bắt buộc

- **Một nguồn mã đặc trưng**: mọi nơi tạo đặc trưng cho mô hình giá đều gọi `predict/features.py`. Không chép logic.
- **Chia dữ liệu theo thời gian**, không chia ngẫu nhiên. Tập kiểm tra chỉ chạy một lần khi chốt mô hình.
- **Luôn so với mốc "tra bảng giá gần nhất"** khi báo cáo kết quả mô hình.
- **Loại dữ liệu**: mọi dòng có `data_kind` là `ACTUAL`, `SAMPLE` hoặc `SYNTHETIC`. Không dùng số liệu
  từ dữ liệu `SYNTHETIC` hay `SAMPLE` để báo cáo độ chính xác. Dữ liệu đi kèm hiện đều là mẫu hoặc mô phỏng.
- **Agent**: mô hình ngôn ngữ chỉ trích ràng buộc và viết lời; số liệu, giá, liên kết lấy nguyên từ kết quả
  công cụ. Thứ tự các bước do mã cố định. Hệ thống phải chạy được khi tắt LLM.
- **Liên kết nhà cung cấp** chỉ lấy từ cơ sở dữ liệu, không để mô hình sinh ra.
- **Mô hình ngôn ngữ**: mô hình của OpenAI gọi qua API (`OPENAI_API_KEY`, `OPENAI_MODEL`, mặc định `gpt-5.6-luna`), điều hướng
  agent bằng gọi công cụ (`agent/orchestrator.py`). Không ghi khóa API vào mã. Mất mạng hoặc thiếu khóa thì chạy luồng cố định
  với regex (`LLM_PROVIDER=none` để ép chế độ này; `ollama` để dùng mô hình cục bộ). Không dùng RAG làm lõi.
  Câu trả lời của mô hình có con số không nằm trong kết quả công cụ thì bị thay bằng bản dữ kiện gốc.
  XGBoost vẫn huấn luyện trên máy; quyết định đổi sang OpenAI chỉ áp dụng cho mô hình ngôn ngữ (12/10/2026).
- **Mã kế thừa**: `drawing/dwg_convert.py` và `drawing/layer_classifier.py` chỉnh sửa từ dự án
  floor-plan-exit-router (MIT). Khi lấy thêm mã bên ngoài, cập nhật `THIRD_PARTY_NOTICES.md`.
- **Bóc tách bằng quy tắc**: thêm quy tắc vào CSV, không viết cứng trong mã. Không quy tắc nào khớp thì để trống
  và báo trong `unmatched`, không đoán. Chỉ chỉnh quy tắc theo bản vẽ `build`; bản vẽ `test` chỉ dùng để báo cáo.
- Chú thích và thông báo cho người dùng viết bằng tiếng Việt. Mỗi thay đổi phải giữ `pytest` đạt.
- Database PostgreSQL phải mã hóa UTF-8.

## Phạm vi

Nhà ở riêng lẻ xây mới đến 5 tầng. Làm sâu cho tường bao che và tường ngăn. Bê tông cốt thép chỉ tối ưu
nguồn cung (khối lượng lấy từ dự toán). Không kiểm tra chịu lực. Không xử lý PDF quét hay ảnh.

## Hiện trạng (13/10/2026)

Đã có và có kiểm thử: đọc DXF, chuyển DWG qua ODA (chỉ kiểm thử giả lập), phân loại layer, nhận diện tường
110/220/330, đo bóc có trừ cửa, bóc tách vật liệu bằng quy tắc (mới thử trên bản vẽ mẫu tự tạo), PostgreSQL 19 bảng (5 nhóm vật liệu đã nạp), huấn luyện XGBoost kèm đối chứng, NSGA-II, trích ràng buộc
bằng regex, API.

Các bảng `users`, `projects`, `project_files`, `takeoff_results`, `optimization_runs`, `model_versions`,
`audit_logs`, `material_aliases`, `standards`, `material_standards`, `labor_rates` đã có lược đồ và kiểm thử
lưu/đọc, nhưng API và các module chưa ghi vào. Bảng `standards` còn trống (người dùng có 123 bản ghi cần nạp).

Chưa có: đăng nhập và phân quyền (trang /app chỉ chọn vai trò), bản đồ trên giao diện, trình thu thập giá,
bge-m3, OSRM và bản đồ, LangGraph, đối chiếu dự toán Excel, dữ liệu thật.

Bản vẽ thật đã thử (13/10/2026, nhóm build, chưa có đáp án đo tay): nhà phố 4 mặt bằng và nhà dân 3 mặt bằng
(xuất qua phần mềm xem nhanh: hatch bị phá, tường trên layer theo nét bút), file kết cấu (bỏ qua đúng).
Tường bao nhận tốt; còn nhận nhầm thành cầu thang, khung cửa sổ, bồn hoa xây trên layer chung; bỏ sót tường vẽ một nét.
Các ngưỡng tự nhận layer (config.py) mới chỉnh trên 2 bản vẽ này.

Vấn đề đã biết:
- Bộ quy tắc hatch (ANSI31, SOLID) là quy ước giả định. Hatch bị phá mất tên mẫu nên không dùng để gán vật liệu được.
- Danh mục thật: chỉ W-GN01-110 và W-GN01-220 đủ số để tối ưu; các phương án khác thiếu định mức, khối lượng tường hoặc λ
  (xem `Catalog.wall_view().missing`). Chưa có phương án lớp 330. Mọi vật liệu tường chưa có hao hụt (`waste_pct`):
  bảng vật liệu không cộng hao hụt, tối ưu dùng `config.WASTE_FACTOR`. VU04 (vữa AAC) tính theo tấn nhưng chưa có khối
  lượng thể tích nên chưa đổi được từ m³. Giá trong `data/catalog` là đại lý MẪU.
- Cửa nhận từ khe tường lấy cao mặc định (2,2 m cửa đi, 1,4 m cửa sổ).
- Trên dữ liệu mô phỏng, mốc tra bảng nhỉnh hơn XGBoost; cần thêm đặc trưng giá kỳ trước.
- Đường gọi OpenAI mới kiểm thử bằng hàm giả, chưa chạy với API thật; mã mô hình `gpt-5.6-luna` chưa được xác nhận trên trang OpenAI.
- Chưa ghi lần tối ưu vào `optimization_runs`. `/api/agent/run` dùng agent gọi công cụ khi có khóa OpenAI, ngược lại luồng cố định.
