# H120, trục và tầng C-2 — trạng thái đối chiếu

## Nguồn bản vẽ

Ảnh PDF kết cấu [trang 19](../data20_00/VN002_C2_A4_PLAN.png) cho thấy C-2 tại trục 4/A; [trang 22](../data20_00/VN002_C2_A4_SECTION.png) cho thấy hai cao độ +3,150/+6,750 m và mặt cắt 220×220; [trang 23](../data20_00/VN002_C2_A4_FLOOR2.png) và [trang 24](../data20_00/VN002_C2_A4_SLAB.png) lần lượt cho thấy mặt bằng sàn tầng 2/tầng 3, ô gần 4/A ở +3,150/+6,750 m, H=120 mm. Các mã tờ và hash PDF đã đối chiếu tại [C2_A4_DOI_CHIEU.md](C2_A4_DOI_CHIEU.md). Đây là kiểm hình PDF, không tự chứng minh reader đã gán được các nguồn này.

Các locator CAD và dữ liệu block do 07 trích được mô tả tại [bàn giao CAD](../data20_07/C2_A4_CAD_SOURCE_HANDOFF.md) và [bàn giao block](../data20_07/C2_A4_BLOCK_AND_MATERIAL_HANDOFF.md): locator là nguồn để truy dấu, không phải kết quả ghép trục/ô sàn đã được reader xác nhận. C2@4/A trong oracle là nhãn báo cáo, không phải ID reader hay database.

## Kết quả API và trạng thái ứng viên

Baseline API thực trước reader mới: response HTTP 200, không có trường `structural_columns`; `column_schedule` rỗng. Response và hash tại [C2_API_HANDOFF.md](C2_API_HANDOFF.md). Do đó baseline **chưa chứng minh có instance, ID, tầng hay H120** trong API.

Tại lần đọc mã này, `SlabSourceCandidate` giữ `thickness_mm`, `level_mm`, `floor_key`, handles, evidence và `region_confirmed=false`. `StructuralColumnInstance` có `top_slab_candidates` riêng với `top_slab_thickness_mm` và `top_slab_source`: ứng viên có provenance không mặc nhiên là sàn đã gán cho cột. Mã reader thu thập ứng viên theo tầng/cao độ khi đủ điều kiện nội bộ, nhưng chưa thấy response candidate của runner 01 để xác minh giá trị thực, ID, mối liên hệ hình học hay trạng thái gán.

Giữ riêng hai trạng thái: **có ứng viên và nguồn**; **đã chứng minh đúng ô sàn đỉnh của instance và gán giá trị**. Chỉ xác nhận trạng thái sau nếu có chứng cứ xác định ô sàn và liên kết đến đúng C-2 4/A/đoạn +3,150→+6,750. Chưa có candidate runtime nên không ghi PASS hay tự điền H120 vào kết quả. Không chạy TestClient, API, full, database hoặc thay schema.
