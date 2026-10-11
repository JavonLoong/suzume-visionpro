"""Refine the side-light trial after inspecting its underlit right facade."""
from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;sys.path.insert(0,str(R));from lighting_setup_v27 import BASE,apply_lighting
O=R/'movie-lighting-v27';bpy.ops.wm.open_mainfile(filepath=str(R/'movie-shore-v26/Suzume_scene_movie_shore_v26.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);s.render.use_border=False;s.render.resolution_x=540;s.render.resolution_y=351;s.render.resolution_percentage=100;s.cycles.samples=12;s.cycles.use_denoising=True;s.render.use_persistent_data=True
variants=[{**BASE,'name':'focused-fill-650'},{**BASE,'name':'focused-fill-1000','rightFill':1000,'leftFill':64,'worldStrength':.055}]
audit=[]
for q in variants:
    apply_lighting(s,q);s.render.filepath=str(O/('trial-'+q['name']+'.png'));bpy.ops.render.render(write_still=True);audit.append(q);(O/'refined-trials-v27.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('LIGHTING_27_REFINED_DONE',q['name'],flush=True)
