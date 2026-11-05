# Ranh giới bảng thép — bản sửa staging đã kiểm

**Cập nhật cuối theo00:** đã chụp `staging/rebar.base.py`, sửa riêng `staging/rebar.py`, không ghi source canonical. `staging/read_table.patch` là diff để01review/áp đúng hunk; hash base/candidate/canonical/test tại `staging_receipt.json`. Kiểm AST xác nhận chỉ hàm read_table đổi, các class/function khác (collect/resolve/scope/provenance) giữ nguyên. Những đoạn “chưa sửa” bên dưới là lịch sử trước lượt staging.

Kết quả cuối **135passed in9.01s,exit0**, session59010 terminal, `stage_final.log`. Chạy qua `staging/run_tests.py`: nạp module candidate đúng namespace `optimat.rough.rebar` trong child trước import caller, assert __file__ đúng staging; test vẫn gọi public collect/rough thật, không mock parser hoặc scope. Child bỏ DATABASE_URL/URLtest/APIkey, bỏ dotenv/LLM. Lệnh: `.venv/Scripts/python.exe docs/review/data20_05/rebar_table_fix/staging/run_tests.py tests/test_rebar_table_boundaries.py tests/test_rough_rebar.py tests/test_rough_partial.py tests/test_rough_takeoff.py -q -p no:cacheprovider --basetemp=docs/review/data20_05/rebar_table_fix/temp_stage_final`.

Bốn ca lỗi ban đầu đã qua; thêm2ca title căn giữa + kg tính đúng từng bảng, title nằm giữa hai miền header phải rỗng/cảnh báo. Hồi quy gồm scope/dedup/table_manifest/hash/xác nhận nguồn và phần thiếu→công tác/vật liệu. Không chạy TestClient/API/DB/full suite.135pass là bằng chứng **staging**, không phải canonical đã sửa hoặc runtime đã phát hành.

Cách sửa: tách cụm header theo X (tên cột lặp hoặc khoảng cách tách lớn), chọn duy nhất miền phù hợp vị trí title, hợp tối đa HEADER_ROWS_MAX hàng chỉ trong miền đó; dừng khi gặp dữ liệu/tiêu đề mới, từ chối cột cùng tên ở vị trí mâu thuẫn. Chỉ khi có đường kính và chiều dài cắt trong miền local mới đọc dữ liệu. Nếu không có hoặc mơ hồ, trả cảnh báo thay vì mượn. Không sửa phép tính kg, scope hay mapping cấu kiện.

Giới hạn: miền bảng hiện suy từ bố trí TEXT/header, chưa dựa lưới/khung CAD hoặc block/table identity. Title lệch ra ngoài miền header, header bị tách từ đơn lẻ không khớp quy tắc, header sát/chồng/mất nhãn có thể bị giữ chưa nhận. Không chứng minh parser bao phủ mọi layout; chưa kiểm block TK_2 VN002. Các thông tin INSERT04 ở cuối chỉ là bàn giao, không là binding sản phẩm.01 cần so hash base trước áp patch; nếu source đã đổi thì review/rebase từng hunk, không chép đè cả file.

Nhiệm vụ00 giao: kiểm lỗi mượn header/hàng bảng bên cạnh trước khi sửa; không DB/TestClient/full suite. Đã đọc caller và source, chỉ thêm `tests/test_rebar_table_boundaries.py` và báo cáo riêng. Chưa sửa rebar.py vì đang có uncommitted scope/provenance của phiên khác, đã hỏi01 xác nhận hunk read_table.

## Caller không crop bảo vệ bảng

- API main.py nhận Drawing từ read_drawing rồi collect_rebar_tables trực tiếp (nhánh mapping scope); structural_parts cũng gọi read_rebar_schedules trên toàn Drawing.
- read_rebar_schedules → collect_rebar_tables → read_table(drawing,title), không crop riêng theo tiêu đề bảng.
- read_table lấy toàn bộ chữ dưới title, gom theo y rồi _header lấy lần khớp đầu cho từng tên cột. Chỉ sau chọn header mới giới hạn X. Hai bảng cùng hàng vì thế dùng chung header đầu. Header nhiều dòng chưa được hợp nhất vì mỗi row phải có đồng thời đường kính/chiều dài.

