# Đối chiếu "Đặc tả quy tắc bóc tách phần thô từ bản vẽ kiến trúc (DXF)" (30/10/2026) với mã

Ghi ngày 30/10/2026. Đặc tả nằm ngoài kho mã (@midu); bảng này cho biết mục nào đã có trong `src/optimat/`, mục nào
được bổ sung trong S12, và ba điểm lệch đã chốt. Số liệu kiểm chứng: `NHAT_KY.md` dòng 30/10/2026 (S12).

## 1. Từng mục của đặc tả

| Mục | Hiện trạng | Bổ sung S12 |
|---|---|---|
| 1, 1A phạm vi: chỉ vật liệu thô, 5 nhóm, nhãn A–D | Pipeline DXF → công tác → vật liệu đã có (S0–S11) | `RoughResult.by_group` (5 nhóm từ `material_groups`; nhóm 3–5 liệt kê "ngoài phạm vi"), `MaterialLine.group_id`, `weight_kg` |
| 2 quy ước bản vẽ | 23 điều khoản QU (`quy_uoc.csv`, `convention_check.py`) | — |
| 2A bước 1–3, 5–7 | `dxf_reader`, `plans`, `walls`, `material_rules`, `structural` | — |
| 2A bước 4 (XGBoost phân loại) | Chỉ luật + "đoán hình học" gắn nhãn, người dùng duyệt | **Không làm** (đặc tả tự xếp đây là mục cắt đầu tiên) |
| 3 trạng thái A/B/C/D | Rải rác: `basis`, `source`, `missing`, `height_source`, `material_confidence` | `rough/status.py`: `WorkItem.status`, `inputs`; `MaterialUse/MaterialLine.status` = xấu nhất; quy tắc 3.1 (D không ra số) và 3.2 (C ghi tạm tính); trang /do-boc tab Phần thô hiện nhãn trạng thái từng dòng (C "tạm tính", vật liệu D ghi "thiếu") |
| 3A bảng mẫu công tác "lưu thành dữ liệu" | Công thức hình học trong mã (`rough/*.py`), ma trận `ho_tro_cau_kien.csv` | **Giữ trong mã** (công thức không hợp dạng bảng); đã chốt |
| 3B hệ số ước chừng: mức căn cứ, khoảng | `dinh_muc_phan_tho.csv` trống chờ TT 38 | Cột `muc_xac_nhan` (nguon / tinh / kinh_nghiem), `qty_min`, `qty_max`, `ngay_tra`; cấp phối M250 (cem.gov.vn) điền với nhãn; hệ số không có `norm_code` → vật liệu C + cảnh báo. Hàm lượng thép 154/139/66–79 và vữa M75 230–260 kg **chưa điền** (hàm lượng thép là tham số người dùng `steel_kg_per_m3`; vữa M75 lấy từ `material_relations` COMPOSED_OF của danh mục) |
| 4 tường xây | `rough/walls.py` (trừ cửa, lanh tô, cột, giằng, dầm; dày khối xây theo phương án) | `ProjectParams.min_opening_m2` (mặc định 0 = trừ mọi lỗ, ghi trong công thức) |
| 5 cấu kiện còn lại | Cột, dầm, sàn, thang, móng, đào đắp, cốp pha, thép — có | — |
| 6 định mức: hạ mã xuống tham khảo | CSV + `wall_systems` (AE.221/222 đã có số) | Mức xác nhận như 3B. 30/10/2026: điền 19/22 dòng từ PDF TT 38/2026 (`data/van_ban/`): trát AK.21200, cán 30 mm AK.41100, cát đệm AB.13410, cấp phối bê tông 11.11321 (M100, PCB30) và 11.12322–11.12324 (PCB40, đá 1×2, sụt 6–8 cm, đã nhân 1,025 m³ vữa / m³ kết cấu), dây buộc TH10 khoảng 7,85–16,07 kg/tấn (C), chống thấm CT02/CT03 theo AK.92100 2,21 kg/m² (C); cấp phối vữa VU01/VU02 theo 12.10133/12.10134; trọng lượng đơn vị cát, đá, gạch, gỗ theo PL VII Phụ lục I. Còn trống: cán 50 mm, chống thấm CT01, ván khuôn phủ phim CP01 |
| 7 kiểm tra chéo | QU-05, `_section_checks`, `compare_estimate.py` | `rough/checks.py` + `khoang_hop_ly.csv` (KH01–KH05, chỉ cảnh báo); KH05 sàn từng tầng so với `ProjectParams.building_area_m2` (người dùng nhập, C: bản vẽ build không ghi diện tích xây dựng nên chưa đọc từ chữ) |
| 11 đầu ra cho bộ tối ưu | Chưa có kg, nhóm, giai đoạn, hướng | `weight_kg`, `group_id`, `WorkItem.stage` (4 giai đoạn), `envelope_by_orientation` khi có `ProjectParams.north_deg`; `rough/boq.py: export_for_optimizer` (JSON: nhóm, kg, m³ vận chuyển, lượng theo giai đoạn, dòng D vào `missing`) qua API `/api/takeoff/rough/optimizer` và `export_boq.py --json` |
| 12 schema `boctach` 19 bảng | 26 bảng `public`, kết quả JSON trong `takeoff_results` | **Không tạo schema song song**; trạng thái, nhóm, kg nằm trong JSON kết quả. Các cột CSV mới chưa vào bảng `rough_norms` (init_db / export_sql bỏ qua) |

## 2. Ba điểm lệch đã chốt (30/10/2026)

1. Không có XGBoost phân loại đối tượng DXF; luật + nhãn "đoán" + chờ người dùng xác nhận (đang có).
2. Bảng mẫu công tác giữ trong mã; chỉ ma trận phạm vi hỗ trợ và định mức là dữ liệu.
3. Không tạo schema `boctach`; giữ 26 bảng và JSON `takeoff_results`. Đổi lược đồ khi nga chốt.

## 3. Cách đọc trạng thái trong kết quả

- `WorkItem.status`, `inputs`: ví dụ `["chiều dài, dày tường: A (hình học mặt bằng)", "chiều cao tầng: B", "cao dầm trừ khỏi tường: C"]` → `C`.
- `MaterialLine.status`: xấu nhất của `uses[].status`; `complete = False` → `D`. `confirmation`: mức xác nhận yếu nhất của hệ số đã nhân.
- `RoughResult.status`: xấu nhất toàn bảng (hiển thị nhanh). BOQ Excel: cột "Trạng thái", "Giai đoạn", "Đầu vào quyết định trạng thái", sheet "Theo nhóm".
- Sai số (mục 7) chỉ tính trên dòng A và B: lọc `status in ("A", "B")` khi so với đáp án.
