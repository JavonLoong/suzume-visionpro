from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
R=Path(__file__).parent;O=R/'poster-steel-v39';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
g=json.loads((O/'steel-geometry-v39.json').read_text());source=json.loads((O/'source-steel-v39.json').read_text());d=np.load(O/'steel-original-v39.npz');M=np.array(g['camera']['matrixWorld']);C=M[:3,3];f=g['camera']['lens']/36*2824
def project(p):
 q=(np.asarray(p)-C)@M[:3,:3];return np.c_[1000+f*q[:,0]/-q[:,2],1412-f*q[:,1]/-q[:,2]]
lo,hi=g['removeRingAngularInterval'];masks={};rows=[]
for rec in source:
 k=rec['key'];v=d[k+'_vertices'];faces=d[k+'_faces'];_,inv=np.unique(np.round(v,5),axis=0,return_inverse=True);wf=inv[faces];edge=np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]);graph=coo_matrix((np.ones(len(edge)),(edge[:,0],edge[:,1])),shape=(inv.max()+1,inv.max()+1)).tocsr();nc,labels=connected_components(graph,directed=False)
 fl=labels[wf[:,0]];remove=np.zeros(len(faces),bool);records=[]
 if k in ['mesh0','mesh1','mesh2']:
  for idx in range(nc):
   which=np.flatnonzero(fl==idx);vv=v[np.unique(faces[which])];angle=np.arctan2(vv[:,0],vv[:,1]);z=vv[:,2];r=np.linalg.norm(vv[:,:2],axis=1);dome=20.3*np.sqrt(np.maximum(1-(np.maximum(z-5.75,0)/12)**2,0))
   middle=vv.mean(0);middle_dome=20.3*np.sqrt(max(1-(max(middle[2]-5.75,0)/12)**2,0))
   post=k in ['mesh0','mesh1'] and any(np.max(np.abs(angle-a))<.023 for a in [lo,hi]) and abs(np.linalg.norm(middle[:2])-middle_dome)<.35 and z.min()>.50
   ring=k in ['mesh0','mesh1'] and z.min()>5.95 and angle.min()>=lo-.012 and angle.max()<=hi+.012 and np.ptp(angle)>.012 and np.ptp(z)<.42
   foot=k=='mesh2' and any(abs(angle.mean()-a)<.02 for a in [lo,hi])
   stray=k in ['mesh0','mesh1'] and abs(angle.mean()-.981997376282069)<.15 and z.min()>5.75+12*np.sin(.6)
   if post or ring or foot or stray:
    remove[which]=True;records.append({'component':int(idx),'faces':len(which),'reason':'unobserved-rib-tip' if stray else ('footing' if foot else ('post' if post else 'ring')),'centerNative':vv.mean(0).tolist(),'bounds':[vv.min(0).tolist(),vv.max(0).tolist()]})
 masks[k]=remove;rows.append({'name':rec['name'],'key':k,'components':int(nc),'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum()),'removedComponents':records})
np.savez_compressed(O/'steel-removal-v39.npz',**masks)
(O/'removal-v39.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
fig,ax=plt.subplots(figsize=(8.8,10));ax.imshow(Image.open(V/'reference-hires.jpg'))
for member in g['members']:
 p=project(member['centerlineNative']);ax.plot(p[:,0],p[:,1],color='#e42e8b' if member['kind']=='post' else '#37ff86',lw=1,alpha=.8)
for rec in rows:
 if rec['removedComponents']:
  p=project([q['centerNative'] for q in rec['removedComponents']]);ax.scatter(p[:,0],p[:,1],s=7,c='#ff6655',alpha=.7)
ax.set_xlim(1150,2000);ax.set_ylim(1600,650);ax.set_title('New centerlines / removed old component centers');fig.tight_layout();fig.savefig(O/'steel-projection-v39.png',dpi=100)
print(json.dumps([{k:q[k] for k in ['name','components','removedTriangles','retainedTriangles']} for q in rows],indent=2))
