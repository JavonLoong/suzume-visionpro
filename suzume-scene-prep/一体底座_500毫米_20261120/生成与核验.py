from pathlib import Path
import json, math, hashlib, zipfile
import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parent
SOURCE = Path('D:/虚拟C盘/学习秋/底座_严格九块_116毫米居中长槽')
LEGACY = PROJECT/'print-stage-500mm-20261113/scripts/build_slim.py'
code = LEGACY.read_text(encoding='utf-8').split('CY=15')[0]
code = code.replace("for p in (A,A/'assembly',O):p.mkdir(parents=True,exist_ok=True)", '')
env = {'__file__': str(LEGACY), '__name__': 'geometry_read_only'}
exec(compile(code, str(LEGACY), 'exec'), env)
mf, M, C, OP = [env[k] for k in ['mf','M','C','OP']]
cube, cyl, union, tm, parts = [env[k] for k in ['cube','cyl','union','tm','parts']]
checks = []
def empty(name, solid, tolerance=.005):
    v = abs(solid.volume())
    assert v < tolerance, (name, v)
    checks.append({'check':name, 'volume_mm3':v, 'pass':True})

# Same assembly coordinates as the nine-piece original: bottom -6, top +8.
# The 104 mm underside relief preserves the original central plate thickness.
base = cyl(250,14,z=-6,n=1536) - cyl(52,5.2,z=-6.2,n=768)
slab = cube((-250,-250,5),(250,250,8.001))
profiles = [C((m^slab).project().to_polygons(),mf.FillRule.Positive)
            for name,m in parts.items() if '_附件' not in name]
socket = C.batch_boolean([p.offset(.25) for p in profiles],OP.Add)
entry = C.batch_boolean([p.offset(.55) for p in profiles],OP.Add)
socket_cut = socket.extrude(3.2).translate((0,0,5))
entry_cut = entry.extrude(.65).translate((0,0,7.4))
base = base - socket_cut - entry_cut
holes = []
for radius in (180,134):
    for i in range(8):
        for off in (-10,10):
            a = math.radians(i*45+22.5+off)
            holes.append(cyl(1.7,2.3,radius*math.cos(a),radius*math.sin(a),2.8))
base = base-union(holes)
# Preserve the original 1..8 index dimples for locating W/S modules.
for i in range(8):
    for k in range(i+1):
        a=math.radians(i*45+22.5+(k-i/2)*.75)
        base=base-cyl(.9,.8,238*math.cos(a),238*math.sin(a),7.3,n=24)
upper = cube((-40,-7,5),(40,7,8.2))
lower = cube((-34,-3.5,-6.2),(34,3.5,5.2))
base = base-upper-lower
assert len(base.decompose())==1
for name,cut in [('建筑钢架槽',socket_cut),('槽口导入',entry_cut),('中央80x14槽',upper),('中央68x7通槽',lower)]:
    empty(name+'保持畅通',base^cut)
for i,h in enumerate(holes): empty(f'定位盲孔{i+1:02d}保持畅通',base^h)
for name,m in parts.items(): empty('原建筑钢架无穿插_'+name,base^m)
foot = cube((-39.75,-6.75,5.2),(39.75,6.75,8))+cube((-33.75,-3.25,-6),(33.75,3.25,5.3))
for lift in (0,.25,1,3,6,10,15):empty('原设计门底脚上拔_'+str(lift),base^foot.translate((0,0,lift)))
sources=[]
originals=[]
for p in sorted(SOURCE.glob('0*.npz')):
    d=np.load(p);old=M(mf.Mesh64(d['vertices'],d['faces'].astype('uint64')))
    originals.append(old)
    # Source NPZ was simplified at 0.002 mm; compare its numerical slivers
    # separately from functional socket/collision tests (which remain 0.005 mm3).
    residual=abs((old-base).volume())
    assert residual < 1 and residual/old.volume() < 1e-5,(p.stem,residual)
    checks.append({'check':'原零件与重建实体差异_'+p.stem,'residual_mm3':residual,'relative_volume':residual/old.volume(),'source_simplification_mm':.002,'pass':True})
    sources.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert len(originals)==9
old_all=union(originals)
mesh=tm(base.simplify(.0001))
assert mesh.is_watertight and mesh.is_winding_consistent
assert np.allclose(mesh.extents,[500,500,14],atol=1e-6)
np.savez_compressed(OUT/'一体底座_原装配坐标.npz',vertices=mesh.vertices,faces=mesh.faces)
printing=mesh.copy();printing.apply_translation([0,0,6])
stl=OUT/'一体底座_500毫米_保留居中长槽.stl'
printing.export(stl,file_type='stl_ascii')
reload=trimesh.load_mesh(stl)
assert reload.is_watertight and reload.is_winding_consistent and len(reload.split())==1
assert np.allclose(reload.extents,[500,500,14],atol=.0001)
# Standard model 3MF with explicit millimetres; no printer-specific G-code.
vertices=''.join(f'<vertex x="{x:.9f}" y="{y:.9f}" z="{z:.9f}"/>' for x,y,z in printing.vertices)
triangles=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in printing.faces)
xml=f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model" name="One-piece base 500mm"><mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object></resources><build><item objectid="1"/></build></model>'
with zipfile.ZipFile(OUT/'一体底座_500毫米_模型.3mf','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model',xml)
report={'result':'PASS','dimensions_mm':reload.extents.tolist(),'components':1,'watertight':bool(reload.is_watertight),'winding_consistent':bool(reload.is_winding_consistent),'volume_mm3':float(reload.volume),'source':str(SOURCE),'source_parts':sources,'added_volume_mm3':float((base-old_all).volume()),'central_upper_slot_mm':[80,14,3],'central_lower_slot_xy_mm':[68,7],'underside_relief_diameter_depth_mm':[104,5],'slice_tested':False,'physical_print_tested':False,'changes':['8外围块和中心盘合为1个封闭实体','填满外围接缝、燕尾配合间隙、中央环形间隙','取消外围M3和中心M2拼接孔及螺母槽、中心拆卸缺口','保留建筑钢架凹槽、32定位盲孔、编号点坑、居中双层长槽和中心底面避空'],'checks':checks,'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()}
(OUT/'几何核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'result':'PASS','size':report['dimensions_mm'],'solids':1,'checks':len(checks),'triangles':len(reload.faces)},ensure_ascii=False))
