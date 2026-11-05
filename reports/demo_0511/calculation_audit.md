# Rà tính toán cho demo 05/11 — 03/11/2026

Phạm vi: chỉ đọc mã và test. Chưa sửa source/data, chưa chạy test hoặc DB. Không đụng N01 (`rebar.py::_num`, `test_rough_rebar.py`) đang do phiên khác giữ.

## Đề nghị giao trước: A01 hao hụt theo từng phần góp

- File độc quyền đề nghị: `src/optimat/rough/materials.py` và `tests/test_rough_materials.py`.
- Bằng chứng: `_Bill.add` (dòng 86–105) giữ `MaterialUse.quantity` và `waste_included` cho từng phần góp. `_Bill.result` (268–273) chỉ phân hai trường hợp: mọi phần đã gồm hao hụt hoặc nhân toàn bộ `line.quantity` với tỷ lệ. Khi cùng mã XM02 nhận phần từ cấp phối TT38 và nguồn không mã, phần TT38 cũng bị cộng hao hụt lần nữa.
- Ca số học: 10 đã gồm + 10 chưa gồm; 3,5%: hiện 20,700, đúng phải 20,350.
- Sửa tối thiểu: tổng hai nhóm phần góp có/không gồm hao hụt và chỉ cộng phần chênh của nhóm chưa gồm. Giữ `quantity` là tổng lượng sử dụng hiện tại, không đổi hợp đồng trường hoặc DB. Không lấy tổng số đã làm tròn từng phần thay cho tổng nội bộ khi mọi phần đều đã gồm.
- Test cần có: hỗn hợp 10+10; tất cả đã gồm; tất cả chưa gồm; thiếu tỷ lệ chỉ báo khi còn phần chưa gồm; phần trừ âm; phần góp thiếu lượng giữ complete=False/status D và không trình bày như lượng mua đầy đủ; số rất nhỏ kiểm sai số làm tròn.
- Chạy trọng tâm đề nghị sau cấp lượt: `.venv/Scripts/python.exe -m pytest tests/test_rough_materials.py tests/test_rough_plaster.py -q -p no:cacheprovider` với môi trường không DB/.env. Full suite do điều phối cấp lượt, không chạy song song.
- Caller đã rà: `_Bill` chỉ khởi tạo trong `materials_for_works`; `.result` được gọi ở cuối hàm này. Đầu ra `quantity_with_waste` dùng trong `rough/takeoff.py::attach_prices`, `rough/boq.py`, frontend `do-boc/Rough.tsx` và `phan-tho/rough.tsx`; không cần đổi chữ ký để sửa công thức.
- Giới hạn liên quan chưa tự gộp: `attach_prices` đang fallback quantity khi quantity_with_waste thiếu, và `complete` hiện nói về lượng sử dụng chứ không riêng lượng mua. Đây là Q02/phần chi phí cần lượt riêng, không âm thầm đổi semantics trong A01.

## Các việc tiếp theo

| Mã | Bằng chứng | Phạm vi tối thiểu / tiêu chí |
|---|---|---|
| Q01 | `status.py::_inputs` CAU_THANG chỉ gọi `_src`, bỏ dày bản thang và nguồn cao tầng. `stairs.stair_works` thực tế dùng cả dày lẫn cao tầng | `status.py`, `tests/test_rough_status.py`: auto+dày nhập tay => C, inputs nêu dày/cao; thiếu dày => D. Giằng structural hiện không giữ source trong linear_works, cần `secondary.py` và test riêng nếu mở rộng |
| Q02 | `takeoff.py` totals giữ tổng phần đã biết và complete=False; frontend hiển thị "còn thiếu" nhưng chưa nhãn "một phần". group_totals chỉ xét có weight_kg, không xét dòng material.complete | Cần phối hợp backend/frontend, không thể sửa chỉ status.py. Chốt quantity là known_part hay tổng đủ trước khi thay semantics |
| N03 | `secondary.py::linear_works` cộng L mọi giằng; `deduct_ties` lần lượt trừ từng member. Test xfail `test_overlapping_ties_deduct_masonry_once` có sẵn | Không nên chỉ union XY: LinearMember chưa có cao độ; hai giằng khác cao độ sẽ bị gộp sai. Cần chốt dữ liệu/cao độ hoặc giới hạn chỉ bản sao xác minh. N03 không phải lượt nhỏ an toàn trước khi chốt hợp đồng |
| B01 | Test cốp pha hiện chỉ COT/SAN; DAM/MONG/CAU_THANG và dòng âm chưa có đủ bằng chứng | `tests/test_rough_materials.py` sau A01: thêm số học theo định mức hiện hành, không sửa CSV khi chưa có quyền |

