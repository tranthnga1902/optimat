# J05c - Điều chỉnh vữa trát trên tường gạch rỗng: thiết kế

Ngày: 03/11/2026. **Chuẩn bị kỹ thuật xong, chờ Codex review hợp đồng; chưa sửa mã, chưa nghiệm thu J05c/J04.**
Phạm vi: chỉ hệ số vữa trát tường do nền gạch rỗng (AK.211/212). Không mở trát cột/dầm/trần, ván ép, phụ gia, cán 50 mm.

Lý do chưa triển khai dù prompt cho phép: hợp đồng dưới đây (a) gán `wall_system_id` cho dòng TRAT (trường có sẵn, nghĩa mới), (b) đổi khóa tra định mức TRAT sang chiều dày + họ vật liệu nền, (c) đổi hành vi hiện tại: tường chưa rõ nền hoặc nền AAC/không nung đang ra 0,017 m³/m² sẽ thành thiếu. Ba điểm này là đổi hợp đồng dữ liệu/đầu ra, theo CLAUDE.md và prompt phải được Codex chốt trước.

## 1. Kiểm nguồn

[N2 PDF 589 / in 588](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=589), bản lưu `data/van_ban/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf` (724 trang). Đã render trang 589 bằng pypdfium2 và xem trực quan; đã trích chữ trang 590-591 bằng pdftotext (chưa xem ảnh 590).

| Bảng | Mã cột 1,0 / 1,5 / 2,0 cm | Vữa xi măng m³/1 m² | Vật liệu khác |
|---|---|---|---|
| AK.21100 trát tường ngoài | AK.21110 / 21120 / 21130 | 0,012 / 0,017 / 0,023 | 0,5 % |
| AK.21200 trát tường trong | AK.21210 / 21220 / 21230 | 0,012 / 0,017 / 0,023 | 0,5 % |

- "Quy định áp dụng định mức" in **một lần, ngay dưới bảng AK.21200**: nếu trát tường xây gạch rỗng thì hao phí vữa tăng 10%. Câu này đứng trong mục AK.21000 TRÁT TƯỜNG, sau cả hai bảng; đọc là áp cho AK.211 và AK.212. Cách đọc này cần Codex xác nhận vì về bố cục câu chỉ nằm dưới bảng thứ hai.
- Hướng dẫn chung AK.20000: vữa khô trộn sẵn đóng bao chỉ điều chỉnh nhân công/máy (k = 0,9), không đổi lượng vữa. Ngoài phạm vi vật tư.
- **Phát hiện mới:** trang 590-591 có bảng riêng **AK.21300/21400 trát tường xây gạch không nung bằng vữa** (chữ trích: 0,006 / 0,008 / 0,011 m³) và **AK.21500/21600** (gạch không nung bằng vữa thông thường). Tức AAC/gạch không nung không thuộc AK.211/212. Hiện `materials.py` tra TRAT chỉ theo chiều dày nên tường AAC đang nhận 0,017 m³/m² của AK.212: đây là sai phạm vi hiện có, không phải chỉ thiếu hệ số 1,10. J05c không tra số AK.213-216 (ngoài phạm vi prompt); chỉ đề xuất cho dòng này ra thiếu.
- "Vật liệu khác 0,5%" là % chi phí vật liệu, không sinh kg/viên. Không coi danh sách vật tư là đủ chỉ vì có vữa.

Số học: 15 mm 0,017 × 1,10 = 0,0187; 20 mm 0,023 × 1,10 = 0,0253 m³/m².

## 2. Truy vết nền tường hiện tại

| Bước | Mã | Hiện trạng |
|---|---|---|
| Vật liệu tường | `ReviewWall.mat` (ghi chú/hatch/layer, người dùng sửa trên `/do-boc`) | Có |
| Phương án tường | `takeoff.py:222` `catalog.resolve_wall([w.mat], w.cls)`; thiếu thì `wall_systems_by_class` (C) | Có, theo từng tường |
| Gộp nhóm | `walls.py:75` khóa `(cls, role, system)` | Mỗi nhóm một phương án |
| Dòng XAY | `walls.py:99` có `wall_system_id=system` | Có |
| Dòng TRAT | `walls.py:106` **không** truyền `wall_system_id`; `variant` = dày trát | **Mất nền** |
| Vật liệu | `materials.py` nhánh `TRAT/CAN_NEN`: `norms_for(w.code, w.variant)` | Chỉ theo dày |
| Họ vật liệu | `materials.family` (khóa ngoại `material_families`): GN01 CLAY_SOLID; GN02, GN03, GO01 CLAY_HOLLOW; AAC01-03 AAC | Có trong danh mục |

