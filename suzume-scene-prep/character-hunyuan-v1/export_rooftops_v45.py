from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-rooftops-v45';native=O/'Suzume_dual_scene_rooftops_v45.blend';verified=json.loads((O/'verification-v45.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==verified['nativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
original=json.loads((O/'source-rooftops-v45.json').read_text());geometry=json.loads((O/'rooftop-geometry-v45.json').read_text());changed={q['name'] for q in verified['changedOriginalMeshes']}
objects=[(s.objects[q['name']],q['key'],q) for q in original['objects'] if q['name'] in changed]+[(s.objects[q['name']],'new',None) for q in geometry['members']]
bins={};members={};original_info={}
for ob,prefix,source in objects:
    m=ob.data;m.calc_loop_triangles();v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];loops=np.array([t.loops[:] for t in m.loop_triangles]);verts=np.array([t.vertices[:] for t in m.loop_triangles]);matidx=np.array([t.material_index for t in m.loop_triangles]);normals=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',normals.ravel());normals=normals@np.linalg.inv(M[:3,:3]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12);uv=np.zeros((len(m.loops),2),'f4')
    if m.uv_layers.active:m.uv_layers.active.data.foreach_get('uv',uv.ravel())
    for index in np.unique(matidx):
        keep=matidx==index;key=prefix if source else prefix+str(index);p=world[verts[keep].ravel()][:,[0,2,1]]*[1,1,-1];n=normals[loops[keep].ravel()][:,[0,2,1]]*[1,1,-1];u=uv[loops[keep].ravel()];bins.setdefault(key,[]).append(np.c_[p,n,u].astype('<f4'));members.setdefault(key,[]).append(ob.name)
        if source:original_info[key]=source
new_materials=[]
for index,mat in enumerate(s.objects[geometry['members'][0]['name']].data.materials):new_materials.append({'key':'new'+str(index),'name':mat.name,'linearRGB':list(mat.diffuse_color[:3]),'roughness':.82,'metalness':.12})
payload=[];offset=0;buckets=[]
for key in sorted(bins):
    data=np.concatenate(bins[key]);raw=data.tobytes();row={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(data),'sourceObjects':members[key]}
    if key in original_info:row['originalVertexCount']=original_info[key]['vertices']
    else:row['newMaterialKey']=key
    buckets.append(row);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'rooftops-v45.bin').write_bytes(binary)
spec={'revision':45,'nativeSha256':verified['nativeSha256'],'strideFloats':8,'buckets':buckets,'newMaterials':new_materials,'binarySha256':hashlib.sha256(binary).hexdigest(),'triangles':sum(q['vertexCount']//3 for q in buckets),'closedAssemblies':4,'browserMaterialsApproximate':True,'browserRuntimeVerified':False}
(O/'browser-rooftops-v45.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('ROOF_45_EXPORTED',spec['triangles'],len(buckets),flush=True)
