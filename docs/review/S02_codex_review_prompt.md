# Prompt cho Codex: review Sprint S02 – Tiếp nhận hồ sơ và CAD parser

Dán toàn bộ phần dưới đây vào Codex (chạy ở thư mục gốc repo `optimat-ai`).

---

Bạn là reviewer cấp cao cho dự án Python OptiMat AI (FastAPI + ezdxf, Windows, Python 3.13, venv ở `.venv`).
Hãy review **chỉ phần việc của Sprint S02** và kiểm tra lại xem nó có thật sự đạt tiêu chí nghiệm thu không.
Trả lời bằng tiếng Việt. **Không sửa code**: chỉ đọc, chạy lệnh kiểm tra và báo cáo. Đọc `CLAUDE.md` trước để nắm quy ước.

## Phạm vi sprint (yêu cầu gốc)

- S02-01: Upload nhiều file, kiểm tra MIME/phần mở rộng, giới hạn kích thước, hash và version.
- S02-02: Tích hợp ODA File Converter chuyển DWG→DXF, log phiên bản và lỗi chuyển đổi.
- S02-03: Dùng ezdxf đọc modelspace, INSERT/BLOCK, LINE, LWPOLYLINE, POLYLINE, ARC, HATCH, TEXT/MTEXT, DIMENSION.
- S02-04: Chuẩn hóa mm, kiểm tra `$INSUNITS`, tỷ lệ 1:1, XREF, bản vẽ có nhiều layout, ghi chú font lỗi.
- S02-05: Báo cáo layer, block, bounding box, đơn vị, số lượng entity, cảnh báo không đọc được.
- Bàn giao: CLI/API tiếp nhận CAD; JSON entity inventory; trang xem thống kê file; bộ 5–10 CAD mẫu hợp lệ/lỗi.
- Nghiệm thu:
  1. Với DXF mẫu, số entity/layer khớp phép đếm độc lập.
  2. File thiếu đơn vị hoặc font không hỗ trợ được gắn cảnh báo.
  3. Chuyển DWG thất bại không sinh kết quả takeoff giả.
- Giới hạn: không suy ra khối lượng từ chiều dài bounding box.

## File thuộc sprint

- `src/optimat/drawing/ingest.py` (mới): `sniff`, `check_upload`, `store_upload`, `convert_with_log`, `inventory_dxf`, `ingest_file`.
- `src/optimat/drawing/dxf_reader.py` (sửa): thêm `declared_insunits()` — file DXF không có HEADER thì ezdxf tự điền
  `$INSUNITS = 6` (mét), trước đây làm bản vẽ bị nhân 1000 mà không cảnh báo; nay coi là 0 (chưa khai báo).
- `src/optimat/api/main.py` (sửa): `POST /api/ingest` (nhiều file, Form `store`), `GET /ui/ingest`.
- `src/optimat/web/ingest.html` (mới): trang xem thống kê.
- `src/optimat/config.py` (sửa): `MAX_UPLOAD_MB`, `UPLOAD_DIR`.
- `scripts/ingest_cad.py` (CLI), `scripts/make_ingest_samples.py` (sinh mẫu).
- `data/sample/ingest/` 12 file mẫu + `expected.json` (trạng thái và mã cảnh báo mong đợi).
- `tests/test_ingest.py` (19 bài).

## Việc cần làm

### 1. Chạy kiểm tra
```powershell
$env:PYTHONIOENCODING = "utf8"
.venv\Scripts\python.exe -m pytest -q tests/test_ingest.py tests/test_drawing_io.py
.venv\Scripts\python.exe scripts/make_ingest_samples.py; git status data/sample/ingest   # sinh lại phải ra file giống hệt (hoặc chỉ khác handle/timestamp)
.venv\Scripts\python.exe scripts/ingest_cad.py data/sample/ingest --out $env:TEMP\inv      # mã thoát 1 là đúng (có file lỗi)
.venv\Scripts\python.exe -m pytest -q                                                       # toàn bộ; so với mốc trước sprint
```
Mốc trước sprint (máy tác giả, không có PostgreSQL kiểm thử): 16 failed, 12 errors, 153 passed — các lỗi đó thuộc
test cần database/mô hình, không thuộc S02. Hãy xác nhận S02 **không thêm** test hỏng nào ngoài các bài đó
(so tên bài hỏng, không chỉ so số lượng).

### 2. Đối chiếu từng tiêu chí nghiệm thu
Với mỗi tiêu chí, ghi **ĐẠT / CHƯA ĐẠT / ĐẠT MỘT PHẦN**, kèm bằng chứng (tên test, dòng code, output lệnh).
- Tiêu chí 1: đọc `raw_count()` trong `tests/test_ingest.py`. Phép đếm có thật sự độc lập với ezdxf không?
  Có bỏ sót trường hợp làm hai bên lệch nhau không (entity paperspace nằm trong mục ENTITIES, `ATTRIB`/`VERTEX`/`SEQEND`,
  DXF nhị phân, entity không có mã 8)? Thử tự viết thêm một phép đếm trên `data/drawings/build/*.dxf` nếu có file.
