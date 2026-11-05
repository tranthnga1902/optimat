# Gói SQL ACTUAL cho demo05/11 — đã apply no-op an toàn

## Cập nhật sau gói07 — trạng thái DB mới nhất

Gói06 bên dưới vẫn là59giá cũ, đã repeatno-op0/0 lúc17:16:28 ngày03/11/2026 giờViệtNam. **Gói07 mới** đã COMMIT lúc17:27:14, thêm1NCC/4giá: tổngsuppliers2866→2867,price_records59→63. Lần2 lúc17:27:45no-op0/0. SQLchuẩn `sql/07_cement_historical_actual.sql`; receiptđầu `07_cement_historical_actual_first_apply_receipt.json`,receiptlần2 `07_cement_historical_actual_apply_receipt.json`. Xem `07_APPLIED.md` choIDs1426–1429 vàsupplierCBG-991233626E.

Đây là4giá xi măngCEMIA lịchsử17/03/2026,đồng/tấn,baoKPK50kg,đãVAT,vậnchuyểnUNKNOWN; giữtênbiếnthểcao cấp/đa dụng trongsource. PDFđãđược hai phiên xemảnh, currencyVNĐ xácnhận trang1. Khônggọilàbáogiámuahiệnhành hoặc thêm6thángdữliệu. Giá/NCC07táchbiệtsource/văn bản/ngày với06;khôngghiđègiácũ.

Lượtthử07đầu bịpsycopgdiễngiải `%20` trongURLnhưplaceholder nênđãrollback. Runnerđãdùng `no_parameters=True`, sauđómớicóhaiapplyreceiptCOMMIT. Băm manifest/PDF/staging/reviewgốcgiữnguyên;khôngsửa07_cement_review.mdhoặcstagingJSONđểđánhdấuapplied, trạngtháiđượcghi riêngở07_APPLIED.md. KhôngcóDBwrite tronglượtcậpnhậttàiliệunày.

13supplier_materials/4vehicles/1labor_rateSAMPLEvẫn tồn tạitừtrước vàkhôngđượcdùnglấpthiếutheoACTUAL-only. Nguồnmuavậttư/giaohàngthậtvẫnthiếu. APIview/structural13cađạttrongbatch74testtrọngtâmtheođiềuphối;sourceổnđịnhchờfullsuite. UIchưakhépdoHMR/CADdài, khôngđánhhoànthànhtoànbộdemo.

Phạm vi theo yêu cầu mới: **ACTUAL có nguồn, thiếu giữ trống**. Agent chuẩn bị không kết nối DB; phiên chính sau review đã apply. Generator/test vẫn ởreports/demo_0511 để giữ khung hash; SQLcanonical đã chép tới **sql/06_demo_actual.sql**, không chỉnh filecanonical trong lượt này.

## File và kết quả dry-run

- `build_demo_actual_sql.py`: generator chỉ đọc CSV/rules/catalog/biên nhận cũ, không dùng get_engine/URL hoặc thực thi dump.
- `06_demo_actual.sql`: transaction PostgreSQL chỉ INSERT suppliers và price_records, ON CONFLICT DO NOTHING, RETURNING khóa thực sự thêm.
- `06_demo_actual.manifest.json`: SHA256 các nguồn/SQL,20supplier candidates và59price candidates với đủ khóa nguồn, `executed=false`.
- `test_demo_actual_sql.py`: các ca validate nguồn/đơn vị/giá hữu hạn, không ACTUAL, duplicate, quote SQL và đọc bằng chứng; không có test DB.

Dry-run: exit0, **20NCC CBG,59giá ACTUAL/BULLETIN,6915 dòng không ghép/đang bị từ chối bỏ qua, ngày2026-06-20**. Đây là ứng viên, không phải số mới. `db_apply_receipt.json`: databaseoptimat, **committed=true, thêm0suppliers/0price_records**, trước/sau2866suppliers/59prices. Tất cả20NCC/59giá đã có nên no-op, không ghi đè hoặc gọi thêm59giá mới.

`apply_actual_sql.py` của phiên chính mặc định preflightREADONLY; `--apply` mớiINSERT transaction+RETURNING và receipt. `db_preflight.json`:apply=false/committed=false. Applyreceipt SQLsha256 `87fec90ac24e34049c00fb4f68f09ec93019e763da6eb0e1b319ba020f5a8d3e`. Không tự generate đè gói đãreview.

DBsnapshot:98materials/22wall_systems ACTUAL,2863ACTUAL+3SAMPLE suppliers,59ACTUAL/BULLETIN prices.13supplier_materials/4vehicles/1labor_rate **đềuSAMPLE**, chưa nguồn mua/xe/nhân côngACTUAL. Snapshotinactiveuser là mốc ban đầu; phiên chính xác nhận sau đó đã có activeadmin/session.

```powershell
Set-Location -LiteralPath 'C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai'
$env:OPTIMAT_NO_DOTENV='1'
$env:PYTHONIOENCODING='utf-8'
.venv/Scripts/python.exe reports/demo_0511/build_demo_actual_sql.py
```

Generator không ghi source data, không import config/DB, không nạp `.env`. Không đặt cờ này như cấu hình dịch vụ web; đây chỉ là process sinh SQL.

## Nguồn và metadata không suy đoán

Nguồn nội dung: `data/cong_bo_gia/02.01_2026_CBGVL-SXD.csv`. Chỉ nhận dòng đã có material_id, quy_tac và giá quy về danh mục, không có ly_do từ chối. Kiểm lại pattern/đơn vị/hệ số theo `data/rules/cong_bo_gia.csv` và mã ACTUAL/đơn vị theo `data/catalog/materials.csv`.

