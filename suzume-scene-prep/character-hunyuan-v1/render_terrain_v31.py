"""Render saved terrain in a fresh process, independently of geometry audits."""
from pathlib import Path
import bpy
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-terrain-v31';bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_terrain_v31.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
print('TERRAIN_RENDER_ENGINE',s.render.engine,'DEVICE',s.cycles.device,flush=True)
s.render.filepath=str(O/'movie-front-v31.png');bpy.ops.render.render(write_still=True);print('TERRAIN_31_FRONT_DONE',flush=True)
night=bpy.data.scenes['Night meadow through the door'];bpy.context.window.scene=night;night.timeline_markers.clear();night.frame_set(72);cam=s.camera.copy();cam.data=s.camera.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();night.collection.objects.link(cam);night.camera=cam;cam.location=(-18,22,5.5);target=Vector((0,230,13));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45
night.render.use_border=False;night.render.use_crop_to_border=False;night.render.resolution_x=720;night.render.resolution_y=468;night.render.resolution_percentage=100;night.cycles.samples=24;night.cycles.use_denoising=True
night.render.filepath=str(O/'night-wide-v31.png');bpy.ops.render.render(write_still=True);print('TERRAIN_31_WIDE_DONE',flush=True)
