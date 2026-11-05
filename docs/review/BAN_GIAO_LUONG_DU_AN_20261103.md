# Bàn giao luồng dự án và trang điều chỉnh — 03/11/2026

Source hiện tại giữ ổn định để QA; không revert các thay đổi đã có từ phiên khác.

## Phạm vi thay đổi phiên này

- Review.tsx: chế độ adjustment, khôi phục/lưu trạng thái bản vẽ, xác nhận đủ mặt bằng chuyển /dieu-chinh, lưu điều chỉnh cho bước tiếp theo.
- Lists.tsx, Dialogs.tsx: màn hình xác nhận chỉ hiển thị kích thước/khối lượng; ẩn chọn vật liệu và bỏ tối ưu nhanh trong hộp thoại xác nhận.
- dieu-chinh/page.tsx: trang riêng tái sử dụng Review với adjustment.
- ProjectBar.tsx, projects.ts, Shell.tsx: giữ ngữ cảnh dự án, tạo dự án mới lưu snapshot lịch sử, mở lại snapshot.
- optimize.tsx: lưu/khôi phục kết quả tối ưu. ui.tsx: cập nhật bước. phan-tho/rough.tsx: liên kết chỉnh sửa sang trang mới.
- Công việc trước đó: Rough.tsx và reference.ts thêm đề xuất từ dữ liệu; API main.py bổ sung mortar_grades/plaster_thicknesses/screed_thicknesses, test_app_data.py bổ sung kiểm tra. Các file này vốn đã có thay đổi của phiên khác trước khi chỉnh. Không chỉnh model.ts trong phiên này.

## Kiểm tra

- TypeScript --noEmit: đạt sau chỉnh cuối.
- ESLint các file Review/Lists/Dialogs/optimize/projects/ProjectBar/Shell: đạt (lần trước chỉnh cuối chỉ đổi nhánh thông báo xác nhận; lần cuối TypeScript đạt).
- git diff --check các file tracked liên quan: đạt.
- Assert self-check Node với localStorage giả: đạt lưu lịch sử khi tạo mới, khôi phục dự án, giữ dữ liệu hiện tại khi ghi lịch sử thất bại.
- Chưa QA trực quan hoặc E2E trên trình duyệt; chưa chạy production build.
- Test API đề xuất: Python hệ thống thiếu ezdxf; lần chạy bằng .venv chưa nhận kết quả tại thời điểm bàn giao. Không chạy full suite, không reset database.

## Giới hạn cần QA

- Lịch sử lưu localStorage trên trình duyệt này, chưa đồng bộ máy chủ/thiết bị. Snapshot bản vẽ CAD lớn có thể vượt quota; cần kiểm tra thực tế và thông báo lỗi lưu.
- Trang điều chỉnh tái sử dụng khung bản vẽ nhưng là URL riêng. Nút bước/menu chưa khóa mọi cách đi tắt URL. Cần kiểm tra luồng nhiều mặt bằng và điều chỉnh lại vật liệu trước tra giá/tối ưu.
- Đổi dự án tải lại trang để loại trạng thái bộ nhớ cũ. Dữ liệu lịch sử gồm bản vẽ hiện tại, confirmed, rough, thông số, constraints, kết quả tối ưu, mã và tên dự án.
- Patch dưới đây là diff tích lũy so với HEAD, gồm thay đổi từ trước; không được dùng làm patch riêng của phiên này hoặc revert theo HEAD.

## SHA256 tại thời điểm bàn giao
frontend/src/app/(user)/do-boc/Review.tsx 7B84419FEFB08F5130E1AD1BB5199E3929555EF105C22DEBBD60C9FAF8FE2AC6
frontend/src/app/(user)/do-boc/Lists.tsx 53E11D82A116EE0D529304AA50C1CB5DC2139CFDA168A98A7051B2CDE76A18A3
frontend/src/app/(user)/do-boc/Dialogs.tsx 454944040B1B03E70C3D17E98F3A2DABF9E228623FC7F65099E95B5D6DEC8CD1
frontend/src/app/(user)/do-boc/Rough.tsx 24CB5BFE829D073B9FAC10F68B0FB8CE188C45BF949EC4D9379F3CF5592387B3
frontend/src/app/(user)/do-boc/model.ts F75176DF82CC6CA25B297E28D971E82A939819C87EBD1FE59821923E9B7247A3
frontend/src/app/(user)/dieu-chinh/page.tsx 4C4D095344BED3249FF7C175BBC25A37CC8B636D5EEACABFF306809A511645C2
frontend/src/app/(user)/phan-tho/rough.tsx E3069C8B78F2977AF1EC281C2A27905C62FB4FC24698BA36ECFB7E04284A902B
frontend/src/app/(user)/toi-uu/optimize.tsx ED6E2FB6EA02A32B4F766956BF8AA78279C95543122B27CE3C119DCF59DC8F1D
frontend/src/components/ProjectBar.tsx 2E432EE6CFB6B9EF438C41EE3FD2E26B314E13204DA346995C7F557C076BE251
frontend/src/components/Shell.tsx 0EF86BE49BD1A7881E5500DB214D793A7C5DC2BAEB2FAFC60535933000A8DD02
frontend/src/components/ui.tsx 2B33F428D900D9D57BBEF2710B0720E3F6CDCD5B258454278F38B43432DBB7D6
frontend/src/lib/projects.ts 88FB97E27E4C58CF97A4A2AAFDEF7BAD9989CDB9AAAFA0A161B95991BC8468A5
frontend/src/lib/reference.ts 1A2A82CEDF4C594A0BE051FEDF4E3D670F120694FD5A2983723B7636F135CDD6

