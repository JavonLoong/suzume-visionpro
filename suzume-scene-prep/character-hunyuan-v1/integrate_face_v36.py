from pathlib import Path
import bpy,numpy as np,json,sys,hashlib
R=Path(__file__).parent;O=R/'movie-face-v36';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint
source=R/'movie-head-v35/Suzume_scene_movie_head_v35.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
h=bpy.data.objects['Suzume mathematical head v35'];other=bpy.data.objects[h.name+' — entered portion'];body=bpy.data.objects['Suzume Hunyuan textured surface'];rig=h.parent;body_hash=fingerprint(body,True)
def world(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([ob.matrix_world@q.co for q in m.vertices]);e.to_mesh_clear();return v
a=np.load(O/'face-fit-v36.npz');before=a['before'];target=a['after'];assert np.max(np.linalg.norm(world(h)-before,axis=1))<1e-7
changed=np.linalg.norm(target-before,axis=1)>1e-10;head_group=h.vertex_groups['head'].index
for i in np.flatnonzero(changed):assert any(g.group==head_group and abs(g.weight-1)<1e-8 for g in h.data.vertices[i].groups)
matrix=np.array(rig.matrix_world@rig.pose.bones['head'].matrix@rig.data.bones['head'].matrix_local.inverted())
local=np.array([v.co[:] for v in h.data.vertices]);local[changed]+=np.linalg.solve(matrix[:3,:3],(target[changed]-before[changed]).T).T
h.data.vertices.foreach_set('co',local.ravel());h.data.update();bpy.context.view_layer.update();after=world(h);error=np.linalg.norm(after-target,axis=1);assert error.max()<1e-6
assert fingerprint(body,True)==body_hash and h.data==other.data
assert np.array_equal(after[~changed],before[~changed])
assert np.array_equal(after[a['ponytailMask']],before[a['ponytailMask']])
mouth_group=h.vertex_groups['Head part :: Quiet mouth line'].index;mouth_ids={v.index for v in h.data.vertices if any(g.group==mouth_group and g.weight>.5 for g in v.groups)}
dark=next(i for i,m in enumerate(h.data.materials) if m.name.startswith('Pupil and eyelashes'));white=next(i for i,m in enumerate(h.data.materials) if m.name.startswith('Warm eye white'));teeth=set(int(i) for i in a['mouthToothVertices']);mouth_faces=0;tooth_faces=0
for polygon in h.data.polygons:
 if all(i in mouth_ids for i in polygon.vertices):
  polygon.material_index=white if sum(i in teeth for i in polygon.vertices)>=len(polygon.vertices)/2 else dark;mouth_faces+=1;tooth_faces+=polygon.material_index==white
assert mouth_faces>0 and tooth_faces>0
h.name='Suzume mathematical head v36';other.name=h.name+' — entered portion';h['head_geometry_revision']=36;s['Character revision']='v36: official-reference face proportions and frontal hairline; v35 ponytail and v32 body retained.'
old=json.loads((R/'movie-head-v35/integration-v35.json').read_text());report={'revision':36,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bodyHash':body_hash,'headHash':fingerprint(h,True),'headVertices':len(local),'changedVertices':int(changed.sum()),'unchangedVertices':int((~changed).sum()),'ponytailVertices':int(a['ponytailMask'].sum()),'ponytailParts':old['ponytailParts'],'headSource':old['headSource'],'neckPonytailAndBodyPreserved':True,'minimumBackClothRayGap':old['minimumBackClothRayGap'],'backClothRays':old['backClothRays'],'sharedSpatialMesh':True,'maximumWorldReconstructionError':float(error.max()),'oneToOneComplete':False}
np.savez_compressed(O/'head-check-v36.npz',before=before,after=after,ponytailMask=a['ponytailMask']);(O/'integration-v36.json').write_text(json.dumps(report,indent=2));s.render.resolution_x=720;s.render.resolution_y=468
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_face_v36.blend'));print('FACE_36_SAVED',json.dumps(report),flush=True)
