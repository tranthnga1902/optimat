# N02-b — Đề xuất hợp đồng mapping/xác nhận và partial

03/11/2026 — **CHỈ ĐỀ XUẤT, CHƯA CẤP TRIỂN KHAI**. BA đã chốt trong `docs/review/N02_CHUAN_BI.md`; N02-a đang khóa ở `hash_after_tag_removal.json` chờ normal/full. Không sửa API/takeoff/steel/models/status/materials hoặc chạy probe/test/DB trong lượt lập tài liệu. Phải đọc lại các file sau khi P0/Q01 bàn giao; tham chiếu dưới đây chỉ là điểm nối đọc hiện tại, không khóa source của writer khác.

## 1. Nguyên tắc đường xác nhận tối thiểu

- Cấp scope có xác nhận ở **lần đọc bảng từ nguồn**, trước khi dedup bảng nguyên. Giữ endpoint structural/rough hiện có, không engine hay UI mới. Sau mapping cần đọc lại đúng nguồn để phục hồi mọi bảng trước khi chọn bỏ bản sao; không cố tái dựng bảng đã bị reader cũ bỏ từ danh sách row còn lại.
- Hướng tối thiểu đã được điều phối chọn: **gửi lại đúng file tại structural upload khi áp mapping**, server tính SHA-256 byte gốc và so revision assignment. Không tạo registry nguồn/DB/service mới, không nhận client path. `file`/đường dẫn tạm/tên người dùng gửi không phải revision. DWG giữ hash gốc và dấu vết chuyển tạm, không đồng nhất hash DXF tạm với hash DWG gốc.
- `scope_source="confirmed"`, tên người kiểm hoặc hash do payload tự khai **không đủ** để tự bỏ dữ liệu hay xóa pending. Chỉ áp mapping khi server tìm đúng bản nguồn + đúng bảng và có thông tin xác nhận đủ. Đây là dấu vết xác nhận nghiệp vụ, không tự chứng minh người khai có chuyên môn.
- Request cũ `rebar` không metadata vẫn nhận và không dedup thêm. Request có mapping mới nhưng không đối chiếu được nguồn/bảng thì không áp mapping; giữ dữ liệu/nguồn và lý do chờ. Không âm thầm bỏ mapping lỗi rồi trình bày tổng đủ. Từ chối cấu trúc mapping không hợp lệ bằng validation; revision cũ/bảng không tồn tại phải báo lỗi/nhu cầu đọc lại rõ, không tự chuyển sang revision khác.

## 2. Tên/kiểu trường dự kiến để điều phối phân file

Đây là đề xuất cho review, chưa là schema được triển khai. Không đổi PostgreSQL; ưu tiên input/result JSON sẵn có.

