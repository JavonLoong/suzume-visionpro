from pathlib import Path
import bpy,numpy as np,json
R=Path(__file__).parent;O=R/'poster-steel-v39'
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-v38/Suzume_dual_scene_v38.blend'))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
arrays={};rows=[]
for o in s.objects:
    if o.type!='MESH' or not o.name.startswith('Broken radial dome steelwork solid mesh'):continue
    m=o.data;assert all(len(p.vertices)==3 for p in m.polygons)
    v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());M=np.array(o.matrix_world);w=v@M[:3,:3].T+M[:3,3]
    ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);f=ids.reshape(-1,3)
    key='mesh'+str(len(rows));arrays[key+'_vertices']=w;arrays[key+'_faces']=f
    rows.append({'name':o.name,'key':key,'vertices':len(v),'faces':len(f),'materials':[m.name for m in o.data.materials]})
np.savez_compressed(O/'steel-original-v39.npz',**arrays);(O/'source-steel-v39.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2),flush=True)
