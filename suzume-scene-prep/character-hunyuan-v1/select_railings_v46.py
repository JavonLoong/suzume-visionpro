from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-railings-v46';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
S=json.loads((O/'source-railings-v46.json').read_text());D=np.load(O/'source-railings-v46.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels']
def project(v):
    q=(v-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
rows=[];masks={};labelsout={}
for ob in S['objects']:
    key=ob['key'];v=D[key+'_vertices'];faces=D[key+'_faces'];uv,inv=np.unique(v.round(5),axis=0,return_inverse=True);fi=inv[faces];edges=np.concatenate([fi[:,[0,1]],fi[:,[1,2]],fi[:,[2,0]]]);mat=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(uv),len(uv)));n,labels=connected_components(mat,directed=False);fl=labels[fi[:,0]];labelsout[key]=fl;masks[key]=np.zeros(len(faces),bool)
    for label in range(n):
        ids=np.flatnonzero(fl==label);pts=v[np.unique(faces[ids])];lo=pts.min(0);hi=pts.max(0);mean=pts.mean(0);rad=float(np.hypot(*mean[:2]));ang=float(np.arctan2(mean[0],mean[1]))
        if not (6.55<lo[2]<7.4 and hi[2]<7.4 and 23.0<rad<23.7 and -.9<ang<-.19):continue
        kind='cornice' if lo[2]<6.61 else 'bar';masks[key][ids]=kind=='bar';screen=project(pts);rows.append({'key':key,'component':int(label),'triangles':len(ids),'kind':kind,'nativeBounds':[lo.tolist(),hi.tolist()],'imageBounds':[screen.min(0).tolist(),screen.max(0).tolist()],'imageCenter':project(mean).tolist(),'angle':ang,'meanRadius':rad})
np.savez_compressed(O/'railing-component-labels-v46.npz',**labelsout);np.savez_compressed(O/'railing-removal-v46.npz',**masks)
(O/'railing-removal-v46.json').write_text(json.dumps({'sourceNativeSha256':S['sourceNativeSha256'],'parts':rows,'removedTriangles':{k:int(m.sum()) for k,m in masks.items()},'selection':'Whole railing pieces at the observed left front roof edge. Cornice candidates are recorded but retained.'},indent=2))
ref=Image.open(V/'reference-hires.jpg').convert('RGB').resize((2124,3000)).crop((0,530*3,280*3,573*3));current=Image.open(R/'poster-rooftops-v45/rooftop-detail-v45.png').convert('RGB').crop((0,105,840,234))
fig,axs=plt.subplots(2,1,figsize=(16,6),dpi=150)
for ax,im,title in zip(axs,[ref,current],['Reference: top and bottom rail','Current: native component bounds']):
    ax.imshow(im,extent=(0,280,573,530));ax.set_title(title);ax.set_ylim(573,530);ax.set_yticks(np.arange(530,574,5));ax.grid(alpha=.35)
for q in rows:
    if q['key']=='mesh18':continue
    (x0,y0),(x1,y1)=q['imageBounds']
    if x1-x0>10:axs[1].plot([x0,x1],[y0,y1],lw=1,label=q['kind'])
fig.tight_layout();fig.savefig(O/'railing-diagnosis-v46.png');plt.close(fig)
print('RAIL_46_SELECTION',len(rows),'removed',sum(m.sum() for m in masks.values()))
print('UPRIGHT_SAMPLES',[(np.round(q['imageCenter'],2).tolist(),np.round(q['imageBounds'],2).tolist()) for q in rows if q['kind']=='bar' and q['nativeBounds'][1][2]-q['nativeBounds'][0][2]>.5 and q['key']!='mesh18'][::10])
