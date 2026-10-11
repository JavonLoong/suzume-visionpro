"""Integrate the reviewed spatial cloud model while preserving the rest of the scene."""
from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;O=R/'movie-night-v30';sys.path.insert(0,str(R))
from night_setup_v30 import apply_night
from night_audit_v30 import fingerprint,topology,material_digest,closed_mesh
q=json.loads((O/'night-spec-v30.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-water-v29/Suzume_scene_movie_water_v29.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
base=json.loads((R/'movie-water-v29/integration-v29.json').read_text(encoding='utf-8'))
clouds=[bpy.data.objects['Spatial twilight cloud volume '+str(i)] for i in range(10)];sky=bpy.data.objects['Native enclosing night sky']
changed={o.data.materials[0].name for o in clouds+[sky]}
unchanged={m.name:material_digest(m) for m in bpy.data.materials if m.name not in changed}
cloud_meshes={o.name:{'localGeometry':fingerprint(o,world=False),'topology':topology(o)} for o in clouds}
apply_night(s,q)
for name,digest in base['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==digest,name
for name,row in base['characters'].items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'],name
for name,digest in unchanged.items():assert material_digest(bpy.data.materials[name])==digest,name
assert base['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
for ob in clouds:
    assert fingerprint(ob,world=False)==cloud_meshes[ob.name]['localGeometry'];assert topology(ob)==cloud_meshes[ob.name]['topology'];assert closed_mesh(ob)[1]
    cloud_meshes[ob.name]['matrix']=[list(row) for row in ob.matrix_world];cloud_meshes[ob.name]['uniqueCorners']=closed_mesh(ob)[0]
s['movie_night_revision']=30;s['one_to_one_complete']=False
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True
audit={'revision':30,'parameters':q,'allDayMeshHashes':base['allDayMeshHashes'],'topologyHashes':base['topologyHashes'],'characters':base['characters'],'camera':base['camera'],'unchangedMaterials':unchanged,'cloudMeshes':cloud_meshes,'skyGeometry':fingerprint(sky),'newGeometryCount':0,'nightViewExposure':.8,'dayViewExposure':s.view_settings.exposure,'waterRevisionPreserved':29,'wallSurfaceRevisionPreserved':28,'referenceImageUsedInSkyOrClouds':False,'oneToOneComplete':False}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_night_v30.blend'));(O/'integration-v30.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print('NIGHT_30_SAVED',len(unchanged),flush=True)
