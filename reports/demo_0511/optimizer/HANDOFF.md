# Optimizer mua vật tư — SOURCE-READY, focused PASS

## Phạm vi

Đã sửa `src/optimat/optimize/problem.py`, riêng Constraints/GroupChoice/WallGroup trong `src/optimat/schemas.py`, thêm `tests/test_optimize_procurement.py`. Không sửa rough, catalog, frontend, main.py, dữ liệu hoặc DB. `tests/test_optimize.py` không đổi. Dùng helper `normalize_unit` do demo_data cung cấp trong catalog/pricing.py.

## Request contract cho giao diện

- `constraints.procurement_mode: bool = False`. Web mua vật tư gửi True. False giữ kịch bản tương thích nhưng luôn nhãn tham khảo/SAMPLE/ước tính.
- `constraints.approved_wall_system_ids: list[str] = []`. Mặc định chỉ hệ thiết kế; hệ khác chỉ khi trong danh sách duyệt và cùng detect_class/vai trò. keep_design_material=True vẫn khóa đúng thiết kế.
- Procurement cần truyền rõ site_lat/site_lon (model_fields_set), hữu hạn và trong miền hợp lệ; không dùng mặc định Hà Nội im lặng.
- Procurement phải có province; không tự lấy nhân công tỉnh duy nhất trong DB.
- Mỗi WallGroup phải có design_wall_system_id và design_material_share=1 cho toàn bộ nhóm đã xác nhận.
- `WallGroup.design_mortar_material_id: str|null = None`: chỉ ghi đè hệ thiết kế; đổi mác chỉ vữa m³->m³ như rough._masonry, không chuyển keo AAC tấn sang vữa trộn. Hệ thay thế vẫn dùng vữa của hệ đó.
- `WallGroup.min_confidence: float|null = None`: cho nguồn đo đã duyệt không có điểm AI.

## Result contract

GroupChoice giữ fields cũ, thêm:

- main_material_cost: tiền vật liệu chính.
- mortar_material_id / mortar_material_name / mortar_quantity / mortar_unit / mortar_unit_price / mortar_cost.
- material_cost trong procurement = main_material_cost + mortar_cost (kịch bản cũ vẫn chỉ vật liệu chính và được ghi nhãn thiếu vữa).
- cost_complete: đủ lượng/giá ACTUAL của phạm vi nhóm đã xét; KHÔNG phải xác nhận báo giá giao hàng hay đảm bảo ngân sách/hạn thực tế. Chỉ có True ở procurement khi đủ mọi nhóm. Xe tính theo cự ly vẫn là ước tính.
- transport_estimated, supply_estimated, cost_basis.
- distance_km nay nullable: quote đã gồm giao không tự tính cự ly, trả null.
- Quote đã gồm giao: vehicle_id='DELIVERY_INCLUDED', trips=0, transport_cost=0, transport_estimated=False. Đây là nhãn phương thức giao trong kết quả, không tạo bản ghi xe ACTUAL/SAMPLE.

## Cổng dữ liệu

- ACTUAL cho hệ tường/vật liệu/vữa/NCC/báo giá/nhân công và xe nếu tự mô hình vận chuyển.
- Giá DEALER/QUOTE có ngày không tương lai, giá hữu hạn dương, sale_unit cùng đơn vị chuẩn; không tự quy bao/kg/tấn. Giá đã có không bị mô hình ghi đè (cả scenario).
- Chỉ quote VAT YES vì mô hình hiện chưa có thuế suất để cộng quote VAT NO; transport_included phải YES/NO. Không rõ điều kiện bị chặn.
- Vữa cùng nhà cung cấp và cùng điều kiện với vật liệu chính; tính lượng vữa và tiền vữa. Vữa tấn cần density của hệ. AE đã gồm hao hụt; nguồn khác phải có % hợp lệ.
- COMPOSED_OF (vữa trộn tại chỗ): chưa mở tính giá từng xi/cát, nên chặn candidate; không dùng giá vữa thành phẩm thay cho cấu tạo đã xác nhận. Đây là giới hạn quan trọng của dữ liệu thật hiện nay.
- Quote transportYES và không ràng buộc tải trọng: không cần bản ghi xe hoặc tọa độ NCC. Nếu có max_vehicle_ton: cần xe ACTUAL phù hợp và max_truck_ton NCC đã biết không vượt hạn để tránh giả định giao vào đường nhỏ.
- Quote transportNO: phải có xe ACTUAL với phí hữu hạn và tọa độ NCC. Cự ly/hành trình/số ngày/chi phí xe là mô hình ước tính, ghi rõ.
- Một nhóm thiếu/chưa báo giá/chưa xác nhận làm cả lần procurement không có solutions; không kiểm ngân sách trên tổng đã bỏ nhóm. Kịch bản cũ vẫn bỏ nhóm kèm notes và nhãn tham khảo.

## Kiểm thử

Lệnh: `.venv/Scripts/python.exe -m pytest tests/test_optimize_procurement.py tests/test_optimize.py -q -p no:cacheprovider`, môi trường OPTIMAT_NO_DOTENV=1, bỏ DATABASE_URL và OPTIMAT_TEST_DATABASE_URL.

Kết quả cuối: **37 passed in 22.47s, exit0**, log `pytest_focused.log`. Gồm 31 ca procurement/kịch bản mới và6 ca optimizer cũ (có đối chứng NSGA-II/vét cạn trên sampleDXF). Không DB, không heavyCAD, không full suite. Mọi dữ liệu ACTUAL trong test là fixture giả lập trong bộ nhớ, đã ghi rõ ở đầu test; không được dùng làm dữ liệu/nghiệm thu thật.

Snapshot: problem.before.py,schemas.before.py,test_optimize.before.py,hash_before.json. Diff: optimizer.patch. Hash cuối: hash_source_ready.json.

- problem.py AF582A5DF4901168D324300506B4E9DB3DF316E4F903CA7C2DDA5D740262B90C
- schemas.py CDF3AD62FEF7E78938A06BDF9DB53CD992532CC26D3FE290FCEF508154528B40
- test_optimize_procurement.py 55A334DCE1EEEFAF6850FA42B2D41CE6618C9FF12C02590A126672E3512A28C4

## Giới hạn còn lại

Chưa chạy trình duyệt/API thực hoặc DB. Chưa có giá xi/cát theo cấp phối trong optimizer (đã chặn), chưa tối ưu gộp chuyến nhiều nhóm, chưa tuyến đường hoặc báo giá vận tải xác nhận; phí xe từng nhóm là ước tính có thể bảo thủ. U chỉ lớp xây, không tự nhận là U hoàn chỉnh tường nhiều lớp. Chưa kiểm hiệu lực báo giá khi nguồn không cung cấp ngày hết hạn; hiển thị ngày và cần xác nhận với NCC. Chưa tuyên bố đủ phương án mua thật trên hồ sơ demo khi dữ liệu còn thiếu.
