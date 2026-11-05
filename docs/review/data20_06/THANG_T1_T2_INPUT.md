# Cầu thang VN002 tầng 1→2 — kiểm tra nguồn và luồng đầu vào

## Chứng cứ đã đọc

Ảnh trích [mặt bằng cầu thang](../data20_00/VN002_THANG_T1_T2_MAT_BANG.png) và [mặt bằng thép](../data20_00/VN002_THANG_T1_T2_MAT_BANG_THEP.png) trong PDF KC trang 37 thể hiện thang tầng 1 lên tầng 2, trục 2–3/A–B; [khung tên](../data20_00/VN002_THANG_T1_T2_TO.png) ghi KC-06-01. Vùng hatch cạnh tầng 2 có ký hiệu `+3.150`, `H=150MM`. Ký hiệu này là thông tin tại vùng hatch được chỉ trên bản vẽ; chỉ từ ảnh này **chưa chứng minh** 150 mm là chiều dày bản nghiêng của tất cả các vế thang. Không thay bằng H=120 của ô sàn C-2 hay tự điền 150 vào tham số chung.

**Bổ sung:** đã xem [chi tiết bản thang](../data20_07/STAIR_WAIST_DETAIL.png) cùng tờ KC-06-01: đường kích thước vuông góc bản nghiêng ghi **120 mm** và chú thích “bậc thang xây gạch”. Kết luận này bổ sung chứng cứ chi tiết vế thang mà các ảnh mặt bằng trước không thể hiện; chưa tự chứng minh ánh xạ reader tới instance/từng vế. H=150 vẫn là chú thích vùng chiếu tới tại +3.150, không dùng cho bản nghiêng.

PDF KC nguồn SHA-256 `4b6ca4f97e80b85ae4d1df555f13ad1b531c8243f52f300ec34d436357060344`, theo [đối chiếu cặp](C2_A4_DOI_CHIEU.md). Nguồn ảnh này là KC; hình học thang từ mặt bằng KT cần truy vết riêng tới revision KT và ghép tầng/vị trí trước khi áp dữ liệu KC. Chưa xác nhận KT và KC cùng revision phát hành.

## Luồng nguồn và nguyên nhân có thể gây thiếu dày

- `drawing/viewer.py:view_payload` lấy `building_stairs` từ các mặt bằng KT. `rough/stairs.py:detect_stairs` nhận các nét bậc để ước lượng số bậc, rộng vế, rộng bậc, chiếu nghỉ; kiểu `Stair` không có trường dày bản hay locator nguồn KC. Một số trường hợp lấy thang đủ nhất làm mẫu cho hình vẽ bị cắt; đó là suy luận và cần kiểm, không tự coi là kích thước thiết kế của thang này.
- `project_analysis.py:_events` đưa phần KC vào `structural_parts`. Những trường do `structural_parts` trả hiện không có mapping chi tiết bản thang theo instance/tầng; nguồn KT cho mặt bằng và KC cho chiều dày chưa được nối với nhau.
- `frontend/.../do-boc/model.ts:roughRequest` chuyển `stairs` từ mặt bằng và lấy `stair_slab_thickness_mm` từ thông số do người dùng nhập. API phần thô `stair_works` chỉ lấy độ dày từ `ProjectParams.stair_slab_thickness_mm`, không đọc `H=...` trong bản vẽ KC. Vì vậy khi tham số này rỗng, hàm liệt kê “dày bản thang” là thiếu và trả lượng `null`; đó là hành vi bảo toàn thông tin thiếu, không phải bằng chứng chi tiết KC đã được nhận diện rồi mất tại khâu cuối.
- Tham số độ dày hiện là **mức dự án**, không theo từng thang hay từng vế. Sao chép tự động một chú thích vùng sang toàn bộ thang có thể gán sai. Cần hợp đồng ứng viên KC kèm file/revision/hash, tờ, handle/locator, loại phần cấu kiện, tầng/vế và bằng chứng quan hệ; chỉ áp khi xác minh đúng vùng và đúng thang. Thiếu hoặc xung đột giữ `null`, không dùng dữ liệu ví dụ làm mặc định.

## Trạng thái

Đây là rà mã và ảnh, chưa tái hiện một lần rough mới cho thang qua API, chưa có receipt chứng minh request cụ thể đã thiếu đúng trường hay xác nhận độ dày vế từ CAD. Không sửa reader, không chạy TestClient/full/DB, không thay schema. Chờ 01 phân công hunk sửa và 07 cung cấp locator/quan hệ CAD trước khi tích hợp.
