# Kế hoạch triển khai hồ sơ hỗn hợp — 04/11/2026

Trạng thái: **hợp đồng chuẩn bị triển khai**, không chứng minh code, runtime, migration hoặc kiểm thử đã hoàn thành. Tài liệu này thay phần mã vai trò trong đề xuất trước `hop_dong_ho_so_da_dinh_dang_20261104.md`.

## DTO và quy tắc

`role` là một trong `KT`, `KC`, `HO_SO`, `TIEN_LUONG`, `THAM_KHAO`. Giữ `THAM_KHAO` cho các revision cũ. `original_format` độc lập, nhận một trong `dxf`, `dwg`, `pdf`, `doc`, `docx`, `xls`, `xlsx` khi đã qua kiểm tra theo định dạng. Không tự đoán vai trò từ đuôi; người dùng chọn và có thể sửa.

Đề xuất bổ sung vào metadata revision hiện có:

```json
{
  "project_id": 101,
  "file_id": 201,
  "revision_id": 301,
  "version": 1,
  "name": "ban-ve.pdf",
  "original_format": "pdf",
  "size_bytes": 1234,
  "sha256": "<sha256-cua-byte-goc>",
  "role": "KT",
  "uploaded_at": "<thoi-gian-may-chu>",
  "source": "user_upload",
  "storage_status": "stored",
  "can_download": true,
  "can_preview": true,
  "preview_reason": null,
  "can_analyze_cad": false,
  "analysis_reason": "Chưa hỗ trợ bóc hình học từ PDF; bổ sung bản CAD khi cần phân tích."
}
```

Đây là ví dụ DTO cho năng lực PDF **sau khi đã triển khai và kiểm thử**, không phải trạng thái runtime hiện nay. `preview_status` hiện có giữ tương thích trong giai đoạn chuyển tiếp; trạng thái xem thực tế phải phản ánh kết quả xử lý. Chỉ trả `storage_status: "stored"` sau commit thành công. Các cờ năng lực do server quyết định theo revision, role, format và bộ đọc thực tế; kiểm quyền và điều kiện phân tích vẫn thực hiện ở từng endpoint. `reason` là `null` khi tương ứng `true`, có thông báo tiếng Việt cụ thể khi `false`. Nguồn Word/Excel chưa có reader vẫn có thể lưu và tải nếu vượt qua kiểm định định dạng; không coi đã xem hoặc phân tích được.

`selected_revisions` trong profile chứa **duy nhất subset CAD KT/KC dùng phân tích**, có thể là `[]`. PDF-only được tạo, lưu, xem và mở lại; nút phân tích giải thích hạn chế. Nếu client cố gửi PDF hoặc tệp vai trò khác vào endpoint analysis thì server từ chối rõ trước khi chạy pipeline, không lọc âm thầm. `source_values.document` được tham chiếu mọi revision thuộc dự án, kể cả PDF/Word/Excel; bổ sung `sheet`/`row` vào `SourceLocation` khi có căn cứ, không sinh vị trí giả. Bảng `TIEN_LUONG` chỉ là nguồn đối chiếu, không cộng vào lượng bóc.

### Đổi vai trò không tải lại byte

Đề xuất endpoint `POST /api/projects/{project_id}/files/{file_id}/role-revisions` với body `{"revision_id":301,"expected_version":1,"role":"HO_SO"}`. Tên route có thể điều chỉnh trước khi tích hợp nhưng semantics phải giữ: server kiểm ownership, revision/file/project; khóa trong giao dịch; `expected_version` phải khớp phiên bản mới nhất của file, revision đang sửa phải đúng phiên bản đó, sai trả `409`; role sai `422`. Tạo revision mới có version tăng, cùng `stored_path`, hash, dung lượng và định dạng; giữ byte và metadata revision cũ. Đọc/tải/preview cả hai revision theo đúng quyền. Nếu role không thay đổi, trả revision hiện hữu hoặc lỗi rõ theo quy ước chốt trước triển khai; không tạo lịch sử giả. Cần tính đến tham chiếu blob dùng chung khi thu gom; không xóa blob chỉ vì một revision bị xóa. `selected_revisions` cũ không tự chuyển sang revision mới; user chọn và lưu snapshot phân tích mới.

## Phạm vi mã dự kiến

