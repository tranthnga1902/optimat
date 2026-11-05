"""Bóc tách các phiên bản đã chọn trong một hồ sơ dự án đã lưu."""
import json
import hashlib
import math
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from . import project_files
from .. import analysis_cache
from .auth import require_user
from zipfile import BadZipFile

from .document_candidates import docx_candidates, spreadsheet_candidates
from ..facts import estimate as estimate_facts, labels as label_facts, params as params_facts
from .stair_evidence import StairEvidenceRequest, stair_from_evidence
from ..catalog.repository import Catalog
from ..db.models import ProjectFile
from ..db.project_documents import ProjectProfileRevision
from ..db.session import get_engine
from ..drawing.dwg_convert import DrawingError
from ..drawing.dxf_reader import read_drawing
from ..drawing.takeoff import takeoff_plans
from ..drawing.view_progress import line_preview
from ..drawing.viewer import add_cad_layers, view_payload
from ..rough.takeoff import structural_parts
from ..schemas import OpeningDefaults

router = APIRouter()


@router.post('/api/projects/{project_id}/stair-evidence')
def validate_stair_evidence(project_id: int, body: StairEvidenceRequest, user: dict | None = Depends(require_user)):
    """Kiểm nguồn từng bộ phận; chỉ trả bản nháp, không lưu hoặc tính."""
    uid = project_files._user(user)
    with Session(get_engine()) as db:
        project_files._project(db, project_id, uid)
        profile = project_files._latest_profile(db, project_id)
        if profile is None or profile.version != body.profile_version:
            raise HTTPException(409, 'Phiên bản hồ sơ dự án đã thay đổi.')
        selected = profile.payload.get('selected_revisions', [])
        sources = {}
        for part in body.parts:
            for fact in part.facts:
                if fact.source is None:
                    continue
                source = fact.source
                if source.model_dump() not in selected:
                    raise HTTPException(409, 'Nguồn thang không nằm trong phiên bản hồ sơ đã chọn.')
                if source.revision_id in sources and sources[source.revision_id] != source:
                    raise HTTPException(409, 'Nguồn thang có revision bị trùng nhưng không khớp.')
                sources[source.revision_id] = source
        for source in sources.values():
            project_files._check_selection(db, project_id, source, verify_bytes=True)
    stair, unmapped = stair_from_evidence(body)
    return {'project_id': project_id, 'profile_version': body.profile_version,
            'stair_id': body.stair_id, 'parts': [p.model_dump() for p in body.parts],
            'stair': stair, 'unmapped': unmapped,
            'status': 'user_selected_unreviewed', 'saved': False,
            'notice': 'Dữ kiện do người dùng chọn, chưa kiểm và chưa lưu hoặc áp vào khối lượng.'}


