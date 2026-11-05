# N02-b3 / Q02 — bàn giao partial, chờ review

03/11/2026 — **SOURCE-READY cuối + partial thuần đạt; CHỜ REVIEW**, chưa tự nghiệm thu b3/N02. Chỉ sửa bốn source file được cấp (`rough/steel.py`, `status.py`, `takeoff.py`, `materials.py`), NEW `tests/test_rough_partial.py`; sau review điều phối mở thêm **đúng hai nhãn** `rough/boq.py`. Không đổi model/schema/frontend/main/rebar/data/DB/deps, không restart/reload/kill worker QA.

## Thay đổi và trước–sau

- `assign_status`: quantity có số nhưng còn missing → D, inputs có lý do; không xóa/zero lượng đã biết. Trạng thái có sẵn được giữ theo `worst_status` với đầu vào mới; inputs có sẵn được bảo toàn/dedup. Helper có D/C do phụ thuộc trước đó không bị nâng A; không parse evidence/free-text để xác định trạng thái. Đã đọc callers: compute_rough gọi một lần trên works mới tạo; test giằng/thang gọi trực tiếp. Ca tính lặp và đầu vào D/C có/không inputs đạt.
- `steel.schedule_works`: row kg=None luôn tạo lý do thiếu ngay cả row cũ chưa có missing. Giữ subtotal kg biết được. `steel_schedule_t` chỉ thay **số tấn**, giữ missing/evidence nguồn của nhóm đã có bảng; scalar nhập không là bằng chứng giải quyết phạm vi. Hàm lượng giữ missing của thể tích bê tông nguồn. Bản tối thiểu bảo thủ giữ toàn bộ missing của bảng khi nhập tổng, không đoán lý do nào được giải quyết từ tổng số.
- `WorkTotal` và tổng cốp pha: con có missing/D/None → complete=False; subtotal và trạng thái yếu nhất giữ nguyên. `group_totals/class_totals.weight_complete` không True khi lượng vật tư nguồn chưa đủ, dù mọi dòng có weight_kg. Comment được sửa cho đúng nghĩa, không thêm field.
- `_Bill.add`: merge missing của công tác vào mọi vật tư/use phụ thuộc (kể cả dây buộc norm_line). Work D chưa có missing dùng lý do nguồn chưa đủ; use/line D, complete=False, giữ số đã biết. Dòng vật tư độc lập không bị hạ chỉ vì vật tư khác pending. A01 raw waste parts, trace use làm tròn, dấu âm/triệt tiêu/None không đổi công thức cộng. `lines_missing` đồng thời hạ complete của dòng liên quan.
- Intermediate bê tông/vữa nhận work nguồn: giữ subtotal nhưng complete=False khi lượng nguồn missing/D/None. Không thêm trường vào IntermediateLine. `attach_prices` giữ guard cũ: có giá tham khảo nhưng est_cost=None khi line incomplete. Optimizer cũ loại dòng D; không thêm engine tính.
- Hai nhãn BOQ nhóm/loại khi weight_complete=False đổi thành **“chưa đủ dữ liệu khối lượng”**, không luôn đổ nguyên nhân cho density. Sheet Vật liệu vẫn giữ missing_reason chi tiết.

Repro điều phối tại `reports/partial_review_20261103/before_b3.json` và `before_b3_known_waste.json` được dùng làm ca bắt buộc: hai bảng pending ×31.60 kg → công tác **0.063 t** theo làm tròn engine, D + missing; tổng chưa đủ. Manual tổng 0.0632 hoặc 0.2 giữ số nhập (làm tròn hiện hành), vẫn pending. Dây buộc TH10 với waste_pct=0 trong **bản sao catalog trong RAM** vẫn incomplete/D do scope, không do thiếu %. Không sửa CSV để tạo ca kiểm. Cùng scope đã rõ → 31.60 kg trước đổi tấn/làm tròn; hai tầng độc lập →63.20 kg; không tự làm mất thiếu quy cách/hao hụt khác.

## Các lượt test — phân biệt đúng phiên bản

Mọi subprocess bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL, đặt OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1; không cacheprovider, basetemp riêng. Dữ liệu SYNTHETIC trong RAM, không TestClient/API/CAD thật/DB/full suite.

