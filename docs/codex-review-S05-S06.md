# Prompt cho Codex: review lại sprint S05 + S06

Dán nguyên phần dưới vào Codex, chạy ở thư mục `optimat-ai/`.

---

Bạn là reviewer cho dự án OptiMat AI (Python, bóc khối lượng phần thô nhà ở từ bản vẽ DXF). Trả lời bằng tiếng Việt.
Đọc `CLAUDE.md` (quy tắc bắt buộc, đặc biệt Quy ước B7: thiếu số thì để trống + cảnh báo, không điền mặc định) và
`docs/boc-mong-cot-dam-san.md` (đặc tả đã làm) trước khi review. KHÔNG sửa mã; chỉ báo cáo.

## Phạm vi thay đổi cần review

- `src/optimat/rough/foundations.py` (mới): `foundation_works`, `tiers_of`, `tier_volume_m3`, `tier_formwork_m2`, `pit`,
  `pit_volume_m3`, `_union_area`, `pit_overlap_m3`, `_neg`, `footing_rects`.
- `src/optimat/rough/models.py`: `WORKS` thêm `DAO_DAT`, `DAP_DAT`; `FootingTier`; trường mới của `FoundationItem`
  (kind, tiers, bottom_level_mm, neck_b_mm, neck_h_mm, positions, plan, source); `ProjectParams.natural_ground_level_mm`,
  `excavation_margin_mm`, `excavation_slope`. (Các phần RoofItem, roofs, basis, evidence, GIANG_TUONG… là của sprint khác — ngoài phạm vi.)
- `src/optimat/rough/beams.py`: `Beam.cut_mm`, `Beam.framed`, `length_mm` trừ `cut_mm`; `beam_joints`, `_rect`, `is_tie_beam`;
  `beam_works` gom theo mã cấu kiện, giằng móng không trừ sàn/không ván đáy, trừ cốp pha chỗ dầm phụ gác vào.
- `src/optimat/rough/columns.py`: `Column.role`; `column_works(..., beams)` trừ cốp pha đầu dầm, bỏ cột kiến trúc, chặn khi dày sàn ≥ chiều cao tầng.
- `src/optimat/rough/takeoff.py`: trong `compute_rough` gọi `beam_joints` (mặt bằng kiến trúc: với cột; bản vẽ kết cấu: với khung móng),
  `_section_checks`, `_slab_form_deduction`, bỏ dòng trừ khi không có cốp pha sàn; `RoughRequest.column_sections`.
- `src/optimat/rough/structural.py`: ký hiệu móng trùng chỗ, `_footing_center`, positions/plan/source, `column_sections`.
- `data/rules/ky_hieu_cau_kien.csv` dòng K02 (`(dk|gm)…`, tên "đà kiềng, giằng móng" — `is_tie_beam` dựa vào tên này).
- Test: `tests/test_rough_foundations.py`, `tests/test_rough_joints.py`, `tests/test_rough_steel.py` (đổi import).

## Tiêu chí nghiệm thu phải kiểm

S05:
1. Móng không có chi tiết bị báo thiếu, không mặc định kích thước (MONG quantity None + missing).
2. Khối lượng từng móng truy ngược được file/chi tiết và kích thước (formula + source).
3. Có test cho: móng trùng, giằng giao đài/móng, nền đào không đủ cao độ.
4. Bê tông lót tách khỏi bê tông kết cấu; cốp pha chỉ diện tiếp xúc cần lắp (không lấy toàn bộ bề mặt).
5. Đắp lại có điều kiện: thiếu số thì trống, âm thì chặn + cảnh báo; hố chồng lấn không đếm hai lần.

S06:
1. Tổng thể tích không tăng do đếm trùng ở giao cột–dầm–sàn và dầm–dầm.
2. Mã cấu kiện có chi tiết nguồn; kích thước không đủ thì bị chặn (quantity None).
3. Báo xung đột cao độ, không nhận diện được tiết diện, ranh giới ô sàn.
4. Sai số công bố theo cột/dầm/sàn riêng, không gộp che lỗi (xem bảng trong docs — kiểm tra bảng có trung thực không).

## Việc cần làm

1. Chạy: `$env:PYTHONIOENCODING="utf8"; .venv\Scripts\python.exe -m pytest -q tests/test_rough_foundations.py tests/test_rough_joints.py tests/test_rough_structural.py tests/test_rough_beams.py tests/test_rough_columns.py tests/test_rough_takeoff.py tests/test_rough_api.py tests/test_rough_steel.py`
   Toàn bộ `pytest` hiện có 15 lỗi có sẵn ở agent/tối ưu/giá (thiếu giá MẪU) — không thuộc sprint này; báo nếu có lỗi mới khác.
2. Tự tính tay lại ít nhất: hố đào chóp cụt (prismoid), móng có lớp vát, khung cột–dầm–sàn 2 cột 1 dầm, hai dầm giao chữ thập
   và chữ T. So với số trong test; báo nếu test đang khóa một số sai.
3. Soi các điểm nghi ngờ sau (xác nhận hoặc bác bỏ, kèm dòng mã):
   - `beam_joints`: dầm vẽ tim–tim cột nhưng cột lệch trục; dầm xiên (không ngang/đứng) — `_rect` chỉ đúng cho dầm ngang/đứng;
     dầm phụ cắt qua dầm chính khi `width` dầm chính None; cặp dầm cùng trục chỉ chạm đầu (lap = 0?).
   - `_section_checks` so cột kiến trúc với `column_sections` của mọi tầng; dòng `_slab_form_deduction` gán vào mặt bằng của dầm
     chứ không phải sàn tầng trên (shortcut đã ghi) — có làm sai tổng cốp pha sàn khi mặt bằng mái không có trong `plans` không?
   - `foundation_works`: `pit` lấy lớp dưới cùng làm đáy hố — đúng khi lót rộng hơn móng không? Hố chồng lấn coi cạnh dài
     theo trục x; `positions` từ `_footing_center` có thể là khung xoay 90°.
   - `_footing_center` có thể bắt nhầm khung khác cùng kích thước (khung tên, ô bảng) trong `LABEL_REACH_MM`?
   - `is_tie_beam` nhập muộn `structural` để tránh vòng import; ký hiệu GM có đụng mẫu khác trong CSV không.
   - Dòng số âm (`_neg`) trong `works`: `materials_for_works`, `steel_works`, tổng `totals`, giao diện `review_app.html` có xử lý đúng không?
   - Trang `review_app.html` gửi lại `beams` có `cut_mm`/`framed` cũ: `beam_joints` có thật sự tính lại từ đầu không?
4. Kiểm tra quy tắc dự án: không viết cứng quy tắc nhận dạng ngoài CSV, chú thích tiếng Việt, không đổi lược đồ DB.

## Định dạng báo cáo

Bảng các phát hiện, xếp nặng → nhẹ: mức (chặn / nên sửa / gợi ý), file:dòng, mô tả, kịch bản sai cụ thể (đầu vào → số sai),
cách sửa đề xuất. Cuối báo cáo: tiêu chí nghiệm thu nào ĐẠT / CHƯA ĐẠT, có bằng chứng.
