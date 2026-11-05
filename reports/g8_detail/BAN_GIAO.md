# G8 — gói hợp đồng và producer staging, chưa canonical

03 đã chuẩn bị bốn tệp trong SOURCE_READY_HASH.json/FINAL_HASH.json: CONTRACT_DE_XUAT.md, staging/quantity_details_proposed.py, staging/M1_AF11110_REFERENCE.json và staging/test_detail_contract.py. Bốn tệp đang HOLD để14 review, không sửa tiếp khi chưa mở lại.

Đã khép validation theo review01: conversion hữu hạn/dương/có unit+nguồn; factor typed giá trị/đơn vị/ý nghĩa/nguồn; DTO tự kiểm sum signed contribution, unit, known/total/complete/scope/delta khi khởi tạo trực tiếp; sum và delta cùng context đủ chữ số, không mất precision sau28 chữ số. WorkDimensions được tái dùng, count/repetition không nhân lại. Fixture M1 riêng9dòng=3.2515m³ và4tích vật tư có nguồn, không catalog/đáp án hồ sơ khác.

Kiểm staging thuần Python trong sandbox, không API/HTTP/CAD/DB:
- attempt1:33passedEXIT0,226canonical hash không đổi; collector chưa khóa staging nên chưa dùng lượt này đơn độc làm bằng chứng source staging bất biến.
- **attempt2_locked:33passedEXIT0**, pytest0,74giây, collector2,79giây; **231 tệp trước/sau không đổi**:226canonical và5tệp vùng G8 (4tệpmanifest cùng exporter_preview_09.py do09 tạo riêng trước snapshot). Exact4manifest đã đối chiếu với hash trước/sau/current đều khớp. Không nhận exporter09 là code03 sở hữu hoặc đã được33test này kiểm.

Bằng chứng: attempt2_locked/focused.log,result.json,process.json,focused_hash_before.json,focused_hash_after.json; FINAL_HASH.json; manifest vàcontract. Nguồn O01 exact4FINALhash vẫn nguyên.

Phạm vi thực: helper lót nhận q trước round3 và hợp đồng DTO; chưa nối emitter, chưa có G8 API/Excel sản phẩm, chưa bao phủ toàn rough. Đã gửi contract cho01/02/09. Chưa tái chạy HTTP outside đã bị automatic approval review từ chối; không full hoặc QA thật.

Bố trí đề xuất tránh vòng import khi01release: DTO đặt models.py sau WorkDimensions/trướcWorkItem, privateDecimal/invariant helper tại models.py; builder/producer helper quantity_details.py chỉ import models, models không import ngược. Không tách WorkDimensions ra module khác hoặc mở rộng refactor. Chờ14 review và01 mở từng hunk, chưa sửa canonical/takeoff/O01.

14 đã chốt review4/4hash, chưa có blocker số học trong phạm vi staging. Bố trí chống circular import được14 đồng ý. Ghi chú chưa chặn: canonical cần reject missing reason chỉ có khoảng trắng; chưa sửa4tệp staging đang HOLD để giữ hash review.
