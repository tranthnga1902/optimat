# S07–S08: Cốt thép theo bảng thống kê, BOQ MVP, cấu kiện phụ

Ngày: 21/10/2026. Mã: `src/optimat/rough/rebar.py`, `secondary.py`, `boq.py`, `steel.py`, `stairs.py`; móc nối trong `takeoff.py`.
Quy tắc: `data/rules/bang_thep.csv`, `thep_kg_m.csv`, `loai_mai.csv`, `ho_tro_cau_kien.csv`, `ky_hieu_cau_kien.csv` (K07–K11).

## Quy ước bảng thống kê thép (S07-01)

- Tiêu đề chứa "THỐNG KÊ THÉP" hoặc "THỐNG KÊ CỐT THÉP" (TEXT/MTEXT). Bảng ACAD_TABLE phải phá (EXPLODE) trước.
- Một hàng tiêu đề cột, bắt buộc có **đường kính** và **chiều dài cắt 1 thanh**; các cột khác nhận theo `bang_thep.csv`
  (cấu kiện, số hiệu, hình dạng, SL 1 CK, số CK, tổng số thanh, khối lượng).
- Chiều dài ghi `(m)` ở tiêu đề thì đổi sang mm; không ghi thì coi là mm. Ngoài 100–30 000 mm: nghi sai đơn vị, để trống.
- Bảng kết thúc ở dòng "TỔNG", tiêu đề khác, hoặc khoảng trống > 3 lần khoảng cách dòng.

## Công thức (S07-02…04)

- kg = tổng số thanh × chiều dài cắt (m) × kg/m (`thep_kg_m.csv`, nguồn TCVN 1651-1/2:2018; chưa đối chiếu số hiệu bảng bản in).
- Tổng số thanh = cột tổng; không có thì SL 1 CK × số CK; cả hai có mà lệch thì cảnh báo đếm trùng.
- Lệch > 3 % so với cột khối lượng của bảng thì cảnh báo; lệch ~1000 lần thì nghi sai đơn vị.
- Dòng trùng hệt (bảng vẽ lặp) chỉ cộng một lần.
- Neo, nối, uốn, móc: **không tự cộng**, lấy nguyên chiều dài cắt của bảng.
- Thứ tự ưu tiên thép: tấn nhập tay > bảng thống kê (`basis = bang_thong_ke`) > hàm lượng người dùng nhập
  (`basis = ham_luong`, cảnh báo "cần review"). Không có cả ba: để trống, `missing` có "bảng thống kê thép".
- Cấu kiện không map được (ký hiệu lạ): dòng `basis = not_supported`, không trả số, không sinh vật liệu.

## Cấu kiện phụ (S08)

| Cấu kiện | Đầu vào | Công thức |
|---|---|---|
| Cầu thang bản | `Stair` nhập tay; `kind` = ban/con/xoan; dầm thang `beam_length_mm`, `beam_width_mm`, `beam_depth_mm` | bản + bậc + chiếu nghỉ + dầm thang; cốn/xoắn: Not supported |
| Giằng tường | `PlanInput.members` (kind GIANG_TUONG) hoặc ký hiệu GT… + cặp nét trên mặt bằng kết cấu | dài × rộng × cao; cốp pha 2 × cao × dài |
| Sê nô | ký hiệu SN… / nhập tay | dài × rộng × cao (chữ nhật quy ước, cảnh báo chữ U) |
| Lanh tô | theo lỗ cửa (walls.py); LT… trên kết cấu chỉ cho cao lanh tô | không đổi |
| Mái bê tông | `ProjectParams.roofs` kind be_tong: diện tích, dày, `replaces_slab_of` | diện tích × dày; cốp pha = diện tích |
| Mái khung | roofs kind khung, hoặc tiêu đề BV13 khớp `loai_mai.csv` | Not supported |

Luật không cộng trùng (S08-04): L1 lỗ cửa có cao cửa + cao lanh tô > cao xây thì không có lanh tô riêng (dầm làm
lanh tô); L2 giằng trên trục tường cùng mặt bằng trừ khỏi khối xây; L3 mái thay sàn bỏ sàn + cốp pha sàn của mặt bằng
đó; L4 ký hiệu LT… không sinh khối lượng.

## Xuất BOQ (S07-05, 06)

`python scripts/export_boq.py kien_truc.dxf --structural ket_cau.dxf [--structural ...] --height 3300 --params p.json`
hoặc `POST /api/takeoff/rough/excel` (thân = RoughRequest). Sheet: Tổng hợp, Theo tầng, Theo cấu kiện, Cốt thép, Vật liệu,
Cảnh báo, Phạm vi hỗ trợ. Mọi dòng công tác có `formula`, `evidence`, `missing_reason`.

## Demo đã chạy

`nha_dan.dxf` + `ket_cau.dxf` (scale 0.5): 115 dòng công tác (12 để trống), 0 dòng thép vì bản vẽ kết cấu không có bảng
thống kê thép (chỉ có "THỐNG KÊ CỘT") → thép để trống, yêu cầu review.

## Chưa hỗ trợ / giới hạn

- ACAD_TABLE chưa đọc; bảng có tiêu đề cột hai tầng (SỐ LƯỢNG / 1 CK / TOÀN BỘ) chưa nhận.
- Giằng, sê nô từ mặt bằng kết cấu chưa gắn tầng kiến trúc → chưa trừ khỏi khối xây (conditional).
- Luật L1, L2 sửa công tác XAY/LANH_TO sau `wall_works` (chép công thức lanh tô): chuyển vào `walls.py` khi rảnh.
- Thép theo bảng chưa chia nhóm đường kính trong bảng vật liệu (sheet Cốt thép có từng dòng Ø).
- Tỷ lệ mặt bằng kết cấu cho giằng/sê nô lấy `structural_scale` (không tự suy như dầm).
- Mái kèo phức tạp, thép triển khai tự do, móng băng/cọc, thang cốn/xoắn: Not supported.
- Chưa có bộ hồ sơ có bảng thép thật để kiểm regression (test dùng bản vẽ giả).
