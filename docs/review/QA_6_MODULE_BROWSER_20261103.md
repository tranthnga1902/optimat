# QA trực tiếp 6 module — điểm bàn giao backend

User giao khởi động lại và kiểm tra đủ 6 module trên Chrome. Hệ thống đang chạy local (API 8000, Next dev 3000), không sửa auth hoặc nạp giá giả.

## Hai lỗi đã tái hiện và sửa

1. /phan-tho crash Cannot read properties of null (reading addEventListener) từ viewport.ts. Đã thêm guard không gắn sự kiện khi không có SVG. reports/module_ui_qa_20261103/viewport_regression.cjs PASS.
2. /vat-lieu và /toi-uu dùng rough.result.wall_groups nhưng API không trả trường này. Đã nối helper final_wall_groups sẵn có qua MasonryGeometry trên WorkItem, metadata nguồn ở walls.py, và field/return RoughResult trong takeoff.py. Không sửa normalize_ties/deduct_ties. tests/test_final_wall_groups_ui.py + test_rough_walls.py: 8 passed. API đã restart để nạp đoạn nối.

## P0 mới phát hiện do contract cập nhật trong lúc QA — HOLD backend chờ owner demo

- Trước đó Giá đã hiển thị đúng GN02 954,21 viên, GN01 12.423,40 viên, vữa M75; tối ưu POST 200 và báo thiếu labour ACTUAL.
- Trong lúc QA, bill.tsx/optimize.tsx đổi (LastWriteTime 21:53:41/42) sang gate: `rough?.result?.plan_scope_confirmed ? rough.result.wall_groups : undefined`.
- frontend model.ts gửi plan_scope_confirmed:true và chỉ gửi states[i].scope === count. Nhưng RoughRequest và RoughResult hiện không có field plan_scope_confirmed, API bỏ mất cờ. Sau mở lại A, UI Giá/Tối ưu gate như thiếu khối xây; tính lại cũng không khắc phục vì response vẫn không có cờ.
- Repro hiện tại trên Chrome: /toi-uu có tiêu đề Phương án tường và Cần kiểm tra và tính lại phần thô để có đủ khối xây. Vật liệu-ready vẫn true và menu Phần thô đã tính. Bản vẽ/thông số/kết quả phần thô đã phục hồi đúng.
- Đây là mismatch contract, chưa kết luận mất lịch sử. Owner backend cần nhận/publish cờ phạm vi đã được xác nhận (theo semantics đã thống nhất), không xóa guard frontend và không lấp dữ liệu SAMPLE/giá giả. Tôi không sửa thêm models.py/walls.py/takeoff.py sau mốc HOLD nhận từ điều phối.

## Hồ sơ và kết quả UI đã kiểm

- Tạo QA 6 module A 03-11, mô tả: Dự án thử luồng đầy đủ: bản vẽ mẫu, vật liệu, phần thô, giá và tối ưu.
- File dùng kiểm thử luồng: data/sample/sample_floor.dxf (dữ liệu mẫu/SYN cho QA hình học, không phải hồ sơ ACTUAL). Có thử mở Nha_pho_unicode_fastview_FIXED.dxf qua Windows nhưng chưa có bằng chứng POST hoàn tất cho file nặng; không tuyên bố QA heavy.
- Một mặt bằng Toàn bộ bản vẽ, scope=count, 5 tường, không lỗ mở. Chiều cao nhập thử 3400mm. Tổng xác nhận 128,11m².
- W1-W4 GN01, W5 đổi từ AAC01 sang GN02; params thử ready_mix/M250, lót M100, vữa xây/trát/cán M75, gỗ, CT02.
- Đã rời module Vật liệu trước khi lưu và quay lại: draft giữ GN02/M250/M75.
- Thông số thử phần thô: trát15mm/cán30mm/sàn120mm/dầm200×300mm. Kết quả xây24,07m³, trát233,62m², sàn6,76m³. Những công tác thiếu dữ liệu vẫn D; không nhập hàm lượng thép giả để làm đủ.
- Giá (trước gate mới): 954,21 viên GN02; 12.423,40 viên GN01; VU02 0,34m³ và6,55m³. Giá thiếu ACTUAL ghi rõ, không tự điền.
- Tối ưu thử: province Hồ Chí Minh, tọa độ công khai trung tâm thành phố10.7769/106.7009, ngân sách150 triệu,7 ngày,xe2,5t,giữ thiết kế. POST/api/optimize200: không có phương án, thiếu đơn giá nhân công ACTUAL phù hợp. Đây không phải nghiệm thu tối ưu mua thành công.
- Tạo B: QA 6 module B 03-11; bản vẽ rỗng,0m²,không badge rough/kết quả A, /toi-uu chặn vì chưa lưu vật liệu. A xuất hiện trong lịch sử.
- Tìm A theo tên, mở lại: file sample_floor.dxf,scope=count,Đã xác nhận,3400mm,5tường,128,11m²; GN02/M250/M75 giữ; sàn120,dầm300 và kết quả xây24,07m³ giữ.
- Chưa kết luận PASS full history cho Giá/Tối ưu vì gate cờ phạm vi mới nói trên. Không chạy lại tối ưu để che mất yêu cầu kiểm tra result persistence.

