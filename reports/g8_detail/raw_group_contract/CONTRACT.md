# Tổng raw và coverage G8 — đề xuất backend, chưa mở source

03/11/2026. Theo BA01: chuẩn bị hợp đồng/hunk để backend phát tổng raw cùng snapshot. Không sửa bốn file lót đang HOLD, không sửa consumer của02/09 hoặc chạy test trong lượt này.

## Quyết định BA được ghi nhận

- P06/P07 dùng `source_quantity` có nhãn rõ khi đầu vào là lượng legacy **đã làm tròn ở bước trước**; geometry chỉ reference. Không mở thay đổi precision engine, không thêm dòng bù residual.
- Khi raw net đổi mà legacy vẫn cùng round3, mutation vẫn phải rebuild detail. Finalizer so legacy hiện tại không thay nghĩa vụ đó.
- P02 void=None có thể làm ledger partial trong khi parent legacy vẫn C. Consumer phải phân biệt `quantity_detail.complete` với trạng thái nguồn/legacy, không tuyên bố engine đã được sửa đánh giá đủ dữ liệu.

## 1. Đầu vào và vị trí gọi

Đầu vào duy nhất là danh sách **WorkItem đã chọn nguồn, hoàn tất net, assign_status và finalize**, cộng context phân loại tương thích của chính kết quả đó. Không lặp `plan_beams`/`structural_beams` raw để dựng công tác mới; không đọc lại bản vẽ, đo lại hoặc dùng norm/giá hiện tại tại bước xuất.

Builder tổng chỉ đọc, không sửa WorkItem.quantity/status/missing/detail, không sửa totals/materials legacy. Đặt sau finalize và trước khi đóng payload lưu/return. Phần giá có thể tiếp tục luồng cũ; thay giá không tự làm lượng raw đổi.

Đầu ra đề xuất optional/backcompat trên RoughResult:

```text
quantity_summary: QuantitySummary | None = None

QuantitySummary:
  schema_version
  quantity_snapshot_hash
  groups: list[QuantityRawGroup]
  coverage: QuantityCoverage
```

Chưa thêm DTO hoặc field vào mã. Snapshot hiện có/đã lưu vẫn là căn cứ xác nhận của người dùng; hash là đối chiếu nội dung, không phải nhãn “đã kiểm”. Kết quả cũ thiếu summary phải ghi “Chưa có tổng raw”, không dùng totals legacy thay thế.

## 2. Khóa snapshot, work và row

- `work_key` gắn theo vị trí trong **mảng works cuối cùng** của một snapshot (ví dụ w:0). Dùng thứ tự gốc backend, không dùng số thứ tự sau khi UI lọc/sắp xếp. Không gọi đây là ID xuyên phiên sửa/tính lại.
- Tham chiếu dòng là `(quantity_snapshot_hash, work_key, row_id)`. row_id chỉ duy nhất trong một công tác. Hai công tác cùng row_id=r1 không được khử trùng vào nhau.
- `quantity_snapshot_hash` đề xuất SHA256 canonical JSON của finalized works cùng context phân nhóm được sử dụng, có schema_version. Context phải đi trong payload hoặc tham chiếu bản lưu bất biến đủ để kiểm lại; không hash một input chỉ tồn tại tạm ở server rồi mất nguồn. Không đưa groups/tổng trở lại chính đầu vào hash, không tạo vòng phụ thuộc. Không lấy timestamp làm chứng minh cùng nội dung.
- takeoff_id/phiên bản kiểm hiện có được giữ để truy vết lưu trữ; không coi một ID đủ chứng minh payload không bị thay. 01/02 chốt kết nối với định danh kiểm hiện tại trước khi mở hunk.
- API/UI/Excel phải dùng cùng summary và mảng works của payload đã kiểm. Nếu hash hoặc membership không khớp, báo stale/chưa có tổng phù hợp; không tự cộng lại để che lỗi. Không có xác nhận người kiểm thì vẫn chưa được coi là đã kiểm dù hash khớp.

## 3. Khóa nhóm: gộp có điều kiện, không parse evidence

Khóa nhóm phải chứa tối thiểu stage, code, variant, unit và nguồn/basis phù hợp. Các trường hiện có cần xét thêm: formwork_of, steel_element, wall_system_id, source, basis; context mác/cấu tạo/phương pháp khi nguồn thật có khai báo.

