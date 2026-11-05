"""Dựng hai tài liệu Word từ đặc tả hiện hành và metadata 20 bảng."""
import ast
import json
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
META=json.loads((HERE/'metadata20.json').read_text(encoding='utf-8'))
FIELDS={}
old=ROOT/'outputs/database_document_20261104/build_document.py'
if old.exists():
    for node in ast.parse(old.read_text(encoding='utf-8')).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIELDS' for t in node.targets):
            FIELDS.update(ast.literal_eval(node.value))
FIELDS.update({
 'profile_revisions':'Các phiên bản thông số công trình; append qua API, giữ version, payload, người/nguồn nếu có.',
 'catalog_metadata':'Thuộc tính mở rộng của danh mục; dữ liệu tham chiếu cũ được bảo toàn trong rule_sets.',
 'kind':'Loại bản ghi theo bảng; xem miền giá trị trong CHECK/trigger.',
 'data_kind':'ACTUAL/SAMPLE/SYNTHETIC; nguồn thật không đồng nghĩa đã được kiểm chứng.',
 'input_snapshot':'Đầu vào, danh mục, quy tắc và điều kiện đã chụp. Lịch sử chuyển đổi có cờ chưa chứng minh đúng danh mục quá khứ.',
 'schema_version':'Phiên bản cấu trúc snapshot.', 'result_sha256':'SHA-256 của result theo chuẩn hóa JSON của ứng dụng; đánh dấu snapshot đã đóng.',
 'document_id':'Khóa nội bộ của bản ghi lưu trữ; khác file_id/revision_id tương thích.',
 'record_type':'file là tệp logic; revision là một phiên bản gắn đúng tệp và dự án.',
 'revision_id':'Định danh phiên bản tệp; chỉ có ở bản ghi revision.',
 'version':'Số phiên bản hoặc định danh phiên bản theo bảng; xem kiểu cột.',
 'format':'Định dạng tệp gốc, ví dụ dwg/dxf/pdf.', 'sha256':'Mã băm file nguồn.',
 'size_bytes':'Kích thước file, byte.', 'set_id':'Khóa nội bộ của bản ghi quy tắc/tham chiếu.',
 'record_key':'Khóa ghép mã hóa JSON theo PK của cấu trúc tương thích; duy nhất trong kind.',
 'payload':'Nội dung có cấu trúc; quy tắc kiểm tra phụ thuộc loại bản ghi.',
 'parameter_id':'Khóa nội bộ của thông số chi phí.', 'element_id':'Khóa cấu kiện trong một lần phân tích.',
 'analysis_id':'Liên kết tới analysis_runs.takeoff_id; giữ khóa cũ cho tương thích.',
 'element_key':'Mã cấu kiện duy nhất trong một lần phân tích; không chỉ dùng mã C1 giữa mọi tầng.',
 'level_code':'Mã tầng trong snapshot; có thể chưa xác định.',
 'geometry':'Hình học chuẩn hóa; hệ tọa độ/đơn vị được mô tả trong nguồn và snapshot.',
 'occurrences':'Các lần biểu diễn cấu kiện trên hình; không nhân số lượng cấu kiện theo số hình.',
 'relations':'Quan hệ cấu kiện trong snapshot; tầng ứng dụng kiểm nội dung/định danh.',
 'evidence_id':'Khóa bằng chứng.', 'source_ref':'Vị trí nguồn: đường dẫn JSON, handle/INSERT, bảng/ô hoặc vùng hình.',
 'raw_content':'Nội dung nguồn nguyên gốc; không tự nâng nguồn snapshot thành nguồn CAD đã kiểm.',
 'created_by':'Người tạo nếu xác định được.', 'measurement_id':'Khóa ứng viên số đo.',
 'property_code':'Đại lượng đo, ví dụ length/height/thickness.', 'value':'Giá trị chuẩn hóa; thiếu để NULL.',
 'selected':'Giá trị/ phương án đang được chọn; kiểm theo bảng.', 'method':'Cách xác định hoặc phương pháp tối ưu theo bảng.',
 'evidence_ids':'Danh sách bằng chứng; trigger kiểm tồn tại và cùng lần phân tích.',
 'item_id':'Khóa dòng công tác.', 'seq':'Thứ tự dòng trong snapshot.', 'known_part':'Phần đã biết, không thay thế tổng còn thiếu.',
 'formula':'Công thức giải thích; không thực thi chuỗi này như mã.', 'scenario_id':'Khóa phương án vật liệu.',
 'origin':'Nguồn phương án: design/user/proposed/optimized.', 'assignments':'Danh sách gán vật liệu, có thể còn chưa xác định.',
 'requirements':'Danh sách nhu cầu vật liệu có nguồn và tính đầy đủ; chưa chọn vật liệu thì có thể rỗng.',
 'catalog_snapshot':'Danh mục và định mức/cấp phối được chụp cho phương án.',
})


