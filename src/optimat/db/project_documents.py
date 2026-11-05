"""Phiên bản bất biến cho hồ sơ gốc và thông tin do chủ dự án cung cấp."""
from datetime import datetime
from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .models import Base


class ProjectDocumentRevision(Base):
    __tablename__ = 'project_document_revisions'
    __table_args__ = (UniqueConstraint('file_id', 'version', name='uq_document_file_version'),
                      CheckConstraint("role IN ('KT','KC','HO_SO','TIEN_LUONG','THAM_KHAO')", name='ck_document_role'),
                      CheckConstraint('version > 0 AND size_bytes > 0', name='ck_document_version_size'))
    revision_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('project_files.file_id', ondelete='CASCADE'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    stored_path: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    format: Mapped[str] = mapped_column(String(16))
    role: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectProfileRevision(Base):
    __tablename__ = 'project_profile_revisions'
    __table_args__ = (UniqueConstraint('project_id', 'version', name='uq_project_profile_version'),
                      CheckConstraint('version > 0', name='ck_project_profile_version'))
    revision_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.project_id', ondelete='CASCADE'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
