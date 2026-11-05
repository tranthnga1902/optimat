# D08 — Độ sẵn sàng dữ liệu giá theo schema 20 bảng

Ngày rà: 04/11/2026. Phiên 16 chỉ ghi hai báo cáo trong `docs/review/data20_16/`. Đây là nhiệm vụ DATA20 mới; các việc W5/demo/AI/browser cũ tiếp tục tạm dừng. Không kết nối DB, đọc backup private, chạy migration/import, train, test, build hoặc gọi AI/web mới. Mã nguồn do các owner khác giữ quyền ghi; các mô tả dưới đây là quan sát khi đọc, không phải freeze toàn checkout.

## Kết luận

**CHƯA SẴN SÀNG huấn luyện/nghiệm thu mô hình giá ACTUAL. Chưa chứng minh có báo giá mua áp dụng đúng đơn trong bộ chứng từ được rà.** Đổi sang 20 bảng không bổ sung quan sát hoặc nâng mức xác minh nguồn.

Kế hoạch DATA20 ghi 63 quan sát trước chuyển đổi. `07_APPLIED.md` và receipt lưu dấu vết 59 quan sát công bố cũ + 4 quan sát xi măng lịch sử, không phải 63 báo giá mua mới. Lượt này không xác nhận số dòng/trạng thái database hiện tại hoặc việc main DB đã chuyển. Thử chuyển bản sao và main DB là việc riêng của root; không suy từ source hoặc biên nhận cũ.

Đầu ra đi kèm: `PRICE_DATA_GAPS.csv` là **ledger khoảng trống**, không phải CSV giá được duyệt để nhập DB/train. Grain: 59 bản ghi CSV được mapping cũ chọn + 4 dòng PDF trong gói07 + các vấn đề cấp bộ nguồn/vật liệu/schema/giao thức. Không cộng số dòng ledger thành số quan sát giá, số nguồn độc lập hoặc tỷ lệ hoàn thành.

## 1. Dấu vết và phạm vi dữ liệu

| Nguồn đã đọc | Quan sát | Cách dùng hiện tại |
|---|---|---|
| `data/cong_bo_gia/02.01_2026_CBGVL-SXD.csv` | 6.974 bản ghi trích xuất; 59 dòng được gắn mã ứng viên cho 26 mã, 21 tên nhà cung cấp phân biệt theo chuỗi | Tra tệp trích xuất có chỉ dẫn, chờ PDF gốc; mapping và điều kiện không tự thành đã xác minh |
| `reports/demo_0511/06_demo_actual.manifest.json`, `07_APPLIED.md` | Gói cũ giữ Hà Nội, ACTUAL/BULLETIN và ngày lưu 20/06/2026 từ lần nhập trước; không kiểm độc lập hiệu lực nguồn trong lượt này | Giữ nhãn đã được báo cáo và phân biệt với trường được xác minh; không tự gán ngày ký/lưu thành ngày hiệu lực hoặc ngày biết thông tin |
| `reports/demo_0511/cement_historical_proposed.json`, `07_cement_review.md`, PDF/ảnh đã kiểm ở lượt trước, receipt đầu | 4 biến thể XM01/XM02 của Vicem Tam Điệp, bao KPK50kg, TCVN6260:2020, Hà Nội, VND/tấn, giá đãVAT; ngày văn bản17/03/2026 | Giá công bố lịch sử; không phải cam kết giá mua hiện hành, không gom bốn biến thể thành cùng SKU |
| `data/sample/prices_sample.csv` | 1.248 dòng, toàn bộ SYNTHETIC, 11/2024–10/2026, `Ha Noi`, AAC01/AAC03/GK02/GK03/GN01 | Chỉ minh họa/kiểm mã; không chuyển ACTUAL, không dùng đánh giá đồ án thật |
| `data/catalog/supplier_materials.csv`, `vehicles.csv`, `labor_rates.csv` | Mỗi tệp chỉ có header, 0 dòng dữ liệu | CSV vận hành cục bộ chưa chứng minh báo giá/xe/nhân công thực. Không suy DB trống từ CSV |
| `data/sample/catalog/` | 13 cặp giá, 4 xe, 1 đơn giá nhân công; SAMPLE theo tệp và README | Giữ ngoài tập phát hành ACTUAL; không dùng làm dữ liệu giao hàng/nhân công thật |
| `models/material_price_metrics.json` | Chỉ số ghi rõ SYNTHETIC, chia832/208/208, test07–10/2026 | Không phải metrics ACTUAL; không huấn luyện hoặc tạo metrics mới trong D08 |

