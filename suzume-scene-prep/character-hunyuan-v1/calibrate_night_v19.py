"""Restore daylight arriving through the door into the otherwise dark realm.

The localized area emitter is a controllable approximation of the courtyard
illumination lost by the one-way Ray Portal lighting transport. Geometry,
instance colors and the complementary character cut remain untouched.
"""
import bpy,json,sys,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'night-calibration-v19';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17.blend'))
day=bpy.data.scenes['Daytime circular hotel'];night=bpy.data.scenes['Night meadow through the door']
realm=bpy.data.collections['Editable night realm'];hinge=bpy.data.objects['Animated door leaf and hinges']
power=15.0
if '--power' in sys.argv:power=float(sys.argv[sys.argv.index('--power')+1])
data=bpy.data.lights.new('Daylight entering the open doorway v19','AREA')
data.shape='RECTANGLE';data.size=1.55;data.size_y=3.15;data.color=(1.0,.93,.84);data.energy=power
light=bpy.data.objects.new(data.name,data);realm.objects.link(light)
light.location=(0,-.18,1.78);light.rotation_euler=Vector((0,1,0)).to_track_quat('-Z','Y').to_euler()
driver=data.driver_add('energy').driver;driver.expression=f'{power}*min(max(opening,0),1)'
var=driver.variables.new();var.name='opening';var.type='SINGLE_PROP';var.targets[0].id=hinge;var.targets[0].data_path='["door_open"]'
light['purpose']='Courtyard light admitted by the open door; inside-world emitter compensates for one-way Ray Portal light transport.'
day.frame_set(72);night.frame_set(72);bpy.context.window.scene=day;bpy.context.view_layer.update()
body=bpy.data.objects['Suzume Hunyuan textured surface'];deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
p=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',p.ravel());M=np.array(body.matrix_world);p=p@M[:3,:3].T+M[:3,3];evaluated.to_mesh_clear()
fingerprint=hashlib.sha256(np.round(p,6).astype('<f4').tobytes()).hexdigest()
assert fingerprint=='bda994f4f36c980ac7e48122ea45f395ce5defbd723d5c82f514aeca5561de47'
audit={'revision':19,'change':'Localized doorway illumination in the spatial night realm',
       'powerWatts':power,'emitterDimensions':[1.55,3.15],'position':list(light.location),
       'doorOpenDriver':driver.expression,'bodyWorldVerticesHash':fingerprint,
       'characterAndFeetUnchanged':True,'plantGeometryAndColorsUnchanged':True,'oneToOneComplete':False,
       'technicalReference':'https://docs.blender.org/manual/zh-hans/5.0/render/shader_nodes/shader/ray_portal.html',
       'limits':'Area emitter approximates incident courtyard light. Film lighting and cloud shapes still require visual calibration.'}
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'))
(O/'lighting-v19.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('NIGHT_LIGHT_CALIBRATION_SAVED',json.dumps(audit),flush=True)
if '--night-preview' in sys.argv:
    s=night;bpy.context.window.scene=s;s.frame_set(72)
    cam=s.camera;cam.location=(0,-4,1.75);cam.rotation_euler=(Vector((0,14,2.2))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=30;cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=36
    s.render.resolution_x=480;s.render.resolution_y=320;s.render.resolution_percentage=100
    s.cycles.samples=16;s.cycles.use_denoising=True
    s.render.filepath=str(O/'night-light-candidate.png');bpy.ops.render.render(write_still=True)
if '--portal-preview' in sys.argv:
    s=day;bpy.context.window.scene=s;s.frame_set(72)
    s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
    s.cycles.samples=32;s.cycles.use_denoising=True
    s.render.filepath=str(O/'portal-light-candidate.png');bpy.ops.render.render(write_still=True)
