# Contract thang cho06/17 — source freeze

Schema máy đọc: STAIR_CONTRACT.json. Không cần đổi DB/schema20bảng. Root01 quyết định tích hợp;03 chưa chạy API/UI/runtime.

## Stair

- id, from_floor, to_floor, scope_source: phạm vi từng thang; tầng đầu/cuối đi cặp. scope_source phải có căn cứ đủ về bộ component, không autofill từ tên tầng.
- steps_material = concrete|masonry|unknown(defaultunknown); steps_material_source. Mất nguồn thì unknown trong phép tính, không lấy defaultconcrete.
- waist_thickness_mm, waist_thickness_basis = normal|vertical|unknown, waist_thickness_source: theo từngthang. Chỉ normal có nguồn được dùng cho bản nghiêng; flightoverride cónguồn riêng ưu tiên. Không điền ProjectParams120toànnhà; H150chiếutới khônggánvế.
- flights: list[StairFlight] hoặcNULL. Field mỗi flight: id,run_mm,rise_mm,width_mm,waist_thickness_mm,thickness_basis,step_count,tread_mm,riser_mm,field_sources(dictfield→source). geometry thiếu nguồn→partial. Chỉ step_count/tread/riser cónguồn mới tính bậc concrete; khôngsuy từH/n.
- landings: list[StairLanding] hoặcNULL. Field mỗi landing: id,area_m2,thickness_mm,ownership stair|floor|beam|unknown,field_sources. ownershipcũng cầnnguồn; floor/beam đượcgiữreference, khôngcộngBT/CPthang. NULLkhác[]đãchốtphạmvi. IDvế/chiếu khôngtrùng; sốđo finitepositive(diệntíchcho phép0cónguồn).
- formwork_scope_source OPTIONAL: chỉ có khi receipt xác nhận cácmặt đãliệtkê làđủ, khôngmặt cạnh/gối/giao khác. Thiếu→CPpartial; nguồn này khôngđiền geometrythiếu hoặc vậtliệubậcunknown.
- Fieldlegacy steps/flight_width/tread/landing_area/beam_* đượcgiữđểroundtrip/thamchiếu; khôngdùng thaygeometrycácvế, khôngcộnglegacybeam khi chưa cónguồn/giao.

## Output

CAU_THANG: signedcontributions cho từng bảnnghiêng/bậcBT/chiếuowned; bậcmasonry làreference0khôngđónggópBT. XAYbậc phátNULL/D với lýdo thiếugeometry/quycách, không tựchọn gạch/vữa. COP_PHA giữđáy/mặtđứngBT đãbiết, bậcxây khôngthêmvánđổBT; mặt/giao chưa rõ→partial.

quantity=phầnbiết(legacyround3) khi có; nếu chỉ córeference0vàmọigeometryunknown thìquantityNULL, không0. quantity_detail.known_part_rawgiữrawtrướcround, total_rawNULLnếuchưađủ;missing/statusDgiữnguyên. Componentfull cónguồn đượcgánCbảo thủ, khôngAgiả từnhậpmanual.

HplanNULL: thang vẫnđượcemit từcomponent riêng; walls/cácphầnphụthuộcH vẫnchặn. Không dùngHplancho từngvế. Khôngcopytemplatecấu tạo/dày/source/sốbậcgiữacáctầng chỉvìrộngvếgiốngnhau.

Actualreplay là SCOPED_SOURCE_REPLAY với source chua_kiem/humanapprovalfalse, khôngoutputCADauto. Chưa cóH/run/width từngvế,area/ownchiếu,giaoCP nênBT/CP/XAYNULL/D. KhôngnhânkgBẢNGTHÉPT1SL1 theo3vếhoặc17bậc; khôngdùngDAIthép làmrun/slope. Khôngautofillfromfloor/height185×17 hoặc lấy+3.900củathangtiếp.
