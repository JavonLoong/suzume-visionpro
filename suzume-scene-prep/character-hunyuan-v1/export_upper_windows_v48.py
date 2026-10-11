from pathlib import Path
import bpy,json,hashlib,numpy as np
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-upper-windows-v48';native=O/'Suzume_dual_scene_upper_windows_v48.blend';v=json.loads((O/'verification-v48.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];D=json.loads((O/'upper-window-geometry-v48.json').read_text());original=json.loads((R/'poster-rooftops-v45/source-rooftops-v45.json').read_text());prior=json.loads((R/'poster-railings-v46/browser-railings-v46.json').read_text());prior_keys={q['key'] for q in prior['buckets'] if 'originalVertexCount' in q};original_info={q['key']:q for q in original['objects']}
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();bins={};members={}
cleanup=json.loads((O/'facade-cleanup-v48.json').read_text());cleanimage=bpy.data.images['Original facade minus thin foreground rods v48'];assert hashlib.sha256(cleanimage.packed_file.data).hexdigest()==cleanup['cleanImageSha256'];assert s.objects[D['sourceObjects'][18]['name']].data.materials[0].name=='Reference facade with foreground rods removed v48';assert cleanup['outsideMaskPixelsPreservedExactly'];(O/'native-atlas-cleanup-verification-v48.json').write_text(json.dumps({'nativeSha256':v['nativeSha256'],'packedCleanAtlasMatchesVerifiedPixels':True,'originalFacadePixelsOutsideMaskPreservedExactly':True,'maskPixels':cleanup['maskPixels'],'cleanAtlasSha256':cleanup['cleanImageSha256']},indent=2))
objects=[(s.objects[q['name']],q['key']) for q in v['changedOriginalMeshes']]+[(s.objects[q['name']],None) for q in D['members']]
for ob,prefix in objects:
 m=ob.data;m.calc_loop_triangles();M=np.array(ob.matrix_world);a=np.array([p.co[:] for p in m.vertices]);world=a@M[:3,:3].T+M[:3,3];faces=np.array([t.vertices[:] for t in m.loop_triangles]);loops=np.array([t.loops[:] for t in m.loop_triangles]);mi=np.array([t.material_index for t in m.loop_triangles]);n=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',n.ravel());n=n@np.linalg.inv(M[:3,:3]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel())
 for mat in np.unique(mi):
  keep=mi==mat;key=prefix if prefix else 'new'+str(mat);p=world[faces[keep].ravel()][:,[0,2,1]]*[1,1,-1];normal=n[loops[keep].ravel()][:,[0,2,1]]*[1,1,-1];data=np.c_[p,normal,uv[loops[keep].ravel()]].astype('<f4');bins.setdefault(key,[]).append(data);members.setdefault(key,[]).append(ob.name)
payload=[];buckets=[];offset=0
for key in sorted(bins):
 data=np.concatenate(bins[key]);raw=data.tobytes();q={'key':key,'byteOffset':offset,'byteLength':len(raw),'vertexCount':len(data),'sourceObjects':members[key]}
 if key.startswith('mesh'):
  q.update({'materialSource':key,'previousLocation':'v46' if key in prior_keys else 'original','originalVertexCount':original_info[key]['vertices']})
  if key=='mesh18':q['materialOverrideNewIndex']=4
 else:q['newMaterialIndex']=int(key[3:])
 buckets.append(q);payload.append(raw);offset+=len(raw)
binary=b''.join(payload);(O/'upper-facade-v48.bin').write_bytes(binary)
spec={'revision':48,'nativeSha256':v['nativeSha256'],'buckets':buckets,'strideFloats':8,'triangles':sum(q['vertexCount']//3 for q in buckets),'binarySha256':hashlib.sha256(binary).hexdigest(),'atlasFile':'upper-facade-pigments-v48.png','atlasSha256':D['atlasSha256'],'cleanAtlasFile':'clean-facade-pigments-v48.png','cleanAtlasSha256':D['cleanAtlasSha256'],'newMaterials':[{'index':0,'kind':'clonePaint','source':'mesh18','textureFile':'upper-facade-pigments-v48.png'},{'index':1,'kind':'standard','linearRGB':[.23,.27,.29],'roughness':.87,'metalness':.08},{'index':2,'kind':'standard','linearRGB':[.10,.17,.23],'roughness':.24,'metalness':.20},{'index':3,'kind':'reuse','source':'mesh16'},{'index':4,'kind':'clonePaint','source':'mesh18','textureFile':'clean-facade-pigments-v48.png'}],'closedSolids':len(D['members']),'browserRuntimeVerified':False,'browserMaterialsApproximate':True};(O/'browser-upper-windows-v48.json').write_text(json.dumps(spec,indent=2));print('UPPER_WINDOWS_48_EXPORTED',spec['triangles'],len(buckets))
def tree(q):
 m=s.objects[q['name']].data;return BVHTree.FromPolygons([v.co for v in m.vertices],[p.vertices[:] for p in m.polygons],all_triangles=True)
frames=[(q,tree(q)) for q in D['members'] if q['kind']=='frame'];contacts=[]
for q in D['members']:
 if q['kind']!='glass':continue
 glass=tree(q);hits=[]
 for frame,t in frames:
  pairs=glass.overlap(t)
  if pairs:hits.append({'frame':frame['name'],'intersectingTrianglePairs':len(pairs)})
 assert len(hits)>=3,(q['name'],hits);contacts.append({'glass':q['name'],'contacts':hits})
assert len(contacts)==5
(O/'glazing-contact-verification-v48.json').write_text(json.dumps({'revision':48,'nativeSha256':v['nativeSha256'],'allFivePaneSolidsSupportedByAtLeastThreeFrameMembers':True,'panes':contacts},indent=2));print('UPPER_WINDOWS_48_GLAZING_CONTACTS_VERIFIED',len(contacts))
