import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1].parent/'print-packed-stl-20261030';A=R/'analysis'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
shade=s.display.shading;shade.light='STUDIO';shade.color_type='MATERIAL';shade.show_shadows=True;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD';s.world.color=(.9,.93,.95);s.view_settings.view_transform='Standard'
camera_data=bpy.data.cameras.new('排盘相机');camera=bpy.data.objects.new('排盘相机',camera_data);s.collection.objects.link(camera)
camera.location=(385,-335,570);camera.rotation_euler=(Vector((128,128,32))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=375;camera_data.clip_end=3000;s.camera=camera
bpy.ops.mesh.primitive_cube_add(size=1,location=(128,128,-1.6));bed=bpy.context.object;bed.dimensions=(256,256,3);mat=bpy.data.materials.new('打印板');mat.diffuse_color=(.12,.17,.19,1);bed.data.materials.append(mat)
colors=[(.83,.74,.53,1),(.36,.69,.74,1),(.65,.78,.63,1),(.74,.62,.81,1),(.80,.56,.48,1)]
layout=json.loads((A/'layout-final.json').read_text(encoding='utf8'))
for i,board in enumerate(layout,1):
 q=np.load(A/f'plate{i}.npz');mesh=bpy.data.meshes.new(str(i));mesh.from_pydata(q['vertices'],[],q['faces']);mesh.update();ob=bpy.data.objects.new(str(i),mesh);s.collection.objects.link(ob)
 for j in range(len(board)):
  mat=bpy.data.materials.new(f'{i}_{j}');mat.diffuse_color=colors[j%len(colors)];mesh.materials.append(mat)
 mesh.polygons.foreach_set('material_index',q['face_groups']);s.render.filepath=str(A/f'第{i}盘.png');bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
