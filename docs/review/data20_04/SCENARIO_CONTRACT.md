# D10 · Lưu và đọc lại phương án vật liệu

**Đối chiếu mã nguồn ngày 04/11/2026.** Một `analysis_runs.takeoff_id` xác định bản bóc. Một `material_scenarios.scenario_id` xác định phương án trên bản bóc đó. Một `optimization_runs.run_id` xác định lượt so sánh có lưu. Mục tiêu nghiệm thu là mở lại một lựa chọn, biết nó dùng lượng nào, giá và điều kiện nào, ai đã xác nhận nếu có, kể cả khi danh mục sau đó thay đổi.

## Phạm vi của bản bóc dùng cho nghiệm thu

Áp dụng cho phần thô **nhà ở riêng lẻ xây mới, tối đa 5 tầng**. Trước khi dùng một `analysis_id` làm ca D10, ghi lại ba căn cứ trên đúng hồ sơ nguồn: loại công trình, xây mới và số tầng theo thiết kế. Mỗi căn cứ cần tên tệp, phiên bản và tờ/trang hoặc vị trí. Gắn kết quả phân loại với bản bóc trong biên bản QA; đây là tiêu chí nghiệm thu tài liệu, chưa phải một phép kiểm tự động của DB. Hồ sơ thiếu căn cứ giữ **chờ xác minh**; hồ sơ xác định ngoài phạm vi ghi lý do và loại khỏi mẫu số. Công tác đã đo hoặc đã lưu có thể được đối chiếu kỹ thuật riêng trong thời gian chờ. [Quy tắc phân loại và mẫu số D07/D10](README.md)

Ví dụ VN002: khung tên xác nhận tên công trình “Nhà ở gia đình”; 4 tầng là metadata từ tên gói/manifest. Số tầng thiết kế và tính chất xây mới còn chờ đối chiếu. DM-1 có thể truy về dầm/cốt thép bể nước của căn nhà, nhưng một dòng đối chiếu đó không đủ xác nhận hồ sơ đủ điều kiện, phê duyệt phương án hoặc phát sinh nhu cầu mua. [Biên bản khung tên VN002](../data20_06/KHUNG_TEN_VN002.md)

## Hợp đồng đang có

| Thành phần | Đường ghi và bằng chứng hiện có | Ý nghĩa khi đọc lại |
|---|---|---|
| Khóa, nguồn gốc, trạng thái | `schema20.py:138–150` đặt FK của `analysis_id`, FK của `run_id`, bốn loại `origin`, yêu cầu `run_id` cho `optimized`, mặc định `selected=false`, tối đa một phương án được chọn trên mỗi bản bóc. | Lượt tối ưu có thể sinh nhiều phương án chưa chọn. `selected` riêng lẻ không ghi người duyệt, thời điểm hoặc phê duyệt mua. |
| Phương án sau bóc | `analysis20.py:64–78` ghi công tác, dùng danh sách vật tư kết quả làm `requirements`, tạo một phương án `origin=proposed` khi có vật tư; `assignments` dùng mặc định rỗng. `catalog_snapshot` của phương án này là trực tiếp các bảng danh mục. | Giữ dòng thiếu và phần lượng biết từ kết quả. Truy nguồn bằng `uses`/công tác/tầng nếu có. Hiện chưa bảo đảm lần tới duy nhất một cấu kiện khi nhiều công tác trùng mã/tầng. Cờ `catalog_is_historical_input` nằm ở bản phân tích cha, cần đọc khi xem dữ liệu chuyển đổi. |
| Gọi tối ưu | `api/main.py:71–83,442–461` yêu cầu hai ID cùng có hoặc cùng trống. Nếu có, kiểm tài khoản/quyền dự án và bản bóc thuộc dự án trước khi gọi bộ tính. Không có hai ID thì tính mà không ghi run qua đường này. | Cặp ID xác định ngữ cảnh lưu. Đối chiếu mã cho thấy solver vẫn nhận `req.groups` của caller; kiểm dự án chưa chứng minh từng nhóm, diện tích hoặc hệ tường trùng bản bóc đã lưu. |
| Lưu kết quả | `optimization20.py:10–30` ghi run và các phương án trong cùng transaction. Run có `method=request.method`, toàn bộ request, 7 tập danh mục/chi phí, thông tin mô hình nếu được nạp và `solutions`. Một solution sinh một scenario `optimized`. | `assignments` là bản tuần tự hóa các `GroupChoice` của solution. `requirements=[]` được ghi cho mọi phương án tối ưu. `catalog_snapshot` có dạng bọc `{catalog, model_files}`, khác cấu trúc ở đường sau bóc. Không diễn giải mảng rỗng là nhu cầu bằng 0. |
| Lượng và tiền đã dùng | `schemas.py::GroupChoice/Solution` và `optimize/problem.py:188–208,307–340` có mã vật liệu chính/vữa, NCC, lượng, đơn vị, giá, tiền vật liệu, vận chuyển, nhân công và cờ ước tính. Bộ mua tường yêu cầu hai báo giá cùng NCC, cùng cơ sở VAT/cước. | Giữ các phần tiền riêng. Tổng solution có thể gồm nhân công. Với VU02, bộ tối ưu chặn mua vữa thành phẩm khi có COMPOSED_OF. Danh sách nhu cầu sau bóc vẫn có thể giữ xi măng/cát để xin giá. |
| Kiểm JSON và liên kết | `compat20.py:253–315` kiểm takeoff cùng dự án, scenario cùng run/analysis, kiểu mảng, mã vật liệu, cặp hệ tường/vật liệu và `item_id` của assignment nếu được cung cấp. Requirement hoàn chỉnh phải có lượng; lượng sau hao hụt phải có tỷ lệ hoặc đủ bằng chứng định mức đã gồm hao hụt theo điều kiện trigger. | Đây là kiểm một số trường được biết trong JSON. Quy cách hàng thực bán, chứng từ dùng cho đơn, trạng thái người kiểm và liên kết nguồn từng phần góp vẫn cần kiểm tại lớp ghi/đọc. |

