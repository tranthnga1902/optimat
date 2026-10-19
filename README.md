# OptiMat AI: bộ khung mã (base code)

Hệ thống AI Agent hỗ trợ tối ưu lựa chọn vật liệu xây tường cho nhà ở riêng lẻ,
dùng XGBoost để dự đoán giá và NSGA-II để tối ưu đa mục tiêu.

Đây là **bộ khung chạy được từ đầu đến cuối trên dữ liệu mẫu**, chưa phải hệ thống hoàn chỉnh.
Mục "Việc cần làm tiếp" ở cuối liệt kê những phần còn thiếu.

Kế hoạch 15 tuần và danh sách việc: `PLAN.md` (có hướng dẫn kết nối DBeaver).
Bối cảnh dự án cho Claude Code: `CLAUDE.md`.

## Cài đặt (Windows, PowerShell)

```powershell
cd optimat-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Cần Python 3.10 trở lên.

### PostgreSQL

Cơ sở dữ liệu gồm 23 bảng, định nghĩa trong `src/optimat/db/models.py`. Có hai cách tạo, cho kết quả như nhau.

**Bước chung:** trong DBeaver, kết nối bằng tài khoản `postgres` rồi chạy từng lệnh trong
`sql/00_create_database.sql` (tạo người dùng `optimat` và database `optimat` mã hóa UTF-8).

**Cách 1, bằng Python (nên dùng):**

```powershell
$env:DATABASE_URL = "postgresql+psycopg://optimat:matkhau@localhost:5432/optimat"
python scripts/init_db.py --prices data/sample/prices_sample.csv
```

**Cách 2, bằng SQL trong DBeaver:** kết nối tới database `optimat` bằng tài khoản `optimat`, mở và chạy
`sql/01_schema.sql` (Alt+X để chạy cả file), rồi `sql/02_seed_sample.sql`, `sql/03_materials.sql`, `sql/05_rules.sql`.

Sau đó trong DBeaver, bấm F5 ở mục Tables để thấy 23 bảng. Sửa `db/models.py` thì chạy
`python scripts/export_sql.py` để sinh lại các file SQL.

Khi có `DATABASE_URL`, hệ thống đọc danh mục, họ vật liệu, đơn giá nhân công, bộ quy tắc, định mức và lịch sử giá từ PostgreSQL. Khi không có, hệ thống đọc
các file CSV trong `data/catalog` (dùng cho kiểm thử). `GET /api/health` cho biết đang dùng nguồn nào.

### Đọc file DWG

Cài ODA File Converter (miễn phí) từ https://www.opendesign.com/guestfiles/oda_file_converter.
Hệ thống tự tìm trong `C:\Program Files\ODA`. Nếu cài chỗ khác, đặt biến môi trường:

```powershell
$env:ODA_CONVERTER_PATH = "D:\duong-dan\ODAFileConverter.exe"
```

Chưa cài thì vẫn dùng được file `.dxf`; tải `.dwg` lên sẽ nhận thông báo hướng dẫn cài đặt.

## Giao diện chung và kiểm soát dữ liệu

`/app` theo bố cục mockup (`docs/mockup/`), hai vai trò:

- **Người dùng**: Hồ sơ và đo bóc (trang Kiểm tra bóc tách nhúng trong khung) → Vật liệu và giá (gộp các mặt bằng đã
  xác nhận, gạch + vữa, giá trong database) → Phương án tối ưu (ràng buộc, trợ lý trích ràng buộc từ câu tiếng Việt, NSGA-II).
- **Quản trị viên**: Kiểm soát dữ liệu (`/api/data/check`), vật liệu và phương án tường, giá và nhà cung cấp, mô hình và cấu hình.

Quy trình dữ liệu: `docs/QUY_TRINH_DU_LIEU.md`.

## Chạy thử

```powershell
# 1. Kiểm tra mọi thứ hoạt động (58 bài kiểm thử, thêm 8 bài khi có PostgreSQL) và kiểm soát dữ liệu
pytest
python scripts/check_data.py
git config core.hooksPath .githooks          # mỗi lần commit tự chạy 2 bước trên
# kiểm thử với PostgreSQL thật: dùng một database RIÊNG, vì bài kiểm thử xóa và tạo lại toàn bộ bảng
# $env:OPTIMAT_TEST_DATABASE_URL = "postgresql+psycopg://optimat:matkhau@localhost:5432/optimat_test"

