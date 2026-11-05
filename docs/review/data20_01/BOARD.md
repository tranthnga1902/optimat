# Bảng điều phối DATA20
**Trạng thái hiện tại:** DB chính đã committed_verified với 20 bảng theo receipt S20; ba API đã khôi phục và qua kiểm tra GET đọc PostgreSQL. DATA20/reader chưa nghiệm thu. Đã đối chiếu một hàng thép VN002, còn thiếu liên kết dầm vật lý/tầng/trục. Các đoạn phía dưới ghi ‘chưa chuyển’ là lịch sử trước commit; xem mục cập nhật cuối.


Cập nhật: 04/11/2026, múi giờ UTC+7. Owner tài liệu: chat 01. Trạng thái đợt: **đang kiểm kê và lập gap ledger; chưa nghiệm thu dữ liệu, chưa phát hành**.

## Quyết định và giới hạn đang hiệu lực

Chủ đồ án đã chốt 20 bảng và giao các phiên hoàn thiện dữ liệu tại chat «Chuẩn hóa bóc tách vật liệu từ bản vẽ» (`01a1a5b2-4833-7363-be04-aeb0c78e6c04`). Chỉ phạm vi DATA20 được tiếp tục. W5/demo/AI/browser/build/deploy và runtime 3001/8001 vẫn tạm dừng.

Nguồn điều hành: [schema 20 bảng](../../schema/CSDL_20_BANG.md), [kế hoạch sáu tuần](../../KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md). Hai Word tại outputs/database20 là tài liệu bàn giao; số trang 20/7 theo phiên schema, 01 chưa render lại. Tên cũ là view tương thích, không phải bảng vật lý bổ sung.

Phiên schema (gọi là **S20** trong bảng này, không nhầm chat 01) giữ quyền ghi duy nhất src/optimat/db/, glue save_review/save_rough/optimize, scripts/schema SQL, Word và test FakeSession đang sửa. Main DB **chưa chuyển**, theo bàn giao S20; thử bản sao 28→20 không phải biên nhận chuyển main DB. Không đọc backup private/DSN/test_url.txt, không reset hay ghi DB thật. Không mở suite/CAD nặng, huấn luyện hoặc gọi AI trả phí.

Các phiên dưới đây chỉ ghi báo cáo trong thư mục riêng. Chưa cấp quyền sửa source/data canonical cho bất kỳ phiên báo cáo nào. 01 không ghi đè tài liệu hoặc báo cáo của owner khác.

## Owner, phụ thuộc và đầu ra

| Owner | Phạm vi và thư mục ghi duy nhất | Đầu ra phải giao | Phụ thuộc | Trạng thái/bằng chứng hiện tại | Cổng nhận |
|---|---|---|---|---|---|
| S20 | Schema/migration/DB/glue/SQL/Word; ngoài quyền ghi của 01 | Receipt bản sao, đối chiếu từng dòng/cột, rollback/restore, test và hash | 14 review; 15 ma trận | Theo bàn giao: bản sao đã chuyển; main chưa chuyển. Full gần nhất dừng 439 passed, 4 skipped, 1 lỗi mock FakeSession thiếu flush, S20 sửa | G0; chưa nhận full pass hoặc production migration |
| 01 | docs/review/data20_01/ | BOARD.md; gap ledger hợp nhất; lựa chọn Pioneer/split; lịch release có phạm vi | Tất cả báo cáo | Đã đọc kế hoạch, exact scope và snapshot 7 phiên đang làm; chưa thu đủ deliverable | Không đóng DATA20 chỉ vì có báo cáo |
| 00 | docs/review/data20_00/ | KE_HOACH_DIEU_PHOI.md; MVP, ngưỡng và quyết định người dùng | Board 01, QA15 | Đã nhận và đọc kế hoạch 00; chưa chốt ngưỡng nghiệp vụ | Ngưỡng nghiệp vụ do người có thẩm quyền chốt |
| 06 | D01; docs/review/data20_06/ | HO_SO_INVENTORY.csv, SCHEMA_MAPPING.md, README.md; 1 Pioneer và 5 hồ sơ đề xuất | File/hash/nguồn/quyền dùng; document_revisions | Đã nhận/đọc 3 báo cáo; 458 đường dẫn được hash, chưa kiểm mở CAD đợt này | G1: đủ cặp, revision/hash, khả năng mở và quyền dùng có bằng chứng |
| 07 | D02–D04; docs/review/data20_07/ | GROUND_TRUTH_READINESS.csv, MAU_NHAN_CAU_KIEN.csv, MAU_NHAN_SO_DO.csv, README.md | 06 hồ sơ; nguồn số đo; người kiểm độc lập | Đã nhận/đọc readiness 4 identity, 249 dòng coverage VN002 và exposure ledger; chưa có oracle độc lập đã kiểm | G2: số đo truy nguồn, split độc lập, đáp án có người kiểm thật |
| 05 | D05–D06; docs/review/data20_05/ | GAP_DINH_MUC.csv, README.md; đối chiếu 31 DB/68 CSV; 3–5 phương án tường | Công tác Pioneer; nguồn định mức/quy đổi/hao hụt | Đã nhận/đọc 286 dòng gap, 22 dòng ưu tiên VN002; chưa đối chiếu từng dòng DB31/CSV68 | G3: hệ số có đơn vị/phạm vi/nguồn; không hao hụt hai lần |
| 04 | D07/D10; docs/review/data20_04/ | SUPPLY_READINESS.csv, SCENARIO_CONTRACT.md, README.md | 05 mã/quy cách; 16 cơ sở giá; S20 optimization20 | Đã nhận/đọc CSV98 mã và hợp đồng 6 ca D10; giá mua chưa đủ | G4/G5: phương án có nguồn và snapshot tái giải thích được |
| 16 | D08; docs/review/data20_16/ | PRICE_DATA_GAPS.csv, READINESS_20.md; mẫu thu thập, baseline, split thời gian/vật liệu | 04 cung ứng; nguồn giá gốc | Đã nhận/đọc ledger78 dòng = 63 quan sát + 15 gap; chưa đủ train/mua | G4: cùng cơ sở giá; báo giá mua khác giá công bố/dự đoán |
| 15 | QA; docs/review/data20_15/ | TEST_MATRIX_28.csv, EVIDENCE_REQUIREMENTS.md; ca bổ sung toàn vẹn/restore | S20 log/receipt đã lọc bí mật; báo cáo các owner | Đã nhận/đọc matrix28 và yêu cầu evidence; execution gate chưa đóng | G0–G6: bằng chứng đúng ca, mẫu số và giới hạn |
| 14 | Review độc lập; docs/review/data20_14/ | REVIEW.md; P1/P2 có tình huống tái hiện | Schema20/compat/migrate/analysis/optimization và callers | Đã nhận/đọc 2 P1 + 3 P2, chuyển S20; chưa có retest sau sửa | G0/G5: lỗi mất dữ liệu/chéo nguồn/immutability có owner xử lý |
| 03 | D09 rule_sets; docs/review/data20_03/ | RULES_INVENTORY.csv, RULE_TEST_GAPS.md, README.md | 07 nhãn, 15 ma trận, S20 hợp đồng JSONB | S20 đã giao reports-only; chưa nhận deliverable | G3/G6; chưa suy đủ D09 từ việc có schema |

Tên đầu ra ở trên là deliverable dự kiến, **không khẳng định tệp đã tồn tại hoặc đã được 01 đọc**. Khi nhận: 01 phải đọc nội dung, kiểm đường dẫn/hash liên quan, phân loại lỗi và cập nhật trạng thái.

## Gap ledger ban đầu

