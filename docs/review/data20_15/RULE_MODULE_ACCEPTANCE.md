# QA module /quy-tac — chuẩn bị đọc artifact

## Re-review cuối hai điểm — CLOSED_STATIC trong phạm vi sửa

Hashđọc khớp01:page `27de75cb469e6ef33a9ffbf1ac75252e799f7b41e1aa48929525f539d0d662b3`;rules `f543150c1d2d076c4ba702b54b68f630a7e6d0c2f80944f1ad6e2bbaefb0a352`.

- **P2 giới hạn CPcột CLOSED_STATIC:**page:17 ghi physicalinstanceCPđểtrốngchờmặtđỡ/giaodầm vàschedulecaođộ chưa trừđầudầm. Đúnggiớihạn03,khôngtuyênbốCOTđủthìCPđủ. Nhãnsource cùngnhómchưa liệtkê columns.py/structural_column_instances.py cho đoạnCPmới;giữgapđộphủsource-label,khôngbácnộidungđãsửa.
- **Giải thích trace/version/work và anchor CLOSED_STATIC về tínhtrungthực:**headerpage:25 nêu rõ chưalink từngrule→version/source-designrow/workrow;link33 ghi chưađịnhvị. rules:33 cóđích#rule-rough_norms+thôngbáo khiAPIerror;:38 cóđích/thôngbáo khi metadata thiếubảng. Không cònanchorđếnkhôngđích tronghaistate này theođọcsource.

**Gap thựcchứcnăng vẫn giữ:**chưaenginebundlehash/versionbinding,nguồnthiếtkếlocator/ruleID vàworkkeydeeplink;disclaimer khôngtạocácmắtxíchnày. Chưaclick/errorfixturemới/build/live/layout/runtimeQA. KhôngP1/P2nộidungnào trongđúnghaiđiểmsửacònmở;source-labelCPnênbổsungkhinângđộphủtruyvết,cònmọigiaodiệnchờlượt01. Chỉreadfile/doc,khôngtest/build/browser/DB.

## Re-review17 hash mới — kết luận tĩnh

Evidencefixture17bổsungqua01:ảnh `tmp/rules17-qa/editor.png`,file://độclập mockAPI/UIprimitives;ownerbáoPASSmởCOT/href=/phan-tho/clickanchor→GET/api/admin/tables/rough_norms/editorreadonly/APIerrorvẫngiữ10nhóm. QA15khônglặpfixture/chưađọcảnhtronglượtnày;phânloại **OWNER_REPORTED_SYNTHETIC_FIXTURE**,khônglive/layout/runtimepass. ESLintterminal96790nod​​iagnostics,tsc6265exit0trướcdeltatext theo01,chưalogriêng;khôngdùngchứngminhtextfix/buildhashhiệnhành. P2CPcột vàtrace/version/workkeygapkhôngđóngbằngfixture.

Đã kiểm byteskhớp release01:page `70fd4b69625804252d84de36dc4fed4957730adeb80b2df0361574351b74c2c8`;rules `4dafade13b6818388ecf6467351d253abbb609e7898f90061008d9fd3532a727`. Chỉ đọc hai source,khôngtest/build/browser/DB. Kếtluậnnàythay trạngtháibảnđầu cho đúnghashmới.

| Finding | Kết quả trên bản mới |
|---|---|
| 03 P1 completeness | CLOSED_STATIC:nhómGộp nêu phạmvi xácđịnh,mọicontribution cólượng/khôngmissing,parentD/thiếu giữknownpart vàtotaltrống;không0giả |
| 03 P1 source≠runtime | CLOSED_STATIC:disclaimer mô tảsource04/11/runtimecầnkiểm,nhánhscopeKC ghi chưa xácminh bảnchạy;C2mathkhôngchứngminhreader |
| QA15 P2 COT/03instance | CLOSED_STATIC:3nhánh,schedulekhôngtựtrừsàn,KTthiếuslabtạmH+warning,instancetrục/gross/slabnguồnriêng/netNULL,C2readerlimit rõ |
| QA15 P2 nguồnchỉtênhàm | PARTIAL_STATIC:filepaths+symbol+ngàyđãcó;chưahash/versionenginebundle/line/ruleID hoặcnguồnthiếtkế từngrule. Khôngclaimtruyvếtđủ |
| QA15 P2 linkchung | MISLABEL_CLOSED_STATIC/GAP_REMAINS:link nayghi rõ “chưa định vị dòng”;khôngđạtdeeplinkproject/review/workkey,cầngiữgiới hạn |
| QA15 P2 precedence/hiệulựcsửa | CLOSED_STATIC phầnmôtả:firstmatchlayer/room,prefixblock,materialpriority+length+confidence;tácđộngghi cần tínhlại/đốichiếu,khônghứaghiđổi côngthức. Runtime/cacheeffectchưakiểm |
| 03 P2 CPslabshortcut | CLOSED_STATIC:ghiđúngplanđangxét,chưatựdògiaoô/tầngtrên |
| 03 P2 SANvoid | CLOSED_STATIC:netoutline−void,voidunknowngross/0chỉconfirmed |
| 03 P2 MAI mapping | CLOSED_STATIC:be_tong+replaces_slab_of,cầnplanthaythế |