@router.get('/api/projects/{project_id}/files/{file_id}/revisions/{revision_id}/candidates')
async def document_candidates(project_id: int, file_id: int, revision_id: int, sheet: int = 1, allow_ai: bool = False,
                              user: dict | None = Depends(require_user)):
    """Đọc ứng viên từ một revision thuộc dự án, không thay kết quả đã kiểm.
    DOCX: kèm thông số gợi ý (KD03); XLS/XLSX: kèm mã công tác từng dòng (KD07). allow_ai: cho gửi chữ lên OpenAI."""
    uid = project_files._user(user)
    if sheet < 1:
        raise HTTPException(422, 'Số sheet phải từ 1.')
    with Session(get_engine()) as db:
        project_files._project(db, project_id, uid)
        file, rev = project_files._revision(db, project_id, file_id, revision_id)
        if rev.role not in ('HO_SO', 'TIEN_LUONG'):
            raise HTTPException(422, 'Chỉ đọc ứng viên từ hồ sơ hoặc tiên lượng.')
        if rev.format not in ('xls', 'xlsx', 'docx'):
            raise HTTPException(422, 'Chỉ trích ứng viên từ XLS, XLSX hoặc DOCX; không nhận PDF, ảnh.')
        path = project_files._verified_path(rev)
        format = rev.format
        source = {'project_id': project_id, 'file_id': file_id, 'revision_id': revision_id,
                  'sha256': rev.sha256, 'role': rev.role, 'filename': file.filename}
    try:
        if format == 'docx':
            result = await run_in_threadpool(docx_candidates, path, source)
            items = [{'ref': c['source']['paragraph'], 'text': c['text']} for c in result['candidates']]
            report = await run_in_threadpool(params_facts.extract, items, file.filename, allow_ai)
            suggested, conflicts = params_facts.suggest(report.facts)
            return {**result, 'input_facts': {**report.model_dump(), 'suggested_params': suggested, 'conflicts': conflicts}}
        result = await run_in_threadpool(spreadsheet_candidates, path, format, sheet, source)
        mapping = await run_in_threadpool(estimate_facts.map_rows, result['candidates'], file.filename, allow_ai)
        return {**result, 'estimate_mapping': mapping}
    except (ValueError, OSError, ImportError, KeyError, BadZipFile) as exc:
        if format == 'docx':
            raise HTTPException(422, 'Không đọc được DOCX; kiểm tra tệp gốc.') from exc
        raise HTTPException(422, 'Không đọc được sheet; kiểm tra số sheet, định dạng hoặc bộ đọc XLS/XLSX.') from exc


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile_version: int = Field(ge=1)
    files: list[project_files.SelectedFile] = Field(min_length=1)
    progressive: bool = False
    client_analysis_id: uuid.UUID | None = None
    allow_ai: bool = False      # KD02: cho gửi chữ của bản vẽ lên OpenAI để gắn nhãn (R8: hồ sơ hạn chế thì để False)


def _dimensions(profile):
    """Chỉ nhận kích thước mm từ giá trị hiệu lực có nguồn ở đúng phiên bản."""
    values = {}
    for field in ('floor_height_mm', *OpeningDefaults.model_fields):
        source = profile.source_values.get(profile.effective_values.get(field))
        if source is None or source.source == 'unknown' or source.value is None:
            continue
        value = source.value
        if (source.unit != 'mm' or isinstance(value, bool) or not isinstance(value, (float, int))
                or not math.isfinite(value) or value <= 0):
            raise HTTPException(422, f'Kiểm tra lại giá trị và đơn vị mm của {field} trong hồ sơ.')
        values[field] = value
    return values.pop('floor_height_mm', None), OpeningDefaults(**values) if values else None


def _column_sources(parts, sources):
    """Chỉ gắn revision khi xác định được nguồn KC duy nhất của instance."""
    if 'structural_columns' not in parts:
        return parts
    columns, unresolved = [], False
    for value in parts['structural_columns']:
        column = jsonable_encoder(value)
        filename = column.get('file') or ''
        matches = [(name, source, path) for name, source, path in sources
                   if not filename or name == filename or Path(path) == Path(filename)]
        if len(matches) == 1 and column.get('source_sha256') and column['source_sha256'].lower() != matches[0][1]['sha256'].lower():
            matches = []
        if len(matches) == 1:
            name, source, _ = matches[0]
            column['file'] = name
            evidence = f"Tệp KC {name}; file_id={source['file_id']}; revision_id={source['revision_id']}; sha256={source['sha256']}"
            column['evidence'] = list(column.get('evidence') or [])
            if evidence not in column['evidence']:
                column['evidence'].append(evidence)
        else:
            unresolved = True
        columns.append(column)
    result = {**parts, 'structural_columns': columns}
    if unresolved:
        result['notes'] = [*(parts.get('notes') or []), 'Chưa xác định duy nhất phiên bản tệp KC cho một số cột; cần đối chiếu nguồn trước khi sử dụng.']
    return result


def _input_facts(drawing, name, allow_ai, need_plan):
    """KD03–KD05: thông số gợi ý từ ghi chú + đề xuất nhãn chờ duyệt. Lỗi ở bước này không làm hỏng phân tích."""
    try:
        report = params_facts.extract(params_facts.candidates(params_facts.cad_texts(drawing)), name, allow_ai)
        extra = label_facts.label_drawing(drawing, name, allow_ai, need_plan)
    except (ValueError, OSError, KeyError) as exc:
        return {'facts': [], 'rejected': [], 'ai': {'status': 'loi', 'message': str(exc)[:200]}}
    return {'facts': report.facts + extra.facts, 'rejected': report.rejected + extra.rejected,
            'ai': {'thong_so': report.ai, **extra.ai}}


