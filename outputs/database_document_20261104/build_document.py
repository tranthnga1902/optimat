from pathlib import Path
import json, re, zipfile, io, hashlib, ast
from xml.etree import ElementTree as ET
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
META=json.loads((HERE/'schema_metadata.json').read_text(encoding='utf-8'))
BY={t['name']:t for t in META}
ZIP=Path('C:/Users/Admin/Downloads/drive-download-20261104T085129Z-1-001.zip')
OUT=HERE/'OptiMat_AI_Tai_lieu_database_toan_he_thong.docx'
doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.72);sec.bottom_margin=Inches(.68)
sec.left_margin=sec.right_margin=Inches(.72)
for name in ['Normal','Body Text','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
    st=doc.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
    st.font.size=Pt(11)
    st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.line_spacing=1.12
doc.styles['Title'].font.size=Pt(27)
doc.styles['Subtitle'].font.size=Pt(13)
for st in doc.styles:
    if st.type==1:
        for node in list(st.element.xpath('./w:pPr/w:pBdr')):node.getparent().remove(node)
        if st.name=='Caption':st.font.color.rgb=RGBColor(0,0,0)
for name,size in [('Heading 1',17),('Heading 2',13),('Heading 3',11)]:
    doc.styles[name].font.size=Pt(size);doc.styles[name].font.bold=True
    doc.styles[name].paragraph_format.space_before=Pt(12)
header=sec.header.paragraphs[0];header.text='OPTIMAT AI   |   TÀI LIỆU THIẾT KẾ DỮ LIỆU'
header.style='Normal';header.runs[0].font.size=Pt(8)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Thiết kế đề xuất  •  04/11/2026  |  Trang ').font.size=Pt(8)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

def clean(s):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]',lambda m:'\\x%02x'%ord(m.group()),str(s))
def p(s,style=None):
    para=doc.add_paragraph(clean(s),style)
    if str(s).startswith(('Grain:','Một dòng là')):para.paragraph_format.keep_with_next=True
    return para
def h(s,level=1):return doc.add_heading(s,level)
def bullets(items):
    for x in items:p(x,'List Bullet')
def table(headers,rows,widths=None):
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    if widths:
        for col,w in zip(t.columns,widths):col.width=Inches(w)
    for c,s in zip(t.rows[0].cells,headers):c.text=str(s)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        cells=t.add_row().cells
        for c,s in zip(cells,row):c.text=clean(s if s is not None else '—')
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        x=OxmlElement('w:'+edge);x.set(qn('w:val'),'single');x.set(qn('w:sz'),'4');x.set(qn('w:color'),'D9D9D9');borders.append(x)
    t._tbl.tblPr.append(borders)
    for ri,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
        for ci,c in enumerate(row.cells):
            if widths:c.width=Inches(widths[ci])
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr=c._tc.get_or_add_tcPr();m=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                z=OxmlElement('w:'+side);z.set(qn('w:w'),'85');z.set(qn('w:type'),'dxa');m.append(z)
            tcpr.append(m)
            fill='DDE8F0' if ri==0 else ('F5F7F9' if ri%2==0 else 'FFFFFF')
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),fill);tcpr.append(sh)
            for para in c.paragraphs:
                para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=1.05
                if ri==0:para.paragraph_format.keep_with_next=True
                for r in para.runs:r.font.size=Pt(9);r.bold=(ri==0)
    p('')
    return t

PURPOSE={
'users':'Một dòng là một tài khoản đăng nhập; quản lý vai trò và trạng thái hoạt động.',
'projects':'Một dòng là một công trình thuộc một người dùng; chứa vị trí và các ràng buộc/thông số cấp dự án.',
'project_files':'Một dòng là một file đã đăng ký cho một công trình; nội dung nhị phân nằm ở stored_path.',
'takeoff_results':'Một dòng là một kết quả đo bóc được lưu. JSONB chứa kết quả và đầu vào đã xác nhận; có luồng tường và phần thô.',
'optimization_runs':'Một dòng là một lần tối ưu, gồm cấu hình, các phương án và chỉ số phương án được chọn.',
'model_versions':'Một dòng là một phiên bản mô hình dự đoán và thông tin huấn luyện/đánh giá.',
'audit_logs':'Một dòng là một sự kiện thao tác quản trị hoặc thu thập dữ liệu được ghi nhật ký.',
'material_groups':'Một dòng là một nhóm vật liệu dùng tổng hợp và phân loại.',
'material_families':'Một dòng là một họ vật liệu; hỗ trợ nhận diện và chọn phương án tường.',
'materials':'Một dòng là một mã vật liệu trong danh mục, có đơn vị chuẩn và thuộc tính kỹ thuật.',
'wall_systems':'Một dòng là một phương án tường sử dụng một mã vật liệu ở một quy cách/chiều dày, kèm định mức khối xây.',
'material_relations':'Một dòng là một quan hệ có hướng giữa hai vật liệu: đi kèm bắt buộc hoặc cấu thành cấp phối.',
'material_aliases':'Một dòng là một tên gọi khác liên kết tới một mã vật liệu.',
'standards':'Một dòng là một tiêu chuẩn, quy chuẩn hoặc văn bản tham chiếu; thông tin hiệu lực cần được xác minh từ nguồn gốc.',
'material_standards':'Một dòng là một cặp vật liệu và tiêu chuẩn áp dụng.',
'material_rules':'Một dòng là một quy tắc nhận tín hiệu chữ, hatch, layer hoặc block để gán loại đối tượng/vật liệu tường.',
'material_notes':'Một dòng là một mẫu ghi chú vật liệu phần thô ánh xạ về mã vật liệu.',
'room_rules':'Một dòng là một quy tắc nhận loại phòng phục vụ công tác theo khu vực, ví dụ chống thấm.',
'rough_norms':'Một dòng là một định mức vật liệu cho mã công tác và biến thể cụ thể; có thông tin nguồn và mức xác nhận.',
'drawing_concepts':'Một dòng là một mẫu layer/block và vai trò tương ứng; đây là tín hiệu hỗ trợ nhận dạng.',
'convention_clauses':'Một dòng là một điều khoản quy ước đầu vào và cách kiểm tra.',
'suppliers':'Một dòng là một nhà cung cấp/đại lý, thông tin vị trí, giao hàng và xác minh.',
'supplier_materials':'Một dòng là một cặp nhà cung cấp–vật liệu với thông tin bán và giá hiện hành; không phải lịch sử báo giá.',
'vehicles':'Một dòng là một phương tiện/phương án vận chuyển với tải trọng và biểu phí.',
'price_records':'Một dòng là một quan sát giá theo vật liệu, nhà cung cấp nếu có, ngày, lượng, đơn vị và nguồn.',
'labor_rates':'Một dòng là một đơn giá công lao động theo địa phương, bậc thợ và thời điểm hiệu lực.'}