## Bằng chứng

- reports/module_ui_qa_20261103/05_gia.jpg
- reports/module_ui_qa_20261103/06_toi_uu.jpg
- reports/module_ui_qa_20261103/07_du_an_B_trong.jpg
- reports/module_ui_qa_20261103/08_tim_lich_su_A.jpg
- reports/module_ui_qa_20261103/09_khoi_phuc_A_khoi_luong.jpg
- reports/module_ui_qa_20261103/10_khoi_phuc_A_vat_lieu.jpg
- Log API trước/sau nối: api.log/api_after_fix.log và *.err.log; tất cả xác nhận qua UI, không TestClient.

## Source SHA256 bàn giao, diff là cumulative so với HEAD
src/optimat/rough/models.py E3845AE56E5FE5774773D8C47F7EFBE28A963D274D5D03551FA8F7BC06D61730
src/optimat/rough/walls.py 20162A2DBCF6CA86B0D8C897D38E05FB9E4D8D8E60848427F6740A2A13CDBE32
src/optimat/rough/takeoff.py 81CCA3C377EE43D392CA581613F5353D878B86E09075D70ACDC6C6B08528730B
src/optimat/rough/wall_groups.py 9811FED6660908AC476E2B336DC4C4B74282F7507FC5F4FBA86F203B542DF74E
tests/test_final_wall_groups_ui.py CCE3E17A544BB064CC30C6D02CF6A863C7EE5BE826AECDD730BBBBB9EDBE2682
frontend/src/app/(user)/do-boc/viewport.ts EA39BEA73DC107CC564A5662FB7E2D0B835DFC72325F0E3FEC121B24BCA2CA04
frontend/src/app/(user)/do-boc/model.ts B99C13A9A5C29FAB088905F066418C59CA81C5A2FE4A7F501A14B7BD5AD7B952
frontend/src/app/(user)/do-boc/Review.tsx 4A699E9CA1D7540DB2B52148A93067B2DF74EBCC305E8B1B5EA4B290CC4ACACD
frontend/src/app/(user)/dieu-chinh/materials.tsx 6E611FE044A52B314CA67F9728586002476B162EAF28AB541AD7C3348A3BE533
frontend/src/app/(user)/vat-lieu/bill.tsx 2732FE357BA93DE243E7EDA1BA86C6735EA6FD93DD36EDB17CC46C09FBEB725F
frontend/src/app/(user)/toi-uu/optimize.tsx 70A7F0AFB4413E441F7D7CB26F9E9669032EB717CB17FA40B5E1D96621C80687

### Xác nhận HOLD cho owner demo

Đã giữ nguyên 3 file src/optimat/rough/models.py, walls.py, takeoff.py tại SHA256 ghi ở trên; không ghi tiếp các file đó/test backend sau khi nhận chuyển owner. Có thể áp bản staging đã kiểm từ owner demo. viewport.ts là fix riêng frontend. QA tiếp tục trên Chrome tab1498891083, đang /toi-uu với dự án A đã restore; API27264 đang phục vụ source bridge cũ. Sau backend source-ready cần restart đúng listener8000 để áp contract cờ phạm vi; không tự nạp giá giả/SAMPLE. Bản QA chi tiết này là repro và xác nhận source HOLD.

## User yêu cầu mới: hiện nét bản vẽ trong lúc chờ + hydration console

