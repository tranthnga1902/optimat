# Điều chỉnh kế hoạch: kiểm công tác trước chọn vật liệu

Chỉ đạo chủ đồ án ngày 03/11/2026: chat “Xem kế hoạch hiện tại” làm cố vấn kế hoạch và gửi yêu cầu cho các phiên liên quan triển khai.
Không tiếp tục tự sửa source trong chat kế hoạch. Tài liệu này bổ sung PLAN.md và KIEM_TRA_CONG_TAC_KHOI_LUONG.md;
phiên “Kiểm tra tiến độ dự án” giữ quyền điều phối writer, freeze và hồi quy chung.

## 1. Luồng đã chốt và nguyên tắc nghiệp vụ

**Dự án → Bóc tách bản vẽ → Kiểm tra công tác và khối lượng → Chọn vật liệu → Vật tư và giá → Tối ưu / xuất bảng mua.**

- `/do-boc`: tiếp nhận KT/KC, nhận dạng, kiểm hình/tầng tham khảo và hình được cộng; xác nhận tường/lỗ mở.
- `/phan-tho`: xem công tác theo tầng và từng cấu kiện; kiểm dài/rộng/cao/dày/diện tích, khoản trừ, khối lượng, nguồn và phần thiếu.
  Bổ sung thông số hình học tại đây; không yêu cầu chọn phương án vật liệu mới được xem/tính khối lượng.
- `/dieu-chinh`: chọn loại vật liệu, phương án tường, mác/cấp phối, cách cung cấp. Không gọi bước này là xác nhận hình học.
- Vật tư/giá dùng đúng bản khối lượng và lựa chọn đã lưu. Nếu chọn vật liệu làm đổi dày/cấu tạo thì đánh dấu các công tác bị ảnh hưởng
  cần kiểm lại, không giữ kết quả tối ưu cũ. Không tự suy thiết kế chỉ để đi qua bước.
- Kiểm khối lượng trước vật liệu là thứ tự hợp lý, nhưng không đồng nghĩa khối lượng độc lập hoàn toàn với cấu tạo.
  Thiếu thông số cần thiết giữ thiếu; chưa biết vật liệu vẫn có thể tính hình học danh nghĩa có nhãn rõ.

## 2. Hợp đồng kích thước cần hoàn thiện trước nghiệm thu

- `WorkItem.dimensions` là danh sách từng cấu kiện/lớp, không chỉ một kích thước đại diện cho nhóm khác nhau.
  Dùng trường có cấu trúc; không phân tích chuỗi formula hoặc suy dài/rộng từ thể tích/diện tích.
- Dài/rộng/cao/dày đơn vị m, diện tích m², số lượng ghi riêng; giữ nguồn và cách hiểu của từng phần.
- Tường: dài từng đoạn, dày khối xây, cao xây phân biệt cao tầng. Cột: hai cạnh tiết diện và cao đoạn.
  Dầm: dài net phân biệt khoản trừ, cao toàn tiết diện phân biệt cao dưới sàn.
- Móng: từng lớp/bậc, đáy và đỉnh lớp vát; nhập thể tích trực tiếp không sinh kích thước giả.
  Đất: kích thước đáy hố và sâu đào không gọi là kích thước khối đắp.
- Sàn/mái/nền: diện tích và dày khi biết; không ép hình thành chữ nhật. Thang: dài chạy ngang phân biệt dài nghiêng,
  cao tầng/cao bậc, rộng vế, bản thang và dầm thang. Thép bảng: chiều dài cắt và số thanh; thép theo hàm lượng không có dài/rộng/cao độc lập.
- Cốp pha và dòng trừ dùng đúng hình học cấu kiện liên quan; khoản trừ/hợp đoạn không được hiển thị như một cấu kiện mới.
  Một view dùng nhiều tầng phải giữ rõ số lần lặp, không nhân cả chiều dài và số lượng gây đếm đôi.
- Phân biệt ô chưa có với ô không áp dụng; thiếu không thành 0. Nhãn “Đã kiểm” không nâng A/B/C/D.

## 3. Phân công cho các phiên hiện có

| Phiên | Trách nhiệm được đề nghị | Điều kiện bàn giao |
|---|---|---|
| Kiểm tra tiến độ dự án | Điều phối duy nhất quyền ghi source, thứ tự tiếp nhận, freeze và full | Xác định owner backend/UI, hash cuối, không full khi writer còn sửa |
| Review lộ trình S13 phần thô | Review hợp đồng kích thước và delta backend; sau đó triển khai sửa nếu được điều phối giao quyền | Ca khác kích thước trong nhóm, thiếu số, đơn vị, nguồn, N03/Q02, không đổi số khối lượng ngoài sửa lỗi được giao |
| Đề xuất chọn nguyên liệu tự động | Chủ trì giao diện/luồng mới sau khi được cấp quyền; giữ preview nhận nét hiện tại | Menu/Steps/guard, bảng và chi tiết kích thước, xác nhận/lưu/khôi phục, mất hiệu lực kết quả cũ; browser QA |
| Xem toàn bộ kế hoạch hệ thống | Đồng bộ luồng vật tư/giá/tối ưu với bản khối lượng đã kiểm và vật liệu đã chọn | Tính lại đúng sau đổi vật liệu, giữ phần thiếu, API/UI/BOQ nhất quán; không nhận test cũ bao phủ delta mới |
| J04 — Rà nguồn định mức phần thô | Nhận thông tin thay đổi snapshot; hồi quy theo lịch của điều phối | Không tự mở full cạnh tranh, báo terminal và hash trước/sau trên nguồn đã freeze |

