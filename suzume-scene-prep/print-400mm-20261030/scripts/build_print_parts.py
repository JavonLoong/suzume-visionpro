import sys,json,math,time,hashlib,warnings
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'.deps'))
import manifold3d as mf
M=mf.Manifold;OP=mf.OpType
OUT=R/'交付文件';STL=OUT/'STL_毫米';ASSEMBLY=R/'analysis'/'assembly_meshes'
for p in [OUT,STL,ASSEMBLY]:p.mkdir(parents=True,exist_ok=True)
warnings.filterwarnings('ignore',category=RuntimeWarning)
rows=[];notes=[]
def cube(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def cyl(r,h,x=0,y=0,z=0,n=64):return M.cylinder(h,r,circular_segments=n).translate((x,y,z))
def union(a):return M.batch_boolean(a,OP.Add)
def tm(m):
 q=m.to_mesh64();return trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=False)
def source(name):
 d=np.load(R/'analysis'/'solid'/(name+'.npz'))
 m=M(mf.Mesh(np.asarray(d['vertices'],dtype=np.float32),np.asarray(d['faces'],dtype=np.uint32)))
 if m.status()!=mf.Error.NoError:raise RuntimeError((name,str(m.status())))
 return m.simplify(.065)
def wedge(m,i,n,gap=.12):
 a=i*2*math.pi/n;b=(i+1)*2*math.pi/n
 return m.trim_by_plane((-math.sin(a),math.cos(a),0),gap).trim_by_plane((math.sin(b),-math.cos(b),0),gap)
def plate_roots(m,name):
 parts=m.decompose();kept=[];removed=[]
 for c in parts:
  b=c.bounding_box();vol=c.volume()
  if b[2]<7.6 and b[5]>5 and vol>2:kept.append(c)
  elif vol>15:
   # Preserve sizeable detached source ornaments as separate printable objects.
   removed.append({'volume':vol,'bounds':list(b),'retained_as_loose_part':True})
   emit(name+f'_附件{len(removed):02d}',c,'独立建筑附件',quantity=1)
  else:removed.append({'volume':vol,'bounds':list(b),'retained_as_loose_part':False})
 if removed:notes.append({'module':name,'detached_components':removed})
 return union(kept)
