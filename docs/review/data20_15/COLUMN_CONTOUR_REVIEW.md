# Review độc lập signal_columns — đọc patch/artifact

Đọc README/patch/after_probe/focused_final của05,sourcecolumns.py vàtests contour/columns. Không chạy lại test/probe/CAD/API/DB/browser. Sourcehash `c0146428bd3f348a553b310cbe5f7813ca2b91eac38f622c6d0663c14f74e748`,testhash `cea7c3df770af4efd7c498685a08e8f5a702b77eb18c666824af8cf1527df6b4` đãkiểmkhớpartifact.

Patch xử lý đúng nguyênnhân bboxfalsepositive:khôngchấpnhận chỉ vì2cạnhbboxđúngrange,kiểmphủliêntụcbốnbiênaxis-aligned bằngtọađộthật;giữ225×335 thayroundbội10. Nétkindhatch khôngđi vào nhánhsignal,hatch/rasterdetect/ưu tiênhatchkhôngđổi. Split/overlap cạnh vànétchéo bêntrong khôngbịloạinếubốnbiênđủ. Epsilon1e-6mm nghĩa khehởthật khôngđượcđoán kín.

Evidence05:56pass12,41s exit0 theofocused_final.log. Probe05 cùngfixturehashaf4efc... (SYNTHETIC):1cột225×335,raw0,262305m³/legacy0,262 vớiheight3500/slab20;trước3cột/tổng0,781 theoartifact00/05.00báođãchạyđộclậpread_drawing→column_works khớp1cột. QA15khôngtựchạy,nênkếtluận **STATIC_REVIEW_ACCEPTED chofixbbox/dimension**,khônglàQA15runtimepass hoặcaccuracyhồsơthật.

## Giới hạn/chỗ cần ca bổ sung để tránh đếm thiếu

1. CộtxoaykhôngsongWCS/hìnhbấtquytắc/hìnhhở khôngđượcnhánhsignalnàychứngminh;rectangleđúngnhưngnétkéo ra ngoài làm bboxlớnhơncóthểbịloại. Khôngnớiepsđểlấpnguồnthiếu;hiểnthịkhônghỗtrợ/cầnkiểm,khônggọichúngkhôngphảicột.
2. **Rủiro tĩnh undercount cầnownerxácminh:**hai contourchữnhậttiếpxúc/chungđầumút sẽunionmộtgroup;nhánhchỉxuấtmộtColumnchoouterbbox. NếuouterbboxvẫnnằmCOLUMN_SIDE_MM,vàbốnbiênđủ,cóthểgộphaiinstance thànhmột;khibboxvượthi,cảgroupbịbỏ. Chưa córuntimeprobeQA15,khôngclaimđãgặptrênCADthật. Đềnghị05/01ca2cộtchạmcạnh/chạmgóc/nétliênkếtvàđườngngoàibbox;giữindividualinstance/ambiguitythaytựnhânhoặcdrop. Khôngtựmởsourcelease.
3. Endpointgroup vẫnround1mm trongkey,biêncoverage dùngtọađộthật:đúngđểkhônglấyroundlàchứngminhkín,nhưng2contourgầnnhau cóthểbịnhậpgroup/tăngbbox vàmiss. Ca khoảngcáchquanhngưỡnground cầnownerkiểmriêng.
4. Hatchtrùngsignalgiữhatch:fix225×335signalkhôngsửarasterhatchrounding/shapeaccuracy. Testdeduphatchhiệncó khôngchứngminhtọađộ/kíchthướchatch225×335chínhxác;đốichiếuhìnhthậtcầnexactsourcebranchvàGT.

Khôngcóbằngchứngnângthànhmọicột/toànnhàđãđạt,khônggắnsốprobevớiVN002C2. GiữriêngphysicalinstanceKC/sourcepriority/readerC2 và20bảng. Phầnunder-count làcaâmđềnghị/findingstatic,chờ01phânscope05;khôngtựruntestđểvượtlease.
