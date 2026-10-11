from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-low-rails-v53';native=O/'Suzume_dual_scene_low_rails_v53.blend';v=json.loads((O/'verification-v53.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];D=json.loads((O/'low-rails-geometry-v53.json').read_text());info={q['key']:q for q in D['sourceObjects']};bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();bins={};members={};targets=[]
for q in v['changedOriginalMeshes']:
 k=q['key'];targets.append({'key':k,'originalName':'Brick and masonry debris solid mesh','originalVertexCount':info[k]['vertices']})
objects=[(s.objects[q['name']],q['key']) for q in v['changedOriginalMeshes']]+[(s.objects[q['name']],None) for q in D['members']]
for ob,prefix in objects:
 m=ob.data;m.calc_loop_triangles();M=np.array(ob.matrix_world);a=np.array([p.co[:] for p in m.vertices]);world=a@M[:3,:3].T+M[:3,3];faces=np.array([t.vertices[:] for t in m.loop_triangles]);loops=np.array([t.loops[:] for t in m.loop_triangles]);mi=np.array([t.material_index for t in m.loop_triangles]);n=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',n.ravel());n=n@np.linalg.inv(M[:3,:3]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());rgba=np.ones((len(a),4),'f4')
 if 'surface_color' in m.color_attributes:m.color_attributes['surface_color'].data.foreach_get('color',rgba.ravel())
 for mat in np.unique(mi):
  keep=mi==mat;key=prefix if prefix else 'new'+str(mat);indices=faces[keep].ravel();p=world[indices][:,[0,2,1]]*[1,1,-1];normal=n[loops[keep].ravel()][:,[0,2,1]]*[1,1,-1];data=np.c_[p,normal,uv[loops[keep].ravel()],rgba[indices]].astype('<f4');bins.setdefault(key,[]).append(data);members.setdefault(key,[]).append(ob.name)
payload=[];buckets=[];offset=0
for key in sorted(bins):
 data=np.concatenate(bins[key]);raw=data.tobytes();q={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(data),'sourceObjects':members[key]}
 if key.startswith('new'):q['fixtureMaterialIndex']=int(key[3:])
 else:q['reuseTargetMaterial']=key
 buckets.append(q);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'low-rails-v53.bin').write_bytes(binary);spec={'revision':53,'nativeSha256':v['nativeSha256'],'targets':targets,'buckets':buckets,'strideFloats':12,'triangles':sum(q['vertexCount']//3 for q in buckets),'binarySha256':hashlib.sha256(binary).hexdigest(),'closedSolids':len(D['members']),'browserRuntimeVerified':False,'browserMaterialsApproximate':True};(O/'browser-low-rails-v53.json').write_text(json.dumps(spec,indent=2));print('LOW_RAILS_53_EXPORTED',spec['triangles'],len(buckets),len(targets))
