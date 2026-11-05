"""KD07: DOCX thuyết minh đọc theo đoạn có id; PDF bị từ chối; thông số còn thiếu gom một lần."""
import asyncio
import hashlib
import io
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from optimat.api import project_analysis as api
from optimat.api import project_document_io as io_api
from optimat.drawing.ingest import UploadRejected
from optimat.rough.models import WorkItem
from optimat.rough.questions import missing_inputs

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def make_docx(paragraphs) -> bytes:
    body = ''.join(f'<w:p><w:r><w:t>{p}</w:t></w:r></w:p>' if p else '<w:p/>' for p in paragraphs)
    body += f'<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Ô bảng</w:t><w:tab/><w:t>dày 15</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
    buf = io.BytesIO()
    with ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml',
                   '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                   'wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels',
                   '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                   'officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', f'<?xml version="1.0"?><w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def test_docx_paragraphs_keep_text_and_order(tmp_path):
    raw = make_docx(['Sàn BTCT dày 100', '', 'Trát vữa XM M75 dày 15'])
    assert io_api.validate_document('thuyet_minh.docx', raw)['ext'] == '.docx'
    path = tmp_path / 'tm.docx'
    path.write_bytes(raw)
    doc = io_api.docx_paragraphs(path)
    assert doc == {'paragraphs': [{'id': 'p1', 'text': 'Sàn BTCT dày 100'}, {'id': 'p3', 'text': 'Trát vữa XM M75 dày 15'},
                                  {'id': 'p4', 'text': 'Ô bảng dày 15'}], 'truncated': False}
    assert io_api.capabilities('HO_SO', 'docx')['can_preview'] is True


def test_pdf_upload_rejected_with_clear_message():
    with pytest.raises(UploadRejected, match='Không nhận PDF'):
        io_api.validate_document('ho_so.pdf', b'%PDF-1.7 ...')


def test_docx_candidates_carry_paragraph_source(tmp_path, monkeypatch):
    path = tmp_path / 'tm.docx'
    path.write_bytes(make_docx(['Bê tông B20 (M250)']))

    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    rev = SimpleNamespace(role='HO_SO', format='docx', sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    async def run_inline(fn, *args):
        return fn(*args)
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api, 'run_in_threadpool', run_inline)
    monkeypatch.setattr(api.project_files, '_user', lambda user: 1)
    monkeypatch.setattr(api.project_files, '_project', lambda *args: None)
    monkeypatch.setattr(api.project_files, '_revision', lambda *args: (SimpleNamespace(filename='tm.docx'), rev))
    monkeypatch.setattr(api.project_files, '_verified_path', lambda revision: path)
    result = asyncio.run(api.document_candidates(1, 2, 3, 1, {'user_id': 1}))
    first = result['candidates'][0]
    assert first['kind'] == 'paragraph' and first['text'] == 'Bê tông B20 (M250)' and first['scope'] == 'unconfirmed'
    assert first['source']['paragraph'] == 'p1' and first['source']['sha256'] == rev.sha256
    path.write_bytes(b'hong')
    with pytest.raises(api.HTTPException) as exc:
        asyncio.run(api.document_candidates(1, 2, 3, 1, {'user_id': 1}))
    assert exc.value.status_code == 422


def test_missing_inputs_grouped_once_most_affected_first():
    def work(code, plan, missing):
        return WorkItem(code=code, name=code, unit='m³', plan=plan, missing=missing, status='D')
    works = [work('DAM', 'T1', ['chiều dày sàn', 'cao dầm']), work('COP_PHA', 'T1', ['chiều dày sàn']),
             work('SAN', 'T2', ['chiều dày sàn', 'chiều dày sàn']), work('XAY', 'T1', [])]
    result = missing_inputs(works)
    assert [(m.input, m.count, m.works, m.plans) for m in result] == [
        ('chiều dày sàn', 3, ['DAM', 'COP_PHA', 'SAN'], ['T1', 'T2']), ('cao dầm', 1, ['DAM'], ['T1'])]