Các phiên chỉ sửa đúng phạm vi được điều phối cấp. Không tạo thêm phiên, không rollback thay đổi của phiên khác.

**Điều phối phản hồi:** bảng trên là đề xuất, không phải release quyền ghi. Owner hiện tại giữ nguyên: phiên UI giữ
main/viewer/Review; demo giữ pricing/optimize/wall_groups; dữ liệu giữ admin_ops/adminprojects/test liên quan;
review/N03 giữ nhiệm vụ hiện tại, O01 chỉ đọc. Root review phiếu rồi mới cấp quyền metadata/luồng mới.
Các thông báo đã gửi chỉ yêu cầu chuẩn bị/review và chờ root cấp quyền, không mở writer song song.

## 4. WIP bàn giao từ chat kế hoạch — chưa source-ready

Writer WorkDimensions/WorkItem.dimensions là chat “Xem kế hoạch hiện tại”, ID 01a1a1ee-cbe0-7ce3-a0de-22f89aab7fbd.
Đã dừng ghi source theo chỉ đạo mới. Không quy các thay đổi này cho nhóm demo.

Danh mục 20 tệp source/self-check đã chạm và SHA256 quan sát tại thời điểm bàn giao:
[manifest](review/WORK_DIMENSIONS_HANDOFF_PLAN_20261103.json). Không có hash/base chụp trước từng lần ghi của chat này,
nên không nhận git diff so HEAD là delta riêng (cây đã có nhiều thay đổi từ trước). Reviewer có staging/base cho bốn tệp
ban đầu theo WORK_DIMENSIONS_REVIEW_20261103.md; root phải kiểm lại hash hiện tại trước khi cấp quyền. Manifest là dấu mốc
quan sát, không cam kết nguồn không bị phiên khác đổi sau đó.

Callers cần review: producer công tác → compute_rough → RoughResult/POST /api/takeoff/rough và rough/auto →
WorkReview/roughRequest → Materials.save → saveMaterialSession → Bill/optimizer/BOQ. Trường dimensions là bổ sung JSON,
không thay lược đồ DB. Kiểm cách lưu JSON hiện có, dữ liệu phiên cũ không tự trở thành đã kiểm.
Các ca bị chạm hành vi cần bổ sung/đối chiếu: test_rough_walls, test_rough_columns, test_rough_joints,
test_rough_stairs, test_rough_foundations, test_rough_secondary, test_rough_steel, test_rough_api;
chat này chưa sửa hay thêm Python test cho dimensions. Self-check frontend cũ chỉ kiểm render thiếu/khóa nút,
không đủ chứng minh tương tác hoặc metadata mới.

- Backend đã có delta kích thước ở rough/models,walls,columns,beams,foundations,areas,stairs,secondary,steel,takeoff.
  Chưa review/kiểm đủ. Reviewer đã nêu nhãn dài net dầm đang ghi khoản trừ, cần sửa phân biệt rõ.
- Frontend đã có WorkReview.tsx, type dimensions trong model.ts; lượt trước có đổi Review/Rough/materials/Steps/Shell/projects.
  Cần kiểm lại guard snapshot, lưu kiểm tra, khôi phục và tính lại sau chọn vật liệu; chưa tuyên bố hoàn tất.
- TypeScript lượt kích thước đạt. Lượt focused có 103 dấu chấm trước khi ngừng tiến triển, đã ngắt handle 76803,
  exit1; không có tổng terminal và không được ghi “103 passed”. Chưa chạy full cho delta kích thước.
- Đã thấy giao diện trên Chrome, nhưng chưa kiểm được hồ sơ thật. File chooser upload bộ Tân Bình bị gate báo người dùng
  từ chối quyền cho http://127.0.0.1:3000. Không thử lách qua native picker, API hoặc browser khác. Chờ người dùng tự chọn
  file hoặc cấp lại quyền; đây là blocker QA, không phải lý do bỏ kiểm thử mã không phụ thuộc browser.

## 5. Thứ tự thực hiện và nghiệm thu

1. Điều phối xác nhận tất cả writer và nguồn hiện tại; khép/sửa snapshot đang lỗi trước khi cho mở công việc mới.
2. Reviewer khóa hợp đồng kích thước và các lỗi delta; owner backend sửa theo hợp đồng, thêm test trực tiếp trên producer và HTTP JSON.
3. Owner UI dùng hợp đồng đã chốt, khép bảng/chi tiết và guard; owner giá/tối ưu xác minh dữ liệu sau chọn vật liệu.
4. Kiểm trọng tâm: khác tiết diện/chiều dài trong nhóm; None/0; móng nhiều lớp/vát; sàn không chữ nhật;
   thang thiếu thông số; thép bảng/hàm lượng; lặp tầng; N03/Q02; phản hồi cũ, lỗi lưu, đổi dự án và reload.
5. Freeze nguồn, full theo điều phối. QA browser trên một bộ ACTUAL-build KT+KC sau khi giải quyết quyền tải file:
   xác nhận hình → kiểm kích thước từng nhóm → sửa/tính/lưu → chọn vật liệu → tính lại vật tư → giá/tối ưu → quay lại/reload.
   Lưu ảnh, hồ sơ/phiên bản và thông số đã dùng; không lấy dữ liệu SYNTHETIC làm bằng chứng độ chính xác thực.
6. Chỉ đánh hoàn tất khi có test terminal, hash ổn định, đối chiếu API/UI/BOQ và browser evidence; thiếu bước nào ghi riêng bước đó.
