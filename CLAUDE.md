# OptiMat AI

Đồ án tốt nghiệp ngành CNTT: hệ thống AI Agent hỗ trợ tối ưu lựa chọn vật liệu xây tường cho nhà ở
riêng lẻ ở miền Bắc Việt Nam, dùng XGBoost để dự đoán giá và NSGA-II để tối ưu đa mục tiêu.
Kế hoạch 15 tuần và danh sách việc nằm trong `PLAN.md`. Trao đổi với người dùng bằng tiếng Việt.

## Lệnh

```powershell
pytest                                                        # 294 bài (21/10/2026: 291 đạt, 3 xfail), bài cần PostgreSQL chỉ chạy khi có OPTIMAT_TEST_DATABASE_URL; conftest bỏ .env và DATABASE_URL (đặt PYTHONIOENCODING=utf8)
python scripts/check_data.py [--strict]                       # kiểm soát dữ liệu; 0 lỗi mới commit (hook .githooks/pre-commit)
python scripts/survey_drawings.py <thư mục hoặc file bản vẽ>     # thống kê layer, hatch, block, ghi chú chưa có quy tắc
python scripts/ingest_cad.py <thư mục hoặc file> [--store data/uploads]   # tiếp nhận hồ sơ CAD (S02): kiểm tra file, hash/phiên bản, chuyển DWG có log, <tên>.inventory.json; trang /tiep-nhan, API /api/ingest
python scripts/make_ingest_samples.py                         # sinh lại 15 file CAD mẫu lỗi/hợp lệ + expected.json ở data/sample/ingest
python scripts/make_s03_fixtures.py [--schema]                   # S03: sinh 15 bản vẽ con chuẩn (SYNTHETIC) từ data/ground_truth/s03/cases.json; --schema: docs/schema/ho_so_chuan_hoa.schema.json; trang /mapping
python scripts/evaluate_takeoff.py                            # so kết quả bóc tách với data/ground_truth
python scripts/batch_takeoff.py <thư mục hoặc file...>        # bóc phần thô hàng loạt, gộp reports/batch/tong_hop.xlsx: đối tượng nhận được, công tác trống + lý do, cảnh báo theo bản vẽ
python scripts/concept_report.py <file.dxf>                  # đối chiếu Quy ước v1.0: <tên>.khai_niem.json (23 điều khoản QU, nguồn từng bộ phận)
python scripts/build_material_check_xlsx.py                  # docs/du-lieu/...Doi chieu vat lieu ban ve.xlsx: định nghĩa vật liệu phần thô + đối chiếu bản vẽ build
$env:PYTHONPATH = "src"
python -m optimat.predict.train --from-db --out models        # huấn luyện từ bảng price_records
python -m optimat.predict.train --data data/sample/prices_sample.csv --out models
python scripts/create_admin.py --email <email> [--name <tên>]  # đặt lại quản trị viên (mật khẩu nhập ở dấu nhắc); admin đầu tiên cũng tạo được ngay trên /dang-nhap khi database chưa có admin
python scripts/init_db.py [--reset] [--reload-rules] [--prices <f.csv>] [--standards <f.csv>]   # tạo 26 bảng, nạp danh mục + quy tắc
python scripts/export_sql.py                                  # sinh lại sql/01, 02, 05 (quy tắc) sau khi sửa db/models.py hoặc data/rules
python scripts/build_materials_sql.py                         # sinh lại sql/03_materials.sql và data/catalog/{materials,wall_systems,material_aliases,material_relations}.csv từ materials_master.xlsx
python scripts/build_upgrade_sql.py                           # sinh lại sql/04_upgrade.sql (nâng cấp database đã có, không mất dữ liệu)
python scripts/import_dealers.py --src D:\daily [--no-db]     # nạp danh bạ đại lý thật (gop_dai_ly.py + geocode_cache.csv) vào data/catalog/suppliers.csv và bảng suppliers, không ghi đè sửa đổi
python scripts/import_price_bulletin.py <file.pdf> [--no-db]   # công bố giá Sở XD: công ty/bãi -> suppliers (CBG-...), giá ghép mã theo data/rules/cong_bo_gia.csv -> price_records (BULLETIN); bảng duyệt data/cong_bo_gia/<số>.csv
python scripts/export_boq.py <kien_truc.dxf> --structural <ket_cau.dxf> --height 3300 --params thong_so.json --out boq.xlsx   # BOQ phần thô ra Excel (S07)
python scripts/evaluate_recognition.py                        # độ chính xác nhận diện tường so với đáp án data/ground_truth/plans/*.gt.json
python scripts/list_objects.py [file.dxf ...]                 # liệt kê tường, cửa, cặp nét bị loại (kèm lý do), block khớp ký hiệu
uvicorn optimat.api.main:app --reload --app-dir src           # API, tài liệu /docs
cd frontend && npm run dev                                    # giao diện web http://localhost:3000 (Next.js 16, React 19, Tailwind 4)
```