Ví dụ CP cột và CP sàn cùng code/unit nhưng khác formwork_of không nhập một nhóm chi tiết. Thép theo bảng và thép ratio không nhập cùng basis. Cùng BE_TONG_LOT chưa đủ để gộp lót nền/lót móng khi context cấp/mác/phương pháp chưa được chứng minh phù hợp.

`source_key` là cấu trúc nghiệp vụ từ field/context có nguồn, **không phải** đoán từ dòng evidence, parse formula hoặc lấy chuỗi tên gần giống. Danh sách trích dẫn riêng của từng dòng vẫn giữ nguyên; khác địa chỉ ô không tự chứng minh khác phương pháp, giống mã cũng không chứng minh cùng quy cách.

Nếu thiếu trường để chứng minh tương thích: giữ một partition riêng theo work_key và đánh `compatibility=isolated_unknown` cùng lý do. Không giả mã định mức/mác hoặc gán source mặc định để gộp. Việc không gộp không tự đổi lượng hoặc trạng thái legacy của công tác.

Đề xuất `QuantityRawGroup`:

| Trường | Ý nghĩa |
|---|---|
| group_id/key | ID trong snapshot + cấu trúc phân nhóm đã dùng |
| member_work_keys | Công tác thuộc nhóm, mỗi công tác chỉ một leaf group |
| unit | Một đơn vị công tác; không cộng m²/m³/tấn |
| compatibility/reasons | resolved hoặc isolated_unknown; không đánh đồng với lượng thiếu |
| known_part_raw | Tổng phần biết từ detail, Decimal string/None |
| total_raw | Chỉ có khi toàn bộ công tác trong nhóm đủ theo detail |
| complete | Đủ phạm vi lượng, không phải “mọi hàng đều có diễn giải cấu kiện” |
| coverage | Đếm phần có components/aggregate/unavailable/None và dòng biết/thiếu/reference |
| missing_work_refs | Work/row + lý do thiếu để mở đúng dòng trong snapshot |

Không tạo một tổng số cho “Cả công trình” chứa nhiều đơn vị. Nếu có cây nhóm, parent cùng đơn vị/compatibility chỉ cộng **một lớp con disjoint**, không cộng leaf rows rồi cộng lại parent totals.

## 4. Quy tắc số học

1. Mỗi WorkItem có detail hợp lệ chỉ góp `known_part_raw` **một lần**. Không vừa cộng raw rows vừa cộng tổng detail. Dấu trừ đã nằm trong tổng signed contribution của detail; group không đổi dấu lần nữa.
2. Không cộng role=reference. Không nhân count/repetitions/conversion/factors lần nữa. Metadata chiều dài/diện tích không tự trở thành contribution.
3. Work chưa có detail không đóng góp số vào known raw. Dù legacy có quantity=1, không dùng1 làm raw hoặc0 thay cho thiếu. Nhóm phải incomplete cho thành viên này.
4. `known_part_raw=None` nếu không có phần biết nào; bằng chuỗi0 nếu thực sự biết0 hoặc cộng/trừ triệt tiêu. Không clamp âm thành0.
5. `total_raw=sum(member.total_raw)` chỉ khi mọi thành viên có detail hợp lệ, complete và total_raw khácNone. Còn bất kỳ thành viên unknown/no_detail/unavailable thì total_raw=None; vẫn giữ known_part_raw. Không bỏ thành viên thiếu khỏi mẫu số để đạt complete.
6. Detail aggregate có thể có tổng lượng đủ nhưng chưa có diễn giải từng cấu kiện. Vì vậy complete=True không làm coverage.components thành đủ; consumer phải hiện đúng hai nghĩa.
7. Nhóm dùng Decimal từ chuỗi, precision đủ cho các số đầu vào như helper đã duyệt. Không cộng các số đã format, không lấy `WorkTotal.quantity` hoặc tổng giá trị làm tròn làm raw.
8. known_part khi còn khoản trừ chưa biết không phải cam kết cận dưới khối lượng mua. Không dùng tổng partial để cấp nhãn đầy đủ cho vật tư/giá/tối ưu.

Các key phải đúng đơn vị trước khi cộng. Không tự quy đổi đơn vị ở grouper để “cho vào cùng tổng”; quy đổi chính xác phải là receipt của dòng/công tác, có from/to/factor/source trước khi nhóm.

