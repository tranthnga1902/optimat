# Khóa cặp ứng viên VN002 — kiểm tra nội bộ

Manifest `data/ground_truth/du_toan/incoming_20261103.json` ghi `source_id=VN002_nha_pho_4_tang_4x15`, `cong_trinh_id=nha_sang_hai_duong_4x15`, `split=build` và liên kết hai tệp bên dưới. Đây là khóa danh tính byte của **cặp ứng viên** cho kiểm tra nội bộ, chưa phải xác nhận hai bản cùng phiên bản thiết kế.

| Vai trò | Tệp (tính từ thư mục optimat-ai) | Byte | SHA-256 | Đơn vị khai báo |
| --- | --- | ---: | --- | --- |
| KT | `data/drawings/build/nha_sang_hai_duong_4x15_kien_truc.dxf` | 17.232.252 | `719ea17b22b856bb31363fbfc9bf218f312112958e9de4f6638e2ede1f1cf8d6` | `HEADER/$INSUNITS`, group 70 = 4: mm |
| KC | `data/drawings/build/nha_sang_hai_duong_4x15_ket_cau.dxf` | 15.295.031 | `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c` | `HEADER/$INSUNITS`, group 70 = 0: không khai báo đơn vị |

SHA-256 nhận diện đúng nội dung tệp tại lúc kiểm, không phải mã phiên bản thiết kế. Đơn vị khai báo trong header không chứng minh tỷ lệ hình học; riêng KC cần xác định đơn vị trước khi dùng kích thước.

**Phiên bản thiết kế: chưa xác định (`null`).** Manifest là bằng chứng liên kết quản lý, chưa xác minh độc lập khung tên, sự tương thích kỹ thuật KT/KC hay quan hệ chuyển đổi DWG→DXF. Metadata nguồn liệt kê `HO SO KET CAU NHA A SANG - HAI DUONG   15-10-2021.dwg`; ngày nằm trong tên tệp, không đủ xác nhận ngày phát hành hoặc revision. Tên `BO KY THUAT NHA A SANG.dwg` cũng không tự chứng minh nguồn của DXF KT. Chưa kiểm tra khung tên hoặc xác nhận công trình đã xây dựng.

Chủ đồ án đã cho phép kiểm tra nội bộ theo chỉ đạo hiện tại. Quyền huấn luyện mô hình và phân phối lại chưa được xác nhận; metadata nguồn cũng ghi quyền chưa rõ. Phạm vi thực hiện: đọc byte để tính hash, kích thước, header đơn vị và metadata; không chạy bộ đọc CAD đầy đủ, bóc tách, database hay runtime. Dữ liệu máy đọc được tại [PAIR_LOCK.json](PAIR_LOCK.json).
