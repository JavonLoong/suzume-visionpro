import bpy,json
from pathlib import Path
R=Path(__file__).parent;O=R/'movie-projection-v24'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_projection_v24.blend'))
col=bpy.data.collections['Editable night realm'];out=[]
for o in col.all_objects:
    if any(s in o.name.lower() for s in ['sky','cloud','meadow','grass','flower']):
        out.append({'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'matrix':[list(r) for r in o.matrix_world],
          'vertices':len(o.data.vertices) if o.type=='MESH' else None,'materials':[{'name':m.name,'nodes':[(n.name,n.type) for n in m.node_tree.nodes] if m.use_nodes else []} for m in o.data.materials] if o.type=='MESH' else []})
(O/'night-inspection-v24.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out),flush=True)