Vì nhóm TRAT sinh cùng vòng lặp với XAY theo `(cls, role, system)`, chỉ cần truyền `system` sang TRAT là nền đi tới từng mặt trát. Hai tường cùng dày nhưng khác phương án đã nằm ở hai nhóm riêng: không bao giờ nhân 1,10 lên tổng vữa trộn lẫn.

Phân loại nền từ `family` của vật liệu chính trong phương án:

| Họ | Phân loại J05c | Ghi chú cần xác nhận |
|---|---|---|
| CLAY_SOLID | đặc, AK.211/212 | |
| CLAY_HOLLOW | rỗng, AK.211/212 × 1,10 | GN02 "2 lỗ" dùng định mức xây AE.22 (wall_systems ghi "không có bảng riêng"); xếp rỗng theo họ + TCVN 1450. Codex/người kiểm xác nhận GN02 có tính là "gạch rỗng" theo ghi chú TT 38 |
| AAC, CLC, CMU_SOLID, ALC_PANEL | ngoài phạm vi AK.211/212 (thuộc AK.213-216 hoặc khác) | Ra thiếu, không tự dùng 1,10 |
| CMU_HOLLOW | chưa rõ (block bê tông rỗng là gạch không nung) | Ra thiếu đến khi Codex chốt |
| Không có phương án / phương án không có họ | chưa rõ | Ra thiếu |

Danh mục: cột `family` không có cột nguồn riêng. Ánh xạ trên dựa vào tên + họ của danh mục gốc `materials_master.xlsx`; nếu Codex coi họ chưa đủ chứng minh nền, phải thêm nguồn cho họ trong XLSX (không sửa CSV sinh ra).

## 3. Hợp đồng đề xuất (chờ Codex chốt)

Không thêm trường mô hình, không thêm bảng DB.

1. **`WorkItem.wall_system_id` trên TRAT**: `walls.py:106` truyền `wall_system_id=system`. Sửa chú thích `models.py:307` thành "công tác xây, trát: phương án tường". Kiểm caller: `secondary.py:_xay_of` lọc `code == "XAY"` nên không bị ảnh hưởng; `takeoff.py:305` thêm bằng chứng `wall_systems_by_class` chỉ cho XAY, phải mở cho TRAT để trạng thái nền theo thông số người dùng ra C (`status.py:59` đọc `evidence`).
2. **Khóa định mức** `TRAT` variant = `"<dày>/<family>"` trong `data/rules/dinh_muc_phan_tho.csv`. `WorkItem.variant` vẫn là dày (API/UI không đổi); `materials.py` ghép khóa khi tra. Cột `rough_norms.variant` là String(32), đủ chỗ, không cần migration; nạp lại bằng `init_db.py --reload-rules`.
3. **Ưu tiên khi người dùng sửa**: nền đi theo vật liệu tường. Người dùng đổi vật liệu trên `/do-boc` hoặc chọn `wall_systems_by_class` thì nền đổi theo. Không thêm ô "loại nền" riêng (không có nhu cầu tách nền khỏi vật liệu xây).
4. **Trạng thái**: dòng có số giữ trạng thái công tác (A/B/C theo nguồn phương án), `confirmation = nguon` vì có `norm_code`. Nhập tay vẫn C, không nâng A do có mã bảng.
5. **Thiếu**: không có dòng cho khóa → `bill.add(... None ...)` với lý do cụ thể: "định mức TRAT dày 15 mm trên nền <họ hoặc 'chưa rõ'> (AK.211/212 chỉ áp gạch đất nung; gạch không nung tra AK.213-216)". Không số 0, không lùi về nền đặc.
6. **CAN_NEN** giữ nguyên `norms_for(w.code, w.variant)`.

### Dữ liệu đề xuất (thay hai dòng TRAT hiện có)

