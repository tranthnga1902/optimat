# A01 — Chuẩn bị sửa hao hụt theo phần góp

03/11/2026 — Codex, **CHỈ ĐỌC / CHƯA TRIỂN KHAI**. Đã rà materials/models/takeoff/boq, callers và test liên quan. Không sửa source/tests/DB, không chạy test. N01 có chủ khác đang kiểm; chỉ mở A01 sau phân công điều phối.

## Hiện trạng và phạm vi sửa nhỏ

- `materials._Bill.add:86–112` giữ lượng tổng chưa làm tròn trong MaterialLine.quantity nhưng MaterialUse.quantity đã làm tròn 4 chữ số; truyền waste_included trên từng use.
- Cờ được truyền từ `_masonry` (mã AE), `norm_line` (norm_code), qua mortar và COMPOSED_OF. Đây là hợp đồng dữ liệu hiện có, không rà lại tính đúng pháp lý của nguồn định mức trong A01.
- `_Bill.result:235–273` chỉ bỏ cộng % khi **mọi** use đã gồm hao hụt. Dòng trộn hai cơ sở bị nhân thừa. Trạng thái được tính trước bước này; thiếu % hiện chỉ thêm missing, không làm complete/status phản ánh thiếu lượng mua.
- Ưu tiên chỉ sửa `src/optimat/rough/materials.py` và `tests/test_rough_materials.py`. Không sửa models/takeoff/BOQ/định mức/schema; nếu cần các file đó, báo điều phối trước. Không tạo engine hoặc quy tắc hao hụt mới.

## Cách sửa đề xuất

1. Trong `_Bill.add`, giữ hai tổng riêng nội bộ theo cùng khóa vật tư: `included` (đã gồm), `not_included` (chưa gồm); cộng số thô trước làm tròn. Có thể dùng dict riêng trong _Bill, không thêm trường API/model. Không cộng lại uses đã làm tròn để tránh sai số tích lũy. Giữ None khác 0, giữ dấu âm.
2. `quantity` giữ nguyên hợp đồng số tổng phần biết trước bước cộng bổ sung; chính xác hơn đây là tổng lượng từ nguồn, **có thể đã gồm hao hụt ở một số use**. Không đổi nó thành tổng mua hoặc trừ hao hụt ngược khỏi định mức. Min/max và uses không bị nhân thêm.
3. Nếu mọi phần biết đã gồm hao hụt, `quantity_with_waste = quantity`; không cần %. Nếu có phần biết chưa gồm, với % hợp lệ: `included + not_included × (1 + pct/100)`. Làm tròn 3 chữ số ở cuối, không từng phần. 0% hợp lệ; phần trừ âm áp cùng hệ số, không abs/clamp.
4. Phải theo dõi **có phần chưa gồm** theo từng đóng góp, không suy từ tổng ròng: +10 và −10 có thể triệt tiêu nhưng không được dùng triệt tiêu làm bằng chứng % đã biết. Đề xuất vẫn yêu cầu % khi có use chưa gồm có lượng khác 0; use 0 đã biết tự nó không cần %. Use None là thiếu lượng, không phải 0.
5. Thiếu/không hợp lệ % (âm, NaN, ±inf) khi có phần cần %: giữ quantity phần biết, `quantity_with_waste=None`, complete=False, lý do rõ và status=D. Không gán % mặc định, không dùng riêng subtotal đã gồm làm tổng mua. Không tự coi %>100 sai nếu chưa có quy tắc dữ liệu; âm của lượng hợp lệ khác âm của tỷ lệ không hợp lệ.
6. Một use chưa biết lượng vẫn giữ complete=False/D. Khi % cho các phần biết hợp lệ, có thể giữ `quantity_with_waste` của **phần biết**; không trình bày nó như tổng đủ. Không có lượng biết thì cả quantity và quantity_with_waste là None. Khi % cần cho phần biết còn thiếu, qww=None như bước 5.
7. Tính lại status sau bước kiểm hao hụt; không nâng mức trạng thái nguồn/confirmation. Không hạ D cho mọi missing một cách máy móc: thiếu khối lượng riêng chỉ thiếu vận chuyển, không tự làm thiếu lượng mua. Giữ phân biệt lý do thiếu lượng/hao hụt với thiếu chuyển đổi vận chuyển.

## Ca hồi quy phải có khi được mở triển khai

