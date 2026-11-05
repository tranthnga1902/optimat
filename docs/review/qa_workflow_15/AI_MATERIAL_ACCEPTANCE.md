# Nghiệm thu AI hỗ trợ lựa chọn vật liệu — chuẩn bị

Theo mục Vai trò AI đã sửa trong `docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md`: **tư vấn toàn bộ phần thô**, thay thế phạm vi nhóm tường trước đây. Tất cả ca **NOT_RUN**. QA15 chỉ docs, chưa có release runtime. Không full/TestClient/browser/API restart hoặc thử lại upload Tân Bình. Hỏi công thức dòng khối lượng là chức năng phụ, không phải cổng demo chọn vật liệu.

Luồng cần chứng minh: khối lượng đã kiểm + yêu cầu tiếng Việt → backend lọc catalog theo ràng buộc → AI so sánh/đề xuất có nguồn → người dùng xác nhận → áp dụng đúng snapshot. Backend quyết định mã hợp lệ và số liệu; lời giải thích không tạo mã/giá/U/thời gian hoặc tự đổi thiết kế.

**Chỉ đạo mới nhất thay vị trí “Chọn vật liệu” trong các mô tả trước:** khối lượng đã kiểm → thẳng `/toi-uu` → phương án nháp toàn phần thô → so sánh với AI → user xác nhận **cả phương án** và lưu/áp dụng. `/dieu-chinh` và xem giá là tùy chọn, không buộc xác nhận từng dòng/chọn tay bất kỳ vật liệu trước khi nhận phương án. Proposed chưa approved vẫn giữ nguyên; người dùng có thể hỏi AI ngay trên Phương án tối ưu. Phân biệt thuật toán NSGA-II chuyên tường với đề xuất có điều kiện cho nhóm khác; không cần mở rộng thuật toán mới để hiển thị các đề xuất đó.

Kế hoạch làm rõ: “Xem tư vấn” dùng `approvedWork`, không yêu cầu `materialRevision` hoặc đủ giá/mã đã chọn; candidate lookup chỉ bổ sung bản nháp. “Chốt bảng mua” chỉ đưa dòng đủ quy cách, cơ sở lượng mua và điều kiện giá vào phần sẵn sàng mua; phần thiếu vẫn hiển thị. AI23/24/26 phải kiểm riêng hai cổng này, không dùng một boolean ready để đồng nhất xem nháp với mua được.

01 chốt hai mode: advice-allrough từ **same approvedWork**, giữ gate quantitychecked; apply wholeplan/giá mua/procurement cần revision và điều kiện tương ứng. Wall no-solution không chặn advice phi tường. AutoFill chỉ unique spec có nguồn trace, giữ override; confirm wholeplan không lấp missing giả và geometry change phải recheck. Owner02 menu/guards/producer;04 nhánh tối ưu và hook12;12 candidatefacts/AI. QA15 chưa nhận release runtime.

Lọc ràng buộc thiết kế trước ngân sách/lịch/địa bàn/nguồn cung; chỉ so tiêu chí áp dụng từng nhóm (U cho tường bao khi có), không ép U cho bê tông/thép. NSGA-II tường là công cụ riêng, không chặn tư vấn nhóm khác. Demo chỉ gạch/vữa **chưa đạt**.

Điều phối01 xác nhận: phiên12 đang chuẩn bị độc lập/staging, chưa gọi API thật. QA15 chỉ đọc/ma trận, không runtime/source. `proposed` khác `approved`: đề xuất chưa là lựa chọn được phép áp dụng; chỉ user confirm mới chuyển sang áp dụng. Không train XGBoost hoặc gắn yêu cầu kiểm AI với upload CAD đã bị gate/nguyên hồ sơ thật.

