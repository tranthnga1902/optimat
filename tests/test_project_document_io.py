import io
import hashlib
import subprocess
from zipfile import ZipFile

import pytest

from optimat.api import project_document_io as io_api
from optimat.drawing.ingest import UploadRejected


def test_pdf_validate_and_render_page(tmp_path):
    pdfium = pytest.importorskip('pypdfium2')
    doc = pdfium.PdfDocument.new()
    page = doc.new_page(300, 400)
    page.close()
    data = io.BytesIO()
    doc.save(data)
    doc.close()
    raw = data.getvalue()
    with pytest.raises(UploadRejected, match='Không nhận PDF'):   # R1: không nhận PDF mới
        io_api.validate_document('test.pdf', raw)
    path = tmp_path / 'sample.pdf'   # PDF đã lưu trước R1 vẫn xem được
    path.write_bytes(raw)
    png, pages = io_api.pdf_preview(path, 1)
    assert pages == 1 and png.startswith(b'\x89PNG\r\n\x1a\n')
    with pytest.raises(ValueError):
        io_api.pdf_preview(path, 2)


def test_xlsx_validate_and_preview(tmp_path):
    from openpyxl import Workbook
    book = Workbook()
    book.active.title = 'Tien luong'
    book.active.append(['Cot', 12])
    data = io.BytesIO()
    book.save(data)
    raw = data.getvalue()
    assert io_api.validate_document('bang.xlsx', raw)['ext'] == '.xlsx'
    path = tmp_path / 'bang.xlsx'
    path.write_bytes(raw)
    out = io_api.xlsx_preview(path, 1)
    assert out['sheet_name'] == 'Tien luong' and out['rows'] == [['Cot', '12']]


def test_reject_wrong_format_and_legacy():
    for name, content in [('fake.pdf', b'%PDF-broken'), ('fake.docx', b'not zip'),
                          ('legacy.xls', b'content'), ('legacy.doc', b'content')]:
        with pytest.raises(UploadRejected):
            io_api.validate_document(name, content)


def test_docx_rejects_macro_and_invalid_xml():
    for content, macro in [(b'<not-valid', False), (b'<document/>', True)]:
        buf = io.BytesIO()
        with ZipFile(buf, 'w') as z:
            z.writestr('[Content_Types].xml', '<Types>wordprocessingml.document.main+xml</Types>')
            z.writestr('word/document.xml', content)
            if macro:
                z.writestr('word/vbaProject.bin', b'macro')
        with pytest.raises(UploadRejected):
            io_api.validate_document('doc.docx', buf.getvalue())