| Ca SYNTHETIC | Kỳ vọng |
|---|---|
| 10 đã gồm + 10 chưa gồm; 3,5% | quantity=20; quantity_with_waste=20,350, không phải 20,700 |
| Tất cả đã gồm; % trống hoặc không dùng được | qww=quantity; không thêm lỗi thiếu % |
| Tất cả chưa gồm; 3,5% / 0% | qww=20,700 / 20,000 cho tổng 20; giữ hành vi đơn cơ sở |
| 10 đã gồm + 10 chưa gồm; % trống | quantity=20, qww=None, complete=False/D; lý do thiếu %, không 0 |
| % âm/NaN/±inf, có phần cần % | Không xuất tổng mua hữu hạn giả hoặc NaN/inf; giữ quantity, qww=None, thiếu rõ |
| 10 đã gồm − 2 chưa gồm; 3,5% | quantity=8; qww=7,930; không đổi dấu hoặc nhân phần đã gồm |
| +10 và −10 chưa gồm, % trống | quantity=0 nhưng qww chưa đủ; không suy đầy đủ từ tổng ròng 0 |
| 10 đã gồm + use None chưa gồm | quantity=10; qww=10 là phần biết, complete=False/D; không giả định use None bằng 0 |
| 10 chưa gồm + use None; %3,5 | quantity=10; qww=10,350 phần biết, complete=False/D |
| Tất cả use None | quantity/qww=None, complete=False/D; không sinh 0 |
| Nhiều phần nhỏ cần làm tròn | Tổng từ số thô; chỉ round cuối; không lệch vì uses round 4 |

Giữ hồi quy `test_masonry_bricks_and_mortar_split`, `test_formwork_materials_by_type_and_element`, `test_concrete_ready_mix_and_site_mix`, `test_missing_work_quantity_warns`, `test_rough_plaster`. Test bê tông thương phẩm hiện khẳng định complete=True dù thiếu % (`test_rough_materials:56–57`); cần đổi kỳ vọng **có chủ ý** sang giữ quantity=10 nhưng qww=None/complete=False/D, không sửa dữ liệu cho test đẹp.

## Ảnh hưởng callers và giới hạn phải báo

- `materials_for_works → compute_rough` (`takeoff:310,335–339`): giữ quantity phần biết; D được truyền lên RoughResult. Không đổi công thức công tác.
- `attach_prices` (`takeoff:360–361`) hiện fallback qww sang quantity nhưng chỉ tính est_cost khi complete. Với thiếu % làm complete=False, không còn chi phí từ lượng mua chưa đủ. Cần kiểm ca này khi điều phối cho phép; không sửa pricing tiện trong A01.
- `weight_kg` và `transport_volume_m3` vẫn tính từ quantity (`materials:257–259`); `by_group/by_class` cộng các số kg đó, **chưa phải kg mua có hao hụt**. `weight_complete` hiện chỉ xét có số kg, có thể True ngay khi một dòng partial/D. Không đổi cơ sở này trong A01; ghi giới hạn, chuyển Q02/P02 xử lý mức đủ và nhãn. Không hứa tổng nhóm sẽ thành tổng mua sau bản sửa.
- BOQ “Vật liệu” (`boq:73–79`) hiện xuất quantity, kg, complete/status/missing, chưa xuất qww. Bộ tối ưu (`boq:100–104`) đưa dòng D vào missing và `known_part=m.quantity`; phải giữ nguyên known_part, không gán 0 hoặc đổi sang lượng mua. Giữ subtotal partial chỉ để rà, không xuất thành vật liệu tối ưu đầy đủ.
- Trang do-boc/Rough.tsx hiển thị qww riêng; trang phan-tho cũng đọc qww. Chưa đổi UI trong A01; phần biết có số nhưng D cần người dùng đọc kèm complete/missing. Nâng nhãn partial thuộc Q02/P02.
- C01 đã chặn so nhóm công tác thiếu/D và chưa mở so vật tư khi thiếu truy vết cùng phạm vi/hao hụt. A01 không tự mở cổng vật tư C01, không tăng KPI hoặc nâng D02 da_kiem.

## Cổng giao dev sau N01

Khóa đúng hai file trước sửa, lưu snapshot/hash; test từng ca bằng Catalog CSV cô lập và fixture SYNTHETIC, không DB. Xin lượt test trọng tâm khi được giao thực thi; chưa chạy trong lượt chuẩn bị này. Bàn giao diff tối thiểu, test/lệnh/log/exit, chứng minh 20,350 và known_part, ảnh hưởng complete/status có chủ ý; ghi giới hạn by_group/BOQ nêu trên. Không full suite nếu chưa được điều phối cấp lượt.
