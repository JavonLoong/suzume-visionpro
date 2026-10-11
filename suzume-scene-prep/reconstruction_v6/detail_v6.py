import bpy
from pathlib import Path
from mathutils import Vector
r=Path(__file__).parent/'reconstruction_v6'
bpy.ops.wm.open_mainfile(filepath=str(r/'Suzume_v6.blend'))
s=bpy.context.scene
c=bpy.data.objects.get('V5 detail inspection');s.camera=c
s.render.resolution_x=1200;s.render.resolution_y=850;s.cycles.samples=24
s.render.filepath=str(r/'detail_v6.png');bpy.ops.render.render(write_still=True)
