# Đề xuất hợp đồng dữ liệu thang tầng 1→2 VN002

## Nguồn đã kiểm

Tờ PDF kết cấu KC-06-01, trang 37: [mặt bằng thang](../data20_00/VN002_THANG_T1_T2_MAT_BANG.png), [chi tiết bản nghiêng](../data20_07/STAIR_WAIST_DETAIL.png), [toàn tờ](../data20_07/STAIR_PAGE37.png). Chi tiết ghi chiều dày 120 mm theo phương vuông góc bản nghiêng và “bậc thang xây gạch”; vùng chiếu tới +3.150 ghi H=150 mm. Không đồng nhất hai vùng. Bảng thép T1 ghi SL=1 và tổng theo đường kính Ø8: 20,8 kg, Ø10: 182,2 kg, cộng số in là 203,0 kg; đây là tổng bảng của một nhóm, không tự phân cho một vế, không trộn thang tầng khác hay dầm. [Nguồn block CAD 07](../data20_07/STAIR_T1_SOURCE.json) có hash KC và các handle INSERT/ATTRIB của hàng bảng. PDF KC SHA-256 `4b6ca4f97e80b85ae4d1df555f13ad1b531c8243f52f300ec34d436357060344`; DXF KC `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`. Chưa chứng minh PDF và DXF cùng revision phát hành.

KT PDF trang 19 KT-17 ([ảnh](../../../../tmp/vn002_kt_ct_19.png)) và trang 20 KT-18 ([ảnh](../../../../tmp/vn002_kt_ct_20.png)) bổ sung mặt bằng và mặt cắt: đường đi bậc 1–17 đổi hướng, mặt bậc nhiều vị trí ghi 250 và cổ bậc nhiều vị trí 185 mm. Cao độ +3.150 ở khu vực bậc 17; +3.900 thuộc phần thang tiếp theo. Sảnh KT +0.150 và mốc ±0.000 trên mặt cắt cần đối chiếu nguồn KT/KC trước khi chốt cao độ đầu từng vế; không lấy 17×185 làm chiều cao mọi vế. Nguồn PDF KT có SHA-256 `59cad635a392c11f061d5a4f78406c00b4248f810643b9332d4b085e0809ea88` theo metadata đã kiểm; mối liên kết revision KT–KC vẫn chưa xác nhận.

## Hiện trạng và rủi ro

`Stair` chỉ giữ tổng số bậc, một rộng vế, một rộng bậc và diện tích chiếu nghỉ; `ProjectParams.stair_slab_thickness_mm` là tham số chung. `stair_works` luôn cộng thể tích tam giác bậc bê tông, dùng cùng độ dày bản nghiêng cho chiếu nghỉ và có thể cộng dầm. Với chú thích bậc xây gạch, không được dùng dòng tam giác đó làm bê tông; không thay `150` chiếu tới cho `120` bản nghiêng, hoặc giả định mọi chiếu nghỉ cùng chiều dày. Hiện chưa có contract tách vế/chiếu nghỉ để nêu nguồn từng phần, nên không coi số tính cũ là lượng thiết kế đã xác minh.

## Contract đề xuất, chưa triển khai

- Mỗi thang có ID bền, tầng đi/tầng đến và vị trí; mỗi **vế** có ID riêng, chiều cao đầu–cuối, số bậc, rộng vế/bậc, chiều dài và chiều dày **vuông góc bản nghiêng**, nguồn từng giá trị và phần thiếu. Không tự chia chiều cao tầng theo số vế khi chưa có căn cứ.
- Mỗi **chiếu nghỉ/chiếu tới** có ID, vùng, cao độ, diện tích và độ dày riêng; liên kết ranh giới và phần giao vế/sàn/dầm kèm nguồn. Vùng thiếu để `null`, không mặc định không có hoặc lấy độ dày vế.
- Phân loại bậc theo nguồn: bê tông, xây gạch hoặc chưa rõ. Chỉ cộng thể tích tam giác bậc vào công tác bê tông khi có căn cứ bậc bê tông; bậc gạch phải có công tác xây riêng và phạm vi/định mức riêng. Khi chưa rõ giữ thiếu, không cộng mặc định.
- Nguồn mỗi fact ghi `project_id`, `file_id`, `revision_id`, hash, vai trò KT/KC, trang/tờ hoặc handle/layer, giá trị gốc và căn cứ ghép instance. Cho phép người dùng nhập từng thang kèm nguồn trong snapshot được chọn, đánh dấu nhập tay/chưa duyệt; không đưa vào tham số toàn dự án hay ghi đè kết quả đã kiểm.
- Thép giữ `group_id`, tờ, phạm vi T1, từng dòng số hiệu/đường kính/dài/số lượng/khối lượng và locator. Tổng in 203 kg chỉ là đối chiếu nhóm, không cộng thêm vào các dòng thành phần. Không áp bảng T1 cho T2→3, dầm hoặc mua hàng khi chưa xác minh phạm vi và hao hụt.
- UI và API cần giữ nguyên provenance, trạng thái thiếu, snapshot ID và phân loại; request thô/results hiển thị từng thành phần và khoản loại trừ. Kiểm tra đối chiếu KT/KC khác revision, hai thang cùng tên, 120/150 khác vùng, thiếu nguồn, bậc xây/gạch và không đếm lặp dầm/sàn/thép.

