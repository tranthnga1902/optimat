# N02-a — SOURCE-READY, chưa chạy kiểm thử

03/11/2026 — đã ghi xong hai file được cấp. **SOURCE-READY / UNTESTED**, dừng ghi mã chờ điều phối release khung kiểm. Không phải hoàn thành/nghiệm thu toàn N02; N02-b bắt buộc còn thiếu.

## File và metadata để phối hợp P0 main

Chỉ sửa `src/optimat/rough/rebar.py`, `tests/test_rough_rebar.py`; không ghi takeoff/steel/models/API/BOQ/CSV hay tài liệu chung. Không đổi chữ trong hàm `_num` N01 (đã đối chiếu tĩnh với snapshot).

Các tên/kiểu đã báo trong commentary trước khi thêm:

| Kiểu/trường mới trong rebar.py | Nghĩa và mặc định |
|---|---|
| `RebarScope.levels: tuple[int, ...]` | Tập tầng tường minh chuẩn hóa, không tự nhân số tầng |
| `RebarScope.element_code: str` | Nhóm theo quy tắc tên cấu kiện đang có; `ALL` chỉ cho tiêu đề ghi “TOÀN BỘ CẤU KIỆN”, không phải mã công tác mới |
| `RebarScope.quantity_basis: Literal["total", "per_member"]` | Reader N02-a chỉ tạo `total`; không tự tạo hay nhân `per_member` |
| `RebarRow.table_id: str = ""` | Tọa độ tiêu đề + thứ tự xác định trong Drawing lượt đọc; chỉ là danh tính bảng, không phải scope/file/revision ID |
| `RebarRow.scope: Optional[RebarScope] = None` | Request cũ không trường vẫn nhận |
| `RebarRow.scope_source: Optional[Literal["title", "confirmed"]] = None` | N02-a chỉ gán `title`; chưa có đường xác nhận/không tự gán `confirmed` |
| `RebarRow.scope_evidence: str = ""` | Nguyên văn tiêu đề làm chứng cứ, kể cả scope chưa đọc được |
| `RebarRow.raw_cells: dict[str, str] = Field(default_factory=dict)` | Ô gốc + `_length_unit` m/mm; không suy scope từ raw_cells. Trường này được điều phối xác nhận riêng |

Không thêm argument vào `read_table` hoặc `read_rebar_schedules`; kiểu trả về giữ `(list[RebarRow], list[str])`. Caller đọc để chuẩn bị: `takeoff.structural_parts` nối rows, `RoughRequest.rebar` giữ row JSON, `steel.schedule_works` gom kg/evidence/missing; API gọi structural_parts. Chưa sửa các caller này. P0 main cần lưu ý row JSON có các trường mới với mặc định; N02-b cần nối source/revision/table identity đúng nghĩa, không coi table_id cục bộ là ID toàn dự án.

## Hành vi mã đã chuẩn bị (chưa xác minh runtime)

- Tự đọc scope theo cú pháp bảo thủ: “BẢNG THỐNG KÊ CỐT THÉP DẦM TẦNG 1 (TỔNG TOÀN TẦNG)” hoặc tập tầng phân cách phẩy + “(TỔNG PHẠM VI)”; nhận TẦNG/LẦU. Nhóm cấu kiện tái dùng quy tắc trong bang_thep.csv, không sửa CSV. Tiêu đề chung, tên tầng không rõ, một mẫu hoặc thiếu chữ chỉ nghĩa tổng không tạo scope. Nhóm tiêu đề trái mã cấu kiện đã đọc cũng giữ scope trống/cảnh báo. Đây là giới hạn cú pháp nhận, không đổi phạm vi BA; tiêu đề rõ theo cách khác sẽ cần ánh xạ N02-b.
- So cả bảng bằng Counter (giữ bội số), gồm shape, số lượng, số đã đọc, missing/notes và ô gốc/đơn vị; không dùng tổng kg hoặc None bằng nhau làm bằng chứng duy nhất. Chỉ bỏ bản sao khi cùng scope có chứng cứ và toàn bảng tương đương. Bảng cùng tầng khác nhóm không tự gộp; ALL chồng các nhóm ở cùng tầng thì cần xác nhận nếu nội dung khác.
- Bỏ khử trùng từng dòng toàn Drawing; hai tầng độc lập giữ cả hai; hai dòng giống nhau trong một bảng không mất. Không có bộ nhớ/dedup xuyên Drawing/file/lần đọc.
- Hai bảng thiếu scope nhưng có dòng tương đương, hoặc scope chồng/cùng scope khác nội dung: giữ rows/nguồn, cảnh báo nghi lặp/chồng và thêm lý do chờ xác nhận vào `row.missing` sau khi so nội dung. Giá trị kg đã đọc được giữ để có số tạm; **chưa chứng minh partial đi tới mọi tổng/vật tư/giá** vì caller chưa được cấp sửa.
- Raw cells so chính xác là lựa chọn bảo thủ: khác cách viết ô dù số bằng nhau có thể không được tự bỏ, thay vì gộp thiếu chứng cứ. Không chuẩn hóa locale hoặc parse ngược evidence.

