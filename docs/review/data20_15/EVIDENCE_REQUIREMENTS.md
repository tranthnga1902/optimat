# QA DATA20 — yêu cầu bằng chứng

Ngày04/11/2026. Chỉ nhiệm vụ DATA20 được tiếp tục; W5/demo/AI/browser vẫn dừng. QA15 chỉ ghi thư mục này, không sửa canonical/source/data,không chạy test/full/CAD/DB/restore/upload/AI. Ma trận TEST_MATRIX_28.csv có đúngTC01–TC28 của kế hoạch;đường evidence là chỗ dự kiến,chưa là artifact. Tất cả NOT_RUN_QA15.

## Cổng phạm vi bắt buộc cho hồ sơ và mẫu số

Chỉ **phần thô nhà ở riêng lẻ xây mới ≤5tầng**. Mỗi hồ sơ/ca phải ghi loại công trình,căn cứ nguồn loại,số tầng theo thiết kế và nguồn/trạng thái kiểm. Chưa rõ loại/xây mới/số tầng:WAIT_VERIFY,không tự nhận vào tập nghiệmthu. Ngoài phạm vi:EXCLUDED_OUT_OF_SCOPE,ghi lýdo và số lượng riêng ngoài mẫu số hợp lệ;không âmthầm loại ca khó/thiếu dữ liệu thuộc phạm vi để làm đẹp kết quả.

Không đếm bể độc lập,cấp thoát nước hoặc nhà công nghiệp thành hồ sơ nhà ở. DM-1 VN002 là dầm/cốt thép bể **thuộc căn nhà**,không mở scope thiết kế công trình bể độc lập. Theo01/06/07,khung tênVN002 ghi “Nhà ở gia đình”;4tầng hiện từmanifest/tên gói,**chưa đồng nghĩa số tầng thiết kế đã kiểm**. Chờ nguồnfile/version/vịtrí và người kiểm để chốt;một nhãn manifest không thay bằng chứng thiết kế.

Giữđúng20bảng vật lý,S20soleowner schema/DB;nhu cầu thêmbảng phải trìnhlýdo/phươngán và **chờ chủđồánduyệt** trước triểnkhai. Báocáo hoặc đềnghịphiênkhác khôngmởquyền. Không chạy lại task/code/DB/browser/test đãdừng.

## Nguồn và cổng bắt buộc

Đã đọc docs/schema/CSDL_20_BANG.md, kế hoạchDATA20, tests/test_schema20.py và schema20.py tĩnh. Đúng20bảng vật lý được khai báo;view tên cũ không tính bảng mới. Không suy metadata tĩnh thành DBmain đã migrate. Root đang solewriter db/glue/SQL;QA15 không mở scope.

Mỗi ca cần inputmanifest/hash/revision,engine/rule/catalog/config/seed,expected độc lập,actual và diff,terminal đầy đủ/exitcode nếu có,lượt release vàhash trước/sau. Không có terminal thì khôngpassed. Mẫu số phải gồm cả missing/unsupported/chưa đánh giá;đơn vị riêng,không cộngm²/m³/kg. SYNTHETIC/SAMPLE/ACTUAL vàsplit rõ;biến thể cùng công trình không là test độc lập. 28ca hợp đồng synthetic không chứng minh sai sốCAD/thực tế. Đáp án phải có người kiểm độc lập/ngày/nguồn;chưa đủ thì BLOCKED,không tự gắn đãkiểm/A/ACTUAL.

Không đọc test_url.txt,backupprivate hoặc inDSN/key/credential. Backup chỉ ghi manifest đã loại bí mật:ID,size/hash,kết quảpg_restore--list vàreceipt restore trênDBriêng có phép;không khôi phục đèDBuser. Không thu thập credential để lấp bằng chứng.

## Bằng chứng hiện có và khoảng trống

