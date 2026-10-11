"""Two native optical trials of the existing water; no saved scene mutation."""
from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;O=R/'movie-water-v29';sys.path.insert(0,str(R));from water_setup_v29 import apply_water
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-surfaces-v28/Suzume_scene_movie_surfaces_v28.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
s.render.use_border=False;s.render.resolution_x=540;s.render.resolution_y=351;s.render.resolution_percentage=100;s.cycles.samples=16;s.cycles.use_denoising=True;s.render.use_persistent_data=True
shared={'reflectionTint':[.61,.86,1.],'transmissionTint':[.62,.90,.93],'transmissionRoughness':.018,'rippleAmplitudeScale':.4}
trials=[dict(shared,name='clear-bed',fresnel=[.18,.42],reflectionRoughness=.11),dict(shared,name='soft-reflection',fresnel=[.25,.38],reflectionRoughness=.20)]
(O/'water-trials-v29.json').write_text(json.dumps(trials,indent=2),encoding='utf-8')
for q in trials:
    apply_water(s,q);s.render.filepath=str(O/('trial-'+q['name']+'-v29.png'));print('WATER_TRIAL_BEGIN',q['name'],flush=True);bpy.ops.render.render(write_still=True);print('WATER_TRIAL_DONE',q['name'],flush=True)
