# N02-b2 — SOURCE-READY, chờ lượt API/worker từ điều phối

03/11/2026 — chỉ sửa vùng được cấp: `src/optimat/api/main.py` (imports + structural worker/endpoint), `src/optimat/rough/takeoff.py` (imports + RoughRequest metadata/notice + structural_parts rebar_reads), NEW `tests/test_rebar_scope_api.py`. **CHỜ REVIEW/API TEST**, chưa tự nghiệm thu b2 hoặc N02 đầy đủ. Không sửa rebar/steel/materials/status/models.py/CSV/DB/frontend/deps, không restart/reload worker PID20288 đang QA bản cũ.

## Hợp đồng và tương thích

- Form tùy chọn `rebar_scope_assignments`: **không truyền** giữ đúng worker/response cũ (không ép caller cũ đọc metadata); **gửi `[]`** bật đường lấy manifest; **gửi danh sách assignment** với cùng file gốc để áp scope. JSON/map sai trả 422; params/đuôi/scale cũ giữ 400 theo luồng trước worker.
- Worker tính `RebarSourceRef.from_bytes(data)` từ byte gốc upload, không filename/client path. DXF đọc trực tiếp; DWG trên đường metadata tái dùng `ingest.convert_with_log` rồi đọc graph DXF đúng một lần. Trace chuyển có sẵn được trả/lưu dưới `rebar_conversion[source_id]`; revision vẫn hash DWG gốc, không hash file chuyển tạm. Đường không truyền map vẫn dùng read_drawing như trước.
- collect một lần → manifest **mọi bảng trước dedup** → resolve toàn bộ map → `structural_parts(..., rebar_reads=[(rows, warnings)])`. Revision/table/content/nhóm scope/override không hợp lệ → ValueError chuyển HTTP422, không gọi structural_parts với kết quả áp dở. Graph/tables không bị đọc lần hai cho metadata.
- `structural_parts` thêm keyword-only rebar_reads mặc định None; có truyền thì phải đúng số Drawing. Caller cũ vẫn reader một lần theo mỗi Drawing; caller có kết quả sẵn dùng đúng cặp rows/warnings theo chỉ số.
- Response đường metadata giữ khóa cũ, thêm `rebar_sources`, `rebar_table_manifest`, `rebar_scope_assignments`, `rebar_conversion`. Ba list + dict này cũng có default_factory rỗng trong RoughRequest. `save_rough` đã lưu input JSON, không cần sửa hàm/lược đồ DB.
- RoughRequest có assignments thì thêm notice duy nhất: JSON chỉ lưu vết, áp/thay mapping cần reupload. Không gọi resolve/dedup, không xóa row/missing, không nâng nhãn confirmed và không parse ngược evidence; row đã resolved cũng được giữ nguyên. Lists/tuple/timezone và trace round-trip bằng model JSON. Đây không phải xác thực danh tính/chuyên môn người khai.

## SOURCE-READY và kiểm thuần đã chạy

Đã lưu `source_ready.json`, `source_ready/`, `hash_source_ready.json`, `N02-b2_source_ready.diff` **trước test**. Chỉ chạy các test model + structural_parts thuần, không TestClient/API/worker endpoint/CAD thật/DB:

```text
python -m pytest tests/test_rebar_scope_api.py -k "scope_model or scope_parts" -q -ra -p no:cacheprovider --basetemp=reports/n02/b2/temp_pure
```

**6 passed, 20 deselected, 0 failed/skipped/xfail, pytest exit0**, 10.33s. `pytest_pure.log`, `result_pure.json` ghi lệnh/kết quả; môi trường bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, OPTIMAT_NO_DOTENV=1. Test lưu input dùng FakeSession/get_engine giả, không có kết nối hay DB thật/test. Hai file reader và test b1 được đối chiếu giữ nguyên hash sau review fix.

Các ca đã chạy: request cũ không metadata; pending/resolved row + metadata JSON round-trip không tự đổi; scope tuple/list và timezone; note reupload không nhân đôi; FakeSession giữ input đầy đủ; structural_parts dùng rebar_reads không gọi reader lại, sai cardinality bị chặn, đường cũ vẫn gọi reader một lần.

## API/worker source test đã viết — CHƯA CHẠY

20 ca còn lại trong NEW test file chờ điều phối/J04: source hash byte không phụ thuộc filename, manifest hai bản trước dedup, cùng/khác tầng; stale revision/table/content/nhóm sai →422 atomic, không half-apply; map JSON lỗi chặn trước worker; DWG hash gốc + trace converter, conversion/read failure và cleanup temp; reupload qua form; JSON-only nhãn confirmed/map inert, không phá row pending/resolved. CAD và converter đều SYNTHETIC/monkeypatch, không chứng minh bản vẽ thật hay converter cài tại máy đạt.

Nhóm worker hồi quy P0 cũ (điều phối gọi 13 ca) phải chạy lại độc lập vì API main đã đổi. Lệnh **đề nghị, chưa chạy bởi phiên này**, ngoài sandbox nếu cần theo bằng chứng socketpair:

```text
python -m pytest tests/test_rebar_scope_api.py tests/test_takeoff_structural_concurrency.py tests/test_takeoff_view_concurrency.py -q -ra -p no:cacheprovider --basetemp=<thư_mục_riêng_do_điều_phối_cấp>
```

Không tự chạy API/TestClient hay full/DB; không đổi source cho test xanh. Cần kiểm response cũ/400/422/worker health/cleanup, đường metadata graph+collect mỗi request một lần và group conflict từ b1 tới HTTP422. Mốc pure6 không thay thế các ca đó.

## Hash/diff và giới hạn

`before/`, `after/`, `N02-b2.diff`, `hash_before.json`, `hash_after.json`, `hash_diff.json` gồm đúng 3 file (test mới before=null). `hash_diff_since_source_ready.json` rỗng; git diff --check exit0. Không nhận là khóa toàn backend vì B01/writer khác có phạm vi riêng.

- main.py sau: `f25d124f4a2366a3678821fc7c8da5898ad0f51d29f841b12351cf0dfad1af24`.
- takeoff.py sau: `03ddde818229db9b4a1abc8174890a289b53bb17884eb94baed88cd1b7ffd56b`.
- NEW test sau: `86c395e041bfc9cfdfa274f2de24e3d95d3cbfb9b51bbc888b9085f9089c3507`.

B3/Q02 còn nguyên, **không sửa trong b2**: điều phối đã lưu repro numeric+scope missing nhưng status A/total complete; manual steel total làm mất missing; dây buộc có waste=0 trong bản sao catalog vẫn complete sai. Xem `reports/partial_review_20261103/before_b3.json` và `before_b3_known_waste.json` khi b3 được cấp; không dùng thiếu hao hụt catalog để làm test vật tư incomplete đạt do sai lý do. B3 phải giữ lượng biết, statusD + missing gốc, tổng/vật tư incomplete, est_costNone, manual total không xóa scope pending. Không suy pure6 hay metadata đã có thành hoàn tất partial.

Dòng nhật ký đề xuất: “03/11/2026 — N02-b2 SOURCE-READY: structural reupload byte gốc/trace DWG, manifest trước dedup, map atomic→422 và metadata request cũ/JSON-only inert; pure model/parts 6 passed20deselected exit0; API/worker13+20 chờ J04, chưa Q02-b3/full/DB/nghiệm thu.”
