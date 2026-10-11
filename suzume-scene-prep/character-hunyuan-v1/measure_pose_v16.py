"""Measure the actual editable mesh and projection before fitting film landmarks."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v15.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
s.render.resolution_x=2552;s.render.resolution_y=1656;s.render.resolution_percentage=100
cam=bpy.data.objects['Door front camera'];s.camera=cam
mesh=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
deps=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(deps)
P=np.empty((len(mesh.data.vertices),3),np.float32);mesh.data.vertices.foreach_get('co',P.ravel())
Q=np.empty_like(P);ev.data.vertices.foreach_get('co',Q.ravel())
M=np.array(mesh.matrix_world);world=Q@M[:3,:3].T+M[:3,3]
def project(v):
 p=world_to_camera_view(s,cam,Vector(v));return [float(p.x*2552),float((1-p.y)*1656)]
names=[g.name for g in mesh.vertex_groups]
weights=np.zeros((len(P),len(names)),np.float32)
for v in mesh.data.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
anchors={}
targets={'left_shoulder':(.082,.018,.923),'right_shoulder':(-.082,.018,.923),
 'waist':(0,.042,.745),'left_hem':(.084,.035,.455),'right_hem':(-.084,.035,.455),
 'left_shoe':(.061,-.069,.014),'right_shoe':(-.061,-.069,.014),
 'left_hand_tip':(.181,-.012,.519),'right_hand_tip':(-.181,-.012,.519)}
for name,target in targets.items():
 idx=int(np.argmin(np.linalg.norm(P-np.array(target),axis=1)))
 anchors[name]={'index':idx,'rest':P[idx].tolist(),'world':world[idx].tolist(),'pixel':project(world[idx])}
idx=int(np.argmax(P[:,2]));anchors['head_top']={'index':idx,'rest':P[idx].tolist(),'world':world[idx].tolist(),'pixel':project(world[idx])}
bones={}
for b in rig.pose.bones:
 h=rig.matrix_world@b.head;t=rig.matrix_world@b.tail
 bones[b.name]={'restHead':list(b.bone.head_local),'restTail':list(b.bone.tail_local),'head':list(b.head),'tail':list(b.tail),'matrix':np.array(b.matrix).tolist(),'restMatrix':np.array(b.bone.matrix_local).tolist(),'worldHead':list(h),'worldTail':list(t),'headPixel':project(h),'tailPixel':project(t)}
projection=cam.calc_matrix_camera(deps,x=2552,y=1656)@cam.matrix_world.inverted()
np.savez_compressed(R/'pose-measure-v15.npz',rest=P,posed=Q,world=world,weights=weights,projection=np.array(projection),rigMatrix=M)
audit={'dimensions':[2552,1656],'cameraMatrix':np.array(cam.matrix_world).tolist(),'cameraLens':cam.data.lens,'cameraSensorFit':cam.data.sensor_fit,'cameraSensorHeight':cam.data.sensor_height,'projection':np.array(projection).tolist(),'rigMatrix':M.tolist(),'anchors':anchors,'bones':bones,'groups':names}
(R/'pose-measure-v15.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('MEASURED_POSE',json.dumps({'anchors':anchors,'bones':{n:{'head':v['headPixel'],'tail':v['tailPixel']} for n,v in bones.items()}}),flush=True)
