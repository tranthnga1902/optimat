# D07 · Khả năng mua vật liệu theo hồ sơ nguồn

**Ngày đối chiếu 04/11/2026.** Chưa có báo giá mua nào trong các nguồn đã rà chứng minh đủ điều kiện cho một đơn hàng cụ thể. Với luồng tường được đề xuất dưới đây, **0/3 vật liệu phải mua** đã có báo giá đạt. Nhu cầu và mã thiết kế vẫn được giữ khi thiếu giá.

## Điều kiện chọn hồ sơ và tính mẫu số

Chỉ đưa vào mẫu nghiệm thu công tác **phần thô của nhà ở riêng lẻ xây mới, tối đa 5 tầng**. Với mỗi hồ sơ, ghi mã công trình, căn cứ loại công trình và tính chất xây mới, số tầng thiết kế cùng tệp/phiên bản/tờ thể hiện số tầng. Thiếu căn cứ nào thì ghi **chờ xác minh** và để ngoài mẫu số đạt chuẩn cho đến khi bổ sung. Nếu xác định là nhà trên 5 tầng, nhà cải tạo, nhà công nghiệp, công trình cấp thoát nước hoặc bể độc lập, ghi **ngoài phạm vi** cùng lý do loại. Với hồ sơ hỗn hợp chỉ xét công tác phần thô phục vụ căn nhà trong ma trận đã duyệt. [Phạm vi phần thô](../../M01_PHAM_VI_PHAN_THO.md) · [Quy tắc chọn hồ sơ DATA20](../data20_00/KE_HOACH_DIEU_PHOI.md)

**VN002 hiện chờ xác minh.** Khung tên KT-01 và KC-01-11 ghi “Nhà ở gia đình”. Con số **4 tầng** đến từ tên gói/manifest. Cần đối chiếu số tầng trên hồ sơ thiết kế và căn cứ xây mới. DM-1 chỉ là dầm và cốt thép bể nước thuộc căn nhà. Không tách DM-1 thành một công trình để tăng mẫu số; đường ống, thiết bị và vận hành bể nằm ngoài phạm vi. [Đối chiếu khung tên và phần còn thiếu](../data20_06/KHUNG_TEN_VN002.md) · [Nguồn thông tin số tầng của gói](../../../data/ground_truth/du_toan/HO_SO_NHAP_20261103.md)

CSV kiểm kê **98 mã vật liệu**. Con số **0/3** ở trên chỉ đo số mã có báo giá đạt trong luồng tường giả định ở Hà Nội. Khi chọn hồ sơ thực, phải xác nhận cả phạm vi công trình, cấu tạo tường và địa điểm giao rồi mới lập mẫu số vật tư của hồ sơ đó. Lượt này chưa bổ sung hồ sơ nào vào mẫu nghiệm thu.

## Cách đọc số liệu

| Phạm vi | Kết quả | Ý nghĩa |
|---|---:|---|
| Kiểm kê DB nguồn trước chuyển đổi | 2.867 nhà cung cấp, 13 cặp NCC–vật liệu, 63 quan sát giá | Số liệu đã ghi trong kế hoạch DATA20 và biên bản nguồn. Phiên này không truy vấn DB. |
| Danh mục CSV chính trong repo | 98 mã vật liệu, 2.843 hồ sơ NCC, 0 cặp cung ứng | 2.843 là số hồ sơ của tệp CSV này. Cả 2.843 ghi `verified=False` và để trống `lead_time_days`. Có 1.267 hồ sơ ghi tỉnh/thành Hà Nội. |
| Thư mục mẫu | 13 cặp, 3 NCC, 5 mã vật liệu | Các mã là AAC01, AAC03, GK02, GK03 và GN01. Thời gian mẫu của SUP_A/B/C không dùng để hẹn giao. |
| Hai manifest giá lịch sử | 59 + 4 = 63 quan sát, 26 mã, địa bàn ghi Hà Nội | Cả 63 mang nhãn BULLETIN. Bốn dòng xi măng đối chiếu CEMIA có VAT, chưa rõ cước. Gói 59 dòng còn chờ đối chiếu PDF gốc theo kiểm kê chứng từ. |

[Kế hoạch DATA20, mục 2–4](../../KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md) · [Biên bản nhập và giới hạn chứng từ](../../../reports/demo_0511/07_APPLIED.md)

**SUPPLY_READINESS.csv** có một dòng cho mỗi mã trong danh mục chính. Các cột `so_*` đếm đúng loại bằng chứng nêu ở tiêu đề. Số 0 ở cột đếm là đã rà nguồn và chưa tìm thấy bản ghi đạt. Đơn giá, đơn vị bán xác nhận, lượng áp dụng, điểm giao, hạn và số ngày giao để trống khi chưa có chứng từ. Đơn vị mua lấy từ danh mục có thể khác với đơn vị nhà cung cấp thực sự báo. Cột đầu mối là danh sách cần đi xác minh. Các mã này chưa được thêm vào `supplier_materials`.

| Ký hiệu trong CSV | Nguồn và cách lần lại |
|---|---|
| M, C | [98 mã và đơn vị](../../../data/catalog/materials.csv) theo `material_id`; [cặp cung ứng chính](../../../data/catalog/supplier_materials.csv) theo cặp khóa |
| S | [Cặp cung ứng mẫu](../../../data/sample/catalog/supplier_materials.csv) theo `material_id`, `supplier_id`, `data_kind` |
| G06, G07 | [Manifest 59 dòng](../../../reports/demo_0511/06_demo_actual.manifest.json) và [manifest 4 dòng xi măng](../../../reports/demo_0511/07_cement_historical_actual.manifest.json), mảng `price_records`, lọc `material_id` để thấy trang, nguồn, ngày và cơ sở giá |
| R | [Các thành phần cấp phối](../../../data/catalog/material_relations.csv), tra `material_id` rồi `COMPOSED_OF` |

