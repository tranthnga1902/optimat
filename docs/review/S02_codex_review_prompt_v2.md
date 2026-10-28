# Prompt cho Codex: review lại Sprint S02 (vòng 2, sau khi sửa theo review vòng 1)

Dán toàn bộ phần dưới vào Codex, chạy ở thư mục gốc repo `optimat-ai`. Prompt vòng 1: `docs/review/S02_codex_review_prompt.md`.

---

Bạn là reviewer cấp cao cho dự án OptiMat AI (Python 3.13, FastAPI, ezdxf, Windows, venv `.venv`). Vòng 1 bạn kết luận
Sprint S02 **CHƯA ĐẠT** và nêu 4 lỗi + 6 test nên thêm. Code đã được sửa. Nhiệm vụ: **xác minh từng điểm đã sửa đúng
và đủ**, tìm lỗi mới do bản sửa gây ra, rồi kết luận lại. Trả lời bằng tiếng Việt. **Không sửa code.** Đọc `CLAUDE.md` trước.

Lưu ý môi trường: nếu pytest lỗi setup vì không ghi được thư mục tạm của Windows, thêm `--basetemp .pytest_tmp`.

## Những gì đã sửa (đối chiếu với báo cáo vòng 1)

| # | Vòng 1 báo | Đã sửa | Ở đâu |
|---|---|---|---|
| 1 | Cao: `declared_insunits()` tìm `$INSUNITS` trên toàn file → TEXT chứa chuỗi đó làm bản vẽ không HEADER bị coi là mét | Chỉ tìm biến mã nhóm 9 trong mục HEADER (DXF văn bản: regex giữa `2/HEADER` và `ENDSEC`; DXF nhị phân: giữa `HEADER\0` và `ENDSEC\0`) | `src/optimat/drawing/dxf_reader.py` `declared_insunits` |
| 2 | TB: hai request cùng tên cùng nhận version=1 | Khóa `threading.Lock` quanh đọc–cấp số–ghi manifest (có ghi chú `shortcut:`: chỉ một tiến trình) | `src/optimat/drawing/ingest.py` `store_upload` |
| 3 | TB: không giới hạn số file mỗi request | `config.MAX_UPLOAD_FILES = 20`, vượt thì 400 | `src/optimat/config.py`, `src/optimat/api/main.py` `ingest` |
| 4 | TB: font khai báo nhưng máy chủ không có → không cảnh báo | Thêm trường `found` cho từng kiểu chữ và cảnh báo `FONT_NOT_FOUND` (chỉ font của kiểu chữ có TEXT/MTEXT dùng trong modelspace), kiểm bằng `ezdxf.fonts.font_manager.has_font` | `ingest.py` `inventory_dxf` |
| 5 | `raw_count` bỏ sót paperspace trong ENTITIES, entity thiếu mã 8 | Viết lại: gom thẻ từng entity, bỏ `67 = 1`, thiếu mã 8 → layer "0" | `tests/test_ingest.py` `raw_count` |
| 6 | Thiếu mẫu DXF nhị phân, XREF overlay, block lồng sâu | Thêm `13_nhi_phan.dxf`, overlay `TRUC_OVERLAY` trong `06_xref.dxf`, `14_block_long_sau.dxf` (5 cấp), `15_khong_header_chu_insunits.dxf` | `scripts/make_ingest_samples.py`, `data/sample/ingest/` (15 file) |

Test mới: `test_headerless_text_insunits_keeps_unitless`, `test_raw_count_paperspace_and_missing_layer`,
`test_binary_dxf_inventory`, `test_declared_font_absent_on_server`, `test_unreadable_entity_is_reported`,
`test_manifest_concurrent_versions_unique`, `test_dwg_failure_all_takeoff_routes` (4 API), `test_api_rejects_too_many_files`.
Phép đếm độc lập nay chạy trên 6 mẫu (thêm 06 XREF, 07 nhiều layout, 14 block lồng). Fixture `fonts_present` (autouse)
giả lập mọi font đều có để kết quả không phụ thuộc máy; riêng test font thì giả lập thiếu `txt`.

