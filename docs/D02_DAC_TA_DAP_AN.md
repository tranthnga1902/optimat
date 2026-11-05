# D02 – Mẫu đáp án công tác và vật tư; bộ nháp hồ sơ build 46_nha_tan_binh

Ngày lập: 03/11/2026. Người lập: Claude (dev); Codex là BA/reviewer.
Trạng thái: **phần kỹ thuật (mẫu, bộ nháp, validator, test) đã sửa vòng 1 theo review Codex (mục 9), chờ review lại; phần xác nhận chờ dữ liệu**: chưa có người kiểm
chuyên môn xác nhận dòng nào. Không có dòng nào `da_kiem`, không có tên người kiểm. D02 **chưa hoàn tất phần dữ liệu thực** và
chưa khóa mẫu số. Căn cứ: [M01](M01_PHAM_VI_PHAN_THO.md) (PTxx, 5A/5B, H0–H6, K1–K7), [kế hoạch](KE_HOACH_NGHIEM_THU_PHAN_THO.md) D02, DL01–DL05.

Nguyên tắc đã giữ:
- Dự toán thật (ACTUAL) là **nguồn đối chứng**, chưa phải đáp án bóc tay độc lập. Không dùng kết quả `compute_rough` làm đáp án.
- File gốc (`46_nha_tan_binh.csv`, `46_vat_tu.csv`, `46_thong_so.json`, `cases.csv`) giữ nguyên; bộ nháp nằm ở thư mục riêng.
- Đáp án mô tả sự thật mong đợi; **không** gắn H1–H6 (đó là kết quả đối chiếu sau này, C01/V01).
- Không đọc/chạy banve1 (test); không chạy bản vẽ bộ 46 trong D02.

## 1. Vị trí và cách chạy lại

```
data/ground_truth/du_toan/d02/
  _mau/                       4 CSV chỉ có tiêu đề: mẫu dùng lại cho hồ sơ mới
  46_nha_tan_binh/            tên thư mục = cases.csv/ten
    khoa_nguon.csv            file nguồn + sha256 đã khóa
    so_hang_muc.csv           sổ hạng mục PT01–PT47 của hồ sơ
    dap_an_cong_tac.csv       đáp án công tác (dòng gốc + dòng con)
    dap_an_vat_tu.csv         đáp án vật tư
```

Kiểm: `optimat.data_check.check_answer_set(<thư mục>)`, được gọi trong `run_checks` (mục `dap_an_d02`) nên chạy cùng
`python scripts/check_data.py` (cần PostgreSQL cho phần danh mục). Không cần DB, chỉ kiểm bộ D02:

```powershell
$env:PYTHONPATH = "src"; python -c "from optimat.data_check import check_answer_set, D02_DIR; [print(f) for f in check_answer_set(D02_DIR / '46_nha_tan_binh')]"
pytest tests/test_ground_truth_d02.py
```

Hồ sơ mới: chép `_mau/` sang `d02/<ten>/`, khai báo `khoa_nguon.csv` (vai trò `du_toan_cong_tac` bắt buộc trùng `cases.csv/du_toan`).
`cases.csv`, `compare_estimate.py`, `evaluate_rough.py` **không đổi**: evaluator vẫn đọc file dự toán gốc; nối bộ D02 vào đánh giá là
việc của C01.

## 2. Cấu trúc dữ liệu

Chung: UTF-8, CSV có tiêu đề; số dùng dấu chấm thập phân; số trống = chưa có (không bao giờ ghi 0 thay); `;` ngăn nhiều id.
Trường số dùng để tính phải là số **hữu hạn**: `NaN`, `inf`, `-inf` bị coi là không phải số (lỗi) và không vào tổng.
Trạng thái kiểm `trang_thai_kiem`: `nhap` (Claude trích/đề xuất) · `cho_kiem` (đủ nguồn số học, chờ người kiểm) · `da_kiem`
(người kiểm xác nhận: bắt buộc `nguoi_kiem`, `ngay_kiem`, nguồn). Chỉ người kiểm được đổi sang `da_kiem`.