**P2 còn thiếu CP nhánhcột:**nhómCOT_THEP/COP_PHA vẫnchỉnêumặttiếpxúcchung;chưa nói CPinstance luônNULL/pending giao vàlegacyschedule chưatrừđầudầm. Reader/modulecột đãtách3nhánh nhưngngườiđọcchưabiếtCPkhôngđồngmứcđủvớiCOT. Đềnghị17thêmgiớihạn03 đãnêu,khôngđổiengine.

`rules.tsx` gateanchorrough_norms kiểmmetadata cóname trướcmởTableEditor,cleanuphash/clicklistenerscó;khônghardcodebảngphảitồntại. TableEditorghiđịnhmức≠sửacôngthứccốđịnh. ChưaclickQA:nếumetadata khôngcórough_norms thìanchorpage vẫnhiệnnhưngkhôngmởeditor/khôngthôngbáo lýdo;ghiUIgap cầnownerchốtcáchbáothiếu,khôngtựkếtluậnruntimefail.

Chưađủtrace/version/workkey,từngrule vẫnlàtómtắtnhómkhôngenginekey. KhôngfindingP1cònmởtrongcácđiểmnàysauđọc;modulechưanative/UI/runtimeQA,khôngnghiệmthuE2E. Chỉ17sửa source theo01,chưacấplượtthửmới.

**Nền đối chiếu03 đã đọc:**QUY_TAC_PHAN_THO_HANDOFF.md/QUY_TAC_PAGE_REVIEW.md vàheader+sample inventory25rule(file/symbol/line/hash/condition/formula/unit/missing/work/runtime). Chưađọcfull25row tronglượtnày. InventoryIDs làIDtài liệu,khôngengineconfigkeys. Re-review17 phảiđốichiếuthêm2P1:complete cầnscope_complete+mọicontributioncólượng/khôngmissing+parentstatus,mọirowcósốchưađủtotal;source_new_frozen_not_integrated/legacy_runtime_unverified khônghiểnthịactiveverified khi01chưaxácnhậnruntimehash.

P2 nền03cầnkhépcùng4findingQA15:3nhánhCOT/nguồnslabriêng;CPinstancepending vàlegacyschedulechưatrừđầudầm;_slab_form_deductionshortcutplan chưađúngô/tầngtrên;SANoutline−void,voidNULL khác0confirmed/grosskhácnet;MAIbe_tong chỉthaySAN/CPkhi `replaces_slab_of` khai báo đúngplan,khôngtựphátgiao mái-sàn. Eligibilitynhàởxâymới≤5tầng làscope nghiệpvụ,chưachứngminhvalidatorchung. Chờ17freeze/hashmới,chưakếtluậnfix/khôngtestbuildbrowserDB.

**Phạm vi re-review đang chờfreeze/hash17 mới:**01 bổsung `frontend/src/app/(admin)/quy-tac/rules.tsx` cạnhpage.tsx. Kiểm nhóm lượngmua chỉ mởTableEditorrough_norms khi metadata thật có bảng/viewđúngcontract;không suy tên bảngluôncó hoặc quyềnghiđượccấp. Nhận diện đi/nhan-dien,côngthứccốđịnh đi/phan-tho phải ghiđiềuhướngchung,khôngdeepworklink. Sửađịnhmức khôngđồngnghĩa thaycôngthứccốđịnh/engine đãnạp. Sourceđangsửa,chưafreeze;QA15 chưareviewdeltamới/click/build/runtime/DB.

## Review tĩnh bản đầu17 — cần sửa trước nghiệm thu nội dung

Page `frontend/src/app/(admin)/quy-tac/page.tsx` SHA256 `00660ea8dd96c3b5c1b53138ef31b68b423bde742844e2b93ed4cb3438dd8413`. Đãđọc page/rules.tsx,03RULE_TEST_GAPS.md và tra các loader_ref/order_semantics trongRULES_INVENTORY.csv;inventoryrấtlớn,chưareview từngdòng. Khôngtest/build/browser/DB,khôngghi source17/03. Cácfinding lànộidung/source tĩnh,khôngvisualruntime.

