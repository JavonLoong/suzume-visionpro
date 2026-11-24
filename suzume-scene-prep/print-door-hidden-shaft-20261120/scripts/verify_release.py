from pathlib import Path
import sys,json,hashlib,zipfile,numpy as np,trimesh,pymeshlab as pm
O=Path(__file__).resolve().parents[1];P=O.parent;sys.path.insert(0,str(P/'print-400mm-20261030/.deps'));import manifold3d as mf
A=O/'analysis';report=json.loads((A/'核验记录.json').read_text('utf-8'))
def load(p):
 d=np.load(p);return mf.Manifold(mf.Mesh64(np.asarray(d['vertices'],dtype=float),np.asarray(d['faces'],dtype=np.uint64)))
f=load(A/'assembly/01_门框与居中底脚.npz');l=load(A/'assembly/02_内藏轴门扇.npz')
for dy in np.linspace(-30,0,121):
 v=max(0,(l.translate((0,float(dy),0))^f).volume());assert v<.001,('leaf_front_insertion',dy,v)
report['leaf_front_insertion_samples']=121
# Verify unchanged courtyard assets in their actual assembly positions.
q=P/'print-white-quality-20261030';rows=json.loads((q/'交付文件/零件清单.json').read_text('utf-8'))['parts'];tested=[]
for row in rows:
 name=row['id']
 if not name.startswith(('W','S')):continue
 p=q/'analysis/assembly_meshes'/(name+'.npz')
 if not p.exists():continue
 obstacle=load(p);v=max(0,(f^obstacle).volume());assert v<.001,(name,'frame',v)
 for angle in range(0,106):
  x,y=report['shaft_xy_mm'];m=l.translate((-x,-y,0)).rotate((0,0,-angle)).translate((x,y,0))
  v=max(0,(m^obstacle).volume());assert v<.001,(name,angle,v)
 tested.append(name)
report['courtyard_collision_checked']=tested
for row in report['parts']:
 p=Path(row['path']);ms=pm.MeshSet();ms.load_new_mesh(str(p));ms.compute_selection_by_self_intersections_per_face();n=ms.current_mesh().selected_face_number();assert n==0,(p.name,n)
 row['self_intersection_faces']=n;row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
report['source_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'print-door-detail-20261113/analysis/software_source.json',Path(r'D:/虚拟C盘/学习秋/底座_严格九块_116毫米居中长槽/09_可换中心圆盘_116毫米_居中长槽.npz')]}
(A/'核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'parts':2,'leaf_insertion_samples':121,'courtyard_parts':tested,'self_intersection_faces':0,'mechanical_checks':len(report['checks'])},ensure_ascii=False))
