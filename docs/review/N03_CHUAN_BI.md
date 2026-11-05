# N03 — Chuẩn bị giằng chồng cùng cao độ

03/11/2026 — Codex. **CHỈ ĐỌC, CHƯA TRIỂN KHAI**. Không sửa source/test hoặc chạy suite trong khung smoke CAD. Các quy tắc dưới đây là đề xuất cần BA duyệt, không phải dữ liệu đã có trong bản vẽ.

## Bằng chứng hiện trạng

- `tests/test_rough_secondary.py:106–112`: xfail strict tạo GT1/GT2 cùng đoạn 0–4.000 mm, b220/d150, nhưng **không khai báo cao độ**. Chỉ kiểm XAY trừ một lần; chưa kiểm bê tông/cốp pha giằng. Test ngầm giả định hai bản ghi là một thể tích, dữ liệu chưa chứng minh giả định đó.
- `secondary.LinearMember:41–56` chỉ có id/kind/XY/b/d/source/keep, không có z hoặc nhóm cao độ; id/ký hiệu không đủ làm định danh cấu kiện vật lý. Cùng plan không có nghĩa cùng cao độ.
- `deduct_ties:95–123` lặp từng giằng, clip trục tường theo vùng XY có dung sai 150 mm, trừ lap×d×dày tường và clamp về 0 từng lần. Không hợp vùng, không kiểm cao độ hoặc giao với cửa/lanh tô/cột đã trừ. `linear_works:59–79` cộng chiều dài từng bản ghi theo b/d/source; bê tông và cốp pha cũng có thể cộng trùng.
- `takeoff:245–249` gọi trừ xây rồi sinh giằng từ `PlanInput.members`; cần cùng một quyết định gộp cho cả hai đường. `req.members` đọc kết cấu chỉ gọi linear_works với plan “bản vẽ kết cấu” (`:280`), không tự gắn tầng/trừ xây.
- `read_secondary:194–236` lấy XY/tiết diện và source structural, chưa lấy cao độ/tầng; cảnh báo chưa gắn tầng. `structural_parts` ghép danh sách members, chưa căn chỉnh vào tầng kiến trúc. K01/K02/K03 xử lý liên kết nguồn/căn chỉnh, không làm tiện trong N03.

## Quy tắc đề xuất đủ hẹp

1. Phải biết **tầng đích + cùng hệ tọa độ XY + cùng cơ sở cao độ** trước khi xem hai bản ghi là ứng viên trùng. Khác tầng hoặc chưa căn chỉnh: không gộp, không dùng giằng kết cấu để trừ tường kiến trúc.
2. Đề xuất bổ sung `z_bottom_mm: float | None = None` trên LinearMember, tính tương đối từ đáy tường/tầng đích, chiều dương lên; d_mm là chiều cao nên khoảng đứng là [z_bottom, z_bottom+d]. Đây là thay đổi hợp đồng request cần duyệt, **không tự thêm trong lượt chuẩn bị**. Cần bằng chứng/nguồn cao độ; không mặc định None=0, không dùng chiều cao tầng làm cao độ giằng.
3. N03 tối thiểu chỉ hợp các đoạn **thẳng hàng thực sự**, cùng đáy/cao/bề rộng đã biết, trong cùng tầng/hệ quy chiếu. Hợp các khoảng dọc trục, kể cả đảo đầu mút; đoạn kề nhau không mất chiều dài. Dung sai clip tường hiện có không phải dung sai gộp hai giằng; không dùng 150 mm để nhập hai trục gần nhau.
4. Cùng hình chiếu nhưng khoảng đứng tách rời: là hai giằng, giữ cả hai lượng và trừ cả hai dải xây, nếu đều nằm trong khối xây. Không dedup hình chiếu toàn cục. Cùng đáy nhưng khác d/b hoặc giao một phần theo chiều đứng: chưa đủ cho phép hợp khoảng 1D; giữ ca cần kiểm, không tự chọn tiết diện lớn nhất hoặc cộng như hai thể tích độc lập đã đủ.
5. Cùng thể tích nhưng khác source/id: chỉ gộp sau khi có căn cứ cùng cấu kiện; giữ toàn bộ evidence. Không chọn source tốt nhất để nâng A/B; giữ phụ thuộc yếu nhất khi dùng nhiều nguồn. Nếu nguồn manual/KC còn chưa khớp tọa độ/tầng, chuyển pending K03. N03 không xử lý ghép nguồn tự động.
6. Trừ xây một lần cho thể tích hợp đã xác nhận; bê tông GIANG_TUONG và cốp pha phải dùng cùng danh sách/chiều dài hợp. Với b220/d150, L4 m: bê tông 0,132 m³; cốp pha hai thành 1,200 m². Không đưa số gộp đúng sang một đường nhưng vẫn cộng trùng ở đường kia.
7. Phạm vi đầu tiên không làm engine giao thể tích 3D. Giằng xiên XY, khác tiết diện/cao độ giao một phần, vượt ranh đứng khối xây hoặc giao vùng cửa/cột/lanh tô đã trừ: cảnh báo cần kiểm, không chứng nhận kết quả net đầy đủ. Ghi rõ giới hạn; clamp về 0 không chứng minh trừ đúng. Nếu BA yêu cầu xử lý chính xác các ca này trong N03, cần mở phạm vi dữ liệu tường/lỗ mở/cột trước.

