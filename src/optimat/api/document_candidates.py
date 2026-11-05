"""Trích ứng viên bảng dự toán từ sheet đã xem, không tính lại hay ghi dữ liệu."""
import re
import unicodedata

from .project_document_io import docx_paragraphs, xls_preview, xlsx_preview


def _key(value):
    text = unicodedata.normalize('NFKD', str(value or '').lower().replace('đ', 'd'))
    return re.sub(r'\s+', ' ', ''.join(c for c in text if not unicodedata.combining(c))).strip()


_HEADERS = {
    'work': {'cong tac', 'ten cong tac', 'ten cong viec', 'noi dung cong viec'},
    'unit': {'don vi', 'dvt', 'don vi tinh'},
    'quantity': {'khoi luong', 'so luong'},
    'unit_price': {'don gia', 'don gia du toan'},
}


def _column(index):
    result = ''
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def spreadsheet_candidates(path, format, sheet, source):
    table = xls_preview(path, sheet) if format == 'xls' else xlsx_preview(path, sheet)
    rows = table['rows']
    headers = None
    for position, row in enumerate(rows):
        found = {}
        for i, cell in enumerate(row):
            key = _key(cell)
            for field, aliases in _HEADERS.items():
                if key in aliases:
                    if field in found:
                        found[field] = None
                    else:
                        found[field] = i
        if found.get('work') is not None and found.get('quantity') is not None:
            headers = (position, found)
            break
    candidates = []
    if headers:
        start, fields = headers
        for row_no, row in enumerate(rows[start + 1:], start + 2):
            def value(field):
                i = fields.get(field)
                return None if i is None or i >= len(row) or row[i] in (None, '') else str(row[i])
            work, quantity = value('work'), value('quantity')
            if not work and not quantity:
                continue
            values = {field: value(field) for field in _HEADERS}
            locations = {field: f'{_column(i)}{row_no}' for field, i in fields.items() if i is not None}
            candidates.append({'kind': 'work_row', 'fields': values, 'scope': 'unconfirmed',
                               'missing': [field for field in ('work', 'unit', 'quantity') if values[field] is None],
                               'price_kind': ('estimate_reference' if source['role'] == 'TIEN_LUONG'
                                              else 'document_price_unclassified') if values['unit_price'] else None,
                               'source': {**source, 'sheet': table['sheet_name'], 'row': row_no, 'cells': locations},
                               'raw_cells': [str(v) if v is not None else None for v in row]})
    return {'status': 'candidates' if headers else 'header_not_found', 'candidates': candidates,
            'source': source, 'sheet': table['sheet_name'], 'sheet_count': len(table['sheets']),
            'truncated': table['truncated'], 'cached_values_only': True,
            'notice': 'Chỉ đọc tối đa 100 dòng và 30 cột của sheet; công thức dùng giá trị lưu sẵn, không tính lại. '
                      'Chưa xác định dòng tổng hay phần góp, không tự cộng. Ứng viên chưa xác nhận; '
                      'đơn giá tài liệu không phải báo giá mua.'}


def docx_candidates(path, source):
    """Đoạn văn thuyết minh/yêu cầu (DOCX, tùy chọn) làm ứng viên có nguồn; chưa trích số, chưa xác nhận.
    Bước trích thông số (KD03) đọc các đoạn này theo id."""
    doc = docx_paragraphs(path)
    candidates = [{'kind': 'paragraph', 'text': p['text'], 'scope': 'unconfirmed',
                   'source': {**source, 'paragraph': p['id']}} for p in doc['paragraphs']]
    return {'status': 'candidates' if candidates else 'empty', 'candidates': candidates, 'source': source,
            'truncated': doc['truncated'],
            'notice': 'Đoạn văn giữ nguyên chữ gốc, chưa trích thông số và chưa xác nhận; tài liệu này là tùy chọn.'}
