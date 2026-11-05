# Review độc lập DATA20 — 14

Ngày 04/11/2026. Chỉ đọc source; không chạy test, SQL, migration, DB hoặc runtime. Đây là kết luận tĩnh và tình huống tái hiện đề nghị owner kiểm trên DB cô lập, không phải receipt thực thi. UI/full cũ vẫn tạm dừng; 03 chưa có bàn giao mới trong trạng thái chat vừa đọc.

## P1 — Có thể gỡ khóa snapshot đã chốt

`src/optimat/db/compat20.py:230–238`: trigger chỉ chặn thay result/input_snapshot/project_id/file_id khi OLD.result_sha256 khác NULL, nhưng cho sửa chính result_sha256. Với analysis đã chốt, UPDATE chỉ đặt result_sha256=NULL được qua; UPDATE tiếp theo có thể sửa result hoặc input_snapshot vì OLD hash đã NULL. Có thể đổi cả khối lượng, count/repetitions, nguồn và giá của snapshot cũ. Cần giữ hash bất biến sau khi chốt và bảo vệ điều kiện khóa độc lập với một trường mà client có thể xóa.

## P1 — Catalog lúc lưu bị nhận là đầu vào lịch sử của phép tính

`src/optimat/db/analysis20.py:68–76`; callers `drawing/review.py:170–187`, `rough/takeoff.py:751–770`: store_details đọc lại các bảng catalog tại thời điểm save, rồi gán catalog_is_historical_input=True khi historical=False. Hàm không nhận catalog thực sự đã dùng để tính. Tình huống: tính với catalog A, cập nhật giá/định mức thành B trước khi lưu, rồi save kết quả A; snapshot lại chứa B và nhận B là đầu vào lịch sử. Catalog truyền trực tiếp hoặc fallback CSV cũng không được chứng minh trùng DB. Cần truyền snapshot catalog thực đã dùng hoặc đánh dấu nguồn chưa xác minh; không dùng catalog hiện tại để chứng nhận giá cũ.

## P2 — Đường dẫn nguồn sai với ReviewPlan không có plans

`src/optimat/db/analysis20.py:23–38`: request có walls ở gốc được bọc thành plans=[request], nhưng occurrences.input_path và evidence.source_ref.path vẫn ghi plans[0].walls / input.plans[0].walls. Với snapshot input.walls[0] không có input.plans, đường dẫn không thể phân giải. raw_content còn nhưng liên kết đến vị trí nguồn gốc sai. Cần chọn prefix theo dạng request thực, giữ index ban đầu.

## P2 — Xóa hoặc chuyển bằng chứng để lại số đo trỏ nguồn mồ côi

`src/optimat/db/compat20.py:262–273`; `schema20.py:120`: evidence_ids là JSONB, validation chỉ diễn ra khi ghi element_measurements. Sau khi số đo tham chiếu evidence E hợp lệ, DELETE E không có reverse constraint bảo vệ; UPDATE E.analysis_id cũng không kiểm các số đo đang tham chiếu. Số đo vẫn giữ ID đã mất hoặc ID khác analysis. Cần chặn thao tác hoặc xử lý tham chiếu ngược trong cùng giao dịch, không âm thầm xóa nguồn.

## P2 — Revision thiếu metadata vẫn qua CHECK do NULL

`src/optimat/db/schema20.py:77`: version, size_bytes, role cho phép NULL; điều kiện version>0 AND size_bytes>0 AND role IN (...) không trả FALSE nếu các trường này NULL và revision_id/sha256 đã có. CHECK SQL chấp nhận NULL. Tình huống insert revision hợp lệ về tệp/dự án, có revision_id và sha256, nhưng version/size_bytes/role=NULL. Cần yêu cầu IS NOT NULL cho từng trường bắt buộc của revision.

## Dấu mốc source

