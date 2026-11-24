import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parents[1];A=O/'analysis/assembly';R=O/'预览';R.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS';s.world.color=(.92,.94,.97);s.view_settings.view_transform='Standard'
sh=s.display.shading;sh.light='STUDIO';sh.color_type='OBJECT';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
cd=bpy.data.cameras.new('预览相机');cam=bpy.data.objects.new('预览相机',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.clip_start=.01;cd.clip_end=2000
objs={}
for p in A.glob('*.npz'):
 d=np.load(p);m=bpy.data.meshes.new(p.stem);m.from_pydata(d['vertices'],[],d['faces']);m.update();ob=bpy.data.objects.new(p.stem,m);s.collection.objects.link(ob);objs[p.stem]=ob
 ob.color=(.82,.84,.86,1)
 if p.stem.startswith('02'):ob.color=(.96,.96,.94,1)
 if '实心杆' in p.stem:ob.color=(.92,.44,.10,1)
 if '中心盘' in p.stem:ob.color=(.37,.51,.61,1)
 if p.stem.startswith('剖视'):ob.hide_render=True;ob.hide_viewport=True
leaf=objs['02_内藏轴门扇'];frame=objs['01_门框与居中底脚'];rod=objs['参考_1毫米实心杆_非打印件'];centre=objs['参考_原116毫米中心盘_不重复打印']
pivot=bpy.data.objects.new('门扇旋转轴',None);s.collection.objects.link(pivot);pivot.location=(12.15,-.75,0);leaf.parent=pivot;leaf.matrix_parent_inverse=pivot.matrix_world.inverted() if False else __import__('mathutils').Matrix.Translation((-12.15,.75,0))
def shot(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;s.render.filepath=str(R/(name+'.png'));bpy.ops.render.render(write_still=True)
shot('01_关闭_正面',(95,-160,95),(0,0,31),125)
pivot.rotation_euler.z=math.radians(-90)
shot('02_打开90度',(95,-160,95),(0,0,31),125)
pivot.rotation_euler.z=0
shot('03_关闭_背面',(-85,155,90),(0,0,31),125)
centre.hide_render=True;frame.hide_render=True
shot('04_门扇内藏轴侧',(95,-160,85),(2,0,35),78)
frame.hide_render=False;centre.hide_render=False
# Side inspection with section clipping is represented by explicit clipped meshes only.
shot('05_轴侧近看',(90,-140,70),(12,0,36),70)
centre.hide_render=True;frame.hide_render=True;leaf.hide_render=True
for key in ['剖视_门框','剖视_门扇']:objs[key].hide_render=False;objs[key].hide_viewport=False
objs['剖视_门扇'].color=(.78,.88,.96,1)
shot('06_真实剖切_橙色为1毫米杆',(90,-170,70),(4,0,31),112)
for key in ['剖视_门框','剖视_门扇']:objs[key].hide_render=True;objs[key].hide_viewport=True
centre.hide_render=False;frame.hide_render=False;leaf.hide_render=False
shot('01_关闭_正面',(95,-160,95),(0,0,31),125)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.clip_start=.01;sp.clip_end=2000;sp.region_3d.view_distance=145;sp.region_3d.view_location=(0,0,30);sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion();sp.shading.color_type='OBJECT'
pivot.rotation_euler.z=0;pivot.keyframe_insert('rotation_euler',frame=1);pivot.rotation_euler.z=math.radians(-105);pivot.keyframe_insert('rotation_euler',frame=64);s.frame_start=1;s.frame_end=64;s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'白门_内藏1毫米轴_门侧试配.blend'))
