import bpy
from pathlib import Path
R=Path(__file__).parent;O=R/'reconstruction_v7';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'reconstruction_v6/Suzume_v6.blend'))
s=bpy.context.scene
# Reduce the pale, overlit look and preserve chromatic shadows.
s.view_settings.view_transform='Standard';s.view_settings.exposure=-.05;s.view_settings.gamma=1
for n in s.world.node_tree.nodes:
 if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.95

def ramp(name,lo,hi):
 m=bpy.data.materials.get(name)
 if not m:return
 for n in m.node_tree.nodes:
  if n.type=='VALTORGB':n.color_ramp.elements[0].color=(*lo,1);n.color_ramp.elements[-1].color=(*hi,1)
ramp('V5 aged blue grey lime plaster',(.021,.053,.068),(.10,.19,.23))
ramp('V5 warm pale green plaster',(.10,.19,.055),(.40,.47,.18))
ramp('V5 worn cornice',(.13,.20,.12),(.38,.47,.28))
ramp('V5 faded painted frame',(.016,.051,.053),(.095,.19,.16))
ramp('V5 bank stone',(.019,.065,.049),(.065,.16,.10))
water=bpy.data.materials['Clear turquoise water']
for n in water.node_tree.nodes:
 if n.type=='BSDF_PRINCIPLED':n.inputs['Base Color'].default_value=(.60,.96,.94,1);n.inputs['Roughness'].default_value=.035
 if n.type=='BSDF_TRANSPARENT':n.inputs[0].default_value=(.30,.85,.80,1)
 if n.type=='MIX_SHADER':n.inputs[0].default_value=.10
s.camera=bpy.data.objects['Reference_camera_630x750'];s.cycles.samples=20;s.render.resolution_x=630;s.render.resolution_y=750;s.render.filepath=str(O/'preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_v7.blend'));bpy.ops.render.render(write_still=True)
