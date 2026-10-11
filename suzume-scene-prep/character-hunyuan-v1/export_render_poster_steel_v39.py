from pathlib import Path
import bpy,bmesh,json,hashlib,numpy as np,ast,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-steel-v39';native=O/'Suzume_dual_scene_steel_v39.blend'
# Reuse only the pure snapshot functions, not the earlier verifier's execution.
tree=ast.parse((R/'verify_render_poster_v38.py').read_text());funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tree_hash','movie_snapshot']];exec(compile(ast.Module(body=funcs,type_ignores=[]),'snapshot helpers','exec'))
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-v38/Suzume_dual_scene_v38.blend'));movie_before=movie_snapshot()
bpy.ops.wm.open_mainfile(filepath=str(native));movie_after=movie_snapshot();assert movie_before==movie_after
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
D=json.loads((O/'steel-geometry-v39.json').read_text());closed=[]
for q in D['members']:
    ob=bpy.data.objects[q['name']+' v39'];m=ob.data;a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());assert np.max(np.abs(a-np.array(q['verticesNative'])))<1e-6
    bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume();bm.free();assert bad==0 and vol>0,(ob.name,bad,vol)
    closed.append({'name':ob.name,'triangles':len(m.polygons),'nonManifoldEdges':bad,'signedVolume':vol})
connections=json.loads((O/'connections-v39.json').read_text());assert connections['allCheckedConnectionsIntersect']
old=json.loads((O/'source-steel-v39.json').read_text());objects=[(s.objects[q['name']],q) for q in old]+[(s.objects[q['name']+' v39'],None) for q in D['members']]
bins={};members={};old_info={}
for ob,original in objects:
    m=ob.data;m.calc_loop_triangles();v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3]
    loops=np.array([t.loops[:] for t in m.loop_triangles]);vert=np.array([t.vertices[:] for t in m.loop_triangles]);matidx=np.array([t.material_index for t in m.loop_triangles]);normals=np.empty((len(m.corner_normals),3),np.float32);m.corner_normals.foreach_get('vector',normals.ravel());N=np.linalg.inv(M[:3,:3]).T;normals=normals@N.T;normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    uv=np.zeros((len(m.loops),2),np.float32)
    if m.uv_layers.active:m.uv_layers.active.data.foreach_get('uv',uv.ravel())
    for idx in np.unique(matidx):
        selected=matidx==idx;key=original['key'] if original else 'new'+str(idx);p=world[vert[selected].ravel()][:,[0,2,1]]*[1,1,-1];n=normals[loops[selected].ravel()][:,[0,2,1]]*[1,1,-1];u=uv[loops[selected].ravel()]
        bins.setdefault(key,[]).append(np.c_[p,n,u].astype('<f4'));members.setdefault(key,[]).append(ob.name)
        if original:old_info[key]=original
material_data=[s.objects[D['members'][0]['name']+' v39'].data.materials[i] for i in range(4)]
spec={'revision':39,'sourceNativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'strideFloats':8,'buckets':[],'newMaterials':[{'linearRGB':list(m.diffuse_color[:3]),'roughness':.82,'metalness':0 if i==3 else .08} for i,m in enumerate(material_data)],'proceduralMaterialApproximationInBrowser':True,'geometryIdenticalToNative':True,'browserRuntimeVerified':False}
payload=[];offset=0
for key in sorted(bins):
    a=np.concatenate(bins[key]);raw=a.tobytes();row={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(a),'sourceObjects':members[key]}
    if key in old_info:row['originalVertexCount']=old_info[key]['vertices']
    else:row['newMaterialIndex']=int(key[3:])
    spec['buckets'].append(row);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'steel-v39.bin').write_bytes(binary);spec['binarySha256']=hashlib.sha256(binary).hexdigest();(O/'browser-steel-v39.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
report={'revision':39,'nativeSha256':spec['sourceNativeSha256'],'freshReopenVerified':True,'movieStatePreservedExactly':True,'closedMembers':closed,'checkedConnectedJoints':len(connections['checks']),'allCheckedConnectionsIntersect':True,'browserTriangles':sum(q['vertexCount']//3 for q in spec['buckets']),'browserGeometryExportVerified':True,'browserMaterialsApproximate':True,'browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'verification-v39.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('POSTER_39_VERIFIED_EXPORTED',report['browserTriangles'],flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v39.png');bpy.ops.render.render(write_still=True);print('POSTER_39_FRONT_DONE',flush=True)
# The unchanged reference camera is used for this native high-resolution crop.
s.render.resolution_x=2000;s.render.resolution_y=2824;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.575;s.render.border_max_x=1;s.render.border_min_y=1-1630/2824;s.render.border_max_y=1-650/2824;s.cycles.samples=24;s.render.filepath=str(O/'steel-detail-v39.png');bpy.ops.render.render(write_still=True);print('POSTER_39_DETAIL_DONE',flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=20;s.render.filepath=str(O/'poster-oblique-v39.png');bpy.ops.render.render(write_still=True);print('POSTER_39_OBLIQUE_DONE',flush=True)
