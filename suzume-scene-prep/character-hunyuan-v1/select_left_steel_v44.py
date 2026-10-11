from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
R=Path(__file__).parent;O=R/'poster-left-steel-v44';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
source=json.loads((O/'source-steel-v44.json').read_text());data=np.load(O/'source-steel-v44.npz');cam=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(cam['matrixWorld']);C=M[:3,3];f=cam['lens']/36*1000
def project(p):
    q=(np.asarray(p)-C)@M[:3,:3];return np.c_[354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]]
rows=[];arrays={};fig,ax=plt.subplots(figsize=(8,10));ax.imshow(Image.open(V/'reference-hires.jpg').resize((708,1000)))
for rec in source['objects']:
    k=rec['key'];v=data[k+'_vertices'];faces=data[k+'_faces'];_,inv=np.unique(np.round(v,5),axis=0,return_inverse=True);weld=inv[faces];edges=np.concatenate([weld[:,[0,1]],weld[:,[1,2]],weld[:,[2,0]]]);graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(inv.max()+1,inv.max()+1)).tocsr();count,labels=connected_components(graph,directed=False);groups=labels[weld[:,0]];remove=np.zeros(len(faces),bool);records=[]
    for index in range(count):
        which=np.flatnonzero(groups==index);p=v[np.unique(faces[which])];angles=np.arctan2(p[:,0],p[:,1]);uv=project(p);mid=p.mean(0)
        # Remove whole disconnected old members in the measured far-left bay,
        # including both duplicate outer ribs, their footings and bowed beams.
        in_bay=angles.min()>-0.85 and angles.max()<-.195 and mid[1]>0
        old_ring=k in ['mesh0','mesh1'] and angles.min()>-1.09 and angles.max()<-.195 and np.ptp(angles)>.012 and p[:,2].min()>5.95 and np.ptp(p[:,2])<.43
        stray=k in ['mesh0','mesh1'] and uv[:,0].min()>248 and uv[:,0].max()<305 and uv[:,1].min()>481 and uv[:,1].max()<520 and mid[1]>0
        if in_bay or old_ring or stray:
            remove[which]=True;records.append({'component':int(index),'triangles':len(which),'reason':'measured-left-bay' if in_bay else ('old-misaligned-tie' if old_ring else 'unobserved-tip-fragment'),'boundsNative':[p.min(0).tolist(),p.max(0).tolist()],'projectionBounds708':[uv.min(0).tolist(),uv.max(0).tolist()],'centerNative':mid.tolist()})
    arrays[k]=remove;rows.append({**rec,'components':int(count),'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum()),'removedComponents':records})
    if records:
        uv=project([q['centerNative'] for q in records]);ax.scatter(uv[:,0],uv[:,1],s=9,alpha=.7,label=k)
np.savez_compressed(O/'steel-removal-v44.npz',**arrays);(O/'removal-v44.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');ax.set_xlim(-30,300);ax.set_ylim(725,340);ax.legend();ax.set_title('Whole old-member centers selected for replacement');fig.tight_layout();fig.savefig(O/'removal-inspection-v44.png',dpi=145)
print(json.dumps([{k:q[k] for k in ['name','removedTriangles','retainedTriangles']} for q in rows],indent=2))
