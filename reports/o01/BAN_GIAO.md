# O01 — chọn nguồn dầm theo tầng

## Thay đổi

4 tệp: takeoff.py, test_rough_beam_sources.py mới, đúng một test lặp tầng trong test_work_dimensions.py và test trùng view trong test_rough_takeoff.py. BASE225_HASH.json là baseline full824/16skip đã nghiệm thu. Snapshot/diff/FINAL_HASH.json giữ bằng chứng delta. Không sửa N03/secondary, công thức beams, status, materials, registry, catalog, BOQ hoặc frontend. AST hàm attach_prices và mọi hàm cũ ngoài compute_rough giữ nguyên.

- Input optional/backcompat: BeamViewScope, BeamFloorSource; beam_view_scopes, beam_floor_sources default{}; cặp PlanInput.beam_floor_key/beam_floor_evidence. Validation căn cứ, miền tầng, ref, scope, manual kept/source; lỗi cấu trúc/cross-reference trả validation error. Legacy thiếu scope vẫn nhận nhưng pending, không nhân count đoán.
- Một owner mỗi tầng. KC đúng tầng chặn cộng manual/suy chưa chọn; manual thay KC cần chọn rõ. View KC rỗng/toàn keepFalse/thiếu tiết diện không suy bù. Chồng tầng hoặc count lệch → DAM/CP pending/D, giữ số tầng không tranh.
- KC tầng khác không tắt infer. None khác []; [] hoặc local toàn keepFalse sinh pending, giữ phần biết các tầng khác. Cao dầm chỉ từ thông số nhập rõ hoặc local được chọn; không lấy KC chưa căn chỉnh/tầng khác để trừ tường. KC có nhưng thiếu cơ sở cao dầm riêng: XAY/TRAT giữ known quantity, D/missing.
- Mỗi WorkItem KC có nhãn view → tầng; không nhân structural_floors lần hai. Trần scope suy B; mapping/choice C; thiếu D.
- Theo BA bổ sung: RoughResult.plan_beams và structural_beams default{} giữ nguồn hình học riêng. Tên KT/KC trùng thì OMIT khóa ở beams legacy + warning, không ghi đè, không suy ra căn chỉnh XY. Plan raw manual chưa chọn vẫn giữ ở plan_beams để truy vết, không dùng raw maps tính lại lượng.

## Review và kiểm

14 đã xác nhận độc lập exact hash4/4 bản sửa, log terminal273pass/EXIT0 và226deps0drift: khép finding P1 local toàn keepFalse và P2 collision geometry ở mức code + pure focused; không phát hiện blocker mới trong gói. Điều phối01 chốt tiếp nhận cuối, không suy ra HTTP/full đã đạt.

- attempt1: sandbox kẹt TestClient/asyncio, faulthandler120s; dừng đúng childPID44272, collector terminal EXIT4294967295, 226 hash không đổi. Không có summary pass, không dùng số parser0 làm kết quả kiểm. Log/trace vẫn giữ.
- attempt1_pure: 268 passed, 2 failed, 4 deselected, EXIT1; 226 hash không đổi. Hai lỗi: thiếu trạng thái XAY/TRAT khi KC chưa căn chỉnh và thứ tự inputs dòng dầm thiếu; đã sửa caller/trace, không đổi test_status để che lỗi.
- **attempt2_pure: 273 passed, 4 deselected, EXIT0; pytest28,54s, collector31,17s; 226 file hash trước/sau không đổi.** Handle46006/PID38476 terminal. Chín tệp test theo slot01: O01, takeoff, structural, dimensions, secondary, status, partial, materials, price_source.
- Bỏ chủ ý 1 ca CAD thật test_ket_cau_build_drawing và 3 ca HTTP dimensions. HTTP ngoài sandbox bị automatic approval review từ chối vì cho rằng chỉ dẫn gần nhất là read-only/no test; không nhờ phiên khác chạy hộ hoặc lách bằng đường khác. Bản pure dùng sandbox thường, không HTTP/DB. Cổng HTTP vẫn chưa đạt cho O01.

Ca fixture SYNTHETIC: BT0,240m³/CP3,200m² mỗi tầng. A:T2/T3/T4, B:T4/T5: chưa chọnT4 giữ0,720/9,600 và pendingD; chọnB:T4 đúng0,960/12,800. Test truyền partial qua vật tư/BOQ/optimizer, thay manual, count mismatch, None/[], unknown scope, height missing, nofalseXY, source maps collision và validation.

## Bàn giao/giới hạn

FINAL_HASH.json, O01.patch, BASE225_HASH.json, snapshot/, attempt1/, attempt1_pure/, attempt2_pure/ gồm log/mã thoát/process/hash trước-sau. Chưa full suite O01, chưa PostgreSQL/CAD thật/QA giao diện hoặc xác nhận đáp án thực. Source giữ HOLD sau terminal;01 quyết định review/HTTP gate và tích hợp. G8 chỉ hợp đồng/staging, chưa ghép producer vào O01; không mở O02/K01.
