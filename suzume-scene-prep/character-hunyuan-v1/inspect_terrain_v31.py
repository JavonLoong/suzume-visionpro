"""Inspect real native terrain and collection wiring before extending the realm."""
from pathlib import Path
import bpy,json,hashlib,sys,numpy as np
R=Path(__file__).parent;O=R/'movie-terrain-v31';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from night_audit_v30 import fingerprint,topology,material_digest
p=R/'movie-night-v30/Suzume_scene_movie_night_v30.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
s=bpy.data.scenes['Night meadow through the door'];bpy.context.window.scene=s;bpy.context.view_layer.update();ob=bpy.data.objects['Rolling meadow ground']
v=np.empty((len(ob.data.vertices),3),np.float32);ob.data.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3]
np.savez_compressed(O/'original-ground-v31.npz',local=v,world=world,matrix=M)
all_meshes={o.name:{'worldHash':fingerprint(o),'topology':topology(o)} for o in s.objects if o.type=='MESH'}
result={'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ground':{'name':ob.name,'matrix':M.tolist(),'parent':ob.parent.name if ob.parent else None,'collections':[c.name for c in ob.users_collection],'vertices':len(v),'polygons':len(ob.data.polygons),'worldBounds':[world.min(0).tolist(),world.max(0).tolist()],'materials':[m.name for m in ob.data.materials]},'nightMeshFingerprints':all_meshes,'materials':{m.name:material_digest(m) for m in bpy.data.materials},'nightCollections':[c.name for c in s.collection.children],'realmCollections':[c.name for c in bpy.data.collections if 'night' in c.name.lower()],'realmInstances':[{'name':o.name,'collection':o.instance_collection.name,'matrix':[list(r) for r in o.matrix_world]} for o in bpy.data.objects if o.instance_collection and 'night' in o.instance_collection.name.lower()]}
(O/'source-inspection-v31.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['nightMeshFingerprints','materials']},ensure_ascii=True),flush=True)
