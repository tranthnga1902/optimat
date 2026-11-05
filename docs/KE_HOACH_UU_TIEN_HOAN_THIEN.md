# Kế hoạch ưu tiên hoàn thiện sớm, có bằng chứng

Chỉ đạo chủ đồ án 03/11/2026: đẩy nhanh hoàn thiện, sát thực tế, chỉn chu, không bịa số liệu.
Ưu tiên này thay thứ tự mở việc cũ; không thay phạm vi M01 hoặc biến mục tiêu chất lượng thành kết quả đã đạt.
Phân vai tại PHAN_VAI_CAC_PHIEN.md;01 điều phối triển khai,00 cố vấn và chốt đặc tả.

## Quy trình từ bản vẽ đến báo giá vật liệu phần thô (04/11/2026)

Áp dụng cho nhà ở riêng lẻ xây mới tối đa 5 tầng theo [ma trận M01](M01_PHAM_VI_PHAN_THO.md). Đây là trình tự nghiệp vụ để tích hợp và nghiệm thu trên các màn hình hiện có.

1. **Nhận hồ sơ.** Lưu thông tin dự án, bản gốc và phiên bản KT/KC, thuyết minh và bảng tiên lượng đối chứng. Đánh dấu phạm vi áp dụng, tài liệu thiếu và xung đột. Xem trước độc lập với phân tích.
2. **Đọc thiết kế.** Gắn số hiệu bản vẽ, tầng/trục, mặt bằng, mặt cắt, chi tiết và bảng thống kê với cấu kiện. Ưu tiên kích thước ghi trên thiết kế. Số đo từ hình học CAD phải có đơn vị và căn cứ đối chiếu. Phóng hình hay kéo thước tỷ lệ hiển thị không thay đổi số đo. Hai nguồn mâu thuẫn thì giữ cả hai, yêu cầu làm rõ trước khi xác nhận phần liên quan.
3. **Lập tiên lượng theo công tác.** Mỗi dòng có cấu kiện/vị trí, số lượng, các kích thước áp dụng, đơn vị, công thức, phần cộng/trừ, kết quả và nguồn. Bê tông theo hình dạng thực, thép theo số thanh × chiều dài triển khai × khối lượng đơn vị đúng đường kính, cốp pha theo mặt tiếp xúc cần làm khuôn. Phân biệt khối lượng công tác với vật tư sẽ mua, kể cả công tác có khối lượng nhưng không phát sinh vật tư mua.
4. **Kiểm và xác nhận khối lượng trước khi lập phương án.** Kiểm đơn vị, lỗ mở, giao dầm–cột–sàn, thang–sàn và mái–sàn. Lưu quy tắc phân bổ và nguồn của phần trừ. Giữ phần chưa tính cùng lý do nếu thiếu căn cứ. So với bảng người dùng cung cấp theo cùng phạm vi, đơn vị và phiên bản. Chênh lệch, kể cả với công trình tương tự, là tín hiệu rà soát. Lưu phiên bản phần đã xác nhận.
5. **Lập và kiểm bảng vật tư từng phương án.** AI hỗ trợ toàn bộ công tác đã kiểm theo thiết kế và nhu cầu người dùng. Gắn từng vật tư với công tác nguồn. Kiểm quy cách, định mức và hao hụt từng phần góp, kể cả hao hụt đã nằm trong định mức. Tách lượng lắp đặt, hao hụt bổ sung có căn cứ và lượng mua sau quy đổi/đóng gói. Không áp tỷ lệ hao hụt chung. Hai phương án bê tông thương phẩm và trộn tại chỗ phải có bảng mua riêng để tránh cộng cả bê tông và thành phần cấp phối cho cùng một khối lượng.
6. **So báo giá theo lượng mua.** Đối chiếu báo giá mua thực theo nhà cung cấp, quy cách, đơn vị, số lượng, địa điểm, hiệu lực, VAT và điều kiện giao hàng. Tính phí giao theo chuyến/đơn đúng một lần. Ghi rõ phần có giá và phần thiếu trong từng phương án. Giá tham khảo hoặc dự đoán có nhãn riêng.
7. **Chốt và bàn giao.** Lưu phương án đã chọn và xuất bảng mua kèm tiên lượng, nguồn vật tư/giá, phiên bản và danh sách cần xác minh trước khi đặt hàng. Gọi tổng là chi phí vật tư theo phạm vi báo giá. Chỉ công bố sai số hoặc thời gian tiết kiệm khi có phép đối chứng thực tế. Khi thay bản vẽ hoặc kích thước, đánh dấu các dòng bị ảnh hưởng để kiểm lại trước khi dùng báo giá cũ.

