# Follow-up — instance_id qua tái phân tích

Ngày04/11/2026. **Chỉ ghi báo cáo/đề xuất, chưa mở hunk hoặc sửa source freeze.** Bản helper6bb3c47a1a2275c05e264e91afc40968fa01670371c8a237df65ca5aed61d6e9/review15_v2 giữ nguyên để root promote.

## Trạng thái do01 bàn giao

- QA15 đóng cả3finding ở mức CLOSED_STATIC cho review15_v2.
- Root chạy API thật8002: structuralHTTP200/80,7s/24instances; uniqueC2@4/A220×220,3150→6750, slab candidate120 chưa xác nhận.
- RoughAPIHTTP200/52works: grossraw0,17424,netNULL; COTw22/CPw50 vàMaterialUse.rowIndex khớp cùngsnapshot.
- KhôngprojectID/save/AI trong lượt root báo.03 chưa tự chạy hoặc kiểm lại API/UI/DB; đây là biên nhận điều phối, không phải lượt kiểm mới của03.

## Vấn đề ID cần xử lý sau demo

Cùng nguồn qua APItempfilename sinh ID prefixb252… trong khi nguồnfilegốc prefix5336…; chỉ có prefix trong thông báo, chưa ghi đủID hoặcreceiptfile. Constructor hiện ghép file vào identity nên đường dẫn staging có thể làmID đổi. Không sửa nóng hoặc tự remap selection trong demo.

rowIndex/w:i chỉ định vị trong mộtresult snapshot, không thay identity bền qua reanalysis. Không dùng w22/w50 làm khóa dài hạn.

## Đề xuất để01 duyệt sau demo

Dùng hash của payload canonical gồm source_sha256 của bytegốc, loại cấu kiện, handlepath gốc + chỉ số lần chèn MINSERT, và scopeđo (hai caođộ chuẩnmm cùng phạm vi đã xác định). Không đưa tempfilepath hoặc tên tải lên vào identity. File/path vẫn giữ riêng để provenance. Handlepath phải giữ rootINSERT để hai lần chèn cùngblock không trùngID; cùngcode4/A và4/B không gộp.

Canonical hóa số vàđơn vị phải được định nghĩa trước:3150 và3150,0 cùng giátrị, không lượng tử hóa tọađộ/kíchthước để ép haiinstance thànhmột. Scopechưa rõ là candidate, không tự nhận mọi đoạn phát sinh sau khi phân giải scope là cùngselection cũ.

Nếusourcehash/handlepath/scope đổi thìIDmới hoặc pending theo chính sách đã chốt; không tự dùng gầnđúng tọađộ/mã để lấy lại lựa chọn. Kết quả snapshotcũ giữ ID vàreceipt cũ, không backfillngầm hoặc đổi MaterialUse.rowIndex.

## Test cần có trước khi mở hunk

1. CùngbyteCAD qua hai thưmục/tênfile/tênupload khác nhau: IDgiống nhau,provenancepath khác được giữ.
2. Nhiềulầnreanalysis cùngsource/scope: IDổnđịnh, không phụthuộc thứtự quét hoặc workindex.
3. HairootINSERT/MINSERT dùng cùngblock: IDkhác; nestedhandlepath giữ đủ.
4. Cùngmã ở4/A và4/B hoặc cùngtrục khácđoạn: IDkhác.
5. Scopeđược viết3150/3150.0 vàđơnvịcanonicalmm: không sinhIDkhác chỉ do format.
6. Sourcehash hoặc scope thực sựđổi: không tái dùng selection cũ; pendingcandidate được phân giải cần ánhxạ có nguồn/xácnhận.
7. Snapshotcũ vớirowIndex, quantity_detail vàmaterials không bị sửa khi phân tích lại.

Chưa chạy các test đề xuất; chưa sửa producer/API/UI/DB. Giữ20bảng,01 quyếtđịnh scope/ownership khi mở côngviệc sau.
