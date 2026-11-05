# Dự toán thật làm đáp án phần thô

## Manifest hồ sơ `cases.csv` (D01, 03/11/2026)

Một dòng một hồ sơ đánh giá. Kiểm bằng `optimat.data_check.check_cases` (chạy trong `scripts/check_data.py`, mục `ho_so`);
`scripts/evaluate_rough.py` chọn hồ sơ ở lối vào bằng `select_cases`.

| Cột | Bắt buộc | Giá trị | Ghi chú |
|---|---|---|---|
| `ten` | có | duy nhất | mã hồ sơ, tên sheet báo cáo |
| `cong_trinh_id` | có | duy nhất theo công trình | mọi phiên bản/tên khác của cùng công trình dùng chung mã; một công trình chỉ ở một split |
| `phien_ban` | không | chữ; `chua_ro` khi chưa biết | không tự đặt phiên bản/hash |
| `data_kind` | có | ACTUAL, SAMPLE, SYNTHETIC | chỉ ACTUAL vào chỉ tiêu chính |
| `split` | có | build, test | không đổi split âm thầm |
| `du_toan` | có | đường dẫn từ gốc dự án | thiếu file là lỗi |
| `kien_truc`, `ket_cau` | không | đường dẫn | bản vẽ không vào Git: thiếu trên máy là cảnh báo, hồ sơ đó không chạy |
| `thong_so` | không | đường dẫn JSON | khai báo mà thiếu file là lỗi |
| `nguon` | không | chữ | nơi lấy tài liệu |
| `quyen_dung` | không | duoc_phep, noi_bo, chua_ro | trống/`chua_ro` = cảnh báo; tải công khai không có nghĩa được phân phối lại |
| `dap_an_trang_thai` | không | chua_kiem, da_kiem | `da_kiem` phải có `nguoi_kiem` |
| `nguoi_kiem` | không | chữ | không tự điền |
| `ghi_chu` | không | chữ | |

Chặn: thiếu cột/giá trị bắt buộc, giá trị ngoài danh sách, tên trùng, file đáp án/thông số khai báo mà không có,
cùng `cong_trinh_id` hoặc cùng file đáp án/bản vẽ (đường dẫn thật, không theo tên file) nằm ở cả build và test.

Lối vào đánh giá: `--muc-dich phat_trien` (mặc định) chỉ chạy build, mọi `data_kind`, ghi nhãn phát triển;
`--muc-dich bao_cao` chỉ chạy ACTUAL + test + đáp án đã kiểm có người kiểm. Hồ sơ bị loại được in và ghi sheet `Bỏ qua`.

Giá trị hiện có (chỉ ghi điều có căn cứ trong thư mục này): hai hồ sơ ACTUAL; `46_nha_tan_binh` build,
`banve1_nha_pho_di_an` test (giữ nguyên). `phien_ban`, `quyen_dung` = `chua_ro`; `dap_an_trang_thai` = `chua_kiem`
(đây là dự toán của người lập, chưa có người kiểm độc lập), nên chưa hồ sơ nào đủ điều kiện chỉ tiêu chính.
D01 không khóa mẫu số, không ánh xạ lại dòng đáp án (D02).

## Bộ đáp án D02 `d02/` (03/11/2026)

Mỗi hồ sơ một thư mục `d02/<ten>/` (sổ hạng mục, đáp án công tác, đáp án vật tư, khóa nguồn sha256); mẫu rỗng ở `d02/_mau/`.
Đặc tả, số liệu bộ 46 và phiếu cho người kiểm: `docs/D02_DAC_TA_DAP_AN.md`. Kiểm: `data_check.check_answer_set` (chạy trong
`check_data.py`). File gốc trong thư mục này và `cases.csv` không đổi; `46_nha_tan_binh` hiện là bộ **nháp**, chưa có dòng
nào được người kiểm xác nhận (`da_kiem`), chưa dùng làm đáp án chỉ tiêu.

`46_nha_tan_binh.csv`: sheet "Công trình" của `Nha Tan Binh.xls` (bộ "46-Nha Dan 5 Tang (KT+KC+DN+BPTC+DuToan)",
kenhxaydung.vn, lập 2016 theo định mức 1776, đơn giá HCM). Nhà 4 × 22,6–25,6 m: trệt, lầu 1–4, sân thượng, mái.

- `data_kind`: ACTUAL (dự toán của công trình thật, không phải đo tay của dự án).
- `split`: build. Bộ bản vẽ này đã dùng để sửa tách mặt bằng (28/10/2026), không dùng làm số báo cáo độ chính xác.
- `khoi_luong` đã đổi về đơn vị của hệ thống (100 m² → m², 100 m → m); `khoi_luong_goc`, `don_vi_goc` giữ nguyên bản.
- `ma_cong_tac`, `cau_kien`: gắn theo tên công tác (mã định mức không đủ: AF.11212 lót và AF.11213 móng chung nhóm);
  trống = **chưa ánh xạ/chưa phân loại**, không tự đồng nghĩa ngoài phạm vi (sửa 03/11/2026, D01). Ghi chú cũ coi dòng
  "BNN" (bể nước ngầm) là không phải bộ phận nhà: không còn đúng, bể nước ngầm/bể phốt phần kết cấu, xây, trát, chống thấm
  là IN theo M01 QĐ-03/04. Phân loại IN/OUT từng dòng làm ở D02 theo `docs/M01_PHAM_VI_PHAN_THO.md` mục 5A.
