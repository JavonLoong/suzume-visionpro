"""Reopen the complete scene, verify light/world setup and preserved spatial geometry."""
from pathlib import Path
import bpy,json,sys,hashlib,math,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-lighting-v27';sys.path.insert(0,str(R));from projection_geometry_v24 import bay_spec,height,center
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_lighting_v27.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
audit=json.loads((O/'integration-v27.json').read_text(encoding='utf-8'));q=audit['lighting']
def fingerprint(ob,evaluated=False):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else ob;mesh=e.to_mesh() if evaluated else ob.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(ob.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
for name,value in audit['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==value,name
for name,row in audit['characters'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob,True)==row['worldHash'],name
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert ob.data==other.data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in ob.material_slots);assert all(sl.material.get('spatial_half')=='otherworld' for sl in other.material_slots)
assert audit['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
for row in audit['lights']:
    ob=bpy.data.objects[row['name']];assert np.max(np.abs(np.array(ob.matrix_world.translation)-row['worldPosition']))<1e-5
    assert np.max(np.abs(np.array(ob.matrix_world.to_quaternion()@Vector((0,0,-1)))-row['worldDirection']))<1e-5
    assert abs(ob.data.energy-row['power'])<1e-5;assert np.max(np.abs(np.array(ob.data.color)-row['color']))<1e-5
nodes=s.world.node_tree.nodes;links=s.world.node_tree.links
assert abs(nodes['Background'].inputs['Strength'].default_value-q['worldStrength'])<1e-6
assert abs(nodes['Film lighting v27 visible sky'].inputs['Strength'].default_value-q['skyStrength'])<1e-6
assert np.max(np.abs(np.array(nodes['Film lighting v27 camera sky color'].inputs[2].default_value[:3])-q['skyTint']))<1e-6
assert any(l.from_node.name=='Film lighting v27 sky and illumination' and l.to_node.type=='OUTPUT_WORLD' for l in links)
assert any(l.from_node.type=='LIGHT_PATH' and l.from_socket.name=='Is Camera Ray' and l.to_node.name=='Film lighting v27 camera or reflection' for l in links)
assert any(l.from_node.type=='LIGHT_PATH' and l.from_socket.name=='Is Glossy Ray' and l.to_node.name=='Film lighting v27 reflection sky contribution' for l in links)
values=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert values==[0,0,15,15];s.frame_set(72)
result={'revision':27,'freshReopenVerified':True,'allDayMeshesUnchanged':len(audit['allDayMeshHashes']),'characterFeetHeadAndPortalPreserved':True,'cameraUnchanged':True,'worldSpaceLightPositionsDirectionsPowersAndColorsVerified':True,'separateCameraAndGlossySkyShaderVerified':True,'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
(O/'verification-v27.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('LIGHTING_27_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--oblique' in sys.argv:
    b=bay_spec(13);a=b['angle'];n=Vector((-math.sin(a),-math.cos(a),0));t=Vector((math.cos(a),-math.sin(a),0));target=Vector((b['chordRadius']*math.sin(a)+center[0],b['chordRadius']*math.cos(a)+center[1],float(height(3.5,13))))
    s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
    camera.location=target+n*12+t*8+Vector((0,0,5));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
    s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'movie-left-oblique-v27.png');bpy.ops.render.render(write_still=True)
