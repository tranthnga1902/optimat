# O01 — Nguồn dầm theo từng tầng, gói chuẩn bị

03/11/2026, Codex. **CHỈ ĐỌC / CHƯA TRIỂN KHAI** trong lúc J04 chạy full tích hợp session62154. Không sửa source/tests/scripts/catalog/DB, không chạy test hoặc CAD nặng. Q02 đã có hợp đồng missing/D/partial; không mở O02/K01 trong lượt này.

## Bằng chứng trên code hiện tại

- `takeoff.compute_rough:253`: `p.beams` khác None thì dùng nguyên danh sách; nếu None và **bất kỳ** req.structural_beams tồn tại thì dùng [], nếu không mới infer_beams. Do đó KC của Tầng2 có thể chặn suy ở Tầng3, nhưng manual trên Tầng2 vẫn được tính rồi KC lại được cộng tại vòng riêng.
- `:258`: khi không có dầm của plan, cao dầm trừ xây có thể lấy từ **mọi** bộ KC nếu tập d chỉ có một giá trị. Một tầng thiếu KC có thể nhận chiều cao dầm của tầng khác. O01 phải ràng cơ sở thông số theo nguồn tầng, không lặng lẽ đổi công thức xây/giằng N03.
- `:232`: cảnh báo BEAM cũng bị bỏ nếu bất kỳ KC tồn tại, chưa xét phủ đúng tầng.
- `_floor_key:162–165` dùng tuple floors_of(title), fallback tiêu đề chuẩn hóa. `duplicate_plans` chọn view có tổng dài lớn nhất khi **cả khóa** bằng nhau; không giải được nhóm T2/T3/T4 và T4/T5. Dài hơn không chứng minh bản đúng/phủ đủ tầng.
- `:293–307`: KC được tính riêng theo view, nhân `structural_floors[view]` (mặc định1). Hai nhóm phủ T4 cùng nhân số tầng có thể cộng lặp T4. Số nhân không mang danh sách tầng đích.
- `used_beams`, beam_sources/status, beam_joints và `_slab_form_deduction` hiện theo plan/view ở hai vòng khác nhau. O01 cần một quyết định nguồn nhất quán, không chỉ sửa tổng DAM trong khi CP/thép hàm lượng/status/cao dầm còn dùng nguồn khác.

## Khóa tầng và dữ liệu còn thiếu

`drawing.registry.floors_of` đã chuẩn hóa TRỆT=T1, LẦU n=T(n+1), TẦNG n=Tn, ST/MAI/MONG khác nhau; có đọc dải và danh sách tầng. Không viết parser tầng khác. `_floor_key` hiện là **tập nhiều tầng của view**, không phải khóa một tầng đích.

`structural.floor_count` chỉ đếm số tầng từ tiêu đề; req.structural_floors chỉ là int, không đủ ghép từng tầng. Ví dụ view tên không rõ tầng nhưng count=3 không cho phép tự gán T2/T3/T4. Tên PlanInput có thể không parse được (ví dụ T2 viết tắt, tên do người dùng đặt); không tự dùng XY trùng hoặc chuỗi gần giống làm bằng chứng cùng tầng. MONG/MAI/ST không nhập với tầng số vì cùng xuất hiện trên một hình chiếu.

PlanInput.beams=None hiện cho phép suy; [] là caller chủ ý không đưa dầm, nhưng chưa có trường chọn manual/KC/inferred theo từng tầng. Chưa có ánh xạ rõ view KC→tầng kiến trúc, nguồn ưu tiên khi hai KC chồng phạm vi, hoặc bằng chứng hai view là mảnh bổ sung thay vì bản trùng. Giao diện roughRequest có chuyển parts KC vào request nhưng chưa biểu diễn quyết định nguồn tầng kiểu này. Không tự tuyên bố đây đã là luồng chọn nguồn hoàn chỉnh trên trang.

## Cách sửa tối thiểu đề xuất sau full và BA duyệt

