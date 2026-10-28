# Prompt review cho Codex: S07–S08 (cốt thép, BOQ MVP, cấu kiện phụ)

Dán nguyên phần dưới vào Codex, chạy ở thư mục `optimat-ai/`.

---

Bạn là reviewer kỹ thuật cho repo Python `optimat-ai` (đồ án: bóc khối lượng phần thô nhà ở từ bản vẽ DXF). Đọc
`CLAUDE.md` trước để biết quy tắc bắt buộc: thêm quy tắc vào CSV không viết cứng; thiếu số thì để trống kèm cảnh báo, không
điền mặc định (Quy ước B7); chú thích và thông báo bằng tiếng Việt; mỗi thay đổi giữ `pytest` đạt.

**Việc cần review**: sprint S07–S08 vừa làm xong. Đặc tả và tóm tắt nằm ở `docs/S07_S08_thep_BOQ_cau_kien_phu.md`.
Repo không có commit cho phần này (nhiều phiên sửa song song) nên hãy đọc trực tiếp các file sau:

- Mới: `src/optimat/rough/rebar.py`, `src/optimat/rough/secondary.py`, `src/optimat/rough/boq.py`, `scripts/export_boq.py`,
  `tests/test_rough_rebar.py`, `tests/test_rough_secondary.py`, `data/rules/bang_thep.csv`, `data/rules/thep_kg_m.csv`,
  `data/rules/loai_mai.csv`, `data/rules/ho_tro_cau_kien.csv`
- Sửa: `src/optimat/rough/models.py` (WORKS thêm GIANG_TUONG, SE_NO, MAI; ROLE_WORK; RoofItem; ProjectParams.roofs;
  WorkItem.basis, WorkItem.evidence), `src/optimat/rough/steel.py` (schedule_works, steel_works(..., rebar)),
  `src/optimat/rough/materials.py` (bỏ qua basis="not_supported"), `src/optimat/rough/stairs.py` (kind, dầm thang),
  `src/optimat/rough/takeoff.py` (PlanInput.members, RoughRequest.rebar/members, móc lintel_under_beam, deduct_ties,
  linear_works, roof_works, drop_slab_under_roof, steel_works với req.rebar, rough_from_drawing đọc nhiều file kết cấu),
  `src/optimat/api/main.py` (POST `/api/takeoff/rough/excel`), `data/rules/ky_hieu_cau_kien.csv` (K07–K11)

**Đối chiếu với tiêu chí nghiệm thu** (ghi rõ đạt / không đạt / đạt một phần, kèm file:dòng làm bằng chứng):

S07
1. Không nhầm thép từ bảng thống kê với thép tự suy: mọi công tác COT_THEP có `basis` đúng (`bang_thong_ke` / `ham_luong` /
   `not_supported` / trống); khi một cấu kiện có bảng thép thì hàm lượng của cấu kiện đó không được cộng thêm.
2. Không có bảng thép chuẩn thì thép để trống và yêu cầu review (kiểm cả trường hợp người dùng nhập hàm lượng: có cảnh báo
   "cần review" không? Có nên coi đó là vi phạm tiêu chí không? Nêu ý kiến).
3. kg = số thanh × chiều dài cắt × kg/m; bảng kg/m có nguồn; kiểm sai đơn vị và đếm trùng hoạt động đúng.
4. Neo, nối, uốn, móc không tự cộng.
5. BOQ Excel có tổng + theo tầng + theo cấu kiện + nhật ký cảnh báo; mỗi dòng có formula, evidence, missing_reason.

S08
6. Mỗi nhóm "supported" trong `ho_tro_cau_kien.csv` có ít nhất một test chuẩn và một case âm tính thật sự kiểm đúng điều đó
   (đọc nội dung test, không chỉ tên).
7. Loại cấu kiện thiếu quy ước ghi Not supported thay vì trả số (mái khung, thang cốn/xoắn, cấu kiện lạ trong bảng thép).
8. Không cộng trùng lanh tô và dầm; giằng và tường; mái và sàn.