## Tái hiện công khai SYNTHETIC

Lệnh `.venv/Scripts/python.exe -m pytest tests/test_rebar_table_boundaries.py -q -p no:cacheprovider --basetemp=docs/review/data20_05/rebar_table_fix/temp_before`.

**4failed in6.79s,exit1**, session12972 đã terminal; `before.log` giữ nguyên:

1. Hai bảng C1/D1 cùng y, x0/x6000: phải giữ C1 L3200 N32 và D1 L2000 N5 riêng.
2. Cùng dữ liệu đảo thứ tự TextItem: không được đổi kết quả bảng.
3. Bảng trái thiếu đường kính header: phải rỗng và cảnh báo đúng bảng; bảng phải hợp lệ vẫn đọc N5, không mượn hàng/header bên trái.
4. Header đường kính và chiều dài nằm hai hàng chữ: phải giữ bảng C1/D1 riêng với N32/N5, không bỏ cả hai.

Đây là4case lỗi trước sửa, không phải4lỗi sản phẩm độc lập hay bằng chứng CAD thật. Không xfail/skip để che. Source/tests hiện có khác giữ nguyên.

## Hướng sửa nhỏ đề nghị sau cấp hunk

Chỉ read_table/tìm header + test mới, không sửa collect/resolve/scope/hash/cấp phối/vật liệu:

- Phân các cụm header theo X trước khi chọn cột; một hàng có tên cột lặp ở hai X khác nhau không được gộp thành một header. Chọn cụm có vị trí phù hợp title; nếu không xác định duy nhất thì cảnh báo và bỏ thay vì mượn.
- Khi hợp header nhiều dòng, chỉ xét các hàng liền kề trong cùng miền X đã xác lập và trước dòng dữ liệu/tiêu đề bảng kế tiếp. Không gom toàn file hoặc lấy hàng khác bảng để đủ đường kính/chiều dài.
- Giới hạn miền X cho cả tìm header lẫn đọc data; không dùng midpoint tiêu đề một cách mù quáng vì title có thể căn trái hoặc căn giữa và bảng rộng khác nhau.
- Giữ raw_cells/evidence/đơn vị/missing và cảnh báo scope hiện có. Sau sửa chạy4ca mới, test_rough_rebar và pure rough_partial/takeoff liên quan; không API TestClient/full/DB.

## VN002 và giới hạn

Bổ sung từ04/00 (bàn giao, chưa tự kiểm CAD): KC hash22cda910…; C-2 group TEXT118CDEF/(SL:2)118CDF0, TK_2 INSERT mark3=118CDA7/mark4=118CDB3. DK20,DAI4300,SL1=2,SLA4,TL42.4 trùng C-1 INSERT118CCC5/118CCD1. C-1A118CD2A/118CD36 trùng tới SL1 nhưng SLA8. Vì vậy không nối nguồn bằng bộ Ø/L/số lượng/kg. Mark7 INSERT118CDD7 DK6/DAI800/SL1=77/SLA154/TL27.3 được bàn giao là toàn cột, không tự chia vào đoạn. Cần group/occurrence/INSERT và liên kết mark tại chi tiết; layer/type proof chưa đủ trong report05, giữ unresolved. `element_code('C-2')` được04 báo None khác C2=COT; chưa sửa vocabulary hoặc chuẩn hóa dấu gạch để đoán cùng cấu kiện. Phạm vi này không bind các mark vào đoạn hoặc chốt khối lượng từng đoạn.

Không đọc lại CAD VN002 trong lượt này, nên không xác nhận một block bảng cụ thể của VN002 đã được hỗ trợ. Source chỉ rõ ACAD_TABLE chưa hỗ trợ, cần EXPLODE TEXT/MTEXT; chữ trong block mà reader đã bung ra vẫn chịu cùng lỗi ranh giới trên. Không hardcode tên/handle/VN002 để qua ca tổng hợp. Bản sửa cuối chưa có, chưa tuyên bố độ chính xác tới vật liệu hoặc nghiệm thu G3.