## Test source đã chuẩn bị và điểm xfail

- Giữ toàn bộ test N01. Hai fixture bảng lặp lịch sử thêm tiêu đề scope tổng “TOÀN BỘ CẤU KIỆN TẦNG 1”, giữ kỳ vọng 5 dòng, còn fixture chung không scope có ca riêng giữ 10 dòng + missing/cảnh báo.
- Thêm ca SYNTHETIC: bản sao có/không mark, hai tầng 31.60 + 31.60 = 63.20 kg, bội số trong bảng, kg bằng nhưng số lượng/chiều dài/shape khác, scope thiếu/mâu thuẫn, tổng nhiều tầng không nhân lại, bảng chồng một phần, hai ô lỗi khác nhau cùng None, đảo thứ tự/lặp lượt đọc, raw_cells/scope JSON round-trip và row cũ không metadata.
- **Chưa bỏ decorator xfail N02** vì chưa được phép chạy test để xác minh. Khi release, lượt đầu đề nghị chạy riêng các test duplicate với `--runxfail`; nếu đạt mới bỏ đúng decorator N02 và chụp lại hash/diff trước bộ trọng tâm bình thường. Source hiện tại có thể XPASS strict ở test N02 đã sửa fixture; không dùng full suite trực tiếp để che/xử lý việc này. N03 không sửa.

## Bằng chứng tĩnh và hash

Không chạy pytest, collect/import probe, compile ứng dụng hay DB. Chỉ đọc file, so text/hash, ghi snapshot/diff và `git diff --check` hai file (exit 0; cảnh báo LF→CRLF của Git không phải lỗi whitespace). Không có log test hay số passed mới.

- `before/`, `after/`: hai snapshot; `N02-a.diff`: diff trực tiếp snapshot, không dùng git HEAD vốn có thay đổi trước.
- `hash_before.json`, `hash_after.json`, `hash_diff.json`: chỉ theo dõi đúng hai file được cấp, không nhận là khóa hash toàn backend lúc P0 main đang ghi file khác.
- `source_ready.json`: trạng thái chưa test và kiểm chữ `_num` giữ nguyên; đây là kiểm tĩnh, không import parser.
- SHA-256 source sau: `52d90b98322a52c2c668a605a7eac5ea123a81ba2830977f94b88a71b02f7b73`.
- SHA-256 test sau: `7d115ccec5531d16d9e6f3cee9c84d9a55c3f5d9c5931fb5f9de14f76ba9bc2e`.

## N02-b / việc còn lại chưa được cấp

1. Ánh xạ scope có người kiểm xác nhận qua input/API, kiểm đúng source/revision/table ID; giữ dấu vết khi sửa trái tiêu đề. Chưa có argument/endpoint/mapping mới trong N02-a.
2. Nối metadata round-trip qua request/response/lưu input; row cũ không bị yêu cầu thêm trường; không dedup thêm trên JSON row do người dùng gửi. Scope_source `confirmed` trong kiểu không thay cho quy trình xác nhận.
3. Thống nhất Q01: row nghi lặp/missing có kg tạm không thành tổng/vật tư/giá hoàn chỉnh. `steel.schedule_works` hiện có gom missing, nhưng chưa được phép kiểm hay sửa phần tổng/trạng thái. Không tự coi một chuỗi cảnh báo là đủ nghiệp vụ.
4. Kiểm T7/T8/T9/T10 của prompt qua callers, tích hợp API/steel/takeoff/Q01 và full khi điều phối cấp. Mọi test ở đây là SYNTHETIC, không tự là đáp án build.

