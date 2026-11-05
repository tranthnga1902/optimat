# Rà dữ liệu cho demo 05/11/2026

Lượt audit ban đầu chỉ đọc CSV/JSON ngày03/11/2026; mục3B bổ sung bằng chứng DB do phiên chính cung cấp. Không sửa nguồn, manifest, đáp án hoặc mô hình. Skill Ponytail: kế thừa bộ đang có, không tạo dữ liệu hoặc lời xác nhận thay người dùng. Yêu cầu mới: **chỉ nhập ACTUAL có nguồn, thiếu giữ trống**.

## 1. Bộ demo nhỏ nhất có căn cứ

**Chọn bộ 46 Nhà Tân Bình làm bộ chính để phát triển và trình diễn tích hợp**, vì có cặp kiến trúc/kết cấu, thông số có nguồn và báo cáo baseline. Đây là hồ sơ ACTUAL–build; đáp án vẫn `chua_kiem`, quyền dùng/phiên bản `chua_ro`. Không dùng kết quả để công bố độ chính xác độc lập, không phát hành lại bản vẽ khi quyền phân phối chưa rõ.

| Thành phần | Đường dẫn từ gốc optimat-ai | Phạm vi dùng |
|---|---|---|
| Kiến trúc | `data/drawings/build/tan_binh_kien_truc.dxf` | File hiện có, 13.067.970 byte |
| Kết cấu | `data/drawings/build/tan_binh_ket_cau.dxf` | File hiện có, 7.878.010 byte |
| Thông số | `data/ground_truth/du_toan/46_thong_so.json` | Thông số lấy từ diễn giải dự toán; C, không phải mặc định chung |
| Dự toán gốc chuẩn hóa | `data/ground_truth/du_toan/46_nha_tan_binh.csv` | Tham khảo phát triển, không phải đo tay độc lập |
| Vật tư nguồn | `data/ground_truth/du_toan/46_vat_tu.csv` | Quy cách/khối lượng/giá lịch sử năm 2016 HCM; không phải báo giá mua hiện tại miền Bắc |
| Manifest | `data/ground_truth/du_toan/cases.csv` | Giữ build, không chuyển sang test |
| Đáp án nháp | `data/ground_truth/du_toan/d02/46_nha_tan_binh/` | 129 dòng công tác cha/con, 24 dòng vật tư; chưa tự nâng trạng thái |
| Báo cáo phát triển dự phòng | `reports/c01_review_fix/c01_duong_co_so_build.xlsx` | Kết quả đã xuất, xem kèm `HUONG_DAN_BAN_SUA.md` và `BAN_GIAO.md`; không gọi là KPI nghiệm thu |

Thông số hiện có: site_mix M200, lót M150, vữa xây/trát M75, trát15mm, sàn100mm, bản thang100mm, dầm200×350mm, cửa đi cao2000mm, 14 móng1200×1200×700mm+lót100mm, nền lót100mm. Thép theo hàm lượng từng cấu kiện lấy chính từ dự toán; vì vậy so thép theo các hệ số này không chứng minh nhận thép độc lập.

Thiếu phải giữ rõ: chiều cao cửa sổ, cao lanh tô thống nhất, cốt đất tự nhiên/đào đắp; phương án vật liệu tường cần chọn, thông số và phạm vi mái/bể cần rà đúng. Không nhập cao tầng3300 hoặc kích thước cửa mẫu như thể là số nguồn. Nhà được mô tả trệt+lầu1–4, sân thượng và mái: xác nhận ánh xạ tầng trước trình diễn để tránh đếm thêm sàn/mái.

## 2. Phương án dự phòng

- Dự phòng tích hợp trước mắt: **cùng bộ 46**, giữ workbook/ảnh/video của lần chạy đã kiểm và thông số cố định. Chưa có bằng chứng một bộ thứ hai đã chạy trọn luồng để hứa dự phòng đầy đủ.
- Dự phòng thao tác đọc bản vẽ: `data/drawings/build/nha_pho.dxf` (20.796.388 byte) hoặc `nha_dan.dxf` (8.176.918 byte). Đã có `.khai_niem.json`, nhưng chưa có đáp án/thông số hoàn chỉnh; không mặc định ghép `ket_cau.dxf` với chúng nếu chưa xác nhận cùng công trình. `nha_pho` có vấn đề tiêu đề tầng3 lặp và thang một vế được ghi trong PLAN.
- `nha_huong_hai_duong_7x12_{kien_truc,ket_cau}.dxf` và `nha_sang_hai_duong_4x15_{kien_truc,ket_cau}.dxf` đều hiện có trong build. Chưa có bộ thông số tương ứng đã xác nhận; hai nhãn tổng thép có mâu thuẫn nội bộ đang cách ly. Không chọn làm đường demo chính khi chưa chạy tích hợp.
- **Không dùng banve1 làm fallback để chỉnh mã**: `data/drawings/test/banve1_{kien_truc,ket_cau}.dxf` vẫn là test, thiếu thông số và tài liệu ghi chưa nhận được tường. Giữ split hiện tại.

