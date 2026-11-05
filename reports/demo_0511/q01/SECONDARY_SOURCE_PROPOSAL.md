# Q01 nguồn giằng/sê nô — đề xuất, CHƯA ÁP DỤNG

Phạm vi dự kiến: `src/optimat/rough/secondary.py::linear_works` và `tests/test_rough_secondary.py`.
Không source edit, test run, schema, công thức hoặc đổi nhóm trong lượt chuẩn bị.
`status.py`/`test_rough_status.py` giữ nguyên hash SOURCE-READY.

## Chỗ mất nguồn

linear_works nhóm theo (b_mm,d_mm), giữ danh sách items từ LinearMember. Cả hai `_work` bê tông/cốp pha không truyền source, nên mặc định WorkItem.source='auto'. Nhánh giằng ở assign_status fallback auto thành C; LinearMember structural không còn được A dù evidence có structural.

Không thể chỉ gắn `source=m.source`: tại vị trí `_work` không có m đại diện nhóm; m còn sót là phần tử cuối vòng lặp trước, có thể thuộc nhóm khác.

## Diff tối thiểu đề nghị

Sau khi tính evidence, thêm:

```python
sources = {m.source for m in items}
source = next(iter(sources)) if len(sources) == 1 else "auto"
```

Truyền `source=source` vào hai `_work` bê tông và cốp pha. Giữ nhóm (b,d), thứ tự, lượng, công thức và evidence như cũ. Nhóm nguồn đồng nhất giữ nguồn gốc; nhóm trộn dùng fallback auto hiện có để không được nâng A sai; evidence vẫn ghi từng nguồn. Không thêm giá trị enum/schema hoặc chuỗi nguồn mới. Nếu muốn nguồn riêng từng work thì group thêm source là thay đổi hợp đồng nhóm, cần lượt riêng; chưa đề nghị.

## Ca kiểm đề nghị

1. Parametrize kind GIANG_TUONG/SE_NO và source structural/manual/inferred. Member 4m b220 d150. linear_works -> assign_status, quantity bê tông0,132m³ không đổi. Expected structural A, manual C, inferred C theo chính sách fallback hiện tại. Hai WorkItem giữ source và CP có status tương ứng.
2. Hai member cùng b,d nhưng khác nguồn structural/manual: vẫn một nhóm bê tông+CP, tổng lượng bằng trước; status C, không nhận A tùy thứ tự; evidence chứa cả hai nguồn. Đổi thứ tự nhập vẫn cùng status/quantity.
3. Hai nhóm tiết diện khác nguồn: mỗi nhóm lấy đúng source của items, tránh stale m loop.
4. keep=False không làm yếu nguồn nhóm đang dùng.

Chạy trọng tâm sau cấp lượt: `tests/test_rough_secondary.py tests/test_rough_status.py`; xfail N03 trùng giằng giữ nguyên vì ngoài scope.

Giới hạn: infer nguồn fallback C là hành vi hiện tại, chưa đổi thành B. Giằng chưa căn KT-KC/tầng vẫn không được tự trừ từ bản kết cấu; đề xuất chỉ phục hồi provenance, không xác nhận hình học hoặc nghiệp vụ.
