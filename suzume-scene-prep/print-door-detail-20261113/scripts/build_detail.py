"""Use the app's actual FBX geometry; strengthen it for printable white models."""
import json,sys,math,hashlib,warnings,itertools
from pathlib import Path
import numpy as np,trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
warnings.filterwarnings('ignore',category=RuntimeWarning)
R=Path(__file__).resolve().parents[1];P=R.parent;A=R/'analysis';F=A/'software_meshes';B=P/'print-stage-500mm-20261113';Q=P/'print-white-quality-20261030'
sys.path.insert(0,str(P/'print-400mm-20261030/.deps'));import manifold3d as mf
from close_tjunctions import close_tjunctions
M,C,OP=mf.Manifold,mf.CrossSection,mf.OpType
for p in [A/'assembly',R/'STL']:p.mkdir(exist_ok=True)
checks=[];rows=[];variants=[]
def cube(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def cyl(r,h,x=0,y=0,z=0,n=64):return M.cylinder(h,r,circular_segments=n).translate((x,y,z))
def union(ms):return M.batch_boolean(ms,OP.Add)
def tm(m):
 d=m.to_mesh64();return trimesh.Trimesh(np.array(d.vert_properties)[:,:3],np.array(d.tri_verts),process=False)
def meshfile(path):
 d=np.load(path);return trimesh.Trimesh(d['vertices'],d['faces'],process=True)
def man(mesh):
 mesh=mesh.copy();mesh.fix_normals();return M(mf.Mesh64(np.asarray(mesh.vertices),np.asarray(mesh.faces,dtype='uint64')))
def source(name):return meshfile(F/(name+'.npz'))
def zero(name,m):
 v=max(0,m.volume());assert v<.003,(name,v);checks.append({'check':name,'interference_mm3':v})
def prism_xz(profile,y0,y1):return profile.extrude(y1-y0).translate((0,0,y0)).rotate((-90,0,0))
def footprint(m):return m.rotate((90,0,0)).project()
def emit(name,m,label,rotate=(0,0,0)):
 # FBX's single-precision coplanar paint overlays can leave zero-thickness
 # boolean crumbs. Remove only numerically negligible, submicron fragments.
 m=m.simplify(.0003);pieces=m.decompose();removed=[p for p in pieces if abs(p.volume())<1e-5 and min(np.array(p.bounding_box()[3:])-p.bounding_box()[:3])<1e-5]
 if removed:
  m=union([p for p in pieces if p not in removed]);checks.append({'check':name+'浮点碎片清理','count':len(removed),'volume_mm3':sum(abs(p.volume()) for p in removed)})
 mesh=tm(m);assert len(m.decompose())==1,(name,[(q.volume(),q.bounding_box()) for q in m.decompose()])
 if np.any(mesh.area_faces<=1e-12):
  before=mesh.volume;mesh.merge_vertices(digits_vertex=5);mesh.update_faces(mesh.area_faces>1e-12);mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
  assert abs(mesh.volume-before)<max(1e-6,abs(before)*1e-8),(name,'degenerate cleanup changed volume')
 if not mesh.is_volume:
  before=tm(m)
  mesh=close_tjunctions(mesh);mesh.fix_normals()
  dv=abs(mesh.volume/before.volume-1);db=float(np.max(abs(mesh.bounds-before.bounds)))
  assert dv<.0001 and db<.005,(name,'repair deviation',dv,db)
  checks.append({'check':name+'接缝拓扑修复','volume_change_fraction':dv,'bounds_change_mm':db})
 m=man(mesh)
 assert mesh.is_volume and mesh.is_winding_consistent and np.all(mesh.area_faces>1e-12),(name,mesh.is_volume,mesh.is_watertight,mesh.is_winding_consistent,float(mesh.area_faces.min()),int(sum(mesh.area_faces<=1e-12)))
 np.savez_compressed(A/'assembly'/(name+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
 printable=tm(m.rotate(rotate));printable.apply_translation(-printable.bounds[0]);folder=R/'STL'/label;folder.mkdir(exist_ok=True)
 p=folder/(name+'.stl');printable.export(p,file_type='stl_ascii');reopened=trimesh.load(p,force='mesh')
 assert reopened.is_volume and len(reopened.split())==1 and np.all(reopened.area_faces>1e-12),name
 rows.append({'id':name,'group':label,'quantity':1,'stl':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_mm':reopened.extents.tolist(),'rotate':list(rotate)})
 print('PART',name,np.round(reopened.extents,3).tolist(),flush=True)
 return m
def components(name):
 result=[]
 for part in source(name).split(only_watertight=False):
  assert part.is_watertight,(name,'non-solid structural component');part.fix_normals();result.append(man(part))
 return result
frame_src=sum([components(n) for n in ['DoorFrame_01','DoorFrame_02','DoorFrame_03']],[])
leaf_sources={n:components(n) for n in ['DoorLeaf_02','DoorLeaf_04','DoorLeaf_05','DoorLeaf_06']}
zmin=-.024705827236175537;zmax=2.2188971042633057
base=json.loads((B/'analysis/slim_manifest.json').read_text(encoding='utf8'))
deck=union([man(meshfile(B/'analysis/assembly'/(r['id']+'.npz'))) for r in base['parts'] if r['id'].startswith('薄底板')])
court={r['id']:man(meshfile(Q/'analysis/assembly_meshes'/(r['id']+'.npz'))) for r in json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts'] if r['id'][0] in 'WS'}
outer=C([[(-32,-22),(32,-22),(32,18),(28,22),(-32,22)]],mf.FillRule.Positive);inner=C([[(-25,-15),(25,-15),(25,11),(21,15),(-25,15)]],mf.FillRule.Positive)
CY=15
def wear(name,scale):
 m=source(name);pieces=m.split(only_watertight=False);polys=[]
 for piece in pieces:
  for tri in piece.triangles:
   p=Polygon(tri[:,[0,2]]*np.array([scale,-scale]))
   if p.area>1e-8:polys.append(p)
 merged=unary_union(polys);contours=[]
 for p in ([merged] if merged.geom_type=='Polygon' else merged.geoms):
  if p.area<.5:continue
  contours.append(np.asarray(p.exterior.coords)[:-1]);contours.extend(np.asarray(q.coords)[:-1] for q in p.interiors)
 if not contours:return M()
 profile=C(contours,mf.FillRule.EvenOdd).simplify(.005).offset(-.25).offset(.22).simplify(.005)
 return prism_xz(profile,-100,100).translate((0,CY,8.4-zmin*scale))
for dots,(factor,height) in enumerate([(1.25,50),(1.5,60),(1.75,70)],1):
 label=f'{height}毫米';scale=(height-1.6)/(zmax-zmin)
 def transform(m):return m.scale((scale,scale,scale)).translate((0,CY,8.4-zmin*scale))
 frame_pieces=[transform(m) for m in frame_src];frame=union(frame_pieces)
 main=transform(leaf_sources['DoorLeaf_02'][0]);body_bounds=np.array(main.bounding_box());body_y0,body_y1=body_bounds[1],body_bounds[4]
 # Maintain a 1.6 mm plank core; build all supports behind the original faces.
 if body_y1-body_y0<1.6:
  main+=cube((body_bounds[0],body_y0,body_bounds[2]),(body_bounds[3],body_y0+1.6,body_bounds[5]));body_y1=body_y0+1.6
 leaf_parts=[main];source_leaf_parts=[]
 for n,items in leaf_sources.items():
  for i,src in enumerate(items):
   if n=='DoorLeaf_02' and i==0:continue
   m=transform(src)
   # The virtual knob overlaps the jamb. Move only its plate/stem/knob inward
   # 1.5 mm so the printable front moulding can stay continuous.
   if n=='DoorLeaf_05' and i>=6:m=m.translate((1.5,0,0))
   bb=np.array(m.bounding_box());source_leaf_parts.append(m)
   if bb[4]<body_y0+.02:
    m+=prism_xz(footprint(m),bb[4]-.03,body_y0+.06)
   elif bb[1]>body_y1-.02:
    m+=prism_xz(footprint(m),body_y1-.06,bb[1]+.03)
   # Hardware's submillimetre neck is reinforced from behind, retaining knob face.
   if n=='DoorLeaf_05' and i in [7,10]:
    cx=(bb[0]+bb[3])/2;cz=(bb[2]+bb[5])/2
    m+=cube((cx-.5,bb[1],cz-.5),(cx+.5,bb[4],cz+.5))
   leaf_parts.append(m)
 leaf=union(leaf_parts)
 assert len(leaf.decompose())==1,('leaf supports',height,[(q.volume(),q.bounding_box()) for q in leaf.decompose()])
 # Convert the app's actual planar wear meshes into shallow engraved relief.
 etch=.24+(height-50)*.004
 protected=C.batch_boolean([footprint(p).offset(.18) for p in source_leaf_parts],OP.Add).simplify(.005)
 scratches=wear('DoorLeaf_00',scale)-prism_xz(protected,-100,100)
 front_slice=cube((body_bounds[0]-.01,body_y0-.1,body_bounds[2]-.01),(body_bounds[3]+.01,body_y0+etch,body_bounds[5]+.01))
 leaf=leaf-(scratches^front_slice)
 # Relieve the jamb only where the original virtual meshes touch/overlap.
 clearboxes=[]
 for m in [main]+source_leaf_parts:
  bb=np.array(m.bounding_box());clearboxes.append(cube(bb[:3]-.25,bb[3:]+.25))
 frame=frame-union(clearboxes)
 # Real 2 mm pin hinges sit behind the original slender visible hinges.
 ax=body_bounds[3];frame_back=max(m.bounding_box()[4] for m in frame_pieces);ay=frame_back+2.35
 moving_z=[6.8+.16*height,6.8+.76*height];moving_h=3.2;fixed_h=2.4;gap=.35;r=2.05
 for j,z in enumerate(moving_z):
  web=cube((ax-3.4,body_y1-.15,z),(ax+.1,ay+.15,z+moving_h));leaf_parts.append(web)
  leaf+=cyl(r,moving_h,ax,ay,z)+web
  fz=z-gap-fixed_h if j==0 else z+moving_h+gap
  frame+=cyl(r,fixed_h,ax,ay,fz)+cube((ax-.1,CY-.01*scale,fz),(.53573*scale,ay+.15,fz+fixed_h))
 # Swept, padded envelopes relieve only jamb material in the leaf's path.
 # Dense angular sampling plus 0.25 mm padding covers the between-step arcs.
 sweep=[]
 for part in leaf_parts:
  bb=np.array(part.bounding_box());corners=np.array(list(itertools.product(*zip(bb[:3]-.25,bb[3:]+.25))))
  points=[]
  for angle in range(0,107,2):
   rad=math.radians(-angle);v=corners.copy();x=v[:,0]-ax;y=v[:,1]-ay
   v[:,0]=ax+x*math.cos(rad)-y*math.sin(rad);v[:,1]=ay+x*math.sin(rad)+y*math.cos(rad);points.extend(v)
  cutter=M.hull_points(np.array(points));sweep.append(cutter)
 frame=frame-union(sweep)
 fragments=frame.decompose();retained=max(fragments,key=lambda p:p.volume())
 for remnant in fragments:
  if remnant is retained:continue
  bb=np.array(remnant.bounding_box());assert remnant.volume()<.5*(height/50)**3 and bb[5]-bb[2]<.5*(height/50) and bb[5]<10,('unexpected disconnected frame',height,remnant.volume(),bb)
  checks.append({'check':label+'去除悬空止口尾料','volume_mm3':remnant.volume()})
 frame=retained
 fw=(.57664305+.57651794)*scale+2.4;fy0=-.14391202*scale+CY-.8;fy1=ay+r+.7
 pedestal=cube((-fw/2,fy0,6.8),(fw/2,fy1,8.5));frame+=pedestal
 bore=cyl(1.2,height+12,ax,ay,-.2);frame-=bore;leaf-=bore
 cassette=outer.extrude(5).translate((0,CY,3))+inner.extrude(3).translate((0,CY,0))
 cassette=cassette-bore-cube((-fw/2-.25,fy0-.25,6.8),(fw/2+.25,fy1+.25,8.1))
 for x,y in base['cassette_bolts']:cassette=cassette-cyl(1.2,5.3,x,y,2.9)-cyl(2.2,1.7,x,y,6.4)
 for j in range(dots):cassette-=cyl(.65,.6,(j-(dots-1)/2)*3,-3,7.5)
 frame=emit(label+'门框',frame,label);leaf=emit(label+'门扇',leaf,label,(-90,0,0));cassette=emit(label+'插座板',cassette,label)
 zero(label+'插座底板',cassette^deck);zero(label+'门框插座',frame^cassette);zero(label+'轴孔贯通',(frame+leaf+cassette)^cyl(1.19,height+10,ax,ay,-.1))
 obstacle=frame+cassette+(deck^cube((-80,-80,-.1),(80,100,8.1)))
 for angle in range(106):
  moved=leaf.translate((-ax,-ay,0)).rotate((0,0,-angle)).translate((ax,ay,0));zero(label+f'开门{angle}',moved^obstacle)
  bb=np.array(moved.bounding_box());assert bb[0]>-80 and bb[3]<80 and bb[1]>-80 and bb[4]<100
  for name,m in court.items():
   mb=np.array(m.bounding_box())
   if np.all(bb[3:]>mb[:3]) and np.all(mb[3:]>bb[:3]):zero(label+name+str(angle),moved^m)
 variants.append({'label':label,'factor':factor,'outer_height_mm':height,'outer_frame_width_mm':fw-2.4,'pivot_xy':[ax,ay],'scale_from_software':scale,'cassette_dots':dots,'opening_sign':-1,'engraving_depth_mm':etch,'pedestal_mm':[fw,fy1-fy0,1.7]})
data={'date':'2026-11-13','status':'软件原门细节转实体打印，静态试配版','base_project':str(B),'software_source':str(A/'software_source.json'),
      'stage_diameter_mm':500,'courtyard_diameter_mm':400,'baseline_door_height_mm':40,'main_door':'60毫米','door_variants':variants,'parts':rows,'checks':checks,
      'shaft_bore_mm':2.4,'shaft_nominal_mm':2,'actual_print_test':False,'servo_drive_finished':False,
      'preserved':['软件 FBX 的六格门板位置与比例','双面层次、细边线、分层门楣与边框','长锁板、圆把手、正面三只细合页','源磨损网格转成浅浮雕'],
      'adapted':['单独的贴面背后补实体连接','门板芯最小 1.6 mm','把手与锁板内移 1.5 mm，避免原虚拟几何重叠切坏门框细线','2 mm 金属轴与功能合页藏到背后','隐蔽门框止口留 0.25 mm 运动间隙','浅槽对应三档台阶；公共底座接口不变']}
(A/'door_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');print('DETAILED_DOORS_PASS',len(rows),len(checks),flush=True)