### 2.1 `khoa_nguon.csv`

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| `duong_dan` | có | từ gốc dự án |
| `vai_tro` | có | **đúng một** `du_toan_cong_tac` (trùng `cases.csv/du_toan`; thiếu, trùng hoặc không đọc được = lỗi, không bỏ qua đối chiếu số gốc); `du_toan_vat_tu` bắt buộc khi có dòng vật tư ghi `dong_vat_tu_goc` (tối đa một); `thong_so`, `ban_ve_*`, `du_toan_goc_xls` |
| `sha256`, `so_byte` | có | tính thật lúc khóa; đổi nội dung → lỗi |
| `trong_kho` | có | `co`: thiếu file là lỗi; `khong` (bản vẽ, file gốc không vào Git): thiếu là cảnh báo |
| `ngay_khoa`, `ghi_chu` | | hash chỉ chứng minh nội dung, không chứng minh nguồn đúng hay quyền dùng |

### 2.2 `so_hang_muc.csv` – sổ hạng mục theo hồ sơ

| Trường | Bắt buộc | Giá trị |
|---|---|---|
| `id` | có | ổn định, ví dụ `46-HM-PT15` |
| `cong_trinh_id` | có | = `cases.csv` |
| `vi_tri` | | tầng/vị trí; bộ 46 hiện ghi "toàn công trình" |
| `ma_pt` | có | PT01–PT47; **đủ 47 mã** (thiếu mã = lỗi: không phát hiện ≠ không có) |
| `ton_tai` | có | `co`, `khong`, `chua_ro`; `chua_ro` phải có `ly_do` |
| `nguon_ton_tai` | có | dòng dự toán, hình bản vẽ… |
| `pham_vi`, `ma_qd` | có | IN/OUT theo M01; OUT cần mã quyết định đặt OUT |
| `ly_do`, `trang_thai_kiem`, `nguoi_kiem`, `ngay_kiem` | | |

### 2.3 `dap_an_cong_tac.csv` – đáp án công tác

Một **dòng gốc** cho mỗi dòng dự toán (kể cả dòng hoàn thiện, dòng chưa có mã); **dòng con** khi diễn giải gốc có số từng phần.

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| `id` | có | dòng gốc `46-Cxx` (xx = stt), dòng con `46-Cxx.k` |
| `dong_goc` | có | `stt` trong file dự toán; dòng con cùng `dong_goc` với cha |
| `cha_id`, `quan_he_cha` | dòng con | một cấp; `phan` = một phần của số cha (được cộng kiểm tổng), `khia_canh` = cùng số nhưng khác phạm vi (vd. vật tư cọc IN / dịch vụ ép OUT) |
| `hang_muc_id`, `ma_pt` | | liên kết sổ hạng mục |
| `pham_vi` | có | `IN`, `OUT`, `chua_phan_loai`; `hon_hop` chỉ cho dòng gốc có dòng con khác phạm vi |
| `ma_qd` | OUT | mã M01 (QĐ-chung, QĐ-02, QĐ-11, QĐ-12, QĐ-13, QĐ-18 mới được đặt OUT) |
| `dem_mau_so` | có | `co`/`khong`/`cho_phan_loai`; suy được từ phạm vi, validator đối chiếu (mục 3) |
| `ma_cong_tac_goc` | | mã do `import_estimate.py` gắn sẵn, giữ nguyên |
| `ma_cong_tac` | | ánh xạ đề xuất (khóa `WORKS`); có thì `don_vi` phải bằng đơn vị của mã |
| `cau_kien`, `vi_tri`, `noi_dung`, `so_luong`, `kich_thuoc` | | |
| `cong_thuc` | | chuỗi trình bày, **không thực thi** |
| `khoi_luong` | có hoặc lý do | dòng gốc = đúng số gốc (đơn vị hệ thống); dòng con = số vế phải trong diễn giải (đổi 100 m² → m² chính xác) |
| `khoi_luong_tinh_lai` | | dòng gốc: tổng phần con; khác số gốc thì bắt buộc ghi (giữ chênh lệch) |
| `don_vi` | có (trừ OUT) | |
| `cong_tru` | | trống, `cong`, `tru`. Số âm chỉ hợp lệ ở dòng con `phan` có `cong_tru = tru` (phần trừ giao nhau, lỗ mở); `tru` mà số dương là lỗi; dòng gốc không âm |
| `phu_thuoc` | | id dòng mà số này phụ thuộc (thép hàm lượng → dòng bê tông) |
| `loai_nguon`, `nguon` | có | `du_toan`, `do_tay`, `tai_lieu_khac` + vị trí |
| `trang_thai_kiem`, `nguoi_kiem`, `ngay_kiem`, `can_kiem` | | `can_kiem`: câu hỏi/việc cho người kiểm |

