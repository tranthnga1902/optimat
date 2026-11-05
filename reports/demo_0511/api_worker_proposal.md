# Đề xuất P0: không chặn event loop khi mở bản vẽ

Trạng thái: READ ONLY, chưa sửa source/chưa chạy backend test. Phạm vi đề nghị chỉ src/optimat/api/main.py và tests/test_takeoff_view_concurrency.py (file test mới).

## Bằng chứng đọc mã

- main.py::takeoff_view là async nhưng gọi trực tiếp read_drawing, _project_inputs, Catalog.load, takeoff_plans và view_payload. Toàn chuỗi đồng bộ này chạy trên event loop.
- run_in_threadpool đã import từ fastapi.concurrency và đang dùng cho /api/ingest. Không thêm dependency.
- _project_inputs tự mở/đóng Session; cần gọi trong cùng worker thay vì chuyển session qua thread.
- /api/health là route sync nên chạy worker riêng nhưng vẫn cần event loop xử lý request. Một tác vụ CAD chặn event loop khiến health/auth không nhận được lượt xử lý.
- Thời gian KT46 ~234s là dữ kiện parent đo, không phải phép đo mới của agent này. Threadpool giải phóng event loop, không hứa giảm CPU/thời gian bóc.

## Thay đổi nhỏ đề nghị

Thêm hàm sync riêng _takeoff_view_payload(data:bytes, suffix:str, file_name:str, overrides:dict|None, project_id:int|None, floor_height_mm:float|None)->dict:

1. Tạo TemporaryDirectory bên trong worker, ghi upload{suffix} bằng data đã đọc bất đồng bộ.
2. Gọi read_drawing trong try/except DrawingError -> HTTPException422 giữ nguyên detail.
3. Gọi _project_inputs, Catalog.load, takeoff_plans, view_payload ngay trong worker.
4. Giữ tempfile còn sống cho đến view_payload hoàn tất, kể cả ngoại lệ. Trả filename gốc hoặc path.name như hiện tại.

Endpoint takeoff_view giữ kiểm suffix và JSON overrides (400 như cũ), await file.read(), rồi `return await run_in_threadpool(_takeoff_view_payload, data, suffix, file.filename or "", overrides, project_id, floor_height_mm)`.

Không chuyển sang route sync đơn thuần vì UploadFile.read đang async; không dùng BackgroundTasks vì người dùng cần payload ngay; không process pool, queue hoặc timeout mới.

## Test mới sẵn sàng triển khai

Dùng asyncio.run + httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app)); không cần pytest-asyncio, mạng/socket/server hay DB.

- Concurrency: monkeypatch read_drawing trả sentinel; _project_inputs/Catalog.load/takeoff_plans/view_payload là stub có kiểm args. Stub CPU ở takeoff_plans đánh dấu threading.Event entered rồi đợi release.wait(timeout2s). Tạo task POST /api/takeoff/view; await asyncio.to_thread(entered.wait,1s); kiểm upload vẫn pending; gọi GET /api/health với wait_for0.5s; health phải trả200 khi release chưa mở. finally release.set, await task. Kiểm worker id khác event loop thread.
- Patch health dependencies MaterialPriceModel.load, dwg_convert.is_available, get_database_url để không I/O/DB. Không sửa endpoint health.
- Contract: stub read_drawing và view_payload kiểm tempfile tồn tại trong lúc xử lý, filename/overrides/project_id/floor_height/openings truyền đủ; sau response path không còn. Kiểm response200 và payload nguyên.
- Error422: read_drawing raise DrawingError("lỗi CAD kiểm thử"), POST nhận422 cùng detail, tempfile dọn; sau lỗi health vẫn200.
- Validation400: file.pdf hoặc layer_overrides JSON lỗi không gọi worker.
- Không dùng sleep. Event timeout tổng mỗi ca vài giây, release ở finally để không treo thread lúc test thất bại.

## Những endpoint còn cùng rủi ro (tách lượt sau)

- /api/takeoff: takeoff_from_file chạy trực tiếp.
- /api/takeoff/plans: takeoff_plans_from_file chạy trực tiếp.
- /api/takeoff/rough/auto: read_drawing + rough_from_drawing + compute_rough.
- /api/takeoff/structural: read_drawing + structural_parts, là bước trực tiếp trên /do-boc nên cần ưu tiên lượt kế.
- /api/agent/run: run_agent/run_pipeline đồng bộ, gồm cả LLM/network.
- /api/concepts/try: đọc và nhận dạng CAD trực tiếp.

Không sửa các endpoint khác trong lượt /view này. Các route sync /api/takeoff/rough, /api/optimize đã được FastAPI chạy worker theo cơ chế sync-route; không cần bọc lồng threadpool.

## Kiểm sau khi cấp lượt

1. Snapshot/hash main.py trước sửa, Edit đúng đoạn helper/endpoint, không ghi đè phần việc của agent khác.
2. Chạy test mới riêng không DB; nếu socketpair asyncio bị sandbox chặn thì dùng phép cấp quyền đã được điều phối xác minh, không sửa ứng dụng để né.
3. Reviewer chạy tập API tập trung sau khi hết lượt test hiện tại.
4. Sau đó chạy thật /view KT46 và song song health/auth; ghi thời gian, không tuyên bố tăng tốc thuật toán chỉ từ health responsive.
