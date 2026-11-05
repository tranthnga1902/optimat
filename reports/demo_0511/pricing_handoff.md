# Bàn giao giá tường và hợp đồng chọn giá

## Bổ sung lượt nối helper và vữa thiết kế

**Cập nhật cuối lượt:19passed in10.35s,exit0** với `--basetemp=reports/demo_0511/pricing_mortar_pytest_tmp`, cùng hai targettest ở dưới. VU01/VU02/VU06 cóCOMPOSED_OF trongcatalog hiện hành; dòng vữa kiểu này nay `is_intermediate=True`, giữ lượng nhưng **không best_offer/best_price/est_cost mua vữa thành phẩm**, dù cóDEALERquote. Rawoffer vẫn hiển thị nhưngineligible kèmlýdo; `price_note` hướng người dùng xemxi/cát theo cấp phối ởbảngphầnthô,missingchi phíthànhphần rõ. Không thêmxi/cátvàobilltường đểtránh cộnglặp với chuỗirough. Testmới chứngminh vữatrộntạichỗ khôngbịbiếnthành đặtmua thànhphẩm.

Hợp đồng dùng chung đã có:

```python
best, checked = select_best_offer(offers, unit, material_data_kind, actual_only, as_of=None)
```

`best` là PriceOffer hoặc None; `checked` là bản sao tất cả nguồn kèm eligible/rejection_reasons/is_reference. Không sửa offers đầu vào. `as_of` nhận date/chuỗiISO, mặc định ngày hiện tại. Giá tương lai bị loại cả chế độ kịch bản; ACTUAL DEALER/QUOTE bắt buộc mã NCC và NCC ACTUAL; BULLETIN vô danh có thể giữ làm nguồn công bố tham khảo. Rough.attach_prices do phiên chính nối, agent không sửa rough.

`bill_of_materials` đọc `getattr(group,"design_mortar_material_id",None)` khi nhóm đã chọn vữa, còn không dùng vữa hệ tường. Không có mã vữa/thiếu định mức vẫn xuất dòng missing, không mất âm thầm. Lượng theo diện tích × dày khối xây × định mức vữa/m³ như chuỗi `_masonry`; mác chọn giữ đúngmãvữa. Chỉ m³ được giữ trực tiếp hoặc tấn với khối lượng thể tích đúng vữa gốc; không lấy mật độ của vữa gốc cho một mã vữa khác, không coi m³ làbao/kg. Không suy cấp phối mua hoặc gộp vữa trộn tại chỗ thành sản phẩm vữa khô.

Định mức AE tiếp tục không cộng hao hụt lần2. Dòng khôngAE thiếu/âmhao hụt giữ lượng đã biết nhưng `est_cost=None`, không trình bày tổng mua giả. Giá chọn và source vẫn giữ để sửa phần thiếu.

