# G8 mảnh DTO/helper — code-ready, chưa nối producer

Theo01 mở đúng3file: src/optimat/rough/models.py, src/optimat/rough/quantity_details.py mới và tests/test_rough_quantity_details.py mới. SOURCE_READY_HASH.json/FINAL_HASH.json khóa3file; DTO.patch và snapshot/models.py ghi delta.

## Đã thay đổi

DTO DetailConversion/DetailFactor/QuantityDetailRow/WorkQuantityDetail đặt sau WorkDimensions/trướcWorkItem; pureDecimal/invariant helpers ởmodels. quantity_details.py importmodels một chiều và chứa summarize/lean builder; models không import ngược. WorkItem.quantity_detail optionalNone, payload cũ giữquantity/status. Khi códetail, validator chặnunit hoặclegacy_quantitykhôngkhớpparent. Blank missing reason bịtừchối.

RawDecimalstring, signedcontribution/reference, unit,known/total/complete/scope/delta tựkiểm cảdirectDTO. Khôngnhâncount/repetitionlần2. Khôngkhôi phụcrawtừlegacyđãround. KhôngđổiWorkDimensionsbody hoặc côngthức/emitter. ASTWorkDimensionskhớpbase; O01exact4FINALhashgiữ; takeoff/N03/price_sourcekhôngđổi.

## Kiểm đã terminal

- Attempt1collectorROOTsai do vịtrífolderlồng: EXIT4,0collected,0hash; khôngtestnàochạy. Đãgiữlog/process/result tạiattempt1_runner_error (bảnbanđầutại reports/reports/g8_detail/canonical_dto/attempt1). ChỉsửaROOTcollector,rồichạyattempt2; khôngđổimãsảnphẩmgiữahailượt.
- **Attempt2:78passed,3deselected,EXIT0**, pytest5,43giây/collector7,28giây,PID44536 terminal. 42testDTO/helper và36pureWorkDimensions. BaHTTPdimensionschủýdeselect,khôngcoilàpass.
- **229tệp hash trước/sau khôngđổi**. Exact3manifestkhớpcurrent/before/after. SovớiO01focused226: thêm2filegóinày vàsrc/optimat/db/project_documents.py củaphiênkhácđãcótrướcsnapshot; changedchỉmodels.py. Khôngclaim78testđãkiểmDBfileđó.
- Cases:JSONroundtrip/payloadcũNone0/status, unit/legacyparentmismatch, directDTOtổnggiả,mixedunit,reference,sign,deduction,missing/zero,repetition,factor/conversionfinitevànguồn,Decimal>28digits,M1reference9dòngvà4tíchvậttưnguồn.

## Chưa làm

Chưagọileanbuildertừfoundation_works; khôngcapturepre-roundtrong_work,khôngemitdetailthật,khôngnốiUI/Excel. quantity_detail=None hiệnlàmặcđịnhcủaproducers. Chưa sửa walls/foundations/secondary/takeoff/boq, khôngfull/DB/CADthật. HTTPoutsideđãbịautomaticapprovalreviewtừchốiởO01,khôngthửlạihoặcnhờphiênkhácchạyhộ.

Sau khi được mở emitter, net mutation/copy(update) phải cậpnhậtdetail vàfinalvalidatecùngsnapshot; fieldoptional khôngtựchứngminhcácproducerđãđủchi tiết. FixtureM1chỉreference,khôngcatalog/groundtruthmới.

Source3fileHOLD,chờ14reviewđộclập và01tiếpnhận. Bằngchứng ởattempt2/{focused.log,result.json,process.json,focused_hash_before.json,focused_hash_after.json}, DTO.patch, FINAL_HASH.json.


## Vòng sửa parent invariant — mốc mới nhất

14 phát hiện parent D/missing có thể nhận detail.complete=True. Theo BA01, chỉ sửa models.py vàtest; helper bytegiữnguyên. Parent cómissing hoặcstatusD naytừchối completeTrue/total_rawcósố; vẫnnhậnknown_part/totalNone vàgiữlegacyquantity/status/missing. Khôngbậtvalidate_assignment hoặcđổistatusengine. Producerfinalize sau net/status/scope mutation làcổngsau,chưarelease.

**attempt3_parent_fix:82passed,3HTTPdeselected,EXIT0**, collector7,10giây,PID40208 terminal;229filehashbefore/after0drift. Exact3manifestFINALmớikhớpcurrent/before/after. CóregressionparentD/missingđủbịreject vàparentpartialgiữknown/JSONroundtrip. Log78/attempt2 giữchỉlàbảntrướcsửa; khôngdùngthaymốchiệntại.

Snapshot/diffriêngvòngsửa ởreview1/snapshot vàreview1/parent_invariant.patch; DTO.patchlàtoànbộdelta3filetừbase. SourceHOLDđợi14reviewnewhash/01nhậncode-ready. Chưacóproducer/API/UI/Excelaccepted.

14 đã chốt độc lập P2 khép trên exact3hash (SOURCE_READY=FINAL=checkout=attempt3before/after), tự đọc log82passed/3HTTPdeselected/EXIT0/229deps0drift; chưa thấy blocker mới trong DTO/helper. Điều phối01 nhận cuối; giữ giới hạn chưa emitter/finalize/UI/Excel/HTTP/full.