- Tôi tiếp tục HOLD models.py/walls.py/takeoff.py sau bàn giao bridge, không đè bản staging của owner demo. Đã thấy owner áp plan_scope_confirmed vào backend; API cần reload đúng8000 khi không có CAD job.
- Phát sinh scope riêng được user giao: progressive viewing. Đang sửa main.py (route /api/takeoff/view hỗ trợ Form progressive=true, default giữ JSON cũ), thêm drawing/view_progress.py, do-boc/read-progress.ts, ReadPreview.tsx và upload branch Review.tsx. Không sửa 3 file backend wall contract nói trên.
- Dữ liệu streaming: status reading → raw line preview → status recognizing → recognized geometry → status rendering → complete CAD. Dùng cùng drawing đã parse, không đọc file hai lần. Preview không publish vào project storage; chỉ complete mới start bản vẽ mới. Hủy/error giữ dữ liệu cũ. UI overlay giữ Board cũ mounted để không mất pan/zoom listeners.
- TypeScript PASS; ESLint Review/read-preview/parser/viewport PASS; parser Node splitUTF8/NDJSON/error/incomplete PASS. Python progress test đang xử lý đường dẫn tempfile trong Windows sandbox (WinError5); không kết luận test pass. Không chạy CADheavy hoặc fullsuite.
- Console hydration user đưa có bis_skin_checked/bis_register/__processed_*; rg frontend/src không có các thuộc tính này, log Chromium cho thấy chúng được chèn vào markup. Tài liệu Next xác nhận extension sửa HTML có thể gây hydration mismatch. Không thêm suppressHydrationWarning hoặc xóa/sửa security setting Chrome.

## QA cuối sau backend owner demo áp cờ phạm vi

- Đã HOLD models/walls/takeoff không ghi tiếp; owner demo áp contract plan_scope_confirmed. API nạp mới qua wrapper14912, log api_progress*. Không có CADheavy đang chạy khi restart (các CAD/rough trước đã terminal200; không tạo heavy mới).
- Sau 1 lần tính lại phần thô để nâng snapshot cũ, Giá mở đúng nhóm vật tư. Không phải mất history: phiên cũ thiếu cờ phạm vi từ API.
- Đã chạy vòng history A→B→A lần2: lưu A mới (history timestamp22:05:42), mởB, tìmA, mởA. Vào thẳng Giá không tính lại: GN02 954,21viên; vàoTối ưu không chạy lại: province Hồ Chí Minh/ngân sách150000000/hạn7/xe2,5t và kết quả no-feasible cũ vẫn hiển thị. Đây là PASS chuyển bước và bảo toàn snapshot6module cho bản vẽ mẫu đã nêu, KHÔNG là tối ưu mua thành công.
- Ảnh bổ sung: 11_khoi_phuc_A_toi_uu.jpg,12_history_A_gia_final.jpg,13_history_A_toi_uu_final.jpg.
- Progressive viewing là scope mới của user: backend main.py đã thay riêng trước khi nhận yêu cầu HOLD main/ingest/view; hiện giữ nguyên source main chờ review/release, không sửa tiếp. Thiết kế và event/payload đã ghi ở mục trước. Không đọc lại CAD; file mới chỉ publish project khi complete. Preview riêng không xác nhận/lậpgiá/tốiưu. Không sửa3file wall contract sau bàn giao.
- Tiến trình test_view_progress.py đã terminal: 4passed, lệnh `.venv/Scripts/python.exe -m pytest tests/test_view_progress.py -q --basetemp reports/module_ui_qa_20261103/pytest_progress_tmp`. Lần đầu lỗi WinError5 sandbox temp, đã dùng fixture workspace tmp_path, không đổi quyền/setting máy. Node parser PASS, TypeScript PASS, ESLint preview/Review/parser/viewport PASS.

## Freeze preview backend theo yêu cầu điều phối

Đã HOLD main.py, drawing/view_progress.py, tests/test_view_progress.py và toàn bộ src/tests/scripts; không ghi backend hoặc chạy lặp test trong lúc full. Test progress đã terminal 4 passed; Node parser PASS. Không có CADheavy đang chạy từ phiên này; chỉ các request rough/price và UI history đã terminal. API owner vẫn là phiên này, actual uvicornPID24880 trên8000, wrapper14912; log api_progress*. Không restart thêm trong lúc full nếu không có điều phối.

