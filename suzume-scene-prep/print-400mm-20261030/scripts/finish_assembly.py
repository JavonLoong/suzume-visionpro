import json,sys,hashlib,warnings,importlib.util
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'.deps'))
import manifold3d as mf
warnings.filterwarnings('ignore');O=R/'交付文件';A=R/'analysis'/'assembly_meshes';S=O/'STL_毫米'
spec=importlib.util.spec_from_file_location('_meshfix',next((R/'.deps'/'pymeshfix').glob('_meshfix*.pyd')));fix=importlib.util.module_from_spec(spec);spec.loader.exec_module(fix)
data=json.loads((O/'零件清单.json').read_text(encoding='utf8'))
def load(n):
 d=np.load(A/(n+'.npz'));m=mf.Manifold(mf.Mesh64(d['vertices'],d['faces'].astype('uint64')))
 assert m.status()==mf.Error.NoError,(n,m.status())
 return m
def cylinder(r,h,z):return mf.Manifold.cylinder(h,r,circular_segments=768).translate((0,0,z))
clear=(cylinder(205,20,5)-cylinder(122,20,5))+mf.Manifold.cube((20,10,20)).translate((-10,-5,5))
for row in data['parts']:
 if not row['id'].startswith('B'):continue
 m=load(row['id'])-clear;q=m.to_mesh64();mesh=trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=True)
 if not mesh.is_watertight:
  v,f=fix.clean_from_arrays(mesh.vertices.astype('float64'),mesh.faces.astype('int32'),verbose=False);mesh=trimesh.Trimesh(v,f,process=True)
 mesh=sorted(mesh.split(only_watertight=False),key=lambda m:m.volume,reverse=True)[0];mesh.fix_normals()
 assert mesh.is_watertight and mesh.is_winding_consistent
 np.savez_compressed(A/(row['id']+'.npz'),vertices=mesh.vertices,faces=mesh.faces);mesh.export(A/(row['id']+'.stl'),file_type='stl_ascii')
 pose=np.array(row['assembly_to_print_matrix']);posed=mesh.copy();posed.apply_transform(pose);posed.export(S/(row['id']+'.stl'),file_type='stl_ascii')
 ck=trimesh.load(S/(row['id']+'.stl'),force='mesh');assert ck.is_watertight
 row.update(size_mm=posed.extents.round(4).tolist(),triangles=len(mesh.faces),volume_mm3=round(mesh.volume,3),assembly_bounds_mm=mesh.bounds.tolist(),stl_sha256=hashlib.sha256((S/(row['id']+'.stl')).read_bytes()).hexdigest())
 print('BASE_MOUNT_SURFACE',row['id'],flush=True)
frame=load('D01_门框与台阶');leaf=load('D02_六格门扇');checks=[]
for angle in [0,15,30,45,60,75,90]:
 moved=leaf.translate((-5.5,2.2,0)).rotate((0,0,angle)).translate((5.5,-2.2,0))
 volume=(moved^frame).volume();assert volume<.001,(angle,volume)
 checks.append({'angle_deg':angle,'interference_mm3':volume})
data['door_clearance_checks']=checks
data['assembly_note']='底盘外圈半径122毫米以外清平至Z=5，避免墙体/钢架底托与水底石块互相穿插；中心白门台阶下清平。'
(O/'零件清单.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print('ASSEMBLY_FIT_COMPLETE',len(data['parts']),flush=True)
