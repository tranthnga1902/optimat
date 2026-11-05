# Ma trận QA độc lập — luồng kiểm khối lượng

Ngày chuẩn bị: 03/11/2026. Vai trò QA15; chỉ ghi thư mục này. **Chưa chạy ca nào trong ma trận; chưa nghiệm thu sản phẩm hoặc hồ sơ thật.**

Luồng chính mới nhất theo PLAN và kế hoạch ưu tiên: `/do-boc` → `/phan-tho` (kiểm/lưu) → `/toi-uu` (nhận nháp toàn phần thô, so sánh AI, xác nhận cả phương án). `/dieu-chinh` và xem giá `/vat-lieu` là tùy chọn. Các ca cũ bên dưới có thứ tự tuyến tính đọc theo thay đổi này; không bắt buộc chọn tay vật liệu/materials-ready thủ công trước mở tối ưu. Giữ gate khối lượng đã kiểm và invalidation. Ca AI23–26 trong AI_MATERIAL_ACCEPTANCE.md là cổng nghiệm thu bổ sung bắt buộc.

Trọng tâm demo đã điều chỉnh bắt buộc: **AI hỗ trợ lựa chọn vật liệu toàn bộ phần thô**, thay thế giới hạn nhóm tường trước đây. Ca AI01–AI15 và bằng chứng API thật có điều kiện tại [AI_MATERIAL_ACCEPTANCE.md](AI_MATERIAL_ACCEPTANCE.md). Đối chiếu mọi công tác đã kiểm theo tầng/cấu kiện với vật tư, không phát sinh hoặc thiếu có lý do; chỉ gạch/vữa chưa đạt. NSGA-II tường không chặn tư vấn nhóm khác. Hỏi công thức dòng là phụ. Giữ cổng bảo toàn dữ liệu, khối lượng đã kiểm và xác nhận trước áp dụng.

## Điều kiện mở lượt QA

- Phiên 01 release lịch, nguồn freeze và phạm vi chạy. **Phiên 05 J04 là sole full**, chỉ chạy khi 01 cấp lịch; phiên 02 sở hữu frontend, browser và API restart, không sở hữu full. Ghi hash trước/sau và terminal đầy đủ. Không tự nhận thông báo phối hợp là quyền mở rộng phạm vi.
- Trạng thái nguồn theo điều phối mới nhất: 03 đang WIP backend dimensions; 02 WIP frontend; 04 audit hợp đồng snapshot trước consumer edit; 14 review độc lập. Chưa coi mã hiện tại là freeze.
- Không chạy full, mở Chrome, sửa sản phẩm/tests/scripts/catalog, reset DB, commit hoặc deploy trong lượt chuẩn bị.
- Upload `tan_binh_kien_truc.dxf` tới `http://127.0.0.1:3000` đã bị gate báo user declined. Không thử lại hay dùng native/API/browser khác cho cùng upload. QA hồ sơ này chờ người dùng tự chọn file hoặc cấp lại quyền.
- Chọn đúng bộ ACTUAL-build KT+KC và đáp án đối chiếu; giữ nhóm test kín. Không dùng fixture/mẫu/overlay để kết luận sai số thật.

## Ma trận

### DrawingWorkList dưới Board — chờ02 handoff incremental

**Review/focusedgóifreezeđãnhận:**manifest0a3b0f3f...khớpverification;6overlayhashkhớp vàstable. QA15chạycheck-work-list.cjs trên2overlay,đềuexit0;receipt/logs `docs/review/data20_15/work_list/`. StaticReviewdelta chỉimport+renderdướiBoard/preview+modeltype,khôngđổistamp/P0logic. Đây làsourceSSR/harnesskhôngbrowser.

**Giới hạnWL01/02:**componentlàdanhmục **dấu hiệu nhận diện** từwalls/columns/stairs/found/drawing_work_signals,khôngresult.works/workkey/quantity/receipt. Nênkhôngclaimbảngcôngtáctínhxong/địnhtuyếnrow/sourceCAD. Structuralglobal hiệnnhãncầnđốichiếutrướcgántầng,khôngfakeposition;drawing_work_signalsglobal chưaghi nhãn“toàntệpkhôngriêngtầng”nêncầnnêuscopekhiindex>=0. p.stairs dùngnguồngốckhôngparamsđãsửa/cờkeep;đúngdanhmụcnhậndiệnnhưngkhôngsốthangđãchốt. Đềnghị02/01làmrõtên/scope,khôngtựmởwriter.