```csv
TRAT,15/CLAY_SOLID,@VUA,Vữa trát,0.017,m³ / m²,,,nguon,2026-11-03,AK.21220,TT 38/2026/TT-BXD Phụ lục II (datafiles.chinhphu.vn),"Trát tường gạch đất nung đặc dày 1,5 cm: 0,017 m³ vữa / m² (AK.21120 trát ngoài cùng số)"
TRAT,15/CLAY_HOLLOW,@VUA,Vữa trát,0.0187,m³ / m²,,,nguon,2026-11-03,AK.21220,TT 38/2026/TT-BXD Phụ lục II (datafiles.chinhphu.vn),"Trát tường gạch rỗng dày 1,5 cm: 0,017 × 1,10 (quy định áp dụng AK.21000, PDF 589) = 0,0187 m³ vữa / m²; đã gồm điều chỉnh, không nhân thêm"
TRAT,20/CLAY_SOLID,@VUA,Vữa trát,0.023,m³ / m²,,,nguon,2026-11-03,AK.21230,TT 38/2026/TT-BXD Phụ lục II (datafiles.chinhphu.vn),"Trát tường gạch đất nung đặc dày 2,0 cm: 0,023 m³ vữa / m² (AK.21130 trát ngoài cùng số)"
TRAT,20/CLAY_HOLLOW,@VUA,Vữa trát,0.0253,m³ / m²,,,nguon,2026-11-03,AK.21230,TT 38/2026/TT-BXD Phụ lục II (datafiles.chinhphu.vn),"Trát tường gạch rỗng dày 2,0 cm: 0,023 × 1,10 = 0,0253 m³ vữa / m²; đã gồm điều chỉnh, không nhân thêm"
```

Hệ số nằm trong dữ liệu dưới dạng số đã nhân (giống cách CSV đã ghi cấp phối bê tông × 1,025), có công thức trong `note`; Python không chứa 1,10 hay danh sách mã. Mặt ngoài/trong cùng số; `norm_code` ghi mã trong, ghi chú nêu mã ngoài. Nếu Codex cần mã đúng từng mặt, thêm mặt vào khóa (`15/CLAY_HOLLOW/NGOAI`) ở vòng sau.

### Bản vá đề xuất (chưa áp)

```diff
--- src/optimat/rough/walls.py:106
-            works.append(_work("TRAT", n * net_area, plan=plan, element=f"{label}, {face}",
+            works.append(_work("TRAT", n * net_area, plan=plan, element=f"{label}, {face}", wall_system_id=system,
--- src/optimat/rough/materials.py (nhánh TRAT/CAN_NEN của materials_for_works)
-            rows = norms_for(w.code, w.variant, norms)
+            key = w.variant
+            if w.code == "TRAT" and w.variant:      # nền trát theo họ vật liệu của phương án tường (AK.211/212 + quy định gạch rỗng)
+                fam = _family_of(bill, view, w.wall_system_id)
+                key = f"{w.variant}/{fam or 'CHUA_RO'}"
+            rows = norms_for(w.code, key, norms)
             if not rows:
-                bill.add(..., [f"định mức {w.code} cho chiều dày {w.variant or '(chưa nhập)'} mm"])
+                bill.add(..., [f"định mức {w.code} cho chiều dày {w.variant or '(chưa nhập)'} mm"
+                               + (f" trên nền {fam or 'chưa rõ'}" if w.code == "TRAT" else "")])
--- src/optimat/rough/takeoff.py:305
-        if w.code == "XAY" and (w.plan, w.wall_system_id) in by_param:
+        if w.code in ("XAY", "TRAT") and (w.plan, w.wall_system_id) in by_param:
```

`_family_of`: `view.loc[id].material_id` → `bill.mats.loc[mid, "family"]`, trống thì None (vài dòng, đặt cạnh `_masonry`). `wall_view()` cần có `material_id` (đã có, `materials.py:_masonry` dùng `s.material_id`).

## 4. Ca nghiệm thu SYNTHETIC (thêm vào `tests/test_rough_materials.py`, `tests/test_rough_walls.py`)

Dùng `Norm(...)` tự dựng như `test_plaster_uses_norm_and_mortar_mix` và cấp phối VU02 hiện có (XM01 307 kg, CA02 1,13 m³ / m³ vữa).