Ca nghiệm thu xuyên suốt: từ một dòng vật tư trên bảng mua lần về đúng báo giá, lượng mua, định mức, công tác đã kiểm, cấu kiện và bản vẽ nguồn. Kiểm thêm một dòng thiếu kích thước hoặc thiếu giá và chứng minh phần thiếu vẫn xuất hiện trên giao diện và bản xuất.

## Đích gần nhất

**Mục tiêu điều phối Web UI 80% (04/11).** Thước đo đề xuất riêng cho khả năng trình diễn của web: năm mốc nghiệp vụ, mỗi mốc 20 điểm. Chỉ ghi điểm cho cả mốc sau khi QA đối chiếu bằng chứng thao tác trình duyệt trên cùng dự án và các phiên bản dữ liệu tương ứng. Bốn mốc đầu là điều kiện cho mức 80, mốc cuối là bàn giao kết quả. Không dùng số màn hình hoặc bài test để suy tiến độ toàn đồ án.

| Mốc | Thao tác người dùng cần chứng minh |
|---|---|
| 1. Hồ sơ | Chọn dự án 23, tải CAD mẫu được phép, nhập/lưu thông tin ngay trên trang, rời rồi mở lại đúng bản gốc và phiên bản. |
| 2. Phân tích | Xem trước độc lập, bấm Bắt đầu phân tích đúng bản đã chọn, chuyển sang bóc tách không tải lần hai. |
| 3. Tiên lượng | Xem cấu kiện, kích thước, công thức và nguồn. Kiểm, sửa, lưu rồi mở lại đúng bản khối lượng, giữ được dòng thiếu. |
| 4. Phương án vật liệu | Từ khối lượng đã kiểm, mở tối ưu trực tiếp, nhận tư vấn theo nhu cầu và quy cách, kiểm cả nhóm ngoài tường, lưu và mở lại phương án. |
| 5. Báo giá và xuất | So giá cùng điều kiện, tách phần chưa có giá và kiểm bảng mua xuất ra khớp giao diện trên đúng phiên bản. |

Tệp SAMPLE dùng để kiểm thao tác; nếu mẫu không phát sinh cấu kiện cần cho mốc sau, ghi rõ giới hạn và kiểm chuỗi trên một hồ sơ khác được phép, không ghép số liệu của hai hồ sơ. Nghiệm thu sai số khối lượng, báo giá mua thực và mục tiêu dữ liệu của toàn đồ án có tiêu chí riêng.

**Các loại tệp đầu vào tại Dự án của tôi (04/11/2026).** Người dùng có thể thêm nhiều tệp và chọn vai trò nghiệp vụ riêng với định dạng: bản vẽ kiến trúc/kết cấu (CAD hoặc PDF), hồ sơ dự án (thuyết minh, yêu cầu kỹ thuật ở PDF hoặc Word), bảng khối lượng/tiên lượng (Excel .xls/.xlsx hoặc PDF). Khi có riêng một bản kiến trúc PDF vẫn cho lưu, xem và mở lại dự án. Cùng là PDF có thể là bản vẽ, thuyết minh hoặc bảng khối lượng. Cho sửa vai trò do hệ thống gợi ý. Giữ bản gốc, phiên bản và tên tệp. PDF xem từng trang; Excel xem bảng/sheet khi bộ đọc hỗ trợ, luôn có tải bản gốc có phân quyền. Gắn nguồn trang/sheet/dòng khi có căn cứ. Trạng thái được dùng để phân tích phụ thuộc khả năng thực tế của bộ đọc; nhận hồ sơ PDF/Excel không tự đồng nghĩa đã nhận dạng hình học CAD hoặc đã nhập đúng số liệu. Nếu chỉ có PDF, chỉ ra các thao tác khả dụng và tệp cần bổ sung cho phép đo chưa hỗ trợ. Bảng khối lượng do người dùng cấp là một nguồn riêng để đối chiếu với kết quả bóc. Chênh lệch được giữ để người dùng duyệt. Không cộng hai nguồn vào cùng tổng. QA thêm ca tải/lưu/mở lại bộ hỗn hợp và ca hồ sơ chỉ có bản vẽ PDF.