| Mã | Khoảng trống và bằng chứng đầu vào | Owner/việc tiếp theo | Chặn |
|---|---|---|---|
| L01 | 128 file, 2 revision và 4 profile là số kiểm kê cũ trong kế hoạch; không chứng minh đủ hồ sơ hoặc đúng quyền | 06 đối chiếu manifest/hash/phiên bản; không tạo hash/quyền giả | Pioneer/thu thập |
| L02 | cases.csv: Tân Bình build, Dĩ An test; incoming VN001/VN002 build. VN003 trùng Dĩ An, VN004 trùng Tân Bình theo HO_SO_NHAP_20261103.md | 06/07 giữ identity, so hash và lịch sử sử dụng; không đếm 4 nguồn thành 4 công trình mới | Split/benchmark |
| L03 | Đáp án nguồn ghi chua_kiem, người kiểm trống; quyền dùng chua_ro | 07 lập nháp có nguồn; 00 thu quyết định/người kiểm; không tự gắn da_kiem | Nghiệm thu nghiệp vụ |
| L04 | 31 rough_norms trong DB nguồn so với 68 CSV theo bàn giao S20 | 05 đối chiếu từng hệ số/phiên bản, không nạp CSV để lấp số dòng | Release định mức |
| L05 | 2.867 suppliers nhưng 13 cặp cung ứng và 63 quan sát giá theo kế hoạch | 04/16 chứng minh từng mã/quy cách/đơn vị/VAT/cước/hiệu lực; Maps không phải báo giá | Mua/tối ưu có giá |
| L06 | Snapshot JSONB còn quan hệ do ứng dụng kiểm; không phải mọi liên kết có FK | 14 review; 15 yêu cầu ca chéo analysis/project, orphan, NULL selected và scenario | Toàn vẹn/phục hồi |
| L07 | Chưa có full regression pass của schema mới; số 439/4/1 là lần dừng theo S20 | S20 sole owner sửa mock và chốt lease chạy; 15 đọc kết quả, không chạy đồng thời | G0/release |
| L08 | Chưa có danh sách >=5 công trình độc lập/2 test đủ nguồn và đáp án kiểm | 06/07 đề xuất; báo thiếu nếu không đủ, không nhân bản cùng công trình | Công bố khả năng tổng quát |
| L09 | D09 chưa có deliverable/owner riêng trong bảy phạm vi S20 giao | 01 đề nghị S20 giao rõ, trước khi cấp quyền src/data | Release quy tắc |

## Pioneer Pack và tập kiểm độc lập

**Đề cử ban đầu, chưa chốt sẵn sàng:** VN002 Nhà Sang làm Pioneer BUILD vì có cặp kiến trúc/kết cấu và dự toán tham chiếu trong incoming_20261103.json/HO_SO_NHAP_20261103.md, đã được dùng phát triển. 06 phải xác minh mức đầy đủ, khả năng mở, hash, phiên bản và quyền dùng; 07 chỉ rõ công tác/số đo chưa đủ, không dùng tiên lượng để điền số thiếu. Nếu không đủ, 06 đề xuất Tân Bình hoặc VN001 cùng bằng chứng; 01 chỉ chốt sau so sánh báo cáo. Chưa có hồ sơ nào được tuyên bố hoàn chỉnh.

**Giữ test hiện đăng ký:** Dĩ An/banve1 (VN003 là cùng identity) trong cases.csv; chưa kết luận còn độc lập trước khi 07 rà lịch sử dùng để phát triển. VN004 không là test mới vì trùng Tân Bình BUILD. Cần thêm ít nhất một công trình test độc lập nếu đạt quy mô 5; nếu chưa đủ hồ sơ/quyền/đáp án thì ghi NOT_EVALUATED và không công bố chỉ số tổng quát. Mọi bản dịch/xoay/đổi layer của một công trình giữ cùng split; SAMPLE chỉ dùng kiểm công thức/ca biến đổi, không đại diện độ chính xác ACTUAL.

Quyết định chốt cần 06 inventory + 07 readiness + 15 kiểm identity/split + 00 chốt phạm vi/người kiểm. Không thay cases.csv hoặc đáp án canonical trong đợt kiểm kê này.

## Các cổng nghiệm thu

- **G0 — Nền tảng kỹ thuật:** đúng 20 bảng vật lý, view không đếm bảng; migration/đối chiếu/rollback/restore trên DB riêng có receipt; test/skip phân loại rõ. Main migration là quyết định riêng, do S20 thực hiện khi được duyệt.
- **G1 — Hồ sơ:** manifest hash/role/revision/quyền dùng/khả năng mở; một Pioneer đủ phạm vi, không chỉ đủ hai tên file.
- **G2 — Nhãn/đáp án:** nguồn từng số đo, ứng viên mâu thuẫn, NULL khác 0; reviewer độc lập, split và mẫu số; A/B/C/D không là trạng thái người duyệt.
- **G3 — Danh mục/định mức/quy tắc:** mã/quy đổi/đơn vị/nguồn/phạm vi; hao hụt một lần; dữ liệu SAMPLE không giả ACTUAL; D09 ca dương/âm và chống leakage.
- **G4 — Cung ứng/giá:** bằng chứng từng vật tư trọng tâm, cùng cơ sở so giá; thiếu giá giữ thiếu; chưa đủ dữ liệu thì chỉ tra giá, chưa train/khẳng định rẻ nhất.
- **G5 — Snapshot/phương án:** đọc lại kết quả cũ sau đổi danh mục/giá; unknown material vẫn có hình học; đổi chiều dày buộc tính lại; không đề xuất thành phê duyệt/mua.
- **G6 — Đánh giá/bàn giao:** 28 ca có evidence/owner và trạng thái PASS/FAIL/NOT_RUN/NOT_EVALUATED; benchmark thực độc lập có mẫu số/dung sai được chốt; manifest source/data/engine/config/hash và hướng dẫn phục hồi.

Đạt kỹ thuật và nghiệm thu nghiệp vụ là hai trạng thái riêng. Chưa có G nào được 01 đóng tại bản board đầu tiên.

## Thứ tự release đề xuất, không phải lệnh triển khai

Không gán ngày hoàn thành khi chưa chốt nhân lực. Sáu tuần trong kế hoạch là khung dự kiến, không là cam kết.

| Đợt | Phạm vi cụ thể dự kiến | Điều kiện bắt đầu / người ghi | Kiểm cần có |
|---|---|---|---|
| R0 — hợp đồng và kiểm kê (Tuần 1) | Chỉ reports/data20; schema20 và glue do S20 | Nhận đủ 7 báo cáo + D09 owner; S20 xử lý review P1/P2 | Đối chiếu gap ledger, full/DB chỉ một lease S20 |
| R1 — Pioneer (Tuần 2) | Manifest hồ sơ/nhãn/ground truth nháp cho công trình BUILD đã chọn | 01 cấp chính xác file/owner sau inventory; 06 hồ sơ, 07 nhãn; không tự thêm test vào build | Hash/khả năng mở/split; chuyên môn kiểm phần đáp án |
| R2 — danh mục/định mức (Tuần 2–3) | data/catalog và dữ liệu định mức/quy tắc đúng các dòng có nguồn được duyệt | 01 duyệt diff theo GAP_DINH_MUC; một owner mỗi file; S20 giữ SQL/import | So đơn vị/hệ số/hao hụt; test tập trung, không reload main |
| R3 — cung ứng/giá/phương án (Tuần 3–4) | Các dòng supplier_materials/price_records/cost và scenario có chứng từ | 04/16 đề xuất delta cụ thể; S20 sole DB writer | Kiểm cùng cơ sở, snapshot và vét cạn ca nhỏ khi được mở lease |
| R4 — đánh giá độc lập (Tuần 4–5) | Đóng băng engine/config/rules/catalog/test; tập độc lập đủ điều kiện | 15 điều phối bằng chứng sau khi được cấp lease; 00 chốt ngưỡng | 28 ca + benchmark thực, không lẫn synthetic với thực |
| R5 — bàn giao (Tuần 6) | Manifest release, restore receipt, từ điển/ERD/report và phần chưa đạt | Sau G0–G6 của phạm vi phát hành; S20 migration main riêng theo quyền | Hồi quy/khôi phục/đọc lại snapshot; công bố giới hạn |

Sau khi báo cáo về, 01 sẽ thay các dự kiến R1–R3 bằng danh sách **đường dẫn + dòng/ID dữ liệu + owner + hash trước/sau + test ảnh hưởng + rollback**, rồi mới cấp quyền ghi canonical. Không dùng bảng này làm quyền tự triển khai.

## Bằng chứng 01 đã đọc

- docs/schema/CSDL_20_BANG.md; docs/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md; AGENTS.md.
- src/optimat/db/schema20.py phần metadata/ánh xạ (chỉ đọc source, chưa truy DB).
- data/ground_truth/index.csv; data/ground_truth/du_toan/cases.csv; data/ground_truth/du_toan/HO_SO_NHAP_20261103.md.
- Exact giao việc S20 cho 00/05/06/07/16/15/04/14 và snapshot wait_threads của 7 phiên báo cáo; tất cả đang hoạt động trong đợt DATA20 khi mở board.

