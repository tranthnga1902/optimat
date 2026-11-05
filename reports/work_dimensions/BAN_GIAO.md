# Backend kích thước — phiên03, đạt focused/review14, chờ01 chốt tích hợp

03/11/2026. Thực hiện đúng release của01, tiếp nhận WIP của00; không rollback. **Đạt focused tại phiên sửa, chưa tự nghiệm thu toàn luồng/full.**

## Phiên bản và phạm vi

- Snapshot byte10producer WIP trước sửa: snapshot/ và hash_before.json. Không dùng HEAD để xóa các sửa N03/Q02/masonry đã có.
- Diff đúng lượt03: backend_dimensions.patch. Schema chính xác fields/types/default/đơn vị tại CONTRACT.md; source-ready11file gồm10producer và tests/test_work_dimensions.py; **FINAL_HASH.json** là mốc cuối, trùng SOURCE_READY_HASH v2 sau focused.
- Chỉ sửa models/walls/columns/beams/foundations/areas/stairs/secondary/steel, vùng metadata/lặp metadata trong takeoff và test mới. Không sửa CSV/DB/status/materials/pricing/registry/main/viewer/frontend/boq/O01.
- protected_N03.json và kiểm AST cuối: sáu hàm _axis/_tie_rect/normalize_ties/_tie_evidence/_tie_formwork_support/deduct_ties giữ nguyên. Không đổi quantity/công thức chọn nguồn dầm, phép trừ N03 hoặc wall_groups glue. Metadata nguồn cao tường được chú thích sau producer; không sửa cách chọn độ sâu đang có.

## Hợp đồng và ví dụ thay đổi

- Mỗi cấu kiện/lớp giữ riêng record; không dùng số đại diện cho nhóm khác chiều dài/tiết diện. Các field số strict hữu hạn, không NaN/±inf, không zero hóa; lỗi metadata đi qua ValueError hiện có của API thành422 rõ. Không nới JSON.
- Model cũ thiếu dimensions vẫn[]. None producer truyền là missing_fields, field không dùng là not_applicable_fields; round-trip JSON giữ hai nghĩa và field_sources, 0 giữ nguyên. Metadata thiếu không tự nâng/hạ trạng thái lượng; quantity/missing/status cuối vẫn là căn cứ.
- Dầm trục4m trừ0,2m: gross4/cut0,2/net3,8, BT0,228; sửa nhãn “đã trừ giao0,2m”, không sửa lượng theo nhãn sai. Height toàn tiết diện0,4 khác concrete_height0,3 dưới sàn. Width fallback params/depth từ Beam có nguồn riêng đúng nhánh.
- Cột từng đoạn giữ tiết diện/cao tính BT/cao tầng/dày sàn; cột bảng giữ hai cao độ có dấu. Chưa đổi quy tắc CP trừ đầu dầm; metadata không thay công thức CP.
- Móng từng lớp và đỉnh vát là field số m. Thể tích nhập trực tiếp thắng thì kích thước có sẵn chỉ reference; không tạo hình hộp từ volume. Đào/đắp giữ hố/sâu/taluy/cao độ như tham chiếu, không gọi đó là khối đắp. _neg có deduction record, quantity âm như cũ.
- Sàn/mái/nền dùng diện tích/dày; không bịa dài×rộng. Area gộp/opening/net metadata phân biệt; voidNone không biến thành0. Ground layers có số lớp riêng dù cùng mã. Chống thấm giữ chu vi/cổ tường có nhãn.
- Thang chạy ngang/dài nghiêng phân biệt; bậc/chiếu nghỉ/dầm riêng. Steel bảng có Øm/dài cắt/count/nguồn; thép hàm lượng/manual không có kích thước thanh thì không tạo giả.
- N03 raw records là reference và một record union riêng, không cộng cả hai; CP đáy thiếu vẫn D/None. _neg record deduction không là cấu kiện mới. Count cho một lần, repetitions giữ số tầng lặp riêng, không nhân length/count thêm lần nữa.
- Caller inject cao dầm từ Beam/KC vào wall_params: source/field_sources chiều cao tường giữ đúng ID/nguồn dầm đã dùng, không trỏ params gốcNone. Paramsdepth0 tường minh vẫn thắng. Nhánh KC chưa xác nhận tầng/căn chỉnh nêu giới hạn O01, không giả đã căn chỉnh hoặc sửa source-selection.

## Kiểm trọng tâm — hai lượt, giữ bằng chứng lỗi gốc

