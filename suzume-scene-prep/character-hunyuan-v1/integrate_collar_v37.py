from pathlib import Path
import bpy,numpy as np,json,sys,hashlib
from mathutils import Matrix
R=Path(__file__).parent;O=R/'movie-collar-v37';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint
source=R/'movie-face-v36/Suzume_scene_movie_face_v36.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
body=bpy.data.objects['Suzume Hunyuan textured surface'];partner=bpy.data.objects['Suzume Hunyuan entered portion'];head=bpy.data.objects['Suzume mathematical head v36'];rig=body.parent
head_hash=fingerprint(head,True);body_before=fingerprint(body,True);a=np.load(O/'collar-fit-v37.npz');before=a['before'];target=a['after'];changed=a['changedMask'];topo=np.load(O/'collar-topology-v37.npz');source_data=np.load(O/'body-source-v37.npz')
def world(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([ob.matrix_world@q.co for q in m.vertices]);e.to_mesh_clear();return v
assert np.linalg.norm(world(body)-before,axis=1).max()<1e-7 and body.data==partner.data
body_modifier=next(m for m in body.modifiers if m.type=='ARMATURE')
original_local=np.array([v.co[:] for v in body.data.vertices]);key_before={k.name:np.array([v.co[:] for v in k.data]) for k in body.data.shape_keys.key_blocks}
assert body.data.shape_keys.use_relative
active_local=key_before['Basis'].copy()
for k in list(body.data.shape_keys.key_blocks)[1:]:active_local+=k.value*(key_before[k.name]-key_before[k.relative_key.name])
def set_delta(delta):
 for k in body.data.shape_keys.key_blocks:k.data.foreach_set('co',(key_before[k.name]+delta).ravel())
 body.data.vertices.foreach_set('co',(original_local+delta).ravel());body.data.update();bpy.context.view_layer.update()
# The existing body uses dual-quaternion volume preservation. Measure its
# actual affine derivative at the collar instead of changing that rig setting.
ids=np.flatnonzero(changed);jac=np.empty((len(ids),3,3));eps=.05
for axis in range(3):
 delta=np.zeros_like(original_local);delta[ids,axis]=eps;set_delta(delta);jac[:,:,axis]=(world(body)[ids]-before[ids])/eps
set_delta(np.zeros_like(original_local));local_delta=np.zeros_like(original_local);local_delta[ids]=np.linalg.solve(jac,(target[ids]-before[ids])[...,None])[...,0]
set_delta(local_delta);after=world(body);error=np.linalg.norm(after-target,axis=1)
if error.max()>8e-7:
 local_delta[ids]+=np.linalg.solve(jac,(target[ids]-after[ids])[...,None])[...,0];set_delta(local_delta);after=world(body);error=np.linalg.norm(after-target,axis=1)
assert error.max()<1e-6,(float(error.max()),int(error.argmax()))
assert np.array_equal(after[~changed],before[~changed]);assert fingerprint(head,True)==head_hash
uv_fix=np.load(O/'collar-uv-v37.npz');uv_changed=uv_fix['changedMask'];uv_after=uv_fix['after'];layer=body.data.uv_layers.active
for loop in body.data.loops:
 if uv_changed[loop.vertex_index]:layer.data[loop.index].uv=uv_after[loop.vertex_index]
# Flare only the front of the replacement neck's lowest 65 mm into the exposed
# chest. The scalp, face, ponytail and neck above the attachment stay untouched.
head_before=world(head);head_target=head_before.copy();neck_group=head.vertex_groups['Head part :: Clean neck'].index;neck_mask=np.array([any(g.group==neck_group and g.weight>.5 for g in v.groups) for v in head.data.vertices]);neck_points=head_before[neck_mask];center=(neck_points.min(0)+neck_points.max(0))/2;radius_y=(neck_points[:,1].max()-neck_points[:,1].min())/2
fade=np.clip((2.515-head_before[:,2])/.065,0,1);fade=fade*fade*(3-2*fade);front=np.clip((head_before[:,1]-center[1])/radius_y,0,1)**2;blend=fade*front*neck_mask
head_target[:,1]+=.020*blend;head_target[:,0]+=(head_before[:,0]-center[0])*.12*blend;head_target[:,2]-=.008*blend;neck_changed=blend>1e-10
hrig=head.parent;Rhead=np.array(hrig.matrix_world);HtoR=np.linalg.inv(Rhead)@np.array(head.matrix_world);head_maps={g.index:np.array(hrig.pose.bones[g.name].matrix@hrig.data.bones[g.name].matrix_local.inverted()) for g in head.vertex_groups if g.name in hrig.pose.bones};head_local=np.array([v.co[:] for v in head.data.vertices])
for i in np.flatnonzero(neck_changed):
 weights=[(g.weight,head_maps[g.group]) for g in head.data.vertices[i].groups if g.group in head_maps];matrix=Rhead@sum(w*m for w,m in weights)@HtoR;head_local[i]+=np.linalg.solve(matrix[:3,:3],head_target[i]-head_before[i])
head.data.vertices.foreach_set('co',head_local.ravel());head.data.update();bpy.context.view_layer.update();head_after=world(head);assert np.linalg.norm(head_after-head_target,axis=1).max()<1e-6;assert np.array_equal(head_after[~neck_changed],head_before[~neck_changed])
head_other=bpy.data.objects[head.name+' — entered portion'];head.name='Suzume mathematical head v37';head_other.name=head.name+' — entered portion';head['head_geometry_revision']=37;head['face_geometry_revision']=36
skin_day=next(slot.material for slot in head.material_slots if slot.material.name.startswith('Suzume warm skin'));skin_night=next(slot.material for slot in head_other.material_slots if slot.material.name.startswith('Suzume warm skin'));skin_faces=json.loads((O/'neck-chest-skin-faces-v37.json').read_text());body.data.materials.append(skin_day)
for ob,material in [(body,skin_day),(partner,skin_night)]:ob.material_slots[1].link='OBJECT';ob.material_slots[1].material=material
for i in skin_faces:body.data.polygons[i].material_index=1
# A closed 2.2 mm rolled edge follows the repaired cloth opening. Its UVs and
# bone weights come from the adjacent original garment, preserving its texture.
seam=a['seamAfter'];t=a['seamParameter'];n=256;cols=8
# Blender's bundled Python has no SciPy: use the periodic harmonic fit saved by
# the calibration script, with linear arc sampling of the final corrected seam.
length=np.linalg.norm(np.diff(np.vstack([seam,seam[0]]),axis=0),axis=1);arc=np.r_[0,np.cumsum(length)];u=np.linspace(0,arc[-1],n,endpoint=False);centers=np.column_stack([np.interp(u,arc,np.r_[seam[:,j],seam[0,j]]) for j in range(3)])
cloth=centers[:,2]>2.485;start=next(i for i in range(n) if cloth[i] and not cloth[(i-1)%n]);keep=[];i=start
while cloth[i]:keep.append(i);i=(i+1)%n
centers=centers[keep];n=len(centers);tangent=np.gradient(centers,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
radial=centers-np.array([-.145,.762,0]);radial[:,2]=0;radial-=np.sum(radial*tangent,axis=1)[:,None]*tangent;radial/=np.linalg.norm(radial,axis=1)[:,None];binormal=np.cross(tangent,radial)
seam_original=topo['originalUnique'][a['seamOrder']];nearest=np.argmin(((centers[:,None,:]-seam[None,:,:])**2).sum(2),axis=1);ring_sources=seam_original[nearest]
uv_layer=body.data.uv_layers.active;uv_by_vertex={}
for loop in body.data.loops:
 if loop.vertex_index in seam_original and loop.vertex_index not in uv_by_vertex:uv_by_vertex[loop.vertex_index]=tuple(uv_layer.data[loop.index].uv)
radius=.0011;verts=[];world_target=[];faces=[];sources=[];uvs=[]
for i in range(n):
 src=int(ring_sources[i]);k=int(np.searchsorted(ids,src));assert ids[k]==src;inv=np.linalg.inv(jac[k])
 for j in range(cols):
  theta=2*np.pi*j/cols;w=centers[i]+radius*(np.cos(theta)*radial[i]+np.sin(theta)*binormal[i]);world_target.append(w);verts.append(active_local[src]+inv@(w-before[src]));sources.append(src);uvs.append(uv_by_vertex[src])
 if i<n-1:
  for j in range(cols):faces.append((i*cols+j,i*cols+(j+1)%cols,(i+1)*cols+(j+1)%cols,(i+1)*cols+j))
faces.append(tuple(reversed(range(cols))));faces.append(tuple((n-1)*cols+j for j in range(cols)))
mesh=bpy.data.meshes.new('Closed rolled collar edge v37');mesh.from_pydata(verts,[],faces);mesh.update();uv=mesh.uv_layers.new(name=uv_layer.name)
for loop in mesh.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
for polygon in mesh.polygons:polygon.use_smooth=True
hem=bpy.data.objects.new('Suzume rolled collar edge v37',mesh);body.users_collection[0].objects.link(hem);hem.parent=rig;hem.matrix_parent_inverse=body.matrix_parent_inverse.copy();hem.matrix_basis=body.matrix_basis.copy()
for group in body.vertex_groups:hem.vertex_groups.new(name=group.name)
for i,src in enumerate(sources):
 for g in body.data.vertices[src].groups:hem.vertex_groups[g.group].add([i],g.weight,'REPLACE')
mod=hem.modifiers.new('Shared character rig','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=body_modifier.use_deform_preserve_volume;mesh.materials.append(body.material_slots[0].material);other=hem.copy();other.data=mesh;other.name=hem.name+' — entered portion';bpy.data.collections['Suzume — portion inside the otherworld'].objects.link(other)
for ob,material in [(hem,body.material_slots[0].material),(other,partner.material_slots[0].material)]:
 ob.material_slots[0].link='OBJECT';ob.material_slots[0].material=material
 for frame,hidden in [(1,True),(24,True),(25,False),(120,False)]:ob.hide_render=hidden;ob.keyframe_insert(data_path='hide_render',frame=frame);ob.hide_viewport=hidden;ob.keyframe_insert(data_path='hide_viewport',frame=frame)
s.frame_set(72);bpy.context.view_layer.update();hem_world=world(hem);assert np.linalg.norm(hem_world-np.array(world_target),axis=1).max()<1e-6
body['collar_geometry_revision']=37;s['Character revision']='v37: smooth collar, clean fabric UVs and neck-base attachment; v36 face, v35 ponytail and v32 grip/feet retained.'
fit=json.loads((O/'fit-v37.json').read_text());report={'revision':37,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bodyBeforeHash':body_before,'bodyHash':fingerprint(body,True),'headBeforeHash':head_hash,'headHash':fingerprint(head,True),'bodyVertices':len(before),'changedCollarVertices':int(changed.sum()),'outsideCollarVerticesPreservedExactly':True,'faceAndPonytailPreservedExactly':True,'changedNeckBaseVertices':int(neck_changed.sum()),'changedUVVertices':int(uv_fix['changedMask'].sum()),'sharedBodyAndHemSpatialMeshes':True,'collarFaceFlips':fit['flippedModifiedTriangles'],'maximumWorldReconstructionError':float(error.max()),'hemVertices':len(hem_world),'hemFaces':len(faces),'hemRadius':radius,'hemTexture':'Existing garment texture and locally repaired UV sampling.','hemExcludesBareSkin':True,'characterParts':['Suzume Hunyuan textured surface',head.name,hem.name],'oneToOneComplete':False}
report['neckChestSkinTriangles']=len(skin_faces);report['neckAndChestShareSkinMaterial']=True
np.savez_compressed(O/'character-check-v37.npz',before=before,after=after,changedMask=changed,hem=hem_world);np.savez_compressed(O/'head-check-v37.npz',before=head_before,after=head_after,neckChangedMask=neck_changed,ponytailMask=np.load(R/'movie-face-v36/head-check-v36.npz')['ponytailMask']);(O/'integration-v37.json').write_text(json.dumps(report,indent=2));s.render.resolution_x=720;s.render.resolution_y=468
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_collar_v37.blend'));print('COLLAR_37_SAVED',json.dumps(report),flush=True)
