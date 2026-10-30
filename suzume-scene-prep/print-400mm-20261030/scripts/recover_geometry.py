import sys,json,math,hashlib,warnings
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'.deps'))
import manifold3d as mf
M=mf.Manifold;O=R/'交付文件';A=R/'analysis/assembly_meshes'
warnings.filterwarnings('ignore')
d=json.loads((O/'零件清单.json').read_text(encoding='utf8'))
def cyl(r,h,z=0,n=768):return M.cylinder(h,r,circular_segments=n).translate((0,0,z))
def box(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def wedge(m,i,n,gap=.12):
 a=i*2*math.pi/n;b=(i+1)*2*math.pi/n
 return m.trim_by_plane((-math.sin(a),math.cos(a),0),gap).trim_by_plane((math.sin(b),-math.cos(b),0),gap)
def src(n):
 q=np.load(R/'analysis/solid'/(n+'.npz'))
 return M(mf.Mesh(q['vertices'].astype('float32'),q['faces'].astype('uint32'))).simplify(.065)
def mesh(m):
 q=m.to_mesh64();v=np.array(q.vert_properties)[:,:3];f=np.array(q.tri_verts)
 raw=trimesh.Trimesh(v,f,process=False)
 merged=trimesh.Trimesh(v,f,process=True)
 print('TOPOLOGY',raw.is_watertight,merged.is_watertight,len(v)-len(merged.vertices),flush=True)
 if not merged.is_watertight:
  # Coincident vertices from distinct manifold sheets must remain separate in STL.
  # Move each of those vertices along its local normal by less than one micron.
  _,inv,count=np.unique(v.round(7),axis=0,return_inverse=True,return_counts=True)
  hit=count[inv]>1
  normals=raw.vertex_normals
  v[hit]+=normals[hit]*.0006
  merged=trimesh.Trimesh(v,f,process=True)
  print('SEPARATE_CONTACTS',int(hit.sum()),merged.is_watertight,flush=True)
 merged.fix_normals(multibody=True)
 assert merged.is_watertight and merged.is_winding_consistent
 return merged
def save(row,m):
 m.fix_normals(multibody=True)
 n=row['id'];np.savez_compressed(A/(n+'.npz'),vertices=m.vertices,faces=m.faces)
 m.export(A/(n+'.stl'),file_type='stl_ascii')
 rot=np.array(row['assembly_to_print_matrix']);rot[:3,3]=0
 p=m.copy();p.apply_transform(rot);shift=-p.bounds[0];p.apply_translation(shift)
 pose=trimesh.transformations.translation_matrix(shift)@rot
 file=O/'STL_毫米'/(n+'.stl');p.export(file,file_type='stl_ascii')
 check=trimesh.load(file,force='mesh');assert check.is_watertight
 row.update(size_mm=p.extents.round(4).tolist(),volume_mm3=round(m.volume,3),triangles=len(m.faces),assembly_bounds_mm=m.bounds.tolist(),assembly_to_print_matrix=pose.tolist(),stl_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),watertight=True,components=len(m.split()))
 print('RECOVERED',n,row['size_mm'],row['volume_mm3'],flush=True)

holes=[]
for r in [180,134]:
 for i in range(8):
  for off in [-10,10]:
   a=math.radians(i*45+22.5+off);holes.append(cyl(1.7,2.3,z=2.8,n=64).translate((r*math.cos(a),r*math.sin(a),0)))
slots=[]
for p in [60,130,-60,-130]:
 slots += [box((-6.2,p-3.2,2.9),(6.2,p+3.2,5.2)),box((p-3.2,-6.2,2.9),(p+3.2,6.2,5.2))]
cut=M.batch_boolean(holes+slots,mf.OpType.Add)
clear=(cyl(205,20,5)-cyl(122,20,5))+box((-10,-5,5),(10,5,25))
ground=src('ground_02').trim_by_plane((0,0,1),4.4)^cyl(197.5,20,n=512)
base=wedge((cyl(200,5,n=1536)+ground)-cut,1,4,.1)-clear
base=M.batch_boolean([x for x in base.decompose() if x.bounding_box()[2]<.2],mf.OpType.Add)
try:b=mesh(base)
except AssertionError:
 # A clean solid base is preferable to a damaged render-derived floor fragment.
 b=mesh(wedge(cyl(200,5,n=1536)-cut,1,4,.1))
 d['base_02_note']='第二块底盘地面浮雕简化为平面，保留全部装配孔和连接槽。'
assert b.volume>150000 and min(b.extents[:2])>199
save(next(x for x in d['parts'] if x['id']=='B02_底盘'),b)
(O/'零件清单.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')

for number in [2,3,4,5,6,8]:
 i=number-1;n=f'W{number:02d}_环形建筑';row=next(x for x in d['parts'] if x['id']==n)
 m=wedge(src(f'wall_{number:02d}'),i,8).trim_by_plane((0,0,1),5)^cyl(197.3,150)
 pieces=[x for x in m.decompose() if x.bounding_box()[2]<7.6 and x.bounding_box()[5]>5 and x.volume()>2]
 m=M.batch_boolean(pieces,mf.OpType.Add)
 for off in [-10,10]:
  a=math.radians(i*45+22.5+off)
  m=m-cyl(1.7,2.05,4.95,n=64).translate((180*math.cos(a),180*math.sin(a),0))
 print('COMPARE',n,'old',row['volume_mm3'],'source',m.volume(),flush=True)
 try:
  recovered=mesh(m)
  save(row,recovered)
 except AssertionError:
  np.savez_compressed(R/'analysis'/(n+'_recover_failed.npz'),vertices=np.array(m.to_mesh64().vert_properties)[:,:3],faces=np.array(m.to_mesh64().tri_verts))
  print('REQUIRES_ALTERNATIVE',n,flush=True)
 (O/'零件清单.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
