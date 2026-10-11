import bpy, numpy as np, subprocess, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=Path(__file__).parent/'head-hunyuan-v1'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(H/'new-head-display.glb'))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.context.view_layer.objects.active=obj
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
obj.name='Suzume independent Hunyuan head'
mod=obj.modifiers.new('Remove reconstruction surface noise','SMOOTH');mod.factor=.25;mod.iterations=3
bpy.ops.object.modifier_apply(modifier=mod.name)
mesh=obj.data
P=np.empty((len(mesh.vertices),3),np.float32);N=np.empty_like(P)
mesh.vertices.foreach_get('co',P.ravel());mesh.vertices.foreach_get('normal',N.ravel())
np.savez(H/'head-paint-geometry.npz',positions=P,normals=N)
if '--prepare' in sys.argv:
    raise SystemExit(0)
if '--colors-exist' not in sys.argv:
    raise RuntimeError('Run --prepare, then sample_head_colors.py, then --colors-exist in separate processes to keep memory bounded.')
colors=np.load(H/'head-vertex-colors-linear.npy')
attribute=mesh.color_attributes.new(name='Head Four View Color',type='FLOAT_COLOR',domain='POINT')
rgba=np.ones((len(P),4),np.float32);rgba[:,:3]=colors
attribute.data.foreach_set('color',rgba.ravel())
mesh.color_attributes.active_color_index=0
mesh.color_attributes.render_color_index=0
mat=bpy.data.materials.new('Suzume head — four view color');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85
bsdf.inputs['Specular IOR Level'].default_value=.15
node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name=attribute.name
mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
mesh.materials.clear();mesh.materials.append(mat)
for face in mesh.polygons:face.use_smooth=True
obj['source']='Tencent Hunyuan3D-2mv; four-view geometry. Local four-view vertex color projection.'
obj['review_status']='Candidate for visual inspection; not yet attached to scene.'
surface=BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
for name,start,end,color in [
    ('Left gold hairpin',(.30,-.38,.585),(.415,-.232,.674),(.62,.34,.055,1)),
    ('Left red hairpin diagonal',(.32,-.31,.375),(.425,-.18,.57),(.38,.065,.055,1)),
    ('Left red hairpin crossbar',(.30,-.345,.47),(.445,-.15,.45),(.38,.065,.055,1))]:
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=2
    curve.bevel_depth=.013;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');spline.points.add(12)
    first,normal_a,_,_=surface.find_nearest(Vector(start))
    last,normal_b,_,_=surface.find_nearest(Vector(end))
    outward=(normal_a+normal_b).normalized()
    for i,point in enumerate(spline.points):
        t=i/12
        co=first.lerp(last,t)+outward*(.06+math.sin(math.pi*t)*.03)
        point.co=(*co,1)
    pin=bpy.data.objects.new(name,curve);bpy.context.scene.collection.objects.link(pin)
    material=bpy.data.materials.new(name+' enamel');material.use_nodes=True
    shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=color;shader.inputs['Roughness'].default_value=.45
    curve.materials.append(material)
    pin.select_set(True)
bpy.ops.object.convert(target='MESH')
del surface,P,N,colors,rgba
bpy.ops.export_scene.gltf(filepath=str(H/'Suzume-head-candidate.glb'),export_format='GLB',use_selection=True,export_animations=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
scene.render.resolution_x=480;scene.render.resolution_y=560;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.5,.5,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
center=Vector((0,0,0))
for pos,power,size in [((3,-4,5),300,4),((-3,-2,1),130,4),((0,4,4),220,3)]:
    d=bpy.data.lights.new('Head softbox','AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Head inspection');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=2.3
bpy.ops.wm.save_as_mainfile(filepath=str(H/'new-head-colored-candidate.blend'))
for label,a in [('front',0),('left',math.pi/2),('back',math.pi),('right',-math.pi/2),('threequarter',math.pi/4)]:
    cam.location=center+Vector((math.sin(a)*5,-math.cos(a)*5,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(H/f'new-head-color-{label}.png');bpy.ops.render.render(write_still=True)
print('COLORED_HEAD_CANDIDATE',len(mesh.vertices),len(mesh.polygons),flush=True)
