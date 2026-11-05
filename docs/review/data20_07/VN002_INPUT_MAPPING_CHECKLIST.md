# Checklist tiếp nhận/mapping VN002 — chỉ đọc nguồn

## Cặp nguồn và lớp xác minh

- [PAIR_LOCK của06](../data20_06/PAIR_LOCK.md) khóa DXF KT719ea17… vàKC22cda910…, KCINSUNITS0. Manifest liên kết quản lý hai file, **chưa xác nhận cùngrevisionthiếtkế**. Không tựsuy hìnhhọcmm từheader; kíchthước đọc trênPDF/ngữcảnhphải giữnguồn.
- NguồnDWG KC trongincoming là `HO SO KET CAU NHA A SANG - HAI DUONG   15-10-2021.dwg`, SHA8e049401408d381aae3aa50b624f41cc13cf2f3d7955334ecbd213b6392cd51e. UI thấy tên tươngtự **chưa đủ chứng minh đúngbyte/revision hoặc đúngconversionDXF đãkhóa**; cầnhash fileupload vàreceiptchuyểnđổi liênkết.07 chưađọcUI/runtime tronglượt này.
- Sốpreview69423/485955 vàcore4vùng/0walls/openings là thôngtin01/00 chuyển, không làphépđo mới của07. Bốnvùng khôngchứng minh bốn tầngđãbóc;0wall/opening khôngchứng minh côngtrình khôngcótường/cửa. Phải giữthiếu và kiểm ýnghĩa từngtrường/count theo pipeline.

## Mapping theo nguồn đã xem

| Đối tượng/phạm vi | KTplan hoặc mặt cắt | KCplan/tờ | KCsection/chi tiết | Đủ và phần thiếu |
| --- | --- | --- | --- | --- |
| C-2 vịtrí4/A, đoạnT2→T3 | Chưa xác lậpKTplan cócùngmốctrục/instance | p19 mặtbằngđịnhvịcộtT1–2–3,C-2 tại4/A;4/B làinstancekhác. p23 sànT2+3.150,p24 KC-03-02 sànT3+6.750 | p22 KC-02-04,C-2 MC2–2:220×220. Caođộ+3.150/+6.750 | **LiênhệKC cónguồn**; nguồnKTinstance,transformgiữthiếu. Chưacóreceiptreader chọnđúnginstance/segment. |
| H120 vùngkề4/A | Chưa nốiKTfloorregion sangKCregion | p24 KC-03-02,ô3–4/A–B,vùng+6.750/H120; legendvùngthường12cm. Khôngtrộn vùnghạcốt gần3/B hoặc+7.500 phía1–2 | p29 KC-04-03,D1-4A trụcA,nhịp3–4,MC3–3 gầngối4:cánh120+sườn280=400 | **Củng cố khác hình trongcùngKC**, khôngđápánđộclập. Slabpolygon/contact/beamclip runtimeNULL; khônggán120toàntờ/nhà. |
| Thép dọcC-2 MC2–2 | KhôngcầnsuyKT đểđọcbar schedule, nhưngvịtríinstanceKTchưa nối | p19 C-2 tại4/A dùngliênkếttheoloại,vịtrí; nhómC-2SL2 khôngtựnhân2 | p22 mã3/4,2Ø20/mã,DAI4300,SL1=2/SLA4; INSERT118CDA7/118CDB3 | Đủtruytừnghàng/chiềudài lắpđặt; chưacắtthéptheo3600mm,đaiđoạnthiếu. KhôngtrộnC1/C1Ahoặcautođánhdấuduyệt. |
| Vùngbểnước trongnhà | Chưa khóaKTplan→KCvùngbể | p11 KC-01-05,chữBỂNƯỚC tạiô1–2/A–B,2500×2000,mépphải→2=890,mépdưới→A=390 | p17 KC-01-11,chi tiếtbểnước; p18 KC-01-12,bảngbểnướcbênphải | **Vùngbể trênKC địnhvị được**. Hướngchi tiếtp17 xoay/đốixứng so p11 chưađủmốcduynhất; haiDM1trái/phảihình17 chưagáncạnhcụthểp11. Tầng/KTlinkNULL. |
| Một hàngDM1bểnước | KTlocationthiếu nhưtrên | p17 có2nhãnDM1+leadertrực tiếp cạnhtrái/phải; khôngsuychỉSL2 | p18 DM1STT1,INSERT1173553:200+2450+200,Ø12,4thanh,11.4m; đơntrọngp3 | Đủtruy **mộthàng**; khôngđủduyệttổngbểØ12đangxungđột. ChưakhóaphysicalinstanceKCplan→detail→barrowduynhất. |
| ThangT1→T2 | KTp19 KT-17mặtbằngnhiềutầng,p20 KT-18cắt1–1/2–2; sảnh+0.150,cổbậc/đầu cuối thayđổi | KCp37 KC-06-01,ô2–3/A–B,ghiđúngT1lênT2. Note+3.150/H150 tạiđầulên | KCp37 bảnnghiêng120vuônggóc,bậcxâygạch,bảngT1SL1támhàng | Cólink **loạithang/tầng/trục/chi tiết** theoảnh; vẫnthiếudatumKT/KC ởgối,caođộ/rộngnet/từngvế,ranhgóc. Không17×185,khôngnhân3tổngbảng,khôngBTbậcgạch. |
| CácfloorplanKT/tường/cửa toànnhà | Chưa kiểmđủtừngplan/vùng/tầng/hướng/scale trênKT | Khôngcómapping từngtường/cửa/host vớiKC tronggóibằngchứngnày | Chưađủsection/height/openingrelations | **Chưa đánhgiá**; khôngdùngcore0wall/openingđểđiềnGT0 hoặcgọiđãbóc4tầng. |

