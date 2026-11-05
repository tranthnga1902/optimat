# J05d - Phụ gia cấp phối M350/M400: hợp đồng dữ liệu

Ngày: 03/11/2026. **Chờ Codex review, chưa triển khai.** Quyền ghi đợt này: chỉ tệp này. Không chọn sản phẩm/liều thay thiết kế.

## 1. Kiểm nguồn

| Bản | Cách kiểm | SHA-256 |
|---|---|---|
| **N7** [Phụ lục VII chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/38.2026.tt-bxd-pl7dmdtvatlieu_signed1.pdf), 180 trang | tải qua WebFetch (bản tạm trong thư mục kết quả công cụ của phiên, không vào repo), render PDF 4 và 15 bằng pypdfium2, xem trực quan | `DE6C99F53053ABF453B1DCF20E4790F92B3D79F5CD22E621FE2DDFE0FB6672D4` |
| **S7** `data/van_ban/PL7-TT-38.pdf`, 180 trang | render cùng hai trang, xem trực quan | theo J04: `8BA969A2…D52D` (không tính lại) |

Không kiểm chữ ký số, không đối chiếu toàn văn N7-S7.

**N7 PDF 4 / in 3, mục I "Định mức cấp phối vật liệu vữa bê tông":**
- Mục 1: số lượng vật liệu trong định mức **chưa tính hao hụt** vận chuyển, bảo quản, thi công.
- Mục 4: khi lập dự toán, lượng phụ gia tính theo: dẻo hóa giảm nước 5-10%, liều 0,5-0,8% khối lượng xi măng; siêu dẻo 12-20%, 0,5-1,0%; poly (polycarboxylate) 21-30%, 0,5-1,5%.
- Mục 5: thi công phải thí nghiệm xác định cấp phối (xi măng, cát, đá, phụ gia, nước) theo điều kiện thực tế.
- Trong hai trang đã đọc, khác thấy được: mục 2 của S7 có thêm "theo TCVN 5574:2012"; N7 không có. Không ảnh hưởng phụ gia. Chưa đối chiếu các trang khác.

**N7 PDF 15 / in 14, bảng 11.12300 độ sụt 6-8 cm, đá Dmax 20 mm [(40-70)% cỡ 0,5×1; (60-30)% cỡ 1×2]**, cho 1 m³ vữa bê tông:

| Mã | Mác | Xi măng kg | Cát vàng m³ | Đá dăm m³ | Nước lít | Phụ gia |
|---|---|---:|---:|---:|---:|---|
| 11.12325 | 350 | 385 | 0,487 | 0,795 | 185 | dẻo hóa |
| 11.12326 | 400 | 426 | 0,478 | 0,779 | 185 | dẻo hóa |

S7 trang 15 khớp từng số với N7. Cột "phụ gia" chỉ ghi loại, không ghi liều. Xi măng/cốt liệu/độ sụt trong CSV đúng biến thể này (PC40/PCB40, Dmax 20, độ sụt 6-8). Dmax 10 hoặc 40 có số khác (vd 11.12345 M350: 364 kg): "M350" một mình chưa đủ xác định cấp phối.

Chú ý cho reviewer: mục 1 nói định mức cấp phối chưa gồm hao hụt; CSV dùng × 1,025 m³ vữa / m³ kết cấu (PL II) và `materials.py` đánh dấu `waste_included=True` cho mọi dòng có `norm_code`. Căn cứ 1,025 theo từng công tác vẫn là giới hạn mở của J04, không xử lý ở đây.

## 2. Hiện trạng và chỗ mất phần thiếu

- `materials.py::_Bill.concrete`, trộn tại chỗ: `norms_for(MIX, grade)` → mỗi dòng CSV một `norm_line`. M350/M400 có ba dòng XM02/CA01/DA01 (385/426 × 1,025 = 394,625/436,65 kg). **Không có dòng phụ gia, không có dòng nước** → đầu ra ba vật liệu đủ số, `complete=True`, trạng thái theo công tác. Phần phụ gia chỉ nằm trong `note` của CSV: người đọc BOQ không thấy thiếu.
- Thương phẩm (`ready_mix`): giữ m³ bê tông theo mác (`ready_mix_material`), không tách vật liệu → không cộng phụ gia. Đúng, giữ nguyên.
- `Norm.value` lấy giữa khoảng khi chỉ có `qty_min/qty_max` (`norms.py`). Nếu đưa 0,5-0,8% vào CSV sẽ sinh lượng 0,65% như lượng mua. **Không làm.**
- Danh mục: PG01 "Phụ gia bê tông (dẻo, chống thấm, đông cứng nhanh)", đơn vị lít, không có khối lượng riêng/liều/sản phẩm; PG02 phụ gia kết nối (Sika Latex) không phải dẻo hóa.

