# KD08 – Tách nguyên nhân chênh XÂY, DẦM, CỐP PHA (bộ 46, build)

Ngày 05/11/2026. Đối chứng là dự toán của người lập (chưa xác nhận, D02) — **không phải đáp án nghiệm thu**.
Chạy lại: `python scripts/kd08_tach_chenh_xay.py --case 46_nha_tan_binh` → `reports/kd08/46_nha_tan_binh_xay.csv`.

## 1. XÂY: −16,6 % (C01) tách thành 3 phần

| Phần | m³ | Giải thích |
|---|---|---|
| Dự toán | 195,14 | dòng con PT32 của 46-C27, 46-C28 (bỏ lan can PT26) |
| Hệ thống, đủ hình (L × cao xây − lỗ) × dày | 164,73 | tính trên `masonry_geometry`, kể cả nhóm đang trống số vì lỗ mở thiếu kích thước |
| Quy ước chiều cao (dự toán lấy cao trọn tầng 3,4 / 3,0 m) | +7,46 | hệ thống trừ cao dầm: **đúng định mức**, không sửa |
| Quy ước chiều dày (dự toán 0,1 / 0,2 m; hệ thống danh nghĩa 0,11 / 0,22 m) | −15,62 | quy ước của danh mục phương án tường; ghi chú, không sửa |
| **Còn lại do hình học** | **+38,57** | chiều dài tường nhận được, lỗ mở |

Theo tầng (sau khi đưa về quy ước dự toán): T1 +15,5; T2 +8,8; T3 +7,5; T4 +7,1; T5 +9,6 m³ (**hệ thống thiếu tường**);
sân thượng **−14,2 m³ (hệ thống thừa)**.

## 2. Nguyên nhân hình học tìm được

1. **Mặt bằng trùng tầng (QU-05)**: tệp KT có hai hình cho mỗi tầng ("… LẦU 2" và "… LẦU 2 (2)"). Quy tắc hiện hành
   `rough/takeoff.duplicate_plans` giữ bản nhận nhiều tường nhất. Ở sân thượng, bản "(2)" nhận 81,6 m (có 10 m tường 330)
   so với 52,0 m của bản kia → nguồn chính của phần thừa 14 m³. Ở lầu 2–4 hai bản lệch ít (61,6 / 56,7 m…).
   Quy tắc "giữ bản nhiều nhất" có lý do (Bietthu7: hai bản lệch 0 m và 29 m) nên **không đổi quy tắc toàn cục theo một hồ sơ**;
   người dùng chọn bản đúng bằng phạm vi mặt bằng (`plan_scope_confirmed`) đã có trên trang kiểm tra.
2. **Thiếu chiều dài tường mỗi tầng** (ước theo công thức dự toán): lầu 1 tường 100 ≈ 63,6 m (hệ thống 53,5 m), tường 200
   ≈ 31 m (18,5 m); lầu 2–4 tường 200 ≈ 26 m/tầng (16–17 m). Thiếu nhiều nhất ở tường 200 dọc trục A-B (tường biên dài
   22,6 m). Cần mở `/do-boc` từng tầng để xem đoạn nào không thành cặp nét (vẽ một nét, layer chung, bị cắt bởi cột) trước
   khi đổi ngưỡng `nguong_nhan_dien.csv`; chưa sửa vì không có đáp án hình học đã xác nhận.
3. **Hồi quy hiện tại (không thuộc KD08)**: sau bản sửa F11/F12 ngày 04/11, nhóm tường có lỗ mở thiếu kích thước bị để trống
   cả nhóm (hệ thống chỉ còn ra số 37 m³ thay vì ~159 m³). 6 bài pytest hỏng cùng nguyên nhân
   (`test_final_wall_groups_ui`, `test_rough_api::test_rough_auto_then_confirm`, `test_s04_walls::…`, …). Phiên đang làm
   F11/F12 cần xử lý; KD08 đo trên `masonry_geometry` để không phụ thuộc lỗi này.

## 3. DẦM −19 %, CỐP PHA DẦM −31,5 %, CỐP PHA SÀN −28,1 % (C01)

Theo D02/C01 §6: dòng 46-C09 nhân "Lầu 1–6" (×6) trong khi công trình trệt + lầu 1–4 + sân thượng; 46-C15 dùng 4×11 khác
4×10 của dòng bê tông dầm; cốp pha sàn hệ thống trừ đáy dầm/cột (O02) còn dự toán không trừ. Phần lớn chênh là **do dự toán và
quy ước**, chưa thấy lỗi hình học có bằng chứng. Việc tiếp: người kiểm D02 xác nhận số tầng của 46-C09 rồi đo lại.

## 4. Kết luận

- Đã có công cụ tách chênh (quy ước / hình học) theo tầng, dùng lại cho mọi hồ sơ build có D02.
- Hình học: hai nguyên nhân có số đo (chọn bản trùng tầng ở sân thượng; thiếu tường 200 dọc trục biên). **Chưa sửa mã nhận
  diện** vì chưa có đáp án hình học xác nhận; sửa theo dự toán chưa kiểm sẽ là chỉnh theo số chưa đúng.
