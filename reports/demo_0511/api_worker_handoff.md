# Bàn giao worker API cho demo 05/11

Trạng thái SOURCE-READY, CHƯA CHẠY BACKEND TEST. Đợi điều phối kết thúc lượt N02 reader/writer và cấp lượt kiểm. Frontend giữ ổn định, không auth/DB/schema/cache/bounds hoặc endpoint khác.

## Phạm vi đã sửa

- src/optimat/api/main.py: chỉ /api/takeoff/view, /api/takeoff/structural và hai helper sync riêng.
- NEW tests/test_takeoff_view_concurrency.py: 5ca dự kiến.
- NEW tests/test_takeoff_structural_concurrency.py: 8ca dự kiến.

Đã dùng run_in_threadpool sẵn import từ fastapi.concurrency, đang có trong /api/ingest. Không thêm dependency hoặc abstraction chung.

## Thay đổi

1. /view giữ suffix400, JSONoverrides400 và await UploadFile.read; chuyển helper _takeoff_view_payload sang worker.
2. Helper sở hữu tempfile/ghi bytes/read_drawing (DrawingError->422)/_project_inputs/Catalog.load/takeoff_plans/view_payload. DBSession nằm trong _project_inputs trên worker, không session nào truyền qua thread. Tempfile giữ sống cho đến payload hoàn tất và dọn kể cả lỗi.
3. /structural giữ suffix400, structural_scale>0 kiểm400, ProjectParams JSON validation400, await UploadFile.read; chuyển helper _takeoff_structural_payload sang worker.
4. Helper kết cấu sở hữu tempfile/ghi bytes/read_drawing (DrawingError->422)/structural_parts/jsonable_encoder; giữ file name, params, scale và nullables nguyên hợp đồng.
5. Threadpool giải phóng eventloop để health/auth/request khác phản hồi. Không tuyên bố giảm thời gian CPU của thuật toán CAD hoặc giải quyết mọi endpoint async.

## Snapshot và diff

- main.before_view_worker.py.txt: bản trước cả hai thay đổi; SHA256 0880CFA8F8835B2C5AC2F9B4AADEA8F82C8B12931C5AAF59A94BC00012EDE1F1.
- main.before_structural_worker.py.txt: bản sau /view, trước /structural.
- api_view_worker.diff: diff riêng /view tại mốc SOURCE-READY đầu.
- api_workers.diff: diff cuối của cả hai endpoint so snapshot đầu.

Không ghi đè toàn file, chỉ apply_patch từng đoạn; giữ phần thay đổi có sẵn của các phiên khác.

## Test đã viết, chưa chạy

/view: concurrencyhealth+workerthread+args+tempfile lifetime; DrawingError422cleanup; validation400suffix/JSON (2ca); project404cleanup.

/structural: concurrencyhealth+workerthread+params/scale/file/nullables+tempfile lifetime; optionalparams/scale; DrawingError422cleanup; validation400suffix/scale0/scalenegative/JSON/modelvalue (5ca).

Các bài dùng asyncio.run và httpx.AsyncClient ASGITransport, monkeypatch công cụ CAD/health, không network/DB/pytest-asyncio. Blockingstub dùng threading.Event timeout3s, entered wait2s, health timeout1s, release trong finally; không sleep. Kiểm request CAD chưa xong khi health trả200. Thử nghiệm socketpair/asyncio thực tế vẫn có thể cần môi trường ngoài sandbox đã được điều phối xác minh.

Lệnh đề nghị sau cấp lượt: `.venv/Scripts/python.exe -m pytest tests/test_takeoff_view_concurrency.py tests/test_takeoff_structural_concurrency.py -q -p no:cacheprovider`, môi trường bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, OPTIMAT_NO_DOTENV=1. Ghi log vào reports/demo_0511/api_worker_tests.log. Chưa dùng số13 làm kết quả passed trước khi chạy.

## Hash SOURCE-READY cuối (SHA256)

- main.py: CF88AC8B0C6FF22390BA2765C9C5135A4A224D647587D53A627ADF4F7BE53C82
- tests/test_takeoff_view_concurrency.py: 53FA6CC26EDF07A714E8908FD49C9FBA0E1FB2033F209ADA53EBD47E7CBBC2F7
- tests/test_takeoff_structural_concurrency.py: 74D7975E5E4AD62FF5AD5A6252B252AFA9B578441935859485F2170A0860EFB6

## Còn thiếu

- Backendtests theo lượt điều phối, reviewer đọc diff/test và kết quả.
- Parent restart đúng API do parent sở hữu khi không còn activejob, rồi đo /view KT46 + health/auth song song; không kill service/session của phiên khác.
- BrowserQA/auth đang phụ thuộc quyền/tài khoản thực tế; không thay auth/DB để né.
- /rough/auto, /takeoff, /takeoff/plans, /agent/run và /concepts/try còn async/syncCPU trực tiếp; ngoài phạm vi lượt này, làm sprint riêng nếu cần.
