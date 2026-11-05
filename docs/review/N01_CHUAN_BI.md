# N01 — Chuẩn bị sửa số trong bảng thép

03/11/2026 — **CHỈ CHUẨN BỊ, chờ C01 và điều phối giao dev**. Không sửa source/test/CSV, không chạy test/DB; không mở N02/N03/A01. File này chưa là bằng chứng nghiệm thu.

## Hiện trạng và phạm vi ảnh hưởng

- `src/optimat/rough/rebar.py::_num:83–94` lấy chuỗi số đầu tiên bằng regex, bỏ dấu chấm nếu khớp nhóm nghìn, rồi đổi phẩy thành chấm. Đọc mã cho thấy `1.200,5` và `1,200.5` đều thành chuỗi không hợp lệ cho `float` → `None`; `1.200` → 1200, `1,200` → 1.2. Đây là mô tả đọc mã, chưa chạy tái hiện.
- Caller sản phẩm trực tiếp chỉ ở `read_table:133`: điều kiện tiếp tục dòng (`166`), Ø và khối lượng bảng ghi (`173`), số thanh/cấu kiện/tổng thanh (`174–175`), chiều dài (`178`). `_num` trong materials/pricing/concepts là hàm khác, ngoài phạm vi. Test gọi trực tiếp `_num` tại `tests/test_rough_rebar.py:42,49`.
- Ngữ cảnh đang có: khóa cột và chữ tiêu đề qua `_header:122`; chiều dài có nhánh `(m)` tại `151,179–180`, không khớp nhánh đó thì chiều dài được coi là mm. Chưa có trường quy ước dấu/locale của bảng. `LENGTH_MM` chỉ kiểm nghi sai đơn vị sau parse, **không chứng minh** dấu là nghìn hay thập phân. Ø tra `unit_mass`, số thanh nhân nhau; không dùng kết quả “có vẻ hợp lý” để chọn cách đọc.
- Ảnh hưởng gián tiếp: `read_rebar_schedules:218` → `steel.schedule_works/steel_works` → `compute_rough` → công tác, vật tư và BOQ. Parse sai làm đổi kg, cảnh báo đối chiếu và khóa khử trùng; N01 không sửa logic khử trùng N02.

## Quy tắc số đã chốt cho đúng một lỗi N01

Quyết định BA của điều phối ngày 03/11/2026: giữ hợp đồng một loại dấu của bộ đọc hiện hành, chỉ mở rộng cú pháp hai dấu rõ ràng. Không thêm locale/schema/UI, không chặn request cũ trong N01; chỉ triển khai sau khi C01 đạt kỹ thuật và điều phối giao dev.

| Dữ liệu | Hành vi cần giữ/kiểm |
|---|---|
| `1.200,5`; `1,200.5` | Đều 1200.5 khi khớp đầy đủ cấu trúc Việt/Anh: nhóm đầu 1–3 chữ số, các nhóm nghìn tiếp theo đúng 3 chữ số, sau dấu thập phân có chữ số. Không chỉ thay/xóa mọi dấu; nhóm sai như `12.00,5` hoặc `1,20.5` trả None, không đoán. |
| Số nguyên không dấu, rỗng; `1,58`, `3.2`; `Ø16` | Giữ đọc số nguyên, rỗng → None, thập phân rõ → 1.58/3.2, tiền tố Ø trong ô đường kính → 16; không làm mất kiểm tra m/mm hiện có. |
| `1.200` hoặc `1,200` | Giữ quy ước phần mềm hiện hành: nhóm chấm nghìn hợp lệ → 1200; phẩy thập phân → 1.2. `5.000` vẫn 5000, `3.200` vẫn 3200; dạng dot decimal đang được chấp nhận như `3.2` vẫn 3.2. Không chọn cách đọc theo kích thước hợp lý, Ø có trong danh mục hay tổng kg gần đúng. |

**Giới hạn:** đây là quy ước phần mềm sẵn có và mở rộng cú pháp rõ, không áp được mọi locale của mọi nguồn. Một dấu ba chữ số có thể mơ hồ ngoài quy ước này; nếu muốn luôn giữ thiếu hoặc yêu cầu xác nhận theo locale thì cần sprint đổi hợp đồng riêng, không làm trong N01. Không hardcode ngoại lệ riêng cho số 5.000 hay đổi kỳ vọng test để đạt. Với `(m)`, đổi sang mm đúng một lần **sau** parse. Giữ evidence/missing và điều kiện dừng dòng hiện có; ca dữ liệu không hợp lệ dùng Ø hợp lệ để kiểm đường thiếu chiều dài, không mở rộng cơ chế giữ dòng khi cả Ø và chiều dài đều không đọc được trong lượt sửa này.

## Test cần giữ/thêm và cổng bàn giao

- **Đúng N01:** bỏ duy nhất xfail của `test_number_mixed_vietnamese_separators` (`test_rough_rebar.py:47–49`) sau khi lỗi được sửa và test chạy đạt; thêm dạng `1,200.5`. **Giữ xfail N02** `test_duplicate_table_without_mark_counted_once` (`52–59`), không chỉnh khử trùng trong lượt N01.
- Giữ nguyên hợp đồng của `test_number_and_element_parsing`, `test_read_schedule_and_kg` (5.000 mm, 3.2 trong cột mm vẫn báo sai đơn vị; dừng TỔNG; evidence), `test_duplicate_table_counted_once`, `test_schedule_steel_separate_from_ratio`, `test_no_schedule_leaves_steel_blank`, `test_boq_excel_sheets`; giữ test nguồn kg/m.
- Thêm kiểm parse hai định dạng hỗn hợp, số nguyên/rỗng/thập phân và nhóm sai; khóa tương thích `1.200 → 1200`, `1,200 → 1.2`, `5.000 → 5000`, `3.2 → 3.2`. Thêm ca `read_table` cho chiều dài mm/m, khối lượng ghi và số thanh hỗn hợp; kiểm quy đổi/kg, chuỗi gốc và missing hiện có với chiều dài sai nhóm + Ø hợp lệ. Không gộp các đại lượng khác đơn vị để kiểm tổng.
- Dev sau C01 đạt kỹ thuật chỉ sửa `_num` cho mixed separators và test tương ứng; giữ callers/evidence/missing hiện có, không thêm ngữ cảnh locale. Lệnh test trọng tâm dự kiến `pytest tests/test_rough_rebar.py`; toàn suite/DB chỉ khi điều phối cấp lượt. **Chưa chạy bất kỳ lệnh test nào trong bản chuẩn bị.**

Bàn giao cập nhật: chỉ sửa file này theo quyết định BA; quy ước một loại dấu đã chốt, còn chờ C01 đạt kỹ thuật và điều phối giao dev. Dòng nhật ký đề xuất: “03/11/2026 — N01 chốt giữ quy ước số cũ, chỉ mở rộng mixed separators hợp lệ; đã cập nhật prep, chưa sửa mã/test hay chạy test; chờ C01 đạt kỹ thuật.”
