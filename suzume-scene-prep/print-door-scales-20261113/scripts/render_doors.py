import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];A=R/'analysis';B=R.parent/'print-stage-500mm-20261113';BA=B/'analysis';Q=R.parent/'print-white-quality-20261030'
data=json.loads((A/'door_manifest.json').read_text(encoding='utf8'));base=json.loads((BA/'slim_manifest.json').read_text(encoding='utf8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='50厘米庭院_三档白门';s.unit_settings.system='METRIC';s.unit_settings.scale_length=1;groups={}
collections={}
def add(name,file,color,group,location=(0,0,0),rotation=0):
    if group not in collections:
        c=bpy.data.collections.new(group);s.collection.children.link(c);collections[group]=c
    d=np.load(file);m=bpy.data.meshes.new(name);m.from_pydata(d['vertices'],[],d['faces']);m.update()
    ob=bpy.data.objects.new(name,m);collections[group].objects.link(ob);ob.scale=(.001,.001,.001);ob.location=Vector(location)*.001;ob.rotation_euler[2]=math.radians(rotation)
    mat=bpy.data.materials.new(name+'_白模');mat.use_nodes=True;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=tuple(c*.8 for c in color)+(1,);bsdf.inputs['Roughness'].default_value=.58;ob.data.materials.append(mat);ob.color=(*color,1)
    groups.setdefault(group,[]).append(ob);return ob
for row in base['parts']:
    if row['id'].startswith('薄底板'):add(row['id'],BA/'assembly'/(row['id']+'.npz'),(.89,.93,.94),'底座')
for x,y,a in base['bridges']:add('接缝条',BA/'assembly/底部接缝条_打印12件.npz',(.7,.73,.74),'底座',(x,y,0),a)
for x,y in base['foot_positions']:add('脚垫',BA/'assembly/隐藏脚垫_打印12件.npz',(.12,.15,.16),'底座',(x,y,0))
for row in json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts']:
    if row['id'][0] in 'WS':add(row['id'],Q/'analysis/assembly_meshes'/(row['id']+'.npz'),(.91,.93,.92),'庭院')
for v in data['door_variants']:
    label=v['label'];ax,ay=v['pivot_xy']
    for suffix in ['插座板','门框','门扇']:
        ob=add(label+suffix,A/'assembly'/(label+suffix+'.npz'),(1,.98,.90) if suffix!='插座板' else (.89,.93,.94),label)
        if suffix!='插座板':
            mod=ob.modifiers.new('预览微倒角','BEVEL');mod.width=.08;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=math.radians(35);mod.use_clamp_overlap=True
        if suffix=='门扇':
            for p in ob.data.vertices:
                x,y=p.co.x-ax,p.co.y-ay;a=math.radians(35);p.co.x=ax+x*math.cos(a)-y*math.sin(a);p.co.y=ay+x*math.sin(a)+y*math.cos(a)
        ob.hide_render=True
camera=bpy.data.cameras.new('同机位对比');cam=bpy.data.objects.new('同机位对比',camera);s.collection.objects.link(cam);camera.type='ORTHO';camera.clip_start=.002;camera.clip_end=5;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.max_bounces=5;s.cycles.adaptive_threshold=.08
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.world.use_nodes=True;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.85,.90,.95,1);bg.inputs['Strength'].default_value=.18
for name,pos,power,size in [('主柔光',(-.45,-.55,1.1),19,.8),('补光',(.6,-.1,.6),7,.7),('后柔光',(-.1,.6,.9),22,.7)]:
    ld=bpy.data.lights.new(name,'AREA');lo=bpy.data.objects.new(name,ld);s.collection.objects.link(lo);lo.location=pos;lo.rotation_euler=(Vector((0,0,0))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0055));ground=bpy.context.object;ground.name='仅渲染用背景';mat=bpy.data.materials.new('浅灰背景');mat.use_nodes=True;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=(.22,.26,.30,1);bsdf.inputs['Roughness'].default_value=.8;ground.data.materials.append(mat)
def pose(eye,target,scale):
    cam.location=Vector(eye)*.001;cam.rotation_euler=(Vector(target)*.001-cam.location).to_track_quat('-Z','Y').to_euler();camera.ortho_scale=scale*.001
def render(name,eye,target,scale,shape=(1400,1100)):
    pose(eye,target,scale);s.render.resolution_x,s.render.resolution_y=shape;s.render.filepath=str(R/name);bpy.ops.render.render(write_still=True)
for v in data['door_variants']:
    if '--lineup-only' in sys.argv:break
    for ob in groups[v['label']]:ob.hide_render=False
    render(f"{v['factor']:g}倍整体.png",(740,-900,650),(0,0,25),650)
    for ob in groups[v['label']]:ob.hide_render=True
# Compare the real geometry under one camera and one scale; no image resizing.
for ob in groups['底座']+groups['庭院']:ob.hide_render=True
ground.location.z=-.0005
pose((0,-260,155),(0,12,32),265)
labels=[]
for i,v in enumerate(data['door_variants']):
    x=(i-1)*78
    for ob in groups[v['label']]:ob.location.x=x*.001;ob.hide_render=False
    curve=bpy.data.curves.new('尺寸标注','FONT');curve.body=f"{v['factor']:g}x  /  {v['outer_height_mm']} mm";curve.align_x='CENTER';curve.size=.005
    ob=bpy.data.objects.new('尺寸标注',curve);s.collection.objects.link(ob);ob.location=(x*.001,-.028,.006);ob.rotation_euler=cam.rotation_euler.copy()
    mat=bpy.data.materials.new('标注深灰');mat.use_nodes=True;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=(.012,.02,.028,1);bsdf.inputs['Roughness'].default_value=.8;ob.data.materials.append(mat);labels.append(ob)
render('三档尺寸对比.png',(0,-260,155),(0,12,32),265,(1800,1000))
for ob in labels:ob.hide_render=True;ob.hide_viewport=True
ground.location.z=-.0055
for ob in groups['底座']+groups['庭院']:ob.hide_render=False
for v in data['door_variants']:
    for ob in groups[v['label']]:ob.location.x=0;ob.hide_render=v['label']!='60毫米';ob.hide_viewport=v['label']!='60毫米'
pose((740,-900,650),(0,0,25),650);s.render.resolution_x,s.render.resolution_y=1400,1100
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_end=5;sp.clip_start=.001;sp.region_3d.view_distance=.75;sp.region_3d.view_location=(0,0,.025);sp.shading.color_type='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'三档白门.blend'))
print('THREE_DOORS_RENDER_COMPLETE',flush=True)
