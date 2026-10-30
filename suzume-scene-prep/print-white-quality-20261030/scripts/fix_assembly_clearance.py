import sys,json,hashlib
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parent/'print-400mm-20261030/.deps'))
import manifold3d as mf
A=R/'analysis/assembly_meshes';O=R/'交付文件'
data=json.loads((O/'零件清单.json').read_text(encoding='utf8'));reports=json.loads((R/'analysis/final-geometry-checks.json').read_text(encoding='utf8'));notes=[]
validated=[json.loads((R/'analysis/validated_parts'/(r['id']+'.json')).read_text(encoding='utf8')) for r in data['parts']]
data['parts']=[x['row'] for x in validated];reports=[x['report'] for x in validated]
def load(n):
 q=np.load(A/(n+'.npz'));return mf.Manifold(mf.Mesh64(q['vertices'],q['faces'].astype('uint64')))
for i in range(1,9):
 wn=f'W{i:02d}_环形建筑';sn=f'S{i:02d}_钢架';w=load(wn);s=load(sn);v=(w^s).volume()
 print('INTERFERENCE',wn,sn,v,flush=True)
 if v<.01:continue
 backup=R/'analysis/before_clearance';backup.mkdir(exist_ok=True)
 np.savez_compressed(backup/(sn+'.npz'),**dict(np.load(A/(sn+'.npz'))))
 original=s.volume();original_bounds=np.array(s.bounding_box())
 # Cut only the steel/prop group where it touches its separate facade module.
 # Six axial offsets provide a small assembly clearance without changing the facade.
 s-=w
 for axis in range(3):
  for sign in [-1,1]:
   shift=[0.,0.,0.];shift[axis]=.2*sign;s-=w.translate(shift)
 pieces=sorted(s.decompose(),key=lambda p:p.volume(),reverse=True);big=pieces[:1]
 # Contact trimming can separate thin remnants of the overlapping floor ledge.
 # Remove only small ledge offcuts below Z=8, or microscopic cut chips.
 assert all(p.volume()<.05 or (p.volume()<10 and p.bounding_box()[5]<8) or (p.volume()<2 and max(np.array(p.bounding_box())[3:]-np.array(p.bounding_box())[:3])<4) for p in pieces[1:]),(sn,'detached structural feature',[(p.volume(),p.bounding_box()) for p in pieces[1:]])
 assert len(big)==1,(sn,'disconnected after clearance',[(p.volume(),p.bounding_box()) for p in pieces])
 s=big[0];assert s.status()==mf.Error.NoError and (s^w).volume()<.001
 q=s.to_mesh64();m=trimesh.Trimesh(np.array(q.vert_properties)[:,:3],q.tri_verts,process=True)
 assert m.is_watertight and m.is_winding_consistent and (m.area_faces>1e-13).all()
 assert original-s.volume()<max(v*1.3,v+20) and (original-s.volume())/original<.2,(sn,'cut beyond measured overlap plus clearance',original,s.volume())
 assert np.max(np.abs(np.array(s.bounding_box())[[2,5]]-original_bounds[[2,5]]))<.001,(sn,'changed base or steel height')
 np.savez_compressed(A/(sn+'.npz'),vertices=m.vertices,faces=m.faces)
 row=next(x for x in data['parts'] if x['id']==sn);pose=np.array(row['assembly_to_print_matrix']);pose[:3,3]=0
 posed=m.copy();posed.apply_transform(pose);shift=-posed.bounds[0];posed.apply_translation(shift);pose=trimesh.transformations.translation_matrix(shift)@pose
 stl=R/'修复后的STL_毫米'/(sn+'.stl');posed.export(stl,file_type='stl_ascii');check=trimesh.load(stl,force='mesh');assert check.is_watertight and check.is_winding_consistent
 row.update(size_mm=posed.extents.round(4).tolist(),assembly_to_print_matrix=pose.tolist(),assembly_bounds_mm=m.bounds.tolist(),volume_mm3=round(m.volume,3),triangles=len(m.faces),stl_sha256=hashlib.sha256(stl.read_bytes()).hexdigest())
 report=next(x for x in reports if x['id']==sn);report.update(volume_mm3=m.volume,bounds_mm=m.bounds.tolist(),assembly_clearance_cut_mm=.2)
 (R/'analysis/validated_parts'/(sn+'.json')).write_text(json.dumps({'row':row,'report':report},ensure_ascii=False,indent=2),encoding='utf8')
 notes.append({'part':sn,'removed_mm3':original-s.volume(),'original_interference_mm3':v,'clearance_mm':.2})
 print('CLEARANCE_FIXED',sn,original-s.volume(),flush=True)
(O/'零件清单.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
(R/'analysis/final-geometry-checks.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
(R/'analysis/assembly-clearance-cuts.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf8')