| ID | Tình huống / thao tác | Oracle |
|---|---|---|
| AI01 P0 | Snapshot đã kiểm, yêu cầu tiếng Việt “ưu tiên chi phí thấp, giao sớm, giữ ràng buộc tường hiện tại”; catalog có nhiều phương án hợp lệ | Chỉ đề xuất mã trong tập backend cho phép; so sánh chi phí/cung ứng/U khi có nguồn, nêu đánh đổi theo yêu cầu; không tự chọn thay người dùng |
| AI02 P0 | Chỉ một phương án hợp lệ | Nói rõ chỉ một lựa chọn phù hợp và giới hạn so sánh; không bịa phương án đối thủ hoặc gọi đó là tối ưu toàn cục |
| AI03 P0 | Không có phương án phù hợp | Nêu không có lựa chọn và ràng buộc gây loại; không tự nới thiết kế/thêm mã; chỉ đề nghị người dùng xem xét ràng buộc, không tự áp |
| AI04 P0 | Có lựa chọn nhưng thiếu giá/nguồn/điều kiện báo giá; thiếu supply/U độc lập từng trường; giá khác cơ sở | Giữ lựa chọn và ghi thiếu rõ; không điền0/ước đoán thành giá mua, không xếp “rẻ nhất” khi thiếu hoặc khác cơ sở quy cách/đơn vị/VAT/giao hàng; phân biệt giá tham khảo/đại lý/dự đoán |
| AI05 P0 | Yêu cầu tiếng Việt mâu thuẫn/thiếu ràng buộc, hoặc yêu cầu dùng mã không tồn tại/bịa giá | Hỏi phần cần làm rõ hoặc nêu giả định rõ chưa áp dụng; không tạo mã/số để thỏa yêu cầu; giữ ràng buộc backend |
| AI06 P0 | Nhận proposed, chưa xác nhận; bấm xác nhận, từ chối rồi chọn lại; lưu/reload | Proposed không tự thành approved hoặc ready; chỉ user confirm mới áp; lưu đúng mã/lựa chọn và materialRevision liên kết projectUid/drawingId/reviewId; từ chối không đổi lựa chọn đang lưu |
| AI07 P0 | Trong lúc AI chờ, sửa lượng/đổi dự án/recompute; response cũ trả sau | Bỏ hoặc đánh hết hiệu lực đề xuất cũ; không ghi vào dự án mới; yêu cầu đề xuất lại trên snapshot mới |
| AI08 P0 | Phương án đổi chiều dày/cấu tạo | Không tự sửa thiết kế; khi người dùng chọn phải vô hiệu kiểm liên quan và tính/kiểm lại trước consumer giá/tối ưu; không tái dùng lượng cũ |
| AI09 P0 | Khối lượng partial/D hoặc chưa kiểm; draft/legacy thiếu ID | Chưa kiểm/draft không được trình bày như bản xác nhận; partial giữ phạm vi/lý do thiếu và chỉ so sánh phần biết, không gọi chi phí phần biết là toàn công trình |
| AI10 P0 | API thật OpenAI khi đủ điều kiện; thêm lỗi timeout/provider | Ghi model thực và request identity/usage/cost nếu provider cung cấp, phân biệt thiếu metadata; phản hồi khớp tập phương án/số liệu backend; lỗi không áp lựa chọn hoặc xóa dữ liệu đã lưu |
| AI11 P0 | Hồ sơ đa nhóm: đối chiếu toàn bộ công tác đã kiểm theo tầng/cấu kiện | Mỗi dòng truy ra vật tư tương ứng, hoặc hiện “không phát sinh vật tư mua”, hoặc còn thiếu kèm lý do; không mất công tác do không có option/catalog/giá; không lấy chỉ tường làm đủ |
| AI12 P0 | Bê tông/cấp phối và thép phát sinh ở móng/cột/dầm/sàn/thang/mái | Giữ mác/cấp phối, quy cách thép và ràng buộc thiết kế; truy nguồn định mức/quy đổi; không hạ quy cách để rẻ hơn; thiếu thông số thì giữ thiếu |
| AI13 P0 | Cốp pha, nền, chống thấm và phụ kiện khi có căn cứ phát sinh | Giữ nhóm và phạm vi công tác liên quan; không tự tạo phụ kiện, định mức hoặc hao hụt; nhóm chưa hỗ trợ vẫn hiện lý do/thông tin cần bổ sung |
| AI14 P0 | So lượng lắp đặt với nhu cầu mua cho từng nhóm, có/thiếu quy cách/hao hụt | Hai lượng và đơn vị/cơ sở quy đổi tách rõ; không gọi kg/tấn lắp đặt là lượng mua khi chưa có căn cứ; không áp cùng một hệ số cho mọi nhóm |
| AI15 P0 | Cùng ràng buộc thiết kế, đổi yêu cầu tiếng Việt giữa ưu tiên giao sớm và chi phí thấp, thêm ngân sách/địa bàn | Đề xuất đổi theo dữ kiện áp dụng có nguồn, giải thích đánh đổi; thiết kế giữ nguyên; tiêu chí thiếu không được bịa để xếp hạng; nhóm ngoài tường vẫn được tư vấn khi NSGA-II không áp dụng |
| AI16 P0 | Hai cấu kiện cùng plan/work, MaterialUse không có element_id | Chỉ hiển thị tổng đúng phạm vi work+plan+via+quantity; không chia đều hoặc gán cho từng cấu kiện. Muốn tính riêng cần đường quy đổi được duyệt với đầu vào đủ; liên kết không đủ phải ghi giới hạn |
| AI17 P0 | Có intermediate vữa/bê tông rồi đã tách ra vật liệu thành phần | Không cộng intermediate thêm lần nữa vào nhu cầu mua/chi phí; giữ truy vết via và cơ sở quy đổi; không tự chọn đồng thời mua hỗn hợp và các thành phần thay thế |
| AI18 P0 | Lượng đã gồm hao hụt nhưng thiếu quy cách bao/cây/tấm; thép thiếu chiều dài cây | Giữ đơn vị lượng đã biết theo quy cách có nguồn (ví dụ kg thép); ghi chưa tính số cây/bao/tấm, không coi hao hụt là đóng gói và không tự giả chiều dài cây |
| AI19 P0 | Không có wall_groups nhưng có bê tông/thép; công tác không phát sinh vật tư mua | Vẫn tư vấn nhóm có dữ liệu, không bắt buộc tường hoặc NSGA-II; công tác không mua được ghi rõ có căn cứ, không biến thiếu dữ liệu thành không phát sinh; giá/U chỉ trong phạm vi áp dụng |
| AI20 P0 | ACTUAL VN00204: 52 Work, 7 Material; 3 COP_PHA khoản trừ −0,194/−0,290/−0,194 m² | Work/uses có nguồn giữ số signed finite, không abs/drop để qua validation; khoản trừ đúng một lần. Lượng đặt mua không âm; không biến âm thành nhu cầu mua, không double trừ |
| AI21 P0 | VN00204: cả 7 vật tư incomplete; chỉ TH10 có ID, 6 missing ID | Giữ tên/rawclass/knownpart/missing; không gộp TH10 thành thép chịu lực; lookup tìm thấy không đồng nghĩa current design/purchase valid; không bịa ID cho 6 dòng |
| AI22 P0 | VN00204: BULLETIN/history có giá tham khảo, không báo giá mua eligible | Không set has_eligible_purchaseprice từ BULLETIN/history; không gọi giá này là giá mua hoặc xếp hạng mua dựa trên dữ liệu không đủ |
| AI23 P0 | Hồ sơ đã kiểm nhưng chưa chọn tay bất kỳ vật liệu; mở thẳng /toi-uu | Có phương án nháp với dữ liệu đủ căn cứ và phần thiếu rõ, điểm vào AI hoạt động theo lượt được giao; không redirect bắt buộc /dieu-chinh hoặc xem giá; không hạ gate kiểm/lưu khối lượng |
| AI24 P0 | Hồ sơ không có tường nhưng có nhóm phần thô khác; đủ một số dữ kiện, thiếu ứng viên/giá/lịch/quy cách ở phần còn lại | Tự điền nháp chỉ khi duy nhất và đủ căn cứ; còn lại là so sánh/phương án có điều kiện, không bịa thông số chịu lực/giá/lịch giao; không đợi NSGA-II tường mới hiện phương án; tổng chỉ bao phủ dòng đủ giá |
| AI25 P0 | Có lựa chọn người dùng đã chốt; nhận nháp, đổi ưu tiên, quay lại chỉnh tay rồi mở tối ưu | Bảo toàn override hợp lệ và nguồn/revision; không tự thay để rẻ hơn; xung đột/thiếu phải hiện rõ; đổi hình học vô hiệu kiểm phần liên quan trước áp dụng |
| AI26 P0 | Chọn và xác nhận cả phương án rồi lưu/reload/đổi dự án/quay lại; draft và lỗi lưu | Một xác nhận cấp phương án, không buộc từng dòng; chỉ applied khi lưu thành công và đúng snapshot; draft không approved/ready; lỗi lưu không mất bản đã chốt; giữ lựa chọn và revision qua restore |
| AI27 P0 | client_snapshot có hash/session hợp lệ nhưng client tự ghi checked/ownership/current revision | Hash chỉ bind payload, không chứng minh ownership/approval/bản mới nhất; UI vẫn cần approvedWork/receipt. Không tuyên bố server verified quyền dự án từ echo/hash; materialRevision nullable ở advice nhưng project/drawing/review binding phải đủ |
| AI28 P0 | Replay offline nguyên response live, rồi biến thể TH100/X-TH10/TH10-A/sai lineId/giá mới 12 triệu | Nguyên mã chỉ được nhắc đúng options dòng; summary chỉ union facts; biến thể phải bị reject, không sửa facts hoặc approved. Không gọi live thêm để kiểm guard; guard mã/số đạt chưa chứng minh văn xuôi đúng ngữ nghĩa |
| AI29 P0 | Session hết hạn/hash-binding-principal sai, payload vượt giới hạn; lỗi provider/hủy/đổi context | Reject đúng cổng, không cắt dòng âm thầm, không lộ key/raw error; giữ bảng gốc; stale answer không áp. Hủy UI không được hứa upstream dừng/phí bằng0 |

