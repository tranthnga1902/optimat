> Tài liệu lịch sử mốc final_v3. Bản hiện hành xem ACTIVE.json và review15_v2/HANDOFF.md; source đã thay sau QA15.

# Bàn giao reader CAD thật COT — source freeze chờ01/15 review

Ngày04/11/2026. **Bản hiện hành: final_v3**, xem ACTIVE.json. final, final_v2 và after.json giữ lịch sử, không dùng thay bản cuối. Không tự nghiệm thu end-to-end hoặc promote runtime.

## Kết quả thật và giới hạn

- KC cùng SHA-256 `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`; KT cùng SHA trong reader.json/manifest, chỉ kiểm file/hash, **không chạy lại bóc tường/KT hoặc full project**.
- Baseline trước sửa: read_dxf thật + find_views(BV06) + reader cũ →0instances,66,93giây, viewsBV06 rỗng. baseline.json/baseline_hash.json và snapshot/ giữ nguồn trước sửa.
- Reader sau sửa: production read_column_instances tiêu thụ nativeCADdoc và unit_scale được cùng hàm declared_insunits/_check_units xác định. Không nhập hình học, trục, cao độ hoặc số oracle vào sản phẩm. Adapter tái hiện ở replay_reader.py; không phải full API.
- final_v3: **24 đoạn theo vị trí,24 gross đọc được**, gồm các loại C-1/C-1a/C-2; số này không phải chứng nhận bao phủ toàn bộ công trình. Cad22,92giây,EXIT0;10hash source/data trước–sau không đổi.
- C-2@4/A, T2: source đo3150→6750mm,220×220mm, gross raw **0.17424m³**. Instance ID `5336a248e7a9b93bfe770983`;32 đường dẫn handle, giữ file/hash/tờ/layer. C-2@4/B là instance khác, không lấySL=02 nhân hoặc coi là một vị trí.
- Có ứng viên h=120mm tại+6750/T3 từ nguồn thật, giữ trong top_slab_candidates với region_confirmed=false. Chưa chứng minh vùng sàn tại nút nên **top_slab_thickness_mm/top_slab_source chưa tự điền, net quantity NULL**. Không ép0,168432. known_part gross trong detail không phải khối lượng net để mua.
- C-1 lân cận đã220×300 ở các đoạn đọc được. after.json sơ bộ từng ra190 là lỗi cửa sổ hẹp/đo nửa cạnh, được giữ lịch sử và **không dùng nghiệm thu**; bản cuối bắt buộc haiDIM có endpoints khớp cùng biên kín.

## Cách sửa gốc

1. Mở INSERT/nhánh lồng theo WCS trước khi lọc hình học; dùng origin_of_copy để giữ handlepath. Không bỏ INSERT chỉ vì điểm chèn xa nội dung. Nguyên nhân gói trích đầu thiếu trục cũng được07 xác nhận trong C2_A4_BLOCK_AND_MATERIAL_HANDOFF.md.
2. Nối nhãn cột với đuôi leader, đầu leader với biên closedrectangle; trục phải có nhãn trong vòng tròn và nét trục dài thẳng hàng. Không dùng vị trí chữ trục làm tim.
3. Chi tiết theo mã có ranh tiêu đề hai bên kể cả đặt lệch hàng; không để tiêu đề ngoài ranh ngang cắt mất đỉnh profile. Cao độ có dấu trong cùng cột đứng; pairedcutmarks cần hai số hiệu và hai nét cắt. HaiDIM ngang/đứng phải cùng tỷ lệ và endpoints đo cùng biên kín4LINE/closedpoly.
4. Chỉ ghép thứ tự tầng khi đọc đủ toàn bộ chuỗi đoạn liên tiếp và số đoạn khớp phạm vi ghi trên mặt bằng. Phần đọc thiếu/xung đột giữ missing, không tự gán tầng.
5. Ghi chú h/cao độ đúng tầng được ghi như ứng viên; không biến thành khoản trừ khi chưa nối vùng. Không hardcode mã/hình/hồ sơ/đáp án trong production.

## Contract bổ sung cho06/02

StructuralColumnInstance có source_sha256, missing và top_slab_candidates. Ứng viên giữ thickness_mm,level_mm,floor_key,handles,evidence,region_confirmed=False; đây không phải xác nhận vùng và không thay top_slab_thickness_mm/source. Reader vẫn trả instance thiếu trục/đo khi đã có nhãn+leader+hình, thay vì tạo lượng0. Nhãn chưa nối được leader/hình không được quảng bá thành vị trí chắc chắn.

Không đổi API/UI/DBschema hoặc dữ liệu chuẩn. Hunk phase reader này nằm ở structural_column_instances.py và tests/test_structural_column_instances.py; core structural/takeoff phase trước giữ. reader_changes.patch là diff helper so snapshot baseline, không phải toàn bộ gitdiff/không nhận công việc phiên khác làm của03.

## Kiểm chứng và freeze

- focused.log: **141passed,3deselected,EXIT0**,6,35giây;3ca loại là HTTP. Bao gồm39test file instance/core/geometry, ca âm thiếu trục/leader/dấu cắt/biên kín, nestedoriginxa, detail lân cận đặt lệch, profile đọc thiếu và slab candidate chưa đủ vùng.
- test_hash_before/after:10tệp không đổi. Hashsource helper hiện hành `95fbc000c79d077ecd0e82e0714bc69ffb822915daa0bc8e805bceba122c4a24`; so khớp bản CAD và bản test. Đây không phải fullsuite hoặc khung yên tĩnh toànrepo.
- Source_snapshot giữ3source core và2test đã giao. Bản log/cad_warnings giữ cảnh báo ACAD_PROXY_OBJECT của ezdxf, không suy unsupported đã được đo đầy đủ.
- Không chạy DB/fullsuite/restart/deploy/browser/AI.01 giữ tích hợp/APIruntime,06giữAPI,02giữUI. Giữ20bảng.

## Điểm còn lại đểreview

Kiểm độc lập nhận dạng4/A≠4/B, ranh DIMfullwidth C1/C1a, scope tầng và sourcehandlepath; đối chiếu adapter với reader API sau khi01/06tích hợp. Chưa chứng minh vùng sàn đủ để tự trừ, chưa tính thép/mua vật tư/mác từ các ghi chú. Nếu có chứng cứ region/biên/leader thật thì mở hunk riêng có ca âm khác vùng/hạ cốt; hiện giữnetNULL theo điều phối00. Không cần đổi guard để khớp oracle.
