# N02 — Prompt giao dev sau khi điều phối cấp lượt

**Trạng thái: prompt đã chuẩn bị, CHƯA KÍCH HOẠT.** Chủ đồ án đã chốt BA ngày 03/11/2026 trong chat X01/N01/N02. Không sửa mã/test hoặc chạy test chỉ vì đọc prompt này; phải có lượt triển khai do điều phối cấp, khóa file và thống nhất điểm nối Q01 trước.

## Nhiệm vụ

Đọc `CLAUDE.md`, `docs/review/DIEU_PHOI_20261103.md`, [N02_CHUAN_BI.md](N02_CHUAN_BI.md), [N01_NGHIEM_THU.md](N01_NGHIEM_THU.md), mã/test **hiện tại**. Sửa đúng N02: chỉ bỏ bản sao **bảng nguyên cùng phạm vi có chứng cứ**, giữ hai tầng độc lập cùng nội dung và giữ bội số dòng. Không dùng tổng kg hay nội dung đơn thuần làm căn cứ phạm vi; không chỉ bỏ điều kiện `and row.mark`.

Nguồn scope: tiêu đề bảng tường minh khi rõ tập tầng/vùng/nhóm cấu kiện và nghĩa tổng; hoặc ánh xạ có người kiểm xác nhận. Không suy từ tọa độ, layer, tên C1 hay mặt bằng gần nhất. Scope khác/thiếu/mâu thuẫn không được khử trùng. Thiếu scope có nghi lặp: giữ rows/evidence, hiện số tạm nếu có nhưng không báo tổng/vật tư/giá liên quan là hoàn chỉnh; dùng hợp đồng partial của Q01. Request cũ vẫn nhận, không dedup thêm danh sách row đã gửi, không tự phục hồi dữ liệu reader cũ đã bỏ, không tự ghi đè kết quả đã xác nhận. Không khử trùng xuyên Drawing/file/revision/lần gửi.

## Phạm vi sửa và cách chia lượt

- File lõi dự kiến: `src/optimat/rough/rebar.py` (định danh bảng, nguồn scope, so bảng có bội số, `read_rebar_schedules`; metadata tùy chọn trong RebarRow nếu được thống nhất), `tests/test_rough_rebar.py`; bằng chứng riêng `reports/n02/`.
- `rough/takeoff.py`, `rough/steel.py`, `api/main.py`, `rough/models.py`, Q01 và test tích hợp liên quan **chỉ được ghi nếu điều phối phân rõ đoạn/file sau khi writer hiện hành bàn giao**. Trước đó đọc caller và lập danh sách trường cần truyền/điểm nối partial; không tự viết engine hoặc state mới để né khóa. Cần đổi file khác phải được điều phối bổ sung phạm vi trước.
- Bắt buộc giữ đường tùy chọn có xác nhận qua input/API trong kết quả N02 đầy đủ; không thay nó bằng sửa evidence chuỗi. Không bắt caller cũ cung cấp metadata, không đổi DB, không làm UI/BOQ mới, không sửa parser N01, CSV, A01, N03, J03 hoặc kế hoạch/NHAT_KY/SPRINTS chung.
- Nếu vượt một ngày dev, tách **N02-a** (reader, phạm vi tiêu đề và bản sao bảng) và **N02-b** (ánh xạ xác nhận, request round-trip, partial qua các caller) theo cấp lượt của điều phối. N02-a chưa đủ để nghiệm thu toàn N02; không đánh hoàn thành khi nghi lặp chỉ có cảnh báo nhưng tổng vẫn báo đủ.
- Snapshot/hash trước sửa và đọc lại đúng vùng ngay trước patch. Nếu khác snapshot do writer khác thì báo điều phối, không ghi đè/hoàn tác. Diff từng đoạn nhỏ; không commit/stage/reset công việc chung.

## Ca nghiệm thu cụ thể

Tất cả fixture dưới đây **SYNTHETIC**, không là đáp án công trình. Ca số học dùng Ø16 với nguồn kg/m hiện có = 1.58, 10 thanh × 2000 mm → **31.60 kg**; không thêm nguồn kg/m mới. Mỗi bảng có tiêu đề/định danh riêng; có thể dùng bảng tối giản để kiểm lượng, còn hai fixture lịch sử giữ 5 dòng/bảng để kiểm hồi quy.