| Artifact đã đọc | Có thể kết luận | Chưa kết luận |
|---|---|---|
| tests/test_schema20.py | Có test exact20/createSQL/view;DBfixture chỉ localhost + tên test riêng,rollback;testimmutablerevision,crossevidenceanalysis,NULLselected,completequantity,workcrosselement,idempotentstore vàsnapshotclosed | Đọc code chưa là terminal thực thi;không đại diện toàn28ca/DBmain/restore |
| reports/schema20_full_regression.log | Terminal dừng:439pass4skip1fail410,16s;test_scope_model_save_input_keeps_metadata_without_database lỗi FakeSession thiếuflush tại save_rough | Full chưa hoàn tất/exit thành công chưa có;không quy lỗi dữ liệu hoặc rollbackmigration từ lỗi mock |
| reports/schema20_regression.log | Mốc riêng42pass1fail31,18s,test_db::test_takeoff_reads_project_params lệch expected openings rỗng với cửa thiếu kích thước | Không suy bản mới đã sửa hoặc gom counts với full;owner cần phân loại contract cũ/hành vi lỗi |
| reports/schema20_targeted.log | Đã thử đọc tail,không nhận nội dung terminal hữu ích | Không ghi targetedpass |
| Tài liệu root mô tả migrationcopy28→20 đối chiếu từng dòng/cột | Thông tin bàn giao,mainDBchưa chuyển theo nhiệm vụ | Chưa nhận report migration sanitized/file manifest cụ thể để QA15 xác minh độc lập;không đọc backup/test_url tìm bằng chứng |

## Ca toàn vẹn bổ sung nằm trong28 ca

### TC28 — trial migration đã đọc, không phải main hoặc restore

Receipt được01 cho đọc:`reports/schema20_migration_trial.json`;`changed=true,tables=20`,28key legacy_rows và20key physical_rows,DBthử có tênriêng. Receipt ghi đối chiếu đầyđủ từng cột/dòng qua view;QA15 đã đọc lời xác nhận và các số đếm,**chưa có row/column diff/hash chi tiết để tự tái kiểm từng giá trị**. MainDB chưa chuyển. Không inDSN hoặc đọcbackupprivate/test_url.

| Đối chiếu trial | Quan sát | Giới hạn |
|---|---|---|
| Legacy→physical |28cấu trúc cũ→20bảng vật lý theo receipt | Không coi28legacy là28tìnhhuống hoặc28bảngvậtlý còn lại |
| project_files128 + project_document_revisions2 | document_revisions130 | Count phù hợp grain file/revision;chưa hashbytes nguồn hoặc locator từng revision |
| vehicles4 + labor_rates1 | cost_parameters5 | Count không chứng minh payload từng cột/loại đúng;receipt xác nhận mapping tổng thể |
| takeoff_results26 | analysis_runs26 | Chưa chứng minh tất cả snapshot đượcclose đúng/hash bất biến từ count |
| audit_logs10 | audit_logs11 | Receipt giải thích thêm1sự kiện migration,không gọi drift không giải thích |
| Backfill mới | elements14,measurements28,evidence14,takeoff_items476,scenarios1 | Không suy đủ nguồnCAD/GT hoặc đủdetail cho26analysis; cầnledgeranalysis→rows/kind/source và idempotence |
| materials98/walls22/relations15/norms31/price63/supply13/suppliers2867/projects24/users3 | Số đếm bảo toàn theo receipt | Không thay row/column reconciliation bằngcount;rule_sets779 cần mappingkind rõ |

**Cổng còn mở:**(1) exact20/legacyview có receipttrial nhưng inventoryconstraint/view/FK vàfullterminal cuối vẫn cần owner;(2)backfill cần danh sáchinput_snapshot vs CADsource,selected NULL/duplicate/crossanalysis,closed snapshot hash vàrerunnoop evidence;(3)rollback DDL/data injection **NOT_RUN** thiếu executionreceipt;(4)restore vàoDBriêng+filehash/openability+đối chiếu **NOT_RUN** thiếu executionreceipt. Backup-list chỉ là prerequisite,không nhận làrestorepass. Không yêu cầu suite khác khiS20 đang chạy remaininglog/XML trênclone.

TheoBOARD01:S20 solewriter/migration và đang sửa mock;D09 chưaowner riêng,G1–G6 dữ liệu/GT/nguồn còn phụ thuộc.28dòngmatrix không nghiệmthuđápán hoặc ngưỡngthực tế. QA15 chỉ cậpnhật tài liệu receipttrial,không tựmigrate/backfill/restore.

