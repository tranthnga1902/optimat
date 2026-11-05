# Trích kiểm khung tên VN002 và hai chú thích DM-1

## Phạm vi mẫu

Chỉ xét **phần thô nhà ở riêng lẻ xây mới không quá 5 tầng**. Khung tên PDF ghi “Nhà ở gia đình”, là căn cứ về loại công trình; tên gói `VN002_nha_pho_4_tang_4x15` ghi 4 tầng, nhưng lượt này chưa kiểm chứng số tầng theo bản vẽ thiết kế và chưa xác minh tính chất xây mới. Vì vậy giữ VN002 **chờ xác minh điều kiện phạm vi**, chưa tính là mẫu đủ điều kiện. Các hồ sơ ngoài phạm vi được loại khỏi mẫu số kèm lý do; hồ sơ chưa rõ được giữ chờ xác minh. DM-1 đang xét là chi tiết bể nước thuộc hồ sơ căn nhà, không coi là hồ sơ công trình bể độc lập hoặc mở rộng sang thiết kế bể độc lập.

Phạm vi: quét có chọn lọc chữ trong hai DXF đã khóa ở [PAIR_LOCK.md](PAIR_LOCK.md), lấy trích đoạn theo handle và tọa độ; sau đó đọc hai ảnh khung tên trích từ PDF nguồn có hash khớp manifest. Không dựng toàn bộ CAD, không kiểm database/API/runtime hay biến đổi block DXF. Đây là kết quả **một phần**; các tọa độ dưới đây là tọa độ thô trong DXF, không suy đơn vị KC.

## Bổ sung: khung tên PDF đã xem trực quan

Ảnh [KT-01](../data20_00/VN002_KT01_KHUNG_TEN.png) và [KC-01-11](../data20_00/VN002_KC0111_KHUNG_TEN.png) đều thể hiện chủ đầu tư **Anh Sang**, địa chỉ **Hải Dương**, tên dự án **Nhà ở gia đình**, hạng mục **Bản vẽ sơ bộ**, và mục **Hoàn thành: 10/2021**. KT-01 là tờ đại diện được trích; khung tên KC-01-11 ghi tên bản vẽ **Chi tiết bể nước**, trang 17 của PDF kết cấu. Ô tên bản vẽ trong ảnh KT-01 để trống. Các hàng đánh số 1–5 trong bảng nội dung điều chỉnh đều không có nội dung; dòng hợp đồng không có ngày cụ thể. Không coi các số hàng trống là số revision hay ngày hoàn thành là ngày phát hành.

Đã tính lại hash byte hai PDF nguồn: `HỒ SƠ KIẾN TRÚC PDF.pdf` là `59cad635a392c11f061d5a4f78406c00b4248f810643b9332d4b085e0809ea88`; `HỒ SƠ KẾT CẤU.pdf` là `4b6ca4f97e80b85ae4d1df555f13ad1b531c8243f52f300ec34d436357060344`. Cả hai khớp metadata nguồn và manifest nhập; PAIR_LOCK khóa hash của hai DXF, không chứng minh quan hệ chuyển đổi hay đồng phiên bản giữa PDF và DXF. Hai khung tên thống nhất các thông tin nêu trên, nhưng **chưa chứng minh cùng revision hoặc cùng lần phát hành**. Chưa có phiếu phát hành hoặc giao nhận xác nhận hai bộ.

## Trích đoạn tìm thấy

