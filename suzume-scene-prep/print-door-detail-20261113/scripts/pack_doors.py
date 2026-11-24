"""Pack the corrected static model; STL only, fixed millimetre coordinates."""
import json,hashlib,sys
from pathlib import Path
import numpy as np,trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon,box
R=Path(__file__).resolve().parents[1];A=R/'analysis';O=R/'整盘STL';O.mkdir(exist_ok=True)
data=json.loads((A/'door_manifest.json').read_text(encoding='utf8'));index={r['id']:r for r in data['parts']};packed=[]
sys.path.insert(0,str(R.parent/'print-400mm-20261030/.deps'));import manifold3d as mf
M=mf.Manifold
def cub(lo,hi):return M.cube(tuple(np.array(hi)-lo)).translate(tuple(lo))
def cyl(r,h):return M.cylinder(h,r,circular_segments=64)
def mesh(m):
    q=m.to_mesh64();return trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=False)
def pack(name,group,placements,kind):
    meshes=[];polys=[]
    for placement in placements:
        source,x,y=placement[:3];angle=placement[3] if len(placement)>3 else 0
        m=source.copy() if isinstance(source,trimesh.Trimesh) else trimesh.load(index[source]['stl'],force='mesh')
        assert m.is_watertight and m.is_winding_consistent
        if angle:m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),[0,0,1]))
        m.apply_translation(-m.bounds[0]);m.apply_translation([x,y,0]);meshes.append(m)
        pts=m.vertices[:,:2];poly=Polygon(pts[ConvexHull(pts).vertices]);polys.append(poly)
        assert box(4,4,252,252).covers(poly.buffer(3)),(name,poly.bounds)
        assert not poly.buffer(3).intersects(box(0,0,18,28)),name
    for i,p in enumerate(polys):
        for j in range(i):assert p.distance(polys[j])>=6,(name,i,j,p.distance(polys[j]))
    full=trimesh.util.concatenate(meshes);folder=O/group;folder.mkdir(exist_ok=True);path=folder/(name+'.stl');full.export(path,file_type='stl_ascii')
    reopened=trimesh.load(path,force='mesh');components=reopened.split()
    assert reopened.is_watertight and reopened.is_winding_consistent and len(components)==len(meshes)
    assert all(c.is_volume and c.volume>0 for c in components)
    packed.append({'id':name,'group':group,'quantity':1,'packed':True,'settings_kind':kind,'stl_path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'components':len(meshes),'size_mm':reopened.extents.tolist(),'placements':[{'id':p[0] if isinstance(p[0],str) else '配合试件','x':p[1],'y':p[2],'rotation_z':p[3] if len(p)>3 else 0} for p in placements]})
    print('PACKED',name,len(meshes),flush=True)

combined=[]
for i,v in enumerate(data['door_variants']):
    label=v['label'];factor=v['factor'];x=24+76*i
    pack(f'白门_{factor:g}倍', '单档', [(label+'插座板',25,40),(label+'门框',103,40),(label+'门扇',170,40)],'door')
    combined += [(label+'插座板',x,40),(label+'门框',x,95),(label+'门扇',x,130)]
pack('三档同盘','同盘',combined,'door')
(A/'packed_manifest.json').write_text(json.dumps(packed,ensure_ascii=False,indent=2),encoding='utf8')
print('DOOR_PACKING_PASS',len(packed),flush=True)