SHA256 preview backend cuối:
src/optimat/api/main.py FD9F48A499B7A4D69B97DB38E33D5F5CEA202B661B1E4E1C16F4CA89126F7DA6
src/optimat/drawing/view_progress.py 1EA7E579F9A6D1BACE9AE833530A73555E8C18AF4C52A73F22A819097E8ED77C
tests/test_view_progress.py B4F52AA77F1C84FC10D3B20B0B9F8AE6715AD2E03BBD53D31EA72BC0B71ECE79

## Kiểm tra Chrome sau yêu cầu xem nét ngay trên bàn vẽ

- Trên dự án QA xem nét sớm 03-11, sample_floor.dxf trả 13/13 nét. Phát hiện luồng dừng ở giai đoạn nhận diện với lỗi JSON NaN. Đối chiếu payload với PostgreSQL chỉ ra năm vật liệu có `detect_class` trống, tạo khóa `NaN` trong cả `systems` và `ready` của `material_options` (drawing/viewer.py). Cần lọc các dòng không có lớp nhận diện khi lập hai bảng tra, vẫn giữ các vật liệu để chọn. Chưa sửa backend đang chạy full regression.
- Giao diện mới tự vẽ nét vào đúng vùng SVG trên bàn vẽ; thanh trạng thái dùng vị trí của hướng dẫn sẵn có, giữ menu, thanh công cụ và panel kết quả. Đã bỏ màn xem riêng. Kiểm tra end-to-end dưới đây sẽ dùng bản sửa API.
Sau khi full đã ghi result.json và hash_after.json (756 pass, 1 lỗi đúng test_review_api), đã sửa viewer.material_options để bỏ dòng thiếu detect_class khỏi bảng tra. Đang nạp lại API và kiểm trực tiếp Chrome.

Kết quả cuối trên Chrome trong dự án QA xem nét sớm 03-11:

- `sample_floor.dxf`: 13/13 nét tự hiện trên nền trắng ở `/do-boc`. Chọn phạm vi, nhập chiều cao kiểm thử 3,40 m, xác nhận 5 đoạn tường, 0 lỗ mở, 128,11 m². Chrome sang Kiểm tra công tác và khối lượng rồi quay lại hiển thị Đã xác nhận. Trong lần mở lại, header/bàn vẽ/panel trước và trong lúc chờ có cùng (x,y,w,h) lần lượt (248,221,733,156), (248,377,263,586), (511,377,470,586).
- `P20_ban_ve.dxf` (fixture synthetic): 525/525 nét, đã bấm Ẩn rồi Xem lại, Chrome hiển thị lớp nét trực tiếp với cả menu, toolbar và bảng khối lượng. Cùng lượt đọc kết thúc, nhập 3,40 m, chốt 21 đoạn tường và 60 lỗ mở, 1.040,40 m². Trang sang bước 3, quay lại xác minh Đã xác nhận. Ảnh thực nằm tại `reports/module_ui_qa_20261103/17_P20_net_trong_panel.jpg` và `18_P20_da_xac_nhan.jpg`.
- Chốt lỗi NaN: khóa `detect_class` trong `/materials/{8,14,15,16,17}/{systems,ready}` của PostgreSQL cục bộ; lọc dòng thiếu lớp khỏi hai bảng tra, giữ vật liệu còn chọn được. `main.py` khai báo JSON dict/NDJSON và vẫn xuất NDJSON nghiêm ngặt. `tests/test_review.py::test_review_api` cùng `tests/test_view_progress.py` đạt **7 passed in 8.74s** (ngoài sandbox, noDB qua conftest). Bằng chứng `reports/module_ui_qa_20261103/inline_tests.log`. Không chạy lại full trong chat này. API trên cổng 8000 PID 36032 wrapper 34468 đã nạp bản sửa dữ liệu. Không sửa 4 tệp WorkDimensions, không dùng subagent. Backend/test đã đóng băng sau lần kiểm thử này.
A0909B5A32474583FC3378DF8268B3C075E210A172A93D189A03FB3D132D6741  .\src\optimat\api\main.py
9E1857950985802EBA40091737B4CF2F9E59F187489F3A0D161E3A0F1C2C38F6  .\src\optimat\drawing\viewer.py
D6EF75C40315426729161C3FE380EC8A8617951653E5827DC63113BBA163CD48  .\tests\test_view_progress.py