## Request cũ thiếu cao độ

- Deserialize vẫn được với z=None nếu trường mới được duyệt; không tự sửa file nguồn/DB hoặc gắn cao độ giả.
- Một giằng đơn/những đoạn không tranh chấp có thể giữ phép tính cũ để tương thích nhưng phải nêu “chưa kiểm cao độ/vị trí đứng”; không nâng thành tổng đã xác nhận. Cách gắn missing/status cần duyệt vì trạng thái hiện vẫn suy từ source.
- Khi từ hai giằng trở lên chồng XY mà thiếu cao độ: **không tự gộp và không tự coi độc lập**. Giữ bản ghi/giá trị thô để rà; nhóm giằng và XAY chịu ảnh hưởng phải có missing/cảnh báo, không xuất như net đầy đủ. Đề xuất quantity net của nhóm bị ảnh hưởng để None nếu chưa có hợp đồng known_part; không dùng số chưa trừ làm net rồi coi đủ. Có thể giữ lượng xây trước trừ trong formula/evidence, chưa thêm schema known_part trong N03.
- Xfail hiện tại không được chỉ bỏ dấu xfail sau dedup XY. Sau duyệt dữ liệu: chuyển ca cùng cao độ sang khai báo z tường minh, thêm ca legacy thiếu z chờ kiểm và ca khác cao độ. Đây là sửa giả định fixture có chủ ý, không đổi dữ liệu để che lỗi.

## Ma trận nghiệm thu đề xuất

Fixture SYNTHETIC: tường dài10 m, cao xây3 m, dày0,22 m, không cửa/cột/lanh tô → 6,600 m³; giằng b220/d150, cùng trục nằm trong chiều cao xây. Số dưới là phép tính đề xuất, **chưa chạy test**.

| Ca | Kỳ vọng |
|---|---|
| Hai đoạn 0–4 m cùng z/tiết diện và đã xác nhận một thể tích | L hợp4 m; BT0,132; CP1,200; XAY6,468 m³ |
| 0–4 m và 2–6 m cùng z/tiết diện | L hợp6 m; BT0,198; CP1,800; XAY6,402 |
| 0–4 m, z=1.000 và z=2.000 mm | Hai dải tách; BT0,264; CP2,400; XAY6,336; không nhập một |
| Đảo đầu mút, đổi thứ tự đầu vào, ba đoạn lặp | Cùng kết quả hợp và đủ evidence, không phụ thuộc thứ tự |
| Cùng XY nhưng khác tầng đích | Hai kết quả theo tầng, không nhập; mỗi tầng trừ riêng |
| Chồng XY, một/cả hai thiếu z; request cũ | Pending/missing, không đoán cùng cao độ, không net đầy đủ |
| Giằng đơn request cũ | Giữ tương thích tính thô theo quyết định BA; cảnh báo chưa xác minh vị trí đứng |
| Khác z nhưng khoảng đứng giao nhau; khác d hoặc b | Chưa hỗ trợ hợp đơn giản; nêu lý do, không báo đủ |
| Hai trục gần nhau nhưng khác trục trong phạm vi150 mm | Không nhập chỉ vì dung sai clip; yêu cầu kiểm quan hệ tường |
| keep=False; SE_NO; giằng ngoài tường | Không trừ XAY theo nhầm kind; giữ hành vi loại/bỏ, giằng ngoài vẫn có lượng riêng nếu đủ dữ liệu |
| Thiếu d/b, chiều dài0, số không hữu hạn | Không trừ giả; validation/cảnh báo theo hợp đồng duyệt, không sinh NaN/inf |
| Giằng KC chưa gắn tầng hoặc nguồn KC+manual chưa căn chỉnh | Không tự ghép/trừ vào kiến trúc; pending K01–K03 |
| Vượt đỉnh/đáy xây, giao cửa/cột/lanh tô | Phải báo giới hạn, không coi clamp0 hoặc trừ dải toàn phần là đáp án đúng |