## Luồng thu thập đầu tiên

Đề xuất **một địa bàn Hà Nội**, ưu tiên hồ sơ có tường ngăn thiết kế khớp **W-GK01-110**. Hệ này dùng gạch bê tông GK01 và vữa VU02. Khi trộn tại chỗ, bảng cần mua gồm **GK01, XM01 và CA02**. VU02 là lượng trung gian. Phải đối chiếu bề dày thiết kế, khối xây thực, mác, cấp phối và phạm vi đã kiểm trước khi lấy lượng đi xin giá. Nếu hồ sơ chỉ định hệ khác, giữ hệ đó và lập lại danh sách vật tư. D07 có thể nghiệm thu phần thu thập báo giá riêng dù bộ tối ưu tường hiện còn chặn vữa trộn tại chỗ. [Hệ tường](../../../data/catalog/wall_systems.csv) · [Cấp phối VU02](../../../data/catalog/material_relations.csv) · [Giới hạn bộ tối ưu](../../../reports/demo_0511/optimizer/HANDOFF.md)

| Ưu tiên | Mã cần xác minh | Đầu mối và căn cứ chọn | Chứng từ còn cần |
|---|---|---|---|
| P0 | GK01 | CBG-40AD431D8F An Thịnh và CBG-6DDCD9EF88 Tiên Sơn Hà Tây được ghi ở G06 cho GK01 | Phiếu giá gạch đúng kích thước, mác và đơn vị bán. Nếu bán pallet/kiện, cần số viên mỗi kiện và điều kiện xử lý kiện lẻ. |
| P0 | XM01 | CBG-991233626E Vicem Tam Điệp xuất hiện ở G07; CBG-D01015FA3A Vicem Bút Sơn ở G06 | Xác nhận đúng PCB30, biến thể và khối lượng bao, đơn vị tấn/bao, ngày giao và điều kiện tại điểm nhận. Giữ riêng từng biến thể trên chứng từ. |
| P0 | CA02 | CBG-6B833AED83 Bãi Cầu Trung Hà và CBG-64FCA58718 Bãi Tàm Xá có dấu vết cung ứng cát tại G06 **cho CA01** | Hỏi riêng có cung cấp cát vàng xây trát đúng yêu cầu CA02 hay không. Cần quy cách, đơn vị m³ và giao nhận. Giá CA01 không được chuyển sang CA02. |
| P1 | BT03 nếu hồ sơ ghi một mác M250 và chọn thương phẩm | YP1187911965 Bê Tông Chèm Hà Nội và YP1188023466 Bê Tông Hùng Phát có hồ sơ ngành tại Hà Nội | Trạm giao, quy cách, lượng tối thiểu mỗi chuyến, cước, bơm, thời gian đổ và thời hạn áp dụng. Hỏi riêng các phụ phí. |
| P1 | GN01 nếu hồ sơ có hệ gạch nung | YP119334495 MEGABUILD và YP721719 Vật liệu xây dựng Đông Anh là đầu mối để hỏi hàng | Xác minh sản phẩm, đại lý, số lượng và phiếu giá. Ba cặp cung ứng mẫu của GN01 không chứng minh hàng thật tại hai đầu mối này. |

Mười mã trên là mười **đầu mối đề xuất**. Địa chỉ trên Maps, tên ngành hoặc việc có mặt trong một công bố chỉ giúp tìm đúng nơi để hỏi. Chưa liên hệ nhà cung cấp. [Danh bạ NCC](../../../data/catalog/suppliers.csv) · [Đầu mối từ công bố Hà Nội](../../../reports/demo_0511/06_demo_actual.manifest.json)

## Tiêu chí nhận một dòng mua

1. Người phụ trách đo bóc chốt `analysis_id`, công tác nguồn, quy cách, định mức và lượng theo đúng phương án. Tách lượng theo định mức, hao hụt bổ sung và lượng đặt sau quy đổi/đóng gói. Thiếu căn cứ quy đổi thì giữ thiếu.
2. Người phụ trách vật tư gắn chứng từ của NCC cụ thể với mã và SKU thực bán. Ghi đơn vị, hệ số đổi có nguồn, bậc lượng hoặc tối thiểu, số lượng đặt, điểm nhận, VAT, cước, bốc dỡ/bơm nếu có, ngày báo, hạn hoặc xác nhận còn áp dụng đúng ngày đặt, khả năng cung cấp và thời gian giao. Nếu chưa rõ điều kiện, dòng ở trạng thái cần xác minh.
3. Người kiểm độc lập lần từ dòng phương án về đúng chứng từ và bản khối lượng. Gom phí theo đúng đơn/chuyến. Chỉ so các báo giá cùng cơ sở. Một báo giá hợp lệ đủ để mô tả một lựa chọn; cần thêm báo giá cùng cơ sở để so. Mục tiêu thu thập là 2–3 báo giá/vật liệu trọng tâm.
4. Đạt D07 cho luồng P0 khi **3/3** mã phải mua đều qua các bước trên. Điều kiện chạy và lưu được phương án D10 được theo dõi riêng trong [hợp đồng phương án](SCENARIO_CONTRACT.md).
