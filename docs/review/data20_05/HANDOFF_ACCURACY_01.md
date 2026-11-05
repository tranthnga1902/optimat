# Bàn giao accuracy05 cho01 — 04/11/2026

Không DB/runtime/full suite. Giữ20bảng.03instancecore/06API/04materials không bị ghi. Những test mới chỉ là SYNTHETIC, không chứng minh accuracy nhà thực tế.

## Cột — canonical theo quyền05, đã kiểm

- Source: `src/optimat/rough/columns.py::signal_columns`; `src/optimat/drawing/dxf_reader.py::Segment.contour_id/_Collector.polyline`.
- Receipt: `docs/review/data20_05/column_contour_fix/v2_receipt.json` và `handoff_manifest.json` (hash hiện tại cả2source+test vẫn khớp hash đã kiểm).
- Handoff/giới hạn: `column_contour_fix/TOUCHING_CONTOURS.md`; diff hàm `column_contour_fix/signal_columns_v2.patch`.
-74ca khác nhau đạt qua2lượt:72pass/2lỗi thư mụcTemp sandbox/11deselected;2converter retry dùng TMP/TEMP trong workspace đạt. Không gọi lượt72pass exit1 là pass đầy đủ trong một lần.
-4ca DXF polyline chung cạnh/chung góc/nét nối/khe0,4: trước4fail, sau4pass qua read_drawing, log touch_before/touch_final. Block INSERT lặp và crop có test riêng giữ2ID/2cột. Cột225×335 không ép bội10. Nét rời chia ô không có identity giữ chưa nhận.
- Giới hạn: contour WCS theo trục; hatch/raster/rotated/nhận định kết cấu chưa được mở rộng, không tự chứng nhận đủ nguồn.

## Bảng thép — chỉ staging, xin01review/áp hunk

**Patch header chính xác:** `docs/review/data20_05/rebar_table_fix/staging/read_table.patch`.

**Base SHA256:** `a05915b14795a4a48f4d9f9532945f88bcc43c8a084dacf877d1ef7dcb7d6085`. Canonical rebar.py hiện vẫn đúng hash base. Candidate chỉ header `staging/rebar.py`: `850a70e3211b22de1a8fabc5e9e409d895997c3dd06972cc2160bcfd90ce3667`.

135pass/exit0 của header-only staging,4case trước fail nay pass. `rebar_table_fix/staging_receipt.json`/`stage_final.log` chứa receipt. Chỉ read_table đổi; AST class/function khác nguyên. Các caller nạp module staged trong child bằng `staging/run_tests.py`, không mock parser/scope. Không copy đè toàn file để áp patch.

## Tokenizer element_code — đề xuất staging riêng

Đã tái hiện5fail/4pass: C-1/C-2/C-1A/D-2 mất mã; C1-C2 bị lấy token cuối thành một cột. MC1-1/MC 1-1 là SECTION, không được đổi thành COT.

**Patch bổ sung một dòng:** `docs/review/data20_05/rebar_table_fix/staging/element_code.patch`, bỏ dấu `-` khỏi delimiter re.split; để element_of hiện có xử lý trọn token theo vocabulary. Không hardcode mã/file. Patch này được sinh trên candidate header nhưng hunk chỉ chạm element_code, có thể review/áp riêng.

Candidate gồm cả hai hunk: `staging/rebar_tokenizer.py`, SHA256 `f0eb2c2d865645167648a1820be2eb3571779730d9d40bbcc55ec255f4660ac5`. Base canonical vẫn hash trên. Hash các file tại `rebar_table_fix/tokenizer_manifest.json`.

**144passed in14.57s,exit0**, session93376 terminal, `rebar_table_fix/token_final.log`. Lệnh `.venv/Scripts/python.exe docs/review/data20_05/rebar_table_fix/staging/run_tokenizer_tests.py tests/test_rebar_element_tokens.py tests/test_rebar_table_boundaries.py tests/test_rough_rebar.py tests/test_rough_partial.py tests/test_rough_takeoff.py -q -p no:cacheprovider --basetemp=docs/review/data20_05/rebar_table_fix/temp_token_final`.9token tests +6header boundary tests và regression scope/dedup/manifest/rough thiếu/vật liệu. Không API/TestClient.

Dấu gạch trong chuỗi range C1-C2 được giữ chưa phân loại, không tự mở thành nhiều cấu kiện. Những dạng tên viết liền kiểu DẦM-D1 không có token mã độc lập có thể không được nhận như trước; cần giữ cảnh báo/đúng vocabulary thay vì tách mù. Chưa thay canonical ở lượt này;01chốt áp header/tokenizer và cấp kiểm sau merge riêng.

## Nguồn VN002 pending

04bàn giao C-1/C-2 có cùng Ø/L/SL/kg; tuyệt đối không join bằng trị số. C-2 groupTEXT118CDEF/(SL:2)118CDF0, INSERTmark3=118CDA7/mark4=118CDB3, mark7=118CDD7.05không bind chúng vào đoạn; link group→INSERT→mark→chi tiết/layer/type còn chưa tự kiểm đầy đủ. Header staging chưa chứng minh hỗ trợ block bảng TK_2/ACAD_TABLE VN002. Nguồn cụ thể được giữ trong rebar_table_fix/README.md, không nâng thành GT hoặc quantity đã kiểm.
