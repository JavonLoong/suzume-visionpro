"""Render only the aperture while selecting an illumination level."""
import bpy
from pathlib import Path
R=Path(__file__).parent;O=R/'night-calibration-v19'
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
light=bpy.data.lights['Daylight entering the open doorway v19'];light.animation_data_clear()
s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
s.render.use_border=True;s.render.use_crop_to_border=True
s.render.border_min_x=.378;s.render.border_max_x=.549;s.render.border_min_y=.102;s.render.border_max_y=.86
s.cycles.samples=24;s.cycles.use_denoising=True;s.render.use_persistent_data=True
for power in [15,30,50]:
    light.energy=power;s.render.filepath=str(O/f'aperture-light-{power}.png')
    bpy.ops.render.render(write_still=True);print('LIGHT_LEVEL_RENDERED',power,flush=True)
