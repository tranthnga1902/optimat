# G8 producer đầu — chỉ bê tông lót móng

## Phạm vi

4file theo01: foundations.py chỉemitterBE_TONG_LOT; quantity_details.py sourcelean/finalize; takeoff.py thêmfinalize sauassign_status vàtrướcvật tư; test_rough_quantity_details.py. Snapshot, LEAN.patch, SOURCE_READY_HASH.json/FINAL_HASH.json giữdelta/phiênbản. Không models, walls._work,secondary/N03,O01resolver,attach_prices,norm/catalog/BOQ/frontend.

- lean_q giữnguyênbiểuthức cũ, tính1lầntrước round3; cùngqcho_workvàdetail. SourcegiữFoundationItem.sourcehoặcthôngsốmóngngườidùng nhập. Ví dụcount2×0,75×2,15×0,1: legacy0,323,detailraw0,3225,delta−0,0005.
- MissingbasevẫnquantityNone,giữmissinglegacy;0vẫnlàsố0. Rawâmkhôngđổi clamp0legacy,hiệnreferenceâm/unavailable cólýdo,khônggiảđónggópnet. CôngtáckhácdetailNone,khôngtuyênbốtoànroughcóG8detail.
- Finalizerdump-revalidateDTOnestedvàWorkItemconstructor,kếthừascopeFalse; parentD/missinghạscope/totalNonegiữknown/legacy/status/missing. Nếuunit/legacyquantityđổisaucapture thìrejectrõ,cầnproducerdựngnetlại,khôngscale/bùhoặcgọigrosslànet.
- Giớihạn:so sánhlegacyđãroundkhôngtựpháthiệnrawnetmutationscùnground3; khôngblocklótvìgóinàykhôngcónetmutationlót. MởN03/L1hoặcemitterkhácsauphảirebuilddetail vàfinalvalidate tạiđúngmutation,khôngcoihelpernàylàbộpháthiệnmọithayđổiđầuvào.

## Bằng chứng

AST_PARITY.json:rawexpressionvà_workcalllegacygiữnguyên,foundationbodyngoàileanhookgiữnguyên;takeoffASTdeltachỉ1callfinalizer,trongkhiO01helper/attach_pricesgiữnguyên. Testsofullpayloadlegacy(totals/materials/status/giá) luồngcóvàkhôngdetail bằngnhau. KhôngthaynormhoặcdùngM1đểhardcodecatalog.

- Attempt1:141passed,1failed,3HTTPdeselected,EXIT1;testfixtureSimpleNamespacecũthiếusource. Códriftambienttests/test_project_files.pydo06write,khôngđổlỗifixturechodrift,khôngclaim231stable. Source-readycũgiữởattempt1/SOURCE_READY_HASH.json.
- FixduynhấtfixtureFoundationItemthậtdefaultsource,khônggetattr/nớihelper.
- **Attempt2:142passed,3HTTPdeselected,EXIT0**,pytest10,52s/collector12,33s;PID41136/session10743 terminal. **231filebefore/afterkhôngđổi**,exact4manifestkhớpcurrent/before/after. Bằngchứngởattempt2/{focused.log,result.json,process.json,focused_hash_before.json,focused_hash_after.json}.
- Focusedgồmquantity_details,beam_sourcesO01,rough_takeoff,rough_foundations,purework_dimensions. BaHTTPbịchủýbỏ;khôngHTTPoutside/DB/CADthật/full.

M1vẫnreferencefixtuređộc lập;4tíchvậttưrawM1khôngphảichuỗivậttưlegacyengine(góinàykhôngđổinềntínhvậttưsangraw). ChưaUI/Excel/QAproductionAPIaccepted.

## Trạng thái bàn giao

Source4fileHOLDsauattempt2,chờ14đọclog/hashmới và01tiếpnhậncode+purefocusedởmứclót. Producerskhácchưađượcmở. KhôngchạyfullhoặcthửlạiHTTPoutsideđãbịautomaticapprovalreviewtừchối.

14đãchốtđộclập:exact4hashSOURCE_READY=FINAL=checkout=attempt2before/after;đọclog142passed/3HTTPdeselected/EXIT0/231deps0drift;fixturelỗi vàsnapshotattempt1đãkhép,khôngblockermớitronggóilean/finalize.01quyếtđịnhtiếpnhậncuối;khôngsuyraG8mọiproducerhoặcAPI/UI/Excel/fullđãđạt.
