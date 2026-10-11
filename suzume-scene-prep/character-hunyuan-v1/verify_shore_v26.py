"""Reopen native files, inspect hollow bores, and preserve character/portal invariants."""
from pathlib import Path
import bpy,bmesh,json,sys,hashlib,math,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-shore-v26';sys.path.insert(0,str(R))
from projection_geometry_v24 import bay_spec,height,center
def appearance(s):
    return {'cameraMatrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens,'lights':{o.name:{'matrix':[list(row) for row in o.matrix_world],'power':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'sizeY':getattr(o.data,'size_y',None)}for o in s.objects if o.type=='LIGHT'}}
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-steel-v25/Suzume_scene_movie_steel_v25.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update();baselineAppearance=appearance(s)
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_shore_v26.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update();assert appearance(s)==baselineAppearance
audit=json.loads((O/'integration-v26.json').read_text(encoding='utf-8'));fit=json.loads((O/'shore-fit-v26.json').read_text(encoding='utf-8'))
def coordinates(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o;mesh=e.to_mesh() if evaluated else o.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return a
def fingerprint(o,evaluated=False):return hashlib.sha256(np.round(coordinates(o,evaluated),6).astype('<f4').tobytes()).hexdigest()
for name,value in audit['unchangedMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==value,name
for name,row in audit['characters'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob,True)==row['worldHash'],name
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert ob.data==other.data
    assert all(slot.material.get('spatial_half')=='courtyard' for slot in ob.material_slots);assert all(slot.material.get('spatial_half')=='otherworld' for slot in other.material_slots)
parts=list(bpy.data.collections['Movie waterfront v26 — sloped solid slabs and hollow pipes'].objects);assert len(parts)==audit['newParts'];hashes={}
for ob in parts:
    a=coordinates(ob).astype('<f4');assert np.isfinite(a).all()
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);assert all(e.is_manifold for e in bm.edges),ob.name;assert bm.calc_volume(signed=True)>0,ob.name;bm.free()
    hashes[ob.name]={'vertices':len(a),'nativeFloat32Hash':hashlib.sha256(a.tobytes()).hexdigest()}
checks=[]
for q in fit['observedPipes']:
    ob=bpy.data.objects[q['name']+' v26'];p=[Vector(v)for v in q['pointsNative']]
    for side in [0,-1]:
        end=p[side];out=(p[0]-p[1]).normalized() if side==0 else (p[-1]-p[-2]).normalized();normal=out.cross(Vector((0,0,1)))
        if normal.length<.01:normal=out.cross(Vector((1,0,0)))
        normal.normalize();bore=ob.ray_cast(end+out*.05,-out,distance=.1)[0];rim=ob.ray_cast(end+out*.05+normal*(q['radius']-q['wall']/2),-out,distance=.1)[0]
        assert not bore and rim,(q['name'],side,bore,rim);checks.append({'pipe':q['name'],'end':side,'axisOpen':not bore,'wallHit':rim})
values=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert values==[0,0,15,15];s.frame_set(72)
result={'revision':26,'freshReopenVerified':True,'allNewMeshesClosed':len(parts),'allPreviousMeshesUnchanged':len(audit['unchangedMeshHashes']),'cameraAndLightsUnchanged':True,'charactersFeetAndPortalPreserved':True,'pipeBoreRayChecks':checks,'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
(O/'verification-v26.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(O/'native-shore-meshes-v26.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8');print('SHORE_26_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--oblique' in sys.argv:
    b=bay_spec(13);a=b['angle'];n=Vector((-math.sin(a),-math.cos(a),0));t=Vector((math.cos(a),-math.sin(a),0));target=Vector((b['chordRadius']*math.sin(a)+center[0],b['chordRadius']*math.cos(a)+center[1],float(height(3.5,13))))
    s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
    camera.location=target+n*12+t*8+Vector((0,0,5));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
    s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'movie-left-oblique-v26.png');bpy.ops.render.render(write_still=True)
