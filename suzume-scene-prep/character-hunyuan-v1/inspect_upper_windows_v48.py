from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path(__file__).parent;O=R/'poster-upper-windows-v48';O.mkdir(exist_ok=True);F=R/'poster-fascia-v47';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
S=json.loads((F/'source-fascia-v47.json').read_text());D=np.load(F/'source-fascia-v47.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels']
def project(v):
 q=(np.asarray(v)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
vv=[];ff=[];face_keys=[];face_indices=[];offset=0
for j,row in enumerate(S['objects']):
 v=D[row['key']+'_vertices'];faces=D[row['key']+'_faces'];vv.append(v);ff.append(faces+offset);face_keys.extend([j]*len(faces));face_indices.extend(range(len(faces)));offset+=len(v)
v=np.concatenate(vv);faces=np.concatenate(ff);face_keys=np.array(face_keys);face_indices=np.array(face_indices)
uv,inv=np.unique(v.round(5),axis=0,return_inverse=True);fi=inv[faces];edges=np.concatenate([fi[:,[0,1]],fi[:,[1,2]],fi[:,[2,0]]]);graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(uv),len(uv)));count,labels=connected_components(graph,directed=False);fl=labels[fi[:,0]]
rows=[];selection={}
for label in range(count):
 ids=np.flatnonzero(fl==label);pts=v[np.unique(faces[ids])];lo=pts.min(0);hi=pts.max(0);mid=pts.mean(0);rad=np.linalg.norm(mid[:2]);ang=np.arctan2(mid[0],mid[1])
 if not(5.60<lo[2]<6.425 and hi[2]<6.425 and 22.7<rad<24.0 and -.95<ang<-.19):continue
 screen=project(pts);sub={}
 for key_index in np.unique(face_keys[ids]):sub[S['objects'][key_index]['key']]=face_indices[ids[face_keys[ids]==key_index]].tolist()
 rows.append({'component':label,'triangles':len(ids),'nativeBounds':[lo.tolist(),hi.tolist()],'imageBounds':[screen.min(0).tolist(),screen.max(0).tolist()],'angle':float(ang),'meanRadius':float(rad),'parts':sub})
print('COMPONENTS',len(rows))
for q in rows:print(q['component'],q['triangles'],[np.round(p,2).tolist() for p in q['imageBounds']],np.round(np.array(q['nativeBounds'])[:,2],3).tolist(),list(q['parts']))
(O/'upper-window-components-v48.json').write_text(json.dumps({'sourceGeometryNativeSha256':S['sourceNativeSha256'],'sourceGeometryUnchangedInV47':True,'components':rows},indent=2))
ref=Image.open(V/'reference-hires.jpg').convert('RGB').resize((2124,3000)).crop((0,558*3,280*3,595*3));cur=Image.open(F/'fascia-detail-v47.png').convert('RGB').crop((0,(558-495)*3,280*3,(585-495)*3))
ref.save(O/'upper-reference-strip-v48.png');cur.save(O/'upper-current-strip-v48.png')
fig,axs=plt.subplots(2,1,figsize=(16,6),dpi=150)
axs[0].imshow(ref,extent=(0,280,595,558));axs[1].imshow(cur,extent=(0,280,585,558))
for q in rows:
 (x0,y0),(x1,y1)=q['imageBounds']
 if x1-x0>10:axs[1].plot([x0,x1,x1,x0,x0],[y0,y0,y1,y1,y0],lw=.6);axs[1].text(x0,y1,str(q['component']),fontsize=6)
for ax,title in zip(axs,['Reference upper facade','v47 with physical component bounds']):ax.set_title(title);ax.set_xlim(0,280);ax.set_ylim(595,558);ax.set_xticks(np.arange(0,281,10));ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(O/'upper-window-diagnosis-v48.png');plt.close(fig)
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
for i in range(12,16):
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;t=np.array([np.cos(a),-np.sin(a),0]);rad=np.array([np.sin(a),np.cos(a),0]);w=2*23.5*np.sin(h)+.022;center=rad*(23.5*np.cos(h));print('BAY',i,project([center-t*w/2+[0,0,6.03],center+t*w/2+[0,0,6.03]]).round(2).tolist())
