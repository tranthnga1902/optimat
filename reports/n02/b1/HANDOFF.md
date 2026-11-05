# N02-b1 — bàn giao reader/manifest/mapping core

**Bản hiện hành sau review fix:** xem [review_fix/HANDOFF.md](review_fix/HANDOFF.md) và `review_fix/hash_after.json`. Kết quả 71 passed và hash bên dưới là bằng chứng trước review fix, không phải khóa source hiện tại hay nghiệm thu b1.

03/11/2026 — **SOURCE-READY + focused reader đạt, CHỜ REVIEW**. Chỉ sửa `src/optimat/rough/rebar.py` và `tests/test_rough_rebar.py`; bằng chứng riêng thư mục này. Không nghiệm thu N02 đầy đủ, chưa mở b2/b3. Không đổi worker PID20288, restart backend, API/takeoff/steel/materials/status/models, CSV/DB/UI/deps hay tài liệu chung.

## Contract đã triển khai trong rebar.py

| Điểm vào | Contract |
|---|---|
| `RebarSourceRef.from_bytes(data: bytes)` | SHA-256 byte caller cung cấp; source_id = `structural:<hash>`. B2 phải gọi bằng byte upload **gốc**, không filename/hash DXF chuyển tạm. Model này không tự chứng minh client đã gửi đúng byte |
| `RebarTableRef`, `RebarScopeAssignment` | Ref nguồn/revision/table ID, content SHA, scope, evidence, người/ngày có timezone, override_reason. Hash đúng cấu trúc; chữ xác nhận không trống; scope phải có tập tầng/nhóm có quy ước. Không tự tạo người kiểm |
| `collect_rebar_tables(drawing)` | Trả `(list[RebarTable], warnings)` trước dedup, đọc từng bảng một lần; gồm cả bảng rỗng, giữ rows/ô gốc, title và scope_from_title |
| `table_manifest(tables, *, source)` | Ref/title/row_count/content_sha256/scope_from_title của **mọi** bảng, không đọc graph/bảng lại; copy scope tránh sửa manifest làm đổi bảng gốc |
| `resolve_rebar_tables(tables, *, source=None, assignments=None)` | Trả `(rows, warnings)`. Validate **toàn bộ** map trước tạo kết quả: cùng source/revision, table tồn tại, content đúng, không lặp assignment cho một table, override trái tiêu đề có lý do. Sai → ValueError cho b2 chuyển 422, không áp một phần hoặc mutate tables/assignments |
| `read_rebar_schedules(drawing)` | Wrapper một đối số như cũ; collect một lần → resolve; vẫn tuple `(rows, warnings)`, không thêm engine/caller mới |

RebarRow thêm `source_id: str = ""`, `revision_sha256: str = ""` để nối row tới ref. Các trường cũ/mặc định vẫn giữ; JSON list tầng đọc lại thành tuple chuẩn hóa. Ngày xác nhận giữ timezone; nguồn/assignment round-trip qua model có test. Chữ `_num` N01 không đổi so snapshot.

Scope/map không lấy từ `RebarRow.scope_source="confirmed"` tự khai. Resolver đặt lại scope từ bảng mới collect hoặc assignment đã qua validation, và làm việc trên **deep copy** rows. Dấu vết assignment (ref/evidence/by/time/override) nằm trong scope_evidence kèm nguyên văn title; không parse ngược chuỗi này để tính. B2 phải lưu typed assignments ngoài input, không dùng chuỗi evidence thay hợp đồng.

## Trước–sau và phần thiếu giữ lại

