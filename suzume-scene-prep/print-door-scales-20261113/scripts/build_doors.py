"""Three linear-size variants of the current 40 mm door, fixed mounting interface."""
import json,hashlib,sys,math
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];P=R.parent;A=R/'analysis';O=R/'STL';B=P/'print-stage-500mm-20261113';Q=P/'print-white-quality-20261030'
for p in (A,A/'assembly',O):p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(P/'print-400mm-20261030/.deps'));import manifold3d as mf
M,C,OP=mf.Manifold,mf.CrossSection,mf.OpType
rows=[];checks=[]
def cube(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def cyl(r,h,x=0,y=0,z=0):return M.cylinder(h,r,circular_segments=64).translate((x,y,z))
def union(ms):return M.batch_boolean(ms,OP.Add)
def load(folder,name):
 d=np.load(folder/(name+'.npz'));return M(mf.Mesh64(d['vertices'],d['faces'].astype('uint64')))
def tm(m):
 d=m.to_mesh64();return trimesh.Trimesh(np.array(d.vert_properties)[:,:3],np.array(d.tri_verts),process=False)
def zero(label,m):
 v=max(0,m.volume());assert v<.001,(label,v);checks.append({'check':label,'interference_mm3':v})
def emit(name,m,label,rotate=(0,0,0)):
 m=m.simplify(.001);original=tm(m);assert original.is_volume and len(m.decompose())==1,name
 assert np.all(original.area_faces>1e-12),name
 np.savez_compressed(A/'assembly'/(name+'.npz'),vertices=original.vertices,faces=original.faces)
 mesh=tm(m.rotate(rotate));shift=-mesh.bounds[0];mesh.apply_translation(shift)
 folder=O/label;folder.mkdir(exist_ok=True);path=folder/(name+'.stl');mesh.export(path,file_type='stl_ascii')
 check=trimesh.load(path,force='mesh');assert check.is_volume and check.is_winding_consistent,name
 assert len(check.split())==1 and np.all(check.area_faces>1e-12),name
 rows.append({'id':name,'group':label,'quantity':1,'stl':str(path),'size_mm':check.extents.tolist(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rotate':list(rotate),'shift':shift.tolist()})
 print('PART',name,np.round(check.extents,3).tolist(),flush=True)
base=json.loads((B/'analysis/slim_manifest.json').read_text(encoding='utf8'))
deck=union([load(B/'analysis/assembly',r['id']) for r in base['parts'] if r['id'].startswith('薄底板')])
court={r['id']:load(Q/'analysis/assembly_meshes',r['id']) for r in json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts'] if r['id'][0] in 'WS'}
source_frame=load(Q/'analysis/assembly_meshes','D01_门框与台阶');source_leaf=load(Q/'analysis/assembly_meshes','D02_六格门扇')
# Fill only the known original 1.3 mm axle bores before scaling. Simply
# subtracting a 2.4 mm drill cannot reduce a scaled bore that is already larger.
frame_filled=source_frame+union([cyl(.66,h,5.5,-2.2,z) for z,h in [(5,1.6),(8.1,3),(25.1,3)]])
leaf_filled=source_leaf+union([cyl(.66,3,5.5,-2.2,z) for z in [11.45,21.75]])
zero('补孔只改变原门轴通道',(frame_filled-source_frame)-cyl(.661,30,5.5,-2.2,4))
zero('补孔只改变原门扇轴道',(leaf_filled-source_leaf)-cyl(.661,30,5.5,-2.2,4))
outer=C([[(-32,-22),(32,-22),(32,18),(28,22),(-32,22)]],mf.FillRule.Positive)
inner=C([[(-25,-15),(25,-15),(25,11),(21,15),(-25,15)]],mf.FillRule.Positive)
CY=15;variants=[]
for dots,(factor,height) in enumerate([(1.25,50),(1.5,60),(1.75,70)],1):
 label=f'{height}毫米';scale=height/26.9
 frame=frame_filled.translate((0,0,-5)).scale((scale,scale,scale)).translate((0,CY,6.8))
 leaf=leaf_filled.translate((0,0,-5)).scale((scale,scale,scale)).translate((0,CY,6.8))
 ax,ay=5.5*scale,CY-2.2*scale
 # Start below zero so the cassette hole truly passes through its bottom.
 bore=cyl(1.2,height+12,ax,ay,-.2);frame-=bore;leaf-=bore
 cassette=outer.extrude(5).translate((0,CY,3))+inner.extrude(3).translate((0,CY,0))
 cassette=cassette-bore-cube((-9*scale-.25,CY-4*scale-.25,6.8),(9*scale+.25,CY+4*scale+.25,8.1))
 for x,y in base['cassette_bolts']:cassette=cassette-cyl(1.2,5.3,x,y,2.9)-cyl(2.2,1.7,x,y,6.4)
 # One/two/three recessed dots distinguish matching cassettes after printing.
 for j in range(dots):cassette-=cyl(.65,.6,(j-(dots-1)/2)*3,-3,7.5)
 emit(label+'门框',frame,label);emit(label+'门扇',leaf,label,rotate=(-90,0,0));emit(label+'插座板',cassette,label)
 zero(label+'共用底座槽',cassette^deck);zero(label+'门框落座',frame^cassette)
 zero(label+'门框不碰底座',frame^deck);zero(label+'门轴贯通',(frame+leaf+cassette)^cyl(1.19,height+12,ax,ay,-.1))
 # Verify the material immediately around the bore, independently of the
 # original outer cylinder's simplified facets. This catches scaled holes
 # larger than 2.4 mm without assuming a perfectly circular outer silhouette.
 for body,z in [(frame,9),(frame,26),(leaf,12),(leaf,23)]:
  zz=(z-5)*scale+6.8;ring=cyl(1.65,.12,ax,ay,zz)-cyl(1.23,.14,ax,ay,zz-.01)
  zero(label+'轴套实心环'+str(z),ring-body)
 shaft=cyl(1,height+10,ax,ay,0)
 obstacle=frame+cassette+(deck^cube((-80,-80,-.1),(80,90,8.1)))
 for angle in range(0,106):
  moved=leaf.translate((-ax,-ay,0)).rotate((0,0,angle)).translate((ax,ay,0))
  bounds=np.array(moved.bounding_box());assert bounds[0]>-80 and bounds[3]<80 and bounds[1]>-80 and bounds[4]<90
  zero(label+f'开门{angle}度',moved^obstacle);zero(label+f'开门{angle}轴孔',moved^shaft)
  lo,hi=np.array(moved.bounding_box()[:3]),np.array(moved.bounding_box()[3:])
  for name,part in court.items():
   bounds=np.array(part.bounding_box())
   if np.all(hi>bounds[:3]) and np.all(bounds[3:]>lo):zero(label+name+str(angle),moved^part)
 variants.append({'label':label,'factor':factor,'outer_height_mm':height,'scale_from_source':scale,'pivot_xy':[ax,ay],
                  'outer_frame_width_mm':13.6*scale,'outer_pedestal_width_mm':18*scale,
                  'opening_width_mm':10*scale,'opening_height_mm':23.1*scale,'hinge_wall_mm':1.35*scale-1.2,
                  'cassette_dots':dots,'cassette_mm':[64,44],'pedestal_pocket_depth_mm':1.2})
data={'date':'2026-11-13','status':'三档白门静态试配，舵机传动未定型','baseline_door_height_mm':40,
      'stage_diameter_mm':500,'courtyard_diameter_mm':400,'base_project':str(B),'main_door':'60毫米','door_variants':variants,
      'parts':rows,'checks':checks,'shaft_bore_mm':2.4,'shaft_nominal_mm':2,'actual_print_test':False,
      'mounting_interface':'保持 64×44 mm 插座板、下方缺角定位舌与 M2 孔位。每档使用专属浅槽和轴孔位置。',
      'actuation_status':'门轴孔已贯通；舵机支架、轴与门扇的传扭连接仍需按舵机实物定型。'}
(A/'door_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print('THREE_DOORS_GEOMETRY_PASS',len(rows),len(checks),flush=True)