### 2.4 `dap_an_vat_tu.csv` – đáp án vật tư

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| `id` | có | `46-Vxx` |
| `cong_tac_id` | | id công tác nguồn (nhiều id ngăn `;`) |
| `dong_vat_tu_goc` | | **số dòng file** của `46_vat_tu.csv` (stt lặp lại theo mục vật liệu/nhân công/máy); có thì `luong` = số gốc |
| `material_id` | | mã danh mục khi khớp; trống được |
| `ten_vat_tu`, `quy_cach` | có quy cách | giữ quy cách dù chưa có mã (vd. Thép tròn Ø ≤ 10 mm) |
| `don_vi_goc`, `don_vi` | | khác nhau chỉ khi đổi chính xác (tấn→kg ×1000, m3→m³, 100m²→m² ×100); viên/bao/tấn/m³ lẫn nhau là lỗi. Có `dong_vat_tu_goc` thì `don_vi_goc` phải bằng đơn vị dòng nguồn và `luong` được so với số nguồn **sau quy đổi** (vd. 0,102 tấn = 102 kg) |
| `luong` | có hoặc `thieu` | không âm, không 0 |
| `co_so_luong` | có | `lap_dat` (lượng lắp vào công trình) hoặc `mua`; **không gộp hai cơ sở** (`material_totals`) |
| `he_so`, `nguon_he_so` | | hệ số là số hữu hạn dương và phải có nguồn; hệ số chỉ đúng theo giả thuyết chưa kiểm thì không ghi vào `he_so` mà ghi ở `thieu` |
| `hao_hut` | có | `da_gom`, `chua_gom`, `chua_ro`; `lap_dat` không được `da_gom` |
| `dung_lam_dap_an` | có | `co`, `khong` (vd. tổng hợp lẫn hoàn thiện), `cho_kiem`; `khong` không được `da_kiem` |
| `loai_nguon`, `nguon`, `trang_thai_kiem`, `nguoi_kiem`, `ngay_kiem`, `thieu` | | |

## 3. Mẫu số và quan hệ cha–con

- Đơn vị mẫu số K1 = **dòng gốc** có `dem_mau_so = co` (`denominator_ids`). Dòng con luôn `khong`: tách dòng không làm tăng mẫu số.
- `dem_mau_so` của dòng gốc: có phần IN → `co`; không có IN nhưng có phần chưa phân loại → `cho_phan_loai`; toàn OUT → `khong`.
- Dòng `cho_phan_loai` **không bị loại ngầm**: mẫu số chỉ khóa được khi hết dòng này (V01). Dòng gốc gộp đạt H1 chỉ khi mọi phần IN đạt (M01 3.1 luật 4).
- Tổng các dòng con `phan` phải bằng số gốc (dung sai max(0,001; 1e-6·|số|)); lệch thì phải ghi `khoi_luong_tinh_lai` = tổng con (cảnh báo,
  người kiểm xác nhận) — không sửa số gốc. Không cộng dòng cha với dòng con.
