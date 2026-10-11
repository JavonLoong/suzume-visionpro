import bpy
from pathlib import Path
p=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(p/'Suzume_reference_reconstruction.blend'))
s=bpy.context.scene;s.view_settings.exposure=1.2
s.camera=bpy.data.objects['01_Film_front_study']
bpy.ops.wm.save_as_mainfile(filepath=str(p/'Suzume_reference_reconstruction.blend'))
for name,file,width in [('01_Film_front_study','front_view.png',1200),('02_Assembly_overview','assembly_view.png',1400)]:
 s.camera=bpy.data.objects[name];s.render.resolution_x=width;s.render.filepath=str(p/file);bpy.ops.render.render(write_still=True)