## Quyết định BA đã chốt — 03/11/2026

Theo phân công điều phối, sáu nội dung dưới đây đã duyệt về phương pháp; **chưa cấp quyền triển khai source/test**:

1. `z_bottom_mm: float | None = None`, hữu hạn nếu có, tương đối đáy tầng/tường. Không default0, không suy từ height_mm. Z khai báo trong PlanInput là người dùng xác nhận, mức C; phải có dấu vết formula/evidence. Source structural không tự nâng độ tin cậy của đầu vào z này lên A.
2. Request cũ vẫn deserialize. Chồng XY thiếu z: không dedup, không coi net/tổng đủ; giữ raw records/evidence. Chỉ giữ số thô dưới dạng known_part khi hợp đồng partial đã có; nếu chưa có thì net=None/missing, nhưng không được làm mất lượng trước trừ. Ca legacy giằng đơn vẫn phải ghi giới hạn vị trí đứng như phần trên.
3. Cùng plan/hệ tọa độ, cùng trục thực, cùng z/b/d: hợp chiều dài và dùng chung cho BT/CP/XAY. Khoảng đứng rời: giữ hai giằng. Bằng nhau chính xác trong lượt đầu; dung sai clip150 mm không dùng để merge.
4. Khác tiết diện, giao đứng một phần hoặc xiên chưa giải được: missing rõ và không trình bày như tổng đủ. Không mở engine3D.
5. Không gộp manual/KC chưa căn chỉnh hoặc chưa gắn tầng, giữ pending K03. Khi cùng thể tích được xác nhận: giữ mọi evidence và nguồn yếu nhất, không chọn nguồn tốt nhất.
6. N03 phải nối partial qua status/tổng/vật tư/BOQ; helper/test hợp đoạn xanh chưa đủ nghiệm thu. Fixture cùng cao độ phải thêm z tường minh, ghi thay đổi giả định, giữ ca legacy riêng; **chưa bỏ xfail hiện tại**.

## Đề xuất chứng cứ nhỏ nhất — báo trước, chưa thêm trường

Đề xuất duy nhất `LinearMember.z_evidence: str | None = None`: mô tả nguồn/cách xác nhận cao độ do người dùng cung cấp, ví dụ “GT1, mặt cắt A-A, đáy +1.000 so đáy tầng T1; đã xác nhận”. Chuỗi này không tự chứng minh căn chỉnh XY/tầng và không phải cờ tự nâng A. Không thêm enum độ tin cậy hoặc nhóm merge ở lượt đầu; đầu vào z trên PlanInput được ghi rõ là C, kể cả khi ghi nguồn bản vẽ.

Caller/điểm truyền dự kiến, cần điều phối duyệt trước sửa:

- PlanInput.members và RoughRequest.members nhận LinearMember qua Pydantic; z=None/z_evidence=None giữ request cũ. Chưa thêm ô frontend; đường nhập mới tạm qua API.
- `read_secondary` chưa đọc được z: để trống cả hai trường, giữ pending. Không tự tạo câu chứng cứ từ source structural.
- `linear_works` đưa số z, gốc quy chiếu và z_evidence (nếu có) vào formula/evidence; `deduct_ties` ghi phần trừ, IDs nguồn và căn cứ hợp vào XAY. Không mất số raw trước trừ khi net bị treo.
- `assign_status` cần nhận phụ thuộc cao độ C một cách có cấu trúc hoặc từ inputs được truyền rõ. Không parse câu evidence tự do để quyết định trạng thái; phương án nối phải thống nhất với writer b2/b3 trước mở file. Chưa thêm trường WorkItem trong lượt chuẩn bị.

## Phạm vi file dự kiến và điểm nối partial

