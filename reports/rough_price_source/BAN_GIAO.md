# Nguồn giá phần thô — đạt focused/review14, chờ01 chốt tích hợp

03/11/2026. Áp riêng hunk04 đã01 duyệt, thêm hiệu lực raw/unknown theo release. Không mở O01 hoặc sửa eligibility/date/DB/CSV/frontend/BOQ/materials/status.

## Base, file và phạm vi

- Base `snapshot/takeoff.py` khớp FINAL_HASH backend kích thước: `3c8095c296b65adab96940b1a6091d6edbba2036aa7d057b25b21f96e349c20e`.
- Chỉ đổi function attach_prices trong takeoff.py và thêm tests/test_rough_price_source.py. AST toàn file ngoài function so base giữ nguyên; không đổi metadata/N03/quantity/status hoặc caller khác. Không sửa tests metadata đã đạt231.
- attach_prices.patch là diff lượt; SOURCE_READY_HASH.json và FINAL_HASH.json giữ2file cuối. Review metadata trước chỉ bảo chứng base, không tự bao phủ hunk nguồn giá này.

## Hành vi

- Reset best_price/price_source/est_cost trước chọn, kể cả không còn material_id/không có offer phù hợp; không giữ giá/thành tiền cũ khi vật liệu hoặc điều kiện đổi. Không đổi các field lượng, metadata, trạng thái/phần thiếu.
- Tái dùng nguyên price_offers/select_best_offer. Source ghép từ **đúng best**: mức giá, NCC/mã NCC, ngày giá, data_kind, chứng từ/source_detail, trang giá hợp lệ, VAT/cước YES/NO/UNKNOWN có nhãn Việt.
- BULLETIN giữ nhãn công bố tham khảo. price_records không phải BULLETIN giữ nhãn giá lịch sử tham khảo. SAMPLE/SYNTHETIC vẫn có dấu loại dữ liệu. Không ghép chứng từ/điều kiện của offer bị loại hoặc bịa chứng từ.
- valid_until nếu có ghi nguyên ngày “hiệu lực đến …”; nếu không có ghi “chưa rõ hiệu lực”. Không suy hiệu lực từ price_date, không gọi báo giá hiện hành chỉ vì có ngày giá, không sửa thuật toán lọc ngày hoặc tạo TTL.
- Giữ cơ sở quantity_with_waste ưu tiên hơn quantity như cũ; chỉ ra est_cost khi có lượng, complete=True và status khác D. D vẫn có thể thấy giá tham khảo nhưng không thành tiền. Không biến số thiếu thành0.

## Kiểm terminal, không DB/API/CAD/full

Collector run_focused.py lưu PID33764/handle70002, lệnh và UTC trong process.json. Child bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPTIMAT_CATALOG_OVERLAY, đặt OPTIMAT_NO_DOTENV=1. Tests nguồn dùng fixture trong RAM và monkeypatch price_offers; các hồi quy Catalog có SAMPLE overlay từ conftest, không dùng làm bằng chứng giá mua thật.

Focused chạy một lần:

```text
test_rough_price_source.py
test_catalog_pricing.py
test_rough_partial.py
test_rough_agent.py::test_rough_materials_get_prices_same_unit_only
test_rough_materials.py::test_incomplete_purchase_quantity_has_no_estimated_cost
```

**95 collected, 95 passed, 0 failed/errors/skipped/xfail/xpass, EXIT0**, pytest13,22giây, collector16,06giây. Hash225file trước/sau không changed/added/removed.

Bằng chứng: focused.log, process.json, result.json, focused_hash_before.json, focused_hash_after.json. Phạm vi hash là Python src/scripts/tests và CSV/JSON dữ liệu như collector ghi, không frontend/docs/DB. Không nạp/reset DB hoặc CAD thật, không full/TestClient.

Các ca xác định: đúng offer cùng đơn vị và chứng từ/trang/terms; đổi offer hết hiệu lực/thiếu điều kiện hoặc mất mã vật tư xóa giá cũ nhưng giữ toàn bộ field lượng; D/partial không tiền; SAMPLE/SYNTHETIC có nhãn; valid_until raw/unknown; lịch sử và VAT/cước chưa rõ không được biến thành hiện hành; complete=True nhưng D vẫn không cost.

## Review và giới hạn

14 đã đọc tĩnh2/2hash và base đúng, chưa finding mới trước terminal; chờ14 đối chiếu log/hash cuối và01 chốt. Đây chỉ là nguồn giá trên MaterialLine.price_source và guard thành tiền, không chứng minh báo giá thực đã được QS/người mua xác nhận hoặc giá thị trường hiện hành.

Cập nhật14 cuối: đã đối chiếu2/2hash với SOURCE_READY/checkout/focused trước–sau, đọc95passed/EXIT0 và225dependency0drift; phần text ngoài attach_prices bằng base. Chưa finding/blocker mới trong hunk, giữ nguyên các giới hạn eligibility/date/ACTUAL/UI/BOQ/DB/full. Review độc lập này không thay01 nghiệm thu tích hợp.

Không đổi eligibility/date/VAT normalization trong pricing, không tự quy đổi đơn vị, không yêu cầu sheetdimensions ở BOQ. Chưa browser/UI/BOQ/DB/full trên snapshot mới. Giữ source/test FINAL_HASH, trả slot cho01; nếu tích hợp sau có delta phải review đúng hash mới.

Dòng tiến độ đề xuất: “03/11/2026 — 03 áp attach_prices nguồn đúngbest/VAT/cước/chứngtừ/tranggiá/hiệulựcraw-unknown, resetgiácũ, Dkhôngthànhtiền; focused95đạtEXIT0/hash225khôngđổi. Ngoàiattach_prices ASTtakeoff giữmetadata/N03; chờ14/01chốttíchhợp, chưafull/UI/DB.”
