import bpy
from pathlib import Path
R=Path(__file__).parent;O=R/'reconstruction_v7'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_v7.blend'))
s=bpy.context.scene;s.cycles.samples=32;s.render.resolution_x=1008;s.render.resolution_y=1200;s.render.filepath=str(O/'front_v7.png')
s['reconstruction_status']='V7 material and lighting color pass; geometry preserved from V6; exact color matching incomplete.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_v7.blend'));bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
 if o.type=='MESH' and not any(c.name=='V5_Volumetric_clouds' for c in o.users_collection):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'Suzume_v7.glb'),export_format='GLB',use_selection=True,export_extras=True)
