# DATA20 · Kế hoạch điều phối dữ liệu phần thô

**Ràng buộc của chủ đồ án:** giải quyết nguyên nhân tại bước đọc và liên kết dữ liệu nguồn. Giữ đúng 20 bảng vật lý. Nếu một thay đổi cần tạo thêm bảng, đầu mối phải nêu vấn đề, bằng chứng, phương án dùng cấu trúc hiện có, tác động và chờ chủ đồ án duyệt trước khi tạo. Lượt đối chiếu DM-1 chỉ đọc bản vẽ, không thay đổi PostgreSQL.

**Cập nhật sau phê duyệt ngày 04/11:** DB chính `optimat` đã chuyển sang 20 bảng, trạng thái `committed_verified`; 28 cấu trúc cũ được đối chiếu dòng/cột trong giao dịch, còn dự án 23 và 26 lần phân tích đã niêm phong. Những mục bên dưới mô tả điều kiện trước lúc triển khai. Chủ đồ án cũng đã cho dùng cặp KT/KC VN002 hiện có để kiểm nội bộ. [Biên nhận DB chính](../../../reports/schema20_main_receipt.json) · [Mức sẵn sàng và dòng VN002 đã đối chiếu](DU_LIEU_SAN_CO_VA_PHAN_THIEU.md).

Ngày lập 04/11/2026. Phạm vi của 00 là kế hoạch và điều kiện nghiệm thu. 01 quản lý người phụ trách, quyền sửa và trạng thái đầu việc trong [bảng DATA20](../data20_01/BOARD.md). D01–D10 dưới đây là mã **gói dữ liệu của đợt DATA20**. Các biên bản cùng mã ở đợt cũ cần đối chiếu lại phạm vi trước khi sử dụng.

## Phạm vi MVP và thứ tự ưu tiên

**Giới hạn áp dụng cho toàn đồ án:** chỉ xét phần thô của **nhà ở riêng lẻ xây mới, không quá 5 tầng**. Khi chọn hồ sơ, ghi loại công trình, số tầng và căn cứ xác định. Hồ sơ chưa rõ điều kiện giữ trạng thái chờ xác minh; công trình ngoài phạm vi không đưa vào mẫu số nghiệm thu. Với hồ sơ hỗn hợp, chỉ xét công tác phần thô phục vụ căn nhà theo ma trận đã duyệt. Ví dụ VN002 chỉ xét dầm và cốt thép của bể nước thuộc nhà; đường ống, thiết bị cấp nước và vận hành bể nằm ngoài phạm vi.

Luồng cần chứng minh cho nhà xây mới tối đa 5 tầng bắt đầu từ một hồ sơ build được phép sử dụng, có bản kiến trúc và kết cấu cùng phiên bản thiết kế. Lần theo một cấu kiện từ bản gốc đến số đo, công tác, khối lượng đã kiểm, phương án vật liệu, lượng mua và báo giá giao tới công trình. Mở rộng cho các nhóm phần thô thực sự xuất hiện. Nếu thiếu vật liệu hoặc giá, bàn giao được phần hình học đã biết cùng danh sách còn thiếu. Chi phí báo cáo là chi phí vật tư.

Ưu tiên đầu là D01–D04 để xác lập mẫu số và dữ liệu hình học. D05–D06 chạy song song trên đúng công tác đó. D07–D08 tập trung một địa bàn và vật liệu cần mua. D09 kiểm bằng ca dương/âm trên build. D10 nối các phiên bản khi đã truy được nguồn. Giá dự đoán phụ thuộc khả năng chia dữ liệu theo thời gian. Thiếu báo giá đủ điều kiện thì dừng phần so mua ở trạng thái thiếu giá.

Giữ mốc demo 22/11/2026 và đồ án 17/01/2027. Sáu tuần là lịch tương đối phụ thuộc nhân lực và dữ liệu. Tại mốc demo chỉ trình phần đã có bằng chứng đến ngày đó. Mục tiêu đợt đầu là 5 hồ sơ thực, trong đó ít nhất 2 công trình test độc lập nếu đủ 5. Mục tiêu dài hạn 12 build/8 test được theo dõi riêng. Hồ sơ SAMPLE, biến thể từ cùng một nhà và các dòng giá công bố có thể phục vụ phát triển nhưng không làm tăng mẫu số thực.

