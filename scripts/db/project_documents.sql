-- Chỉ chạy sau khi đã review; không reset hoặc backfill dữ liệu hiện hữu.
BEGIN;
CREATE TABLE project_document_revisions (
  revision_id BIGSERIAL PRIMARY KEY,
  file_id INTEGER NOT NULL REFERENCES project_files(file_id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  sha256 VARCHAR(64) NOT NULL,
  stored_path TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  format VARCHAR(16) NOT NULL,
  role VARCHAR(16) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_document_file_version UNIQUE (file_id, version),
  CONSTRAINT ck_document_role CHECK (role IN ('KT', 'KC', 'THAM_KHAO')),
  CONSTRAINT ck_document_version_size CHECK (version > 0 AND size_bytes > 0)
);
CREATE INDEX ix_project_document_revisions_file_id ON project_document_revisions(file_id);
CREATE TABLE project_profile_revisions (
  revision_id BIGSERIAL PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_project_profile_version UNIQUE (project_id, version),
  CONSTRAINT ck_project_profile_version CHECK (version > 0)
);
CREATE INDEX ix_project_profile_revisions_project_id ON project_profile_revisions(project_id);
COMMIT;