26 mã ứng viên trong CSV cũ: AAC01, AAC02, AAC03, CA01, CA03, CT02, CT04, CT05, CT06, DA01, DA02, DA03, DA04, GK01, MA02, PG02, TH01, TH02, TH03, TH05, TH07, TH08, VU03, XM01, XM02, XM03. Không có GN01/GN03/VU02/CA02 hoặc bê tông thương phẩm BT01–BT07 trong gói 59 dòng. Không có trong gói không đồng nghĩa không tồn tại trên thị trường hay ở nơi khác chưa được rà.

Không gọi gói cũ là “tháng01” từ số văn bản `02.01/2026/CBGVL-SXD`. Không nhân quantity1 trong importer thành quan sát lượng mua thực. Cột `observed_date` của ledger chỉ giữ ngày ghi trong artifact; `verified_effective_date`, `verified_known_at`, `verified_quantity` tiếp tục trống nếu không có bằng chứng. Nhãn ACTUAL được báo cáo trong manifest/receipt được giữ ở `declared_data_kind`, không đồng nghĩa nội dung nào cũng đã xác minh.

CSV chứa điều kiện có thể do parser thêm hoặc kế thừa ô gộp. Ví dụ điều kiện cát/đá tại bãi được mã parser gán theo văn bản chung. Vì chưa đối chiếu PDF gốc, giữ nguyên văn trong `raw_terms` nhưng không nâng thành VAT/cước đã xác minh. “Cát vàng” chung chưa chứng minh đúng CA01 hạt to hoặc CA02 xây trát. Các mã thép/AAC/vữa tương tự cần đối chiếu quy cách, không chỉ regex.

## 2. Ánh xạ D08 vào đúng 20 bảng

| Thành phần | Nơi lưu vật lý | Giới hạn/việc cần owner chốt |
|---|---|---|
| Quan sát giá theo ngày/nguồn | `price_records` giữ nguyên trong `schema20.KEPT`, cột từ `models.PriceRecord` | `material_id`, supplier tùy chọn cho BULLETIN, date/province/quantity/unit/unit_price, VAT/cước/source/data_kind/price_level. Supplier trống không được tạo ID giả; trainer hiện drop các dòng thiếu supplier |
| Cung ứng và giá hiện hành | `suppliers`, `supplier_materials` | D07 xác minh nhà bán/địa điểm/SKU/leadtime và điều kiện mua; UNIQUE cặp supplier–material chưa lưu riêng nhiều SKU/bậc lượng/phiên bản báo giá |
| Xe và nhân công | `cost_parameters(kind, record_key, payload)`; `vehicles`, `labor_rates` là view tương thích | Giữ nguồn, địa bàn, ngày/đơn vị/cơ sở chi phí của payload; không đếm view thành bảng thứ21/22, không biến SAMPLE thành ACTUAL |
| Metadata mô hình | `rule_sets`, kind=`model_versions`; view tương thích cùng tên | Chỉ đăng ký metadata khi được release; artifact mô hình ngoài DB, hash/phiên bản phải gắn đúng tập dữ liệu |
| Giá thực dùng trong phương án/lần chạy | `material_scenarios.catalog_snapshot`, `optimization_runs` theo D10 | Lưu đúng đầu vào từng revision; không gán danh mục tại thời điểm chuyển đổi thành danh mục đã dùng trong quá khứ |

