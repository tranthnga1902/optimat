# N02-b — Ma trận test và khóa file sau baseline

03/11/2026 — **CHỈ TÀI LIỆU, chưa cấp ghi source/test; full baseline đang chạy**. Giữ nguyên `N02-b_PROPOSAL.md`; điều phối đã chấp nhận thiết kế collect → manifest → resolve, wrapper tuple cũ, reupload byte hash gốc + table/content hash, validate mapping toàn bộ/422 atomic và metadata tùy chọn round-trip. Không registry/engine/DB/UI mới.

Các tên test dưới đây là **đề xuất**, chưa tạo/chạy. T7–T10 tham chiếu `docs/review/N02_GIAO_DEV.md`; mọi dữ liệu minh họa là SYNTHETIC. Đường nhập/xác nhận mapping qua API là phần bắt buộc của BA, không được bỏ khi không làm UI. Không suy yêu cầu thêm màn hình/giao diện từ chữ “map”.

## 1. T7–T10 → test function/file dự kiến

| Ca / mốc | File test dự kiến | Tên test và bằng chứng cụ thể |
|---|---|---|
| T7 / b1 | `tests/test_rough_rebar.py` | `test_collect_manifest_keeps_tables_before_dedup`: manifest có cả hai bảng kể cả sau resolve chỉ giữ một; collect một lần. `test_resolve_confirmed_scope_requires_source_table_and_content`: cùng byte nguồn/ID bảng/content và xác nhận đủ mới gộp; giữ evidence/by/time/override. 2 bảng 31.60 kg → 31.60 kg khi xác nhận bản sao; scope tầng riêng → 63.20 kg |
| T7 / b2 | `tests/test_takeoff_structural_concurrency.py` | `test_structural_upload_applies_scope_map_in_worker_once`: upload cùng mapping; server tính hash byte gốc; spy graph/collect mỗi thứ một lần; worker trả manifest trước dedup và rows sau resolve. `test_scope_map_roundtrip_keeps_confirmation`: sources/manifest/assignments qua response → RoughRequest JSON → input lưu theo đường hiện có; tuple/list/timezone không đổi nghĩa. Không cần DB để chứng minh serialization; đường lưu DB chỉ khi được cấp riêng |
| T8 / b1 | `tests/test_rough_rebar.py` | `test_scope_override_requires_reason_and_preserves_title`: sửa trái tiêu đề thiếu lý do không áp; đủ lý do/người/ngày/nguồn thì lưu cả gốc và sửa. `test_scope_map_validation_is_atomic`: hai assignment, một đúng/một sai → lỗi toàn bộ trước mutate/dedup, bảng đầu không bị bỏ; input tables không bị sửa dở |
| T8 / b2 | `tests/test_takeoff_structural_concurrency.py` | `test_structural_scope_map_invalid_returns_422_atomic`: JSON lỗi, bảng không tồn tại, thiếu by/evidence/timezone hoặc override_reason → 422 có lý do/bảng; không trả kết quả áp một phần, không thay dữ liệu đã xác nhận. Không tạo auth workflow mới |
| T9 / b1 | `tests/test_rough_rebar.py` | `test_legacy_reader_tuple_and_row_defaults_unchanged`: wrapper vẫn `(rows, warnings)`, call một đối số; RebarRow cũ không metadata vẫn nhận, raw_cells mặc định độc lập; source/mapping rỗng không tự thêm dedup JSON |
| T9 / b2 | `tests/test_rough_takeoff.py` | `test_legacy_request_rebar_roundtrip_without_source`: request cũ giữ số/evidence/missing qua model dump/load; không bắt source/assignments. `test_rough_json_confirmed_label_does_not_resolve_pending`: gắn scope_source=confirmed/mapping tự khai vào JSON không làm bỏ row hoặc xóa pending; có cảnh báo reupload khi muốn áp mapping mới |
| T9 / b2 | `tests/test_rough_agent.py` hoặc test API hiện có được cấp | `test_rough_api_legacy_request_and_inert_scope_map`: `/rough` nhận request cũ; mapping JSON-only chỉ lưu vết, không áp mới. Hai row pending vẫn còn cả hai và giữ lý do. Kiểm theo hợp đồng response thực tế sau P0, không sửa nhiều file API test trùng nhau |
| T10 / b1 | `tests/test_rough_rebar.py` | `test_scope_map_rejects_stale_revision_or_content`: table_id trùng nhưng revision/content sai không áp. `test_same_local_table_id_in_two_sources_not_deduplicated`: hai Drawing nguồn khác cùng ID/nội dung vẫn giữ đủ; source hash không tự là scope |
| T10 / b2 | `tests/test_takeoff_structural_concurrency.py` | `test_structural_scope_map_uses_uploaded_bytes_not_filename`: cùng filename nhưng đổi byte → revision khác/422 map cũ; đổi filename nhưng cùng byte → cùng revision. `test_dwg_scope_revision_uses_original_bytes`: giả lập converter, hash so DWG gốc, trace chuyển còn; không dùng hash DXF tạm làm revision gốc. `test_stale_table_manifest_rejected_on_reupload`: parser/converted content thay đổi → content hash không khớp, 422, không áp nhầm bảng |

Test atomic b1 phải kiểm cấu trúc tables gốc không đổi sau lỗi; không chỉ kiểm thông báo lỗi. Test nguồn phải so hash server tính từ byte upload thực trong fixture, không mock hàm hash để luôn trả số assignment khai. Spy converter/read_graph phù hợp nhưng không thay việc tính hash. Kết quả test hash/content không là chứng cứ chuyên môn của công trình.

