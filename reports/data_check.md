# Kiểm soát dữ liệu OptiMat AI (2026-10-19, nguồn postgresql)

Kết quả: **ĐẠT** · 0 lỗi · 44 cảnh báo · 2 ghi chú

| Hạng mục | Số liệu |
|---|---|
| Vật liệu (vật liệu tường) | 99 (16) |
| Phương án tường (đủ số liệu tối ưu) | 20 (2) |
| Theo lớp tường: phương án / đủ số liệu | 110: 7/1, 150: 3/0, 220: 5/1, 330: 0/0 |
| Tên gọi khác, quy tắc bóc tách | 277, 27 |
| Nhà cung cấp, dòng giá đại lý (có giá) | 3, 14 (14) |
| Vật liệu tường đã có giá | 0/16 |
| Lịch sử giá (price_records): tổng / thật | 1248 / 0 |
| Đáp án đo tay: bản vẽ, theo nhóm | 1, {'build': 1} |

## Cảnh báo (44)

| Khu vực | Mục | Nội dung |
|---|---|---|
| dap_an | data/ground_truth | Chưa có bản vẽ nhóm test có đáp án đo tay: chưa có số sai số để báo cáo. |
| dinh_muc_phan_tho | dinh_muc_phan_tho.csv | 22/22 dòng định mức còn trống, chờ tra TT 38/2026: công tác dùng các dòng này chưa ra vật liệu mua về. |
| gia | 16 vật liệu tường | Chưa có giá đại lý nào: AAC01, AAC02, AAC03, ALC01, ALC02, GK01, GK02, GK03, GK04, GN01, GN02, GN03, PN01, TN01, TN02, TN03. |
| gia | price_records | Chưa có dòng giá THẬT (ACTUAL): mô hình giá chỉ học trên dữ liệu mô phỏng, chưa dùng được để báo cáo độ chính xác. |
| nguon_cung | SUP_A | Chưa có liên kết (Google Maps, website): kết quả tối ưu không dẫn link được. |
| nguon_cung | SUP_B | Chưa có liên kết (Google Maps, website): kết quả tối ưu không dẫn link được. |
| nguon_cung | SUP_C | Chưa có liên kết (Google Maps, website): kết quả tối ưu không dẫn link được. |
| nguon_cung | supplier_materials | Có 14 dòng giá MẪU hoặc MÔ PHỎNG: không dùng để báo cáo. |
| phuong_an_tuong | W-AAC01-100 | Chưa đủ số liệu để tối ưu, thiếu: khối lượng tường kg/m². |
| phuong_an_tuong | W-AAC02-150 | Chưa đủ số liệu để tối ưu, thiếu: khối lượng tường kg/m². |
| phuong_an_tuong | W-AAC03-200 | Chưa đủ số liệu để tối ưu, thiếu: khối lượng tường kg/m². |
| phuong_an_tuong | W-ALC01-100 | Chưa đủ số liệu để tối ưu, thiếu: số lượng vật liệu / m² tường, công / m² tường, khối lượng tường kg/m². |
| phuong_an_tuong | W-ALC02-150 | Chưa đủ số liệu để tối ưu, thiếu: số lượng vật liệu / m² tường, công / m² tường, khối lượng tường kg/m². |
| phuong_an_tuong | W-GK01-110 | Chưa đủ số liệu để tối ưu, thiếu: số lượng vật liệu / m² tường, công / m² tường, khối lượng tường kg/m². |
| phuong_an_tuong | W-GK01-220 | Chưa đủ số liệu để tối ưu, thiếu: số lượng vật liệu / m² tường, công / m² tường, khối lượng tường kg/m². |
| phuong_an_tuong | W-GK02-190 | Chưa đủ số liệu để tối ưu, thiếu: hệ số dẫn nhiệt λ. |
| phuong_an_tuong | W-GK03-100 | Chưa đủ số liệu để tối ưu, thiếu: khối lượng tường kg/m², hệ số dẫn nhiệt λ. |
| phuong_an_tuong | W-GK04-xx | Chưa có lớp nhận diện bản vẽ (chiều dày): bóc tách không quy về được phương án này. |
| phuong_an_tuong | W-GN02-110 | Chưa đủ số liệu để tối ưu, thiếu: số lượng vật liệu / m² tường, công / m² tường, khối lượng tường kg/m². |
| phuong_an_tuong | W-GN02-220 | Chưa đủ số liệu để tối ưu, thiếu: số lượng vật liệu / m² tường, công / m² tường, khối lượng tường kg/m². |
| phuong_an_tuong | W-GN03-105 | Chưa đủ số liệu để tối ưu, thiếu: khối lượng tường kg/m². |
| phuong_an_tuong | W-GN03-150 | Chưa đủ số liệu để tối ưu, thiếu: khối lượng tường kg/m². |
| phuong_an_tuong | W-PN01-xx | Chưa có lớp nhận diện bản vẽ (chiều dày): bóc tách không quy về được phương án này. |
| phuong_an_tuong | W-TN01-xx | Chưa có lớp nhận diện bản vẽ (chiều dày): bóc tách không quy về được phương án này. |
| phuong_an_tuong | W-TN02-xx | Chưa có lớp nhận diện bản vẽ (chiều dày): bóc tách không quy về được phương án này. |
| phuong_an_tuong | W-TN03-xx | Chưa có lớp nhận diện bản vẽ (chiều dày): bóc tách không quy về được phương án này. |
| phuong_an_tuong | lớp 150 | Lớp 150 chưa có phương án nào đủ số liệu để tối ưu. |
| phuong_an_tuong | lớp 330 | Chưa có phương án tường nào cho lớp 330: tường 330 nhận diện được nhưng không gán được vật liệu. |
| vat_lieu | AAC01 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | AAC02 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | AAC03 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | ALC01 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | ALC02 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | GK01 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | GK02 | Vật liệu tường còn trống: hệ số dẫn nhiệt λ, hao hụt thi công (%). |
| vat_lieu | GK03 | Vật liệu tường còn trống: khối lượng / đơn vị, hệ số dẫn nhiệt λ, hao hụt thi công (%). |
| vat_lieu | GK04 | Vật liệu tường còn trống: khối lượng / đơn vị, hao hụt thi công (%). |
| vat_lieu | GN01 | Vật liệu tường còn trống: hao hụt thi công (%). |
| vat_lieu | GN02 | Vật liệu tường còn trống: khối lượng / đơn vị, hao hụt thi công (%). |
| vat_lieu | GN03 | Vật liệu tường còn trống: khối lượng / đơn vị, hao hụt thi công (%). |
| vat_lieu | PN01 | Vật liệu tường còn trống: khối lượng / đơn vị, hệ số dẫn nhiệt λ, hao hụt thi công (%). |
| vat_lieu | TN01 | Vật liệu tường còn trống: khối lượng / đơn vị, hao hụt thi công (%). |
| vat_lieu | TN02 | Vật liệu tường còn trống: khối lượng / đơn vị, hao hụt thi công (%). |
| vat_lieu | TN03 | Vật liệu tường còn trống: khối lượng / đơn vị, hao hụt thi công (%). |

## Ghi chú (2)

| Khu vực | Mục | Nội dung |
|---|---|---|
| dap_an | data/sample/sample_floor.dxf | Bản vẽ mẫu tự tạo, chỉ để kiểm thử mã. |
| dap_an | data/sample/sample_floor.dxf | Bản vẽ mẫu tự tạo, chỉ để kiểm thử mã. |
