import json,time,warnings,sys
from pathlib import Path
import numpy as np,trimesh,pymeshlab as pm
R=Path(__file__).resolve().parents[1];OLD=R.parent/'print-400mm-20261030';warnings.filterwarnings('ignore');np.random.seed(4103)
d=json.loads((OLD/'交付文件/零件清单.json').read_text(encoding='utf8'));reports=[]
for row in d['parts']:
 name=row['id']
 if name.startswith('B') or (len(sys.argv)>1 and not any(name.startswith(s) for s in sys.argv[1:])):continue
 start=time.time();q=np.load(OLD/'analysis/assembly_meshes'/(name+'.npz'));mesh=trimesh.Trimesh(q['vertices'],q['faces'],process=True)
 components=[]
 for part in mesh.split(only_watertight=False):
  components.append({'volume_mm3':float(part.volume),'faces':len(part.faces),'bounds_mm':part.bounds.tolist(),'extent_mm':part.extents.tolist(),'touches_mounting_plane':bool(part.bounds[0,2]<5.1)})
 ms=pm.MeshSet();ms.add_mesh(pm.Mesh(mesh.vertices,mesh.faces));ms.compute_selection_by_self_intersections_per_face()
 sel=ms.current_mesh().face_selection_array();self_faces=int(sel.sum())
 if self_faces:np.savez_compressed(R/'analysis'/(name+'_self_intersections.npz'),centers=mesh.triangles_center[sel])
 count=1200 if name[0] in 'WS' and '_附件' not in name else 500
 points,faces=trimesh.sample.sample_surface(mesh,count);normals=mesh.face_normals[faces];orig=points-normals*.0001
 hit,ids,tid=mesh.ray.intersects_location(orig,-normals,multiple_hits=False)
 thickness=np.linalg.norm(hit-orig[ids],axis=1)
 valid=thickness>.0003;thickness=thickness[valid];ids=ids[valid];faces=faces[ids];points=points[ids]
 np.savez_compressed(R/'analysis'/(name+'_thickness.npz'),points=points,thickness=thickness)
 result={'id':name,'watertight':bool(mesh.is_watertight),'consistent_normals':bool(mesh.is_winding_consistent),'volume_mm3':float(mesh.volume),'self_intersecting_faces':self_faces,'zero_area_faces':int((mesh.area_faces<1e-12).sum()),'components':components,'samples':len(thickness),'thickness_percentiles_mm':np.percentile(thickness,[1,5,10,50]).tolist() if len(thickness) else [],'sample_fraction_below_04':float((thickness<.4).mean()),'sample_fraction_below_08':float((thickness<.8).mean()),'seconds':round(time.time()-start,1)}
 reports.append(result);(R/'analysis/geometry-audit.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(result,ensure_ascii=False),flush=True)