| # | Đầu vào | Kỳ vọng |
|---|---|---|
| 1 | TRAT 10 m², dày 15, phương án GN02 (CLAY_HOLLOW), M75 | vữa trung gian 0,187 m³; XM01 57,409 kg; CA02 0,21131 m³ |
| 2 | như 1, dày 20 | vữa 0,253 m³ |
| 3 | 10 m², 15, GN01 (CLAY_SOLID) | vữa 0,170 m³; XM01 52,19 kg |
| 4 | tường ngăn GN02 10 m² mỗi mặt (`walls.py` sinh "hai mặt", 20 m²) | vữa 0,374 m³; diện tích chỉ nhân 2 một lần |
| 5 | hai nhóm cùng 220, một GN01 một GN02, mỗi nhóm 10 m² | hai `MaterialUse` riêng 0,170 và 0,187 (tổng 0,357), không phải 0,340 × 1,10 |
| 6 | không phương án / CMU_HOLLOW / dày 25 / chưa chọn mác | dòng thiếu có lý do cụ thể, `complete=False`, không số 0 |
| 7 | AAC01 dày 15 | thiếu, lý do nêu AK.213-216; không 0,0187 và không 0,017 |
| 8 | CAN_NEN 30 mm cùng hồ sơ | 0,035 m³/m², không đổi |
| 9 | công tác TRAT nhập tay âm −2 m² trên GN02 | phần góp −0,0374 m³, đúng dòng rỗng (giới hạn Q02: chưa kiểm cơ chế gộp phần biết/thiếu toàn hệ) |
| 10 | GN02 chọn qua `wall_systems_by_class` | dòng TRAT trạng thái C; nhập tay giữ C dù có `norm_code` |
| 11 | `walls.py`: TRAT mang `wall_system_id` của nhóm | kiểm trên `wall_works` |

Ca cũ phải đổi: `test_plaster_uses_norm_and_mortar_mix` dùng `variant="15"` không có phương án → sau sửa sẽ ra thiếu; chuyển sang có `wall_system_id` W-GN01-220.

## 5. Đường dữ liệu và kiểm tra khi triển khai

- CSV → `init_db.py --reload-rules` (bảng `rough_norms`), hoặc sinh lại `sql/05_rules.sql` bằng `export_sql.py`. Không cần `04_upgrade.sql`.
- `check_data.py`: dòng mới có `qty` + `norm_code` + mã vật liệu `@VUA` như dòng cũ; không có quy tắc nào kiểm variant là số (đã đọc `_check_rough_norms`).
- Chạy test trọng tâm rồi toàn bộ pytest một lần, không đồng thời với phiên D02 trên cùng DB kiểm thử. Có DB kiểm thử thì `check_data` trên DB đã nạp lại, ghi hash CSV.
- UI: không đổi (variant vẫn là dày). Chỉ API/BOQ đổi số và lý do thiếu.

## 6. Phải chờ

| Mục | Ai | Ghi chú |
|---|---|---|
| Chốt hợp đồng mục 3 (khóa variant, TRAT mang phương án, hành vi thiếu cho AAC/chưa rõ) | Codex | điều kiện để sửa mã |
| Ghi chú +10% áp cho cả AK.211 | Codex | bố cục chỉ in một lần dưới AK.212 |
| GN02 (2 lỗ), GO01 (ống 4 lỗ) là "gạch rỗng" theo TT 38 | Codex / người kiểm | họ danh mục chưa có cột nguồn |
| CMU_HOLLOW thuộc nhóm nào | Codex | hiện đề xuất thiếu |
| Loại nền, mặt, dày, diện tích, mác vữa của hồ sơ thật | D02 người kiểm | D02 hiện 0 dòng xác nhận |
| Định mức AK.213-216 cho AAC/không nung | gói khác | ngoài J05c; hiện AAC đang nhận nhầm AK.212 |

## 7. Bàn giao

- Tạo duy nhất tệp này. Không sửa mã, CSV/XLSX/SQL/DB, D02, J04, CLAUDE.md, SPRINTS.md, NHAT_KY.md.
- Đã kiểm: render PDF 589 và xem; trích chữ PDF 590-591; đọc `walls.py`, `materials.py`, `norms.py`, `models.py`, `status.py:_inputs`, `takeoff.py` (đoạn gán phương án, bằng chứng), `secondary.py:_xay_of`, `data_check._check_rough_norms`, `db/models.py` cột variant, CSV định mức, danh mục, quan hệ vữa, test TRAT hiện có.
- Chưa chạy pytest/check_data (không đổi mã/dữ liệu). Số trong mục 4 là tính tay.
- **Chuẩn bị kỹ thuật xong, chờ Codex review.**

## 8. Triển khai sau [Codex review vòng 1](../review/J05BCD_CODEX_REVIEW_V1.md) (03/11/2026)