Chưa chạy test, migration, CAD, build/deploy, AI/browser hoặc ghi dữ liệu canonical trong đợt này. Các số liệu lịch sử từ kế hoạch/bàn giao được ghi đúng nguồn, không trình bày như phép đo DB mới của 01.

## Cập nhật nhận bằng chứng · 04/11/2026

01 đã tự đọc reports/schema20_migration_trial.json, SHA-256 `C334AA3C1A2CBB90CE36545F7907CCE01BC3D15CF5914FE238CC2DDF4175DE47`. Receipt ghi 28 khóa legacy, 20 physical: 24 projects; 128 file + 2 revision = 130 document_revisions; 26 analysis_runs; 98 materials; 2.867 suppliers; 63 price_records; 31 work_norms. Backfill ghi 14 elements / 28 measurements / 14 evidence / 476 takeoff_items / 1 scenario. Audit 10→11 phù hợp một sự kiện chuyển đổi. Trường verified tuyên bố đối chiếu mọi cột/dòng qua view; 01 chưa có diff/hash từng cột để tự tái kiểm, chưa có execution receipt restore/rollback. Đây là receipt **bản sao thử**, không là main migration hoặc đáp án CAD đã kiểm.

S20 đã báo sửa FakeSession.flush/connection và mock store_details, đang chạy reports/schema20_remaining.log + remaining.xml trên clone riêng. 01 chỉ đọc tail thấy tiến độ, chưa có kết quả cuối; không cộng số của hai lượt thành full pass, không cấp suite khác. L07 giữ mở.

Đã đọc [kế hoạch 00](../data20_00/KE_HOACH_DIEU_PHOI.md): nhận deliverable kế hoạch ở mức tài liệu; MVP/split/benchmark và quyết định người dùng được tách rõ. Các ngày demo/đồ án và ngưỡng phần trăm trong tài liệu 00 là mục tiêu tham chiếu, không tự thành tiêu chí DATA20 được duyệt. Chốt ngưỡng trước khi mở test vẫn là gate.

Đã đọc [yêu cầu QA15](../data20_15/EVIDENCE_REQUIREMENTS.md), kiểm CSV TEST_MATRIX_28 có đúng 28 dòng TC01–TC28 và trạng thái NOT_RUN_QA15 ở bản đầu. QA15 sau đó đã đối chiếu trial counts và ghi rõ thiếu diff/hash chi tiết, restore/rollback chưa chạy. **Nhận ma trận/yêu cầu bằng chứng, chưa nghiệm thu 28 ca.** Số backfill không chứng minh độ phủ ground truth; không đóng G0/G2/G6.

Nguồn D01/split 01 đã đối chiếu trực tiếp cases.csv và HO_SO_NHAP_20261103.md. Đã giao 06 so mức đầy đủ của VN002/Tân Bình/VN001 và 07 rà nguy cơ Dĩ An test đã bị dùng phát triển. Chờ inventory/readiness để chốt Pioneer; không thay split/canonical.

### Review 14 — cổng snapshot/toàn vẹn đang chặn

Đã đọc [REVIEW.md của 14](../data20_14/REVIEW.md) và đối chiếu trực tiếp hai đoạn source P1 (01 chỉ đọc, chưa chạy DB):

| ID | Mức | Tình huống cụ thể | Owner / điều kiện đóng |
|---|---|---|---|
| L10 | P1 | compat20.py protect_snapshot chỉ bảo vệ result/input/project/file khi OLD.result_sha256 khác NULL; có thể UPDATE hash=NULL rồi sửa snapshot ở lượt sau | S20 sửa khóa hash, test từ chối cả 2 bước trên clone; 14 đọc diff, 15 nhận terminal |
| L11 | P1 | analysis20.py lấy catalog tại save và gắn catalog_is_historical_input=True dù không nhận catalog thực dùng tính; kết quả A có thể mang nguồn B | S20 truyền snapshot thực hoặc ghi chưa xác minh; ca catalog A→B trước save, không nhận B là input lịch sử |
| L12 | P2 | ReviewPlan có walls ở gốc nhưng đường dẫn ghi input.plans[0].walls | S20 giữ prefix/index đúng loại request; kiểm path phân giải về raw snapshot |
| L13 | P2 | DELETE/chuyển evidence có thể để measurement.evidence_ids JSONB trỏ nguồn mất/khác analysis | S20 bảo vệ tham chiếu ngược hoặc từ chối giao dịch; test nguồn đã được dùng |
| L14 | P2 | CHECK revision chấp nhận NULL version/size_bytes/role theo ngữ nghĩa SQL | S20 yêu cầu NOT NULL có điều kiện record_type=revision; test từng trường thiếu |

01 đã chuyển cả 5 finding cho S20, không mở quyền ghi source cho phiên khác. Đây là finding review tĩnh, chưa receipt DB tái hiện; **G0/G5 và main migration giữ mở** đến khi có bản sửa/đối chiếu và kiểm phù hợp.

### Split độc lập — tín hiệu cần xác minh

07 báo dấu vết test DWG/cột có nguồn banve1 và tài liệu M01 đã đọc tiên lượng Dĩ An. Vì vậy TEST trong cases.csv chỉ là split đăng ký, chưa chứng minh holdout độc lập. Đã yêu cầu 07 cung cấp path/line/lịch sử sử dụng và đề xuất test thay thế. Không tự đổi split hoặc xóa khỏi mẫu số. L02/L08 giữ mở; không công bố accuracy độc lập của Dĩ An lúc này.


### D09 đã có owner; chỉ tiêu thu thập được làm rõ

