from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
r=Path('suzume-scene-prep/character-hunyuan-v1');o=r/'poster-foreground-v51';s=json.loads((o/'source-foreground-v51.json').read_text());d=np.load(o/'source-foreground-v51.npz');vv=[];ff=[];keys=[];indices=[];offset=0
for j,row in enumerate(s['objects']):
 v=d[row['key']+'_vertices'];f=d[row['key']+'_faces'];vv.append(v);ff.append(f+offset);keys.extend([j]*len(f));indices.extend(range(len(f)));offset+=len(v)
v=np.concatenate(vv);faces=np.concatenate(ff);keys=np.array(keys);indices=np.array(indices);unique,inv=np.unique(v.round(5),axis=0,return_inverse=True);fi=inv[faces];e=np.concatenate([fi[:,[0,1]],fi[:,[1,2]],fi[:,[2,0]]]);g=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(unique),len(unique)));_,labels=connected_components(g,directed=False);fl=labels[fi[:,0]];order=np.argsort(fl);groups=np.split(order,np.flatnonzero(np.diff(fl[order]))+1);c=np.array(s['camera']['position']);rot=np.array(s['camera']['rotation']);f=s['camera']['focalPixels'];rows=[]
for ids in groups:
 p=v[np.unique(faces[ids])];lo=p.min(0);hi=p.max(0);q=(p-c)@rot;uv=np.c_[354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]];x0,y0=uv.min(0);x1,y1=uv.max(0)
 if not(130<x0<x1<280 and 667<y0<y1<715):continue
 parts={s['objects'][j]['key']:indices[ids[keys[ids]==j]].tolist() for j in np.unique(keys[ids])};row={'component':int(fl[ids[0]]),'nativeBounds':[lo.tolist(),hi.tolist()],'screenBounds':[[x0,y0],[x1,y1]],'parts':parts};rows.append(row);print(row['component'],len(ids),np.round(row['screenBounds'],1).tolist(),'z',np.round([lo[2],hi[2]],3).tolist(),list(parts))
(o/'prop-components-v51.json').write_text(json.dumps({'sourceNativeSha256':s['sourceNativeSha256'],'components':rows},separators=(',',':')))