Lõi dự kiến `rough/secondary.py` và `tests/test_rough_secondary.py`: schema z/chứng cứ, hợp đoạn đủ căn cứ, danh sách chuẩn hóa dùng nhất quán cho bê tông/cốp pha/trừ xây. Nếu caller phải gọi chuẩn hóa một lần, cần xin quyền `rough/takeoff.py`, không chép hai thuật toán khác nhau vào hai helper.

Các điểm nối cần phối hợp sau N02-b2/b3, **không tranh quyền ghi hiện tại**:

| Điểm | Hợp đồng N03 phải giữ |
|---|---|
| status.assign_status / kế thừa CP, thép hàm lượng | Chưa đủ quan hệ giao: missing/D; dùng z người dùng xác nhận: phụ thuộc C, không bị source A ghi đè |
| takeoff tổng XAY/GIANG/CP | Có known_part khi hợp đồng partial cho phép; net chưa biết không thành 0, không complete chỉ vì một số khác None |
| materials_for_works / _Bill | Không sinh lượng vật tư đủ từ nhóm giằng/XAY net chưa biết; giữ phần biết đúng cơ sở và trạng thái thiếu |
| BOQ / optimizer / API | Thể hiện missing và lượng phần biết riêng; không xuất subtotal/raw như net đủ hoặc vật tư tối ưu đầy đủ |
| read_secondary / req.members | Chưa gắn tầng/căn chỉnh/cao độ thì pending, không tự áp trừ vào PlanInput |

Không sửa CAD parser/frontend/DB/ledger trong chuẩn bị này. Việc lưu raw trước trừ vào known_part, và cách truyền trạng thái C của z, phải dùng hợp đồng b2/b3 cuối; chưa chốt tên trường sản phẩm hoặc cách lưu DB thay writer đó.

## Trạng thái và cổng mở triển khai

**ĐÃ CHỐT phương pháp BA; CHỜ hợp đồng partial và quyền ghi sau N02-b2/b3.** Dữ liệu cao độ thật vẫn cần bổ sung, không có quyết định BA nào biến z thiếu thành z đã biết. Không source/test, không suite; không triển khai để làm xanh xfail bằng giả định hình chiếu. Trước giao dev cần chốt đề xuất z_evidence và cơ chế truyền phụ thuộc C qua status, khóa đúng vùng file/callers, rồi dùng ma trận nghiệm thu ở trên với fixture z tường minh và legacy riêng.


## Chữ ký/caller đề xuất cụ thể — chờ root duyệt trước source

Cập nhật theo contract status điều phối đã xác nhận: `assign_status` giữ `worst_status(w.status, *inputs)` và prior inputs. N03 gắn trước `status="C"`, `inputs=["cao độ đáy giằng: C (người dùng xác nhận)"]` cho lượng phụ thuộc z trong PlanInput; thiếu quan hệ giao thì quantity=None/missing/statusD. Không parse evidence/formula để suy mức tin cậy. `z_evidence: str | None = None` đã được BA chấp thuận thiết kế, chỉ mô tả chứng cứ, không dùng làm cờ merge/đủ.

### a. Một kết quả chuẩn hóa dùng chung

Chữ ký đề xuất, chưa thêm mã:

```python
normalize_ties(members: list[LinearMember], *,
               plan_context: bool = False) -> list[_TieGroup]

linear_works(plan: str, members: list[LinearMember], *,
             tie_groups: list[_TieGroup] | None = None) -> tuple[list[WorkItem], list[str]]
```

`_TieGroup` là kiểu nội bộ trong secondary.py, không phải schema sản phẩm: `members: tuple[LinearMember, ...]` giữ mọi bản ghi gốc/IDs/source/z_evidence; `segments: tuple[tuple[float,float,float,float], ...]` chứa đoạn XY hợp đã xác nhận; `missing: tuple[str, ...]` chứa lý do chưa thể gộp/tính đủ. Z/b/d lấy từ nhóm gốc đồng nhất, không lưu hai bản thông số có thể lệch. Nhóm chưa đủ không có segments được công nhận là tổng đủ; records vẫn nguyên để giữ lượng thô trong evidence.

Helper tạo các nhóm cùng tầng/hệ tọa độ đã được caller xác nhận, cùng nguồn hoặc đã xác nhận quan hệ nguồn; cùng trục ngang/dọc chính xác, cùng z/b/d, rồi hợp khoảng dọc trục. Xét nhóm tranh chấp trước khi cộng lượng: thiếu z/khác tiết diện/giao đứng một phần làm missing đúng nhóm liên quan; không chỉ bỏ nhóm lỗi rồi trình bày phần còn lại là tổng đủ. Có nguồn manual+structural chưa căn chỉnh thì pendingK03; chưa thêm field xác nhận căn chỉnh trong N03. plan_context chỉ là phạm vi dữ liệu do caller truyền, không tự chứng minh hai nguồn đã căn chỉnh.

