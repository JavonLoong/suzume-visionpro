import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v16.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
mesh=bpy.data.objects['Suzume Hunyuan textured surface'];other=bpy.data.objects['Suzume Hunyuan entered portion'];rig=bpy.data.objects['Suzume Hunyuan rig']
assert mesh.data==other.data and mesh.modifiers[0].object==other.modifiers[0].object==rig
assert mesh.material_slots[0].material!=other.material_slots[0].material
assert mesh.material_slots[0].material['spatial_half']=='courtyard'
assert other.material_slots[0].material['spatial_half']=='otherworld'
assert len(rig.pose.bones)==20 and mesh.data.shape_keys.key_blocks['Film lower-body proportions v16'].value==1
packed=[{'name':im.name,'packed':bool(im.packed_file),'size':list(im.size)} for im in bpy.data.images if im.name.startswith('texture_pbr')]
assert len(packed)==3 and all(p['packed'] and p['size']==[4096,4096] for p in packed)
deps=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(deps);q=np.empty((len(ev.data.vertices),3),np.float32);ev.data.vertices.foreach_get('co',q.ravel())
m=np.array(mesh.matrix_world);w=q@m[:3,:3].T+m[:3,3]
gate=mesh.material_slots[0].material['portal_plane_blender_y'];grip=np.array(rig['Right palm contact world'])
audit={'revision':16,'reopened':True,'editableBones':len(rig.pose.bones),'triangles':len(mesh.data.polygons),'packedTextures':packed,'sharedGeometryAndRig':True,'independentPortalMaterials':True,'minWorldZ':float(w[:,2].min()),'nearestGripSurface':float(np.linalg.norm(w-grip,axis=1).min()),'partition':{'courtyard':int((w[:,1]<=gate).sum()),'otherworld':int((w[:,1]>=gate).sum())},'oneToOneComplete':False}
label='back' if '--back' in sys.argv else 'front'
s.camera=bpy.data.objects['Door front camera']
if label=='back':
 s.camera.location=(-1.2,6,2.3);s.camera.rotation_euler=(Vector((0,0,1.65))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=800;s.render.resolution_y=520;s.render.resolution_percentage=100;s.cycles.samples=20;s.cycles.use_denoising=False
s.render.filepath=str(R/f'native-pose-{label}-v16.png');bpy.ops.render.render(write_still=True)
audit['render']=s.render.filepath
(R/f'verification-{label}-v16.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('V16_NATIVE_VERIFIED',json.dumps(audit),flush=True)
