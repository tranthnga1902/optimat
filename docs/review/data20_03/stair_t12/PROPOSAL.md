# Cầu thang VN002 tầng1→2 — rà nguồn và đề xuất hunk

Ngày04/11/2026. **Chỉ đọc/đề xuất, chưa được cấp sửa canonical hoặc chạy runtime/test.** HelperC2 vẫnfreeze6bb3…, không reuse hoặc mở lại. RootP0confirm được ưu tiên.

## Nguồn và mức xác minh

- Đã xem docs/review/data20_07/STAIR_WAIST_DETAIL.png: ghi BẬC THANG XÂY GẠCH; DIM120 đặt vuông góc hai mặt bản nghiêng. Đã đọc STAIR_T1_SOURCE.json: waist120normal, upperlanding150, candidate3vế chưa giải hết hình học; volume vàCPareaNULL, approvalchua_kiem/humanfalse. Bảng thép phạmviwholeT1SL1, không nhân theo sốvế.
- Theo00/01: KTp19KT-17mặtbằng; p20KT-18cắt1–1/2–2 có3vế/bậc1–17/hai vùng đổi hướng; mặtbậc nhiều chỗ250,cổ185 nhưngđầu/cuối chênh; +3.150ởbậc17,+3.900thuộc thangtiếp. Cần đối chiếu sảnhKT+0.150 vàKC±0.000. Hai path tmp/vn002_kt_ct_19.png/20.png không tồn tại tại repo khi03kiểm, nên03 chưa tự xem/khẳng định nguồnKT này.
- Chưa cósource_native/DIM/levelscope đủ từngvế, landingclearbounds vàquyền sởhữu giao. Không lập thểtích hoặc dựtoán dựa lời mô tả/PDFbơm tay.

## Hiện trạng consumer thật

1. rough/stairs.py::Stair chưa có vậtliệubậc, chiều dày bản riêng từng thang, danh sách vế/caođộ hoặc chiều dày chiếu nghỉ riêng. landing_area_m2 mặcđịnh0 dễ lẫn chưa nhập với khôngcó.
2. stair_works lấy duy nhất params.stair_slab_thickness_mm; H lấy p.height_mm từ compute_rough. slope=hypot(n×tread,H); slab=w×slope×t; luôn cộng steps=n×tread×(H/n)/2×w. Landing=area×cùngt, không phân biệt150toplanding/120waist. CP luôn thêm n×(H/n)×w thànhbậc.
3. detect_stairs suy sốbậc từnét+1, gộp cácvếsong song cạnh nhau; khôngđọc ghi chúbậcgạch/DIMnormal/level của từngvế. building_stairs cócopy mẫu nhiều bậc nhất giữa các mặtbằng chỉ dựabềrộngvế, chưa chứngminh cùngcấu tạo/scope. Bậc trêntầngmái bị bỏ theo tên.
4. drawing/viewer.py::plans_data và takeoff.py::rough_from_drawing gọi building_stairs; compute_rough gọi stair_works với height của plan. Frontend model.ts giữ thangđầu đểchỉnh, spread metadata từst0 vàgiữtail stairs; nhưng vẫn ép landing rỗng→0. Chưa cófield nhập/source/hiểnthịcho cấu tạo bậc vàtừngvế.
5. tests/test_rough_stairs.py::test_two_flight_stair và test_work_dimensions.py::test_stair_horizontal_slope_steps_landing_and_beam_are_separate đang assertcộngBTtamgiác theo giảđịnhcũ. tests/test_rough_stairs_detect.py::test_partial_flight_takes_full_stair_of_building đang assertcopy mẫu sang tầngkhác. Cần đổi tiềnđề test cónguồn, không xóaassert để né lỗi.

## Contract đề xuất — theo từng thang trong snapshot

Đây là đề xuất, chưa thành API/schema đã triển khai:

- Stair giữ id/mark riêng với from_floor/to_floor; markT1 không mặc nhiên là tầng1. source file/revision/hash/view/handle hoặc page/region cho từng field, nguồn nhập/cáchđo vàmức xácnhận.
- steps_material: concrete|masonry|unknown vàsource/scope của note. Không coi trường vắng là concrete. Note chỉ cóhiệu lực cho thang/chi tiết được nối, không cả nhà hoặc mọi thang cùngmã.
- waist_thickness_mm + thickness_basis=normal + nguồn theo từngthang/vế. **Không điền ProjectParams120toànnhà.** Không áp normalformula cho chiều dày đứng; nếu cần đổi hệ đo thì phải cógóc/hình học/source rõ.
- flights: mỗi vế có id, start/endlevel hoặc rise cónguồn, run_horizontal_mm đo được, width, waistnormal và liên kết với các vùng đổi hướng. riser_count khác tread_count; không suy run=n×tread hoặc H=n×185 nếu chưa chứngminh quan hệ.
- landings: từng phần có area hoặc boundary rõ, thickness riêng, level/basis vàownership(thuộc thang/sàn/dầm/chưa rõ). H150ởchiếutới khônggán mọi chiếunghỉ hoặcvế. Không trừ/cộng ôgiao hai lần.
- Scope level phải phân biệt mặt hoàn thiện/đáy hoặc mặt kếtcấu; KT+0.150 vàKC0 không đủ để tự lập mộtoffset+150toànhồsơ. +3.900thuộc thangtiếp không đưa vào vế T1→2.
- Thiếugeometry: giữ nullable/missing vànguồn chouserkiểm. Nhập cónguồn theo từngthang là nhánh đượcusercho phép, không giả vờ đãparseCADtựđộng.

