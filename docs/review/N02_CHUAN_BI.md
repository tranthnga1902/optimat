# N02 — Chuẩn bị phân biệt bảng thép lặp và phạm vi độc lập

03/11/2026 — **BA ĐÃ ĐƯỢC CHỦ ĐỒ ÁN CHỐT trong chat này; CHỜ ĐIỀU PHỐI CẤP LƯỢT DEV, chưa triển khai/nghiệm thu N02**. N01 đã đạt kỹ thuật theo [kết luận điều phối](N01_NGHIEM_THU.md). Lượt này chỉ cập nhật tài liệu và chuẩn bị [prompt giao dev](N02_GIAO_DEV.md); không sửa source/tests/data/DB, không chạy test. Không đụng các phần A01/Q01/BOQ đang có writer khác.

## Hiện trạng và dữ liệu phạm vi

| Điểm đọc mã hiện tại | Có / thiếu |
|---|---|
| `src/optimat/rough/rebar.py:read_rebar_schedules:225–242` | `seen` dùng chung mọi bảng trong **một Drawing**; khóa `(element chuẩn hóa, mark chuẩn hóa, Ø, chiều dài cắt, tổng thanh)`. Có mark thì dòng sau bị bỏ; không mark thì giữ cả hai. Không có tầng/phạm vi hay danh tính bảng trong khóa; không xét shape và các missing. Có thể bỏ nhầm hai tầng độc lập hoặc hai dòng hợp lệ giống nhau trong cùng bảng. Không dùng tổng kg hiện tại, nhưng khóa nội dung vẫn chưa đủ chứng minh cùng phạm vi. |
| `rebar.py:RebarRow:39`, `read_table:140` | Có tiêu đề bảng, số thứ tự dòng, tên cấu kiện, mark/shape, số thanh/cấu kiện, giá trị tính và evidence chuỗi gồm tọa độ/layer/ô gốc. Chưa có scope tầng/vùng/instance, file/phiên bản, table ID hay quan hệ bản sao được xác nhận. C1/mark 1 có thể tái sử dụng ở nhiều tầng; tên bảng hay layer giống nhau không chứng minh phạm vi giống nhau. |
| `src/optimat/drawing/dxf_reader.py:TextItem:52`, `Drawing:97`; `drawing/sheets.py:View:43`, `find_views:100` | Text có tọa độ/layer; Drawing không có trường file ID; View có tiêu đề/khung có thể hỗ trợ tìm ngữ cảnh, nhưng rebar chưa ghép scope từ View. Tọa độ phân biệt vị trí bản sao, không phân biệt phạm vi áp dụng. Tiêu đề tầng rõ là chứng cứ tiềm năng; gần một mặt bằng hay cùng file không tự chứng minh cùng tầng. |
| `src/optimat/rough/takeoff.py:structural_parts:469–495`, caller `rough_from_drawing:442`; `api/main.py:225` | Đọc từng Drawing rồi nối rows, không khử trùng xuyên file. `RoughRequest.rebar` nhận danh sách row. `file` ngoài request không đủ chỉ nguồn từng bảng kết cấu trong danh sách. Caller tương lai cần truyền scope/nguồn đã xác định nếu BA chọn cách này; không tự sửa takeoff/API lúc đang khóa writer. |
| `src/optimat/rough/steel.py:schedule_works:15–34` | Gom theo mã công tác + tên cấu kiện, cộng kg và giữ evidence; không chia tầng. N02 phải giữ đủ hai bộ row độc lập trước bước cộng; tách trình bày tầng/Ø là hợp đồng liên quan Q01/J03, không mở rộng BOQ trong lượt này. |

[M01](../M01_PHAM_VI_PHAN_THO.md) PT39/mục 2.6 ghi lỗi bảng thép và mất Ø; số “2 xfail” là hiện trạng lịch sử trước N01, không dùng thay kết luận N01 mới. M01 mục 3–4 yêu cầu cùng phạm vi/đơn vị, không mất phần thiếu và không đổi mẫu số để tăng tỷ lệ; PP-20 tách cách tạo dữ liệu khỏi A/B/C/D. Không đổi nhãn dữ liệu hay coi bảng thiếu scope là đáp án đã kiểm.

## Quy tắc BA đã chốt