Hợp đồng mục 3 được chốt, với các điều chỉnh của review: +10% áp cả AK.211 và AK.212 (BA đọc phạm vi); nguồn ghi chung "AK.211/AK.212", không hiển thị AK.212 như mã mặt ngoài; CMU_HOLLOW là gạch không nung, không nhận +10%; AAC/CMU/CLC/panel/chưa rõ ra thiếu, chưa tra AK.213-216.

### Diff

| Tệp | Thay đổi |
|---|---|
| `src/optimat/rough/walls.py` (`wall_works`) | dòng TRAT nhận `wall_system_id=system` của nhóm |
| `src/optimat/rough/models.py` (`WorkItem.wall_system_id`) | chú thích thêm "trát: nền trát" |
| `src/optimat/rough/takeoff.py` (`compute_rough`, đoạn gắn bằng chứng `wall_systems_by_class`) | áp cho `XAY` và `TRAT` → trát theo phương án người dùng chọn là C |
| `src/optimat/rough/materials.py` (`materials_for_works` nhánh TRAT/CAN_NEN, hàm mới `_family_of`) | TRAT tra khóa `<dày>/<family>`; thiếu dày hoặc family thì không tra (khởi tạo an toàn, không dùng biến chưa gán) và lý do nêu "trên nền <họ | chưa rõ>". CAN_NEN giữ `norms_for(w.code, w.variant)` |
| `data/rules/dinh_muc_phan_tho.csv` | thay `TRAT,15` và `TRAT,20` bằng `15/CLAY_SOLID` 0,017; `15/CLAY_HOLLOW` 0,0187; `20/CLAY_SOLID` 0,023; `20/CLAY_HOLLOW` 0,0253; `norm_code` "AK.211/AK.212"; ghi chú nêu mã từng mặt và phép × 1,10 |
| `tests/test_rough_plaster.py` (mới) | 16 ca SYNTHETIC |
| `tests/test_rough_materials.py::test_plaster_uses_norm_and_mortar_mix` | đổi sang có phương án W-GN01-220; thêm ca chưa có phương án → thiếu (giữ hành vi mới, không che) |

Không đổi trường/bảng DB, không đổi UI (`variant` vẫn là dày). Python không chứa 1,10 hay danh sách mã GNxx.

### Ca đã chạy (`tests/test_rough_plaster.py`)

- 100 m² vữa trung gian: GN02 15 → 1,87; GN02 20 → 2,53; GO01 15 → 1,87; GN01 15 → 1,7; GN01 20 → 2,3 m³. XM01 (tấn) và CA02 kiểm theo số đã làm tròn 3 chữ số của đầu ra; mọi phần góp `waste_included`.
- Hai nền cùng dày, mỗi nền 100 m²: vữa 3,57 m³ (không phải 3,4 × 1,10); hai `MaterialUse` CA02 riêng 1,921 / 2,1131.
- 100 m² rồi trừ −20 m² cùng nền rỗng: 1,496 m³.
- Thiếu: không phương án, phương án không tồn tại, AAC02, GK02 (CMU_HOLLOW), dày 25, chưa nhập dày → đúng một dòng thiếu D, không có vữa trung gian, lý do nêu họ/"chưa rõ"/"chưa nhập".
- Chưa chọn mác: vữa vẫn 1,87 m³, dòng vật liệu thiếu "mác vữa".
- CAN_NEN 30 mm 10 m² → 0,35 m³ (không đổi).
- `wall_works`: mặt trong/ngoài tường bao GN02 mang W-GN02-220; tường ngăn không vật liệu mang None và ra thiếu; mặt ngoài nhận 0,0187.
- `compute_rough` với `wall_systems_by_class`: mọi TRAT trạng thái C, có đầu vào "phương án tường: C".

### Lệnh và kết quả (Python `.venv`)

