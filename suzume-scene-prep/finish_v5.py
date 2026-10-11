import bpy,math,json,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v5'
if not (OUT/'Volume_cloud_trial.blend').exists():shutil.copyfile(OUT/'Suzume_v5.blend',OUT/'Volume_cloud_trial.blend')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Suzume_v5.blend'))
s=bpy.context.scene;s.camera=bpy.data.objects['Reference_camera_630x750']
clouds=bpy.data.collections.get('V5_Volumetric_clouds');clouds.hide_render=True;clouds.hide_viewport=True
w=bpy.data.worlds.new('V5 reference-inspired generated cloud panorama');s.world=w;w.use_nodes=True;n=w.node_tree.nodes;n.clear();lk=w.node_tree.links
o=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');env=n.new('ShaderNodeTexEnvironment');im=bpy.data.images.load(str(OUT/'sky_generated_v5.png'));im.pack();env.image=im
coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeMapping');mapping.inputs['Rotation'].default_value[2]=math.radians(-35);mapping.inputs['Scale'].default_value=(1,1,1);lk.new(coord.outputs['Generated'],mapping.inputs['Vector']);lk.new(mapping.outputs[0],env.inputs['Vector'])
lk.new(env.outputs[0],bg.inputs[0]);bg.inputs['Strength'].default_value=.85;lk.new(bg.outputs[0],o.inputs[0])
water=bpy.data.materials['Clear turquoise water']
for node in water.node_tree.nodes:
 if node.type=='BUMP':node.inputs['Distance'].default_value=.012;node.inputs['Strength'].default_value=.25
s.cycles.samples=48;s.render.resolution_x=1008;s.render.resolution_y=1200;s.render.filepath=str(OUT/'front_v5.png');s.view_settings.view_transform='Standard';s.view_settings.exposure=.3
s['sky_source']='Generated with built-in imagegen using the official reference sky for style. Environment orientation is art-directed; not original movie clouds.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v5.blend'));bpy.ops.render.render(write_still=True)
bpy.ops.object.camera_add(location=(3,-3.5,2.6));c=bpy.context.object;c.name='V5 detail inspection';c.rotation_euler=(Vector((1,5,1.1))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=32;s.camera=c;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.filepath=str(OUT/'detail_v5.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['Reference_camera_630x750'];s.render.resolution_x=1008;s.render.resolution_y=1200;s.render.filepath=str(OUT/'front_v5.png');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v5.blend'))
(OUT/'status.json').write_text(json.dumps({'rebuilt':['visible solid masonry','arched wall openings','irregular submerged paving','non-periodic water ripples'],'sky':'Packed reference-inspired imagegen panorama; procedural and HDR experiments rejected','sky_source':'sky_generated_v5.png','generation_prompt':'sky_prompt.txt','environment_in_glb':False,'unverified':['exact original cloud shapes','depths','rear layout','full 1:1 accuracy']},ensure_ascii=False,indent=2),encoding='utf-8')
print('V5_FINAL_READY')
