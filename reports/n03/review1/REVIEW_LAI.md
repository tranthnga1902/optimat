# N03 vòng 1 — CẦN SỬA, chưa mở full suite

Codex review lại theo yêu cầu trực tiếp của chủ đồ án ngày 03/11/2026. Đọc source, test và log focused151; kiểm SHA256 cả secondary.py/takeoff.py/test_rough_secondary.py đều trùng FINAL_HASH của vòng1. Không sửa source/test trong lượt review này.

Hai ca review trước đã có sửa đúng hướng: kiểm giao tiết diện XY và trừ xây theo min(b_giằng,dày_tường). Tuy nhiên còn lỗi chặn dưới đây; 151 test đạt chưa chứng minh ca kết hợp.

## [P1] Cổng thiếu giao cửa/cột làm mất cảnh báo cốp pha đáy

Vùng: `secondary.deduct_ties`, đoạn `if not reasons` chứa cả phép tính lượng XAY và kiểm `first.b_mm / 1000 > thick` để ghi group.formwork_missing. `linear_works` dựa vào formwork_missing này để chặn lượng CP.

Tái hiện độc lập với Catalog.from_csv(None), fixture SYNTHETIC `_tie(b_mm=300)` trên tường220, dài giằng4 m, cao150, z1000:

| Dữ liệu | BT m³ | CP m² | Trạng thái CP | missing CP |
|---|---:|---|---|---|
| Không opening | 0,180 | None | D | đáy không được tường đỡ đầy |
| Thêm ReviewOpening(id='O1', wall='W1', w=1000, h=2000) | 0,180 | 1,200 | C | rỗng |

Probe Python mã thoát0, OPTIMAT_NO_DOTENV=1; bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPTIMAT_CATALOG_OVERLAY. Không DB/API/CAD thật. Hash kiểm sau probe vẫn trùng bản bàn giao. Không có căn cứ để thêm opening làm phần đáy chưa xác định trở thành đủ.

Sửa tối thiểu đề nghị: tách kiểm điều kiện đỡ đáy CP khỏi điều kiện được phép tính net XAY. Khi b/độ dày tường và quan hệ trục đủ căn cứ đã cho thấy đáy không được đỡ đầy thì phải giữ missing CP ngay cả khi XAY bị chặn vì cửa/cột/ranh đứng. Không bỏ các gate XAY và không hạ BT đã biết theo lỗi riêng CP. Nếu chưa biết điều kiện đỡ, không mặc định đáy đã được đỡ đầy.

Thêm test kết hợp b300 + opening; nên kiểm thêm b300 + cột đã trừ hoặc metadata giao chưa cung cấp. Giữ các ca b100/b220 và BT/XAY đúng của vòng1. Sau sửa chốt hash và focused lại trước review/full.

## Trạng thái điều phối

Đã báo chat điều phối giữ chưa đạt, không mở full suite. Yêu cầu chủ đồ án là chỉ chạy full nếu review đạt nên điều kiện hiện chưa thỏa. Chưa chạy lại151/full, chưa sửa ledger chung do điều phối giữ quyền ghi; tài liệu này là bằng chứng tiến độ của lượt review. Chưa nghiệm thu N03.