Tại vòng lặp `compute_rough` trên một PlanInput: gọi helper **một lần** với plan_context=True, truyền chính cùng tie_groups cho deduct_ties và linear_works. Không tạo giằng giả với id đã nối rồi mất records; mỗi WorkItem tổng hợp giữ tất cả IDs và dấu vết trong evidence (không cắt 5 ID như nhãn hiển thị). Sê nô vẫn đi đường hiện có, không hợp nhầm với giằng.

`linear_works` khi caller không truyền tie_groups sẽ gọi chính helper với plan_context=False, không có thuật toán gộp thứ hai; không mặc định có căn cứ tầng chỉ vì plan là một chuỗi tên. Chữ ký cũ vẫn gọi được, nhưng ca mơ hồ không còn được cam kết số đủ.

### b. Ranh đứng thực của khối xây

Chữ ký mở rộng tương thích cách gọi, tất cả args mới keyword-only:

```python
deduct_ties(works, plan, walls, systems, members, catalog, *,
            tie_groups: list[_TieGroup] | None = None,
            wall_height_mm: float | None = None,
            openings: list[ReviewOpening] | None = None,
            column_len_in_walls: dict[str, float] | None = None) -> list[str]
```

Caller compute truyền `wall_height_mm=p.height_mm - (wall_params.beam_depth_mm or 0.0)`, đúng cơ sở hiện của wall_works; không dùng params gốc nếu wall_params đã suy cao dầm. Nếu beam_depth còn thiếu, giữ cảnh báo cơ sở chiều cao xây hiện có, không tuyên bố ranh này đã được kiểm từ bản vẽ.

Khoảng xây dùng [0, wall_height_mm]. Chỉ trừ khi 0≤z_bottom và z_bottom+d≤wall_height, các số hữu hạn, d>0. Vượt ranh hoặc không có wall_height: net XAY liên quan chưa được chứng minh, missing/None, giữ trước-trừ trong formula/evidence; không clip phần đứng hoặc clamp rồi coi đúng. Không có args mới vẫn deserialize/call được nhưng phải ghi thiếu cơ sở thay vì trừ mù; đây là thay đổi mức đủ có chủ ý, cần test legacy.

### c. Phát hiện chồng với các phần đã trừ — bảo thủ đúng tường

Không cần thêm tọa độ cửa hoặc engine3D. `ReviewOpening` hiện chỉ có wall/w/h, **không có vị trí dọc tường hoặc cao bậu**; `column_overlaps` chỉ trả chiều dài tổng theo wall.id, không khoảng giao. Vì vậy không thể chứng minh chính xác giằng có tránh lỗ/cột trên cùng tường bằng dữ liệu hiện tại.

Đề xuất tối thiểu: compute truyền `openings=p.openings` và `column_len_in_walls=overlaps` đã dùng trong wall_works. Sau khi clip giằng xác định có lap>0 với một wall kept/masonry, nếu tường đó có opening.keep=True hoặc column_len_in_walls[wall.id]>0 thì gắn missing cho XAY chứa tường ấy, giữ raw/evidence, không trừ tiếp như net đã chắc. Có opening được giữ là đủ để đánh cần kiểm, kể cả nhỏ dưới ngưỡng/chưa h vì không có vị trí để chứng minh tránh nhau. Đây là báo thiếu có chủ ý, không khẳng định đã giao thật. Mọi lanh tô trong wall_works hiện sinh từ openings nên cùng cổng này bảo vệ cả vùng lanh tô, kể cả L1 vừa hoàn trả một phần. Không parse formula để đoán L1 đã sửa dòng nào.

None của openings/column_len_in_walls nghĩa caller chưa cung cấp thông tin; không đồng nhất với []/{} đã biết không có. Nếu thiếu một trong hai thì chỉ nhóm XAY có tường mà giằng chồng mới thiếu căn cứ, không làm D các tường khác toàn mặt bằng. `_xay_of` hiện nhóm theo cls/role/system, nên một tường bị ảnh hưởng sẽ làm cả dòng XAY gộp đó chưa đủ; ghi rõ wall.id và giữ số trước trừ, **không chia ngược tổng cho tường**. BT/CP giằng vẫn có thể đủ nếu hình học giằng đã chứng minh, còn vật tư XAY net chưa biết phải thiếu theo b3.

