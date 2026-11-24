"""Appearance correction: original detailed white door, 13 mm display base.
No claimed servo fit: only the replaceable cassette and 2 mm shaft path are fixed.
"""
import json,hashlib,sys,math
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];P=R.parent;A=R/'analysis';O=R/'STL'
for p in (A,A/'assembly',O):p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(P/'print-400mm-20261030/.deps'))
import manifold3d as mf
M,C,OP=mf.Manifold,mf.CrossSection,mf.OpType
Q=P/'print-white-quality-20261030';rows=[];checks=[]
def cube(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def cyl(r,h,x=0,y=0,z=0,n=64):return M.cylinder(h,r,circular_segments=n).translate((x,y,z))
def hexcut(af,h,x,y,z):return cyl(af/math.sqrt(3),h,x,y,z,n=6)
def union(ms):return M.batch_boolean(ms,OP.Add)
def load(name):
 d=np.load(Q/'analysis/assembly_meshes'/(name+'.npz'));return M(mf.Mesh64(d['vertices'],d['faces'].astype('uint64')))
def tm(m):
 q=m.to_mesh64();return trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=False)
def emit(name,m,group,qty=1,rotate=(0,0,0)):
 m=m.simplify(.002);original=tm(m)
 assert original.is_watertight and original.is_winding_consistent and len(m.decompose())==1,name
 np.savez_compressed(A/'assembly'/(name+'.npz'),vertices=original.vertices,faces=original.faces)
 mesh=tm(m.rotate(rotate));shift=-mesh.bounds[0];mesh.apply_translation(shift)
 folder=O/group;folder.mkdir(exist_ok=True);path=folder/(name+'.stl');mesh.export(path,file_type='stl_ascii')
 check=trimesh.load(path,force='mesh')
 if not check.is_watertight:
  check.update_faces(check.nondegenerate_faces(height=1e-12));check.update_faces(check.unique_faces());check.remove_unreferenced_vertices()
  assert check.is_watertight,name;check.export(path,file_type='stl_ascii');check=trimesh.load(path,force='mesh')
 assert check.is_watertight and check.is_winding_consistent,name
 assert max(check.extents[:2])<240 and check.extents[2]<245,name
 np.savez_compressed(A/(name+'_print.npz'),vertices=check.vertices,faces=check.faces)
 rows.append({'id':name,'group':group,'quantity':qty,'size_mm':check.extents.tolist(),'rotate':list(rotate),'shift':shift.tolist(),'stl':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 print('PART',name,np.round(check.extents,2).tolist(),flush=True)
def zero(label,m):
 v=max(0,m.volume());assert v<.005,(label,v);checks.append({'check':label,'interference_mm3':v})

manifest=json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))
parts={row['id']:load(row['id']) for row in manifest['parts'] if row['id'][0] in 'WS'}
cuts=[];profiles=[];slab=cube((-210,-210,5),(210,210,8.001))
for name,body in parts.items():
 if '_附件' in name:continue
 profile=C((body^slab).project().to_polygons(),mf.FillRule.Positive)
 profiles.append(profile)
socket=C.batch_boolean([p.offset(.25) for p in profiles],OP.Add).simplify(.01)
entry=C.batch_boolean([p.offset(.55) for p in profiles],OP.Add).simplify(.01)
cuts.extend([socket.extrude(3.2).translate((0,0,5)),entry.extrude(.65).translate((0,0,7.4))])
for radius in (180,134):
 for i in range(8):
  for off in (-10,10):
   a=math.radians(i*45+22.5+off);cuts.append(cyl(1.7,2.3,radius*math.cos(a),radius*math.sin(a),2.8))
CY=15
outer=C([[(-32,-22),(32,-22),(32,18),(28,22),(-32,22)]],mf.FillRule.Positive)
inner=C([[(-25,-15),(25,-15),(25,11),(21,15),(-25,15)]],mf.FillRule.Positive)
cuts.extend([outer.offset(.25).extrude(5.2).translate((0,CY,3)),inner.offset(.25).extrude(8.4).translate((0,CY,-.2))])
bolt_points=[(x,y+CY) for x in (-28.5,28.5) for y in (-18.5,18.5)]
for x,y in bolt_points:cuts.extend([cyl(1.2,8.4,x,y,-.2),hexcut(4.3,1.9,x,y,-.1)])
# Fasteners enter from underneath: no exposed heads on the outer presentation rim.
bridges=[]
for x in (-100,100):
 for y in (-210,0,210):bridges.append((x,y,0))
for y in (-100,100):
 for x in (-210,0,210):bridges.append((x,y,90))
for x,y,angle in bridges:
 for d in (-17,17):
  px,py=(x+d,y) if angle==0 else (x,y+d)
  cuts.extend([hexcut(5.9,2.7,px,py,-.1),cyl(1.7,4.1,px,py,-.1)])
