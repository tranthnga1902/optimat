# Codex review J05c triển khai và J05b/J05d bản 2

Ngày 03/11/2026. Review trực tiếp mã/dữ liệu/tài liệu trong workspace, không dựa riêng báo cáo Claude.

## Kết luận

- **J05c: CẦN SỬA phần đồng bộ dữ liệu và bằng chứng kiểm; chưa nghiệm thu.** Hướng công thức/truy nền đúng hợp đồng; 43 test trọng tâm chạy lại đạt. Đường PostgreSQL thực tế vẫn dùng định mức cũ nên mã mới chưa vận hành nhất quán.
- **J05b: chấp thuận thiết kế lựa chọn `van_ep_af83`, giữ `van_ep` cũ chưa xác định hệ, bốn dòng mỗi cấu kiện và loại MAI khỏi ánh xạ đợt này.** Phần metadata `raw_class` cần chốt/duyệt lược đồ trước triển khai.
- **J05d: chấp thuận thiết kế giai đoạn 1 dòng thiếu và thông báo chung đã sửa.** Cùng phụ thuộc quyết định metadata với J05b. Giai đoạn 2 vẫn chưa duyệt và chưa được triển khai.

## 1. Phải sửa: dữ liệu PostgreSQL/SQL chưa khớp khóa tra mới

**Hiện trạng:** `materials_for_works` đã tra TRAT theo `<dày>/<family>`. CSV có bốn khóa mới. Nhưng `sql/05_rules.sql` vẫn chứa hai dòng `TRAT,15` và `TRAT,20` cũ.

**Kiểm trực tiếp:** reviewer đã chạy truy vấn chỉ đọc qua `load_norms()` với cấu hình PostgreSQL hiện tại, không nạp hoặc sửa DB. Kết quả TRAT:

```text
[('15', 0.017), ('20', 0.023)]
```

**Ca lỗi:** tường GN01 hoặc GN02 dày 15 mm có đủ phương án, chạy môi trường dùng DB hiện tại sẽ không tìm được `15/CLAY_SOLID` hoặc `15/CLAY_HOLLOW` và trả thiếu. Môi trường CSV chạy đúng không chứng minh môi trường PostgreSQL đúng. Bộ cài dùng SQL sinh hiện tại cũng nạp lại định mức cũ.

**Yêu cầu sửa tối thiểu:**

1. Sinh lại SQL quy tắc bằng script dự án, không sửa SQL bằng tay. Vì `export_sql.py` cũng sinh 01/02, kiểm diff và giữ thay đổi của phiên khác; bàn giao rõ tệp nào thay đổi do lần sinh. Không tự nạp DB thật.
2. Kiểm trên DB kiểm thử riêng có bốn dòng mới, hoặc một bài kiểm đường loader qua DB kiểm thử đã nạp phiên bản CSV này. Ghi hash, nguồn, cách nạp và kết quả tra; chưa có DB kiểm thử thì báo chờ kiểm DB, không đánh J05c hoàn tất.
3. Chuẩn bị hướng dẫn chuyển phiên bản/rollback cho phiên tích hợp: mã mới cần dữ liệu khóa mới cùng lần phát hành. Không chỉ nói “có thể reload sau” trong khi kết luận mã đã hoạt động trên DB. Việc nạp DB vận hành phải là bước được chủ đồ án cho phép, chưa thực hiện ở lượt review.

## 2. Phải sửa: bằng chứng check_data bị mô tả sai nguồn

**Hiện trạng:** bàn giao mục 8 J05c ghi `scripts/check_data.py` đạt 0 lỗi, “CSV, không có DB”. Tệp báo cáo hiện có ghi rõ `nguồn postgresql`, 0 lỗi / 1915 cảnh báo / 2 ghi chú. `data_check.run_checks(catalog=None)` từ chối chạy khi không có DATABASE_URL; lệnh script chuẩn không tự kiểm CSV trong trường hợp đó.

**Tác động:** 0 lỗi của dữ liệu DB cũ không xác nhận CSV mới và không xác nhận DB đã cập nhật J05c. Không có OPTIMAT_TEST_DATABASE_URL không có nghĩa không có DATABASE_URL của môi trường thường.

**Sửa:** ghi lại chính xác nguồn của lần check, không đổi nhãn báo cáo thành CSV để hợp thức hóa. Muốn kiểm CSV trực tiếp cần dùng đường kiểm có catalog CSV rõ ràng và bảo đảm các loader định mức/quy tắc cũng đọc CSV, không lẫn DB. Dùng tiến trình kiểm riêng, không in giá trị kết nối hay nạp dữ liệu thật. Ghi riêng kết quả CSV và DB kiểm thử. Không ghi đè báo cáo của phiên khác; dùng out-dir riêng khi chạy script hỗ trợ.

## 3. Kết quả kiểm mã J05c

Đã đọc nhánh TRAT, `_family_of`, truyền phương án ở `wall_works`, evidence trong `compute_rough`, comment WorkItem và CSV/test mới. Không thấy lỗi công thức +10% hoặc nhân lặp trong đường đã kiểm. Thiếu variant không dùng biến chưa gán. CAN_NEN giữ đường cũ. Trạng thái vật liệu thiếu giữ D, không xóa diện tích TRAT đã biết.

Reviewer tự chạy:

```text
.venv/Scripts/python.exe -m pytest tests/test_rough_plaster.py tests/test_rough_materials.py tests/test_rough_walls.py tests/test_rough_status.py -q
43 passed in 16.86s
```

Hash CSV khớp bàn giao:
`0E677EAA3CFFEB4AFFD1FA3BAAAFB35C288F63E05EC39481E73C437CB092D542`.