## Checklist cho01 tiếpnhận mà chưa cần chạy mới

1. KhóahashfileUI vàquan hệDWG→DXF→PDF; thiếureceiptconversion/versionthìghiUNKNOWN,khônggộp bằngtên.
2. Mỗivùngpreview phải cótitle/sheet/floorcandidate/bbox/transform/nguồn; cùngtầng cóthểnhiềuhình, cùngmãcấukiện cóthểnhiềuinstance. Chưachốtthìkhôngđếmthànhfloor.
3. Trụckhungvẽ/chữtrục phải quaINSERTtransform; góiC2bổsungđãchỉraoriginINSERTnằmxavùngnộidung. Khônglọcchỉđiểmchèn rồi kếtluậnthiếuhìnhcột/trục.
4. Soidentity4/Akhác4/B trướcghépMC2–2; gắncaođộ/tầng/rulegrossnet cónguồn. Unknownslabregionkhôngfallback120toànnhà.
5. KTplan/section khôngđủđểgánKCinstance thìhiểnthịchưagán; khôngbiếnnhập taycónguồn thànhA tựnhận. Tường/cửa cầnhost/kíchthước riêng,khônglấysố0đểchethiếu.
6. Giữhồsơ nhàởriênglẻxâymới≤5tầng làcổngphạmvi; khungtênNhàởgiađình cónguồn,4tầng mới làkhai báo tên/manifest tronglượtkiểm này. Khôngsuy phạmvihoànchỉnh từ4vùngcore.

Cácartifactchi tiết thamchiếu: C2_A4_ORACLE_HANDOFF.md; C2_A4_CAD_SOURCE_HANDOFF.md; C2_A4_BLOCK_AND_MATERIAL_HANDOFF.md; C2_SLAB_CONTACT_CHECK.md; C2_REBAR_SOURCE_CHECK.md; WATER_LOCATION_PAGE11_CHECK.md; TWO_DM1_WATER_POSITIONS.md; STAIR_T1_CHECK.md trongthưmụcnày. Đây làchecklistphạmvinguồn đãcó, khôngreceiptQAhoặcGTđãkiểm.

Lượt07 chỉghibáocáotổnghợpmapping; khôngCAD/full/AI/DB/runtime/TânBình,khôngmởlạinhánhOffice,khôngsửanguồn/canonical/split hoặc schema20bảng.
