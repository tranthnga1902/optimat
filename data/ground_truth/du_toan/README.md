# Dự toán thật làm đáp án phần thô

`46_nha_tan_binh.csv`: sheet "Công trình" của `Nha Tan Binh.xls` (bộ "46-Nha Dan 5 Tang (KT+KC+DN+BPTC+DuToan)",
kenhxaydung.vn, lập 2016 theo định mức 1776, đơn giá HCM). Nhà 4 × 22,6–25,6 m: trệt, lầu 1–4, sân thượng, mái.

- `data_kind`: ACTUAL (dự toán của công trình thật, không phải đo tay của dự án).
- `split`: build. Bộ bản vẽ này đã dùng để sửa tách mặt bằng (28/10/2026), không dùng làm số báo cáo độ chính xác.
- `khoi_luong` đã đổi về đơn vị của hệ thống (100 m² → m², 100 m → m); `khoi_luong_goc`, `don_vi_goc` giữ nguyên bản.
- `ma_cong_tac`, `cau_kien`: gắn theo tên công tác (mã định mức không đủ: AF.11212 lót và AF.11213 móng chung nhóm);
  trống = ngoài phạm vi phần thô (hoàn thiện, cửa, điện nước) hoặc không phải bộ phận nhà (dòng "BNN" bể nước ngầm).
- `dien_giai`: các dòng diễn giải khối lượng theo trục, tầng, nối bằng " | ".

So sánh: `python scripts/compare_estimate.py data/ground_truth/du_toan/46_nha_tan_binh.csv <Kien_truc.dxf> --structural <Ket cau.dwg>`.

`46_thong_so.json`: thông số công trình cho bộ 46, lấy từ diễn giải của chính dự toán (không phải số mặc định):
sàn dày 100 (`× 0,1`), dầm 200 × 350 (bê tông `0,2 × 0,25` dưới sàn + sàn 100), móng 1200 × 1200 × 700, lót 100
(số khối M1–M4 = 14 đọc từ mặt bằng móng, khớp `× 14`), trát 15, lót nền 100 (`22,6 × 4 × 0,1`), mác M200 / M150 / vữa M75;
hàm lượng thép kg/m³ = hệ số tấn/m³ của dự toán (móng 0,11; cột 0,05 + 0,22; dầm 0,05 + 0,24; sàn 0,11; thang 0,21;
lanh tô 0,28), nên so thép chỉ kiểm khối lượng bê tông, không kiểm thép. Không có: lanh tô (cần kích thước cửa), cầu thang
(số bậc), đào đắp (cốt tự nhiên).

Lỗ mở (thêm 28/10/2026): bản vẽ không ghi cỡ cửa (không bảng thống kê cửa, block không thuộc tính). Chỉ lấy số dự toán
ghi rõ: cửa đi `0,8*2` → `door_height_mm` 2000. Không đặt chiều cao cửa sổ và lanh tô: dự toán không định nghĩa một giá trị
chung (ô cửa cao 2,5–3,3 m; lanh tô hai loại 200 gối 300 và 100 gối 350), nên các lỗ mở đó chưa trừ và lanh tô để trống (B7).
Khóa `openings` của file JSON là kích thước cửa của dự án (bảng `projects`), `scripts/compare_estimate.py` tách riêng khỏi
ProjectParams. Mọi số trong thư mục này là dữ liệu tham khảo để đối chiếu, không đưa vào mã hay làm mặc định.
