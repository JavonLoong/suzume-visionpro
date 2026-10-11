from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-door-v32';bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_door_v32.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
s.render.filepath=str(O/'movie-front-v32.png');bpy.ops.render.render(write_still=True);print('DOOR_32_FRONT_DONE',flush=True)
# A neutral studio inspection includes the complete hand, even beyond the portal.
# Its purpose is contact inspection; it is not presented as the final night scene.
ins=bpy.data.scenes.new('Door and hand contact inspection v32');ins.render.engine='CYCLES';ins.cycles.samples=32;ins.cycles.use_denoising=True
ins.view_settings.view_transform='AgX';ins.view_settings.exposure=.8
dep=bpy.context.evaluated_depsgraph_get();names=['Suzume Hunyuan textured surface','Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
root=bpy.data.objects['Complete six-panel white door and frame'];objects=[bpy.data.objects[n] for n in names]+[o for o in root.children_recursive if o.type=='MESH']
for ob in objects:
 mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep);mesh.transform(ob.matrix_world);mesh.materials.clear()
 for slot in ob.material_slots:
  mat=slot.material.copy();nodes=mat.node_tree.nodes if mat.use_nodes else None
  if nodes:
   mix=nodes.get('Spatial doorway half-space');out=next((n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
   if mix and out:mat.node_tree.links.new(mix.inputs[1].links[0].from_socket,out.inputs['Surface'])
  mesh.materials.append(mat)
 ins.collection.objects.link(bpy.data.objects.new(ob.name+' inspection',mesh))
bpy.context.window.scene=ins;world=bpy.data.worlds.new('Neutral contact background');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.19,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;ins.world=world
target=Vector((.27,1.06,2.08))
for p,power,size in [((-3,3,6),480,4),((2,4,3),260,3),((-2,-2,5),300,3)]:
 d=bpy.data.lights.new('Contact softbox','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(d.name,d);ins.collection.objects.link(o);o.location=p;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Contact inspection camera');cam=bpy.data.objects.new(data.name,data);ins.collection.objects.link(cam);ins.camera=cam;data.lens=60;data.sensor_fit='VERTICAL';data.sensor_height=36
cam.location=(-1.8,3.4,2.7);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
ins.render.resolution_x=800;ins.render.resolution_y=650;ins.render.resolution_percentage=100;ins.render.filepath=str(O/'door-hand-inspection-v32.png');bpy.ops.render.render(write_still=True);print('DOOR_32_HAND_DONE',flush=True)
