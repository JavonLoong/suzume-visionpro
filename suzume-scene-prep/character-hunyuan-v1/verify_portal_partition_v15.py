import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v15.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
day_mesh=bpy.data.objects['Suzume Hunyuan textured surface'];night_mesh=bpy.data.objects['Suzume Hunyuan entered portion']
assert day_mesh.data==night_mesh.data
assert day_mesh.material_slots[0].material['spatial_half']=='courtyard'
assert night_mesh.material_slots[0].material['spatial_half']=='otherworld'
assert day_mesh.material_slots[0].material!=night_mesh.material_slots[0].material
gate=float(day_mesh.material_slots[0].material['portal_plane_blender_y'])
deps=bpy.context.evaluated_depsgraph_get();evaluated=day_mesh.evaluated_get(deps);P=np.empty((len(evaluated.data.vertices),3),np.float32);evaluated.data.vertices.foreach_get('co',P.ravel());M=np.array(day_mesh.matrix_world);world=P@M[:3,:3].T+M[:3,3]
split={'courtyardVertices':int((world[:,1]<=gate).sum()),'otherworldVertices':int((world[:,1]>=gate).sum()),'totalVertices':len(P),'gateY':gate}
assert split['courtyardVertices']>0 and split['otherworldVertices']>0
label='back' if '--back' in sys.argv else 'front'
s.camera=bpy.data.objects['Door front camera']
if label=='back':
 s.camera.location=(-1.2,6,2.3);s.camera.rotation_euler=(Vector((0,0,1.65))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=640;s.render.resolution_y=416;s.render.resolution_percentage=100;s.cycles.samples=12;s.cycles.use_denoising=False
s.render.filepath=str(R/f'native-partition-{label}-v15.png');bpy.ops.render.render(write_still=True)
(R/f'partition-check-{label}-v15.json').write_text(json.dumps({'reopened':True,'partition':split,'render':s.render.filepath,'samples':12,'denoising':False},indent=2),encoding='utf-8')
print('PARTITION_NATIVE_VERIFIED',label,json.dumps(split),flush=True)
