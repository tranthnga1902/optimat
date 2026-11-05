# C01 – Đường cơ sở phần thô trên hồ sơ build 46

Ngày lập: 03/11/2026. Người lập: Claude (dev); Codex là BA/reviewer. Trạng thái: **chờ Codex review**.

**Đây là báo cáo PHÁT TRIỂN / ĐỐI CHỨNG BUILD.** Nguồn đối chứng là dự toán thật đã chuẩn hóa ở D02 nhưng **chưa có người kiểm
xác nhận** (0 dòng `da_kiem`); mẫu số 34 chỉ là dự kiến. Mọi chênh lệch dưới đây **không phải độ chính xác nghiệm thu**, không
dùng để công bố chỉ tiêu, không có tỷ lệ hoàn tất 95%. Không chạy banve1 (test). Không sửa thuật toán, định mức, đáp án.

## 1. Chạy lại

```powershell
$env:OPTIMAT_NO_DOTENV = "1"; Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue   # danh mục CSV của kho (tái lập, có hash)
python scripts/c01_duong_co_so.py            # -> reports/c01_duong_co_so_build.xlsx (luôn ghi đè)
pytest tests/test_c01_duong_co_so.py
```

Có `DATABASE_URL` thì danh mục đọc từ PostgreSQL (chỉ đọc); sheet `Trang_thai` ghi `nguon_danh_muc`. Bộ 46 mất khoảng 1,5 phút.

## 2. Luồng dữ liệu

```
cases.csv ──select_cases("phat_trien")──► hồ sơ build ──check_answer_set──► bộ D02 không lỗi (cảnh báo giữ lại)
   │ loại test / thiếu D02 / D02 lỗi / tính lỗi ──────────────────────────────────────────────► Bo_qua
   ▼
evaluate_rough.rough_for_case (compute_rough) ──► works, materials, by_group, by_class, warnings
   │
D02 dap_an_cong_tac ──lá đáp án (mục 3)──► Doi_chieu_cong_tac (64 dòng gốc)
                         └─tổng theo khóa──► So_sanh_nhom ◄── tổng hệ thống theo khóa (như compare())
                                                └─ summarize() ──► Theo_trang_thai (A/B, C/D, không có số)
D02 dap_an_vat_tu ──────────────────────────► Vat_tu_nhom ◄── materials (cùng mã, cùng đại lượng)
materials, by_group, by_class ─────────────► He_thong_vat_tu
D02 can_kiem, cảnh báo validator, cảnh báo hệ thống ► Can_kiem;  sha256 mã/quy tắc/danh mục/dữ liệu ► Hash
```

Thay đổi mã: `scripts/evaluate_rough.py` tách `rough_for_case` khỏi `run_case` (hợp đồng `run_case` giữ nguyên); thêm
`scripts/c01_duong_co_so.py`, `tests/test_c01_duong_co_so.py`. Không đổi `compare()`, `data_check`, schema, DB.

## 3. Quy tắc ánh xạ và cơ sở tổng

- **Lá đáp án**: dòng gốc không tách, hoặc các dòng con `phan` của nó. Dòng con `khia_canh` (cọc) không phải lá. Không cộng cha với con.
- Lá chỉ vào phép so khi: `pham_vi = IN`, có số, có mã công tác, **PTxx thuộc phạm vi công tác hệ thống đang tính** (bảng `PT_WORK`
  trong script: PT01→DAO_DAT, PT02→DAP_DAT, PT04/PT05→BE_TONG_LOT, PT06→MONG, PT10/PT13→DAM, PT12→COT, PT14→GIANG_TUONG,
  PT16→LANH_TO, PT17→SAN, PT19→CAU_THANG, PT23→MAI, PT27→SE_NO, PT32→XAY, PT33→TRAT, PT35→CAN_NEN, PT36/PT37→CHONG_THAM; thép
  hàm lượng PT40 theo cấu kiện), đơn vị bằng đơn vị `WORKS`. Lá khác giữ ở cột `phan_khong_so` kèm lý do (OUT, chưa phân loại,
  PT chưa có công tác cùng phạm vi, chưa ánh xạ, thiếu số, khác đơn vị).
- **Khóa so** = khóa của `compare()`: mã công tác; cốp pha và thép thêm cấu kiện. Lá PT23 (mái) dưới dòng "sàn mái" vào nhóm
  `MAI` / `COP_PHA/MAI`, không vào `SAN`.
- Dòng gốc mà mọi phần đều vào cùng một nhóm: dùng **số gốc** của nguồn, không thay bằng tổng con (46 dòng 28: 90,066, không phải
  94,14). Dòng gốc chỉ vào được một phần: cộng số của các phần đủ điều kiện (số có sẵn trong nguồn), không chia tỷ lệ.
- **So ở mức nhóm**: một tổng hệ thống ↔ tổng các lá của nhóm, một lần. Dòng đáp án chỉ ghi nhóm của nó, không mang kết quả khớp riêng.
- Nhóm **so được** khi hai phía đều có, hệ thống có số và đủ (`complete`, không phần thiếu). Không so: ghi lý do; hệ thống có mà
  đối chứng không có = "thừa hoặc nguồn thiếu" (vẫn hiện). Đáp án 0: chỉ báo chênh tuyệt đối. Số trống giữ trống.