- `pytest tests/test_rough_plaster.py tests/test_rough_materials.py tests/test_rough_walls.py tests/test_rough_status.py -q` → **43 passed**.
- `pytest -q` toàn bộ (không có `OPTIMAT_TEST_DATABASE_URL` trong môi trường, bài PostgreSQL bị bỏ) → **390 passed, 3 xfailed, 1 failed**: `tests/test_drawing_io.py::test_real_drawing_read_in_world_coords[nha_huong_hai_duong_7x12_kien_truc.dxf]`, `IndexError` tại `src/optimat/drawing/encoding.py:113`. J05c không chạm `encoding.py`; tệp này đang có thay đổi chưa commit của phiên khác (+40 dòng). Chưa chạy lại riêng để xác nhận trước thay đổi đó.
- `scripts/check_data.py` → 0 lỗi, 1915 cảnh báo, 2 ghi chú. **Đính chính (review vòng 2):** lần này chạy trên PostgreSQL theo `DATABASE_URL` trong `.env` (báo cáo ghi "nguồn postgresql"), tức DB còn dữ liệu cũ; **không** phải kiểm CSV như đã ghi. Lệnh này cũng đã ghi đè `reports/data_check.md` / `.json` của workspace (không có bản sao để khôi phục bản trước). Kết quả kiểm đúng nguồn ở mục 9.
- SHA-256 `data/rules/dinh_muc_phan_tho.csv` sau sửa: `0E677EAA3CFFEB4AFFD1FA3BAAAFB35C288F63E05EC39481E73C437CB092D542`.
- Chưa nạp/kiểm trên PostgreSQL kiểm thử (không có DB): đường DB **chưa kiểm**. Khi có: `init_db.py --reload-rules` trên DB kiểm thử rồi `check_data.py`.

### Giới hạn

- Phiên điều phối ghi trong CLAUDE.md không có trong danh sách phiên đang chạy; chưa gửi được thông báo sửa `models.py`/`takeoff.py`. Phiên tích hợp cần ghi `NHAT_KY.md`/`SPRINTS.md` (không sửa trong đợt song song).
- Tường AAC/không nung trước đây ra 0,017 m³/m² nay ra thiếu: thay đổi số trên hồ sơ có AAC là chủ ý theo review.
- Q02 (gộp phần biết/thiếu toàn hệ) không đổi.
- Chưa áp hồ sơ thật, chưa đo KPI; chờ D02 xác nhận nền/dày/mặt/mác.
- **Bàn giao J05c: đã triển khai, chờ Codex review; không tự nghiệm thu.**

## 9. Đồng bộ dữ liệu và bằng chứng kiểm (review vòng 2, 03/11/2026)

**Phân biệt bằng chứng:** các lệnh, số lượng và kết quả CSV/DB kiểm thử dưới đây do Claude bàn giao từ lần chạy trước. Lượt rà chỉ đọc theo [gói đồng bộ](../review/J05C_GOI_DONG_BO.md) đã đối chiếu bốn dòng TRAT CSV/SQL và thấy mã test bổ sung, nhưng chưa kiểm báo cáo scratchpad gốc hoặc chạy xác nhận độc lập các kết quả đó. Lượt sửa tài liệu này không chạy test, không truy vấn/nạp DB và không xác nhận DB vận hành đã đồng bộ.

### SQL sinh lại

- Lệnh: `OPTIMAT_NO_DOTENV=1 python scripts/export_sql.py` (không đọc `.env`, không kết nối DB). Sao lưu 01/02/05 trước khi sinh rồi so.
- `sql/01_schema.sql`, `sql/02_seed_sample.sql`: **không đổi** byte nào.
- Theo bàn giao lần sinh, `sql/05_rules.sql` đổi đoạn `rough_norms` từ 31 lên 68 dòng; năm bảng quy tắc còn lại được báo là giống bản sao trước sinh. Bốn dòng TRAT mới thay hai dòng cũ làm tăng 2 trong tổng tăng 37; không gọi toàn bộ 37 dòng tăng là ngoài J05c. Các thay đổi ngoài TRAT (cốp pha gỗ AF.81, cấp phối M150/M350/M400, dòng VAN_EP...) phải được liệt kê và review diff riêng trước phát hành; lượt rà này chưa xác minh độc lập toàn bộ diff hoặc nguồn từng dòng. Bộ cài dùng toàn bộ SQL sẽ nạp cả phần ngoài J05c.

### Kiểm theo nguồn