Kiểm mới nhất:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_catalog_pricing.py tests/test_material_rules.py::test_bill_of_materials_prices_by_catalog_code -q -p no:cacheprovider --basetemp=reports/demo_0511/pricing_selector_pytest_tmp
```

Môi trường OPTIMAT_NO_DOTENV=1,UTF-8,khôngDB như lượt dưới: **18 passed in6.34s,exit0**. Bổ sung ca futureprice/as_of,QUOTEACTUALkhôngsuppliercode,missingwastekhôngcost,gradevữaVU01giữmã,thiếuvữa/địnhmứchiệnmissing,đổim³→tấnđúngdensityvàkhôngmượndensitykhácmã. Không fullsuite/API/DB trong lượt này.

Lượng vữa tường theo nhóm đã xác nhận và hệ tường không tự chứng minh khớp tổng rough khi rough còn có khoản trừ cột/lanh tô hoặc phạm vi công tác khác; đối chiếu hình học thuộc phần tích hợp của phiên chính.

Phạm vi được giao: `src/optimat/catalog/pricing.py`, `tests/test_catalog_pricing.py`, một fixture trong `tests/test_material_rules.py`. Không sửa API, frontend, rough, optimizer, DB hoặc dữ liệu vận hành.

## Thay đổi

- `normalize_unit(unit)->str`: chuỗi thiếu trả rỗng; UnicodeNFKC, casefold và gom khoảng trắng. `m³/m3`, `m²/m2` bằng nhau; không đổi bao/kiện/viên/kg/tấn hoặc suy số lượng trong tên đơn vị.
- `price_offers` giữ `sale_unit` thực hoặc đơn vị `price_records.unit`; **không suy sale_unit từ materials.unit**. Giữ `raw_price`, `unit_source`, `source_detail`, `supplier_data_kind`.
- Mỗi `BillLine.offers` giữ cả dòng không dùng được, có `eligible`, `rejection_reasons`, `is_reference`. Không thay đổi đối tượng nguồn dùng chung. Đơn giá không dương/hữu hạn, đơn vị thiếu/khác hoặc mức giá chưa rõ không tạo chi phí.
- `bill_of_materials(groups,catalog,actual_only=False)` giữ chữ ký tương thích. `True` yêu cầu vật liệu/giá/nhà cung cấp ACTUAL, ngày hợp lệ; ưu tiên DEALER/QUOTE cùng đơn vị. Chỉ khi không có giá mua hợp lệ mới dùng BULLETIN làm **tham khảo tường**, `best_offer.is_reference=True` và `price_note` nói rõ không phải báo giá mua/giao hiện hành.
- `BillLine.best_offer` là **đúng đối tượng được chọn**, `best_price`/`est_cost` từ đối tượng đó. UI không tự lấy offer đầu tiên vì nó có thể khác đơn vị hoặc bị loại.
- Định mức `norm_code` bắt đầuAE theo quy tắc rough đã gồm hao hụt: cả gạch và vữa `waste_included=True`, không cộng thêm% và không báo thiếu hao hụt. ChưaAE vẫn dùng% vật liệu như cũ.
- Truy vấn lịch sử tách `unit`/`source` trong DISTINCT để không làm mất các biến thể cùng nhà cung cấp, cùng ngày (ví dụ4giáCEMIA mới). Nguồn/biến thể tiếp tục giữ riêng, không tự hợp nhất thành một SKU.

Fixture mẫu cũ không cósale_unit. Một test giá qua mã danh mục nay **khai báo sale_unit tường minh trong fixture**, thay vì giữ suy luận nguy hiểm ở mã thật; không sửaCSVmẫu hoặc dòngDB.

## Callers cần phiên chính nối

- API giá tường, confirm, agent cần truyền `actual_only=True` khi ở chế độ mua thật; mặc địnhFalse dành kịch bản/kiểm tương thích.
- Frontend đọc `best_offer`; hiển thịBULLETIN và `price_note`; giá bị loại vẫn xem được lý do nhưng không lấy nhân lượng.
- Agent optimizer được gửi hợp đồng normalize_unit và AEwaste; không tự suy sale_unit hoặc tính chuyển đổi kiện/bao khi chưa có căn cứ riêng.
- Rough `attach_prices` vẫn thuộc phiên khác. Nó cần cùng chính sách nguồn/đơn vị nếu chế độ thật; không suy việc sửa giá tường đã sửa hết giá phần thô.

## Kiểm đã chạy

```powershell
$env:OPTIMAT_NO_DOTENV='1'
$env:PYTHONIOENCODING='utf-8'
Remove-Item Env:DATABASE_URL,Env:OPTIMAT_TEST_DATABASE_URL -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -m pytest tests/test_catalog_pricing.py tests/test_material_rules.py::test_bill_of_materials_prices_by_catalog_code -q -p no:cacheprovider --basetemp=reports/demo_0511/pricing_pytest_tmp_final
```

**13 passed in4.65s,exit0.** Kiểm giá50/kiện không nhân số viên, đơn vị thiếu không suy, giá cùng đơn vị đúng, SAMPLE ởoffer/supplier/material không tạo chi phí thật, DEALERưu tiênBULLETINrẻhơn, fallbackthamkhảo rõ,giá0/âm/NaN/Inf/ngàythiếu/sai bịloại,AEgạch/vữa khôngcộnghao hụt lần2.

Chưa fullsuite, API/TestClient hoặc DB trong lượt này. Không cam kết giá còn hiệu lực chỉ từ ngày nguồn; chưa thực hiện quy đổi bao/kiện hoặc xác minh thời hạn báo giá. `actual_only=True` không biến BULLETIN thành báo giá mua.