Reviewer chạy riêng bài Claude báo lỗi:

```text
.venv/Scripts/python.exe -m pytest "tests/test_drawing_io.py::test_real_drawing_read_in_world_coords[nha_huong_hai_duong_7x12_kien_truc.dxf]" -q
1 passed in 39.31s
```

Không tái hiện lỗi IndexError trong lần chạy riêng. Không suy kết quả này thành toàn bộ suite đã đạt hoặc chắc chắn lỗi ngoài J05c. Không sửa encoding.py của phiên khác. Sau khi hoàn tất sửa dữ liệu, chạy lại toàn suite một lần trong trạng thái workspace được ghi nhận; nếu còn lỗi, giữ trace và đối chiếu riêng. Chưa cần sửa encoding theo phỏng đoán.

Bổ sung kiểm nhỏ còn thiếu trong test: phương án tồn tại nhưng family trống (khác phương án không tồn tại), TRAT quantity=None với nền hợp lệ. Chứng minh thiếu tương ứng giữ lượng trống và lý do; không mở cơ chế gộp Q02.

Lý do thiếu hiện chỉ ghi họ và dày, chưa nêu nhóm mã AK.213-216 cho AAC như bảng thiết kế cũ hứa. Có thể bổ sung giải thích chung ở tài liệu/đầu ra phù hợp mà không hardcode danh sách mã AACxx; hoặc sửa kỳ vọng tài liệu cho đúng phạm vi đã triển khai. Không cần triển khai bảng không nung trong J05c.

## 4. Chốt bản 2 J05b và J05d

**J05b được chốt về hành vi:** `van_ep_af83` là lựa chọn hệ riêng có C, không nâng lựa chọn cũ; ánh xạ SAN/DAM/GIANG_TUONG/COT chữ nhật; MAI và các dạng chưa có căn cứ giữ thiếu. Không đổi số liệu nguồn. Dòng vật liệu khác thiếu phải còn sau lọc và sau khi ba mã chính được bổ sung. Đây vẫn là hao phí định mức, không lượng mua/thuê ban đầu.

**Metadata raw_class:** phương án A hợp lý hơn vá riêng cho hai gói vì truyền được ý nghĩa dòng chưa có mã mà không đoán tên. Codex chấp thuận về thiết kế, **chưa thay thế sự duyệt lược đồ DB của chủ đồ án** theo quy định kho. Không viết migration hoặc chạy ALTER trước khi được duyệt. Không cần dừng việc chuẩn bị bản mô tả thay đổi dưới đây:

- Cột tùy chọn `rough_norms.raw_class`, CSV cùng tên, Norm cùng tên; NULL ở dữ liệu cũ không đổi hành vi.
- Chỉ gợi ý cho dòng chưa có mã; dòng có material_id thì danh mục là nguồn chính. Kiểm giá trị thuộc tập lớp đã có.
- Khi nhiều phần góp gộp cùng khóa nhưng gợi ý lớp mâu thuẫn: báo lỗi/xung đột cụ thể, không chọn tùy thứ tự ghi. Định nghĩa điều này trước khi sửa `_Bill.add`.
- Migration và rollback chỉ tác động cột mới; rollback schema phải đi cùng rollback code/CSV để không để loader đọc cột không tồn tại. Không đổi CP04 bộ sang kg, không thêm sản phẩm thật thiếu nguồn.
- Kiểm đường lọc compute_rough/optimizer và CSV/DB, không chỉ test materials_for_works.

**J05d giai đoạn 1:** thông báo chung mới đúng phạm vi; giữ riêng lý do thiếu sản phẩm/liều ở dòng hiển thị. Câu “không đổi lược đồ” trong mục 3 bản 2 phải sửa: bản 2 đã đề xuất raw_class có đổi schema; chỉ phần thêm hai dòng/thông báo là không cần schema nếu xét riêng.

**J05d giai đoạn 2:** chỉ giữ dưới dạng đề xuất. Bảng lịch sử còn `dose_pct_cement`/`confirmed_by` nhưng hợp đồng mới dùng `dose_fraction`/`confirmed_on`, dễ nhầm khi triển khai. Đánh rõ bảng cũ đã bị thay hoặc bỏ; nêu trường người xác nhận và nguồn mật độ nếu cần trước khi trình duyệt sau. Không mở giai đoạn 2 để xử lý việc J05c chưa đồng bộ DB.

## 5. Giao lượt tiếp theo

Claude xử lý mục 1-3 cho J05c, hoàn thiện thông tin bản 2 ở mục 4; chưa tự nạp DB thật, chưa triển khai J05b/J05d khi schema còn chờ duyệt. Được tiếp tục công việc chuẩn bị không phụ thuộc schema, không phải xin lại hợp đồng J05c đã chốt.

Chưa nghiệm thu J04/J05 trên công trình, D02 vẫn phải có người kiểm xác nhận. Không sửa cases/đáp án thực hoặc nâng KPI. Không có phiên điều phối đang chạy là giới hạn phối hợp đã ghi, không phải bằng chứng mã sai; quyền sửa đoạn nhỏ J05c đã được review vòng 1 cho phép. Giữ nhật ký đợt song song trong tài liệu riêng; chưa tự ghi đè file tổng hợp.

Review này chỉ tạo tài liệu, chạy test và đọc DB. Không sửa mã/CSV/SQL/DB hoặc chạy lại check_data ghi đè báo cáo. Không chạy lại toàn suite trong lượt này; số 390/3/1 là báo cáo Claude, không phải kết quả reviewer tự chạy.
