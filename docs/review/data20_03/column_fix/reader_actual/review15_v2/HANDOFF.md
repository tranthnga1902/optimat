# Phản hồi QA15 — reader vòng sửa1

Ngày04/11/2026. **Source freeze chờQA15 review lại**, không tự đóng finding. Bản active theo ACTIVE.json là review15_v2, thay final_v3/review15_v1. Hunk sửa đúng helper và test instance, không runtime/DB/fullsuite. Hashhelper `6bb3c47a1a2275c05e264e91afc40968fa01670371c8a237df65ca5aed61d6e9`.

| Finding | Thay đổi | Bằng chứng test |
|---|---|---|
| Globalnearest planhead chưa guard | _plan_heads_at_axes dùng footprint giới hạn hai nét trục, mở margin theo chiều cao chữ; chỉ đúng1head đủ điều kiện mới gắn. Có2head/tie/cùngscope/kháctầng hoặc khônghead thì giữ grid/source và pending, không lấy phần tử gần nhất | test_two_eligible_plan_heads_stay_pending_even_if_one_is_closer (3ca); test_global_nearby_heading_outside_axis_footprint_cannot_supply_floor |
| Span dict giữ nguồn cuối | _merge_column_spans gom toàn bộ refs, không ghi đè provenance. Cùng đoạn khác tiết diện hoặc expected_count thì pending, vẫn giữ cả hai nguồn trong payload | test_duplicate_span_keeps_all_sources_and_conflicting_profile_counts_do_not_merge; test_conflicting_duplicate_span_preserves_both_detail_sources |
| DIM chọnmax che cặp đúng/mơ hồ | Thử mọi cặp ngang/đứng cùng tỷ lệ có biên kín trongcell; một physicalboundary/value duy nhất mới áp. Nhiều biên hợp lệ thì pending và giữ refs; DIMlớn khôngbiên không che cặp đúng. DuplicateDIMcùngbiên gom nguồn. NativeDIMchéo bị loại giống quy tắc linearDIM | test_larger_dimension_without_boundary_does_not_hide_valid_pair; test_two_valid_dimension_boundaries_stay_pending; test_duplicate_dimensions_same_boundary_keep_provenance; test_native_diagonal_dimension_is_not_a_horizontal_section_measurement |

Footprint từ hệ trục là cửa sổ eligibility hình học của reader, không phải polygon khung tờ đã được kiểm độc lập. Không coi một gói kết quả đủ chứng minh mọi bố cục CAD; nhiều head/biên/nguồn không duy nhất vẫn pending. Không thay guard để giữ số oracle.

## Kết quả và nguồn

- CAD thật qua productionreader adapter:24đoạn/24grossknown,EXIT0,34.18giây. Cùng cặp nguồn trong manifest; KT chỉ hash, không chạy lại bóc tường/fullproject hoặc API.
- C-2@4/A3150→6750,220×220,grossraw **0.17424m³**;4/B vẫn riêng. Nguồn/H120candidate có scope tầng/cao độ nhưng chưa kiểm vùng, net vẫn NULL. Khônggán mã/mác/thép hoặc lượng mua.
- focused.log: **151passed,3deselected,EXIT0**,19,60giây;49test fileinstance gồm ca âm mới. Ba ca loại là HTTP. KhôngDB, khôngdotenv.
- hash_before/after củaCAD:10nguồn/data khôngđổi. test_hash_before/after:10source/test khôngđổi. Ba source core hiện tại khớp cảreceiptCAD vàreceipt test. Đây khôngphải khungyên tĩnh toànrepo hoặc fullsuite.
- source_snapshot giữ bản đãkiểm; review15_changes.patch so đúngsnapshot final_v3 cho helper/test, không gomgitdiff côngviệc khác. target_trace.json vàreader.json giữserializedpayload thật.

Bản review15_v1 là lượt trước guard nativeDIMchéo; không dùng làm bảnactive. Giữ lịch sử final_v3/baseline/sơbộ190, không nghiệmthu bằng file cũ. Root01 giữ quyền tíchhợp;03 chờ QA15 và giữfreeze. UI/API khôngđược03kiểm lại;net/vùngsàn chưanghiệmthu.
