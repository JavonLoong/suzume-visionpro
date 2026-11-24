import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];SRC=R.parent/'print-door-detail-20261113'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='门背拉杆耳_试配';s.unit_settings.system='METRIC'
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=next(x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.6;return m
white=material('白色打印件',(.78,.80,.77));orange=material('新增摇臂示意',(.76,.32,.075));metal=material('另备金属轴',(.24,.28,.31))
def add(name,path):
 d=np.load(path);mesh=bpy.data.meshes.new(name);mesh.from_pydata(d['vertices']*.001,[],d['faces']);mesh.update();ob=bpy.data.objects.new(name,mesh);s.collection.objects.link(ob);ob.data.materials.append(white);return ob
for suffix in ['门框','插座板']:add('60毫米'+suffix,SRC/'analysis/assembly'/('60毫米'+suffix+'.npz'))
leaf=add('60毫米拉杆门扇',R/'analysis/assembly/60毫米门扇.npz');leaf.data.materials.append(orange)
manifest=json.loads((R/'analysis/linkage_manifest.json').read_text(encoding='utf8'));v=next(v for v in manifest['variants'] if v['height_mm']==60);ax,ay=v['pivot_xy']
# Highlight the rear extension only; the delivered STL is one white printable part.
for polygon in leaf.data.polygons:
 c=polygon.center*1000
 if v['horn_bottom_z_mm']-.01<=c.z<=v['horn_top_z_mm']+.01 and c.y>ay+1.5:polygon.material_index=1
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.001,depth=.066,location=(ax*.001,ay*.001,.033));bpy.context.object.name='2毫米金属轴_需另备';bpy.context.object.data.materials.append(metal)
bpy.ops.mesh.primitive_plane_add(size=.5,location=(0,0,-.0004));ground=bpy.context.object;ground.data.materials.append(material('背景',(.22,.27,.3)))
s.world.use_nodes=True;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Strength'].default_value=.3
for name,loc,power,size in [('柔光',(.15,.20,.25),8,.2),('补光',(-.15,-.10,.20),5,.25)]:
 d=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,d);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,.015,.03))-ob.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.size=size
d=bpy.data.cameras.new('门背近景');camera=bpy.data.objects.new('门背近景',d);s.collection.objects.link(camera);s.camera=camera;d.type='ORTHO';d.ortho_scale=.102;d.clip_start=.001
camera.location=(.1,.17,.11);camera.rotation_euler=(Vector((0,.018,.033))-camera.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'门背拉杆耳.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'拉杆试配.blend'));print('LINKAGE_RENDER_COMPLETE')
