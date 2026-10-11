from pathlib import Path
import bpy,json,sys,hashlib,numpy as np
from collections import Counter
R=Path(__file__).parent;O=R/'movie-face-v36';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint;from character_export_utils import export_character
f=O/'Suzume_scene_movie_face_v36.blend';bpy.ops.wm.open_mainfile(filepath=str(f));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);a=json.loads((O/'integration-v36.json').read_text());head=bpy.data.objects['Suzume mathematical head v36'];body=bpy.data.objects['Suzume Hunyuan textured surface'];other=bpy.data.objects[head.name+' — entered portion']
assert fingerprint(head,True)==a['headHash'] and fingerprint(body,True)==a['bodyHash'];assert head.data==other.data
for ob,half in [(head,'courtyard'),(other,'otherworld')]:
 assert all(slot.material['spatial_half']==half and abs(slot.material['portal_plane_blender_y']-.072)<1e-6 for slot in ob.material_slots)
 assert all(m.object==body.parent for m in ob.modifiers if m.type=='ARMATURE')
closed=[]
for g in head.vertex_groups:
 if not g.name.startswith('Head part :: Solid ponytail lock'):continue
 indices={v.index for v in head.data.vertices if any(q.group==g.index and q.weight>.5 for q in v.groups)};faces=[list(p.vertices) for p in head.data.polygons if all(i in indices for i in p.vertices)];edges=Counter(tuple(sorted((p[i],p[(i+1)%len(p)]))) for p in faces for i in range(len(p)));assert set(edges.values())=={2};closed.append({'name':g.name,'vertices':len(indices),'faces':len(faces),'boundaryEdges':0})
assert len(closed)==6
for frame,hidden in [(1,True),(72,False)]:s.frame_set(frame);assert head.hide_render==hidden and other.hide_render==hidden
s.frame_set(72);material_counts=Counter(p.material_index for p in head.data.polygons);assert len(material_counts)>=10
mouth_group=head.vertex_groups['Head part :: Quiet mouth line'].index;mouth_ids={v.index for v in head.data.vertices if any(g.group==mouth_group and g.weight>.5 for g in v.groups)};mouth_materials=Counter(head.data.materials[p.material_index].name for p in head.data.polygons if all(i in mouth_ids for i in p.vertices));assert len(mouth_materials)==2 and any(n.startswith('Pupil and eyelashes') for n in mouth_materials) and any(n.startswith('Warm eye white') for n in mouth_materials)
old=np.load(R/'movie-head-v35/head-check-v35.npz');current=np.load(O/'head-check-v36.npz');assert np.array_equal(old['after'][old['ponytailMask']],current['after'][current['ponytailMask']])
parts=export_character(R/'viewer/character-v36',36,['Suzume Hunyuan textured surface','Suzume mathematical head v36'])
v={'revision':36,'freshReopenVerified':True,'nativeSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bodyFeetAndGripPreserved':True,'sharedRigAndSpatialPartitionVerified':True,'closedPonytailParts':closed,'materialRegions':len(material_counts),'closedAndOpenVisibilityVerified':True,'partTriangles':parts,'oneToOneComplete':False,'browserRuntimeVerified':False}
v['mouthMaterialFaceCounts']=dict(mouth_materials);v['v35PonytailPreservedExactly']=True
(O/'verification-v36.json').write_text(json.dumps(v,indent=2));print('FACE_36_REOPEN_EXPORT_OK',json.dumps(v),flush=True)
