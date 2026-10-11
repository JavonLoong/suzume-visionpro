"""Fit the editable mathematical head candidate to the preserved v16 body.

This is an alternate head, not a new Hunyuan generation or a v17 replacement.
"""
import bpy, numpy as np, json, math, sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;H=R/'head-hunyuan-v1'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='Suzume clean head integration v18 candidate'
with bpy.data.libraries.load(str(H/'head-socket-v16.blend'),link=False) as (source,target):
    target.objects=['Suzume Hunyuan textured surface']
body=target.objects[0]
scene.collection.objects.link(body)
rig=next(m.object for m in body.modifiers if m.type=='ARMATURE')
if rig.name not in scene.objects:scene.collection.objects.link(rig)
with bpy.data.libraries.load(str(H/'clean-v18'/'Suzume-clean-head-v18.blend'),link=False) as (source,target):
    target.objects=source.objects
parts=[]
for obj in target.objects:
    if obj.type=='MESH' and obj.get('head_part_v18'):
        scene.collection.objects.link(obj);parts.append(obj)
        mask=obj.vertex_groups.new(name='Attachment neck only')
        if obj.name=='Clean neck':mask.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    else:bpy.data.objects.remove(obj,do_unlink=True)
for obj in scene.objects:obj.select_set(False)
for obj in parts:obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
joined=bpy.context.object;joined.name='Suzume clean mathematical head'
new_parts=[joined]
for obj in new_parts:
    P=np.empty((len(obj.data.vertices),3),np.float32)
    obj.data.vertices.foreach_get('co',P.ravel())
    original=P.copy()
    P*=.118
    P[:,0]-=.004
    P[:,2]+=1.1751030684-.9738872647*.118
    neck_group=obj.vertex_groups['Attachment neck only'].index
    neckness=np.array([any(g.group==neck_group and g.weight>.5 for g in v.groups) for v in obj.data.vertices],np.float32)
    if obj.name=='Suzume clean mathematical head':
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
    obj['independent_head_generation']='Reference-driven mathematical geometry, manually parameterized face and hair. Hunyuan v17 supplies registration dimensions only.'
    obj['head_attachment_revision']=18

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
    mesh.calc_loop_triangles();counts[obj.name]=len(mesh.loop_triangles)
    material_indices=np.empty(len(mesh.polygons),np.int32)
    mesh.polygons.foreach_get('material_index',material_indices)
    mesh.materials.clear()
    for slot in obj.material_slots:mesh.materials.append(slot.material)
    mesh.polygons.foreach_set('material_index',material_indices)
    copy=bpy.data.objects.new(obj.name+' — baked v18',mesh);baked.append(copy)
assert abs(min_height-.2034619255)<.00001,min_height
assert len(rig.data.bones)==20
assert counts[body.name]==408817
audit={'revision':18,'headSource':'Reference-driven mathematical reconstruction; no additional Hunyuan generation',
       'originalBodySource':'Hunyuan3D 3.1; v16 pose and foot correction preserved',
       'headReplaced':True,'faceColorMethod':'Editable material regions, curved eye geometry and physical left hairpins',
       'partTriangles':counts,'rigBones':20,'minimumWorldHeight':min_height,
       'sourceBodyTrianglesPreserved':408817,'headRestScale':.118,
       'neckBlendZ':[.976,1.023],'oneToOneComplete':False,
       'limitations':['Facial identity remains approximate.','This candidate does not replace the v17 default.','Full-scene portal rendering requires separate verification.']}
(H/'integration-v18.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
scene['Character revision']='v18 candidate: mathematical face and hair on the preserved v16 Hunyuan body/rig.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_character_head_v18.blend'))
export_scene=bpy.data.scenes.new('Baked v18 character export')
bpy.context.window.scene=export_scene
for obj in baked:export_scene.collection.objects.link(obj);obj.select_set(True)
bpy.context.view_layer.objects.active=baked[0]
for fmt,ext in [('GLB','glb'),('GLTF_SEPARATE','gltf')]:
    bpy.ops.export_scene.gltf(filepath=str(R/'viewer'/f'suzume-posed-v18.{ext}'),export_format=fmt,use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
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
    scene.render.filepath=str(R/f'posed-{label}-v18.png');bpy.ops.render.render(write_still=True)
print('HEAD_INTEGRATION_V18_EXPORTED',json.dumps(audit),flush=True)