def _merge_facts(parts):
    facts = [f for p in parts for f in p['facts']]
    suggested, conflicts = params_facts.suggest(facts)
    return {'facts': [f.model_dump() for f in facts], 'rejected': [r for p in parts for r in p['rejected']],
            'ai': [p['ai'] for p in parts], 'suggested_params': suggested, 'conflicts': conflicts,
            'notice': 'Thông số gợi ý (mức B) đọc từ ghi chú bằng quy tắc hoặc AI gắn nhãn + mã đọc số; chưa áp vào '
                      'khối lượng, người dùng xác nhận mới dùng. Đề xuất nhãn (tờ, ký hiệu, cột bảng) chờ quản trị duyệt.'}


def _events(inputs, names, provenance, profile, allow_ai=False):
    height, openings = _dimensions(profile)
    catalog = Catalog.load()
    views, structural_drawings, structural_names, structural_sources = [], [], [], []
    fact_parts = []
    for item, source in zip(inputs, provenance['files'], strict=True):
        name = names[item.file_id]
        yield {'type': 'status', 'stage': 'reading', 'message': f'Đang đọc {name} từ hồ sơ đã lưu…'}
        drawing = read_drawing(str(item.path))
        if item.role == 'KC':
            yield {'type': 'status', 'stage': 'facts', 'message': f'Đang đọc ghi chú thông số trong {name}…'}
            fact_parts.append(_input_facts(drawing, name, allow_ai, need_plan=False))
            structural_drawings.append(drawing)
            structural_names.append(name)
            structural_sources.append((name, source, str(item.path)))
            continue
        yield {'type': 'preview', 'preview': line_preview(drawing)}
        yield {'type': 'status', 'stage': 'recognizing', 'message': f'Đang nhận diện mặt bằng trong {name}…'}
        plans = takeoff_plans(drawing, height, catalog, openings)
        yield {'type': 'status', 'stage': 'facts', 'message': f'Đang đọc ghi chú thông số trong {name}…'}
        fact_parts.append(_input_facts(drawing, name, allow_ai,
                                       need_plan=all(getattr(p, 'name', '') == 'Toàn bộ bản vẽ' for p in plans)))
        view = view_payload(drawing, plans, name, cad=False)
        for plan in view['plans']:
            plan['source_revision'] = source
        yield {'type': 'recognized', 'data': view}
        yield {'type': 'status', 'stage': 'rendering', 'message': f'Đang dựng nền CAD của {name}…'}
        add_cad_layers(drawing, view, plans)
        views.append(view)
    if len(views) == 1:
        view = views[0]
    else:
        # Giữ từng mặt bằng và nền CAD riêng. Tên trùng gây nhập nhằng khi liên kết với kết cấu.
        plans = [plan for v in views for plan in v['plans']]
        duplicates = [name for name, count in Counter(p['plan']['name'] for p in plans).items() if count > 1]
        if duplicates:
            raise HTTPException(422, 'Các bản kiến trúc trùng tên mặt bằng: ' + ', '.join(duplicates)
                                + '. Chọn lại bộ tệp để đối chiếu phạm vi trước khi tính.')
        view = {'file': ' + '.join(v['file'] for v in views), 'plans': plans,
                'materials': views[0]['materials'], 'families': views[0]['families'],
                'source_drawings': [{'file': v['file'], 'conventions': v.get('conventions')} for v in views]}
    structural = None
    if structural_drawings:
        params, parts = structural_parts(structural_drawings)
        parts = _column_sources(parts, structural_sources)
        structural = {**parts, 'file': ' + '.join(structural_names), 'foundations': params.foundations,
                      'lintel_height_mm': params.lintel_height_mm}
    yield {'type': 'complete', 'data': {'view': view, 'structural': structural, 'provenance': provenance,
                                        'input_facts': _merge_facts(fact_parts)}}


