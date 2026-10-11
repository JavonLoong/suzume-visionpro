from pathlib import Path
import json, hashlib, shutil, html, zipfile
from PIL import Image,ImageDraw
import collect_refs as c
R=c.ROOT; out=R/'参考图100幅'; imgs=out/'images';imgs.mkdir(parents=True,exist_ok=True)
groups={
'入口与废墟建筑':[183,185,187,188,191,192,193,194,196,198,200,201,203,205,209],
'水池与白门全景':[210,213,216,222,224,228,236,241,243,252,262,263,264,265,268,341,354,430,442,444,446,449],
'门体与水线细节':[220,221,225,227,229,233,234,235,238,240,245,247,249,255,260],
'建筑背景与空间关系':[237,258,330,331,334,335,338,339,340,343,349,352,353,355,358,359,427,428,434,436,439,447,448],
'关门段结构补充':[345,350,351,361,362,378,379,381,384,385,387,389,390,392,396,399,400,402,403,412,418]
}
spec=[(n,g) for g,ns in groups.items() for n in ns]
assert len(spec)==96,len(spec)
records=[]
existing=[('official_front.jpg','官方正面广角视觉图','https://suzume-tojimari-movie.jp/','官网宣传图'),('wide_oblique.jpg','门侧面与池岸台阶','https://www.esquirehk.com/lifestyle/suzume-no-tojumari','媒体刊载画面'),('open_door_front.png','开门近正面','https://knowmore212683881.wordpress.com/2022/09/15/suzume-no-tojimari-review/','转载预告截图'),('approach_bridge.jpg','温泉废墟入口桥','https://sxodim.com/astana/article/sudzume-zakryvayushchaya-dveri','媒体刊载画面')]
for f,title,url,typ in existing:
 records.append(dict(path=R/'references'/f,title=title,source=url,group='较大尺寸参考',kind=typ,note='不同画面版本需分别校准相机。'))
lookup={i['id']:i for i in json.loads((c.WORK/'candidate_pages.json').read_text())}
for n,g in spec:
 id=str(14016000+n); item=lookup[id];p=c.WORK/(id+'.jpg')
 if not p.exists():c.fetch(item)
 note='图库缩略图；用于机位及画面检索，原图页本次被网站验证阻挡。'
 if g=='关门段结构补充':note+=' 有特效、浪花或人物遮挡，只参考可见结构。'
 records.append(dict(path=p,title=f'{g} · 电影截图 {id}',source=item['detail'],gallery=item['page'],group=g,kind='电影截图缩略图',note=note))
hashes={}; cards=[]
for n,r in enumerate(records,1):
 p=r.pop('path');im=Image.open(p);im.verify();w,h=Image.open(p).size
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 assert sha not in hashes,('duplicate',p,hashes.get(sha))
 hashes[sha]=str(p);dest=imgs/f'{n:03d}_{p.name}';shutil.copy2(p,dest)
 r.update(number=n,file='images/'+dest.name,width=w,height=h,sha256=sha)
 # Perceptual hashes annotate related frames; no claim of 100 unique cameras.
 small=Image.open(p).convert('L').resize((9,8));px=list(small.getdata())
 r['dhash']=sum((px[y*9+x]>px[y*9+x+1])<<(y*8+x) for y in range(8) for x in range(8))
for i,r in enumerate(records):
 r['similar_reference_numbers']=[s['number'] for s in records[:i] if (r['dhash']^s['dhash']).bit_count()<=8]
for r in records:
 sim=('近似构图参考编号：'+', '.join(map(str,r['similar_reference_numbers']))) if r['similar_reference_numbers'] else ''
 cards.append(f'''<article data-group="{r['group']}"><a href="{r['file']}"><img loading="lazy" src="{r['file']}" alt="{html.escape(r['title'])}"></a><h2>{r['number']:03d} · {html.escape(r['title'])}</h2><p>{r['width']} × {r['height']} · {r['kind']}</p><p>{r['note']}</p><small>{sim}</small><a href="{html.escape(r['source'])}" target="_blank" rel="noopener">来源 / 原图入口</a></article>''')