| Finding | Vị trí / tác động | Đề nghị17/01 |
|---|---|---|
| P2 QTR02/05/07 — nhóm COT bỏ sót nhánh physicalinstance và giới hạnreader | page.tsx nhómCOT chỉnêu schedule_column_works/column_works. Contract03 có instance_column_works,missing source→NULL;nhánhcộtKT columns.py:240–257 thiếu slab lạitạmcao tầng cówarning. Gộp hai nhánh dễhiểu thiếuH vẫnnetđủ hoặcđãtựđọcC2 | Nêu ba nhánh/cơsởgrossnet/NULLsource rõ;ghi C2phéptínhinput≠readerVN002 chưaautonốitrục-section-slab;khôngchènexpectedvàodata production |
| P2 QTR01/02/06 — tênhàm không phải nguồn truyvết rule | page.tsx `<small>Bộ tính: {source}</small>` chỉchuỗitên,khôngfile/version/locator/ruleID/consumerlink;10nhóm làtómtắt,cầnphânbiệt rulequyước với nguồnthiếtkế/tiêuchuẩn | Gắnsourcepath/symbol vàmốc phùhợp;ghi rõ mô tảengine/đọc tĩnh,chưaphêduyệt. Khôngnângtrạngtháitừinventory cóloader/test_ref |
| P2 QTR06 — link chung không đưa tới côngtác | page.tsx href=/phan-tho và/nhan-dien,khôngproject/review/workkey/anchor | Ghi làđiềuhướngtrangchung;chưađạttruyvết rule→workcụthể.01chốt cầndeeplink hoặcghi gap,khôngtuyênbốlinkcụthểđãcó |
| P2 QTR02/08 — ưu tiênrule vàhiệulựcsửa chưa rõ | page nhómnhậndiện nóilayerkhớpđầu,nhưng03inventory phânbiệt materialrules prioritygiảm+patternlength,room/layerfirstmatch,blockprefixdài;rules.tsx vẫnTableEditor ghiview trongDB trongkhienginecònCSV/cache | Nêu scope từngprecedence;thayđổibảng khôngđồngnghĩaengineđãdùng/rerun. Khôngcầnsửaloader;giữnhãnđúngcapability vàconsumer |

Điểmđãđốichiếu:10nhóm cótómtắtcôngthức/đơnvị m³,m²,kg/m;TableEditor đượcgiữ,rule_viewsfallbackkhôngtạobảngmới. ChưađủđểđạtQTR01–08từngrule:thiếuversion/sourcecondition vàliênkếtwork,khôngcótrạngtháiruntimeverified. Foundation pit_overlap cónguồn thực nhưnggiới hạnpositions/hướng/phạmvi phảiđọccùngcontract,khôngdiễngiảitựnhậnhốmọiloại. Khôngphátfindingphéptínhmớihoặcthay19regressionC2.

QTR01/02/05/06/07/08: GAP_STATIC;QTR03/04:PARTIAL_STATIC;UI/layout/navigation vàsaveeffect runtime:NOT_RUN. Chờ17delta/hash và01xếplượt,QA15khôngtựmởtest/browser.

01 giao17 triểnkhai/03inventorysource readonly;QA15 chỉtiêuchítrongthưmục này,không sửa file17/03. TấtcảQTR01–08 NOT_RUN,chờartifact17+inventory03+slot01. Khôngtest/build/browser/DB hoặc thêm bảng;exact20 giữnguyên.

| ID | Đối chiếu trên artifact/source | Oracle |
|---|---|---|
| QTR01 | Mỗi rule có địnhdanh/version,nguồn và locator | Nguồn thật/fileversion/page/row/handle khi có;thiếu ghi rõ,không bịa link;quyước engine khác thiết kế/tiêu chuẩn đãduyệt |
| QTR02 | Điều kiện áp dụng/nhánhconsumer | Côngtác/cấukiện/tầng/phạmvi/điều kiện đủ-thiếu rõ;trỏ symbol/sourcehash thực dùng,không nhận tênrule là đãwired |
| QTR03 | Côngthức vàđơnvị | Input/output/chiềuđổi/hệsố/sốlầnlặp cónghĩa;raw/legacyrounding tách;khôngphân tích formula text đểsinh sốđo giả |
| QTR04 | Cộng/trừ/giao/gom | Nêu gross/net/deduction/reference,quyước phânbổ tránhđếmđôi;group khácinstance,SLtype không Ninstance;unknown không0 |
| QTR05 | Missing/unsupported/conflict | Giữ phầnbiết+lýdo+scope;NULL khác0/khôngápdụng,source xungđột khôngtựgiải đểđủ;trạngthái nguồnA/B/C/D khácđãkiểm |
| QTR06 | Link rule→work→consumer | Link đúngworkcode/variant/caller,ảnhhưởngđầu ra thật;rulechỉtài liệu/đềxuất phảighi rõ,chưa gọiđangáp dụng nếuconsumerkhôngđọc |
| QTR07 | C2 minh họa | .174240gross/.168432net chỉfixture đủinput/căn cứH120 đúngnhánh;readerVN002chưaautonốitrục/section/slabregion thìghi chưađạt. Không hardcodeC2/4A/oracle vào production đểdemo |
| QTR08 | Trạngthái UI vàcậpnhật | Mỗi nhãn active/verified/pending phản ánh consumer+evidence đúnghash;khôngnâng từstaticcode/puretest thànhCAD/E2E. Sourcekhácversion thìcảnhbáo/ghi mốc,khôngreceiptcũthaymới |

Gói cầnnhận:route/component17+manifesthash,inventorystatic03 vàconsumerpath/line đúngmốc,danhmục rule cùng nguồn/điều kiện/đơnvị;ảnh/receipt nếu01giaoactor chạy. QA15 lập ledger ruleID→source→consumer→work→evidence→status/gap/owner. Reviewđọc chỉchứngminh phùhợpartifact;layout/navigation/interactions cầnlượt riêng01. Không tựchạy lại19regression C2 vì chỉthêm trangquytắc;chỉđềxuấtca mới nếudelta thực thaylogic.