def _recording(events, key):
    """Ghi lại các sự kiện đã mã hóa; lưu cache ngay khi có 'complete' (luồng không tiến dần dừng ở đó)."""
    saved = []
    for event in events:
        saved.append(json.loads(_event_json(event)))
        if event['type'] == 'complete':
            analysis_cache.save(key, saved)
        yield event


def _replay(events, provenance):
    yield {'type': 'status', 'stage': 'cache',
           'message': 'Dùng lại kết quả đã phân tích cho cùng tệp, thông số và quy tắc.'}
    yield from events[:-1]
    complete = events[-1]
    yield {**complete, 'data': {**complete['data'], 'provenance': jsonable_encoder(provenance)}}


def _event_json(event):
    return json.dumps(jsonable_encoder(event), ensure_ascii=False, allow_nan=False)


def _stream(events, receipt_base=None):
    try:
        for event in events:
            line = _event_json(event)
            yield line + '\n'
            if event['type'] == 'complete' and receipt_base is not None:
                receipt = {**receipt_base, 'completed_at': datetime.now(timezone.utc).isoformat(),
                           'response_sha256': hashlib.sha256(line.encode('utf-8')).hexdigest(),
                           'response_hash_scope': 'utf8_ndjson_complete_line_without_newline'}
                yield _event_json({'type': 'receipt', 'receipt': receipt}) + '\n'
    except (DrawingError, ValueError, HTTPException) as exc:
        message = exc.detail if isinstance(exc, HTTPException) else str(exc)
        yield json.dumps({'type': 'error', 'message': message}, ensure_ascii=False) + '\n'


@router.post('/api/projects/{project_id}/analysis', response_model=None)
async def analyze_project(project_id: int, body: AnalysisRequest, request: Request, user: dict | None = Depends(require_user)):
    uid = project_files._user(user)
    request_hash = hashlib.sha256(await request.body()).hexdigest()
    def prepare():
        with Session(get_engine()) as db:
            inputs = project_files.resolve_analysis_files(db, project_id, uid, body.profile_version, body.files)
            payload = db.scalar(select(ProjectProfileRevision.payload).where(
                ProjectProfileRevision.project_id == project_id, ProjectProfileRevision.version == body.profile_version))
            names = dict(db.execute(select(ProjectFile.file_id, ProjectFile.filename).where(
                ProjectFile.project_id == project_id, ProjectFile.file_id.in_([i.file_id for i in inputs]))).all())
            return inputs, payload, names
    inputs, payload, names = await run_in_threadpool(prepare)
    profile = project_files.ProfilePayload.model_validate(payload)
    provenance = {'project_id': project_id, 'profile_version': body.profile_version,
                  'files': [i.model_dump() for i in body.files]}
    receipt_base = {**provenance, 'analysis_id': str(uuid.uuid4()),
                    'client_analysis_id': str(body.client_analysis_id) if body.client_analysis_id else None,
                    'started_at': datetime.now(timezone.utc).isoformat(), 'request_sha256': request_hash,
                    'request_hash_scope': 'utf8_http_request_body', 'receipt_version': 1}
    key = cached = None
    if analysis_cache.enabled():
        key = await run_in_threadpool(analysis_cache.make_key, provenance['files'], names,
                                      {'profile': payload, 'allow_ai': body.allow_ai})
        cached = await run_in_threadpool(analysis_cache.load, key)
    if cached:
        events = _replay(cached, provenance)
    else:
        events = _events(inputs, names, provenance, profile, body.allow_ai)
        if key:
            events = _recording(events, key)
    if body.progressive:
        return StreamingResponse(_stream(events, receipt_base), media_type='application/x-ndjson',
                                 headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
    def complete():
        for event in events:
            if event['type'] == 'complete':
                line = _event_json(event)
                receipt = {**receipt_base, 'completed_at': datetime.now(timezone.utc).isoformat(),
                           'response_sha256': hashlib.sha256(line.encode('utf-8')).hexdigest(),
                           'response_hash_scope': 'utf8_synthetic_ndjson_complete_line_without_newline'}
                return {**jsonable_encoder(event['data']), 'analysis_receipt': receipt}
    try:
        return await run_in_threadpool(complete)
    except DrawingError as exc:
        raise HTTPException(422, str(exc)) from exc
