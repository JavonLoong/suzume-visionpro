"""Water-region trials: shallow scattering, grazing reflection and clear paving."""
from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;O=R/'movie-water-v29';sys.path.insert(0,str(R));from water_setup_v29 import apply_water
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-surfaces-v28/Suzume_scene_movie_surfaces_v28.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
s.render.resolution_x=540;s.render.resolution_y=351;s.render.resolution_percentage=100;s.cycles.samples=16;s.cycles.use_denoising=True;s.render.use_persistent_data=True
s.render.use_border=True;s.render.use_crop_to_border=False;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=0;s.render.border_max_y=.53
shared=json.loads((O/'water-refined-trials-v29.json').read_text())[0];shared.update(fresnel=[.005,.65],fresnelPower=8,hazeOpticalDepth=.15)
trials=[dict(shared,name='blue-scattering',hazeStrength=.55,hazeColorLinear=[.04162454519007973,.11022486473055675,.24189745987108655],hazeColorDisplay=[80,125,165]),dict(shared,name='gentle-scattering',hazeStrength=.35,hazeColorLinear=[.05665439900900135,.13624405892532795,.24611224943215995],hazeColorDisplay=[95,135,165])]
(O/'water-haze-trials-v29.json').write_text(json.dumps(trials,indent=2),encoding='utf-8')
for q in trials:
    apply_water(s,q);s.render.filepath=str(O/('trial-'+q['name']+'-v29.png'));print('WATER_TRIAL_BEGIN',q['name'],flush=True);bpy.ops.render.render(write_still=True);print('WATER_TRIAL_DONE',q['name'],flush=True)