- Trước b1: chỉ đọc scope tiêu đề trong reader, không có manifest/mapping core. Sau b1: hai bảng tiêu đề chung có thể được xác nhận cùng scope bằng assignment đúng nguồn/bảng/content → giữ một bảng 31.60 kg; xác nhận hai tầng độc lập → giữ 63.20 kg (SYNTHETIC).
- Scope `per_member` không được dùng dedup hay nhân tầng; giữ số đã đọc và missing/cảnh báo chờ xác nhận. Với đường resolve có source, thiếu scope dù một bảng vẫn pending. Wrapper cũ không context giữ hành vi N02-a: một bảng chung vẫn giữ số cũ; có nghi lặp/chồng thì missing như trước. Không biến thiếu metadata thành lỗi request cũ.
- So nguyên bảng vẫn Counter có bội số/shape/ô lỗi gốc/đơn vị; content SHA sắp canonical theo chữ JSON và bội số, không phụ thuộc thứ tự dòng. Content hash **không** là scope. Giữ raw_cells khác nhau dù cùng None; không thay bằng tổng kg.
- Ref/assignment thuộc source khác hoặc revision/content stale bị chặn; duplicate table_id trong một lời gọi resolve bị chặn. Mỗi lần resolve chỉ thuộc một Drawing/context; ghép kết quả hai source giữ hai row, không dedup xuyên file. B2 không được ghép bảng nhiều Drawing rồi gán một context chung.
- Hash nguồn được kiểm với source context do caller cung cấp, **chưa có byte upload/API nối vào**. Không coi model hợp lệ là chứng thực nguồn; worker b2 phải tính hash gốc từ upload và áp map trước dedup.

## Bằng chứng kiểm thử và hash

Đã lưu SOURCE-READY trước test: `source_ready.json`, `hash_source_ready.json`, snapshot `source_ready/`, `N02-b1_source_ready.diff`. Sau đó chỉ chạy pure reader theo release, không TestClient/DB/CAD thật hoặc full suite.

Lệnh (venv Python):

```text
python -m pytest tests/test_rough_rebar.py -k "not schedule_steel_separate_from_ratio and not no_schedule_leaves_steel_blank and not boq_excel_sheets" -q -ra -p no:cacheprovider --basetemp=reports/n02/b1/temp_reader
```

**71 passed, 3 deselected, 0 failed, 0 skipped/xfail, pytest exit 0**, 6.11s. `pytest_reader.log`, `result_reader.json` có lệnh/mã thoát; bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, đặt OPTIMAT_NO_DOTENV/PYTHONIOENCODING/PYTHONDONTWRITEBYTECODE. Ba ca compute/steel/BOQ không chạy; không dùng số này thay kiểm tích hợp API hoặc partial. Test chỉ thao tác Drawing SYNTHETIC trong bộ nhớ/models/CSV quy tắc sẵn có.

Đã kiểm T7 reader (manifest trước dedup, xác nhận cùng/khác scope, đọc bảng một lần); T8 reader (atomic cả danh sách, lý do override, evidence/by/time); T9 (wrapper/row cũ và JSON round-trip, nhãn confirmed không tự là assignment); T10 reader (source hash byte, revision/content khác, namespace nguồn). Ca xuyên API/lưu input/DWG conversion trace và Q02 partial tổng/vật tư **chưa có**, còn b2/b3.

`before/`, `after/`, `N02-b1.diff`, `hash_before.json`, `hash_after.json`, `hash_diff.json`: chỉ hai file được cấp, không tuyên bố khóa toàn backend khi có writer khác. `hash_diff_since_source_ready.json` rỗng: hai file không đổi trong lúc focused. `git diff --check` hai file exit 0; chỉ cảnh báo Git LF→CRLF.

- Source sau: `54199764811dc7fe48cea14fb62897a43c448516dee95868147c0450288e7328`.
- Test sau: `cc6d17126176b65742fe4bd00558071649d8b1b0c51dec5f5247ca765877b30c`.

## Việc tiếp và phối hợp

Điều phối review b1 độc lập trước cấp b2. B2 nối reupload/mapping vào worker/API/structural_parts và typed input/manifest; b3 thuộc **Q02 numeric + missing**, không tự coi Q01 đã xử lý. Không cắt ánh xạ xác nhận hoặc partial ra khỏi nghiệm thu N02 đầy đủ. J04/B01 đang có quyền NEW `tests/test_rough_formwork_materials.py` và reports/b01; b1 không đụng các file ấy. Khi chuẩn bị ghi materials ở b3 phải đợi B01 bàn giao/hash ổn định và điều phối cấp lượt riêng.

Dòng nhật ký đề xuất: “03/11/2026 — N02-b1 reader collect/manifest/resolve + map nguồn/revision/table/content atomic; giữ wrapper cũ/parser N01; focused pure reader 71 passed, 3 deselected, exit0; hash hai file ổn định qua test; chờ review, chưa API/b2/Q02-b3 hoặc nghiệm thu toàn N02.”
