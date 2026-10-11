import bpy, json, math
from pathlib import Path
from mathutils import Vector

R=Path(__file__).parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'Suzume_Hunyuan31_original.glb'))
s=bpy.context.scene
objects=[o for o in s.objects if o.type=='MESH']
points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
center=(lo+hi)*.5;h=hi.z-lo.z
for o in objects:o.name='Suzume_Hunyuan31_Original'
texture_names=['texture_pbr_20250901_normal','texture_pbr_20250901','texture_pbr_20250901_metallic-texture_pbr_20250901_roughness']
for i,name in enumerate(texture_names):
 im=bpy.data.images.get(name)
 if im:
  color_space=im.colorspace_settings.name
  replacement=bpy.data.images.load(str(R/f'texture-{i}.png'),check_existing=False)
  replacement.colorspace_settings.name=color_space;replacement.pack()
  im.user_remap(replacement);bpy.data.images.remove(im);replacement.name=name
s.render.engine='CYCLES';s.cycles.samples=24
s.render.resolution_x=700;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
s.world=bpy.data.worlds.new('Character inspection studio');s.world.use_nodes=True
wn=s.world.node_tree.nodes;wn.clear();bg=wn.new('ShaderNodeBackground');out=wn.new('ShaderNodeOutputWorld');s.world.node_tree.links.new(bg.outputs[0],out.inputs[0])
bg.inputs[0].default_value=(.8,.8,.8,1);bg.inputs[1].default_value=.65
for pos,power,size in [((2,-3,4),140,3),((-3,-1,2),80,3),((0,3,3),120,2)]:
 d=bpy.data.lights.new('Soft studio area','AREA');d.energy=power;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=Vector(pos)*h
 o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
c=bpy.data.cameras.new('InspectionCamera');cam=bpy.data.objects.new('InspectionCamera',c);s.collection.objects.link(cam);s.camera=cam
c.type='ORTHO';c.ortho_scale=h*1.12
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_Hunyuan31.blend'))
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_Hunyuan31.blend'))
s=bpy.context.scene;cam=s.camera
report={'boundsBlender':[list(lo),list(hi)],'height':h,'meshObjects':len(objects),'images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'hasData':im.has_data} for im in bpy.data.images if im.size[0]],'source':'Hunyuan 3D 3.1 four-view generation','rigged':False,'reopenedBeforeRendering':True}
assert all(i['packed'] and i['hasData'] for i in report['images'])
(R/'blender-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for name,angle in [('front',0),('left',-math.pi/2),('back',math.pi),('right',math.pi/2)]:
 cam.location=center+Vector((math.sin(angle)*h*3,-math.cos(angle)*h*3,0))
 cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(R/('model-'+name+'.png'));bpy.ops.render.render(write_still=True)
cam.location=center+Vector((0,-h*3,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
s['asset_status']='Original Hunyuan character; needs rigging and pose correction before scene integration.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_Hunyuan31.blend'))
print('CHARACTER_INSPECTION_COMPLETE',json.dumps(report))