(out/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
buttons=''.join(f'<button onclick="filterCards(this.dataset.g)" data-g="{g}">{g}</button>' for g in ['全部']+list(dict.fromkeys(r['group'] for r in records)))
doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>铃芽之旅 · 100幅园林参考</title><style>body{font:15px/1.65 system-ui,'Microsoft YaHei',sans-serif;background:#edf2ee;color:#19382f;margin:0}header,main{max-width:1300px;margin:auto;padding:24px}h1{font-size:30px;margin:0}nav{display:flex;gap:8px;flex-wrap:wrap}button{padding:9px 13px;border:1px solid #abc0b3;border-radius:6px;background:white;color:#234d40;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px}article{padding:16px;background:white;border-radius:10px}img{width:100%;height:190px;object-fit:contain;background:#142720}h2{font-size:16px}p{margin:8px 0}a{color:#216354}small{display:block;color:#82601f}.notice{padding:14px;background:#fff0ca}#count{font-weight:bold}</style><header><h1>铃芽之旅 · 100幅园林建模参考</h1><p>已按画面筛选并校验100个图像文件 · 2026-09-20</p><p class="notice">4幅较大尺寸参考 + 96幅250×140电影截图缩略图。100幅不代表100个独立方位：含同场景不同动作、开合与光照状态，近似构图已提示。没有AI生成、补画或放大。缩略图用于镜头定位，不作为精细建模或混元直接输入。</p><nav>'''+buttons+'''</nav><p id="count">显示100幅</p></header><main class="grid">'''+''.join(cards)+'''</main><script>function filterCards(g){let n=0;document.querySelectorAll('article').forEach(e=>{let show=g==='全部'||e.dataset.group===g;e.hidden=!show;if(show)n++});document.getElementById('count').textContent='显示'+n+'幅'}</script></html>'''
(out/'index.html').write_text(doc,encoding='utf8')
for j in range(4):
 subset=records[j*25:(j+1)*25];canvas=Image.new('RGB',(1250,800),'#edf2ee');d=ImageDraw.Draw(canvas)
 for k,r in enumerate(subset):
  im=Image.open(out/r['file']).convert('RGB');im.thumbnail((240,135));x=k%5*250;y=k//5*160;canvas.paste(im,(x,y));d.text((x+4,y+138),f"{r['number']:03d} | {r['width']}x{r['height']}",fill='black')
 canvas.save(out/f'总览{j+1}.jpg',quality=90)
readme='''# 铃芽之旅园林参考：100幅

打开index.html浏览、分类筛选；images内为100个独立图片文件；manifest.json记录每张图的来源、像素尺寸、SHA256及近似构图编号。

## 实际质量

4幅较大尺寸参考来自上轮资料，96幅是Fancaps公开列表中的电影截图缩略图（250×140）。原图页被网站安全验证阻挡，未取得高清版。保留原像素，不用放大伪装高清。

这100幅不是100个独立机位。已按画面人工筛掉大量纯人物特写和无关场景，但为观察开门、涉水、关门及结构遮挡变化，保留部分相近机位的不同帧。文件SHA256无重复；感知哈希相近的帧在图库及清单里有提示，不能把它们理解为新的方位。

## 建模用途

- 白门及水池全景：对照围合、柱梁、远近关系。
- 斜俯视：观察门脚、周围铺地和水线；不是正交平面图。
- 室内反看水池：补充入口窗框和池边反向关系。
- 门体与水线细节：定位门锁、门板、砖脚、台阶的高清镜头需求。
- 关门段：特效和人物遮挡较多，仅使用看得见的结构，不把特效当实体。

先以4张较大图校准主相机，再利用缩略图决定需要获取哪些高清镜头。现阶段不适合拿96张缩略图直接批量输入混元，也不足以确定精确施工尺寸。完整正交俯视、建筑背面仍未恢复。

图库：https://fancaps.net/movies/MovieImages.php?movieid=5535&name=Suzume_2022
每幅具体来源见manifest.json或index.html的来源按钮。图片版权属于各自权利人。
'''
(out/'说明.md').write_text(readme,encoding='utf8')
with zipfile.ZipFile(R/'铃芽之旅_100幅参考图.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in out.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(out.parent))
print(json.dumps({'count':len(records),'unique_sha256':len(hashes),'groups':{g:sum(r['group']==g for r in records) for g in set(r['group'] for r in records)},'zip':str(R/'铃芽之旅_100幅参考图.zip')},ensure_ascii=False))
