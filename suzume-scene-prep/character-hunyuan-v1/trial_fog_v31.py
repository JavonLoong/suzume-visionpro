"""Compare a more visible low mist, preserving the already fitted terrain."""
from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;O=R/'movie-terrain-v31';sys.path.insert(0,str(R));from terrain_setup_v31 import fog_material
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_terrain_v31.blend'));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
q=json.loads((O/'terrain-spec-v31.json').read_text(encoding='utf-8'));q.update(fogDensity=.045,fogEmissionGain=1.2)
for i,row in enumerate(q['fogVolumes']):fog_material(bpy.data.objects['Low meadow mist v31 '+str(i)],row,q)
(O/'mist-visible-trial-v31.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
s.render.resolution_x=960;s.render.resolution_y=624;s.render.resolution_percentage=100;s.cycles.samples=12;s.cycles.use_denoising=True;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.36;s.render.border_max_x=.58;s.render.border_min_y=.37;s.render.border_max_y=.71
s.render.filepath=str(O/'trial-visible-mist-v31.png');bpy.ops.render.render(write_still=True);print('VISIBLE_MIST_TRIAL_DONE',flush=True)
