import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
H = Path(__file__).parent
result = json.loads((H/'public-generation-result-2.json').read_text(encoding='utf-8'))
source = result[0]['value']
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=source)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for obj in meshes:
    obj.name = 'New Hunyuan 2mv head — untextured source'
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mat = bpy.data.materials.new('Neutral clay inspection')
    mat.diffuse_color = (.6,.64,.69,1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (.6,.64,.69,1)
    bsdf.inputs['Roughness'].default_value = .75
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
scene = bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x=600
scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.world.color=(.3,.3,.3)
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
center=Vector((0,0,0))
for pos,power,size in [((3,-4,5),450,4),((-3,-2,1),180,4),((0,4,4),350,3)]:
    data=bpy.data.lights.new('Softbox','AREA')
    data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj)
    obj.location=pos;obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Head four-view inspection')
camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera)
data.type='ORTHO';data.ortho_scale=2.3;scene.camera=camera
scene['Head model origin']='Tencent official Hunyuan3D-2mv Turbo; independent 4-view generation; no texture yet.'
bpy.ops.wm.save_as_mainfile(filepath=str(H/'new-head-untextured.blend'))
for name,angle in [('front',0),('left',math.pi/2),('back',math.pi),('right',-math.pi/2)]:
    camera.location=center+Vector((math.sin(angle)*5,-math.cos(angle)*5,0))
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(H/f'new-head-clay-{name}.png')
    bpy.ops.render.render(write_still=True)
print('NEW_HEAD_INSPECTION_COMPLETE',flush=True)
