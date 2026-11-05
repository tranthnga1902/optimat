# Bản vẽ

- `build/`: bản vẽ dùng để chỉnh quy tắc và ngưỡng nhận diện (nhà phố, nhà dân, kết cấu do người dùng cung cấp;
  `tan_binh_kien_truc.dxf`, `tan_binh_ket_cau.dxf` = bộ 46 Nhà Tân Bình, đổi từ DWG ngày 02/11/2026).
- `test/`: bản vẽ chỉ dùng để báo cáo sai số, không xem khi chỉnh quy tắc (`banve1_kien_truc.dxf`, `banve1_ket_cau.dxf`:
  nhà phố Dĩ An, có dự toán `data/ground_truth/du_toan/banve1_nha_pho_di_an.csv`).
- `raw_20261102/`: hồ sơ gốc người dùng gửi (DWG kiến trúc, kết cấu, điện, nước, biện pháp thi công, dự toán .xls).

File `.dxf`, `.dwg` không đưa vào git (lớn). Xem trang kiểm tra: `/do-boc` của frontend.
