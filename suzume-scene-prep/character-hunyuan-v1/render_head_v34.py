from pathlib import Path
import bpy,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-head-v34';sys.path.insert(0,str(R));from character_export_utils import bake_parts
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_head_v34.blend'));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
if '--front-only' in sys.argv:
 s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'movie-front-v34.png');bpy.ops.render.render(write_still=True);print('HEAD_34_SCENE_DONE',flush=True);raise SystemExit(0)
copies=bake_parts(['Suzume Hunyuan textured surface','Suzume mathematical head v34']);studio=bpy.data.scenes.new('Independent head parts inspection v34');bpy.context.window.scene=studio
for o in copies:studio.collection.objects.link(o)
studio.render.engine='CYCLES';studio.cycles.samples=24;studio.cycles.use_denoising=True;studio.view_settings.view_transform='AgX';studio.view_settings.exposure=.8
world=bpy.data.worlds.new('Head inspection background');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.12,.15,.18,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;studio.world=world;target=Vector((-.15,.6,2.65))
for p,power,size in [((-3,-3,6),400,4),((2,2,4),240,3)]:
 d=bpy.data.lights.new('Head softbox','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(d.name,d);studio.collection.objects.link(o);o.location=p;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Head inspection camera');cam=bpy.data.objects.new(d.name,d);studio.collection.objects.link(cam);studio.camera=cam;d.type='ORTHO';d.ortho_scale=1.35;studio.render.resolution_x=650;studio.render.resolution_y=800;studio.render.resolution_percentage=100
for label,pos in [('side',(-5,.6,2.75)),('back',(-.15,-4.5,2.75)),('front',(-.15,5,2.75))]:
 cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();studio.render.filepath=str(O/f'head-{label}-v34.png');bpy.ops.render.render(write_still=True);print('HEAD_34_'+label.upper()+'_DONE',flush=True)