## Oracle và gói đầu vào cần owner bàn giao

### Đã đọc bàn giao12 — chưa nghiệm thu tích hợp

Đã đọc `docs/review/row_assistant_12/{HANDOFF,MATERIAL_CONTRACT,MATERIAL_CASES}.md`. Owner báo canonical agent hash `463E8F88B2C92958B6217CDE60EA419ECDBB345EF2569E912094D2ADB300210E`, purelogic26 pass/4,17s; chưa main/UI hook nghiệm thu. QA15 chưa chạy lại hoặc tự xác minh hash hiện hành. Canonical HTTP mock còn PENDING_APPROVAL do TestClient/socketpair; không chạy hộ hoặc dùng công cụ khác vượt gate. Mapping ca12 M01–M17 sang AI01–29 chỉ là chuẩn bị, không chuyển terminal staging sang canonical HTTP/UI.

Live04 đã có đúng một HTTP200 ACTUAL diagnostic checked=false/partial=true; guard cũ từ chối TH10 hợp lệ. Replay offline sửa guard không phải live mới và không tự chứng minh canonical hash mới đã replay. Chờ01/04 bàn giao receipt/replay cuối để review; không gọi API thêm. Không áp dòng “live SYN sau release” trong MATERIAL_CASES cũ để mở thêm lượt ngoài authorization01.

