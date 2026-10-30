import json,math,hashlib
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];O=R.parent/'print-packed-stl-20261030';A=O/'analysis';S=O/'STL';S.mkdir(exist_ok=True)
rows={r['id']:r for r in json.loads((R/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts']}
layout=json.loads((A/'layout-final.json').read_text(encoding='utf8'));reports=[]
for i,board in enumerate(layout,1):
 meshes=[];groups=[];plates=[]
 for j,part in enumerate(board):
  row=rows[part['id']];q=np.load(R/'analysis/assembly_meshes'/(row['id']+'.npz'));m=np.array(row['assembly_to_print_matrix']);v=q['vertices']@m[:3,:3].T+m[:3,3];v-=v.min(axis=0)
  a=part['turn']*math.pi/2;rot=np.round([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
  v[:,:2]=v[:,:2]@rot.T+np.array(part['xy']);mesh=trimesh.Trimesh(v,q['faces'],process=False)
  assert mesh.is_watertight and mesh.is_winding_consistent and abs(mesh.bounds[0,2])<1e-7,part
  meshes.append(mesh);groups.append(np.full(len(mesh.faces),j));plates.append({'id':part['id'],'bounds_mm':mesh.bounds.tolist(),'faces':len(mesh.faces)})
 combined=trimesh.util.concatenate(meshes);path=S/f'第{i}盘.stl';combined.export(path,file_type='stl_ascii')
 reloaded=trimesh.load(path,force='mesh');components=reloaded.split(only_watertight=False)
 assert len(components)==len(board),(i,'part count mismatch',len(components),len(board))
 assert reloaded.is_watertight and reloaded.is_winding_consistent and all(c.volume>0 for c in components),(i,'invalid STL')
 assert len(reloaded.faces)==len(combined.faces),(i,'lost triangles on export')
 assert np.max(np.abs(reloaded.bounds-combined.bounds))<1e-6,(i,'export changed extents')
 assert np.max(np.abs((reloaded.bounds[:,:2].sum(axis=0)/2)-128))<1e-5,(i,'not centered')
 assert max(reloaded.extents[:2])<242 and reloaded.extents[2]<245,(i,'oversize')
 np.savez_compressed(A/f'plate{i}.npz',vertices=combined.vertices,faces=combined.faces,face_groups=np.concatenate(groups))
 report={'plate':i,'filename':path.name,'components':len(components),'watertight':True,'normal_consistency':True,'size_mm':reloaded.extents.tolist(),'bounds_mm':reloaded.bounds.tolist(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'items':plates}
 reports.append(report);print('EXPORTED_CLOSED',i,len(components),reloaded.extents.round(2),flush=True)
(A/'export-checks.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('ALL_FOUR_STL_EXPORTED',flush=True)