Phạm vi hiện tại: phân tích và đề xuất, không sửa canonical, chạy API/UI/full hoặc DB. Chưa có receipt app cho thang này; chưa xác nhận tất cả các vế, chiều cao riêng và hình học chiếu nghỉ. Không tự đưa các giá trị ví dụ vào production.

Theo thông tin 01 chuyển, lần kiểm QA25 gần nhất chưa có tệp; 06 chưa tự kiểm UI và không xem trạng thái đó là kết quả demo.

## Đầu vào API từng thang được thêm ở source

`POST /api/projects/{project_id}/stair-evidence` nhận `profile_version`, `stair_id`, `parts[]`; mỗi part có `part_id`, `kind` (`stair`, `flight`, `landing`, `steps`), `facts[]`. Fact có tên trường, giá trị hoặc null, revision nguồn `file_id/revision_id/sha256/role` và locator `page/sheet/handle/note`. Hỗ trợ `from_floor`/`to_floor`, `run_mm`, `rise_mm`, `step_count`, `riser_mm`, độ dày theo phương `normal`, và ownership chiếu nghỉ `stair/floor/beam/unknown`. `steps_material` phân biệt `masonry`, `concrete`, `unknown`; mỗi part dùng bộ trường phù hợp. Giá trị không rỗng bắt buộc có nguồn và locator; giá trị rỗng không bị tự điền.

API kiểm quyền chủ dự án, profile phiên bản hiện tại, revision có trong lựa chọn của profile, role/hash và hash byte qua `_check_selection`; không suy mặc định từ oracle. Response giữ nguyên bộ phận và facts, `status=user_selected_unreviewed`, `saved=false`. Đây là **đầu vào kiểm nguồn dạng nháp**, không lưu snapshot, không kết nối UI hay tính khối lượng; 03/17 cần adapter có ý thức và xác nhận khi nhận contract mới. Hunk tại `api/stair_evidence.py` và endpoint/import riêng trong `api/project_analysis.py`; không sửa `_column_sources` hay `_events`. Hai test focused trực tiếp hàm đạt, không TestClient/DB/runtime; chưa kiểm UI đầu-cuối hay thao tác người dùng thực.

Hợp đồng `parts/facts` là dạng kiểm provenance, **chưa phải** model `Stair/StairFlight/StairLanding` của 03. Adapter phải ánh xạ tường minh từng field và `field_sources`, không mặc định ownership hoặc tự chuyển một ứng viên thành giá trị đã duyệt. Phần hiển thị và tính thực tế chưa được nối.

**Bổ sung mapper 06:** response `stair-evidence` nay có `stair` dạng `Stair` cùng `unmapped`. Mỗi vế/chiếu giữ ID, từng số đo và `field_sources` trỏ revision/locator do người dùng chọn, ghi rõ chưa kiểm. Chỉ gắn phạm vi khi có cả nguồn tầng đầu/cuối; nếu vật liệu bậc có nhiều lựa chọn hoặc hình học bậc chưa gắn vế thì giữ chưa ánh xạ. Mỗi lần dựng chỉ dùng body hiện tại; test bỏ vế/vật liệu xác nhận mapper không giữ dữ kiện cũ. Chưa có xác nhận việc UI xóa snapshot khi đổi dự án/revision hay adapter của 17 gắn `stair` vào `RoughRequest`; không coi đây là WorkReview end-to-end.

Candidate API riêng [STAIR_CANDIDATE_project_analysis.py](STAIR_CANDIDATE_project_analysis.py) ghép từ base C-2 frozen và đúng hunk thang, **không chứa endpoint Office đang tạm dừng**; hash file, helper và test tại [STAIR_API_CANDIDATE.json](STAIR_API_CANDIDATE.json). Hai test focused gọi hàm trực tiếp đạt, gồm khác dự án, profile không khớp và source không thuộc hồ sơ; không TestClient, runtime hay DB. Candidate chưa được nạp hoặc chạy trên ứng dụng.

**Kiểm tra mapper→Stair→compute_rough:** ba test focused đạt trên source hiện hành. Một case số liệu giả lập có vế đủ nguồn, bậc xây và chiếu chưa có ownership tạo phần bản nghiêng đã biết, phần chiếu chưa đủ và tổng partial; không cộng bê tông tam giác bậc, cốp pha còn partial khi thiếu phạm vi. Trường hợp thiếu rise không tạo lượng vế, hai lựa chọn vật liệu mâu thuẫn giữ `unknown`. Đây là test có nguồn giả lập, không phải phép chạy VN002 thực hoặc xác nhận UI. Manifest đã cập nhật hash test.

**Giới hạn nguồn PDF:** endpoint thang kiểm fact.source thuộc `profile.payload.selected_revisions`; API lưu profile hiện chỉ cho chọn revision CAD KT/KC vào danh sách đó (`project_files.py` dùng `can_analyze_cad`). `_check_selection` kiểm role/hash/path, không tự giới hạn định dạng, nhưng cổng profile ngăn PDF nguồn chi tiết đi tới endpoint theo lựa chọn thông thường. Không nới quyền, không đưa PDF vào parser CAD và không giả revision PDF là CAD; cần một hợp đồng nguồn hồ sơ được duyệt riêng trước khi UI dùng PDF trực tiếp. Dữ kiện KT/KC CAD trong profile vẫn theo kiểm quyền/revision hiện tại.