1. Lập phạm vi từng view KC bằng floors_of hoặc mapping người dùng xác nhận, giữ source view và danh sách tầng. Đối chiếu count với tập đích; thiếu/xung đột không nhân đoán. Chuẩn hóa tầng kiến trúc theo cùng quy tắc, không dùng tiêu đề view làm chứng minh căn chỉnh XY.
2. Lập đúng một lựa chọn nguồn cho mỗi tầng: KC đã xác nhận của tầng đó; hoặc manual đã được chọn thay thế; hoặc suy khi không có KC và được phép. KC của tầng khác không tắt suy tầng đang xét. Không tự cộng manual/suy chưa chọn lên KC cùng tầng.
3. Tầng có KC nhưng thiếu tiết diện không được lặng lẽ thay bằng suy/manual để làm đủ số. Giữ phần biết, missing/D theo Q02; nguồn khác chỉ dùng khi có quyết định thay thế có dấu vết.
4. Với các view nhiều tầng chồng một phần, tách **phạm vi tầng**, không nhân rồi trừ ngược theo tỷ lệ. Mỗi tầng chỉ có một owner KC đã chọn. Phần không tranh chấp vẫn có thể giữ known_part; tầng tranh chấp pending, không đếm đủ hoặc mặc định OUT. Không chọn view dài nhất cho phần giao nếu chưa có quy tắc BA/bằng chứng.
5. Dùng lựa chọn đó nhất quán để sinh DAM/CP, cao dầm theo tầng, beam_sources/status, vật tư và thép hàm lượng. Mỗi đoạn/tầng đích chỉ góp một lần; evidence giữ view gốc, tầng đích, nguồn bị loại và lý do. Raw view không mất dù không được chọn.
6. Không chuyển hình học KC sang trừ xây/sàn kiến trúc khi chưa xác nhận cùng hệ tọa độ/tầng. Giữ hạn chế O02 về CP ô sàn và K01/K02 về liên kết/căn chỉnh; không sửa giao hình học bằng gán lại tên tầng đơn thuần. Không đổi điểm gọi N03 ngoài cơ sở wall_params đã được chốt.

## Ma trận ca nghiệm thu dự kiến

Fixture SYNTHETIC thuần Python, không chạy trong lượt chuẩn bị. Dầm ngang dài4 m, b200/d400, sàn100, không giao cột/dầm/móng, không lỗ framed: mỗi tầng BT=0,240 m³, CP=(2×0,3+0,2)×4=3,200 m². Các giá trị này chỉ kiểm phép chọn nguồn và số tầng, không định chuẩn dầm thật. Ca infer có thể cô lập bằng stub infer_beams trả hình học xác định, không giả nhận dạng CAD thành đã kiểm.

| Ca | Kỳ vọng cần kiểm |
|---|---|
| Tầng2 có KC; beams=None ở tầng đó | Chỉ KC, không infer; BT0,240/CP3,200 nếu đủ dữ liệu |
| Tầng2 có KC + manual4m chưa chọn thay thế | Không cộng0,480; giữ manual như nguồn chưa chọn/cảnh báo, kết quả dựa nguồn được duyệt |
| Tầng2 chọn manual thay KC tường minh | Chỉ manual, ghi nguồn/phụ thuộc C; không cộng lại KC ở vòng view |
| Chỉ Tầng2 có KC, Tầng3 không có và beams=None | Tầng3 vẫn được suy theo quy tắc; infer không bị tắt toàn repo |
| Không KC, beams=[] so với None | [] không tự suy; None mới cho phép suy. Cần BA chốt [] có nghĩa đã xác nhận không có hay mới loại lựa chọn |
| KC Tầng2 thiếu d, manual có đủ nhưng chưa được chọn | Không fallback làm đủ; quantity phần KC chưa biết None/D, giữ căn cứ thiếu |
| A phủ T2/T3/T4, B phủ T4/T5, cùng fixture4m/tầng | Sau lựa chọn owner T4 tường minh: tổng4 tầng0,960 m³/12,800 m², không nhân5 tầng1,200/16,000 |
| Cùng hai nhóm trên nhưng T4 chưa chốt owner | T2/T3/T5 có phần biết0,720/9,600; toàn phạm vi incomplete/D, T4 pending, không gán0 |
| A/B hình học khác nhau ở T4 | Yêu cầu chọn nguồn/tách bổ sung có bằng chứng; không max chiều dài hoặc suy tương đương từ tổng gần nhau |
| Hai view cùng cả tập tầng, một view dài hơn | Giữ hồi quy hiện tại có cảnh báo, nhưng BA phải chốt lúc nào được chọn max như request cũ và lúc nào pending |
| Count=3 nhưng mapping chỉ có2 tầng hoặc tiêu đề không xác định | Báo xung đột/thiếu phạm vi; không tự nhân count và không đặt tầng giả |
| LẦU1 với TẦNG2; ST với MAI; MONG với T1 | Cặp đầu cùng khóa T2 theo quy tắc đã có; các cặp sau không nhập sai |
| KC Tầng2 d400, Tầng3 chưa có cơ sở d | Không lấy d400 từ tầng2 để chứng nhận chiều cao xây tầng3 đã đúng; giữ phụ thuộc/thiếu theo quy tắc BA |
| Plan bị skip thiếu height, KC vẫn có view/tầng | Không im lặng mất phạm vi; phân biệt KC tính độc lập được với thiếu ánh xạ vào kiến trúc |
| Đảo thứ tự views/plans, đổi tên hiển thị nhưng mapping giữ nguyên | Kết quả owner và số tầng không đổi; không trùng evidence hoặc số nhân |
| BT/CP nguồn tầng partial→vật tư/BOQ/optimizer | Giữ known_part và D/missing theo Q02; không biến số thô/tổng một phần thành đủ |

