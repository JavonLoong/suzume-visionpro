import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-through-v12.blend'))
day=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=day
with bpy.data.libraries.load(str(R/'Suzume_Hunyuan31_rigged.blend'),link=False) as (src,dst):
 dst.objects=['Suzume Hunyuan rig','Suzume Hunyuan textured surface']
collection=bpy.data.collections.new('Suzume — Hunyuan four-view reconstruction');day.collection.children.link(collection)
for ob in dst.objects:collection.objects.link(ob)
rig=bpy.data.objects['Suzume Hunyuan rig'];mesh=bpy.data.objects['Suzume Hunyuan textured surface']
rig.location=(-.15,.75,.055);rig.rotation_euler[2]=math.pi;rig.scale=(2.55,)*3
bpy.context.view_layer.update()
spec=json.loads((R/'rig-audit.json').read_text())['rig']
rest={n:[Vector(a),Vector(b),p] for n,(a,b,p) in spec.items()}
offset=Vector((0,0,-.035));poses={n:[a+offset,b+offset] for n,(a,b,p) in rest.items()}
poses['root']=[rest['root'][0],rest['root'][1]]

def solve(a,c,l1,l2,pole):
 d=(c-a).length;stretch=max(1,d/(l1+l2)*1.006);l1*=stretch;l2*=stretch
 axis=(c-a).normalized();v=Vector(pole);v=(v-axis*v.dot(axis)).normalized()
 u=(d*d+l1*l1-l2*l2)/(2*d);h=math.sqrt(max(0,l1*l1-u*u))
 return a+axis*u+v*h,stretch

def set_bone(name,a,b):
 bone=rig.data.bones[name];r=bone.tail_local-bone.head_local
 q=r.rotation_difference(b-a)@bone.matrix_local.to_quaternion()
 mat=q.to_matrix().to_4x4()@Matrix.Diagonal((1,(b-a).length/r.length,1,1));mat.translation=a
 rig.pose.bones[name].matrix=mat
 bpy.context.view_layer.update()

# Grip point is the measured centre of the actual open leaf's knob.
grip_world=Vector((.5209017718526389,1.5034190625413137,1.866))
grip=rig.matrix_world.inverted()@grip_world
shoulder=poses['upper_arm.R'][0];wrist=grip+Vector((0,.040,.026))
elbow,arm_stretch=solve(shoulder,wrist,(rest['upper_arm.R'][1]-rest['upper_arm.R'][0]).length,(rest['forearm.R'][1]-rest['forearm.R'][0]).length,(-.6,.15,-1))
knuckles=grip+Vector((0,-.018,-.015));tips=grip+Vector((0,.008,-.041))
poses.update({'upper_arm.R':[shoulder,elbow],'forearm.R':[elbow,wrist],'hand.R':[wrist,knuckles],'fingers.R':[knuckles,tips]})
# Relax the left arm; keep the wrist cords on their original surface.
poses['upper_arm.L']=[poses['upper_arm.L'][0],Vector((.112,.017,.728))]
poses['forearm.L']=[poses['upper_arm.L'][1],Vector((.151,.065,.578))]
poses['hand.L']=[poses['forearm.L'][1],Vector((.159,.069,.522))]
poses['fingers.L']=[poses['hand.L'][1],Vector((.160,.070,.477))]
leg_stretch={}
for side,world_ankle in [('L',(-.29,.08,.220)),('R',(.005,.80,.38))]:
 hip=poses['thigh.'+side][0];ankle=rig.matrix_world.inverted()@Vector(world_ankle)
 knee,stretch=solve(hip,ankle,(rest['thigh.'+side][1]-rest['thigh.'+side][0]).length,(rest['shin.'+side][1]-rest['shin.'+side][0]).length,(0,-1,.1))
 poses['thigh.'+side]=[hip,knee];poses['shin.'+side]=[knee,ankle]
 poses['foot.'+side]=[ankle,ankle+Vector((0,-.08,-.043))];leg_stretch[side]=stretch
for name,(a,b) in poses.items():set_bone(name,a,b)
rig['Right palm contact world']=list(grip_world)
rig['Pose status']='Scene reconstruction pose; full surface retained. Individual finger fit and film silhouette still need refinement.'
rig['Arm stretch ratio']=arm_stretch
# The same rig is visible to rays transported through the real spatial doorway.
instance=bpy.data.objects.new('Suzume continuation through spatial portal',None);instance.instance_type='COLLECTION';instance.instance_collection=collection;instance.location=(0,0,-1600);day.collection.objects.link(instance)
for ob in [mesh,instance]:
 for frame,value in [(1,True),(24,True),(25,False),(120,False)]:
  ob.hide_render=value;ob.keyframe_insert(data_path='hide_render',frame=frame)
  ob.hide_viewport=value;ob.keyframe_insert(data_path='hide_viewport',frame=frame)
day.frame_set(72);day.camera=bpy.data.objects['Door front camera']
day['Character revision']='v14: actual Hunyuan 3D 3.1 four-view mesh, 500,000 triangles, packed 4k PBR, editable skeleton.'
note=bpy.data.texts.new('混元人物与检查说明');note.write('人物由四张一致 A-pose 重建视图提交混元 3D 3.1 得到。\n50 万三角面，三张 4K 贴图已内嵌。原始 GLB 与 A-pose Blender 保存在 character-hunyuan-v1。\n场景内保留骨骼和原始表面，可修改姿态。第 72 帧显示开门人物；第 1 帧隐藏。\n人物造型、手指贴合和步态仍是重建，尚未达到影片一比一标准。\n')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_distance=7;area.spaces.active.region_3d.view_location=(0,0,1.7)
bpy.ops.wm.save_as_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v14.blend'))
audit={'nativeFile':str(V/'suzume-full-scene-hunyuan-v14.blend'),'source':'Suzume_Hunyuan31_original.glb','triangles':len(mesh.data.polygons),'rigBones':len(rig.pose.bones),'armStretch':arm_stretch,'legStretch':leg_stretch,'gripWorld':list(grip_world),'portalCharacterInstance':True,'packedCharacterImages':[{'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.name.startswith('texture_pbr')],'visualReview':'pending','oneToOneComplete':False}
(R/'integration-audit.json').write_text(json.dumps(audit,indent=2))
if '--no-render' in sys.argv:
 print('HUNYUAN_INTEGRATION_SAVED',json.dumps(audit),flush=True)
 raise SystemExit(0)
day.render.resolution_x=960;day.render.resolution_y=624;day.render.resolution_percentage=100;day.cycles.samples=24;day.cycles.use_denoising=True
day.render.filepath=str(R/'scene-open-front-v14.png');bpy.ops.render.render(write_still=True)
day.camera.location=(-1.7,-6.8,1.6);day.camera.rotation_euler=(Vector((0,.1,1.75))-day.camera.location).to_track_quat('-Z','Y').to_euler()
day.render.filepath=str(R/'scene-open-side-v14.png');bpy.ops.render.render(write_still=True)
print('HUNYUAN_INTEGRATION_COMPLETE',json.dumps(audit),flush=True)
