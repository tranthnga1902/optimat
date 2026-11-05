# DATA20 — 07, D02–D04 — 04/11/2026

**Cổng phạm vi bổ sung:** chỉ phần thô nhà ở riêng lẻ xây mới≤5 tầng. Đọc [căn cứ phạm vi từng hồ sơ](PHAM_VI_HO_SO.md): VN002 có khung tên “Nhà ở gia đình”,4 tầng hiện mới là khai báo manifest/tên gói; số tầng thiết kế và tính chất xây mới chưa kiểm giữNULL. Các báo cáo nguồn/đápán không tự chứng nhận điều kiện phạm vi. DM-1 là cấu kiện bể thuộc căn nhà, không tính thành công trình bể độc lập hoặc identity mới.

Gói nháp ngoài DB, đối chiếu `docs/schema/CSDL_20_BANG.md`, kế hoạch DATA20 và các trường vật lý tại `src/optimat/db/schema20.py`. Không sửa canonical hoặc chạy lại đo CAD. Không đọc backup/DSN, không kết nối DB, không chạy suite. Tài liệu Word không được chỉnh trong lượt này; nguồn hợp đồng dùng Markdown/schema hiện hành.

## Ba tệp

- `GROUND_TRUTH_READINESS.csv`: **4 công trình duy nhất**, giữ Tân Bình/Hương/Sang ở build, Dĩ An ở test. Đã đọc từng file KT/KC/tiên lượng để tính SHA-256, ghi scope và thiếu. Hai nguồn incoming trùng công trình cũ không trở thành hai hồ sơ mới. Không có công trình thứ5 để báo đủ chỉ tiêu.
- `MAU_NHAN_CAU_KIEN.csv`: **2 nhãn nhóm nháp** có handle/layer/tọa độ: nhóm thép lanh tô Hương và nhóm thống kê thépØ12 bể nước Sang. Đây không phải2 cấu kiện vật lý đã nhận dạng đầy đủ. Giữ floor, vùng hình, tỷ lệ, transform và số instance trống khi chưa xác định. Các lần xuất hiện KLCT/tổng hợp không tạo thêm bể vật lý.
- `MAU_NHAN_SO_DO.csv`: **4 ứng viên khối lượng đọc từ chữ CAD**, gồm92,9kg Hương và20,6/17,0/36,9kg Sang. Mỗi dòng truy được công trình/file/hash/trang/hình/handle/tọa độ/quan hệ. Không gọi chúng là đo hình học từ đường nét, không chuyển ô khối lượng thành chiều dài/tiết diện. Ba số Sang được giữ ở tầng con/tổng khác nhau; chưa chọn số chuẩn hoặc tự thay36,9 thành37,6.

## Ánh xạ và quy ước nhập tương lai

`element_key/kind/level_code/occurrences/relations` là ứng viên cho `building_elements`; `property_code/value/unit/status/selected/method` cho `element_measurements`; file/hash/handle/tọa độ/raw_content là dữ liệu để tạo `document_revisions` và `evidence_sources.source_ref/raw_content`. Phê duyệt/thiếu/quyền dùng giữ trong metadata/payload phù hợp. Nhãn `steel_schedule_group` và mã `design_steel_mass` là đề xuất ngữ nghĩa trong báo cáo, cần người tích hợp ánh xạ vào vocabulary ứng dụng; không tuyên bố importer đã hỗ trợ.

Các cột `analysis_id`, `revision_id`, `evidence_id` để trống: không phát minh FK. Đây là template bàn giao, **không phải CSV có thể INSERT trực tiếp**. Khi được cấp quyền nhập, tạo snapshot/file revision có thực, liên kết evidence cùng analysis, lấy ID thật rồi gắn measurement. Không ghi ground truth vào `takeoff_items` như thể nó là lần chạy đã đánh giá; đáp án vẫn nằm ngoài DB theo hợp đồng DATA20.

Ô trống nghĩa chưa xác định/NULL, không phải0. `status=A` ở4 dòng chỉ phản ánh số đọc trực tiếp từ ô chữ nguồn đã có handle; **không phải trạng thái người thật đã duyệt**, không chứng minh bảng nhất quán hoặc hình học đúng. `selected=false` tất cả; `approval_status=nhap`, reviewer/ngày kiểm đều trống. Không đánh dấu đã kiểm có người thật. Nhãn theo nhóm phải được tách thành occurrence vật lý và nối đúng tầng trước khi dùng đánh giá nhận dạng từng cấu kiện.

Đối với Sang, `conflict_group` nhóm theoØ12 của cùng bể; `relation=component_subtotal` và `summary_cell` phân tầng phép cộng.20,6+17,0=37,6 khác36,9 là mâu thuẫn bảng, không phải ba giá trị thay thế cùng một phạm vi. Không cộng cả cha lẫn con và không chọn tổng để che phần thiếu. Đường dẫn INSERT trống vì bằng chứng hiện dùng TEXT modelspace đã trích, không suy chuỗi INSERT mới.

## Sẵn sàng và thiếu

D02 Tân Bình hiện0 dòng `da_kiem`; các nhãn incoming `human_approval=false`. Hương4/Sang5 nhãn DEV mức bảng,211/244 dòng cách ly; toàn incoming464 dòng có455 cách ly. Chín nhãn DEV không phải chín đáp án độc lập đã kiểm. Dĩ An giữ split test nhưng chưa có đáp án kiểm độc lập hoặc xác nhận lịch sử sử dụng test; không tuyên bố độc lập chỉ từ tên split. Quyền dùng/phiên bản hồ sơ chưa rõ phải được chủ đồ án xác nhận trước phát hành dữ liệu.

Chưa hoàn thiện vùng hình/tầng/transform, danh mục physical instance, các số đo hình học, quy tắc giao/trừ và bộ đáp án độc lập. Không đo lại CAD nặng hoặc mở toàn464 dòng để đủ số lượng trong lượt này. Các quyết định bể, cover, miền rải, nắp cửa thăm và đơn trọng đã có tại `reports/review_housing_20261103/DIEM_CAN_CHOT_THEP_BE.md`; không coi template này là phê duyệt các quyết định đó.

## Kiểm tại chỗ và bàn giao

Tạo CSV UTF-8 BOM, dùng thư viện CSV để giữ đúng dấu phẩy/JSON có trích dẫn. Assert4 công trình duy nhất,2 nhóm,4 ứng viên, người kiểm trống và selected=false. File nguồn đọc được khi hash; không kết luận đã parse/mở thành công mọi drawing bằng CAD từ phép hash. Không chạy test suite, CAD pipeline hoặc DB; không thay đổi mã, snapshot hay bộ đáp án canonical.

Đề nghị01 cấp lượt tiếp theo: chọn một hồ sơ build và phạm vi nhỏ để gắn từng instance/vùng/tầng, chốt vocabulary và hướng ánh xạ template vào snapshot thử nghiệm; người kiểm thực xác nhận từng phần có nguồn. Chưa có quyền đó thì gói này dừng ở dữ liệu nháp có truy vết.