FIELDS={
'material_id':'Mã vật liệu trong danh mục.','wall_system_id':'Mã phương án tường.','supplier_id':'Mã nhà cung cấp; có thể trống ở giá công bố.',
'project_id':'Mã công trình.','file_id':'Mã file nguồn.','takeoff_id':'Mã kết quả bóc tách.','user_id':'Mã người dùng.',
'run_id':'Mã lần tối ưu.','version':'Định danh phiên bản mô hình.','model_version':'Phiên bản mô hình đã sử dụng.',
'name':'Tên hiển thị.','title':'Tiêu đề hoặc tên đầy đủ.','description':'Mô tả nghiệp vụ.','sort_order':'Thứ tự hiển thị.',
'data_kind':'Nguồn dữ liệu: ACTUAL, SAMPLE hoặc SYNTHETIC; không đồng nghĩa đã kiểm chứng.',
'unit':'Đơn vị tính chuẩn của giá trị/vật liệu.','purchase_unit':'Đơn vị mua hàng.','unit_conversion':'Hệ số quy đổi; phải đối chiếu chiều quy đổi tại nơi sử dụng.',
'unit_factor':'Hệ số đổi từ viên sang đơn vị danh mục trong định mức tường.','group':'Nhóm vật liệu.','family':'Họ vật liệu.',
'family_id':'Mã họ vật liệu.','group_id':'Mã nhóm vật liệu.','is_wall':'Đánh dấu họ vật liệu dùng cho tường.',
'qty_per_m2':'Định mức trên m² thuộc dữ liệu mẫu cũ; cần tránh dùng thay định mức wall_systems.',
'weight_kg_per_m2':'Khối lượng trên m² thuộc dữ liệu mẫu cũ.','labor_days_per_m2':'Công trên m² thuộc dữ liệu mẫu cũ.',
'thickness_mm':'Chiều dày, mm; ý nghĩa phụ thuộc vật liệu, không phải chiều dày mặc định của mọi tường.',
'lambda_w_mk':'Hệ số dẫn nhiệt, W/(m·K).','length_mm':'Chiều dài, mm.','width_mm':'Chiều rộng, mm.','height_mm':'Chiều cao, mm.',
'unit_weight_kg':'Khối lượng kg trên một đơn vị danh mục.','waste_pct':'Tỷ lệ hao hụt theo phần trăm; cần giữ nguồn.',
'transport_volume_m3':'Thể tích vận chuyển trên đơn vị vật liệu, m³.','subgroup':'Phân nhóm chi tiết.',
'usage_text':'Mô tả công dụng.','usage_role':'Vai trò sử dụng; hiện lưu dạng chuỗi.','tier':'Mức tham gia tối ưu/tra cứu.',
'needs_lambda':'Có yêu cầu dữ liệu hệ số dẫn nhiệt hay không.','price_priority':'Mức ưu tiên thu thập giá.',
'reference_brands':'Các thương hiệu tham khảo.','standards_text':'Mô tả tiêu chuẩn dạng văn bản; khác liên kết material_standards.',
'tech_notes':'Ghi chú kỹ thuật.','data_note':'Ghi chú chất lượng dữ liệu.','raw_class':'Loại vật liệu thô dùng lọc nhu cầu.',
'relation_type':'REQUIRES hoặc COMPOSED_OF.','related_material_id':'Mã vật liệu đi kèm/thành phần.',
'quantity':'Lượng vật liệu hoặc quy mô quan sát; đọc cùng đơn vị và mục đích bảng.','quantity_unit':'Đơn vị của hệ số quan hệ.',
'alias':'Tên gọi khác.','standard_id':'Mã nội bộ của văn bản tiêu chuẩn.','code':'Mã/số hiệu.',
'kind':'Loại văn bản/đối tượng theo nghiệp vụ bảng.','status':'Trạng thái, cần xem miền giá trị theo bảng.',
'valid_from':'Ngày bắt đầu hiệu lực.','valid_to':'Ngày kết thúc hiệu lực.',
'source_url':'Đường dẫn tài liệu gốc.','source':'Nguồn dữ liệu hoặc tài liệu làm căn cứ.','note':'Ghi chú.',
'rule_id':'Mã quy tắc ổn định.','pattern':'Mẫu nhận dạng.','signal':'Loại tín hiệu cần so khớp.',
'target':'Đích nhận dạng; hiện có thể là họ, mã hoặc danh sách cách nhau bằng |.',
'element':'Loại đối tượng mà quy tắc xác định.','priority':'Độ ưu tiên quy tắc.',
'work_code':'Mã công tác phần thô.','variant':'Biến thể định mức theo quy cách/mác.',
'material_name':'Tên vật liệu ghi trong nguồn định mức.','qty':'Hệ số lượng vật liệu trên một đơn vị công tác.',
'qty_unit':'Đơn vị hệ số định mức.','qty_min':'Cận dưới của hệ số.','qty_max':'Cận trên của hệ số.',
'norm_code':'Mã định mức làm căn cứ; không tự khẳng định hiệu lực văn bản.',
'muc_xac_nhan':'Phân loại căn cứ hệ số: nguồn, tính hoặc kinh nghiệm.','ngay_tra':'Ngày tra nguồn; hiện là chuỗi.',
'province':'Địa phương; hiện lưu bằng chuỗi.','lat':'Vĩ độ.','lon':'Kinh độ.',
'lead_time_days':'Thời gian cung ứng, ngày.','dealer_type':'Loại hình đại lý.',
'brands':'Các thương hiệu cung ứng, hiện lưu chuỗi.','address':'Địa chỉ.',
'ward':'Phường/xã.','district':'Quận/huyện được lưu theo dữ liệu thu thập.',
'maps_url':'Liên kết vị trí.','phone':'Số điện thoại.','zalo':'Liên hệ Zalo.','email':'Địa chỉ email.',
'website':'Website.','facebook':'Trang Facebook.','tax_code':'Mã số thuế.','opening_hours':'Giờ hoạt động.',
'delivers':'Có giao hàng hay không.','delivery_radius_km':'Bán kính giao hàng, km.',
'max_truck_ton':'Tải trọng xe tối đa có thể phục vụ, tấn.','min_order':'Điều kiện đơn tối thiểu dạng văn bản.',
'vat_invoice':'Có xuất hóa đơn VAT hay không.','payment':'Điều kiện thanh toán.',
'price_public':'Mức công khai giá: YES, NO hoặc PARTIAL.','price_page_url':'Trang giá.',
'verified':'Đã xác minh nhà cung cấp theo quy trình hiện tại.','collected_at':'Ngày thu thập.',
'collected_by':'Người thu thập.','base_price':'Giá hiện hành, phải đọc cùng ngày giá và cơ sở VAT/vận chuyển.',
'product_url':'Trang sản phẩm.','dealer_product_name':'Tên sản phẩm tại đại lý.','brand':'Thương hiệu.',
'sale_unit':'Đơn vị bán của đại lý.','price_level':'Loại nguồn giá; xem CHECK của bảng.',
'price_date':'Ngày của giá.','vat_included':'YES/NO/UNKNOWN về VAT.',
'transport_included':'YES/NO/UNKNOWN về vận chuyển.','in_stock':'Trạng thái còn hàng nếu biết.',
'payload_ton':'Tải trọng, tấn.','base_fee':'Phí vận chuyển cơ bản.','fee_per_km':'Phí trên km.',
'date':'Ngày quan sát giá.','unit_price':'Đơn giá theo đơn vị của dòng.','grade':'Bậc thợ.',
'rate_per_day':'Đơn giá một công/ngày theo nguồn.','full_name':'Tên người dùng.',
'password_hash':'Mật khẩu dạng băm; không đưa vào xuất dữ liệu thông thường.',
'role':'Vai trò; xem bảng và ràng buộc tương ứng.','is_active':'Trạng thái hoạt động.',
'site_lat':'Vĩ độ công trình.','site_lon':'Kinh độ công trình.',
'floor_height_mm':'Chiều cao tầng cấp dự án, mm; không đại diện mọi tầng nếu công trình khác cao độ.',
'door_width_mm':'Rộng cửa đi bổ sung cấp dự án, mm.','door_height_mm':'Cao cửa đi bổ sung cấp dự án, mm.',
'window_width_mm':'Rộng cửa sổ bổ sung cấp dự án, mm.','window_height_mm':'Cao cửa sổ bổ sung cấp dự án, mm.',
'budget':'Ngân sách.','deadline_days':'Thời hạn, ngày.','max_vehicle_ton':'Giới hạn tải trọng xe đến công trình, tấn.',
'excluded_materials':'Danh sách vật liệu loại trừ; snapshot theo ngữ cảnh dự án/lần chạy.',
'filename':'Tên file gốc.','file_type':'Loại file được ứng dụng sử dụng.','stored_path':'Vị trí lưu file; không chứa nội dung nhị phân.',
'uploaded_at':'Thời điểm tải file.','result':'JSONB chứa kết quả bóc tách và đầu vào; chưa có CHECK toàn bộ cấu trúc ở DB.',
'layer_overrides':'Ánh xạ layer do người dùng điều chỉnh.','confirmed_at':'Thời điểm xác nhận; chưa có cột người xác nhận riêng.',
'method':'Phương pháp tối ưu.','config':'Cấu hình lần chạy dạng JSONB.','solutions':'Danh sách phương án dạng JSONB.',
'chosen_index':'Chỉ số phương án đã chọn; cần kiểm tra nằm trong danh sách.',
'price_snapshot_date':'Ngày bảng giá tham chiếu; chưa tự bảo đảm đóng băng toàn bộ dòng giá.',
'llm_model':'Định danh mô hình ngôn ngữ.','tool_calls':'Dấu vết gọi công cụ dạng JSONB.',
'target':'Đích nhận dạng hoặc mục tiêu mô hình tùy bảng.','trained_at':'Thời điểm huấn luyện.',
'data_rows':'Số dòng dữ liệu huấn luyện.','contains_synthetic':'Có dữ liệu giả lập trong huấn luyện hay không.',
'metrics':'Chỉ số đánh giá mô hình dạng JSONB.','file_path':'Đường dẫn tệp mô hình.',
'action':'Tên sự kiện thao tác.','detail':'Chi tiết sự kiện dạng JSONB.',
'created_at':'Thời điểm tạo.','updated_at':'Thời điểm cập nhật; xem cơ chế cập nhật ở ứng dụng.',
'id':'Khóa số tự tăng nội bộ.','log_id':'Khóa sự kiện nhật ký.'}

def meaning(c):
    if c.get('comment'):return c['comment']
    if c['name'] in FIELDS:return FIELDS[c['name']]
    if c['name'].endswith('_source'):return 'Nguồn xác định thuộc tính tương ứng.'
    return 'Thuộc tính nghiệp vụ; đối chiếu định nghĩa nguyên gốc và luồng sử dụng ở mã nguồn.'

def diagram(path, groups):
    im=Image.new('RGB',(1500,780),'white');d=ImageDraw.Draw(im)
    fp='C:/Windows/Fonts/arial.ttf';bold='C:/Windows/Fonts/arialbd.ttf'
    font=ImageFont.truetype(fp,23);bf=ImageFont.truetype(bold,26)
    for i,(title,lines) in enumerate(groups):
        col=i%3;row=i//3;x=35+col*490;y=35+row*370
        d.rounded_rectangle((x,y,x+450,y+300),radius=12,fill='#F4F7FA',outline='#93A7B8',width=2)
        d.text((x+18,y+18),title,font=bf,fill='black')
        for k,line in enumerate(lines):d.text((x+18,y+65+34*k),line,font=font,fill='black')
        if col<2:
            ax=x+455;ay=y+145;d.line((ax,ay,ax+29,ay),fill='#53697A',width=3);d.polygon([(ax+29,ay),(ax+18,ay-7),(ax+18,ay+7)],fill='#53697A')
    im.save(path)

