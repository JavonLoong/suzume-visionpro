from pathlib import Path
import sys,json,hashlib,zipfile,xml.etree.ElementTree as ET
import numpy as np
import trimesh

OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'一体底座_500毫米_20261120'
sys.path.insert(0,str(OUT.parent/'print-400mm-20261030/.deps'))
import manifold3d as mf
d=np.load(SRC/'一体底座_原装配坐标.npz')
original=mf.Manifold(mf.Mesh64(d['vertices'],d['faces'].astype('uint64')))
# Original assembly: bottom Z=-6, seat Z=-1, top Z=8.
# Remove the centre disk and its nominal radial clearance, retaining the ledge.
cut=mf.Manifold.cylinder(9.2,58.25,circular_segments=768).translate((0,0,-1))
ring=original-cut
assert len(ring.decompose())==1
assert abs((ring-original).volume())<.005
assert abs((ring^cut).volume())<.005
assert abs((original-ring-cut).volume())<.005
q=ring.simplify(.0001).to_mesh64()
mesh=trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=False)
assert mesh.is_watertight and mesh.is_winding_consistent
assert np.allclose(mesh.extents,[500,500,14])
np.savez_compressed(OUT/'无中心盘底座_原装配坐标.npz',vertices=mesh.vertices,faces=mesh.faces)
printing=mesh.copy();printing.apply_translation([0,0,6])
stl=OUT/'一体底座_去中心盘_500毫米.stl';printing.export(stl,file_type='stl_ascii')
loaded=trimesh.load_mesh(stl)
assert loaded.is_watertight and loaded.is_winding_consistent and len(loaded.split())==1
assert np.allclose(loaded.extents,[500,500,14])
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
with zipfile.ZipFile(SRC/'一体底座_500毫米_模型.3mf') as z:
    root=ET.fromstring(z.read('3D/3dmodel.model'))
    obj=root.find(f'{{{ns}}}resources/{{{ns}}}object');obj.set('name','One-piece ring base 500mm')
    old=obj.find(f'{{{ns}}}mesh');obj.remove(old)
    new=ET.SubElement(obj,f'{{{ns}}}mesh');verts=ET.SubElement(new,f'{{{ns}}}vertices');faces=ET.SubElement(new,f'{{{ns}}}triangles')
    for x,y,h in printing.vertices:ET.SubElement(verts,f'{{{ns}}}vertex',x=f'{x:.9f}',y=f'{y:.9f}',z=f'{h:.9f}')
    for a,b,c in printing.faces:ET.SubElement(faces,f'{{{ns}}}triangle',v1=str(a),v2=str(b),v3=str(c))
    with zipfile.ZipFile(OUT/'一体底座_去中心盘_模型.3mf','w',zipfile.ZIP_DEFLATED) as dest:
        for name in z.namelist():dest.writestr(name,ET.tostring(root,encoding='utf-8',xml_declaration=True) if name=='3D/3dmodel.model' else z.read(name))
with zipfile.ZipFile(OUT/'一体底座_去中心盘_模型.3mf') as z:
    assert z.testzip() is None
    r=ET.fromstring(z.read('3D/3dmodel.model'));assert r.attrib['unit']=='millimeter'
    v=np.array([[float(t.attrib[k]) for k in ['x','y','z']] for t in r.iter(f'{{{ns}}}vertex')])
    f=np.array([[int(t.attrib[k]) for k in ['v1','v2','v3']] for t in r.iter(f'{{{ns}}}triangle')])
    model=trimesh.Trimesh(v,f,process=False)
    assert model.is_watertight and model.is_winding_consistent and len(model.split())==1
    assert abs(model.volume-loaded.volume)<.01
report={'result':'PASS','size_mm':loaded.extents.tolist(),'one_closed_solid':True,'upper_opening_diameter_mm':116.5,'upper_opening_depth_mm':9,'lower_through_hole_diameter_mm':104,'ledge_thickness_mm':5,'ledge_radial_width_mm':6.25,'original_preserved':str(SRC),'original_npz_sha256':hashlib.sha256((SRC/'一体底座_原装配坐标.npz').read_bytes()).hexdigest(),'change_only_inside_central_cut':True,'stl_3mf_agree':True,'volume_mm3':float(loaded.volume),'slice_tested':False,'physical_tested':False,'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()}
(OUT/'几何核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'00_说明.txt').write_text('''一体底座·去中心圆盘版

外圈是一体的一个封闭实体，中央圆盘已去掉。
外径500mm，总厚14mm，原建筑与钢架槽、定位盲孔、编号点坑保持不变。
中央上口直径116.5mm、深9mm；下口直径104mm，贯通底面。
保留下方5mm厚、径向宽6.25mm的承托台阶；不是上下等径的直通圆孔。
原中央双层长槽随圆盘一起去除。此版不含中心盘，也没有重新增加中心固定螺丝孔。
完整一体版保留在相邻“一体底座_500毫米_20261120”文件夹。

STL按毫米、100%导入；3MF是含毫米单位的模型文件，不是已切片的打印文件。
STL、3MF重新读取均确认单一封闭实体、500×500×14mm，且两者体积一致。
布尔差集检查确认改动局限于中央切除区域，外围未改尺寸和位置。
未切片、未实体打印。500mm整圆无法放入原X1 Carbon；需匹配大尺寸设备。
底面朝下，中央开口及下方承托台阶均向上敞开；其余槽孔仍需由实际切片检查。
''',encoding='utf-8-sig')
render=(SRC/'生成预览.py').read_text(encoding='utf-8').replace('一体底座_原装配坐标.npz','无中心盘底座_原装配坐标.npz').replace('一体底座_500x500x14毫米','无中心盘一体底座_500x500x14毫米').replace('02_中央双层长槽','02_中央开口与承托台阶').replace('03_底面中央避空','03_底面贯通圆口').replace('一体底座_可编辑.blend','无中心盘一体底座_可编辑.blend')
(OUT/'生成预览.py').write_text(render,encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
