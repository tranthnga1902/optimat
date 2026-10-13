# Quy trình phát triển và kiểm soát dữ liệu

## 1. Mỗi loại dữ liệu có một nguồn

| Dữ liệu | Nguồn duy nhất (sửa ở đây) | Sinh ra / nạp vào |
|---|---|---|
| 75 vật liệu, phương án tường, quan hệ, tên gọi khác | `data/catalog/materials_master.xlsx` | `python scripts/build_materials_sql.py` → `sql/03_materials.sql` + `data/catalog/{materials,wall_systems,material_aliases}.csv` |
| Quy tắc bóc tách vật liệu | `data/rules/material_rules.csv` | đọc trực tiếp |
| Đại lý, giá đại lý | Mẫu `docs/du-lieu/OptiMat AI - Thu thap dai ly.xlsx` → bảng `suppliers`, `supplier_materials` | PostgreSQL (chế độ không có database: `data/catalog/suppliers.csv`, `supplier_materials.csv`) |
| Lịch sử giá (huấn luyện XGBoost) | bảng `price_records` | `scripts/init_db.py --prices <file.csv>` |
| Đáp án đo tay | `data/ground_truth/index.csv`, `walls.csv` | `scripts/evaluate_takeoff.py` |
| Bản vẽ | `data/drawings/build/` (chỉnh quy tắc), `data/drawings/test/` (chỉ để báo cáo) | không đưa vào git (file lớn) |
| Lược đồ database | `src/optimat/db/models.py` | `scripts/export_sql.py`, `scripts/build_upgrade_sql.py` → `sql/01`, `02`, `04` |

Không sửa tay file sinh tự động (`sql/*.sql`, `data/catalog/materials.csv`, `wall_systems.csv`, `material_aliases.csv`).

## 2. Quy ước số liệu

- Mỗi dòng có `data_kind`: `ACTUAL` (có nguồn thật), `SAMPLE` (mẫu), `SYNTHETIC` (mô phỏng). Chỉ `ACTUAL` được dùng để báo cáo.
- Ô chưa có nguồn để trống, không ước lượng. Hệ thống tự loại phương án thiếu số liệu khỏi tối ưu và ghi lý do.
- Giá có `price_level` (DEALER, QUOTE, BULLETIN) và `price_date`; giá quá 90 ngày bị cảnh báo.
- Mã vật liệu dùng chung từ bản vẽ đến giá: `GN01`, `AAC01`...; phương án tường `W-GN01-220`. Không dùng mã MAT_* cũ.

## 3. Vòng làm việc

```powershell
# 1. sửa nguồn (Excel, CSV quy tắc, mã nguồn)
python scripts/build_materials_sql.py      # nếu đã sửa materials_master.xlsx
python scripts/check_data.py               # kiểm soát dữ liệu: 0 lỗi mới được commit
pytest                                     # kiểm thử mã
git add -A; git commit -m "..."            # hook pre-commit chạy lại 2 bước trên
```

Bật hook một lần cho mỗi bản sao: `git config core.hooksPath .githooks`.

`python scripts/check_data.py --strict` coi cảnh báo như lỗi: dùng trước khi chốt số liệu cho chương thực nghiệm
(khi đó không được còn giá mẫu, phương án thiếu số liệu hay thiếu đáp án nhóm test).

Báo cáo mới nhất: `reports/data_check.md` (được commit để thấy dữ liệu thay đổi theo thời gian).
Trên giao diện: `/app` → vai trò Quản trị viên → Kiểm soát dữ liệu.

## 4. Kiểm tra gì

| Mức | Ví dụ |
|---|---|
| Lỗi (chặn commit) | mã vật liệu lặp; phương án tường hoặc giá trỏ tới mã không có; quy tắc trỏ tới họ không có; giá thiếu mức giá hoặc ngày; đáp án đo tay dùng mã lạ |
| Cảnh báo | phương án thiếu định mức, khối lượng, λ; lớp tường chưa có phương án (330); vật liệu tường chưa có giá; giá mẫu; chưa có giá thật; chưa có đáp án nhóm test; tên gọi trỏ tới nhiều vật liệu |
| Ghi chú | bản vẽ mẫu tự tạo trong đáp án |
