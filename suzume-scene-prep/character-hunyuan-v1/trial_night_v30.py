"""Render a focused portal region for two spatial density/emission trials."""
from pathlib import Path
import bpy,json,sys,copy
R=Path(__file__).parent;O=R/'movie-night-v30';sys.path.insert(0,str(R));from night_setup_v30 import apply_night
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-water-v29/Suzume_scene_movie_water_v29.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
s.render.resolution_x=960;s.render.resolution_y=624;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.use_persistent_data=True
s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.354;s.render.border_max_x=.617;s.render.border_min_y=.45;s.render.border_max_y=.87
base=json.loads((O/'night-spec-initial-v30.json').read_text());trials=[dict(copy.deepcopy(base),name='layered',density=.045,emissionGain=1.35),dict(copy.deepcopy(base),name='denser',density=.075,emissionGain=1.15)]
(O/'night-trials-v30.json').write_text(json.dumps(trials,indent=2),encoding='utf-8')
for q in trials:
    apply_night(s,q);s.render.filepath=str(O/('trial-'+q['name']+'-v30.png'));print('NIGHT_TRIAL_BEGIN',q['name'],flush=True);bpy.ops.render.render(write_still=True);print('NIGHT_TRIAL_DONE',q['name'],flush=True)
