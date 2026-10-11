import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v14.blend'))
scene=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=scene;scene.frame_set(72)
mesh=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
deps=bpy.context.evaluated_depsgraph_get();posed=bpy.data.meshes.new_from_object(mesh.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
posed.transform(mesh.matrix_world)
obj=bpy.data.objects.new('Suzume — posed Hunyuan reconstruction',posed)
studio=bpy.data.scenes.new('Posed character inspection');bpy.context.window.scene=studio;studio.collection.objects.link(obj)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
(R/'viewer').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(R/'viewer'/'suzume-posed.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
bpy.ops.export_scene.gltf(filepath=str(R/'viewer'/'suzume-posed.gltf'),export_format='GLTF_SEPARATE',use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
studio.render.engine='CYCLES';studio.cycles.samples=16;studio.cycles.use_denoising=True
studio.render.resolution_x=700;studio.render.resolution_y=1000;studio.render.resolution_percentage=100
studio.view_settings.view_transform='Standard';studio.view_settings.look='None'
world=bpy.data.worlds.new('Pose inspection neutral studio');studio.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear();bg=nodes.new('ShaderNodeBackground');out=nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],out.inputs[0]);bg.inputs[0].default_value=(.5,.5,.5,1);bg.inputs[1].default_value=.7
center=Vector((-.15,.65,1.55))
for pos,power,size in [((3,-4,6),650,4),((-4,1,3),300,4),((0,5,5),550,3)]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);studio.collection.objects.link(o);o.location=pos;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
camData=bpy.data.cameras.new('Pose inspection');cam=bpy.data.objects.new('Pose inspection',camData);studio.collection.objects.link(cam);studio.camera=cam;camData.type='ORTHO';camData.ortho_scale=3.4
for label,a in [('back',0),('side',math.pi/2),('front',math.pi)]:
 cam.location=center+Vector((math.sin(a)*8,-math.cos(a)*8,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 studio.render.filepath=str(R/f'posed-{label}-v14.png');bpy.ops.render.render(write_still=True)
print('POSED_EXPORT_AND_INSPECTION_COMPLETE',flush=True)
