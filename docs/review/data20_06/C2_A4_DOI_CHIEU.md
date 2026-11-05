# Đối chiếu nguồn C-2 tại 4/A — kiểm tra nội bộ

Đã xem độc lập các ảnh trích trong [VN002_C2_A4.md](../data20_00/VN002_C2_A4.md) và trích lại khung tên bốn trang PDF kết cấu. Số trang dưới đây tính từ 1.

| Trang | Mã tờ theo khung tên | Đối chiếu trực quan |
| --- | --- | --- |
| 19 | [KC-02-01](C2_KHUNG_TEN_P19.png) | Mặt bằng định vị cột tầng 1–2–3; tại giao trục 4/A có ký hiệu C-2, ghi 22×22 và kích thước cạnh 220. |
| 22 | [KC-02-04](C2_KHUNG_TEN_P22.png) | Chi tiết cột C-2; mặt cắt 2–2 có hai cạnh 220, hai cao độ +3.150 và +6.750, chênh 3.600 mm; `SL=02` là nhãn số lượng của loại cột. |
| 23 | [KC-03-01](C2_KHUNG_TEN_P23.png) | Mặt bằng kết cấu sàn tầng 2; ô trục 3–4/A–B cạnh cột 4/A ghi +3.150 và H=120 mm. |
| 24 | [KC-03-02](C2_KHUNG_TEN_P24.png) | Mặt bằng kết cấu sàn tầng 3; ô trục 3–4/A–B cạnh cột 4/A ghi +6.750 và H=120 mm. |

PDF nguồn `HỒ SƠ KẾT CẤU.pdf` có SHA-256 `4b6ca4f97e80b85ae4d1df555f13ad1b531c8243f52f300ec34d436357060344`, khớp metadata và manifest. Hai DXF được kiểm lại hash: KT `719ea17b22b856bb31363fbfc9bf218f312112958e9de4f6638e2ede1f1cf8d6`; KC `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`, khớp [PAIR_LOCK.json](PAIR_LOCK.json). Cặp PDF–DXF chưa có chứng cứ nguồn chuyển đổi hoặc cùng revision; cùng tên công trình và tháng hoàn thành không xác nhận cùng lần phát hành.

Các giá trị vị trí, tiết diện và cao độ đã đối chiếu ở trên hỗ trợ phép tính hình học của báo cáo gốc; quy ước phân bổ giao cột–dầm–sàn vẫn cần được kiểm trong phạm vi BOQ và không coi là khối lượng thực tế thi công. Phạm vi này kiểm một đoạn tại 4/A, không nhân `SL=02` hay suy sang 4/B. Chưa chạy ứng dụng hoặc kiểm database.