WL03P0chỉstaticdelta khôngthayhandlers,SSRkhôngchứngminhregressionstampinteractive;WL04scroll/keyboard/layoutvẫnNOT_RUNđợifixturebrowserlease. KhôngpromoteQAroutevàorelease/khônginjectstorage.

01bàngiao:02đangtíchhợp2fileincremental trênP0v3,khôngwholeReview;QAUI3003PID29856→8003hiệnchỉP0build,originmớichưadata. 3002userdraftactive,chỉrootđọc/khôngreload. QA15chờexact2file/hash+lease;browsergate**BLOCKED_NO_ALLOWED_UI_DATA** đếnkhi3003códataqua luồngđượcphép;khônginjectstorage/noTânBìnhreupload. Sourceharnessnếucó chỉgọilàharness,khôngUIpass.

| ID | Tiêu chí review/QA dự kiến | Gate |
|---|---|---|
| WL01 P0 | Worklist hiện dướiBoard,đúngsnapshot/tầng/subset/workkey,khôngtựgánconfirmed | 02artifacthash+consumerbinding |
| WL02 P0 | Chọn dòng/đốichiếunguồn đúngcấukiện,khônggánvịtríCADgiả;missing/NULL/statusgiữ | Sourceharness vàUIđượcphép táchriêng |
| WL03 P0 | Partialworklist khôngtổnggiả/exportscopekhôngmất;P0confirm/stamps khôngregress | Incremental2filekhôngoverwritedeltaP0v3 |
| WL04 P1 | Layout dướiBoard,scroll/keyboard/names/empty/loading/error | Browser3003códatađượcphép,khôngchỉmockDOM |

### P0 lỗ mở widthNone — criteria-only chờ06/02hash+01lease

01DOMobserve3002/phan-tho khoảng47workfloatparseerror,đangthuresponse;chưaQA15runtime/findingrootcause.06ownerReviewOpening/consumers,02serializer/confirmfilter/formatterfullpath;khôngtrùng03stairs/05rebar. TấtcảOP01–07NOT_RUN,khôngtest/full/DB/browsertrướcrelease.

| ID | Input độc lập | Expected |
|---|---|---|
| OP01 P0 | width=NULL,heightđủ vàwidthđủ,height=NULL riêng | OptionalunknownđượcgiữNULLđúngfield/source,khôngfloatparseerror/0giả;IDopening,parentwall,scopekhôngmất;phụthuộcthựcgiữpending |
| OP02 P0 | Cùngwall/groupcóknown+unknownopening | Giữknownpart/reasonunknown;khôngdropunknownđểclaimnetđủ,khôngdoubletrừ;raw/gross/netphânbiệt |
| OP03 P0 | Haiwall/groupchỉmộtnhómbịthiếudim | Nhómbịảnhhưởngpending,nhómđộc lậpvẫntính;totalđãbiếtkhônggọiđủtoànscope;khôngglobalfailhoặctựbỏID |
| OP04 P0 | keep=falsewidth/heightNULL | Giữrecord/source/parentvàcờloại,khôngđưaopeningđãloạivàokhoảntrừ;khôngđòidimđểtínhnhómkhôngphụthuộc,khôngtựkeep=true |
| OP05 P0 | invalidstring/rỗng,âm,NaN/Infinity,widthvàheightparametrize | Validation/normalize theoexactcontract,khôngépstringrác/âm/nan thành0hoặcchấpnhậnJSONinvalid. Lỗimessagerõ,khôngmấtdraft/source;NULLkhácinputinvalid |
| OP06 P0 | Source→serializer→confirmrequest→roughresponse→formatter/table/detail/reload | Khôngserializer/filterdropIDparent/missing;khôngtoFixed/Number/parseFloatbiếnNULLthành0;stale/project/revisionguardP0giữ,khônglưuconfirmedgiả |
| OP07 P0 | Partial→Excel/BOQ/materials/optimizer | Dòngthiếuvẫnhiện,lýdođúngnhóm;khônggiámua/optimizerquantity/tổnggiảtừknownpart;nhómđủvẫncócăn cứriêngvàcoveragechi phíphảighi rõ |