Lệnh collector `reports/work_dimensions/run_focused.py` ghi command/PID, toàn bộ log, count/exit và dependency hash. Child bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPTIMAT_CATALOG_OVERLAY, đặt OPTIMAT_NO_DOTENV=1; các metadata oracle dùng Catalog.from_csv(None). Hồi quy cũ có thể dùng sample overlay theo conftest; không dùng chúng để công bố độ chính xác thật. TestClient ngoài sandbox qua escalation được cấp, không DB/CAD thật/full.

Danh sách focused: test_work_dimensions, rough_secondary, rough_status, rough_partial, rough_materials, rough_columns, rough_stairs, rough_formwork_materials, rough_foundations. Không thêm xfail hoặc bỏ assert để che metadata.

1. **attempt1/**: handle43013/PID13868, **227 passed/1 failed/EXIT1**. Failure thực là IndexError ở test_neg vì producer chưa có deduction record; hash224file không đổi. Giữ nguyên log/result/hash/process, không gán passed theo dấu chấm.
2. Sau terminal mới sửa _neg và finding14 về nguồn cao tường, thêm assert beam nguồn manual/structural và explicitdepth0.
3. **attempt2/**: handle25083/PID30768 terminal, **231 passed, 0 failed/errors/skipped/xfail/xpass, EXIT0**, pytest28,58giây (collector30,68giây). Hash224file trước/sau khớp, không changed/added/removed. Source-ready11file vẫn đúng hash cuối sau kiểm.

Bằng chứng cuối: attempt2/focused.log, process.json, result.json, focused_hash_before.json, focused_hash_after.json. Phạm vi hash: Python src/scripts/tests; CSV catalog/rules; CSV/JSON ground_truth. Không claim frontend/docs/DB/worker hoặc toàn repo khác ngoài scope bất biến.

## Review độc lập và giới hạn

- 14 review đúng11hash trước/sau, xác nhận hai finding _neg/nguồn height đã khép ở code, chưa có finding mới trước khi nhận terminal231. Báo cáo14 ở docs/review/backend_dimensions_14/. Chờ14 đối chiếu terminal và01 chốt.
- Cập nhật review14 cuối: đã đối chiếu11/11hash với checkout và attempt2/hash_after, đọc terminal231passed/EXIT0 và224dependency0drift; không thấy blocker mới trên gói metadata, không thấy thay quantity/nhân đôi count/repetitions. Hai finding khép ở code và focused03. Đây là review độc lập chỉ đọc, không thay root nghiệm thu toàn luồng.
- Case source-height mới đã assert p.beams manual và structural, chưa assert riêng nhánh fallback req.structural_beams. Có ghi nguồn/thông báo hạn chế trong code; đây là giới hạn coverage, không tuyên bố đã giải O01 liên tầng.
- Không sửa status hoặc số quantity để làm metadata đẹp. Hở sàn chưa nhập void trong engine là giới hạn có trước: metadata giữ missing/netNone, gói này không nhận đã khép logic quantity/status của hạng mục đó. Không dùng metadata thay điều kiện tối ưu Q02.
- BOQ MVP được00/01 chốt parity công tác/tầng/quantity/đơn vị/formula/source/status/missing, không yêu cầu sheetdimensions. Giữ boq.py nguyên; hồi quy partial/BOQ cũ đạt trong focused, chưa claim đã thêm toàn bộ bảng kích thước vào Excel hoặc hoàn tất parity browser/API/Excel trên hồ sơ thật.
- Chưa full/CAD ACTUAL-build/browser/DB/lưu dự án thật. Gate upload hồ sơ thật đang từ chối, không lách qua API/native/browser khác. Chưa nghiệm thu cả luồng /phan-tho→/dieu-chinh→/vat-lieu→/toi-uu.

## Điều phối tiếp

Giữ source/test ở FINAL_HASH. Trả slot cho01; không tự chạy full hoặc sửa thêm. 02 dùng exact CONTRACT cho UI,14 review chỉ đọc;01 phân lịch parity/freeze/full sau khi các writer khác bàn giao ổn định. O01 chỉ tài liệu thiết kế đã duyệt, chưa triển khai.

Dòng tiến độ đề xuất: “03/11/2026 — 03 tiếp nhận backenddimensions WIP, khép nhãn net/cut, finite/None0/nguồn, cấu kiện/lớp/tầng lặp và raw/hợp/khoản trừ; vòng đầu227/1fail giữlog, sửa theo14 rồi focused231 đạt EXIT0/hash224khôngđổi. Chờ14/01review cuối và UI/parity/full, chưa ACTUAL/DB/O01.”