SHA256 khi đọc: analysis20.py `8ad9f1788be2adfbef1b36c5e7582e95d466f62eba72424dabebb39fa6f9f75a`; compat20.py `57eaa81adb0d562470d3120033fc16268a590aecad955f8e10d5c919091eb1b8`; schema20.py `4175ad0bc65e61232f0da85b826d3a846026c983aa76075b2f8bca82c1491a61`.

Không kết luận có lỗi nhân đôi count/repetitions mới trong công thức từ các thay đổi lưu trữ này. Không coi việc đọc source là chứng minh migration không mất dữ liệu, UI/full đã đạt hoặc giá thương mại đã được kiểm. FakeSession.flush đang do owner sửa, không ghi là blocker schema.

## Re-review sau patch S20

Năm finding gốc: **CLOSED_STATIC**. Hash đã được đưa vào điều kiện bất biến; catalog được API capture trước compute và truyền save, thiếu capture ghi unverified và rules_input_verified=False; root walls dùng đúng path; evidence_ids chuẩn hóa bigint JSON và reverse trigger bảo vệ nguồn đang dùng; revision CHECK yêu cầu explicit NOT NULL. Chưa xác minh bằng SQL/test hoặc receipt clone; không nâng thành CLOSED_VERIFIED.

Hash mới: analysis20.py `ebcec9897e95dc3482b4d46499f1fc27f26bc1c69037411d6cc0ec55474c1bf9`; compat20.py `02a74a5879913e746a5e41036f0b4ed944b18adf91a078983e567e730d8bbf29`; schema20.py `3d17b1cb993de69eb804fad3739708202efa3cf5647f1f476e3ef8b848422ba7`.

**P2 OPEN mới — frozen-child còn cho thêm/chuyển dòng vào snapshot đã chốt.** `compat20.py:270–286`: trigger chỉ BEFORE UPDATE OR DELETE và chỉ kiểm parent OLD. INSERT child vào analysis đã đóng không bị chặn; UPDATE child từ analysis chưa chốt sang analysis đã đóng cũng không kiểm parent NEW. Áp dụng building_elements, takeoff_items, element_measurements. Có thể thêm quantity/count/payload hoặc số đo vào projection đã đóng, lệch result JSON bất biến. Owner cần kiểm trên DB cô lập: sealed A/unsealed B; insert child A và move child B→A phải reject, insert/mutate B vẫn hợp lệ. Cần guard INSERT cùng parent NEW khi UPDATE. Đã báo ngay 01 để chuyển S20; reviewer không sửa source hay chạy ca này.

Đã đọc `reports/schema20_focused_latest.log`: 52 passed in 28.05s. Đây là receipt owner, reviewer không chạy. Khi đọc receipt, hash compat20 vẫn là `02a74a5879913e746a5e41036f0b4ed944b18adf91a078983e567e730d8bbf29`, guard trên chưa đổi; không thấy ca insert/move vào sealed trong test_schema20.py. P2 mới vẫn OPEN và đã báo lại 01 trước main. Log này không chứng minh main DB đã chuyển.

### Patch tiếp theo — P2 mới CLOSED_STATIC

`compat20.py:270–299` đã kiểm parent OLD cho UPDATE/DELETE và parent NEW cho INSERT/UPDATE, khóa parent NEW FOR UPDATE; ba trigger bao phủ INSERT/UPDATE/DELETE. `tests/test_schema20.py:182` bổ sung sáu thao tác insert/move vào A sealed cho ba bảng, cùng ca UPDATE B open vẫn được. Đúng lỗ hổng đã báo được khép ở mức source; chưa xác nhận thực thi hoặc concurrency. Không phát hiện blocker mới trong delta này.

Hash: compat20.py `c4f08e102d39153e06dc45340a0f025bce9945b1a2da60e2300d6f74fa562f40`; test_schema20.py `96a93de6a9a51813c2313b3bee5ca6422e2c312466ef4535d76ae3382898dd5a`. Chờ receipt focused mới; 52 passed ở trên là trước patch này. Đã báo 01 chuyển S20. Không chạy test/DB/source write.
