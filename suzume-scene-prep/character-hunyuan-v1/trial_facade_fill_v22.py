"""Compare facade illumination without changing the saved scene."""
from pathlib import Path
import bpy, sys, json

R = Path(__file__).parent
O = R / 'movie-material-v22'
bpy.ops.wm.open_mainfile(filepath=str(O / 'Suzume_scene_movie_material_v22.blend'))
s = bpy.data.scenes['Daytime circular hotel']
bpy.context.window.scene = s
s.frame_set(72)
s.render.use_border = True
s.render.use_crop_to_border = False
s.render.border_min_x = 520 / 720
s.render.border_max_x = 1
s.render.border_min_y = (468 - 250) / 468
s.render.border_max_y = (468 - 45) / 468
s.render.use_persistent_data = True
s.cycles.samples = 24
s.cycles.use_denoising = True
light = bpy.data.lights['Soft courtyard fill on the movie facade v22']
variants = [{'name': str(power), 'power': power, 'color': [1, .98, .95]} for power in [2400, 3600, 4800]]
if '--warm' in sys.argv:
    variants = [
        {'name': '4800-warm', 'power': 4800, 'color': [1, .90, .72]},
        {'name': '4800-high-warm', 'power': 4800, 'color': [1, .90, .72], 'shift': [-2, 0, 2.8]},
        {'name': '6000-high-warm', 'power': 6000, 'color': [1, .90, .72], 'shift': [-2, 0, 2.8]},
    ]
emitter = bpy.data.objects[light.name]
base_position = emitter.location.copy()
for variant in variants:
    light.energy = variant['power']
    light.color = variant['color']
    emitter.location = base_position
    if 'shift' in variant:
        from mathutils import Vector
        emitter.location += Vector(variant['shift'])
        target = Vector(json.loads((O / 'integration-v22.json').read_text(encoding='utf-8'))['fillLight']['target'])
        emitter.rotation_euler = (target-emitter.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    s.render.filepath = str(O / f"facade-trial-{variant['name']}.png")
    bpy.ops.render.render(write_still=True)
    print('FACADE_TRIAL_RENDERED', json.dumps(variant), flush=True)