| Nơi / tên dự kiến | Kiểu, nghĩa và mặc định tương thích |
|---|---|
| `RebarSourceRef.source_id` | `str`: server tạo `structural:<revision_sha256>` từ upload; chỉ namespace nguồn, không nhận client path hay dùng filename làm căn cứ |
| `RebarSourceRef.revision_sha256` | `str`: SHA-256 nguồn đã được server đối chiếu; đổi byte là revision khác; không dùng số thứ tự file làm hash |
| `RebarTableRef` | `{source_id: str, revision_sha256: str, table_id: str}`; namespace đủ để hai file có cùng table_id cục bộ không bị gộp |
| Manifest bảng do reader trả trước dedup | Mỗi bảng có `ref: RebarTableRef`, `title: str`, `row_count: int`, `content_sha256: str`, `scope_from_title: RebarScope | None`; gồm cả bảng đã được đề nghị bỏ bản sao. Content hash giúp kiểm đúng bản bảng, **không** chứng minh scope hay thay so bội số/ô gốc |
| `RebarScopeAssignment.ref` | `RebarTableRef`: đúng bảng trong manifest được đối chiếu nguồn; không ghép gần nhất theo tọa độ |
| `RebarScopeAssignment.content_sha256` | `str`: hash nội dung bảng từ manifest của lần đọc trước, phải khớp bảng trước dedup trong lần reupload; hash không thay cho scope |
| `RebarScopeAssignment.scope` | `RebarScope` hiện có: levels/element_code/quantity_basis; chỉ tổng đã rõ được tự dedup, không tự nhân `per_member` |
| `RebarScopeAssignment.evidence` | `list[str]`: chi tiết/ghi chú nguồn chỉ phạm vi và nghĩa số lượng; phải có khi xin áp mapping |
| `RebarScopeAssignment.confirmed_by`, `confirmed_at` | `str`, `datetime`: người xác nhận nghiệp vụ và thời điểm có timezone; bắt buộc, không tự điền người kiểm. Đây là xác nhận đầu vào có truy vết; không thêm UI/auth workflow để xác minh chuyên môn trong N02 |
| `RebarScopeAssignment.override_reason` | `str | None = None`: bắt buộc khi sửa trái tiêu đề; lưu cả scope/title ban đầu và kết luận mới, không ghi đè chứng cứ gốc |
| Input structural form `rebar_scope_assignments` | `str | None = None`: JSON danh sách mapping khi gửi cùng byte nguồn; thiếu thì đường cũ. Worker parse/validate rồi cấp scope trước dedup |
| `RoughRequest.rebar_sources`, `rebar_scope_assignments` | `list[...] = Field(default_factory=list)`: round-trip nguồn đã đối chiếu và mapping; không bắt request cũ thêm dữ liệu |
| Row nguồn | Đề nghị `RebarRow.source_id: str = ""`, `revision_sha256: str = ""` để nối row với bảng/nguồn qua input JSON; caller cũ vẫn nhận. Không parse ngược evidence và không tạo registry |

Không bổ sung cờ `verified=True`, registry, token ký, session service hay DB mới. `/rough` chỉ có JSON thì **không áp mapping mới, không dedup lại**; metadata nguồn/mapping ở đó chỉ để lưu vết. `confirmed` tự đặt không được xóa missing/pending hoặc nâng mức xác nhận. Muốn thay phạm vi đang pending phải gửi lại file + assignment qua structural upload để server đọc đúng nguồn và áp trước dedup. Byte nguồn không có trong request JSON thì không tuyên bố đã kiểm lại nguồn. Không tự đổi xác nhận đầu vào thành chứng thực danh tính/chuyên môn.

## 2A. Hợp đồng hàm/tham số/return cụ thể đề nghị triển khai

Các chữ ký dưới đây là **đặc tả trong tài liệu**, chưa áp vào mã. Giữ cùng một pipeline thu bảng → áp scope → so bảng; không thêm engine hoặc đọc lại graph hai lần.

```python
# rebar.py: RebarTable là dữ liệu trung gian của reader, không bảng DB.
# RebarTable: table_id, title, rows, scope_from_title (chưa loại bản sao).
collect_rebar_tables(drawing) -> tuple[list[RebarTable], list[str]]
table_manifest(tables: list[RebarTable], *, source: RebarSourceRef
               ) -> list[RebarTableManifest]
resolve_rebar_tables(tables: list[RebarTable], *,
                     source: RebarSourceRef | None = None,
                     assignments: list[RebarScopeAssignment] | None = None
                     ) -> tuple[list[RebarRow], list[str]]
read_rebar_schedules(drawing) -> tuple[list[RebarRow], list[str]]

# takeoff.py: keyword-only mới; đường cũ không truyền vẫn gọi wrapper như cũ.
structural_parts(drawings, params=None, structural_scale=None, *,
                 rebar_reads: list[tuple[list[RebarRow], list[str]]] | None = None
                 ) -> tuple[ProjectParams, dict]

# main.py: thêm cuối, có mặc định để các caller hiện hành vẫn hợp lệ.
_takeoff_structural_payload(data, suffix, file_name, project, structural_scale,
                           rebar_scope_assignments: list[RebarScopeAssignment] | None = None
                           ) -> dict
```