Muốn thu hẹp cảnh báo trong tương lai cần khoảng cột dọc tường và vị trí/bậu cửa đã kiểm, không thêm vào N03 tối thiểu. Không giả tạo bậu=0 cho cửa sổ.

### d. Giằng kết cấu chưa gắn tầng/căn chỉnh

Caller cuối compute đang gọi `linear_works("bản vẽ kết cấu", req.members)`. N03 phải truyền kết quả `normalize_ties(req.members, plan_context=False)` hoặc để đường default làm việc đó; **không kiểm tên plan để phân biệt**. Những giằng này giữ records/evidence, pending tầng/cao độ/căn chỉnh, không trừ XAY kiến trúc và không gộp với PlanInput.members. Nếu chưa có hợp đồng known_part cho raw thì quantity=None/missing; không bỏ mất số thô trong evidence. Nguồn source=structural không phải bằng chứng hoàn tất liên kết tầng.

### Điểm nghiệm thu xuyên luồng và quyền file

Sau root duyệt chữ ký: cần cấp secondary.py/test_rough_secondary.py và đúng vùng compute_rough trong takeoff.py để truyền các kwargs trên; phối hợp contract b3, không tranh sửa khi full suite khóa. Không đổi walls/columns/ReviewOpening/frontend/DB trong phương án tối thiểu. N03 phải có ca compute→status/totals→materials→BOQ/optimizer: chồng cùng z đủ thì đúng BT/CP/XAY; chồng thiếu z hoặc net bị cổng cửa/cột chặn thì missing/D/None không thành 0 hoặc vật tư đủ, raw không mất. Có ca hai tường khác nhóm chỉ một nhóm bị ảnh hưởng, ca cùng nhóm ghi giới hạn tổng gộp, và req.members đổi tên plan vẫn pending như cũ.

**Chỉ là đề xuất chữ ký/caller và phạm vi, CHƯA root duyệt để viết source. Không chạy test/suite trong lượt này.**


## Chốt BA chữ ký/caller — đã duyệt thiết kế, SOURCE HOLD

Điều phối đã đối chiếu code và duyệt phương án ở mục chữ ký/caller: normalize_ties/_TieGroup nội bộ; plan_context=False mặc định; tie_groups dùng chung; các kwargs wall_height_mm/openings/column_len_in_walls. Cổng thiếu thông tin giao cửa/cột là bảo thủ có căn cứ, không khẳng định giao thật. Không tạo tọa độ cửa/bậu hoặc đổi walls/columns.

Điều kiện bắt buộc khi được cấp triển khai:

- Giữ raw records trước chuẩn hóa; nhãn có thể rút 5 IDs nhưng evidence phải đầy đủ. Chỉ merge khi cùng trục/hệ quy chiếu và z/b/d đủ căn cứ; sê nô giữ hành vi cũ.
- Z người dùng khai báo làm phụ thuộc C qua w.status/inputs theo contract b3; không đổi assert A→C mà thiếu giải thích cap cao độ. Không parse evidence hoặc sửa status.py tiện trong N03.
- Test None khác []/{}; tường khác nhóm không bị ảnh hưởng giữ số. Nếu một tường trong XAY gộp cần kiểm, cả net nhóm=None/missing, lưu số trước trừ trong evidence, không phân bổ ngược.
- Fixture giằng đã xác nhận tầng/cao độ cần khai báo z và ngữ cảnh tường minh; giữ ca legacy thiếu z/context riêng. Không sửa/xóa xfail khi chưa được cấp source và chưa kiểm xuyên luồng.
- Phạm vi dự kiến được mở sau full terminal/hash: secondary.py, test_rough_secondary.py và đúng vùng caller compute_rough. Không status/models/walls/columns/DB/frontend. Chỉ thực hiện khi root cấp quyền rõ; thiết kế được duyệt chưa phải quyền ghi source.

**Hiện tại SOURCE HOLD:** full suite điều phối thông báo session93390/PID32352 đang chạy. Lượt này chỉ cập nhật tài liệu; không ghi source/test, không chạy test/probe, không tự kết luận tiến trình đã dừng.
