from pathlib import Path
import bpy, json, hashlib
from mathutils import Vector
R=Path(__file__).parent
O=R/'poster-v38';O.mkdir(exist_ok=True)
source=R/'movie-collar-v37/Suzume_scene_movie_collar_v37.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
cameras=[]
for obj in bpy.data.objects:
    if obj.type=='CAMERA':
        cameras.append({'name':obj.name,'location':list(obj.matrix_world.translation),'rotation':list(obj.rotation_euler),'lens':obj.data.lens,'sensorFit':obj.data.sensor_fit,'sensorWidth':obj.data.sensor_width,'sensorHeight':obj.data.sensor_height,'shift':[obj.data.shift_x,obj.data.shift_y]})
meshes=[]
for obj in s.objects:
    if obj.type!='MESH' or obj.hide_render: continue
    if not any(k in obj.name.lower() for k in ['door','frame','steel','hotel','water','sky','cloud']):continue
    pts=[obj.matrix_world@Vector(v) for v in obj.bound_box]
    meshes.append({'name':obj.name,'vertices':len(obj.data.vertices),'parent':obj.parent.name if obj.parent else None,'bounds':[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)],'materials':[m.name if m else None for m in obj.data.materials]})
out={'source':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scenes':[x.name for x in bpy.data.scenes],'activeCamera':s.camera.name,'cameras':cameras,'meshes':meshes}
(O/'inspection-v38.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:out[k] for k in ['scenes','activeCamera','cameras']},indent=2),flush=True)
