from pathlib import Path
import bpy
R=Path(__file__).parent;O=R/'poster-v38'
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-collar-v37/Suzume_scene_movie_collar_v37.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(1)
s.render.use_border=False;s.render.use_crop_to_border=False
s.render.resolution_x=424;s.render.resolution_y=600;s.render.resolution_percentage=100
s.cycles.samples=16;s.cycles.use_denoising=True
s.render.filepath=str(O/'poster-current-before-v38.png')
bpy.ops.render.render(write_still=True)
print('POSTER_38_BASELINE_DONE',flush=True)
