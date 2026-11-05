"""Hồ sơ thuộc chủ dự án; xem bản gốc độc lập với bóc tách."""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .. import config
from ..db.models import Project, ProjectFile
from ..db.project_documents import ProjectDocumentRevision as Revision, ProjectProfileRevision as Profile
from ..db.session import get_database_url, get_engine
from ..drawing.dxf_reader import read_drawing
from ..drawing.ingest import UploadRejected
from ..drawing.view_progress import line_preview
from .auth import require_user
from .project_document_io import capabilities, docx_paragraphs, pdf_preview, validate_document, xls_preview, xlsx_preview

router = APIRouter()
Role = Literal['KT', 'KC', 'HO_SO', 'TIEN_LUONG', 'THAM_KHAO']


class ProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = Field(default='', max_length=512)


class SelectedFile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    file_id: int
    revision_id: int
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    role: Role


class SourceLocation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    page: int | None = Field(default=None, ge=1)
    floor: str | None = None
    table: str | None = None
    sheet: str | None = None
    row: int | None = Field(default=None, ge=1)
    cell: str | None = None
    cad_handle: str | None = None


class SourceValue(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source: Literal['manual', 'document', 'unknown']
    value: str | float | bool | None = None
    unit: str | None = None
    document: SelectedFile | None = None
    location: SourceLocation | None = None

    @model_validator(mode='after')
    def validate_source(self):
        if self.source == 'document' and self.document is None:
            raise ValueError('Nguồn tài liệu cần tham chiếu phiên bản tệp.')
        if self.source != 'document' and (self.document is not None or self.location is not None):
            raise ValueError('Chỉ nguồn tài liệu được có tham chiếu và vị trí.')
        if self.source == 'unknown' and self.value is not None:
            raise ValueError('Nguồn chưa biết không thể có giá trị.')
        return self


class ProfilePayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    # Mỗi giá trị trong ba nhóm là khóa tham chiếu tới source_values, không nhúng provenance tùy ý.
    design_facts: dict[str, str] = Field(default_factory=dict)
    material_preferences: dict[str, str] = Field(default_factory=dict)
    source_values: dict[str, SourceValue] = Field(default_factory=dict)
    effective_values: dict[str, str] = Field(default_factory=dict)
    selected_revisions: list[SelectedFile] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_references(self):
        refs = (*self.design_facts.values(), *self.material_preferences.values(), *self.effective_values.values())
        if any(ref not in self.source_values for ref in refs):
            raise ValueError('Giá trị phải tham chiếu nguồn đã khai báo.')
        return self


class ProfileUpdate(BaseModel):
    expected_version: int = Field(ge=0)
    payload: ProfilePayload


class RoleUpdate(BaseModel):
    revision_id: int = Field(gt=0)
    expected_version: int = Field(gt=0)
    role: Role


def _user(user: dict | None) -> int:
    if not get_database_url():
        raise HTTPException(503, 'Cần kết nối cơ sở dữ liệu để dùng hồ sơ dự án.')
    if not user or not user.get('is_active'):
        raise HTTPException(401, 'Cần đăng nhập để dùng hồ sơ dự án.')
    return user['user_id']


def _project(db: Session, project_id: int, user_id: int, lock: bool = False) -> Project:
    query = select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
    project = db.scalar(query.with_for_update() if lock else query)
    if project is None:
        raise HTTPException(404, 'Không tìm thấy dự án.')
    return project


def _revision(db: Session, project_id: int, file_id: int, revision_id: int) -> tuple[ProjectFile, Revision]:
    row = db.execute(select(ProjectFile, Revision).join(Revision, Revision.file_id == ProjectFile.file_id).where(
        ProjectFile.project_id == project_id, ProjectFile.file_id == file_id, Revision.revision_id == revision_id)).first()
    if row is None:
        raise HTTPException(404, 'Không tìm thấy phiên bản tệp trong dự án.')
    return row[0], row[1]


def _metadata(file: ProjectFile, rev: Revision) -> dict:
    return {'project_id': file.project_id, 'file_id': file.file_id, 'revision_id': rev.revision_id,
            'version': rev.version, 'sha256': rev.sha256, 'name': file.filename,
            'original_format': rev.format, 'size_bytes': rev.size_bytes, 'role': rev.role,
            'uploaded_at': rev.created_at, 'preview_status': 'not_requested', 'source': 'user_upload',
            **capabilities(rev.role, rev.format)}


def _verified_path(rev: Revision) -> Path:
    root = config.DATA_DIR.resolve() / 'project_documents'
    raw = Path(rev.stored_path)
    if root.is_symlink() or raw.is_symlink() or raw.parent.is_symlink():
        raise HTTPException(404, 'Không tìm thấy bản gốc được lưu.')
    path = raw.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, 'Không tìm thấy bản gốc được lưu.')
    try:
        digest = hashlib.sha256()
        size = 0
        with path.open('rb') as stream:
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
    except OSError as exc:
        raise HTTPException(404, 'Không đọc được bản gốc.') from exc
    if size != rev.size_bytes or digest.hexdigest() != rev.sha256:
        raise HTTPException(409, 'Bản gốc không còn khớp phiên bản đã lưu.')
    return path


