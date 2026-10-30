import json,math,time
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.signal import correlate
from shapely.geometry import Polygon,box
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];OUT=R.parent/'print-packed-stl-20261030';A=OUT/'analysis';A.mkdir(parents=True,exist_ok=True)
data=json.loads((R/'交付文件/零件清单.json').read_text(encoding='utf8'))
items=[];SIZE=256
for row in data['parts']:
 n=row['id']
 if not (n[0] in 'WS' and '_附件' not in n):continue
 q=np.load(R/'analysis/assembly_meshes'/(n+'.npz'));v=q['vertices'];m=np.array(row['assembly_to_print_matrix']);v=v@m[:3,:3].T+m[:3,3];v-=v.min(axis=0)
 points=np.unique(v[:,:2].round(6),axis=0);h=points[ConvexHull(points).vertices]
 versions=[]
 for turn in range(4):
  angle=turn*math.pi/2;rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
  poly=Polygon(h@rot.T);lo=np.array(poly.bounds[:2]);shape=Polygon(np.array(poly.exterior.coords)[:-1]-lo)
  # Convex silhouettes include every elevated beam; padding allows brims/supports.
  expanded=shape.buffer(4.5,join_style=2);x0,y0,x1,y1=expanded.bounds
  offset=np.floor([x0,y0])-1;extent=np.ceil([x1,y1])-offset+1
  im=Image.new('1',tuple(extent.astype(int)),0);ImageDraw.Draw(im).polygon([tuple(p-offset) for p in np.array(expanded.exterior.coords)],fill=1)
  versions.append({'turn':turn,'mask':np.asarray(im,dtype=np.float32),'rot':rot,'lo':lo,'offset':offset,'shape':shape})
 items.append({'id':n,'area':Polygon(h).area,'versions':versions})
empty=np.zeros((SIZE,SIZE),np.float32);empty[:7,:]=1;empty[-7:,:]=1;empty[:,:7]=1;empty[:,-7:]=1;empty[:29,:19]=1
rng=np.random.default_rng(410);best=None;started=time.time()
for attempt in range(100):
 order=sorted(items,key=lambda a:-(a['area']*(1 if attempt==0 else rng.uniform(.65,1.35))))
 boards=[]
 for item in order:
  chosen=None
  for bi,board in enumerate(boards+[{'occupied':empty.copy(),'parts':[]} ]):
   candidates=[]
   for ver in item['versions']:
    mask=ver['mask'];scores=correlate(board['occupied'],mask,mode='valid',method='fft');yy,xx=np.where(scores<.1)
    if not len(xx):continue
    # Bottom-left packing, alternating the dominant axis between attempts.
    rank=(yy+mask.shape[0])*256+xx if attempt%2==0 else (xx+mask.shape[1])*256+yy
    k=rank.argmin();candidates.append((int(rank[k]),int(xx[k]),int(yy[k]),ver))
   if candidates:
    _,x,y,ver=min(candidates,key=lambda c:c[0]);chosen=(bi,board,x,y,ver);break
  assert chosen is not None,item['id']
  bi,board,x,y,ver=chosen
  if bi==len(boards):boards.append(board)
  mask=ver['mask'];board['occupied'][y:y+mask.shape[0],x:x+mask.shape[1]]+=mask
  board['parts'].append({'id':item['id'],'turn':ver['turn'],'xy':(np.array([x,y])-ver['offset']-ver['lo']).tolist()})
 # Auto-centering in a slicer must preserve the X1C's excluded front-left corner.
 valid=True;layout=[]
 for board in boards:
  polys=[]
  for part in board['parts']:
   it=next(i for i in items if i['id']==part['id']);ver=it['versions'][part['turn']]
   xy=np.array(part['xy'])+ver['lo'];polys.append(Polygon(np.array(ver['shape'].exterior.coords)+xy))
  bounds=np.array([p.bounds for p in polys]);lo=bounds[:,:2].min(axis=0);hi=bounds[:,2:].max(axis=0);shift=np.array([128,128])-(lo+hi)/2
  shifted=[Polygon(np.array(p.exterior.coords)+shift) for p in polys]
  bed=box(7,7,249,249);keepout=box(0,0,18,28)
  if any(not bed.covers(p.buffer(3)) or p.buffer(3).intersects(keepout) for p in shifted):valid=False;break
  if any(shifted[i].distance(shifted[j])<7 for i in range(len(shifted)) for j in range(i)):valid=False;break
  layout.append([dict(p,xy=(np.array(p['xy'])+shift).tolist()) for p in board['parts']])
 if valid and (best is None or len(layout)<len(best)):
  best=layout;print('PACKED',len(best),'large plates',[[p['id'] for p in b] for b in best],flush=True)
  (A/'layout.json').write_text(json.dumps(best,ensure_ascii=False,indent=2),encoding='utf8')
 if best is not None and len(best)<=4:break
assert best is not None
print('PACKING_COMPLETE',len(best),'large plus one small plate','seconds',round(time.time()-started,1),flush=True)
