# D09 — Khoảng trống và điều kiện bàn giao

Ngày 04/11/2026. Kết luận đọc tĩnh; không có lần chạy kiểm thử trong lượt này. Không coi quy tắc thử nghiệm hoặc nhãn CSV là quy tắc được duyệt.

## Khoảng trống ưu tiên

1. **Khóa toàn bộ đầu vào thực thi.** `src/optimat/db/schema20.py` chỉ gộp các kind được khai báo. `src/optimat/config.py`, `drawing/encoding.py`, `rough/structural.py`, `rough/rebar.py`, `drawing/sheets.py`, `rough/secondary.py` vẫn đọc các CSV phụ trợ. `drawing/material_rules.py` sinh quy tắc từ aliases/families và dùng hằng số ưu tiên/độ tin cậy trong mã. Snapshot riêng rule_sets không tái hiện đủ engine.
2. **Thứ tự là dữ liệu nghiệp vụ.** `db/session.py::read_rule_table` đọc DB theo id; CSV giữ thứ tự đầu vào. material_rules sắp priority giảm rồi độ dài pattern giảm; hòa giữ thứ tự đầu vào. room_rules và layer concept dùng khớp đầu tiên; block concept ưu tiên prefix dài. Cần test CSV–DB cho cùng thứ tự, hòa ưu tiên, xung đột, nạp lại và thay đổi id. Chưa chứng minh hai chế độ tương đương.
3. **Typed payload cần kiểm nghiệp vụ.** `db/compat20.py` dùng cấu trúc legacy và constraint; `db/schema20.py` yêu cầu payload object và version dương. Đề xuất schema theo kind: trường bắt buộc, từ chối khóa lạ, enum signal/role/kind, regex biên dịch được, số hữu hạn, kích thước dương khi có, target tồn tại và tương thích cấu kiện. Không tuyên bố các kiểm này đã có đầy đủ. Ca âm: NaN/inf, regex lỗi, target mất, sai role, thiếu khóa, khóa dư và kiểu dữ liệu sai. Phải đọc lại trigger/model hiện hành trước khi triển khai; không thay schema trong gói D09.
4. **Version của một dòng không phải version bundle.** Cần manifest bất biến gồm bundle_id, nguồn đọc thực tế CSV/DB, thứ tự thực thi, rule_sets kind/record_key/version/payload hash, hash toàn bộ CSV phụ trợ, aliases/families, mã engine và cấu hình. Gắn bundle với analysis ngay lúc tính; thay quy tắc tạo bundle mới, không ghi đè snapshot cũ. Kiểm cache khi đổi nguồn hoặc bundle. Đây là đề xuất, chưa khóa bundle nào.
5. **Nguồn và bằng chứng.** material_notes loader không mang toàn bộ cột xác minh CSV vào NoteRule; room_kind trả loại phòng, không tự chứng minh lưu rule_id cho từng hit. Cần trace từ kết quả về rule_id/bundle, văn bản gốc, file revision, handle/bbox khi có. Không dùng số dòng hay nhãn ban_ve_build làm bằng chứng người kiểm đã duyệt.
6. **Cấu trúc CSV.** README liệt kê bảy bản ghi có ô dư sau header. Inventory giữ chúng trong __extra_cells__; cần chủ dữ liệu đối chiếu trước khi typed validation/import. Không tự nối chuỗi hoặc sửa nội dung nguồn.

## Ma trận tình huống cần đối chiếu với VN002/Pioneer

| Chủ đề | Nguồn và ca hiện có | Ca âm/khoảng trống cần kiểm |
|---|---|---|
| Đơn vị | drawing/dxf_reader.py, drawing/ingest.py; tests/test_drawing_io.py::test_declared_inch_but_dimensions_in_mm và test_declared_units_kept_when_dimensions_agree_or_too_few; tests/test_ingest.py::test_headerless_dxf_is_not_meters | đơn vị thiếu/mâu thuẫn, giữ cảnh báo; không coi fallback là xác nhận |
| Tỷ lệ theo hình, DIM | drawing/dimensions.py::view_scale; drawing/plans.py; data/rules/nguong_nhan_dien.csv; tests/test_thresholds.py | nhiều hình khác tỷ lệ, DIM sửa chữ hoặc mâu thuẫn; ca tỷ lệ giữa hình cần đối chiếu thực, chưa chứng minh bao phủ |
| Block lồng | drawing/dxf_reader.py; tests/test_drawing_io.py::test_every_transform_read_in_world_coords có lồng sáu cấp, xoay/lật và MINSERT | vượt giới hạn độ sâu, biến đổi không đều, giữ nguồn theo cấp |
| REGION | drawing/ingest.py có cảnh báo UNSUPPORTED_ENTITY | chưa xác nhận test REGION riêng; không biến hình bỏ qua thành lượng 0 hoặc trạng thái đủ |
| Mã/tầng | drawing/plans.py, drawing/sheets.py, rough/structural.py; tests/test_encoding_plans.py::test_floor_order, test_floor_heights_top_floor_and_near_levels, test_abbreviated_and_detail_titles | mã trùng khác tầng; tên KC/KT khác; tầng chưa xác định giữ pending |
| Bảng lặp | rough/rebar.py; tests/test_rough_rebar.py::test_scoped_whole_table_copy_keeps_one_with_source, test_independent_levels_same_content_both_survive | test_equal_kg_or_changed_shape_not_proof_of_copy, test_partial_table_overlap_does_not_remove_rows, test_ambiguous_or_conflicting_title_never_establishes_scope; cần đối chiếu hồ sơ thực |

Các đường nguồn ngắn trong bảng đều nằm dưới src/optimat/. Test được nhận diện qua đọc mã, không phải báo cáo chạy. Chưa lập ánh xạ từng dòng quy tắc tới fixture dương/âm và nguồn thực đã kiểm. Có thể dùng chung fixture cho nhóm quy tắc nếu chỉ rõ assert nào chứng minh quy tắc nào; không đặt quota số dòng.

## Bàn giao để root quyết định

- Chủ schema/glue kiểm đề xuất typed validation và manifest, giữ đúng 20 bảng; D09 không sửa SQL hoặc DB.
- Chủ dữ liệu xử lý bảy ô dư và bổ sung nguồn/phiên bản còn thiếu; không tự chuyển trạng thái đã kiểm.
- Chủ hồ sơ rà tình huống trên VN002/Pioneer trước; chỉ đề nghị thêm hồ sơ khi xác định được ca còn thiếu.
- Chạy kiểm thử và kiểm parity/freeze chỉ trong nhiệm vụ được giao sau; báo cáo này không mở full suite hoặc khôi phục công việc cũ.