Cần01bàngiaoresponseevidenceđãloạibímật,exactnullable/errorcontract,sourcehashvàtesthunklease;QA15khôngtựsửamodelđểbypassvalidation. DanhsáchcheckboxFS giữchờ,khôngdùngfixnullableđểđóngsubsetgate.

### Checkbox chọn tầng — nhiệm vụ mới05/11, chờ01/02artifact vàslot

QA15 đãliênhệ01xinexactcontract/hash/receipt,canonicaldo-bocchưa tìmthấyfloorselector mới tronglượtđọc;khôngcoicâycanonical là3002runtime. TấtcảFS01–07NOT_RUN,khôngDBmainwrite/browser/testtrướcrelease.

| ID | Ca độc lập cần chứng minh | Oracle |
|---|---|---|
| FS01 P0 | Chỉ chọn tập con A từA/B/C;B/Cchưa xác nhận | Ađiđượckiểmcôngtác theođúnggate;B/Ckhôngchặn/khôngbịtựchốt hoặcđổi thànhthamkhảo;result/receiptghi rõsubset |
| FS02 P0 | Quaylại chọn/tớiB/C rồitrởA,reload | Giữnguồn/file/revision/hình/tầng vàtrạngtháingoàiscope;đổisubsetinvalidationđúng,khôngdùngreceiptchỉsốdòngcũ |
| FS03 P0 | Một tầngnhiềuhình;viewdùngnhiềutầng/nhãnchưarõ | Đếmtầngnghiệpvụkhácsốhình/checkbox;khôngauto nhân/đếmđôi,khônggánfloorgiả |
| FS04 P0 | Autoselectthiếudữliệu/nghitrùng/cảnhbáo | Nêunguồnvàlýdo;khôngtựconfirm/scope/height,mụcnghitrùngkhôngâmthầmbỏ;userđiềuchỉnhđược |
| FS05 P0 | Bỏchọntấtcả | CTAdisable cólýdo,khôngPOST/khônggiữsubsetcũngầm |
| FS06 P1 | Tab/Space/ShiftTab,names/focus | Checkboxnativelabelrõ,trạngtháireadable,keyboardtoggle/focuskhôngmất,khôngchỉpointer |
| FS07 P0 | 3002P0confirm/networkcached/recovery vàchọnscopekhiđangawait | Oneflight/stale/fullcontext/persistatomic/partialrestorekhôngregress;khôngPOSTthayhìnhngoàichọn,khôngreusecachedsaisubset |
| FS08 P0 | Chọn1/2tầng từ11nhóm;chọn tấtcả/bỏ/chỉcầnkiểm | Gatekiểmchỉsubsetthật,khôngrequireall11;bulkbuttonsđúngflagscontract,mụcngoài khôngtựreference/checked/confirmed. Chỉcầnkiểm khôngâmthầmđổiphạmvi thiết kế |
| FS09 P0 | Một tầng có2view,đổinhóm chọn,sửa draft rồiquaylại | Chọntầngkhôngmặcđịnhcộngmọiviewtrùng;giữdraft/tùychỉnhcónguồn,khôngresetngầm;invalidatework/receipt/material/optimization đúngscope/revision,khôngmấttầngngoàichọn |

Nguồnrequest00;01/02giữproducer/runtimelease. KhôngcầnthửghiDBchính;fixture/harness/browserread chỉtrongslotđượccấp. Báo00khiđủkếtquả,táchSTATIC/SYN/liveUI/E2E.

01chốttriểnkhai3002trước,cả3001sau;hunk02selector/chỉnhscope khác17thangoverlayđangfreeze. QA15criteria-only,khôngviếtchung/test/full/DB/browser đến02contract+01lease. Flagsbulk/địnhnghĩa“cầnkiểm”phảiđọccontractthật,tránhQA tựđặtlogic làmconsumerpassgiả.

Currentruntime theo01:3001PID39344 build9YNZoA-zaLYiXseciOaUF→8001PID40212/DBoptimatverified,3page200/15assets/proxy58path gồm2assistant;receipts web80_3001_20261104_102839_177.json vàcandidate8001_verified_20261104.json/80hashstable. F01–F03source/focused/type/lint vàOriginmock8pass đãnhận. Các mốcWIP/3001→8000cũ bên dưới làlịchsử;3000/8000giữnguyên/5roleDBđãáp. Chưabrowser4mốc/ACTUAL/80;01solebrowserattachtimeout/login,chờuserselfchoosefile,QA15khôngruntime/ảnh/upload/Start/LLM.

