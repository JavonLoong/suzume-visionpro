from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-steel-v25'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_steel_v25.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
materials=[bpy.data.materials[n] for n in ['Film corroded I-section steel v25','Film exposed steel connections v25']]
original={m.name:[list(e.color) for e in m.node_tree.nodes['Steel and oxide colors'].color_ramp.elements] for m in materials}
s.render.use_border=True;s.render.use_crop_to_border=False;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=(468-257)/468;s.render.border_max_y=1;s.render.use_persistent_data=True;s.cycles.samples=24
for factor in [1.0,.45]:
    for m in materials:
        bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=0;bs.inputs['Roughness'].default_value=.90
        for e,c in zip(m.node_tree.nodes['Steel and oxide colors'].color_ramp.elements,original[m.name]):e.color=(*[v*factor for v in c[:3]],1)
    s.render.filepath=str(O/f'steel-diffuse-trial-{factor}.png');bpy.ops.render.render(write_still=True);print('STEEL_MATERIAL_TRIAL',factor,flush=True)
