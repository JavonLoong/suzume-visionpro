import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
out=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
d=np.load(out/'无中心盘底座_原装配坐标.npz')
m=bpy.data.meshes.new('一体底座网格');m.from_pydata(d['vertices'],[],d['faces']);m.update()
o=bpy.data.objects.new('无中心盘一体底座_500x500x14毫米',m);bpy.context.collection.objects.link(o);o.color=(.55,.72,.79,1)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS'
s.world.color=(.94,.95,.97);s.view_settings.view_transform='Standard'
sh=s.display.shading;sh.light='STUDIO';sh.color_type='OBJECT';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
cd=bpy.data.cameras.new('预览相机');cam=bpy.data.objects.new('预览相机',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.clip_end=5000
def shot(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
shot('01_一体底座俯视',(0,0,700),(0,0,0),660)
shot('02_中央开口与承托台阶',(90,-130,180),(0,0,4),180)
shot('03_底面贯通圆口',(360,-460,-600),(0,0,0),660)
shot('00_一体底座整体',(430,-530,600),(0,0,0),620)
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.clip_end=5000;a.spaces.active.clip_start=.05;a.spaces.active.region_3d.view_distance=650;a.spaces.active.region_3d.view_location=(0,0,0);a.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion();a.spaces.active.shading.color_type='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'无中心盘一体底座_可编辑.blend'))