Cập nhật01:DBdelta5roles committed_verified/API10060=DBoptimat/CHECKvalidated,countOIDstable chỉDBdelta,chưarestart/mixedfileUI. MaterialAdvisor F02/F03 hash02B29C...type/lint0 chưabuild/Chrome;F01 vàOrigin127.0.0.1:3001/HTTPmock cònWIP.01 solebrowser chờuserlogin. Các mốc “5roleschưaáp/02browser” cũ được thay bởi cập nhật này;không cộng điểm4mốc,giữACTUAL/D02/G8P03–P07.

Đối chiếu bốn mốc WebUI đầu và timeline ảnh/receipt T0–T6 tại [WEBUI_FOUR_MILESTONES.md](WEBUI_FOUR_MILESTONES.md). Mốc1 hồ sơ là ứng viên đóng sớm nhất sau userlogin và release02/06, chưa là đạt;không ghi%thựcđạt từ điểm đề xuất/testcount. Sample_floor thiếu nhómphi tường phải ghi giới hạn,không ghép hồsơ.

Mốc04/11 mới do01 xác minh và sprint còn mở được ghi đầu CHAIN_ACCEPTANCE_GAPS.md:fullretry1096pass/19skip/15deselect,263hashstable chỉ pure;mainhooksource accepted nhưngAPI8000 chưaassistant;frontend3001 verified đangchờuserlogin;5roleDBchưaáp/targetchưaverified. G8P03–P07,mixedfile/DOC/DB/runtime,CH01–05,AI/UI/runtime,ACTUAL/D02,Excel/UIcùngrevision còn mở theo bảngowner/exit/nextaction. NativeNOT_RUN/D02humanfalse/P03permissionpending giữ riêng. QA15 không runtime.

Ca xuyên chuỗi mới CH01–CH05 và khoảng trống bằng chứng tại [CHAIN_ACCEPTANCE_GAPS.md](CHAIN_ACCEPTANCE_GAPS.md): bảng mua→báo giá→lượng mua→norm/hao hụt từng phần góp→work đã kiểm→cấu kiện/bản vẽ/revision; dòng thiếu phải còn UI/bản xuất. Chưa có E2E đạt; QA15 chỉ đối chiếu docs, CAD23 vẫn dừng theo user.

Bổ sung PF22–25: PDF-only lưu/reopen/view/download không ép CAD; mixed CAD/PDF/Word/XLS/XLSX theo reader thật; role history giữ bytes/hash, provenance ownership/revision/page/sheet, tách khối lượng nguồn đối chứng với khối lượng bóc và giữ chênh để duyệt. Role enum đang chuẩn bị, chưa runtime/upload mới trước release01.

Hồ sơ trước phân tích tại `/du-an-cua-toi`: ca PF01–21 trong [PROJECT_SOURCE_ACCEPTANCE.md](PROJECT_SOURCE_ACCEPTANCE.md), gồm version/nguồn/quyền, preview không tự đo bóc, inline EDIT từ VIEW và bố cục mới desktop SPLIT list trái/detail phải, mobile list→detail không overflow. Ảnh user17 mới thay ảnh gửi nhầm, không dùng dữ liệu ảnh làm nguồn. QA15 chưa chạy; hiện02 giữ ca server23, QA15 chờ receipt/timeline review độc lập, không upload/Start/delete.

### Thứ tự thực thi theo ưu tiên hoàn thiện mới

Đã đọc `docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md` và `docs/PHAN_VAI_CAC_PHIEN.md`. Chuẩn bị song song, không mở thêm quyền chạy. QA15 lập ca; 02 thao tác browser theo lịch 01; 05 là sole full. Không mở Chrome/full/TestClient trong lượt này.