| Đường | Cách chạy | Kết quả |
|---|---|---|
| CSV | tiến trình riêng, bỏ `DATABASE_URL`, `OPTIMAT_NO_DOTENV=1`, overlay rỗng, `run_checks(catalog=Catalog.from_csv(None))`; báo cáo ghi vào scratchpad (không đè `reports/`) | `nguon_du_lieu = csv`; **0 lỗi**, 1891 cảnh báo, 2 ghi chú; `load_norms()` TRAT = 15/CLAY_HOLLOW 0,0187; 15/CLAY_SOLID 0,017; 20/CLAY_HOLLOW 0,0253; 20/CLAY_SOLID 0,023 |
| DB kiểm thử (`OPTIMAT_TEST_DATABASE_URL`) | nạp bằng fixture `tests/test_db.py::seeded_db` (`init_db.py --reset` từ CSV hash `0E677EAA…D542` + số MẪU đại lý/giá); `check_data.py --out-dir <scratchpad>` với `DATABASE_URL` = URL kiểm thử | báo cáo "nguồn postgresql"; **0 lỗi**, 1896 cảnh báo, 2 ghi chú; `load_norms()` 68 dòng, TRAT đúng 4 khóa trên |
| DB vận hành (`DATABASE_URL` trong `.env`) | **không nạp, không sửa trong các lượt review này** | Mốc truy vấn chỉ đọc ở review V2 trước đây thấy khóa cũ `15`, `20`; chưa truy vấn xác nhận lại hiện trạng. Nếu DB vẫn giữ khóa cũ, mã J05c sẽ báo thiếu cho dòng trát vốn có đủ nền/dày. Không khẳng định DB thật đã đồng bộ hoặc vẫn nguyên trạng chỉ từ mốc cũ |

Bài kiểm đường DB thêm vào `tests/test_db.py::test_rules_and_families_from_db`: sau khi loader DB khớp CSV, khẳng định đúng 4 khóa TRAT mới (bị bỏ qua khi không có DB kiểm thử).

### Test bổ sung (`tests/test_rough_plaster.py`, nay 19 ca)

- Phương án tồn tại nhưng vật liệu chính trống họ (thay họ GN02 trong bản sao danh mục): thiếu, lý do "chưa rõ", không vữa trung gian.
- TRAT `quantity=None` trên nền hợp lệ (W-GN02-220): XM01, CA02 trống số, `complete=False`; vữa trung gian `(None, False)`.
- Lần chạy: `pytest tests/test_rough_plaster.py tests/test_db.py::test_rules_and_families_from_db` → **20 passed** (có DB kiểm thử).

### Đính chính phạm vi lý do thiếu

Lý do thiếu triển khai chỉ nêu dày và họ nền ("định mức TRAT cho chiều dày 15 mm trên nền AAC"), **không** nêu nhóm AK.213-216 như bảng ca ở mục 4 dự kiến. Giữ như vậy để không đưa danh sách mã/bảng vào Python; nhóm AK.213-216 cho gạch không nung ghi ở mục 1 tài liệu này.

### Hướng dẫn phát hành / rollback cho phiên tích hợp

**Chỉ là kế hoạch, chưa thực thi.** Triển khai sau đường cơ sở C01 và sau khi điều phối cấp lượt; DB vận hành cần chủ đồ án cho phép phạm vi nạp cụ thể. J05c không cần đổi schema; không gộp raw_class/J05b/J05d vào lượt này.

Mã J05c và dữ liệu khóa mới phải đi **cùng một lần phát hành**: mã mới + DB khóa cũ không tìm được `<dày>/<family>`; mã cũ + DB khóa mới không tìm được khóa dày thuần. Trước phát hành phải khóa snapshot mã/CSV/SQL và dữ liệu thực tế của môi trường đích. Git HEAD hoặc bản SQL cũ không tự chứng minh nội dung DB trước nạp.

Chọn rõ một trong hai đường, review phạm vi và rollback trước khi chạy:

| Đường dự kiến | Phạm vi tác động và điều kiện | Backup / rollback tương ứng |
|---|---|---|
| Nạp cả sáu bảng quy tắc | `init_db.py --reload-rules` xóa/nạp `material_rules`, `room_rules`, `rough_norms`, `material_notes`, `drawing_concepts`, `convention_clauses`; script còn có bước tạo bảng/nạp các bảng đang trống. `sql/05_rules.sql` cũng nạp sáu bảng, có BEGIN/COMMIT; hai cách không tương đương mọi tác dụng phụ. Phải review toàn bộ dữ liệu/phạm vi được phép trước khi chọn | Sao lưu và có cách khôi phục **đủ sáu bảng** từ môi trường đích, cùng snapshot mã/dữ liệu phát hành và các tác động khác đã được phép. Không chỉ sao lưu/restore rough_norms. Không coi việc xóa rồi nạp của script là một transaction nguyên tử cho toàn bộ thao tác |
| Chỉ nạp rough_norms | Cần kế hoạch thao tác giới hạn đúng bảng, transaction và kiểm điều kiện trước/sau được review riêng. Chưa có script mới hoặc quyền thực thi ở đây; không chạy toàn `--reload-rules` hoặc toàn `05_rules.sql` rồi gọi đó là nạp riêng | Sao lưu rough_norms thực tế và snapshot mã/CSV tương ứng; rollback đúng bảng trong phạm vi đã review, không tác động năm bảng còn lại |