- `read_rebar_schedules` là wrapper tương thích gọi collect **một lần** và resolve bằng scope tiêu đề; vẫn trả đúng tuple `(rows, warnings)`, không đổi callers một đối số.
- Worker structural nhận form JSON tùy chọn `rebar_scope_assignments: str | None = Form(None)` cùng byte upload. Parse cấu trúc/chuỗi không rỗng/timezone trước; tính hash từ `data`, tạo source; đọc graph một lần, collect bảng một lần; manifest từ các bảng **trước dedup**, validate toàn bộ assignment rồi resolve. `table_manifest` chỉ duyệt bảng đã thu, không gọi `read_drawing`/`read_table` lại.
- Mỗi assignment phải khớp source_id + revision_sha256 + table_id + content_sha256 của manifest mới. Cùng table có assignment mâu thuẫn, revision/content sai, table không tồn tại hoặc override trái tiêu đề thiếu lý do → HTTP 422 có lý do/bảng liên quan; không áp một nửa danh sách. Không thay nguồn hoặc bỏ dữ liệu đã lưu khi trả lỗi. Scope tổng đã rõ mới cho bỏ bảng nguyên tương đương; `per_member` giữ chờ, không nhân.
- Worker gọi `structural_parts([drawing], ..., rebar_reads=[(rows, warnings)])`. `structural_parts` kiểm độ dài rebar_reads đúng số Drawing nếu có, lấy đúng cặp theo chỉ số thay vì gọi reader lại. Các cấu kiện khác tiếp tục luồng hiện có. Caller cũ không truyền thì reader chạy như hiện nay. Không cache graph/global registry.
- Response structural giữ các khóa cũ, thêm `rebar_sources: [source]`, `rebar_table_manifest: manifest`, `rebar_scope_assignments: assignments_đã_áp`; manifest bao gồm cả bảng bị bỏ bản sao và scope gốc. Cần thêm `RoughRequest.rebar_table_manifest: list[RebarTableManifest] = Field(default_factory=list)` cùng hai list đã đề xuất để lưu JSON; đây là metadata đầu vào, không là cơ chế tự áp mapping trong compute_rough.
- Với DWG, response source kèm trace chuyển đổi sẵn có (nếu có) và hash byte gốc; không thêm dịch vụ chuyển đổi. Assignment so revision gốc, còn content_sha256 kiểm đúng bảng đã chuyển/đọc ở lần đó; thay converter/rules làm nội dung khác thì mapping cũ không áp im lặng.
- JSON-only `/rough`: các list metadata được giữ khi round-trip/lưu input nhưng không dùng để xóa row hay xóa lý do chờ. Nếu client muốn áp mapping mới, trả cảnh báo rõ phải reupload nguồn; giữ numeric + pending của phần liên quan. Không tạo endpoint/apply flag để lách việc thiếu byte nguồn. Các trường `confirmed_by/at/evidence` chỉ được dùng làm căn cứ áp mapping trong worker đã đối chiếu byte nguồn/bảng, không phải từ `RebarRow.scope_source` tự khai.

## 3. Callers/file cần phân quyền sau khi writer ổn định