def clean(s):
    s=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]',lambda m:'\\x%02x'%ord(m.group()),str(s))
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',s)
    return s.replace('**','').replace('`','')


def new_doc(title,subtitle):
    d=Document();s=d.sections[0]
    s.page_width=Inches(8.5);s.page_height=Inches(11)
    s.top_margin=Inches(.7);s.bottom_margin=Inches(.65);s.left_margin=s.right_margin=Inches(.7)
    for st in d.styles:
        if st.type==1:
            st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
            for el in list(st.element.xpath('./w:pPr/w:pBdr')):el.getparent().remove(el)
    for name,size in [('Normal',11),('Title',26),('Subtitle',13),('Heading 1',17),('Heading 2',13),('Heading 3',11)]:
        st=d.styles[name];st.font.size=Pt(size);st.paragraph_format.space_after=Pt(6);st.paragraph_format.line_spacing=1.1
    hp=s.header.paragraphs[0];hp.text='OPTIMAT AI   |   DATABASE VÀ DỮ LIỆU 20 BẢNG';hp.runs[0].font.size=Pt(8)
    f=s.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    f.add_run('04/11/2026  |  Trang ').font.size=Pt(8)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
    d.add_paragraph(title,'Title');d.add_paragraph(subtitle,'Subtitle')
    d.add_paragraph('Bản cập nhật ngày 04 tháng 11 năm 2026')
    d.core_properties.title=title;d.core_properties.author='OptiMat AI'
    return d


