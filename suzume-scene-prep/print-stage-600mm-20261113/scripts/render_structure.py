import bpy, json, math, numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];A=R/'analysis';Q=R.parent/'print-white-quality-20261030'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='600毫米庭院展示台_结构样机'
s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS'
manifest=json.loads((A/'structure_manifest.json').read_text(encoding='utf8'))
groups={}
def add(name,file,color,group,location=(0,0,0),rot=(0,0,0)):
    d=np.load(file);me=bpy.data.meshes.new(name);me.from_pydata(d['vertices'],[],d['faces']);me.update()
    ob=bpy.data.objects.new(name,me);s.collection.objects.link(ob);ob.color=(*color,1)
    ob.location=location;ob.rotation_euler=[math.radians(v) for v in rot]
    groups.setdefault(group,[]).append(ob);return ob
def part(name,color,group,location=(0,0,0),rot=(0,0,0)):
    return add(name,A/'assembly'/(name+'.npz'),color,group,location,rot)
basecolor=(.72,.76,.77);footcolor=(.32,.43,.46);doorcolor=(.90,.85,.70)
for row in manifest['parts']:
    if row['id'].startswith('底板'):part(row['id'],basecolor,'deck')
for i in range(8):part('出线围边_打印1件' if i==6 else '围边_打印7件',basecolor,'skirts',rot=(0,0,45*i))
for x,y in manifest['positions']['post_centers']:part('中央支脚_打印4件',footcolor,'posts',(x,y,0))
for x,y,angle in manifest['positions']['bridge_points']:part('接缝压条_打印12件',footcolor,'bridges',(x,y,0),(0,0,angle))
for row in json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts']:
    if row['id'][0] in 'WS':add(row['id'],Q/'analysis/assembly_meshes'/(row['id']+'.npz'),(.62,.67,.67),'courtyard')
part('主门插座板',(.33,.58,.61),'door')
part('主门门框',doorcolor,'door')
leaf=part('主门门扇',doorcolor,'door')
# Rotate the leaf around the actual shaft, not its bounding-box center.
for v in leaf.data.vertices:
    x,y=v.co.x-20,v.co.y-35;a=math.radians(65)
    v.co.x=20+x*math.cos(a)-y*math.sin(a);v.co.y=35+x*math.sin(a)+y*math.cos(a)
for name in ('门轴_打印1件','门轴承托垫圈','舵盘接头','舵盘夹片'):
    part(name,(.82,.48,.23) if '轴' in name else (.38,.43,.48),'drive',(20,35,8),(0,0,0 if name=='门轴承托垫圈' else 65))
part('舵机升降托架',(.25,.48,.56),'drive',(0,20,-52))
for y in (-2,48):part('舵机滑动横梁_打印2件',(.25,.48,.56),'drive',(0,y,-48))
for x in (-75,75):
    for y in (-24,64):
        part('升降吊耳_打印4件',(.4,.46,.49),'drive',(x,y,0),(0,0,180 if x<0 else 0))
        part('侧向垫圈_打印4件',(.8,.55,.28),'drive',(-75 if x<0 else 71,y,-42),(0,90,0))

def box(name,center,size,color,group):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);ob=bpy.context.object;ob.name=name;ob.dimensions=size;ob.color=(*color,1);groups.setdefault(group,[]).append(ob);return ob
# Explicit envelope only, not a claim that a specific physical servo fits.
box('舵机外形占位_待实测',(20,23,-58),(22,40,40),(.62,.24,.21),'placeholder')
box('舵盘占位_待实测',(20,35,-23),(24,8,3),(.6,.34,.25),'placeholder')

camera_data=bpy.data.cameras.new('结构相机');camera=bpy.data.objects.new('结构相机',camera_data);s.collection.objects.link(camera)
camera_data.type='ORTHO';camera_data.clip_end=5000;s.camera=camera
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100
shade=s.display.shading;shade.light='STUDIO';shade.color_type='OBJECT';shade.show_shadows=True;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD'
s.world.color=(.91,.94,.96);s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG'
def render(file,eye,target,scale):
    camera.location=eye;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=scale
    s.render.filepath=str(R/file);bpy.ops.render.render(write_still=True)
render('整体装配.png',(740,-900,740),(0,0,35),790)
render('门高10厘米.png',(740,-900,740),(0,0,35),790)
for label,ax,h in [('小门',15,8),('大门',25,12)]:
    for ob in groups['door']:ob.hide_render=True
    extras=[]
    for suffix in ['插座板','门框','门扇']:
        ob=part(label+suffix,doorcolor if suffix!='插座板' else (.33,.58,.61),'comparison');extras.append(ob)
        if suffix=='门扇':
            for v in ob.data.vertices:
                x,y=v.co.x-ax,v.co.y-35;a=math.radians(65)
                v.co.x=ax+x*math.cos(a)-y*math.sin(a);v.co.y=35+x*math.sin(a)+y*math.cos(a)
    render(f'门高{h}厘米.png',(740,-900,740),(0,0,35),790)
    for ob in extras:ob.hide_render=True
for ob in groups['door']:ob.hide_render=False

for key in ('skirts','posts','bridges','drive','placeholder'): 
    for ob in groups[key]:ob.hide_render=True
render('嵌槽与门_俯视.png',(0,-70,1100),(0,0,0),790)
for ob in groups['courtyard']+groups['door']:ob.hide_render=True
render('底板嵌槽.png',(0,0,1100),(0,0,0),790)

for key in ('deck','courtyard','skirts','posts','bridges'):
    for ob in groups[key]:ob.hide_render=True
for key in ('door','drive','placeholder'):
    for ob in groups[key]:ob.hide_render=False
render('门轴与下置舵机.png',(235,-350,205),(10,30,15),330)

for key in groups:
    for ob in groups[key]:ob.hide_render=(key=='comparison');ob.hide_viewport=(key=='comparison')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_end=5000;sp.clip_start=.1;sp.region_3d.view_distance=850;sp.region_3d.view_location=(0,0,35);sp.shading.color_type='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'600毫米庭院结构样机.blend'))
print('STRUCTURE_RENDERS_COMPLETE',flush=True)