| Thứ tự | Rủi ro cần khép trước | Ca ưu tiên | Owner phụ thuộc / cổng mở |
|---|---|---|---|
| 1 | Mất dữ liệu, trộn phiên, ghi đè bởi response cũ | S02, S04, S05, S03, S01 | 02 và 01: hợp đồng revision/lưu/khôi phục, nguồn release |
| 2 | Sai lượng, đơn vị, tạo số giả, thiếu bị coi là đủ | D03, D01, D02, D08, F02, F04 | 03 + review14: JSON/producer và N03/raw-net; 04 kiểm truyền subtotal |
| 3 | Luồng bị chặn hoặc đi tiếp bằng bản chưa kiểm/lưu | F01, F03, S06, M02 | 02/03: guard và hợp đồng kích thước khớp |
| 4 | Vật tư/giá/tối ưu dùng lượng cũ hoặc sai loại giá | M01, M03 và G01 bên dưới | 04/05: cùng cơ sở lượng, nguồn/quy cách/hao hụt rõ |
| 5 | Hình học chi tiết và hồ sơ thực | D04–D07 rồi A01 | 06/07 xác minh hồ sơ/đáp án; 01 xếp lịch; người dùng gỡ blocker upload |

**G01 — P0, S+A, chưa chạy:** trên cùng revision, kiểm lượng lắp đặt → lượng mua có định mức/quy cách/hao hụt và đơn vị rõ; tách giá công bố/tham khảo, báo giá đại lý và giá dự đoán. Thiếu báo giá hợp lệ phải hiện chưa có giá mua; không lấy giá bất kỳ cùng mã để che thiếu quy cách/VAT/giao hàng, không gọi chi phí vật tư là tổng dự toán. Bằng chứng E03–E05; owner04/05/11 cung cấp tiêu chí nghiệp vụ hiện có, QA không tự đặt số hoặc nguồn thay thế.

Mỗi lần bàn giao nhận một delta nhỏ cùng ví dụ trước/sau và terminal, chạy đúng ca liên quan khi 01 release. Không chờ toàn bộ các đợt mới chuẩn bị; cũng không dùng testcount để tính phần trăm hoàn thành hoặc đặt ngày xong thiếu căn cứ. Thiếu dữ liệu/đáp án/quyền thao tác ghi BLOCKED với owner và bước tiếp theo.

Mọi ca dưới có trạng thái **CHƯA CHẠY**. P0 chặn nghiệm thu luồng; P1 chặn nghiệm thu phần hiển thị/hình học liên quan. S = synthetic kiểm hợp đồng; A = ACTUAL-build kiểm luồng thực. Ca S đạt không thay ca A.

