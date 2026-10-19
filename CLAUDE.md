# OptiMat AI

Đồ án tốt nghiệp ngành CNTT: hệ thống AI Agent hỗ trợ tối ưu lựa chọn vật liệu xây tường cho nhà ở
riêng lẻ ở miền Bắc Việt Nam, dùng XGBoost để dự đoán giá và NSGA-II để tối ưu đa mục tiêu.
Kế hoạch 15 tuần và danh sách việc nằm trong `PLAN.md`. Trao đổi với người dùng bằng tiếng Việt.

## Lệnh

```powershell
pytest                                                        # 134 bài; 146 bài khi có OPTIMAT_TEST_DATABASE_URL (đặt PYTHONIOENCODING=utf8)
python scripts/check_data.py [--strict]                       # kiểm soát dữ liệu; 0 lỗi mới commit (hook .githooks/pre-commit)
python scripts/survey_drawings.py <thư mục hoặc file bản vẽ>     # thống kê layer, hatch, block, ghi chú chưa có quy tắc
python scripts/evaluate_takeoff.py                            # so kết quả bóc tách với data/ground_truth
python scripts/view_takeoff.py <file.dxf> --open             # trang Kiểm tra bóc tách tự chứa (--steps: trang 5 bước)
python scripts/concept_report.py <file.dxf> --open           # đối chiếu Quy ước v1.0: <tên>.khai_niem.html (23 điều khoản QU, nguồn từng bộ phận)
python scripts/build_material_check_xlsx.py                  # docs/du-lieu/...Doi chieu vat lieu ban ve.xlsx: định nghĩa vật liệu phần thô + đối chiếu bản vẽ build
$env:PYTHONPATH = "src"
python -m optimat.predict.train --from-db --out models        # huấn luyện từ bảng price_records
python -m optimat.predict.train --data data/sample/prices_sample.csv --out models
python scripts/init_db.py [--reset] [--reload-rules] [--prices <f.csv>] [--standards <f.csv>]   # tạo 26 bảng, nạp danh mục + quy tắc
python scripts/export_sql.py                                  # sinh lại sql/01, 02, 05 (quy tắc) sau khi sửa db/models.py hoặc data/rules
python scripts/build_materials_sql.py                         # sinh lại sql/03_materials.sql và data/catalog/{materials,wall_systems,material_aliases,material_relations}.csv từ materials_master.xlsx
python scripts/build_upgrade_sql.py                           # sinh lại sql/04_upgrade.sql (nâng cấp database đã có, không mất dữ liệu)
uvicorn optimat.api.main:app --reload --app-dir src           # giao diện chung /app, trang kiểm tra /ui/takeoff, tài liệu /docs
```

Biến môi trường: `DATABASE_URL` (PostgreSQL: danh mục, họ vật liệu, đơn giá nhân công, quy tắc, định mức đều đọc từ database;
không đặt thì đọc CSV trong `data/catalog`, `data/rules` — chỉ dùng cho kiểm thử),
`OPTIMAT_TEST_DATABASE_URL` (database kiểm thử riêng, bị xóa bảng mỗi lần chạy),
`OPTIMAT_CATALOG_OVERLAY` (thư mục CSV đè lên data/catalog khi không có PostgreSQL; conftest đặt `data/sample/catalog` = số MẪU),
`OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_PROVIDER` (mô hình ngôn ngữ của agent),
`ODA_CONVERTER_PATH` (đường dẫn ODAFileConverter.exe nếu không cài ở thư mục mặc định).

## Kiến trúc

Luồng: bản vẽ DWG/DXF -> nhận diện tường -> đo bóc -> tìm nguồn cung -> dự đoán giá -> tối ưu -> giải thích.

