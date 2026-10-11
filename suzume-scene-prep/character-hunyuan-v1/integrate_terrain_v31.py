"""Add the far terrain and fog to both the editable realm and the transported realm."""
from pathlib import Path
import bpy,json,sys,numpy as np,hashlib
R=Path(__file__).parent;O=R/'movie-terrain-v31';sys.path.insert(0,str(R));from terrain_setup_v31 import apply_terrain
from night_audit_v30 import fingerprint,topology,material_digest,closed_mesh
q=json.loads((O/'terrain-spec-v31.json').read_text(encoding='utf-8'));source=R/'movie-night-v30/Suzume_scene_movie_night_v30.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
baseline=json.loads((R/'movie-night-v30/integration-v30.json').read_text(encoding='utf-8'));original=json.loads((O/'source-inspection-v31.json').read_text(encoding='utf-8'));assert hashlib.sha256(source.read_bytes()).hexdigest()==original['sourceSha256']
before=np.load(O/'original-ground-v31.npz');near=np.hypot(before['world'][:,0],before['world'][:,1])<=q['unchangedNearRadius']
ground,extension,fogs=apply_terrain(q)
for name,row in original['nightMeshFingerprints'].items():
    if name!='Rolling meadow ground':assert fingerprint(bpy.data.objects[name])==row['worldHash'],name
    assert topology(bpy.data.objects[name])==row['topology'],name
local=np.array([v.co[:] for v in ground.data.vertices],np.float32);assert np.array_equal(local[near],before['local'][near]);assert closed_mesh(extension)[1]
for name,digest in baseline['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==digest,name
for name,row in baseline['characters'].items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'],name
for name,digest in original['materials'].items():assert material_digest(bpy.data.materials[name])==digest,name
assert baseline['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
s['movie_terrain_revision']=31;s['one_to_one_complete']=False
audit={'revision':31,'parameters':q,'allDayMeshHashes':baseline['allDayMeshHashes'],'topologyHashes':baseline['topologyHashes'],'characters':baseline['characters'],'camera':baseline['camera'],'oldNightMeshes':original['nightMeshFingerprints'],'oldMaterials':original['materials'],'nearGroundVertexCount':int(near.sum()),'groundWorldHash':fingerprint(ground),'extensionWorldHash':fingerprint(extension),'extensionTopologyHash':topology(extension),'newObjects':[extension.name]+[o.name for o in fogs],'nightRealmCollection':ground.users_collection[0].name,'oldGroundTopologyPreserved':True,'oneToOneComplete':False}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_terrain_v31.blend'));(O/'integration-v31.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print('TERRAIN_31_SAVED',json.dumps({'nearGroundVerticesUnchanged':int(near.sum()),'newObjects':audit['newObjects']}),flush=True)
