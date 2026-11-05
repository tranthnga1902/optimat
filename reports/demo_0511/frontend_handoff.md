# Bàn giao frontend demo 05/11

Trạng thái: ĐẠT kiểm tra tĩnh và regression harness; CHỜ thao tác trình duyệt thật. Không coi đây là nghiệm thu giao diện cuối.

## File source đã sửa

- frontend/src/app/(user)/do-boc/Review.tsx
- frontend/src/app/(user)/do-boc/model.ts

Đã chụp nguyên bản đầu lượt trước sửa trong Review.before.tsx.txt và model.before.ts.txt. Không reset hoặc ghi đè các thay đổi có sẵn; không sửa backend, DB, dependencies, lockfile, lib/store.ts, Rough.tsx hay tài liệu dùng chung.

## Kết quả

1. Sửa tường/cửa/chiều cao hủy xác nhận lưu trên trình duyệt của đúng file+mặt bằng, để trang vật liệu/tối ưu không dùng khối lượng cũ. Giữ xác nhận thuộc file khác.
2. Revision bảo vệ request xác nhận và phần thô: response của dữ liệu trước sửa/đổi file không được khôi phục kết quả cũ.
3. Khi sửa dữ liệu, xóa optimat-rough ngay; tự tính lại nếu trước đó đã tính. Nếu request cũ còn chạy thì đợi theo timer, không bỏ mất lượt tính mới.
4. Tính lỗi không để downstream giữ thành công cũ; đọc kết cấu chưa thành công thì không tính bằng dữ liệu kết cấu thiếu mà hiển thị lỗi.
5. Mở lại cùng file hủy các xác nhận của file đó; không tự xóa mọi file vì có thể cùng công trình. Upload kiến trúc và kết cấu cạnh tranh có counter riêng để response cũ không thay file mới.
6. Upload kiến trúc gửi project_id khi có, để API lấy chiều cao/kích thước cửa của dự án.
7. Giữ height_source trong PlanState, confirm và rough payload; sửa chiều cao thành nhập tay; undo khôi phục cả nguồn cùng chiều cao.
8. Giữ nguyên các thang thứ2+ và dữ liệu gốc của thang đầu. UI hiện rõ form chỉ sửa thang đầu, các thang sau giữ dữ liệu nhận dạng. Chưa có UI chỉnh từng thang.

## Kiểm đã chạy

- `node reports/demo_0511/frontend_regression.cjs`: PASS, exit0. Harness biên dịch module TypeScript bằng package đã cài, mô phỏng React hooks/store/fetch/timer, không gọi API/DB. Kiểm payload hai thang (giữ id), height_source, upload project_id, invalidate confirmed sau sửa, chặn rough/confirm response cũ, tính lại sau request đang chạy, lỗi tính và mở file khác.
- `node node_modules/typescript/bin/tsc --noEmit --incremental false` tại frontend: exit0, không lỗi.
- `node node_modules/eslint/bin/eslint.js 'src/app/(user)/do-boc/Review.tsx' 'src/app/(user)/do-boc/model.ts'`: exit0, 0errors, 1warning. Warning là eslint-disable có sẵn tại line66 không còn cần; không tự sửa đoạn ngoài nhiệm vụ.
- Không chạy full pytest/DB, npm build hoặc browser.

## Hash cuối lượt (SHA256)

- Review.tsx: 64A336AFF0203ED0CC94BD5E0712730EC8F3A5915A9E2623EDAE8CB7BEB5C9ED
- model.ts: B2666173681AE7E0070241446A65A618566DB4410420C048B78F7B01717B88D0

## QA trình duyệt cần thực hiện

1. Đăng nhập nếu DB yêu cầu; mở bộ build, xác nhận tầng, sang Vật liệu ghi số; quay lại sửa tường/chiều cao, xác nhận cũ phải biến mất trước khi chốt lại.
2. Tính phần thô; đổi thông số trong lúc request đang chạy; kết quả sau cùng phải dùng thông số mới, không nháy lại thành công cũ trên /phan-tho.
3. Mở KT+KC, đọc ghi chú kết cấu; API lỗi phải hiện lỗi và không để /phan-tho giữ thành công cũ.
4. Bộ có hai thang: request phải giữ hai; UI cảnh báo chỉ chỉnh đầu; kiểm bảng chi tiết hai thang.
5. Mở fileA, tính rồi chuyển fileB trong lúc tính; không nhận kết quả fileA làm fileB.

