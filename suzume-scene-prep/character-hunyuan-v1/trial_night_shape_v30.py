"""Cloud-only shape diagnostic using the calibrated film camera, no image planes."""
from pathlib import Path
import bpy,json,sys,copy
R=Path(__file__).parent;O=R/'movie-night-v30';sys.path.insert(0,str(R));from night_setup_v30 import apply_night
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-water-v29/Suzume_scene_movie_water_v29.blend'))
day=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=day;day.frame_set(72)
s=bpy.data.scenes.new('Night cloud diagnostic v30');s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.use_persistent_data=True
s.view_settings.view_transform='AgX';s.view_settings.look=day.view_settings.look;s.view_settings.exposure=.8
s.world=bpy.data.worlds.new('Cloud diagnostic black world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
cam=day.camera.copy();cam.data=day.camera.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();s.collection.objects.link(cam);s.camera=cam
for name in ['Native enclosing night sky']+['Spatial twilight cloud volume '+str(i) for i in range(10)]:s.collection.objects.link(bpy.data.objects[name])
bpy.context.window.scene=s
s.render.resolution_x=960;s.render.resolution_y=624;s.render.resolution_percentage=100
s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.354;s.render.border_max_x=.617;s.render.border_min_y=.60;s.render.border_max_y=.87
q=json.loads((O/'night-spec-initial-v30.json').read_text());q.update(fieldRevision=2,density=.065,emissionGain=1.15,turbulence=1.0)
q['clouds'][0]['halfSize'][2]=6.2;q['clouds'][1]['halfSize'][2]=3.6;q['clouds'][2]['halfSize'][2]=2.6;q['clouds'][3]['halfSize'][2]=4.2
trials=[dict(copy.deepcopy(q),name='filaments'),dict(copy.deepcopy(q),name='broken',turbulence=1.7,density=.085,emissionGain=1.05)]
(O/'night-shape-trials-v30.json').write_text(json.dumps(trials,indent=2),encoding='utf-8')
for q in trials:
    apply_night(s,q);s.render.filepath=str(O/('shape-'+q['name']+'-v30.png'));print('NIGHT_SHAPE_BEGIN',q['name'],flush=True);bpy.ops.render.render(write_still=True);print('NIGHT_SHAPE_DONE',q['name'],flush=True)