## Tiêu chí sẵn sàng và bằng chứng để 01 nhận việc

| Gói | Điều kiện để nhận | Khi còn thiếu |
|---|---|---|
| D01 · Hồ sơ | Manifest truy được dự án, vai trò tệp, revision, hash, nguồn, quyền sử dụng và split. Kiểm mở và ghép đúng bộ KT/KC. | Ghi thiếu tệp, sai phiên bản hoặc chưa rõ quyền. Chỉ đưa hồ sơ đủ điều kiện vào mẫu số tương ứng. |
| D02 · Cấu kiện | Mỗi cấu kiện thuộc đúng lần chạy, hình và tầng. Đối chiếu một cấu kiện lặp ở mặt bằng/chi tiết/bảng và một đối tượng dễ nhận nhầm. | Ghi chưa định danh hoặc có thể trùng, không tự cộng số lần xuất hiện. |
| D03 · Số đo | Từ giá trị chuẩn truy được giá trị gốc, đơn vị, cấu kiện, vị trí/handle và phương pháp. Tách giá trị được chọn, ứng viên xung đột và giả thiết A/B/C/D theo quy ước hiện hành. | Thiếu giữ NULL và lý do. Phân biệt rõ số 0 đo được với số chưa biết. |
| D04 · Đáp án | Người kiểm độc lập ký đúng revision, công thức, đơn vị, giao/trừ và phạm vi công tác. Split theo công trình; có danh sách dòng đủ/không đủ điều kiện. | Nhãn nháp dùng phát triển. Không lấy kết quả hệ thống làm đáp án cho chính nó. |
| D05 · Danh mục | Vật liệu có mã duy nhất, nhóm, quy cách và đơn vị lắp đặt/mua. Hệ số đổi có chiều và nguồn; nhãn dữ liệu được giữ đến đầu ra. | Để trống thuộc tính thiếu; chưa quy ra bao, viên, tấn khi thiếu quy cách. |
| D06 · Định mức | Liên kết đúng công tác, hệ vật liệu và phiên bản định mức/cấp phối. Tái tính một dòng mua từ lượng đã kiểm, ghi rõ vị trí cộng hao hụt. | Giữ lượng lắp đặt và nêu hệ số thiếu. Thay chiều dày ảnh hưởng hình học phải tính lại. |
| D07 · Nguồn cung | Mỗi vật liệu được tuyên bố mua được có ít nhất một cặp nhà bán–quy cách xác minh được tại địa bàn, kèm nguồn, ngày, đơn vị bán, lượng tối thiểu và điều kiện giao. | Ghi nhà bán tiềm năng. Một địa chỉ bản đồ chưa chứng minh có bán đúng mặt hàng. |
| D08 · Giá | Có chứng từ đúng SKU, lượng/bậc giá, ngày hiệu lực, địa điểm giao, VAT và vận chuyển. Tính phí dùng chung một lần; phân nhãn giá mua, công bố và dự đoán. | Tách số dòng có một giá mua khỏi số dòng có hai nhà bán so được. Khuyết điều kiện thì báo phần thiếu. |
| D09 · Quy tắc | Bộ quy tắc có phiên bản, thứ tự ưu tiên, nguồn, loại payload, ca dương/âm và trường hợp ngoài phạm vi. Chốt hash trước mở test. | Khi xem test để sửa, chuyển ca đó về phát triển và chuẩn bị ca độc lập mới. |
| D10 · Phương án | Từ lịch sử lần chạy truy được revision hồ sơ và lượng đã kiểm, phiên bản định mức/danh mục, nguồn giá, cấu hình/seed và trạng thái duyệt. Phát lại ca nhỏ và đối chiếu tay hoặc vét cạn. | Tách tư vấn có điều kiện khỏi lựa chọn đã xác nhận. Giá mới không làm đổi kết quả cũ. |

## Mốc theo tuần

Theo BOARD của 01 ngày 04/11, 06 phụ trách D01, 07 phụ trách D02–D04, 05 phụ trách D05–D06, 04 phụ trách D07/D10 và 16 phụ trách D08. 15 giữ ma trận QA, 14 review độc lập và S20 giữ phần schema. 03 đã nhận kiểm kê quy tắc D09 và ca âm. Chất lượng D09 còn chờ review. Khi chọn 5 hồ sơ, đối chiếu trùng danh tính VN003/Dĩ An và VN004/Tân Bình theo manifest, giữ nguyên split và yêu cầu quyền dùng của từng công trình.

