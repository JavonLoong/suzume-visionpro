import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];O=R/'交付文件';A=R/'analysis'/'assembly_meshes'
d=json.loads((O/'零件清单.json').read_text(encoding='utf8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='400毫米庭院_分件总装';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001;scene.unit_settings.length_unit='MILLIMETERS'
colors={'B':(.15,.44,.5,1),'W':(.7,.72,.65,1),'S':(.33,.19,.09,1),'D':(.92,.92,.84,1)}
for row in d['parts']:
 if row['id'][0] not in colors:continue
 x=np.load(A/(row['id']+'.npz'));me=bpy.data.meshes.new(row['id']);me.from_pydata(x['vertices'],[],x['faces']);me.update();ob=bpy.data.objects.new(row['id'],me);scene.collection.objects.link(ob);ob.color=colors[row['id'][0]]
 ob['零件编号']=row['id'];ob['打印数量']=row['quantity'];ob['模型单位']='毫米';ob['外径基准']='400 mm'
camdata=bpy.data.cameras.new('总装相机');cam=bpy.data.objects.new('总装相机',camdata);scene.collection.objects.link(cam);cam.location=(490,-620,590);cam.rotation_euler=(Vector((0,0,30))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=510;camdata.clip_end=3000;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
shade=scene.display.shading;shade.light='STUDIO';shade.color_type='OBJECT';shade.show_shadows=True;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD';scene.world.color=(.87,.9,.92)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(O/'总装核对图.png')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.clip_end=5000;area.spaces.active.clip_start=.05;area.spaces.active.region_3d.view_distance=600;area.spaces.active.region_3d.view_location=(0,0,25);area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion();area.spaces.active.shading.color_type='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'铃芽庭院_400mm_分件总装.blend'))
bpy.ops.render.render(write_still=True)
print('ASSEMBLY_SAVED',flush=True)