def table(d,headers,rows,widths=None):
    n=len(headers);widths=widths or ([.42,1.12,2.14,1.55,1.87] if n==5 else [7.1/n]*n)
    t=d.add_table(rows=1,cols=n);t.autofit=False
    for col,w in zip(t.columns,widths):col.width=Inches(w)
    for c,v in zip(t.rows[0].cells,headers):c.text=clean(v)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        for c,v in zip(t.add_row().cells,row):c.text=clean(v)
    borders=OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
    t._tbl.tblPr.append(borders)
    for i,row in enumerate(t.rows):
        cant=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(cant)
        for j,c in enumerate(row.cells):
            c.width=Inches(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DDE8F0' if i==0 else 'F5F7F9' if i%2==0 else 'FFFFFF');pr.append(sh)
            mar=OxmlElement('w:tcMar')
            for side in ('top','left','bottom','right'):
                b=OxmlElement('w:'+side);b.set(qn('w:w'),'85');b.set(qn('w:type'),'dxa');mar.append(b)
            pr.append(mar)
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(2);p.paragraph_format.line_spacing=1.05
                if i==0:p.paragraph_format.keep_with_next=True
                for r in p.runs:r.font.size=Pt(9.5);r.bold=(i==0)
    d.add_paragraph('')


def markdown(d,path):
    lines=path.read_text(encoding='utf-8').splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if line.startswith('|'):
            cells=lambda x:[v.strip() for v in x.strip().strip('|').split('|')]
            headers=cells(line);i+=1;rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=cells(lines[i])
                if not all(re.fullmatch(r':?-+:?',x.replace(' ','')) for x in row):rows.append(row)
                i+=1
            if len(headers)==8 and headers[0]=='Kiểm / ID':
                table(d,['Kiểm / ID','Vấn đề cần xử lý','Hiện trạng','Phụ trách'],
                      [(r[0],r[1],r[3],r[5]) for r in rows],[.85,2.55,2.45,1.25])
                for r in rows:
                    d.add_heading(clean(r[0]+' '+r[1]),3)
                    for label,index in [('Bằng chứng đã có',2),('Việc cần bổ sung',4),('Điều kiện hoàn thành',6),('Chủ đồ án cần chốt',7)]:
                        p=d.add_paragraph();p.add_run(label+': ').bold=True;p.add_run(clean(r[index]))
            else:
                table(d,headers,rows)
            continue
        if line.startswith('# '):i+=1;continue
        if line.startswith('### '):d.add_heading(clean(line[4:]),2)
        elif line.startswith('## '):d.add_heading(clean(line[3:]),1)
        elif line.startswith('- '):d.add_paragraph(clean(line[2:]),'List Bullet')
        elif line:d.add_paragraph(clean(line))
        i+=1


db=new_doc('Thiết kế cơ sở dữ liệu OptiMat AI','20 bảng vật lý và hướng dẫn chuyển đổi dữ liệu')
db.add_paragraph('Tài liệu hiện hành thay thiết kế 45 bảng. Cấu trúc được sinh từ schema20.py; tên cũ được duy trì bằng view chuyển tiếp để các API và công cụ nhập dữ liệu tiếp tục hoạt động. Không có bản sao bảng cũ được giữ ẩn trong schema khác.')
db.add_paragraph('Giữ riêng cấu kiện, số đo, bằng chứng và dòng khối lượng. Phương án vật liệu được chọn sau; bản vẽ chưa chỉ định vật liệu vẫn có thể lưu và kiểm tra hình học.')
markdown(db,ROOT/'docs/schema/CSDL_20_BANG.md')
db.add_heading('9 Từ điển dữ liệu đầy đủ của 20 bảng',1)
db.add_paragraph(f'Metadata hiện khai báo {len(META)} bảng và {sum(len(t["columns"]) for t in META)} cột. PK là khóa chính, FK là khóa ngoại. Kiểu, khả năng NULL và liên kết dưới đây lấy từ mã nguồn; các kiểm tra JSONB và bất biến bổ sung bằng trigger trong compat20.py.')
for t in META:
    db.add_heading(t['name']+'   '+t['title'],2)
    rows=[]
    for c in t['columns']:
        meaning=c.get('comment') or FIELDS.get(c['name']) or ('Nguồn của thông số tương ứng.' if c['name'].endswith('_source') else 'Thuộc tính theo nghiệp vụ bảng; xem mô tả grain và cấu trúc snapshot.')
        if c['fk']:meaning+=' FK → '+', '.join(c['fk'])+'.'
        if c['default'] is not None:meaning+=' Default DB: '+repr(c['default'])+'.'
        rows.append((c['name'],c['type']+(' / PK' if c['pk'] else ''),'Có' if c['nullable'] else 'Không',meaning))
    table(db,['Cột','Kiểu và khóa','NULL','Ý nghĩa và liên kết'],rows,[1.7,1.35,.5,3.55])
    if t['checks']:
        db.add_paragraph('CHECK khai báo:')
        for c in t['checks']:db.add_paragraph(clean(c))
db.add_heading('10 Quan hệ FK vật lý',1)
links=[(t['name'],c['name'],f) for t in META for c in t['columns'] for f in c['fk']]
table(db,['Bảng chứa FK','Cột','Tham chiếu'],links,[2.2,1.8,3.1])
db.add_paragraph('Ngoài FK, trigger kiểm quan hệ cùng dự án/lần phân tích, các evidence_id trong JSONB và các gán vật liệu trong scenario. Các mảng occurrences/relations còn cần kiểm ở ứng dụng; xem giới hạn tại mục 5.')
db.add_heading('11 Nguồn đối chiếu và kiểm thử',1)
db.add_paragraph('Nguồn: db/schema20.py, db/compat20.py, db/migrate20.py, db/analysis20.py, db/optimization20.py, các generator SQL và tests/test_schema20.py. Báo cáo migration và backup được giữ riêng trong backups/schema20, không phát tán trong tài liệu.')
db.add_paragraph('Tình trạng áp dụng và số ca kiểm thử đạt được ghi trong báo cáo bàn giao dự án. Có script và metadata không đồng nghĩa tất cả dữ liệu nghiệp vụ đã đầy đủ; kế hoạch dữ liệu sáu tuần là tài liệu đi kèm.')
db.save(HERE/'OptiMat_AI_CSDL_20_bang.docx')

plan=new_doc('Kế hoạch hoàn thiện dữ liệu OptiMat AI','Sáu tuần và 28 tình huống kiểm chứng trên hệ thống 20 bảng')
plan.add_paragraph('Kế hoạch này xác định dữ liệu phải thu thập, người chịu trách nhiệm theo vai trò, đầu ra từng tuần và điều kiện nghiệm thu. Các mục tiêu thu thập là đề xuất triển khai, không phải tuyên bố dữ liệu đã có hoặc chất lượng đã đạt.')
markdown(plan,ROOT/'docs/KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md')
plan.save(HERE/'OptiMat_AI_Ke_hoach_hoan_thien_data.docx')
print(json.dumps({'files':['OptiMat_AI_CSDL_20_bang.docx','OptiMat_AI_Ke_hoach_hoan_thien_data.docx'],'tables':len(META),'columns':sum(len(t['columns']) for t in META)},ensure_ascii=True))
