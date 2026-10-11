"""Reopen and check section topology, I-profile voids, and unchanged scene."""
from pathlib import Path
import bpy,bmesh,json,sys,math,hashlib,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-steel-v25';sys.path.insert(0,str(R))
from projection_geometry_v24 import bay_spec,height,center
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_steel_v25.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
audit=json.loads((O/'integration-v25.json').read_text(encoding='utf-8'));fit=json.loads((O/'steel-fit-v25.json').read_text(encoding='utf-8'))
def coordinates(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o;mesh=e.to_mesh() if evaluated else o.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return a
def fingerprint(o,evaluated=False):return hashlib.sha256(np.round(coordinates(o,evaluated),6).astype('<f4').tobytes()).hexdigest()
for name,value in audit['unchangedOtherMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==value,name
for name,row in audit['characters'].items():
    o=bpy.data.objects[name];assert fingerprint(o,True)==row['worldHash']
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert o.data==other.data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in o.material_slots);assert all(sl.material.get('spatial_half')=='otherworld' for sl in other.material_slots)
assert not any(o.name.startswith('Broken radial dome steelwork solid mesh') for o in s.objects)
parts=list(bpy.data.collections['Movie steelwork v25 — complete radial structure'].objects);assert len(parts)==audit['newParts']==732
closed=[];meshes={}
for o in parts:
    a=coordinates(o).astype('<f4');assert np.isfinite(a).all();meshes[o.name]={'vertices':len(a),'nativeFloat32Hash':hashlib.sha256(a.tobytes()).hexdigest()}
    if o['steel_kind'] in ['column','rib','observed-bow','observed-hanger']:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);assert all(e.is_manifold for e in bm.edges),o.name;bm.free();closed.append(o.name)
checks=[]
for q in fit['mainColumns']:
    o=bpy.data.objects[f"I-section support column {q['index']} v25"];a=q['angle'];radial=Vector((math.sin(a),math.cos(a),0));tangent=Vector((math.cos(a),-math.sin(a),0));base=Vector(q['point']);base.z=-1
    for name,u,v,expected in [('web',0,0,True),('flange',.10,.12,True),('I-section recessed cavity',.10,0,False)]:
        hit=o.ray_cast(base+tangent*u+radial*v,Vector((0,0,1)),distance=11)[0];assert hit==expected,(q['name'],name,hit);checks.append({'column':q['index'],'sample':name,'hit':hit})
for name in ['Film corroded I-section steel v25','Film exposed steel connections v25']:
    m=bpy.data.materials[name];assert not any(n.type=='TEX_IMAGE' for n in m.node_tree.nodes);assert any(n.type=='TEX_NOISE' for n in m.node_tree.nodes)
    assert any(l.from_node.type=='NEW_GEOMETRY' and l.from_socket.name=='Position' and l.to_node.type=='TEX_NOISE' for l in m.node_tree.links)
values=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert values==[0,0,15,15];s.frame_set(72)
fill=bpy.data.objects[audit['rightFacadeFill']['name']];assert np.max(np.abs(np.array(fill.location)-audit['rightFacadeFill']['position']))<1e-5
assert abs(fill.data.energy-audit['rightFacadeFill']['powerWatts'])<.1
front=fill.rotation_euler.to_quaternion()@Vector((0,0,-1))
for name in audit['characters']:
    o=bpy.data.objects[name];assert max((o.matrix_world@Vector(corner)-fill.location).dot(front) for corner in o.bound_box)<0
leaves=[o for o in parts if o['steel_kind']=='ivy-leaf'];assert len(leaves)==202
result={'revision':25,'freshReopenVerified':True,'allOtherDayMeshesUnchanged':len(audit['unchangedOtherMeshHashes']),'charactersAndPortalPreserved':True,'newParts':len(parts),'closedStructuralSections':len(closed),'mainColumnCrossSectionRays':checks,'attachedIvyLeaves':len(leaves),'proceduralIsotropicMetal':True,'movedFillPreservesForegroundBehindEmitter':True,'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
(O/'verification-v25.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(O/'native-steel-meshes-v25.json').write_text(json.dumps(meshes,indent=2),encoding='utf-8');print('STEEL_25_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--oblique' in sys.argv:
    b=bay_spec(13);a=b['angle'];normal=Vector((-math.sin(a),-math.cos(a),0));tangent=Vector((math.cos(a),-math.sin(a),0));target=Vector((b['chordRadius']*math.sin(a)+center[0],b['chordRadius']*math.cos(a)+center[1],float(height(3.5,13))))
    s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
    camera.location=target+normal*12+tangent*8+Vector((0,0,5));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
    s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'movie-left-oblique-v25.png');bpy.ops.render.render(write_still=True)
