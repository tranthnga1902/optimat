from pathlib import Path
import json
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from pypdf import PdfReader
P=Path(__file__).resolve().parent
pdf=pdfium.PdfDocument(str(P/'render/review.pdf'))
pages=[]
for i in range(len(pdf)):
    im=pdf[i].render(scale=1.4).to_pil().convert('RGB')
    im.save(P/f'render/page-{i+1:02}.png')
    im.thumbnail((306,405))
    tile=Image.new('RGB',(326,440),'#D9DDE1');tile.paste(im,((326-im.width)//2,22))
    ImageDraw.Draw(tile).text((10,421),f'Page {i+1}',fill='black')
    pages.append(tile)
for j in range(0,len(pages),6):
    sheet=Image.new('RGB',(978,880),'white')
    for k,im in enumerate(pages[j:j+6]):sheet.paste(im,((k%3)*326,(k//3)*440))
    sheet.save(P/f'render/contact-{j//6+1}.png')
reader=PdfReader(P/'render/review.pdf')
stats=[{'page':i+1,'characters':len(p.extract_text() or '')} for i,p in enumerate(reader.pages)]
print(json.dumps({'pages':len(pdf),'low_text_pages':[x for x in stats if x['characters']<220]},ensure_ascii=True))
