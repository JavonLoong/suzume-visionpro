import bpy,json
from pathlib import Path
from mathutils import Vector
out=Path(__file__).resolve().parents[1]/'analysis'
out.mkdir(parents=True,exist_ok=True)
result={'file':bpy.data.filepath,'scenes':[]}
for s in bpy.data.scenes:
 bpy.context.window.scene=s
 bpy.context.view_layer.update()
 rows=[]
 for ob in s.objects:
  row={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'hidden_render':ob.hide_render,'hidden_viewport':ob.hide_viewport,'collections':[c.name for c in ob.users_collection]}
  if ob.type=='MESH':
   bounds=[ob.matrix_world@Vector(c) for c in ob.bound_box]
   row.update(vertices=len(ob.data.vertices),faces=len(ob.data.polygons),bounds=[[min(p[i] for p in bounds) for i in range(3)],[max(p[i] for p in bounds) for i in range(3)]],mods=[m.type for m in ob.modifiers])
  rows.append(row)
 result['scenes'].append({'name':s.name,'objects':rows})
(out/'source-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'scenes':[{'name':s['name'],'objects':len(s['objects'])} for s in result['scenes']]},ensure_ascii=True),flush=True)
