-- Không đổi/xóa dữ liệu role mới để ép rollback.
BEGIN;
LOCK TABLE public.project_document_revisions IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.project_document_revisions WHERE role IN ('HO_SO', 'TIEN_LUONG')) THEN
        RAISE EXCEPTION 'Không thể rollback khi còn revision dùng role mới';
    END IF;
END $$;
ALTER TABLE public.project_document_revisions DROP CONSTRAINT ck_document_role;
ALTER TABLE public.project_document_revisions ADD CONSTRAINT ck_document_role
    CHECK (role IN ('KT', 'KC', 'THAM_KHAO'));
COMMIT;
