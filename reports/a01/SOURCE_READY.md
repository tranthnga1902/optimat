# A01 — SOURCE-READY, chưa chạy test

03/11/2026, Codex. Hai file được giao đã viết xong và dừng ghi, chờ điều phối mở khung kiểm:

- src/optimat/rough/materials.py
- tests/test_rough_materials.py

Snapshot byte trước sửa: snapshot/. Hash trước: hash_before.csv. Hash bản giao: SOURCE_READY_HASH.json. Diff đúng lượt: A01_source.patch.

Sửa tối thiểu: _Bill giữ subtotal số thô đã gồm/chưa gồm và cờ có đóng góp khác 0 cần tỷ lệ; result chỉ cộng hao hụt cho subtotal chưa gồm. Không dùng tổng net0 suy đủ tỷ lệ. Giữ quantity, uses, min/max và dấu âm; round cuối. Thiếu/âm/NaN/inf tỷ lệ khi cần: qww=None, complete=False/D. Phần chưa biết giữ incomplete, quantity/qww phần biết nếu tính được; thiếu riêng density không làm thiếu lượng mua.

Đã viết ca test: 20→20,350; đơn cơ sở/0%; mọi phần đã gồm không cần tỷ lệ; thiếu và tỷ lệ không hợp lệ; dòng trừ; triệt tiêu +10−10; None và known_part xuất optimizer; subtotal trước làm tròn; thiếu density; attach_prices không tính est_cost từ lượng mua chưa đủ và đối chứng có tỷ lệ tính 2.035. Test thương phẩm đổi complete=False/D có chủ ý khi thiếu tỷ lệ.

**Chưa chạy test, import kiểm hành vi, full suite hoặc DB**; không tuyên bố các ca đã đạt. Không sửa models/takeoff/BOQ/catalog hoặc file của Q01. Không tự nghiệm thu. Giới hạn by_group/BOQ giữ như A01_CHUAN_BI.md; A01 không tự mở cổng so vật tư C01.

Lệnh đề xuất khi được điều phối release: `.venv/Scripts/python.exe -m pytest tests/test_rough_materials.py tests/test_rough_plaster.py -q -p no:cacheprovider --basetemp=reports/a01/pytest_tmp`, log/exit riêng reports/a01/. Caller attach_prices/optimizer được kiểm qua test trong file materials, không sửa callers.