Ưu tiên: A01 -> Q01 -> B01, Q02 phối hợp UI/backend; N03 cần chốt cao độ trước. Chỉ triển khai khi parent/điều phối giải phóng phạm vi file. Báo cáo này chưa chứng minh sai số bộ bản vẽ thật hoặc trạng thái runtime.

## Kế hoạch diff Q01 độc lập (đọc sâu, chưa sửa source)

Phạm vi đề nghị chỉ `src/optimat/rough/status.py` + `tests/test_rough_status.py`. Không `materials.py`, không `rebar.py`, không `models.py`/schema.

1. Nhánh `_inputs(... code == CAU_THANG)` giữ nguyên `_src(w.source, ...)` để không mất phân biệt auto B/manual C/structural A.
2. Thêm `_param(params.stair_slab_thickness_mm, "dày bản thang")`: công thức `stair_works` dùng dày này cho bản và chiếu nghỉ. Khi auto geometry B + dày nhập C, trạng thái cuối C.
3. Thêm đầu vào chiều cao tầng theo `h` (giống tường/cột), vì công thức dùng H cho slope và riser. Nguồn cao độ -> B, nhập tay -> C, không có nguồn -> D. Với dòng CAU_THANG có số nhưng không có map chiều cao, đầu vào là D, không gán B im lặng.
4. Giữ đường `quantity is None` hiện hành: D + lý do từ missing. Không đổi công thức hay khối lượng.
5. Cốp pha thang kế thừa trạng thái cha đã có ở assign_status cuối, nên tự thành C; thép theo hàm lượng cũng kế thừa, không cần sửa caller.

Bằng chứng caller: `compute_rough` truyền `{p.name: p.height_source or ("nhập tay" if p.height_mm else "chưa có")}` vào assign_status; stair_works dùng `height_mm` và params.stair_slab_thickness_mm. `_inputs` hiện chỉ ghi nguồn hình học thang.

Các test tối thiểu dự kiến:
- Gọi stair_works bằng Stair auto (22 bậc, rộng1000, bậc250), H3300, dày120; assign_status với cao độ tầng trên: CAU_THANG C; inputs có thang B, cao tầng B, dày C; cốp pha C; lượng trước/sau không đổi.
- Parametrize nguồn auto/manual/structural ở WorkItem để kiểm `_src` không bị mất A/B/C; không giả định stair_works hiện hỗ trợ structural (nó chuẩn hóa non-auto thành manual).
- Thiếu dày: stair_works sinh quantity None, status D, missing dày bản thang; không biến thiếu thành0.
- Có lượng nhưng height_sources trống: trạng thái D, inputs nêu thiếu nguồn cao tầng.

Giới hạn cố ý: nguồn structural của giằng hiện bị mất từ `linear_works`, không thể sửa đúng chỉ status.py. Việc đó cần lượt riêng ở secondary.py; không đưa vào Q01 thang độc lập. `stair_works` hiện chưa nhận dày từ từng Stair, nên không được gắn A cho dày chỉ vì hình học có source structural.

Lệnh trọng tâm sau cấp lượt: `.venv/Scripts/python.exe -m pytest tests/test_rough_status.py tests/test_rough_stairs_detect.py tests/test_rough_secondary.py -q -p no:cacheprovider` (môi trường không DB). Các xfail giằng/thép không liên quan không được tự mở hoặc xóa.