# 2. Huấn luyện mô hình giá ngay trên máy (vài giây), kết quả ghi vào models/
$env:PYTHONPATH = "src"
python -m optimat.predict.train --data data/sample/prices_sample.csv --out models
#    hoặc lấy dữ liệu từ bảng price_records trong PostgreSQL:
python -m optimat.predict.train --from-db --out models

# 3. Chạy hệ thống: giao diện chung http://localhost:8000/app, tài liệu API http://localhost:8000/docs
uvicorn optimat.api.main:app --reload --app-dir src
```

Chạy thử cả luồng bằng Python:

```python
from optimat.agent.pipeline import run_pipeline
state = run_pipeline("data/sample/sample_floor.dxf",
                     message="Ngõ chỉ xe 2,5 tấn vào được, ngân sách 60 triệu, không dùng gạch nung",
                     floor_height_mm=3300, use_llm=False)
print(state["explanation"])
```

`run_pipeline` nhận cả file `.dwg`. Nếu layer tường không theo tên quen thuộc, truyền
`layer_overrides={"Layer1": "WALL"}` để chỉ định.

`use_llm=True` sẽ gọi mô hình Qwen qua Ollama (cần cài Ollama và `ollama pull` mô hình ghi trong
`src/optimat/config.py`). Nếu Ollama không chạy, hệ thống tự dùng bộ trích bằng biểu thức chính quy.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `src/optimat/drawing/` | Đọc DXF và DWG (`dxf_reader.py`, `dwg_convert.py`), gán vai trò layer (`layer_classifier.py`), chuyển mã phông TCVN3 (`encoding.py`), nhận diện tường (`walls.py`), đo bóc (`takeoff.py`) |
| `src/optimat/db/` | Lược đồ 23 bảng PostgreSQL (`models.py`), kết nối (`session.py`) |
| `sql/` | File SQL để tạo database, bảng và dữ liệu mẫu trực tiếp trong DBeaver |
| `src/optimat/catalog/` | Nạp danh mục vật liệu, nhà cung cấp, phương tiện; ước lượng cự ly |
| `src/optimat/predict/` | Đặc trưng (`features.py`), huấn luyện và so sánh mô hình (`train.py`), nạp mô hình để dự đoán (`cost_model.py`) |
| `src/optimat/optimize/` | Bài toán ba mục tiêu, NSGA-II và vét cạn để đối chứng (`problem.py`) |
| `src/optimat/agent/` | Trích ràng buộc từ câu tiếng Việt (`llm.py`), luồng điều phối (`pipeline.py`) |
| `src/optimat/api/` | API FastAPI: `/api/takeoff`, `/api/takeoff/plans`, `/api/takeoff/view`, `/api/takeoff/confirm`, `/ui/takeoff`, `/api/catalog/wall-materials`, `/api/price/bill`, `/api/optimize`, `/api/agent/run`, `/api/constraints/parse`, `/api/health` |
| `data/catalog/` | Danh mục mẫu dạng CSV |
| `data/sample/` | Bản vẽ DXF mẫu và dữ liệu giá mô phỏng |
| `scripts/` | Khởi tạo cơ sở dữ liệu (`init_db.py`), sinh lại dữ liệu mẫu |
| `THIRD_PARTY_NOTICES.md` | Phần mã kế thừa từ dự án khác và giấy phép |
| `notebooks/` | Notebook thí nghiệm (tùy chọn, cần `pip install notebook`) |
| `tests/` | Kiểm thử, có đáp án đo tay cho bản vẽ mẫu |

## Dữ liệu mẫu và dữ liệu thật

**Toàn bộ dữ liệu đi kèm là số mẫu hoặc mô phỏng**, chỉ để kiểm tra mã chạy đúng:

- `data/catalog/*.csv`: cột `data_kind = SAMPLE`. Định mức, hệ số dẫn nhiệt, giá, tọa độ và liên kết
  (`example.com`) đều là số minh họa. Thay bằng số liệu từ định mức của Bộ Xây dựng, catalog nhà sản
  xuất và trang sản phẩm thật của nhà phân phối.
- `data/sample/prices_sample.csv`: cột `data_kind = SYNTHETIC`, sinh bằng công thức. File chỉ số
  `models/material_price_metrics.json` tự ghi cảnh báo khi dữ liệu có phần mô phỏng.
  **Không dùng các chỉ số này trong báo cáo.**

Dữ liệu giá thật cần đúng các cột: `date, material_id, supplier_id, province, unit, quantity, unit_price`
và nên có `source`, `data_kind`.

## Việc cần làm tiếp

1. **Nhận diện tường**: xử lý góc tường (hiện hụt khoảng một chiều dày ở mỗi góc), tường vẽ bằng hatch
   hoặc multiline, tách vùng mặt bằng từng tầng, xác định tường bao che theo đường bao nhà thay cho
   quy ước "tường từ 220 trở lên".
2. **Phông chữ**: kiểm tra bảng TCVN3 trên bản vẽ thật, bổ sung bảng VNI, đọc ghi chú vật liệu.
3. **Mô hình giá**: trên dữ liệu mẫu, cách "tra bảng giá gần nhất" đang ngang hoặc nhỉnh hơn XGBoost,
   vì mô hình cây không ngoại suy được xu hướng theo thời gian. Hướng cải thiện: thêm đặc trưng giá kỳ
   trước (lag), dự đoán mức thay đổi so với giá gần nhất thay vì dự đoán thẳng giá.
4. **Vận chuyển**: hiện tính bằng công thức và cự ly ước lượng. Thay bằng OSRM và mô hình XGBoost thứ hai
   khi có dữ liệu cước.
5. **Agent**: chuyển các bước trong `pipeline.py` sang LangGraph, thêm bước chờ người dùng xác nhận.
6. **Lưu trữ**: các bảng người dùng, dự án, kết quả đo bóc, nhật ký đã có nhưng API chưa ghi vào; cần nối API
   với các bảng này, thêm trình thu thập giá ghi vào `supplier_materials` và `price_records`, và dùng Alembic
   để quản lý thay đổi lược đồ.
7. **Giao diện**: ứng dụng React gọi vào API này.
8. **Đối chiếu BOQ** từ file Excel.

## Bóc tách vật liệu bằng quy tắc

Sau khi nhận diện tường, hệ thống gán vật liệu theo thiết kế cho từng tường dựa trên bốn loại tín hiệu trong
bản vẽ: ghi chú, hatch, tên layer và tên block. Bộ quy tắc nằm trong `data/rules/material_rules.csv`, mở và
sửa bằng Excel (lưu dạng CSV UTF-8), không cần sửa mã.

| Cột | Ý nghĩa |
|---|---|
| `signal` | `text`, `hatch`, `layer` hoặc `block` |
| `pattern` | text, layer: chuỗi con viết thường không dấu; hatch: tên mẫu; block: biểu thức chính quy |
| `target` | Họ vật liệu của danh mục (`CLAY_SOLID`, `AAC`...) hoặc mã vật liệu (`GN01`); nhiều giá trị cách nhau bằng `\|` |
| `element` | `WALL_MASONRY`, `CONCRETE` (loại khỏi khối lượng xây), `DOOR`, `WINDOW` |
| `priority` | Số lớn hơn thắng khi nhiều quy tắc cùng khớp |

Tín hiệu không có quy tắc được liệt kê trong `unmatched`; hệ thống để trống vật liệu chứ không đoán.
Ngoài CSV, mỗi tên gọi khác của vật liệu tường trong danh mục (`material_aliases`) tự thành một quy tắc ghi chú.
Họ hoặc mã vật liệu + lớp chiều dày tường được quy đổi sang phương án tường (`wall_systems.detect_class`) để có
`material_id` và `wall_system_id` thật; danh mục có nhiều phương án cùng lớp thì để người dùng chọn trên trang kiểm tra.

```powershell
python scripts/survey_drawings.py data/drawings/build     # xem tín hiệu nào chưa có quy tắc
python scripts/evaluate_takeoff.py                        # so với đáp án trong data/ground_truth
```

Số liệu đánh giá hiện chỉ đến từ bản vẽ mẫu tự tạo, không dùng để báo cáo độ chính xác.
