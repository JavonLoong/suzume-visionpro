import trimesh,numpy as np,json,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=RuntimeWarning)
R=Path(__file__).resolve().parents[1];P=R/'analysis'/'prepared';P.mkdir(exist_ok=True)
report={};S=400/58
for cat in ['wall','steel','ground','frame','leaf']:
 d=np.load(R/'analysis'/(cat+'.npz'));m=trimesh.Trimesh(d['vertices']*S,d['faces'],process=True)
 parts=m.split(only_watertight=False);keep=[];dropped=[]
 for i,c in enumerate(parts):
  c.merge_vertices(digits_vertex=5)
  c.update_faces(c.nondegenerate_faces());c.update_faces(c.unique_faces());c.remove_unreferenced_vertices()
  if not len(c.faces):continue
  c.fix_normals(multibody=True)
  # Ignore painted chips and decals with no physical thickness; do not turn them into lumps.
  centered=c.vertices-c.vertices.mean(axis=0)
  vals,axes=np.linalg.eigh(centered.T@centered)
  ext=np.ptp(centered@axes,axis=0)
  if min(ext)<.025 or (c.is_watertight and abs(c.volume)<.012):
   dropped.append({'component':i,'faces':len(c.faces),'reason':'paint decal / sub-resolution chip','pca_extents_mm':ext.tolist()});continue
  # Thicken slender isolated mullions/rods without scaling their length.
  target=.85 if cat=='wall' else (1.2 if cat=='steel' else .7)
  if cat in ['wall','steel'] and max(ext)<30 and min(ext)<target:
   projected=centered@axes
   projected*=np.maximum(ext,target)/np.maximum(ext,1e-9)
   c.vertices=projected@axes.T+c.vertices.mean(axis=0)
  if cat in ['frame','leaf'] and max(ext)<2 and abs(c.volume)<.1:
   dropped.append({'component':i,'faces':len(c.faces),'reason':'door weathering / sub-resolution detail'});continue
  c.vertices[:,2]+=5
  keep.append(c)
 if keep:
  joined=trimesh.util.concatenate(keep)
  np.savez_compressed(P/(cat+'.npz'),vertices=joined.vertices,faces=joined.faces)
 report[cat]={'source_components':len(parts),'kept':len(keep),'dropped':dropped,'triangles':sum(len(c.faces) for c in keep)}
 print(cat,len(keep),'kept;',len(dropped),'discarded paint/tiny elements',flush=True)
(R/'analysis'/'physical-adaptations.json').write_text(json.dumps(report,indent=2))