- Trạng thái đề xuất từng dòng gốc (không phải H1–H6 đã xác nhận): `ngoai_pham_vi`, `cho_phan_loai`, `chua_anh_xa`,
  `khong_cung_pham_vi_he_thong`, `he_thong_khong_co_dong`, `thieu_dau_vao`, `mot_phan` (có phần bị loại hoặc nhóm hệ thống chưa đủ),
  `co_ket_qua_chua_xac_nhan`. Có số **không** đồng nghĩa đủ.
- `Theo_trang_thai` tái dùng `evaluate_rough.summarize`: A/B, C/D, không có số tách riêng; chỉ nhóm so được có `lech_pct`.
- Nhóm mà số hệ thống dựa trên thông số nhập (`foundations`, `steel_kg_per_m3`) được ghi chú: bộ 46 lấy các thông số này **từ chính
  dự toán** (README du_toan), nên MONG, COP_PHA/MONG khớp 0,0% và thép theo hàm lượng **không chứng minh độ chính xác**.
- **Vật tư**: chỉ so dòng `mua`, `dung_lam_dap_an` ≠ `khong`, có `material_id` trùng vật tư hệ thống, cùng đại lượng sau đổi đơn vị
  chính xác, với `quantity_with_waste` của hệ thống khi dòng đó đủ. Lắp đặt, nhóm Ø chưa rõ (`46-V23`), tổng lẫn hoàn thiện: giữ dòng,
  ghi lý do. Không chia tổng xi măng/cát theo tỷ lệ. Nhóm/loại hệ thống (kg) ở `He_thong_vat_tu`, không so với m³/viên/tấn.

## 4. Kết quả bộ 46 (build, ACTUAL, D02 nháp, danh mục CSV)

### Bao phủ (`Bao_phu`, `Doi_chieu_cong_tac`)

| Số | Giá trị | Quan hệ |
|---|---|---|
| Dòng gốc / dòng con | 64 / 65 | như D02 |
| Phạm vi IN / hon_hop / OUT / chưa phân loại | 31 / 3 / 28 / 2 | = 64 |
| Mẫu số dự kiến | 34 | IN + hon_hop; **chưa khóa** (2 dòng chờ phân loại, 0 dòng đã kiểm) |
| Trạng thái đề xuất: có kết quả (chưa xác nhận) | 18 | |
| một phần / thiếu đầu vào / hệ thống không có dòng | 3 / 3 / 2 | 46-C10, C16, C27 / C12, C18, C26 / C02, C03 |
| không cùng phạm vi hệ thống / chưa ánh xạ | 6 / 2 | C29, C30, C31, C33, C34, C35 / C01 (cọc), C06 (đáy/nắp bể) |
| chờ phân loại / ngoài phạm vi | 2 / 28 | C36, C37 / OUT |
| Tổng | 64 | 18 + 3 + 3 + 2 + 6 + 2 + 2 + 28 |
| Sổ hạng mục chưa rõ có/không | 18 | không suy "không có" từ việc hệ thống không sinh dòng |

### So khối lượng theo nhóm (`So_sanh_nhom`; 26 nhóm, 18 so được)

