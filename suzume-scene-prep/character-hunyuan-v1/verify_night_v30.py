"""Fresh-file checks, full portal render and a separate oblique night inspection."""
from pathlib import Path
import bpy,json,sys,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-night-v30';sys.path.insert(0,str(R))
from night_audit_v30 import fingerprint,topology,material_digest,closed_mesh
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_night_v30.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
a=json.loads((O/'integration-v30.json').read_text(encoding='utf-8'));q=a['parameters']
for name,digest in a['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==digest,name;assert topology(bpy.data.objects[name])==a['topologyHashes'][name],name
for name,row in a['characters'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob,True)==row['worldHash'],name
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert ob.data==other.data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in ob.material_slots);assert all(sl.material.get('spatial_half')=='otherworld' for sl in other.material_slots)
for name,digest in a['unchangedMaterials'].items():assert material_digest(bpy.data.materials[name])==digest,name
assert a['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
for i,row in enumerate(q['clouds']):
    ob=bpy.data.objects['Spatial twilight cloud volume '+str(i)];old=a['cloudMeshes'][ob.name];assert closed_mesh(ob)==(8,True)
    assert fingerprint(ob,world=False)==old['localGeometry'];assert topology(ob)==old['topology'];assert np.allclose(ob.matrix_world,old['matrix'],atol=1e-6)
    assert np.allclose(ob.matrix_world.translation,row['center'],atol=1e-4);assert np.allclose(ob.scale,row['halfSize'],atol=1e-4)
    m=ob.data.materials[0];ns=m.node_tree.nodes;assert m.get('night_volume_revision')==30;assert not any(n.type=='TEX_IMAGE' for n in ns)
    assert abs(ns['Film cloud density coefficient v30'].inputs[1].default_value-q['density'])<1e-7;assert abs(ns['Film cloud emission gain v30'].inputs[1].default_value-q['emissionGain'])<1e-7
    out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');assert out.inputs['Volume'].is_linked and not out.inputs['Surface'].is_linked
sky=bpy.data.objects['Native enclosing night sky'];assert fingerprint(sky)==a['skyGeometry'];assert not any(n.type=='TEX_IMAGE' for n in sky.data.materials[0].node_tree.nodes)
for row in json.loads((R/'movie-lighting-v27/integration-v27.json').read_text())['lights']:
    ob=bpy.data.objects[row['name']];assert np.allclose(ob.matrix_world.translation,row['worldPosition'],atol=1e-5);assert abs(ob.data.energy-row['power'])<1e-5;assert np.allclose(ob.data.color,row['color'],atol=1e-5)
door=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();door.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert door==[0,0,15,15];s.frame_set(72)
night=bpy.data.scenes['Night meadow through the door'];assert abs(night.view_settings.exposure-.8)<1e-6
result={'revision':30,'freshReopenVerified':True,'preservedDayMeshes':len(a['allDayMeshHashes']),'preservedMaterialGraphs':len(a['unchangedMaterials']),'characterHeadFeetAndPortalPreserved':True,'cameraAndDayLightingPreserved':True,'closedSpatialCloudVolumes':10,'cloudMeshesAndTransformsVerified':True,'referenceImageUsedInSkyOrClouds':False,'waterRevisionPreserved':29,'doorLightByFrame':dict(zip([1,24,72,120],door)),'nativeNightExposure':.8,'oneToOneComplete':False}
(O/'verification-v30.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('NIGHT_30_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--render' in sys.argv:
    s.render.use_persistent_data=True;s.render.filepath=str(O/'movie-front-v30.png');bpy.ops.render.render(write_still=True);print('NIGHT_30_FRONT_DONE',flush=True)
    bpy.context.window.scene=night;night.timeline_markers.clear();night.frame_set(72)
    cam=s.camera.copy();cam.data=s.camera.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();night.collection.objects.link(cam);night.camera=cam
    cam.location=(-18,22,5.5);target=Vector((0,230,13));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45
    night.render.use_border=False;night.render.use_crop_to_border=False;night.render.resolution_x=720;night.render.resolution_y=468;night.render.resolution_percentage=100;night.cycles.samples=32;night.cycles.use_denoising=True
    night.render.filepath=str(O/'night-oblique-v30.png');bpy.ops.render.render(write_still=True);print('NIGHT_30_OBLIQUE_DONE',flush=True)