**Bố cục theo ảnh đã đính chính (04/11/2026).** Trên desktop đặt danh sách công trình theo chiều dọc ở cột trái với tìm kiếm, nút Thêm và dấu hiệu dự án đang chọn. Cột phải hiển thị thông tin công trình và bảng hồ sơ của dự án đó. Sửa/Xóa ở cuối chi tiết; Sửa mở biểu mẫu ngay tại cột phải, Lưu/Hủy trở về chế độ xem. Trên điện thoại, chuyển từ danh sách sang chi tiết và có đường quay về danh sách. Dùng dữ liệu của dự án đang mở. Ảnh tham chiếu chỉ định bố cục. Kiểm demo trong cùng dự án QA và giữ nguyên lịch sử phiên bản tệp.

**Quyết định của chủ đồ án ngày 03/11/2026.** Đã duyệt bổ sung hai bảng PostgreSQL `project_document_revisions` và `project_profile_revisions` theo phương án phiên 01 trình. Phạm vi gồm phiên bản bất biến của tệp nguồn, lịch sử thông tin dự án và tham chiếu đúng bộ tệp dùng cho lần phân tích. Phiên 01 tiếp tục giao 06 triển khai migration/API và phối hợp 02/17/15 khi hạn mức và xét duyệt công cụ hoạt động trở lại. Ghi riêng trạng thái đã duyệt, đã áp migration và đã kiểm runtime. Kiểm migration trên DB kiểm thử trước, bảo toàn dữ liệu hiện hữu theo phương án quay lui đã trình. Tiêu chí demo là toàn bộ thao tác trước phân tích diễn ra ngay trên trang Dự án của tôi, sau đó thấy đúng phiên bản được chuyển sang bóc tách.

**Bố cục `/du-an-cua-toi` theo quyết định mới nhất.** Mở trang vào danh sách công trình theo chiều dọc. Bấm một công trình để xem thông tin, tệp, phiên bản và nguồn ngay trên trang. Cuối phần chi tiết đặt Sửa và Xóa. Bấm Sửa mới mở biểu mẫu trong trang. Lưu thành công quay về chế độ xem với giá trị mới. Hủy quay về chế độ xem với giá trị đã lưu trước đó. Nút Thêm ở danh sách mở biểu mẫu tạo mới trong trang. Hành vi Xóa chờ quyết định riêng. Tải tệp qua bộ chọn tệp thông thường. Bản xem trước và nút Bắt đầu phân tích nằm trên trang chi tiết. Demo lần lượt tải bản vẽ, sửa và lưu thông tin, về danh sách và mở lại dự án, đối chiếu bản gốc/phiên bản và giá trị hiệu lực, rồi bấm phân tích để thấy đúng tệp được chuyển sang bóc tách. Lưu ảnh thực tế ở các mốc này.

**Hồ sơ dự án do người dùng cung cấp và kiểm nguồn.** Tại trang Dự án của tôi, tách rõ “Thông tin công trình” và “Hồ sơ gốc” trên cùng dự án. Tái dùng thông tin đã lưu. Cho nhập, sửa và lưu tên/mô tả, địa điểm hoặc khu vực giao hàng, loại công trình, số tầng, thông số theo tầng nếu biết, ghi chú và nhu cầu lựa chọn vật liệu như ngân sách vật tư, thời điểm cần hàng, vật liệu ưu tiên/loại trừ. Phân biệt dữ kiện thiết kế và mong muốn của người dùng. Trường tùy chọn được để trống.

Mỗi giá trị trích có liên kết “Xem nguồn” về đúng tệp và phiên bản, kèm trang, tầng, bảng/ô hoặc vị trí CAD nếu đã xác định. Nếu chỉ biết tệp thì mở đúng tệp và ghi mức truy vết đó. Thông tin do người dùng nhập được ghi rõ nguồn nhập tay. Hiện riêng giá trị gốc và giá trị chọn để phân tích khi người dùng sửa hoặc khi hai nguồn khác nhau, bảo toàn tệp gốc. Hỗ trợ đính kèm tài liệu làm căn cứ (ví dụ PDF thuyết minh hoặc bảng tiên lượng), hiển thị nguyên bản với định dạng hỗ trợ hoặc cho tải đúng tệp khi chưa xem trước được. Trước nút phân tích, cho người dùng kiểm bộ tệp/phiên bản, thông tin sẽ dùng và phần chưa có. Việc xem hồ sơ không đòi chạy nhận dạng trước. Demo phải chứng minh nhập một thông tin, mở lại dự án, xem nguồn của một mục có căn cứ, mở bản gốc và bấm phân tích đúng bộ đã chọn.