Không có cột vật lý rõ ràng trong `PriceRecord` hiện được đọc cho currency, known_at, ngày hiệu lực bắt đầu/kết thúc, SKU/bậc lượng và dấu vết kiểm độc lập. `SupplierMaterial` giữ note nhưng không có `valid_until` dạng cột; `PriceOffer` có optional valid_until không tự chứng minh đường lưu trữ bền vững. Cần root/schema20 và owner04 chốt cách bảo toàn metadata, có thể bằng artifact sidecar có phiên bản và tham chiếu nguồn trong cấu trúc hiện hành. Đây là gap bàn giao, **không đề nghị phiên16 thêm bảng/cột hoặc tự quyết payload mới**. Khi chưa có nơi lưu/đọc tương ứng thì chưa công bố pipeline đã phủ những trường đó.

## 3. Tra giá, giá mua và dự đoán là ba khả năng riêng

- **Chỉ tra tham khảo:** giá công bố có nguồn/locator nhưng chưa có điều kiện mua, chưa rõ ngày biết/hiệu lực/địa bàn hoặc mapping. Hiện đúng với gói63 ở mức chứng từ đã rà. Với 59 dòng, ghi thêm chưa đối chiếu PDF; không dùng raw CSV như xác minh độc lập.
- **Có thể xét mua:** phải có báo giá DEALER/QUOTE thực, đúng SKU/quy cách/đơn vị/lượng/nơi giao/ngày đặt và hiệu lực hoặc xác nhận nhà bán; VAT/giao/phí và nguồn truy được. Một `eligible=True` trong selector không đủ: cần không phải reference và còn đối chiếu chứng từ với đơn. Maps chỉ hỗ trợ tìm vị trí.
- **Có thể đánh giá dự đoán:** phải có tập ACTUAL đúng mục tiêu, nhiều kỳ thực sự độc lập, ngày biết thông tin, phân tầng cơ sở giá và giao thức chia được duyệt. Có một báo giá mua không tự đủ train; có đủ lịch sử BULLETIN cũng không tự dự đoán được giá mua giao công trình.

Nếu thiếu dữ liệu huấn luyện, dùng tra nguồn gần nhất **đã biết trước ngày cần tra và đúng cơ sở**, ghi ngày/địa bàn/đơn vị/VAT/giao và tuổi giá. Không có giá tương thích thì trả thiếu; không lấy giá rẻ nhất khác tỉnh/khác VAT, không kéo dài hiệu lực và không lấy dự đoán lấp giá mua.

Kế hoạch mới đặt mục tiêu khởi đầu một địa bàn, khoảng10 NCC liên quan và phấn đấu2–3 báo giá cùng cơ sở/vật liệu trọng tâm; đây không phải số đã đạt. PLAN trước đây nêu ≥6tháng/≥3đại lý; không biến các con số đó thành tiêu chí thống kê tự động. DATA20 yêu cầu đủ chia thời gian/vật liệu và công bố giới hạn, không đặt số dòng train tùy tiện.

## 4. Biểu mẫu thu thập đề xuất — tái dùng artifact đã có

Không tạo mẫu mới hoặc sửa Excel trong lượt DATA20. Tái dùng:

`C:/Users/Admin/.codex/visualizations/2026/11/03/01a1a207-0d6b-7120-b459-4ebbd2497138/outputs/01a1a207-0d6b-7120-b459-4ebbd2497138/Bao_gia_MVP_dieu_kien_04_20261104.xlsx`

Tệp có bảng Báo giá, Hướng dẫn, Giải thích cột, Maps, Đối chiếu đơn mua, Phí giao và dịch vụ. Hai bảng đối chiếu/phí mới để trống; 63 dòng lịch sử chưa duyệt train. Không gọi tệp này là dữ liệu đã nạp vào schema20; chưa kiểm native Excel hoặc mapping import20.

Trường thu tối thiểu:

1. Mã dòng/chứng từ/nhóm nguồn/phiên bản, mã vật liệu ứng viên và đã duyệt tách riêng, tên gốc/brand/SKU/mác/quy cách, mã và tên NCC khi có.
2. Đơn vị bán, giá và lượng/bậc giá/tối thiểu nguyên gốc; tiền tệ; đơn vị chuẩn/hệ số và nguồn quy đổi; không tự điền1 hay suy trọng lượng bao.
3. Địa bàn áp dụng, kho và địa chỉ giao phân biệt; ngày lập, kỳ gốc, hiệu lực từ/đến, ngày thực sự biết, ngày thu và ngày xác minh riêng. Thiếu ngày thì không tự đặt ngày01.
4. VAT đã gồm hay chưa/thuế suất nếu có; vận chuyển/bốc dỡ/bơm/chờ; cách thu theo đơn/chuyến/m³/giờ, phí đã gồm trong giá và phạm vi phân bổ. Không tự thuế hóa hoặc chia phí.
5. URL/tệp chứng từ gốc+trang/dòng+hash; người kiểm/trạng thái xác minh/duyệt train; ACTUAL/SAMPLE/SYNTHETIC và BULLETIN/DEALER/QUOTE độc lập nhau.
6. Nếu xét mua, tham chiếu project/drawing/review/material revision, dòng lượng mua và đơn/đợt giao; xác nhận đúng lượng/quy cách/nơi giao/ngày đặt bằng chứng từ NCC. Các trường chưa có nơi lưu20 giữ trong artifact có nguồn, chờ owner chốt nhập.

Không thu thêm danh bạ hàng nghìn dòng để thay báo giá đúng vật liệu. Ưu tiên mã đang dùng trong một hồ sơ build đã chốt; gạch/vữa và xi/cát đúng cấp phối trước. Bê tông chỉ lấy mác/cách cấp đúng thiết kế, không tự thay cấu tạo để có báo giá. D07/D05/D06 chốt SKU/đơn vị/cấp phối trước D08 chuẩn hóa giá.

## 5. Chia tập và mốc đối chứng đề xuất

**Chốt mục tiêu trước:** dự đoán giá công bố cùng địa bàn/cơ sở hay báo giá đại lý theo lượng và điều kiện giao. Không gộp hai mục tiêu bằng một nhãn unit_price. Tách currency, SKU, đơn vị, địa bàn, VAT/giao, cấp lượng; chỉ quy đổi nếu có nguồn và lưu cả bản gốc.

**Chia thời gian:** dùng mốc thông tin thực sự sẵn có, không chỉ ngày văn bản được nhập hồi tố. Đăng ký cutoff/horizon trước; train cũ, validation kế tiếp, test tương lai giữ kín. Nhóm bản sao/chứng từ đính chính và các dòng cùng sự kiện; không để copy cùng báo giá đi qua hai tập, không sao chép giá để lấp tháng. Với gói hiện có, hai ngày lưu17/03 và20/06 không đủ một đánh giá tương lai đáng tin; một số vật liệu chỉ có một kỳ. Không gọi 63 là63 kỳ hoặc63 mẫu độc lập.

**Theo vật liệu:** báo count theo vật liệu/SKU×tỉnh×đơn vị×price_level×VAT/cước×kỳ; tách vật liệu/cặp NCC đã gặp và chưa gặp. Nhóm chưa có lịch sử hoặc tập test độc lập thì chỉ báo coverage/không đánh giá. Nếu thử giữ lại vật liệu chưa gặp, đó là thí nghiệm cold-start riêng, không trộn kết quả nội suy theo thời gian. Không tách các biến thể cùng nguồn thành các “vật liệu độc lập” để làm điểm cao.

**Baseline bắt buộc:** giá gần nhất đã biết cho đúng nhóm đồng nhất trước cutoff; định nghĩa rõ fixed-origin hoặc rolling, không dùng giá tương lai. Không có nhóm tương thích thì ghi không có baseline. Median theo vật liệu chỉ là baseline phụ nếu còn đúng cơ sở và phải công khai fallback. Ridge dùng cùng đầu vào sẵn có và giao thức lượng dữ liệu fit được chốt; đối chiếu XGBoost trên đúng cùng tập dòng/coverage.

**Báo cáo:** MAE/RMSE theo đơn vị/vật liệu, MAPE khi giá dương, R² chỉ khi tập đủ nghĩa; counts, kỳ, số nguồn độc lập, độ phủ/fallback/cold-start và phần loại. Không dùng R² gộp giá viên/tấn/m³ làm kết luận chính. Được phép XGBoost thua baseline; không đổi split để thắng. Không đưa metrics mô phỏng hiện có sang chương ACTUAL.

## 6. Các cổng trước train — hiện chưa đạt