## Hợp đồng cần BA chốt trước source

1. **Nguồn ưu tiên:** mặc định có KC đúng tầng thì ưu tiên KC và chặn cộng manual/suy chưa chọn; cần trường/cách xác nhận thay thế manual nào? Có cho kết hợp hai nguồn trên cùng tầng nếu chứng minh phạm vi cấu kiện rời không, hay giữ pending ngoài O01?
2. **Mapping nhỏ nhất:** đề xuất mapping view→list khóa tầng và lựa chọn owner theo tầng dạng optional để tương thích request cũ; tên/kiểu/schema/caller phải được duyệt trước thêm. Có dùng được Floor/Registry đã có không, hay request chưa mang đủ evidence để tái dùng trực tiếp?
3. **Legacy:** None/[] và view rỗng/toàn keep=False là chưa đọc được, người dùng đã loại hết, hay đã xác nhận không có dầm? Không dùng “có key trong dict” thay cho bằng chứng phủ tầng. Count thiếu/mismatch cần chốt pending hay lỗi validation.
4. **Trùng toàn bộ và chồng một phần:** max chiều dài của duplicate_plans hiện là quy ước; có giữ cho request cũ chỉ trùng cả tập tầng, kèm cảnh báo, hay yêu cầu xác nhận luôn? Phần giao mới không tự dùng quy ước này nếu chưa duyệt.
5. **Hệ tọa độ và cao dầm:** mapping tầng chỉ đủ chống cộng lặp, chưa đủ trừ cột/sàn/tường. Chốt phần nào O01 được truyền wall_params và phần nào phải pending O02/căn chỉnh; không tự áp KC vào hình học kiến trúc.

## Phạm vi dự kiến và bàn giao khi được mở

Chủ yếu takeoff.compute_rough/_floor_key và tests/test_rough_structural.py, có thể cần hồi quy tests/test_rough_takeoff.py (test_structural_beam_views_same_floor_counted_once). Thay đổi schema RoughRequest chỉ sau BA duyệt mapping/selection; không viết engine mới hoặc sửa registry/floor_count tiện khi chưa chứng minh parser sai. Không sửa beam_works/công thức/CSV để làm tổng khớp.

Trước source: chờ full hiện tại terminal/hash, chốt BA đầu vào, khóa đúng vùng takeoff đang dùng metadata masonry/N03 của phiên khác, lưu snapshot/hash. Bàn giao diff nhỏ, ca fixture/source-selection, expected vs actual theo tầng/view, CP/BT/vật tư và giới hạn căn chỉnh. Chưa D03 so bản vẽ thật, chưa O02/K01, chưa tự nghiệm thu.


## BA đã chốt nguyên tắc — DTO đề xuất cụ thể, CHƯA thêm schema

Điều phối đã duyệt: ưu tiên đúng một KC hợp lệ/phủ đúng tầng; manual thay KC cần chọn tường minh có evidence, không trộn nhiều nguồn cùng tầng trong O01. None cho phép suy chỉ ở tầng không có KC; [] là chủ ý không dùng dầm plan, không chứng nhận thiết kế không có dầm. KC rỗng/toàn keepFalse không tự lấp bằng suy. Tranh tầng hoặc count lệch phải pending; không chọn max chiều dài để giữ số legacy. Mapping tầng không chứng minh căn chỉnh XY; không lấy d tầng khác hoặc trừ KC lên hình học KT.

### 1. Tên/kiểu trường nhỏ nhất đề xuất

Đây là đề xuất để root duyệt trước code, không phải field đã tồn tại:

```python
class BeamViewScope(BaseModel):
    floors: list[str]             # ít nhất 1 khóa chuẩn, không lặp
    evidence: str                # không rỗng: căn cứ người dùng xác nhận phạm vi

class BeamFloorSource(BaseModel):
    source: Literal["structural", "manual"]
    ref: str                     # structural: key view; manual: tên PlanInput
    evidence: str                # không rỗng: căn cứ chọn/thay nguồn

# RoughRequest: optional/default để payload cũ vẫn nhận được
beam_view_scopes: dict[str, BeamViewScope] = Field(default_factory=dict)
beam_floor_sources: dict[str, BeamFloorSource] = Field(default_factory=dict)

# PlanInput: chỉ cần khi tên plan không xác định duy nhất một tầng
beam_floor_key: str | None = None
beam_floor_evidence: str | None = None
```

Không field DB/enum mới về mức tin cậy, không group cấu kiện hoặc field căn chỉnh XY trong O01. Hai trường trên PlanInput cần thiết vì mapping chỉ view KC→T2 không cho biết plan tên “Mặt bằng A” là T2 hay T3. Nếu root chưa duyệt cặp này, plan có tên không xác định tầng phải pending, không đoán ghép.

Khóa tầng tái dùng miền chuẩn của floors_of (T1/T2…, ST/MAI/MONG). Mapping tường minh phải dùng khóa chuẩn; không parse câu evidence. Scope/ref phải tồn tại trong request; source manual phải trỏ đúng một plan và danh sách dầm plan đã được chọn, không fallback từ None. Tên plan trùng làm ref mơ hồ cần báo lỗi/pending, không lấy phần tử cuối theo dict. Đề xuất kiểm lỗi cấu trúc/cross-reference rõ ở request validation; thiếu thông tin nghiệp vụ legacy thì giữ issue/partial, không làm request cũ không deserialize.

Map `beam_view_scopes` có mặt cho một view nghĩa người dùng xác nhận phạm vi trong evidence; không thêm cờ confirmed song song dễ lệch. Nếu map vắng, floors_of(title) có thể đưa phạm vi **suy từ tiêu đề**, có nhãn, không đủ tự giải tranh nguồn. PlanInput beam_floor_key tường minh phải đi kèm beam_floor_evidence; nếu vắng cả hai, dùng floors_of(name) chỉ khi đúng một khóa. Đề xuất thiếu một trong cặp là lỗi validation, cần root chốt.

### 2. JSON ví dụ

Phần bổ sung bên cạnh request hiện có (tọa độ/tiết diện dầm vẫn ở structural_beams hoặc plans[*].beams, không nhân bản geometry vào DTO):

```json
{
  "beam_view_scopes": {
    "KC_A_TANG_2_3_4": {
      "floors": ["T2", "T3", "T4"],
      "evidence": "Người kiểm xác nhận hình KC-A dùng Tầng 2, 3, 4"
    },
    "KC_B_TANG_4_5": {
      "floors": ["T4", "T5"],
      "evidence": "Người kiểm xác nhận hình KC-B dùng Tầng 4, 5"
    }
  },
  "beam_floor_sources": {
    "T4": {
      "source": "structural",
      "ref": "KC_B_TANG_4_5",
      "evidence": "Chọn KC-B cho Tầng 4; KC-A không tính thêm trên tầng này"
    }
  }
}
```

A vẫn giữ raw phạm vi T2/T3/T4, B giữ T4/T5. Phạm vi **hiệu lực sau chọn** là A:T2/T3 và B:T4/T5, không lấy số nhân3/2 gốc nhân thêm lần nữa. Nếu bỏ choiceT4, giữ known_part ở T2/T3/T5 và issueT4.

Ví dụ thay KC của T4 bằng manual (phần plans chứa tên này, beam_floor_key=T4, beam_floor_evidence không rỗng và beams manual không rỗng):

```json
{
  "beam_floor_sources": {
    "T4": {
      "source": "manual",
      "ref": "Mặt bằng kiến trúc lầu 3",
      "evidence": "Người dùng chọn dầm nhập tay cho T4 thay bộ KC; không cộng KC trên T4"
    }
  }
}
```

Chỉ là mẫu hợp đồng, chưa có request thật/case được kiểm. `source="manual"` không cho phép cộng đồng thời selected KC; danh sách chứa nguồn mixed/manual+inferred cần validation/issue rõ, không giả thành manual đã xác nhận. Không thêm choice “none” để suy rằng không có dầm; [] tiếp tục mang nghĩa không dùng dầm plan.