- Không tách theo tỷ lệ: chỉ tách khi diễn giải gốc có số từng phần; không có thì giữ dòng gộp + `can_kiem`.

## 4. Bảng kiểm nguồn bộ 46 (hiện có / còn thiếu)

| Nhóm | Hiện có (đã khóa hash trong `khoa_nguon.csv`) | Còn thiếu |
|---|---|---|
| A. Hồ sơ | Mã `tan_binh_46`; phiên bản `chua_ro`; bản vẽ `tan_binh_kien_truc.dxf`, `tan_binh_ket_cau.dxf` (ngoài Git, có trên máy); dự toán gốc `Nha Tan Binh.xls` (ngoài Git); nguồn kenhxaydung.vn; quyền dùng `chua_ro` | Phiên bản hồ sơ; danh mục hình (tên hình, sheet) của mặt cắt, chi tiết móng/thang/mái/bể, bảng thép; quyền dùng |
| B. Đáp án công tác | 64 dòng dự toán + diễn giải (kích thước, số lượng, tầng ở dạng chuỗi) | Đo/kiểm độc lập trên bản vẽ; phần trừ giao nhau ghi rõ; người kiểm, ngày kiểm |
| C. Đáp án vật tư | Tổng hợp vật tư dự toán (gồm cả hoàn thiện, điện nước) | Định mức 1776 từng công tác để tách vật tư theo công tác; xác nhận lượng mua/lắp đặt; quy cách thép theo Ø thật |

## 5. Bộ 46: số liệu

| Chỉ số | Số | Quan hệ |
|---|---|---|
| Dòng dự toán gốc | 64 | = số dòng gốc trong `dap_an_cong_tac.csv` (validator kiểm đủ, không trùng) |
| Dòng con | 65 | 17 dòng gốc có tách (63 `phan`, 2 `khia_canh`); không vào mẫu số |
| Dòng gốc IN / hon_hop / OUT / chưa phân loại | 31 / 3 / 28 / 2 | 31 + 3 + 28 + 2 = 64 |
| Mẫu số dự kiến (`dem_mau_so = co`) | 34 | = 31 IN + 3 hon_hop (cọc, lanh tô gộp, trát cột gộp) |
| `cho_phan_loai` (dòng gốc) | 2 | trát gờ chỉ (36), quét nước xi măng (37); mẫu số còn 34–36 tùy phân loại |
| Dòng chưa phân loại (gốc + con) | 9 | 46-C12.3, C27.14, C35.1, C35.2, C35.4, C36, C37, C37.1, C37.2 |
| Đã ánh xạ mã công tác (dòng gốc) | 32 | 27 dòng gốc đã có mã từ `import_estimate.py`; đề xuất thêm XAY (29, 30), TRAT (31, 33, 34, 35); bỏ mã khỏi dòng 6 (đáy/nắp bể, cần kiểm) |
| Dòng gốc `cho_kiem` / `nhap` | 6 / 58 | `cho_kiem`: 2, 7, 13, 30, 31, 34 (công thức gốc đủ, số học khớp) |
| Dòng **đã kiểm thực sự** | **0** | không có người kiểm |
| Sổ hạng mục: IN có / IN chưa rõ / OUT có / OUT chưa rõ | 26 / 16 / 3 / 2 | 47 = PT01–PT47 |
| Vật tư: mua-cho_kiem / mua-không dùng / lắp đặt-cho_kiem | 14 / 6 / 4 | 24 dòng; vật tư hoàn thiện, điện nước, nhân công, máy không đưa vào |

Dòng gộp đã xử lý (yêu cầu bắt buộc):
- **Lanh tô (12)**: tên gồm mái hắt/máng nước/tấm đan/ô văng nhưng diễn giải chỉ có lanh tô 200 (1,296), lanh tô 100 (0,3), đan bếp (0,24 – chưa
  phân loại), đan bể tự hoại (0,588 – PT31). Ô văng/mái hắt/máng nước: **không có số** → sổ hạng mục PT27, PT29 `chua_ro`.
