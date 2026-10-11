from pathlib import Path
import bpy,json,sys,hashlib,numpy as np
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent;O=R/'movie-hair-v33';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint,topology;from character_export_utils import export_character,CHARACTER_PARTS
f=O/'Suzume_scene_movie_hair_v33.blend';bpy.ops.wm.open_mainfile(filepath=str(f));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);a=json.loads((O/'integration-v33.json').read_text());head=bpy.data.objects[CHARACTER_PARTS[1]];body=bpy.data.objects[CHARACTER_PARTS[0]]
assert fingerprint(head,True)==a['headHash'] and topology(head)==a['topologyHash'];assert fingerprint(body,True)==a['bodyHashPreserved']
for n,h in a['pinsPreserved'].items():assert fingerprint(bpy.data.objects[n],True)==h
for n in CHARACTER_PARTS:
 day=bpy.data.objects[n];night=bpy.data.objects['Suzume Hunyuan entered portion' if n==CHARACTER_PARTS[0] else n+' — entered portion'];assert day.data==night.data
 for ob,half in [(day,'courtyard'),(night,'otherworld')]:assert ob.material_slots[0].material['spatial_half']==half and abs(ob.material_slots[0].material['portal_plane_blender_y']-.072)<1e-6
s.render.resolution_x=2552;s.render.resolution_y=1656
e=head.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();point=head.matrix_world@mesh.vertices[a['tipVertex']].co;q=world_to_camera_view(s,s.camera,point);pixel=np.array([q.x*2552,(1-q.y)*1656]);e.to_mesh_clear();assert np.linalg.norm(pixel-a['tipTargetPixels'])<.01,pixel
parts=export_character(R/'viewer/character-v33',33)
v={'revision':33,'freshReopenVerified':True,'nativeSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'headHash':a['headHash'],'actualTipPixelError':float(np.linalg.norm(pixel-a['tipTargetPixels'])),'bodyFeetGripAndPinsExactlyPreserved':True,'pairedSpatialPartitionVerified':True,'headTopologyPreserved':True,'partTriangles':parts,'minimumBackClothRayGap':a['minimumHairToBackClothGap'],'browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'verification-v33.json').write_text(json.dumps(v,indent=2));print('HAIR_33_REOPEN_EXPORT_OK',json.dumps(v),flush=True)
