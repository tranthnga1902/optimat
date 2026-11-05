# Cột vật lý KC — bàn giao core chờ review

Ngày 04/11/2026. Đã đóng băng source sau lượt focused cuối theo điều phối 01. Chỉ đạt trọng tâm kỹ thuật, **VN002 reader end-to-end chưa đạt**.

## Thay đổi của 03

- `src/optimat/rough/structural_column_instances.py` mới: DTO StructuralColumnInstance, phép tính Decimal gross/khoản trừ/net, nguồn file/tờ/layer/handle và thiếu dữ liệu; chọn đúng cột KT có mapping. Mỗi instance sinh COT riêng. Cốp pha chưa chứng minh giao dầm/mặt đỡ giữ NULL và missing.
- `src/optimat/rough/structural.py`: element_of nhận gạch nối giữa prefix và số, không phá MC1-1; StructuralTakeoff giữ structural_columns; ColumnSpan có floor_key tùy chọn. read_structural gọi reader instance.
- `src/optimat/rough/takeoff.py`: nhận/truyền structural_columns; không còn có bất kỳ bảng cột thì bỏ toàn bộ cột KT. Mapping chỉ loại đúng plan+column ID; cột chưa đối chiếu có thể chồng nguồn giữ pending/NULL, không cộng đôi. Bảng có scope tầng không làm mất cột ngoài tầng. Bảng aggregate chưa map với instances giữ pending; schedule-only giữ công thức cũ riêng. Chặn ID lặp, mapping không tồn tại, cùng vị trí chồng đoạn cao độ; đoạn liền kề được giữ riêng.
- `tests/test_structural_column_instances.py` mới; `tests/test_rough_structural.py` sửa đúng ca global-drop-all thành giữ local pending. Không sửa columns.py/models.py/registry.py/plans.py hoặc API/UI/schema/SQL.

Git diff toàn tệp đang gồm cả công việc trước của các phiên khác, không coi toàn bộ diff với HEAD là thay đổi của 03. Hash cuối xác định chính xác bản đã kiểm, không phục hồi hoặc ghi đè công việc người khác.

## Contract cho caller

`RoughRequest.structural_columns: list[StructuralColumnInstance]`:

- instance_id, code; grid_x/grid_y; floor_key; z_from_mm/z_to_mm; b_mm/h_mm.
- deduct_top_slab=True mặc định; top_slab_thickness_mm chỉ nhận kèm top_slab_source. Không lấy slab chung để điền phần thiếu. deduct_top_slab=False nghĩa tính chiều cao đủ, phải được caller chọn theo phương pháp đo.
- file, sheet, layers[], handles[], evidence[]. Không có file/nguồn/vị trí hoặc số đo cần thiết thì lượng COT NULL.
- matched_plan/matched_column_id/mapping_evidence phải đi cùng nhau và tham chiếu tồn tại; không tự nối theo mã loại, kích thước giống nhau hoặc tọa độ hai hệ bản vẽ.

quantity_detail giữ gross và khoản trừ có dấu bằng số thập phân gốc, nguồn và missing; legacy quantity vẫn round3 theo engine. Fixture kỹ thuật cho gross 0,174240 / trừ 0,005808 / net 0,168432 chỉ chứng minh phép tính khi đã có input, không chứng minh reader đã lấy được từ CAD. Cùng mã khác trục tách riêng. Không đặt hàm lượng thép hoặc mác bê tông mặc định.

## Giới hạn reader và dữ liệu thực

Reader mới chỉ dùng thuộc tính block có tên/đơn vị rõ (COLUMN_CODE, GRID_X, GRID_Y, Z_FROM_MM, Z_TO_MM, WIDTH_MM, DEPTH_MM, TOP_SLAB_THICKNESS_MM). Nhãn COLUMN trên BV06 chưa nối được nguồn giữ dạng pending; không coi nhãn bảng thống kê là instance đủ. Chưa có thuật toán tự nối các hình rời theo trục/leader/section/cao độ. Chưa xác nhận block attributes này tồn tại trong VN002. Drawing hiện không giữ handle trên TextItem/BlockRef; reader chưa khôi phục handle cho nhãn bị mất thông tin, không tự bịa handle.

Đã đọc artifact nguồn `docs/review/data20_07/C2_A4_CAD_SOURCE.json`, không đọc oracle làm đầu vào production: window column_plan_p19 có 76 entity (32 DIMENSION, 27 TEXT, 8 LINE, 8 LEADER, 1 LWPOLYLINE). Không có INSERT hoặc nhãn trục 4/A/B; 8 LINE thuộc bảng LS-THAY. Có hai leader C-2 nhưng chưa đủ để xác định 4/A và 4/B. Đã báo 01 cần bổ sung nguồn trục/đối tượng/hệ biến đổi. Bbox window thủ công chưa là view bbox được engine nhận. Chưa tự nối section 2–2 hoặc slab region chỉ từ việc cùng cửa sổ.

## Kiểm chứng cuối và freeze

`focused_final.log`: **129 passed, 3 deselected, EXIT=0**, 5,49 giây. Ba ca bị loại là HTTP. Tắt dotenv, bỏ DATABASE_URL và OPTIMAT_TEST_DATABASE_URL trong tiến trình con; không dùng DB. Không chạy CAD thật/full suite/restart/browser/AI trong lượt kiểm cuối.

`final_hash_before.json` / `final_hash_after.json`: 8 tệp source/test không thay đổi khi chạy; `final_result.json` ghi lệnh và thời điểm. Đây không phải hash toàn repo hoặc bằng chứng khung yên tĩnh toàn dự án. Một lượt mở rộng trước đã bị dừng do chọn cả test HTTP; không dùng lượt đó làm kết quả đạt. Lượt 129 đầu được giữ riêng, hash cuối mới là bản review hiện tại.

01 giữ cập nhật tiến độ chung và quyết định review/tích hợp. Chưa cấp full suite; chưa nghiệm thu đáp án, UI hoặc tính tự động của VN002. Giữ đúng 20 bảng vật lý, không migration/DB writes.