- **Xây kết cấu phức tạp (29)**: bậc thang xây trệt 0,4725 + lầu 2,1375 (PT20; diễn giải ghi "tam cấp" nhưng hình học là bậc tam giác — hỏi người
  kiểm), tam cấp vào nhà 0,54 (PT21), thành bể tự hoại 3,92 (PT31). Tổng 7,07 khớp.
- **BNN (30, 31)**: xây 2,816 m³, trát 28,16 m² → PT30 IN (QĐ-03); README cũ coi là ngoài phạm vi đã sửa ở D01.
- **Dòng 6 "bê tông móng" 1,878**: diễn giải là Đáy + Nắp (bể?) → IN, chưa gắn PTxx, bỏ mã MONG đề xuất, chờ người kiểm.
- **Trát (33–35)**: dầm (589,7, không diễn giải), trần (444,95), trụ cột gộp cầu thang 67 / lanh tô 28 / cột 239 / cạnh tường 30,62 → cột IN
  (QĐ-11), ba phần còn lại chưa phân loại (QĐ-11 chỉ nêu cột/dầm/trần).
- **Cọc (1, 4)**: dòng 1 = vật tư cọc 308 m (PT09 IN) và dịch vụ ép (OUT) là hai `khia_canh` cùng số; dòng 4 đập đầu cọc OUT (QĐ-02).
- **Thép (19–26)**: theo hàm lượng tấn/m³; `phu_thuoc` trỏ dòng bê tông; thể tích dùng trong diễn giải khác dòng bê tông (móng 14,12 vs
  14,112 + 1,878; cột 14,69 vs 17,092; dầm 44,66 vs 37,22; sàn 38,28 vs 47,855; thang 5,36 vs 5,85; lanh tô 1,59 vs 2,424). **Không phải đáp án
  thép độc lập.**

Lệch phát hiện khi tách (giữ nguyên số gốc, ghi `khoi_luong_tinh_lai`): **dòng 28** tổng 9 phần = 94,14 m³ khác số gốc 90,066 (đúng bằng phần
"Lầu 1" 4,074); dòng trát 32 dùng 94,14. Dòng 15 phần "Mái" dùng 4×11 trong khi dòng 9 dùng 4×10.

## 6. Ví dụ truy vết

1. **Công tác độc lập** – `46-C07`: `46_nha_tan_binh.csv` stt 7, AF.11213 → "1,2*1,2*0,7*14 = 14,112" m³ → PT06 (sổ `46-HM-PT06`), `MONG`,
   14 khối M1–M4, `cho_kiem`. Câu hỏi: M1–M4 có phải đài cọc (PT08) vì có 44 cọc?
2. **Dòng gộp nhiều hạng mục** – `46-C29` (7,07 m³, `dem_mau_so = co`, một mẫu số) → `.1` 0,4725 PT20, `.2` 2,1375 PT20, `.3` 0,54 PT21,
   `.4` 3,92 PT31; Σ = 7,07 = số gốc. Vật tư `46-V10` gạch thẻ 7.685,09 viên gắn cả `46-C29` (chưa tách theo phần: thiếu định mức).
