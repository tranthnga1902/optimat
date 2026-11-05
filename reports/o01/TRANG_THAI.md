# O01 — source-ready, chưa chạy kiểm thử

Phạm vi: takeoff.py (DTO, cross-reference validation, resolver theo tầng, caller compute_rough) và test lựa chọn nguồn. Không sửa công thức beam_works, N03, status/materials/registry/catalog/boq/frontend. AST các hàm cũ ngoài compute_rough, kể cả attach_prices, giữ nguyên.

- Mỗi tầng một owner; scope từ tiêu đề trần B, mapping/choice trần C. Count lệch, phạm vi không rõ, nhiều view chưa chọn → pending DAM/CP quantity=None/D; phần tầng không tranh vẫn giữ lượng.
- KC đúng tầng chặn cộng manual/suy chưa được chọn; manual thay thế phải ref đúng plan, đúng tầng, có dầm manual kept và evidence. KC rỗng/thiếu tiết diện không tự suy bù.
- Giữ geometry key view gốc. WorkItem KC mang view → tầng; không nhân structural_floors lần nữa. Mapping tầng không chứng minh căn chỉnh XY.
- KC tầng khác không tắt infer; None khác []. Không dùng d KC từ bất kỳ tầng nào để lấp chiều cao xây. Metadata cao dầm chỉ truy local beams thực sự được chọn; thông số beam_depth_mm nhập tường minh vẫn giữ.
- Dầm có đủ dữ liệu không bị mất chỉ vì plan thiếu height; chiều cao tường/cột vẫn xử lý thiếu như trước.

Fixture thuần Python SYNTHETIC: dầm4m/b200/d400/sàn100 → BT0,240m³/CP3,200m² mỗi tầng. A:T2/T3/T4, B:T4/T5: chưa ownerT4 giữ known0,720 vàpendingD; chọnB:T4 →0,960/12,800.

Bằng chứng: BASE225_HASH.json từ full đã nghiệm thu, snapshot/takeoff.py và test_rough_takeoff.py, O01.patch, SOURCE_READY_HASH.json. Mới kiểm AST/snapshot, chưa tuyên bố test pass. Chờ01 cấp slot focused và14 review. Không full/DB/CAD thật.