Các giới hạn phải hiện trong kết luận: client_snapshot không độc lập xác minh ownership/approved/current; dùng session RAM demo một worker; current_lookup không phải current_design; supply/U thiếu nguồn giữ null; purchase_quantity null khi chưa đủ cơ sở. Callback onPropose chỉ đề xuất, chưa chứng minh whole-plan apply ởAI26. Guard schema không thay kiểm ngữ nghĩa lời khuyên, budget/time/U hoặc E2E trên bản đã kiểm.

Nhận từ 01/02/04: route/payload cuối và release lượt cụ thể; snapshot/version; danh sách mã catalog hợp lệ và lý do loại; dữ liệu nguồn của chi phí, cung ứng, U cùng đơn vị/điều kiện/ngày; expected cho nhiều/một/không phương án và thiếu giá. Không tự bịa catalog fixture có vẻ như mã thật. Fixture kỹ thuật do owner cấp phải ghi SYNTHETIC, tách khỏi hồ sơ/dữ liệu ACTUAL.

Gói đa nhóm cần có danh sách toàn bộ công tác đã kiểm và mapping theo tầng/cấu kiện: bê tông/cấp phối, thép, cốp pha, xây/trát, nền, chống thấm, phụ kiện khi phát sinh. Mỗi dòng ghi lượng lắp đặt, vật tư/nhóm liên quan, cơ sở lượng mua, nguồn và trạng thái đủ/thiếu/không phát sinh. Nhóm không phát sinh trên hồ sơ phải ghi rõ; muốn chứng minh xử lý nhóm đó dùng ca synthetic riêng được owner cung cấp, không bịa rằng hồ sơ thực có nhóm này.

