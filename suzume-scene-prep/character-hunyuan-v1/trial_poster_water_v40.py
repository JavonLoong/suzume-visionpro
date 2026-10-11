from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;O=R/'poster-water-v40';sys.path.insert(0,str(R))
from poster_water_setup_v40 import apply_water
name=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'balanced'
q=json.loads((O/('water-'+name+'.json')).read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-steel-v39/Suzume_dual_scene_steel_v39.blend'))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);apply_water(s,q)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=354;s.render.resolution_y=500;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/('trial-'+name+'.png'))
bpy.ops.render.render(write_still=True);print('WATER_TRIAL_DONE',name,flush=True)
