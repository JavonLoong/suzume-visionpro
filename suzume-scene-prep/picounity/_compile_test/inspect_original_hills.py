import bpy, json, sys
from pathlib import Path
from mathutils import Vector
sys.stdout.reconfigure(encoding='utf-8')
source = Path(r'D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\character-hunyuan-v1\poster-right-bow-v56\Suzume_dual_scene_right_bow_v56.blend')
bpy.ops.wm.open_mainfile(filepath=str(source))
report=[]
for ob in bpy.data.objects:
    if ob.type == 'MESH' and any(s in ob.name.lower() for s in ('hill','mount','ridge','meadow','草原','丘','山')):
        pts=[ob.matrix_world @ Vector(v) for v in ob.bound_box]
        report.append({'name':ob.name,'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'hide':ob.hide_render,'polygons':len(ob.data.polygons)})
out=Path(__file__).with_name('original-hills.json')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