def office_package(ext, *, types_root=None, override_part=None, override_type=None,
                   rel_root=None, rel_target=None, rel_mode='Internal', main_root=None, include_rels=True):
    is_doc = ext == 'docx'
    part = 'word/document.xml' if is_doc else 'xl/workbook.xml'
    typ = ('application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml' if is_doc else
           'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
    main_ns = ('http://schemas.openxmlformats.org/wordprocessingml/2006/main' if is_doc else
               'http://schemas.openxmlformats.org/spreadsheetml/2006/main')
    root = 'document' if is_doc else 'workbook'
    types = (f'<Types xmlns="{types_root or io_api.CONTENT_TYPES_NS}">'
             f'<Override PartName="{override_part or "/" + part}" ContentType="{override_type or typ}"/></Types>')
    rels = (f'<Relationships xmlns="{rel_root or io_api.REL_NS}">'
            f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            f'Target="{rel_target or part}" TargetMode="{rel_mode}"/></Relationships>')
    content = main_root or f'<{root} xmlns="{main_ns}"/>'
    buf = io.BytesIO()
    with ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', types)
        if include_rels:
            z.writestr('_rels/.rels', rels)
        z.writestr(part, content)
    return buf.getvalue()


def test_minimal_docx_package_is_accepted():
    assert io_api.validate_document('project.docx', office_package('docx'))['ext'] == '.docx'


@pytest.mark.parametrize('ext', ['docx', 'xlsx'])
@pytest.mark.parametrize('mutation', [
    {'types_root': 'urn:fake'}, {'override_part': '/fake.xml'},
    {'override_type': 'text/wordprocessingml.document.main+xml'},
    {'rel_root': 'urn:fake'}, {'rel_target': 'elsewhere.xml'},
    {'rel_mode': 'External'}, {'main_root': '<document/>'}, {'include_rels': False},
])
def test_office_package_rejects_fake_parts(ext, mutation):
    with pytest.raises(UploadRejected):
        io_api.validate_document('project.' + ext, office_package(ext, **mutation))


def test_capability_separates_role_and_format():
    assert io_api.capabilities('KT', 'pdf')['can_analyze_cad'] is False
    assert io_api.capabilities('KT', 'dxf')['can_analyze_cad'] is True
    assert io_api.capabilities('TIEN_LUONG', 'dxf')['can_analyze_cad'] is False
    assert io_api.capabilities('HO_SO', 'docx')['can_preview'] is True   # KD07: xem DOCX theo đoạn


def test_m1_xls_copy_validated_and_sheet_preview():
    from pathlib import Path
    import xlrd
    path = Path(__file__).resolve().parents[1] / 'tmp/m1_xls_fixture_20261104.xls'
    if not path.exists():
        pytest.skip('Cần bản sao fixture M1 được phép và khớp hash.')
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '9312133c01b959194447ed90b8fdb0b889b98fb7bb5cc4a078a6da2ffe0f1ced'
    result = io_api.validate_document('M1.xls', data)
    assert result['sha256'] == hashlib.sha256(data).hexdigest()
    out = io_api.xls_preview(path, 2)
    assert out['sheet_name'] == 'Tien luong' and out['cached_values_only'] is True
    assert len(out['rows']) <= io_api.PREVIEW_ROWS and all(len(row) <= io_api.PREVIEW_COLS for row in out['rows'])
    assert io_api.xls_preview(path, 1)['sheet'] == 1
    with pytest.raises(ValueError):
        io_api.xls_preview(path, len(out['sheets']) + 1)
    book = xlrd.open_workbook(file_contents=data, on_demand=True)
    try:
        sheet = book.sheet_by_index(1)
        for r in range(min(sheet.nrows, 100)):
            for c in range(min(sheet.ncols, 30)):
                cell = sheet.cell(r, c)
                if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                    assert out['rows'][r][c] is None
                elif cell.ctype == xlrd.XL_CELL_NUMBER:
                    assert out['rows'][r][c] == str(cell.value)
                elif cell.ctype == xlrd.XL_CELL_TEXT:
                    assert out['rows'][r][c] == str(cell.value)[:500]
    finally:
        book.release_resources()


@pytest.mark.parametrize('sheet', [0, -1])
def test_xls_preview_rejects_nonpositive_before_read(sheet, tmp_path):
    with pytest.raises(ValueError):
        io_api.xls_preview(tmp_path / 'missing.xls', sheet)


def test_xls_rejects_fake_ole_wrong_type_and_oversize():
    for data in (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\0' * 512,
                 office_package('docx'), b'a' * (io_api.MAX_XLS_BYTES + 1)):
        with pytest.raises(UploadRejected):
            io_api.validate_document('bad.xls', data)


def test_xls_missing_dependencies_and_timeout(monkeypatch):
    monkeypatch.setattr(io_api, '_available', lambda _: False)
    assert not io_api.capabilities('TIEN_LUONG', 'xls')['can_preview']
    with pytest.raises(UploadRejected):
        io_api.validate_document('bad.xls', b'xls')
    monkeypatch.setattr(io_api, '_available', lambda _: True)
    def timed_out(*args, **kwargs):
        raise subprocess.TimeoutExpired('reader', 1)
    monkeypatch.setattr(io_api.subprocess, 'run', timed_out)
    with pytest.raises(UploadRejected):
        io_api.validate_document('timeout.xls', b'xls')


def test_xls_reader_failure_is_rejected(monkeypatch):
    monkeypatch.setattr(io_api, '_available', lambda _: True)
    monkeypatch.setattr(io_api.subprocess, 'run', lambda *args, **kwargs: type('Result', (), {
        'returncode': 1, 'stdout': b''})())
    with pytest.raises(UploadRejected):
        io_api.validate_document('locked.xls', b'xls')


def test_xls_is_not_cad_analysis():
    caps = io_api.capabilities('TIEN_LUONG', 'xls')
    assert caps['can_preview'] is True and caps['can_analyze_cad'] is False


def test_xls_values_keep_zero_blank_text_and_dates():
    from types import SimpleNamespace
    import xlrd
    convert = lambda kind, value: io_api._xls_cell_value(SimpleNamespace(ctype=kind, value=value), xlrd, 0)
    assert convert(xlrd.XL_CELL_NUMBER, 0.0) == '0.0'
    assert convert(xlrd.XL_CELL_EMPTY, '') is None
    assert convert(xlrd.XL_CELL_TEXT, 'chưa rõ') == 'chưa rõ'
    assert convert(xlrd.XL_CELL_DATE, 2.0).startswith('1900-01-02')
    assert convert(xlrd.XL_CELL_ERROR, 7)