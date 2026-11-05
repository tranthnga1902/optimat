# Thang tầng1→2 — bàn giao phaseA/B chờreview

Source freeze theo ACTIVE.json; chưa tựnghiệmthu runtime hoặc hìnhhọc VN002. STAIRS SHA `059d396d0df3dfd68f075e8984980036514c4b9239bc313408631e4a9302324b`. C2helper vẫn6bb3…, đãkiểm khôngđổi.

## Thay đổi vàownership

- stairs.py DTO flight/landing + fieldscónguồn từngthang. Bậcmasonry khôngcộngtamgiácBT hoặcCPthànhđổBT. Unknownkhônggiảconcrete; defaultglobalH/t khônglàmgeometrythaythế.
- Từngvế dùngL=hypot(run,rise), V=width×L×t_normal. Landingdày/ownershipriêng; floor/beamreferencekhôngcộnglặp. Legacydầmthang chưa cónguồn/giao giữunknown, khôngcộngkhốihộpsốnhậpđểđủ.
- building_stairs giữcandidatevẽdở, khôngcopyrefconfirmedmaterial/thickness/source/sốbậc sangtầngkhác theo width. Không tạo drawingreaderfilemới.
- Haihunkđược01cấp: status.py chỉCAU_THANGbasisstair_components bỏglobalH/t; takeoff.py chỉgateHplanNoneemitstair độc lập trướccontinue, khôngemitđôi vàwallslegacy vẫnchặn. Khôngđổi logicC2.
- Testthangriêng +đúnghunktestworkdimensions/status/fixtureStairđãcấp; oldcompletecase dùngconcretetườngminh+sources/flights/landings+receiptCPsynthetic. NoParamscase giữfixturelegacyunknown, giữassertkhôngđoán. Khôngđổiassert đểlàmnguồnmasonrythànhBT.

ẢnhKT19/20sauđóđãđọc ởdocs/review/data20_07, cósốthang/3vế/caođộkhácnhau; chưatríchđượcgeometryclear/chuyểnmốcKT–KC từngvế. Khôngdùng17×185 hoặc+3.900đểđiềnH. NguồnwaistKCghi rõBẬCTHANGXÂYGẠCHvà120vuônggóc;150chiếutớilàphầnriêng.

## Kiểm chứng

- **239passed,3deselected,EXIT0**,23,57giây;3caHTTPloại. Gồmthang,caller/status,partial/quantity_detailvàC2regression. Khôngfullsuite/DB/AI/API/browser.
- **131tệp** tronghash_before/after khôngđổi khi replay+focused. Bao gồm backend.py, testschọn,CSVrules/catalogvànguồnảnh/JSONđãđọc. Khôngtuyênbốtoànrepofrontendwriterđãyêntĩnh.
- Replaynguồnscoped: final/replay/request.json,result.json,receipt.json; replay.logEXIT0. Nguồn07humanapprovalfalse/chua_kiemgiữnguyên. BTthang,CP,XAYbậc **NULL/D**, không0giả hoặc con sốoracle. Có3placeholdervếtheocandidatecountnhưngkhôngclaimđãparse3vếđủ.
- Cònthiếu: run/rise/width+source từngvế; ranh/area/ownershipchiếu; đốichiếuKTfinish+0.150vớiKC0(khôngtựoffsettoànnhà); cạnh/gối/giaoCP; geometryquycáchbậcxây; steelmark→componentnếu muốnchiawholeT1schedule. Khôngconsume/thêmkgtheo3vế/17bậc.

## Bàn giao

CONTRACT.md/STAIR_CONTRACT.json cho06/17. stairs_changes.patch so đúngsnapshotcósẵn, khônggitHEAD: giữ130+/5−stairs cótrước, khôngnhận làcông03. source_snapshotchứabảnđãkiểm; receiptghi exactcommand/hash.

01/15reviewgeometry/materialguard/scope/status/partialtrướctíchhợp; root01quản lýruntime. Khôngđộngmodels.MaterialUse/materials04/SQL/DBschema/datachuẩn; giữ20bảng. Chưa chạygiao diện, tải hồsơthật quaAPIhoặcđổiP0confirm. KhôngfakeQA25.
