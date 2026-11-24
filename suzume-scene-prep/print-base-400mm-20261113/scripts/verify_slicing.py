import io, json, sys, zipfile
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'analysis'
Q = ROOT.parent / 'print-white-quality-20261030'
sys.path.insert(0, str(Q / 'scripts'))
import fast_common
fast_common.R = ROOT
q = np.load(A / 'print_plate.npz')
settings = fast_common.settings(json.loads((Q / 'analysis/base_settings.json').read_text(encoding='utf8')), .28)
settings.update({'enable_support': '0', 'wall_loops': '3', 'sparse_infill_density': '10%',
                 'sparse_infill_pattern': 'gyroid', 'brim_width': '5', 'brim_object_gap': '.1',
                 'top_shell_layers': '3', 'bottom_shell_layers': '3',
                 'top_shell_thickness': '.84', 'bottom_shell_thickness': '.84',
                 'ironing_type': 'no ironing', 'top_surface_pattern': 'monotonic'})
xml = io.StringIO()
xml.write('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Application">BambuStudio-02.01.01.52</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><resources><object id="1" type="model"><mesh><vertices>')
for p in q['vertices']:
    xml.write('<vertex x="%.17g" y="%.17g" z="%.17g"/>' % tuple(p))
xml.write('</vertices><triangles>')
for f in q['faces']:
    xml.write('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f))
xml.write('</triangles></mesh></object><object id="2" type="model"><components><component objectid="1"/></components></object></resources><build><item objectid="2" printable="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></build></model>')
config = f'''<?xml version="1.0" encoding="UTF-8"?><config><object id="2"><metadata key="name" value="Base400-quarter"/><metadata key="extruder" value="1"/><part id="1" subtype="normal_part"><metadata key="name" value="Base400-quarter"/><metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><mesh_stat face_count="{len(q['faces'])}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/></part></object><plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Base400-quarter"/><metadata key="printer_model_id" value="BL-P001"/><metadata key="locked" value="false"/><model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="0"/><metadata key="identify_id" value="2"/></model_instance></plate><assemble><assemble_item object_id="2" instance_id="0" transform="1 0 0 0 1 0 0 0 1 0 0 0" offset="0 0 0"/></assemble></config>'''
src = A / 'Base400.3mf'
with zipfile.ZipFile(src, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('3D/3dmodel.model', xml.getvalue())
    z.writestr('Metadata/model_settings.config', config)
    z.writestr('Metadata/project_settings.config', json.dumps(settings))
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/octet-stream"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
result = fast_common.slice_one(src, A / 'Base400.gcode.3mf')
assert result['exit_code'] == 0 and result.get('outside') == 'false' and result.get('gcode_files'), result
result.update(total_plates=4, total_seconds=result['seconds'] * 4, total_grams=round(result['grams'] * 4, 2), actual_print_test=False)
(A / 'slicing_check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
print('BASE_SLICING_PASS', result['total_seconds'], result['total_grams'], flush=True)
