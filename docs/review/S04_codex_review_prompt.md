# Prompt cho Codex: review Sprint S04 (Takeoff tường xây và lỗ mở)

Dán nguyên phần dưới vào Codex, mở ở thư mục `optimat-ai/`.

---

Bạn là reviewer cho dự án OptiMat AI (Python 3.13, FastAPI, ezdxf). Đọc `CLAUDE.md` trước: nó có quy tắc bắt buộc
(không đoán khi thiếu số liệu — Quy ước B7; quy tắc nằm trong CSV, không viết cứng; chú thích và thông báo bằng tiếng Việt).
Trả lời bằng tiếng Việt. **Chỉ review, không sửa mã**, trừ khi tôi đồng ý sau đó.

## Phạm vi sprint S04

Mục tiêu: bóc diện tích/thể tích tường theo tầng và loại tường.

- S04-01 Nhận hai nét song song, layer tường, bề dày 110/150/220/330 (`config.WALL_THICKNESS_CLASSES`).
- S04-02 Chiều dài theo trục tim hoặc thông thủy theo quy tắc chọn; xử lý góc nối và đoạn trùng.
- S04-03 Chiều cao tầng từ cao độ đã duyệt; thiếu thì không suy đoán.
- S04-04 Ghép cửa với tường; trừ lỗ mở **đúng một lần**; giao cột/vách bê tông.
- S04-05 Đổi m²/m³ khối xây ra gạch, vữa theo định mức có nguồn; hao hụt cộng ở bước mua (procurement).
- S04-06 Lưu WallSegment, WallGroup, rule trace, các trường hợp unmatched.

Tiêu chí nghiệm thu: chạy được trên 5+ mặt bằng quy ước có đáp án; chênh lệch báo theo từng nhóm tường; sai số mục tiêu
chốt trước khi test; mọi cửa trừ một lần và xuất được nguồn. Giới hạn: vữa theo cấp phối/định mức, không giả định mọi tường cùng loại.

## Thay đổi của sprint này (đọc kỹ)

- `src/optimat/drawing/walls.py`: `LENGTH_RULES`, `net_lengths()` (thông thủy: mỗi đầu tường nằm trong thân một tường
  không song song thì bớt đoạn tới mặt tường đó; mỗi đầu bớt theo một tường).
- `src/optimat/drawing/takeoff.py` `compute_takeoff()`: tham số `length_rule`; bỏ block cửa trùng (cùng tên, cách ≤ 50 mm);
  block nằm ở khe cửa đã nhận bằng cung/nét kính thì không trừ lần hai, nối nguồn vào `evidence`; chặn lỗ mở > diện tích tường;
  `net_length_mm` từng tường; nhóm tường dùng chiều dài theo quy tắc. `takeoff_plans`, `takeoff_from_file` truyền tham số.
- `src/optimat/drawing/review.py` `compute_review()` (công thức chốt duy nhất): `ReviewPlan.length_rule`, chặn lỗ mở > diện tích tường.
- `src/optimat/schemas.py`: `WallSegment.net_length_mm`, `TakeoffResult.length_rule`.
- `src/optimat/api/main.py`: Form `length_rule` ở `/api/takeoff`, `/api/takeoff/plans`, lỗi quy tắc trả 422.
- `tests/test_s04_walls.py`: 7 mặt bằng tự dựng + 3 bài cho `compute_review`.

Mã đã có từ trước, liên quan (đọc để đối chiếu, không phải thay đổi mới): `walls.py` (`detect_walls`, `dedupe_walls`,
`extend_corners`, `bridge_openings`), `plans.py` (`floor_heights`), `catalog/pricing.py` (`bill_of_materials`, hao hụt
`waste_pct`), `rough/walls.py` (`wall_works`: trừ cột, dầm, lanh tô), `material_rules.py` (rule trace, `unmatched`).

## Cần kiểm tra

1. **Đúng công thức** `net_lengths`: góc L (đã kéo tới giao trục tim), chữ T (tường ngăn dừng ở mặt tường bao), chữ thập,
   tường xiên, tường ngắn hơn bề dày tường giao, hai tường giao ở cùng một đầu. Có trường hợp bớt quá tay, bớt hai lần,
   hoặc làm chiều dài âm không?
2. **Cửa trừ đúng một lần**: tìm mọi đường một lỗ mở có thể bị trừ hai lần hoặc bị bỏ sót, gồm
   khe cửa + block + cung; hai block khác tên cùng chỗ; block trùng nhưng lệch > 50 mm; cửa sát góc gắn nhầm tường vuông góc;
   cửa ở khe chưa có chiều cao (gap `height_mm=None`) cùng block có thuộc tính WIDTH/HEIGHT; gộp tường sau khi nối khe
   (`dedupe_walls` lần hai) làm `wall_id` của lỗ mở trỏ sai. So `openings_count` với số lỗ thực trừ.
   Kiểm cả vòng gán lại `item.evidence` trong `compute_takeoff` (so `(x, y)` bằng dấu `==`).
3. **Nhất quán giữa đo bóc tự động và công thức chốt**: cùng một mặt bằng, `compute_takeoff` và `compute_review`
   (đầu vào từ `review_input_from_takeoff`) có cho cùng `length_m`, `opening_area_m2`, `net_area_m2` với cả hai quy tắc không?
   Lưu ý `compute_review` dùng dày danh nghĩa `float(cls)` còn `compute_takeoff` dùng `thickness_mm` đo được.
   Trang `review_app.html` tính tạm theo trục tim và chưa gửi `length_rule`: có chỗ nào làm người dùng thấy số khác số chốt?