### 3. Quy tắc resolver và lỗi còn thiếu

- Tách validation count khỏi allocation: nếu `structural_floors[view]` được khai báo, đối chiếu với raw tập tầng của view trước khi chọn owner. Count thiếu entry không tự default1 để mâu thuẫn tiêu đề nhiều tầng; chỉ dùng tập đích đã xác định. Count lệch chưa biết tầng nào thừa/thiếu thì view/phạm vi đó pending, không phân bổ số count theo vị trí đầu danh sách.
- Chỉ có đúng một KC có scope hợp lệ ở tầng thì mặc định chọn KC. Hai view cùng tầng không dùng max chiều dài, kể cả trùng cả tập tầng; lựa chọn owner tường minh mới giải tranh. Các tầng không tranh vẫn tính phần biết. Nếu view có key nhưng rỗng/toàn keepFalse thì có dấu hiệu phạm vi chưa đủ/lựa chọn đã loại, không tự biến thành tầng thiếu KC để suy bù.
- KC thiếu tiết diện vẫn là nguồn được chọn nhưng quantity phần thiếu=None/D. Không đánh view “không hợp lệ” rồi tự chọn nguồn khác để làm đủ. Phải phân biệt invalid scope/ref với thiếu thông số hình học.
- Khi không có KC đúng tầng và p.beams=None, cho infer như hiện tại. p.beams=[] không infer, có cảnh báo lựa chọn không dùng plan beams; chưa coi đó là đáp án dầm bằng0. Không map được tầng plan thì không cho KC của tầng khác tắt suy toàn repo; đồng thời kết quả không được cam kết đầy đủ khi chưa loại trừ tranh phạm vi với KC chưa map.
- Scope/key/choice từ người dùng là phụ thuộc C có cấu trúc; scope suy từ tiêu đề cần nhãn suy. Không tự gán A cho toàn kết quả chỉ vì Beam.source=structural. Mức trần của nhãn scope suy (B hay chỉ issue chưa xác nhận) cần root duyệt trước gắn status; không parse evidence.

### 4. Caller/đầu ra ảnh hưởng — xin quyền trước triển khai

- RoughRequest/PlanInput (takeoff.py): nhận các field optional và kiểm liên kết; frontend hiện chưa gửi chúng. Không tuyên bố hoàn thiện ô chọn nguồn trên UI trong lượt backend.
- compute_rough: tạo allocation theo tầng **trước** vòng kiến trúc và vòng KC; dùng cùng quyết định cho việc sinh DAM/CP, cảnh báo BEAM, d của wall_params và beam_sources. Chưa căn chỉnh XY thì không dùng KC làm beams kiến trúc để trừ cột/sàn/tường. Nếu wall_params thiếu cơ sở riêng tầng, giữ issue/missing theo BA, không dùng d tổng các tầng để lấp.
- beam_works/beam_joints: giữ công thức và geometry thuộc nguồn gốc của nó. Phân phối theo tầng đích không nhân structural_floors thêm ở cuối. Không lấy p.columns chưa căn chỉnh để cắt KC. O02 tiếp tục quản lý trừ CP ô sàn; O01 không tự chuyển khoản trừ KC sang SAN của KT.
- WorkItem.plan/status/evidence: cần nhất quán tầng đích và view nguồn; đề xuất plan hiển thị tầng đích/plan KT chỉ khi mapping duy nhất, evidence giữ view/raw phạm vi/choice. Root cần chốt quy tắc nhãn trước đổi để không làm hỏng status theo plan hoặc sheet BOQ. Không thêm WorkItem schema mới tiện trong O01.
- RoughResult.beams đang là dict plan/view→geometry. Không lặng lẽ đổi key view thành tầng KT khiến UI coi XY KC là đã căn chỉnh. Có thể giữ geometry theo view gốc và tính beam_sources cho từng WorkItem.plan riêng; nếu cần output allocation mới phải báo tên/kiểu trước, không tự thay hợp đồng beams.
- Totals/materials/optimizer/BOQ dùng Q02 để giữ phần biết không tranh, D/missing của phần tranh/thiếu. Không để chỉ warning mà tổng bị hiểu là đủ.

### 5. Ca trước–sau để root duyệt DTO