def emit(name,m,category,quantity=1,rotate=None):
 if m.is_empty():raise RuntimeError('empty '+name)
 m=m.simplify(.035)
 mesh=tm(m);mesh.fix_normals(multibody=True)
 assert mesh.is_watertight,(name,'nonmanifold')
 assert mesh.is_winding_consistent,(name,'inconsistent normals')
 assert mesh.volume>0,(name,'nonpositive volume')
 np.savez_compressed(ASSEMBLY/(name+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
 mesh.export(ASSEMBLY/(name+'.stl'),file_type='stl_ascii')
 posed=mesh.copy();rot=np.eye(4)
 if rotate is not None:rot=trimesh.transformations.rotation_matrix(math.radians(rotate[1]),rotate[0]);posed.apply_transform(rot)
 shift=-posed.bounds[0];posed.apply_translation(shift)
 dims=posed.extents
 assert max(dims[:2])<225 and dims[2]<245,(name,dims)
 posed.export(STL/(name+'.stl'),file_type='stl_ascii')
 row={'id':name,'category':category,'quantity':quantity,'size_mm':dims.round(3).tolist(),'triangles':len(mesh.faces),'watertight':bool(mesh.is_watertight),'volume_mm3':round(float(mesh.volume),3),'components':len(mesh.split()),'assembly_bounds_mm':mesh.bounds.round(4).tolist(),'assembly_to_print_matrix':(trimesh.transformations.translation_matrix(shift)@rot).round(8).tolist(),'stl_sha256':hashlib.sha256((STL/(name+'.stl')).read_bytes()).hexdigest()}
 rows.append(row);print('PART',name, row['size_mm'],len(mesh.faces),'faces',row['components'],'components',flush=True)
 return row
holes=[]
for radius in [180,134]:
 for i in range(8):
  for off in [-10,10]:
   a=math.radians(i*45+22.5+off);holes.append((radius*math.cos(a),radius*math.sin(a)))
slots=[]
for p in [60,130,-60,-130]:
 slots.extend([cube((-6.2,p-3.2,2.9),(6.2,p+3.2,5.2)),cube((p-3.2,-6.2,2.9),(p+3.2,6.2,5.2))])
socket_cuts=union([cyl(1.7,2.3,x,y,2.8) for x,y in holes]+slots)
disc=cyl(200,5,n=1536)
for i in range(4):
 start=time.time();m=source(f'ground_{i+1:02d}')
 m=m.trim_by_plane((0,0,1),4.4)^cyl(197.5,20,z=0,n=512)
 base=wedge((disc+m)-socket_cuts,i,4,gap=.1)
 # Keep the basal component; separate tiny floating source pipes are intentionally excluded.
 parts=base.decompose();good=[c for c in parts if c.bounding_box()[2]<.2]
 dropped=[c for c in parts if c.bounding_box()[2]>=.2]
 notes.append({'base':i+1,'unsupported_ground_islands_excluded':len(dropped),'excluded_volume_mm3':sum(c.volume() for c in dropped)})
 emit(f'B{i+1:02d}_底盘',union(good),'底盘')
 print('SECONDS',round(time.time()-start,1),flush=True)
for cat,code,radius,cn in [('wall','W',180,'环形建筑'),('steel','S',134,'钢架')]:
 for i in range(8):
  start=time.time();name=f'{code}{i+1:02d}_{cn}'
  m=source(f'{cat}_{i+1:02d}')
  m=wedge(m,i,8).trim_by_plane((0,0,1),5)
  m=m^cyl(197.3,150,n=768)
  # Same labelled sockets in module underside and base.
  hh=[]
  for off in [-10,10]:
   a=math.radians(i*45+22.5+off);hh.append(cyl(1.7,2.05,radius*math.cos(a),radius*math.sin(a),4.95))
  m=plate_roots(m,name)-union(hh)
  emit(name,m,cn)
  print('SECONDS',round(time.time()-start,1),flush=True)
# White door: matching six-panel proportions, FDM wall thickness and separated pin hinge.
z0=6.6;zt=31.9;px=5.5;py=-2.2
frame=cube((-6.8,-1.2,z0),(6.8,1.2,zt))-cube((-5,-2,z0+.8),(5,2,zt-1.4))
pedestal=cube((-9,-4,5),(9,4,6.6))
frame=(frame+pedestal)-cyl(1.55,24,px,py,7.3)
def barrel(z,h):return cyl(1.35,h,px,py,z)-cyl(.65,h+.2,px,py,z-.1)
for z,h in [(8.1,3),(25.1,3)]:
 frame=frame+barrel(z,h)+cube((4.9,-2.2,z),(6.2,-.35,z+h))
# Drill after adding webs so all knuckles have a clear 1.3 mm bore.
frame=frame-cyl(.65,28,px,py,5)
leaf=cube((-4.5,-.8,7.75),(4.5,.8,30.05))
for xa,xb in [(-3.8,-.5),(.5,3.8)]:
 for za,zb in [(8.5,12.3),(13.2,22.8),(23.7,29.3)]:
  leaf=leaf-cube((xa,-.85,za),(xb,-.35,zb))
for z,h in [(11.45,3),(21.75,3)]:
 leaf=leaf+barrel(z,h)+cube((4.0,-2.2,z),(4.7,-.4,z+h))+cube((4.0,-2.3,z),(5.8,-1.6,z+h))
leaf=leaf-cyl(.65,28,px,py,5)
# Raised knob remains attached and is large enough to survive handling.
knob=M.sphere(.65,16).translate((-3.7,-1.0,18.2));leaf=leaf+knob
for angle in [0,15,30,45,60,75,90]:
 rotated=leaf.translate((-px,-py,0)).rotate((0,0,angle)).translate((px,py,0))
 overlap=(rotated^frame).volume()
 assert overlap<.001,('Door leaf/frame collision',angle,overlap)
emit('D01_门框与台阶',frame,'白门',rotate=((1,0,0),90))
emit('D02_六格门扇',leaf,'白门',rotate=((1,0,0),90))
emit('K01_底盘拼接键',cube((0,0,0),(12,6,2)),'连接件',quantity=8)
emit('K02_模块定位销',cyl(1.5,3.8,n=32),'连接件',quantity=32)
# Door uses an external 1 mm metal pin; no fragile printed hinge axle is supplied.
# Calibration sample with three candidate sockets; pin/keys printed alongside separately.
coupon=cube((0,0,0),(38,18,5))
for j,r in enumerate([1.6,1.7,1.8]):coupon=coupon-cyl(r,3.2,7+j*12,9,1.9)
coupon=coupon-cube((14,0,2.9),(26.4,6.4,5.1))
emit('T01_先打印配合试块',coupon,'试装件')
manifest={'project':'铃芽之旅400毫米打印分件首版','source_scene':'Official poster courtyard v38 in v56 blend','diameter_mm':400,'source_span_m':58,'scale_mm_per_source_unit':400/58,'assumed_printer':'Bambu Lab X1 Carbon','assumed_nozzle_mm':.4,'assumed_material':'PLA','base_thickness_mm':5,'radial_seam_gap_mm':.2,'module_seam_gap_mm':.24,'socket_diameter_mm':3.4,'pin_diameter_mm':3,'pin_length_mm':3.8,'hinge_metal_pin_diameter_mm':1,'hinge_bore_mm':1.3,'hinge_knuckle_gap_mm':.35,'parts':rows,'adaptation_notes':notes,'limits':['400 mm is the base outer diameter; distant forest, sky, character, virtual night world are excluded.','Painted damage under 0.025 mm and small detached remnants are excluded. Source-derived structural detail thickened and voxel-unified at 0.28 mm.','The six-panel door has been rebuilt at print-safe thickness with a separate leaf and pin hinge. Door handle/panels are simplified.','PLA and 0.4 mm nozzle are assumptions. Test coupon and a door sample need real printing before the full batch.','3MF projects are offline; no printer upload or print job is initiated.']}
(OUT/'零件清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('BUILD_COMPLETE',len(rows),'part files',flush=True)
