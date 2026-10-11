"""Remove scale above the animated hinge and retarget only the gripping arm."""
from pathlib import Path
import bpy,json,numpy as np,math,sys,hashlib
from mathutils import Matrix,Vector
R=Path(__file__).parent;O=R/'movie-door-v32';O.mkdir(exist_ok=True);sys.path.insert(0,str(R))
from night_audit_v30 import fingerprint
source=R/'movie-terrain-v31/Suzume_scene_movie_terrain_v31.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s
hinges=[bpy.data.objects[n] for n in ['Animated door leaf and hinges','Synchronized night door leaf']]
body=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
arm_names=['upper_arm.R','forearm.R','hand.R','fingers.R']
def world(o,evaluated=False):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o
 m=e.to_mesh() if evaluated else e.data
 p=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',p.ravel());M=np.asarray(o.matrix_world);p=p@M[:3,:3].T+M[:3,3]
 if evaluated:e.to_mesh_clear()
 return p
def sweep():
 rows=[]
 for f in [1,36,48,60,72]:
  s.frame_set(f);bpy.context.view_layer.update();M=hinges[0].matrix_world
  rows.append({'frame':f,'angle':hinges[0].rotation_euler.y,'width':(M@Vector((1.6,0,0))-M@Vector((0,0,0))).length,'thickness':(M@Vector((0,0,.095))-M@Vector((0,0,0))).length})
 return rows
