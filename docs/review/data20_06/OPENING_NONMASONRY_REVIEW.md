# Phân loại lỗ mở gắn tường bê tông — rà read-only

## Quan sát

`drawing/review.py:compute_review` tạo `ids` chỉ từ tường `keep && masonry`; vì vậy lỗ đang giữ gắn tường B `keep=true, masonry=false` bị phân loại như không có tường hợp lệ. `rough/walls.py:wall_works` dùng `all_kept_ids` cho kiểm parent, nên cùng lỗ đó được coi là đã gắn tường và không ảnh hưởng nhóm xây A. Hai đường chưa nhất quán.

Kiểm tra tính toán cô lập trong bộ nhớ, không DB/API/runtime, với tường xây A và tường bê tông B đang giữ, lỗ `door` gắn B:

| Rộng/cao | Review | Rough cho nhóm xây A |
| --- | --- | --- |
| 900/2000 mm | `complete=false`, A nằm `pending_groups`, lý do sai “chưa gắn tường đang giữ” | `XAY=0,99 m³` trước kiểm phương án tường, không có lý do orphan |
| null/null | Tương tự, dù parent B tồn tại | Tương tự, không tính lỗ B vào xây A |

Đây là kết quả hàm trên source canonical đã kiểm hash trùng patch freeze, không phải response runtime hay kiểm chính sách giá/nguồn. Bốn file review/walls/secondary/checks vẫn khớp `patched_sha256` trong [manifest](OPENING_BACKEND_MANIFEST.json).

## Contract đề xuất trước khi cấp hunk

1. Phân biệt **parent tồn tại, đang giữ, masonry**; **parent tồn tại, đang giữ, không masonry**; và **parent thiếu/đã loại**. Chỉ trường hợp cuối là orphan đối với quan hệ gắn tường; không gọi B là “chưa gắn tường”.
2. Lỗ gắn B không tham gia khấu trừ hoặc chặn lượng xây/trát của A chỉ vì khác loại tường. `keep=false` không tham gia tính. Nếu B có công tác bê tông/hoàn thiện riêng, chiều rộng/cao thiếu phải hiện pending trong đúng phạm vi đó; không suy đã trừ hay đã tính đủ công tác bê tông.
3. Bảo toàn ID, parent, keep, w/h và nguồn trong response/snapshot, kể cả lỗ ngoài phạm vi xây; nêu rõ `complete` đang là **đủ phạm vi xây** hay là **toàn bộ công tác**. Có thể bổ sung danh sách ngoài phạm vi xây và lý do, nhưng chưa quyết định hình JSON hay thay đổi API trước khi 01/02 thống nhất consumer/export/optimizer. Không chuyển null thành 0, không âm thầm bỏ lỗ.
4. Regression tối thiểu: parent B không masonry `w/h` đủ và null; A vẫn đủ phạm vi xây, B giữ danh tính/phân loại; parent không tồn tại/đã loại vẫn pending; `keep=false` không chặn; hai mặt bằng tách biệt; chiều cao/rộng không hợp lệ vẫn 422. Kiểm cả `compute_review`, rough và serializer/UI trước release.

Chưa sửa bốn file, chưa đổi runtime/candidate, chưa sửa schema. Đây là đề xuất phân loại, không chứng minh lỗ B đã được bóc bê tông.

## Hunk được 01 cấp và kết quả

Đã sửa riêng `drawing/review.py`: parent đang giữ không masonry được giữ trong `outside_masonry_openings`, kèm cảnh báo không áp dụng khối xây/chưa xét công tác khác; không làm nhóm xây pending. Parent thiếu/đã loại vẫn pending; parent masonry thiếu kích thước vẫn chặn nhóm tương ứng. `complete` ở đây chỉ phản ánh **phạm vi nhóm xây của review**, không xác nhận công tác bê tông có lỗ đã được tính. Input/save vẫn giữ danh tính lỗ; chưa kiểm DB/runtime.

Test `tests/test_incomplete_openings.py`: **22 passed**, gồm B không masonry đủ hoặc thiếu từng kích thước, parent bị loại và mặt bằng độc lập. [Patch tăng dần](OPENING_NONMASONRY.patch) so với base hash `7a2ecd852e5196879bcfb5071da998db21a78217947b4566e6dbba9b21d66fd1`, [manifest hash](OPENING_NONMASONRY_MANIFEST.json); `git apply --check` thành công trên bản sao base. Không sửa ba file width còn lại hoặc runtime candidate.
