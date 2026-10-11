"""Export a complete evaluated character, leaving spatial scene materials intact."""
from pathlib import Path
import bpy
from array import array
CHARACTER_PARTS=['Suzume Hunyuan textured surface','Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
def bake_parts(names=CHARACTER_PARTS):
 deps=bpy.context.evaluated_depsgraph_get();result=[]
 for name in names:
  ob=bpy.data.objects[name];mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps);mesh.transform(ob.matrix_world)
  material_indices=array('i',[0])*len(mesh.polygons);mesh.polygons.foreach_get('material_index',material_indices);mesh.materials.clear()
  for slot in ob.material_slots:
   mat=slot.material.copy();nodes=mat.node_tree.nodes if mat.use_nodes else None
   if nodes:
    mix=nodes.get('Spatial doorway half-space');out=next((n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
    if mix and out:mat.node_tree.links.new(mix.inputs[1].links[0].from_socket,out.inputs['Surface']);mat['spatial_half']='full_surface'
   mesh.materials.append(mat)
  mesh.polygons.foreach_set('material_index',material_indices)
  result.append(bpy.data.objects.new(name+' — complete evaluated mesh',mesh))
 return result
def export_character(directory,revision,names=CHARACTER_PARTS):
 directory=Path(directory);directory.mkdir(exist_ok=True);copies=bake_parts(names);scene=bpy.data.scenes.new('Complete posed character export '+str(revision));bpy.context.window.scene=scene
 for o in copies:scene.collection.objects.link(o);o.select_set(True)
 bpy.context.view_layer.objects.active=copies[0]
 for fmt,ext in [('GLTF_SEPARATE','gltf'),('GLB','glb')]:bpy.ops.export_scene.gltf(filepath=str(directory/f'suzume-posed-v{revision}.{ext}'),export_format=fmt,use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
 counts={}
 for o in copies:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
 return counts