Validation phải ràng summary với works cha, không chỉ tự so các trường summary: membership không lặp/không trỏ work ngoài snapshot; mỗi work đúng một leaf group; group key/unit tương thích; known/total/complete và counts khớp detail thật; hash/context khớp nội dung. Kiểm lại số tổng để phát hiện payload stale/giả không có nghĩa được ghi đè tổng sai bằng giá trị tính mới. Kết quả rỗng chỉ có count0, không tự thành “đủ100%”. Không bật validate_assignment toàn model hoặc dựa model_copy để bỏ qua cổng này.

## 5. Coverage: count trước, chưa công bố phần trăm

Phân loại WorkItem thành bốn nhóm không giao nhau: components, aggregate, unavailable, no_detail. Tổng bốn count bằng work_count trong phạm vi snapshot đang xét.

Đếm thêm độc lập:

- quantity_complete_works / quantity_incomplete_works: theo detail, không dùng parentC thay cho complete.
- contribution_rows / known_contribution_rows / unknown_contribution_rows: reference không vào mẫu số này; known chỉ nói raw_quantity có số, không nâng dependency đang thiếu.
- reference_rows: để truy vết, không góp khối lượng và không tăng số dòng bóc đã tính.
- compatibility_pending_works: chưa đủ context gộp, không phải tự động thiếu hình học.
- legacy_D_works / legacy_missing_works nếu cần đối chiếu; hai count này có thể giao nhau, không cộng thành một mẫu số.

`coverage.complete_components` chỉ true khi không còn no_detail/unavailable/aggregate và các thành viên đều đủ. Không gọi coverage này là độ chính xác, tự động hóa, tỷ lệ đáp ứng thực tế hoặc KPI M01/D02. Mẫu số nghiệm thu hồ sơ thật/ngoài phạm vi vẫn do các cổng đó quyết định.

## 6. Ví dụ giao thức riêng

`SYNTHETIC_GROUP_EXAMPLE.json` chỉ là ví dụ hợp đồng, chưa phải output backend hoặc đáp án thực.

- Hai work, mỗi work raw0,3225/legacy0,323: group raw0,6450, không phải tổng legacy0,646.
- Mỗi work đều có row_id=r1 nhưng scoped work khác nhau; phải giữ hai contribution.
- Thêm một reference100: raw không tăng.
- Thêm work có contribution unknown và work không có detail (legacy1): known raw vẫn0,6450, total=None, complete=False. Không cộng1 vào raw.
- Coverage bốn work: components3/no_detail1; contribution3 gồm known2/unknown1; reference1. Không suy “3/4 đã đủ” vì một work components đang unknown.

Ví dụ không chứa mã AF hay mức dùng M1; không làm bằng chứng cho norm/vật tư thực. Fixture M1 có nguồn vẫn là một reference riêng.

## 7. Hunk cần xin mở khi consumer lót xong

| Vùng | Hunk dự kiến | Ràng buộc |
|---|---|---|
| models.py | DTO summary/group/coverage và invariants | Không đổi quantity/status hoặc các DTO detail đã nhận nếu chưa báo consumer |
| quantity_details.py hoặc module nhỏ quantity_summary.py | Builder đọc finalized works, grouping context, Decimal sum/count/hash | Không vòng import models; không parse formula/evidence, không gọi engine/norm lại |
| takeoff.py | Gọi sau finalize và gắn summary vào chính RoughResult | O01 resolver/raw maps và attach_prices giữ; không đổi totals/materials legacy |
| tests/test_rough_quantity_summary.py mới | Row scoping, reference/sign/unknown0/no_detail, mixed unit/spec/basis, snapshot stale, sum precision, parentC/detailpartial | Pure theo slot01; không HTTP outside/full |
| 02 consumer | Hiện tổng/coverage từ backend và chặn nhầm C=detail đủ | Sole02 sau release, không tự viết source ở03 |
| 09 exporter | Đọc đúng summary đã kiểm, không dựng raw từ legacy hoặc format | Sole09 sau release; rõ raw vs legacy/coverage |

Cần chốt trước source: DTO/tên field, canonical hash/membership gắn snapshot hiện hữu, structured compatibility context và cách xử lý nhóm chưa đủ quy cách. Hiện chưa có summary này trong API. Chỉ chuẩn bị contract, không dựa vào đó để tuyên bố UI/Excel đã dùng backend raw total.
