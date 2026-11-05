# Canonical hai hunk đã áp và freeze

01 cho phép sole-writer05 áp đúng read_table + element_code khi hash base khớp. Đã kiểm base `a05915b14795a4a48f4d9f9532945f88bcc43c8a084dacf877d1ef7dcb7d6085` và candidate `f0eb2c2d865645167648a1820be2eb3571779730d9d40bbcc55ec255f4660ac5` trước ghi. Thay đúng hai hàm trên bytes base, giữ mọi phần khác và newline hiện có. AST ngoài2hàm nguyên; AST toàn canonical sau áp bằng candidate. Full-file hash khác candidate vì giữ cách xuống dòng của base, không phải đổi logic.

**Hash canonical freeze:** `76f09b3d09a2b33a3e5d568c49ece3f5e9d46c083a52cb6790088dec8aa4c6b0`.

**144passed in19.28s,exit0**, session68072 terminal. Chạy canonical `python -m pytest`, không loader staging: đúng tests/test_rebar_element_tokens.py, test_rebar_table_boundaries.py, test_rough_rebar.py, test_rough_partial.py, test_rough_takeoff.py. `canonical_final.log`, `canonical_test_receipt.json` lưu command và hash trước/sau6file (source+5test), stable=true. Child bỏ DATABASE_URL/URLtest/APIkey/dotenv, LLM none; không DB/HTTP/OpenAI/TestClient/full/runtime. `canonical_apply.json` giữ receipt áp2hunk.

## TK_2 còn pending

Probe file SYNTHETIC `tk2_synthetic.dxf`: native INSERT TK_2/ATTRIB DK20,DAI4300,SL1=2,SLA4,DT17.2,TL42.4 đi qua read_drawing giữ đủ trong BlockRef.attribs (các thuộc tính cũng được đọc thành TextItem). Tuy nhiên collect_rebar_tables không tạo hàng vì không có header TEXT đúng mẫu. `tk2_receipt.json` ghi raw_ATTRIB_loaded=true/schedule_rows=0 và warning, VN002_actual_verified=false.

Vậy reader cấp thấp đọc được ATTRIB; adapter tag→hàng/group/mark/phạm vi của bảng TK_2 chưa có trong bản sửa này. Không gọi kết quả0hàng là không có thép, không gắn dữ liệu này vào C-2/đoạn. Đặc biệt C-1/C-2 trùng bộ số theo04: phải bind qua group/INSERT/mark/chi tiết, không join bằng số. Chưa mở CAD VN002 để xác minh layer/type/path trong lượt này, chưa claim sửa header đã giải quyết bảng VN002.

Source rebar.py đã freeze sau focused, chờ01/15review. Mọi báo cáo staging trước giữ làm lịch sử, không còn là trạng thái áp canonical hiện tại. Không ghi phần materials của04, instancecore của03 hoặc API của06.