## Bổ sung theo yêu cầu người dùng: thông tin trước khi mở bản vẽ

- Writer đã hoàn tất frontend: ProjectBar.tsx, projects.ts, Review.tsx. Tên dự án bắt buộc, địa điểm/loại công trình/số tầng/ghi chú tùy chọn. Chặn mở bản vẽ trước khi lưu thông tin; lịch sử tìm kiếm theo thông tin nhận diện, snapshot giữ metadata.
- TypeScript, ESLint 3 file trên đạt. Assert self-check metadata snapshot/reset/restore đạt. Chưa QA trình duyệt.
- Không ghi backend trong lượt bổ sung này. Thay đổi main.py/test_app_data.py về API đề xuất đã thực hiện ở lượt đầu tiên trước yêu cầu tách luồng; không biết thời điểm snapshot integration của chat khác để khẳng định thứ tự.
- Poll chính xác handle exec 43694 (lệnh `.venv/Scripts/python.exe -m pytest tests/test_app_data.py::test_catalog_reference_comes_from_data -q` từ lượt đầu) sau khi nhận yêu cầu điều phối: vẫn trả session_id 43694, chưa output/chưa exit. Không restart và không chạy thêm backend test. Không suy đoán process đã chết.
frontend/src/components/ProjectBar.tsx 762BB2FBE64A8CDBCBAE3495ADDAE1251E842D5881275D5A4B0680F6FC567BED
frontend/src/lib/projects.ts B3F238B4A4EA3E3F60F22755A8E9D7D0E6D675FE165EE49F1B8DA8E9A1594FBB
frontend/src/app/(user)/do-boc/Review.tsx EAE4B85EDD362C87A2ACE8F4EA19C6D7F75C882A725B036EAC830E5FE4CE80A2

## P0: chặn điều hướng khi snapshot hiện tại chưa lưu thành công

- Source ready: chỉ sửa frontend/src/app/(user)/do-boc/Review.tsx; giữ các thay đổi revision/stale response, height_source, multi-stair hiện tại. Không chỉnh backend/model/Rough/phan-tho trong lượt này.
- persistReview dùng chung cho autosave, auto chuyển sau xác nhận, và kiểm tra ngay trước click liên kết nội bộ. Capture trên document bảo vệ cả nút Tiếp, Steps và Shell menu; lỗi quota giữ nguyên snapshot đã lưu và dữ liệu hiện tại trong React, hiển thị lỗi, không router.push. Lần bấm tiếp theo thử lưu lại trước khi cho đi.
- TypeScript --noEmit đạt; ESLint Review.tsx đạt (chạy trong frontend).
- node reports/demo_0511/project_navigation_persistence_regression.cjs: PASS. Chạy trực tiếp phần callback hiện tại trong source: auto success lưu current confirmation trước routing; quota chặn auto/manual và giữ OLD; retry manual thành công lưu CURRENT rồi mới cho điều hướng.
- Harness chưa thay thế browser QA. Không bảo vệ thao tác nhập URL trực tiếp, reload hoặc đóng trình duyệt; khi quota cần giữ trang mở. Không thay storage engine/dependency/schema. Không thay lịch sử.

### Bổ sung guard truy cập URL trực tiếp