## 3. Giá, phương án tường và vận chuyển trên đĩa

| Nguồn CSV | Kết quả đọc trực tiếp | Ý nghĩa demo |
|---|---|---|
| `data/catalog/materials.csv` | 98 dòng ACTUAL | Có danh mục, không đồng nghĩa đủ mọi thông số |
| `data/catalog/wall_systems.csv` | 22 dòng ACTUAL | Theo các trường nguồn dùng trong `wall_view`, 5 phương án đủ trường số: W-GN01-110, W-GN01-220, W-GN03-105, W-GN03-150, W-GK01-110 |
| `data/catalog/suppliers.csv` | 2.843 ACTUAL; 142 có cả lat/lon; **0 lead_time_days; 0 verified=True** | Danh bạ không phải báo giá hoặc thời gian cung ứng đã kiểm |
| `data/catalog/supplier_materials.csv` | **0 dòng** | Chưa có báo giá mua trong CSV |
| `data/catalog/vehicles.csv` | **0 dòng** | Tối ưu CSV có thể bị chặn vì không có xe |
| `data/catalog/labor_rates.csv` | **0 dòng** | Không hứa tổng chi phí có nhân công |
| `data/cong_bo_gia/02.01_2026_CBGVL-SXD.csv` | 6.974 dòng; 59 dòng có mã và giá quy về danh mục; 26 mã | Công bố giá tham khảo, không mặc định là báo giá còn hiệu lực/giao tận công trình |

26 mã có giá quy đổi ở bảng công bố: CA03, CA01, DA04, DA03, DA01, DA02, XM01, XM02, XM03, VU03, GK01, CT02, CT04, PG02, CT06, CT05, TH01, TH02, TH08, TH07, TH03, MA02, TH05, AAC01, AAC02, AAC03. **Không có GN01, GN03 hoặc VU02**. Chỉ GK01 giao với tập 5 phương án đủ trường, vẫn phải kiểm vữa đi kèm và điều kiện báo giá.

Số văn bản `02.01/2026/CBGVL-SXD` không phải bằng chứng tháng01. Biên nhận lần nhập cũ lưu ngày **20/06/2026**; gói SQL mới bảo toàn đúng mốc này từ dump bằng chứng, chưa đọc kiểm lại PDF gốc. Một ngày giá không đủ bằng chứng lịch sử6tháng hoặc còn hiệu lực đến05/11. Giá cát tại bãi có ghi chưa bao gồm vận chuyển. Không đổi giá nguồn thành báo giá mua hoặc chi phí giao. Có mã ACTUAL không tự chứng minh toàn bộ điều kiện thương mại.

`Catalog.load()` dùng PostgreSQL khi cấu hình có DB, còn `Catalog.from_csv()` mới đọc CSV. Giá `price_records` được `catalog/pricing.py` nạp qua PostgreSQL; CSV công bố không tự trở thành bảng giá runtime. Không suy DB trống hay đủ từ CSV; trạng thái DB thực ở mục3B.

## 3B. Bổ sung DB và lần nhập ACTUAL đã thực hiện

**Cập nhật mới nhất:** gói07 đã nhập thành công lúc17:27:14 ngày03/11/2026 (giờ ViệtNam), thêm1NCC và4giá lịch sử ACTUAL/BULLETIN; tổng hiện **2867suppliers/63price_records**. Lần chạy lại17:27:45 làno-op0/0. Chi tiết, IDthực thêm và timestamp ở `07_APPLIED.md`, `07_cement_historical_actual_first_apply_receipt.json` và receiptlần2. Các số2866/59 bên dưới làsnapshot trướcgói07, không phải tổng mới nhất.

`reports/demo_0511/db_readiness.json` là snapshot đọc DB `optimat`:98materials ACTUAL,22wall_systems ACTUAL,2866suppliers (2863ACTUAL+3SAMPLE),59price_records ACTUAL/BULLETIN. **13supplier_materials đều SAMPLE,4vehicles đều SAMPLE,1labor_rate SAMPLE; chưa có báo giá mua/xe/nhân công ACTUAL trong các bảng đó.** Sốusers1 và tài khoản inactive trong snapshot là mốc cũ: phiên chính xác nhận sau đó đã có activeadmin/session, không còn coi đây là lỗi đăng nhập hiện tại.

Theo user chọn ACTUAL-only, đã chuẩn bị và phiên chính apply gói `sql/06_demo_actual.sql` (canonical), kiểm nguồn/hash và natural keys bằng `reports/demo_0511/apply_actual_sql.py`. `db_apply_receipt.json`: **committed=true, thêm0suppliers/0price_records**, trước/sau vẫn2866suppliers và59prices vì toàn bộ20NCC/59giá ứng viên đã có. Đây là no-op an toàn, **không phải thêm59giá mới**, không ghi đè giá cũ, không thay dữ liệu SAMPLE hiện có. Script mặc định chỉ preflight đọc, `--apply` mới ghi.

