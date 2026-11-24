"""Door-side pushrod horns. Servo placement is a kinematic assumption, not a mount."""
import sys,json,math,hashlib
from pathlib import Path
import numpy as np,trimesh,pymeshlab as pm
R=Path(__file__).resolve().parents[1];P=R.parent;A=R/'analysis';SRC=P/'print-door-detail-20261113';BASE=P/'print-stage-500mm-20261113'
for p in [A/'assembly',R/'STL',A/'slice_projects']:p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(P/'print-400mm-20261030/.deps'));import manifold3d as mf
sys.path.insert(0,str(SRC/'scripts'));from close_tjunctions import close_tjunctions
M=mf.Manifold
data=json.loads((SRC/'analysis/door_manifest.json').read_text(encoding='utf8'))
checks=[];rows=[];variants=[]
def tm(m):
 d=m.to_mesh64();return trimesh.Trimesh(np.asarray(d.vert_properties)[:,:3],np.asarray(d.tri_verts),process=False)
def man(m):return M(mf.Mesh64(np.asarray(m.vertices),np.asarray(m.faces,dtype='uint64')))
def load(name):
 d=np.load(SRC/'analysis/assembly'/(name+'.npz'));return man(trimesh.Trimesh(d['vertices'],d['faces'],process=False))
def cube(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(lo)
def cyl(r,h,x=0,y=0,z=0):return M.cylinder(h,r,circular_segments=64).translate((x,y,z))
def zero(name,m):
 vol=max(0,m.volume());assert vol<.001,(name,vol);checks.append({'name':name,'interference_mm3':vol})
def move(m,ax,ay,a):return m.translate((-ax,-ay,0)).rotate((0,0,-a)).translate((ax,ay,0))
for v in data['door_variants']:
 label=v['label'];h=v['outer_height_mm'];ax,ay=v['pivot_xy'];z0=6.8+.16*h+.6;z1=z0+2
 original=load(label+'门扇');frame=load(label+'门框');cassette=load(label+'插座板')
 arm=cube((0,-2,z0),(12,2,z1))+cyl(2,2,0,0,z0)+cyl(2,2,12,0,z0)
 for radius in [6,9,12]:arm-=cyl(.6,2.4,radius,0,z0-.2)
 arm=arm.rotate((0,0,135)).translate((ax,ay,0));arm-=cyl(1.2,2.4,ax,ay,z0-.2)
 leaf=(original+arm).simplify(.0003);m=tm(leaf)
 old=m.volume;m.merge_vertices(digits_vertex=5);m.update_faces(m.area_faces>1e-12);m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
 if not m.is_volume:m=close_tjunctions(m)
 assert m.is_volume and abs(m.volume/old-1)<1e-5 and np.all(m.area_faces>1e-12)
 leaf=man(m);assert len(leaf.decompose())==1
 zero(label+'仅增加背部摇臂',original-leaf)
 np.savez_compressed(A/'assembly'/(label+'门扇.npz'),vertices=m.vertices,faces=m.faces)
 np.savez_compressed(A/'assembly'/(label+'新增摇臂.npz'),vertices=tm(arm).vertices,faces=tm(arm).faces)
 for angle in range(106):
  moving=move(leaf,ax,ay,angle);zero(label+f'门扇开门{angle}',moving^(frame+cassette))
  assert moving.bounding_box()[2]>8.5
  # Illustrative parallel linkage: both arms use the same radius, pivots 40 mm apart.
  # Check wire, vertical pins and retaining bends against actual door geometry.
  theta=math.radians(135-angle)
  for radius in [6,9,12]:
   x=ax+radius*math.cos(theta);y=ay+radius*math.sin(theta);wire_r=.4
   main=cyl(wire_r,40).rotate((0,90,0)).translate((x,y,z1+1.2))
   pin=cyl(wire_r,4.4,x,y,z0-1.2)
   hook=cyl(wire_r,1.5).rotate((0,90,0)).translate((x-1.5,y,z0-1.2))
   zero(label+f'拉杆{radius}孔开门{angle}',(main+pin+hook)^(moving+frame+cassette))
 printed=tm(leaf.rotate((-90,0,0)));printed.apply_translation(-printed.bounds[0]);printed.apply_translation((30,40,0))
 path=R/'STL'/f'门扇{h}.stl';printed.export(path,file_type='stl_ascii');back=trimesh.load(path,force='mesh')
 assert back.is_volume and len(back.split())==1 and back.bounds[1,0]<252 and back.bounds[1,1]<252
 ms=pm.MeshSet();ms.load_new_mesh(str(path));ms.compute_selection_by_self_intersections_per_face();assert ms.current_mesh().selected_face_number()==0
 rows.append({'id':f'门扇{h}','group':'拉杆试配','quantity':1,'packed':True,'components':1,'settings_kind':'door','stl_path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size_mm':back.extents.tolist()})
 variants.append({'height_mm':h,'pivot_xy':v['pivot_xy'],'horn_bottom_z_mm':z0,'horn_top_z_mm':z1,'horn_thickness_mm':2,'rod_plane_z_mm':z1+1.2,'radii_mm':[6,9,12],'bore_mm':1.2,'added_volume_mm3':leaf.volume()-original.volume()})
 print('LINKAGE_PART_PASS',h,flush=True)
out={'status':'门侧拉杆耳试配；整机安装未定型','source':str(SRC),'wire_diameter_candidate_mm':.8,'existing_support_pin_mm':2,'door_horn_closed_angle_deg':135,'variants':variants,'parts':rows,'checks':checks,
 'kinematic_assumptions':{'servo_pivot_relative_xy_mm':[40,0],'servo_hole_radius':'must match selected door hole radius','both_joint_axes':'parallel vertical','wire_link_length_mm':40,'physical_servo_envelope_checked':False,'minimum_transmission_angle_deg':30,'opening_checked_deg':[0,105]},
 'unknowns':['舵机外壳长宽高及摇臂转动平面高度','舵机中心到选用拉杆孔的距离','实际孔径与钢丝松紧','安装盒位置和固定孔'],
 'physical_print_test':False,'servo_drive_finished':False}
(A/'linkage_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
(A/'packed_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('LINKAGE_GEOMETRY_PASS',len(rows),len(checks),flush=True)