4. **Không đoán (B7)**: thiếu chiều cao tầng thì `groups` rỗng; thiếu kích thước cửa thì không trừ + cảnh báo. Có nhánh nào
   điền số mặc định không?
5. **S04-05**: bảng vật liệu (`bill_of_materials`) dùng định mức của phương án tường từng nhóm, không gộp mọi tường thành
   một loại; hao hụt chỉ cộng khi có `waste_pct`, không cộng ở bước đo bóc.
6. **S04-06 truy vết**: từ kết quả có lần ra được với mỗi tường: quy tắc vật liệu đã khớp, nguồn chiều cao, cửa nào trừ vào
   đâu, tín hiệu nào `unmatched` không? Kết quả chốt lưu vào `takeoff_results` có giữ `length_rule` không?
7. **Test**: bài trong `tests/test_s04_walls.py` có thật sự bắt lỗi không (thử nghĩ nếu bỏ đoạn khử trùng thì test nào hỏng)?
   Đáp án tính tay có đúng không? Còn thiếu trường hợp nào trong danh sách bàn giao: tường thẳng, giao góc, cửa sát góc,
   cửa trùng, không có cao độ?
8. Tương thích ngược: mặc định `length_rule="tim"` phải giữ nguyên mọi số cũ (`tests/test_takeoff.py`, `test_review.py`,
   `test_rough_*`). Hiệu năng: `net_lengths` là O(n²) theo số tường — có vấn đề với mặt bằng thật vài trăm tường không?

## Vòng 2: đã sửa theo review lần 1 — kiểm lại từng điểm

| Phát hiện lần 1 | Cách đã sửa | Chỗ cần soi |
|---|---|---|
| Block khác tên / lệch > 50 mm trừ hai lần | Ghép theo tường chủ + khoảng cửa dọc trục chồng nhau > 50 mm, nguồn nối vào `evidence` | `takeoff.py` vòng `for block in ...`; giả định điểm chèn block = tâm cửa (ghi `shortcut:`) có làm lỡ ghép không |
| Block gần khe ghép nhầm sang tường vuông góc | Cùng cơ chế trên (chỉ ghép khi cùng tường chủ) | Đồng thời sửa lỗi cũ: đánh số lại tường sau khi nối khe làm tráo `wall_id` của cửa; nay đổi theo bảng `renamed` |
| Nhóm gộp hai phương án vật liệu | Khóa nhóm = (lớp, vai trò, phương án hoặc mã vật liệu) ở `compute_takeoff`, `compute_review`, `review_app.html` `compute()` | Tối ưu (`optimize/problem.py`) nay nhận nhiều nhóm cùng `wall_type`: có chỗ nào giả định mỗi lớp một nhóm không? `evaluate.py` cộng lại theo lớp |
| Giao xiên trừ thiếu | `(t/2 - off) / sin(góc)` | `walls.net_lengths`; góc gần song song (ngưỡng cos > 0,9 bị bỏ qua) |
| Trang không theo `length_rule` | Ô chọn "Chiều dài", `netLengths` JS (chép công thức), `payload()` gửi `length_rule` | JS khớp Python (đã so trên 4 tường); hoàn tác (`snapshot`) có giữ quy tắc |
| `openings_count` đếm cả lỗ chưa trừ | Chỉ đếm lỗ có `wall_id` | Các nơi đọc `openings_count` |
| Bản chốt thiếu căn cứ | `ReviewPlan.height_source`, `unmatched`; `ReviewWall.rule`, `msrc`; `ReviewOpening.ev` | Lưu trong `takeoff_results.result.input`; trang gửi đủ chưa |

Ngoài ra: `data/ground_truth/index.csv` có thêm cột kích thước cửa của dự án; độ lệch 3,46% ở nhóm 220 trước đây là do
chưa trừ cửa (B7: không có kích thước thì không trừ), nay 0%. Vẫn chỉ có 1 bản vẽ build, chưa có bản test.
Test mới trong `tests/test_s04_walls.py`: khác tên/lệch, cửa góc trên tường vuông góc, block xa tường, giao xiên 45°,
tách nhóm theo vật liệu, số tự động = số chốt với cả hai quy tắc.

## Cách chạy

```powershell
$env:PYTHONIOENCODING = "utf8"
.venv\Scripts\python -m pytest tests/test_s04_walls.py tests/test_takeoff.py tests/test_review.py tests/test_rough_walls.py -q
.venv\Scripts\python -m pytest -q        # toàn bộ; trước sprint này đã có ~15 lỗi ở giá/xe/agent/quản trị do thiếu giá MẪU
```

Bản vẽ thật (nếu có trên máy) ở `data/drawings/build/`; `python scripts/evaluate_takeoff.py` so với `data/ground_truth/`.

## Định dạng trả lời

Bảng xếp theo mức nghiêm trọng (Nghiêm trọng / Trung bình / Nhỏ), mỗi dòng: file:dòng, lỗi là gì, đầu vào cụ thể làm sai
→ kết quả sai, cách sửa gợi ý (một câu). Sau đó: tiêu chí nghiệm thu nào **đạt / chưa đạt / chưa kiểm được** và vì sao.
Không liệt kê góp ý về phong cách nếu không ảnh hưởng đúng sai.