**Tìm lỗi cụ thể**, ưu tiên:
- `rebar.py`: gom hàng theo y (`_rows`) khi chữ cao 0 hoặc bảng nghiêng; gán ô vào cột theo x gần nhất khi TEXT căn trái
  còn tiêu đề căn giữa; dò dòng tiêu đề lấy mọi chữ phía dưới tiêu đề trên toàn bản vẽ (có thể bắt nhầm bảng khác cùng hàng y);
  `_num` với "1.200,5", "2x16", "Ø16a200"; điều kiện dừng bảng; khóa dòng trùng chỉ áp dụng khi có số hiệu.
- `secondary.py`: `lintel_under_beam` chép công thức lanh tô của `walls.wall_works` — kiểm có khớp đúng công thức hiện tại
  của `walls.py` (thể tích, cốp pha, dày tường theo phương án) và trường hợp `beam_depth_mm` trống; `_xay_of` tìm công tác XAY
  theo nhãn chuỗi — có thể không khớp khi nhãn đổi; `deduct_ties` có trừ hai lần khi giằng chồng hai tường thẳng hàng không;
  `read_secondary` dùng `structural_scale` thay vì tỷ lệ tự suy từng hình như dầm.
- `takeoff.py`: thứ tự gọi (roof/drop_slab trước steel để hàm lượng sàn không tính cho sàn đã bỏ); mặt bằng không có chiều
  cao bị `continue` trước các luật mới; cao lanh tô tự điền từ LT… chỉ khi duy nhất một giá trị.
- `steel.py`: `steel_schedule_t` thắng bảng bản vẽ; nhóm theo (mã, ký hiệu) — "C1" và "CỘT C1" có thành hai nhóm không.
- `boq.py`: sắp xếp khi `plan` trống, công tác có mã không nằm trong WORKS.
- Thông báo người dùng có đúng tiếng Việt, không viết cứng quy tắc nhận dạng trong mã (TITLE_RE, ngưỡng LENGTH_MM, KG_TOL có
  nên ra CSV không).

**Chạy kiểm thử** (Windows, PowerShell):
```
$env:PYTHONIOENCODING = "utf8"
.venv\Scripts\python -m pytest -q tests/test_rough_rebar.py tests/test_rough_secondary.py tests/test_rough_steel.py tests/test_rough_stairs.py tests/test_rough_takeoff.py tests/test_rough_structural.py tests/test_rough_api.py
.venv\Scripts\python -m pytest -q
```
Toàn bộ trước khi bàn giao: 255 đạt, 15 lỗi có sẵn ở `test_agent_api`, `test_agent_openai`, `test_app_data`, `test_db`,
`test_material_rules`, `test_optimize`, `test_review` (dữ liệu đại lý/xe mẫu, không thuộc S07–S08). Báo nếu con số khác.
Nếu có bản vẽ thật: `.venv\Scripts\python scripts/export_boq.py data/drawings/build/nha_dan.dxf --structural data/drawings/build/ket_cau.dxf --height 3300 --scale 0.5 --out boq.xlsx`
rồi mở file kiểm các sheet.

**Viết thêm test âm tính** nếu thấy thiếu (đặt trong hai file test mới), nhưng KHÔNG sửa mã nguồn: chỉ báo cáo.

**Đầu ra**: một bảng tiêu chí 1–8 (đạt / một phần / không đạt + bằng chứng), rồi danh sách lỗi xếp theo mức độ
(nghiêm trọng / trung bình / nhỏ), mỗi lỗi: file:dòng, kịch bản đầu vào gây sai, kết quả sai, đề xuất sửa ngắn. Cuối cùng
liệt kê điểm cần giảng viên/người dùng quyết định (ví dụ: hàm lượng thép có được giữ làm phương án dự phòng không).
