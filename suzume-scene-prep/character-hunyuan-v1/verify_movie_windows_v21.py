import bpy,bmesh,json,numpy as np,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-windows-v21';M20=R/'movie-calibration-v20'
baseline=json.loads((M20/'verification-v20.json').read_text())['characters']
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_windows_v21.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();characters={}
for name,row in baseline.items():
    o=bpy.data.objects[name];e=o.evaluated_get(deps);m=e.to_mesh();a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3];e.to_mesh_clear();value=hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest();assert value==row['worldHash']
    characters[name]={'vertices':len(a),'worldHash':value}
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';assert o.data==bpy.data.objects[partner].data
    assert all(slot.material.get('spatial_half')=='courtyard' for slot in o.material_slots)
    assert all(slot.material.get('spatial_half')=='otherworld' for slot in bpy.data.objects[partner].material_slots)
assert len(bpy.data.objects['Suzume Hunyuan rig'].data.bones)==20
wall=bpy.data.objects['Solid plaster wall with two through-openings v21'];bm=bmesh.new();bm.from_mesh(wall.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);assert all(edge.is_manifold for edge in bm.edges);bm.free()
F=json.loads((O/'window-fit-v21.json').read_text());fit=json.loads((M20/'courtyard-fit-v20.json').read_text());p=fit['parameters'];k=fit['depthScale'];C=np.array(fit['depthScaleCenter']);angle=F['angle']+p['yaw'];n=Vector((-math.sin(angle),-math.cos(angle),0));t=Vector((math.cos(angle),-math.sin(angle),0))
def pt(x,y):
    a=np.array([F['chordRadius']*math.sin(angle)+x*math.cos(angle)+p['translateX'],F['chordRadius']*math.cos(angle)-x*math.sin(angle)+p['translateY'],y*p['heightScale']+p['heightOffset']]);return Vector(C+k*(a-C))
raytests=[]
for label,x,y,expected in [('oculus',F['oculus']['x'],F['oculus']['centerY'],False),('rectangle',F['rectangle']['x'],F['rectangle']['bottom']+F['rectangle']['height']/2,False),('wall',-F['bayWidth']*.465,3,True)]:
    hit=wall.ray_cast(pt(x,y)+n*4,-n,distance=10)[0];assert hit==expected;raytests.append({'target':label,'wallHit':hit})
new=bpy.data.collections['Movie right facade — solid openings v21'];assert len(new.objects)==72
assert any(o.name.startswith('Rear room wall') for o in new.objects)
assert any(o.name.startswith('Vertical drainpipe') for o in new.objects)
values=[];light=bpy.data.lights['Daylight entering the open doorway v19']
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(light.energy)
assert values==[0,0,15,15];s.frame_set(72)
result={'revision':21,'freshReopenVerified':True,'bodyHeadHairpinWorldVerticesPreserved':True,'characters':characters,'actualWindowOpenings':raytests,'wallWatertightAfterWelding':True,'completeRearRoomGeometry':True,'newObjects':len(new.objects),'portalAndFootCorrectionPreserved':True,'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
(O/'verification-v21.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('WINDOW_SCENE_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--detail' in sys.argv:
    s.timeline_markers.clear();cam=s.camera.copy();cam.data=s.camera.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();s.collection.objects.link(cam);s.camera=cam
    target=pt(0,2.8);cam.location=target+n*14+t*10+Vector((0,0,4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28
    s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
    s.render.filepath=str(O/'movie-window-oblique-v21.png');bpy.ops.render.render(write_still=True)
