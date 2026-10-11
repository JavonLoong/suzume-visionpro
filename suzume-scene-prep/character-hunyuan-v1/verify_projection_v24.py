"""Fresh-reopen geometry, portal, camera and editable-room checks."""
from pathlib import Path
import bpy,bmesh,json,math,numpy as np,hashlib,sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent;sys.path.insert(0,str(R))
from projection_geometry_v24 import O,P,F,height,bay_spec,center,old_edges,new_edges,map_source
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_projection_v24.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
baseline=json.loads((R/'movie-bays-v23/verification-v23.json').read_text(encoding='utf-8'))['characters'];characters={}
for name,row in baseline.items():
    o=bpy.data.objects[name];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3];e.to_mesh_clear()
    val=hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest();assert val==row['worldHash'];characters[name]={**row,'minWorldZ':float(a[:,2].min())}
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion'
    assert o.data==bpy.data.objects[partner].data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in o.material_slots)
    assert all(sl.material.get('spatial_half')=='otherworld' for sl in bpy.data.objects[partner].material_slots)
assert len(bpy.data.objects['Suzume Hunyuan rig'].data.bones)==20
assert abs(bpy.data.objects['Spatial doorway portal aperture'].matrix_world.translation.y-.071999914944)<1e-6
assert abs(s.camera.data.lens-P['lensMm'])<1e-4
assert np.max(np.abs(np.array(s.camera.location)-[P['cameraX'],-P['distance'],P['cameraZ']]))<1e-5
fits=json.loads((O/'bay-fit-v24.json').read_text(encoding='utf-8'))['bays'];right=json.loads((O/'right-fit-v24.json').read_text(encoding='utf-8'))
walls={int(o['movie_bay']):o for o in bpy.data.collections['Movie courtyard projection v24 — complete solid rooms'].objects if o.get('geometry_role')=='lowerWall'}
def point(b,x,z,front=0):
    a=b['angle'];r=b['chordRadius']-front
    return Vector((r*math.sin(a)+x*math.cos(a)+center[0],r*math.cos(a)-x*math.sin(a)+center[1],float(height(z,b['index']))))
checks=[];lower={}
for b in fits+[right]:
    i=b['index'];wall=walls[i];normal=Vector((-math.sin(b['angle']),-math.cos(b['angle']),0))
    openings=b.get('openings',[dict(right['rectangle'],name='rectangle'),dict(x=right['oculus']['x'],bottom=right['oculus']['centerY']-.1,height=.2,name='oculus')])
    for op in openings:
        pos=point(b,op['x'],op['bottom']+op['height']*.45);hit=wall.ray_cast(pos+normal*2,-normal,distance=5)[0];assert not hit,(i,op['name']);checks.append({'bay':i,'name':op['name'],'wallHit':False})
    pos=point(b,-b['bayWidth']/2+.025,3);assert wall.ray_cast(pos+normal*2,-normal,distance=5)[0]
    bm=bmesh.new();bm.from_mesh(wall.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);assert all(e.is_manifold for e in bm.edges);bm.free()
    lower[str(i)]=[list(wall.matrix_world@v.co) for v in wall.data.vertices]
camera_errors=[]
for obs in F['observations']:
    if 'world' not in obs:continue
    uv=world_to_camera_view(s,s.camera,Vector(obs['world']));actual=[uv.x*2552,(1-uv.y)*1656]
    # Output aspect differs by 0.17% from source aspect; horizontal prediction
    # therefore has a small known difference, never an unexplained large one.
    error=float(np.linalg.norm(np.array(actual)-obs['projected']));assert error<1.1,(obs['name'],actual,error)
    camera_errors.append({'name':obs['name'],'native':actual,'mathProjectionDifferencePixels':error})
values=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert values==[0,0,15,15];s.frame_set(72)
# Shared radial room boundaries coincide after the complete-circle remap.
joins=[]
for edge in range(1,32):
    theta=old_edges[edge];v=np.array([[r*math.sin(theta),r*math.cos(theta),1.22] for r in [23.5,28.]])
    a=map_source(v);target=new_edges[edge];actual=np.arctan2(a[:,0]-center[0],a[:,1]-center[1]);err=float(np.max(np.abs(np.angle(np.exp(1j*(actual-target))))));assert err<1e-8;joins.append(err)
result={'revision':24,'freshReopenVerified':True,'characters':characters,'bodyHeadFeetAndPortalGeometryPreserved':True,'eightOpenings':checks,'fiveWallsWatertight':True,'cameraChecks':camera_errors,'ringBoundaryMaximumAngularError':max(joins),'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
(O/'verification-v24.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(O/'native-lower-walls-v24.json').write_text(json.dumps(lower),encoding='utf-8');print('PROJECTION_24_VERIFIED',json.dumps(result),flush=True)
if '--oblique' in sys.argv:
    b=bay_spec(13);a=b['angle'];normal=Vector((-math.sin(a),-math.cos(a),0));tangent=Vector((math.cos(a),-math.sin(a),0));target=point(b,0,3.5)
    s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
    camera.location=target+normal*12+tangent*8+Vector((0,0,5));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
    s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'movie-left-oblique-v24.png');bpy.ops.render.render(write_still=True)