**Dự án của tôi — hồ sơ trước phân tích.** Tại `/du-an-cua-toi`, người dùng tải lên bản kiến trúc, kết cấu và bản tham khảo theo dự án. Giữ nguyên tệp nguồn, gắn định danh và phiên bản. Danh sách cho xem tên, loại hồ sơ, định dạng, dung lượng, thời điểm tải, phiên bản và trạng thái. Người dùng mở bản gốc để xem, phóng/di chuyển; với CAD dùng bản hiển thị dựng từ nguồn, ghi rõ định dạng gốc và cho tải đúng tệp nguồn. Khi chưa dựng được bản xem trước phải báo lý do. Thông tin nhập tay, ghi trên bản vẽ và chưa xác định được phân biệt rõ.

Trước khi chạy, cho kiểm/sửa thông tin dự án, địa điểm và số tầng khi biết, vai trò từng tệp và phiên bản chọn phân tích. Tải lên hoặc mở xem chỉ lưu/dựng bản xem trước. Chỉ nút “Bắt đầu phân tích” gửi các tệp đã chọn sang bước bóc tách, không yêu cầu tải lần hai. Nghiệm thu gồm mở lại dự án, mở đúng bản gốc và phiên bản sau tải lại trang, phân quyền qua backend, xem trước lỗi và xác minh chưa chạy bóc tách khi chỉ xem. Ưu tiên tái sử dụng luồng tiếp nhận tệp hiện có; 01 phân vùng trước khi ghi source chung.

**Vai trò AI trong demo.** Tại bước Chọn vật liệu, trợ lý hỗ trợ toàn bộ phần thô thuộc phạm vi dự án. Đi từ từng công tác đã kiểm theo tầng/cấu kiện tới các dòng vật tư tương ứng và nhu cầu người dùng (ngân sách, lịch giao, địa bàn, cách cung cấp). Bao phủ móng, cột, dầm, sàn, thang, mái và cấu kiện phụ, xây/trát, nền và chống thấm khi phát sinh. Nhóm vật tư gồm bê tông và vật liệu cấp phối, thép theo quy cách, cốp pha, gạch và vữa, vật tư nền/chống thấm và phụ kiện theo căn cứ. Công tác không phát sinh vật tư mua được ghi rõ. Khối lượng lắp đặt và lượng mua phải có cơ sở quy đổi riêng.

Lọc theo yêu cầu thiết kế trước, sau đó mới xếp phương án phù hợp với ưu tiên người dùng. Chỉ so tiêu chí áp dụng cho nhóm đó (ví dụ hệ số U cho phương án tường bao). Ghi nguồn của mã, định mức, giá, vận chuyển và thời gian giao khi có. Nhóm chưa có quy cách, định mức, báo giá hoặc lựa chọn hợp lệ vẫn hiện cùng lý do và thông tin cần bổ sung. Người dùng xác nhận lựa chọn; thay đổi cấu tạo ảnh hưởng khối lượng phải kiểm lại. Phạm vi tư vấn toàn phần thô độc lập với phạm vi thuật toán NSGA-II hiện dành cho tường.

Nghiệm thu trên một hồ sơ nhiều nhóm bằng cách đối chiếu tất cả dòng công tác đã kiểm với các dòng vật tư/nhóm không phát sinh hoặc còn thiếu. Kiểm ca có nhiều/một/không có phương án, thay đổi ưu tiên người dùng, thiếu giá và không thay quy cách thiết kế để hạ giá. Kiểm một lượt API thật bằng dữ liệu demo được phép. Demo chỉ có gạch/vữa chưa đạt phạm vi trợ lý.

Một luồng dùng được, giữ dữ liệu và giải thích được:
**Dự án → Bóc tách KT/KC → Kiểm công tác/kích thước/khối lượng → Nhận phương án vật liệu tại Tối ưu → So sánh với AI → Áp dụng phương án/xuất bảng mua.**

**Điều chỉnh của chủ đồ án, ưu tiên so với mô tả bước Chọn vật liệu ở trên.** Sau khi lưu khối lượng đã kiểm, người dùng có thể mở thẳng `/toi-uu`. Hệ thống lập phương án nháp toàn phần thô từ bản đã kiểm và nhu cầu người dùng. Màn chỉnh vật liệu và xem chi tiết giá là tùy chọn. Trợ lý AI có điểm vào chính ngay trên màn phương án.

