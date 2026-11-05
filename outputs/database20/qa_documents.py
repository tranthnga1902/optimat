from pathlib import Path
import json
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
reports=[]
for stem in ['OptiMat_AI_CSDL_20_bang','OptiMat_AI_Ke_hoach_hoan_thien_data']:
    pdf=pdfium.PdfDocument(str(ROOT/'render'/f'{stem}.pdf'))
    target=ROOT/'render'/stem;target.mkdir(exist_ok=True)
    thumbnails=[]
    for i in range(len(pdf)):
        im=pdf[i].render(scale=1.6).to_pil().convert('RGB');im.save(target/f'page-{i+1:02}.png')
        im.thumbnail((306,405));tile=Image.new('RGB',(326,440),'#DDE2E6')
        tile.paste(im,((326-im.width)//2,10));ImageDraw.Draw(tile).text((10,423),str(i+1),fill='black');thumbnails.append(tile)
    for i in range(0,len(thumbnails),6):
        sheet=Image.new('RGB',(978,880),'white')
        for j,im in enumerate(thumbnails[i:i+6]):sheet.paste(im,((j%3)*326,(j//3)*440))
        sheet.save(target/f'contact-{i//6+1}.png')
    reader=PdfReader(ROOT/'render'/f'{stem}.pdf')
    reports.append({'file':stem,'pages':len(pdf),'near_blank_pages':[i+1 for i,p in enumerate(reader.pages) if len(p.extract_text() or '')<100]})
print(json.dumps(reports,ensure_ascii=True))
