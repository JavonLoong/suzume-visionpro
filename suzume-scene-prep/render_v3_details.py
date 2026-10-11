import bpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).parent/'reconstruction_v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
s=bpy.context.scene;primary=s.camera;s.render.resolution_x=900;s.render.resolution_y=900;s.cycles.samples=48
for name,pos,target,lens in [('door_detail',(2.8,-4,2.2),(0,0,1.2),58),('facade_detail',(6,-1,2.5),(5,6,1.7),48)]:
 bpy.ops.object.camera_add(location=pos);c=bpy.context.object;c.name=name;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;s.camera=c;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
s.camera=primary;s.render.resolution_x=1008;s.render.resolution_y=1200;s.render.filepath=str(OUT/'front_v3.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