| Điểm nối đọc hiện tại | Việc cần làm ở lượt được cấp |
|---|---|
| `rough/rebar.py:read_rebar_schedules` | Tách collect/manifest/resolve theo 2A, giữ wrapper một đối số và tuple cũ. Không dedup xuyên source; mapping sai không làm mất bảng |
| `rough/takeoff.py:structural_parts`, `rough_from_drawing` | Nhận rebar_reads tùy chọn để không đọc bảng lại; giữ đúng nguồn từng Drawing khi nối rows. Không tái sử dụng file kiến trúc làm nguồn mọi bảng kết cấu; đường auto không được tự áp mapping nếu không đi qua reupload đã kiểm |
| `api/main.py:_takeoff_structural_payload`, `takeoff_structural`; rough/excel khi cần | Mapping chỉ có hiệu lực khi gửi lại file qua structural, hash server tính từ data; một lần đọc graph/collect, trả manifest + input. `/rough` không dedup row JSON hoặc áp mapping mới. Excel và API cùng compute_rough |
| `rough/takeoff.py:RoughRequest`, `save_rough` | Default rỗng cho field tùy chọn; tuples/list và datetime JSON giữ nghĩa; lưu input + nguồn/mapping trong JSON hiện có. Chưa kiểm DB, không đổi lược đồ |
| `rough/steel.py:schedule_works`, `steel_works` | Giữ hai scope độc lập dù cùng C1/mark; lượng có thể cộng nhưng nguồn đủ. Nghi lặp/khác revision/mapping không hợp lệ phải giữ missing tới công tác. Kiểm ưu tiên `steel_schedule_t`: tổng t nhập không tự giải quyết tính đúng phạm vi nếu thiếu nguồn xác nhận |
| Q01: `rough/status.py`, tổng trong `rough/takeoff.py`, `rough/materials.py` và `attach_prices` | Dùng hợp đồng hoàn tất chung sau Q01, không tạo status N02 riêng. Khối lượng có số + missing/pending không được thành tổng complete hoặc vật tư/giá hoàn chỉnh |

Hiện đọc thấy `schedule_works` đã gom missing, nhưng `assign_status` chủ yếu chặn khi quantity=None; tổng công tác dựa số quantity biết được. Vì writer Q01 đang có việc, đây là **điểm cần kiểm lại**, không đề nghị sửa chồng ngay. `MaterialLine.complete` và est_cost chỉ đúng khi cờ thiếu được truyền xuyên suốt; một cảnh báo reader không đủ chứng minh.

### Partial: vị trí cụ thể trong ba file, không tạo trạng thái mới

| File/hàm | Hợp đồng cần bảo toàn sau Q01; chỉ sửa khi được cấp |
|---|---|
| `rough/steel.py:schedule_works`, `steel_works` | Cộng kg biết được thành quantity tạm, gom tất cả row.missing (kể cả nghi lặp/mapping chưa áp) vào WorkItem.missing và giữ evidence từng nguồn. Tổng t nhập tay không tự xóa lý do chưa xác nhận scope của nhóm bị thay thế; phải có xác nhận phạm vi tương ứng, nếu không vẫn thiếu. Không dedup thêm hay nhân tầng ở bước steel |
| `rough/takeoff.py:compute_rough` sau assign_status và khi dựng WorkTotal; `attach_prices` | Tái dùng quy tắc Q01 cho numeric + missing: giữ quantity tạm nhưng trạng thái D/inputs lý do, WorkTotal.complete=False nếu bất kỳ dòng góp phần còn missing/D hoặc không có quantity. Kiểm rõ COT_THEP để không nâng A chỉ vì basis bảng. Không sửa status.py chồng Q01 nếu Q01 đã trả đúng; nếu chưa đủ phải báo điểm nối cho điều phối, không mở file thứ tư im lặng. `attach_prices` đã có guard m.complete: giữ báo giá tham khảo nhưng est_cost=None khi lượng chưa hoàn chỉnh |
| `rough/materials.py:_Bill.add`, `materials_for_works` nhánh COT_THEP và norm_line/dây buộc | Missing của công tác phải truyền vào mọi MaterialUse/vật tư phụ thuộc của chính công tác, kể cả dây buộc qua định mức; không chỉ dòng thép chính. Lượng đã tính vẫn giữ; line.complete=False, status D và missing nguồn; một use thiếu làm tổng vật tư tương ứng chưa đủ. Không chặn các vật tư độc lập không liên quan, không coi hệ số định mức đủ là đã giải quyết scope |