Biến môi trường (đặt trong file `.env` ở thư mục gốc, chép từ `.env.example`, không vào Git; pytest bỏ qua `.env`): `DATABASE_URL` (PostgreSQL: danh mục, họ vật liệu, đơn giá nhân công, quy tắc, định mức đều đọc từ database;
không đặt thì đọc CSV trong `data/catalog`, `data/rules` — chỉ dùng cho kiểm thử),
`OPTIMAT_TEST_DATABASE_URL` (database kiểm thử riêng, bị xóa bảng mỗi lần chạy),
`OPTIMAT_CATALOG_OVERLAY` (thư mục CSV đè lên data/catalog khi không có PostgreSQL; conftest đặt `data/sample/catalog` = số MẪU),
`OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_PROVIDER` (mô hình ngôn ngữ của agent),
`OPTIMAT_SECRET_KEY` (khóa ký cookie đăng nhập; thiếu thì sinh mỗi lần khởi động),
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
  cảnh báo; cửa nhận từ khe tường thiếu cao vẫn giữ trong danh sách (cao trống) để trang kiểm tra nhập. Thiếu chiều cao tầng (nhập tay, cao độ sàn, dự án) thì `groups` rỗng, `height_source` = "chưa có".
  `material_rules.py` gán vật liệu theo thiết kế từ ghi chú, hatch, layer, block; `evaluate.py` chấm điểm và khảo sát;
  `render.py` vẽ lại bản vẽ gốc như phần mềm CAD (ezdxf drawing → SVG: màu ACI, kiểu nét, chữ TCVN3 đổi Unicode,
  hatch, kích thước, block; nền đen, nét 1 px) làm nền trang kiểm tra, cắt theo từng mặt bằng + trang "Toàn bộ bản vẽ"
  có khung các mặt bằng đã tách; ma trận trong `<g class="cad">` đưa về đúng tọa độ lớp nhận dạng. Vẽ mất ~25 s với file 8–20 MB.
  `viewer.py` gom dữ liệu cho trang Kiểm tra bóc tách (chỉ hiển thị kết quả đo bóc, không tính lại).
  Trang Kiểm tra bóc tách (`/do-boc` của frontend): bản vẽ bên trái, danh sách nhận dạng bên phải; người dùng
  loại bỏ, sửa loại/vai trò/vật liệu, vẽ thêm tường, thêm/sửa cửa, sửa chiều cao rồi xác nhận. Trang chỉ tính tạm;
  `review.py` (`/api/takeoff/confirm`) là công thức chốt duy nhất; trả bảng vật liệu + giá, lưu `takeoff_results` khi
  gửi `project_id` (trang: `/do-boc?project=<id>`) và có PostgreSQL. Sau xác nhận, trang gọi `/api/optimize`.
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
  `takeoff.py` `compute_rough` (công thức chốt duy nhất) và `rough_from_drawing`.
  **Bản vẽ kết cấu** (21/10/2026): `drawing/sheets.py` nhận 14 loại bản vẽ phần thô theo tiêu đề (`data/rules/loai_ban_ve.csv`),
  báo loại còn thiếu; `rough/structural.py` đọc mặt bằng móng/dầm: móng đếm theo ký hiệu M…, dầm và
  đà kiềng đo theo cặp nét gần ký hiệu D…/ĐK… (`data/rules/ky_hieu_cau_kien.csv`), tiết diện ghi bằng chữ thắng, số tầng đọc
  từ tiêu đề ("LẦU 2-3-4" = 3). Có dầm kết cấu thì không suy dầm trên mặt bằng kiến trúc. API `/api/takeoff/rough/auto` nhận
  thêm `structural_file`, `structural_scale` (để trống = tự suy). Hình chi tiết: `drawing/dimensions.py` đọc DIMENSION và suy
  tỷ lệ từng hình (hiển thị / đo); `structural.py` đọc mặt cắt MC, GỐI, NHỊP ra kích thước móng (`footing_detail_sizes`) và
  tiết diện dầm (`beam_detail_sizes`); `rough/foundations.py` chỉ tính khối lượng từ các kích thước đó. Các CSV quy tắc thêm từ 19/10 (`loai_ban_ve`, `ky_hieu_cau_kien`, `do_tin_cay`, `bang_thep`,
  `thep_kg_m`, `loai_mai`, `ho_tro_cau_kien`, `cong_bo_gia`) chưa có bảng PostgreSQL và chưa qua `check_data` (đọc thẳng file).
  Chưa đọc: cốt thép Ø trên hình chi tiết (thép lấy từ bảng thống kê, S07), mặt bằng sàn, cầu thang, mái, lanh tô. Thông số công trình (`ProjectParams`) và
  định mức thiếu thì để trống + cảnh báo, không điền mặc định (Quy ước B7). API `/api/takeoff/rough/auto`, `/api/takeoff/rough`
  (lưu `takeoff_results` với `result.kind = "rough"`); tab "Phần thô" trên trang kiểm tra, trang `/phan-tho`; công cụ
  agent `boc_phan_tho`, bước `step_rough` khi có thông số. Kế hoạch và trạng thái: `SPRINTS.md`, nhật ký: `NHAT_KY.md`.
