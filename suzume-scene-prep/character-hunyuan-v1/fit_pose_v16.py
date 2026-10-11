"""Film-space pose fit, retaining v15's editable mesh and portal partition."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v15.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
s.render.resolution_x=2552;s.render.resolution_y=1656;s.render.resolution_percentage=100
cam=bpy.data.objects['Door front camera'];s.camera=cam
mesh=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
base=json.loads((R/'pose-measure-v15.json').read_text())
deps=bpy.context.evaluated_depsgraph_get()
proj=cam.calc_matrix_camera(deps,x=2552,y=1656)@cam.matrix_world.inverted()
inverse=proj.inverted();world_to_rig=rig.matrix_world.inverted()
def unproject(pixel,depth_y):
 x,y=pixel;ndc=Vector((x/2552*2-1,1-y/1656*2,-1,1));near=inverse@ndc;near/=near.w
 ndc.z=1;far=inverse@ndc;far/=far.w
 a=Vector(near[:3]);d=Vector(far[:3])-a
 return a+d*((depth_y-a.y)/d.y)
def pixel(v):
 q=world_to_camera_view(s,cam,Vector(v));return np.array([q.x*2552,(1-q.y)*1656])
P=np.empty((len(mesh.data.vertices),3),np.float32);mesh.data.vertices.foreach_get('co',P.ravel())
weights=np.load(R/'pose-measure-v15.npz')['weights']
colors=np.load(R/'character-vertex-albedo.npy')
def ramp(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# The original geometric ponytail mask also covered a small patch of white
# back cloth. Albedo separates the dark hair from that patch without remeshing.
repair=(P[:,1]>.045)&(P[:,2]>.875)&(P[:,2]<.959)&(abs(P[:,0])<.075)&(colors.max(axis=1)>=140)
repair_indices=np.flatnonzero(repair).tolist();zz=P[repair,2]
for name in ['head','pelvis','spine','chest','neck']:mesh.vertex_groups[name].remove(repair_indices)
chest=ramp(.783,.887,zz);neck=ramp(.925,.965,zz);pelvis=ramp(.751,.807,zz)
replacement={'pelvis':1-pelvis,'spine':pelvis*(1-chest),'chest':pelvis*chest*(1-neck),'neck':pelvis*chest*neck}
for name,w in replacement.items():
 quant=np.rint(w*128).astype(np.int16)
 for q in np.unique(quant):
  if q:mesh.vertex_groups[name].add(np.array(repair_indices)[quant==q].tolist(),int(q)/128,'REPLACE')
arm_weights=sum(weights[:,i] for i,n in enumerate(base['groups']) if n.startswith(('upper_arm.','forearm.','hand.','fingers.')))
def lower_warp(z):return np.interp(z,[0,.07,.35,.45,.743,1.3],[0,.07,.318,.407,.743,1.3])
if mesh.data.shape_keys is None:mesh.shape_key_add(name='Basis')
key=mesh.shape_key_add(name='Film lower-body proportions v16');shaped=P.copy()
shaped[:,2]+=(lower_warp(P[:,2])-P[:,2])*(1-arm_weights)
shaped[:,0]*=1-.07*ramp(.420,.447,P[:,2])*(1-ramp(.447,.743,P[:,2]))*(1-arm_weights)
key.data.foreach_set('co',shaped.ravel());key.value=1
# Warp the rest skeleton with its surface, retaining smooth anatomical weights.
# The whole lower-body mapping is continuous, including the exposed knees.
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.data.edit_bones:
 if bone.name=='pelvis' or bone.name.startswith(('thigh.','shin.','foot.')):
  bone.head.z=float(lower_warp(bone.head.z));bone.tail.z=float(lower_warp(bone.tail.z))
bpy.ops.object.mode_set(mode='OBJECT')
rest={b.name:(b.head_local.copy(),b.tail_local.copy()) for b in rig.data.bones}
poses={n:[Vector(v['head']),Vector(v['tail'])] for n,v in base['bones'].items()}
def torso_shift(v):
 t=min(1,max(0,(v.z-.710)/(.903-.710)))
 return v+Vector((0,0,.030*t))
for n in ['pelvis','spine','chest','neck','head']:
 poses[n]=[torso_shift(p) for p in poses[n]]
# The hips stay closer to the threshold than the head. Preserve the measured
# screen coordinates while distributing the forward lean through the torso.
for name,depths in [('pelvis',(.42,.46)),('spine',(.46,.59)),('chest',(.59,.75))]:
 for part,depth in enumerate(depths):
  old_world=rig.matrix_world@poses[name][part]
  poses[name][part]=world_to_rig@unproject(pixel(old_world),depth)
for side in ['L','R']:
 old_world=rig.matrix_world@poses['thigh.'+side][0]
 poses['thigh.'+side][0]=world_to_rig@unproject(pixel(old_world),.42)
head_scale=1.15
poses['head'][1]=poses['head'][0]+(rest['head'][1]-rest['head'][0])*head_scale
for side in ['L','R']:poses['upper_arm.'+side][0]=torso_shift(poses['upper_arm.'+side][0])
# Measured screen landmarks constrain positions; original depth is retained
# for both arms, avoiding a flat billboard fit.
for name,part,target in [('upper_arm.L',1,(1080,849)),('forearm.L',1,(1051,975)),
                          ('hand.L',1,(1054,1011)),('fingers.L',1,(1056,1043)),
                          ('upper_arm.R',1,(1299,808))]:
 original=rig.matrix_world@poses[name][part]
 poses[name][part]=world_to_rig@unproject(target,original.y)
poses['forearm.L'][0]=poses['upper_arm.L'][1]
poses['hand.L'][0]=poses['forearm.L'][1]
poses['fingers.L'][0]=poses['hand.L'][1]
poses['forearm.R'][0]=poses['upper_arm.R'][1]
# The real knob remains the fixed contact target; retain the v15 right hand.
# Both soles are now near the threshold. The trailing left heel stays outside.
def solve_knee(a,c,l1,l2):
 d=(c-a).length;stretch=max(1,d/(l1+l2)*1.004);l1*=stretch;l2*=stretch
 axis=(c-a).normalized();pole=Vector((0,-1,.05));v=(pole-axis*pole.dot(axis)).normalized()
 along=(d*d+l1*l1-l2*l2)/(2*d);h=math.sqrt(max(0,l1*l1-along*along))
 return a+axis*along+v*h,stretch
ankles={'L':(-.30,-.235,.171),'R':(.005,.105,.245)}
leg_stretch={}
for side,ankle in ankles.items():
 a=poses['thigh.'+side][0];c=world_to_rig@Vector(ankle)
 l1=(rest['thigh.'+side][1]-rest['thigh.'+side][0]).length
 l2=(rest['shin.'+side][1]-rest['shin.'+side][0]).length
 knee,leg_stretch[side]=solve_knee(a,c,l1,l2)
 poses['thigh.'+side]=[a,knee];poses['shin.'+side]=[knee,c]
 poses['foot.'+side]=[c,c+Vector((0,-.080,-.043))]

for b in rig.data.bones:b.inherit_scale='NONE'
def set_bone(name,a,b):
 bone=rig.data.bones[name];r=bone.tail_local-bone.head_local
 q=r.rotation_difference(b-a)@bone.matrix_local.to_quaternion()
 width=head_scale if name=='head' else 1
 mat=q.to_matrix().to_4x4()@Matrix.Diagonal((width,(b-a).length/r.length,width,1));mat.translation=a
 rig.pose.bones[name].matrix=mat;bpy.context.view_layer.update()
for name,(a,b) in poses.items():set_bone(name,a,b)

# Correct toe placements using mesh anchors, with independent 3-D floor/depth
# constraints. Translation is propagated through the knee/ankle chain.
targets={'head_top':(1195,493),'left_shoulder':(1114,691),'right_shoulder':(1245,704),
         'waist':(1172,848),'left_hem':(1092,1136),'right_hem':(1262,1110),
         'left_shoe':(1114,1484),'right_shoe':(1215,1439),'left_hand_tip':(1056,1043)}
# Hem annotations refer to the visible outer edge, not an interior cloth vertex.
old_world=np.load(R/'pose-measure-v15.npz')['world']
for name,idx in [('left_hem',169642),('right_hem',105198)]:
 base['anchors'][name].update({'index':idx,'rest':P[idx].tolist(),'world':old_world[idx].tolist(),'pixel':pixel(old_world[idx]).tolist()})
def world_vertices():
 dep=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(dep)
 q=np.empty_like(P);ev.data.vertices.foreach_get('co',q.ravel())
 m=np.array(mesh.matrix_world);return q@m[:3,:3].T+m[:3,3]
for iteration in range(2):
 world=world_vertices()
 for side,keyname in [('L','left_shoe'),('R','right_shoe')]:
  idx=base['anchors'][keyname]['index'];old=Vector(world[idx])
  # A grounded trailing toe and slightly lifted leading shoe determine depth.
  goal=unproject(targets[keyname],old.y)
  if goal.z<.045:
   # Intersect the target ray with the minimum sole height instead of sinking.
   a=unproject(targets[keyname],0);b=unproject(targets[keyname],1)
   goal=a+(b-a)*((.045-a.z)/(b.z-a.z))
  delta=world_to_rig.to_3x3()@(goal-old)
  ankle=poses['shin.'+side][1]+delta;a=poses['thigh.'+side][0]
  knee,leg_stretch[side]=solve_knee(a,ankle,(rest['thigh.'+side][1]-rest['thigh.'+side][0]).length,(rest['shin.'+side][1]-rest['shin.'+side][0]).length)
  poses['thigh.'+side]=[a,knee];poses['shin.'+side]=[knee,ankle]
  poses['foot.'+side]=[ankle,ankle+Vector((0,-.080,-.043))]
  for name in ['thigh.'+side,'shin.'+side,'foot.'+side]:set_bone(name,*poses[name])

# Collision correction uses the actual three foundation blocks from
# door-solid-geometry.js. Body landmarks must yield to solid contact.
foundation=[(-1.24,1.24,-.44,.50,.0725),(-1.05,1.05,-.34,.31,.16),(-.935,.935,-.215,.215,.195)]
def support_height(points):
 h=np.full(len(points),.015)
 for xmin,xmax,ymin,ymax,top in foundation:
  hit=(points[:,0]>=xmin)&(points[:,0]<=xmax)&(points[:,1]>=ymin)&(points[:,1]<=ymax)
  h[hit]=np.maximum(h[hit],top)
 # The aperture starts at Z=.22. A foot straddling its plane must clear that
 # edge, including the threshold thickness and numerical safety margin.
 near=(points[:,1]>.015)&(points[:,1]<.145)
 h[near]=np.maximum(h[near],.240)
 return h
foot_masks={side:(P[:,2]<.112)&(P[:,0]*(1 if side=='L' else -1)>0) for side in ['L','R']}
collision_steps=[]
for iteration in range(3):
 world=world_vertices()
 for side,mask in foot_masks.items():
  points=world[mask];heights=support_height(points)
  lift=max(0,float((heights+.009-points[:,2]).max()))
  if lift<1e-5:continue
  collision_steps.append({'iteration':iteration,'side':side,'liftWorldZ':lift})
  delta=world_to_rig.to_3x3()@Vector((0,0,lift));ankle=poses['shin.'+side][1]+delta;a=poses['thigh.'+side][0]
  knee,leg_stretch[side]=solve_knee(a,ankle,(rest['thigh.'+side][1]-rest['thigh.'+side][0]).length,(rest['shin.'+side][1]-rest['shin.'+side][0]).length)
  poses['thigh.'+side]=[a,knee];poses['shin.'+side]=[knee,ankle];poses['foot.'+side]=[ankle,ankle+Vector((0,-.080,-.043))]
  for name in ['thigh.'+side,'shin.'+side,'foot.'+side]:set_bone(name,*poses[name])
world=world_vertices();measure=[]
collision={side:{'vertices':int(mask.sum()),'minimumClearance':float((world[mask,2]-support_height(world[mask])).min()),'minimumSoleZ':float(world[mask,2].min())} for side,mask in foot_masks.items()}
assert all(check['minimumClearance']>.006 for check in collision.values())
for name,target in targets.items():
 idx=base['anchors'][name]['index'];before=np.array(base['anchors'][name]['pixel']);after=pixel(world[idx]);ref=np.array(target)
 measure.append({'name':name,'vertex':idx,'target':list(target),'before':before.tolist(),'after':after.tolist(),'errorBefore':float(np.linalg.norm(before-ref)),'errorAfter':float(np.linalg.norm(after-ref)),'world':world[idx].tolist()})
gate=float(mesh.material_slots[0].material['portal_plane_blender_y'])
partition={'courtyard':int((world[:,1]<=gate).sum()),'otherworld':int((world[:,1]>=gate).sum()),'total':len(world)}
rig['Pose status']='v16: measured film landmarks; fitted head/shoulders, draped skirt, lower stride; knob contact and editable rig retained.'
rig['Head scale']=head_scale
s['Character revision']='v16: reference-space pose calibration with v15 portal separation retained.'
s.render.resolution_x=800;s.render.resolution_y=520
out=V/'suzume-full-scene-hunyuan-v16.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
audit={'revision':16,'reference':'reference-opening-50525.jpg','referenceDimensions':[2552,1656],
 'landmarks':'Manual visible feature annotations; pixels quantify this camera only, not all-angle identity.',
 'measurements':measure,'meanPixelErrorBefore':float(np.mean([r['errorBefore'] for r in measure])),
 'meanPixelErrorAfter':float(np.mean([r['errorAfter'] for r in measure])),
 'legStretch':leg_stretch,'proportionVertices':int((np.abs(shaped[:,2]-P[:,2])>1e-5).sum()),'backClothWeightsRepaired':len(repair_indices),'partition':partition,'nativeFile':str(out),
 'footCollision':collision,'footCollisionCorrections':collision_steps,'foundationColliders':foundation,
 'oneToOneComplete':False,'visualReview':'pending','limitations':['Reconstructed face, hairpins and sleeve topology remain approximate','Landmark fit does not establish unseen-view fidelity']}
(R/'pose-calibration-v16.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('POSE_FIT_SAVED',json.dumps(audit),flush=True)