Tác giả đã tự kiểm: bỏ khóa ở mục 2 thì `test_manifest_concurrent_versions_unique` hỏng 3/3 lần, có khóa thì đạt.

## Việc cần làm

1. **Chạy**
   ```powershell
   $env:PYTHONIOENCODING = "utf8"
   .venv\Scripts\python.exe -m pytest -q tests/test_ingest.py tests/test_drawing_io.py
   .venv\Scripts\python.exe scripts/make_ingest_samples.py
   .venv\Scripts\python.exe scripts/ingest_cad.py data/sample/ingest --out $env:TEMP\inv
   .venv\Scripts\python.exe -m pytest -q -rfE
   ```
   Ghi **tên** các bài hỏng của lượt chạy toàn bộ. Không bài nào trong `tests/test_ingest.py`, `tests/test_drawing_io.py`
   được hỏng. Các bài hỏng còn lại phải không liên quan tới `drawing/ingest.py` hay `declared_insunits` — để chứng minh,
   chạy lại các bài đó sau khi tạm thay `declared_insunits(doc, path)` trong `read_dxf` bằng
   `int(doc.header.get("$INSUNITS", 0) or 0)` (hoàn tác ngay sau đó) và so danh sách.

2. **Xác minh từng bản sửa** (với mỗi mục: ĐÚNG / CHƯA ĐỦ / SAI + bằng chứng):
   - Mục 1: thử tự tạo các ca: HEADER có `$INSUNITS` sau nhiều biến khác; HEADER không có `$INSUNITS` nhưng ENTITIES có
     TEXT `$INSUNITS`; xuống dòng CRLF; có dòng `999` chú thích đầu file; DXF nhị phân có/không có biến; file R12 có HEADER
     nhưng không có biến. Regex có thể khớp nhầm giá trị (mã nhóm khác 9) không? `read_bytes()` cả file 20 MB hai lần
     (`read_dxf` + `inventory_dxf`) có đáng lo không?
   - Mục 2: khóa có bao cả ghi file gốc lẫn manifest không; chạy CLI song song với server thì sao (đã ghi là giới hạn)?
   - Mục 3: giới hạn đặt trước hay sau khi Starlette đã nhận hết body? Tổng dung lượng tối đa mỗi request thực tế là bao nhiêu?
   - Mục 4: `has_font` của ezdxf có nhận font SHX (`txt`, `romans.shx`) không, hay mọi bản vẽ thật sẽ luôn bị `FONT_NOT_FOUND`?
     Cảnh báo này có làm `status`/`takeoff_allowed` sai không (không được chặn)? Font của kiểu chữ chỉ dùng trong DIMENSION
     hoặc block có bị bỏ sót không — nêu rõ đó là thiếu sót hay chấp nhận được.
   - Mục 5: `raw_count` mới còn độc lập với ezdxf không; đọc thử `data/drawings/build/*.dxf` (nếu có) và so với `ingest_file`.
   - Mục 6: sinh lại mẫu, so `expected.json` với kết quả thật.

3. **Tìm lỗi mới** do bản sửa gây ra (hồi quy) trong `dxf_reader.read_dxf` (dùng chung cho đo bóc) và `ingest.py`.

4. **Kiểm lại 3 tiêu chí nghiệm thu** S02 (đếm entity/layer khớp đếm độc lập; cảnh báo thiếu đơn vị/font; DWG lỗi
   không sinh takeoff giả) và giới hạn "không suy ra khối lượng từ bounding box".

## Định dạng báo cáo

1. **Kết luận**: ĐẠT / CHƯA ĐẠT nghiệm thu, một câu.
2. **Bảng bản sửa**: # | kết quả | bằng chứng.
3. **Bảng tiêu chí**: tiêu chí | kết quả | bằng chứng.
4. **Lỗi mới/còn lại**, nặng nhất trước: mức | file:dòng | tái hiện (đầu vào → kết quả sai) | cách sửa ngắn.
   Chỉ ghi lỗi đã tái hiện; phỏng đoán ghi "chưa kiểm chứng".
5. **Danh sách bài hỏng** của lượt chạy toàn bộ và kết luận có liên quan S02 không.
6. **Chưa kiểm tra được**.