Dòng nhật ký đề xuất: “03/11/2026 — N02-a SOURCE-READY: reader bảng+scope tiêu đề rõ, giữ bội số, metadata tùy chọn; chỉ rebar/test đổi, `_num` N01 giữ nguyên; chưa test/import probe/DB, chờ release; mapping xác nhận và partial xuyên caller còn N02-b, chưa nghiệm thu toàn N02.”

## Cập nhật điều phối — khóa source chờ focused

Điều phối đã đọc `source_ready.json`, hash diff và review tĩnh reader; chốt hai file tại `hash_after.json`. Không sửa tiếp mã/test trong lượt focused. Các trường metadata đã được điều phối chấp nhận; `scope_source="confirmed"` từ payload đơn thuần không đủ làm căn cứ tự khử trùng, đường xác nhận đúng bảng/phiên bản vẫn thuộc N02-b.

Kế hoạch do điều phối cung cấp: giao J04 chạy focused rebar/steel/API worker/rough agent với `--runxfail` (N03 ngoài tập). Chỉ sau khi kết quả đạt và có giao việc tiếp mới bỏ đúng decorator xfail N02, chụp hash/diff mới và chạy normal theo cấp lượt. Phiên này chưa chạy test/import probe/DB, chưa gỡ tag. Chờ kết quả focused; chưa mở N02-b hoặc nghiệm thu N02.

## Cập nhật — đã bỏ đúng tag, STABLE chờ normal/full

Điều phối báo đã đọc kết quả focused API worker + N02-a: **74 passed, 0 skipped/failed, `--runxfail`, pytest exit 0; hash207 không đổi**. Đây là kết quả do điều phối cung cấp; phiên này không chạy lại. Theo lượt được cấp sau kết quả đó, chỉ xóa decorator xfail của `test_duplicate_table_without_mark_counted_once`; kiểm text xác nhận không đổi asserts hoặc reader.

- Snapshot `before/` và `after/`, `hash_after.json` giữ nguyên bằng chứng SOURCE-READY trước gỡ tag.
- `tag_removal.diff`: chỉ một dòng decorator bị xóa; `hash_after_tag_removal.json`: khóa mới; `stable/`: snapshot hai file hiện tại; `N02-a_stable.diff`: diff tổng từ trước N02-a; `tag_removal_result.json`: ghi nhận thay đổi giới hạn và trạng thái chưa normal/full.
- Hash source giữ `52d90b98322a52c2c668a605a7eac5ea123a81ba2830977f94b88a71b02f7b73`; hash test mới `eaa8c02bfea6da858e6895155bdcc8d4af7bd7a2ec1135ce7c53a319fce43a0a`.
- **STABLE**, dừng sửa hai file trong normal/full do điều phối/J04 chạy tiếp. Không tự chạy test/DB/full hoặc nghiệm thu toàn N02; N03 giữ nguyên.
- Trong lúc chờ chỉ lập [đề xuất N02-b](N02-b_PROPOSAL.md), chưa áp mapping/caller/partial vào mã.

## Cập nhật — normal đạt, chờ full integration_0511

Điều phối báo đã tự chạy normal rebar + steel sau bỏ tag: **56 passed, 9.82s, pytest exit 0**. Điều phối cấp J04 chạy full baseline `integration_0511`; hai file rebar/test_rebar giữ nguyên khóa stable, phiên này không chạy backend test hoặc sửa source trong thời gian hồi quy.

[N02-b_PROPOSAL.md](N02-b_PROPOSAL.md) đã đủ danh sách tên/kiểu dự kiến: `RebarSourceRef`, `RebarTableRef`, manifest bảng trước dedup, `RebarScopeAssignment` với scope/evidence/người và thời điểm xác nhận/lý do override, input tùy chọn structural và RoughRequest; điểm nối reader → structural_parts/worker/API → lưu input → steel/Q01/tổng/vật tư/giá. Đề xuất chia b1 nguồn+manifest+reader, b2 upload/round-trip, b3 partial xuyên luồng. Chưa áp bất kỳ field/arg/caller nào của N02-b, chưa có kết quả test N02-b; cần điều phối phân quyền file và duyệt hợp đồng trước mở mã.

Normal N02-a đạt không thay cho nghiệm thu N02 đầy đủ; còn mapping nguồn/bảng/phiên bản được xác nhận và partial xuyên caller. Không đóng mục tiêu điều phối chung.
