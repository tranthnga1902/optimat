# TK_2/ATTRIB — candidate staging, chưa áp production

Theo quyền01: chỉ candidate riêng, giữ rebar canonical freeze để phát hành gross. Không sửa canonical reader/rebar, helper03, materials04, DB/schema/API/runtime. `manifest.json` ghi hash snapshot base, candidate/test/probe và canonical lúc bàn giao. `candidate.patch` là diff **module đề xuất mới ngoài production**, không phải patch read_table đã được phép áp. Không copy tự động vào src.

## Hợp đồng candidate

- `load_source(path,expected_hash)` kiểm file đúng hash rồi đọc native DXF. `native_rows` chỉ duyệt INSERT modelspace TK_2/TK_14, giữ handlepath modelspace/INSERT, type/layer, raw tags và từng ATTRIB handle/type/layer. Không join theo bộ số, SH hoặc tên gần nhất.
- `read_region` chỉ nhận frame_handle có thực, LWPOLYLINE kín chữ nhật WCS ở modelspace; chưa hỗ trợ khung LINE rời, khung trong block/OCS khác hoặc nhận tự động ranh giới bảng. Không dựng bbox từ hàng muốn lấy. Khung phải chứa duy nhất một nhãn nhóm cột và một nhãn SL; nhiều nhóm hoặc thiếu thì warning/không nhận.
- Đơn vị DK/DAI/DT/TL phải được caller cung cấp cùng bằng chứng (mm/mm/m/kg); INSUNITS không thay bằng chứng đơn vị cột bảng. Candidate chỉ hỗ trợ mẫu nhãn cột và tag TK_2 rõ, không claim parser mọi bảng.
- SH giữ nguyên, các số phải hữu hạn/dương; SL1/SLA nguyên, kiểm SL1×số cấu kiện=SLA và DAI/1000×SLA=DT. Thiếu/trùng tag hoặc bất nhất giữ pending, không sửa số. SLA là tổng số thanh, **không nhân số cấu kiện lần hai**. TL là khối lượng in, không tự thay bằng kg tính. Không phát vật liệu mua hay RebarRow production.
- Mọi hàng checked=false, segment/axis=None, còn pending phạm vi/tầng/chi tiết. TK_14 giữ raw source và warning chưa hỗ trợ, không phân77đai vào đoạn. Group xác nhận bằng khung chỉ là nhóm bảng, không phải vị trí vật lý trong nhà.

## Kiểm tổng hợp

`test_tk2.py`: **13passed in4.91s,exit0**, session9360 terminal; `final_test.log`. Lệnh `.venv/Scripts/python.exe -m pytest docs/review/data20_05/tk2_staging/test_tk2.py -q -p no:cacheprovider --basetemp=docs/review/data20_05/tk2_staging/temp_final`.

Ba khung tổng hợp C-1/C-2/C-1A riêng. C-1 và C-2 trùng toàn bộ số nhưng handlepath/frame/group khác, không dedup. C-2 có2CK, mỗi mark2thanh/CK, SLA4/DT17,2m/TL42,4kg mỗi mark. Hai mark tổng8thanh/34,4m; kiểm đối chứng34,4×2,470=84,968kg toàn nhóm, không nhân thêm2 lần; đây là kiểm tổng hợp với hệ số đối chứng, không chốt khối lượng VN002. C-1A tổng8thanh/mark không bị lấy4. Có ca unknown units, khung chứa nhiều nhóm, SLA/DT mâu thuẫn, NaN, số thanh lẻ, thiếu/trùng tag, TK_14 pending và hash sai. Không TestClient/full/DB/OpenAI.

## Nguồn thật đã đọc, giới hạn còn mở

`probe_actual.py` đọc đúng `data/drawings/build/nha_sang_hai_duong_4x15_ket_cau.dxf`, SHA256 `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`. Dùng locators packet04 **chỉ đối chiếu native source**, không đưa handle kỳ vọng này vào thuật toán nhận bảng. `actual_raw_receipt.json` có7INSERT+6TEXT anchor; kiểm raw ATTRIB theo từng handle với packet04, bổ sung type/layer/ATTRIB handle trực tiếp từ DXF. Label group của packet04 được ghi là claim bàn giao, không trở thành group binding của candidate.

- C-2 TEXT118CDEF/(SL:2)118CDF0, TK_2 INSERTmark3=118CDA7/mark4=118CDB3; C-1 INSERT118CCC5/118CCD1 có cùng trị số; C-1A118CD2A/118CD36 khác SLA8. Native raw rows giữ group=None/segment=None/axis=None.
- Đai7 INSERT118CDD7 thực tế là TK_14, SL1=77/SLA154; chưa có phân bổ đoạn.
- `$INSUNITS=0`. Chưa tái kiểm header/chữ đơn vị của bảng để chứng thực DK/DAI/DT/TL trong lượt này. Source04 nêu PDF KC-02-04 p22/KC-00 p3 là hướng kiểm tiếp, không tự coi mã tag là chứng thực đơn vị.
- Chỉ tìm được2closed-polyline bao anchor C-2: EA8BF0 layerLS-THAY (vùng lớn, hơi lệch trục),1191A63 layerTpl_Bound (khung trang). Chưa có chứng cứ chúng là ranh giới riêng nhóm C-2. Không lấy khung trang hoặc tọa độ quanh anchor làm table oracle.
- **0hàng accepted vào nhóm**, không phải0thép hoặc không đọc được ATTRIB. Ranh giới bảng/nhóm, đơn vị và liên kết mark→chi tiết đoạn/axis/tầng vẫn pending. Không đưa42,4/42,484kg hoặc77đai vào lượng mua4/A.

## Tích hợp đề nghị, chưa được triển khai

Muốn dùng trong production: xác minh khung/grid/region cụ thể từ hình nguồn (có handlepath và containment), đơn vị header, rồi adapter giữ source context vào RebarRow/TableManifest mà không nâng scope. BlockRef hiện thiếu nativehandle/INSERTpath. Có thể thêm trường mặc định tùy chọn `source_handle` và `insert_path` trong staging reader, nhưng cần bảo toàn chuỗi native INSERT occurrence qua transform/crop, không dùng tên block thay handle hoặc tự tạo native handle từ virtual entity. Candidate hiện đọc native modelspace riêng nên **chưa sửa BlockRef**, chưa hỗ trợ TK_2 lồng/MINSERT. Không thay helper03 hoặc gán mark vào đoạn bằng tên/giá trị.

Đề nghị01/07/04 chốt ranh giới geometry/units trước mở thêm hunk. Chỉ khi đủ bằng chứng và review01/15 mới tích hợp, chạy hồi quy canonical rồi áp; manifest/test staging không là giấy phép phát hành hay nghiệm thu nguồn VN002.