- `data/rules/*.csv` là nguồn nạp của 6 bảng `material_rules`, `room_rules`, `rough_norms`, `material_notes` (ghi chú vật liệu
  phần thô, so nguyên từ, `drawing/material_notes.py`), `drawing_concepts` (`concepts.csv`), `convention_clauses` (`quy_uoc.csv`) (sửa bằng Excel rồi `init_db.py --reload-rules`
  hoặc sinh lại `sql/05_rules.sql`; có `DATABASE_URL` thì mã chỉ đọc bảng). `data/rules/material_rules.csv`: bộ quy tắc. `data/rules/room_rules.csv`: tên phòng (WC, ban công) cho chống thấm.
  `data/rules/dinh_muc_phan_tho.csv`: định mức trát, cán nền, cấp phối bê tông trộn tại chỗ, dây buộc, chống thấm, cốp pha
  (ô số chờ tra TT 38/2026, có số thì bắt buộc ghi số hiệu bảng). `data/ground_truth/`: đáp án đo tay (cột `split` = build hoặc test).
- `src/optimat/catalog/`: danh mục vật liệu, nhà cung cấp, phương tiện (PostgreSQL hoặc CSV).
- **Đại lý** (19/10/2026): ~2.800 đại lý thật miền Bắc (Trang Vàng, Hòa Phát, OpenStreetMap; thu thập ở `D:\daily`), chưa có giá,
  phần lớn chưa có tọa độ; `lat`, `lon`, `lead_time_days` để trống được, tối ưu bỏ qua đại lý thiếu (có ghi chú). Trang
  `/dai-ly`: bản đồ Leaflet (nền Esri: mạng chặn `*.openstreetmap.org`, CARTO đòi khóa API), danh sách lọc theo tỉnh, mở chi tiết để sửa,
  bấm bản đồ để đặt vị trí, ghi chép (dòng có ngày giờ thêm vào đầu `note`); lưu qua `/api/admin/tables/suppliers`.
  **Công bố giá** (19/10/2026): `catalog/bulletin.py` đọc PDF công bố giá (pdfplumber, bảng 4 và 12 cột), ghép mã bằng
  `data/rules/cong_bo_gia.csv` (quy tắc đầu tiên khớp, kèm đơn vị và hệ số đổi giá, vd. kg -> tấn x1000); không khớp thì để trống.
  Giá vào `price_records` (mức BULLETIN, chưa VAT) nên tự hiện trong bảng vật liệu (`/api/price/bill`); `supplier_materials` không nhận mức này.
  Đại lý, giá đại lý, phương tiện MẪU chuyển sang `data/sample/catalog` (chỉ kiểm thử); `data/catalog/supplier_materials.csv`, `vehicles.csv` rỗng.
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
- `src/optimat/api/`: FastAPI (chỉ API). Giao diện web: `frontend/` (Next.js 16 App Router, React 19, Tailwind CSS 4, TypeScript;
  xem `frontend/README.md`), gọi API qua `/api` (rewrite trong `frontend/next.config.ts`, biến `OPTIMAT_API`).
  Người dùng: `/do-boc` (kiểm tra bóc tách), `/vat-lieu`, `/phan-tho`, `/toi-uu` + trợ lý, `/tiep-nhan`, `/mapping`;
  quản trị: `/tong-quan`, `/du-an`, `/nguoi-dung`, `/kiem-soat`, `/danh-muc`, `/dai-ly`, `/gia`, `/nhan-dien`, `/quy-tac`, `/co-so-du-lieu`, `/mo-hinh`. Bảng dữ liệu dùng
  `frontend/src/components/Sheet.tsx` (kiểu Excel). Không còn trang HTML nào: mọi giao diện là React.
  Quản trị cơ sở dữ liệu (`api/admin_db.py`, trang `/co-so-du-lieu`): trạng thái kết nối, số dòng 26 bảng; sửa, thêm, xóa
  6 bảng quy tắc và 2 bảng đại lý `suppliers`, `supplier_materials` (nút "Quản lý đại lý" ở trang Giá, nhà cung cấp) khi có PostgreSQL (kiểm mã vật liệu, biểu thức chính quy, vai trò; ghi `audit_logs`; tải CSV để đồng bộ về
  `data/rules` trước `--reload-rules`). Danh mục vật liệu không sửa trên web (nguồn duy nhất `materials_master.xlsx`).
  Trang kiểm tra ghi mặt bằng đã chốt vào localStorage `optimat-confirmed` để trang `/vat-lieu` gộp các tầng (bản chính thức: `takeoff_results`).
