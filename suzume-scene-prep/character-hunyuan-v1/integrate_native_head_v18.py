"""Install the reviewed replacement head on both sides of the spatial portal."""
import bpy,json,numpy as np,sys
from pathlib import Path
R=Path(__file__).parent;H=R/'head-hunyuan-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17.blend'))
day=bpy.data.scenes['Daytime circular hotel'];night=bpy.data.scenes['Night meadow through the door']
bpy.context.window.scene=day
body=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
inside=bpy.data.collections['Suzume — portion inside the otherworld']
day_collection=body.users_collection[0]
gate=float(bpy.data.objects['Spatial doorway portal aperture'].matrix_world.translation.y)
head_names=['Suzume clean mathematical head']
with bpy.data.libraries.load(str(R/'Suzume_character_head_v18.blend'),link=False) as (source,target):
    target.objects=head_names
parts=target.objects
unused_rigs=set()
for obj in parts:
    day_collection.objects.link(obj)
    if obj.parent and obj.parent!=rig:unused_rigs.add(obj.parent)
    obj.parent=rig
    for modifier in obj.modifiers:
        if modifier.type=='ARMATURE':modifier.object=rig

def clipped_material(base,entered):
    material=base.copy();material.name=base.name+(' — otherworld v18' if entered else ' — courtyard v18')
    nodes=material.node_tree.nodes;links=material.node_tree.links
    out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    surface=out.inputs['Surface'].links[0].from_socket
    geo=nodes.new('ShaderNodeNewGeometry');geo.name='World position at portal'
    xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],xyz.inputs[0])
    test=nodes.new('ShaderNodeMath');test.operation='LESS_THAN' if entered else 'GREATER_THAN';test.inputs[1].default_value=gate
    links.new(xyz.outputs['Y'],test.inputs[0])
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    mix=nodes.new('ShaderNodeMixShader');mix.name='Spatial doorway half-space'
    links.new(test.outputs[0],mix.inputs[0]);links.new(surface,mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
    material['spatial_half']='otherworld' if entered else 'courtyard'
    material['portal_plane_blender_y']=gate
    return material

pairs=[]
for obj in parts:
    other=obj.copy();other.data=obj.data;other.name=obj.name+' — entered portion';inside.objects.link(other)
    base_materials=[slot.material for slot in obj.material_slots]
    for target,entered in [(obj,False),(other,True)]:
        for slot,base in zip(target.material_slots,base_materials):
            slot.link='OBJECT';slot.material=clipped_material(base,entered)
    pairs.append((obj,other))
old_names=['Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
for name in old_names+[name+' — entered portion' for name in old_names]:
    old=bpy.data.objects.get(name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
for unused in unused_rigs:
    if unused!=rig:bpy.data.objects.remove(unused,do_unlink=True)
day.frame_set(72);night.frame_set(72);bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
minimum=1000;partition={}
for obj in [body]+parts:
    evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
    P=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',P.ravel())
    M=np.array(obj.matrix_world,dtype=float);P=P@M[:3,:3].T+M[:3,3]
    minimum=min(minimum,float(P[:,2].min()))
    partition[obj.name]={'vertices':len(P),'courtyardVertices':int((P[:,1]<=gate).sum()),'otherworldVertices':int((P[:,1]>=gate).sum()),'maxHeight':float(P[:,2].max())}
    evaluated.to_mesh_clear()
assert abs(minimum-.2034619255)<1e-5
assert len(rig.data.bones)==20
for a,b in pairs:
    assert a.data==b.data
    assert all(slot.material.get('spatial_half')=='courtyard' for slot in a.material_slots)
    assert all(slot.material.get('spatial_half')=='otherworld' for slot in b.material_slots)
    assert all(mod.object==rig for ob in [a,b] for mod in ob.modifiers if mod.type=='ARMATURE')
assert bpy.data.objects['Suzume continuation through spatial portal'].instance_collection==inside
audit={'revision':18,'nativeHeadIntegrated':True,'pairedParts':len(pairs),
       'sharedGeometryAndRig':True,'independentComplementaryMaterials':True,
       'standaloneNightIncludesNewHead':True,'portalGateY':gate,'partition':partition,
       'minimumWorldHeight':minimum,'rigBones':20,'oldHeadObjectsRemoved':True,
       'nativeRenderVerified':False,'oneToOneComplete':False}
day['Character revision']='v18 candidate: mathematical head on Hunyuan body; v16 rig/foot clearance and complementary portal clipping preserved.'
day['Head replacement status']='Alternate editable head candidate. Facial likeness remains approximate; not a new Hunyuan generation.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_scene_clean_head_v18.blend'))
(H/'native-integration-v18.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('NATIVE_V18_SAVED',json.dumps(audit),flush=True)
if '--render' in sys.argv:
    day.render.resolution_x=720;day.render.resolution_y=468;day.render.resolution_percentage=100
    day.cycles.samples=12;day.cycles.use_denoising=False
    day.render.filepath=str(R/'native-pose-front-v18.png')
    bpy.ops.render.render(write_still=True)
    audit['nativeRenderVerified']=True
    (H/'native-integration-v18.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('NATIVE_V18_RENDERED',flush=True)