1. **Bản sao cùng phạm vi:** phải có chứng cứ cùng tập cấu kiện/vị trí/tầng, cùng phiên bản thiết kế và cùng nghĩa số lượng (đã nhân cấu kiện/tầng hay chưa). Hai bản ở hai tọa độ có thể là bản sao; hai file có thể là hai nguồn độc lập. Không kết luận chỉ bằng tên, khoảng cách, nội dung hay tổng kg.
2. Chỉ khi scope đã xác định trùng nhau **và** toàn bộ bảng tương đương mới bỏ một bản sao; lưu cảnh báo chỉ rõ nguồn giữ/nguồn bỏ. So cấu trúc bảng bằng tập dòng có **bội số** (không set làm mất hai dòng giống nhau), giữ shape, số lượng, thông tin thiếu cần thiết; số hiệu trống không ngăn nhận bản sao nếu hai điều kiện trên đủ. Hai dòng giống nhau trong một bảng vẫn giữ đúng bội số.
3. **Hai tầng/vùng/cấu kiện độc lập:** giữ cả hai bảng kể cả giống toàn bộ số liệu, mark hoặc kg. Ví dụ SYNTHETIC: một bảng có một dòng 10 thanh × 2 m × 1 kg/m = 20 kg; hai bản sao cùng scope → 20 kg, tầng 1 và tầng 2 độc lập → 40 kg. Bảng đã ghi tổng cho tầng 1–2 không tự nhân thêm hai lần.
4. **Scope chưa rõ / bảng chỉ trùng một phần / khác phiên bản hoặc số lượng:** không tự xóa hoặc tự cộng như tổng hoàn chỉnh. Giữ rows/evidence, cảnh báo cần xác nhận và không công bố tổng đủ; cơ chế pending/partial phải thống nhất với Q01, chưa tự thêm trạng thái/schema. Khác revision cần người dùng chọn nguồn có hiệu lực, không tự chọn bằng nội dung.

## Phương án BA tối thiểu đã duyệt

Nguồn quyết định: yêu cầu trực tiếp của chủ đồ án trong chat này ngày 03/11/2026: “Chốt phương án BA này cho N02.” Quyết định phê duyệt hành vi dưới đây, **không phải cấp lượt sửa mã/test**. Vị trí trường metadata, danh sách file được ghi và cách nối partial theo Q01 phải được điều phối thống nhất trước triển khai; không hỏi lại phạm vi BA đã chốt.

**Giới hạn một lượt:** chỉ nhận bản sao của bảng nguyên trong cùng một Drawing/phiên bản đầu vào. Không khử trùng xuyên file, giữa các lần gửi request hoặc giữa các revision; không giải bảng phân mảnh và không thiết kế giao diện xác nhận mới. Phạm vi khác nhau luôn giữ riêng. Nội dung chỉ dùng kiểm tương đương **sau khi** biết cùng phạm vi.

### Lấy phạm vi từ đâu

1. **Tự đọc chỉ khi ngay tiêu đề bảng nói rõ phạm vi**, ví dụ “THỐNG KÊ THÉP DẦM TẦNG 1”. Tách tầng + nhóm/vùng cấu kiện được ghi tường minh và lưu nguyên chữ làm chứng cứ. Hai bảng “DẦM TẦNG 1” và “DẦM TẦNG 2” có phạm vi khác nhau. Không suy tầng từ C1/D1, layer, tọa độ, bảng gần mặt bằng nào hay việc chỉ thấy một tầng trong file. Tiêu đề chung “THỐNG KÊ THÉP” không đủ; chữ mâu thuẫn/không phân tích được giữ chưa rõ. Nếu tiêu đề chỉ nói một loại điển hình mà chưa rõ số cấu kiện/phạm vi áp dụng, cũng chưa đủ để tự gộp.
2. **Đường bổ sung tối thiểu là ánh xạ bảng → phạm vi do người kiểm xác nhận qua input/API**, không cần chờ UI: chọn các bảng là bản sao cùng phạm vi hoặc xác định chúng áp dụng cho các tầng/vùng riêng. Lưu giá trị, trích nguồn và người xác nhận theo M01 QĐ-19; không sửa chuỗi evidence để giả có xác nhận. Nếu thông tin nhập mâu thuẫn chữ gốc thì giữ dấu vết cả hai, yêu cầu xác nhận sửa có lý do; không tự chọn nguồn thắng.
3. Dùng **danh tính bảng** riêng với **phạm vi áp dụng**. Danh tính bảng có thể dựa vào Drawing của lượt đọc + vị trí tiêu đề/chỉ số bảng để gắn đúng ánh xạ và truy vết; nó không chứng minh hai bảng cùng phạm vi. Khi gửi lại, phải đối chiếu đúng phiên bản nguồn/bảng, không áp ánh xạ cũ lên file mới chỉ vì tọa độ giống nhau.

