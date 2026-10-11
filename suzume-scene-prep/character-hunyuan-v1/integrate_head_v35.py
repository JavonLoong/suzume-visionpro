from pathlib import Path
import bpy,numpy as np,json,sys,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'movie-head-v35';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint
source=R/'movie-head-v34/Suzume_scene_movie_head_v34.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
h=bpy.data.objects['Suzume mathematical head v34'];other=bpy.data.objects[h.name+' — entered portion'];rig=h.parent;body=bpy.data.objects['Suzume Hunyuan textured surface'];body_hash=fingerprint(body,True)
a=np.load(O/'head-fit-v35.npz');before=a['before'];after=a['after'].copy();pony=a['ponytailMask'];local=np.array([v.co[:] for v in h.data.vertices])
def world(ob,faces=False):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([ob.matrix_world@q.co for q in m.vertices]);fs=[tuple(p.vertices) for p in m.polygons];e.to_mesh_clear();return (v,fs) if faces else v
assert np.max(np.linalg.norm(world(h)-before,axis=1))<1e-7
# Build the actual skinned affine map for each weight bucket. Inverting its
# linear part preserves the original neck/head weights and editable rig.
bone_maps={g.index:np.array(rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()) for g in h.vertex_groups if g.name in rig.pose.bones}
rig_world=np.array(rig.matrix_world);maps=[]
for v in h.data.vertices:
 weights=[(q.weight,bone_maps[q.group]) for q in v.groups if q.group in bone_maps];total=sum(q[0] for q in weights);assert abs(total-1)<1e-6
 maps.append(rig_world@sum(w*m for w,m in weights))
maps=np.array(maps);predicted=np.einsum('nij,nj->ni',maps[:,:3,:3],local)+maps[:,:3,3];assert np.max(np.linalg.norm(predicted-before,axis=1))<1e-6
verts,fs=world(body,True);tree=BVHTree.FromPolygons(verts,fs,all_triangles=True)
C=np.array([.15354844661181763,-11.7300315454759,2.8782074998654252]);p=.07098138634927482;f=86.54434612692005/36*1656;up=np.array([0,np.sin(p),np.cos(p)]);forward=np.array([0,np.cos(p),-np.sin(p)])
def project(v):
 d=v-C;dep=d@forward;return np.column_stack([1276+f*d[:,0]/dep,828-f*(d@up)/dep])
uv=project(after);phase=np.clip((2.91-after[:,2])/.78,0,1);curve=phase*phase*(3-2*phase)*pony
def gaps():
 hits=[]
 for i in np.flatnonzero(pony&(after[:,2]<2.65)):
  hit,n,_,_=tree.ray_cast(Vector((after[i,0],-2,after[i,2])),Vector((0,1,0)),4)
  if hit is not None and n.y<-.15:hits.append((i,float(hit.y-after[i,1])))
 return hits
amplitude=0
for _ in range(3):
 hits=gaps();need=max(max(0,.025-gap)/max(curve[i],1e-7) for i,gap in hits)
 if need==0:break
 step=need+.008;amplitude+=step;after[:,1]-=step*curve
 ids=np.flatnonzero(pony);q=(828-uv[ids,1])/f;dy=after[ids,1]-C[1];dz=(q*np.cos(p)-np.sin(p))/(np.cos(p)+q*np.sin(p))*dy;dep=np.cos(p)*dy-np.sin(p)*dz
 after[ids,2]=C[2]+dz;after[ids,0]=C[0]+(uv[ids,0]-1276)/f*dep
hits=gaps();assert min(gap for _,gap in hits)>.015
delta=np.linalg.solve(maps[:,:3,:3],(after-before)[...,None])[...,0];local+=delta
h.data.vertices.foreach_set('co',local.ravel());h.data.update();bpy.context.view_layer.update();evaluated=world(h);error=np.linalg.norm(evaluated-after,axis=1);print('DEFORM_ERROR',float(error.max()),int(error.argmax()),flush=True);assert error.max()<1e-6
assert fingerprint(body,True)==body_hash and h.data==other.data
h.name='Suzume mathematical head v35';other.name=h.name+' — entered portion';h['head_geometry_revision']=35
s['Character revision']='v35: head placement and ponytail width fitted to the movie back-view reference; Hunyuan body, grip and feet preserved.'
old=json.loads((R/'movie-head-v34/integration-v34.json').read_text());report={'revision':35,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bodyHash':body_hash,'headHash':fingerprint(h,True),'headVertices':len(local),'ponytailVertices':int(pony.sum()),'ponytailParts':old['ponytailParts'],'headSource':old['headSource'],'headScaleAndPonytailOutlineUpdated':True,'neckBottomPreserved':True,'minimumBackClothRayGap':min(g for _,g in hits),'backClothRays':len(hits),'additionalRearCurveAmplitude':amplitude,'sharedSpatialMesh':True,'maximumWorldReconstructionError':float(np.linalg.norm(evaluated-after,axis=1).max()),'maximumProjectionDriftAfterClearance':float(abs(project(evaluated)[pony]-uv[pony]).max()),'oneToOneComplete':False}
np.savez_compressed(O/'head-check-v35.npz',before=before,after=evaluated,ponytailMask=pony)
(O/'integration-v35.json').write_text(json.dumps(report,indent=2));s.render.resolution_x=720;s.render.resolution_y=468
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_head_v35.blend'));print('HEAD_35_SAVED',json.dumps(report),flush=True)
