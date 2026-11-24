import hashlib,json
from pathlib import Path
import numpy as np,trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon,box
R=Path(__file__).resolve().parents[1];A=R/'analysis';O=R/'整盘STL';O.mkdir(exist_ok=True)
manifest=json.loads((A/'structure_manifest.json').read_text(encoding='utf8'));byname={x['id']:x for x in manifest['parts']}
packed=[]
def get(name):return trimesh.load(byname[name]['stl_path'],force='mesh')
def pack(name,group,placements,kind):
    meshes=[];polys=[]
    for source,x,y in placements:
        m=get(source);m.apply_translation(-m.bounds[0]);m.apply_translation([x,y,0]);meshes.append(m)
        q=m.vertices[:,:2];poly=Polygon(q[ConvexHull(q).vertices]);polys.append(poly)
        assert box(4,4,252,252).covers(poly.buffer(3)),(name,source,poly.bounds)
        assert not poly.buffer(3).intersects(box(0,0,18,28)),(name,source,'excluded corner')
    for i,p in enumerate(polys):
        for j in range(i):assert p.distance(polys[j])>=6,(name,placements[i],placements[j],p.distance(polys[j]))
    mesh=trimesh.util.concatenate(meshes);folder=O/group;folder.mkdir(exist_ok=True)
    path=folder/(name+'.stl');mesh.export(path,file_type='stl_ascii')
    loaded=trimesh.load(path,force='mesh')
    assert loaded.is_watertight and loaded.is_winding_consistent and len(loaded.split())==len(meshes),name
    np.savez_compressed(A/(name+'_packed.npz'),vertices=mesh.vertices,faces=mesh.faces)
    packed.append({'id':name,'group':group,'quantity':1,'packed':True,'settings_kind':kind,'stl_path':str(path),
                   'stl_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'components':len(meshes),'placements':placements})
    print('PACKED',name,len(meshes),flush=True)
normal='围边_打印7件';wire='出线围边_打印1件';width=byname[normal]['print_size_mm'][0]
ys=[35+i*(byname[normal]['print_size_mm'][1]+7) for i in range(4)]
pack('围边第1盘','底座',[ (normal,128-width/2,y) for y in ys],'base')
pack('围边第2盘','底座',[ (normal if i<3 else wire,128-width/2,y) for i,y in enumerate(ys)],'base')
placements=[('中央支脚_打印4件',20+i*53,10) for i in range(4)]
placements += [('接缝压条_打印12件',8+c*58,70+r*27) for r in range(3) for c in range(4)]
pack('支脚与接缝条','底座',placements,'base')
for label,cm in [('小门','08'),('主门','10'),('大门','12')]:
    pack(cm+'厘米门组件','门',[(label+'插座板',22,7),(label+'门框',22,120),(label+'门扇',111,120)],'door')
placements=[('舵机升降托架',20,8),('舵盘接头',182,8),('舵盘夹片',182,48),
            ('门轴_打印1件',187,94),('门轴承托垫圈',211,94)]
placements += [('侧向垫圈_打印4件',182+i*12,118) for i in range(4)]
placements += [('舵机滑动横梁_打印2件',20,y) for y in (118,138)]
placements += [('升降吊耳_打印4件',x,y) for x,y in [(20,163),(97,163),(20,191),(97,191)]]
pack('通用传动件','门',placements,'drive')
(A/'packed_manifest.json').write_text(json.dumps(packed,ensure_ascii=False,indent=2),encoding='utf8')
print('PACKED_DELIVERY_GEOMETRY_PASS',len(packed),flush=True)
