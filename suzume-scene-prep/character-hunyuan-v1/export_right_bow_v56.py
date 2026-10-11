from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-right-bow-v56';native=O/'Suzume_dual_scene_right_bow_v56.blend';v=json.loads((O/'verification-v56.json').read_text());D=json.loads((O/'right-bow-geometry-v56.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
targets=[{'key':q['key'],'name':'Poster steel '+q['key']+' v44'} for q in v['changedOriginalMeshes']]
objects=[(s.objects[q['name']],q['key']) for q in v['changedOriginalMeshes']]+[(s.objects[D['name']],'new0')]
payload=[];buckets=[];offset=0
for ob,key in objects:
 m=ob.data;m.calc_loop_triangles();M=np.array(ob.matrix_world);a=np.array([p.co[:] for p in m.vertices]);world=a@M[:3,:3].T+M[:3,3];faces=np.array([t.vertices[:] for t in m.loop_triangles]);loops=np.array([t.loops[:] for t in m.loop_triangles]);n=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',n.ravel());n=n@np.linalg.inv(M[:3,:3]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());p=world[faces.ravel()][:,[0,2,1]]*[1,1,-1];normal=n[loops.ravel()][:,[0,2,1]]*[1,1,-1];data=np.c_[p,normal,uv[loops.ravel()]].astype('<f4');raw=data.tobytes();q={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(data),'sourceObjects':[ob.name]}
 if key=='new0':q['newMaterialIndex']=0
 else:q['reuseTargetMaterial']=key
 buckets.append(q);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'right-bow-v56.bin').write_bytes(binary);spec={'revision':56,'nativeSha256':v['nativeSha256'],'targets':targets,'buckets':buckets,'strideFloats':8,'triangles':sum(q['vertexCount']//3 for q in buckets),'binarySha256':hashlib.sha256(binary).hexdigest(),'closedNewMembers':1,'atlasFile':D['texture'],'atlasSha256':D['textureSha256'],'surfaceUpdates':v['surfaceMaterialUpdates'],'browserRuntimeVerified':False,'browserMaterialsApproximate':True};(O/'browser-right-bow-v56.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('RIGHT_BOW_56_EXPORTED',spec['triangles'],len(buckets),len(targets))