1. D05–D08 cung cấp export ACTUAL-only được duyệt, nguồn+hash/locator, đúng SKU/đơn vị/tiền tệ/địa bàn/loại giá/VAT/cước. Có bảng lượng/kỳ thật và log loại, không nhãn ACTUAL do default hoặc vì có dòng DB.
2. Kiểm quantity và giá hữu hạn dương; ngày có nguồn/không tương lai; ngày biết, trùng chứng từ và đơn vị. Quantity1 lịch sử không chứng minh chiết khấu hay lượng giao. Supplier NULL ở BULLETIN phải có chính sách train công khai, không tạo nhà cung cấp giả để tránh dropna.
3. Owner/root chốt đường bảo toàn metadata chưa có cột20, contract xuất lịch sử và version/hash. Không gọi trực tiếp `--from-db` trên DB chưa được phê duyệt hoặc chưa chuyển đổi.
4. Có train/val/test thật sự chia được, cutoff/horizon/mục tiêu/coverage/metrics đã đăng ký và tập test chưa dùng phát triển. Không coi việc code time_split chạy được là đủ.
5. Owner được release khép các gap code hiện thấy: loader chưa lọc ACTUAL/price_level/source/cơ sở; bỏ hàng thiếu supplier; chỉ cảnh báo SYNTHETIC chứ chưa gate SAMPLE/UNKNOWN; chưa kiểm log quantity≤0/Inf. Baseline đang group material+supplier bỏ tỉnh/đơn vị/VAT/giao và đánh giá mask khác XGBoost/Ridge; Ridge fit train+val khác XGBoost. Model.load chưa gate provenance, knows chỉ kiểm hai ID riêng. Phiên16 không sửa các phần này.
6. 01/root cấp lượt thực nghiệm riêng, input đã duyệt, output mới không đè models, seed/config/dependencies+hash được lưu. Metadata mô hình và đầu vào thực dùng chỉ đăng ký sau review theo D10; không chạy hoặc tạo model trong D08.

Chưa đề xuất chạy train trên gói63. Khi các cổng được release, dùng CSV export đã duyệt thay cho truy cập DB trực tiếp; cú pháp CLI hiện có là `python -m optimat.predict.train --data <export_ACTUAL_da_duyet.csv> --out <thu_muc_output_moi>`. Đây là mẫu lệnh, không xác nhận input tồn tại, đủ điều kiện hoặc được cấp phép thực thi.

## 7. Bàn giao và giới hạn

- D07/owner nguồn cung: chứng từ thật đúng lượng/SKU/nơi giao và hiệu lực; leadtime/địa điểm/xe/nhân công có nguồn, không lấy sample bù.
- D05/D06: duyệt mapping và cơ sở quy đổi/cấp phối; CA01/CA02, thép và biến thể xi măng cần giữ đúng quy cách.
- Root schema20/owner04: bảo toàn metadata còn thiếu; contract báo giá theo đơn và snapshot/đường xuất, không cấp thêm bảng từ báo cáo này.
- 16/D08: ledger đủ trường quan sát và gap, biểu mẫu tái dùng, split/baseline/cổng readiness. Chỉ rà nguồn được giao; việc thu mới do điều phối phân công.

Đã đọc hai Markdown schema/kế hoạch20 và source schema20/models/predict; Word mới được thông báo là bản xuất nhưng chưa kiểm bố cục Word trong lượt này. Các PDF/ảnh có bằng chứng rà ở lượt trước, lượt DATA20 chỉ tái dùng báo cáo/manifest/receipt; chưa mở hoặc tải lại để tuyên bố kiểm độc lập mới. Chưa kiểm migration/main DB, không đọc thư mục backup hay thông tin kết nối. CSV gap là báo cáo kỹ thuật; không thay CSV canonical, Excel, models hoặc dữ liệu vận hành.

Kiểm báo cáo: đọc lại UTF-8/cấu trúc CSV, số dòng theo grain và hash các tệp nguồn thực đọc; không chạy suite hay import module ứng dụng. Hash/số dòng chỉ phục vụ truy vết, không chứng minh nghiệm thu hoặc trạng thái DB sau chuyển đổi.
