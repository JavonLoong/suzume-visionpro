"""Export the complete calibrated surface; both worlds clip it at runtime."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v16.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
mesh=bpy.data.objects['Suzume Hunyuan textured surface']
deps=bpy.context.evaluated_depsgraph_get()
posed=bpy.data.meshes.new_from_object(mesh.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
posed.transform(mesh.matrix_world)
obj=bpy.data.objects.new('Suzume — film-calibrated Hunyuan reconstruction v16',posed)
materials=[]
for slot in mesh.material_slots:
 mat=slot.material.copy();mat.name='Suzume full surface v16'
 nodes=mat.node_tree.nodes;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
 mix=nodes.get('Spatial doorway half-space')
 if mix:mat.node_tree.links.new(mix.inputs[1].links[0].from_socket,out.inputs['Surface'])
 materials.append(mat)
posed.materials.clear()
for mat in materials:posed.materials.append(mat)
studio=bpy.data.scenes.new('Calibrated character inspection v16');bpy.context.window.scene=studio;studio.collection.objects.link(obj)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
if '--inspection-only' not in sys.argv:
 for fmt,ext in [('GLB','glb'),('GLTF_SEPARATE','gltf')]:
  bpy.ops.export_scene.gltf(filepath=str(R/'viewer'/f'suzume-posed-v16.{ext}'),export_format=fmt,use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
if '--no-render' in sys.argv:raise SystemExit(0)
studio.render.engine='CYCLES';studio.cycles.samples=16;studio.cycles.use_denoising=True
studio.render.resolution_x=700;studio.render.resolution_y=1000;studio.render.resolution_percentage=100
studio.view_settings.view_transform='Standard';studio.view_settings.look='None'
world=bpy.data.worlds.new('Pose inspection neutral studio v16');studio.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.5,.5,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
center=Vector((-.15,.45,1.6))
for pos,power,size in [((3,-4,6),650,4),((-4,1,3),300,4),((0,5,5),550,3)]:
 d=bpy.data.lights.new('Softbox v16','AREA');d.energy=power;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(d.name,d);studio.collection.objects.link(o);o.location=pos;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Pose inspection v16');cam=bpy.data.objects.new(d.name,d);studio.collection.objects.link(cam);studio.camera=cam;d.type='ORTHO';d.ortho_scale=3.5
for label,a in [('back',0),('side',math.pi/2),('front',math.pi)]:
 cam.location=center+Vector((math.sin(a)*8,-math.cos(a)*8,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 studio.render.filepath=str(R/f'posed-{label}-v16.png');bpy.ops.render.render(write_still=True)
print('V16_SURFACE_EXPORTED_AND_RENDERED',flush=True)
