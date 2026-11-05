# Nguồn bảng thép và cổng bind mark → đoạn cột

Ngày04/11/2026. Bổ sung chỉ đọc; không sửa rebar/reader/source freeze hoặc chạy test. Các trị số native dưới đây do04 bàn giao theo KC SHA22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c;03 chưa tự đọc lại các INSERT/ATTRIB này trong lượt bổ sung. Đây là locator/fact cần đối chiếu, không phải đáp án đã duyệt.

## Nguồn04 báo

| Group | Mark/source | Thuộc tính được báo | Giới hạn |
|---|---|---|---|
| C-2 TEXT118CDEF, SL2 TEXT118CDF0 | mark3 TK_2 INSERT118CDA7; mark4 INSERT118CDB3 | DK20,DAI4300,SL1=2,SLA=4,DT17.2,TL42.4 mỗi dòng | Chưa chứng minh mark thuộc đoạn đích hoặc chia cho4/A/4/B |
| C-2 | mark7 INSERT118CDD7 | DK6,DAI800,SL1=77,SLA154,TL27.3 | Nguồn toàn cột, không tự thành đai riêng đoạn3150→6750 |
| C-1 | INSERT118CCC5/118CCD1 | Trùng trị số với các dòngC-2 được báo | Không join theo Ø/L/tổngkg |
| C-1a | INSERT118CD2A/118CD36 | Trùng đến SL1, SLA8 | Số tổng khác không đủ làm group identity hoặc phạm vi đoạn |

## Cổng liên kết tổng quát cần đủ

1. Khóa file/revision/hash + bảng/group + rootINSERT/handlepath + mark trong group. Mark3 củaC-1 khác mark3 củaC-2, kể cả tất cả số đo giống nhau.
2. Nối mark từ bảng tới ký hiệu/leader trên đúng hình chi tiếtC-2, rồi tới đoạn cao độ hoặc phần thanh thực sự bao phủ đoạn. Khớp Ø/L chỉ là kiểm tra chéo, không là bằng chứng bind.
3. Phân biệt tổng số cho nhóm cột, số cho một cột và số áp dụng đoạn; giữ nguồn hệ số. Không tự chia SLA cho2 hoặc nhân theo số tầng để ra lượng4/A.
4. Chiều dài cắt4300 không đồng nhất cao đoạn3600; phần neo/nối/uốn không suy từ hiệu700. Thanh đi qua nhiều đoạn cần quy ước phân bổ và nguồn, không tính lại theo kg/m³.
5. Mark7 toàn cột phải giữ whole-member/scope_pending cho mục tiêu một đoạn nếu chưa có phân bố. Không trừ/lấy tỷ lệ chiều cao, không đoán số đai từ a200 nếu chưa có vùng đai/gối/neo đầy đủ.
6. Có bản ghi nguồn đo được nhưng chưa có bind thì giữ lượng của dòng bảng đúng scope gốc và missing của đoạn; không đổi thành số0, không cộng vào segment khác để có giá.

## Lỗi phân loại mã đã xác định từ source

`src/optimat/rough/rebar.py::element_code` khoảng dòng197–203 tách text bằng regex `[\s(),:;-]+` trước khi gọi structural.element_of. Vì vậy C-2 bị tách thành C và2, dù element_of đã nhận C-2 ở nhánh cột. Cần chủrebar kiểm cách giữ dấu nối bên trong mã, đồng thời vẫn tách dấu phân cách chú thích.03 không sửa file này hoặc CSV; đây không phải vấn đề được giải bằng bind theo số tổng.

## Trạng thái

GrossACTUAL4/A từ final_v3 giữ nguyên. Chưa bind bất kỳ mark thép mới nào vào đoạn; không phát kg/nhu cầu mua/mã vật liệu cho đoạn từ báo cáo này. Giao01 điều phối05 kiểm tokenizer/group header và04 giữ nguồn bảng,03 chỉ mở bind khi có đủ đường nối hình chi tiết. Giữ20bảng.
