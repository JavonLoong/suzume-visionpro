import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent;O=R/'movie-calibration-v20'
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
cam=s.camera
rows=[]
for o in s.objects:
    if o.type not in ['MESH','LIGHT','CAMERA']:continue
    if o.type=='MESH' and not any(x in o.name.lower() for x in ['hotel','dome','steel','tree','ivy','flagstone','slab','debris','water','floor']):continue
    pts=[o.matrix_world@Vector(v) for v in o.bound_box] if o.type=='MESH' else []
    rows.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'modifiers':[m.type for m in o.modifiers], 'hide':o.hide_render,'location':list(o.matrix_world.translation),'bounds':[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)] if pts else [],'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []})
out={'camera':{'name':cam.name,'position':list(cam.matrix_world.translation),'rotation':list(cam.rotation_euler),'lens':cam.data.lens,'sensorFit':cam.data.sensor_fit,'sensorHeight':cam.data.sensor_height,'sensorWidth':cam.data.sensor_width,'shiftX':cam.data.shift_x,'shiftY':cam.data.shift_y,'resolution':[s.render.resolution_x,s.render.resolution_y]},'objects':rows}
anchors=json.loads((O/'courtyard-fit-v20.json').read_text())['before']
import math
check=[]
for a in anchors:
    t=a['angle'];r=a['radius'];x=a['localX'];z=a['height'];p=Vector((r*math.sin(t)+x*math.cos(t),r*math.cos(t)-x*math.sin(t),z))
    uv=world_to_camera_view(s,cam,p);check.append({'name':a['name'],'blenderUV':[uv.x*2552,(1-uv.y)*1656],'fitUV':a['projected']})
out['actualProjectionCheck']=check
(O/'scene-inspection.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out),flush=True)
