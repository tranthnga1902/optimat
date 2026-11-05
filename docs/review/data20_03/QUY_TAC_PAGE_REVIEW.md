# Review tĩnh /quy-tac bản đầu của17

Ngày 04/11/2026. Chỉ đọc source/page và ghi báo cáo; không sửa file17/core freeze, không test/build/DB/runtime/browser. Bản page được đọc: SHA-256 `f44de1ad4d0347ad7552dd42bcd246d1f57354fd60d074a89252b64178d1211e`. Nếu17 sửa tiếp, cần đối chiếu bản mới; số dòng dưới áp dụng bản này.

## 1. [P1] Điều kiện đủ của nhóm đang được mô tả thiếu

`frontend/src/app/(admin)/quy-tac/page.tsx:18`: “Đủ khi các phần đóng góp đều có lượng”. Consumer `src/optimat/rough/quantity_details.py::summarize` còn yêu cầu scope_complete và mọi contribution không missing. `quantity_summary.py::_quantity_complete` yêu cầu detail có complete/total_raw; `finalize_quantity_details` còn hạ complete khi parent D hoặc missing.

Ví dụ: tất cả contribution có raw nhưng scope_complete=False thì known_part có số, total_raw vẫn NULL. Người dùng không được coi có số ở mọi dòng là đã đủ phạm vi.

Đề nghị17: ghi “Chỉ đủ khi phạm vi đã xác định, mọi đóng góp có lượng và không còn thiếu; có số chưa đồng nghĩa tổng đã đủ.” Không đổi công thức engine.

## 2. [P1] Đang mô tả hành vi mới như đã được runtime tự áp dụng

`page.tsx:10` nói cột mặt bằng/bảng tổng chưa đối chiếu được giữ nguồn và đánh dấu thiếu; `page.tsx:32` nói bộ tính tự áp dụng khi đủ đầu vào. Hành vi pending/selective replacement mới có trong source freeze của03, chưa tích hợp runtime theo01. Chưa có kiểm chứng process hiện chạy dùng hash mới; reader VN002 chưa đạt end-to-end.

Ví dụ: bản core cũ có column_schedule thì bỏ toàn bộ column_works, khác câu giữ cột pending. Không thể dùng trang lời giải thích để chứng minh runtime đã sửa.

Đề nghị17: tách mô tả đang có trong source khỏi trạng thái triển khai đã được01 xác nhận. Với mục cột mới, ghi chưa tích hợp/chưa xác minh runtime và không tuyên bố tự nhận C-2 theo trục từ CAD. Khi tích hợp xong mới đổi trạng thái.

## 3. [P2] Mục COT bỏ sót nhánh instance và khoản trừ có nguồn

`page.tsx:13` chỉ nêu bảng cao độ/mặt bằng. Source mới còn `structural_column_instances.py::instance_column_works`: gross theo hai cao độ, trừ slab đỉnh khi deduct_top_slab=True và có nguồn riêng; thiếu nguồn net NULL, không dùng slab chung. Cùng code khác grid là hai instance.

Ví dụ fixture đã có input: 220×220, đoạn3600mm cho gross0,174240m³; nguồn slab120 cho khoản trừ0,005808 và net0,168432. Đây không phải bằng chứng reader đã đo được VN002. Nếu áp câu n×tiết diện×cao độ đủ cho nhánh instance, người dùng bỏ mất khoản trừ và nhầm gross với net.

Đề nghị17: chia ba nhánh, gắn trạng thái mới/chưa tích hợp cho instance, ghi gross/net và nguồn slab riêng. Nêu legacy mặt bằng thiếu slab lấy cả H và cảnh báo; schedule chưa tự trừ slab, không coi hai nhánh tương đương.

## 4. [P2] Cốp pha đáy sàn chưa bảo đảm đúng tầng/ô sàn

`page.tsx:15` nói khấu trừ diện tích tiếp xúc dầm/cột, nhưng `takeoff.py::_slab_form_deduction` còn shortcut gán vào plan dầm/cột, chưa dò sàn tầng trên. Công thức hiện trừ tổng mặt bằng dầm + đỉnh cột của plan, chưa phải phép kiểm giao đúng ô sàn theo cao độ.

Ví dụ: cột/dầm của planT2 nhưng sàn đỉnh thuộc scope khác, không được hiểu khoản trừ đã tự chuyển đúng tầng trên.

Đề nghị17: giữ công thức tham khảo và ghi hạn chế mapping tầng/ô; yêu cầu kiểm nơi áp khoản trừ. Không mô tả là đã tự đối chiếu mọi giao.

## 5. [P2] Mục SAN thiếu khoản trừ ô trống và trường hợp chỉ biết gross

`page.tsx:15`: chỉ nói diện tích×dày. `areas.py::area_works` dùng outline−void; khi void chưa nhập, legacy vẫn có thể giữ lượng theo diện tích gộp với cảnh báo, còn detail có khoản trừ chưa biết và total chưa đủ.

Ví dụ: outline50m², slab100mm, void5m² thì BT4,5m³; thiếu void không được xem số gross5m³ là net đã xác nhận.

Đề nghị17: bổ sung diện tích net=diện tích gộp−ô trống; phân biệt void=0 đã xác nhận với chưa nhập. Không ghi engine luôn tự tìm đủ lỗ thang.

## 6. [P2] Thay sàn bằng mái cần mapping được khai báo

`page.tsx:15`: mô tả “khi có cấu kiện mái, kiểm tra phần sàn trùng mái” dễ bị hiểu engine tự tìm trùng hình học. `secondary.py::drop_slab_under_roof` chỉ bỏ SAN và CP/SAN cho plan được chỉ rõ trong roof.replaces_slab_of, với roof.kind=be_tong.

Ví dụ: có mái nhưng replaces_slab_of trống thì không tự bỏ sàn chỉ vì hình học có thể trùng.

Đề nghị17: ghi điều kiện chọn rõ mặt bằng sàn được mái thay thế; đây là mapping đầu vào, chưa phải nhận dạng giao mái–sàn tự động.

## Phần chưa phát hiện sai lệch rõ trong lượt đọc

Công thức thép theo bảng tổng thanh×chiều dài cắt×kg/m đúng với `rough/rebar.py::read_table`; số kg ghi trong bảng chỉ đối chiếu. Câu layer khớp đầu tiên phù hợp consumer, nhưng không áp thứ tự đó cho block (prefix dài trước). Nhãn hàm trên trang là chỉ dẫn tra cứu, chưa phải liên kết đến dòng công tác; link /phan-tho chỉ mở bước chung.

Inventory25quy tắc kèm consumer/hash ở `QUY_TAC_PHAN_THO_INVENTORY.csv`; ID trong đó là ID báo cáo, không phải cấu hình được engine đọc. Phạm vi nghiệp vụ vẫn chỉ nhà ở riêng lẻ xây mới≤5tầng, giữ20bảng. Không có quyền biến chỉnh sửa mô tả trên trang thành thay đổi công thức khi chưa có consumer thực.
