import bpy
from pathlib import Path
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v5'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Suzume_v5.blend'))
s=bpy.context.scene
s['reconstruction_status']='V5 rebuilt visible masonry, paving and water; generated sky environment; full 1:1 reconstruction unverified'
bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
 if o.type=='MESH' and not any(c.name=='V5_Volumetric_clouds' for c in o.users_collection):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_v5.glb'),export_format='GLB',use_selection=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v5.blend'))
