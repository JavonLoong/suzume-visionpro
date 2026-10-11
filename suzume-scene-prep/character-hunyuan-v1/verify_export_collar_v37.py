from pathlib import Path
import bpy,numpy as np,json,hashlib,sys
from collections import Counter
R=Path(__file__).parent;O=R/'movie-collar-v37';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint;from character_export_utils import export_character
f=O/'Suzume_scene_movie_collar_v37.blend';bpy.ops.wm.open_mainfile(filepath=str(f));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);a=json.loads((O/'integration-v37.json').read_text());body=bpy.data.objects[a['characterParts'][0]];head=bpy.data.objects[a['characterParts'][1]];hem=bpy.data.objects[a['characterParts'][2]]
def world(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=np.array([ob.matrix_world@q.co for q in m.vertices]);faces=np.array([p.vertices[:] for p in m.loop_triangles]);e.to_mesh_clear();return v,faces
assert fingerprint(body,True)==a['bodyHash'] and fingerprint(head,True)==a['headHash'];actual,body_faces=world(body);check=np.load(O/'character-check-v37.npz');mask=check['changedMask'];assert np.array_equal(actual[~mask],check['before'][~mask]) and np.linalg.norm(actual-check['after'],axis=1).max()<1e-7
old=check['before'][body_faces];new=actual[body_faces];n0=np.cross(old[:,1]-old[:,0],old[:,2]-old[:,0]);n1=np.cross(new[:,1]-new[:,0],new[:,2]-new[:,0]);affected=np.any(mask[body_faces],axis=1);assert np.all((n0*n1).sum(1)[affected]>=0);assert np.all(np.linalg.norm(n1[affected],axis=1)>2e-10)
hc=np.load(O/'head-check-v37.npz');hw,hf=world(head);assert np.array_equal(hw[~hc['neckChangedMask']],hc['before'][~hc['neckChangedMask']]);assert np.array_equal(hw[hc['ponytailMask']],hc['before'][hc['ponytailMask']])
uv=np.load(O/'collar-uv-v37.npz');expected_uv=uv['after'];layer=body.data.uv_layers.active;maximum_uv_error=max(np.linalg.norm(np.array(layer.data[loop.index].uv)-expected_uv[loop.vertex_index]) for loop in body.data.loops);assert maximum_uv_error<1e-7
hempoints,hfaces=world(hem);edges=Counter(tuple(sorted((int(p[i]),int(p[(i+1)%3])))) for p in hfaces for i in range(3));assert set(edges.values())=={2};q=hempoints-hempoints.mean(0);volume=float(np.einsum('ij,ij->i',q[hfaces[:,0]],np.cross(q[hfaces[:,1]],q[hfaces[:,2]])).sum()/6);assert volume>0
hem_uv=np.zeros((len(hempoints),2))
for loop in hem.data.loops:hem_uv[loop.vertex_index]=hem.data.uv_layers.active.data[loop.index].uv[:]
cloth_vertices=np.zeros(len(actual),bool)
for polygon in body.data.polygons:
 if polygon.material_index==0:cloth_vertices[list(polygon.vertices)]=True
np.savez_compressed(O/'export-uv-check-v37.npz',body=expected_uv,hem=hem_uv,bodyTexturedMask=cloth_vertices)
other_body=bpy.data.objects['Suzume Hunyuan entered portion'];other_head=bpy.data.objects[head.name+' — entered portion'];other_hem=bpy.data.objects[hem.name+' — entered portion']
for ob,other in [(body,other_body),(head,other_head),(hem,other_hem)]:assert ob.data==other.data and ob.parent==other.parent
assert hem.material_slots[0].material==body.material_slots[0].material and other_hem.material_slots[0].material==other_body.material_slots[0].material
assert body.material_slots[1].material in [x.material for x in head.material_slots] and other_body.material_slots[1].material in [x.material for x in other_head.material_slots]
skin_faces=json.loads((O/'neck-chest-skin-faces-v37.json').read_text());assert set(p.index for p in body.data.polygons if p.material_index==1)==set(skin_faces)
assert next(m for m in body.modifiers if m.type=='ARMATURE').use_deform_preserve_volume and next(m for m in hem.modifiers if m.type=='ARMATURE').use_deform_preserve_volume
for frame,hidden in [(1,True),(72,False)]:
 s.frame_set(frame)
 for ob in [head,other_head,hem,other_hem]:assert ob.hide_render==hidden
s.frame_set(72);texture=json.loads((O/'uv-repair-v37.json').read_text());assert hashlib.sha256(Path(texture['baseColorImage']).read_bytes()).hexdigest()==texture['originalImageSha256']
parts=export_character(R/'viewer/character-v37',37,a['characterParts']);v={'revision':37,'freshReopenVerified':True,'nativeSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'feetGripAndNonCollarGeometryPreserved':True,'faceAndPonytailPreservedExactly':True,'neckBaseBlended':True,'collarTriangleFlips':0,'collarDegenerateTriangles':0,'clothUVSamplingVerified':True,'maximumUVError':float(maximum_uv_error),'originalTexturePixelsPreserved':True,'closedHemBoundaryEdges':0,'hemSignedVolume':volume,'sharedSpatialMeshesAndMaterialsVerified':True,'dualQuaternionBodyAndHemPreserved':True,'closedAndOpenVisibilityVerified':True,'partTriangles':parts,'oneToOneComplete':False,'browserRuntimeVerified':False}
v['neckChestSkinTriangles']=len(skin_faces);v['neckAndChestSkinMaterialShared']=True
(O/'verification-v37.json').write_text(json.dumps(v,indent=2));print('COLLAR_37_REOPEN_EXPORT_OK',json.dumps(v),flush=True)