Đã đọc reports/demo_0511/frontend_storage_audit.md. Review.tsx thêm reviewMatchesConfirmed: trước khi hydrate trang adjustment, so file/plan, chiều cao, tổng diện tích, groups, confirmed_at, takeoff_id giữa snapshot và optimat-confirmed. Nếu khác, không setData snapshot cũ, hiện thông báo quay lại trang đo bóc để lưu phiên hiện tại. Không xóa confirmed hoặc lịch sử. Guard này phát hiện snapshot cũ so với kết quả đã xác nhận; không thể khôi phục chỉnh sửa chưa lưu khi người dùng đóng/reload trang. Harness bổ sung direct-entry stale rejected / matching accepted và kiểm thứ tự guard trước hydration: PASS; TypeScript sau bổ sung PASS. Đây là giới hạn có chủ đích, chưa bổ sung revision schema/storage mới.
Source ready Review.tsx SHA256: 92A72C0CDB2AFE05525349DC93EDC172B0E58799FFA4E6F9F4C595A8469A5F15

## Popup tạo dự án theo yêu cầu mới

- Chỉ ProjectBar.tsx và projects.ts; không sửa Review hoặc backend.
- Dự án mới mở native dialog, tên và mô tả bắt buộc, nút Mở dự án. Chưa submit thì không archive/reset dự án cũ; Hủy giữ phiên hiện tại. Khi chưa có dự án, popup xuất hiện ở /do-boc. Edit thông tin dùng cùng popup, giữ metadata cũ và dùng note để lưu mô tả tương thích lịch sử.
- switchProject nhận snapshot tên/mô tả mới; dự án chỉ có metadata cũng được archive.
- TypeScript đạt; project_popup_regression.cjs PASS; diff --check đạt. Chưa browser QA vì công cụ UI đã dừng với Cốc Cốc do URL policy không được hỗ trợ.

## Chốt bàn giao cuối sau popup — source giữ ổn định

SHA256:
- frontend/src/components/ProjectBar.tsx: 982F154735A0617DDDA399B7ED839CB5509B45374DFB9FA801867E53D453C309
- frontend/src/lib/projects.ts: BB0C3AABD3339E2D86AFB1D8DCDCB8653F5FB6FE547277B7A5687A9B5C68328C
- frontend/src/app/(user)/do-boc/Review.tsx: 92A72C0CDB2AFE05525349DC93EDC172B0E58799FFA4E6F9F4C595A8469A5F15

Các lệnh đã đạt (không chạy lại backend):
- Từ frontend: ./node_modules/.bin/tsc.cmd --noEmit
- Từ frontend: ./node_modules/.bin/eslint.cmd src/components/ProjectBar.tsx src/lib/projects.ts
- Từ frontend: ./node_modules/.bin/eslint.cmd "src/app/(user)/do-boc/Review.tsx"
- Từ root repo: node reports/demo_0511/project_popup_regression.cjs
- Từ root repo: node reports/demo_0511/project_navigation_persistence_regression.cjs
- Từ root repo: git diff --check -- frontend/src/components/ProjectBar.tsx frontend/src/lib/projects.ts

Test cũ exec handle 43694:
- Command gốc: .venv/Scripts/python.exe -m pytest tests/test_app_data.py::test_catalog_reference_comes_from_data -q
- Poll đúng handle vẫn trả session_id 43694, không output/exit.
- Đã gửi Ctrl+C duy nhất tới handle 43694 qua write_stdin; tool trả terminal exit_code 1, không output. Test bị ngắt, KHÔNG có kết quả kiểm thử.
- Không kết luận stack socketpair: không có stack trace. Truy vấn Win32_Process để đối chiếu command bị từ chối truy cập CIM; không escalation, không kill Python hàng loạt, không restart test.
- Không có backend test nào mới được khởi chạy trong lượt bàn giao này.


## Bàn giao compact snapshot sau QA trực tiếp Chrome

Source giữ ổn định:
- frontend/src/app/(user)/do-boc/Review.tsx SHA256 2D534F689AF422D711E5C50E3556B026E96F00781B388F96C2CCF0E3BED2C6CE
- Vùng thay đổi: saveNotice (dòng 43), hydrate restoredPi/states (96–103), persistReview fallback loại khóa cad (108–129), status notice (485). Không thay model, engine hoặc backend. Diff kèm là cumulative so với HEAD, không phải patch độc lập của lượt compact.

