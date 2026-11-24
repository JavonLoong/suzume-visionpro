import hashlib, json, math, sys, zipfile
from pathlib import Path
import numpy as np, trimesh
R=Path(__file__).resolve().parents[1];P=R.parent;A=R/'analysis'
sys.path.insert(0,str(P/'print-400mm-20261030/.deps'))
import manifold3d as mf
M,C,OP=mf.Manifold,mf.CrossSection,mf.OpType

def load(path):
    q=np.load(path);return M(mf.Mesh64(q['vertices'],q['faces'].astype('uint64')))
def cube(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def cyl(r,h,x=0,y=0,z=0,n=64):return M.cylinder(h,r,circular_segments=n).translate((x,y,z))
def mesh(m):
    q=m.to_mesh64();return trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=False)

items=[]
def item(name,body,xy,rotation=0):
    body=body.rotate((0,0,rotation));m=mesh(body);m.apply_translation(-m.bounds[0]);m.apply_translation([*xy,0])
    assert m.is_watertight and m.is_winding_consistent,name
    items.append({'name':name,'mesh':m,'bounds':m.bounds.tolist()})
    return m

for name,xy in [('W01_环形建筑',(8,8)),('S01_钢架',(112,8))]:
    body=load(P/'print-white-quality-20261030/analysis/assembly_meshes'/(name+'.npz'))
    foot=body^cube((-250,-250,5),(250,250,8.001))
    shape=C(foot.project().to_polygons(),mf.FillRule.Positive)
    outline=shape.offset(3.5);inner=shape.offset(-3)
    probe=(outline-inner).extrude(1.2)+(outline-shape.offset(.25)).extrude(3).translate((0,0,1.2))
    item(name+'原件轮廓试槽_单边025',probe,xy)
    # Nominal original part fits this full-outline probe at its bottom datum.
    check=(body.translate((0,0,-3.8))^probe).volume()
    assert check < .001,(name,check)

for i,gap in enumerate((.15,.25,.35)):
    b=cube((0,0,0),(36,30,6))
    b=b-cube((3,4,1),(13+2*gap,16+2*gap,6.2))
    b=b-cyl(4.5+(.2+i*.1),6.2,25,10,-.1)
    b=b-cyl((8+2*gap)/math.sqrt(3),4.2,25,23,1.9,n=6)
    # One, two and three notches identify the three fit settings without text fonts.
    for j in range(i+1):b=b-cube((4+j*3,26,5),(5.2+j*3,30.2,6.1))
    item(f'配合试块_{gap:.2f}',b,(8+i*42,168))
male=cube((0,0,0),(10,12,5))+cube((-2,-2,-2),(12,14,0))
item('标准插脚_10x12',male,(139,168))
item('门轴',load(A/'assembly/门轴_打印1件.npz'),(185,8))
item('舵盘接头',load(A/'assembly/舵盘接头.npz'),(181,36))
item('舵盘夹片',load(A/'assembly/舵盘夹片.npz'),(181,76))

# A single uniform spacer type makes the carrier-to-hanger offset explicit.
spacer=cyl(4,4)-cyl(1.7,4.2,z=-.1)
spacer_mesh=mesh(spacer);spacer_mesh.apply_translation(-spacer_mesh.bounds[0])
out=R/'STL/门通用件/侧向垫圈_打印4件.stl';spacer_mesh.export(out,file_type='stl_ascii')
q=mesh(spacer);np.savez_compressed(A/'assembly/侧向垫圈_打印4件.npz',vertices=q.vertices,faces=q.faces)
np.savez_compressed(A/'侧向垫圈_打印4件_print.npz',vertices=spacer_mesh.vertices,faces=spacer_mesh.faces)
manifest=json.loads((A/'structure_manifest.json').read_text(encoding='utf8'))
manifest['parts'].append({'id':'侧向垫圈_打印4件','group':'门通用件','quantity':4,'print_size_mm':spacer_mesh.extents.tolist(),
                        'volume_mm3':float(q.volume),'faces':len(q.faces),'components':1,'rotation_degrees':[0,0,0],
                        'print_translation':(-q.bounds[0]).tolist(),'note':'4 mm 厚，放在托架侧耳与升降吊耳之间。',
                        'stl_path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(A/'structure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
for i in range(4):item('侧向垫圈'+str(i+1),spacer,(184+i*12,120))

# Check exact XY silhouettes and safe printer margin.
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
polys=[]
for x in items:
    m=x['mesh'];h=m.convex_hull.vertices
    from scipy.spatial import ConvexHull
    v=h[:,:2];poly=Polygon(v[ConvexHull(v).vertices]);polys.append(poly)
    assert box(5,5,248,248).covers(poly.buffer(2)),x['name']
for i,p in enumerate(polys):
    for j in range(i):assert p.distance(polys[j])>3,(items[i]['name'],items[j]['name'],p.distance(polys[j]))
combined=trimesh.util.concatenate([x['mesh'] for x in items])
trial=R/'STL/试配';trial.mkdir(exist_ok=True)
file=trial/'试配.stl';combined.export(file,file_type='stl_ascii')
reloaded=trimesh.load(file,force='mesh');assert reloaded.is_watertight and reloaded.is_winding_consistent
assert len(reloaded.split())==len(items)
np.savez_compressed(A/'trial_plate.npz',vertices=combined.vertices,faces=combined.faces)
(A/'trial_layout.json').write_text(json.dumps([{'name':x['name'],'bounds':x['bounds']} for x in items],ensure_ascii=False,indent=2),encoding='utf8')
print('TRIAL_PLATE_PASS',len(items),'separate printable pieces',flush=True)
