"""Staging only: bounded, literal document-text candidates; no approval or DB writes."""
import hashlib
import io
import re
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

MAX_BYTES = 20 * 1024 * 1024
MAX_XML_BYTES = 8 * 1024 * 1024
MAX_PAGES = 100
MAX_CHARS = 2_000_000
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
LABELS = {
    'địa điểm': 'address', 'địa điểm xây dựng': 'address', 'địa chỉ': 'address',
    'dia diem': 'address', 'dia chi': 'address',
    'số tầng': 'floor_count', 'so tang': 'floor_count',
    'bê tông': 'concrete_spec', 'cấp bê tông': 'concrete_spec',
    'mác bê tông': 'concrete_spec', 'be tong': 'concrete_spec',
    'thép': 'steel_spec', 'cốt thép': 'steel_spec', 'thep': 'steel_spec',
    'yêu cầu vật liệu': 'material_requirement', 'yeu cau vat lieu': 'material_requirement',
}


def text_of(node):
    return ''.join(t.text or '' for t in node.iter(W + 't'))


def docx_units(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        matches = [x for x in archive.infolist() if x.filename == 'word/document.xml']
        if len(matches) != 1 or matches[0].file_size > MAX_XML_BYTES:
            raise ValueError('Missing/duplicate/oversized document.xml')
        xml = archive.read(matches[0])
    if b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
        raise ValueError('DTD and entities are not supported')
    body = ET.fromstring(xml).find(W + 'body')
    if body is None:
        raise ValueError('Missing DOCX body')
    units = []
    paragraph = table = 0
    for child in body:
        if child.tag == W + 'p':
            paragraph += 1
            units.append((text_of(child), dict(paragraph=paragraph, page=None)))
        elif child.tag == W + 'tbl':
            table += 1
            for ri, row in enumerate(child.findall(W + 'tr'), 1):
                cells = row.findall(W + 'tc')
                for ci, cell in enumerate(cells, 1):
                    raw = '\n'.join(text_of(p) for p in cell.findall(W + 'p'))
                    units.append((raw, dict(table=table, row=ri, cell=ci, page=None)))
                if len(cells) == 2:
                    label, value = (text_of(c).strip() for c in cells)
                    # Adjacent cells are joined only when the first is an exact known label.
                    if unicodedata.normalize('NFC', label).casefold().rstrip(':：').strip() in LABELS:
                        units.append((label.rstrip(':：') + ': ' + value,
                                      dict(table=table, row=ri, label_cell=1, value_cell=2, page=None,
                                           label_raw=label, value_raw=value)))
    return units


def pdf_units(data):
    import pypdfium2 as pdfium
    units = []
    with pdfium.PdfDocument(data) as doc:
        if len(doc) > MAX_PAGES:
            raise ValueError('PDF exceeds page limit')
        size = 0
        for index in range(len(doc)):
            with doc[index] as page, page.get_textpage() as textpage:
                raw = textpage.get_text_range()
            size += len(raw)
            if size > MAX_CHARS:
                raise ValueError('Text exceeds character limit')
            units.append((raw, dict(page=index + 1)))
    return units


def extract_profile(data, suffix, filename=''):
    """Return unselected candidates with literal evidence; text is never instructions."""
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError('Expected bytes within20MiB')
    suffix = suffix.lower().lstrip('.')
    if suffix not in ('pdf', 'docx'):
        raise ValueError('Only PDF text and DOCX are supported')
    units = pdf_units(data) if suffix == 'pdf' else docx_units(data)
    if sum(len(raw) for raw, _ in units) > MAX_CHARS:
        raise ValueError('Text exceeds character limit')
    candidates = []
    for raw, location in units:
        for line_number, line in enumerate(raw.splitlines(), 1):
            # Exact label at line start; no execution, tools, evaluation or inferred defaults.
            match = re.fullmatch(r'\s*([^:：\n]{1,80})\s*[:：]\s*(\S.*?)\s*', line)
            if not match:
                continue
            field = LABELS.get(unicodedata.normalize('NFC', match[1]).casefold().strip())
            if field is None:
                continue
            value = match[2]
            unit = None
            status = 'needs_confirmation'
            if field == 'floor_count':
                floor = re.fullmatch(r'([1-9]\d?)\s*(?:tầng|tang)?', value, re.I)
                if floor:
                    value, unit = int(floor[1]), 'tầng'
                else:
                    value, status = None, 'unparsed'
            candidates.append(dict(candidate_id=f'candidate-{len(candidates)+1}', field=field,
                                   value=value, unit=unit, raw_value=match[2], raw_text=line,
                                   location=dict(location, line=line_number),
                                   selected=False, human_approval=False, status=status))
    for candidate in candidates:
        alternatives = {str(c['value']).casefold() for c in candidates
                        if c['field'] == candidate['field'] and c['value'] is not None}
        if len(alternatives) > 1:
            candidate['conflict_group'] = candidate['field']
            if candidate['value'] is not None:
                candidate['status'] = 'conflicting_candidates'
    has_text = any(raw.strip() for raw, _ in units)
    return dict(schema_version='profile-text-staging-v1', filename=filename,
                sha256=hashlib.sha256(data).hexdigest(), candidates=candidates,
                status='needs_confirmation' if candidates else 'no_labeled_fields' if has_text else 'no_text_layer_or_empty',
                human_approval=False, ocr_used=False, partial=False,
                limitations=['Literal labels only; no header/footer/nested-table extraction for DOCX.',
                             'DOCX paragraph/cell references are logical positions, not rendered page numbers.',
                             'PDF text reading order may differ from visual layout; no spatial table inference.',
                             'Requirements are untrusted data, never executable commands; no material catalog mapping.',
                             'Floor count is a candidate, not proof of project scope or new construction.'])
