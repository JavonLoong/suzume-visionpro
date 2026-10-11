import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;H=R/'head-hunyuan-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17_instances.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
rig=bpy.data.objects['Suzume Hunyuan rig'];body=bpy.data.objects['Suzume Hunyuan textured surface'];night_body=bpy.data.objects['Suzume Hunyuan entered portion']
assert body.data==night_body.data
assert len(rig.pose.bones)==20
assert body.data.shape_keys.key_blocks['Film lower-body proportions v16'].value==1
rows=[]
for name in ['Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']:
    a=bpy.data.objects[name];b=bpy.data.objects[name+' — entered portion']
    assert a.data==b.data
    assert all(m.object==rig for o in [a,b] for m in o.modifiers if m.type=='ARMATURE')
    assert all(slot.material.get('spatial_half')=='courtyard' for slot in a.material_slots)
    assert all(slot.material.get('spatial_half')=='otherworld' for slot in b.material_slots)
    a.data.calc_loop_triangles();rows.append({'name':name,'triangles':len(a.data.loop_triangles)})
assert not bpy.data.objects.get('Original head v16 — replacement reference only')
images=[im for im in bpy.data.images if im.name.startswith('texture_pbr')]
assert len(images)==3 and all(im.packed_file for im in images)
cam=bpy.data.objects['Door front camera'];s.camera=cam
cam.location=(-1.2,6,2.3);cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
s.cycles.samples=12;s.cycles.use_denoising=False
s.render.filepath=str(R/'native-pose-back-v17.png');bpy.ops.render.render(write_still=True)
audit={'revision':17,'freshReopenVerified':True,'sharedDayNightGeometryAndRig':True,'complementaryPortalMaterials':True,'preserved20BoneRig':True,'preservedV16ProportionShapeKey':True,'originalPackedBodyTextures':3,'newParts':rows,'backRender':s.render.filepath,'oneToOneComplete':False}
(H/'verification-v17.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('V17_REOPEN_AND_BACK_RENDER_VERIFIED',json.dumps(audit),flush=True)
