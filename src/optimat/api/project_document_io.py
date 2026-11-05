"""Kiểm định hồ sơ và xem trước giới hạn; không nhận dạng hay chạy macro."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
import os
import subprocess
import sys
from itertools import islice
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .. import config
from ..drawing.ingest import UploadRejected, check_upload

MAX_EXPANDED = 100 * 1024 * 1024
MAX_ENTRIES = 2000
MAX_XLS_BYTES = 10 * 1024 * 1024
MAX_XLS_STREAMS = 500
MAX_XLS_SHEETS = 128
XLS_TIMEOUT_SECONDS = 15
PREVIEW_ROWS = 1000  # bảng tiên lượng nhà ở thường 200-500 dòng
PREVIEW_COLS = 30
CONTENT_TYPES_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
OFFICE_REL = {'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument',
              'http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument'}
MAIN_ROOTS = {
    '.docx': {'{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document',
              '{http://purl.oclc.org/ooxml/wordprocessingml/main}document'},
    '.xlsx': {'{http://schemas.openxmlformats.org/spreadsheetml/2006/main}workbook',
              '{http://purl.oclc.org/ooxml/spreadsheetml/main}workbook'},
}


def _available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _safe_xml(data: bytes):
    if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('XML có khai báo hoặc mã hóa không được hỗ trợ')
    return ElementTree.fromstring(data)


def validate_document(name: str, data: bytes, mime: str | None = None) -> dict:
    ext = Path(name).suffix.lower()
    if ext in {'.dwg', '.dxf'}:
        return check_upload(name, data, mime)
    if ext == '.doc':
        raise UploadRejected('Chưa hỗ trợ kiểm định .doc; hãy lưu thành .docx.')
    if ext == '.pdf':
        # Ràng buộc R1 (05/11/2026): chỉ nhận dạng trích xuất trực tiếp được; tệp PDF đã lưu trước vẫn tải/xem được.
        raise UploadRejected('Không nhận PDF. Hãy tải bản CAD (DWG/DXF), dự toán XLS/XLSX hoặc thuyết minh DOCX.')
    if ext not in {'.docx', '.xlsx', '.xls'}:
        raise UploadRejected('Định dạng tệp chưa được hỗ trợ.')
    if not data or len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise UploadRejected('Tệp rỗng hoặc vượt giới hạn dung lượng.')
    if ext == '.xls':
        try:
            _xls_call(data, 0)
        except (ValueError, OSError) as exc:
            raise UploadRejected('Không đọc được XLS: tệp sai định dạng, bị khóa, quá lớn hoặc vượt thời gian xử lý.') from exc
    else:
        try:
            with ZipFile(io.BytesIO(data)) as z:
                entries = z.infolist()
                if len(entries) > MAX_ENTRIES or sum(i.file_size for i in entries) > MAX_EXPANDED:
                    raise ValueError('Container quá lớn')
                names = [i.filename for i in entries]
                if len(set(names)) != len(names) or any(i.flag_bits & 1 or i.filename.startswith('/') or
                        '..' in i.filename.replace('\\', '/').split('/') or
                        (i.file_size > 1024 * 1024 and i.file_size > 200 * max(i.compress_size, 1)) for i in entries):
                    raise ValueError('Container không an toàn')
                if any(n.lower().endswith('vbaproject.bin') for n in names):
                    raise ValueError('Không nhận tệp chứa macro')
                part = 'word/document.xml' if ext == '.docx' else 'xl/workbook.xml'
                content_type = ('application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
                                if ext == '.docx' else
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
                if '[Content_Types].xml' not in names or '_rels/.rels' not in names or part not in names:
                    raise ValueError('Thiếu cấu trúc OOXML')
                if (z.getinfo('[Content_Types].xml').file_size > 1024 * 1024 or
                    z.getinfo('_rels/.rels').file_size > 1024 * 1024 or z.getinfo(part).file_size > 10 * 1024 * 1024):
                    raise ValueError('XML quá lớn')
                types = _safe_xml(z.read('[Content_Types].xml'))
                rels = _safe_xml(z.read('_rels/.rels'))
                content = _safe_xml(z.read(part))
                if types.tag != f'{{{CONTENT_TYPES_NS}}}Types' or rels.tag != f'{{{REL_NS}}}Relationships':
                    raise ValueError('Namespace hoặc root OOXML không hợp lệ')
                overrides = [node for node in types if node.tag == f'{{{CONTENT_TYPES_NS}}}Override'
                             and node.get('PartName') == '/' + part]
                if len(overrides) != 1 or overrides[0].get('ContentType') != content_type:
                    raise ValueError('Kiểu main part không khớp')
                links = [node for node in rels if node.tag == f'{{{REL_NS}}}Relationship'
                         and node.get('Type') in OFFICE_REL]
                if (len(links) != 1 or links[0].get('TargetMode', 'Internal') != 'Internal'
                        or links[0].get('Target', '').lstrip('/') != part or content.tag not in MAIN_ROOTS[ext]):
                    raise ValueError('Quan hệ hoặc root main part không hợp lệ')
                if z.testzip() is not None:
                    raise ValueError('Dữ liệu ZIP hỏng')
        except (BadZipFile, OSError, ValueError, KeyError, RuntimeError, ElementTree.ParseError) as exc:
            raise UploadRejected('Tệp Office sai định dạng, bị khóa, hỏng hoặc vượt giới hạn an toàn.') from exc
    return {'name': name, 'ext': ext, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MAX_DOCX_PARAGRAPHS = 2000


def docx_paragraphs(path: Path) -> dict:
    """Đoạn văn của DOCX theo thứ tự (cả ô bảng), id = số thứ tự w:p trong thân; chữ giữ nguyên, không suy số.
    Tệp đã qua validate_document khi tải lên; ở đây vẫn đọc XML an toàn (_safe_xml)."""
    with ZipFile(path) as z:
        if z.getinfo('word/document.xml').file_size > 10 * 1024 * 1024:
            raise ValueError('XML quá lớn')
        root = _safe_xml(z.read('word/document.xml'))
    paragraphs, index = [], 0
    for p in root.iter(f'{W_NS}p'):
        index += 1
        text = ''.join((t.text or '') if t.tag == f'{W_NS}t' else ' ' for t in p.iter()
                       if t.tag in (f'{W_NS}t', f'{W_NS}tab')).strip()
        if text:
            paragraphs.append({'id': f'p{index}', 'text': text})
        if len(paragraphs) >= MAX_DOCX_PARAGRAPHS:
            return {'paragraphs': paragraphs, 'truncated': True}
    return {'paragraphs': paragraphs, 'truncated': False}


def capabilities(role: str, format: str) -> dict:
    preview = (format in {'dxf', 'dwg'} or (format == 'pdf' and _available('pypdfium2')) or
               (format == 'xlsx' and _available('openpyxl')) or format == 'docx' or
               (format == 'xls' and _available('olefile') and _available('xlrd')))
    analysis = role in {'KT', 'KC'} and format in {'dxf', 'dwg'}
    return {'storage_status': 'stored', 'can_download': True, 'can_preview': preview,
            'preview_reason': None if preview else 'Chưa hỗ trợ xem trước định dạng này; có thể tải bản gốc.',
            'can_analyze_cad': analysis,
            'analysis_reason': None if analysis else 'Tệp này không hỗ trợ bóc hình học CAD với vai trò hiện tại.'}


def pdf_preview(path: Path, page: int) -> tuple[bytes, int]:
    import pypdfium2 as pdfium
    document = pdfium.PdfDocument(str(path))
    try:
        pages = len(document)
        if page < 1 or page > pages:
            raise ValueError('Trang ngoài phạm vi tài liệu.')
        selected = document[page - 1]
        try:
            width, height = selected.get_size()
            if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
                raise ValueError('Kích thước trang không hợp lệ.')
            scale = min(1.5, 2000 / width, 2000 / height)
            bitmap = selected.render(scale=scale)
            try:
                out = io.BytesIO()
                bitmap.to_pil().save(out, format='PNG')
                return out.getvalue(), pages
            finally:
                bitmap.close()
        finally:
            selected.close()
    finally:
        document.close()


def xlsx_preview(path: Path, sheet: int) -> dict:
    from openpyxl import load_workbook
    book = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    try:
        names = book.sheetnames
        if sheet < 1 or sheet > len(names):
            raise ValueError('Sheet ngoài phạm vi tài liệu.')
        ws = book[names[sheet - 1]]
        # Không tin max_row/max_column: file sinh bằng thư viện ngoài thường thiếu thẻ dimension (None -> chỉ đọc 1 ô).
        ws.reset_dimensions()
        raw = list(islice(ws.iter_rows(values_only=True), PREVIEW_ROWS + 1))
        rows = [[None if v is None else str(v)[:500] for v in row[:PREVIEW_COLS]] for row in raw[:PREVIEW_ROWS]]
        return {'sheets': names, 'sheet': sheet, 'sheet_name': ws.title, 'rows': rows,
                'truncated': len(raw) > PREVIEW_ROWS or any(len(r) > PREVIEW_COLS for r in raw)}
    finally:
        book.close()


def _xls_call(data: bytes, sheet: int) -> dict:
    if not data or len(data) > MAX_XLS_BYTES:
        raise ValueError('Tệp XLS rỗng hoặc vượt 10 MB.')
    if not _available('olefile') or not _available('xlrd'):
        raise ValueError('Máy chủ thiếu bộ đọc XLS.')
    root = str(Path(__file__).resolve().parents[2])
    code = ('import sys;sys.path.insert(0,sys.argv[1]);'
            'from optimat.api.project_document_io import _xls_worker;_xls_worker()')
    try:
        result = subprocess.run([sys.executable, '-c', code, root, str(sheet)], input=data,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=XLS_TIMEOUT_SECONDS, check=False,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'})
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Đọc XLS quá thời gian cho phép.') from exc
    if result.returncode or len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError('Không đọc được cấu trúc XLS.')
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Không đọc được kết quả XLS.') from exc


def _xls_worker() -> None:
    """Tiến trình con chỉ đọc dữ liệu; giới hạn kích thước và thời gian ở tiến trình gọi."""
    try:
        import olefile
        import xlrd
        data = sys.stdin.buffer.read(MAX_XLS_BYTES + 1)
        sheet = int(sys.argv[2])
        if not data or len(data) > MAX_XLS_BYTES or not olefile.isOleFile(io.BytesIO(data)):
            raise ValueError('Không phải OLE.')
        with olefile.OleFileIO(io.BytesIO(data), raise_defects=olefile.DEFECT_INCORRECT) as ole:
            streams = ole.listdir(streams=True, storages=False)
            if (len(streams) > MAX_XLS_STREAMS or ole.exists('WordDocument') or
                    sum(ole.get_size(s) for s in streams) > MAX_XLS_BYTES or
                    not (ole.exists('Workbook') or ole.exists('Book'))):
                raise ValueError('Cấu trúc XLS không hợp lệ.')
        book = xlrd.open_workbook(file_contents=data, on_demand=True)
        try:
            names = book.sheet_names()
            if not names or len(names) > MAX_XLS_SHEETS or sheet < 0 or sheet > len(names):
                raise ValueError('Số sheet không hợp lệ.')
            # Kiểm ít nhất một sheet thật cả khi chỉ kiểm định tệp.
            ws = book.sheet_by_index(max(sheet - 1, 0))
            rows = []
            if sheet:
                for r in range(min(ws.nrows, PREVIEW_ROWS)):
                    row = []
                    for c in range(min(ws.ncols, PREVIEW_COLS)):
                        cell = ws.cell(r, c)
                        row.append(_xls_cell_value(cell, xlrd, book.datemode))
                    rows.append(row)
            result = {'sheets': names, 'sheet': sheet, 'sheet_name': ws.name, 'rows': rows,
                      'truncated': ws.nrows > PREVIEW_ROWS or ws.ncols > PREVIEW_COLS, 'cached_values_only': True,
                      'notice': 'Giá trị công thức là giá trị lưu sẵn; chưa tính lại. Định dạng bảng có thể không giữ đầy đủ.'}
            sys.stdout.write(json.dumps(result, ensure_ascii=False, allow_nan=False))
        finally:
            book.release_resources()
    except Exception:
        sys.exit(1)


def xls_preview(path: Path, sheet: int) -> dict:
    if sheet < 1:
        raise ValueError('Số sheet phải từ 1.')
    return _xls_call(path.read_bytes(), sheet)


def _xls_cell_value(cell, xlrd, datemode: int):
    if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
        return None
    if cell.ctype == xlrd.XL_CELL_ERROR:
        return xlrd.error_text_from_code.get(cell.value, '#LỖI')
    if cell.ctype == xlrd.XL_CELL_BOOLEAN:
        re