| Tuần | Đầu ra cần kiểm trước khi chuyển bước |
|---|---|
| 1 | Kiểm kê 20 bảng vật lý, ánh xạ view tương thích, manifest và khoảng trống. Chọn hồ sơ đầu tiên, người kiểm và khóa quy trình benchmark. |
| 2 | Hoàn thiện một gói build từ CAD đến công tác và định mức. Mỗi lượng và hệ số dùng trong ví dụ đều có nguồn. |
| 3 | Mở rộng hồ sơ, tách test độc lập, kiểm chéo đáp án; xác minh nhà cung cấp và chứng từ tại địa bàn đã chọn. |
| 4 | Kiểm ứng viên trên DB thử đúng quyền. Kiểm liên kết chéo dự án, JSONB, tính trùng, đơn vị và 28 tình huống. Mỗi ca ghi đạt, sai, bị chặn hoặc chưa đánh giá cùng bằng chứng. |
| 5 | Đánh giá độc lập trên bản đã khóa, công bố mẫu số/sai số/phần thiếu từng nhóm; đối chứng các phương án mua và tối ưu đủ điều kiện. |
| 6 | Đóng gói manifest, đối chiếu phục hồi DB **cùng tệp gốc**, kiểm hash, snapshot và lần chạy cũ. Bàn giao phạm vi đã kiểm và danh sách tồn tại có owner. |

## Chốt ngưỡng trước khi mở tập test

Tuần 1, người phụ trách đo bóc và QA lập phiếu rồi trình chủ đồ án chốt trên số liệu build. Ghi đối tượng, đơn vị, quy tắc matching, mẫu số, dung sai, cách làm tròn và điều kiện loại từng ca. Chỉ mở đánh giá độc lập sau khi khóa danh sách công trình, hash hồ sơ/đáp án, phiên bản engine, danh mục và ngưỡng. Nếu chưa có người kiểm hoặc mẫu số bằng 0, ghi “chưa đánh giá được”.

- **Nhận diện và số đo:** precision = đúng/số nhận diện, recall = đúng/số cấu kiện trong đáp án. Báo tỷ lệ số đo gắn đúng cấu kiện, hình, tầng, đơn vị và nguồn. Cấu kiện bỏ sót vẫn nằm trong mẫu số recall.
- **Khối lượng:** báo chênh lệch có dấu lẫn sai số tuyệt đối theo nhóm, không để bù trừ che sai. Với đáp án khác 0, báo cả sai số tương đối. Với đáp án bằng 0, báo sai tuyệt đối theo đơn vị. Tách A/B, C và phần D chưa tính. Dung sai số học trên dữ liệu tổng hợp và sai số bóc CAD thực có phiếu riêng.
- **Mục tiêu đề xuất đã có trong kế hoạch đồ án:** ≥95% dòng đáp án hoàn tất, ≥95% dòng mua đủ quy cách, ≥95% dòng mua có báo giá ACTUAL, ≥90% dòng mua so được hai nhà bán, sai số mục tiêu ≤10% cho từng nhóm đủ điều kiện, mọi dòng thiếu có lý do, sai khác đầu ra tối đa một đơn vị làm tròn cuối. Chốt lại mẫu số, cách tổng hợp và ngưỡng với nghiệp vụ trước test. Chạy hết 28 ca không tự động đạt các mục tiêu này.

## Quyết định cần chủ đồ án

| Thời điểm | Quyết định và hệ quả |
|---|---|
| Trước khi nhập gói đầu | Chọn hồ sơ được phép dùng, xác nhận quyền và địa bàn; chọn người lập và người kiểm độc lập. Khi chưa đủ hồ sơ, thu hẹp tuyên bố demo theo dữ liệu có thật. |
| Trước khi khóa benchmark | Duyệt split, công tác trong phạm vi, mẫu số và ngưỡng theo nhóm. Chốt cách tính với giả thiết, hồ sơ thiếu và đáp án bằng 0. |
| Trước khi so mua | Chọn nhóm vật liệu và nhu cầu mua đã kiểm cho địa điểm/ngày giao cụ thể. Xác định điều kiện VAT, phí chuyến và mức bằng chứng chấp nhận từ nhà bán. |
| Trước khi chuyển DB chính | Chủ đồ án xem biên bản đối chiếu bản sao, kết quả phục hồi, hồi quy và phương án quay lại do đầu mối schema bàn giao. Việc chốt thiết kế 20 bảng và kết quả thử trên bản sao là hai mốc riêng với chuyển DB chính. |