- `src/optimat/drawing/`: đọc DXF/DWG, phân loại layer, chuyển mã TCVN3, ghép cặp nét song song thành tường, đo bóc.
  Bản vẽ thật: `dxf_reader.py` mở block, nhận hatch bị phá (nét song song cách đều), đọc cung cửa và chữ trong thuộc tính;
  quy tắc chung của `dxf_reader.py`: mọi tọa độ đổi sang WCS (đối tượng 2D ghi theo OCS, block lật làm OCS khác WCS);
  `geometry_mismatch()` đối chiếu từng điểm với ezdxf mỗi lần `read_dxf` (lệch thì cảnh báo, giữ qua `crop`), test chạy trên mọi bản vẽ trong `data/drawings/build`, `test`;
  `plans.py` tách các mặt bằng tầng theo tiêu đề và đọc cao độ sàn; `walls.py` tự nhận layer tường bằng hình học
  (cặp nét đúng chiều dày, ưu tiên cặp có hatch gạch chéo ở giữa), bỏ thành cầu thang, gộp tường trùng, nối góc L
  tới giao trục tim, nối khe cửa (cung cánh cửa, block, nét kính) rồi trừ lỗ mở; `takeoff.py` xác định tường bao che
  bằng tia dò ra ngoài nhà và có `takeoff_plans()` đo từng mặt bằng.
  Chiều cao tầng và kích thước cửa là thông số dự án (bảng `projects`: `floor_height_mm`, `door_/window_width_mm`,
  `door_/window_height_mm`), truyền vào đo bóc qua `OpeningDefaults` và `project_id` (Form) của các API đo bóc; không có số
  mặc định (Quy ước B7). Kích thước cửa: thuộc tính block → quy tắc block → thông số dự án; thiếu thì không trừ lỗ mở đó và
  cảnh báo. Thiếu chiều cao tầng (nhập tay, cao độ sàn, dự án) thì `groups` rỗng, `height_source` = "chưa có".
  `material_rules.py` gán vật liệu theo thiết kế từ ghi chú, hatch, layer, block; `evaluate.py` chấm điểm và khảo sát;
  `render.py` vẽ lại bản vẽ gốc như phần mềm CAD (ezdxf drawing → SVG: màu ACI, kiểu nét, chữ TCVN3 đổi Unicode,
  hatch, kích thước, block; nền đen, nét 1 px) làm nền trang kiểm tra, cắt theo từng mặt bằng + trang "Toàn bộ bản vẽ"
  có khung các mặt bằng đã tách; ma trận trong `<g class="cad">` đưa về đúng tọa độ lớp nhận dạng. Vẽ mất ~25 s với file 8–20 MB.
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
- **Phần thô** (17/10/2026, `src/optimat/rough/`): bóc toàn bộ phần thô ra công tác và vật liệu mua về; tối ưu NSGA-II vẫn
  chỉ cho tường. `walls.py` xây (trừ cửa, lanh tô, cột, dầm), trát, lanh tô; `areas.py` đường bao + phòng trên lưới 10 mm → sàn,
  cán nền, nền trệt, chống thấm; `columns.py` cột từ vùng tô đặc; `beams.py` dầm nhập tay hoặc suy từ tường + cột; `stairs.py`
  thang (nhập tay); `steel.py` thép theo hàm lượng từng cấu kiện, móng nhập tay; `materials.py` công tác → vữa/bê tông → vật liệu
  (định mức gạch của `wall_systems`, cấp phối vữa = quan hệ COMPOSED_OF, còn lại `data/rules/dinh_muc_phan_tho.csv`);
  `takeoff.py` `compute_rough` (công thức chốt duy nhất) và `rough_from_drawing`. Thông số công trình (`ProjectParams`) và
  định mức thiếu thì để trống + cảnh báo, không điền mặc định (Quy ước B7). API `/api/takeoff/rough/auto`, `/api/takeoff/rough`
  (lưu `takeoff_results` với `result.kind = "rough"`); tab "Phần thô" trên trang kiểm tra, mục "Phần thô" trên `/app`; công cụ
  agent `boc_phan_tho`, bước `step_rough` khi có thông số. Kế hoạch và trạng thái: `SPRINTS.md`, nhật ký: `NHAT_KY.md`.