Hành vi và kiểm tra:
- Thử lưu đầy đủ trước. Chỉ khi lỗi mới thử snapshot không chứa cad (nền SVG overview/các mặt bằng). Giữ các trường khác nguyên dạng; không sửa dữ liệu đang mở.
- Giữ mọi mặt bằng, selected plan khi pi >= 0, segs/walls/openings/columns/stairs, states (gồm chiều cao và vật liệu đã chỉnh), planP, structural, groups, confirmed_at, takeoff_id. Nếu selected là overview pi=-1 nhưng compact không có SVG overview, mở mặt bằng đầu tiên; đây là thay đổi chế độ xem, không mất mặt bằng. Các mặt bằng chưa có states được initState khi hydrate.
- rough/results/material choices và lịch sử nằm ở khóa riêng, persistReview không đụng vào. Harness kiểm snapshot và các khóa riêng không đổi, không chỉ kiểm chuỗi source.
- Nếu cả full và compact đều lỗi: trả false, giữ snapshot cũ/currentstate/history; auto/manual/menu bị guard chặn như trước. Guard direct adjustment vẫn đối chiếu snapshot với confirmed đã công bố. Không xóa lịch sử để giải phóng bộ nhớ.
- node reports/demo_0511/project_navigation_persistence_regression.cjs PASS sau mở rộng fixture 2 mặt bằng, pi=1, vật liệu đã chọn, groups, confirmed_at/takeoff_id, structural, rough và history. Test compact-failure giữ snapshot/state/history PASS.
- TypeScript: từ frontend ./node_modules/.bin/tsc.cmd --noEmit PASS sau sửa restoredPi.
- ESLint Review.tsx PASS trước bổ sung restoredPi (chưa tuyên bố run lại bản cuối).
- Không TestClient/backend test mới, không POST CAD mới trong lượt bàn giao. Trước đó popup được kiểm trực tiếp: required fields chặn bỏ trống, tạo dự án A thành công. Sau user login, giao diện có bản Nha_pho_unicode_fastview_FIXED.dxf với 4 mặt bằng và cảnh báo quota thật; chưa xác minh POST upload/compact end-to-end. Chooser tiện ích thiếu Allow access to file URLs; chưa thay setting. Browser QA đầy đủ còn CHỜ.

Giới hạn nền CAD và xem lại:
- Khi hydrate từ compact, nền CAD gốc không còn; dùng nét đã đọc. Dữ liệu hình học đo bóc vẫn có. Thông báo giao diện ghi rõ mất nền CAD khi mở lại.
- Cần xem CAD nguyên gốc: mở file nguồn trong trình xem CAD, hoặc mở lại cùng file qua Mở bản vẽ trong một dự án kiểm tra riêng. Hiện upload lại cùng file sẽ chạy bóc tách lại và reset draft của file đó; không nên upload đè lên phiên đã chỉnh chỉ để khôi phục nền. Chưa thêm chức năng nạp riêng SVG và bảo toàn chỉnh sửa; cần thống nhất trước khi làm.

## Tách module theo yêu cầu người dùng — source mới

Luồng: /du-an-cua-toi (dự án/lịch sử) → /do-boc (kích thước/khối lượng) → /dieu-chinh (chọn vật liệu) → /phan-tho (thông số, công tác, nhu cầu vật tư) → /vat-lieu (giá/nhà cung cấp/chi phí) → /toi-uu (ràng buộc/phương án).

Thay đổi:
- Thêm dieu-chinh/materials.tsx: chọn vật liệu tường, bê tông/vữa/ván khuôn/chống thấm từ danh mục, lưu các mặt bằng qua confirm API hiện có. Không editor hình học hoặc bảng tính phần thô tại đây.
- Thêm lib/review-session.ts: kiểu phiên, phân loại trường vật liệu, ghi snapshot/confirmed/params nhất quán có rollback nếu quota; vô hiệu kết quả rough/optimization cũ sau lưu lựa chọn.
- Material draft lưu choices+params gọn, giữ khi đổi trang, nằm trong snapshot lịch sử qua projects.ts; cờ materials-ready chặn dùng kết quả vật liệu cũ khi chưa lưu. Chặn điều hướng lúc đang lưu; response sau unmount không ghi sang dự án khác.
- /phan-tho/page.tsx dùng Review roughOnly, chỉ hiển thị biểu mẫu/kết quả phần thô và chọn mặt bằng, không có Board, chỉnh hình học, xác nhận tường hoặc chọn vật liệu. Giữ pipeline/guards cũ; lấy lại rough đã lưu khi mở module. Chọn mặt bằng đầu tiên nếu snapshot đang ở overview.
- Rough.tsx loại các trường chọn vật liệu đã chuyển module, không còn đơn giá/thành tiền; vẫn tính trên params đã lưu.
- /vat-lieu bỏ hành động xóa/bỏ mặt bằng và bảng xác nhận hình học, thêm giá vật tư phần thô từ API result. /toi-uu giữ chức năng tối ưu, chặn kết quả async từ phiên đã unmount.
- Module dự án riêng; ProjectBar ở module khác chỉ giữ tên/ngữ cảnh và link quản lý, popup tạo dự án vẫn giữ. Shell/Steps cập nhật đúng thứ tự sáu module.
- Review bỏ mã dự án nhập tay và Lưu làm đáp án khỏi giao diện người dùng; pipeline mã dự án có sẵn vẫn tương thích.

