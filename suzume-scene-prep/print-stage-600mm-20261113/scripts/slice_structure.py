import io,json,sys,zipfile,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];A=R/'analysis';Q=R.parent/'print-white-quality-20261030'
sys.path.insert(0,str(Q/'scripts'));import fast_common
fast_common.R=R
manifest=json.loads((A/'structure_manifest.json').read_text(encoding='utf8'))
# Keep the already built part in sync with the improved flat printing direction.
row=next(x for x in manifest['parts'] if x['id']=='升降吊耳_打印4件')
d=np.load(A/'assembly/升降吊耳_打印4件.npz');m=trimesh.Trimesh(d['vertices'],d['faces'],process=False)
m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]));shift=-m.bounds[0];m.apply_translation(shift)
m.export(row['stl_path'],file_type='stl_ascii');assert trimesh.load(row['stl_path'],force='mesh').is_watertight
row.update(rotation_degrees=[0,90,0],print_translation=shift.tolist(),print_size_mm=m.extents.tolist(),sha256=hashlib.sha256(Path(row['stl_path']).read_bytes()).hexdigest())
np.savez_compressed(A/'升降吊耳_打印4件_print.npz',vertices=m.vertices,faces=m.faces)
(A/'structure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
base=json.loads((Q/'analysis/base_settings.json').read_text(encoding='utf8'))
checks=A/'slice_projects';checks.mkdir(exist_ok=True)
items=manifest['parts']+[{'id':'试配盘','stl_path':str(R/'STL/试配/试配.stl'),'group':'试配','quantity':1}]
if (A/'packed_manifest.json').exists():items+=json.loads((A/'packed_manifest.json').read_text(encoding='utf8'))

def prepare(i,row):
    m=trimesh.load(row['stl_path'],force='mesh');assert m.is_watertight and m.is_winding_consistent
    if row['id']!='试配盘' and not row.get('packed'):
        m.apply_translation([128-m.bounds[:,0].mean(),128-m.bounds[:,1].mean(),-m.bounds[0,2]])
    height=.28 if row['group']=='底座结构' or row.get('settings_kind')=='base' else .20
    if row['id']=='门轴_打印1件':height=.16
    settings=fast_common.settings(base,height,'small')
    settings.update({'enable_support':'0','wall_loops':'3','sparse_infill_density':'12%',
                     'sparse_infill_pattern':'gyroid','brim_width':'3','brim_object_gap':'.15',
                     'top_shell_layers':'3','bottom_shell_layers':'3','top_shell_thickness':'.84',
                     'bottom_shell_thickness':'.84','ironing_type':'no ironing'})
    if row['id'].startswith('底板'):settings['sparse_infill_density']='10%'
    if row['id'] in ['门轴_打印1件','舵盘接头','门轴承托垫圈','侧向垫圈_打印4件']:
        settings.update(wall_loops='4',sparse_infill_density='100%',sparse_infill_pattern='concentric')
    if row.get('settings_kind')=='drive':settings.update(wall_loops='4',sparse_infill_density='100%',sparse_infill_pattern='concentric')
    if row['id']=='试配盘':settings.update(brim_type='no_brim',brim_width='0')
    xml=io.StringIO();xml.write('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Application">BambuStudio-02.01.01.52</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><resources><object id="1" type="model"><mesh><vertices>')
    for p in m.vertices:xml.write('<vertex x="%.17g" y="%.17g" z="%.17g"/>'%tuple(p))
    xml.write('</vertices><triangles>')
    for f in m.faces:xml.write('<triangle v1="%d" v2="%d" v3="%d"/>'%tuple(f))
    xml.write('</triangles></mesh></object><object id="2" type="model"><components><component objectid="1"/></components></object></resources><build><item objectid="2" printable="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></build></model>')
    config=f'''<?xml version="1.0" encoding="UTF-8"?><config><object id="2"><metadata key="name" value="Check{i:02d}"/><metadata key="extruder" value="1"/><part id="1" subtype="normal_part"><metadata key="name" value="Check{i:02d}"/><metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/></part></object><plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Check{i:02d}"/><metadata key="locked" value="false"/><model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="0"/><metadata key="identify_id" value="2"/></model_instance></plate><assemble><assemble_item object_id="2" instance_id="0" transform="1 0 0 0 1 0 0 0 1 0 0 0" offset="0 0 0"/></assemble></config>'''
    src=checks/f'Check{i:02d}.3mf'
    unchanged=False
    if src.exists():
        with zipfile.ZipFile(src) as old:
            unchanged=(old.read('3D/3dmodel.model').decode()==xml.getvalue() and json.loads(old.read('Metadata/project_settings.config'))==settings)
    with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model',xml.getvalue());z.writestr('Metadata/model_settings.config',config)
        z.writestr('Metadata/project_settings.config',json.dumps(settings))
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/octet-stream"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    return src,row,height,unchanged

def run(task):
    src,row,height,unchanged=task;dst=checks/(src.stem+'.gcode.3mf')
    cached=A/(dst.stem+'_result.json')
    result=json.loads(cached.read_text(encoding='utf8')) if unchanged and cached.exists() and dst.exists() else {}
    if result.get('exit_code')!=0:result=fast_common.slice_one(src,dst)
    assert result['exit_code']==0 and result.get('outside')=='false' and result.get('gcode_files'),result
    with zipfile.ZipFile(dst) as z:
        g=z.read(result['gcode_files'][0]);md=z.read(result['gcode_files'][0]+'.md5').decode().strip().lower()
        assert hashlib.md5(g).hexdigest()==md
    result.update(id=row['id'],group=row['group'],quantity=row['quantity'],layer_height_mm=height,stl_sha256=hashlib.sha256(Path(row['stl_path']).read_bytes()).hexdigest(),md5_valid=True)
    return result
tasks=[prepare(i,row) for i,row in enumerate(items,1)]
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,tasks))
(A/'slicing_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('ALL_STRUCTURE_PARTS_SLICED',len(results),flush=True)