| ID | Ưu tiên / lớp | Thao tác và dữ liệu | Kết quả phải chứng minh | Bằng chứng |
|---|---|---|---|---|
| F01 | P0 S+A | Từ bóc tách vào kiểm, chưa chọn vật liệu; truy cập trực tiếp các route | Menu/Steps đúng thứ tự; xem/tính hình học được; bước sau dùng đúng snapshot đã kiểm | E02–E04 |
| F02 | P0 S+A | Từng dòng nguồn A/B/C/D; kiểm rồi bỏ kiểm | Cờ kiểm độc lập nguồn; C/D không nâng A; D không biến mất; đếm trạng thái đúng | E03–E05 |
| F03 | P0 S+A | Chưa tính, dirty, lỗi tính/lưu, chưa kiểm một dòng trong phạm vi | Chặn tiếp với lý do đúng; không xác nhận bản chưa lưu | E03–E06 |
| F04 | P0 S+A | Xác nhận một phần với số đã biết và phần thiếu | Hiện phạm vi/lý do, yêu cầu xác nhận rõ; giữ subtotal và D xuyên API/UI/BOQ | E03–E05 |
| D01 | P0 S+A | Cùng nhóm có nhiều tiết diện/chiều dài; mở chi tiết | Có từng cấu kiện/lớp và nguồn; không lấy một kích thước đại diện; không suy từ formula | E03–E05 |
| D02 | P0 S+A | Cao tầng/cao xây khác nhau; sửa cao rồi tính/lưu | Phân biệt hai loại cao; kết quả phụ thuộc cập nhật; xác nhận cũ mất hiệu lực | E03–E06 |
| D03 | P0 S | None, 0, không áp dụng; mm→m; nhập sai đơn vị/âm | Thiếu là “Chưa có”, không áp dụng “—”; 0 hợp lệ giữ 0; validation không tạo số giả | E03–E05 |
| D04 | P1 S+A | Cột nhiều cạnh; dầm dài net/khoản trừ/cao toàn và dưới sàn | Kích thước đúng nghĩa, khoản trừ không thành cấu kiện; CP dùng đúng hình học | E03–E05 |
| D05 | P1 S+A | Móng nhiều lớp/vát; nhập thể tích trực tiếp; đất đào/đắp | Giữ từng lớp, đáy/đỉnh; không sinh kích thước giả; sâu đào không gọi là khối đắp | E03–E05 |
| D06 | P1 S+A | Sàn không chữ nhật, lỗ mở thiếu/đã xác nhận; nhiều thang/vế | Giữ diện tích và dày khi biết; không ép chữ nhật/suy lỗ thang; phân biệt chạy ngang/nghiêng, cao tầng/bậc | E03–E05 |
| D07 | P1 S+A | Thép bảng và hàm lượng; view lặp tầng | Bảng có dài cắt/số thanh; hàm lượng không tạo dài/rộng/cao; nhân lặp đúng một lần | E03–E05 |
| D08 | P0 S | N03: giằng hẹp/bằng/rộng tường, lệch trục/giao tiết diện; Q02 có số nhưng thiếu | Không trình bày khối lượng một phần như đủ; giữ missing/status/CP và số đã biết đúng phạm vi | E03–E05, E07 |
| S01 | P0 S+A | Sửa đầu vào hoặc override đo tay rồi tính/lưu/reload | Giữ gốc, override, đơn vị, lý do, nguồn; nhập bổ sung giữ C; đúng phiên đã lưu | E03–E06 |
| S02 | P0 S | Giả lập tính lỗi, lưu lỗi và quota giữa nhiều lần ghi | Không hiện thành công/cho tiếp; không trộn snapshot; retry phục hồi nhất quán | E04–E06 |
| S03 | P0 S+A | Reload/back/forward; snapshot legacy thiếu metadata kiểm | Bản mới phục hồi đúng; bản cũ buộc kiểm lại, không tự đánh đã kiểm | E04–E06 |
| S04 | P0 S+A | Đổi dự án A→B→A; lỗi quota khi đổi | Không rò cờ kiểm/kết quả giữa dự án; rollback không mất bản hiện hành; lịch sử nhất quán | E04–E06 |
| S05 | P0 S | Response cũ trả sau request mới; đổi dự án/file/tầng trong lúc chờ | Bỏ response cũ; không ghi vào snapshot/dự án mới; xác nhận liên quan hết hiệu lực | E03–E06 |
| S06 | P0 S+A | Đổi KT/KC, phạm vi hình cộng/tham khảo hoặc tầng | Kiểm lại phần bị ảnh hưởng; không cộng hình tham khảo; không giữ tối ưu cũ | E03–E06 |
| S07 | P0 S | Lưu dự án A, chuyển B rồi mở A qua history nhiều vòng, tạo archive mới mỗi vòng | `projectSessionId` của cùng dự án ổn định; không dùng `archive.id` thay đổi mỗi lần làm định danh dự án; B có định danh riêng, không nhận xác nhận của A | E04–E06 |
| S08 | P0 S | Lưu kiểm, chọn vật liệu rồi reload; sửa document hoặc phát lại snapshot có một liên kết sai | `documentRevision`/`reviewId`/`materialRevision` khớp quan hệ snapshot theo hợp đồng cuối; consumer từ chối chuỗi lệch hoặc cũ, không dùng vật tư/giá/tối ưu của revision khác | E03–E06 |
| S09 | P0 S+A | Kiểm một số dòng, xác nhận partial, lưu/reload/đổi dự án; cùng file nhưng recompute/reorder works hoặc đổi scope | `checked:number[]` chỉ hợp lệ với immutable `reviewId` và đúng thứ tự works snapshot; recompute/reorder/scope đổi vô hiệu receipt cũ, không áp index A sang B. `partial`/`confirmed` cùng receipt; phần thiếu và A/B/C/D giữ nguyên | E03–E06 |
| S10 | P0 S | Mở legacy thiếu liên kết revision/định danh; lưu draft hoặc gặp lỗi lưu giữa chừng | Legacy phải kiểm lại; draft không set ready và không mở khóa consumer; lỗi lưu không nâng trạng thái sẵn sàng | E04–E06 |
| M01 | P0 S+A | Đổi khối lượng đã kiểm sau khi có vật tư/giá/tối ưu | Bản cũ hết hiệu lực; bước sau chỉ dùng revision hiện hành, không hiện chi phí cũ như hợp lệ | E03–E06 |
| M02 | P0 S+A | Chọn vật liệu đổi dày/cấu tạo | Buộc tính và kiểm lại công tác bị ảnh hưởng trước đi tiếp; không tự suy thiết kế | E03–E06 |
| M03 | P0 S+A | Chọn vật liệu không đổi hình học; vật liệu/giá thiếu | Bảo toàn khối lượng đã kiểm; tính vật tư đúng lựa chọn; thiếu giữ thiếu, không dùng số mẫu ngầm | E03–E05 |
| A01 | P0 A | Trọn luồng KT+KC → sửa/tính/lưu → vật liệu → vật tư/giá → tối ưu → quay lại/reload | Đối chiếu API/UI/BOQ cùng revision; nguồn ACTUAL xác minh riêng; quay video, ghi giới hạn | E01–E08 |