3. **Công tác → định mức → vật tư, lắp đặt vs mua** – thép Ø ≤ 10: `46-C20` 0,7345 + `46-C22` 2,233 + `46-C24` 4,2108 tấn (theo hàm lượng,
   phụ thuộc `46-C08/C09/C10`) → `46-V21` **lắp đặt** 7.178,3 kg (tấn × 1000, `hao_hut = chua_gom`) → hệ số 1,005 (suy từ dự toán, cần đối chiếu
   AF.61 ĐM 1776) → `46-V19` **mua** 7.214,1915 kg (`46_vat_tu.csv` dòng 81, `da_gom`).
   Thép **Ø ≤ 18**: chỉ `46-C19/C21/C23` (nguồn ghi ≤ 18 mm) → `46-V22` lắp đặt 15.503,4 kg. `46-C25`, `46-C26` (cầu thang, lanh tô) nguồn chỉ ghi
   **Ø > 10 mm** → `46-V23` lắp đặt 1.570,8 kg, quy cách "chưa xác định nhóm chi tiết", **không** tự xếp vào ≤ 18. Dòng mua `46-V20` 17.415,684 kg
   (số nguồn, giữ nguyên) chỉ liên kết `46-C19/C21/C23`, không ghi `he_so`; ghi ở `thieu` giả thuyết chờ kiểm: nếu hai dòng > 10 mm thuộc
   nhóm ≤ 18 thì 17.415,684 = (15.503,4 + 1.570,8) × 1,02.
   Cọc: 308 m lắp đặt (`46-V24`) → ×1,01 → 311,08 m mua (`46-V08`). `material_totals` cộng riêng (quy cách, đơn vị, cơ sở).
4. **Cốp pha → gỗ ván** – Σ cốp pha `46-C13…C18` = 1.552,73 m² → hệ số 0,00792 m³/m² (suy) → `46-V12` gỗ ván 12,2976 m³ (mua).

## 7. Phiếu xác nhận cho người kiểm

Người kiểm (người có chuyên môn xây dựng, không phải Claude) điền **trực tiếp vào CSV** của `d02/46_nha_tan_binh/`:
`trang_thai_kiem = da_kiem`, `nguoi_kiem`, `ngay_kiem` (YYYY-MM-DD), và bổ sung vào `nguon` hình/sheet đã đối chiếu. Đo lại thì ghi
`loai_nguon = do_tay`, số mới vào `khoi_luong_tinh_lai` (giữ `khoi_luong` = số gốc) và phần trừ vào `cong_tru`. Sau đó chạy `check_answer_set`.

**A. Đủ nguồn số học, chỉ cần xác nhận** (`cho_kiem`): 46-C02 (đào), 46-C07 (móng M1–M4), 46-C13 (cốp pha móng), 46-C30, 46-C31 (BNN),
46-C34 (trát trần); các dòng con có số trong diễn giải và tổng khớp: C05, C08, C09, C10, C12, C14, C15, C16, C18, C27, C29, C32, C35, C37.

**B. Cần đo lại / đối chiếu bản vẽ** (vị trí):

| Dòng | Câu hỏi | Kiểm ở đâu |
|---|---|---|
| 46-C03 | Đắp đất 20 m³ không có diễn giải: tính từ đâu? | MB móng, mặt cắt móng, cốt tự nhiên |
| 46-C33 | Trát dầm 589,7 m² không có diễn giải | MB dầm các tầng |
| 46-C02 | Hệ số 0,9 và sâu 1,3 m | mặt cắt móng |
| 46-C06 | Đáy 2,6×2,6×0,15 + nắp 2,4×1,8×0,1×2 là của bể nào; có phải bê tông móng? | chi tiết bể nước ngầm/bể tự hoại |
| 46-C07, PT08 | M1–M4 là móng đơn hay đài cọc | chi tiết móng, MB cọc |
| 46-C01, 46-C04 | 44 cọc ép vs 42 đập đầu cọc; dài thiết kế 7 m? | MB cọc, bảng cọc |
| 46-C08 | Cao 7 + 13,3 m có gồm cổ cột (PT11)? cột "Tời" là gì? | mặt cắt, MB cột |
| 46-C09, 46-C15 | "Lầu 1-6" × 6 tầng với nhà trệt + 4 lầu + sân thượng; "Trệt" là đà kiềng? mái 4×10 hay 4×11 | MB dầm, mặt cắt |
| 46-C11 | Hệ số 1,3 của thang | chi tiết thang |
| 46-C28 | Lệch 90,066 vs 94,14 (phần Lầu 1) | MB tường lầu 1 |
| 46-C29.1–.2 | Là bậc thang xây (PT20) hay tam cấp | chi tiết thang |
| 46-C27.12 | Lan can trước 4,5 × 0,1 × 1 × 5: tường lan can xây (PT26)? | mặt đứng, sân thượng |
| PT14, PT15, PT27–PT29, PT36–PT38, PT10, PT24 | Có/không (sổ hạng mục `chua_ro`) | MB kết cấu, chi tiết |