deck=cyl(300,8,n=1536)-union(cuts);tiles=[]
for row in range(3):
 for col in range(3):
  lo=(-300+200*col+(.15 if col else 0),-300+200*row+(.15 if row else 0),-.1)
  hi=(-100+200*col-(.15 if col<2 else 0),-100+200*row-(.15 if row<2 else 0),8.1)
  m=deck^cube(lo,hi);tiles.append(m);emit(f'薄底板{row+1}{col+1}',m,'底座')
deck=union(tiles)
for name,m in parts.items():zero(name+'落座',m^deck)
bridge=cube((-26,-10,-3),(26,10,0))
for x in (-17,17):bridge=bridge-cyl(1.7,3.2,x,0,-3.1)
emit('底部接缝条_打印12件',bridge,'底座',12,rotate=(180,0,0))
foot=cyl(10,5,z=-5)
emit('隐藏脚垫_打印12件',foot,'底座',12)
foot_positions=[(x,y) for x in (-100,100) for y in (-100,100)]+[(255*math.cos(i*math.pi/4),255*math.sin(i*math.pi/4)) for i in range(8)]
source_frame,source_leaf=load('D01_门框与台阶'),load('D02_六格门扇')
variants=[]
for label,height in [('35毫米',35),('40毫米',40),('45毫米',45)]:
 scale=height/26.9
 # Seat the fine pedestal 1.2 mm into its own matched cassette pocket.
 frame=source_frame.translate((0,0,-5)).scale((scale,scale,scale)).translate((0,CY,6.8))
 leaf=source_leaf.translate((0,0,-5)).scale((scale,scale,scale)).translate((0,CY,6.8))
 ax,ay=5.5*scale,CY-2.2*scale
 # 2 mm metal shaft, 2.4 mm running bore; retain the source knuckle arrangement.
 bore=cyl(1.2,height+10,ax,ay,2)
 frame=frame-bore;leaf=leaf-bore
 cassette=outer.extrude(5).translate((0,CY,3))+inner.extrude(3).translate((0,CY,0))
 cassette=cassette-bore
 cassette=cassette-cube((-9*scale-.25,CY-4*scale-.25,6.8),(9*scale+.25,CY+4*scale+.25,8.1))
 for x,y in bolt_points:cassette=cassette-cyl(1.2,5.3,x,y,2.9)-cyl(2.2,1.7,x,y,6.4)
 emit(label+'门框',frame,label)
 emit(label+'门扇',leaf,label,rotate=(-90,0,0))
 emit(label+'插座板',cassette,label)
 zero(label+'插座',cassette^deck)
 zero(label+'门框落座',frame^cassette)
 for angle in range(0,106,3):
  moved=leaf.translate((-ax,-ay,0)).rotate((0,0,angle)).translate((ax,ay,0))
  zero(label+f'开门{angle}',moved^(frame+cassette))
  for name,part in parts.items():
   lo,hi=np.array(moved.bounding_box()[:3]),np.array(moved.bounding_box()[3:]);b=np.array(part.bounding_box())
   if np.all(hi>b[:3]) and np.all(b[3:]>lo):zero(label+name+str(angle),moved^part)
 variants.append({'label':label,'outer_height_mm':height,'scale_from_source':scale,'pivot_xy':[ax,ay],
                  'outer_pedestal_width_mm':18*scale,'outer_frame_width_mm':13.6*scale,
                  'opening_width_mm':10*scale,'opening_height_mm':23.1*scale,
                  'hinge_wall_mm':1.35*scale-1.2,'pedestal_pocket_depth_mm':1.2,
                  'release_for_static_trial':label=='40毫米'})
data={'date':'2026-11-13','status':'外观修订与静态试配；驱动仓待实测舵机尺寸后定型',
      'stage_diameter_mm':600,'courtyard_diameter_mm':400,'deck_thickness_mm':8,'foot_height_mm':5,'overall_stage_height_mm':13,
      'cassette_mm':[64,44],'clearance_per_side_mm':.25,'shaft_bore_mm':2.4,'shaft_nominal_mm':2,
      'main_door':'40毫米','door_variants':variants,'parts':rows,'checks':checks,
      'foot_positions':foot_positions,'bridges':bridges,'cassette_bolts':bolt_points,
      'actuation_status':'只预留门轴通道；叶片与金属轴的固定、卧放舵机及换向传动尚未定型，不能据此宣称电动门完成。',
      'unknowns':['舵机实际三维尺寸、输出轴方位和舵盘接口','卧放传动与局部仓的最终高度','打印槽口和轴孔的实物配合'],
      'supersedes':'print-stage-600mm-20261113 高底座/粗门方案，不再交付该方案。','actual_print_test':False}
(A/'slim_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print('SLIM_GEOMETRY_PASS',len(rows),len(checks),flush=True)
