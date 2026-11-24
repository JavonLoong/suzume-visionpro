import bpy, json, numpy as np
from pathlib import Path
from mathutils import Vector

R = Path(__file__).resolve().parents[1]
A = R / 'analysis'
Q = R.parent / 'print-white-quality-20261030'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
s = bpy.context.scene
s.name = '400毫米庭院与兼容底座'
s.unit_settings.system = 'METRIC'
s.unit_settings.scale_length = .001
s.unit_settings.length_unit = 'MILLIMETERS'
colors = [(.30, .53, .60, 1), (.39, .62, .65, 1), (.48, .69, .67, 1), (.35, .58, .60, 1)]
def add(p, name, color):
    q = np.load(p)
    me = bpy.data.meshes.new(name)
    me.from_pydata(q['vertices'], [], q['faces'])
    me.update()
    ob = bpy.data.objects.new(name, me)
    s.collection.objects.link(ob)
    ob.color = color
    return ob
for i in range(4):
    add(A / f'base{i+1}.npz', f'底座第{i+1}块', colors[i])
camdata = bpy.data.cameras.new('预览相机')
cam = bpy.data.objects.new('预览相机', camdata)
s.collection.objects.link(cam)
camdata.type = 'ORTHO'
camdata.ortho_scale = 525
camdata.clip_end = 5000
s.camera = cam
s.render.engine = 'BLENDER_WORKBENCH'
s.render.resolution_x = 1200
s.render.resolution_y = 1000
s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
shade = s.display.shading
shade.light = 'STUDIO'
shade.color_type = 'OBJECT'
shade.show_shadows = True
shade.show_cavity = True
shade.cavity_type = 'BOTH'
shade.cavity_ridge_factor = 1.6
shade.cavity_valley_factor = 1.6
shade.background_type = 'WORLD'
s.world.color = (.88, .92, .94)
s.view_settings.view_transform = 'Standard'
def render(name, position, look):
    cam.location = position
    cam.rotation_euler = (Vector(look) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = str(R / name)
    bpy.ops.render.render(write_still=True)
render('底座俯视.png', (0, 0, 700), (0, 0, 0))
render('底座透视.png', (460, -620, 690), (0, 0, 0))
for row in json.loads((Q / '交付文件/零件清单.json').read_text(encoding='utf8'))['parts']:
    if row['id'][0] not in 'WSD':
        continue
    add(Q / 'analysis/assembly_meshes' / (row['id']+'.npz'), row['id'], (.86, .85, .81, 1))
camdata.ortho_scale = 525
render('庭院总装.png', (490, -620, 590), (0, 0, 35))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.clip_end = 5000
            space.clip_start = .05
            space.region_3d.view_distance = 600
            space.region_3d.view_location = (0, 0, 30)
            space.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
            space.shading.color_type = 'OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(R / '庭院与底座.blend'))
print('RENDERS_COMPLETE', flush=True)
