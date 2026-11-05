# N03 — Chờ điều phối review kỹ thuật

03/11/2026 — Codex. Đã triển khai theo thiết kế BA duyệt; **không tự nghiệm thu**. Không full suite/API/CAD thật/DB, không restart worker.

## Phạm vi thực tế

1. `src/optimat/rough/secondary.py`: LinearMember có z_bottom_mm optional hữu hạn và z_evidence optional; _TieGroup/normalize_ties nội bộ; linear_works và deduct_ties dùng cùng kết quả hợp đủ căn cứ. Giữ raw members, IDs và evidence; z khai báo ở PlanInput cap C qua status/inputs có cấu trúc. Sê nô giữ đường tính cũ.
2. `src/optimat/rough/takeoff.py`: chỉ thêm import normalize_ties, tạo một tie_groups trong vòng PlanInput rồi truyền chung vào linear/deduct cùng wall_height_mm/openings/overlaps. req.members dùng context=False tường minh. Diff chỉ ba vùng này, giữ các sửa N02/Q02 khác.
3. `tests/test_rough_secondary.py`: các fixture toán xác nhận cùng tầng/cao độ khai báo z/context; bổ sung ca legacy riêng, ca khác cao độ, chồng chưa giải được, gates và kiểm xuyên luồng.

Snapshot byte trước sửa: snapshot/, hash_before.csv. SOURCE_READY_HASH.json giữ mốc trước test; sau đó chỉ bổ sung test và bỏ đúng decorator xfail đã chứng minh, không thay hai file source. **FINAL_HASH.json là hash bản bàn giao cuối**. N03.patch là diff so snapshot, không so toàn bộ cây đang có thay đổi của phiên khác.

## Kết quả đúng và phần chưa biết

- Hai đoạn 4 m trùng cùng trục/z/b/d/source/context đã xác nhận → dài hợp4 m, BT0,132 m³, CP1,200 m², XAY6,468 m³ từ raw6,600. Cùng kết quả chuẩn hóa cho ba phép tính, không cộng trùng.
- Chồng một phần 0–4 và 2–6 m → BT0,198, CP1,800, XAY6,402; đảo đầu mút/thứ tự không thay kết quả. Bản ghi lặp thêm không tăng lượng; 8 IDs vẫn đủ evidence dù nhãn chỉ giữ5.
- Hai cao độ1.000/2.000 mm → giữ hai giằng BT0,264, CP2,400, XAY6,336. Khác tầng không hợp toàn cục.
- Thiếu context/z, khác tiết diện, giao đứng một phần, khác nguồn chưa căn chỉnh, trục xiên/không hợp lệ → nhóm giằng thiếu/D, quantity=None, raw BT/tiết diện/XY/z giữ trong evidence. Cao độ z=None không thành0; NaN/inf bị validation chặn.
- deduct_ties xét ranh [0, cao xây thực] theo wall_params. Vượt ranh/chưa có ranh không clip đoán hoặc clamp0. Nếu một tường có lỗ/lanh tô hoặc đã trừ cột mà thiếu vị trí giao: ghi “cần kiểm”, không khẳng định có giao thật; nhóm XAY chứa tường đó net=None/D, raw trước trừ giữ evidence. Nhóm tường khác không bị hạ theo toàn mặt bằng.
- None của openings/overlaps là chưa cung cấp; []/{} là đã biết rỗng. Dung sai150 mm chỉ định vị ứng viên cần kiểm, không merge trục gần nhau. Không dùng tên plan làm bằng chứng; req.members chưa gắn tầng vẫn pendingK03 và không trừ kiến trúc.
- Hợp đồng partial hiện có không thêm known_part vào WorkItem: net chưa biết dùng None, số trước trừ giữ evidence/formula. Vật tư/tổng/status đi theo hợp đồng b3, BOQ hiển thị thiếu và optimizer đưa dòng D vào missing; không phân bổ ngược tổng XAY cho từng tường.

## Lệnh và log

Mỗi tiến trình test đặt OPTIMAT_NO_DOTENV=1, PYTHONIOENCODING=utf-8, bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL/OPTIMAT_CATALOG_OVERLAY. Không dùng DB hay CAD thật; test read_secondary dùng Drawing SYNTHETIC dựng trong bộ nhớ. Không TestClient/HTTP.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_rough_secondary.py::test_overlapping_ties_deduct_masonry_once --runxfail -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/test_rough_secondary.py -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/test_rough_secondary.py tests/test_rough_status.py tests/test_rough_partial.py tests/test_rough_materials.py -q -p no:cacheprovider
```

1. `xfail_proof.log`: **1 passed, 8,17 s, EXIT=0** khi decorator vẫn còn; --runxfail chỉ đúng node N03. Fixture đã khai báo z=1.000 theo giả định cùng cao độ được BA duyệt, giữ assert XAY và thêm BT/CP; không xóa assert để né lỗi.
2. Sau bằng chứng mới bỏ đúng decorator đó. `focused.log`: **48 passed, 13,78 s, EXIT=0**.
3. Bổ sung kiểm ca đủ đi qua vật tư/BOQ/optimizer, 8 IDs và tách tầng. `focused_final.log`: **143 passed, 23,61 s, EXIT=0** trên secondary/status/partial/materials. Đây là focused, không phải full suite.

Các thay đổi kỳ vọng fixture có chủ ý: source structural không còn A khi dùng z do người dùng khai báo trong PlanInput, nên assert C kèm lý do cao độ; ca giằng thiếu d/z trước đây giữ net xây như đủ nay net=None/missing và giữ raw. Legacy thiếu z/context có test riêng. Không đổi dữ liệu thật để bỏ xfail.

## Giới hạn để reviewer đánh giá

- Chưa engine3D, chưa xác định vị trí cửa/bậu hoặc khoảng cột; vì vậy gate bảo thủ có thể làm nhiều nhóm pending hơn. Nhóm XAY gộp có một tường cần kiểm làm cả net nhóm chưa xác định; chưa chia số ngược cho tường.
- Chưa mở đường nhập z trên UI, chưa gắn tầng/căn chỉnh giằng KC tự động; K01–K03 còn nguyên. Người gọi API cũ vẫn deserialize nhưng kết quả thiếu cơ sở không còn được trình bày như lượng đầy đủ.
- Chuẩn hóa so trục/z/b/d chính xác, không thêm tolerance; giữ nguồn khác pending khi cùng hình chiếu chưa chứng minh quan hệ. Chiều cao xây chưa có cao dầm vẫn theo cơ sở/cảnh báo của wall_works hiện có, không tự bịa chiều cao.
- Chưa chạy suite/API/CAD thật/DB hoặc parity worker. Giữ source/test ổn định ở FINAL_HASH để điều phối review và cấp hồi quy sau.

Dòng nhật ký đề xuất: “03/11/2026 — N03 sửa hợp giằng có cao độ/ngữ cảnh và gates trừ xây, giữ raw/partial/C nguồn z; chứng minh xfail riêng rồi bỏ đúng decorator, focused143 đạt EXIT0. Chờ review độc lập/full được cấp; chưa CAD/API/DB, chưa K01–K03.”