Ca xuyên ba file bắt buộc: hai bảng chưa rõ là bản sao, mỗi bảng 31.60 kg → công tác 0.0632 t tạm (theo làm tròn engine), missing còn; tổng thép chưa complete; vật tư thép/dây buộc tương ứng chưa complete, est_cost=None dù có giá. Sau reupload xác nhận bản sao → 0.0316 t trước làm tròn; sau xác nhận hai tầng độc lập → 0.0632 t trước làm tròn. Hai đường cuối chỉ complete nếu các đầu vào khác như quy cách/hao hụt đều đủ; không dùng kiểm scope để che thiếu khác. Các số SYNTHETIC không là đáp án build.

## 4. Chia mốc triển khai, mỗi lượt tối đa một ngày dev

1. **N02-b1 — nguồn + manifest + áp mapping ở reader**: chỉ sau duyệt field/arg và quyền file. Kiểm hai file cùng tọa độ không chung namespace; source/revision/table sai không áp; manifest có bảng trước dedup; scope xác nhận đúng bỏ một bản sao; scope khác giữ hai bảng. Chưa nghiệm thu N02 nếu chưa nối API/partial.
2. **N02-b2 — upload/worker và round-trip input**: sau P0 main bàn giao API/takeoff. Test mapping gửi cùng file, hash server tính đúng, người/ngày/nguồn và override_reason được giữ; stale revision không áp; row/request cũ vẫn nhận; tuples thành list rồi đọc lại giữ nghĩa; metadata `confirmed` giả/thiếu đối chiếu không gây bỏ row. Đọc lại nguồn khi đổi scope để không mất bảng bị bỏ ở lần trước. Không UI/DB schema mới.
3. **N02-b3 — partial xuyên steel/tổng/vật tư/giá**: sau Q01 ổn định, khóa riêng các đoạn. Ca nghi lặp có kg tạm: công tác giữ số + lý do, tổng không complete; vật tư liên quan incomplete và không có chi phí hoàn chỉnh; hai tầng độc lập đủ phạm vi vẫn 63.20 kg. Kiểm bảng nhiều tầng đã tổng không nhân tiếp, tổng theo bảng nhập tay không che nguồn thiếu. API/excel cùng compute_rough; không sửa ma trận BOQ đang writer khác giữ khi chưa cấp.

Mỗi mốc bàn giao diff/test/hash/giới hạn riêng; nếu một mốc quá một ngày, tách tiếp trước thực hiện. Điều phối có thể gộp file khi đã phân quyền rõ, không gộp nghiệm thu khi còn một đường xác nhận hoặc partial chưa đủ.

## 5. Điều kiện nghiệm thu N02 đầy đủ

Hoàn tất các ca T7/T8/T9/T10 trong prompt cùng hồi quy N02-a/N01: mapping có hiệu lực chỉ với nguồn+bảng+revision đúng, override có dấu vết; thiếu nguồn giữ pending; request cũ không bị từ chối hay dedup lại. Source xác nhận không làm mất dữ liệu từ scope độc lập. T14 giữ ô lỗi gốc; numeric+missing không thành complete ở tổng/vật tư/giá. Đường lưu input/request/response/Excel nhất quán; test DB/full chỉ khi có lượt riêng. Dữ liệu SYNTHETIC chứng minh kỹ thuật, không thay đáp án build/người kiểm.

Chưa chạy thử hay áp bất kỳ trường/arg/caller nào trong đề xuất này. Hướng reupload, không registry/service/DB/path, một pipeline và tuple cũ đã được điều phối chọn. Còn cần cấp lượt triển khai và xác nhận contract cụ thể tại 2A/vị trí partial sau Q01, danh sách file/mốc được mở. Phạm vi nghiệp vụ BA không cần hỏi lại; mapping và partial không được cắt khỏi nghiệm thu N02 đầy đủ.