[Schema vật lý](../../../src/optimat/db/schema20.py) · [Ghi bản bóc](../../../src/optimat/db/analysis20.py) · [Ghi tối ưu](../../../src/optimat/db/optimization20.py) · [Kiểm liên kết](../../../src/optimat/db/compat20.py) · [Đầu vào API](../../../src/optimat/api/main.py)

## Khoảng thiếu cần 01 phân công

| Ưu tiên | Khoảng thiếu và hệ quả | Tiêu chí đóng trên DB thử riêng |
|---|---|---|
| P0 | Caller có thể gửi nhóm thuộc đúng dự án nhưng khác diện tích, mã hoặc phiên bản khối lượng của `takeoff_id`. | Đối chiếu nhóm với snapshot phía server trước khi lưu, hoặc ghi rõ là giả định của kịch bản. Giá theo lượng cũ không thể xuất hiện như kết quả mua của lượng mới. |
| P0 | Scenario tối ưu lưu lựa chọn nhưng thiếu nhu cầu riêng, công tác nguồn và quy đổi. Cùng tên `catalog_snapshot` đang có hai hình dạng JSON. | Chốt phiên bản/hình dạng JSON theo origin. Đọc được cả bản cũ. Với từng vật liệu mua, nối được assignment → requirement → công tác đúng analysis và căn cứ định mức. Lưu rõ giá trị đã biết, lý do thiếu, đơn vị, phần hao hụt đã nằm trong định mức, lượng bổ sung và lượng thực mua có nguồn. |
| P0 | Bảng danh mục được chụp rộng nhưng chưa có khóa dòng chứng từ hoặc snapshot cấu trúc riêng cho giá được chọn, bậc lượng, địa điểm, hiệu lực và đơn/chuyến. `cost_basis` của chế độ mua có diễn giải và nguồn, chưa đáp ứng tất cả các trường D07. | Mở lại bản cũ sau sửa giá, đổi điều kiện hoặc đổi bao/kiện vẫn truy được đúng phiếu, dòng, mã, đơn vị bán/chuẩn, chiều đổi, lượng, ngày, nơi giao, VAT và cước. Khi chưa xác nhận hiệu lực, vẫn giữ trạng thái chờ. |
| P1 | `method='auto'` lưu giá trị được yêu cầu. Solver chọn vét cạn hay NSGA-II theo kích thước không gian. Code lưu `solutions` nhưng bỏ `notes` và `n_evaluated`; seed, số thế hệ, cỡ quần thể, ngày tính hiệu lực thực và các hằng số tính có thể lấy mặc định ngoài request. Với 0 nghiệm thì run không có scenario con và lý do có thể mất. | Lưu cả cấu hình có hiệu lực, thuật toán đã chạy, phiên bản engine/quy tắc, số lượt đánh giá và lý do thiếu nghiệm. Khi đổi mặc định vẫn giải thích được run cũ. Gắn phiên bản/hash mô hình đã dùng khi có dự đoán và phân biệt với trường hợp có model được nạp nhưng choice dùng giá có nguồn. |
| P1 | Phương án `optimized` và `selected` biểu diễn hai việc khác nhau. Glue đang xét không tạo biên nhận người duyệt hoặc sự kiện audit cho việc chốt phương án. | Có hành động chọn riêng, gắn người/thời điểm/bản bóc và ghi vào `audit_logs` trong cùng giao dịch với cập nhật lựa chọn. Lượt chạy lỗi hoặc mở lại không được tự xác nhận. |