- `data/rules/*.csv` là nguồn nạp của 6 bảng `material_rules`, `room_rules`, `rough_norms`, `material_notes` (ghi chú vật liệu
  phần thô, so nguyên từ, `drawing/material_notes.py`), `drawing_concepts` (`concepts.csv`), `convention_clauses` (`quy_uoc.csv`) (sửa bằng Excel rồi `init_db.py --reload-rules`
  hoặc sinh lại `sql/05_rules.sql`; có `DATABASE_URL` thì mã chỉ đọc bảng). `data/rules/material_rules.csv`: bộ quy tắc. `data/rules/room_rules.csv`: tên phòng (WC, ban công) cho chống thấm.
  `data/rules/dinh_muc_phan_tho.csv`: định mức trát, cán nền, cấp phối bê tông trộn tại chỗ, dây buộc, chống thấm, cốp pha
  (ô số chờ tra TT 38/2026, có số thì bắt buộc ghi số hiệu bảng). `data/ground_truth/`: đáp án đo tay (cột `split` = build hoặc test).
- `src/optimat/catalog/`: danh mục vật liệu, nhà cung cấp, phương tiện (PostgreSQL hoặc CSV).
- `src/optimat/db/`: lược đồ SQLAlchemy 26 bảng (danh mục, nguồn cung và giá, người dùng và dự án, vận hành) và kết nối.
- `data/catalog/materials_master.xlsx`: nguồn của danh mục 93 vật liệu (75 + 18 vật liệu phần thô thêm 19/10/2026), phương án tường (`wall_systems`), quan hệ (`material_relations`).
  Sửa số liệu ở đây rồi sinh lại SQL; mỗi thông số có mã nguồn, ô chưa có nguồn để trống.
- `sql/`: bản SQL sinh tự động, không sửa tay. Database mới: 00 → 01 → 02 (mẫu) → 03 → 05. Database đã có: 04 → 03 → 05;
  04 thêm bảng, cột, ràng buộc còn thiếu, cuối file có truy vấn kiểm tra (rỗng là đủ). Sửa `db/models.py` thì sinh lại 01, 02, 04, 05.
  Họ vật liệu: bảng `material_families` (nguồn `data/catalog/material_families.csv`, `is_wall` = họ tường), `materials.family` là khóa ngoại.
  Đơn giá nhân công: bảng `labor_rates` (theo `Constraints.province`, bản mới nhất); thiếu thì chi phí nhân công = 0 kèm ghi chú.
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

Nhà ở riêng lẻ xây mới đến 5 tầng. Bóc khối lượng toàn bộ phần thô ra vật liệu (hướng nga chốt 17/10/2026, chờ giảng viên
duyệt); tối ưu đa mục tiêu làm sâu cho tường bao che và tường ngăn. Không lập dự toán, không kiểm tra chịu lực. Không xử lý PDF quét hay ảnh.

## Hiện trạng (13/10/2026)

Đã có và có kiểm thử: đọc DXF, chuyển DWG qua ODA (chỉ kiểm thử giả lập), phân loại layer, nhận diện tường
110/220/330, đo bóc có trừ cửa, bóc tách vật liệu bằng quy tắc (mới thử trên bản vẽ mẫu tự tạo), PostgreSQL 26 bảng (5 nhóm vật liệu đã nạp), huấn luyện XGBoost kèm đối chứng, NSGA-II, trích ràng buộc
bằng regex, API.

Các bảng `users`, `projects`, `project_files`, `takeoff_results`, `optimization_runs`, `model_versions`,
`audit_logs`, `material_aliases`, `standards`, `material_standards` đã có lược đồ và kiểm thử
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
  bảng vật liệu và tối ưu đều không cộng hao hụt (có ghi chú). Bảng `labor_rates` thật còn trống (số MẪU ở `data/sample/catalog`). VU04 (vữa AAC) tính theo tấn nhưng chưa có khối
  lượng thể tích nên chưa đổi được từ m³. Giá trong `data/catalog` là đại lý MẪU.
- Cửa nhận từ khe tường: rộng theo khe, cao theo thông số cửa của dự án (chưa đọc bảng thống kê cửa, QU-15).
- Trên dữ liệu mô phỏng, mốc tra bảng nhỉnh hơn XGBoost; cần thêm đặc trưng giá kỳ trước.
- Đường gọi OpenAI mới kiểm thử bằng hàm giả, chưa chạy với API thật; mã mô hình `gpt-5.6-luna` chưa được xác nhận trên trang OpenAI.
- Chưa ghi lần tối ưu vào `optimization_runs`. `/api/agent/run` dùng agent gọi công cụ khi có khóa OpenAI, ngược lại luồng cố định.
