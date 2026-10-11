"""Reopen the material candidate, check preserved geometry, and render two views."""
from pathlib import Path
import bpy, bmesh, numpy as np, hashlib, json, math, sys
from mathutils import Vector

R = Path(__file__).parent
O = R / 'movie-material-v22'
W = R / 'movie-windows-v21'
baseline = json.loads((W / 'verification-v21.json').read_text(encoding='utf-8'))['characters']
integration = json.loads((O / 'integration-v22.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(O / 'Suzume_scene_movie_material_v22.blend'))
s = bpy.data.scenes['Daytime circular hotel']
bpy.context.window.scene = s
s.frame_set(72)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
characters = {}
for name, row in baseline.items():
    o = bpy.data.objects[name]
    e = o.evaluated_get(deps)
    mesh = e.to_mesh()
    a = np.empty((len(mesh.vertices), 3), np.float32)
    mesh.vertices.foreach_get('co', a.ravel())
    M = np.array(o.matrix_world)
    a = a @ M[:3, :3].T + M[:3, 3]
    e.to_mesh_clear()
    value = hashlib.sha256(np.round(a, 6).astype('<f4').tobytes()).hexdigest()
    assert value == row['worldHash'], name
    characters[name] = {'vertices': len(a), 'worldHash': value}
    partner = 'Suzume Hunyuan entered portion' if name == 'Suzume Hunyuan textured surface' else name + ' — entered portion'
    assert o.data == bpy.data.objects[partner].data
    assert all(slot.material.get('spatial_half') == 'courtyard' for slot in o.material_slots)
    assert all(slot.material.get('spatial_half') == 'otherworld' for slot in bpy.data.objects[partner].material_slots)
assert len(bpy.data.objects['Suzume Hunyuan rig'].data.bones) == 20

wall = bpy.data.objects['Solid plaster wall with two through-openings v21']
a = np.empty(len(wall.data.vertices)*3, np.float32)
wall.data.vertices.foreach_get('co', a)
assert hashlib.sha256(a.tobytes()).hexdigest() == integration['wallGeometryHash']
bm = bmesh.new()
bm.from_mesh(wall.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-4)
assert all(edge.is_manifold for edge in bm.edges)
bm.free()

F = json.loads((W / 'window-fit-v21.json').read_text(encoding='utf-8'))
fit = json.loads((R / 'movie-calibration-v20' / 'courtyard-fit-v20.json').read_text(encoding='utf-8'))
p = fit['parameters']; k = fit['depthScale']; C = np.array(fit['depthScaleCenter'])
angle = F['angle'] + p['yaw']
n = Vector((-math.sin(angle), -math.cos(angle), 0))
t = Vector((math.cos(angle), -math.sin(angle), 0))
def point(x, y):
    q = np.array([F['chordRadius']*math.sin(angle)+x*math.cos(angle)+p['translateX'],
                  F['chordRadius']*math.cos(angle)-x*math.sin(angle)+p['translateY'],
                  y*p['heightScale']+p['heightOffset']])
    return Vector(C+k*(q-C))
raytests = []
for label, x, y, expected in [
    ('oculus', F['oculus']['x'], F['oculus']['centerY'], False),
    ('rectangle', F['rectangle']['x'], F['rectangle']['bottom']+F['rectangle']['height']/2, False),
    ('wall', -F['bayWidth']*.465, 3, True),
]:
    hit = wall.ray_cast(point(x,y)+n*4, -n, distance=10)[0]
    assert hit == expected
    raytests.append({'target': label, 'wallHit': hit})
values = []
door_light = bpy.data.lights['Daylight entering the open doorway v19']
for frame in [1, 24, 72, 120]:
    s.frame_set(frame); bpy.context.view_layer.update(); values.append(door_light.energy)
assert values == [0, 0, 15, 15]
s.frame_set(72)

fill = bpy.data.objects['Soft courtyard fill on the movie facade v22']
assert abs(fill.data.energy-integration['fillLight']['powerWatts']) < .01
assert np.max(np.abs(np.array(fill.location)-integration['fillLight']['position'])) < 1e-4
assert np.max(np.abs(np.array(fill.data.color)-integration['fillLight']['color'])) < 1e-5
forward = fill.rotation_euler.to_quaternion() @ Vector((0,0,-1))
foreground = []
for name in baseline:
    ob = bpy.data.objects[name]
    dots = [float((ob.matrix_world@Vector(corner)-fill.location).dot(forward)) for corner in ob.bound_box]
    assert max(dots) < 0
    foreground.append({'object': name, 'maximumEmitterForwardDistance': max(dots)})
for name in integration['materials'].values():
    assert bpy.data.materials[name].users > 0
assert len(bpy.data.collections['Movie right facade — solid openings v21'].objects) == 72

roof = {}
for change in integration['changedRoofParts']:
    o = bpy.data.objects[change['part']]
    coords = [list(o.matrix_world@v.co) for v in o.data.vertices]
    assert np.isfinite(coords).all()
    roof[o.name.removesuffix(' v21')] = coords
(O / 'native-roof-geometry-v22.json').write_text(json.dumps(roof), encoding='utf-8')
result = {
    'revision':22, 'freshReopenVerified':True, 'characters':characters,
    'bodyHeadHairpinWorldVerticesPreserved':True, 'portalAndFootCorrectionPreserved':True,
    'wallGeometryPreserved':True, 'wallWatertightAfterWelding':True,
    'actualWindowOpenings':raytests, 'facadeParts':72,
    'doorLightPowerByFrame':dict(zip([1,24,72,120],values)),
    'foregroundEntirelyBehindEmitter':foreground,
    'oneToOneComplete':False,
}
(O / 'verification-v22.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('FACADE_REOPEN_VERIFIED', json.dumps(result), flush=True)

if '--render' in sys.argv:
    s.render.use_border = False
    s.render.use_persistent_data = True
    s.render.resolution_x = 720; s.render.resolution_y = 468; s.render.resolution_percentage = 100
    s.cycles.samples = 32; s.cycles.use_denoising = True
    s.render.filepath = str(O / 'movie-front-v22.png')
    bpy.ops.render.render(write_still=True)
    # Timeline markers otherwise replace the temporary review camera during rendering.
    s.timeline_markers.clear()
    camera = s.camera.copy(); camera.data = s.camera.data.copy()
    camera.animation_data_clear(); camera.data.animation_data_clear()
    s.collection.objects.link(camera); s.camera = camera
    target = point(0,2.8)
    camera.location = target+n*14+t*10+Vector((0,0,4))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens = 28
    s.render.filepath = str(O / 'movie-window-oblique-v22.png')
    bpy.ops.render.render(write_still=True)
