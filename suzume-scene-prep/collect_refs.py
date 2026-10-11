from pathlib import Path
import requests, json, time, concurrent.futures as cf
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
from io import BytesIO
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'collection'; WORK.mkdir(exist_ok=True)
def page(p):
 u=f'https://fancaps.net/movies/MovieImages.php?name=Suzume_2022&movieid=5535&page={p}'
 r=requests.get(u,timeout=25);r.raise_for_status()
 s=BeautifulSoup(r.text,'html.parser');out=[]
 for im in s.select('img'):
  src=im.get('src','')
  if 'mvt.fancaps.net/' in src:
   out.append(dict(id=Path(src).stem,thumb=src,page=u,detail='https://fancaps.net/movies/'+im.parent['href'],p=p))
 return out
def fetch(item):
 path=WORK/(item['id']+'.jpg')
 if not path.exists():
  r=requests.get(item['thumb'],timeout=25);r.raise_for_status();Image.open(BytesIO(r.content)).verify();path.write_bytes(r.content)
 return item
def sheet(items,name):
 w=240;h=125;cols=5
 canvas=Image.new('RGB',(w*cols,h*((len(items)+cols-1)//cols)), '#eee'); d=ImageDraw.Draw(canvas)
 for n,it in enumerate(items):
  path=WORK/(it['id']+'.jpg')
  if not path.exists():continue
  im=Image.open(path).convert('RGB');im.thumbnail((235,100))
  x=n%cols*w;y=n//cols*h;canvas.paste(im,(x,y));d.text((x+3,y+102),f"p{it['p']} / {it['id']}",fill='black')
 canvas.save(WORK/name)
if __name__=='__main__':
 allitems=[]
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  for items in ex.map(page,[1,5,10,15,20,25,30]):allitems.extend(items)
 (WORK/'overview_pages.json').write_text(json.dumps(allitems,indent=2),encoding='utf8')
 sample=[]
 for p in [1,5,10,15,20,25,30]:
  its=[i for i in allitems if i['p']==p];sample.extend(its[::max(1,len(its)//5)][:5])
 with cf.ThreadPoolExecutor(max_workers=4) as ex:
  for f in cf.as_completed([ex.submit(fetch,i) for i in sample]):
   try:f.result()
   except Exception as e:print(type(e).__name__,flush=True)
 sheet(sample,'overview.jpg');print('overview ready',len(allitems),flush=True)