Khóa phạm vi đã chốt về nghĩa: trong namespace của Drawing/phiên bản, gồm tập tầng/vị trí áp dụng, nhóm/vùng cấu kiện và nghĩa số lượng (**tổng của cả phạm vi** hay **một mẫu cần nhân**). Chỉ nhận đường tổng đã xác định cho tự bỏ bản sao ở lượt tối thiểu; bảng mẫu hoặc “tầng 1–2” chưa rõ đã nhân hay chưa giữ chờ xác nhận. Không cần liệt kê từng instance nếu bảng thiết kế áp dụng cho cả một loại. Thiếu phần khóa có ảnh hưởng tới phân biệt phạm vi thì không coi hai scope bằng nhau. Tên bảng giống nhau không thay cho khóa này.

### Thiếu phạm vi và request cũ

| Tình huống | Quyết định BA đã chốt |
|---|---|
| Cùng scope có chứng cứ, hai bảng nguyên tương đương, kể cả thiếu mark | Giữ một bộ row; ghi bảng giữ/bảng bỏ và chứng cứ phạm vi. Dùng bội số dòng, không set; thiếu mark không cản gộp bảng nguyên. |
| Scope tầng 1 và tầng 2 độc lập, nội dung giống nhau | Giữ cả hai; tổng lượng đủ số của hai bảng được cộng, không khử trùng toàn cục theo mark/nội dung. Không cần đổi tên C1 ở từng tầng để né khóa. |
| Bảng thiếu scope hoặc scope mâu thuẫn | Không tự xóa row. Nếu có bảng giống/chồng nội dung có thể là bản sao, đánh dấu **nghi lặp, chờ xác nhận**; giữ evidence hai nguồn. Tổng số học có thể hiện như số tạm đã cộng, nhưng phần liên quan chưa được báo đủ/đã xác nhận; không coi lượng mua hoặc giá tương ứng là hoàn chỉnh. Cách biểu diễn partial dùng hợp đồng Q01 đã thống nhất, không tạo trạng thái riêng. Không kết luận mọi bảng thiếu scope đều là bản sao. |
| Request cũ chỉ có `rebar: list[RebarRow]`, không có metadata phạm vi | Vẫn nhận, không bắt sửa payload, không yêu cầu locale/schema DB/UI mới. Danh sách đã gửi là dữ liệu được cung cấp: không chạy thêm dedup theo nội dung và không phục hồi các row đã bị reader cũ bỏ trước đó. Giữ giá trị và evidence/missing sẵn có; nghi lặp mà chưa có xác nhận thì xử lý tạm/partial như trên. HTTP 200 hay giữ số cũ không chứng minh đầy đủ phạm vi. |
| Auto reader được nâng cấp đọc lại bản vẽ cũ | Giữ đường gọi cũ không metadata. Tiêu đề rõ thì dùng phạm vi đọc được; thiếu thì giữ các bảng và cảnh báo nghi lặp. Số có thể tăng so với reader cũ đã bỏ nhầm hai tầng; đây là sửa lỗi khử trùng, không cam kết tái tạo số sai cũ. Không tự ghi đè kết quả đã lưu/xác nhận; muốn tính lại phải là lần tính lại có chủ đích. |
| Bảng khác revision, cùng scope nhưng chỉ trùng một phần, hoặc cùng nội dung nhưng nghĩa số lượng chưa rõ | Giữ nguồn và yêu cầu chọn/xác nhận; không tự hợp hoặc bỏ bằng fingerprint. Ngoài phần tự xử lý của lượt tối thiểu. |

