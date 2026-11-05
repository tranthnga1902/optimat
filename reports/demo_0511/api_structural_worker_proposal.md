# Đề xuất lượt riêng: /api/takeoff/structural

READ ONLY proposal, chưa triển khai endpoint này.

Caller hiện tại: /do-boc Review.onStructural POST multipart file -> main.takeoff_structural; đọc CAD rồi structural_parts synchronously trên event loop. Kết quả có foundations/lintel_height_mm và parts (structural_beams, column_schedule, rebar, members, sheets...), giữ hợp đồng hiện tại.

Phạm vi xin cấp riêng: main.py đúng helper+endpoint takeoff_structural, NEW tests/test_takeoff_structural_concurrency.py. Không ghép /rough/auto hoặc /agent/run vào lượt này.

Cách sửa: endpoint giữ suffix400, structural_scale>0 kiểm400 và ProjectParams JSON validation400 như cũ; await file.read(); await run_in_threadpool(_takeoff_structural_payload, data, suffix, filename, project, structural_scale). Helper sync sở hữu TemporaryDirectory/ghi bytes/read_drawing với DrawingError->422, structural_parts và jsonable_encoder chạy cùng worker khi tempfile còn sống. ProjectParams được tạo riêng từng request, không Session/engine/cache nào truyền qua thread. Không đổi tên trường/thêm schema/nguồn quy tắc.

Test sẵn để viết: AsyncClient ASGITransport không mạng/DB; structural_parts chặn bằng threading.Event wait tối đa3s, health phải phản hồi khi chưa release; kiểm worker thread khác event loop; scale/project và filename/parts/nullable values giữ nguyên. Kiểm tempfile tồn tại lúc structural_parts chạy và dọn sau success/error. Ca DrawingError422, invalid suffix/scale/JSON400 trước helper. Không sleep, luôn release trong finally, không pytest-asyncio dependency mới.

Có thể tái dùng kiểu health mocks từ test_view nhưng không tạo shared abstraction chỉ cho hai file test. Chỉ chạy test sau coordinator cấp lượt; không sửa frontend/DB/auth/cache.