- `dien_giai`: các dòng diễn giải khối lượng theo trục, tầng, nối bằng " | ".

So sánh: `python scripts/compare_estimate.py data/ground_truth/du_toan/46_nha_tan_binh.csv <Kien_truc.dxf> --structural <Ket cau.dwg>`.

`46_thong_so.json`: thông số công trình cho bộ 46, lấy từ diễn giải của chính dự toán (không phải số mặc định):
sàn dày 100 (`× 0,1`), dầm 200 × 350 (bê tông `0,2 × 0,25` dưới sàn + sàn 100), móng 1200 × 1200 × 700, lót 100
(số khối M1–M4 = 14 đọc từ mặt bằng móng, khớp `× 14`), trát 15, lót nền 100 (`22,6 × 4 × 0,1`), mác M200 / M150 / vữa M75;
hàm lượng thép kg/m³ = hệ số tấn/m³ của dự toán (móng 0,11; cột 0,05 + 0,22; dầm 0,05 + 0,24; sàn 0,11; thang 0,21;
lanh tô 0,28), nên so thép chỉ kiểm khối lượng bê tông, không kiểm thép. Dày bản thang 100 (`2,5 × 3,6 × 0,1`, thêm
03/11/2026; số bậc, vế, bậc thang do hệ thống tự nhận trên mặt bằng). Không có: lanh tô (cần kích thước cửa), đào đắp
(cốt tự nhiên).

Lỗ mở (thêm 28/10/2026): bản vẽ không ghi cỡ cửa (không bảng thống kê cửa, block không thuộc tính). Chỉ lấy số dự toán
ghi rõ: cửa đi `0,8*2` → `door_height_mm` 2000. Không đặt chiều cao cửa sổ và lanh tô: dự toán không định nghĩa một giá trị
chung (ô cửa cao 2,5–3,3 m; lanh tô hai loại 200 gối 300 và 100 gối 350), nên các lỗ mở đó chưa trừ và lanh tô để trống (B7).
Khóa `openings` của file JSON là kích thước cửa của dự án (bảng `projects`), `scripts/compare_estimate.py` tách riêng khỏi
ProjectParams. Mọi số trong thư mục này là dữ liệu tham khảo để đối chiếu, không đưa vào mã hay làm mặc định.

## `banve1_nha_pho_di_an.csv` (thêm 02/11/2026)

Sheet "Bang khoi luong" của `du_toan_23-4.xls` trong bộ `banve1` người dùng gửi (nhà phố xây mới, Dĩ An – Bình Dương,
lập 04/2011 theo định mức cũ, chữ VNI). Bản vẽ: `data/drawings/test/banve1_kien_truc.dxf`, `banve1_ket_cau.dxf`
(DWG gốc trong `data/drawings/raw_20261102/`).

- `data_kind`: ACTUAL. `split`: **test** — bộ chưa từng dùng để chỉnh quy tắc; chỉ dùng để báo cáo, không sửa quy tắc theo nó.
- Sinh bằng `python scripts/import_estimate.py <xlsx> --sheet "Bang khoi luong" --first-col 2 --encoding vni --out ...`
  (file .xls đã lưu lại thành .xlsx bằng Excel). `ma_cong_tac`, `cau_kien` gắn tự động theo tên công tác: cần xem lại.
- Lưu ý khi so: dòng bê tông dầm (stt 11, AF.12314) gồm cả móng M1–M3 (6,944 m³) và đà kiềng; bê tông lót (stt 4) gồm
  cả đà kiềng, hầm phân, bể nước; đào đất (stt 2) gồm hầm phân, bể nước ngầm. Thép theo hệ số kg/m³ của người lập (100–250).
- Tường xây gạch ống 8×8×19 (AE.63233); trát tường 2 cm (AK.21134), láng nền 2 cm.
- Chưa có file thông số công trình (`*_thong_so.json`) cho bộ này: dày sàn 100, dầm 200 × 400, cột 200 × 250 đọc được từ diễn giải.

Bộ "Du Toan Nha Tan Binh" trong cùng file nén chính là bộ 46 ở trên: bản vẽ nay lưu ở
`data/drawings/build/tan_binh_kien_truc.dxf`, `tan_binh_ket_cau.dxf` (giữ split build).

## Tổng hợp vật tư (`banve1_vat_tu.csv`, `46_vat_tu.csv`, thêm 02/11/2026)

Sheet "TH vat tu" (banve1, 2011) và "Tổng hợp VT" (bộ 46, 2016) của hai dự toán: tên, đơn vị, khối lượng, đơn giá gốc,
đơn giá thực tế (HCM, Bình Dương; không phải miền Bắc), `material_id` khi khớp rõ ràng với danh mục. Dùng làm đáp án cho
bước quy đổi vật liệu (đặc tả mục 7: tổng hợp vật tư so với khối lượng × định mức). Thép để trống mã: dự toán chia theo
đường kính (≤10, ≤18, 20 mm) khác cách chia mã TH của danh mục. Giá chưa nạp vào `price_records` (vùng và năm khác phạm vi).