Giới hạn mapping theo thông tin04 qua00: MaterialUse hiện chỉ có work+plan+via+quantity, không có element_id. Bảng đối chiếu phải ghi độ phân giải thực tế; không tuyên bố truy tới từng cấu kiện khi nguồn chỉ hỗ trợ tổng công tác/tầng. Yêu cầu nghiệp vụ theo cấu kiện không cho phép QA tự chia lượng; đường tính riêng cần owner/01 duyệt và đầu vào đủ.

Trước **một lượt API thật trên SYNTHETIC demo**: 01 xác nhận nguồn freeze, release dữ liệu SYN demo được phép gửi, provider/khóa đã cấu hình bởi owner và phạm vi gọi cụ thể. Không gửi nguyên hồ sơ thật, không phụ thuộc hoặc dùng đường khác cho upload CAD bị từ chối. Không đọc/in khóa hoặc tự phát sinh lời gọi trả phí từ lượt chuẩn bị. Thiếu điều kiện ghi BLOCKED, không dùng mock làm bằng chứng API thật. Đây không thay thế QA ACTUAL-build còn blocker upload; không train XGBoost trong lượt này.

**Ngoại lệ được01 xác nhận sau chỉ đạo cũ:** user đã authorize **04 sole một live ACTUAL minimal deidentified** cho VN00204; quy tắc SYN-only trước đây không áp lên lượt này. 12 sửa offline/staging; chưa call trước pass. QA15 không được gọi runtime. Gói bằng chứng của ca này phải giữ đúng nhãn **LIVE_STAGING / checked=false / partial=true**, không hạ gate UI hoặc khối lượng, không tuyên bố E2E. Không gửi nguyên hồ sơ và không thử lại upload Tân Bình. Các điều kiện của những lượt API khác vẫn theo release riêng của01.

Theo thông tin01, staging `WorkFact.quantity ge0` đang reject khoản trừ trước API; đây là blocker được bàn giao, chưa phải probe QA15. Cần evidence offline sau sửa cho signed finite và các ca AI20–22 trước lượt live do04 thực hiện. Core full 824 pass/225 hash ổn do01 báo không chứng minh AI đã áp hoặc bao phủ; QA15 chưa xác minh terminal gói full này trong lượt docs.

## Bằng chứng cần lưu cho từng ca

