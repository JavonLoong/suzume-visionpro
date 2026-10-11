"""Independent mathematical head parts and closed ponytail volumes on the v32 body."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent;O=R/'movie-head-v34';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from night_audit_v30 import fingerprint
source=R/'movie-door-v32/Suzume_scene_movie_door_v32.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
body=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig'];body_hash=fingerprint(body,True);day_collection=body.users_collection[0];inside=bpy.data.collections['Suzume — portion inside the otherworld'];gate=.0719999149441719
old=['Suzume independent Hunyuan head','Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']
for name in old+[n+' — entered portion' for n in old]:
 ob=bpy.data.objects.get(name)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
with bpy.data.libraries.load(str(R/'head-hunyuan-v1/clean-v18/Suzume-clean-head-v18.blend'),link=False) as (src,dst):dst.objects=src.objects
parts=[];pony_audit=[]
for ob in dst.objects:
 if ob.type!='MESH' or not ob.get('head_part_v18'):bpy.data.objects.remove(ob,do_unlink=True);continue
 day_collection.objects.link(ob);parts.append(ob);component=ob.vertex_groups.new(name='Head part :: '+ob.name);component.add(list(range(len(ob.data.vertices))),1,'REPLACE')
 if ob.name.startswith('Solid ponytail lock'):
  bm=bmesh.new();bm.from_mesh(ob.data);boundary=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=boundary,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(not e.is_boundary for e in bm.edges);bm.to_mesh(ob.data);bm.free();pony_audit.append({'name':ob.name,'closed':True,'vertices':len(ob.data.vertices)})
 for vertex in ob.data.vertices:
  p=vertex.co.copy()
  if ob.name.startswith('Solid ponytail lock'):
   k=int(ob.name.rsplit(' ',1)[1]);old_tip=.09*np.cos(2*np.pi*k/6)*1.3+.025;new_tip=old_tip if k==0 else .025
   t=float(np.clip((.51-p.z)/(.51+.77+.10*(k%3)/2),0,1));blend=float(np.clip((t-.2)/.7,0,1));blend=blend*blend*(3-2*blend);p.x+=(new_tip-old_tip)*blend
  q=p*.118;q.x-=.004;q.z+=1.1751030684-.9738872647*.118
  if ob.name=='Clean neck':
   t=float(np.clip((-.4-p.z)/.48,0,1));t=t*t*(3-2*t);a=np.arctan2(p.y-.04,p.x-.015);q.x=q.x*(1-t)+(-.003+.019*np.cos(a))*t;q.y=q.y*(1-t)+(-.002+.026*np.sin(a))*t
  vertex.co=q
for ob in s.objects:ob.select_set(False)
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();head=bpy.context.object;head.name='Suzume mathematical head v34';head.parent=rig;head.matrix_parent_inverse.identity();head.matrix_basis.identity()
coords=np.array([v.co[:] for v in head.data.vertices]);ids={g.name:g.index for g in head.vertex_groups};neck_id=ids['Head part :: Clean neck'];pony_ids={i for n,i in ids.items() if n.startswith('Head part :: Solid ponytail lock')}
neck_mask=np.array([any(g.group==neck_id and g.weight>.5 for g in v.groups) for v in head.data.vertices]);pony=np.array([any(g.group in pony_ids and g.weight>.5 for g in v.groups) for v in head.data.vertices])
head_group=head.vertex_groups.new(name='head');neck_group=head.vertex_groups.new(name='neck');weight=np.clip((coords[:,2]-.976)/.047,0,1);weight=weight*weight*(3-2*weight);weight=1-(1-weight)*neck_mask
for bucket in np.unique(np.rint(weight*100).astype(int)):
 indices=np.flatnonzero(np.rint(weight*100).astype(int)==bucket).tolist()
 if bucket:head_group.add(indices,float(bucket)/100,'REPLACE')
 if bucket<100:neck_group.add(indices,1-float(bucket)/100,'REPLACE')
mod=head.modifiers.new('Shared character rig','ARMATURE');mod.object=rig;bpy.context.view_layer.update()
def world(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([q.co[:] for q in m.vertices]);M=np.array(ob.matrix_world);v=v@M[:3,:3].T+M[:3,3];e.to_mesh_clear();return v
before=world(head);tip=int(np.argmin(np.where(pony,before[:,2],100)));target=np.array([1183.5,772.]);s.render.resolution_x=2552;s.render.resolution_y=1656
def pixel(v):
 p=world_to_camera_view(s,s.camera,Vector(v));return np.array([p.x*2552,(1-p.y)*1656])
# Each strand is independent of scalp and skin. Smooth longitudinal stretching
# therefore cannot pull a neck triangle or generate a connecting sheet.
original_z=(coords[:,2]-(1.1751030684-.9738872647*.118))/.118;progress=np.maximum(.57-original_z,0)*pony
base=coords.copy();extension=1.55
coords[:,2]-=(extension-1)*progress*.118;head.data.vertices.foreach_set('co',coords.ravel());head.data.update();bpy.context.view_layer.update();extended=world(head)
e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();verts=np.array([v.co[:] for v in m.vertices]);M=np.array(body.matrix_world);verts=verts@M[:3,:3].T+M[:3,3];faces=[tuple(f.vertices) for f in m.polygons];e.to_mesh_clear();tree=BVHTree.FromPolygons(verts,faces,all_triangles=True)
phase=np.clip((3.01-extended[:,2])/.88,0,1);curve=phase*phase*(3-2*phase)*pony;deficit=np.zeros(len(coords));selected=np.flatnonzero(pony&(extended[:,2]<2.65))
for i in selected:
 hit,n,_,_=tree.ray_cast(Vector((extended[i,0],-2,extended[i,2])),Vector((0,1,0)),4)
 if hit is not None and n.y<-.15:deficit[i]=max(0,extended[i,1]-(hit.y-.025))
amplitude=float(np.max(deficit[selected]/np.maximum(curve[selected],1e-8)))+.015;coords[:,1]+=amplitude*curve/2.9325
head.data.vertices.foreach_set('co',coords.ravel());head.data.update();bpy.context.view_layer.update();w=world(head)
# Match the tip at its independent, collision-safe depth using X/Z only.
epsilon=.001;J=np.column_stack([(pixel(w[tip]+np.eye(3)[i]*epsilon)-pixel(w[tip]))/epsilon for i in [0,2]]);delta=np.linalg.solve(J,target-pixel(w[tip]));fade=(progress/max(progress[tip],1e-6))**2
coords[:,0]-=delta[0]*fade/2.9325;coords[:,2]+=delta[1]*fade/2.9325
head.data.vertices.foreach_set('co',coords.ravel());head.data.update();bpy.context.view_layer.update();after=world(head);assert np.max(np.linalg.norm(after[~pony]-before[~pony],axis=1))<1e-7
clear=[]
for i in np.flatnonzero(pony&(after[:,2]<2.65)):
 hit,n,_,_=tree.ray_cast(Vector((after[i,0],-2,after[i,2])),Vector((0,1,0)),4)
 if hit is not None and n.y<-.15:clear.append(float(hit.y-after[i,1]))
assert min(clear)>.01,min(clear)
def clipped(base,entered):
 mat=base.copy();nodes=mat.node_tree.nodes;links=mat.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);surface=out.inputs['Surface'].links[0].from_socket;geo=nodes.new('ShaderNodeNewGeometry');xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],xyz.inputs[0]);test=nodes.new('ShaderNodeMath');test.operation='LESS_THAN' if entered else 'GREATER_THAN';test.inputs[1].default_value=gate;links.new(xyz.outputs['Y'],test.inputs[0]);transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');mix.name='Spatial doorway half-space';links.new(test.outputs[0],mix.inputs[0]);links.new(surface,mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface']);mat['spatial_half']='otherworld' if entered else 'courtyard';mat['portal_plane_blender_y']=gate;return mat
other=head.copy();other.data=head.data;other.name=head.name+' — entered portion';inside.objects.link(other);materials=[slot.material for slot in head.material_slots]
for ob,entered in [(head,False),(other,True)]:
 for slot,base_mat in zip(ob.material_slots,materials):slot.link='OBJECT';slot.material=clipped(base_mat,entered)
 for frame,value in [(1,True),(24,True),(25,False),(120,False)]:ob.hide_render=value;ob.keyframe_insert(data_path='hide_render',frame=frame);ob.hide_viewport=value;ob.keyframe_insert(data_path='hide_viewport',frame=frame)
s.frame_set(72);bpy.context.view_layer.update();assert fingerprint(body,True)==body_hash
head['head_geometry_revision']=34;head['head_origin']='Reference-driven mathematical head; Hunyuan 3.1 body retained. Not a new Hunyuan head generation.'
s['Character revision']='v34: independently editable mathematical head with six closed ponytail locks; v32 body and rigid door.'
report={'revision':34,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bodyHash':body_hash,'headHash':fingerprint(head,True),'headVertices':len(coords),'ponytailVertices':int(pony.sum()),'ponytailParts':pony_audit,'skinScalpAndPinsUnaffectedByPonytailDeformation':True,'tipVertex':tip,'targetTipPixels':target.tolist(),'actualTipPixels':pixel(after[tip]).tolist(),'minimumBackClothRayGap':min(clear),'backClothRays':len(clear),'rearCurveAmplitude':amplitude,'sharedSpatialMesh':True,'headSource':'Mathematical geometry derived from existing v18 components; no new Hunyuan submission.','oneToOneComplete':False}
np.savez_compressed(O/'head-check-v34.npz',before=before,after=after,ponytailMask=pony);(O/'integration-v34.json').write_text(json.dumps(report,indent=2));s.render.resolution_x=720;s.render.resolution_y=468
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_head_v34.blend'));print('HEAD_34_SAVED',json.dumps(report),flush=True)
