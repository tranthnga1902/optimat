-- Chỉ chạy sau khi kiểm thử và duyệt delta; không thay migration lịch sử.
BEGIN;
ALTER TABLE public.project_document_revisions DROP CONSTRAINT ck_document_role;
ALTER TABLE public.project_document_revisions ADD CONSTRAINT ck_document_role
    CHECK (role IN ('KT', 'KC', 'HO_SO', 'TIEN_LUONG', 'THAM_KHAO'));
COMMIT;
