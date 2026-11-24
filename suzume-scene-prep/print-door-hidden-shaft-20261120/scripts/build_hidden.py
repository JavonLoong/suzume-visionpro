from pathlib import Path
import sys,json,math,itertools,numpy as np,trimesh
O=Path(__file__).resolve().parents[1];P=O.parent
sys.path.insert(0,str(P/'print-400mm-20261030/.deps'));import manifold3d as mf
sys.path.insert(0,str(P/'print-door-detail-20261113/scripts'));from close_tjunctions import close_tjunctions
M=mf.Manifold
A=O/'analysis';(A/'assembly').mkdir(exist_ok=True);(O/'试配STL_非整机定稿').mkdir(exist_ok=True)
def tm(m):
 d=m.to_mesh64();return trimesh.Trimesh(np.array(d.vert_properties)[:,:3],np.array(d.tri_verts),process=False)
def man(m):return M(mf.Mesh64(np.asarray(m.vertices,dtype=float),np.asarray(m.faces,dtype=np.uint64)))
def load(p):
 d=np.load(p);return man(trimesh.Trimesh(d['vertices'],d['faces'],process=True))
def box(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(lo)
def cyl(r,z0,z1,x=0,y=0):return M.cylinder(z1-z0,r,circular_segments=64).translate((x,y,z0))
def union(parts):return M.batch_boolean(parts,mf.OpType.Add)
# Actual unmodified visual geometry extracted before the old external hinge was added.
frame=load(A/'clean_frame.npz');leaf=load(A/'clean_leaf.npz')
ax,ay=12.15,12.75
# Continuous shaft sleeve is integrated into the moving hinge-side vertical edge.
# It stays inside the original frame silhouette and hides the 1 mm rod.
leaf+=cyl(1.2,9.364624438826164,64.0267059595614,ax,ay)+box((10.5,12.25,9.364624438826164),(ax,13.55,64.0267059595614))
# Clearance envelope: samples every degree, each vertex cloud padded 0.25 mm.
# Divide the original leaf into height bands to avoid erasing frame around the knob.
cutters=[cyl(1.45,9.364624438826164-.25,64.0267059595614+.25,ax,ay)]
bounds=json.loads((A/'clean_component_bounds.json').read_text('utf-8'))
bounds.append([10.5,12.25,9.364624438826164,ax,13.55,64.0267059595614])
for bound in bounds:
 b=np.array(bound);corners=np.array(list(itertools.product(*zip(b[:3]-.25,b[3:]+.25))))
 pts=[]
 for angle in range(106):
  a=math.radians(-angle);v=corners.copy();x=v[:,0]-ax;y=v[:,1]-ay
  v[:,0]=ax+x*math.cos(a)-y*math.sin(a);v[:,1]=ay+x*math.sin(a)+y*math.cos(a);pts.extend(v)
 cutters.append(M.hull_points(np.array(pts)))
# Give the unpinned leaf a clear front-to-back assembly path as well.
for bound in bounds:
 b=np.array(bound);lo=b[:3]-.2;hi=b[3:]+.2;lo[1]-=30
 cutters.append(box(tuple(lo),tuple(hi)))
cutters.append(box((ax-1.4,ay-30,9.164624438826164),(ax+1.4,ay,64.2267059595614)))
frame-=union(cutters)
# A slender fixed rear jamb remains within the original frame silhouette.
# It too is relieved by the same motion envelope, never allowed to collide.
frame+=(box((11.54,14.6,8.4),(13.94,15.77,64.65))-union(cutters))
# Move the door to the new centre slot, top of 60mm door is Z68, base surface Z8.
shift=(0,-13.5,1.2);frame=frame.translate(shift);leaf=leaf.translate(shift);ay-=13.5
# Recessed shoulder + table-reaching tongue match 80x14 / 68x7 slot.
foot=box((-39.75,-6.75,5),(39.75,6.75,8))+box((-33.75,-3.25,-6),(33.75,3.25,5))
# Narrow threshold supports frame; top of leaf is untouched.
foot+=box((-15.7,-3.1,8),(15.7,3.1,9.8))
frame+=foot
fragments=frame.decompose();tiny=[p for p in fragments if p.volume()<1];assert all(p.bounding_box()[5]<11 for p in tiny)
frame=union([p for p in fragments if p.volume()>=1])
# 1mm rod: 1.4mm running-clearance bore in fixed supports, 1.2mm bond bore in leaf.
frame-=cyl(.7,-6.1,68.1,ax,ay)
leaf-=cyl(.6,-6.1,68.1,ax,ay)
# Rod fixed to leaf by a provisional bond joint. Adhesive/material not qualified.
rod=cyl(.5,-5.8,67.6,ax,ay)
checks=[]
def zero(name,m):
 vol=max(0,m.volume());assert vol<.001,(name,vol);checks.append({'name':name,'intersection_mm3':vol})
for name,m in [('frame',frame),('leaf',leaf)]:
 print(name,'pieces',len(m.decompose()),'vol',m.volume(),'bounds',m.bounding_box(),flush=True)
 assert len(m.decompose())==1,(name,'disconnected',[(p.volume(),p.bounding_box()) for p in m.decompose()])
zero('rod_frame',rod^frame);zero('rod_leaf',rod^leaf)
# Existing 116 mm centre plate is immutable input.
centre_path=Path(r'D:/虚拟C盘/学习秋/底座_严格九块_116毫米居中长槽/09_可换中心圆盘_116毫米_居中长槽.npz')
centre=load(centre_path)
zero('frame_116mm_centre_plate',frame^centre)
for angle in range(106):
 moved=leaf.translate((-ax,-ay,0)).rotate((0,0,-angle)).translate((ax,ay,0))
 zero('leaf_frame_'+str(angle),moved^frame);zero('leaf_centre_'+str(angle),moved^centre)
# Insertion: door with its tongue goes straight down into the centre plate.
for dz in np.linspace(0,20,81):zero('frame_insert_'+str(round(float(dz),2)),frame.translate((0,0,float(dz)))^centre)
parts=[]
for name,m,rotation in [('01_门框与居中底脚',frame,(0,0,0)),('02_内藏轴门扇',leaf,(-90,0,0))]:
 m=m.simplify(.0002);mesh=tm(m);mesh.merge_vertices(digits_vertex=5);mesh.update_faces(mesh.area_faces>1e-12);mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
 if not mesh.is_volume:mesh=close_tjunctions(mesh)
 assert mesh.is_volume and mesh.is_winding_consistent and len(mesh.split())==1,(name,'invalid_mesh',mesh.is_watertight,mesh.is_winding_consistent,len(mesh.split()),mesh.volume)
 np.savez_compressed(A/'assembly'/(name+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
 printed=mesh.copy();printed.apply_transform(trimesh.transformations.euler_matrix(*np.deg2rad(rotation)));printed.apply_translation(-printed.bounds[0])
 path=O/'试配STL_非整机定稿'/(name+'.stl');printed.export(path,file_type='stl_ascii');back=trimesh.load(path,force='mesh');assert back.is_volume
 parts.append({'name':name,'path':str(path),'volume_mm3':mesh.volume,'size_mm':printed.extents.tolist()})
for name,m in [('参考_1毫米实心杆_非打印件',rod),('参考_原116毫米中心盘_不重复打印',centre)]:
 mesh=tm(m);np.savez_compressed(A/'assembly'/(name+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
report={'status':'门侧几何试配草案；非舵机整机定稿','height_above_deck_mm':60,'height_assumption':'沿用原工程默认60毫米，未由用户确认','shaft_diameter_mm':1,'fixed_bore_mm':1.4,'moving_bond_bore_mm':1.2,'shaft_xy_mm':[ax,ay],'shaft_bottom_z_mm':-5.8,'deck_top_z_mm':8,'table_z_mm':-6,'servo':'unknown; coupling and mount not designed','rod_to_leaf':'provisional bonded joint, material/adhesive/strength untested','checks':checks,'parts':parts,'opening_checked_deg':[0,105],'actual_print_or_servo_test':False,'sliced':False}
(A/'核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print('PASS',len(checks),flush=True)

# True geometric section through the axis, for visual inspection only.
window=box((9.7,-20,-6.1),(14.8,ay,68.1))
for name,m in [('剖视_门框',frame-window),('剖视_门扇',leaf-window)]:
 mesh=tm(m);np.savez_compressed(A/'assembly'/(name+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
