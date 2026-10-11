import bpy
from pathlib import Path
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
s=bpy.context.scene;n=s.world.node_tree.nodes;lk=s.world.node_tree.links
for node in n:
 if node.type=='TEX_NOISE':node.inputs['Scale'].default_value=12
maps=[node for node in n if node.type=='MAP_RANGE']
for node,r in zip(maps,[.30,.25,.12,.065,.07]):node.inputs['From Min'].default_value=1-r*r*.5
add=next(node for node in n if node.type=='MATH' and node.operation=='ADD');old=add.inputs[0].links[0].from_socket
mass=n.new('ShaderNodeMath');mass.operation='MULTIPLY';mass.inputs[1].default_value=.35;lk.new(old,mass.inputs[0]);lk.new(mass.outputs[0],add.inputs[0])
ramp=next(node for node in n if node.type=='VALTORGB');els=list(ramp.color_ramp.elements)
for e,p in zip(els,[.58,.70,.84]):e.position=p
els[2].color=(*tuple(((c+.055)/1.055)**2.4 for c in [.80,.88,.96]),1)
s.camera=bpy.data.objects['Reference_camera_630x750'];s.render.resolution_x=1008;s.render.resolution_y=1200
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
s.render.filepath=str(OUT/'front_v3.png');bpy.ops.render.render(write_still=True)
exec((ROOT/'render_v3_details.py').read_text(encoding='utf-8'))