Nguồn đối chiếu: [đặc tả 20 bảng](../../schema/CSDL_20_BANG.md) và [kế hoạch hoàn thiện dữ liệu sáu tuần](../../KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md).


## Phiếu quyết định sau kiểm kê DATA20 · 04/11

**Ưu tiên hiện hành theo mục 11 của kế hoạch chung.** Bắt đầu từ một phạm vi nhỏ trong hồ sơ VN002 đang có. Việc cần chủ đồ án lúc này là xác nhận quyền dùng, phiên bản KT/KC và người có thể kiểm số đo cho phạm vi đó. Đầu ra P0 cần thấy là cấu kiện xác định được trên đúng tầng/hình, số đo truy được nguồn, công thức cộng/trừ và danh sách phần thiếu. Đối chiếu với người kiểm trước khi chuyển sang định mức, cấu tạo vật liệu (P1), rồi mới đến nguồn cung, giá và so mua (P2). Hai công trình test độc lập là nhu cầu của đợt đánh giá sau. Chưa giao tìm, mua hồ sơ mới hoặc thu báo giá ở P0. Lúc nhận checklist C00–C17, chỉ C00 (kiểm kê) đã đánh dấu xong. Theo dõi từng bằng chứng ở [mục 11 kế hoạch chung](../../KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md).

01 đã chọn **VN002 làm hồ sơ build đầu tiên để hoàn thiện**. Hiện có bốn công trình phân biệt. Dĩ An còn mang split TEST đã đăng ký, nhưng dữ liệu đã được xem trong quá trình phát triển; loại riêng khỏi phép đo độc lập và ghi lý do. Mục tiêu đợt đầu là 3 build + 2 test độc lập. Các chỉ tiêu thu thập chi tiết nằm trong BOARD của 01.

| Chủ đồ án cung cấp hoặc chốt | Thông tin tối thiểu | Khi chưa có |
|---|---|---|
| Quyền dùng VN002 | Người có quyền, căn cứ/phạm vi cho phép (nội bộ đồ án, chạy phân tích, trình chiếu/chia sẻ), revision KT/KC nào được dùng | Chỉ ghi ứng viên build; không coi tên hồ sơ là bằng chứng cấp quyền |
| Người lập và kiểm | Đầu mối lập đáp án và người đối chiếu độc lập, phạm vi công tác họ có thể kiểm | Giữ nhãn nháp |
| Hai công trình test | Mã hoặc đầu mối cung cấp hai công trình mới, có KT/KC, quyền dùng, chưa dùng để chỉnh quy tắc | Ghi thiếu mẫu số; không dùng biến thể build hoặc Dĩ An để lấp chỗ |
| Ngưỡng nghiệp vụ | Người duyệt và thời điểm duyệt phiếu ngưỡng theo nhóm trên tập build; khóa định nghĩa, ngưỡng, mẫu số và phiên bản trước khi mở đáp án test | Giữ chỉ tiêu ở mức đề xuất |
| Nơi và điều kiện giao hàng | Địa bàn, điểm giao, ngày dự kiến, nhóm vật tư và lượng theo revision đủ căn cứ | Chưa so chi phí giao tới công trình. 63 quan sát công bố không thay cho chứng từ mua; GK01/XM01/CA02 hiện 0/3 mã đủ báo giá |

05 còn đối chiếu viên gạch 60/65 mm và phạm vi định mức. Chưa đổi quy cách để ép khớp dữ liệu. Chuyển DB chính là quyết định riêng sau sửa/kiểm các phát hiện snapshot, tham chiếu JSONB, revision và quyền trên bản sao. Mỗi quyết định trên có thể trả lời riêng; ghi “chưa có” nếu chưa đủ căn cứ.
