# Q01 — SOURCE-READY (03/11/2026)

## Phạm vi đã sửa

- `src/optimat/rough/status.py`: thêm đúng hai đầu vào cho CAU_THANG: dày bản thang từ ProjectParams và nguồn chiều cao tầng. Giữ nguồn hình học `_src` hiện có.
- `tests/test_rough_status.py`: thêm 4 hàm test / 6 ca (3 nguồn tham số hóa), kiểm auto+dày nhập -> C, cốp pha kế thừa C, không đổi khối lượng, thiếu dày -> D, thiếu nguồn cao tầng -> D, giữ nguồn auto/manual/structural trong inputs.
- Không sửa công thức, schema, giằng, materials/A01, N01 hoặc tài liệu chung.

## Bằng chứng

- Snapshot trước sửa: `status.before.py`, `test_rough_status.before.py`, `hash_before.json`.
- Diff riêng của lượt: `q01.patch`.
- Hash SOURCE-READY: `hash_source_ready.json`.
- status.py SHA256: F35DF97DE208E3CD9C9E7C67BE82197FB94819D291403695BC1DF1870652A812
- test_rough_status.py SHA256: E27C58BBC3F9AA4FBB186CDFEDE9E944E28A7AFE9CB7C48079DE6715FD55556C

## Chưa kiểm

Chưa chạy backend test/full suite/DB theo khóa kiểm của coordinator. Trạng thái SOURCE-READY, chưa ĐẠT hoặc nghiệm thu. Parent có thể chạy test trọng tâm sau khi giải phóng lượt. Structural geometry chỉ kiểm ở WorkItem trực tiếp; stair_works hiện chuẩn hóa nguồn không-auto thành manual, chưa thay hợp đồng đó. Thiếu height_sources chỉ hạ trạng thái D; giữ lượng đã có theo scope không đổi công thức.

Lệnh kiểm đề nghị sau cấp lượt: `.venv/Scripts/python.exe -m pytest tests/test_rough_status.py tests/test_rough_stairs_detect.py tests/test_rough_secondary.py -q -p no:cacheprovider` với DATABASE_URL/OPTIMAT_TEST_DATABASE_URL bị loại và OPTIMAT_NO_DOTENV=1.
