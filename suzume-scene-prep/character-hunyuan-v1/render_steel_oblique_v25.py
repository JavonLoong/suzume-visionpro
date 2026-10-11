"""Render the same comparison viewpoint as v24, without altering the saved camera."""
from pathlib import Path
import bpy,sys,math
from mathutils import Vector
R=Path(__file__).parent;sys.path.insert(0,str(R))
from projection_geometry_v24 import bay_spec,height,center
O=R/'movie-steel-v25';bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_steel_v25.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
b=bay_spec(13);a=b['angle'];normal=Vector((-math.sin(a),-math.cos(a),0));tangent=Vector((math.cos(a),-math.sin(a),0));target=Vector((b['chordRadius']*math.sin(a)+center[0],b['chordRadius']*math.cos(a)+center[1],float(height(3.5,13))))
s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
camera.location=target+normal*12+tangent*8+Vector((0,0,5));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'movie-left-oblique-v25.png');bpy.ops.render.render(write_still=True)
