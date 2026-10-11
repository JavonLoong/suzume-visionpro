from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-railings-v46';O.mkdir(exist_ok=True)
source=R/'poster-rooftops-v45/Suzume_dual_scene_rooftops_v45.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='934df5dbec658241e56773fa0d15bfd221358c624120e609b7603a1b936075ba'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
rows=[];arrays={};cam=np.array(s.camera.matrix_world);C=cam[:3,3];rot=cam[:3,:3];f=s.camera.data.lens/s.camera.data.sensor_height*1000
for obj in s.objects:
    if obj.type!='MESH' or not obj.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    m=obj.data;key='mesh'+str(len(rows));v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(obj.matrix_world);world=v@M[:3,:3].T+M[:3,3]
    m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],np.int32);arrays[key+'_vertices']=world;arrays[key+'_faces']=faces
    rows.append({'key':key,'name':obj.name,'vertices':len(v),'triangles':len(faces),'materials':[x.name for x in m.materials]})
np.savez_compressed(O/'source-railings-v46.npz',**arrays)
data={'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':rows,'camera':{'position':C.tolist(),'rotation':rot.tolist(),'focalPixels':f},'otherMeshNames':[x.name for x in s.objects if x.type=='MESH' and x.name not in {q['name'] for q in rows}]}
(O/'source-railings-v46.json').write_text(json.dumps(data,indent=2));print('RAILING_46_SOURCE',len(rows),sum(q['triangles'] for q in rows),flush=True)
