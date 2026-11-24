"""Pack the corrected static model; STL only, fixed millimetre coordinates."""
import json,hashlib,sys
from pathlib import Path
import numpy as np,trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon,box
R=Path(__file__).resolve().parents[1];A=R/'analysis';O=R/'整盘STL';O.mkdir(exist_ok=True)
data=json.loads((A/'slim_manifest.json').read_text(encoding='utf8'));index={r['id']:r for r in data['parts']};packed=[]
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
tile_plates=[
    [('薄底板11',25,40,180),('薄底板33',110,110,180)],
    [('薄底板13',25,40,90),('薄底板31',110,110,90)],
    [('薄底板12',25,40)], [('薄底板21',25,40)],
    [('薄底板22',25,40)], [('薄底板23',25,40)], [('薄底板32',25,40)]]
for n,ps in enumerate(tile_plates,1):
    if n<=6:
        ps += [('底部接缝条_打印12件',25,10),('底部接缝条_打印12件',84,10),('隐藏脚垫_打印12件',143,10),('隐藏脚垫_打印12件',170,10)]
    pack('底座'+str(n),'底座',ps,'base')
pack('白门','门',[('40毫米插座板',25,40),('40毫米门框',100,40),('40毫米门扇',140,40)],'door')
# Three running gaps: 0.15/0.25/0.35 mm per side. The same 20 x 10 tongue
# enters all three sockets. Hole blocks check a 2 mm metal rod in both
# printed orientations, without spending material on the whole model.
socket=cub((0,0,0),(88,20,6))
for i,gap in enumerate((.15,.25,.35)):
    x=15+29*i
    socket=socket-cub((x-10-gap,5-gap,2.8),(x+10+gap,15+gap,6.1))
    for k in range(i+1):socket=socket+cyl(.6,.5).translate((x-2+2*k,2,6))
tongue=cub((0,0,0),(24,14,2))+cub((2,2,2),(22,12,5))
vblock=cub((0,0,0),(32,12,5));hblock=cub((0,0,0),(32,12,7))
for i,d in enumerate((2.2,2.4,2.6)):
    x=6+10*i;vblock=vblock-cyl(d/2,5.2).translate((x,6,-.1))
    hblock=hblock-cyl(d/2,12.2).rotate((90,0,0)).translate((x,12.1,3.5))
    for k in range(i+1):
        vblock=vblock+cyl(.5,.5).translate((x-2+2*k,2,5))
        hblock=hblock+cyl(.5,.5).translate((x-2+2*k,2,7))
nutblock=cub((0,0,0),(30,16,8))
for x,af,depth,r,h in [(8,5.9,2.6,1.7,4),(23,4.3,1.8,1.2,8.2)]:
    nutblock=nutblock-M.cylinder(depth+.1,af/np.sqrt(3),circular_segments=6).translate((x,8,-.1))-cyl(r,h+.1).translate((x,8,-.1))
pack('试配','试配',[(mesh(socket),25,40),(mesh(tongue),120,40),(mesh(vblock),25,70),(mesh(hblock),65,70),(mesh(nutblock),105,70)],'trial')
(A/'packed_manifest.json').write_text(json.dumps(packed,ensure_ascii=False,indent=2),encoding='utf8')
print('SLIM_PACKING_PASS',len(packed),flush=True)
