# Sửa nhận cột theo đường bao — 04/11/2026

Theo nhiệm vụ 00 giao 05: chỉ sửa `rough/columns.py::signal_columns` và thêm `tests/test_rough_column_contours.py`. Không sửa `detect_columns`, raster hatch, schema/DB/runtime hoặc canonical vật liệu. Đã đọc ownership hiện tại của 01: 03 giữ structural_column_instances/structural/takeoff, 06 giữ project_analysis; không sửa các hunk này. Những thay đổi có sẵn trong columns.py (raster chia cụm và column_works/dimensions) được giữ, không reset file về HEAD. Không gửi tin tự động sang chat khác; bàn giao bằng artifact và phản hồi trong chat này.

## Lỗi và cách sửa

Trước: union các nét theo đầu mút, chỉ kiểm bbox nằm trong kích thước cột, nên L/U/đường chéo/hình nơ/hình thang đều có thể thành cột. Hai cạnh bị làm tròn bước10mm:225×335 thành220×340.

Sau: giữ phân loại layer/block và nhóm nét hiện có; kiểm các đoạn phủ liên tục **cả bốn cạnh khung bao chữ nhật theo trục x/y**, bằng tọa độ thật (epsilon1e-6mm). Cho phép cạnh chia đoạn, đoạn trùng/chồng, đường chéo/nét phụ bên trong nếu bốn cạnh vẫn đủ. Không dùng đầu mút làm tròn làm bằng chứng kín; khe0,5mm vẫn bị từ chối. Giữ b_mm/h_mm đo được, không ép về bội10. Tâm vẫn theo hợp đồng cũ làm tròn0,1mm.

## Tái hiện và kiểm

- Trước sửa source:14 ca mới đều fail (6 hình không đủ chữ nhật,6 ca kích thước/translation/block,2 ca normal rough entrypoint). Hai ca block lúc đầu thiếu quy tắc ký hiệu trong fixture; sau đó test cấu hình riêng match_block_signal cho block, không thêm quy tắc canonical. Không gọi toàn bộ14 failure là14 lỗi sản phẩm độc lập.
- Sau sửa:18/20 đạt; hai block fixture cần cấu hình như trên. Lượt rộng đầu41passed/15errors do pytest không tạo được basetemp sandbox, không phải15 regression sản phẩm. Lượt workspace55passed/1failed do DXF fixture chưa khai báo mm; đã đặt INSUNITS=4, không sửa reader để làm test qua.
- Cuối: **56 passed in12.41s, exit0**, session8252 đã terminal. Lệnh: `.venv/Scripts/python.exe -m pytest tests/test_rough_column_contours.py tests/test_rough_columns.py tests/test_rough_takeoff.py tests/test_rough_joints.py tests/test_s04_walls.py -q -p no:cacheprovider --basetemp=docs/review/data20_05/column_contour_fix/pytest_temp2`. Log `focused_final.log`.
-15 ca mới:6 false-positive negatives;6 true-positive contour có split/nét phụ/translation/block;2 `rough_from_drawing → compute_rough` kiểm số cột/kích thước/thể tích;1 DXF thực thi `read_drawing → detect_columns → column_works` với INSERT dịch chuyển và hai hình giả. Mọi dữ liệu mới là SYNTHETIC.
- Probe cùng bytes của00: SHA256 fixture `af4efc2420327ae2a4f8a032cce0ffcd291a5b6ee4dff35bf1ffebd39558ff52`; trước3cột220×340/tổng0,781m³ theo `data20_00/column_accuracy_probe/before.json`; sau **1cột225×335, raw0,262305m³, công tác0,262m³**. Input probe05 height3500/slab20, tức cao tính3,48m; đây là đầu vào tổng hợp, không phải thông số VN002. `after_probe.json` lưu hash/source/test và kết quả.
- Lệnh probe riêng ban đầu kế thừa DATABASE_URL Windows, loader thử kết nối nhưng bị sandbox từ chối trước khi probe chạy; không có truy vấn/ghi thành công. Đã bỏ DATABASE_URL/URLtest/APIkey trong child trước import và chạy lại CSV thành công. Không đổi biến môi trường chung hoặc xin mở kết nối DB.

## Artifact và giới hạn

`signal_columns.patch` chỉ diff hàm được sửa so phiên bản trước giống HEAD, không đại diện toàn bộ uncommitted diff của columns.py. Test mới ở `tests/test_rough_column_contours.py`; source SHA256 sau sửa `c0146428bd3f348a553b310cbe5f7813ca2b91eac38f622c6d0663c14f74e748`, test SHA256 `cea7c3df770af4efd7c498685a08e8f5a702b77eb18c666824af8cf1527df6b4`. Các log lượt lỗi giữ nguyên, không ghi đè thành pass.

Giới hạn: chỉ chữ nhật theo trục WCS và đúng layer/block đã khai báo. Không suy đường bao chữ nhật bất kỳ là cột kết cấu đã duyệt; vẫn cần kiểm người dùng/nguồn. Cột xoay, hình bất quy tắc, nét hở thật, contour có nét kéo ra ngoài bbox có thể không được nhận; không nới bbox để tự đoán. Nhánh hatch/raster và ưu tiên hatch khi trùng contour giữ nguyên nên không claim đã sửa độ chính xác kích thước hatch. Không chạy full suite, CAD thật, API/browser/runtime hoặc DB; chưa công bố accuracy trên nhà ở thực tế. Chờ00 chạy lại probe độc lập và01/15 review trước phát hành.
