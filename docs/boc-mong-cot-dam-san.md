# Bóc móng, đất, cột, dầm, sàn (S05, S06 — 21/10/2026)

Mã: `src/optimat/rough/foundations.py` (móng, lót, đào đắp), `beams.py` (`beam_joints`, giằng), `columns.py`,
`takeoff.py` (`_section_checks`, `_slab_form_deduction`), `structural.py` (vị trí móng, ký hiệu trùng, tiết diện cột ghi chữ).
Test: `tests/test_rough_foundations.py`, `tests/test_rough_joints.py`.

Nguyên tắc chung: thiếu số thì để trống kèm `missing`/cảnh báo, không lấy kích thước mặc định (Quy ước B7). Mỗi dòng công tác
có `formula` đã thay số; móng đọc từ bản vẽ có `source` (mặt bằng chứa ký hiệu, hình chi tiết, số mặt cắt) nối vào công thức.

## Catalog biểu thức — móng và đất (S05)

| Đại lượng | Biểu thức | Ghi chú |
|---|---|---|
| Móng đơn / móng băng, một khối | Σ thể tích các lớp `tiers` (dưới lên); không có lớp: dài × rộng × cao | móng băng: dài = chiều dài băng đã trừ phần giao |
| Lớp hộp | L × B × h | |
| Lớp vát (`top_length_mm`, `top_width_mm`) | h/6 × (A_đáy + 4·A_giữa + A_đỉnh) | đúng cho chóp cụt chữ nhật |
| Bê tông lót | n × L × B lớp dưới cùng × dày lót | dòng `BE_TONG_LOT` riêng, mác `lean_concrete_grade` |
| Cốp pha móng | n × Σ 2(L + B) × h các lớp **thẳng đứng** | mặt trên, mặt đáy, mặt vát không tính |
| Sâu đào H | cốt tự nhiên − (cao độ đáy móng − dày lót) | H ≤ 0: không đào, báo "không đủ cao độ" |
| Hố đào | đáy (L + 2c) × (B + 2c), đỉnh rộng thêm 2mH; V = H/6 (A_đáy + 4A_giữa + A_đỉnh) | c, m, cốt tự nhiên người dùng xác nhận theo hồ sơ |
| Hố chồng lấn | − ∫ (Σ diện tích hố − diện tích hợp) dz | chỉ khi có vị trí từng khối; 200 lát theo độ sâu |
| Đắp lại | V hố − V lót − V móng − V cổ móng chôn dưới cốt tự nhiên | âm: để trống + cảnh báo; thiếu tiết diện cổ móng: để trống |
| Giằng móng / đà kiềng (ĐK…, GM…) | dài (trừ đoạn nằm trong khung móng) × b × h | không trừ sàn; cốp pha 2 thành, không ván đáy |

Chưa nhập cốt tự nhiên, c, m thì không sinh dòng đào đắp (một cảnh báo). Móng cùng tên nhập hai lần: bỏ dòng sau.
Ký hiệu móng trùng chỗ trên mặt bằng (< 100 mm): đếm một lần.

## Quy tắc nút giao — cột, dầm, sàn (S06)

| Giao | Ưu tiên | Cách tính |
|---|---|---|
| Cột – sàn | sàn | cột cao H − dày sàn |
| Dầm – sàn | sàn | dầm tính phần (cao − dày sàn) |
| Cột – dầm | cột | dầm cắt ở mặt cột (`cut_mm` = đoạn trong cột) |
| Dầm – dầm | dầm chính (cao hơn → rộng hơn → dài hơn) | dầm phụ cắt ở mặt dầm chính |
| Dầm trùng trục | dầm trước | bỏ đoạn chồng của dầm sau, báo đếm trùng |
| Cốp pha cột | | 2(b + h) × hc − Σ b_dầm × (d − dày sàn) mỗi đầu dầm gác vào |
| Cốp pha dầm | | (2 × (d − dày sàn) + b) × L − Σ b_phụ × (d_phụ − dày sàn) chỗ dầm phụ gác vào |
| Cốp pha đáy sàn | | diện tích sàn − ô trống; dòng trừ riêng: − Σ b × L mặt dầm − Σ đỉnh cột |
| Lỗ mở sàn | | `void_area_m2` của mặt bằng trừ khỏi bê tông và cốp pha sàn |

Báo lỗi (S06-06): dầm cao ≥ chiều cao tầng, dày sàn ≥ chiều cao tầng (chặn cột), dầm thiếu tiết diện (để trống),
đường bao sàn hở (có sẵn từ S3b), cột trên mặt bằng kiến trúc không khớp tiết diện cột ghi chữ nào trên bản vẽ kết cấu
(chỉ báo; người dùng đặt `role = "kien_truc"` thì cột đó không tính bê tông, cốp pha). Dầm đọc từ bản vẽ hoặc nhập tay
gom theo mã cấu kiện (`D1: 3 dầm 200×350`), BOQ theo tầng (`plan`) và mã.

## Bảng sai số so với đo bóc tay

Chỉ có đáp án đo tay cho móng của `data/drawings/build/ket_cau.dxf` (đọc tay chi tiết, ngày 21/10/2026; số này đã khóa
trong `tests/test_rough_structural.py::test_ket_cau_build_drawing`). Chưa có đáp án đo tay cho cột, dầm, sàn: không
công bố sai số gộp thay thế.

| Cấu kiện | Đại lượng | Đo tay | Hệ thống | Sai số |
|---|---|---|---|---|
| Móng M1 | số khối; L × B × h; lót | 4; 1350 × 1700 × 700; 100 | 4; 1350 × 1700 × 700; 100 | 0 % |
| Móng M2 | số khối; L × B × h; lót | 6; 1300 × 1700 × 700; 100 | 6; 1300 × 1700 × 700; 100 | 0 % |
| Móng M3, M4 | số khối | 2; 2 | 2; 2 | 0 %; kích thước chưa đo tay |
| Vị trí khung móng (để kiểm hố chồng lấn) | số khối tìm được | 14 | 6 (M2 4/6, M3 2/2) | còn thiếu 8 — để trống kèm cảnh báo |
| Cột | m³ theo tầng | chưa có | | chưa đánh giá |
| Dầm | m³ theo tầng, mã | chưa có | | chưa đánh giá |
| Sàn | m³ theo tầng | chưa có | | chưa đánh giá |
| Đào, đắp | m³ | chưa có (cần cốt tự nhiên, c, m từ hồ sơ) | | chưa đánh giá |

## Giới hạn

- Móng cọc, đài cọc, hố móng phức tạp, biện pháp đào đặc biệt: chưa có công thức, nhập `volume_m3` tay.
- Móng coi cạnh dài theo trục x khi kiểm hố chồng lấn và cắt giằng (móng xoay 90° cần thêm hướng).
- Đào rãnh giằng móng, cổ móng (bê tông) chưa tính; cổ móng chỉ dùng để trừ đất đắp.
- Trừ đáy sàn trên dầm, cột gán vào mặt bằng của dầm/cột, chưa dò ô sàn tầng trên theo cao độ.
- Dầm đọc từ bản vẽ kết cấu chưa được cắt ở mặt cột (cột không đọc trên mặt bằng kết cấu); chỉ cắt ở dầm chính, móng.
- Tập mẫu ưu tiên (S05-01) mới có 1 file kết cấu thật (`ket_cau.dxf`).
