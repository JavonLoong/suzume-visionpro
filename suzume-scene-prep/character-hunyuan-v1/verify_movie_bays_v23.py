"""Fresh-reopen checks and an oblique view of the rebuilt complete rooms."""
from pathlib import Path
import bpy,bmesh,json,math,numpy as np,hashlib,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-bays-v23'
def fingerprint(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o
    mesh=e.to_mesh() if evaluated else e.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return {'vertices':len(a),'worldHash':hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()}
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-material-v22/Suzume_scene_movie_material_v22.blend'))
right={o.name:fingerprint(o) for o in bpy.data.collections['Movie right facade — solid openings v21'].objects}
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_bays_v23.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
for name,row in right.items():assert fingerprint(bpy.data.objects[name])==row
baseline=json.loads((R/'movie-material-v22/verification-v22.json').read_text(encoding='utf-8'))['characters'];characters={}
for name,row in baseline.items():
    o=bpy.data.objects[name];characters[name]=fingerprint(o,True);assert characters[name]==row
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion'
    assert o.data==bpy.data.objects[partner].data
    assert all(slot.material.get('spatial_half')=='courtyard' for slot in o.material_slots)
    assert all(slot.material.get('spatial_half')=='otherworld' for slot in bpy.data.objects[partner].material_slots)
assert len(bpy.data.objects['Suzume Hunyuan rig'].data.bones)==20
F=json.loads((O/'bay-fit-v23.json').read_text(encoding='utf-8'))
placement=json.loads((R/'movie-calibration-v20/courtyard-fit-v20.json').read_text(encoding='utf-8'));p=placement['parameters'];k=placement['depthScale'];C=np.array(placement['depthScaleCenter'])
def point(b,x,y,z=0):
    a=b['angle']+p['yaw'];r=b['chordRadius']-z
    q=np.array([r*math.sin(a)+x*math.cos(a)+p['translateX'],r*math.cos(a)-x*math.sin(a)+p['translateY'],y*p['heightScale']+p['heightOffset']])
    return Vector(C+k*(q-C))
checks=[];gaps=[];lower_geometry={}
for b in F['bays']:
    wall=bpy.data.objects[f"Bay {b['index']} Lower story wall v23"]
    n=Vector((-math.sin(b['angle']+p['yaw']),-math.cos(b['angle']+p['yaw']),0))
    for q in b['openings']:
        center=point(b,q['x'],q['bottom']+q['height']*.4)
        assert not wall.ray_cast(center+n*4,-n,distance=10)[0]
        checks.append({'bay':b['index'],'opening':q['name'],'wallHit':False})
    rects=[q for q in b['openings'] if q['type']=='rectangle']
    if len(rects)==2:
        x=(rects[0]['x']+rects[0]['width']/2+rects[1]['x']-rects[1]['width']/2)/2
        y=max(q['bottom'] for q in rects)+.7;center=point(b,x,y)
        assert wall.ray_cast(center+n*4,-n,distance=10)[0]
        gaps.append({'bay':b['index'],'solidWallBetweenWindows':True})
    bm=bmesh.new();bm.from_mesh(wall.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);assert all(e.is_manifold for e in bm.edges);bm.free()
    lower_geometry[str(b['index'])]=[list(wall.matrix_world@v.co) for v in wall.data.vertices]
group=bpy.data.collections['Movie left and central bays — solid windows v23']
counts={int(c.name.split()[2]):len(c.objects) for c in group.children};assert sum(counts.values())==669
values=[];light=bpy.data.lights['Daylight entering the open doorway v19']
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(light.energy)
assert values==[0,0,15,15];s.frame_set(72)
lighting=json.loads((O/'lighting-v23.json').read_text(encoding='utf-8'));light_checks=[]
for spec in lighting['lights']:
    o=bpy.data.objects[spec['name']];assert abs(o.data.energy-spec['powerWatts'])<.01
    assert np.max(np.abs(np.array(o.location)-spec['position']))<1e-5
    forward=o.rotation_euler.to_quaternion()@Vector((0,0,-1))
    for name in baseline:
        character=bpy.data.objects[name]
        assert max((character.matrix_world@Vector(corner)-o.location).dot(forward) for corner in character.bound_box)<0
    light_checks.append({'name':o.name,'powerWatts':o.data.energy,'foregroundBehindEmitter':True})
result={'revision':23,'freshReopenVerified':True,'characters':characters,'bodyHeadFootAndPortalPreserved':True,'rightBayV22GeometryPreserved':True,'rightBayObjects':len(right),'newPartsByBay':counts,'openings':checks,'solidWindowSeparators':gaps,'fourWallsWatertight':True,'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
result['facadeLights']=light_checks
(O/'verification-v23.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(O/'native-lower-walls-v23.json').write_text(json.dumps(lower_geometry),encoding='utf-8')
print('MOVIE_BAYS_23_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--front' in sys.argv:
    s.render.use_border=False;s.render.use_persistent_data=True;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
    s.render.filepath=str(O/'movie-front-v23.png');bpy.ops.render.render(write_still=True)
if '--oblique' in sys.argv:
    b=next(b for b in F['bays'] if b['index']==13);a=b['angle']+p['yaw'];n=Vector((-math.sin(a),-math.cos(a),0));t=Vector((math.cos(a),-math.sin(a),0))
    s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
    target=point(b,0,3.5);camera.location=target+n*23+t*16+Vector((0,0,8));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
    s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
    s.render.filepath=str(O/'movie-left-oblique-v23.png');bpy.ops.render.render(write_still=True)