Generator/validation9tests đạt (xem db_import_handoff.md). Gói06 bảo toàn ngày20/06/2026 từ lần nhập cũ, chưa kiểm lại PDF nguồn đó. **Gói07 khác:** PDFCEMIA tháng3 đã tải, render và hai phiên xem ảnh13/14;4giá XM01/XM02 ngày17/03/2026,đồng/tấn,baoKPK50kg,đãVAT,transportUNKNOWN. Không cóquyđổi đơnvị; têncao cấp/đa dụng giữ trongsource. Hai mốc lịch sử không giải quyết thiếu GN01/GN03/VU02, báo giá mua, xe hoặcleadtime thật; không dùngSAMPLElấpthiếu. SQLchuẩn `sql/07_cement_historical_actual.sql`.

## 4. Mô hình giá hiện có

`models/material_price_xgb.json`, `models/material_price_spec.json`, `models/material_price_metrics.json` tồn tại. Metrics ghi **data_kinds=[SYNTHETIC], contains_synthetic=true**, chia832/208/208, tập kiểm07–10/2026. Phạm vi mã trong spec: AAC01,AAC03,GK02,GK03,GN01; nhà cung cấp SUP_A/SUP_B/SUP_C; Ha Noi. Không có bằng chứng mô hình đã huấn luyện ACTUAL. Không báo MAPE/R² hiện tại như chất lượng trên giá thật; không dùng mô hình này lấp báo giá ACTUAL còn thiếu. Chưa huấn luyện lại hoặc ghi đè artifacts trong lượt này.

## 5. Chạy nhỏ nhất sau khi điều phối cấp lượt

Các lệnh dưới là hướng dẫn, **chưa chạy**. Chạy tại gốc optimat-ai. Không init/reset/reload DB. Để tái lập baseline CSV không DB, dùng process tách biệt bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPTIMAT_CATALOG_OVERLAY và đặt OPTIMAT_NO_DOTENV=1; không ghi giá trị bí mật ra log.

```powershell
.venv/Scripts/python.exe scripts/compare_estimate.py data/ground_truth/du_toan/46_nha_tan_binh.csv data/drawings/build/tan_binh_kien_truc.dxf --structural data/drawings/build/tan_binh_ket_cau.dxf --params data/ground_truth/du_toan/46_thong_so.json --out reports/demo_0511/46_compare.xlsx
.venv/Scripts/python.exe scripts/c01_duong_co_so.py --out reports/demo_0511/46_baseline.xlsx
```

Để chạy web: backend `uvicorn optimat.api.main:app --app-dir src`, frontend `npm run dev` tại frontend; dùng cấu hình DB hiện hành đã kiểm, đăng nhập và chọn đúng cặp file46. Không dùng overlay mẫu âm thầm để thông tối ưu.

**Hở audit BOQ đã được giao sửa:** lúc đọc ban đầu export_boq truyền JSON có `openings` thẳng vào ProjectParams, khác compare_estimate tách OpeningDefaults. Phiên chính báo bản sửa BOQ/Q01 đã có nguồn, đang chờ điều phối kiểm tích hợp trọng tâm. Không tiếp tục coi đây là lỗi chưa ai xử lý, cũng chưa đánh nghiệm thu trước kết quả kiểm. Agent dữ liệu không sửa nguồn.

## 6. Dữ liệu chặn cần xử lý ngay

1. DB runtime đã được đọc và gói ACTUAL đã apply no-op theo mục3B; còn thiếu báo giá mua/giao hàng ACTUAL. Phân biệt SAMPLE tồn tại trong DB với đầu vào được phép dùng.
2. Khóa hồ sơ46 và ánh xạ tầng; dùng thông số có nguồn, giữ cửa sổ/lanh tô/đào đất thiếu. Rà số lớn nhất trên build.
3. Muốn demo tối ưu ACTUAL: bổ sung báo giá có nguồn cho vật liệu chính và vữa/cấp phối của các phương án chọn; NCC, thời gian giao, tọa độ hoặc phí giao/xe phải có căn cứ. Không tự tạo ACTUAL hoặc hiệu lực.
4. Khi chưa đủ dữ liệu: trình diễn bóc/vật tư/giá tham khảo/phần thiếu. Theo lựa chọn ACTUAL-only mới của user, không nạp hoặc dùng SAMPLE để làm tối ưu thông luồng; báo rõ thiếu hoặc chưa có nghiệm từ dữ liệu thật.
5. D02 chưa có xác nhận độc lập; `data/ground_truth/index.csv` và `walls.csv` chỉ có sample_floor SYNTHETIC/mẫu, không phải5 mặt bằng đo tay thật. Không hứa sai số toàn hệ thống đã được chứng minh.

Giới hạn hiện tại: DBread/apply córeceipt;74testtrọng tâm đạt theo điều phối, gồm13caAPIview/structural, chưa thay fullsuite hoặc nghiệm thuUI. Source ổn định đang chờ toànsuite. Trìnhduyệt chưa khép doHMR vàCADxửlýdài; CPU161s/~1,1GB làquan sát mộtmốc, không phải kếtquảđạt. Frontend2harness+tsc/lint đạt; cònthiếu dữliệu mua/giaoACTUAL vàkiểm trọn luồng.