Các trường còn thiếu có thể được đặc tả trong JSONB có phiên bản của **20 bảng hiện hữu**. Chỉ chủ sở hữu schema/glue triển khai sau khi 01 giao quyền. [Lựa chọn solver và mặc định](../../../src/optimat/optimize/problem.py) · [Kết quả và cờ chi phí](../../../src/optimat/schemas.py)

## Ca kiểm bàn giao

Đây là tiêu chí cho lần kiểm riêng của 01/QA. Phiên 04 chỉ đọc mã và đối chiếu tệp dữ liệu.

| Ca | Dữ kiện và thao tác | Kết quả cần quan sát |
|---|---|---|
| D10-00 · Chọn hồ sơ | Đọc căn cứ loại công trình, xây mới và số tầng cho cùng bản bóc. Đối chiếu một trường hợp chỉ có số tầng trong tên gói và một công trình bể độc lập. | Hồ sơ đủ ba căn cứ và thuộc phạm vi mới vào mẫu số nhà ở. Hồ sơ chỉ có số tầng theo tên gói chờ xác minh. Bể độc lập bị loại kèm lý do. Một dầm bể thuộc căn nhà chỉ nhận phạm vi của cấu kiện phần thô liên quan. |
| D10-01 · Liên kết và rollback | Lưu run trên bộ thử với hai ID khác dự án, rồi thử cùng dự án nhưng thay diện tích nhóm; gây lỗi ở scenario thứ hai. | Từ chối liên kết chéo và phân biệt giả định khác bản bóc. Nếu insert thứ hai lỗi, không còn run hoặc scenario lưu dở. Dùng lệch `item_id` cùng mã công tác nhưng khác analysis như ca âm độc lập. |
| D10-02 · Hai phương án | Cùng một bản bóc, dựng hai lựa chọn giữ nguyên hình học. Đổi chiều dày ở lựa chọn thứ ba. | Hai phương án đầu có lượng, định mức, giá/thiếu giá và nguồn độc lập. Đổi dày phải kiểm/tính lại. Không mang lượng hoặc tiền từ phương án cũ sang. Đối chiếu TC19–TC21. |
| D10-03 · D07 và cấp phối | Hệ W-GK01-110 đúng hồ sơ, dùng VU02 trộn tại chỗ, một thành phần chưa có báo giá. Thêm một BULLETIN cùng mã rồi thử báo giá theo kiện lệch đơn vị. | Giữ thiếu thành phần, không tạo giá mua từ công bố hoặc giả hệ số kiện. VU02 trung gian không cộng tiền song song với XM01/CA02. Kiểm cước ghép trên cùng đơn một lần; cước chưa biết để trống. Đối chiếu TC22–TC25. |
| D10-04 · Đọc lại khi nguồn đổi | Sau khi lưu, thay danh mục giá, lead time, quy tắc mặc định và cấu hình solver trong môi trường thử. | Đọc run/scenario cũ không gọi lại giá hiện hành. Có thể chỉ đúng đầu vào, giá, điều kiện, khoản ước tính, seed nếu dùng và nguồn. Nếu chỉ có danh mục chụp lúc chuyển đổi, phải hiện giới hạn lịch sử. Đối chiếu TC27. |
| D10-05 · Rỗng và thiếu | Lưu lượt không nghiệm do thiếu báo giá, lượt phân tích có dòng thiếu lượng, và công tác thực sự có lượng bằng 0. | Phân biệt ba trường hợp: không có phương án hợp lệ, có nhu cầu chưa biết lượng, và lượng 0 có căn cứ. Không để `requirements=[]` xóa lý do không nghiệm hoặc biến phần chưa định lượng thành 0. |
| D10-06 · Chọn và mở lại | Hai người/bản trình duyệt chọn hai phương án của cùng analysis; đổi sang bản bóc mới rồi mở lịch sử. | Tối đa một lựa chọn cho mỗi analysis. Người, thời điểm và lý do chọn truy được, bản mới không tự kế thừa phê duyệt. Snapshot cũ giải thích được sau khôi phục. Đối chiếu TC26–TC28. |

[Các ca schema đã có trong mã kiểm thử](../../../tests/test_schema20.py) · [Kế hoạch TC01–TC28](../../KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md)