## Giới hạn và phần chưa làm

- Chưa sửa min0 của cốt đất âm, chưa đồng bộ giá/status sang trang /phan-tho vì chưa cấp phạm vi các file đó.
- Xác nhận hiện vẫn gộp nhiều file trên localStorage; project isolation chưa triển khai. Chuẩn bị demo dùng nút Xóa kết quả đã lưu để tránh gộp dự án cũ.
- Form nhiều thang chưa làm; chỉ bảo toàn dữ liệu máy chủ để không mất phần thô.
- Không sửa lỗi backend/giá/dữ liệu thật hoặc gọi OpenAI; phụ thuộc các agent tương ứng.
- Harness không thay browser QA hoặc chứng minh số học phần thô.

## Bổ sung lượt 2: cốt đất và trang phần thô

Phạm vi được điều phối cấp thêm: frontend/src/app/(user)/do-boc/Rough.tsx và frontend/src/app/(user)/phan-tho/rough.tsx. Snapshot trước sửa: RoughTab.before.tsx.txt, roughPage.before.tsx.txt.

- Riêng natural_ground_level_mm không còn min0, nhận cốt âm. Các trường số công trình khác giữ min0 và từ chối số âm/non-finite khi commit, trả lại giá trị cũ; bỏ trống vẫn được để biểu diễn thiếu.
- /phan-tho hiển thị best_price, est_cost và price_source nguyên từ API. price_source hiện gộp loại nguồn, nhà cung cấp, ngày, data_kind; chưa có trường ngày riêng nên không tự tách/đoán. Ghi rõ BULLETIN không phải báo giá mua xác nhận.
- Thêm A/B/C/D cho tổng công tác, cốp pha, vật tư; số đã tính một phần có nhãn một phần; thiếu giá và thiếu thông số hiển thị rõ. Không tính lại hoặc cộng tiền ở frontend.
- `node reports/demo_0511/frontend_rough_regression.cjs`: PASS, exit0; kiểm cốt âm, từ chối chiều dày âm, bỏ trống, hiển thị nguyên giá/thành tiền API, nguồn/ngày/BULLETIN, trạng thái và phần thiếu.
- tsc sau hai file: exit0; eslint hai file: exit0, không lỗi/cảnh báo.

Hash SHA256:
- Rough.tsx: 5545C8F12816A10436784B884DA019FC6C7EA7D704F47B569A7147206022EDE2
- /phan-tho/rough.tsx: 72D0AD768C02968535891FAA1F34DF4B8B32432C4CBB0B73084418A5771BA988

### Sửa edge do review phát hiện: thang đầu thiếu số bậc

Điều phối cấp quyền sửa model.ts trong phạm vi ban đầu. Đã thêm fixture first steps=null + second valid vào frontend_regression.cjs, tái hiện FAIL1 thay vì2 trước sửa; sau sửa PASS. Khi người dùng xóa số bậc của thang đã nhận, giữ thực thể với steps=null và source manual, không coi là thao tác xóa. Giữ ID của thang đầu, dữ liệu nguồn và thang thứ2. Không có nhận dạng và không có đầu vào thang thì không tạo thực thể giả. Snapshot ngay trước sửa edge: model.before_missing_stair_fix.ts.txt.

Các mục giới hạn ở trên về cốt đất và giá trang /phan-tho đã được giải quyết bởi lượt2 này; UI chỉnh từng thang, project isolation và browser QA vẫn chưa làm. Parent báo đăng nhập thực tế đang bị chặn bởi tài khoản DB không hoạt động; không sửa auth/DB để né.

Kiểm cuối sau sửa edge: tsc --noEmit --incremental false exit0; eslint model.ts/Rough.tsx/phan-tho/rough.tsx exit0, không lỗi/cảnh báo. Hash model.ts mới thay hash lượt1: F75176DF82CC6CA25B297E28D971E82A939819C87EBD1FE59821923E9B7247A3. Không còn test nền thuộc agent frontend.

## Bổ sung lượt3: thích ứng thay đổi giao diện do phiên người dùng khác