## Gói bằng chứng bắt buộc

**Tiêu chí mới thay thế ghi chú BOQ phạm vi (a) bên dưới:** theo user và01, UI + Excel Tiên lượng G8 là deliverable bắt buộc. Dùng [G8_M1_ACCEPTANCE.md](G8_M1_ACCEPTANCE.md) để kiểm9 dòng/bốn vật tư M1, mở lại Excel và tách cached/formula/raw/published rounding. Không coi ghi chú cũ “không sheet riêng/chỉ parity” là đủ nghiệm thu yêu cầu G8 mới; vẫn không tự thêm metadata ngoài contract được giao.

Bổ sung QA đa nhóm AI16–AI19 tại AI_MATERIAL_ACCEPTANCE.md: MaterialUse thiếu element_id không được chia đều/gán lượng cấu kiện; intermediate không cộng trùng; hao hụt không thay quy cách đóng gói; không wall_groups vẫn tư vấn bê tông/thép và ghi riêng công tác không phát sinh mua.

Cập nhật chuẩn bị: schema bàn giao03 đã có tại `reports/work_dimensions/CONTRACT.md`/`SOURCE_READY_HASH.json`, oracle được cụ thể hóa trong `DIMENSIONS_CASES.md`; chưa freeze tích hợp hoặc cấp lượt QA15. BOQ MVP chỉ yêu cầu parity cùng snapshot về công tác/tầng/lượng/đơn vị/công thức/nguồn/trạng thái/phần thiếu, gồm dòng đủ và partial; không yêu cầu sheet dimensions riêng.

Mapping tên được 01 chốt: `projectUid` = projectSessionId, `drawingId` = documentRevision, `reviewId`/`materialRevision` giữ nguyên; `checked:number[]` là phạm vi checkedWorkKeys có điều kiện S09. Không đổi tên hoặc thêm field trùng chỉ để giống thuật ngữ ma trận. `projectUid` phải bền qua restore khi `archive.id` đổi. Draft không ready; legacy thiếu ID phải kiểm lại. Schema dimensions mới (basis/repetitions/nguồn theo field/missing-not-applicable) chờ 01 gửi chính xác để hoàn thiện oracle.

- **E01 Nguồn:** tên/hash KT+KC, phân nhóm build, phiên bản đáp án đo tay và cách đo; không đưa bí mật/tài khoản vào báo cáo.
- **E02 Môi trường:** release của 01, hash freeze trước/sau các tệp liên quan, revision/build frontend/backend, giờ chạy, database và loại dữ liệu (không ghi credential), trạng thái overlay.
- **E03 API:** request/response đã loại bí mật, revision/request identity, dimensions/source/status/missing, công thức/khoản trừ và lượng trước/sau; ghi lỗi HTTP khi có.
- **E04 UI:** ảnh/video có route, dự án, tầng, dòng/chi tiết, cờ kiểm, cảnh báo/guard; ảnh trước/sau thao tác cùng dữ liệu.
- **E05 Đối chiếu:** bảng theo công tác/tầng/đơn vị giữa đầu vào, API, UI, BOQ và đáp án; dung sai được chốt trước theo phép tính, không tự dùng ngưỡng <10% cho mọi loại công tác.
- **E06 Persistence/race:** bản lưu trước/sau đã loại bí mật, trình tự response, fault injection và ảnh reload; ghi cả lỗi rollback nếu có.
- **E07 Terminal:** lệnh, môi trường test riêng, tổng passed/failed/skipped, exit code, hash trước/sau. Dấu chấm hoặc process bị ngắt không phải tổng passed.
- **E08 Kết luận:** từng ID PASS/FAIL/BLOCKED/SKIPPED kèm đường dẫn bằng chứng, lý do, owner; tách kiểm hành vi và độ chính xác hồ sơ thật.