- TC26: chéo ownership/project,analysis/revision và evidence tồn tại nhưng khácanalysis;work→element khácanalysis;scenario assignments/requirements/catalog IDs orphan hoặc sai context. Kiểm cả transaction từ chối/không nửa dữ liệu. JSONB occurrences/relations chưa có toànFK phải chỉ rõ tầng app chịu trách nhiệm,không tuyên bố bảo vệ hết.
- TC10/11: selected NULL và hai selected cùngproperty;giữ0 hợp lệ khácNULL;manualmethod không lênA. Có ca concurrency doowner chạy khi được phép,không chỉ sequential.
- TC20/27: đổi quy cách/geometry tạo tính lại scope,không dùng snapshot/price cũ;snapshot result/input/project/file đãclosed bất biến. Danh mục chụp lúcmigration có catalog_is_historical_input=false,không gọi là input lịch sử thật.
- TC23/26: requirementsJSONB phải listobject,complete=true cóquantity;quantity_with_waste thiếuwaste_pct chỉ khi mọiuseswaste_included=true;giữ signed deductions,không abs/clamp hoặc áp knownpart≤total mù.
- TC28: inventory28structures cũ và20physical mới/view/grain;so đầy đủ mọi dòng/cột/null/type/ID/sequence;rerunnoop;backfillidempotent không nâng input_snapshot thành CADverified. Injecterror/DDLrollback doowner trongcopyDB,khôngresetmain. Restore riêng + filehash/openability + đối chiếu lại;pg_restore--list không thay restore thực.

## Mẫu receipt tối thiểu và next action

### Gate tiếp nhận mainmigration mới được user duyệt

**Runtime artifactreview đãđọc,thay PENDING_COPY:**`docs/review/data20_01/runtime_schema20/quiesce_receipt.json` xácnhận6PIDđượcquiesce,remainingListeners=[];`restart_receipt.json` ghi8001/8002/8765 OpenAPI200/58paths,listenerPID14432/33012/42556;chỉGET,khôngPOSTanalysis/optimize/AI. `read_only_smoke.json` có9checks:health/wall-materials/reference mỗi3cổng200,healthcatalogSource=postgresql,wall22/family10/vehicle4. Hai catalogroute khôngtựtrảcatalogSource;01đãđọcCatalog.load(folderNone+DBURL→from_db,khôngCSVfallback),nên kếtluậnDB-backed dựatrênhealth+sourceaudit+GET,táchkhỏiidentity/hash mọirow. QA15 chỉđọcJSONkhôngquery/kiểmprocesslại.

GateRUNTIME:READ_ONLY_SMOKE_RECEIPT_REVIEWED theođúng3cổng/mốc17:47+07;khôngUI/E2E/writepaths/ownership/accuracy. PENDING_COPYtrongcácghi chú cũ làlịchsử. Main/targeted/ACL/RESTORE vẫngiữcổngriêng;chưađóngRESTORE/accuracy/checklist17ô vìruntimeGETđạt.

**MAIN receipt đã nhận:**QA15 đãđọc `reports/schema20_main_receipt.json`:statuscommitted_verified/databaseoptimat/physical_tables20,sealed_analyses26,project23presenttrue;28legacystructuresverified trongtransaction,applicationrolereadback7views,backup_validatedtrue. Đây là receiptS20,QA15khôngqueryDBđộclập. Sourcehashes compatc4f08e.../schema3d17b1.../analysis ebcec989.../migrate187aa7... trongartifact. Các câu “mainchưachuyển/chờmainreceipt” trướcđây làlịchsử,đượcmốcnàythaythế.

Receipt ghi focused52/compute66/finalintegrity16passed;01 xácnhậnfinal16/3,11s đúngfrozenchildcases và14closedstatic. QA15 chưađọcterminal/assertionsfull của16 tronglượtnày,nên ghi OWNER_VERIFIED_TARGETED,chưa tựnâng mọiTCthànhPASS.01đãquiesce6API/restart,GEThealth/catalog200postgresql3cổng,khôngPOST theo thôngtinbàngiao. Thưmục `docs/review/data20_01/runtime_schema20/` chưađọcđược/khôngtrảinventory tại thờiđiểmreview;runtimeartifactreview **PENDING_COPY**,khônggọiendpointbù.

GateMAIN:RECEIPT_RECEIVED_COMMITTED_VERIFIED;POSTFIX:OWNER_VERIFIED_TARGETED+STATIC;ACL:receipt7viewreadback,chưafullACLmatrixQA;RESTOREexecution:NOT_RUN/chưareceipt. Backupvalidated khôngthayrestore. Chưaaccuracy/checklist17ô,khôngsuyrowtrace06/07làDBverification. RuntimeS20restart khôngtựmởW5/demo/browser/AI.

