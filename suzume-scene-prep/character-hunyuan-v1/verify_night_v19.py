"""Verify the saved light fix against the unchanged v17 character and portal."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
R=Path(__file__).parent;O=R/'night-calibration-v19'
names=['Suzume Hunyuan textured surface','Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
def fingerprints():
    s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();result={}
    for name in names:
        o=bpy.data.objects[name];e=o.evaluated_get(deps);mesh=e.to_mesh()
        p=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',p.ravel());M=np.array(o.matrix_world);p=p@M[:3,:3].T+M[:3,3]
        result[name]={'vertices':len(p),'worldHash':hashlib.sha256(np.round(p,6).astype('<f4').tobytes()).hexdigest()}
        e.to_mesh_clear()
    return result
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17.blend'));before=fingerprints()
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'));after=fingerprints();assert before==after
day=bpy.data.scenes['Daytime circular hotel'];night=bpy.data.scenes['Night meadow through the door']
light=bpy.data.objects['Daylight entering the open doorway v19'];realm=bpy.data.collections['Editable night realm']
assert list(light.users_collection)==[realm]
assert bpy.data.objects['Night realm reached through the door'].instance_collection==realm
assert light.name in night.objects
values=[]
for frame in [1,24,72,120]:
    day.frame_set(frame);bpy.context.view_layer.update();values.append(float(light.data.energy))
assert values==[0,0,15,15],values
day.frame_set(72);night.frame_set(72)
for name in names:
    a=bpy.data.objects[name]
    partner='Suzume Hunyuan entered portion' if name==names[0] else name+' — entered portion'
    b=bpy.data.objects[partner];assert a.data==b.data
    assert all(slot.material.get('spatial_half')=='courtyard' for slot in a.material_slots)
    assert all(slot.material.get('spatial_half')=='otherworld' for slot in b.material_slots)
body=bpy.data.objects[names[0]];rig=bpy.data.objects['Suzume Hunyuan rig']
assert len(rig.data.bones)==20
assert body.data.shape_keys.key_blocks['Film lower-body proportions v16'].value==1
audit={'revision':19,'freshReopenVerified':True,'allCharacterWorldVerticesExactlyPreserved':True,
       'characterFingerprints':after,'portalGeometryAndComplementaryMaterialsPreserved':True,
       'newLightConfinedToNightCollection':True,'doorLightPowersByFrame':dict(zip([1,24,72,120],values)),
       'originalRigAndFootCorrectionPreserved':True,'oneToOneComplete':False}
(O/'verification-v19.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('V19_LIGHT_AND_CHARACTER_VERIFIED',json.dumps(audit),flush=True)