CSV không chứa ngày/VAT/địa bàn đầy đủ. Generator **không suy ngày theo tên file**; đọc literal ACTUAL/BULLETIN INSERT của lần nhập đã có trong `sql/optimat_day_du.sql`, ghép đúng supplier_id + material_id + trang/tên/đơn vị nguồn. Kiểm lại đơn giá/quy đổi/đơn vị/quantity1; giữ nguyên date,province,source,VAT,transport từ biên nhận đó. Dump chỉ là **bằng chứng lần nhập trước**, không phải PDF gốc được đọc kiểm lại. Generator từ chối mapped row không có đúng một metadata receipt hoặc không khớp.

**Đính chính wording audit cũ:** `02.01/2026/CBGVL-SXD` là số văn bản; không đủ căn cứ gọi “công bố tháng01”. Lần nhập cũ lưu **2026-06-20**; importer `read_pdf` có logic đọc dấu thời gian chữ ký `20/06/2026`, và reports/data_check.json ghi cùng ngày. Gói này bảo toàn mốc lưu đã có, không xác minh lại PDF nguyên bản hoặc hiệu lực báo giá đến05/11.

Source price giữ chính xác định dạng cũ `Công bố giá 02.01/2026/CBGVL-SXD (Hà Nội), tr.N: tên (đơn vị nguồn)` để không phá khóa chống trùng. Đây vẫn là **BULLETIN tham khảo**, không phải báo giá mua, không chứng minh còn hiệu lực/giao đến công trình.

## An toàn/idempotent và hạn chế

- Không schema/migration/DROP/DELETE/UPDATE; không đụng13giá SAMPLE/4xe SAMPLE/nhân công SAMPLE đang có.
- Không tạo supplier_materials, vehicles, labor_rates hoặc số đo/leadtime giả. NCC mới chỉ có tên/tỉnh/nguồn/ngày, coords/leadtimeNULL, verifiedFALSE.
- Khóa supplier là supplier_id ổn định dùng helper bulletin.supplier_id. Khóa giá theo index hiện có: `(material_id, COALESCE(supplier_id,''), date, quantity, source)`. Mọi ứng viên có supplier_id/date/quantity/source không NULL.
- ON CONFLICT DO NOTHING giữ bản hiện có nguyên vẹn: không sửa giá khác nhau cùng khóa, không biến SAMPLE có sẵn thành ACTUAL. Cần ghi conflict retained, không báo đã sửa số cũ.
- Thiếu material/schema hoặc vi phạm FK phải rollback toàn transaction; không tự thêm mã/đơn vị vào DB để làm script qua.
- PostgreSQL phải có schema/index chuẩn đã rà; nếu index dedup bị thiếu thì dừng và báo, không tự sửa schema trong gói này.

## Quy trình apply đã dùng / cho lần bổ sung được cấp tiếp

1. Kiểm không còn khung hash/test khóa việc DB; dùng database hiện hành được chủ đồ án cho phép. Không dùng test DB reset.
2. Đọc manifest/SQL/hash; kiểm mỗi required supplier hiện có vẫn ACTUAL; kiểm material unit runtime trùng manifest và unique index uq_price_records_dedup hiện có. Nếu lệch dừng, không tự update.
3. Ghi pre-count theo data_kind và snapshot các ứng viên đã tồn tại theo đúng natural key. Không log mật khẩu/URL.
4. DBeaver: mở `06_demo_actual.sql`, chạy cả script; giữ autocommit phù hợp BEGIN/COMMIT. Các câu RETURNING cho biết khóa thực thêm. Nếu chạy bằng SQLAlchemy phiên chính cần thu RETURNING từng INSERT và lưu receipt, transaction duy nhất, không chạy sql/optimat_day_du.sql.
5. Ghi receipt: hashSQL, database identity không chứa credentials, thời gian, suppliers_inserted, price_ids_inserted, conflict_retained, counts trước/sau. Chạy lại lần2 để chứng minh inserted0 khi source không đổi.
6. Chỉ rollback đúng ID/khóa **thực sự RETURNING trong lần apply** khi có yêu cầu; không DELETE mọi khóa candidate trong manifest vì chúng có thể là dữ liệu đã có trước. Không có rollback tự động mang tính phá hủy trong gói.

Trạng thái kiểm: generator chạy thành công; phiên chính applyDBno-op theo receipt trên. Agent được cấp lượt testreport-scoped:

```powershell
$env:OPTIMAT_NO_DOTENV='1'
$env:PYTHONIOENCODING='utf-8'
Remove-Item Env:DATABASE_URL,Env:OPTIMAT_TEST_DATABASE_URL,Env:OPTIMAT_CATALOG_OVERLAY -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -m pytest reports/demo_0511/test_demo_actual_sql.py -q -p no:cacheprovider --basetemp=reports/demo_0511/sql_test_tmp
```

Kết quả **9 passed in0.15s, exit0** kiểm generator/validation/escaping từfixture. Bằng chứng DB tách riêng: preflight+applyreceiptCOMMITTEDno-op, không cóIDthêm đểrollback. Không dùng9tests như testDB/fullsuite. Lần bổ sung mới vẫn cầnreview/source/hash mới, không tự chạy lại.

Lợi ích của gói này là một lần nhập có nguồn, tái lập và không trộn dữ liệu mẫu. Nó **không bổ sung báo giá gạch GN01/GN03/VU02 hoặc vận chuyển/leadtime thật** vì nguồn hiện có không cung cấp chúng; tối ưu mua ACTUAL vẫn có thể thiếu dữ liệu sau no-op.
