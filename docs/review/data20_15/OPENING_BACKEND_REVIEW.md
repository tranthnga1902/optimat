# QA độc lập openingnullable backend

## UI v3 orphan delta — CLOSED_SOURCE_HARNESS

Manifesthash `5c1d7dc4268dbeb6852840d80af0447602b75b3a3cdfd43db63cb294650a352e`khớp;14overlayhashkhớptrướcvàsau. Deltafrom-v2chỉmodel orphanpendingWalls=allkeptids khiunassigned,linkedmissingvẫntheoownerwall/group;CSVwallpendingtrống. Khôngđổigroupingtheonghivấnđãbác.

QA15chạy6harnessv3(3/port3001/3002),tấtcảexit0;artifactsopening_ui_v3/{result.json,hash_before.json,hash_after.json,6logs}. Orphan2wallgroupsknown0,totalNULL,groupnetNULL,CSVtrống;keepfalse khôngảnhhưởng,linkedmissinggiữgroupđộc lập. Confirmstamps/quota/retry/partialsave-reopen/6contextchanges/happyfinish vàprice/optimizerknownscopeguardsvẫnPASSfixture. Khôngfindingmớiđúngdelta/harness,orphanfindingv2 **CLOSED_SOURCE_HARNESS**.

Khôngbuild/browser/runtime/DB/AI/full,khôngactual47workend-to-end;sourceharnessmockkhôngthayHTTPAPI8003hoặcuserUI.01giữquyềngraft/build/promotev3,kếtquảv2khôngthayhashv3.

## Frontend v2 sourceharness — PROVISIONAL orphanfix còn mở

Manifest877ffe52...khớp;14overlayhash(7/port)khớptrước/sau,chạy3harness/port source-only đềuexit0:check-openings/check-partial-confirm/check-consumers. Log/result tạiopening_ui_v2/. KhôngDB/AI/browser/runtime/full;khôngconsumer/sourcewrite. Harnessgiữ4IDparent/nullable/keep,invalid24cases,partialsave/reopen/quota/stamps/sửa tầngkhác,giá/optimizerchặntổnggiảvàhiệnknownscope đạttrongfixture hiệncó.

**Chưaacceptv2:**01xácnhậnorphan kept chưa làmallgroupsplanđónetNULL/known0 nhưbackend;harnesscókiểmtotalNULL/orphanpreserved nhưngchưakiểmknown/groupnet củaorphanplan. Cần02fix+caorphan2wallgroups/planT1 vàindependentplanT2 giữsố. Nghi vấnnon-dominantmatgrouping trước đó đã01báckhiđọcfullsource (keycls|role|matđãđúng),**khôngghi thànhfinding/khôngyêucầuđổigrouping**. Chờhashmới,khôngdùng6harnesspass trênv2đóngorphanfix.

## V2 LT/orphan + invalidcrossproduct — focusedPASS

01cấplượtsau06freeze;4canonicalhashkhớpmanifestmới vàkhôngđổitrướcsau. Chạytests/test_incomplete_openings.py+QA15test_opening_invalid_dimensions.py(trongthưmụcQAriêng):**36passed7,97s exit0**,logs/results/hashes tạiopening_focused_v2. Trongđó18caseownerfilehiệnhành+18caseQA15crossproduct;khôngđồngnhất“12ownerpassed”cũvớisốcollecthiệnchạy. KhôngDB/dotenv/OpenAI/CAD/HTTP/full.

LT/CPwidthknown,heightNULLvẫncólượngvàwarningchưakiểmgiaodầm;XAY/TRATNULL theoopeningareaunknown. WidthNULLLTNULL. Orphanopeningkept làmplanT1affectedpending,planT2tiếptụctính;wallgroup chưađủkhônggiảcomplete. OP05cảw/h×bad/empty/numericstring/negative/zero/NaN/+inf/−infđềureject,2caNULLkeepfalsegiữIDparent. Khôngfindingmới trongđúngscope36case.

LTdependencyfindingbảntrước CLOSED_FOCUSED;nhậnwarningkhôngbằnggiaođãkiểm. OP06frontend/P0fullpathvàOP07exportoptimizer/partialreopenvẫnPENDINGmanifest02/lease01,khôngđóngbằngbackendpass. Khôngphảiruntime47work/E2E.

Đọc06manifest/patch/tests;canonical4filekhớppatchedhashtrướcvàsauchạy. Slot01:chỉtests/test_incomplete_openings.py,**7passed10,25s exit0**,khôngdotenv/DB/OpenAI/CADthật/HTTP/full. Artifactsopening_focused/{focused.log,result.json,hash_before.json,hash_after.json}. Khôngsourcewrite.

OP01–04 backend được7ca chứngminh:widthNULLvsheightNULL,mixedknownunknown,keepfalse,ID/parentgiữ,trườnghợpunassigned;affectedXAY/TRAT/lintelpending,groupđộc lậpvẫntính. compute_reviewcompletefalse,totalNULL,billtotalNULL,pendingopenings/groups giữID/parent,knownnet chỉgồmgroupđủ. OP05hiệntestâmw-1,h-1,wbad,hnan;modelstrictpositivefinitebaohaifield nhưngtestmatrixchưađủcảfield×invalidstring/0/inf/NaN (coveragegap,khôngruntimebug).

## Consumer gaps cần01phânscope,khôngtựsửa

- **OP06frontendPENDING**:02serializer/formatterđangsửa,chưahash/test/UI;backend7pass khôngđónglỗi47workUI. Confirmedtype/tổngnullable/exportcsv/publishedsummary/recovery cầngiữcomplete/pending,khôngdropIDhoặcfilterpendinggroup.
- **OP07optimizer boundaryPENDING:**review.groups chỉchứagroupđủ,cácgroupthiếu chuyểnpending_groups. `/api/materials` và`/api/optimize` ởmain.py:414/465 nhậnreq.groups,grouplistkhôngmangReviewResult.complete/pending_groups. Chỉtruyềngroups cóthểtínhphầnhợplệnhưngkhôngtựchứngminhtoànscope;owner02/04/01cầnevidenceconsumertruyềnpartialscope/cảnhbáo/nobuytotalgiả. Khôngkhẳngđịnhsolverphảichặnmọipartial;phảighiđúngscope. Chưa cótestexport/optimizer trong7ca.
- **Knownparttrongaffectedgroup:**pendingReviewGroupgiữgrossvàknownopening,netNULL;roughXAY/TRATquantityNULLkhôngcóassertknowncontributionledger trongtest. PhảikiểmexportkhôngđánhNULLthành0vàgiữdòng/lýdo,khônglấyformula cósố làmnet. rough/boq.pyđãcónhãncomplete/missing nhưnggói nàychưachạyconsumer/export.
- **Tĩnh cầnquyếtđịnhnghiệpvụ:**heightNULL,widthđủ thìlanh tô/CP cũngNULLtheopatch dùphéptínhlintelcóthểchỉcầnwidth. Testhiệnchủýrequirepending,nênkhônggọilàregressionđãchứngminh;03/06cầnchốtđồthịphụthuộcthực đểtránhđếmthiếuquámức. Khôngtựnớigatemissing.

KếtluậnPASSbackendfocusedhẹp;OP01–07toànchuỗichưađạt. Chưaruntime/DBsave/Excel/optimizerE2E,mọiwriteconsumer phải01lease. Giữ20bảng.