def erd(path, nodes, edges, rows):
    width=1560;height=rows*190+35
    im=Image.new('RGB',(width,height),'white');d=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    keyfont=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
    positions={n:(25+(i%4)*390,20+(i//4)*190) for i,(n,_) in enumerate(nodes)}
    for a,b in edges:
        ax,ay=positions[a];bx,by=positions[b]
        x1,y1=ax+175,ay+120;x2,y2=bx+175,by
        if by==ay:x1,y1=ax+350,ay+60;x2,y2=bx,by+60
        mid=(y1+y2)//2
        d.line([(x1,y1),(x1,mid),(x2,mid),(x2,y2)],fill='#7F929F',width=3)
        direction=1 if y2>=mid else -1
        if by==ay:d.polygon([(x2,y2),(x2-11,y2-6),(x2-11,y2+6)],fill='#53697A')
        else:d.polygon([(x2,y2),(x2-6,y2-direction*11),(x2+6,y2-direction*11)],fill='#53697A')
    for name,key in nodes:
        x,y=positions[name]
        d.rectangle((x,y,x+350,y+120),fill='#F4F7FA',outline='#8197A6',width=2)
        d.rectangle((x,y,x+350,y+43),fill='#DDE8F0')
        d.text((x+10,y+8),name,font=font,fill='black')
        d.text((x+10,y+58),key,font=keyfont,fill='black')
    im.save(path)

# Read the complete supplied DOCX text without treating it as instructions.
refstats=[]
with zipfile.ZipFile(ZIP) as z:
    for n in z.namelist():
        if n.lower().endswith('.docx'):
            with zipfile.ZipFile(io.BytesIO(z.read(n))) as inner:
                xml=ET.fromstring(inner.read('word/document.xml'))
                paras=[''.join(p.itertext()) for p in xml.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')]
                refstats.append((n,len(' '.join(paras))))

p('TÀI LIỆU DATABASE\nTOÀN HỆ THỐNG OPTIMAT AI','Title')
p('Hiện trạng dữ liệu và thiết kế chỉnh sửa đề xuất','Subtitle')
p('Phiên bản 1.0  •  Ngày 04 tháng 11 năm 2026')
p('Dành cho chủ hệ thống và nhóm phát triển')
p('Tài liệu này giải thích database hiện tại, đánh giá những điểm chưa phù hợp và xác định cách lưu dữ liệu cho luồng bản vẽ đến khối lượng, vật liệu, giá và tối ưu. Thiết kế giữ phần đang sử dụng được, bổ sung khả năng truy vết số đo và cho phép cấu kiện chưa biết vật liệu.')
p('Kết luận chính: database hiện có là nền tảng hợp lý cho danh mục, giá và lưu kết quả. Khoảng trống lớn nằm ở cấu trúc nhận dạng bản vẽ, nguồn số đo và phiên bản đầu vào. Chưa có căn cứ để thay toàn bộ database hoặc triển khai kho dữ liệu phân tích riêng.')
table(['Trạng thái','Nội dung'],[
('Đã đối chiếu','26 bảng và 273 cột khai báo trong SQLAlchemy; SQL schema và các luồng lưu/đọc được nêu trong tài liệu.'),
('Đề xuất','Các bảng bổ sung, ràng buộc và lộ trình chuyển đổi; chưa triển khai vào ứng dụng.'),
('Chưa xác minh','Lược đồ, số dòng, hiệu năng, quyền truy cập và dữ liệu thực tế trong PostgreSQL đang chạy.')],[1.25,5.75])
p('Các ví dụ số liệu trong tài liệu là minh họa. Không sử dụng làm định mức, báo giá hoặc đáp án nghiệm thu thực tế.')
doc.add_page_break()
h('Mục lục')
chapters=['1 Căn cứ và cách đọc tài liệu','2 Nghiệp vụ và kiến trúc dữ liệu','3 Kiểm kê database hiện tại','4 Đánh giá thiết kế hiện tại','5 Thiết kế dữ liệu mục tiêu','6 Luồng dữ liệu và hợp đồng xử lý','7 Chất lượng dữ liệu và kiểm chứng','8 Chuyển đổi và tương thích','9 Vận hành và kiểm thử','10 Ví dụ xuyên suốt','11 Kết luận thiết kế và thứ tự thực hiện','Phụ lục A Từ điển 26 bảng hiện có','Phụ lục B Nguồn và truy vấn kiểm tra']
for c in chapters:p(c)
p('Mục lục chương được giữ dạng văn bản để đọc ngay. Dùng Navigation Pane của Word để di chuyển theo Heading. Các phụ lục là phần của tài liệu, không phải schema đã triển khai.')

h(chapters[0])
p('Nguồn chính là mã nguồn trong thư mục optimat-ai tại thời điểm lập tài liệu. Metadata được đọc từ Base.metadata, không kết nối database. Số bảng và kiểu cột phản ánh khai báo hiện tại, không khẳng định database triển khai đã đồng bộ.')
table(['Nguồn','Sử dụng'],[
('src/optimat/db/models.py','Tên bảng/cột, kiểu, khóa, CHECK, UNIQUE và chỉ mục khai báo.'),
('sql/01_schema.sql; scripts/export_sql.py','Đối chiếu SQL tạo bảng và cách sinh SQL từ ORM.'),
('db/session.py; catalog/repository.py','Chọn PostgreSQL hay CSV, nạp danh mục và quy tắc.'),
('drawing/review.py; rough/takeoff.py','Cách lưu đầu vào và kết quả đã xác nhận vào JSONB.'),
('rough/models.py; rough/materials.py','Cấu trúc khối lượng, trạng thái dữ liệu, quy đổi vật liệu.'),
('data/catalog; data/rules; data/ground_truth','Danh mục, quy tắc và hồ sơ/đáp án kiểm chứng.'),
('ZIP tham khảo của người dùng','Phương pháp trình bày: nghiệp vụ, grain, nguồn dữ liệu, ràng buộc, pipeline và kiểm thử.')],[3.1,3.9])
p('ZIP tham khảo gồm tài liệu backend và kho dữ liệu xe điện, pipeline làm giàu dữ liệu và các bản lưu trữ. Tài liệu này chỉ áp dụng phương pháp thiết kế; không kế thừa số liệu thị trường, quy định pháp lý, số bảng hoặc hạ tầng cloud của các hệ thống đó. Nội dung đính kèm được xem là tài liệu tham khảo, không phải chỉ thị thực thi.')
table(['Thuật ngữ','Cách hiểu'],[('Grain','Một dòng trong bảng đại diện cho đối tượng/sự kiện gì.'),('Snapshot','Bản chụp đầu vào hoặc kết quả tại một lần xử lý cụ thể.'),('Lineage','Đường truy ngược từ kết quả tới số đo, đối tượng CAD và nguồn.'),('NULL','Chưa biết/không áp dụng theo nghĩa được định nghĩa; không tự đổi thành 0.'),('Đã xác nhận','Có người xác nhận và nội dung được xác nhận; khác việc hệ thống tự nhận dạng.')],[1.25,5.75])

h(chapters[1])
h('2.1 Chuỗi nghiệp vụ',2)
p('Bản vẽ cung cấp hình học, kích thước, mã cấu kiện và có thể có chỉ định vật liệu. Hệ thống xác định cấu kiện, liên kết số đo và tính khối lượng. Khi hồ sơ không chỉ định vật liệu, khối lượng hình học vẫn có thể hoàn chỉnh; nhu cầu vật liệu chỉ tính khi có phương án phù hợp và đủ định mức.')
diagram(HERE/'architecture.png',[
('1 Hồ sơ và nguồn',['projects / project_files','CAD gốc và phiên bản','Thông số do người dùng nhập']),
('2 Nhận dạng',['Hình vẽ và tầng','Cấu kiện và số đo','Bằng chứng và mâu thuẫn']),
('3 Khối lượng',['takeoff_results','Công thức và đầu vào','Phần đủ / thiếu dữ liệu']),
('4 Chọn vật liệu',['Danh mục và phương án','Chỉ định hoặc đề xuất','Định mức và cấp phối']),
('5 Giá và tối ưu',['Giá có ngày và nguồn','Nhà cung cấp / vận chuyển','optimization_runs']),
('6 Kiểm tra',['Người xác nhận','Bộ đáp án độc lập','Lịch sử và khả năng tái lập'])])
doc.add_picture(str(HERE/'architecture.png'),width=Inches(7))
p('Hình 1  Các lớp dữ liệu nghiệp vụ và trình tự xử lý',style='Caption')
h('2.2 Phân chia nơi lưu',2)
bullets(['PostgreSQL lưu định danh, quan hệ, số đo đã diễn giải, danh mục, phiên bản và kết quả cần truy vấn.','File CAD, tài liệu gốc, ảnh render và mô hình lưu ở vùng file; database lưu đường dẫn, mã băm và thông tin nguồn. Không đưa toàn bộ CAD nhị phân vào JSONB.','JSONB tiếp tục dùng cho payload không đồng nhất, thuộc tính CAD và snapshot. Những quan hệ cần kiểm tra bằng khóa ngoại không chỉ giấu trong JSONB.','CSV phục vụ nhập dữ liệu, kiểm thử và chế độ không kết nối DB. Một lần chạy phải ghi rõ đã dùng nguồn nào; không trộn ngầm CSV và PostgreSQL.','Chưa tạo data warehouse riêng. Báo cáo hiện tại có thể dùng truy vấn/view; chỉ tách kho khi có nhu cầu lịch sử/tải phân tích đã đo được.'])

h(chapters[2])
groups=[('Danh mục và quy đổi',['material_groups','material_families','materials','wall_systems','material_relations','material_aliases','standards','material_standards']),('Nhận dạng và định mức',['material_rules','material_notes','drawing_concepts','convention_clauses','room_rules','rough_norms']),('Nguồn cung và giá',['suppliers','supplier_materials','vehicles','price_records','labor_rates']),('Hồ sơ và kết quả',['users','projects','project_files','takeoff_results','optimization_runs']),('Vận hành',['model_versions','audit_logs'])]
for title,names in groups:
    h(title,2);table(['Bảng','Một dòng đại diện cho'],[(n,PURPOSE[n]) for n in names],[2.0,5.0])
h('Sơ đồ quan hệ chính hiện có',2)
core=['users','projects','project_files','takeoff_results','material_families','materials','wall_systems','optimization_runs','suppliers','supplier_materials','price_records','model_versions']
edges=[]
for name in core:
    for c in BY[name]['columns']:
        for fk in c['fk']:
            parent=fk['target'].split('.')[0]
            if parent in core:edges.append((parent,name))
erd(HERE/'erd_current.png',[(n,'PK '+', '.join(c['name'] for c in BY[n]['columns'] if c['pk'])) for n in core],edges,3)
doc.add_picture(str(HERE/'erd_current.png'),width=Inches(7))
p('Hình 2  Quan hệ FK chính hiện có. Mũi tên đi từ bảng được tham chiếu tới bảng chứa FK. Các bảng còn lại và toàn bộ FK được ghi trong phụ lục A.',style='Caption')
h('3.1 Cách hệ thống hiện lưu kết quả',2)
p('drawing/review.py lưu JSONB gồm kết quả xác nhận và khóa input. rough/takeoff.py hàm save_rough lưu kind="rough", kết quả và input vào takeoff_results. Cả hai luồng tạo dòng mới và có confirmed_at. Như vậy không chính xác nếu nói hệ thống chưa lưu đầu vào hoặc phải tách ngay toàn bộ JSON thành bảng.')
p('Hai hàm lưu này khởi tạo TakeoffResultRow mà không truyền file_id. Cột liên kết file tồn tại nhưng riêng các đường lưu đã kiểm tra chưa gắn nó. Đây là khoảng trống truy vết cần sửa ở cả caller và hàm lưu, không chỉ thêm cột.')
h('3.2 Dữ liệu chưa nằm trong SQL',2)
p('Một số cấu hình nhận dạng như ngưỡng, ký hiệu cấu kiện và bảng kg/m thép vẫn ở data/rules. scripts/export_sql.py chỉ ánh xạ sáu CSV quy tắc vào SQL. Không nên mô tả mọi CSV là một bảng SQL đang được sử dụng.')
table(['Nguồn','Cách quản lý đề xuất'],[('Các bảng catalog và sáu bảng rule hiện có','Tiếp tục quản lý qua DB khi dùng DATABASE_URL; lưu snapshot/phiên bản cho lần tính.'),('CSV cấu hình nhận dạng còn lại','Giữ file có version/hash; chưa tạo một bảng cho từng CSV nếu không cần chỉnh sửa tại runtime.'),('Ground truth và cases.csv','Tiếp tục lưu bộ dữ liệu kiểm chứng có cấu trúc và mã băm; không trộn vào kết quả người dùng.'),('File mô hình và CAD','Giữ file ngoài DB, kiểm tra tồn tại và hash; kiểm soát quyền truy cập theo dự án.')],[2.8,4.2])

h(chapters[3])
findings=[
('P1','Truy vết file chưa kín','project_files chưa có hash/phiên bản; hai hàm lưu kết quả đã xem chưa truyền file_id.','Bổ sung thông tin phiên bản file và nối kết quả với đầy đủ file nguồn qua lần trích xuất.'),
('P1','Chưa có cấu trúc nguồn số đo','26 bảng hiện tại chưa có bảng số đo, đối tượng CAD hay liên kết bằng chứng riêng. JSONB có lưu dữ liệu nhưng DB chưa ràng buộc các quan hệ này.','Thêm cấu trúc tối thiểu cho cấu kiện, số đo và bằng chứng; giữ payload gốc.'),
('P1','Chưa chặn quan hệ chéo công trình ở DB','takeoff_results có project_id và file_id là hai FK độc lập; optimization_runs cũng có project_id và takeoff_id độc lập.','Dùng khóa ghép hoặc trigger kiểm tra cùng project; không dựa riêng vào việc ID tồn tại.'),
('P1','Snapshot giá chưa đủ để tái lập','optimization_runs lưu price_snapshot_date; ngày không xác định duy nhất bộ giá nếu dữ liệu cùng ngày bị sửa hoặc nạp thêm.','Lưu ID/hash các dòng giá và giá trị thực dùng, cùng phiên bản danh mục, định mức và cấu hình.'),
('P1','Xác nhận chưa có người xác nhận riêng','takeoff_results có confirmed_at nhưng không có confirmed_by trong bảng.','Bổ sung confirmed_by và hash nội dung được xác nhận; JSON lịch sử được bảo toàn.'),
('P2','Một số mã vật liệu chưa có FK','rough_norms.material_id và material_notes.material_id hiện là String; material_rules.target có nhiều dạng và phân cách |.','Phân biệt mã thật và token @VUA; kiểm tra nhập dữ liệu trước, rồi thêm FK/quan hệ phù hợp.'),
('P2','Thuộc tính cũ và mới dễ dùng nhầm','materials còn cột định mức mẫu theo m², trong khi wall_systems có định mức theo m³.','Đánh dấu deprecated, thống kê caller, chuẩn hóa nguồn tính; chưa xóa ngay.'),
('P2','Phạm vi kiểm tra số học còn hạn chế','Nhiều số đo, hệ số, tải trọng trong models chưa có CHECK dương hoặc miền giá trị tương ứng.','Bổ sung theo nghĩa từng trường, không áp CHECK quantity >= 0 cho dòng khấu trừ.'),
('P2','Chưa đóng băng bộ quy tắc','export_sql.py nạp quy tắc bằng DELETE rồi INSERT; ID số có thể không còn đại diện nội dung cũ.','Snapshot theo rule_id + nội dung/hash; không dùng ID tự tăng làm định danh phiên bản.'),
('P2','Giá hiện hành và lịch sử khác grain','supplier_materials chỉ có một dòng mỗi cặp supplier/material; price_records giữ quan sát lịch sử.','Giữ hai bảng nhưng quy định rõ giao dịch cập nhật, ngày hiệu lực, đơn vị và cơ sở giá.'),
('P2','Nhãn dữ liệu không phải xác minh','data_kind mặc định ACTUAL ở nhiều bảng; ACTUAL không chứng minh nguồn đã được kiểm tra.','Tách nguồn gốc và trạng thái kiểm chứng, chặn import không khai báo nguồn gốc.'),
('P3','Tài liệu đếm bảng không đồng nhất','README còn mô tả 23 bảng; models và SQL hiện khai báo 26.','Sinh kiểm kê từ metadata và cập nhật tài liệu cùng thay đổi schema.')]
for pri,title,evidence,fix in findings:
    h(pri+'  '+title,2);p('Căn cứ: '+evidence);p('Hướng xử lý: '+fix)
p('Các phát hiện trên phản ánh cấu trúc và đường mã đã kiểm tra. Chưa kết luận dữ liệu production đã có sai lệch, chưa đánh giá SQL injection, hiệu năng toàn hệ thống hoặc mức độ an toàn triển khai.')

# Target schema: compact logical specification, deliberately not represented as deployed DDL.
TARGET=[
('extraction_runs','Một lần trích xuất/nhận dạng trên bộ file và cấu hình cố định.',[
('extraction_id','BIGINT PK','Định danh lần trích xuất.'),('project_id','INTEGER FK NOT NULL','Công trình sở hữu.'),('status','VARCHAR NOT NULL','RUNNING, SUCCEEDED, PARTIAL hoặc FAILED.'),('input_manifest','JSONB NOT NULL','Danh sách file_id, hash file, loại hồ sơ và phiên bản.'),('parser_version','VARCHAR NOT NULL','Phiên bản bộ đọc/nhận dạng.'),('config_snapshot','JSONB NOT NULL','Quy tắc, ngưỡng và hash đầu vào.'),('started_at / finished_at','TIMESTAMPTZ','Thời điểm bắt đầu/kết thúc.'),('error_detail','JSONB NULL','Lỗi theo file/bước; không chứa bí mật.')], 'Một lần chạy có thể dùng nhiều file. Manifest phải kiểm tra mọi file cùng project. Dữ liệu lần chạy thành công không bị ghi đè.'),
('building_levels','Một tầng/cao độ chuẩn hóa trong một phiên bản trích xuất.',[
('level_id','BIGINT PK','Định danh tầng.'),('extraction_id','BIGINT FK NOT NULL','Phiên bản nhận dạng.'),('level_code / name','VARCHAR','Mã ổn định trong phiên bản và tên hiển thị.'),('elevation_mm','NUMERIC NULL','Cao độ, mm; có thể âm.'),('height_mm','NUMERIC NULL','Chiều cao tầng, mm; biết thì > 0.'),('evidence','JSONB NOT NULL','Danh sách evidence_id làm căn cứ hoặc ghi chưa xác định.')], 'UNIQUE(extraction_id, level_code). Không gộp tầng chỉ vì tên giống nhau. Quan hệ chứng cứ phải được kiểm tra khi ghi.'),
('drawing_views','Một vùng hình vẽ trong một file của lần trích xuất.',[
('view_id','BIGINT PK','Định danh hình vẽ.'),('extraction_id / file_id','FK NOT NULL','Lần trích xuất và file nguồn.'),('view_code / name','VARCHAR','Mã trong file và tiêu đề nguyên gốc.'),('view_type','VARCHAR NOT NULL','Mặt bằng, mặt cắt, chi tiết, bảng thống kê hoặc chưa rõ.'),('bbox','JSONB NOT NULL','Vùng bao trong hệ tọa độ nguồn.'),('transform','JSONB NOT NULL','Biến đổi từ tọa độ nguồn sang hệ chuẩn; có đơn vị.'),('scale_status','VARCHAR NOT NULL','VERIFIED, INFERRED, UNKNOWN hoặc CONFLICT.'),('metadata','JSONB NOT NULL','Tầng liên quan, chữ tiêu đề, bằng chứng tỷ lệ.')], 'File phải thuộc input_manifest và cùng project. Một mặt cắt có thể liên quan nhiều tầng; không ép một hình chỉ có một tầng.'),
('building_elements','Một cấu kiện vật lý trong một phiên bản nhận dạng.',[
('element_id','BIGINT PK','Định danh cấu kiện.'),('extraction_id','BIGINT FK NOT NULL','Phiên bản nhận dạng.'),('level_id','BIGINT FK NULL','Tầng chủ nếu xác định được.'),('element_code','VARCHAR NOT NULL','Mã nội bộ duy nhất trong lần nhận dạng.'),('design_label','VARCHAR NULL','Mã ghi trên bản vẽ, có thể lặp như C1.'),('element_type','VARCHAR NOT NULL','Tường, cửa, cột, dầm, sàn, móng, cầu thang hoặc khác.'),('geometry','JSONB NOT NULL','Hình học chuẩn hóa và loại hình học.'),('recognition_status','VARCHAR NOT NULL','CANDIDATE, VERIFIED, REJECTED hoặc UNRESOLVED.')], 'UNIQUE(extraction_id, element_code). Không bắt buộc material_id. Không đặt UNIQUE riêng cho design_label.'),
('element_occurrences','Một lần cấu kiện xuất hiện trong một hình vẽ.',[
('occurrence_id','BIGINT PK','Định danh lần xuất hiện.'),('element_id / view_id','BIGINT FK NOT NULL','Cấu kiện và hình biểu diễn.'),('role','VARCHAR NOT NULL','PLAN, SECTION, DETAIL hoặc SCHEDULE.'),('source_refs','JSONB NOT NULL','Handle CAD kèm đường dẫn INSERT lồng nhau và file_id.'),('source_geometry','JSONB NOT NULL','Hình học gốc dùng khoanh vùng trên hình.')], 'Cấu kiện và hình phải cùng extraction. Handle đơn lẻ không đủ phân biệt các lần INSERT cùng block. Không đếm mỗi occurrence thành một cấu kiện.'),
('evidence_sources','Một bằng chứng nguyên gốc có thể chỉ tới trên hồ sơ hoặc thao tác người dùng.',[
('evidence_id','BIGINT PK','Định danh bằng chứng.'),('extraction_id','BIGINT FK NOT NULL','Ngữ cảnh phiên bản.'),('file_id / view_id','FK NULL','Nguồn CAD/tài liệu; NULL được phép khi người dùng nhập.'),('source_kind','VARCHAR NOT NULL','DIMENSION, TEXT, GEOMETRY, SCHEDULE hoặc USER_INPUT.'),('source_ref','JSONB NOT NULL','Handle, đường dẫn block, bbox hoặc vị trí ô bảng.'),('raw_content','JSONB NOT NULL','Nội dung gốc và đơn vị gốc.'),('created_by','INTEGER FK NULL','Người nhập nếu là bổ sung thủ công.'),('content_hash','VARCHAR(64) NOT NULL','Mã băm nội dung bằng chứng.')], 'Bằng chứng thủ công phải có người nhập. Nếu có file/view thì phải cùng ngữ cảnh. Nội dung gốc bất biến trong phiên bản.'),
('element_measurements','Một giá trị ứng viên của một thông số cấu kiện.',[
('measurement_id','BIGINT PK','Định danh số đo ứng viên.'),('element_id','BIGINT FK NOT NULL','Cấu kiện được đo.'),('property_code','VARCHAR NOT NULL','LENGTH, WIDTH, HEIGHT, THICKNESS, AREA, COUNT...'),('value','NUMERIC NULL','Giá trị chuẩn hóa; thiếu thì NULL.'),('unit','VARCHAR NOT NULL','mm, m², m³, count theo loại thông số.'),('method','VARCHAR NOT NULL','DIRECT, GEOMETRIC, DERIVED hoặc USER_INPUT.'),('verification_status','VARCHAR NOT NULL','CANDIDATE, ACCEPTED, REJECTED hoặc CONFLICT.'),('accepted_by / accepted_at','FK / TIMESTAMPTZ NULL','Người và thời điểm xác nhận.'),('derivation','JSONB NOT NULL','Công thức và ID đầu vào nếu là giá trị suy ra.')], 'Chỉ một giá trị ACCEPTED cho mỗi (element_id, property_code), bằng unique index có điều kiện. Các giá trị xung đột cùng được giữ.'),
('measurement_evidence','Một liên kết giữa số đo ứng viên và bằng chứng.',[
('measurement_id','BIGINT PK/FK','Số đo.'),('evidence_id','BIGINT PK/FK','Bằng chứng.'),('role','VARCHAR NOT NULL','SUPPORT hoặc CONTRADICT.')], 'Khóa chính ghép. Hai đầu phải cùng extraction; số đo được chấp nhận phải có căn cứ hoặc chuỗi suy dẫn hợp lệ.'),
('element_relations','Một quan hệ có hướng giữa hai cấu kiện.',[
('relation_id','BIGINT PK','Định danh quan hệ.'),('from_element_id / to_element_id','BIGINT FK NOT NULL','Hai cấu kiện liên quan.'),('relation_type','VARCHAR NOT NULL','OPENING_IN, CONNECTS_TO, PART_OF hoặc quan hệ có định nghĩa.'),('evidence_ids','JSONB NOT NULL','Bằng chứng của liên kết.'),('verification_status','VARCHAR NOT NULL','Trạng thái xác nhận quan hệ.')], 'Hai cấu kiện cùng extraction; CHECK hai ID khác nhau; UNIQUE hai đầu và loại. Ngăn chu trình PART_OF bằng kiểm tra ứng dụng/trigger.'),
('review_issues','Một vấn đề cần kiểm tra trong phiên bản nhận dạng hoặc lần bóc.',[
('issue_id','BIGINT PK','Định danh vấn đề.'),('extraction_id','BIGINT FK NOT NULL','Phiên bản liên quan.'),('element_id / measurement_id','FK NULL','Đối tượng cụ thể nếu có.'),('issue_code','VARCHAR NOT NULL','MISSING, CONFLICT, DUPLICATE hoặc UNSUPPORTED.'),('severity / status','VARCHAR NOT NULL','Mức ảnh hưởng và OPEN/RESOLVED/WAIVED.'),('detail','JSONB NOT NULL','Mô tả, bằng chứng, phần kết quả bị ảnh hưởng.'),('resolved_by / resolved_at','FK / TIMESTAMPTZ NULL','Người và thời điểm xử lý.'),('resolution','TEXT NULL','Cách xử lý; không âm thầm bỏ qua.')], 'Đóng vấn đề phải có kết quả xử lý và người/thời điểm. WAIVED vẫn phải hiển thị ảnh hưởng tới tính đầy đủ.'),
('takeoff_items','Một dòng đóng góp hoặc khấu trừ của một công tác trong snapshot bóc tách.',[
('item_id','BIGINT PK','Định danh dòng công tác.'),('takeoff_id','INTEGER FK NOT NULL','Kết quả bóc tách chủ.'),('element_id','BIGINT FK NULL','Cấu kiện nếu ánh xạ được.'),('work_code / unit','VARCHAR NOT NULL','Công tác và đơn vị.'),('row_role','VARCHAR NOT NULL','CONTRIBUTION hoặc DEDUCTION.'),('quantity / known_part','NUMERIC NULL','Tổng khi đầy đủ và phần đã biết; không lấy thiếu làm 0.'),('formula','TEXT NOT NULL','Công thức giải thích kết quả.'),('input_snapshot','JSONB NOT NULL','ID số đo, giá trị thực dùng, đơn vị, quy tắc và phiên bản.'),('basis_status / is_complete','VARCHAR / BOOLEAN','A/B/C/D và tính đầy đủ theo luồng hiện có.')], 'Khấu trừ được phép âm theo quy ước đã công bố. Khi chưa đầy đủ, quantity NULL; known_part có thể có số. Không cộng khác đơn vị.'),
('material_scenarios','Một phương án vật liệu của một snapshot khối lượng.',[
('scenario_id','BIGINT PK','Định danh phương án.'),('takeoff_id','INTEGER FK NOT NULL','Snapshot khối lượng.'),('name / status','VARCHAR NOT NULL','Tên và DRAFT/PROPOSED/CONFIRMED/REJECTED.'),('catalog_snapshot','JSONB NOT NULL','Mã, thuộc tính, định mức/cấp phối và hash thực dùng.'),('created_by / created_at','FK / TIMESTAMPTZ','Người tạo nếu có và thời điểm.'),('confirmed_by / confirmed_at','FK / TIMESTAMPTZ NULL','Xác nhận lựa chọn.')], 'CONFIRMED cần người và thời điểm. Thay thuộc tính ảnh hưởng hình học phải tạo lần tính lại, không dùng khối lượng cũ tùy tiện.'),
('material_assignments','Một lựa chọn vật liệu cho một dòng công tác trong một phương án.',[
('assignment_id','BIGINT PK','Định danh gán vật liệu.'),('scenario_id / item_id','BIGINT FK NOT NULL','Phương án và công tác.'),('material_id','VARCHAR(64) FK NULL','Vật liệu chính nếu đã xác định.'),('wall_system_id','VARCHAR(64) FK NULL','Phương án tường nếu áp dụng.'),('origin','VARCHAR NOT NULL','DESIGN, USER hoặc PROPOSED.'),('selection_status','VARCHAR NOT NULL','UNKNOWN, CANDIDATE hoặc SELECTED.'),('evidence_snapshot','JSONB NOT NULL','Chỉ định, lý do hoặc thông tin người chọn.')], 'UNKNOWN cho phép NULL vật liệu. SELECTED cần vật liệu hợp lệ; nếu có wall_system thì phải khớp material_id. Item và scenario phải cùng takeoff.'),
('material_requirements','Một thành phần vật liệu do một lựa chọn công tác sinh ra.',[
('requirement_id','BIGINT PK','Định danh dòng vật tư.'),('assignment_id','BIGINT FK NOT NULL','Lựa chọn công tác nguồn.'),('material_id','VARCHAR(64) FK NOT NULL','Vật liệu thành phần.'),('unit','VARCHAR NOT NULL','Đơn vị lượng vật liệu.'),('quantity / quantity_with_waste','NUMERIC NULL','Lượng chưa hao hụt và sau hao hụt.'),('norm_snapshot','JSONB NOT NULL','Định mức, cấp phối, hệ số đổi, hao hụt và nguồn.'),('is_complete / missing','BOOLEAN / JSONB','Tính đầy đủ và lý do thiếu.')], 'Chỉ tổng hợp dòng cùng mã/đơn vị/cơ sở. Chưa biết hao hụt thì lượng sau hao hụt NULL, không mặc định 0%. Giữ dòng nguồn để tránh cộng hai lần cấp phối.')]

h(chapters[4])
h('5.1 Quyết định giữ và bổ sung',2)
p('Giữ 26 bảng hiện tại làm nền tảng. Thiết kế đích đề xuất thêm 14 bảng logic, triển khai theo giai đoạn chứ không tạo tất cả ngay. Đây không phải cam kết mọi bảng đã cần ở runtime; mỗi bảng chỉ đưa vào migration khi luồng đọc/ghi tương ứng được triển khai và kiểm thử.')
p('So với phác thảo ban đầu, chưa tạo drawing_entities để sao chép toàn bộ CAD. Đối tượng gốc được giữ trong file bất biến, còn occurrence/evidence lưu tham chiếu đủ để mở lại đối tượng. Chỉ bổ sung kho entity riêng khi đo được nhu cầu truy vấn hoặc chi phí đọc file. Cũng chưa tạo takeoff_item_inputs riêng: input_snapshot bất biến đủ cho tái lập và tránh thêm bảng chỉ để sao chép số đo.')
table(['Bảng đang có','Chỉnh sửa đề xuất'],[
('project_files','Thêm sha256, revision_label, supersedes_file_id, discipline, file_size_bytes; không ghi đè file cũ. Hash không UNIQUE toàn hệ thống vì cùng file có thể thuộc các dự án khác nhau.'),
('takeoff_results','Thêm extraction_id, schema_version, result_hash, confirmed_by. Giữ result/input JSONB và file_id để tương thích; extraction manifest là nguồn đầy đủ khi dùng nhiều file.'),
('optimization_runs','Thêm input_manifest/hash trong config có version; chụp giá, danh mục, định mức, random_seed, cấu hình thuật toán và mô hình thực dùng.'),
('materials / wall_systems / rough_norms','Giữ bảng; quy định nguồn thẩm quyền, đơn vị và phiên bản snapshot. Tránh nhân bản định mức mẫu cũ.'),
('material_notes / rough_norms','Làm sạch mã; mã vật liệu thật dùng FK. Token @VUA được mô hình hóa như vai trò chọn vật liệu, không tạo vật liệu giả @VUA.'),
('users / projects / audit_logs','Giữ; kiểm tra quyền qua project chủ và ghi sự kiện xác nhận/chuyển phiên bản.')],[2.0,5.0])
h('5.2 Từ điển các bảng bổ sung',2)
p('Kiểu dưới đây là đặc tả đề xuất, chưa phải DDL đã thực thi. BIGINT dùng cho dữ liệu phát sinh lớn; FK tới bảng hiện có phải giữ đúng kiểu khóa INTEGER/VARCHAR. Các dòng ghi hai tên bằng dấu / là hai cột riêng khi triển khai.')
for name,grain,cols,rules in TARGET:
    h(name,3);p('Grain: '+grain)
    table(['Cột đề xuất','Kiểu và bắt buộc','Ý nghĩa'],cols,[2.0,1.65,3.35]);p('Ràng buộc: '+rules)
h('5.3 Quan hệ và toàn vẹn',2)
table(['Quan hệ','Bội số / điều kiện'],[
('projects → project_files','1–N; mọi file của lần trích xuất thuộc cùng project.'),
('projects → extraction_runs','1–N; một lần trích xuất đóng băng input_manifest.'),
('extraction_runs → views / levels / elements','1–N cho mỗi nhóm; không trộn giữa phiên bản.'),
('elements ↔ drawing_views','N–N qua element_occurrences.'),
('elements → measurements ↔ evidence','1–N số đo ứng viên; N–N bằng chứng qua measurement_evidence.'),
('elements ↔ elements','Quan hệ có hướng qua element_relations; cửa chủ và cấu kiện đều cùng extraction.'),
('extraction_runs → takeoff_results → takeoff_items','1–N; kết quả được xác nhận là snapshot.'),
('takeoff_results → scenarios → assignments → requirements','1–N từng bước; assignment phải dùng item thuộc đúng takeoff.'),
('projects → optimization_runs','1–N; kiểm tra takeoff cùng project và chụp đầu vào thực dùng.')],[3.4,3.6])
p('Các điều kiện cùng project/extraction/takeoff phải được bảo đảm bằng FK ghép tới khóa UNIQUE tương ứng hoặc trigger có kiểm thử. CHECK không được dùng để giả vờ kiểm tra dữ liệu ở bảng khác. JSONB chứa danh sách ID được kiểm tra ở transaction ghi; nếu cần quan hệ truy vấn thường xuyên thì tách bảng nối khi triển khai.')
nodes=[('extraction_runs','project_id → projects'),('drawing_views','extraction_id, file_id'),('building_levels','extraction_id'),('building_elements','extraction_id, level_id'),('element_occurrences','element_id, view_id'),('evidence_sources','extraction_id, file_id'),('element_measurements','element_id'),('element_relations','from / to element_id'),('measurement_evidence','measurement_id, evidence_id'),('review_issues','extraction_id, element_id'),('takeoff_results','extraction_id đề xuất'),('takeoff_items','takeoff_id, element_id'),('material_scenarios','takeoff_id'),('material_assignments','scenario_id, item_id'),('material_requirements','assignment_id')]
edges=[('extraction_runs','drawing_views'),('extraction_runs','building_levels'),('building_levels','building_elements'),('drawing_views','element_occurrences'),('building_elements','element_occurrences'),('building_elements','element_measurements'),('evidence_sources','measurement_evidence'),('element_measurements','measurement_evidence'),('extraction_runs','takeoff_results'),('takeoff_results','takeoff_items'),('takeoff_results','material_scenarios'),('material_scenarios','material_assignments'),('takeoff_items','material_assignments'),('material_assignments','material_requirements')]
erd(HERE/'erd_target.png',nodes,edges,4)
doc.add_picture(str(HERE/'erd_target.png'),width=Inches(7))
p('Hình 3  Quan hệ chính trong thiết kế bổ sung. Sơ đồ lược bớt FK người dùng/danh mục và một số liên kết để dễ đọc; mục 5.2 là đặc tả đầy đủ hơn. takeoff_results là bảng đang có.',style='Caption')
h('5.4 Kiểu dữ liệu và chỉ mục',2)
bullets(['Hiện trạng dùng Float, tài liệu không tự đổi toàn bộ sang Numeric. Thiết kế mới dùng NUMERIC cho số lượng chuẩn hóa; độ chính xác/scale được chốt từ miền giá trị và dung sai trước migration. Tiền cần số thập phân chính xác khi đưa vào chốt giá.','TIMESTAMPTZ cho sự kiện; DATE cho ngày giá/ngày hiệu lực. Hiển thị theo múi giờ người dùng; lưu và trao đổi thời điểm có múi giờ.','Chỉ mục ưu tiên: project_id, extraction_id, (extraction_id, element_code), (element_id, property_code), các FK của occurrence/evidence/item và (scenario_id, item_id).','Dùng unique index có điều kiện để chặn hai số đo ACCEPTED cho cùng thuộc tính. Không đặt GIN trên mọi JSONB; chỉ tạo khi truy vấn và EXPLAIN chứng minh cần.','Chỉ giữ trường nullable khi có nghĩa nghiệp vụ rõ. Không dùng chuỗi rỗng thay NULL cho giá trị số/ngày; không biến UNKNOWN thành NO.'])

h(chapters[5])
flows=[('6.1 Tiếp nhận hồ sơ','Kiểm quyền project → lưu file mới → tính hash/size → tạo project_files. Khi DWG cần chuyển DXF, giữ cả hash gốc, đầu ra chuyển đổi và phiên bản converter trong manifest. Chuyển đổi thất bại phải kết thúc có lỗi; không sinh khối lượng rỗng như thành công.'),('6.2 Nhận dạng và chuẩn hóa','Tạo extraction_run → đọc các hình và tỷ lệ → tạo cấu kiện ứng viên, occurrences, evidence và số đo. Bộ đọc CAD vẫn làm việc với file gốc; trường hợp scale chưa xác định không tính đại lượng phụ thuộc tỷ lệ.'),('6.3 Kiểm tra và xác nhận số đo','So các ứng viên cho cùng thuộc tính; mở review_issue khi mâu thuẫn. Người dùng chấp nhận một giá trị trong transaction, lưu bằng chứng và nhật ký. Số đo đã được dùng ở snapshot cũ không bị sửa ngược; sửa tạo phiên bản/kết quả mới.'),('6.4 Tính khối lượng','Dùng số đo đã đủ căn cứ và quy tắc đo bóc → tạo takeoff_items và snapshot JSONB tương thích. Giữ dòng cộng/trừ và nguồn; tổng chỉ có khi phạm vi đầy đủ, phần đã biết hiển thị riêng.'),('6.5 Chọn và quy đổi vật liệu','Tạo scenario, gán vật liệu theo chỉ định hoặc lựa chọn. Chưa chọn vẫn lưu khối lượng. Định mức/cấp phối đủ thì sinh requirements; thiếu định mức thì lưu missing. Vật liệu đề xuất không tự trở thành vật liệu thiết kế.'),('6.6 Giá và tối ưu','Chọn dữ liệu giá theo vật liệu, đơn vị, ngày, địa phương, nhà cung cấp và VAT/vận chuyển. Chụp giá trị được dùng, phương án vật liệu và ràng buộc trước tối ưu. Lưu phương án, lựa chọn và dấu vết chạy vào optimization_runs.')]
for title,text in flows:h(title,2);p(text)
h('6.7 Hợp đồng tương thích API',2)
p('Giữ các định danh và cấu trúc công khai đang sử dụng. Bổ sung schema_version, extraction_id, tham chiếu nguồn và trạng thái đầy đủ theo dạng trường tùy chọn trong giai đoạn chuyển đổi. Luồng đọc cũ tiếp tục dùng JSONB; lớp ánh xạ tạo dữ liệu mới và snapshot cũ trong cùng transaction khi có thể. Không hứa tên endpoint mới khi chưa thiết kế API.')
p('Tách trạng thái nguồn số liệu A/B/C/D hiện có khỏi trạng thái người kiểm và trạng thái chọn vật liệu. Một số đo A có thể chưa được người kiểm xác nhận; công tác đủ số đo vẫn có thể chưa có phương án vật liệu.')

h(chapters[6])
table(['Nhóm kiểm tra','Yêu cầu'],[
('Đơn vị và tỷ lệ','Mọi giá trị có đơn vị và hệ tọa độ; tỷ lệ riêng từng hình; phát hiện đơn vị khai báo khác DIMENSION.'),
('Tính đầy đủ','Thiếu cao/dày/tiết diện phải chỉ ra công tác bị ảnh hưởng; không điền 0 để đủ bảng.'),
('Không trùng','Một cấu kiện có nhiều hình; INSERT lặp khác cấu kiện; không dùng tên C1 làm khóa duy nhất.'),
('Nguồn','Một số đo phải truy về bằng chứng và file hash; giá/định mức truy về nguồn và snapshot.'),
('Quan hệ','Cửa đúng tường chủ, chi tiết đúng mã cấu kiện/tầng; không chấp nhận liên kết chéo project.'),
('Vật liệu','Chưa biết khác không dùng; không đoán vật liệu từ chiều dày; phương án thay đổi hình học cần tính lại.'),
('Kiểm chứng','ACTUAL/SAMPLE/SYNTHETIC tách khỏi trạng thái đã kiểm; dữ liệu test tách theo công trình.')],[1.5,5.5])
h('7.1 Bộ dữ liệu cần chuẩn bị',2)
p('Mỗi hồ sơ gồm CAD gốc, danh mục hình, nhãn cấu kiện, số đo có nguồn, liên kết hình–chi tiết và đáp án có người kiểm. Bộ nghiệm thu phải gồm tên layer/block mới, block lồng và xoay, nhiều tỷ lệ, cửa không có bảng thống kê, kích thước ghi đè và các hồ sơ thiếu dữ liệu. Biến thể tổng hợp dùng kiểm tra bất biến, không thay hồ sơ thật.')
p('README ground_truth/du_toan hiện ghi hai hồ sơ ACTUAL và đáp án chưa được kiểm độc lập đủ điều kiện chỉ tiêu chính. Đây là trạng thái được tài liệu nguồn ghi nhận; chưa kiểm lại từng dòng dữ liệu trong lần lập tài liệu này. Không công bố độ chính xác nhận dạng từ số lượng hồ sơ hoặc từ chạy đúng công thức.')
h('7.2 Chỉ số nghiệm thu',2)
bullets(['Độ đúng/độ phủ nhận dạng cấu kiện trên danh sách đáp án đầy đủ.','Tỷ lệ số đo liên kết đúng cấu kiện, đúng đơn vị và đúng hình chi tiết.','Sai số khối lượng theo công tác trên hồ sơ đủ đáp án; báo riêng phần không thể đánh giá.','Tỷ lệ dòng có nguồn truy vết; tỷ lệ phát hiện đúng thiếu/mâu thuẫn; số lần tính trùng.','Không gộp hồ sơ có đáp án chưa kiểm với nhóm nghiệm thu chính; mọi báo cáo có mẫu số và danh sách hồ sơ bị loại.'])

h(chapters[7])
stages=[('Giai đoạn 1','Chốt hiện trạng','Xuất schema thực tế chỉ đọc, thống kê dữ liệu, so ORM–SQL–DB. Kiểm tra constraint chưa validate, null/orphan và phiên bản triển khai.'),('Giai đoạn 2','Khép nguồn và snapshot','Thêm metadata file, schema_version/result_hash/confirmed_by; truyền liên kết file đúng; chụp manifest đầu vào. Chưa yêu cầu tách toàn bộ JSON.'),('Giai đoạn 3','Lưu nhận dạng có cấu trúc','Triển khai extraction, view, level, element, occurrence, measurement, evidence, relation và issue cùng các luồng ghi/đọc thực tế.'),('Giai đoạn 4','Tách công tác và phương án','Tạo takeoff_items cùng material_scenarios/assignments/requirements khi cần truy vấn/so sánh; đồng thời giữ snapshot tương thích.'),('Giai đoạn 5','Làm sạch danh mục','Thêm FK/CHECK sau khi xử lý mã không khớp, token và đơn vị. Loại cột legacy chỉ sau kiểm caller và chuyển dữ liệu.')]
table(['Bước','Mục tiêu','Công việc'],stages,[1.0,1.7,4.3])
h('8.1 Ánh xạ dữ liệu cũ',2)
bullets(['takeoff_results.result/input → snapshot gốc được giữ nguyên; chỉ tách những cấu kiện/số đo thật sự có trong JSON.','Kết quả cũ không có source handle/file hash được đánh dấu LEGACY_UNVERIFIED trong metadata; không tự tạo bằng chứng hoặc người xác nhận.','file_id thiếu chỉ backfill khi tìm được căn cứ duy nhất. Không ghép file chỉ theo tên gần giống.','rule_id và nội dung/hash được chụp; không nối lịch sử theo ID tự tăng sau lần reload.','Mỗi migration có mã phiên bản, tiền điều kiện, số dòng trước/sau, bước đối chiếu, khả năng chạy lại và kế hoạch rollback.'])
h('8.2 Quy tắc tương thích',2)
p('Thực hiện expand → backfill → kiểm tra → chuyển reader → ngừng đường cũ. Trong giai đoạn ghi kép, một giao dịch phải đảm bảo bảng mới và snapshot không lệch nhau; nếu thao tác file ngoài DB thì có trạng thái pending và bước khôi phục. Không xóa bảng/cột đang được API cũ sử dụng. Rollback ứng dụng vẫn phải đọc được JSONB được giữ lại.')

h(chapters[8])
h('9.1 Quyền và bảo toàn dữ liệu',2)
p('Mọi truy vấn dự án phải kiểm quyền sở hữu/vai trò. Không dựa vào việc biết project_id hoặc file_id. Tài khoản ứng dụng chỉ có quyền cần thiết; tài khoản chạy migration tách riêng. Mật khẩu chỉ lưu hash; không ghi connection string, token hoặc password_hash trong nhật ký/export thông thường.')
p('Xóa user/project hiện có nhiều quan hệ CASCADE; cần thiết kế chính sách giữ/xóa dữ liệu trước khi mở chức năng xóa. Đề xuất khóa chỉnh sửa snapshot đã xác nhận, cho phép tạo phiên bản mới; đây là chính sách mới, chưa phải hành vi DB hiện có.')
h('9.2 Sao lưu và quan sát',2)
bullets(['Sao lưu PostgreSQL cùng file CAD/mô hình và manifest hash; backup DB riêng không khôi phục được stored_path đã mất file.','Kiểm thử restore trên môi trường riêng; đo thời gian và mức mất dữ liệu chấp nhận được rồi mới chốt lịch backup.','Theo dõi lần trích xuất lỗi/chậm, issue chưa xử lý, file mất, bản ghi không có nguồn và lệch snapshot.','Thử nghiệm hiệu năng bằng tập CAD thực tế; chỉ tối ưu index/partition khi có kế hoạch truy vấn và số đo.'])
h('9.3 Ma trận kiểm thử',2)
tests=[('T01','Cấu kiện chưa biết vật liệu','Lưu được cấu kiện và khối lượng; nhu cầu vật liệu vẫn chưa xác định.'),('T02','Một cột trên ba hình','Một element, ba occurrence; không nhân ba khối lượng.'),('T03','Hai số đo mâu thuẫn','Giữ cả hai ứng viên và issue; chỉ một giá trị được chấp nhận.'),('T04','Quan hệ chéo dự án','Giao dịch bị từ chối dù từng ID riêng lẻ tồn tại.'),('T05','Cập nhật file cùng tên','Tạo phiên bản/hash mới; snapshot cũ vẫn trỏ file cũ.'),('T06','Nhiều tỷ lệ và block lồng','Biến đổi đúng; source_ref phân biệt INSERT lặp.'),('T07','Thiếu số đo','quantity chưa đầy đủ là NULL; known_part không bị mất.'),('T08','Dòng khấu trừ','Cho phép lượng âm hợp lệ; tổng đúng theo đơn vị.'),('T09','Thay giá/định mức cùng ngày','Lần chạy cũ vẫn giải thích được bằng snapshot cũ.'),('T10','Chạy lại migration/backfill','Không nhân bản; số dòng và hash kiểm tra nhất quán.'),('T11','Chọn phương án đổi độ dày','Bắt buộc tính lại phần hình học/công tác chịu ảnh hưởng.'),('T12','Restore DB và file','Mở lại nguồn, kiểm hash và tái hiện được ví dụ kiểm thử.')]
table(['Mã','Tình huống','Kết quả mong đợi'],tests,[.5,2.2,4.3])
p('Ma trận trên là yêu cầu kiểm thử đề xuất. Tài liệu này không tuyên bố đã chạy các ca trên ứng dụng hoặc database. Kiểm tra thực hiện cho tài liệu gồm đối chiếu metadata, tính đầy đủ của từ điển và kiểm tra bố cục Word.')

h(chapters[9])
p('Ví dụ giả định: bản CAD thể hiện tường dài 5.000 mm, cao 3.000 mm, dày 200 mm; một cửa rộng 900 mm, cao 2.200 mm. Hồ sơ chưa ghi vật liệu. Bỏ qua giao cột/dầm trong ví dụ để tập trung vào cách lưu dữ liệu.')
example=[('projects / project_files','CT001; KT_R01.dxf; mã băm file gốc.'),('extraction_runs','EX001; parser và cấu hình; manifest chứa file kiến trúc/kết cấu sử dụng.'),('drawing_views / building_levels','Mặt bằng tầng 1, mặt cắt A-A; cao độ và biến đổi tọa độ.'),('building_elements','W1 là tường, O1 là cửa; chưa có vật liệu.'),('element_occurrences','W1 xuất hiện trên mặt bằng và mặt cắt; cùng một cấu kiện.'),('element_measurements','W1: 5000/3000/200 mm; O1: 900/2200 mm; mỗi giá trị có trạng thái và nguồn.'),('evidence_sources / measurement_evidence','Chiều dài từ DIMENSION; chiều cao từ mặt cắt; cửa từ bảng cửa hoặc số đo có căn cứ.'),('element_relations','O1 OPENING_IN W1.'),('takeoff_items','Diện tích thuần 13,02 m²; khối tường 2,604 m³, công thức và đầu vào được chụp.'),('material_scenarios / assignments','Phương án A đang chờ chọn vật liệu; UNKNOWN, material_id NULL.'),('material_requirements','Chưa ra số lượng viên/vữa vì chưa chọn quy cách và định mức.')]
table(['Bảng','Dữ liệu minh họa'],example,[2.5,4.5])
p('Công thức: diện tích thuần = 5 × 3 − 0,9 × 2,2 = 13,02 m²; khối tường = 13,02 × 0,2 = 2,604 m³. Đây là khối lượng hình học; chỉ gọi là khối xây đã xác nhận khi loại cấu kiện và phương pháp đo bóc được kiểm tra phù hợp.')
p('Sau khi người dùng chọn phương án gạch X phù hợp chiều dày thiết kế, assignment chuyển SELECTED và giữ nguồn USER. Lượng gạch = khối xây × hệ số viên/m³ của đúng quy cách. Nếu hệ số vữa hoặc hao hụt thiếu thì chỉ phần tương ứng chưa hoàn chỉnh; không dùng số mặc định để lấp chỗ trống.')

h(chapters[10])
p('Chưa cần làm lại toàn bộ database. Ưu tiên đầu tiên là xác định nguồn thẩm quyền, khép liên kết file và đóng băng đầu vào. Tiếp theo mới bổ sung cấu trúc số đo/cấu kiện phục vụ nhận dạng trên hồ sơ chưa gặp. Danh mục và định mức được dùng sau bước khối lượng, không dùng để ép cấu kiện phải có sẵn vật liệu.')
table(['Nhóm','Quyết định'],[('26 bảng hiện có','Giữ làm nền tảng; chỉnh ràng buộc và truy vết theo phát hiện.'),('14 bảng logic bổ sung','Thiết kế đích đề xuất; đưa vào theo luồng được triển khai, không tạo bảng trống cho đủ số lượng.'),('drawing_entities / kho phân tích riêng','Chưa đưa vào thiết kế triển khai ban đầu; chỉ bổ sung khi có nhu cầu đo được.'),('Định mức và pháp lý','Phải xác minh nguồn và phiên bản; tài liệu này không xác nhận tính hiệu lực của văn bản được ghi trong code.'),('Database thực tế','Cần introspection chỉ đọc trước khi lập migration chính thức.')],[2.0,5.0])

h(chapters[11])
p('Phụ lục được sinh từ metadata SQLAlchemy hiện tại: 26 bảng, 273 cột. PK = khóa chính; FK = khóa ngoại; NN = không cho NULL; NULL = cho phép NULL. Các mô tả là diễn giải nghiệp vụ, còn kiểu/khóa/default được đọc từ khai báo. Default liệt kê ở đây là server_default; default phía Python không được coi là default ở PostgreSQL.')
for t in META:
    h(t['name']+'   '+t['title'],2);p(PURPOSE[t['name']])
    rows=[]
    for c in t['columns']:
        flags=('PK; ' if c['pk'] else '')+('NULL' if c['nullable'] else 'NN')
        desc=meaning(c)
        if c['fk']:desc+=' FK → '+', '.join(f['target']+(' [xóa: '+f['delete']+']' if f['delete'] else ' [xóa: mặc định]') for f in c['fk'])+'.'
        if c['default'] is not None:desc+=' Mặc định DB: '+c['default']+'.'
        rows.append((c['name'],c['type']+'\n'+flags,desc))
    table(['Cột','Kiểu và khóa','Ý nghĩa và liên kết'],rows,[1.75,1.35,3.9])
    if t['unique']:p('UNIQUE: '+'; '.join('('+', '.join(x)+')' for x in t['unique']))
    if t['constraints']:
        p('CHECK đang khai báo:')
        for s in t['constraints']:p(s)
    if t['indexes']:
        p('Chỉ mục khai báo: '+'; '.join(i['name']+(' [UNIQUE]' if i['unique'] else '')+' ('+', '.join(i['columns'])+')' for i in t['indexes']))
    if not t['constraints']:p('Không có CHECK cấp bảng được khai báo trong metadata. Điều này không loại trừ kiểm tra tại ứng dụng.')

doc.add_page_break();h(chapters[12])
h('B1 Nguồn trong dự án',2)
sources=['src/optimat/db/models.py','src/optimat/db/session.py','src/optimat/catalog/repository.py','src/optimat/drawing/takeoff.py','src/optimat/drawing/dimensions.py','src/optimat/drawing/review.py','src/optimat/rough/models.py','src/optimat/rough/materials.py','src/optimat/rough/takeoff.py','scripts/export_sql.py','sql/01_schema.sql','data/ground_truth/du_toan/README.md']
table(['Đường dẫn tương đối từ gốc optimat-ai','Dấu vết kiểm tra'],[(s,hashlib.sha256((ROOT/s).read_bytes()).hexdigest()[:16]) for s in sources],[5.25,1.75])
p('Dấu vết là 16 ký tự đầu SHA-256 tại lúc tạo tài liệu, dùng nhận biết nguồn đã thay đổi; không thay thế lưu bản mã nguồn đầy đủ.')
h('B2 Tài liệu tham khảo người dùng cung cấp',2)
p('Nguồn: '+ZIP.name+'. Chỉ dùng làm tham chiếu phương pháp; không coi nội dung lĩnh vực khác là sự thật nghiệp vụ OptiMat.')
for n,size in refstats:p(n)
h('B3 Truy vấn introspection chỉ đọc',2)
p('Chạy trên môi trường được cấp quyền trước khi lập migration. Không xuất dữ liệu bí mật; kết quả dùng so sánh schema thực tế với phụ lục A.')
queries=["SELECT table_name, ordinal_position, column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'public' ORDER BY table_name, ordinal_position;", "SELECT conrelid::regclass AS table_name, conname, contype, convalidated, pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE connamespace = 'public'::regnamespace ORDER BY 1, 2;", "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;", "SELECT t.takeoff_id FROM takeoff_results t JOIN project_files f ON f.file_id = t.file_id WHERE t.project_id <> f.project_id;", "SELECT r.run_id FROM optimization_runs r JOIN takeoff_results t ON t.takeoff_id = r.takeoff_id WHERE r.project_id <> t.project_id;"]
for i,q in enumerate(queries,1):
    h('Truy vấn '+str(i),3);para=p(q)
    for r in para.runs:r.font.name='Consolas';r.font.size=Pt(9)
h('B4 Giới hạn kiểm tra',2)
p('Đã đọc cấu trúc mã nguồn và SQL; không mở connection string hay truy vấn PostgreSQL đang chạy. Chưa chạy migration, benchmark hoặc toàn bộ regression của ứng dụng. Không thực hiện thay đổi bảng/cột, dữ liệu nghiệp vụ hoặc script SQL hiện hành. Tài liệu mô tả thiết kế mục tiêu để triển khai tiếp, không chứng nhận hệ thống đã nhận diện mọi bản vẽ.')

doc.core_properties.title='Tài liệu database toàn hệ thống OptiMat AI'
doc.core_properties.subject='Hiện trạng và thiết kế chỉnh sửa đề xuất'
doc.core_properties.author='OptiMat AI'
doc.core_properties.keywords='PostgreSQL, CAD, bóc tách, vật liệu, database'
doc.save(OUT)
# Basic coverage validation independent of rendering.
assert len(META)==26 and sum(len(t['columns']) for t in META)==273
assert len(TARGET)==14
assert all(n in BY for _,ns in groups for n in ns)
print(json.dumps({'output':str(OUT),'tables':len(META),'columns':273,'proposed_tables':len(TARGET),'paragraphs':len(doc.paragraphs),'word_tables':len(doc.tables)},ensure_ascii=True))
