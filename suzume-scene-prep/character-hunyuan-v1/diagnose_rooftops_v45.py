from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path(__file__).parent;O=R/'poster-rooftops-v45';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
S=json.loads((O/'source-rooftops-v45.json').read_text());D=np.load(O/'source-rooftops-v45.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels']
def project(v):
    q=(v-C)@rot;return np.stack((354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]),axis=-1)
rows=[];masks={};components={}
for ob in S['objects']:
    key=ob['key'];v=D[key+'_vertices'];faces=D[key+'_faces'];unique,inv=np.unique(v.round(5),axis=0,return_inverse=True);fi=inv[faces];edges=np.concatenate([fi[:,[0,1]],fi[:,[1,2]],fi[:,[2,0]]]);a=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(unique),len(unique)));n,labels=connected_components(a,directed=False);fl=labels[fi[:,0]];components[key]=fl;masks[key]=np.zeros(len(faces),bool)
    for label in range(n):
        inds=np.flatnonzero(fl==label);pts=v[np.unique(faces[inds])];lo=pts.min(0);hi=pts.max(0);mean=pts.mean(0);rad=float(np.hypot(*mean[:2]));ang=float(np.arctan2(mean[0],mean[1]));uv=project(pts)
        above_roof=lo[2]>=6.50 or (lo[2]>=6.45 and hi[2]-lo[2]>1.0)
        if not above_roof or not -.88<ang<-.19 or not 23.7<rad<26.5:continue
        masks[key][inds]=True;rows.append({'key':key,'component':label,'triangles':len(inds),'angle':ang,'meanRadius':rad,'boundsNative':[lo.tolist(),hi.tolist()],'boundsImage':[uv.min(0).tolist(),uv.max(0).tolist()]})
np.savez_compressed(O/'rooftop-component-labels-v45.npz',**components)
np.savez_compressed(O/'rooftop-removal-v45.npz',**masks)
(O/'rooftop-removal-v45.json').write_text(json.dumps({'sourceNativeSha256':S['sourceNativeSha256'],'selection':'Whole components above native Z 6.50, plus tall attached trim whose minimum Z is 6.45 or higher. Mean radius 23.7..26.5, angle -0.88..-0.19. Front railing, roof slabs, cornice and rear parapet are excluded.','components':rows,'removedTriangles':{k:int(v.sum()) for k,v in masks.items()}},indent=2))
ref=Image.open(V/'reference-hires.jpg').convert('RGB').resize((1416,2000));cur=Image.open(R/'poster-left-steel-v44/poster-front-v44.png').convert('RGB').resize((1416,2000))
fig,axs=plt.subplots(2,1,figsize=(14,7),dpi=150)
for ax,im,title in zip(axs,[ref,cur],['Official reference rooftop','v44 rooftop; selected equipment bounds']):
    ax.imshow(im,extent=(0,708,1000,0));ax.set_xlim(0,300);ax.set_ylim(585,495);ax.set_title(title);ax.grid(alpha=.15)
for q in rows:
    (u0,v0),(u1,v1)=q['boundsImage']
    if q['triangles']<100 and (u1-u0<2 or v1-v0<2):continue
    axs[1].plot([u0,u1,u1,u0,u0],[v0,v0,v1,v1,v0],lw=.7,alpha=.7)
fig.tight_layout();fig.savefig(O/'rooftop-diagnosis-v45.png');plt.close(fig)
print('ROOF_45_COMPONENTS',len(rows),'TRIANGLES',sum(q['triangles'] for q in rows))
for q in rows:
    if q['triangles']>50:print(q['key'],q['component'],q['triangles'],np.round(q['boundsImage'],2).tolist(),np.round(q['boundsNative'],2).tolist())