### Hợp đồng producer cho bước kiểm công tác (đang thực hiện)

`optimat-project-uid` là mã cố định tạo một lần cho mỗi dự án và lưu theo lịch sử. `optimat-review` có `projectUid`, `drawingId` (phiên bản hình học/file) và `materialRevision` sau khi đã tính vật tư. `optimat-rough` là `WorkSnapshot` gồm `projectUid,drawingId,file,reviewId,at,request,result,materialRevision?`, request là JSON thực tế đã POST cho lần tính đó. `optimat-work-review` là `WorkReceipt` gồm cùng `projectUid,drawingId,file,reviewId`, `checked` là các chỉ số dòng thuộc đúng kết quả bất biến của reviewId, `partial`, `confirmed`. Phạm vi thiếu đối chiếu bằng result.works qua cùng reviewId. `approvedWork` ở lib/work-review.ts kiểm receipt, phiên hình và phạm vi. Consumer chỉ dùng kết quả mua khi approvedWork + đúng optimat-project-uid + materials-ready + materialRevision không rỗng và trùng giữa optimat-review/optimat-rough. BOQ dùng snapshot.request. Bản nháp không tự công bố. Chưa chốt source-ready.
Contract producer các kiểu DrawingVersion, WorkVersion, WorkSnapshot, WorkReceipt và approvedWork(snapshot, receipt, drawing) ở frontend/src/lib/work-review.ts đã chốt cho consumer. Không có khóa archive thay projectUid. Khi đổi cấu tạo, giữ pending cùng result/request mới, chuyển dấu kiểm chỉ cho dòng khớp duy nhất theo số đo/khối lượng, không chuyển theo chỉ số cũ. Đã kiểm Chrome P20 trước vật liệu, reload 1/21 dòng, xác nhận phần thiếu rồi đổi GN01: 6/23 dòng cần xem lại, GN01 vẫn còn; kiểm lại và lưu thành công mới mở giá. Harness work_review_regression.cjs đạt.

### Kết quả producer/UI và tỷ lệ hiển thị (02)

Phạm vi bàn giao: các kiểu và khóa đã mô tả phía trên, UI kiểm/chi tiết/partial, lưu vật liệu nguyên tử và giữ các dòng khớp khi cần kiểm lại. Code UI đọc đúng các trường trong reports/work_dimensions/CONTRACT.md. Hình học lượng cuối và nguồn lấy từ API; metadata reference/union/deduction không được cộng lại. Hỗ trợ giấy 1:N khi tiêu đề chứa TL/tỷ lệ/scale và gắn đúng hình, nguồn hiện theo tiêu đề. Tiêu đề mâu thuẫn hoặc chỉ thấy khung tên không tự gán. Cho nhập tỷ lệ tham chiếu cho từng hình. Không hiệu chỉnh đơn vị tọa độ. Slider, bánh xe, kéo nền và Vừa khung dùng cùng viewport/thước.

Bằng chứng Chrome trên hồ sơ tổng hợp P20 (không suy ra độ chính xác trên hồ sơ thật): 1/21 dòng được khôi phục sau reload; dù đã kiểm tất cả vẫn khóa tiếp khi chưa đồng ý phạm vi 19 dòng có phần thiếu. Thay W1 bằng GN01 phát sinh 6/23 dòng cần xem lại; giữ GN01 và 17 dấu kiểm không đổi, sau kiểm lại và lưu mới có nút xem giá. Đổi zoom 109% về 100% và nhập tỷ lệ tham chiếu không làm đổi 1.040,40 m²/Đã xác nhận. Ảnh 19_kiem_lai_sau_doi_vat_lieu.jpg, 20_ty_le_va_zoom.jpg trong reports/module_ui_qa_20261103.