| Tệp | Handle / owner | XY thô | Trích nguyên văn trường chữ DXF | Nhận xét |
| --- | --- | --- | --- | --- |
| KT | `5BA` / `57D` | 1896547.538, -943963.808 | `%%Uhoµn thµnh: 10/2021` | Chữ kiểu font VnAvantH trong định nghĩa block; `%%U` là mã định dạng. Chưa chứng minh ngày phát hành hoặc vị trí trên tờ đại diện. |
| KC | `1163045` / `115D5E3` | 1896547.538, -943963.808 | `%%Uhoµn thµnh: 10/2021` | Chữ nằm trong định nghĩa block; chưa gắn được với tờ DM-1. |
| KT | `692` / `57D` | 1897388.980, -922431.719 | `%%Uanh sang` | Chữ trong block, chưa đủ khẳng định tên đầy đủ của công trình tại khung tên tờ được chọn. |
| KC | `116311B` / `115D5E3` | 1897388.980, -922431.719 | `%%Uanh sang` | Chữ trong block, chưa xác nhận biến đổi/điểm chèn hay tờ áp dụng. |
| KT | `6067455` / `2` | 1386688.888, -109055.916 | `KT-01` | Đã tìm thấy mã chữ; chưa đối chiếu vị trí với khung tên trực quan. |
| KT | `6068B47` / `2` | 1389046.1, -108310.1 | `MÆT B»NG M¸I` | Chữ thô kiểu font cũ ở vùng gần mã KT-01; khoảng cách tọa độ không đủ chứng minh chúng nằm cùng tờ. |
| KC | `11914C9` / `1F` | -1478898.582, -1084965.478 | `KC-01-09` | Mã tờ dạng chữ trong không gian mô hình, chưa xác minh thuộc chú thích DM-1 nào. |
| KC | `1172208` / `1F` | -1427894.297, -1084964.178 | `KC-01-10` | Mã tờ dạng chữ trong không gian mô hình, chưa xác minh thuộc chú thích DM-1 nào. |
| KC | `11730A7` / `1F` | -1437212.338, -1058717.022 | `dm-1: l=2500mm; sl=02` | Chú thích thứ nhất; `11730A6` tại (-1438866.279, -1058217.022) ghi `%%UmÆt c¾t dÇm mãng dm-1` theo mã chữ/font bản vẽ. |
| KC | `11732A5` / `1F` | -1386567.052, -1058718.323 | `dm-1: l=2500mm; sl=02` | Chú thích thứ hai; `11732A4` tại (-1388220.993, -1058218.323) ghi cùng tiêu đề mã chữ/font. |

Các trích đoạn được chép từ giá trị chữ trong DXF; chuỗi chữ có dấu dùng font/mã tiếng Việt cũ nên không coi ký tự thô là bản phiên âm đầy đủ. Hai dòng `dm-1` nói `sl=02` nhưng không tự chứng minh hai chú thích là cùng một cấu kiện hay cùng tờ. Quan hệ với bể nước và ánh xạ chính xác tờ–khung tên cần xem hình và kiểm biên tờ/điểm chèn block, chưa được xác minh ở đây.

## Chưa xác nhận

- Đã đọc tên dự án và mã tờ KT-01/KC-01-11 trong ảnh PDF; chưa xác minh mối liên hệ PDF–DXF hoặc ánh xạ các handle DM-1 với tờ bằng hình học/block.
- Ngày hoàn thành `10/2021` đã thấy trực quan trong hai khung tên PDF được trích. Ngày phát hành: chưa tìm được bằng chứng phù hợp trong phạm vi kiểm tra.
- Số revision, lịch sử sửa, phiếu phát hành: chưa tìm được bằng chứng phù hợp trong phạm vi trích kiểm; không kết luận không tồn tại. Danh mục có các mã KT/KC dạng chữ, chưa xác nhận đầy đủ danh mục hay phiếu phát hành.
- Không suy ngày trong metadata/tên file, hoặc cùng chữ `10/2021`, thành cùng revision. Phiên bản thiết kế của cặp vẫn chưa xác định. Muốn khép đối chiếu cần kiểm trực quan tờ, khung tên, điểm chèn và hồ sơ phát hành gốc được phép sử dụng.
- Với DXF KT, đã kiểm tra chữ và điểm chèn block trong một vùng quanh `KT-01`; chưa tìm được liên hệ chắc chắn với hai chi tiết bể nước. Đây là giới hạn của lượt trích kiểm, không khẳng định các thông tin đó vắng mặt.

Nguồn: hai tệp và SHA-256 nêu tại [PAIR_LOCK.json](PAIR_LOCK.json). Tệp gốc không bị thay đổi.
