"""Split the editable character at the spatial doorway in both native worlds."""
import bpy,json
from pathlib import Path
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v14.blend'))
day=bpy.data.scenes['Daytime circular hotel'];night=bpy.data.scenes['Night meadow through the door'];bpy.context.window.scene=day
mesh=bpy.data.objects['Suzume Hunyuan textured surface']
portal=bpy.data.objects['Spatial doorway portal aperture']
day.frame_set(72);bpy.context.view_layer.update()
gate_y=portal.matrix_world.translation.y
entered=bpy.data.collections.new('Suzume — portion inside the otherworld');night.collection.children.link(entered)
night_mesh=mesh.copy();night_mesh.data=mesh.data;night_mesh.name='Suzume Hunyuan entered portion';entered.objects.link(night_mesh)
def half_material(original,inside):
 mat=original.copy();mat.name=original.name+(' — otherworld half' if inside else ' — courtyard half')
 nodes=mat.node_tree.nodes;links=mat.node_tree.links
 out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
 surface=out.inputs['Surface'].links[0].from_socket
 position=nodes.new('ShaderNodeNewGeometry');position.name='World position at portal'
 xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(position.outputs['Position'],xyz.inputs[0])
 clip=nodes.new('ShaderNodeMath');clip.name='Discard the opposite world';clip.operation='LESS_THAN' if inside else 'GREATER_THAN';clip.inputs[1].default_value=gate_y;links.new(xyz.outputs['Y'],clip.inputs[0])
 transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');mix.name='Spatial doorway half-space'
 links.new(clip.outputs[0],mix.inputs[0]);links.new(surface,mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
 mat['spatial_half']='otherworld' if inside else 'courtyard';mat['portal_plane_blender_y']=gate_y
 return mat
base_materials=[slot.material for slot in mesh.material_slots]
for ob,inside in [(mesh,False),(night_mesh,True)]:
 for i,original in enumerate(base_materials):
  ob.material_slots[i].link='OBJECT';ob.material_slots[i].material=half_material(original,inside)
 ob['Space partition']='Blender Y >= gate belongs to night; Y <= gate belongs to courtyard. Same geometry and rig, complementary materials.'
instance=bpy.data.objects['Suzume continuation through spatial portal'];instance.instance_collection=entered
night.frame_set(72);day.frame_set(72)
day['Character revision']='v15: complementary world-space clipping; entered body exists only in the otherworld, with matching reflections and shadows.'
notes=bpy.data.texts.new('穿门空间分隔 v15');notes.write('人物按门洞平面进行世界坐标裁分。\n庭院只保留未进入的表面，夜景只保留已进入的表面。\n二者共用原始网格与骨骼；绕到门后不会在庭院看见已进入的身体。\nCycles 透明射线同时控制阴影与水中倒影。\n')
bpy.ops.wm.save_as_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v15.blend'))
audit={'revision':15,'method':'Complementary world-space material clipping on shared editable geometry and rig','gatePlaneBlenderY':gate_y,'dayKeeps':'Y <= gate','nightKeeps':'Y >= gate','sharedMesh':night_mesh.data==mesh.data,'sharedRig':night_mesh.modifiers[0].object==mesh.modifiers[0].object,'nightInstanceCollection':instance.instance_collection.name,'nightStandaloneLinked':entered.name in night.collection.children,'imagesPacked':all(im.packed_file for im in bpy.data.images if im.name.startswith('texture_pbr')),'visualReview':'pending'}
(R/'portal-partition-native-v15.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('NATIVE_PARTITION_SAVED',json.dumps(audit),flush=True)