TypeScript và ESLint đạt; harness work_review_regression.cjs, scale_regression.cjs, viewport_regression.cjs, read_progress_regression.cjs đạt. Hash bàn giao producer_ui_source_sha256.json, diff tích lũy so với HEAD producer_ui_cumulative.patch (bao gồm WIP đã có trước lượt này; không phải patch riêng để áp đè). Tạm đóng vùng source UI sau bàn giao. Không có full mới trong phiên 02, chưa kiểm ACTUAL-build KT+KC Tân Bình, không thử lại upload. Backend phục vụ Chrome lần này chưa nạp schema kích thước mở rộng mới nhất của 03; đối chiếu lại API/UI/BOQ sau phối hợp nạp bản tương ứng. Chưa có trường API liên kết riêng từ ghi chú tỷ lệ rời tới hình, trường hợp đó vẫn cần nhập tham chiếu.
API cục bộ đã nạp lại lúc 22:48:23 ngày 03/11/2026 sau khi kiểm đúng wrapper của checkout, không có kết nối/tác vụ con, CPU ổn định. PID mới 31124, wrapper 4632, health ok, catalog PostgreSQL, OpenAPI 0.1.0 đã có GET /api/admin/projects/{project_id}/files/{file_id}. Hash và kết quả: reports/module_ui_qa_20261103/api_reload_verified.json. Đây là kiểm đăng ký route, chưa tải 100 tệp. Không sửa source backend trong lượt nạp lại.

### UI 02 · AI phạm vi dự án/công tác và bảng dữ liệu kiểu Excel

Yêu cầu trực tiếp trong chat UI: mở rộng trợ lý toàn phần thô, hỏi cả dự án hoặc từng công tác đã kiểm, thử chọn + lưu trên Chrome. Đã nối scope adapter và bảng trên /dieu-chinh với MaterialAdvisor.tsx theo MATERIAL_CONTRACT; không sử dụng endpoint agent tường. Frontend đã kiểm Chrome P20 lọc “xi mang”, chọn XM01, lưu, tải lại vẫn chọn. 23 công tác, 10 vật tư; lọc một công tác bê tông cột còn 1 công tác và 1 dòng vật tư. Ảnh reports/module_ui_qa_20261103/21_bang_vat_tu_da_luu.jpg. Đã chuẩn bị hook API, chưa gọi OpenAI live. Cổng 8000 hiện /api/models báo configured, chưa có hai route trợ lý. Full225 retry1 result.json đã terminal. Lưu ý P20 có work COP_PHA trừ giao quantity=-2,25 m²: WorkFact staging dùng ge=0 sẽ chặn context toàn dự án, cần giữ khoản trừ có dấu (không zero/null hóa). Cần đủ route + điều kiện 1 lượt SYN trước nghiệm thu hỏi AI.

Cập nhật UI: sau khi nạp lại đúng project P20, Chrome đã lưu và khôi phục XM01 + mác M250 cài đặt trực tiếp trong ô bảng, không phải kiểm thử API trực tiếp. Hai phạm vi hoạt động, không lấy lượng chung để điền cho cấu kiện không có liên kết riêng. `material_scope_regression.cjs` PASS; ngoài sandbox/noDB/mock, bản staging signed hiện tại chạy `tmp/row_assistant_12/tests` terminal **19 passed in 2.97s** (advisor_mock.log). Adapter public: frontend/src/app/(user)/dieu-chinh/advice-scope.ts export adviceScope(work, receipt, rowIndex|null, materialRevision[,proposedMaterialIds]); dùng component MaterialAdvisor. Mã chọn chỉ là đề xuất khi khác thiết kế, không thay thế số mua hay tự xác nhận. 02 chưa gọi OpenAI và giữ lượt thật cho 04. Sẵn sàng include_router khi module nguồn được áp dụng. Frontend chỉ tsc báo TS2367 ở purchase-session.ts (04 đang thay đổi); lint và regression phần này đạt.

Kiểm đường hỏi trên Chrome: P20 → phạm vi Bê tông cột (1/23 công tác) → gửi câu hỏi. API runtime hiện chưa có /api/assistant/material-session nên trả thông báo chưa bật, vẫn báo phương án đã lưu. Không gửi dữ liệu ra OpenAI. Patch ghép đã chuẩn bị ở reports/module_ui_qa_20261103/material_advisor_integration.patch, git apply --check thành công tại mốc staging, không áp khi quyền backend còn thuộc điều phối. Khi 12 cập nhật bản cuối phải so hash/test lại; giữ duy nhất lượt live của 04. TypeScript toàn frontend và ESLint các file UI đã đạt sau khi 04 chốt helper; bộ kiểm scope/khôi phục và 19 ca offline đạt. Ảnh Chrome cuối 22_bang_excel_xm01_m250.jpg.