Đã đọc AGENTS.md mới (tiếng Việt có dấu, UTF-8). Không sửa source trong lượt3. Luồng hiện tại: /do-boc chỉ kích thước/khối lượng -> /dieu-chinh điều chỉnh vật liệu/phần thô -> /vat-lieu -> /toi-uu. Gate dự án yêu cầu tên và thông tin trước mở bản vẽ. Đây là thay đổi được người dùng giao cho phiên khác, giữ nguyên.

Chỉ cập nhật reports/demo_0511/frontend_regression.cjs và frontend_rough_regression.cjs:

- Mock useRouter, Review({adjustment}), nút Xác nhận kích thước/khối lượng và Lưu điều chỉnh mặt bằng; fixture project-name/project-info hợp lệ.
- Cải thiện mock useEffect theo dependency thay vì cách gọi mount trước đây; không hạ ca kiểm dữ liệu.
- Giữ tất cả kiểm stale rough/confirm, invalidation store, chiều cao/nguồn, thang nhiều và thiếu, đổi file/lỗi request.
- Thêm kiểm luồng kích thước không có tab phần thô, xác nhận đủ chuyển /dieu-chinh, trang điều chỉnh khôi phục snapshot và mở phần thô.
- Thêm kiểm gợi ý vật liệu từ reference không tự chọn khi render và callback chọn mác truyền đúng giá trị.
- Cả hai harness đã chạy PASS exit0 trên source quan sát mới. Đây là kiểm mô phỏng, UIQA thực tế vẫn CHỜ; không chạy backend tests trong lượt khóa.

Rà quota chỉ đọc và probe tổng hợp được ghi frontend_storage_audit.md. Đã tái hiện rủi ro: khi ghi optimat-review bị từ chối, warning có và tự chuyển bị chặn nhưng Link /dieu-chinh vẫn hoạt động dù snapshot cũ; optimat-confirmed mới khác snapshot. Harness in OBSERVED QUOTA RISK, không đánh đạt cho hành vi lỗi này. Chưa đo quota/dung lượng browser thực và không đọc browser storage thật.

Source quan sát (không phải hash do agent sửa lượt3): ReviewEAE4B85EDD362C87A2ACE8F4EA19C6D7F75C882A725B036EAC830E5FE4CE80A2; Rough24CB5BFE829D073B9FAC10F68B0FB8CE188C45BF949EC4D9379F3CF5592387B3; pageE3069C8B78F2977AF1EC281C2A27905C62FB4FC24698BA36ECFB7E04284A902B; modelF75176DF82CC6CA25B297E28D971E82A939819C87EBD1FE59821923E9B7247A3.

Điều phối đã HOLD source do phiên giao diện đang thêm gate dự án. Không áp quota patch, không revert/chạm source. Chờ nguồn ổn định và cấp lượt mới trước sửa Review.tsx.

## Lượt scope/restores mới

Source đã sửa: Review.tsx/model.ts, dieu-chinh/materials.tsx, lib/review-session.ts. Mỗi hình phải chọn scope count/reference; chưa chọn giữnull và chặn xác nhận/tính. Không tự kết luận bản trùng là cùng tầng. roughRequest loại reference, chặn0count/unresolved, gửi plan_scope_confirmed=true. Thêm RoughResult.wall_groups nullable optional và wall_group_issues optional.

Restore legacy được vô hiệu phê duyệt trước gate adjustment; giữ hình học để quay Bóc tách phân loại. Material UI chỉ hiện/count confirmed cho count. Geometry edit xóa materialdraft/ready; material/params edit hủy rough/optimization tức thì. Transaction save vật liệu chặn scope chưa duyệt hoặc confirmed chứa reference, giữ lựa chọn vào snapshot; sau lưu phải qua module phần thô nhậpthôngsố/tính trước giá, không tính sớm.

Kiểm: TypeScript exit0; ESLint4file exit0; reports/demo_0511/frontend_scope_regression.cjs PASS, gồm unresolved/0count/reference exclusion, missing/multiple stairs, height source, actual material transaction rejects legacy/reference confirmations, scope persistence và clear old rough/optimization. Không backendfull.

