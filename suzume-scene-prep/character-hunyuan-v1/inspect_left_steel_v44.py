from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(__file__).parent;O=R/'poster-left-steel-v44';O.mkdir(exist_ok=True);native=R/'poster-lower-clouds-v43/Suzume_dual_scene_lower_clouds_v43.blend'
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();arrays={};rows=[]
for ob in s.objects:
    if ob.type!='MESH' or not ob.name.startswith('Broken radial dome steelwork solid mesh'):continue
    m=ob.data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];ix=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ix);faces=ix.reshape(-1,3);key='mesh'+str(len(rows));arrays[key+'_vertices']=world;arrays[key+'_faces']=faces
    rows.append({'name':ob.name,'key':key,'vertices':len(v),'faces':len(faces),'materials':[m.name for m in ob.data.materials]})
np.savez_compressed(O/'source-steel-v44.npz',**arrays);(O/'source-steel-v44.json').write_text(json.dumps({'sourceNativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'objects':rows},indent=2),encoding='utf-8');print(json.dumps(rows,indent=2),flush=True)