## 3. Đề xuất giai đoạn 1: giữ dòng thiếu có nguồn (không cần trường mới)

Thêm vào `data/rules/dinh_muc_phan_tho.csv` một dòng cho mỗi mác, **không có qty, qty_min, qty_max, material_id**:

```csv
BE_TONG_TRON,M350,,Phụ gia dẻo hóa (cấp phối 11.12325),,kg / m³,,,,,11.12325,TT 38/2026/TT-BXD Phụ lục VII (datafiles.chinhphu.vn),"Bảng ghi phụ gia dẻo hóa, không ghi liều; hướng dẫn mục 4: 0,5–0,8% khối lượng xi măng khi lập dự toán. Chưa có sản phẩm và liều thiết kế: không tính lượng"
BE_TONG_TRON,M400,,Phụ gia dẻo hóa (cấp phối 11.12326),,kg / m³,,,,,11.12326,TT 38/2026/TT-BXD Phụ lục VII (datafiles.chinhphu.vn),"như trên, cấp phối 11.12326"
```

**Bản 2 (sửa theo [Codex review vòng 1](../review/J05BCD_CODEX_REVIEW_V1.md) mục 1, 4):** tên dòng đổi thành "Phụ gia dẻo hóa (cấp phối 11.12325) - chưa có sản phẩm, liều thiết kế" để lý do riêng hiện ngay trên đầu ra (tên là chữ hiển thị, không dùng để khớp phân loại).

Luồng hiện có xử lý: `norm_line` → `value is None` → dòng vật liệu `quantity=None`, `complete=False`, D; ba dòng XM02/CA01/DA01 giữ số (khóa dòng khác nhau, không bị kéo thành D). `boq.export_for_optimizer` đưa dòng vào `missing`.

**Thông báo (review mục 4):** câu chung theo bản chất, không nói "liều" cho mọi dòng:

```diff
-        miss = [] if value is not None else [f"{label} (chưa tra TT 38/2026)"]
+        why = f"đã có nguồn {n.norm_code}; chưa xác định lượng/điều kiện áp dụng" if n.norm_code else "chưa tra TT 38/2026"
+        miss = [] if value is not None else [f"{label} ({why})"]
```

Dòng trống không nguồn (vd CAN_NEN 50) giữ "chưa tra TT 38/2026". Lý do riêng phụ gia nằm ở tên dòng (hiển thị ở API, BOQ, `missing` của optimizer). Không thực thi nội dung `note`, không đổi `Norm.value`.

**Phân loại (review mục 1):** dòng không mã tên "Phụ gia…" hiện rơi vào `khac` qua `RAW_CLASS_BY_NAME` → bị lọc mất khi người dùng chọn `phu_gia`. Đề xuất cột tùy chọn `raw_class` trên `rough_norms` (CSV + DB), dòng này ghi `phu_gia`; chi tiết, migration, rollback và check_data ở [J05b bản 2 mục 5 (A)](J05B_VAN_EP_THIET_KE.md). Không gán mọi dòng của công tác bê tông thành `phu_gia`. Cần chủ đồ án duyệt lược đồ trước tích hợp.

Ca thêm khi tích hợp: `compute_rough` với `material_classes=["phu_gia"]` giữ dòng phụ gia (D) và đưa vào optimizer `missing`; `["xi_mang"]` giữ XM02, loại dòng phụ gia; không chọn lọc thì cả bốn dòng có mặt.

`check_data` (`_check_rough_norms`, đã đọc mã, chưa chạy): dòng trống `qty` không bị báo lỗi, chỉ được đếm vào cảnh báo "còn trống" chung. Không đổi `Norm.value`. Riêng hai dòng CSV và thông báo không cần đổi lược đồ; phần phân loại bên dưới (cột `raw_class`) **có** đổi lược đồ `rough_norms` và chờ chủ đồ án duyệt.

