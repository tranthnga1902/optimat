# Hợp đồng đề xuất: hồ sơ nhiều định dạng

Trạng thái: **đề xuất phối hợp backend và giao diện, chưa triển khai hoặc nghiệm thu**. Hợp đồng mã vai trò và capability được chốt trong `ke_hoach_contract_tephhonhop_20261104.md` thay thế tài liệu này. Nguồn yêu cầu: `docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md`, mục “Các loại tệp đầu vào tại Dự án của tôi (04/11/2026)”.

## Vai trò nghiệp vụ và định dạng

Trường `role` do người dùng xác nhận, độc lập với `original_format`. Không suy luận vai trò từ đuôi tệp; nếu hệ thống gợi ý thì chỉ là gợi ý có thể sửa.

| Mã đề xuất | Nhãn hiển thị | Phạm vi |
|---|---|---|
| `KT` | Bản vẽ kiến trúc | Bản vẽ CAD hoặc PDF |
| `KC` | Bản vẽ kết cấu | Bản vẽ CAD hoặc PDF |
| `HO_SO` | Tài liệu dự án | Thuyết minh, yêu cầu kỹ thuật và tài liệu dự án |
| `TIEN_LUONG` | Bảng khối lượng/tiên lượng | Nguồn do người dùng cung cấp để đối chiếu |
| `THAM_KHAO` | Tham khảo | Giữ tương thích bản ghi cũ và tài liệu khác |

Các mã mới vừa `VARCHAR(16)` hiện có nhưng **không qua check constraint hiện tại**; cần migration đã rà soát để mở rộng constraint trước khi lưu. Mô hình backend, DTO, frontend và test phải cập nhật cùng hợp đồng; không đổi vai trò lịch sử cũ bằng suy đoán.

`original_format` biểu thị định dạng kiểm tra từ nội dung và đối chiếu đuôi: `dxf`, `dwg`, `pdf`, `doc`, `docx`, `xls`, `xlsx`. Sự phù hợp giữa vai trò và định dạng cần xác định trên server: CAD và PDF có thể là KT/KC; tài liệu dự án là PDF/Word; tiên lượng là PDF/Excel. `THAM_KHAO` giữ khả năng tham chiếu định dạng được nhận. Không xác nhận `.doc`/`.xls` được hỗ trợ cho đến khi có bộ kiểm nội dung và test tương ứng.

## Metadata một revision

Các trường hiện có giữ nguyên: `project_id`, `file_id`, `revision_id`, `version`, `name`, `original_format`, `size_bytes`, `sha256`, `role`, `uploaded_at`, `source`. Không trả đường dẫn hệ thống.

Các trường đề xuất bổ sung cho UI:

```json
{
  "storage_status": "stored",
  "can_download": true,
  "can_preview": false,
  "preview_reason": "Chưa hỗ trợ xem trước định dạng này; có thể tải bản gốc.",
  "can_analyze_cad": false,
  "analysis_reason": "Chưa hỗ trợ bóc hình học từ định dạng này."
}
```

Ví dụ chỉ minh họa hình dạng DTO; không ngụ ý bất kỳ định dạng nào đã được cài đặt. `can_preview` và `can_analyze_cad` do backend xác định từ **vai trò, định dạng đã kiểm, revision và năng lực hiện có**, không do đuôi tệp hoặc frontend tự suy ra. Khi boolean là `false`, reason là chuỗi tiếng Việt cụ thể; khi `true`, reason có thể `null`. Năng lực là trạng thái tại lúc trả DTO, không hứa tệp sẽ luôn xử lý thành công; preview/analysis phải báo lỗi thật nếu đọc thất bại.

Phân biệt rõ:

1. **Đã nhận**: request gửi tới máy chủ; chưa khẳng định lưu thành công.
2. **Đã lưu**: chỉ trả `storage_status: "stored"` sau khi kiểm tra và giao dịch DB hoàn tất; revision và hash có thể mở lại. Lỗi upload không được tạo trạng thái lưu thành công.
3. **Xem được**: `can_preview` thể hiện có bộ xem phù hợp; kết quả xem thực tế có trạng thái riêng `ready`/`error` và lý do. PDF xem đúng revision theo trang; Excel chỉ xem sheet khi thực sự có bộ đọc phù hợp.
4. **Phân tích được**: `can_analyze_cad` chỉ bật nếu đường xử lý hỗ trợ vai trò và định dạng ấy. PDF có vai trò KT không tự động được coi là CAD. Chọn PDF là đủ để **lưu và mở lại dự án**, không bắt buộc phải phân tích.

Endpoint tải nguyên bản tiếp tục xác nhận chủ sở hữu và quan hệ project/file/revision, kiểm tra đường dẫn, kích thước và SHA-256; trả đúng byte, `private, no-store` và `nosniff`. Endpoint xem PDF cần quyền tương đương và trả đúng revision, với cách hiển thị theo trang được triển khai an toàn; không sử dụng route admin. Excel/Word không xem được thì nêu lý do và cho tải nguyên bản.

## Phiên bản, nguồn và phân tích

- Tên, byte gốc, hash và revision bất biến. Sửa vai trò phải được lưu có lịch sử và không ghi đè byte; backend cần chốt thao tác tạo phiên bản metadata, cách tham chiếu blob và kiểm thử thu gom trước triển khai. Lựa chọn phân tích gắn revision, hash, role và profile version; thay vai trò không âm thầm thay snapshot cũ.
- Nguồn document phải thuộc cùng dự án và đúng revision. Vị trí trang, sheet, dòng hoặc ô chỉ ghi khi đã biết; cần mở rộng `SourceLocation` với `sheet`, `row` và các trường vị trí phù hợp. Nếu chỉ biết tệp, ghi mức truy vết tệp, không tự tạo trang/sheet/dòng.
- Bảng tiên lượng là nguồn riêng để đối chiếu, không tự đưa vào pipeline CAD hoặc cộng cùng khối lượng bóc. Giữ chênh lệch để người dùng duyệt; chưa coi đã có tính năng đối chiếu chỉ vì tệp được lưu.
- Có thể lưu dự án và hồ sơ chỉ có một tệp KT PDF. Nếu pipeline chưa nhận PDF, UI cho xem/tải và nêu rõ chưa thể bóc cùng tệp cần bổ sung; không ép upload CAD để lưu.

## Đối chiếu hiện trạng cần sửa

`src/optimat/drawing/ingest.py` chỉ kiểm DXF/DWG; `project_files.py` gọi bộ này cho mọi upload, preview chỉ CAD; `ProjectDossier.tsx` chỉ chọn `.dwg,.dxf`; `ProjectFilesPanel.tsx` chỉ khai báo ba role cũ. `project_analysis.py` dùng `read_drawing` cho KT/KC và chưa phân tích PDF. `openpyxl` và `pdfplumber` có trong requirements không chứng minh đã có luồng xem Excel/PDF hoặc hỗ trợ `.xls`.

Kiểm thử trước nghiệm thu: bộ chỉ có KT PDF và bộ hỗn hợp; upload hai revision cùng tên khác byte; sửa role giữ lịch sử; mở lại và tải đúng hash; user khác bị từ chối; nội dung sai định dạng, rỗng, quá lớn, hỏng hoặc bị mã hóa trả trạng thái rõ; kiểm giới hạn giải nén và parsing cho định dạng container; preview không chạy bóc/LLM; PDF/Excel unsupported không bị chọn nhầm cho CAD; tiên lượng không cộng vào lượng bóc.