S20 đã giao **03 chỉ ghi docs/review/data20_03/**: RULES_INVENTORY.csv, RULE_TEST_GAPS.md, README.md; không src/data/test/DB. L09 đóng ở mức **đã phân công**, chưa đóng chất lượng D09. 03 chỉ tiếp DATA20, các việc CAD/W5 trước vẫn dừng.

Chỉ tiêu do S20 chuyển từ yêu cầu mới của chủ đồ án, tất cả là **mục tiêu chưa hoàn thành**:

| Gói | Chỉ tiêu thu thập/rà soát | Cách nhận |
|---|---|---|
| Hồ sơ/nhãn/đáp án | 5 công trình ACTUAL, 3 BUILD + 2 TEST; 5 bộ nhãn và 5 bộ đáp án đầy đủ | Giữ split cũ/identity, quyền dùng, nguồn và reviewer; chưa có đủ 2 test độc lập |
| Biến thể/kiểm chứng | 20 biến thể từ BUILD; 28 ca hợp đồng | Không đếm biến thể thành ACTUAL/test độc lập; chạy hết không tự là đạt |
| Danh mục/định mức | Rà 98 vật liệu, ưu tiên 15; 5 hệ tường đủ; rà 68 dòng CSV định mức và 15 quan hệ | Đối chiếu 31 DB source riêng, kiểm đơn vị/nguồn/phạm vi/hao hụt |
| Cung ứng | 10 NCC tại 1 địa bàn; 45 báo giá/cặp vật liệu–NCC mục tiêu (15 × 3) | Chứng từ đúng mã/quy cách/đơn vị/lượng/điểm giao/hiệu lực; không dùng 13 cặp SAMPLE để đạt |
| Chi phí/quy tắc | 1 bộ nhân công, 3 phương án vận chuyển, 1 phiên bản ruleset | Giá/hệ số có nguồn, version/hash và điều kiện áp dụng |
| Quan sát giá mở rộng | 360 quan sát = 15 vật liệu × 24 tháng | Là mục tiêu thu thập thêm; không nhân bản 63 BULLETIN, không bảo đảm đủ train hoặc đủ báo giá mua |

S20 báo đang bổ sung bảo toàn GRANT/ACL từ 28 cấu trúc nguồn sang 20 bảng/view/sequence. 01 chưa kiểm implementation hoặc receipt thực thi; G0 bổ sung kiểm quyền trước/sau với cùng tài khoản trên clone, không in DSN/credential. Main DB chưa chuyển.

### Nhận báo cáo 04 ở mức kiểm kê/hợp đồng

01 đã đọc [SUPPLY_READINESS/README của 04](../data20_04/README.md), [SCENARIO_CONTRACT.md](../data20_04/SCENARIO_CONTRACT.md) và kiểm CSV có 98 dòng. Nhận deliverable báo cáo, **chưa đạt D07/D10**: 13 cặp SAMPLE phủ 5 mã, CSV chính chưa có cặp; 63 BULLETIN không là báo giá mua; luồng GK01/XM01/CA02 đề xuất có 0/3 mã có báo giá đủ căn cứ. Hà Nội/W-GK01-110 chỉ là phương án thu thập có điều kiện thiết kế khớp, không thay cấu tạo Pioneer VN002 để chạy mua.

L15 (G5): API có kiểm cùng dự án nhưng req.groups chưa đối chiếu với lượng trong takeoff; scenario optimized ghi requirements=[] dù assignments có lượng; catalog_snapshot có hai dạng. 01 đối chiếu source optimization20.py thấy requirements=[] và method=request.method. L16: chưa lưu đầy đủ effective algorithm/seed/config, notes/n_evaluated, biên nhận chọn scenario và chứng từ giá theo đơn. Đã chuyển S20 sole-writer xem xét; đây là review tĩnh, chưa test tái hiện. Không suy requirements=[] thành nhu cầu bằng 0. 04 đưa 6 ca D10 để QA nhận vào phạm vi khi được phép chạy.


## Chốt vòng kiểm kê và đề xuất release sau nhận báo cáo

**Chọn VN002 làm hồ sơ BUILD mục tiêu hoàn thiện Pioneer.** Đây là quyết định thứ tự làm việc, không chứng nhận đủ cặp/version/quyền/mở CAD hoặc nghiệm thu D01–D04. Hai hash DXF KT/KC tại báo cáo 06 được giữ nguyên; các file nguồn không bị sửa. Test đăng ký Dĩ An giữ nguyên identity/split nhưng tính độc lập nghiêm ngặt không đạt theo exposure ledger; cần thu **hai identity TEST mới** có quyền/đáp án, không đếm alias/biến thể hoặc đổi split âm thầm để đạt 3+2. Nếu giữ cả 4 identity cũ và thu 2 mới, tổng kho là 6; vẫn có thể chọn phạm vi release 5 sau quyết định minh bạch, không coi Dĩ An là holdout chưa xem.

| Deliverable đã đọc | Kiểm nhẹ 01 thực hiện | Kết luận được nhận / gate chưa đạt |
|---|---|---|
| 06 HO_SO_INVENTORY + README + SCHEMA_MAPPING | Đếm 458 dòng; đọc giới hạn magic/hash, UNKNOWN/SYNTHETIC, thiếu version/quyền và so Pioneer | Nhận inventory; không nhận 458 công trình/file độc lập hoặc mở CAD. 28/28 file metadata khớp theo báo cáo06, chưa là QA parser mới |
| 07 readiness/templates/coverage/exposure | Đếm 4 identity và 249 source works VN002; đọc 2 nhóm nháp/4 ứng viên và 5 DEV/244 cách ly | Nhận nhãn nháp có nguồn, không có oracle độc lập đã xác nhận; không cộng toàn249 (có ngoài phần thô) thành mẫu số chính thức |
| 05 gap/README | Đếm 286 dòng báo cáo, 22 VN002; đọc đề xuất C05-01…09 và hash baseline | Nhận gap, chưa nhận hệ số nguồn mới hoặc đủ5tường; đối chiếu DB31/CSV68 theo từng dòng còn thiếu export |
| 04 supply/contract | Đếm 98 dòng; đọc 13 SAMPLE/0 CSV chính, 6 ca D10 và G5 mismatch | Nhận kiểm kê và contract review; chưa có báo giá mua đủ điều kiện |
| 16 price/readiness | Đếm 78 dòng ledger; đọc 63 quan sát lịch sử + 15 gap, cơ sở giá và cổng train | Nhận ledger, không phải 78 giá mới; 1.248 SYNTHETIC và SAMPLE không được dùng thay ACTUAL |
| 14/15/00 | Đọc finding code, matrix28/evidence mapping và kế hoạch | Nhận báo cáo kỹ thuật; chưa đóng nghiệp vụ, benchmark hoặc main migration |

### Lịch và phạm vi release cụ thể đề nghị

Các bước dưới đây là đề xuất có phụ thuộc; **chưa cấp quyền canonical mới hoặc thực hiện import**. Mỗi delta cần hash trước/sau, diff nhỏ, kiểm ảnh hưởng và rollback; một file chỉ một owner ghi.

| Thứ tự | Đường dẫn / ID | Owner đề nghị | Điều kiện mở và bằng chứng đóng |
|---|---|---|---|
| R0a | src/optimat/db/compat20.py, schema20.py, analysis20.py; tests/test_schema20.py | S20 sole writer;14 review/15 evidence | Xử lý L10–L14 (hash khóa, catalog provenance, path, evidence reverse link, revision NULL); regression/focused chỉ theo lease S20, không cấp suite đồng thời |
| R0b | src/optimat/db/migrate20.py và SQL tương thích liên quan | S20 | Bảo toàn ACL/GRANT/view/sequence, đối chiếu đầy đủ; receipt rollback/restore có thực thi trên clone. Main migration cần quyết định riêng |
| R0c | src/optimat/db/optimization20.py và caller optimize trong api/main.py | S20 | Đối chiếu req.groups với takeoff hoặc ghi rõ giả định; requirements/snapshot version và effective config không nói quá nguồn; 6 ca D10/G5 |
| R1a | data/ground_truth/du_toan/incoming_20261103.json, cases.csv và manifest VN002 đề xuất | 06 manifest;07 nhãn;01 chốt từng file trước ghi | Quyền/role/version/lineage và parser mở cặp KT/KC đúng lượt; không sửa split Dĩ An hoặc tự thêm ACTUAL/approval |
| R1b | normalized_20261103/nha_sang_hai_duong_4x15.*; các ID D20-07-VN002-W001…W249 | 07 theo scope công tác được chốt | Tách phần thô/ngoài phạm vi, từng cấu kiện/số đo/giao-trừ có nguồn và reviewer; W007 xung đột không ép tổng. Giữ tiên lượng nguồn, không dùng chính engine làm đáp án |
| R1c | Ledger exposure di_an_banve1/VN003 và manifest 2 TEST mới | 07/15 report,06 intake | Phê duyệt phạm vi công bố test đã phơi lộ và quyền/expected mới; không cần sửa split chỉ để sửa nhãn độc lập |
| R2a | data/rules/dinh_muc_phan_tho.csv, CAN_NEN/30 (C05-08) | 05 sau review nguồn | Xác nhận AK.41120/trang đúng so mã nhóm AK.41100 hiện có; chỉ chuẩn mã khi đúng, không đổi hệ số 0,035 vô căn cứ |
| R2b | data/catalog/materials.csv GN01; wall_systems.csv W-GN01-110/220 (C05-01) | 05 sau kiểm chéo | Chốt gạch cao60/65, đúng quy cách/nguồn trước thay suất643/550 hoặc vữa; không tạo hệ tường55 bằng chia đôi110 |
| R2c | dinh_muc_phan_tho.csv TRAT và material_relations.csv VU02 (C05-03); M100/M250 C05-04 | 05, mỗi file một lượt | 07 tách nền/tường/cột/dầm/trần/thang; nguồn đúng đá/Dmax/xi măng/mác/độ sụt; không lấy Dmax20 cho đá4×6 hoặc áp nguồn tường cho mọi mặt |
| R2d | rule_sets/CSV quy tắc canonical tương ứng inventory03 | 03 đề xuất; S20 giữ SQL/DB | Chờ inventory D09 chỉ rõ từng kind/key/path/delta và ca dương/âm; đóng băng trước TEST, không quy tắc cài đáp án |
| R3 | supplier_materials/price_records/cost export, metadata báo giá có version trong20bảng | 04 nguồn cung,16 giá; S20 DB/glue | Chứng từ đúng SKU/đơn vị/lượng/địa điểm/VAT/cước/hiệu lực/known_at; ưu tiên vật tư thực trong VN002. Hà Nội/hệ GK01 chỉ thu nếu hợp thiết kế, không thay GN01 của hồ sơ để đủ giá |
| R4 | Bộ test độc lập/28ca/manifest release; chưa chỉ định sửa predict/train/models | 15 QA,00 ngưỡng,01 điều phối | 2 holdout có quyền/GT, hash và ngưỡng chốt trước mở; chưa train từ63BULLETIN hoặc360điểm mục tiêu chưa có |

### Quyết định/dữ liệu cần chủ đồ án qua 00

1. Quyền dùng VN002 (nội bộ/huấn luyện/chia sẻ), xác nhận cặp hồ sơ cùng revision và người lập/người kiểm độc lập.
2. Nguồn hai công trình TEST chưa dùng phát triển, quyền truy cập đáp án và lịch sử tiếp cận; thiếu thì không công bố benchmark độc lập.
3. Công tác phần thô/phạm vi và ngưỡng/mẫu số trước test; không tự áp các phần trăm tham chiếu trong kế hoạch khác.
4. Địa bàn/ngày/điểm giao, nhu cầu đã kiểm và chứng từ để nhận báo giá. Hiện chưa đủ để mua/so rẻ nhất hoặc train ACTUAL.
5. Main migration chỉ sau review, hồi quy, phục hồi và ACL đã có bằng chứng; schema20 chốt không thay thế quyết định triển khai.

01 đã gửi packet này cho 00/S20, chưa hỏi lại hoặc tự điền các trường thiếu. Các việc độc lập hiện còn: S20 xử lý review/kiểm theo lease,03 hoàn thiện inventory; các phiên dữ liệu đã hoàn thành kiểm kê có thể chờ quyền/dữ liệu tiếp theo trong đúng thư mục, không tự mở task cũ.

### Hồi quy — bằng chứng mới, không gộp tùy ý

01 đọc tail reports/schema20_remaining.log thấy **734 passed trong212,80s**. Đây là phần còn lại sau lần full dừng439passed/4skip/1mockfail theo S20, không tự cộng thành một terminal full sạch; chờ S20 đối chiếu nodeid/hash/exit và retest sau sửa P1/P2 mới. Không dùng log trước sửa để đóng lỗi review sau đó.

## Checklist chủ đồ án — mục11 đã append, giữ nguyên kế hoạch cũ

Theo yêu cầu mới qua S20, 01 được sole-writer append mục11 vào docs/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md; S20 giữ Word. Đã bổ sung 18 dòng C00–C17: 1 ô đã kiểm **chỉ phần kiểm kê báo cáo**, 17 ô còn mở. C01–C13 ưu tiên gốc đọc bản vẽ/nguồn/đối chứng; C14–C15 vật liệu/phương án ở sau, C16–C17 giá/mô hình ở sau nữa. Không bắt có vật liệu để bóc hình học.

Có ID/ưu tiên, vấn đề gốc, tài liệu có sẵn, THIẾU/CHƯA KIỂM/ĐẠT, việc cần bổ sung, owner, điều kiện đóng và nội dung cần chủ đồ án. Đã đọc C01 cùng cảnh báo bản cũ và hướng dẫn bản sửa, yêu cầu khối lượng/M1, report06/07/15/14; đọc source dxf_reader/dimensions/plans/registry để nêu giới hạn cụ thể. 03 đã gửi summary D09; 01 đối chiếu tên test đơn vị/transform trong source và ghi mục11.4. Ba artifact inventory D09 vẫn chờ03; summary không thay deliverable.

Đã kiểm byte: toàn bộ **20.947 byte đầu** của plan (mục1–10) giữ nguyên SHA256 `fb53e3a8a85a07becba50daf21b989860eef42a28ac19db9f8045c11a9d723bd`. Không thay mục cũ hoặc tự mở quyền CAD/source/runtime. Ưu tiên một phạm vi nhỏ VN002 từ dữ liệu đang có; không giao mua/tìm/tải bộ khác trước khi biết thiếu. Dĩ An giữ split đăng ký và issue phơi lộ, không đổi split. Các mục tiêu5 hồ sơ/45quote/360 quan sát tiếp tục là mục tiêu, chưa ready.

Bước tiếp theo thuộc quyềnS20: nhận checklist, tái sinh Word từ plan mới và render/kiểm theo quy trình; 01 không ghi Word. Việc chạy reader/đo CAD hay sửa canonical cần lease/phạm vi cụ thể sau checklist, không suy từ việc ghi kế hoạch.

## Lượt kiểm nội bộ VN002 và cửa sổ chuyển DB mới được cho phép

Chủ đồ án qua00 đã cho phép dùng cặp KT/KC VN002 hiện có để kiểm nội bộ. 01 đã xác minh nguyên usermessage trong chat00 và giao06 khóa file/path/hash/đơn vị (không bịa revision thiết kế),07 truy đúng một cấu kiện hoặc hàng thống kê có đủ nguồn. Chỉ đọc nhỏ trên FILE; không full CAD/rough/DB/W5/demo. 01 tự hash lại hai DXF: KT719ea17b22b856bb31363fbfc9bf218f312112958e9de4f6638e2ede1f1cf8d6; KC22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c; khớp báo cáo06. Quyền nội bộ đã được mở; không suy quyền train/phân phối.

01 đã tự mở ảnh KC-01-12 trang18 và KC-00 trang3 có sẵn. Ứng viên kiểm nhỏ: bảng thép **bể nước bên phải**, DM-1 (SL2),STT1:Ø12,L2850mm,2thanh/CK,4thanh toàn bộ,11,4m,10,1kg; đơn trọng bảng3 là0,888kg/m. Chờ07 locator từng số và06 pair lock; chưa đóng C01/C06/C10 hoặc da_kiem. Không dùng tổng bểØ12=36,9 đang mâu thuẫn, không nhân SL2 lần nữa. Ảnh lịch sử không thay việc khóa nguồn/ảnh mới đúng file.

Chủ đồ án cũng đã duyệt **S20** chuyển DB chính sang20. Trạng thái hiện tại: **đã duyệt, S20 chuẩn bị/chạy focused latest fixes/ACL; CHƯA có receipt main commit đọc lại để01 công bố đã chuyển**. 01/14/15 không chạy DB/test,06/07 chỉ FILE. Đã đề nghị tạm ngừng mọi API/client ghi trong cửa sổ chuyển;01 chỉ xác nhận không có writer trong phạm vi mình và các chỉ thị đang giao, không bảo đảm client ngoài chat đã dừng. S20 chịu trách nhiệm maintenance/lock,backup/atomic migrate/postcheck và bảo toàn dữ liệu;không reset. Cập nhật thành đã chuyển chỉ khi đọc receipt thật;không lấy clone mới hoặc thiết kế20 làm bằng chứng main.

## Main migration và runtime — biên nhận đã đọc sau commit

01 đã đọc reports/schema20_main_receipt.json: **committed_verified**,databaseoptimat,20bảng vật lý,26analysesđãkhóa,project23còntồn tại;counts24projects/130document_revisions/98materials/2867suppliers/63price_records/work_norms31. ReceiptS20ghi đối chiếu28cấu trúc trongtransaction,roleoptimatđọc7viewlegacy/reportingđạt.Đã đọcfinal_integrity16pass3,11s;14đãCLOSED_STATIC5findinggốcvàguardINSERT/NEWparentmới theohashcompat20c4f08e102d39153e06dc45340a0f025bce9945b1a2da60e2300d6f74fa562f40. Không coi đây là restoreexecution hoặc readeraccuracy.

S20yêucầu01quiesceđúng6PIDAPI8001/8002/8765.01đốichiếuCIMvenvlauncher/childparentrồidừng,verified0PID/0listener;khôngdừngPythonkhác. Saucommittedreceipt+chỉthịrestart,S20chỉrõcwdrepo,.envmặcđịnhkhôngoverrideDSN;01đãrestartHidden:

| Port | Launcher / listener | OpenAPI | Health/source | Danh mục đọc được |
|---|---|---|---|---|
| 8001 |2304/14432 |200,58paths |200,postgresql |22hệ tường,10họ,4xe |
| 8002 |45120/33012 |200,58paths |200,postgresql |22hệ tường,10họ,4xe |
| 8765 |39472/42556 |200,58paths |200,postgresql |22hệ tường,10họ,4xe |

01 đọcCatalog.load():khi cóDATABASE_URLđọcfrom_db,khôngfallbackCSVởnhánhnày;GETwall-materials/referencequaSQL/viewthànhcông.KhôngPOST/analysis/optimize/AIhoặctestghiDB. [Quiesce receipt](runtime_schema20/quiesce_receipt.json),[restart](runtime_schema20/restart_receipt.json),[GETsmoke](runtime_schema20/read_only_smoke.json) đãcopyvàothưmụcbáocáoriêng,khôngenv/DSN/credential. Runtimeđãkhôiphục;cửasổquiesceđãbáoS20/00,nhưngW5/demo/AIvẫndừngtheophạmviuserchưa cho tiếp. RESTOREexecution/benchmark/ngườikiểmnguồnvẫnlàgateriêngchưađóng.

## VN002 — nhận kiểm nhỏ, không nghiệm thu cả cấu kiện

06PAIR_LOCK.md/jsonđãvề,01đọcvàtựđốichiếubyte/header:KTmm,KCchưakhaibáo;revisionthiếtkếNULL,khóacặpứngviêntheomanifestkhôngfakeversion. 07ONE_ELEMENT_TRACE.md/json+2ảnhđãvề;01tựmởpixelảnhvàtínhDecimaltừATTRIB. [Biên bản01](VN002_ONE_ROW_REVIEW.md) chốt **một hàngDM1#1bểNƯỚC** theoKC01-12p18,4×2,85×0,888=10,1232kg→10,1kg. Tầng/trục/2dầmvậtlývẫnNULL,chiềudài theo bảngchưakiểmđộclậptim/uốn/cover,khôngduyệttổngbểhoặcda_kiem. Quyềnnộibộđượcuserduyệt;train/phânphốichưasuyra. Đãgửi00ảnh/locator/giớihạn;khôngchạylạirough/full/CADbatch.


## Ràng buộc schema và lượt truy hai DM-1 bể nước

Chủ đồ án vừa chốt tại00: **giải quyết vấn đề gốc, giữ đúng20bảng DB; không tự thêm bảng vật lý**. Nếu thật sự cần thêm, owner phải trình lý do, phương án trong20bảng và ảnh hưởng, rồi **chờ chủ đồ án duyệt trước**. Đề nghị kỹ thuật hoặc lời giao phiên khác không thay quyền duyệt này.01 đã chuyển nguyên ràng buộc tớiS20 và03/05/06/07/16/15/04/14/02/17/12; các scope đang dừng không tự mở lại.01 chỉ ghiBOARD, không sửa schema/plan/Word trong lượt này.

Lượt mới được duyệt:06/07 chỉ đọc FILEVN002 để tìm hai vị trí DM-1 của **bể nước**, không bể phốt, và kiểm khung tên KT/KC.01 đã tự mở pixel trang16KC01-10(bể phốt, loại trừ),trang17KC01-11(bể nước),ảnh mặt bằng/ảnh ngữ cảnh mới của07. Trên mặt bằng đáy trang17 có hai chữDM-1 vàleader trực tiếp vào cạnh dài trái/phải; không chỉ dựaSL2.07 đã lưuhandleTEXT1173211/1173213,LEADER1173210/1173212 vàxy trongTWO_DM1_WATER_TRACE.json. Vị tríA/B là tên kiểm cục bộ, không phải trục nhà.

01 cũng đã tự mở ảnh00 VN002_KC_MAT_BANG_TUONG_MONG.png (trang11KC01-05):có chữBỂ NƯỚC trongô1–2/A–B,ghi2500×2000và890tới trục2,thấy số390gầnmépdưới.Đã yêu cầu07 kiểm độc lập endpointsDIM390 và liên kết sang hìnhchi tiết; không gắn trái/phải p17 thành phía trụcA/B hoặc1/2 nếu chưa có mốc định hướng. Tuyến1–1/2–2 trênchi tiết là mặt cắt, không là trục nhà.

Khung tênPDFdo00render đã được01mởpixel:VN002_KT01_KHUNG_TEN.png vàVN002_KC0111_KHUNG_TEN.png trongdata20_00;cùng chủAnhSang/HảiDương,Nhàởgiađình,Bảnvẽsơbộ,Hoànthành10/2021;khungđiềuchỉnhcóhàngnhưngtrống.Đã yêu cầu06tích hợp vớiDXFtrace,không coi cùng ngày là cùngrevision/lầnpháthành. Chưa đóng gate phiên bản thiết kế hoặc nghiệm thu hai dầm vật lý trên toàn nhà.

## Cập nhật 04/11/2026 21:19 — module Quy tắc bóc tách staging

- Phạm vi: 17 sole writer `frontend/src/app/(admin)/quy-tac/page.tsx` và `rules.tsx`; 03 đối chiếu 25 quy tắc/consumer; 15 review độc lập. Không thêm bảng, không ghi DB, không thay runtime chính 3001.
- Hai P1 và các P2 đã đóng ở mức review tĩnh. Hash cuối page `27DE75CB469E6EF33A9FFBF1AC75252E799F7B41E1AA48929525F539D0D662B3`, rules `F543150C1D2D076C4BA702B54B68F630A7E6D0C2F80944F1AD6E2BBAEFB0A352`.
- 01 build snapshot frontend riêng: 92 tệp nguồn ổn định; build `XAER9r8guzcs7heKavA8s`, stage `http://127.0.0.1:3002/quy-tac`, launcher PID 25484. Build/API proxy 8001 và HTTP route 200 đạt. Chỉ nghiệm thu route quy tắc, không coi các module khác trong snapshot đã đạt.
- Chrome thật đăng nhập Trần Nga/admin: thấy 10 nhóm; mở COT và Gộp để kiểm nội dung; liên kết định mức mở `rough_norms` 31/31 dòng. Không bấm Sửa/Xóa/Ghi. Tab 1498892249 giữ mở; chụp màn hình trong lịch sử CUA.
- Bằng chứng tại `C:/Users/Admin/.codex/visualizations/2026/11/03/01a1a0af-a01f-7af3-bf7d-34ef9a0c5576/rules-demo-stage/`: `build.log`, `source_manifest.json`, `stage_receipt.json`, `http_receipt.json`, `api_proxy_check.json`, `browser_receipt.json`.
- Đạt kỹ thuật có giới hạn: tra cứu thuật toán và điều hướng bảng định mức trên staging. Chưa nghiệm thu sửa định mức rồi tính lại dự án; chưa có trace rule/version/nguồn thiết kế/workkey riêng. Main 3001 chưa triển khai bản này.
- C2 độc lập: 03 129 focused passed/3 deselected; 15 19 synthetic passed, source stable. Reader CAD VN002 vẫn CHƯA ĐẠT; không coi phép tính đủ đầu vào là đã nhận đúng cột 4/A từ bản vẽ. Source core đang freeze chờ dữ kiện trục/section/region.
## Cập nhật 04/11/2026 23:30 — phát hành quy tắc, candidate C2 và P0 xác nhận

- Main 3001 đã chuyển riêng module `/quy-tac`: build `4jlXI5sLtByy4nUnvUq92`, PID 712; Chrome Trần Nga/admin kiểm thấy 10 nhóm và nội dung COT mới. Nền 78 TS/JS khôi phục từ source map của build đang chạy, chỉ ghép hai tệp rule đã review; CSS/assets hiện có được giữ. Rollback: visualization/rules-main-promote/rollback.ps1. Ảnh thật `rules-main-promote/rules-main.jpg`.
- Core reader active `review15_v2`, helper `6bb3c47a1a2275c05e264e91afc40968fa01670371c8a237df65ca5aed61d6e9`. QA15 đóng 3 finding tĩnh về heading/nguồn trùng/cặp DIM. Owner 151 focused passed/3 HTTP deselected, actual 24 đoạn; không gọi đây là full suite hoặc accuracy toàn dự án.
- Candidate backend riêng 8002 từ snapshot 87 Python files; API 8001 giữ nguyên. Frozen API ecf631..., rebar canonical 76f09... đã có 144 focused pass; models/materials rowIndex của04 giữ đúng cùng snapshot. Không tích hợp nhánh tài liệu mới đang tạm dừng.
- Public API candidate thực: KC hash22cda9..., structural POST200/80,7s/24instances/targetCount1; C-2@4/A 220×220mm,3150→6750mm, khác4/B. Rough POST200/52works: COT w:22 gross raw0.17424m³/netNULL, CP w:50 NULL; MaterialUse riêng rowIndex22/50. Không project ID, takeoff_idNULL/không save; chưa dự án KT/KC đầy đủ hoặc revision E2E. ID trong API dùng tempfile khác adapter: chỉ dùng work key cùng snapshot, không bind xuyên lần chạy.
- Bằng chứng candidate dưới `C:/Users/Admin/.codex/visualizations/2026/11/03/01a1a0af-a01f-7af3-bf7d-34ef9a0c5576/c2-backend-candidate/`: source_manifest, frozen_components, runtime_receipt, structural.response/receipt, rough.request/response/receipt. UI minimal 4 tệp overlay02 đã build `H6w7Rhgb_8Aew79ERRLSc`, chưa promote vì ưu tiên P0 dưới.
- Kiểm Chrome QA25 hiện chưa có bản vẽ, đã lưu `qa25_before.jpg` và DOM. User đã bật file URL permission nhưng setFiles vẫn bị tiện ích từ chối; kiểm chrome://extensions bị URL policy chặn nên không dùng workaround. Chờ thao tác operator đúng nguồn; không đánh dấu E2E đạt.
- P0 user bấm xác nhận: live tab1498892249 ở3002/do-boc, Dự án2/file tk nguen binh.dwg,11hình,scope chưa chọn; modal kẹt Đang gửi. Đối chiếu chính source build3002: sendConfirm return trước request khi scope thiếu nhưng Dialog busy không reset; log8001 không có POSTconfirm. Đã lưu `confirm-stuck.jpg`/DOM.02 sole writer Review/Dialogs+test, chuẩn bị overlay riêng3002 và3001. Root không reload user, không bấm gửi lại/không tự phân loại11hình hoặc chọn số. Chờ patchP0 trước đổi runtime.
- User tạm dừng riêng phân tích Office/PDF/dự toán và AI tài liệu để làm sau; giữ mã/bằng chứng06/07/17, không deploy vào candidate. C2 tiếp tục. Auto-review chặn root nhắn chat12 vì phạm vi ủy quyền chưa có chat12; không vòng qua kênh khác.
## Cập nhật 05/11/2026 00:03 — P0 xác nhận đã lên hai cổng và kiểm live

- 3002: build `XLGfOY4MIuGt8ZUp-wppq`, PID29104, proxy8001 giữ nguyên. 3001: build `LKTDjEOitNSiJBETPtyW8`, PID11648, proxy8002 C2snapshot. Hai build/HTTP200; source snapshot/base và rollback trong các receipt dưới visualization `p0-3002-release-r2`, `c2-p0-3001-release-r2`. Không đưa nhánh Office/AI đang dừng vào bản phát hành.
- P0 gốc: guard scope thoát trước network nhưng Dialog busy giữ vô hạn. Bản mới dẫn đúng hình thiếu scope/height, một POST/lần, cached server success chỉ thử lưu local/chuyển bước, không POST lại. QA15 đóng P2 cached/recovery đầy đủ project UID/numeric ID/drawing/revision/input context; owner harness gồm sửa tầng khác/quay về tầng đã xác nhận và quota/stale/HTTP lỗi. Không full/DB test.
- User xác nhận đã giữ chỉnh sửa và Ctrl+Shift+R nhưng tab bridge vẫn giữ bundle cũ/modal RAM; 01 nạp lại đúng tab sau xác nhận đó. Quan sát live: module mới khớp HTTP; Dự án2/file `tk nguen binh.dwg`, hình Lầu1 giữ3,35m/23tường/15lỗ/241,36m²; không còn modal Đang gửi. Nút Phân loại hình6/11 chỉ focus SELECT phạm vi, giữ giá trị chưa chọn, không gửi confirm. Vẫn11/11 hình chưa phân loại: không tự chọn count/reference hoặc xác nhận thay user. Happy path server lưu bản vẽ này chưa nghiệm thu, chỉ harness kỹ thuật.
- Ảnh live `p0-3002-release-r2/verified-live.jpg`, DOM và `browser_receipt.json`; đã gửi00/user trạng thái cụ thể. Handoff Chrome tab1498892249 ở3002/do-boc. Bản vẽ gốc/dữ liệu người dùng không bị tải lại từ file.
- QA25 được kiểm fresh trên3001 sau promote, chọn lại đúng QA VN002 thay QA24(sample_floor): chưa có bản vẽ và nút analysis disabled. Ảnh `c2-p0-3001-release-r2/qa25-current.jpg`/DOM đã gửi00; chờ operator hai file KT/KC, không ảnh C2/thang E2E giả. C2publicAPI+component integration vẫn đạt có giới hạn như mục trước.
- Nhánh thang T1→T2:03 solewriter stairs.py + status._inputs nhánh stair_components + takeoff gate planHNone + test hẹp;06 API provenance/mapper riêng;17 StairTrace và hunk PlanParams/roughRequest/Review callback scoped/WorkReview sau02 nhả. Không sửa P0stamp/Dialogs/C2helper6bb3.07 giữ nguồnKCp37/KTp19–20: bản nghiêng120 vuông góc,bậc xây gạch,chiếu tới150 tách riêng; chiều cao/run/gối từng vế còn thiếu thìNULL. ThépT1 tổng in203kg khác tính lại203,15482kg, chưa gán từng vế hoặc mua. Chưa deploy nhánh thang mới.
- 04 grade-evidence và05 TK2 đang staging riêng, chưa ghép runtime. Claim M250/B20 có nguồn nhưng bảng/vùng định vị trước, không gọi automatic instance binding. Không tự chọn supply/giá/hao hụt.
- Chủ đồ án đã trực tiếp cấp đúng một thông báo tới chat12 sau auto-review từ chối trước đó;01 đã gửi thành công thông báo tạm dừng AI tài liệu. Phần Office/PDF/DOCX extraction feature vẫn paused theo user; đọc nguồn bản vẽ cho C2/thang vẫn được phép.
## Cập nhật 05/11/2026 — hai lỗi đang chặn demo sau xác nhận

- Đọc trực tiếp Chrome 3002: Dự án 2, `tk nguen binh.dwg`; user đang sửa Lầu 2, 17 tường/12 lỗ, có N1–N5 thêm tay. Không reload, không xác nhận số thay user, không đọc lại/reupload hồ sơ Tân Bình. Đã lưu ảnh hiện trạng tại visualization/current-draft-3002.jpg.
- P0 width-null: rough nhận w=null nhưng DTO cũ yêu cầu float. 06 sole writer review.py/walls.py/secondary.py/checks.py + test riêng; patch dựa immutable C2 backend, giữ ID/parent/keep và nhóm thiếu. Confirm partial trả complete=false, pending_openings/pending_groups, tổng toàn plan NULL, known subtotal riêng. QA15 focused 7 pass ban đầu, chưa đóng OP06 frontend/OP07 optimizer-export. 01 phát hiện lanh tô bị chặn dư khi chỉ thiếu chiều cao cửa; 06 đang sửa theo phụ thuộc rộng + gối/cao lanh tô. Không promote patch cũ.
- 02 sole writer Review/Dialogs/model: serializer giữ lỗ thiếu, formatter full path, partial confirm/reopen/tổng NULL; ưu tiên trước checkbox tầng. Bộ chọn tầng ở bước3 và bước2 là scope tiếp theo, không auto phân loại hình ngoài lựa chọn. Cần giữ complete/pending đến consumer, không trình known groups thành tổng toàn mặt bằng.
- Mất nét: 03 đã tái hiện tổng hợp ARC/TEXT/INSERT ngoài segment bbox; 17 bổ sung fallback arcs/texts/hatch và overview origin. 17 đã freeze hunk viewer origin, chuyển sole writer viewer/bbox/crop cho03. Contract thêm display_bbox trong hệ SVG Y xuống, giữ legacy world origin/analysis bbox; whole CAD không crop theo segment-only, single plan vẫn giới hạn. 02 giữ3 hunk fit trong Review,17 chỉ Board/ReadPreview; không đổi nhận dạng để sửa hiển thị.
- 01 tạo opening-backend-candidate từ đúng87 file có hash của c2-backend-candidate, chưa áp hotfix/chưa chạy server. Runtime3001/3002 và API8001/8002 giữ nguyên chờ QA. Không kéo nhánh Office/AI đang dừng, không ghép thang vào width hotfix.
- Thang03 SOURCEFREEZE:239 focused passed/3 deselected, chưa runtime/DB/E2E. 00 đang sửa lỗi trùng tên móng riêng foundations.py, không trùng scope các owner trên. Kết quả kỹ thuật và nghiệm thu nghiệp vụ tiếp tục tách riêng; không tự nhận QS hoặc da_kiem.

## Cập nhật 05/11/2026 — gói width v3 đã QA, runtime giữ nguyên

- Backend width source freeze bốn tệp: QA15 36 focused passed, sửa dependency lanh tô chỉ cần rộng và thông số lanh tô; orphan chỉ làm mặt bằng tương ứng chờ. API ứng viên 8003 listener10924/launcher35428 chạy immutable C2+width, không Office/thang. Synthetic HTTP confirm/rough/optimizer export đều200, no project_id/takeoff_idNULL; affectedXAYNULL, nhóm độc lập1.1; totals.completefalse, optimizerstatusD+missingID. Bằng chứng visualization/opening-backend-candidate/http_receipt.json, requests/responses/script/source_manifest87file.
- Frontend P0 v3 manifest5c1d7dc4268dbeb6852840d80af0447602b75b3a3cdfd43db63cb294650a352e: 7tệp mỗi nền, QA15 6harness/14hash stable; orphanallgroups/CSVblank, linkedonlygroup, partialreopen/stamps/quota/consumer scope đạt fixture. Hai candidate opening-3001/3002 buildP0 và build bổ sung worklist+toolbar đều đạt; CHƯA promote3001/3002, source mới đang ghép tiếp theo manifest, không gọi build cũ là đã có delta mới.
- WorkList incremental3file manifest0a3b0f3f7bbc5f3ee356d4e303cd9eebfbf5dde3dd75ca30c7603b1776954e80 đã ghép. BrowserQA15 trên clone3004 buildvUTEZTneoAakH8Pr47sfm/PID18104:5states/keyboard/desktop390mobile đạt dữliệutổnghợp; khôngprojectE2E. Label-onlydelta component3841e44c03b88d57342d154d4038d0dc9f7afb8f44d25258da13309a1b23d60c QAstatic/harness đạt, chưaghép/build. Danhsách là dấuhiệu nhận diện, khôngresult.works/khốilượngđãchốt.
- Toolbar-onlypatch17 F1CC9677... đãghép candidate; browser17 desktop1440/mobile390 nooverflow, modes/fit/zoom/labels/EnterSpace đạtSYN,4ảnh reports/cad_fallback_ui/toolbar-*.png. CloneQA hookuseWallClasses shim đượcghi rõ, khôngđưarouteQA/shimvàorelease. ExcelUI3file+2consumerdelta giữriêngchưaQA/runtime, khônglẫnvàotoolbar.
- Live3002/API8001/PID29104/34752 giữ nguyên. Từngquan sát lượtKC Sang preview69423/485955 stage recognizing;CPU8001tăng1280.875→1317.984375, RAM908554240, no consoleerrors/tracebacktail. Đây số nét sampled không%progress. Sauđó usertựchuyển /du-an-cua-toi, Dựán2chỉ2hồsơTânBình; khôngsuyKCstreamcomplete/cancel. 01khôngreload/hủy/reupload/đổirole hayxácnhận số. Chưa chứngminh snapshotkhôiphụcđủN1–N5; userready/checkpointlàgate trướcactive-tabreload.
- Bbox03 đang sinh narrowpatch theo exact opening-backend-candidate base, cósignals4emptyplans+renderpartialwarning.17/02 nhận composefrontenddelta trên width+worklist+toolbarbase, khôngđèpartialconfirm. Candidate8003chưa cóbbox/signalsmới, khôngclaimactualKCworklistđạt. Thang239tests vẫnfrozenriêng.
- Chủđồán qua00ưu tiên đầu vào:00solewriterProjectFilesPanel.tsx vàread-progress.tsNDJSON,structural.py/_clusters/foundations.py;06/03ràreadonlycontractKCđộclập/file-tờ/sectionlinks,07đốichứng nguồnVN002,15criteria/QA. ChặnchỉKCtheoexistingprojectcontract vànêuvai trò/phạmvi/thiếu trướcStart; khôngyêucầuup lại tệpđãlưu, khôngmởOffice/AIpaused, khôngthêmbảngDB.00benchmark_clusters14.489s→.142s cùng4cụm chỉlàthời gianmộtbước, khôngtoànlượt.

## Cập nhật 05/11/2026 — kiểm khôi phục N1–N5 và gate bản nháp

- Theo chỉ thị chỉ đọc của chủ đồ án qua00,01 dùng giao dịch READ ONLY/timeout8s/rollback, SELECT đúng databaseoptimat/project26/filetk nguen binh.dwg, không restore hay ghi DB. Có10bản xác nhận27–36. Bản27/Lầu2 lúc00:02:41 giữ N1–N4 manual/keeptrue/900×2200mm; N1–N3 cùngW11,N4W14; hình học tường cha còn nhưng không có x/y cửa. Không thấyN5 trong10bản. Bản27chỉ7openings vìserializercũlọc4auto thiếu rộng, khácDOM12openings(7auto+N1–N5). N5quan sátDOM900×2200,parentW2chỉlàbằngchứngmàn hình, khôngsnapshotkhôiphụcđủ.
- Bản nháp hiện mở lại trong tab kiểm tra riêng3002 làKC Sang/4vùnglanhtô/0tườnglỗ/scopeunset. Tab kiểm tra đã đóng; tabuser khôngreload. Chrome khôngcótab3002/do-bockhácgiữRAMcũ. Sourceprojects.ts archivekhiswitchProject, Reviewđổifilekhôngarchive;UIẩn historytrùngprojecthiệnmở. ChưađọcđượcarchivecũquaUI, khôngkếtluậnN5mấtvĩnhviễn. Khôngtruy storageẩn/ReactRAM/chromehistory hoặcđọc lạiTânBình.
- Biên nhận ownvis/saved_manual_openings_project26.json và MANUAL_OPENINGS_RECOVERY_REVIEW.md. Script đãrollbackvàghifiletrướckhigặplỗiUnicodeconsole;khôngphảilỗiDB. KhôngtựxácnhậnbaN1–N3làba lỗvậtlýkhácnhaukhingaycùngparentW11dài1,6m/chưatọađộ.
- Userqua00giaopatchlưu/mởRIÊNG:06DTOReviewOpeninggiữx/yfiniteoptional/nullkhác0,02serializer+snapshottheoproject/drawing/revisiontrướcđổifile+previewarchivechỉđọc. Khôngthêmbảng/khôngupdateproject26/khôngtựsuyvịtríbảncũ;15criteriaqueuedchờcontract/freeze. Cầncheckpointbềnvữngtrướcreloaduser.
- Widthfindingmớiđãđóngbackendfocused:openingparentnonmasonrykeptkhônglàorphan,khôngchặnmasongroups;outside_masonry_openingsgiữID/null;parentmissing/removedpendingall.06incrementalreviewtargetc106399...22pass;15independent22pass7,31s,baseunchanged. Patchnewlinekhôngbyte-repro;rootgraft exactreviewedbytes+SHA, khônggọiapplyoutputđạt. Frontend02đanghợpđồng3states riêng;API8003/8004vẫngiữfreezeold,khôngđổisourcerunning.
- Bbox03QA15independent16pass11,04s;API8004displaycandidate(listener13840/launcher40272)actualHTTPsyntheticREF5000:paths2→3/displaybbox[0,-4150,5450,1000],legacywall/opening/bbox/size/originunchanged. Receiptownvis/display-backend-candidate/http_display_receipt.json. KhôngactualVN002/DBsave. acceptance-backend-candidateđãcopy87source+reviewnonmasonry,noserver.
- INPUTroles02rebasedmanifestfa9d7f...2file/base,15PASS4harness/twobases,IN01/02/06partial,IN04/05notrun;khôngactualmulti-upload. Rootghép exactoverlaybytes/verifybase-targetSHAđểtránhCRLFpatchkháchash. CADfrontend4filecompose02/17đãghépcandidate(theopatchon_width_worklist_toolbar +cad_review_bbox_opening), labelcomponent3841đãghép. Cácthayđổisource mới CHƯArebuild;source_manifest cũ cầnregenerate;khôngpromotetrướckhibuild/QAcuối.
- Live3001PID11648/API8002và3002PID29104/API8001giữnguyên;3003đãdừng;3004QAclonePID18104giữfixturetoolbar/worklistcũ. ExcelUI/checkbox/thangvẫngóiriêngchưađưa vào release mới. DIM01–10queuedvới00foundationpostimagebf4ee4...,khôngcoilàfreezeintegrated/khôngtestmớitrướclượt.