- `src/optimat/data_check.py` + `scripts/check_data.py` + `/api/data/check`: kiểm soát dữ liệu (lỗi chặn commit, cảnh báo, ghi chú).
  Quy trình: `docs/QUY_TRINH_DU_LIEU.md`. Tài liệu, mẫu thu thập: `docs/`. Bản vẽ thật: `data/drawings/build/` (không vào git).

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
- **Phiên điều phối**: "Kiểm tra MD chung và xung đột phiên" (`local_c4532ed5-eff3-4fb1-babd-b31112fcd44d`). Mỗi phiên khi
  bắt đầu gửi tới phiên này (SendMessage) một dòng: sprint, file định sửa; khi xong gửi file đã sửa + kết quả pytest. File
  dùng chung (`rough/models.py`, `rough/takeoff.py`, `drawing/takeoff.py`, `api/main.py`, `CLAUDE.md`, `SPRINTS.md`) chỉ sửa
  bằng Edit từng đoạn nhỏ, không ghi đè cả file; đổi tên trường hay cách gộp nhóm thì báo phiên điều phối trước.
- **Nhiều phiên song song**: mỗi phiên xong việc ghi một dòng `NHAT_KY.md` và cập nhật trạng thái trong `SPRINTS.md`.
  Hai lộ trình: S0–S10 một chữ số (phần thô, 17–19/10) và S01–S08 hai chữ số (theo mã yêu cầu `S02-01`…, từ 21/10); ghi đủ
  hai chữ số để không lẫn (S4b ≠ S04). Database kiểm thử `OPTIMAT_TEST_DATABASE_URL` bị xóa bảng mỗi lần chạy: hai phiên
  chạy pytest cùng lúc sẽ làm hỏng bài của nhau, lỗi DB chập chờn thì chạy lại một mình trước khi kết luận.

## Phạm vi

Nhà ở riêng lẻ xây mới đến 5 tầng. Bóc khối lượng toàn bộ phần thô ra vật liệu (hướng nga chốt 17/10/2026, chờ giảng viên
duyệt); tối ưu đa mục tiêu làm sâu cho tường bao che và tường ngăn. Không lập dự toán, không kiểm tra chịu lực. Không xử lý PDF quét hay ảnh.

