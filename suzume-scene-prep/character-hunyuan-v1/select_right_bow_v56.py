from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent;O=R/'poster-right-bow-v56';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
S=json.loads((O/'source-right-bow-v56.json').read_text());D=np.load(O/'source-right-bow-v56.npz');M=np.array(S['camera']['matrixWorld']);C=M[:3,3];f=S['camera']['lens']/36*1000
def project(p):
 q=(np.asarray(p)-C)@M[:3,:3];return np.c_[354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]]
rows=[];arrays={}
for ob in S['objects']:
 key=ob['key'];v=D[key+'_vertices'];faces=D[key+'_faces'];_,inv=np.unique(np.round(v,5),axis=0,return_inverse=True);w=inv[faces];edges=np.concatenate([w[:,[0,1]],w[:,[1,2]],w[:,[2,0]]]);graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(inv.max()+1,inv.max()+1)).tocsr();n,labels=connected_components(graph,directed=False);groups=labels[w[:,0]];remove=np.zeros(len(faces),bool);components=[]
 for i in range(n):
  which=np.flatnonzero(groups==i);p=v[np.unique(faces[which])];uv=project(p);lo=uv.min(0);hi=uv.max(0)
  if 500<lo[0]<535 and 690<hi[0]<730 and hi[0]-lo[0]>150 and lo[1]>565 and hi[1]<635 and p[:,1].min()>10:
   remove[which]=True;components.append({'component':i,'triangles':len(which),'boundsNative':[p.min(0).tolist(),p.max(0).tolist()],'projectionBounds708':[lo.tolist(),hi.tolist()]})
 arrays[key]=remove
 rows.append({**ob,'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum()),'removedComponents':components})
np.savez_compressed(O/'right-bow-removal-v56.npz',**arrays);(O/'removal-v56.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
ref=Image.open(V/'reference-hires.jpg').crop((500*2000/708,570*2.824,2000,635*2.824)).resize((1040,325),Image.Resampling.LANCZOS).convert('RGB');ref.save(O/'right-bow-reference-v56.png');draw=ImageDraw.Draw(ref)
for u in range(500,709,10):
 x=(u-500)*5;draw.line((x,0,x,325),fill=(150,80,80),width=1);draw.text((x+2,1),str(u),fill='red')
for v in range(575,635,5):
 y=(v-570)*5;draw.line((0,y,1040,y),fill=(80,80,150),width=1);draw.text((2,y+1),str(v),fill='blue')
ref.save(O/'right-bow-reference-grid-v56.png');print(json.dumps(rows,indent=2))
