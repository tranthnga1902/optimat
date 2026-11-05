# J05b - Ván ép AF.83: thiết kế (bản 2)

Ngày: 03/11/2026. **Bản 2 sửa theo [Codex review vòng 1](../review/J05BCD_CODEX_REVIEW_V1.md) mục 1-4; chờ Codex chốt. Chưa sửa mã/dữ liệu.**
Quyền ghi: chỉ tệp này (J05c đang giữ mã dùng chung). Không đánh J05b/J04 hoàn tất.

## 1. Nguồn (giữ từ bản 1)

[N2 PDF 455-457 / in 454-456](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl2dmdtxaydung_signed1.pdf#page=455), đã render và xem ảnh. AF.83000 "Ván khuôn bằng ván ép công nghiệp có khung xương, cột chống bằng hệ giáo ống", đơn vị 100 m².

| Bảng | Cấu kiện | Ván công nghiệp m² | Khung xương nhôm kg | Cột chống thép ống kg | Vật liệu khác |
|---|---|---:|---:|---:|---|
| AF.83100 | sàn mái | 21,00 | 12,00 | 36,15 | 5 % |
| AF.83200 | tường | 13,13 | 12,65 | 38,13 | 5 % |
| AF.83300 | xà dầm, giằng | 21,00 | 15,05 | 39,61 | 5 % |
| AF.83400 | cột vuông, chữ nhật | 13,13 | 13,73 | 38,13 | 5 % |

**Chiều cao:** trong miền ba cột đã tra (≤28, ≤100, ≤200 m), ba hao phí vật liệu của mỗi bảng bằng nhau; chỉ nhân công/máy khác. Không suy cho miền ngoài bảng. Ghi `norm_code` mã nhóm (AF.83300…) kèm ghi chú "ba cột chiều cao ≤28/≤100/≤200 m cùng hao phí vật liệu"; không ghi mã cột AF.83x11 khi chưa có chiều cao có nguồn. Chiều cao không là điều kiện ra số vật tư.

**Luân chuyển:** trang AF.83 không nêu số lần luân chuyển hay việc số đã gồm luân chuyển. Bản 1 suy "21/100 nghĩa là tấm dùng nhiều lần": **rút lại**. Chưa đọc thuyết minh chung chương AF về ván khuôn; không khẳng định cơ sở luân chuyển. Đầu ra chỉ ghi "hao phí định mức AF.83, không phải lượng mua/thuê ban đầu".

## 2. Lựa chọn hệ (sửa review mục 2)

Hiện `ProjectParams.formwork_type: Literal["go", "van_ep"]`. `van_ep` chỉ nói tấm ván, không chứng minh khung nhôm + chống thép ống.

**Đề xuất nhỏ nhất:** thêm một giá trị, không thêm trường.

```python
formwork_type: Optional[Literal["go", "van_ep", "van_ep_af83"]] = None
#   van_ep      = ván ép, chưa xác định hệ khung/chống: vật liệu cốp pha để trống (như hiện nay)
#   van_ep_af83 = ván ép công nghiệp + khung xương nhôm + cột chống thép ống (TT 38 AF.83), người dùng xác nhận (C)
```

- Tương thích: API/kết quả lưu (`takeoff_results`) có `van_ep` giữ nghĩa cũ và vẫn ra thiếu; không tự nâng thành AF.83. Literal mở rộng không làm hỏng JSON cũ.
- Trạng thái: thêm đầu vào "hệ ván khuôn: C (người dùng chọn AF.83)" trong `status.py::_inputs` cho COP_PHA, nên mọi dòng AF.83 tối đa C.
- UI `model.ts`: thêm lựa chọn "ván ép công nghiệp, khung nhôm, chống thép ống (AF.83)"; giữ "ván ép (chưa xác định hệ)".
- Hệ hỗn hợp theo cấu kiện: chưa mở.

## 3. Ma trận cấu kiện (sửa)

| `formwork_of` | Đề xuất với `van_ep_af83` |
|---|---|
| SAN | AF.83100 |
| DAM, GIANG_TUONG | AF.83300 |
| COT (mã chỉ tạo cột b×h) | AF.83400 |
| MAI | **không ánh xạ trong đợt này**: `RoofItem` không có trường phân biệt mái bằng/nghiêng (`area_m2` ghi "theo mặt nghiêng"), nên không chứng minh được mái bằng. Ra thiếu |
| MONG, CAU_THANG, LANH_TO, SE_NO | không có bảng AF.83 → thiếu |
| tường/vách | không có công tác → chưa hỗ trợ, không mở |

Thông báo thiếu cho cấu kiện không có bảng: "AF.83 không có bảng ván khuôn cho <cấu kiện>: chưa hỗ trợ vật liệu cốp pha hệ này". Không gợi ý đổi sang gỗ hay nhập tay.

## 4. Biểu diễn phần thiếu (sửa review mục 3)

Mỗi cấu kiện ánh xạ có **bốn** dòng định mức:

| Dòng | qty /m² (vd DAM) | `material_id` đợt này |
|---|---|---|
| Ván ép công nghiệp - hao phí AF.83 | 0,21 m² | trống (CP01 chờ quy cách) |
| Khung xương nhôm - hao phí AF.83 | 0,1505 kg | trống |
| Cột chống thép ống - hao phí AF.83 | 0,3961 kg | trống (CP04 là bộ) |
| Vật liệu khác, phụ kiện hệ AF.83 (5% chi phí vật liệu, chưa quy ra lượng) | trống | trống |

Dòng thứ tư luôn D (không có số) và còn lại sau khi ba dòng đầu được gắn mã sau này → BOQ/optimizer không bao giờ trình hệ là danh sách mua đầy đủ chỉ từ ba dòng chính. Không quy 5% thành kg/bộ, không chọn CP05. Thông báo của dòng trống có nguồn dùng câu chung của review mục 4 (xem J05d mục 3): "đã có nguồn AF.83300; chưa xác định lượng/điều kiện áp dụng".

## 5. Phân loại để không bị lọc mất (sửa review mục 1)

**Lỗi đã xác nhận trong mã:** `_Bill.result` cho dòng không có `material_id` dùng `RAW_CLASS_BY_NAME` (thép/gạch/bê tông/vữa, còn lại `khac`). "Ván ép…", "Khung xương nhôm…", "Vật liệu khác…" → `khac`; "Cột chống thép ống…" → `thep`. `compute_rough` lọc theo `material_classes`: chọn `cop_pha` thì cả bốn dòng biến mất; chọn `thep` thì chống thép ống lẫn vào thép cốt.

Hai cách, cả hai không đổi tên dòng, không bỏ bộ lọc:

**(A) Khuyến nghị, cần chủ đồ án duyệt lược đồ:** cột tùy chọn `raw_class` trên định mức.
- CSV `dinh_muc_phan_tho.csv` thêm cột `raw_class`; `Norm.raw_class: str | None`; bảng `rough_norms` thêm `raw_class String(32) NULL` (sửa `db/models.py`, sinh lại `sql/01`, `04`, `05`; `04_upgrade.sql` `ALTER TABLE rough_norms ADD COLUMN IF NOT EXISTS raw_class varchar(32)`; rollback `DROP COLUMN`).
- `check_data`: giá trị phải thuộc `RAW_CLASSES`; chỉ dùng khi `material_id` trống (có mã thì danh mục thắng, báo cảnh báo nếu lệch).
- `_Bill.add` nhận `raw_class` gợi ý, lưu vào dòng khi dòng chưa có mã; `result()` chỉ rơi về `RAW_CLASS_BY_NAME` khi không có gợi ý.
- Cùng cơ chế giải quyết J05d (phụ gia không có mã → `phu_gia`). Đây là lý do khuyến nghị (A) thay vì vá riêng.
- **Mâu thuẫn gợi ý (review vòng 2):** dòng không mã gộp theo khóa `name|unit`. Nếu hai phần góp cùng khóa mang `raw_class` khác nhau (hoặc một có, một NULL) thì `_Bill.add` ghi lý do thiếu "xung đột loại vật liệu: <a> / <b>" vào dòng (dòng thành D) và giữ loại của phần đầu tiên **chỉ để không mất dòng khi lọc**; không âm thầm chọn theo thứ tự. `check_data` cũng báo lỗi khi hai dòng CSV cùng `material_name` + đơn vị khác `raw_class`, để xung đột bị chặn ngay ở dữ liệu.
- NULL ở dữ liệu cũ: hành vi y như hiện nay (`RAW_CLASS_BY_NAME`).
- **Phát hành / rollback đi cặp:** migration chỉ thêm cột NULL (`04_upgrade.sql`); thứ tự lên: ALTER → mã đọc cột → CSV có cột → `--reload-rules`. Rollback: hoàn mã + CSV trước, rồi mới `DROP COLUMN`; nếu DROP trước, `read_rule_table` vẫn đọc được (SELECT *), nhưng mã mới mong cột sẽ nhận chuỗi rỗng → ghi rõ trong kế hoạch phát hành để không để mã đọc cột không tồn tại.
- Kiểm: lọc `compute_rough(material_classes=[...])` và `export_for_optimizer()["missing"]`, trên cả CSV và DB kiểm thử (mở rộng `tests/test_db.py::test_rules_and_families_from_db`, đã có khung so loader DB = CSV).

**(B) Không đổi DB, chỉ cho J05b:** dòng không có mã sinh từ công tác COP_PHA lấy `cop_pha`. Đúng cho mọi dòng của công tác cốp pha (gỗ CP03, đinh CP06 trong danh mục cũng là `cop_pha`), nhưng không giải quyết J05d. Nếu chọn (B), J05d vẫn cần (A) hoặc một cách khác.

## 6. Bản vá đề xuất (chưa áp; tích hợp sau J05c)

```diff
--- materials.py, nhánh COP_PHA
-            rows = norms_for(w.code, f"GO_{w.formwork_of}" if kind == "GO" else kind, norms) if kind else []
+            # VAN_EP (hệ chưa xác định) không có dòng: thiếu như hiện nay; VAN_EP_AF83 theo cấu kiện
+            rows = norms_for(w.code, f"{kind}_{w.formwork_of}", norms) if kind in ("GO", "VAN_EP_AF83") else []
```

CSV: xóa `COP_PHA,VAN_EP,CP01` (để `van_ep` ra thiếu bằng thông điệp "định mức ván khuôn van_ep…: hệ khung/chống chưa xác định"), thêm 16 dòng `VAN_EP_AF83_{SAN,DAM,GIANG_TUONG,COT}`, cột `raw_class = cop_pha` nếu chọn (A).

## 7. Ca nghiệm thu (đề xuất)

| # | Đầu vào | Kỳ vọng |
|---|---|---|
| 1 | `van_ep_af83`, DAM 10 m² | 2,1 m²; 1,505 kg; 3,961 kg có số, `complete=False`; dòng "vật liệu khác" trống, D |
| 2 | COT 10 m² | 1,313 / 1,373 / 3,813 |
| 3 | SAN 10 m² + trừ âm −1 m² (`takeoff.py` đáy sàn trên dầm/cột) | 1,89 / 1,08 / 3,2535 |
| 4 | `van_ep` (cũ) | một dòng thiếu, lý do hệ chưa xác định; không có khung/chống |
| 5 | MAI, MONG, CAU_THANG, LANH_TO, SE_NO | thiếu, thông điệp không gợi ý đổi hệ |
| 6 | `compute_rough` + `material_classes=["cop_pha"]` | bốn dòng còn đủ, `raw_class == "cop_pha"`; vào `export_for_optimizer()["missing"]` |
| 7 | `material_classes=["thep"]` | chỉ thép cốt + dây buộc; chống thép ống không lẫn vào |
| 8 | `material_classes=["xi_mang","cat","da"]` | dòng cốp pha bị loại đúng phạm vi đã chọn |
| 9 | `go` | hồi quy: không đổi so với test hiện có |
| 10 | giả lập gắn CP01 cho dòng ván | dòng "vật liệu khác" vẫn D, `RoughResult.status` không lên trên D |
| 11 | `van_ep_af83` | đầu vào trạng thái có "hệ ván khuôn: C" |

## 8. Thông tin còn cần thu

| Mục | Ai |
|---|---|
| Duyệt (A) cột `raw_class` trên `rough_norms` hoặc chọn (B) | Codex + chủ đồ án (lược đồ DB) |
| Duyệt giá trị `van_ep_af83` | Codex |
| Quy cách ván để khớp CP01; mã khung nhôm và chống thép ống kg; kg/bộ nếu cần bộ; phụ kiện | người dùng / nhà cung cấp hệ |
| Thuyết minh chung chương AF về luân chuyển ván khuôn | tra tiếp nếu cần khẳng định |
| Cách phân biệt mái bằng BTCT để mở MAI | Codex (trường mới, đợt sau) |
| Dòng đáp án D02 liên quan đã người kiểm xác nhận | D02 |

## 9. Bàn giao

- Bản 2 chỉ sửa tệp này. Đã đọc lại `_Bill.result` (phân loại theo tên), `compute_rough` (lọc `material_classes`), `boq.export_for_optimizer` (`missing`), `RoofItem`, `RoughNorm`.
- Chưa chạy pytest cho J05b (không đổi mã J05b).
- **Chờ Codex review bản 2.**
