"""Repair local UV sampling; the original texture images remain unchanged."""
from pathlib import Path
import numpy as np,json,hashlib
from PIL import Image
from scipy.spatial import cKDTree
R=Path(__file__).parent;O=R/'movie-collar-v37';a=np.load(O/'body-source-v37.npz');fit=np.load(O/'collar-fit-v37.npz');w=a['world'];uv=a['uv'];loop=fit['seamBefore']
W=R/'viewer/character-v36';g=json.loads((W/'suzume-posed-v36.gltf').read_text());node=next(n for n in g['nodes'] if n.get('name','').startswith('Suzume Hunyuan textured'));mat=g['materials'][g['meshes'][node['mesh']]['primitives'][0]['material']];ti=mat['pbrMetallicRoughness']['baseColorTexture']['index'];image=W/g['images'][g['textures'][ti]['source']]['uri'];rgb=np.array(Image.open(image).convert('RGB'));h,width=rgb.shape[:2]
def sample(p):return rgb[np.clip(((1-p[:,1])*h).astype(int),0,h-1),np.clip((p[:,0]*width).astype(int),0,width-1)].astype(float)
colors=sample(uv);distance,nearest=cKDTree(loop).query(w);cloth=(distance<.017)&(loop[nearest,2]>2.492);ids=np.flatnonzero(cloth);tree=cKDTree(w);out=uv.copy();chosen=[];failed=[]
for i in ids:
 aim=w[i]-np.array([0,0,.024]);dist,near=tree.query(aim,k=256);c=colors[near];duv=np.linalg.norm(uv[near]-uv[i],axis=1);clean=(c[:,0]-c[:,2]<18)&(c[:,0]-c[:,1]<12)&(c.mean(1)>90)&(duv<.045)&(dist<.027)
 if not clean.any():failed.append(int(i));continue
 score=dist+.12*duv;score[~clean]=np.inf;j=near[score.argmin()];fade=float(np.clip((.017-distance[i])/.009,0,1));fade=fade*fade*(3-2*fade);out[i]=uv[i]*(1-fade)+uv[j]*fade;chosen.append([int(i),int(j)])
changed=np.linalg.norm(out-uv,axis=1)>1e-10
np.savez_compressed(O/'collar-uv-v37.npz',before=uv,after=out,changedMask=changed)
faces=a['faces'];center=w[faces].mean(axis=1);face_color=colors[faces].mean(axis=1);skin=(abs(center[:,0]+.145)<.065)&(center[:,1]>.81)&(center[:,2]>2.435)&(center[:,2]<2.49)&(face_color[:,0]-face_color[:,2]>35)&(face_color[:,0]-face_color[:,1]>18)
(O/'neck-chest-skin-faces-v37.json').write_text(json.dumps(np.flatnonzero(skin).tolist()))
report={'revision':37,'changedUVVertices':int(changed.sum()),'selectedClothVertices':len(ids),'unresolvedCandidateVertices':failed,'baseColorImage':str(image),'originalImageSha256':hashlib.sha256(image.read_bytes()).hexdigest(),'texturePixelsUnchanged':True,'method':'Move only UV samples in the 17 mm cloth edge band to nearby clean fabric in the same atlas chart; front bare-skin segment is excluded.'}
report['neckChestSkinTriangles']=int(skin.sum())
(O/'uv-repair-v37.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
