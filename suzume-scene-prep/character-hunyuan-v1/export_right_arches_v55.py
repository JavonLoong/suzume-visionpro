from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-right-arches-v55';native=O/'Suzume_dual_scene_right_arches_v55.blend';v=json.loads((O/'verification-v55.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];D=json.loads((O/'right-arches-geometry-v55.json').read_text());original_info={q['key']:q for q in json.loads((R/'poster-rooftops-v45/source-rooftops-v45.json').read_text())['objects']};prior={}
for directory,filename,prefix,revision in [('poster-railings-v46','browser-railings-v46.json','Poster facade ',46),('poster-upper-windows-v48','browser-upper-windows-v48.json','Poster upper facade ',48),('poster-arches-v49','browser-arches-v49.json','Poster arched facade ',49),('poster-lower-facade-v50','browser-lower-facade-v50.json','Poster lower facade ',50),('poster-foreground-v51','browser-foreground-v51.json','Poster foreground ',51),('poster-ground-v52','browser-ground-v52.json','Poster ground ',52),('poster-right-facade-v54','browser-right-facade-v54.json','Poster right facade ',54)]:
 for q in json.loads((R/directory/filename).read_text())['buckets']:
  if q['key'].startswith('mesh'):prior[q['key']]=prefix+q['key']+' v'+str(revision)
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();bins={};members={};targets=[];prior54=json.loads((R/'poster-right-facade-v54/right-facade-geometry-v54.json').read_text())
for q in v['changedOriginalMeshes']:
 k=q['key'];targets.append({'key':k,'name':prior.get(k),'originalName':'Circular ruined hotel with exterior entrance solid mesh','originalVertexCount':original_info[k]['vertices']})
targets.extend([{'key':'prior54_'+str(i),'name':'Poster right facade new'+str(i)+' v54'} for i in range(3)])
objects=[(s.objects[q['name']],q['key'],'old') for q in v['changedOriginalMeshes']]+[(s.objects[q['name']],None,'new') for q in D['members']]+[(s.objects[q['name']],None,'prior') for q in prior54['members'] if q['name'] not in D['replacedObjects']]
for ob,prefix,mode in objects:
 m=ob.data;m.calc_loop_triangles();M=np.array(ob.matrix_world);a=np.array([p.co[:] for p in m.vertices]);world=a@M[:3,:3].T+M[:3,3];faces=np.array([t.vertices[:] for t in m.loop_triangles]);loops=np.array([t.loops[:] for t in m.loop_triangles]);mi=np.array([t.material_index for t in m.loop_triangles]);n=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',n.ravel());n=n@np.linalg.inv(M[:3,:3]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel())
 for mat in np.unique(mi):
  keep=mi==mat;key=prefix if prefix else ('new' if mode=='new' else 'prior54_')+str(mat);p=world[faces[keep].ravel()][:,[0,2,1]]*[1,1,-1];normal=n[loops[keep].ravel()][:,[0,2,1]]*[1,1,-1];data=np.c_[p,normal,uv[loops[keep].ravel()]].astype('<f4');bins.setdefault(key,[]).append(data);members.setdefault(key,[]).append(ob.name)
payload=[];buckets=[];offset=0
for key in sorted(bins):
 data=np.concatenate(bins[key]);raw=data.tobytes();q={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(data),'sourceObjects':members[key]}
 if key.startswith('new'):q['newMaterialIndex']=int(key[3:])
 else:q['reuseTargetMaterial']=key
 buckets.append(q);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'right-arches-v55.bin').write_bytes(binary);spec={'revision':55,'nativeSha256':v['nativeSha256'],'targets':targets,'buckets':buckets,'strideFloats':8,'triangles':sum(q['vertexCount']//3 for q in buckets),'binarySha256':hashlib.sha256(binary).hexdigest(),'closedSolids':len(D['members']),'archUnits':len(D['arches']),'atlasFile':'right-arcade-pigments-v55.png','atlasSha256':v['restoredAtlasSha256'],'browserRuntimeVerified':False,'browserMaterialsApproximate':True};(O/'browser-right-arches-v55.json').write_text(json.dumps(spec,indent=2));print('RIGHT_ARCHES_55_EXPORTED',spec['triangles'],len(buckets),len(targets))
