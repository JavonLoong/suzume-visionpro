import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'交付文件/排盘图';O.mkdir(exist_ok=True)
plates=json.loads((R/'analysis/plates.json').read_text(encoding='utf8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=768;s.render.resolution_y=768;s.render.resolution_percentage=100
shade=s.display.shading;shade.light='STUDIO';shade.color_type='OBJECT';shade.show_shadows=True;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD';s.world.color=(.9,.93,.95)
s.render.image_settings.file_format='PNG';s.view_settings.view_transform='Standard'
camera_data=bpy.data.cameras.new('排盘相机');camera=bpy.data.objects.new('排盘相机',camera_data);s.collection.objects.link(camera)
camera.location=(420,-320,530);camera.rotation_euler=(Vector((128,128,30))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=355;camera_data.clip_end=3000;s.camera=camera
bpy.ops.mesh.primitive_cube_add(size=1,location=(128,128,-1.6));bed=bpy.context.object;bed.name='256毫米打印板';bed.dimensions=(256,256,3);bed.color=(.12,.17,.19,1)
for p in plates:
 d=np.load(R/'analysis/plate_meshes'/(p['code']+'.npz'));mesh=bpy.data.meshes.new(p['code']);mesh.from_pydata(d['vertices'],[],d['faces']);mesh.update();ob=bpy.data.objects.new(p['code'],mesh);s.collection.objects.link(ob)
 for j in range(len(p['items'])):
  mat=bpy.data.materials.new(p['code']+str(j));mat.diffuse_color=(.82,.66,.36,1) if j%2==0 else (.36,.69,.74,1);mesh.materials.append(mat)
 mesh.polygons.foreach_set('material_index',d['face_groups'])
 shade.color_type='MATERIAL';bedmat=bpy.data.materials.get('底板材质')
 if bedmat is None:bedmat=bpy.data.materials.new('底板材质');bedmat.diffuse_color=(.12,.17,.19,1);bed.data.materials.append(bedmat)
 s.render.filepath=str(O/(p['code']+'.png'));bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
 print('RENDERED',p['code'],flush=True)