| Bằng chứng | Kết quả / phiên bản |
|---|---|
| `pytest_partial.log`, `result_partial.json` | Lượt đầu **36 passed, 1 failed**, exit1. Lỗi kỳ vọng test dây buộc dùng 11.95; CSV sẵn có là khoảng 7.85–16.07, trung điểm **11.96**. Chỉ sửa số kỳ vọng thành phép tính khoảng đúng, không sửa catalog/source để né lỗi. Giữ nguyên log đầu |
| `pytest_pure_regression.log`, `result_pure_regression.json` | Sau sửa kỳ vọng: **105 passed**, exit0, 13.41s. Partial + test_rough_materials (A01), test_rough_formwork_materials (B01), test_rough_steel, test_rough_status (Q01 thang), test_rough_stairs. Handle **81537 đã terminal** trước sửa nhãn BOQ cuối |
| `pytest_partial_final.log`, `result_partial_final.json` | Bản cuối thêm ca prior status không inputs và nhãn BOQ trung tính: **41 passed**, exit0, 9.37s. Chỉ NEW test_rough_partial.py. Handle **59794 đã terminal**; không test nào còn chạy của phiên này |

Lệnh bản cuối:

```text
python -m pytest tests/test_rough_partial.py -q -ra -p no:cacheprovider --basetemp=reports/n02/b3/temp_partial_final
```

Không cộng 105 + 41 vì có ca chồng. 105 là hồi quy trước sửa nhãn cuối; 41 kiểm source cuối. API/Excel HTTP, worker, tích hợp đầy đủ và full cần điều phối/J04 cấp tiếp. Test Excel/optimizer ở bộ partial dùng trực tiếp **compute_rough chung** và BOQ/export hiện có, không gọi API hay tính lại công thức song song.

Các ca thêm: numeric/zero/âm/None + missing; structured D/C có/không inputs và gọi lại; known+unknown kg; manual override pending; scope cùng/khác tầng; formwork subtotal có con thiếu; intermediate bê tông/vữa; mọi dependent use/line và vật tư độc lập; group/class có kg nhưng incomplete; báo giá tham khảo/không est_cost; optimizer loại D và BOQ lý do đúng; request cũ/confirmed JSON không xóa pending; raw parts chính xác trước làm tròn, dấu âm và None.

## Môi trường và SOURCE-READY/hash

Trước chạy test đã gặp shell exit **-1073741502 / 0xC0000142** và Node **0xC000026B**, không tạo test handle. Không restart/kill; các lệnh đọc sau đó phục hồi. Đã đọc lại `reports/MOI_TRUONG_20261103.md` và callers, chốt SOURCE-READY trước test. Không lấy focused166 b2 làm bằng chứng b3. Không sửa báo cáo môi trường dùng chung của điều phối.

- `before/`, `hash_before.json`: snapshot bốn source + path test mới; `boq_label_hash_before.json` chụp riêng trước đúng lượt điều phối mở hai nhãn BOQ. `hash_before_all.json` tổng hợp hai mốc cấp quyền, không giả chụp mọi file cùng lúc.
- `source_ready.json`/`source_ready/` và `N02-b3_source_ready.diff`: mốc đầu trước test. `hash_source_ready_corrected.json`: sau sửa kỳ vọng 11.96. `source_ready_final.json`, `source_ready_final/`, `N02-b3_source_ready_final.diff`, `hash_source_ready_final.json`: mốc cuối sau sửa nhãn và trước final41.
- `after/`, `N02-b3.diff`, `hash_after.json`, `hash_diff.json`: source cuối; `hash_diff_since_source_ready_final.json` rỗng, không đổi trong lúc final41. `git diff --check` exit0. Tập hash chỉ gồm sáu file được cấp, không nhận là hash toàn backend.

## Việc còn lại

Đề nghị điều phối review riêng preservation trạng thái cũ, manual total giữ missing, ảnh hưởng nguồn vào intermediate và nhãn weight_complete. Sau review cấp J04 focused API/worker + b1/b2/A01/B01/Q01/N03 phù hợp rồi full nếu cần; chưa tự tuyên bố N02 hoàn tất. N03 chưa sửa; status/inputs contract đã sẵn cho structured dependency theo yêu cầu điều phối. Không mở UI/new schema để xử lý partial.

Dòng nhật ký đề xuất: “03/11/2026 — N02-b3/Q02 SOURCE-READY: numeric+missing giữ số/D, manual total giữ pending, subtotal/vật tư/intermediate/weight flags chưa đủ; BOQ hai nhãn trung tính; pure regression105 trước nhãn cuối và finalpartial41 đạt, log đầu lỗi kỳ vọng dây buộc giữ riêng; chờ review/API/full, chưa nghiệm thu N02.”