| Tệp hoặc nhóm | Thay đổi dự kiến |
|---|---|
| `src/optimat/db/project_documents.py` | Đồng bộ `ck_document_role` với năm mã; không sửa định nghĩa migration lịch sử đã áp. |
| `scripts/db/` | Thêm delta SQL mở rộng check và script rollback có guard; không tạo bảng, backfill, đổi owner hay xóa dữ liệu. |
| `src/optimat/api/project_files.py` | Role DTO, kiểm định theo định dạng/dung lượng, capability metadata, lưu/tải/preview đúng revision, sửa role với optimistic concurrency, provenance sheet/dòng và chặn non-CAD trong resolver. |
| `src/optimat/drawing/ingest.py` hoặc module kiểm định hồ sơ mới | Giữ hành vi CAD đang dùng; validator tách theo loại nội dung. PDF, OLE (`.doc`/`.xls`) và OOXML (`.docx`/`.xlsx`) cần kiểm tra cấu trúc riêng, giới hạn đầu vào và container; không xem chữ ký đầu tệp là bằng chứng tài liệu lành mạnh/đọc được. Không chạy macro, OCR hay LLM. |
| `src/optimat/api/project_analysis.py` | Xác nhận resolver chặn non-CAD và role không hợp lệ trước pipeline; không nhập tiên lượng vào BOQ. Các giá trị profile đã có mapping chỉ dùng theo snapshot có nguồn. |
| `frontend/src/components/ProjectFilesPanel.tsx`, `frontend/src/app/(user)/du-an-cua-toi/ProjectDossier.tsx`, `frontend/src/lib/project-records.ts` | Chủ sở hữu UI phối hợp cập nhật enum, chọn nhiều tệp, sửa role, trạng thái/capability do server trả, xem PDF đúng trang và bộ xem sheet khi có. Không giả định năng lực theo đuôi. |
| `tests/test_project_files.py`, `tests/test_project_files_db.py`, test mới cho validator/migration | Bổ sung ca dưới đây; kiểm thử DB trong PostgreSQL thử nghiệm cô lập, không dùng dữ liệu thật. |

Không sửa các vùng do owner khác đang giữ; bảng trên là handoff vị trí thay đổi, không cấp quyền ghi vào tệp do người khác phụ trách.

## Delta DDL đề xuất — chưa thực thi

Migration mới, giữ nguyên `scripts/db/project_documents.sql` và receipt cũ:

```sql
BEGIN;
ALTER TABLE public.project_document_revisions
  DROP CONSTRAINT ck_document_role;
ALTER TABLE public.project_document_revisions
  ADD CONSTRAINT ck_document_role
  CHECK (role IN ('KT', 'KC', 'HO_SO', 'TIEN_LUONG', 'THAM_KHAO'));
COMMIT;
```

Chỉ chạy sau khi xác nhận đúng database, schema hiện tại và tên/nội dung constraint, sao lưu/snapshot phù hợp, rồi kiểm thử trong DB cô lập. Nếu constraint không đúng hoặc thiếu thì dừng và báo drift; không dùng `IF EXISTS` để che sai lệch.

### Rollback đề xuất — chỉ khi không có revision dùng role mới

```sql
BEGIN;
LOCK TABLE public.project_document_revisions IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.project_document_revisions
             WHERE role IN ('HO_SO', 'TIEN_LUONG')) THEN
    RAISE EXCEPTION 'Không thể thu hẹp role khi còn revision sử dụng role mới';
  END IF;
END $$;
ALTER TABLE public.project_document_revisions DROP CONSTRAINT ck_document_role;
ALTER TABLE public.project_document_revisions ADD CONSTRAINT ck_document_role
  CHECK (role IN ('KT', 'KC', 'THAM_KHAO'));
COMMIT;
```

Nếu đã có dữ liệu role mới, **không xóa hoặc đổi role để ép rollback**; ngừng đường ghi liên quan, giữ lịch sử và xử lý tương thích theo kế hoạch riêng. Cần kiểm thử khóa/race và rollback trên database cô lập, không áp tự động lên database ứng dụng.

## Kiểm thử cần có

1. **PDF-only**: tạo project, tải KT PDF, lưu profile `selected_revisions=[]`, tải lại/mở đúng revision, xem trang, tải nguyên byte/SHA; analysis trả lý do chưa hỗ trợ trước pipeline.
2. **Hỗn hợp**: CAD KT/KC, PDF thuyết minh, Word, Excel `.xls`/`.xlsx` và PDF tiên lượng theo role đúng; kiểm validator, dung lượng, tên và khả năng từng tệp; chỉ CAD KT/KC được chọn cho analysis. Tệp hỏng/đổi đuôi/tài liệu không đọc được trả lỗi hoặc capability đúng, không chạy macro.
3. **Vai trò và phiên bản**: đổi role tạo revision mới không upload byte; bản cũ/byte/hash không đổi; hai request cùng expected version chỉ một request thành công; stale version `409`; kiểm nguồn cũ vẫn trỏ đúng revision và không tự đổi snapshot analysis.
4. **Quyền và integrity**: chủ A thành công; B/ẩn danh không đọc, tải, xem, đổi role hay chọn nguồn A; file/revision khác project bị từ chối; byte bị thay, thiếu file, symlink/traversal bị từ chối; download so SHA-256.
5. **Không có side effect phân tích**: spy pipeline/LLM/save; upload, mở, xem PDF/Excel và lưu profile không chạy bóc/LLM hoặc ghi `takeoff_results`; bảng tiên lượng không cộng vào BOQ.
6. **Delta/rollback**: test constraints trước/sau, role cũ giữ nguyên, role mới hợp lệ, role khác bị từ chối; rollback thành công khi không có role mới và từ chối an toàn khi có; đối chiếu schema/data hiện hữu. Không triển khai DB ứng dụng đến khi review và test cô lập đạt.