@router.get('/api/projects')
def list_projects(user: dict | None = Depends(require_user)) -> list[dict]:
    uid = _user(user)
    with Session(get_engine()) as db:
        return [_project_data(p) for p in db.scalars(select(Project).where(Project.user_id == uid).order_by(Project.project_id.desc()))]


def _project_data(p: Project) -> dict:
    return {'project_id': p.project_id, 'name': p.name, 'address': p.address, 'created_at': p.created_at, 'updated_at': p.updated_at}


@router.post('/api/projects', status_code=201)
def create_project(body: ProjectInput, user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    name = body.name.strip()
    if not name:
        raise HTTPException(422, 'Tên dự án không được để trống.')
    with Session(get_engine()) as db, db.begin():
        project = Project(user_id=uid, name=name, address=body.address.strip())
        db.add(project)
        db.flush()
        return _project_data(project)


@router.get('/api/projects/{project_id}')
def get_project(project_id: int, user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    with Session(get_engine()) as db:
        return _project_data(_project(db, project_id, uid))


@router.patch('/api/projects/{project_id}')
def update_project(project_id: int, body: ProjectInput, user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    if not body.name.strip():
        raise HTTPException(422, 'Tên dự án không được để trống.')
    with Session(get_engine()) as db, db.begin():
        p = _project(db, project_id, uid, lock=True)
        p.name, p.address = body.name.strip(), body.address.strip()
        db.flush()
        return _project_data(p)


@router.get('/api/projects/{project_id}/files')
def list_files(project_id: int, user: dict | None = Depends(require_user)) -> list[dict]:
    uid = _user(user)
    with Session(get_engine()) as db:
        _project(db, project_id, uid)
        rows = db.execute(select(ProjectFile, Revision).join(Revision, Revision.file_id == ProjectFile.file_id)
                          .where(ProjectFile.project_id == project_id).order_by(ProjectFile.file_id, Revision.version))
        return [_metadata(f, r) for f, r in rows]


@router.post('/api/projects/{project_id}/files', status_code=201)
async def upload_file(project_id: int, file: UploadFile = File(...), role: Role = Form(...),
                      file_id: int | None = Form(None), user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    name = Path((file.filename or '').replace('\\', '/')).name
    if not name or len(name) > 255:
        raise HTTPException(422, 'Tên tệp không hợp lệ.')
    with Session(get_engine()) as db:
        _project(db, project_id, uid)
    data = await file.read(config.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    try:
        info = await run_in_threadpool(validate_document, name, data, file.content_type)
    except UploadRejected as exc:
        raise HTTPException(422, str(exc)) from exc
    with Session(get_engine()) as db, db.begin():
        _project(db, project_id, uid, lock=True)
        if file_id is None:
            entry = ProjectFile(project_id=project_id, filename=name, file_type=info['ext'][1:], stored_path='')
            db.add(entry)
            db.flush()
            version = 1
        else:
            entry = db.scalar(select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.file_id == file_id))
            if entry is None:
                raise HTTPException(404, 'Không tìm thấy tệp trong dự án.')
            if name != entry.filename or info['ext'][1:] != entry.file_type:
                raise HTTPException(422, 'Phiên bản mới phải giữ tên và định dạng tệp.')
            version = (db.scalar(select(func.max(Revision.version)).where(Revision.file_id == file_id)) or 0) + 1
        storage = config.DATA_DIR / 'project_documents'
        root = storage / str(project_id)
        root.mkdir(parents=True, exist_ok=True)
        if storage.is_symlink() or root.is_symlink() or not root.resolve().is_relative_to(storage.resolve()):
            raise HTTPException(409, 'Kho tệp dự án không hợp lệ.')
        path = root / (secrets.token_hex(24) + info['ext'])
        with path.open('xb') as stream:
            stream.write(data)
        if version == 1:
            entry.stored_path = str(path.resolve())
        rev = Revision(file_id=entry.file_id, version=version, sha256=info['sha256'], stored_path=str(path.resolve()),
                       size_bytes=len(data), format=info['ext'][1:], role=role)
        db.add(rev)
        db.flush()
        # shortcut: nếu giao dịch thất bại, tệp mồ côi được giữ lại; cần tác vụ thu gom sau khi đối chiếu DB.
        return _metadata(entry, rev)


@router.post('/api/projects/{project_id}/files/{file_id}/role-revisions')
def change_role(project_id: int, file_id: int, body: RoleUpdate, user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    with Session(get_engine()) as db, db.begin():
        _project(db, project_id, uid, lock=True)
        entry, old = _revision(db, project_id, file_id, body.revision_id)
        latest = db.scalar(select(func.max(Revision.version)).where(Revision.file_id == file_id))
        if latest != body.expected_version or old.version != latest:
            raise HTTPException(409, 'Phiên bản tệp đã thay đổi; hãy tải lại.')
        _verified_path(old)
        if old.role == body.role:
            return _metadata(entry, old)
        rev = Revision(file_id=file_id, version=latest + 1, sha256=old.sha256, stored_path=old.stored_path,
                       size_bytes=old.size_bytes, format=old.format, role=body.role)
        db.add(rev)
        db.flush()
        return _metadata(entry, rev)


@router.get('/api/projects/{project_id}/files/{file_id}/revisions/{revision_id}/original')
def original(project_id: int, file_id: int, revision_id: int, user: dict | None = Depends(require_user)):
    uid = _user(user)
    with Session(get_engine()) as db:
        _project(db, project_id, uid)
        f, rev = _revision(db, project_id, file_id, revision_id)
        path = _verified_path(rev)
        return FileResponse(path, filename=f.filename, media_type='application/octet-stream',
                            headers={'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'private, no-store'})


@router.get('/api/projects/{project_id}/files/{file_id}/revisions/{revision_id}/preview')
async def preview(project_id: int, file_id: int, revision_id: int, user: dict | None = Depends(require_user),
                  sheet: int = 1) -> dict:
    uid = _user(user)
    with Session(get_engine()) as db:
        _project(db, project_id, uid)
        _, rev = _revision(db, project_id, file_id, revision_id)
        path, format = _verified_path(rev), rev.format
    if format == 'pdf':
        if not capabilities('', format)['can_preview']:
            raise HTTPException(422, 'Máy chủ chưa hỗ trợ xem trước PDF; hãy tải bản gốc.')
        try:
            _, pages = await run_in_threadpool(lambda: pdf_preview(path, 1))
        except Exception as exc:
            raise HTTPException(422, 'Không thể xem PDF; tệp có thể bị hỏng hoặc bị khóa.') from exc
        return {'status': 'ready', 'original_format': format, 'kind': 'pdf', 'pages': pages,
                'revision_id': revision_id, 'sha256': rev.sha256}
    if format in {'xls', 'xlsx'}:
        if not capabilities('', format)['can_preview']:
            raise HTTPException(422, 'Máy chủ chưa hỗ trợ xem bảng Excel; hãy tải bản gốc.')
        try:
            table = await run_in_threadpool(lambda: xls_preview(path, sheet) if format == 'xls' else xlsx_preview(path, sheet))
        except Exception as exc:
            raise HTTPException(422, 'Không thể xem sheet Excel; hãy kiểm tra tệp và số sheet.') from exc
        return {'status': 'ready', 'original_format': format, 'kind': format, 'table': table,
                'revision_id': revision_id, 'sha256': rev.sha256}
    if format == 'docx':
        try:
            doc = await run_in_threadpool(lambda: docx_paragraphs(path))
        except Exception as exc:
            raise HTTPException(422, 'Không thể xem DOCX; tệp có thể bị hỏng.') from exc
        return {'status': 'ready', 'original_format': format, 'kind': 'docx', **doc,
                'revision_id': revision_id, 'sha256': rev.sha256}
    if format not in {'dxf', 'dwg'}:
        raise HTTPException(422, 'Chưa hỗ trợ xem trước định dạng này; hãy tải bản gốc.')
    try:
        result = await run_in_threadpool(lambda: line_preview(read_drawing(str(path))))
    except Exception as exc:
        raise HTTPException(422, 'Không thể xem trước tệp CAD; hãy kiểm tra tệp và bộ chuyển DWG.') from exc
    return {'status': 'ready', 'original_format': format, 'preview': result,
            'warnings': ['Đã giảm số nét hiển thị.'] if result['shown'] < result['total'] else []}


@router.get('/api/projects/{project_id}/files/{file_id}/revisions/{revision_id}/preview/pages/{page}')
async def preview_pdf_page(project_id: int, file_id: int, revision_id: int, page: int,
                           user: dict | None = Depends(require_user)) -> Response:
    uid = _user(user)
    with Session(get_engine()) as db:
        _project(db, project_id, uid)
        _, rev = _revision(db, project_id, file_id, revision_id)
        if rev.format != 'pdf' or not capabilities(rev.role, rev.format)['can_preview']:
            raise HTTPException(422, 'Không hỗ trợ xem trang cho tệp này.')
        path = _verified_path(rev)
    try:
        image, _ = await run_in_threadpool(lambda: pdf_preview(path, page))
    except Exception as exc:
        raise HTTPException(422, 'Không thể xem trang PDF; kiểm tra số trang và tệp gốc.') from exc
    return Response(image, media_type='image/png', headers={'Cache-Control': 'private, no-store',
                                                            'X-Content-Type-Options': 'nosniff'})


def _latest_profile(db: Session, project_id: int) -> Profile | None:
    return db.scalar(select(Profile).where(Profile.project_id == project_id).order_by(Profile.version.desc()).limit(1))


def _check_selection(db: Session, project_id: int, selected: SelectedFile, verify_bytes: bool = False) -> Path | None:
    _, rev = _revision(db, project_id, selected.file_id, selected.revision_id)
    if rev.sha256 != selected.sha256 or rev.role != selected.role:
        raise HTTPException(409, 'Phiên bản hoặc vai trò tệp không còn khớp lựa chọn.')
    return _verified_path(rev) if verify_bytes else None


@router.get('/api/projects/{project_id}/profile')
def get_profile(project_id: int, user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    with Session(get_engine()) as db:
        _project(db, project_id, uid)
        current = _latest_profile(db, project_id)
        return {'version': current.version if current else 0,
                'payload': current.payload if current else ProfilePayload().model_dump()}


@router.patch('/api/projects/{project_id}/profile')
def update_profile(project_id: int, body: ProfileUpdate, user: dict | None = Depends(require_user)) -> dict:
    uid = _user(user)
    payload = body.payload.model_dump()
    try:
        json.dumps(payload, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, 'Thông tin dự án không hợp lệ.') from exc
    with Session(get_engine()) as db, db.begin():
        _project(db, project_id, uid, lock=True)
        current = _latest_profile(db, project_id)
        version = current.version if current else 0
        if version != body.expected_version:
            raise HTTPException(409, 'Thông tin dự án đã thay đổi; hãy tải lại trước khi lưu.')
        for selection in body.payload.selected_revisions:
            _, selected_rev = _revision(db, project_id, selection.file_id, selection.revision_id)
            _check_selection(db, project_id, selection)
            if not capabilities(selected_rev.role, selected_rev.format)['can_analyze_cad']:
                raise HTTPException(422, 'Chỉ chọn tệp CAD kiến trúc hoặc kết cấu để phân tích.')
        for source in body.payload.source_values.values():
            if source.document is not None:
                _check_selection(db, project_id, source.document)
        rev = Profile(project_id=project_id, version=version + 1, payload=payload)
        db.add(rev)
        db.flush()
        return {'version': rev.version, 'payload': rev.payload}


@dataclass(frozen=True)
class StoredAnalysisFile:
    file_id: int
    revision_id: int
    sha256: str
    role: str
    path: Path


def resolve_analysis_files(db: Session, project_id: int, user_id: int, profile_version: int,
                           files: list[SelectedFile]) -> list[StoredAnalysisFile]:
    """Caller xác thực user; pipeline đọc path nội bộ, không gửi path/bytes về browser.

    Hàm chỉ kiểm tra snapshot và tệp, chưa ánh xạ profile vào options phân tích.
    Caller không được thay snapshot bằng Project.address hoặc giá trị mặc định mới nhất.
    """
    _project(db, project_id, user_id)
    profile = _latest_profile(db, project_id)
    if (profile.version if profile else 0) != profile_version:
        raise HTTPException(409, 'Phiên bản thông tin dự án đã thay đổi.')
    if not files or not any(f.role == 'KT' for f in files):
        raise HTTPException(422, 'Cần chọn ít nhất một bản vẽ kiến trúc KT.')
    if len({f.revision_id for f in files}) != len(files):
        raise HTTPException(422, 'Không được chọn trùng phiên bản tệp.')
    if len({f.file_id for f in files}) != len(files):
        raise HTTPException(422, 'Chỉ chọn một phiên bản cho mỗi tệp.')
    if any(f.role not in ('KT', 'KC') for f in files):
        raise HTTPException(422, 'Chỉ phân tích tệp kiến trúc hoặc kết cấu CAD.')
    for f in files:
        _, revision = _revision(db, project_id, f.file_id, f.revision_id)
        if not capabilities(revision.role, revision.format)['can_analyze_cad']:
            raise HTTPException(422, 'Định dạng tệp chưa hỗ trợ phân tích CAD.')
    if profile is None or sorted((f.model_dump() for f in files), key=lambda x: x['revision_id']) != sorted(
        (f for f in profile.payload.get('selected_revisions', [])),
        key=lambda x: x['revision_id']):
        raise HTTPException(409, 'Lựa chọn tệp không khớp hồ sơ đã lưu.')
    return [StoredAnalysisFile(f.file_id, f.revision_id, f.sha256, f.role,
                               _check_selection(db, project_id, f, verify_bytes=True)) for f in files]