## 2. Khóa file theo từng mốc được cấp riêng

| Mốc (≤1 ngày dev/lượt) | File source dự kiến cần khóa | File test dự kiến cần khóa / cổng trước mở tiếp |
|---|---|---|
| b1 collect/manifest/resolve + mapping core | `src/optimat/rough/rebar.py` | `tests/test_rough_rebar.py`. Viết test source hash/atomic/legacy wrapper trước khi thay callers. Chạy trọng tâm chỉ sau release; b1 phải đạt nguồn đúng/nguồn sai + request/row cũ trước b2; không coi b1 là hoàn tất N02 |
| b2 upload worker + rebar_reads + round-trip | `src/optimat/api/main.py` (structural endpoint/worker và guard JSON-only nếu cần); `src/optimat/rough/takeoff.py` (RoughRequest/structural_parts, giữ compute_rough duy nhất); rebar.py chỉ phần context/ref nếu b1 còn cần sửa đã phân rõ | `tests/test_takeoff_structural_concurrency.py`, `tests/test_rough_takeoff.py`; chọn đúng một file API/agent test hiện có cần nối. Sau P0 main ổn định và b1 đã kiểm đạt. Cấp theo đoạn/file, snapshot mới, không viết đè bản P0. Nếu quá một ngày tách upload/worker và JSON-only/round-trip thành hai lượt |
| b3 **Q02** partial numeric + missing | `src/optimat/rough/steel.py`, `src/optimat/rough/takeoff.py` (status sau gán/tổng/guard giá), `src/optimat/rough/materials.py`; `src/optimat/rough/status.py` chỉ khi điều phối cấp rõ điểm nối sau Q01 | `tests/test_rough_steel.py`, `tests/test_rough_takeoff.py`, `tests/test_rough_materials.py`; `tests/test_rough_status.py` chỉ khi được mở. Khóa riêng theo điều phối; không tự mở 4 source file vì cần partial. Chia steel→tổng và vật tư/giá nếu vượt một ngày |

Caller cũ không truyền tham số mới phải chạy qua adapter/wrapper cũ. Schema ở đây chỉ là trường model/API tùy chọn đã đề xuất, không đổi PostgreSQL hoặc thêm service. Báo điều phối trước khi cần file ngoài bảng; không tự chọn file do writer khác đang giữ.

## 3. Q02: partial xuyên luồng bắt buộc trước nghiệm thu N02 đầy đủ

**Không coi Q01 đã xử lý numeric + missing.** Đây là đường biết thiếu thuộc Q02; phải đọc lại sau baseline, áp đúng quyền file điều phối cấp. Dùng A/B/C/D và cờ complete sẵn có, không thêm loại trạng thái N02 riêng.

| Test dự kiến | Đầu vào và kỳ vọng |
|---|---|
| `test_schedule_pending_scope_keeps_numeric_and_missing` — test_rough_steel.py | Hai row 31.60 kg chưa rõ scope → số tạm giữ, missing/evidence hai nguồn còn; thép tổng nhập tay không tự xóa thiếu scope nếu không có xác nhận thay thế đủ nguồn |
| `test_rough_pending_rebar_total_is_incomplete` — test_rough_takeoff.py | Numeric thép + pending/missing → status D theo contract Q02, tổng complete=False; phần số đã tính được giữ theo làm tròn engine, không biến thành None/0 để né kiểm |
| `test_pending_rebar_marks_steel_and_tie_wire_incomplete` — test_rough_materials.py | Thiếu scope truyền tới thép **và dây buộc**/định mức phụ thuộc; line/use có lý do, incomplete; không làm mất phần đã biết hoặc hạ vật tư độc lập không liên quan |
| `test_pending_material_keeps_offer_but_no_complete_cost` — test_rough_takeoff.py | Có báo giá đúng đơn vị vẫn giữ best_price/source nhưng est_cost=None vì lượng chưa đủ; API/Excel gọi cùng compute_rough, không công thức chốt song song |
| `test_reuploaded_scope_resolution_preserves_other_missing` — test tích hợp được cấp | Reupload map đúng có thể giải quyết nghi lặp, nhưng thiếu Ø/quy cách/hao hụt khác vẫn thiếu. Bản sao 31.60 kg và hai tầng độc lập 63.20 kg trước đổi tấn/làm tròn; không nâng đủ toàn bộ chỉ vì map đã áp |

## 4. Trạng thái và bàn giao

Đã đủ ma trận tên test/file và vùng cần khóa để điều phối giao từng lượt sau full. Chưa tạo test source, chưa áp helper/arg/metadata của N02-b, chưa chạy test/collect/import probe/DB. Không sửa proposal đã chốt trong lượt này; proposal nhắc Q01 là điểm nối lịch sử, còn **quyền thực hiện numeric + missing theo Q02 và cấp file mới của điều phối** như tài liệu này.

Điều kiện không được cắt: mapping có xác nhận qua đường nhập/API, kiểm nguồn/revision/table/content, request cũ và partial tổng/vật tư/giá đều phải đạt trước kết luận N02 đầy đủ. UI mới ngoài phạm vi; không dùng việc chưa có UI làm lý do bỏ đường nhập/API bắt buộc. Full/DB và nghiệm thu do điều phối cấp/quyết định; tài liệu này không tự mở lượt dev.