## 4. Hợp đồng đầu vào giai đoạn 2 (khi có liều thiết kế) - chưa duyệt, chưa làm

**Bản 2 định nghĩa rõ** (review: tên, kiểu, cardinality, đơn vị):

```python
class AdmixtureDose(BaseModel):            # một mác một dòng; trùng mác thì từ chối
    grade: str                             # khớp variant BE_TONG_TRON (M350)
    mix_code: str                          # khớp norm_code của dòng cấp phối (11.12325); lệch: từ chối, giữ dòng thiếu
    kind: Literal["deo_hoa", "sieu_deo", "poly"]   # khớp cột phụ gia của cấp phối; lệch: từ chối
    material_id: str                       # mã sản phẩm trong danh mục, đơn vị kg hoặc lít
    dose_fraction: float                   # phân số khối lượng xi măng: 0,6% ghi 0.006; hữu hạn, 0 < x < 1
    density_kg_l: float | None = None      # > 0; bắt buộc khi đơn vị sản phẩm là lít
    source: str                            # thiết kế / phiếu thí nghiệm cấp phối, không rỗng
    confirmed_on: date
ProjectParams.admixtures: list[AdmixtureDose] = []
```

Không dùng khoảng 0,5-0,8% làm giới hạn cứng của `dose_fraction` (TT 38 là số tham khảo lập dự toán, liều thiết kế theo sản phẩm). Khi có dòng hợp lệ cho mác: tính dòng sản phẩm và **bỏ** dòng thiếu giai đoạn 1 của mác đó; không hợp lệ: giữ dòng thiếu + lý do từ chối.

Người xác nhận và nguồn mật độ, nếu Codex cần trước khi trình duyệt sau: thêm `confirmed_by: str` (người/đơn vị xác nhận liều) và `density_source: str | None` (TDS của sản phẩm, bắt buộc khi có `density_kg_l`).

**Bảng bản 1 dưới đây ĐÃ BỊ THAY bởi khối `AdmixtureDose` ở trên; không dùng để triển khai** (`dose_pct_cement` → `dose_fraction` dạng phân số; `confirmed_by` → `confirmed_by` + `confirmed_on`). Giữ chỉ để truy vết:

Liều là của công trình, không phải định mức chung → không vào `dinh_muc_phan_tho.csv`. Đề xuất một trường tùy chọn trên `ProjectParams` (chưa thêm):

| Trường | Bắt buộc để tính | Ghi chú |
|---|---|---|
| `grade` | có | mác áp dụng (M350, M400) |
| `mix_code` | có | cấp phối đang dùng (11.12325); khác CSV thì không tính, báo lệch |
| `kind` | có | `deo_hoa` \| `sieu_deo` \| `poly`; phải khớp cột phụ gia của cấp phối, không thay loại |
| `material_id` | có | mã sản phẩm cụ thể trong `materials_master.xlsx` (thêm mới khi có TDS); không đổi tên/đơn vị PG01 |
| `dose_pct_cement` | có | một số, không khoảng |
| `density_kg_l` | khi đơn vị mua là lít | của đúng sản phẩm, có nguồn TDS |
| `source`, `confirmed_by` | có | thiết kế/thí nghiệm cấp phối; thiếu thì không tính |

Tính: kg/m³ kết cấu = kg xi măng/m³ kết cấu của dòng CSV cùng mác (đã × 1,025) × liều. Không nhân 1,025 lần nữa. Lít = kg / `density_kg_l`; thiếu thì dòng lít trống + lý do, không dùng 1 kg = 1 L. Trạng thái C (thông số người dùng), có `norm_code` không nâng A. Ưu tiên: liều xác nhận thắng dòng thiếu giai đoạn 1; không có thì giữ thiếu. Không yêu cầu người dùng chọn số giữa khoảng để BOQ hết trống.

Cấp phối thí nghiệm thay toàn bộ xi măng/cát/đá/nước là việc khác (thay dòng CSV theo công trình), ngoài J05d.