**Postfix mới theo01/14:**5findinggốc CLOSED_STATIC,chưa đồng nghĩatargetedexecutionđạt. P2mới:`protect_analysis_child20` chỉUPDATE/DELETE+OLDparent,INSERTvào sealedA hoặcmovechild từunsealedB→sealedA cóthểlọt. Chờ14exactreport/hash vàS20fix;không dùngoldlogsđóng.

- TC26/27 bổsung:INSERTchild mới vào sealedanalysisA phảireject;UPDATEchild.analysis_id từunsealedB sangsealedA phảireject theoNEWparent,giữOLDrow/giao dịchkhôngnửadữliệu.
- Kiểm riêng DELETE/UPDATEchild thuộcsealedOLDparent vàINSERT/UPDATEvớiunsealedparenthợplệ đểtránhchặnmù;giữcrossproject/crossanalysisgatesđộc lập. Phạmvichildtable cụthểtheo14/S20contract,khôngtựsuymọibảngđãbảovệ.
- Receiptcầnmatrixoperation INSERT/UPDATE/DELETE ×OLD/NEWsealedstate,hashsource/DDLtrigger,terminal/assertionssaufix vàsnapshotbeforeafter;executionNOT_RUN_QA15. MAINmigrationcommit hoặc5findingclosedstatic khôngđóngP2này.

01 xác nhận userqua00 đãduyệt S20 chuyểnmainDB20;S20solewriterlease. **Authorization không phải executionreceipt**:trạngtháiQA15 hiện chờartifact sanitized,không tựDB/test. Các mốc “mainchưachuyển” phía trên làbàn giao trướcauthorization,chưađượcđổi thànhmigratedchođếnreceiptthật.

| Gate nhận | Cần đọc sau bàn giao | Không dùng thay |
|---|---|---|
| MAIN | TargetaliasđãxácminhkhôngDSN;backupverified;start/commit/exit;20physical/28legacymapping;rowcolumnreconciliation/sequence/IDs;exceptionrollbacknếucó | Lờiuserduyệt,trialsốđếm,matrix28 hoặcscript tồn tại |
| POSTFIX-P1/P2 | Hashsaufix+targetedterminal/assertions đúng5finding14;closedhash/cataloghistorical/path/reverseevidence/NULLmetadata;14review | Remaining734pass ởmốc trướcfix hoặcfullcũ/đọcsourcechưaexecution |
| ACL | Owner/grant/role/sequence/view quyền trước-sau theođúngcontract,khônglọtbímật | Chỉrowcounts hoặc20tables |
| RESTORE | RestoreexecutiontrênDBriêngđượcphép,hashbackup/sourcefile,openability/rows/columns/ACL vàsnapshotreadback | pg_restore--list,backupexists hoặcmigrationcommit |

Mỗi gate đánh riêng RECEIVED/PASS/FAIL/BLOCKED/NOT_RUN theo evidence đúngversion;khônggộpMAINsuccess thànhđóngP1/RESTORE. NếuS20receipt chưa có hoặc thiếu artifact,ghiđúngmục thiếu để01phânlượt;không chạy bù/nhờactor khác.06/07chỉkiểmFILEVN002độc lập,khôngDB/W5;không dùngfilechecksđónggateDB hoặcACTUALaccuracy.

### Mapping review14 → ca DATA20 (đọc tĩnh, mọi execution NOT_RUN)

Nguồn `docs/review/data20_14/REVIEW.md`:5finding trên mốcsource riêng;S20 đang gỡP1/bổsungACLpreservation,receiptroot chưađóng. Không nhận source đã đổi làfinding tựđóng.

| Finding14 | TC / ca âm cần bằng chứng | Gate / artifact đóng |
|---|---|---|
| P1 gỡ snapshot bằng result_sha256=NULL rồi sửa result/input | TC27/28;TC26context | Trênclone closedanalysis,thử clear/changehash rồi mutate phảibịtừchối,giữhash+result/project/file;transaction+beforeafterdump/hash;S20 sửa,14review |
| P1 catalog lúcsave nhận nhầm historicalinput | TC27;TC19/20 | TínhcatalogA→đổiDBB→save;chỉsnapshotA thựcusedhoặcnguồnunverified,khônghistoricaltruechoB;source/config/clock+savedpayload+đốichiếu |
| P2 path ReviewPlan input.walls sai input.plans | TC26/28;TC10 nguồnNULL | Resolve mọi evidence/occurrencepath trêninputgốc haihìnhdạng giữindex;rawcontent không thay pathđúng;inputhash+pathresolutionledger |
| P2 DELETE/move evidence để JSONB evidence_ids orphan | TC26/28;TC10/11 selectedsource | Saumeasurementvalid,delete/updateanalysisnguồn bịchặnhoặcrepairatomic đúngcontract;khôngNULLgiả/khôngmấtevidence;reverseintegrityreceipt |
| P2 CHECKrevisionNULLlọt | TC26/28 | Parametrize version/size/roleNULL vàthiếumetadata bắtbuộc,insert/update qua physical/view;rejectatomic;khôngmấtrevisioncũ |

