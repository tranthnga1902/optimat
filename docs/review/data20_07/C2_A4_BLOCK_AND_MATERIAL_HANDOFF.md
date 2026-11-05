# Bổ sung nguồn block thật và vật liệu C-2 cho01/03/02

## Block nguồn — nguyên nhân gói đầu thiếu trục/hìnhcột

Artifact **`docs/review/data20_07/C2_A4_CAD_BLOCK_SOURCE.json`** (440KB), cùngKC hash22cda910… có4INSERTgốc,6blockdefinitions,142entity chiếu ra world từ blockmặtbằng thật. Gói đầu chỉ lọc điểm chèn theo cửa sổ nên **bỏ sót INSERT có origin nằm xa vùng nội dung hiển thị**; không kết luận CAD thiếu hình/trục từ gói đầu.

Root hìnhmặtbằng **INSERT11844AA**, block`qqqe213123213`, điểmchèn(96733,936046;−46366,127120) nằm ngoài cửa sổ, nhưng boundingbox sau transform **x[−1845653,080204;−1825693,079826], y[−1104490,127246;−1096430,126994]** nằm ở hình cần đọc. Root này chứa hìnhhọc/trục, khác các TEXT/DIM/LEADER đặt ngoài block tại modelspace.

Callshape: `roots` giữattributes/matrix44rows/attribs; `block_definitions[name]` giữbase_point vàentitysource. `world_entities_physical_plan` là cácentityvirtual sautransform, mỗi dòng có`source_path` bảo toàn handle gốc khiezdxf cung cấp; không dùng virtualhandle rỗng làmID thật. Chỉ dùng **một** cách biểu diễn (raw+transform hoặcworld) khi nhận dạng, không đếm cảhai.

Chữtrục thực sau transform: trục4 sourcepath`11844AA→1163C71` và`→1163C7D`; A`→1163C75/1163C81`; B`→1163C76/1163C82`. Cùng artifact cóLINE/CIRCLE/hìnhbiên để readerkiểm giao trục/định vị, không chốt tim chỉ bằng tọađộchữ. Hai nhãnC-2 modelspace vẫn là11844DA(4/B),11844E1(4/A) tronggói đầu. Phải ghépsource leader/hìnhbiên theo hìnhhọc; không ép nhãnoracle4/A vào production. Dùnggói cũ cho detailcaođộ/slabH120 vàgói bổsung cho blockmặtbằng; bbox là cửa sổkiểm, không là outputreader.

## Quy cách vật liệu đọc từ hồ sơ, chưa là lựa chọn catalog

- Mặt cắt **2–2 p22**: hai nhóm **2Ø20 +2Ø20**, tổng4thanh dọc trong mặt cắt; đai **Ø6 a200**. SourceCAD tronggói đầu: tên2–2 TEXT1185923; chữ2Ø20 TEXT1185C10/1185C24; Ø6 TEXT1185C14, A200 TEXT1185C15. Chỉ dẫn số hiệu trongraw có thể làATTDEF/legacyglyph; ảnhPDF hỗ trợ đọc quy cách, không lấy ký hiệu2–2 làm trụcnhà.
- Grade theo đườngkính tại **p3 KC-00, bảng3**: Ø20 **CB-400V** (TEXT10FFB11); Ø6 **CB-240T** (TEXT10FFAEF). Cần kiểm liên kết dòngDK bằng bảngPDF `reports/review_housing_20261103/sang_notes_page3.png`; không tự gán grade thép dọc cho đai. HàngØ12 CB300V không áp vàoØ20.
- **Bê tông:** bảngvậtliệu ở p2KC-00 ghi nhómcột/váchM250. Đã trích note **B20(M250)** từ block`GHI CHU NHA BE TONG 2`, TEXT **11058EA**, rootINSERT **118449B** tronggói bổsung; raw chữlegacy giữ nguyên và readercầnáp transform của root. Các tờchi tiết cùnghồsơ cũng có note này, xem ảnhtoàntrang17 `TWO_DM1_WATER_CONTEXT.png`. Đây là ghi chú thiết kế, **không phải chữ trực tiếp trên mặt cắt2–2**. Grade/mác không tự xác định đá, độsụt, cấp phối hoặc phương thức mua.

Chưa có khối lượng thép đoạn3,150→6,750 theo từngthanh/uốn/nối; **4Ø20 vàØ6a200 chỉ là quy cách bố trí**, không là nhu cầu mua. Chưa ánh xạ concrete/steelgrade sang mãmaterials/catalog hoặc tínhbao/thép dài thươngmại. Thiếu quy cách mua/định mức phải hiệnthiếu; không nhúng mã vậtliệu hoặc oracle vào runtime.

Lượt07 chỉtríchnguồn vàghiartifact, không sửa reader/sourceproduction/canonical/DB hoặc chạy runtime/full. Trạngthái chưa duyệt giữ nguyên;6block/142entity không là sốcấu kiện thật.01/03/06 có thể dùng để váreader generic theo quyền đượcgiao.