- Giữ các lựa chọn đã chốt. Vật tư hoặc cấp phối phù hợp duy nhất, đủ căn cứ thiết kế, danh mục và quy đổi thì điền vào bản đề xuất kèm nguồn. Nhiều ứng viên thì lập phương án, so sánh theo tiêu chí người dùng và nêu đánh đổi. Chỉ áp dụng khi người dùng chốt phương án, không buộc xác nhận từng dòng.
- **Xem tư vấn** dùng trực tiếp bản khối lượng đã kiểm (`approvedWork`). Người dùng mở được `/toi-uu` dù chưa có `materialRevision`, chưa chọn mã ở danh sách và chưa đủ giá. Backend tìm ứng viên từ quy cách, danh mục và nguồn đã biết. Việc tìm ra một mã phù hợp chỉ thêm mã vào bản nháp. **Chốt bảng mua** lưu lựa chọn của người dùng và chỉ đưa vào phần sẵn sàng mua những dòng đủ quy cách, cơ sở lượng mua và điều kiện giá tương ứng. Phần chưa đủ vẫn hiển thị cùng lý do.
- Thiếu thông số quyết định an toàn/quy cách, giá hay lịch giao thì giữ rõ phần thiếu. Cho phép phương án có điều kiện, ghi giả định và ảnh hưởng; mọi tổng chi phí chỉ bao phủ các dòng có đủ giá. AI không tự đổi thiết kế đã duyệt. Thay đổi hình học phải quay lại kiểm phần bị ảnh hưởng.
- Nghiệm thu với hồ sơ chưa chọn tay vật liệu, gồm cả ca không có tường. Từ khối lượng đã kiểm phải tới được phương án có dữ liệu, hỏi AI và lưu lựa chọn. Kiểm cả ca thiếu giá, không có ứng viên, đổi ưu tiên, quay lại chỉnh tay và bảo toàn phiên bản. Phân biệt kết quả thuật toán chuyên tường với phương án đề xuất có điều kiện cho các nhóm khác.
Chạy trên hồ sơ ACTUAL-build có nguồn; người dùng được sửa và xác nhận một phần. Không hứa tự nhận đủ mọi hồ sơ.
Không lấy các tỷ lệ95%/10% trong kế hoạch làm thành tích; báo giá dự đoán không thành báo giá mua thật.

## Ba đợt ưu tiên, mở ngay khi đủ phụ thuộc

| Đợt | Công việc | Phụ trách | Cổng ra |
|---|---|---|---|
| 1. Khép tính đúng và luồng | Sửa lỗi chặn JSON; kích thước từng cấu kiện/lớp có nguồn; N03/raw-net; UI mới/guard/lưu/khôi phục | 02/03;04 audit glue;14 review độc lập | Hợp đồng UI/backend khớp, focused terminal đạt, không mất số biết/không gán0 phần thiếu |
| 2. Khép vật tư và dữ liệu | Kiểm định mức/quy cách/hao hụt hiện có; tính lại sau chọn vật liệu; tách giá tham khảo/báo giá mua; kiểm tệp hồ sơ và đáp án | 04/05/06/07;16 readiness mô hình | API/UI/BOQ cùng cơ sở lượng, nguồn/đơn vị rõ; phần thiếu vẫn hiện |
| 3. Kiểm thực tế và đóng gói | QA quy trình với một hồ sơ ACTUAL-build KT+KC, sửa lỗi quan trọng, freeze/full một lượt; hướng dẫn và video khi luồng ổn | 15 chuẩn bị,02 thao tác theo lịch01;05 full | Có bằng chứng thao tác/ảnh, test terminal/hash ổn định; công bố giới hạn còn lại |

Các đợt chồng phần việc độc lập, không chờ xong toàn bộ một đợt mới chuẩn bị đợt sau. Không mở rộng cấu kiện,
dashboard, bản đồ hay tái cấu trúc không cần thiết khi luồng lõi còn lỗi. Không nhân thêm chat cho cùng nhiệm vụ.
Không đặt ngày xong giả khi dữ liệu/quyền thao tác chưa đủ:01 nêu blocker, người xử lý, việc tiếp theo và chỉ dự báo
thời gian khi có căn cứ thực thi. Mốc demo22/11 và đồ án17/01 giữ làm mốc ngoài, không là lý do chờ đến sát hạn.