TC10/11 vẫn phải kiểmNULLselected/twoselected độc lập;5finding không tự chứng minh hai cổng này đã đạt. ACLpreservation bổsungTC28:so owner/grant/view/sequence quyền trước/sau migration/restore theo manifest lọcbímật;không chỉ countdata. Chưa executionreceipt thìNOT_RUN.

### Mapping sáu ca D10 của04 → ma trận28 (execution NOT_RUN)

Nguồn `docs/review/data20_04/SCENARIO_CONTRACT.md`;đây là tiêu chí đọcsource,khôngterminalDB.

| Ca04 | Mapping | Evidence bổ sung / exit |
|---|---|---|
| D10-01 linkage/rollback | TC26/28 | Crossproject/crossanalysisitem;sam eproject nhưnggroups khácsavedquantity phảirejecthoặclabelscenarioassumption;failinsert scenario2 rollbackrun+mọiscenario |
| D10-02 hai phươngán/đổi dày | TC19/20/21 | Requirement/norm/price/missing riêng từngscenario;option3geometrychange invalidates scope,recompute khôngmangquantity/costcũ |
| D10-03 D07/cấp phối | TC21/22/23/24/25 | Hệ W-GK01-110 chỉkhiđúngscopeđượccấp,VU02intermediate khôngdoubleXM01/CA02;thiếugiá/BULLETIN/kiệnlệchunit giữthiếu;cướcghép1lần |
| D10-04 đọc nguồn đổi | TC27/28 | Price/leadtime/rules/effectivesolverconfig/seed/modelusedsnapshot giữcũ;khôngcurrentlookuplấpoldrun;catalogmigrationflag giới hạnlịchsử |
| D10-05 rỗng/thiếu/0 | TC10/18/21/27 | No-solutionreason khácunknownquantity khác0cócăn cứ;requirements=[] khôngxóamissing;notes/n_evaluated/effectivealgorithmđủđểgiảithích |
| D10-06 chọn/reopen | TC11/26/27/28 | Concurrentselecttốiđa1/analysis;actor/time/reason+auditatomic;newanalysis khônginheritapproval;historyrestore truyđược |

Nhữnggappurchase/provenance/confirmation/config của04 là điều kiện chưa đạt,không yêu cầuQA15tựsửaschemahoặcđặtJSONmới. OwnerS20/04 chốtschemaJSONversion/legacyread/selectedaudit và01 cấp lượt cô lập.

### Cập nhật điều phối phụ thuộc

D09 đãgiao03 reports-only `docs/review/data20_03`,thayghi chú “chưaowner” ởmốcBOARDcũ.16đãbàngiao2filedata20_16:63observations+15gap records,**không phải78giá**;chưađủtrainhoặcpurchase. Giữmẫusốgiáquan sát táchgap,khôngđếmnhânđôichomục tiêu. QA15chưađọctừngdòngreport16tronglượtnày,đâylàthôngtin01xácnhận.

Receipt theo caseID: status/input IDs+hash/data_kind/split/GTstate/owner/release;expected+actual+delta+tolerance đã chốt;denominator included/excluded+reason;artifactpaths;source/version beforeafter;terminalexit;DBtarget alias khôngDSN;rollback/restore scope;giới hạn. Ca chưasource/GT/config phảighiBLOCKEDkhông tạo dữ liệu để đónggate.

Đề nghị01/root cung cấp reportmigrationcopy sanitized (row/column reconciliation,backup-list/restore/rollback/backfill receipts và hashes),phân loại haifail logs,cấp focused riêng nếu cần. Chưa tự chạy. Sauđó01 giaoowners theo10góidữliệu,QA15 kiểm evidence của28ca trước release;ngưỡngaccuracythực do nghiệp vụ chốt,không tự đặt.
