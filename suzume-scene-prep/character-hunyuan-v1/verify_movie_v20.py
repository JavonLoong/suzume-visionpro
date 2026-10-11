import bpy,json,hashlib,numpy as np,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-calibration-v20'
names=['Suzume Hunyuan textured surface','Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']

def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();out={}
    for name in names:
        o=bpy.data.objects[name];e=o.evaluated_get(deps);m=e.to_mesh();a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
        out[name]={'vertices':len(a),'worldHash':hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest(),'minZ':float(a[:,2].min())};e.to_mesh_clear()
    return out

before=snapshot(R/'Suzume_scene_Hunyuan_v19.blend')
after=snapshot(O/'Suzume_scene_movie_candidate_v20.blend');assert before==after
s=bpy.context.scene
for name in names:
    a=bpy.data.objects[name];partner='Suzume Hunyuan entered portion' if name==names[0] else name+' — entered portion';b=bpy.data.objects[partner]
    assert a.data==b.data
    assert all(x.material.get('spatial_half')=='courtyard' for x in a.material_slots)
    assert all(x.material.get('spatial_half')=='otherworld' for x in b.material_slots)
lights=[];light=bpy.data.lights['Daylight entering the open doorway v19']
for f in [1,24,72,120]:s.frame_set(f);bpy.context.view_layer.update();lights.append(light.energy)
assert lights==[0,0,15,15];s.frame_set(72)
gn=[]
for o in s.objects:
    for m in o.modifiers:
        if m.type=='NODES':
            rs=[n for n in m.node_group.nodes if n.bl_idname=='GeometryNodeRealizeInstances'];gn.append({'object':o.name,'realizeNodesMuted':all(n.mute for n in rs)})
            assert all(n.mute for n in rs)
checks={'revision':20,'freshReopenVerified':True,'characterWorldVerticesExactlyPreserved':True,'characters':after,'complementaryPortalMaterialsPreserved':True,'doorLightFrames':[1,24,72,120],'doorLightPowers':lights,'geometryInstances':gn,'allAngleImagesReviewed':False,'oneToOneComplete':False}
(O/'verification-v20.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');print('V20_VERIFIED',json.dumps(checks),flush=True)
if '--front' in sys.argv:
    s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True
    s.render.filepath=str(O/'movie-front-candidate-v20.png');bpy.ops.render.render(write_still=True)
if '--overview' in sys.argv:
    # A real oblique perspective checks the entire circular courtyard.
    # Saved animation markers select the original hero camera during rendering.
    # Remove those bindings only in this unsaved review session.
    s.timeline_markers.clear()
    cam=s.camera.copy();cam.data=s.camera.data.copy();cam.name='Movie courtyard review camera';s.collection.objects.link(cam);s.camera=cam
    cam.location=(105,-160,105);cam.rotation_euler=(Vector((16,-39,8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=26
    s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=16;s.cycles.use_denoising=True
    s.render.filepath=str(O/'movie-overview-v20.png');bpy.ops.render.render(write_still=True)
if '--side' in sys.argv:
    s.timeline_markers.clear()
    cam=s.camera.copy();cam.data=s.camera.data.copy();cam.name='Movie doorway side review camera';s.collection.objects.link(cam);s.camera=cam
    cam.location=(-5.2,-1.8,2.35);cam.rotation_euler=(Vector((-.1,.4,1.75))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=30
    s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
    s.render.filepath=str(O/'movie-side-v20.png');bpy.ops.render.render(write_still=True)