- Tiêu chí 2: `NO_UNITS`, `FONT_UNSUPPORTED`, `FONT_MISSING`. Font lỗi hiện chỉ dựa trên tên font (VNI = không chuyển mã
  được; style không khai báo font). Đánh giá: có đủ cho "font không hỗ trợ" không, hay cần kiểm tra font có trên máy chủ?
- Tiêu chí 3: lần theo mọi đường DWG: `ingest_file` → `convert_with_log`; `/api/takeoff`, `/api/takeoff/view`,
  `/api/takeoff/rough/auto`, `/api/agent/run` với DWG hỏng. Có đường nào trả về khối lượng/kết quả rỗng-nhưng-"thành công"
  thay vì lỗi không? `takeoff_allowed` có được bên nào dùng để chặn không, hay chỉ là thông tin?

### 3. Soi lỗi (ưu tiên theo mức độ nghiêm trọng)
- **Bảo mật / ranh giới tin cậy**: `store_upload` ghi file theo `sha256 + ext` — có đường nào để tên file người dùng
  điều khiển đường dẫn ghi (path traversal) không? `manifest.jsonl` có bị ghi đồng thời từ nhiều request (race) làm trùng
  số phiên bản không? Giới hạn kích thước trong `/api/ingest` (`f.read(limit + 1)`) có thật sự chặn file lớn trước khi
  nạp vào bộ nhớ không (Starlette có spool ra đĩa trước không)? Số lượng file mỗi request có bị giới hạn không?
  `sniff()` có thể bị lừa không và hậu quả là gì? XSS trên `ingest.html` (tên layer/block/font do người dùng kiểm soát).
- **Đúng đắn**: `declared_insunits()` tìm chuỗi `b"$INSUNITS"` trong toàn bộ file — có dương tính giả (chuỗi nằm trong
  TEXT) không, có tốn bộ nhớ với file 20 MB không, có ảnh hưởng tới kết quả đo bóc các bản vẽ cũ không?
  Ngưỡng `PLAUSIBLE_EXTENT_MM` (1 m – 1 km) có hợp lý không với file chứa nhiều bản vẽ rải xa nhau trong modelspace?
  `_dim_mismatch` so chữ ghi đè với số đo × scale nhưng bỏ qua DIMLFAC — có cảnh báo sai không?
  Đếm `inserts` dựa trên `doc.entitydb` có tính cả INSERT trong block bị xóa/không dùng không?
  `paper` (layout có nội dung) loại VIEWPORT — layout chỉ có viewport phụ thì sao?
  `entity_counts` chỉ tính modelspace, còn `entities` có cả paperspace — có gây nhầm cho người dùng JSON không?
- **Hiệu năng**: thời gian `inventory_dxf` trên file 20 MB (`data/drawings/build/nha_pho.dxf` nếu có; khoảng 25–40 s,
  chủ yếu ezdxf đọc file và tính khung bao từng entity). `/api/ingest` chạy tuần tự từng file trong threadpool — có chặn
  server lâu không? Có cần giới hạn số entity xuất ra JSON không?
- **Giới hạn sprint**: xác nhận không chỗ nào dùng `bbox_mm` để tính khối lượng.
- **Phong cách dự án**: thông báo người dùng bằng tiếng Việt; quy tắc không viết cứng khi lẽ ra nằm trong CSV
  (`CLAUDE.md`: "Bóc tách bằng quy tắc"); mã ngắn, theo idiom của `drawing/dxf_reader.py`.

### 4. Bộ mẫu
Kiểm tra 12 file trong `data/sample/ingest/` có phủ đủ: hợp lệ mm, thiếu đơn vị, đơn vị mét, sai tỷ lệ, DIMLFAC + chữ ghi
đè, XREF, nhiều layout, font VNI + SPLINE, modelspace rỗng, DXF hỏng, DWG hỏng, PDF đổi đuôi. Thiếu ca nào quan trọng
(DXF nhị phân, DXF mã hóa khác UTF-8/cp1258, block lồng nhau sâu, XREF overlay, entity hình học hỏng → `UNREADABLE_ENTITY`
hiện chưa có mẫu nào kích hoạt)?

## Định dạng báo cáo

1. **Kết luận**: sprint ĐẠT / CHƯA ĐẠT nghiệm thu, một câu lý do.
2. **Bảng tiêu chí**: tiêu chí | kết quả | bằng chứng.
3. **Lỗi tìm được**, xếp từ nghiêm trọng nhất: mức (Cao/Trung bình/Thấp) | file:dòng | mô tả | tình huống tái hiện cụ thể
   (đầu vào → kết quả sai) | cách sửa đề xuất (ngắn). Chỉ ghi lỗi đã tự kiểm chứng hoặc tái hiện được; phỏng đoán thì ghi rõ
   "chưa kiểm chứng".
4. **Ca kiểm thử nên thêm** (tên test + điều cần khẳng định).
5. **Những gì bạn không kiểm tra được** (ví dụ: không có ODA trên máy, không có bản vẽ thật).
