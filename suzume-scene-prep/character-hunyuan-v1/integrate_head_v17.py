"""Fit the independent Hunyuan head to the preserved v16 body and rig."""
import bpy, numpy as np, json, math, sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;H=R/'head-hunyuan-v1'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='Suzume independent head integration v17'
with bpy.data.libraries.load(str(H/'head-socket-v16.blend'),link=False) as (source,target):
    target.objects=['Suzume Hunyuan textured surface']
body=target.objects[0]
scene.collection.objects.link(body)
rig=next(m.object for m in body.modifiers if m.type=='ARMATURE')
if rig.name not in scene.objects:scene.collection.objects.link(rig)
head_names=['Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
with bpy.data.libraries.load(str(H/'new-head-colored-candidate.blend'),link=False) as (source,target):
    target.objects=head_names
new_parts=target.objects
for obj in new_parts:
    scene.collection.objects.link(obj)
    P=np.empty((len(obj.data.vertices),3),np.float32)
    obj.data.vertices.foreach_get('co',P.ravel())
    original=P.copy()
    P*=.118
    P[:,0]-=.004
    P[:,2]+=1.1751030684-.9738872647*.118
    neckness=np.clip((.50-original[:,1])/.25,0,1)
    neckness=neckness*neckness*(3-2*neckness)
    neckness*=original[:,2]<-.40
    if obj.name=='Suzume independent Hunyuan head':
        t=np.clip((-.4-original[:,2])/.48,0,1)
        t=t*t*(3-2*t);t*=neckness
        angle=np.arctan2(original[:,1]-.04,original[:,0]-.015)
        neck_x=-.003+.019*np.cos(angle)
        neck_y=-.002+.026*np.sin(angle)
        P[:,0]=P[:,0]*(1-t)+neck_x*t
        P[:,1]=P[:,1]*(1-t)+neck_y*t
    obj.data.vertices.foreach_set('co',P.ravel());obj.data.update()
    obj.parent=rig
    obj.matrix_parent_inverse.identity()
    obj.matrix_basis.identity()
    obj.vertex_groups.clear()
    head=obj.vertex_groups.new(name='head');neck=obj.vertex_groups.new(name='neck')
    weight=np.clip((P[:,2]-.976)/.047,0,1)
    weight=weight*weight*(3-2*weight)
    weight=1-(1-weight)*neckness
    # Quantizing only the blend weights keeps the neck smooth while avoiding
    # hundreds of thousands of individual Python/RNA calls.
    buckets=np.rint(weight*100).astype(int)
    for bucket in np.unique(buckets):
        indices=np.flatnonzero(buckets==bucket).tolist()
        if bucket:head.add(indices,float(bucket)/100,'REPLACE')
        if bucket<100:neck.add(indices,1-float(bucket)/100,'REPLACE')
    mod=obj.modifiers.new('Shared v16 character rig','ARMATURE');mod.object=rig
    obj['independent_head_generation']='Tencent Hunyuan3D-2mv Turbo; generated from four dedicated head views.'
    obj['head_attachment_revision']=17

# The character-only inspection/export uses complete materials; spatial clips
# are reinstated on day/night copies when assembling the native full scene.
for slot in body.material_slots:
    material=slot.material.copy();slot.link='OBJECT';slot.material=material
    nodes=material.node_tree.nodes;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    mix=nodes.get('Spatial doorway half-space')
    if mix:material.node_tree.links.new(mix.inputs[1].links[0].from_socket,out.inputs['Surface'])
    material['spatial_half']='full_surface'
scene.frame_set(72);bpy.context.view_layer.update()
objects=[body]+new_parts
deps=bpy.context.evaluated_depsgraph_get()
baked=[];counts={};min_height=1000
for obj in objects:
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
    mesh.transform(obj.matrix_world)
    P=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',P.ravel())
    min_height=min(min_height,float(P[:,2].min()))
    counts[obj.name]=len(mesh.polygons)
    mesh.materials.clear()
    for slot in obj.material_slots:mesh.materials.append(slot.material)
    copy=bpy.data.objects.new(obj.name+' — baked v17',mesh);baked.append(copy)
assert abs(min_height-.2034619255)<.00001,min_height
assert len(rig.data.bones)==20
assert counts[body.name]==408817
audit={'revision':17,'headSource':'Tencent official Hunyuan3D-2mv Turbo four-view generation',
       'originalBodySource':'Hunyuan3D 3.1; v16 pose and foot correction preserved',
       'headReplaced':True,'faceColorMethod':'Four-view projected vertex colors; physical left-only hairpins',
       'partTriangles':counts,'rigBones':20,'minimumWorldHeight':min_height,
       'sourceBodyTrianglesPreserved':408817,'headRestScale':.118,
       'neckBlendZ':[.976,1.023],'oneToOneComplete':False,
       'limitations':['Head geometry and texture registration remain approximate.','This character-only file has not yet proved full-scene portal rendering.']}
(H/'integration-v17.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
scene['Character revision']='v17: independently generated Hunyuan head on the preserved v16 rigged body.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_character_head_v17.blend'))
export_scene=bpy.data.scenes.new('Baked v17 character export')
bpy.context.window.scene=export_scene
for obj in baked:export_scene.collection.objects.link(obj);obj.select_set(True)
bpy.context.view_layer.objects.active=baked[0]
for fmt,ext in [('GLB','glb'),('GLTF_SEPARATE','gltf')]:
    bpy.ops.export_scene.gltf(filepath=str(R/'viewer'/f'suzume-posed-v17.{ext}'),export_format=fmt,use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
bpy.context.window.scene=scene
if '--no-render' in sys.argv:raise SystemExit(0)
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
scene.render.resolution_x=500;scene.render.resolution_y=750;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
world=bpy.data.worlds.new('Head integration neutral studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.5,.5,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
center=Vector((-.15,.45,1.6))
for pos,power,size in [((3,-4,6),650,4),((-4,1,3),300,4),((0,5,5),550,3)]:
    d=bpy.data.lights.new('Integration softbox','AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Integration inspection');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
for label,a,target,scale in [('front',math.pi,center,3.5),('side',math.pi/2,center,3.5),('head',math.pi,Vector((-.15,.75,2.95)),1.0),('head-side',math.pi/2,Vector((-.15,.75,2.95)),1.0)]:
    d.ortho_scale=scale;cam.location=target+Vector((math.sin(a)*8,-math.cos(a)*8,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(R/f'posed-{label}-v17.png');bpy.ops.render.render(write_still=True)
print('HEAD_INTEGRATION_V17_EXPORTED',json.dumps(audit),flush=True)