| Nhóm | Đối chứng | Hệ thống | Trạng thái | Chênh % | Ghi chú |
|---|---|---|---|---|---|
| COT | 17,092 | 18,625 | A | +9,0 | cột từ bảng thống kê cột |
| COP_PHA/COT | 332,48 | 315,64 | A | −5,1 | |
| CAU_THANG | 5,85 | 5,593 | B | −4,4 | |
| COP_PHA/CAU_THANG | 67,5 | 52,031 | B | −22,9 | |
| SAN | 43,455 | 42,392 | C | −2,4 | phần mái tách sang MAI |
| BE_TONG_LOT | 11,784 | 10,796 | C | −8,4 | dựa trên thông số |
| MONG, COP_PHA/MONG | 14,112; 47,04 | 14,112; 47,04 | C | 0,0 | **khớp do thông số lấy từ dự toán** |
| DAM / COP_PHA/DAM | 37,22 / 598,72 | 30,165 / 409,834 | C | −19,0 / −31,5 | D03 |
| COP_PHA/SAN | 434,55 | 312,367 | C | −28,1 | O02 (trừ đáy dầm/cột) |
| XAY | 191,063 | 159,324 | C | −16,6 | đã loại lan can (PT26), gối đỡ (chưa phân loại) |
| TRAT | 3.009,94 | 2.162,62 | C | −28,2 | dự toán suy trát = thể tích / dày × 2 |
| COT_THEP/* (MONG, COT, DAM, SAN, CAU_THANG) | | | C | −0,1 … −32,5 | theo hàm lượng = thể tích bê tông × hệ số của chính dự toán |
| Không so (8) | | | | | LANH_TO, COP_PHA/LANH_TO, COT_THEP/LANH_TO: D (thiếu cao lanh tô); MAI, COP_PHA/MAI, DAO_DAT, DAP_DAT: hệ thống không sinh dòng; CAN_NEN: hệ thống có, đối chứng không |

`Theo_trang_thai`: A/B 4 nhóm (4 so được, 3 trong ±10%, lệch TB 10,4%); C/D 18 nhóm (14 so được, 6 trong ±10%); không có số 4.
Đây là đối chứng build chưa xác nhận, **không phải KPI**.

### Vật tư (`Vat_tu_nhom`, `He_thong_vat_tu`)

0/24 dòng vật tư D02 so được. Lý do: tổng lẫn hoàn thiện/không dùng làm đáp án (6); cơ sở lắp đặt (4: thép ≤ 10, ≤ 18, > 10 chưa xác
định nhóm, cọc); chưa có mã danh mục để ghép (6, gồm thép mua theo nhóm Ø); hệ thống không có vật tư cùng mã (6: cọc, gạch thẻ, gạch
ống, gỗ ván, đinh, que hàn); hệ thống chưa đủ hoặc chưa có lượng có hao hụt (2: đá 1×2 104,07 m³ nhưng chưa đủ; dây thép thiếu % hao hụt).

## 5. Đối chiếu tay

1. **Công tác độc lập – COT**: D02 `46-C08` = stt 8 = 17,092 m³ (tổng 4 phần trục khớp). Hệ thống: 34 dòng COT từ "bảng thống kê
   cột", Σ = 18,625 m³, trạng thái A. Chạy `compare()` cũ trên cùng kết quả: `he_thong` 18,625, lệch 9,0% — trùng.
2. **Dòng gộp – XAY**: `46-C27` có 14 phần; loại `.12` lan can 2,25 (PT26) và `.14` gối đỡ 0,18 (chưa phân loại) →
   103,427 − 2,25 − 0,18 = 100,997; `46-C28` mọi phần cùng nhóm → dùng số gốc 90,066 (không phải 94,14); `46-C29`, `46-C30` (bậc, tam
   cấp, bể) không cùng phạm vi. Đối chứng 191,063 ↔ hệ thống 159,324. `compare()` cũ cộng cả dòng 27 nguyên: 193,493 — khác do phạm vi.
   Tương tự MONG: cũ 15,99 (gộp đáy/nắp bể dòng 6), C01 14,112; SAN: cũ 47,855 (gộp mái), C01 43,455.
3. **Vật tư mua/lắp đặt – thép**: D02 lắp đặt Ø ≤ 10 (7.178,3 kg), Ø ≤ 18 (15.503,4 kg), Ø > 10 chưa xác định (1.570,8 kg); mua 7.214,1915 /
   17.415,684 kg. Hệ thống xuất một dòng thép (tấn) không chia Ø, không mã danh mục → **chưa đủ điều kiện so** (J03). Không gộp > 10 vào ≤ 18,
   không trộn lắp đặt với mua.

## 6. Sai lệch và thiếu cần xử lý sau (không sửa trong C01)

| Phát hiện | Nguồn | Sprint |
|---|---|---|
| Cốp pha dầm −31,5%, cốp pha sàn −28,1%, dầm −19% | So_sanh_nhom; D02 C09/C15 (×6 tầng?), C16 | D03, O02 |
| Trát −28,2%: dự toán suy từ thể tích/dày × 2, hệ thống đo mặt tường | D02 C32 | J05 (gạch rỗng), kiểm D02 |
| Xây −16,6% | XAY | cần phân tích nhận tường (chưa gắn sprint) |
| Lanh tô, cốp pha, thép lanh tô D: thiếu cao lanh tô | 46_thong_so (README: không đặt) | DL02 |
| MAI, COP_PHA/MAI không sinh dòng: `roofs` chỉ nhập qua API, thông số bộ 46 không có | M01 PT23 | O04, L01, X03 |
| Đào/đắp không sinh dòng: thiếu cao độ đất, cao độ đáy móng | M01 PT01–02 | P01/X03 |
| CAN_NEN hệ thống 477,99 m², đối chứng không có dòng | dự toán chỉ có lát nền (hoàn thiện) | D02 (người kiểm) |
| Vật tư: không ra gỗ/đinh cốp pha (chưa chọn `formwork_type`), thép không chia Ø, dây thép thiếu hao hụt | He_thong_vat_tu | B01, J03, A01 |
| MONG/thép khớp vì thông số lấy từ dự toán | 46_thong_so.json | D02/T01 (cần thông số độc lập) |

## 7. Giới hạn

- Nguồn đối chứng chưa xác nhận; bảng `PT_WORK` là ánh xạ đề xuất theo M01, chưa được người kiểm xác nhận.
- So ở mức tổng công tác/cấu kiện, chưa theo tầng (hệ thống và D02 chưa có khóa tầng chung).
- Danh mục CSV của kho có thể khác PostgreSQL thật; số trong báo cáo ứng với `nguon_danh_muc` ghi ở `Trang_thai`.