**C. Thiếu thông số/định mức/quy cách**: thép 19–26 (thể tích khác dòng bê tông; cần bảng thống kê thép thật nếu có); vật tư V01, V09–V18
(định mức 1776 theo công tác); hệ số 1,005 / 1,01 / 0,00792 là **suy từ số dự toán**, cần tra định mức; 1,02 cho Ø ≤ 18 chỉ là giả thuyết (phụ thuộc nhóm của stt 25, 26), người kiểm xác nhận Ø thật của thép cầu thang/lanh tô; quy cách thép theo Ø thật
(dự toán chỉ chia ≤ 10, ≤ 18).

**D. Chưa phân loại IN/OUT (người kiểm/BA quyết)**: trát gờ chỉ (36); quét nước xi măng (37, QĐ-11: có phải lớp cấu tạo cần thiết?);
đan bếp (12.3); gối đỡ bàn bếp (27.14); trát cầu thang, lanh tô, cạnh tường (35.1, 35.2, 35.4).

## 8. Giới hạn

- Chưa có đáp án đo tay độc lập được người kiểm xác nhận: **không dùng bộ này để báo chỉ tiêu**; mẫu số chưa khóa.
- `vi_tri` mới ở mức "toàn công trình"/tầng trong chuỗi diễn giải; chưa tách theo tầng thành trường riêng.
- Hệ số vật tư suy từ số dự toán chỉ là kiểm tính nhất quán, không phải định mức có nguồn.
- Validator kiểm hợp đồng dữ liệu, không kiểm đúng sai nghiệp vụ; không tính KPI (C01/V01).

## 9. Phản hồi review Codex vòng 1

| # | Vấn đề | Đã sửa | Test |
|---|---|---|---|
| 1 | `khoa_nguon.csv` rỗng vẫn 0 lỗi; bỏ qua đối chiếu số gốc và kiểm kê | Bắt buộc đúng một `du_toan_cong_tac` (trùng manifest, đọc được); `du_toan_vat_tu` bắt buộc khi có `dong_vat_tu_goc`; đối chiếu chạy theo cờ nguồn đọc được, không theo dữ liệu có/không | `test_empty_or_missing_source_lock_is_blocked` (nguồn 999, tổng con 3) |
| 2 | `NaN` được nhận là số, `material_totals` ra `nan` | `_num_or_none` chỉ nhận số hữu hạn; số âm: chỉ dòng con phần trừ (`cong_tru = tru`); `luong` không âm; `he_so` dương | `test_non_finite_and_negative_numbers` |
| 3 | 0,102 tấn → 102 kg báo khác số gốc | So sau quy đổi chính xác (`EXACT_UNITS` có hệ số), dung sai làm tròn; `don_vi_goc` phải bằng đơn vị nguồn; dòng gốc công tác cũng so có dung sai | `test_exact_unit_conversion_compared_after_conversion` |
| 4 | `46-V22` gom thép chỉ biết Ø > 10 mm vào Ø ≤ 18 | Tách `46-V23` lắp đặt Ø > 10 mm (chưa xác định nhóm); `46-V22` chỉ C19/C21/C23 (15.503,4 kg); `46-V20` mua giữ số nguồn, bỏ hệ số, ghi giả thuyết ở `thieu` | `test_steel_only_known_above_10mm_not_assigned_to_le_18_group` |