## Harness hiện có và giới hạn đã đọc

| Nguồn | Phạm vi có thể tái dùng sau release | Chưa chứng minh |
|---|---|---|
| `frontend/scripts/check-work-review.cjs` | Render tĩnh React với một dòng sàn thiếu dày, kiểm chữ thiếu/nút disabled | Tương tác, lưu/quota/reload, race, đổi dự án, metadata kiểm, hồ sơ thật |
| `tests/test_rough_api.py` + `tests/conftest.py` | HTTP rough/auto rồi rough, bỏ tường, input lỗi; sample_floor.dxf là mẫu, catalog overlay mẫu mặc định | Dimensions từng loại, route browser, dữ liệu ACTUAL hoặc giá thật |
| `tests/test_rough_status.py` | Quy tắc nguồn/status, thiếu thang/cao/dày và tham số | Cờ “Đã kiểm” độc lập nguồn trong UI/persistence |
| `tests/test_rough_partial.py` | Fixture ghi SYNTHETIC; subtotal/missing/D xuyên công tác, vật tư, giá và optimizer | Độ chính xác công trình hoặc luồng browser mới |
| `tests/test_rough_build_drawings.py` | File build thật nha_dan/nha_pho, đọc/bóc cột; skip nếu thiếu file | Trọn KT+KC, toàn bộ kích thước, đáp án độc lập, giá ACTUAL, browser |
| Các `test_rough_{walls,columns,beams,joints,foundations,areas,stairs,secondary,steel,takeoff}.py` | Danh sách cần owner đối chiếu delta producer trên hash freeze | Không mặc định test cũ đã phủ dimensions mới; lượt này chỉ kiểm kê, chưa đọc/chạy toàn bộ |
| `docs/review/N03_REVIEW_20261103.md` | Ca số hẹp/bằng/rộng, giao tiết diện và mốc review riêng | Mốc hash cũ không đại diện nguồn cuối; chưa là full hoặc hình học thực |

Đã đọc `AGENTS.md`, `PLAN.md`, hai đặc tả luồng, manifest WIP, harness và các phần lưu phiên liên quan. Manifest `WORK_DIMENSIONS_HANDOFF_PLAN_20261103.json` ghi `source_ready:false`, không có before hash và không phải isolated diff. WIP có TypeScript đạt ở lượt cũ; lượt focused bị ngắt với 103 dấu chấm không được ghi “103 passed”. Chưa có full cho delta kích thước theo bàn giao.

`saveMaterialSession` đang có cơ chế lưu nhiều khóa/rollback và invalidation; `switchProject` chứa khóa `optimat-work-review`. Đây là điểm thiết kế ca fault injection, không phải kết luận chúng đã đạt. Cần kiểm cả lỗi xảy ra trong rollback, không chỉ lần ghi đầu.

## Blocker và đề nghị lịch cho phiên 01

1. Chờ owner source-ready, hợp đồng dimensions cuối và hash freeze; cần kiểm N03/Q02 trên nguồn tích hợp.
2. Chờ 01 cấp lượt QA kỹ thuật sau freeze; full chỉ giao 05 J04, browser/API restart do 02 giữ theo lịch 01. QA15 không lặp full hoặc TestClient; lượt chuẩn bị không chiếm tài nguyên này.
3. Quyền upload hồ sơ Tân Bình còn bị từ chối; chỉ người dùng tự chọn file/cấp lại quyền mới gỡ blocker. Không dùng API thay upload.
4. Chưa có gói E01–E08 trên revision cuối. Đề nghị lịch: hợp đồng/producer + HTTP → fault injection/persistence synthetic → hồi quy theo 01 → browser ACTUAL-build khi quyền upload được giải quyết.

Kết luận lượt chuẩn bị: hoàn thành ma trận và danh sách bằng chứng; **không có kết quả test mới, không xác nhận QA hồ sơ thật đạt**.