Sau nạp được phép, cần khởi động lại các tiến trình ứng dụng hoặc dùng cơ chế xóa cache phù hợp đã được review: `load_norms()` có cache, đổi DB không tự làm worker đang chạy đọc số mới. Kiểm nguồn/khóa và kết quả tính trong tiến trình mới hoặc đã refresh cache, không chỉ kiểm bằng truy vấn SQL.

Cổng kiểm sau phát hành dự kiến: đúng bốn khóa TRAT và số theo bảng trên, `check_data` đúng nguồn/phiên bản với báo cáo thư mục riêng, ca GN01/GN02 qua ứng dụng/API/BOQ cùng số và phần thiếu. Test/DB kiểm thử/full suite chỉ chạy khi điều phối cấp lượt; ca build không thay xác nhận nghiệp vụ D02.

Nếu rollback: hoàn tác **phần diff J05c** từ snapshot phát hành cùng dữ liệu của đường đã chọn, bảo toàn thay đổi của phiên khác; không checkout/reset cả file hoặc nạp CSV cũ không rõ phiên bản. Restart/refresh cache và kiểm lại với cặp mã/dữ liệu đã rollback. Chưa chạy bất kỳ bước backup, nạp, rollback hoặc kiểm DB nào trong lượt sửa tài liệu này.

### Toàn bộ pytest

Chưa có kết quả toàn suite mới được xác nhận trong mục 9. Các kết quả ở mục 8 là bằng chứng lịch sử, không phải lần kiểm của lượt sửa tài liệu này. Chỉ chạy lại khi điều phối cấp lượt sau C01; không tự chạy song song hoặc dùng kết quả bài lẻ để tuyên bố toàn suite đạt.

### Bổ sung của Claude (03/11/2026, sau lượt sửa tài liệu ở trên)

**Toàn suite đã chạy một lần**, 16:14-16:25, `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -rfEs`, có `OPTIMAT_TEST_DATABASE_URL`: **397 passed, 3 xfailed, 0 failed, 0 skipped** (680 s). Lượt chạy được phối hợp trực tiếp với phiên M01/D02: phiên đó báo đã xong pytest của mình lúc 16:01 và xác nhận không chạy pytest/không dùng DB kiểm thử trong lúc J05c chạy. Đây **không** phải lượt do phiên điều phối C01 cấp; nếu Codex yêu cầu đúng quy trình C01 thì cần chạy lại. Workspace lúc chạy: 156 mục trong `git status --short` (nhiều phiên chưa commit). Bài `test_drawing_io[nha_huong_hai_duong_7x12_kien_truc.dxf]` đạt trong lần này; lỗi `IndexError` của mục 8 không tái hiện, không sửa `encoding.py`.

**Diff `rough_norms` trong `sql/05_rules.sql`** (so bản sao trước khi sinh, theo `work_code variant`):

| Thay đổi | Dòng |
|---|---|
| bỏ | `TRAT 15`, `TRAT 20`, `COP_PHA` variant trống CP01 "nhập tay" (1) |
| thêm do J05c | `TRAT 15/CLAY_SOLID`, `15/CLAY_HOLLOW`, `20/CLAY_SOLID`, `20/CLAY_HOLLOW` (4) |
| thêm ngoài J05c | `COP_PHA GO_<cấu kiện>` cho MONG, COT, DAM, GIANG_TUONG, SAN, MAI, LANH_TO, SE_NO (4 dòng mỗi loại) và CAU_THANG (3): 35; `COP_PHA VAN_EP` CP01 trống số (1) |

Tổng: −3, +40 = +37. **Đính chính:** các dòng cấp phối `BE_TONG_TRON` M150/M350/M400 **không** nằm trong diff (đã có trong SQL trước); câu "cấp phối M150/M350/M400" ở đầu mục 9 là sai của Claude. Phần ngoài J05c là định mức cốp pha gỗ AF.81 và dòng ván ép, cần review riêng trước phát hành như đoạn trên đã nêu.