CẢNH BÁO kiểm còn thiếu: frontend_regression.cjs cũ vẫn giả định trang adjustment tích hợprough, nay không còn đúng. Không coi logPASS cũ là bằng chứng cho luồng hiện tại; cần viết lại harness mới cho module geometry/materials/roughOnly nhưng giữ các ca stale-response/confirmation. frontend_scope_regression không thay được các ca này. UIQA thực tế chưa hoàn tất.

Hashes: Review73AD0B9C304F09B5696985071CE60887F6EA8A4E75000E23A9A33F4F84A80114; modelDF92C2F2C5A53D4716BDC11F6C74ACE7B3DFFE2947EAC9859B1B0B70917E666C; materials6E611FE044A52B314CA67F9728586002476B162EAF28AB541AD7C3348A3BE533; review-session952D83877F288A1E99DECF910DBD6E8BC989EBDED5D2A365F2E100258C7BCB53.

## Hoàn tất rewrite harness theo module hiện tại

frontend_regression.cjs đã được viết lại và chạy PASS exit0. Harness cũ lưu frontend_regression.before_rewrite.cjs.txt để tra cứu. Luồng thật được kiểm qua callback/component module hiện tại: geometry explicit scope -> confirm -> persisted session -> roughOnly sau material-ready. Vẫn giữ kiểm multiple/missing stairs và height source, stale confirm response, parameter edit trong lúc rough request pending và tự tính lại, rough error không giữ success cũ, unmount không publish response cũ, quota chặn manual navigation qua capture listener, legacy scope migration.

Cả frontend_scope_regression và frontend_rough_regression chạy PASS exit0. tsc --noEmit --incremental false exit0; eslint4source exit0. Không dùng các logPASS historical cũ để thay lần kiểm mới.

Phát hiện bổ sung đã sửa: Review.start upload file mới/samefilename trước đây chưa clear materialdraft/ready/optimization. Nay xóa các trạng thái cũ trước nhận hình học mới; regression seed cả3key và xác nhận đã clear, PASS. Review hash cuối4A699E9CA1D7540DB2B52148A93067B2DF74EBCC305E8B1B5EA4B290CC4ACACD. Các hash model/materials/review-session giữ như lượt scope ở trên.

Rendered smoke đang chờ lượt build/URL dev an toàn của parent; Get-NetTCPConnection3000/3001 không trả listener trong môi trường này, không suy chắc server đã tắt từ kết quả đó. Không reset/tạo admin hoặc chạm DB. BrowserQA vẫn chưa được thay bằng harness.

## Smoke route render đã hoàn thành

Đã dùng server local đang chạy, không build/reset .next hoặc tạo tài khoản. GET chỉ đọc /do-boc, /dieu-chinh, /phan-tho đều HTTP200, HTML hợp lệ, không Next500fallback. Kết quả frontend_route_smoke.json (20331/20367/20439bytes tại lúc kiểm). Sandbox ban đầu chặn loopback WinError10013; auto-review đã cho require_escalated thực hiện đúng các request chỉ đọc, không DB/admin/reset.

Điều này xác minh compile/render route, không chứng minh thao tác đăng nhập/upload CAD thật hoặc hydration của dữ liệu trình duyệt. Ba harness hiện tại PASS và TypeScript/ESLint đạt như trên. Không còn test nền thuộc agent frontend. Không chạm bill.tsx/optimize.tsx.

## Kiểm trực tiếp hai trang giá/tối ưu mới

reports/demo_0511/frontend_procurement_regression.cjs tải module Bill/Optimize thực, mock hooks/store/api, PASSexit0. Kiểm khôngrough/legacy thiếu plan_scope_confirmed/issues đều không post; groups cónet30 được gửi thay hình học33 trong confirmed; bill actual_onlytrue, dùng best_offer BEST_ACTUAL thay offers[0]WRONG_FIRST, hiển thị ngày; optimize procurement_modetrue, mặc định giữ thiết kế, province thiếu chặn handler, lat/lon có required+bounds; validrequest gửi vị trí/tỉnh đúng.

Không sửa bill.tsx/optimize.tsx, không DB/build. Giới hạn: đây là harness component, không trình duyệt; site coordinate required được xác minh qua thuộc tính DOM, handler chỉ guardprovince, validation vị trí còn dựa browser/backend. Không gán đây là lỗi trình duyệt đã tái hiện.
