import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];A=R/'analysis';Q=R.parent/'print-white-quality-20261030'
data=json.loads((A/'slim_manifest.json').read_text(encoding='utf8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='薄底座与原型细门_外观修订';s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001
groups={}
def add(name,file,color,group,location=(0,0,0),rotation=0,bevel=False):
    d=np.load(file);m=bpy.data.meshes.new(name);m.from_pydata(d['vertices'],[],d['faces']);m.update()
    ob=bpy.data.objects.new(name,m);s.collection.objects.link(ob);ob.color=(*color,1);ob.location=location;ob.rotation_euler[2]=math.radians(rotation);groups.setdefault(group,[]).append(ob)
    if bevel:
        mod=ob.modifiers.new('细小边缘倒角_预览','BEVEL');mod.width=.08;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=math.radians(35);mod.use_clamp_overlap=True
    return ob
for row in data['parts']:
    if row['id'].startswith('薄底板'):add(row['id'],A/'assembly'/(row['id']+'.npz'),(.89,.93,.94),'base')
for x,y,angle in data['bridges']:add('接缝条',A/'assembly/底部接缝条_打印12件.npz',(.7,.73,.74),'base',(x,y,0),angle)
for x,y in data['foot_positions']:add('隐藏脚垫',A/'assembly/隐藏脚垫_打印12件.npz',(.12,.15,.16),'base',(x,y,0))
for row in json.loads((Q/'交付文件/零件清单.json').read_text(encoding='utf8'))['parts']:
    if row['id'][0] in 'WS':add(row['id'],Q/'analysis/assembly_meshes'/(row['id']+'.npz'),(.91,.93,.92),'courtyard')
for variant in data['door_variants']:
    label=variant['label'];ax,ay=variant['pivot_xy']
    for suffix in ['插座板','门框','门扇']:
        ob=add(label+suffix,A/'assembly'/(label+suffix+'.npz'),(1,.98,.90) if suffix!='插座板' else (.89,.93,.94),label,bevel=suffix!='插座板')
        if suffix=='门扇':
            for v in ob.data.vertices:
                x,y=v.co.x-ax,v.co.y-ay;a=math.radians(35)
                v.co.x=ax+x*math.cos(a)-y*math.sin(a);v.co.y=ay+x*math.sin(a)+y*math.cos(a)
        ob.hide_render=True;ob.hide_viewport=label!='40毫米'
camdata=bpy.data.cameras.new('修订相机');cam=bpy.data.objects.new('修订相机',camdata);s.collection.objects.link(cam);camdata.type='ORTHO';camdata.clip_end=5000;s.camera=cam
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100
sh=s.display.shading;sh.light='STUDIO';sh.color_type='OBJECT';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='SCREEN';sh.curvature_ridge_factor=1.2;sh.curvature_valley_factor=.45;sh.background_type='WORLD'
available=[x.name for x in bpy.context.preferences.studio_lights]
if 'paint.sl' in available:sh.studio_light='paint.sl'
s.world.color=(.93,.95,.96);s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG'
# Render the actual geometry at metre scale under soft area lights, rather than
# over-bright viewport edge highlighting.
for engine in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try:s.render.engine=engine;break
    except Exception:pass
s.unit_settings.scale_length=1
for ob in list(s.objects):
    if ob.type!='MESH':continue
    ob.scale=(.001,.001,.001);ob.location*=.001
    mat=bpy.data.materials.new(ob.name+'_实体材质');mat.use_nodes=True
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=tuple(float(c)*.8 for c in ob.color[:3])+(1,);bsdf.inputs['Roughness'].default_value=.58
    ob.data.materials.append(mat)
s.world.use_nodes=True;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.85,.90,.95,1);bg.inputs['Strength'].default_value=.35
for name,pos,power,size in [('主柔光',(-.45,-.55,1.1),95,.8),('补光',(.6,-.1,.6),35,.7),('后柔光',(-.1,.6,.9),110,.7)]:
    ld=bpy.data.lights.new(name,'AREA');lo=bpy.data.objects.new(name,ld);s.collection.objects.link(lo);lo.location=pos;lo.rotation_euler=(Vector((0,0,0))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0055));ground=bpy.context.object;ground.name='仅渲染用背景'
mat=bpy.data.materials.new('背景浅灰');mat.use_nodes=True;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=(.79,.82,.84,1);bsdf.inputs['Roughness'].default_value=.8;ground.data.materials.append(mat)
camdata.clip_start=.002;camdata.clip_end=5;s.view_settings.view_transform='AgX'
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.max_bounces=5
s.cycles.adaptive_threshold=.08
for ob in s.objects:
    if ob.type=='LIGHT':ob.data.energy*=.20
bg.inputs['Strength'].default_value=.18
bsdf.inputs['Base Color'].default_value=(.22,.26,.30,1)
def render(filename,eye,target,scale):
    cam.location=Vector(eye)*.001;cam.rotation_euler=(Vector(target)*.001-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale*.001;s.render.filepath=str(R/filename);bpy.ops.render.render(write_still=True)
for variant in data['door_variants']:
    label=variant['label']
    for ob in groups[label]:ob.hide_render=False
    render(label+'整体.png',(740,-900,650),(0,0,25),750)
    for ob in groups[label]:ob.hide_render=True
for ob in groups['40毫米']:ob.hide_render=False
for ob in groups['base']+groups['courtyard']:ob.hide_render=True
groups['40毫米'][0].hide_render=True
ground.hide_render=True
render('四厘米白门细节.png',(70,-110,68),(0,13,27),74)
ground.hide_render=False
for ob in groups['base']+groups['courtyard']:ob.hide_render=False
groups['40毫米'][0].hide_render=False
cam.location=Vector((740,-900,650))*.001;cam.rotation_euler=(Vector((0,0,25))*.001-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=.75
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_end=5;sp.clip_start=.001;sp.region_3d.view_distance=.8;sp.region_3d.view_location=(0,0,.025);sp.shading.color_type='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'细门与薄底座.blend'))
print('SLIM_PREVIEW_COMPLETE',flush=True)