Kiểm tra đã đạt:
- Từ frontend: ./node_modules/.bin/tsc.cmd --noEmit
- Từ frontend: ./node_modules/.bin/eslint.cmd "src/app/(user)/dieu-chinh/materials.tsx" "src/app/(user)/do-boc/Review.tsx" "src/app/(user)/do-boc/Rough.tsx" "src/app/(user)/vat-lieu/bill.tsx" "src/app/(user)/toi-uu/optimize.tsx" src/lib/review-session.ts src/lib/projects.ts src/components/ProjectBar.tsx src/components/Shell.tsx src/components/ui.tsx
- node reports/demo_0511/module_flow_regression.cjs: UI phân nhiệm, snapshot/confirmed nhất quán, quota rollback, geometry/metadata/history giữ nguyên, draft/ready reset và phục hồi theo dự án.
- node reports/demo_0511/project_navigation_persistence_regression.cjs: guards và compact retention PASS; chỉ cập nhật điều kiện source guard để nhận roughOnly mới.
- node reports/demo_0511/frontend_rough_regression.cjs: signed ground, negative dimensions và dữ liệu kết quả PASS; assertion chọn bê tông sửa thành không nằm trong module rough.
- git diff --check các file tracked liên quan PASS.

Giới hạn QA: Chrome không kết nối được 127.0.0.1:3000 (connection refused rồi timeout). Đã thử frontend dev, terminal báo Ready nhưng Chrome vẫn timeout; chưa có bằng chứng visual/end-to-end trên phiên source mới. Không khởi chạy backend hoặc backend test, không gửi thêm CAD. Lịch sử/draft tiếp tục là localStorage của trình duyệt, có thể hết quota; giữ các guard và thông báo. API confirm lưu từng mặt bằng trên server; nếu một request lỗi giữa chừng, frontend giữ lựa chọn/draft và chỉ publish toàn bộ local snapshot khi đủ kết quả. Không tuyên bố transaction server giữa nhiều mặt bằng.

SHA256 source cuối:
frontend/src/app/(user)/du-an-cua-toi/page.tsx 7197D405BF59C16B7232EC22148FEB3AF90BBB6C95BE8894671D94229B06A8B8
frontend/src/app/(user)/dieu-chinh/page.tsx EE0A096EDDE2965FC27B8DB41ECCB21185E3452231D9A1F4E269FAAC43D36160
frontend/src/app/(user)/dieu-chinh/materials.tsx 432CD8B6F49630E7FB8875045E1B6CD73C5AFB45277A88C4AAAFB5428C6FB70C
frontend/src/app/(user)/phan-tho/page.tsx 8EF97653E82AB11A4D133AD7734B1645DCCDD0E1E98DCAF83FF3DD32F5486B71
frontend/src/app/(user)/do-boc/Review.tsx F68E8D9C7D8624E32A9CE58DC2201E74CCDF3185768DC8BE0BA2D57CC59C48D7
frontend/src/app/(user)/do-boc/Rough.tsx D8C2FA96B5247D2249E159652733CC249836443E4D643E2594E425707E7C3369
frontend/src/app/(user)/vat-lieu/bill.tsx 36AA644535449C3289BAB5E1D3B1F811F23C32867F3AC06FEC5EACF6D3FF70DD
frontend/src/app/(user)/toi-uu/optimize.tsx 2E942AE1DE2BE79E601371E6E985B45E5577A5EC6654DDB14DF96AE52FA64911
frontend/src/lib/review-session.ts 1AF31D1FB9982C8D876AA37C32242BF4C6585AA5AB42145D6C354D6C6A6C9322
frontend/src/lib/projects.ts C1F3B1A9A7BE5A6B628CE04AEBC5CB072BEB1389077417E9AE7EECECAB0060B1
frontend/src/components/ProjectBar.tsx 1E80B0546002F68D2D66F07EFA283BF2DAB16AC854C39E494C303ED0150C0E2F
frontend/src/components/Shell.tsx 755C461912EF06FD5696AE982CC7E6BEAD974C961B5053D62C85E24E5A7E3776
frontend/src/components/ui.tsx 504BEAA3D781E51CEC6806F4262C5CAF6C874C2CB221269E662EBAE2876C6CE2
