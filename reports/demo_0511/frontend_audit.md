# Frontend audit cho demo 05/11

Rà tĩnh ngày 03/11/2026. Chưa sửa source, chưa chạy app/test/DB. Đây là lỗi/giới hạn đọc được từ mã, không phải biên bản nghiệm thu trình duyệt.

## Luồng và điều kiện chạy

- FastAPI: `.venv/Scripts/python.exe -m uvicorn optimat.api.main:app --app-dir src --host 127.0.0.1 --port 8000` tại optimat-ai.
- Next.js: `npm run dev` tại frontend; OPTIMAT_API mặc định http://127.0.0.1:8000; rewrite /api, timeout300s.
- Shell gọi /api/auth/me qua useMe; có DB thì phải đăng nhập tài khoản hiện có; không có DB thì chọn vai trò. Không tạo/reset tài khoản hoặc DB trong audit.
- /do-boc upload /api/takeoff/view -> sửa từng mặt bằng -> /api/takeoff/confirm -> optimat-confirmed localStorage -> /vat-lieu gọi /api/price/bill -> /toi-uu gọi /api/optimize.
- Phần thô: /do-boc tab Phần thô, upload /api/takeoff/structural, gửi /api/takeoff/rough -> optimat-rough -> /phan-tho.
- Đã cài node_modules, tsc. package.json có dev/build/start/lint, chưa có frontend test runner. Python có tests API/rough, không kiểm callback React/localStorage.

## P0/P1 và phạm vi sửa đề nghị

### P0. Xác nhận cũ vẫn được dùng sau sửa tường

- Review.tsx `markDirty` chỉ xóa `confirmed[pi]` trong state; `remember` đã ghi optimat-confirmed vào localStorage.
- bill.tsx và optimize.tsx dùng trực tiếp toàn bộ optimat-confirmed, không nhìn state của Review.
- Kết quả: xác nhận mặt bằng, sửa chiều cao/vật liệu/giữ-bỏ tường rồi chuyển trang sẽ vẫn tra giá/tối ưu khối lượng cũ.
- Sửa nhỏ: khi dirty, loại đúng file+plan khỏi store và trạng thái local; không xóa toàn bộ hồ sơ khác. Khi request confirm đang chạy mà dữ liệu đã đổi, không ghi response cũ như bản chốt mới.
- Scope: Review.tsx, có thể helper thuần trong lib/store.ts nếu kiểm được bằng test nhỏ.
- Ca nghiệm thu: confirm -> sửa -> trang Vật liệu không chứa mặt bằng stale -> confirm lại -> đúng khối lượng mới.

### P0. Kết quả phần thô cũ còn tồn tại khi tính lỗi/đổi file

- computeRough catch chỉ setRough(error), không hủy optimat-rough. start(D) setRough(null) nhưng không hủy optimat-rough.
- /phan-tho hiển thị store và ghi đã tính từ file cũ. Ngoài ra busyRef chỉ bỏ lần gọi mới khi request cũ đang chạy; response cũ vẫn có thể ghi sau start(file mới) hoặc sửa dữ liệu.
- Sửa nhỏ: vô hiệu hóa kết quả downstream khi đầu vào thay đổi; token revision/request để response cũ không được ghi; nếu đang tính mà edit thì xếp một lần tính lại sau request hiện tại. Abort/unmount cleanup nếu cần.
- Scope: Review.tsx. Không sửa API.
- Ca nghiệm thu: tính fileA -> mở fileB hoặc sửa khi request đang chạy -> không còn kết quả fileA được trình bày như mới; lỗi API không để /phan-tho báo thành công cũ.

### P0/P1. Mất cầu thang thứ hai, mất nguồn chiều cao

- model.ts `st0(p)` chỉ lấy stairs[0]; initPlanParams chép một thang; roughRequest tạo một id T1.
- roughRequest không gửi height_source dù backend PlanInput hỗ trợ. payload confirm luôn dùng P.plan.height_source cũ kể cả người dùng đã sửa chiều cao.
- Scope: model.ts + Review.tsx + Rough.tsx nếu cho sửa đủ nhiều thang; cần đọc guide React/Next local trước edit.
- Cách tối thiểu: giữ array thang từ API, cho sửa từng thang; height_source giữ auto khi chưa sửa, chuyển nhập tay khi thay đổi, giữ qua undo.
- Ca: 2 thang -> gửi 2; sửa một không đổi thang kia; chiều cao chưa sửa giữ nguồn, sửa -> nhập tay; undo phục hồi nguồn.

### P1. Upload bản vẽ không gửi mã dự án

- Review.upload chỉ append file; /api/takeoff/view có project_id để đọc height/opening defaults.
- Scope: Review.tsx append project_id khi có.
- Ca: mã dự án hợp lệ được gửi cùng upload; không mã vẫn upload được. Không dùng mặc định giả cho thiếu nguồn.

### P1. Cốt đất âm bị ràng buộc min0 và /phan-tho thiếu giá

- Rough.tsx áp min0 cho mọi numeric rough field, trong đó natural_ground_level_mm hướng dẫn âm. Sửa min theo field này.
- /phan-tho/rough.tsx không hiện best_price/est_cost/status dù tab Phần thô có; không phải lỗi API nhưng demo dễ tưởng mất giá sau chuyển trang.
- Scope: Rough.tsx và /phan-tho/rough.tsx, thêm trường hiển thị theo type backend hiện có, không tính lại tiền ở frontend.

## Cẩn trọng về nhiều hồ sơ

optimat-confirmed gộp mọi file; Review.start không xóa nó. Có thể là chủ đích cho nhiều file cùng công trình, nên không tự xóa toàn bộ khi mở file khác. Demo cần làm sạch bằng nút Xóa kết quả đã lưu hoặc chọn workspace/project rõ; giải pháp project isolation là thay đổi hợp đồng riêng.

## Kiểm tra đề nghị sau cấp quyền ghi

1. Đọc node_modules/next/dist/docs/01-app guide liên quan component client/state, không đổi Next config hay dependencies.
2. Test helper thuần cho invalidation/revision và payload nhiều thang/nguồn nếu tách vừa đủ; không thêm thư viện.
3. `node_modules/.bin/tsc --noEmit` và eslint đúng các file sửa; npm build khi được cấp lượt.
4. Thao tác trình duyệt một bộ build, ghi ảnh trước/sau cho stale confirm, nhiều thang, cấu trúc và giá.
5. Không toàn suite/DB và không sửa common docs cho tới điều phối cấp lượt.
