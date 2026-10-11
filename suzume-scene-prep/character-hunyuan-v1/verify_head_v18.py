"""Fresh-file check of the alternate head and unchanged body/foot geometry."""
import bpy,numpy as np,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;H=R/'head-hunyuan-v1'
def body_fingerprint():
    s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
    body=bpy.data.objects['Suzume Hunyuan textured surface']
    deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
    p=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',p.ravel())
    transform=np.asarray(body.matrix_world);p=p@transform[:3,:3].T+transform[:3,3]
    result={'worldVerticesSha256':hashlib.sha256(np.round(p,6).astype('<f4').tobytes()).hexdigest(),
            'vertices':len(p),'minimumHeight':float(p[:,2].min())}
    evaluated.to_mesh_clear();return result
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17.blend'))
original=body_fingerprint()
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_clean_head_v18.blend'))
current=body_fingerprint();assert original==current,(original,current)
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s
rig=bpy.data.objects['Suzume Hunyuan rig'];body=bpy.data.objects['Suzume Hunyuan textured surface']
assert body.data==bpy.data.objects['Suzume Hunyuan entered portion'].data
assert len(rig.pose.bones)==20
assert body.data.shape_keys.key_blocks['Film lower-body proportions v16'].value==1
a=bpy.data.objects['Suzume clean mathematical head'];b=bpy.data.objects[a.name+' — entered portion']
assert a.data==b.data
assert all(m.object==rig for o in [a,b] for m in o.modifiers if m.type=='ARMATURE')
assert all(slot.material.get('spatial_half')=='courtyard' for slot in a.material_slots)
assert all(slot.material.get('spatial_half')=='otherworld' for slot in b.material_slots)
assert not bpy.data.objects.get('Suzume independent Hunyuan head')
images=[im for im in bpy.data.images if im.name.startswith('texture_pbr')]
assert len(images)==3 and all(im.packed_file for im in images)
gn=[]
for group in bpy.data.node_groups:
    for node in group.nodes:
        if node.bl_idname=='GeometryNodeRealizeInstances':
            gn.append({'group':group.name,'muted':node.mute})
assert len(gn)>=6 and all(row['muted'] for row in gn)
cam=bpy.data.objects['Door front camera'];s.camera=cam
cam.location=(-1.2,6,2.3);cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
s.cycles.samples=12;s.cycles.use_denoising=False
s.render.filepath=str(R/'native-pose-back-v18.png')
if '--no-render' not in sys.argv:bpy.ops.render.render(write_still=True)
audit={'revision':18,'freshReopenVerified':True,'bodyAndFootWorldVerticesExactlyPreserved':True,
       'bodyGeometry':current,'sharedDayNightGeometryAndRig':True,'complementaryPortalMaterials':True,
       'preserved20BoneRig':True,'preservedV16ProportionShapeKey':True,'originalPackedBodyTextures':3,
       'retainedInstancedEnvironment':gn,'backRender':s.render.filepath if '--no-render' not in sys.argv else None,'oneToOneComplete':False}
(H/'verification-v18.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('V18_REOPEN_AND_BACK_RENDER_VERIFIED',json.dumps(audit),flush=True)
