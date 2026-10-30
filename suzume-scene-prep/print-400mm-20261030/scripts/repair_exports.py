import json,trimesh,pymeshlab as pm,numpy as np,warnings,hashlib,importlib.util
from pathlib import Path
warnings.filterwarnings('ignore')
R=Path(__file__).resolve().parents[1];OUT=R/'交付文件';A=R/'analysis'/'assembly_meshes';S=OUT/'STL_毫米'
spec=importlib.util.spec_from_file_location('_meshfix',next((R/'.deps'/'pymeshfix').glob('_meshfix*.pyd')));meshfix=importlib.util.module_from_spec(spec);spec.loader.exec_module(meshfix)
manifest=json.loads((OUT/'零件清单.json').read_text(encoding='utf8'));report=[];newrows=[]
for row in manifest['parts']:
 name=row['id'];d=np.load(A/(name+'.npz'));m=trimesh.Trimesh(d['vertices'],d['faces'],process=True)
 pieces=sorted([x for x in m.split(only_watertight=False) if abs(x.volume)>.2],key=lambda x:abs(x.volume),reverse=True)
 for index,mesh in enumerate(pieces):
  subname=name if index==0 else name+f'_散件{index:02d}'
  before=len(mesh.faces)
  if not mesh.is_watertight or not mesh.is_winding_consistent:
   print('REPAIR',subname,flush=True)
   v,f=meshfix.clean_from_arrays(np.asarray(mesh.vertices,dtype=np.float64),np.asarray(mesh.faces,dtype=np.int32),verbose=False,joincomp=False,remove_smallest_components=True)
   mesh=trimesh.Trimesh(v,f,process=True)
  mesh.fix_normals(multibody=True)
  assert mesh.is_watertight,(subname,'repair failed')
  assert mesh.is_winding_consistent,(subname,'normals')
  mesh.export(A/(subname+'.stl'),file_type='stl_ascii')
  np.savez_compressed(A/(subname+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
  pose=np.array(row['assembly_to_print_matrix']);posed=mesh.copy();posed.apply_transform(pose)
  extra_shift=-posed.bounds[0];posed.apply_translation(extra_shift);pose=trimesh.transformations.translation_matrix(extra_shift)@pose
  posed.export(S/(subname+'.stl'),file_type='stl_ascii')
  # STL does not preserve vertex indices. Re-import and verify actual deliverable geometry.
  check=trimesh.load(S/(subname+'.stl'),force='mesh',process=True)
  if not check.is_watertight:
   raise RuntimeError((subname,'STL roundtrip non-manifold'))
  rr=dict(row,id=subname,quantity=row['quantity'] if index==0 else 1,size_mm=posed.extents.round(4).tolist(),triangles=len(mesh.faces),watertight=True,components=1,volume_mm3=round(mesh.volume,3),assembly_bounds_mm=mesh.bounds.round(4).tolist(),assembly_to_print_matrix=pose.tolist(),stl_sha256=hashlib.sha256((S/(subname+'.stl')).read_bytes()).hexdigest())
  newrows.append(rr);report.append({'part':subname,'faces_before':before,'faces_after':len(mesh.faces),'roundtrip_watertight':True})
  print('VERIFIED',subname,len(mesh.faces),flush=True)
manifest['parts']=newrows;manifest['export_validation']=report
(OUT/'零件清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(R/'analysis'/'export-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('VERIFIED_ALL',len(newrows),flush=True)