| Ca | Đầu vào và điều kiện | Kỳ vọng |
|---|---|---|
| T1 bản sao có mark | Hai bảng nguyên cùng Drawing, scope tổng dầm tầng 1 rõ và giống nhau; mỗi bảng một dòng trên, mark 1 | 1 dòng, 31.60 kg; cảnh báo truy được bảng giữ/bỏ và nguồn scope |
| T2 bản sao thiếu mark | Như T1 nhưng mark trống | Vẫn 1 dòng, 31.60 kg; thiếu mark không làm cộng hai lần |
| T3 hai tầng độc lập | Một bảng scope tầng 1, một bảng tầng 2, cùng C1/mark/Ø/L/số lượng | 2 dòng, 63.20 kg; hai nguồn evidence còn đủ, không xóa một tầng |
| T4 bội số trong bảng | Một bảng có hai dòng hợp lệ giống nhau: 63.20 kg; bản sao nguyên bảng cùng scope | Giữ 2 dòng, 63.20 kg; không set còn một dòng hoặc cộng thành 126.40 kg |
| T5 bằng kg không đủ | Hai bảng cùng scope: A 10×2 m; B 20×1 m, đều Ø16 và 31.60 kg; hoặc khác shape | Không gộp hai bảng; giữ nguồn, báo cùng scope khác nội dung/chờ xác nhận, không công bố tổng đủ |
| T6 thiếu scope | Hai bảng tiêu đề chung, cùng nội dung, không ánh xạ; thử cả có/không mark | Giữ 2 dòng/63.20 kg số tạm, nghi lặp/partial; không gộp. Fixture lịch sử 5 dòng/bảng phải giữ 10 dòng trong ca riêng này |
| T7 nhập xác nhận | T6 có ánh xạ đúng bảng/phiên bản, cùng scope tổng, nguồn + người xác nhận | Giữ 1 bộ; request/response/lưu input round-trip giữ metadata và dấu vết xác nhận; không cần UI |
| T8 xung đột phạm vi | Tiêu đề tầng 1 nhưng ánh xạ tầng 2 không có xác nhận sửa kèm lý do | Không tự chọn nguồn thắng/gộp; giữ hai chứng cứ và lý do chờ. Xác nhận sửa hợp lệ phải có dấu vết |
| T9 request cũ | JSON chỉ có danh sách RebarRow cũ, không scope/table ID | Nhận hợp lệ; giữ row/giá trị/evidence/missing; không thêm dedup trên danh sách, không báo hoàn tất nếu có nghi lặp chưa giải quyết |
| T10 namespace nguồn | Hai Drawing hoặc revision khác có bảng giống hệt; ánh xạ thuộc revision cũ | Không khử trùng xuyên nguồn; không áp ánh xạ cũ vào revision mới. Ngoài phạm vi tự xử lý thì báo rõ |
| T11 phạm vi chồng | Bảng tổng tầng 1–2 và bảng riêng tầng 1; hoặc một bảng chỉ là phần của bảng khác | Không coi scope bằng nhau/không tự trừ dòng; giữ pending/partial, chưa có tổng đủ |
| T12 nghĩa số lượng | Bảng đã tổng cho tầng 1–2: 10 thanh tổng; bảng mẫu chỉ ghi 10 thanh/mẫu chưa rõ số mẫu | Bảng tổng 31.60 kg, không nhân hai; bảng mẫu chưa rõ không được tự nhân/gộp như tổng |
| T13 ổn định | Đảo thứ tự các bảng/dòng T1–T4 và tính lại cùng input | Tổng/bội số không đổi, không trừ thêm; nguồn giữ/bỏ luôn truy được (không bắt chuỗi cảnh báo giữ cùng thứ tự) |
| T14 thiếu dữ liệu | Bản sao một bảng thiếu L/Ø/số thanh hoặc đọc chưa đủ, khác missing/nội dung nguồn | Không dùng kg=None hay các giá trị None giống nhau làm bằng chứng bảng tương đương; không xóa phần thiếu, không biến tổng thiếu thành đủ |

Hai test lịch sử `test_duplicate_table_counted_once` và xfail `test_duplicate_table_without_mark_counted_once`: bổ sung chứng cứ scope hợp lệ cho **ca bản sao**, giữ kỳ vọng 5 dòng; đồng thời thêm ca tiêu đề chung không scope giữ 10 dòng. Không chỉ đổi kỳ vọng/xóa test để đạt. Chỉ bỏ đúng xfail N02 sau khi lỗi được kiểm đạt; giữ xfail N03. Giữ toàn bộ ca N01 (dấu hỗn hợp hợp lệ/sai nhóm, một dấu cũ, mm/m, recorded kg, số lượng, evidence/missing), dừng TỔNG, thép theo bảng khác hàm lượng và tích hợp `steel_works/compute_rough`. Row độc lập phải được cộng đúng; nghi lặp/partial phải đi tới tổng/vật tư liên quan theo Q01, không chỉ cảnh báo trong reader.

## Kiểm tra và bàn giao sau cấp lượt

1. Chỉ chạy trọng tâm khi điều phối cấp lượt: dự kiến `pytest tests/test_rough_rebar.py tests/test_rough_steel.py tests/test_rough_agent.py` và test caller/Q01 thực sự bị ảnh hưởng được cấp. Bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, đặt OPTIMAT_NO_DOTENV=1; không DB thật/test. Nếu TestClient cần loopback, dùng bằng chứng môi trường trong reports/c01_regression và xin thực thi ngoài sandbox đúng ca qua cơ chế require_escalated, không sửa app để né môi trường.
2. Chưa full suite/DB khi chưa được cấp lượt riêng; không chỉnh theo dữ liệu test công trình. Đọc log và mã thoát pytest riêng, không nhầm lỗi in log với kết quả test. Không tự đánh da_kiem hay nghiệm thu.
3. Lưu snapshot/hash/diff/log/result dưới `reports/n02/`; manifest nguồn trước/sau, danh sách file thực sự đổi, test chạy/không chạy, trước–sau T1/T3/T6/T9, partial còn thiếu. Bàn giao metadata/compatibility và ca chưa đủ bằng chứng; đề xuất dòng nhật ký để điều phối ghi. Không sửa tài liệu chung.

**Cổng kết thúc:** dev ghi “CHỜ REVIEW”; điều phối review độc lập và cấp hồi quy. Chốt BA không thay cho nghiệm thu kỹ thuật, xác nhận dữ liệu thực hoặc cấp quyền ghi file đang do phiên khác giữ.
