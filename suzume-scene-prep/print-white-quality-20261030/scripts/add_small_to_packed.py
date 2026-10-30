import json,math
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.signal import correlate
from shapely.geometry import Polygon,box
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R.parent/'print-packed-stl-20261030';A=O/'analysis'
rows=json.loads((R/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts'];byid={r['id']:r for r in rows}
layout=json.loads((A/'layout.json').read_text(encoding='utf8'))
def hull(row):
 q=np.load(R/'analysis/assembly_meshes'/(row['id']+'.npz'));m=np.array(row['assembly_to_print_matrix']);v=q['vertices']@m[:3,:3].T+m[:3,3];v-=v.min(axis=0)
 points=np.unique(v[:,:2].round(6),axis=0);return points[ConvexHull(points).vertices]
def rot(turn):
 a=turn*math.pi/2;return np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
polys=[];im=Image.new('1',(256,256),0);draw=ImageDraw.Draw(im)
draw.rectangle((0,0,255,6),fill=1);draw.rectangle((0,249,255,255),fill=1);draw.rectangle((0,0,6,255),fill=1);draw.rectangle((249,0,255,255),fill=1);draw.rectangle((0,0,18,28),fill=1)
for part in layout[-1]:
 p=Polygon(hull(byid[part['id']])@rot(part['turn']).T+np.array(part['xy']));polys.append(p)
 draw.polygon(list(p.buffer(4.5,join_style=2).exterior.coords),fill=1)
occupied=np.asarray(im,dtype=np.float32)
small=[r for r in rows if not (r['id'][0] in 'WS' and '_附件' not in r['id'])]
small.sort(key=lambda r:-Polygon(hull(r)).area)
for row in small:
 h=hull(row)
 for copy in range(row['quantity']):
  options=[]
  for turn in range(4):
   r=rot(turn);p=Polygon(h@r.T);padded=p.buffer(4.5,join_style=2);lo=np.floor(padded.bounds[:2])-1;hi=np.ceil(padded.bounds[2:])+1
   maskim=Image.new('1',tuple((hi-lo).astype(int)),0);ImageDraw.Draw(maskim).polygon([tuple(x-lo) for x in np.array(padded.exterior.coords)],fill=1);mask=np.asarray(maskim,dtype=np.float32)
   scores=correlate(occupied,mask,mode='valid',method='fft');yy,xx=np.where(scores<.1)
   if len(xx):
    rank=(yy+mask.shape[0])*256+xx;k=rank.argmin();x=int(xx[k]);y=int(yy[k]);options.append((int(rank[k]),turn,x,y,lo,mask))
  assert options,('small part has no room',row['id'],copy)
  _,turn,x,y,lo,mask=min(options,key=lambda c:c[0]);xy=np.array([x,y])-lo
  occupied[y:y+mask.shape[0],x:x+mask.shape[1]]+=mask
  layout[-1].append({'id':row['id'],'turn':turn,'xy':xy.tolist(),'copy':copy+1});polys.append(Polygon(h@rot(turn).T+xy))
b=np.array([p.bounds for p in polys]);shift=np.array([128,128])-(b[:,:2].min(axis=0)+b[:,2:].max(axis=0))/2
for i,p in enumerate(layout[-1]):p['xy']=(np.array(p['xy'])+shift).tolist();polys[i]=Polygon(np.array(polys[i].exterior.coords)+shift)
assert all(box(7,7,249,249).covers(p.buffer(3)) and not p.buffer(3).intersects(box(0,0,18,28)) for p in polys),'recentered plate outside or keepout'
assert all(polys[i].distance(polys[j])>=7 for i in range(len(polys)) for j in range(i)),'parts too close'
from collections import Counter
assert Counter(p['id'] for board in layout for p in board)==Counter({r['id']:r['quantity'] for r in rows})
(A/'layout-final.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf8')
print('COMPLETE_LAYOUT',len(layout),'plates',[len(b) for b in layout],'parts',sum(map(len,layout)),flush=True)