## Hunk tối thiểu cần01 chốt sauP0

### A — chặn vậtliệu bậc sai và nguồn dày riêng

Ownerđềxuất03: rough/stairs.py::Stair/stair_works + tests/test_rough_stairs.py và testfile mới chuyênscope. Bậcmasonry **không cộng BTtamgiác** vàkhôngtính vánkhuôn đổBTthànhbậc nhưconcrete; unknown giữphần bậc/CPthànhbậc pending. Lượng bảnnghiêng/landing/beam chỉ tính khi geometry vànguồn đủ. Nếu cần phát bậcxây, tách nhu cầu XAY cósource/quy cách; thiếu dữliệu thìpending, khôngtựchọnmãgạch/vữa hoặcđịnhmức.

Đổi testcũ thành steps_material=concrete cócăn cứ đểgiữkiểm côngthứcBTbậc; thêmmasonry/unknown. Không giữdefaultconcrete imlặng chỉ đểtestcũ đạt. Cần01chốt cách xửlý payloadlegacy thiếufield trướcedit.

### B — hình học nhiều vế, chiếu nghỉ vàsnapshot

Owner03đềxuất trong stairs.py; takeoff.py chỉ đúngcallerhunk được01cấp đểkhông lấyHplan áp mỗi vế; viewer.py reader notes/geometry cầnowner01chốt. Khôngreuse C2_linearDIMhelper lọc toàncục ngang/đứng cho DIM120vuônggóc bảnnghiêng: phải đối chiếu vectorDIM với bản/vế.

Côngthức riêng từngvế: L_i=hypot(run_i,rise_i), V_bản=Σ width_i×L_i×t_normal_i. V_landing=Σ owned_area_j×t_landing_j; beam riêng vàgiao córeceipt. Tổng bậcconcrete chỉ từ geometry của bậcconcrete đúngscope; masonry không vào CAU_THANG_BT. Không nhân chiều cao tầng cho mỗi vế.

02giữ UI/model.ts: nhập vàgiữfield theo từngStair/snapshot; khôngrỗng→0 hoặc biến nhánh nhập nguồn thành auto.06giữ API/mapper: giữfields/source/scopemapping;04giữ materials/MaterialUse; chưa đụng sharedmodels.py/materials.py trongphaseA. status.py nếu cầnđổi phải xinownerđúnghunk, khônggán hoàn tất theo ProjectParamsglobal khi nguồnthangkhác.

## Test cần giao — chưa viết/chạy trong lượt này

1. Cùng bản/thông số, steps_material=masonry: không cóBTtamgiác, khôngCPvánkhuônbậc đổBT; concreteexplicit vẫn giữ côngthức đãduyệt; unknownkhông tự thành concrete.
2. Note masonrycủa thangA không ảnhhưởng thangB; cùngmarkkhác tầng/scope/file/revision khôngbind tựđộng.
3. Ba vế rise/run riêng: cộngΣhypot, khônghypot(sumrun,Hfloor) hoặc3×Hfloor. Thiếu rise/run mộtvế giữmissing, khôngchia đều theo tổngsốbậc.
4. 120normal áp cho đúngwaist;150toplanding áp riêngđúngcomponent; không đổi vế khác hoặcProjectParams.
5. Mặtbậc250/riser185 chưađủđể17×185chốtH; +3.900khônglọt vàoT1→2; kháclevelbasisKT/KC giữpending.
6. Landing chưa nhập khácarea0đãxácnhận; landing đãthuộcSAN khôngcộnglặp trongCAU_THANG; CPside/support/jointmissing khôngthành đủ.
7. Không dùngDAIthép làmLslope; wholeT1scheduleSL1 không×3vế/×17bậc; thiếusteel scopekhôngđổikgm³.
8. JSONsnapshotroundtrip/source/manualconfirmed đượcgiữ; rowIndex khớp đúng snapshot, khônggán lại theo mã.
9. Reader khôngcopy cấu tạo/material/level/tầng từtemplatewidthmatching sangthangkhác khi khôngcócăn cứ.

## Ownership vàbàn giao

03chưa sửa source/test. gitstatusđangcó stairs.py modified(130insertions/5deletions sovớiHEAD), là trạngthái cósẵn khi rà, không chứngminh cówriterđangchạy hoặc làdiffcủa03.04knownhunksMaterialUse/materials,05knownhunksrebar/columns khôngtrùng stairs.py, nhưngcần01xácnhậnsolewriterchínhthức trướcedit. Đãgửi01 kiểm ownership; chưacấphunk thìgiữproposal-only.

READ_HASH.json ghi cácfile đãđọc vàảnhKC; khônglàmtest/hồiquy/CADactual/runtime/DB/build/browser/AI hoặcđổi20bảng. QA25emptytheothôngbáo01 khôngđược thay bằng dữliệugiả. KhôngcôngbốVthang/các%hoànthiện từđềxuấtnày.