| Đầu vào | Hiện tại đọc mã cho thấy | Mục tiêu sau DTO/resolver được duyệt |
|---|---|---|
| KC chỉT2; KT T3 beamsNone | T3 bị tắt suy vì dictKC có dữ liệu | Chỉ T2 ưu tiênKC; T3 được suy có nhãn và cảnh báo |
| T2 có KC và manual chưa chọn | Hai vòng có thể cộng cả hai | ChỉKC; manual giữ như nguồn chưa chọn |
| ChoiceT4 manual có ref/evidence | Chưa có hợp đồng chọn nguồn | ChỉmanualT4, không cộng KC T4; giữ nguồnC |
| A:T2/T3/T4, B:T4/T5 không choice | Hai tuplekhác nên không dedup, có thể nhân5 | T4 pending; known3tầng, incomplete |
| Cùng trên, choiceT4=B | Không có owner theo phần giao | A2tầng+B2tầng, đúng4tầng; raw phạm vi vẫn giữ |
| View tên mơ hồ count3 | Có thể nhân3 mà không biết tầng | Pending scope; không tự gán3tầng |
| Manual refkhông tồn tại/choiceviewkhông phủT4 | Chưa có validation tương ứng | Lỗi cross-reference rõ; không fallback |
| KC thiếu d nhưng manual đủ chưa chọn | Có thể tínhmanual rồiKC thiếu riêng | Không thay nguồn âm thầm; KC partial/D |

**Cổng tiếp:** root cần duyệt tên DTO/cặp field PlanInput, validation/cách ghi nhãn scope và output allocation/plan. Chưa ghi source/test, chưa chạy probe, không O02/K01. Backend đang khóa cho full session62154; báo cáo chuẩn bị này không thay kết quả full hoặc nghiệm thu O01.


## Chốt DTO BA — ĐÃ DUYỆT THIẾT KẾ / SOURCE HOLD

Điều phối đã duyệt BeamViewScope/BeamFloorSource, hai map request default{}, cặp beam_floor_key/beam_floor_evidence optional trên PlanInput như mục DTO ở trên. Chưa cấp ghi source/test trước khi full62154 terminal, hash sau được kiểm và root giao đúng vùng takeoff.

Ràng buộc đã chốt, thay cho các câu hỏi còn mở tương ứng:

- Floors thuộc đúng miền chuẩn floors_of, list không rỗng/không trùng, evidence không rỗng. Sai cấu trúc/cross-reference hoặc chỉ có một field trong cặp PlanInput → validation422. Payload cũ vẫn deserialize; thiếu scope nghiệp vụ giữ pending, không suy bổ sung tầng để bảo toàn số cũ. Evidence người dùng không có nghĩa đã được người kiểm độc lập xác nhận.
- Scope suy rõ từ tiêu đề: trần B với structured inputs/evidence; mapping hoặc chọn/thay nguồn người dùng: trần C; tranh/missing: D. Dùng prior_status/inputs assign_status hiện giữ lại; không sửa status.py hoặc parse evidence để quyết định trạng thái.
- WorkItem KC giữ view gốc và tầng đích rõ, ví dụ “KC-A → T2”; BT/CP/thép hàm lượng cùng nhãn. Manual/infer theo plan gốc, evidence ghi khóa tầng. Không mượn PlanInput.name để giả đã căn chỉnh XY.
- RoughResult.beams giữ key geometry view/plan hiện có. Không thêm output allocation/schema mới trong lượt backend; evidence WorkItems phải đủ truy vết nguồn, owner, phạm vi và tầng đích.
- Không dùng KC khấu trừ KT/cao tường khi chưa có alignment/căn cứ riêng. params.beam_depth_mm do người dùng nhập vẫn áp theo hợp đồng cũ; chiều sâu manual chỉ theo plan của chính nó. Không đọc d của tầng khác để lấp phần thiếu.
- Thiếu scope/count mismatch/KC rỗng không fallback làm đủ. Giữ phần số biết đã chứng minh và sinh pending DAM/COP_PHA(of DAM) quantity=None/missingD cho phần chưa biết, để totals/materials đi đúng Q02. Không thêm pending thành số0, không nâng tổng phần biết thành tổng đủ.

Điểm khóa trước source: full session62154 và snapshot tích hợp; takeoff đang có N03 + dữ liệu thực xây của writer khác. Chỉ triển khai khi root cấp rõ vùng request/PlanInput/resolver/callers và test liên quan. Không tự mở O02/K01, không sửa beam_works/status/roughmodels/DB/frontend tiện trong O01; cần mở file khác phải báo ảnh hưởng trước. Lượt này chỉ ghi tài liệu, không test/probe/code.