## Hiện trạng (13/10/2026; việc sau ngày này xem `SPRINTS.md`, `NHAT_KY.md`)

Đã có và có kiểm thử: đọc DXF, chuyển DWG qua ODA (chỉ kiểm thử giả lập), phân loại layer, nhận diện tường
110/220/330, đo bóc có trừ cửa, bóc tách vật liệu bằng quy tắc (mới thử trên bản vẽ mẫu tự tạo), PostgreSQL 26 bảng (5 nhóm vật liệu đã nạp), huấn luyện XGBoost kèm đối chứng, NSGA-II, trích ràng buộc
bằng regex, API.

Các bảng `users`, `projects`, `project_files`, `takeoff_results`, `optimization_runs`, `model_versions`,
`audit_logs`, `material_aliases`, `standards`, `material_standards` đã có lược đồ và kiểm thử
lưu/đọc; API mới ghi `takeoff_results` (xác nhận đo bóc, phần thô) và `audit_logs` (trang quản trị), đọc thông số
`projects`; các bảng còn lại chưa ghi. Bảng `standards` còn trống (người dùng có 123 bản ghi cần nạp).

Đăng nhập và phân quyền (23/10/2026, Sprint AD-01, `api/auth.py`): chỉ bật khi có PostgreSQL; API quản trị (`/api/admin/*`, ghi ký hiệu
nhận diện) trả 401/403 cho người chưa đăng nhập hoặc không phải admin; không có database thì chọn vai trò như cũ. API của người dùng
thường chưa bắt đăng nhập. Lộ trình quản trị AD-01..06: `SPRINTS.md`.

Chưa có: trình thu thập giá,
bge-m3, OSRM (bản đồ đại lý Leaflet đã có, chưa tính quãng đường), LangGraph, đối chiếu dự toán Excel, dữ liệu thật.

Bản vẽ thật đã thử (13/10/2026, nhóm build, chưa có đáp án đo tay): nhà phố 4 mặt bằng và nhà dân 3 mặt bằng
(xuất qua phần mềm xem nhanh: hatch bị phá, tường trên layer theo nét bút), file kết cấu (bỏ qua đúng).
Tường bao nhận tốt; còn nhận nhầm thành cầu thang, khung cửa sổ, bồn hoa xây trên layer chung; bỏ sót tường vẽ một nét.
Các ngưỡng tự nhận layer (config.py) mới chỉnh trên 2 bản vẽ này.

Vấn đề đã biết:
- Bộ quy tắc hatch (ANSI31, SOLID) là quy ước giả định. Hatch bị phá mất tên mẫu nên không dùng để gán vật liệu được.
- Danh mục thật: chỉ W-GN01-110 và W-GN01-220 đủ số để tối ưu; các phương án khác thiếu định mức, khối lượng tường hoặc λ
  (xem `Catalog.wall_view().missing`). Chưa có phương án lớp 330. Mọi vật liệu tường chưa có hao hụt (`waste_pct`):
  bảng vật liệu và tối ưu đều không cộng hao hụt (có ghi chú). Bảng `labor_rates` thật còn trống (số MẪU ở `data/sample/catalog`). VU04 (vữa AAC) tính theo tấn nhưng chưa có khối
  lượng thể tích nên chưa đổi được từ m³. Chưa có giá đại lý thật và phương tiện thật: tối ưu, tra giá chỉ chạy với bộ MẪU (kiểm thử).
- Cửa nhận từ khe tường: rộng theo khe, cao theo thông số cửa của dự án (chưa đọc bảng thống kê cửa, QU-15).
- Trên dữ liệu mô phỏng, mốc tra bảng nhỉnh hơn XGBoost; cần thêm đặc trưng giá kỳ trước.
- Đường gọi OpenAI mới kiểm thử bằng hàm giả, chưa chạy với API thật; mã mô hình `gpt-5.6-luna` chưa được xác nhận trên trang OpenAI.
- Chưa ghi lần tối ưu vào `optimization_runs`. `/api/agent/run` dùng agent gọi công cụ khi có khóa OpenAI, ngược lại luồng cố định.
