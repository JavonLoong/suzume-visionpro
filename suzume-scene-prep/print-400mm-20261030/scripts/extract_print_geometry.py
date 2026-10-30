import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'analysis';out.mkdir(exist_ok=True)
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;bpy.context.view_layer.update()
groups={'wall':[],'steel':[],'ground':[],'frame':[],'leaf':[],'pedestal':[]}
sources={k:[] for k in groups};excluded=[]
for ob in s.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 name=ob.name;coll=' '.join(c.name for c in ob.users_collection)
 cat=None
 if name.startswith('Circular ruined hotel') or any(x in coll for x in ['facade','clerestory','arcade','window storey','rooftop equipment','balcony railing','roof fascia']):cat='wall'
 elif name.startswith('Broken radial dome steelwork') or any(x in coll for x in ['steelwork','right bow']):cat='steel'
 elif name.startswith(('Flooded polygon','Brick and masonry')) or any(x in coll for x in ['bank and stones','pipe supports']):cat='ground'
 elif name.startswith('Complete six-panel white door and frame surface'):cat='frame'
 elif name.startswith('Animated door leaf and hinges surface'):cat='leaf'
 elif name in ['Mesh.007','Mesh.008','Mesh.009']:cat='pedestal'
 if not cat:excluded.append(name);continue
 mesh=ob.data;mesh.calc_loop_triangles()
 v=np.empty((len(mesh.vertices),3),dtype=np.float64);mesh.vertices.foreach_get('co',v.ravel())
 m=np.array(ob.matrix_world);v=v@m[:3,:3].T+m[:3,3]
 f=np.array([list(p.vertices) for p in mesh.loop_triangles],dtype=np.int32)
 if not len(f):continue
 if np.linalg.det(m[:3,:3])<0:f=f[:,::-1]
 groups[cat].append((v,f));sources[cat].append({'name':name,'vertices':len(v),'triangles':len(f)})
for cat,parts in groups.items():
 vs=[];fs=[];n=0
 for v,f in parts:vs.append(v);fs.append(f+n);n+=len(v)
 np.savez_compressed(out/(cat+'.npz'),vertices=np.concatenate(vs),faces=np.concatenate(fs))
print(json.dumps({k:{'objects':len(v),'triangles':sum(x['triangles'] for x in v)} for k,v in sources.items()}),flush=True)
(out/'selected-source-objects.json').write_text(json.dumps({'source':bpy.data.filepath,'scene':s.name,'selected':sources,'excluded':excluded},ensure_ascii=False,indent=2),encoding='utf8')