### Coverage ledger bắt buộc theo chốt01

Lập một dòng cho mỗi công tác trong snapshot đã kiểm; tách tầng/cấu kiện khi nguồn có đủ liên kết. Không có element_id thì ghi tổng theo work/plan, không tạo liên kết giả. `knownparts` là phần đã biết, không tự gọi toàn bộ đủ. Ba vật liệu cùng thuộc một nhóm tường không chứng minh đa nhóm công tác.

| projectUid / drawingId / reviewId | Work / tầng / cấu kiện hoặc giới hạn tổng | Nhóm công tác | Lượng lắp đặt / ĐVT | materialuses + via | knownparts | unsupported / missing + lý do | Nhu cầu mua / ĐVT / cơ sở | Hao hụt / cơ sở đã gồm hay chưa | Nguồn / thiết kế | proposed / approved / materialRevision |
|---|---|---|---|---|---|---|---|---|---|---|
| Chưa có dữ liệu thực thi | NOT_RUN | Chưa điền | Chưa điền | Chưa điền | Chưa điền | Chưa điền | Chưa điền | Chưa điền | Chưa điền | Chưa điền |

Ca demo E2E đa nhóm cần **hai bản: đủ và partial**, có tối thiểu các nhóm công tác độc lập thực sự trong fixture được owner cấp (không tự tạo số để lấp nhóm): snapshot đã kiểm → nêu nhu cầu tiếng Việt → backend facts/ledger → so sánh phương án theo thiết kế trước cost/time → proposed → user confirm → approved/lưu → reload/consumer cùng revision. Bản partial giữ knownparts, unsupported/missing và lý do xuyên suốt; không làm mất dòng hoặc gọi tổng chi phí phần biết là đủ.

Đường demo chính mới: cả hai bản bắt đầu **không chọn tay vật liệu**, tới thẳng `/toi-uu`; có thêm bản không tường. Xác nhận ở cấp phương án; chỉnh tay là nhánh tùy chọn để kiểm override/restore. Các ca AI23–26 thay cổng cũ yêu cầu materials-ready thủ công trước mở tối ưu, nhưng không thay cổng receipt khối lượng đã kiểm/lưu.

Lượt oneAPI SYN được phép chỉ khi01 release riêng, **ngoài Full225**; không gộp hoặc suy bằng chứng API thật từ kết quả full. 12 staging, 02 hook và 04 facts theo điều phối; QA15 vẫn docs-only, không chạy runtime.

- Yêu cầu tiếng Việt nguyên văn; snapshot identity và receipt đã kiểm/partial trước thao tác.
- Catalog revision và tập phương án backend trả về, lý do loại, số liệu/nguồn/đơn vị/điều kiện dùng so sánh.
- Request/response và tool trace đã loại bí mật; đối chiếu từng mã và từng con số trong lời giải thích với dữ kiện backend, bao gồm lời khẳng định khi thiếu dữ liệu.
- UI trước/sau xác nhận, bản lưu và materialRevision; guard/reload và invalidation nếu đổi hình học hoặc response cũ.
- Với AI10: thời gian, model, mã lần gọi do provider cung cấp, usage/chi phí nếu có nguồn; lỗi và trạng thái dữ liệu sau lỗi. Không suy chi phí khi thiếu thông tin.
- PASS/FAIL/BLOCKED theo từng ca; ghi rõ mock/synthetic/API thật/ACTUAL-build, không gộp thành “AI đạt” khi thiếu lớp bằng chứng.

Thứ tự sau khi 01 giao lượt: AI11/14 (đủ phạm vi công tác/cơ sở lượng) → AI03/04/06/07/08 (bịa số, tự áp và dùng lượng cũ) → AI12/13/15 và AI01/02/05/09 → AI10 khi đủ điều kiện. Tiếp tục giữ các ca mất dữ liệu/guard trong TEST_MATRIX; thay trọng tâm demo không bỏ các cổng này.
