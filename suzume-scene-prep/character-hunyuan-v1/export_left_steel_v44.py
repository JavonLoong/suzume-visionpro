from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-left-steel-v44';native=O/'Suzume_dual_scene_left_steel_v44.blend';verified=json.loads((O/'verification-v44.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==verified['nativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
original=json.loads((R/'poster-steel-v39/source-steel-v39.json').read_text());right=json.loads((R/'poster-steel-v39/steel-geometry-v39.json').read_text());left=json.loads((O/'steel-geometry-v44.json').read_text())
objects=[(s.objects[q['name']],q['key'],q) for q in original]+[(s.objects[q['name']+' v39'],'right',None) for q in right['members']]+[(s.objects[q['name']],'left',None) for q in left['members']]
bins={};members={};original_info={}
for ob,prefix,source in objects:
    m=ob.data;m.calc_loop_triangles();v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];loops=np.array([t.loops[:] for t in m.loop_triangles]);verts=np.array([t.vertices[:] for t in m.loop_triangles]);matidx=np.array([t.material_index for t in m.loop_triangles]);normals=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',normals.ravel());normals=normals@np.linalg.inv(M[:3,:3]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12);uv=np.zeros((len(m.loops),2),'f4')
    if m.uv_layers.active:m.uv_layers.active.data.foreach_get('uv',uv.ravel())
    for index in np.unique(matidx):
        keep=matidx==index;key=prefix if source else prefix+str(index);p=world[verts[keep].ravel()][:,[0,2,1]]*[1,1,-1];n=normals[loops[keep].ravel()][:,[0,2,1]]*[1,1,-1];u=uv[loops[keep].ravel()];bins.setdefault(key,[]).append(np.c_[p,n,u].astype('<f4'));members.setdefault(key,[]).append(ob.name)
        if source:original_info[key]=source
new_materials=[]
for prefix,ob in [('right',s.objects[right['members'][0]['name']+' v39']),('left',s.objects[left['members'][0]['name']])]:
    for index,mat in enumerate(ob.data.materials):new_materials.append({'key':prefix+str(index),'name':mat.name,'linearRGB':list(mat.diffuse_color[:3]),'roughness':.82 if prefix=='right' else .80,'metalness':0 if index==3 else (.08 if prefix=='right' else .07)})
payload=[];offset=0;buckets=[];probes=[]
for key in sorted(bins):
    data=np.concatenate(bins[key]);raw=data.tobytes();row={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(data),'sourceObjects':members[key]}
    if key in original_info:row['originalVertexCount']=original_info[key]['vertices']
    else:row['newMaterialKey']=key
    for i in [0,len(data)//2,len(data)-1]:probes.append({'key':key,'index':int(i),'positionNormalUV':data[i].tolist()})
    buckets.append(row);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'steel-v44.bin').write_bytes(binary)
spec={'revision':44,'nativeSha256':verified['nativeSha256'],'strideFloats':8,'buckets':buckets,'newMaterials':new_materials,'binarySha256':hashlib.sha256(binary).hexdigest(),'triangles':sum(q['vertexCount']//3 for q in buckets),'closedNewLeftMembers':20,'closedRetainedRightMembers':16,'browserMaterialsApproximate':True,'browserRuntimeVerified':False};(O/'browser-steel-v44.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(O/'steel-probes-v44.json').write_text(json.dumps(probes,indent=2),encoding='utf-8');print('LEFT_STEEL_44_EXPORTED',spec['triangles'],flush=True)
