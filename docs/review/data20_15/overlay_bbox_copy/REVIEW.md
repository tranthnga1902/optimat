# QA15 — bbox release_handoff

05/11/2026 — PASS focused: **16 passed in 11.04s, EXIT0**. Không phát hiện blocker mới trong phạm vi patch đã giao.

Độc lập sao chép `src` từ base `opening-backend-candidate`, kiểm hash base và patch, `git apply --check` rồi áp exact release.patch trên bản sao. Base không có `data`: dùng snapshot catalog/rules/sample cục bộ của handoff apply_check; lần chuẩn bị đầu dừng trước áp patch/test vì thiếu thư mục data, không phải test failure. Chỉ chạy hai test bàn giao, không lấy tests/conftest của repo. Receipt và hash trước ở `receipt.json`, `hash_before.json`; terminal ở `focused.log`.

Patch SHA256: `6ce7d18f2d04961683f40b4a621eb873b1d09fdf9d3409b25fa69b53d2b4b3e7`. Bốn target khớp manifest trước/sau; hai source base vẫn đúng hash ban đầu. Viewer target `c58d12f0bd0cdcfd736f5f995187523e2bde2304746a823597eb69f43101767f`; render target `40fb0d1e8c2f61f65bf7cce71f64b4ec4271859eb46c7784750d66c077ca5797`.

Review patch và focused xác nhận: display_bbox theo mm/Y xuống cùng origin; legacy bbox/size và dữ liệu đo giữ nguyên; arc R100, text/insert xa, mm/m, circle và native extent sau crop có coverage. Explicit plan giữ crop ±1500 mm, overview giữ neighbor. Signals ở cấp hồ sơ cho bốn plan rỗng, không tự tạo quantity/tầng. Lỗi renderer.view từng plan/overview giữ nhận diện và warning/cad_missing; catch mới không bao nhận diện/hash. Kiểm hash lỗi recognition là review phạm vi catch, không có ca fault injection riêng trong 16 test.

Giới hạn: synthetic DXF và snapshot dữ liệu cục bộ; chưa CAD thật/VN002/API/browser/DB/full/TestClient. Không sửa/graft/restart runtime 8003. Frontend phải dùng display_bbox để fit, không suy fit chỉ từ display_size; lượt này không nghiệm thu tích hợp frontend. DIM01–10 giữ PREPARED/NOT_RUN chờ 01 freeze và giao lượt riêng.
