# Thử trợ lý bằng OpenAI trên bộ kiến trúc và kết cấu nhà Sang

Ngày 03/11/2026. Hồ sơ VN002 có hai bản DXF ở Hải Dương. Đã đối chiếu SHA-256 cả hai tệp với bản bóc CAD lưu trong dự án. Phạm vi gồm **52 dòng công tác và 7 dòng vật tư**. Bản bóc có trạng thái `chua_kiem`; các dòng giữ `checked=false` và `partial=true`. Xem [nguồn và phiên bản đầu vào](provenance.json).

## Lượt gọi thật

Trong khoảng 23:11:20–23:11:43 giờ Việt Nam, trợ lý staging gửi đúng một yêu cầu tới OpenAI chính thức. Chỉ gửi dữ kiện vật tư rút gọn, không gửi bản vẽ, ảnh, tên công trình, mã dự án hoặc địa chỉ. OpenAI trả HTTP 200, model `gpt-5.6-luna`, đầy đủ bảy dòng. Lượt này chạy trực tiếp hàm tư vấn; API trên cổng demo chưa có tuyến trợ lý toàn phần thô tại thời điểm kiểm. [Biên nhận](live_receipt.json) · [Câu trả lời thật](reply.openai.json)

| Nhóm trong bản bóc | Kết quả tư vấn |
|---|---|
| Gạch xây | Chưa xác định cấu tạo tường để chọn mã. |
| Vữa trát | Cần nền trát, chiều dày và định mức tương ứng. |
| Bê tông | Chưa đủ căn cứ chốt mác và vật tư/cấp phối. |
| Vữa cán nền | Thiếu chiều dày và định mức theo lớp. |
| Thép chịu lực | Bản bóc hiện tại chưa chia được theo quy cách, đường kính. Cần đối chiếu bảng thống kê kết cấu. |
| Dây thép buộc | Tra được mã **TH10**, dây thép buộc 1 ly. Danh mục thực tại thời điểm thử có **0 nguồn báo giá** cho mã này. AI giữ mã ở mức gợi ý kiểm và không xác định lượng đặt mua. |
| Cốp pha | Chưa có căn cứ chọn loại ván và quy cách mua. |

Lượng mua, tổng chi phí và lịch giao chưa xác định. Các hạng mục không xuất hiện trong bộ đầu vào này, chẳng hạn một dòng chống thấm đã định được vật liệu, cần hồ sơ khác để nghiệm thu riêng.

## Hai lỗi đã tái hiện

1. Bộ kiểm đầu vào từ chối ba dòng trừ diện tích cốp pha sàn. Đã sửa mã staging để giữ đúng **−0,194; −0,290; −0,194 m²**, không biến khoản trừ thành nhu cầu mua. Đầu vào sau sửa giữ đủ 52 dòng. [Kết quả kiểm trước lượt gọi](offline_advisor_tests.log)
2. Bộ kiểm đầu ra từ chối câu trả lời thật vì `TH10` chứa chữ số. Hai lần xuất hiện đều đúng phạm vi, ở phần tóm tắt và dòng dây buộc. Vì thế lượt gọi đầu có phản hồi của nhà cung cấp nhưng chatbot chưa hiển thị được câu trả lời. Phép kiểm hồi quy phải dùng nguyên JSON đã lưu, đồng thời chặn `TH10` ở dòng gạch, `TH100` và giá tự thêm. Kết quả phát lại được ghi riêng với biên nhận gọi thật.

## Kiểm bản sửa lúc 23:31

Đã phát lại nguyên phản hồi OpenAI trên bản sửa độc lập của phiên 04. Cả 7 dòng được chấp nhận, đúng mã TH10 ở dòng dây buộc, 6 dòng chưa có mã và 0 báo giá mua. Sáu biến thể sai đều bị chặn, gồm đặt TH10 ở dòng gạch, sửa mã thành TH100, thêm tiền tố hoặc hậu tố, tự thêm giá 12 triệu và hứa giao trong 7 ngày. Lượt phát lại không gọi OpenAI và không áp dụng lựa chọn vào dự án.

[Kết quả trên bản độc lập](replay_isolated.json) · [Bản vá bộ kiểm](guard.proposed.patch)

## Kiểm lại trên mã staging chung

Phiên 12 đã nhập bản sửa vào module tư vấn. Phiên 04 kiểm độc lập trên bản `E243796E`: 25 ca kiểm logic đạt trong 4,15 giây, mã nguồn giữ nguyên suốt lượt kiểm. Sau đó, câu trả lời thật ban đầu đã qua chính bộ kiểm staging chung, nhận đủ 7 dòng và chỉ gợi ý TH10 cho dây buộc. Sáu biến thể sai tiếp tục bị từ chối. Mã nguồn cũng giữ nguyên trong lượt phát lại, với 0 cuộc gọi OpenAI mới. Đây là kết quả kiểm logic tư vấn; nghiệm thu thao tác trên trình duyệt qua API demo vẫn là bước riêng. [Biên nhận phát lại trên staging chung](replay.json) · [Log 25 ca kiểm](rebased_offline_tests.log)

## Kiểm trên mã chính ngày 04/11

Đã phát lại nguyên đầu vào và nội dung trả lời từ lượt gọi thật trên `src/optimat/agent/material_advisor.py`, SHA-256 `463E8F88B2C92958B6217CDE60EA419ECDBB345EF2569E912094D2ADB300210E`. Kiểm hash nguồn trước và sau trùng nhau. Thử nghiệm dùng danh mục cục bộ và đối chiếu dữ kiện của cả 7 dòng với biên nhận gốc. Cả 7 câu tư vấn được nhận, chỉ TH10 được đề xuất ở dòng dây buộc, 6 biến thể sai bị chặn. Không có cuộc gọi OpenAI hoặc kết nối DB. Bước này kiểm logic của mã chính; chưa kiểm giao diện qua tuyến HTTP đang chạy. [Biên nhận phát lại trên mã chính](replay_canonical.json)
