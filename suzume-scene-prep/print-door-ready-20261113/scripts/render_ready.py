import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];A=R/'analysis';data=json.loads((A/'door_manifest.json').read_text(encoding='utf8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='完整白门_背面拉杆孔';s.unit_settings.system='METRIC';collections={}
def mat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.6;return m
white=mat('白色打印件',(.78,.80,.77));metal=mat('金属轴示意_不在STL中',(.24,.28,.31))
for v in data['door_variants']:
 label=v['label'];collection=bpy.data.collections.new(label);s.collection.children.link(collection);collections[label]=collection
 for suffix in ['门框','门扇','插座板']:
  name=label+suffix;d=np.load(A/'assembly'/(name+'.npz'));mesh=bpy.data.meshes.new(name);mesh.from_pydata(d['vertices']*.001,[],d['faces']);mesh.update()
  ob=bpy.data.objects.new(name,mesh);collection.objects.link(ob);ob.data.materials.append(white)
 ax,ay=v['pivot_xy'];height=math.ceil(14.75+.76*v['outer_height_mm'])
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.001,depth=height*.001,location=(ax*.001,ay*.001,height*.0005));ob=bpy.context.object;ob.name=label+'金属轴示意_另备'
 for old in list(ob.users_collection):old.objects.unlink(ob)
 collection.objects.link(ob);ob.data.materials.append(metal)
 collection.hide_render=label!='60毫米';collection.hide_viewport=label!='60毫米'
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0004));bpy.context.object.name='预览背景';bpy.context.object.data.materials.append(mat('背景',(.22,.27,.30)))
s.world.use_nodes=True;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Strength'].default_value=.2
for name,loc,power,size in [('柔光',(-.15,-.18,.25),3,.18),('补光',(.15,.10,.20),2,.20)]:
 d=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,d);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,.015,.03))-ob.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.size=size
d=bpy.data.cameras.new('门侧检查');camera=bpy.data.objects.new('门侧检查',d);s.collection.objects.link(camera);s.camera=camera;d.type='ORTHO';d.ortho_scale=.100;d.clip_start=.001
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG'
def render(name,loc):
 camera.location=loc;camera.rotation_euler=(Vector((0,.015,.032))-camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(R/name);bpy.ops.render.render(write_still=True)
render('白门正面.png',(.075,-.18,.095));render('白门背面.png',(.1,.17,.10))
camera.location=(.075,-.18,.095);camera.rotation_euler=(Vector((0,.015,.032))-camera.location).to_track_quat('-Z','Y').to_euler()
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.clip_start=.0001;sp.clip_end=2;sp.region_3d.view_distance=.13;sp.region_3d.view_location=(0,.015,.032);sp.region_3d.view_rotation=camera.rotation_euler.to_quaternion();sp.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'白门.blend'));print('COMPLETE_DOOR_RENDER_PASS')