## Quy tắc không bịa số

- Kích thước lấy từ hình học/chữ/bảng có nguồn hoặc nhập tay có ghi nguồn; suy luận/giả định hiển thị riêng, không gọi là đo trực tiếp.
- Thiếu thì để trống, lý do và phạm vi khối lượng một phần; không điền mặc định cho đủ bảng. Không suy cạnh từ diện tích/thể tích.
- ACTUAL/SAMPLE/SYNTHETIC tách biệt; đáp án chưa kiểm không dùng tuyên bố sai số. Không đổi split theo kết quả test.
- Giá công bố/tham khảo, báo giá đại lý và giá dự đoán phân biệt đúng nguồn/điều kiện. Thiếu báo giá hợp lệ thì chưa có giá mua,
  không gọi chi phí vật tư là tổng dự toán. Không dùng đơn giá bất kỳ cùng mã để che thiếu quy cách/VAT/giao hàng.
- Không ghi passed khi không có kết quả terminal; không suy phần trăm hoàn thành từ testcount. Chỉ ghi nghiệm thu đúng phạm vi đã kiểm.

## Cách rút ngắn thời gian mà vẫn chỉn chu

- Mỗi owner bàn giao một thay đổi nhỏ có ví dụ trước/sau và test trọng tâm;14/15 review/chuẩn bị ngay bên cạnh dev.
- Chỉ một writer mỗi vùng mã, không full trên source đang đổi; không chạy nhiều suite/CAD nặng tranh tài nguyên.
- Chặn lỗi mất dữ liệu, sai lượng, sai đơn vị, số giả/giá sai trước; tiếp theo là hiển thị dễ hiểu, điều hướng và phản hồi lỗi.
- UI kiểm được từng cấu kiện, kích thước, nguồn, khoản trừ và phần thiếu; không cần đi tìm công thức trong nhiều màn hình.
- Người dùng vừa từ chối gate upload Tân Bình tại localhost3000: không thử lại hoặc lách qua công cụ khác.
 15 chuẩn bị ma trận/test không phụ thuộc upload; QA hồ sơ thật chờ người dùng tự chọn hoặc cấp lại quyền, ghi rõ chưa nghiệm thu.

## Báo cáo để chủ đồ án kiểm soát

### Ưu tiên đầu vào hồ sơ nhà ở (05/11/2026)

| Việc | Đầu mối | Bằng chứng để đóng việc |
|---|---|---|
| Chọn vai trò và phiên bản trước khi chạy | 01 phối hợp 02/17 | Thử chọn đồng thời DWG kiến trúc và kết cấu, chọn riêng KC, chọn hai phiên bản cùng tệp. Thấy lý do nếu chưa chạy được và biết phần nào có thể kiểm khi chỉ có KT. |
| Phân tách hồ sơ lớn theo tệp, tờ và tầng | 03/06 | Chạy lại VN002 qua đúng đường vào dự án. Ghi riêng thời gian đọc, nhận diện, dựng CAD, lưu và mở lại. Tách vùng phải giữ tham chiếu sang mặt cắt, chi tiết và bảng thép. Vùng thiếu nguồn được giữ lại để kiểm. |
| Đối chứng cấu kiện trước khi dùng để chọn vật liệu | 07/15 | Ghi tên tệp, phiên bản, tầng/trục, ký hiệu, kích thước ghi trên hình, công thức và phần thiếu. Kiểm riêng nhận diện đúng, nhận nhầm, bỏ sót và sai khối lượng trên cùng phạm vi đã đo tay. |

01 chỉ chốt khi có kết quả trên bản chạy và bản vẽ được phép. Số nét xem trước và thời gian đo riêng một hàm không phải tỷ lệ hoàn thành hay thời gian toàn luồng.

01 tổng hợp theo việc: đã đạt có bằng chứng / đang sửa / chờ dữ liệu hoặc quyết định. Mỗi mục có owner và hành động kế tiếp.
00 đề xuất điều chỉnh nếu phạm vi hoặc dữ liệu thay đổi. Các phiên chuyên môn báo kết quả về01, không tự mở thêm phạm vi.
Phiên16 chỉ chốt độ sẵn sàng; XGBoost huấn luyện/đánh giá khi đủ dữ liệu và được xếp lịch, không giữ luồng đo bóc chờ mô hình.