before_sweep=sweep();s.frame_set(72);bpy.context.view_layer.update()
before_world=world(body,True)
preserved_names=['Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
preserved={n:fingerprint(bpy.data.objects[n],True) for n in preserved_names}
old_bones={n:rig.pose.bones[n].matrix.copy() for n in arm_names}
old_endpoints={n:(rig.pose.bones[n].head.copy(),rig.pose.bones[n].tail.copy()) for n in arm_names}
old_knob=hinges[0].matrix_world@Vector((1.5625,1.626,.18))
s.frame_set(1);bpy.context.view_layer.update()
closed={o.name:world(o) for h in hinges for o in h.children_recursive if o.type=='MESH'}
for h in hinges:
 assert np.max(np.abs(np.array(h.matrix_parent_inverse)-np.eye(4)))<1e-7
 scale=abs(h.parent.scale.x)
 h.matrix_parent_inverse=Matrix.Diagonal((1/scale,1,1,1))
 h.location.x*=scale;h.scale.x*=scale
 h['rigid_leaf_revision']=32
bpy.context.view_layer.update()
closed_delta=max(float(np.max(np.linalg.norm(world(bpy.data.objects[n])-p,axis=1))) for n,p in closed.items())
assert closed_delta<1e-6,closed_delta
after_sweep=sweep();assert np.ptp([x['width'] for x in after_sweep])<1e-6
assert np.ptp([x['thickness'] for x in after_sweep])<1e-6
s.frame_set(72);bpy.context.view_layer.update()
new_knob=hinges[0].matrix_world@Vector((1.5625,1.626,.18));delta=rig.matrix_world.inverted().to_3x3()@(new_knob-old_knob)
shoulder=old_endpoints['upper_arm.R'][0];wrist=old_endpoints['hand.R'][0]+delta
upper_length=(old_endpoints['upper_arm.R'][1]-shoulder).length
lower_length=(old_endpoints['forearm.R'][1]-old_endpoints['forearm.R'][0]).length
axis=(wrist-shoulder).normalized();distance=(wrist-shoulder).length
assert abs(upper_length-lower_length)<distance<upper_length+lower_length
pole=old_endpoints['upper_arm.R'][1]-shoulder;pole=(pole-axis*pole.dot(axis)).normalized()
along=(distance**2+upper_length**2-lower_length**2)/(2*distance)
elbow=shoulder+axis*along+pole*math.sqrt(max(0,upper_length**2-along**2))
for n,a,b in [('upper_arm.R',shoulder,elbow),('forearm.R',elbow,wrist)]:
 old_vector=old_endpoints[n][1]-old_endpoints[n][0];new_vector=b-a
 mat=old_vector.rotation_difference(new_vector).to_matrix().to_4x4()@old_bones[n]
 # Bone axis is local Y; retain the existing transverse scale and twist.
 mat.col[1]*=new_vector.length/old_vector.length;mat.translation=a
 rig.pose.bones[n].matrix=mat;bpy.context.view_layer.update()
for n in ['hand.R','fingers.R']:
 mat=old_bones[n].copy();mat.translation+=delta;rig.pose.bones[n].matrix=mat;bpy.context.view_layer.update()
rig['Right palm contact world']=list(new_knob)
rig['Pose status']='v32: rigid door leaf; gripping right arm retargeted at open pose; v16 feet and v17 independent head preserved.'
after_world=world(body,True)
indices={body.vertex_groups[n].index for n in arm_names}
arm_mask=np.array([any(g.group in indices and g.weight>0 for g in v.groups) for v in body.data.vertices])
unrelated_delta=float(np.linalg.norm(after_world[~arm_mask]-before_world[~arm_mask],axis=1).max())
assert unrelated_delta<2e-6,unrelated_delta
for n,h in preserved.items():assert fingerprint(bpy.data.objects[n],True)==h,n
rest=np.array([v.co[:] for v in body.data.vertices]);feet={}
for side,sign in [('L',1),('R',-1)]:
 mask=(rest[:,2]<.112)&(rest[:,0]*sign>0);p=after_world[mask];support=np.full(len(p),.015)
 for xmin,xmax,ymin,ymax,z in [(-1.24,1.24,-.44,.50,.0725),(-1.05,1.05,-.34,.31,.16),(-.935,.935,-.215,.215,.195)]:
  inside=(p[:,0]>=xmin)&(p[:,0]<=xmax)&(p[:,1]>=ymin)&(p[:,1]<=ymax);support[inside]=np.maximum(support[inside],z)
 near=(p[:,1]>.015)&(p[:,1]<.145);support[near]=np.maximum(support[near],.240)
 feet[side]={'minimumClearance':float((p[:,2]-support).min()),'minimumSoleZ':float(p[:,2].min()),'maximumChange':float(np.linalg.norm(after_world[mask]-before_world[mask],axis=1).max())}
 assert feet[side]['minimumClearance']>.006 and feet[side]['maximumChange']<2e-6
assert body.data==bpy.data.objects['Suzume Hunyuan entered portion'].data
audit={'revision':32,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'beforeSweep':before_sweep,'afterSweep':after_sweep,'closedLeafMaximumVertexChange':closed_delta,'closedLeafMeshesChecked':len(closed),'oldKnobWorld':list(old_knob),'newKnobWorld':list(new_knob),'knobDisplacement':list(new_knob-old_knob),'nonRightArmMaximumVertexChange':unrelated_delta,'rightArmVertices':int(arm_mask.sum()),'footCollision':feet,'preservedHeadHashes':preserved,'bodyEvaluatedHash':fingerprint(body,True),'rightArmBones':{n:{'matrix':[list(r) for r in rig.pose.bones[n].matrix],'head':list(rig.pose.bones[n].head),'tail':list(rig.pose.bones[n].tail)} for n in arm_names},'oneToOneComplete':False,'limitations':['Right hand has grouped fingers and needs visual inspection.','The character is a static open-door pose, not a complete walking or grasp animation.','Close movie camera fitting remains unresolved; no sky changes made in this revision.']}
np.savez_compressed(O/'character-check-v32.npz',before=before_world,after=after_world,rightArmMask=arm_mask)
(O/'integration-v32.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
s['Door rig revision']='v32: fixed dimensions throughout opening; both spatial door copies synchronized.'
out=O/'Suzume_scene_movie_door_v32.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));print('RIGID_DOOR_SAVED',json.dumps({k:v for k,v in audit.items() if k not in ['rightArmBones','preservedHeadHashes']}),flush=True)