**Ảnh hưởng hợp đồng tối thiểu đề xuất:** tái dùng RebarRow/evidence/missing/notes và kiểu trả về nếu đủ; metadata tùy chọn chỉ cần danh tính bảng, khóa phạm vi và chứng cứ/cách xác định phạm vi, có người xác nhận khi nhập tay. Caller không truyền vẫn hợp lệ. Chốt vị trí metadata/ánh xạ cùng điều phối trước khi sửa trường hoặc caller, không parse ngược chuỗi evidence để tính. Không thể chỉ sửa `and row.mark` mà đáp ứng phương án này; nếu reader + truyền metadata + partial vượt một ngày thì chia lượt theo hợp đồng đã duyệt.

**Cổng triển khai còn lại:** điều phối cấp lượt ghi file, thống nhất metadata/caller và nối nghi lặp/partial với Q01. Giới hạn cùng Drawing, nguồn phạm vi, tương thích request cũ và hành vi không xóa khi chưa rõ đã được chủ đồ án duyệt. Không cần người kiểm bịa tầng cho fixture chung; chưa được tự triển khai hoặc chạy test khi điều phối chưa cấp lượt.

## Diff nhỏ và ca kiểm dự kiến (chưa thực hiện)

- Sau khi điều phối cấp lượt: sửa cục bộ `read_rebar_schedules` theo đơn vị **bảng + scope**, thay khử trùng dòng toàn cục; tái dùng `read_table`, parser N01, evidence/cảnh báo và kiểu trả về khi đủ nghĩa. Chỉ thêm trường scope/nguồn hoặc tham số nếu chứng minh thật sự thiếu, báo điều phối trước đổi hợp đồng/caller. Không chỉ xóa điều kiện `and row.mark`; không dedup bằng tổng kg hay nội dung đơn thuần.
- Test hiện có `tests/test_rough_rebar.py:test_duplicate_table_without_mark_counted_once:105` (xfail N02) và `test_duplicate_table_counted_once:127` dùng hai bảng tiêu đề chung **không khai báo scope**. Sau BA, bổ sung tiêu đề phạm vi tường minh hoặc ánh xạ có xác nhận cho fixture bản sao, giữ kỳ vọng 5 dòng; thêm riêng fixture chung cũ giữ 10 dòng + cảnh báo nghi lặp/partial. Không giả định hai bảng cùng nội dung luôn cùng phạm vi; không chỉ đổi kỳ vọng để đạt. Chỉ bỏ đúng xfail N02 sau test đạt; giữ N03.
- Thêm SYNTHETIC: bản sao có/không mark cùng scope; hai tầng cùng nội dung/mark giữ 10 dòng và gấp đôi lượng đủ dữ liệu; hai dòng giống nhau trong một bảng giữ bội số; hai bảng cùng kg nhưng khác Ø/shape/chiều dài/số lượng không gộp; scope thiếu giữ evidence và lý do chờ; bảng trùng một phần/khác revision không tự bỏ; đảo thứ tự/tính lại không đổi tổng; bảng áp dụng nhiều tầng đã nhân không nhân tiếp. Giữ toàn bộ ca N01, dừng TỔNG, thiếu kích thước/missing, tích hợp `steel_works/compute_rough` kiểm lượng và bằng chứng hai nguồn còn đủ. Xuyên file chỉ thêm ca/triển khai khi cổng phạm vi đã chốt.
- Bổ sung tương thích: request `rebar` cũ round-trip giữ row/giá trị; thiếu metadata không bị từ chối. Metadata nhập tay mâu thuẫn tiêu đề không tự thắng; ánh xạ cũ không áp vào revision mới; tiêu đề chung + layer/tọa độ gần nhau vẫn chưa rõ scope. Bảng tổng tầng 1–2 và bảng riêng tầng 1 là vùng chồng, không coi scope bằng nhau hay tự cộng thành tổng đủ.

Bàn giao: BA đã chốt; [prompt dev](N02_GIAO_DEV.md) có phạm vi sửa và ca nghiệm thu cụ thể, chưa gửi thực thi. Chưa có diff mã hay kết quả test mới. Dòng nhật ký đề xuất: “03/11/2026 — Chủ đồ án chốt BA N02: scope từ tiêu đề tường minh hoặc ánh xạ có xác nhận; thiếu scope giữ dữ liệu/partial, request cũ vẫn nhận; đã chuẩn bị prompt, chờ điều phối cấp lượt dev/test, chưa sửa mã hay nghiệm thu.”