DB: giai đoạn 2 là trường JSON trong `ProjectParams` (đã lưu cùng `takeoff_results`), không cần bảng mới. Sản phẩm mới đi đường XLSX → `build_materials_sql.py` → `sql/03`.

## 5. Ca nghiệm thu đề xuất

Kiểm số học tham khảo (không phải lượng mua):

| Mác | Xi măng kg/m³ vữa | Phụ gia kg/m³ vữa 0,5-0,8% | kg/m³ kết cấu (× 1,025 một lần) |
|---|---:|---:|---:|
| M350 | 385 | 1,925-3,080 | 1,973125-3,157000 |
| M400 | 426 | 2,130-3,408 | 2,183250-3,493200 |

Test (SYNTHETIC, ghi rõ khi dùng số liều/kg-L giả):

| # | Đầu vào | Kỳ vọng |
|---|---|---|
| 1 | trộn tại chỗ M350 10 m³, giai đoạn 1 | XM02 3946,25 kg; CA01 4,992 m³; DA01 8,149 m³ có số; dòng phụ gia `quantity=None`, `complete=False`, lý do nêu 11.12325 và thiếu liều |
| 2 | như 1, M400 | XM02 4366,5 kg; dòng phụ gia thiếu |
| 3 | M250 | không có dòng phụ gia (cấp phối không ghi) |
| 4 | thương phẩm M350 | chỉ dòng bê tông thương phẩm; không dòng phụ gia, không XM02 |
| 5 | (giai đoạn 2) liều SYNTHETIC 0,6%, sản phẩm kg | 10 m³ M350 → 3946,25 × 0,006 = 23,6775 kg |
| 6 | (gđ 2) sản phẩm lít, thiếu kg/L | dòng lít trống + lý do |
| 7 | (gđ 2) kg/L SYNTHETIC 1,2 | 23,6775 / 1,2 = 19,73125 L |
| 8 | (gđ 2) `kind = sieu_deo` cho 11.12325 | từ chối, lý do lệch loại |
| 9 | trừ âm −2 m³ M350 | ba vật liệu trừ đúng phần góp; dòng phụ gia vẫn thiếu (giai đoạn 1), không ra số âm |
| 10 | dòng khoảng không được đưa vào `qty_min/qty_max` | test dữ liệu: dòng BE_TONG_TRON phụ gia không có khoảng (chặn midpoint) |
| 11 | nguồn nhập tay (gđ 2) | trạng thái C |

## 6. Giới hạn và dữ liệu cần thu

- **Nước**: cấp phối ghi 185 L/m³ vữa; CSV chưa có dòng nước. Có xuất nước là vật tư hay không: đối chiếu D02/M01, không tự thêm.
- Ghi chú "giảm nước 5-10%" không áp lên cấp phối đã có.
- Cần từ thiết kế/người dùng: cấp phối xác nhận (mã, biến thể xi măng/Dmax/độ sụt), cách cấp bê tông theo cấu kiện, loại và sản phẩm phụ gia, liều, TDS, kg/L nếu mua lít, quy cách đóng gói. TDS tìm được trên web chỉ là ứng viên chờ thiết kế chọn.
- Chờ D02 có dòng phụ gia/bê tông trộn được người kiểm xác nhận trước khi áp hồ sơ hay đo chỉ tiêu (hiện 0 dòng).
- Không tự sửa cơ chế known_part tổng quát (Q02).

## 7. Bàn giao

- Tạo duy nhất tệp này. Không sửa mã, CSV/XLSX/SQL/DB, D02, J04, CLAUDE.md, SPRINTS.md, NHAT_KY.md. Bản N7 tải tạm không lưu vào `data/van_ban`.
- Đã kiểm: N7 và S7 PDF 4, 15 bằng ảnh; `materials.py::concrete/norm_line`, `norms.py::Norm.value`, CSV BE_TONG_TRON, PG01/PG02.
- Chưa chạy pytest/check_data. Ca số tính tay.
- **Chờ Codex review, chưa triển khai.**
- Bản 2 (03/11/2026): sửa thông báo, tên dòng, phân loại theo review vòng 1; định nghĩa lại hợp đồng giai đoạn 2; rút câu "khác duy nhất". Chỉ sửa tệp này, không đổi mã J05d.
