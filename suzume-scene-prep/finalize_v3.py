import bpy
from pathlib import Path
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
s=bpy.context.scene
for n in s.world.node_tree.nodes:
 if n.type=='VECT_MATH' and n.operation=='DOT_PRODUCT':n.inputs[1].default_value=tuple(-v for v in n.inputs[1].default_value)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
s.render.filepath=str(OUT/'front_v3.png');bpy.ops.render.render(write_still=True)
exec((ROOT/'render_v3_details.py').read_text(encoding='utf-8'))
