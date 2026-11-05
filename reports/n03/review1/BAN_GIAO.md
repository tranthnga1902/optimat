# N03 sửa review vòng 1 — CHỜ REVIEW LẠI

03/11/2026, Codex. Hai lỗi root tái hiện đã được sửa trong secondary.py và test_rough_secondary.py; **không tự nghiệm thu**, chưa full suite/API/CAD thật/DB/restart. Snapshot trước vòng sửa ở snapshot/, hash_before.csv. N03_review1.patch là diff riêng vòng này. N03.patch và FINAL_HASH.json ở thư mục cha đã cập nhật bản cuối; hash cũ giữ trong previous_FINAL_HASH.json.

## 1. Giao tiết diện XY, không chỉ giao trục

normalize_ties tạo hình chữ nhật XY của đoạn ngang/dọc bằng b thật, đầu đoạn phẳng. Kiểm diện tích giao dương rồi kiểm khoảng cao độ đứng. Hai trục song song lệch nhưng tiết diện giao, hoặc hai tiết diện giao gần đầu đoạn khi trục chưa cắt nhau: đánh missing cả nhóm BT/CP liên quan, giữ raw/IDs/evidence. Không tự tính hợp 3D hoặc cộng như đủ.

Ca root: L4 m, b220/d150, y0 và y100, cùng z1000 → cả hai nhóm missing/D, BT/CP None; không còn tổng đủ0,264. Tổng hợp hình học0,192 m³ root nêu chỉ là căn cứ chứng minh0,264 sai, **bản sửa không tự xuất0,192 như đã hỗ trợ hợp lệch trục**.

Các tiết diện rời y400, chỉ chạm biên y220 hoặc khoảng z rời không bị nhập/hạ thiếu nhầm bởi cổng này. Bổ sung test giao gần đầu đoạn: trục đứng x4050 gần đầu trục ngang x4000 nhưng b220 làm tiết diện còn giao; nhóm pending thay vì giả tổng đủ.

## 2. Trừ xây đúng bề rộng giao

Khi đã chứng minh cùng trục, không có cổng thiếu khác, thể tích trừ = lap × d_giằng × min(b_giằng, dày_tường). Không sửa lượng BT để ép khớp XAY.

Probe SYNTHETIC (`probe.json`, Python EXIT0), tường220/dài10/cao xây3 m, giằng dài4/cao150:

| b giằng mm | BT m³ | Net XAY m³ | CP m² |
|---|---:|---:|---|
| 100 | 0,060 | 6,540 | 1,200, C |
| 220 | 0,132 | 6,468 | 1,200, C |
| 300 | 0,180 | 6,468 | None/D: đáy không được tường đỡ đầy, chưa xác định CP đáy |

Giữ các gates cao độ/tầng/cửa/cột/ranh đứng trước đó. Không nhân toàn bộ dày220 khi giằng chỉ rộng100. Vật tư gạch nhận đúng net mới; test b100/220/300 kiểm lượng, trạng thái, vật tư và BOQ CP rộng hơn tường.

## Điểm nối nội bộ cốp pha

_TieGroup có thêm `formwork_missing: tuple[str, ...]` nội bộ; bỏ frozen để deduct_ties ghi lý do đáy chưa được đỡ đầy vào chính kết quả chuẩn hóa dùng chung trước khi linear_works chạy. Không đổi schema/API/model sản phẩm hoặc caller takeoff. linear_works chỉ hạ CP cho lý do riêng này, không làm mất lượng BT đã biết hoặc giả CP đáy=0. Bản ghi raw không bị sửa.

**takeoff.py không thay đổi trong vòng sửa**, đã kiểm hash bằng bản FINAL_HASH cũ. Các vùng N02/Q02 giữ nguyên. Không sửa file ngoài hai source/test được giao; báo cáo/snapshot/log nằm riêng reports/n03/review1/.

## Kiểm đã chạy

Môi trường: OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8; bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPTIMAT_CATALOG_OVERLAY. Catalog.from_csv(None), fixture SYNTHETIC, không TestClient/HTTP/CAD thật/DB.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_rough_secondary.py -k review -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/test_rough_secondary.py tests/test_rough_status.py tests/test_rough_partial.py tests/test_rough_materials.py -q -p no:cacheprovider
```

- two_issues.log: **8 passed, 51 deselected, 8,62 s, EXIT=0**.
- focused.log: **151 passed, 25,18 s, EXIT=0**, gồm các ca N03 cũ và xuyên status/tổng/vật tư/BOQ/optimizer.
- Probe riêng lưu số b100/220/300 và missing của lệch100/rời400 trong probe.json; không chỉnh dữ liệu thật.

Giới hạn còn nguyên: chưa hợp tiết diện lệch trục/giao3D, chưa xác định vị trí lỗ/cột, chưa tự gắn tầng KC. Giữ các ca này missing/D; đây là báo thiếu có căn cứ, không nghiệm thu đầy đủ các cấu hình đó. Giữ source/test ở FINAL_HASH mới, chờ root review trước cấp full.
