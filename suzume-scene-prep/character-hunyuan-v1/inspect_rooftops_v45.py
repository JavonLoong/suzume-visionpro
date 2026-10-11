from pathlib import Path
import bpy, json, hashlib, numpy as np
from mathutils import Vector

R=Path(__file__).parent;O=R/'poster-rooftops-v45';O.mkdir(exist_ok=True)
source=R/'poster-left-steel-v44/Suzume_dual_scene_left_steel_v44.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='0015d1aba946addbbcd9d05a7922e720fb15c773c3ae4300566eb812b1f886c1'
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
rows=[];arrays={};f=s.camera.data.lens/s.camera.data.sensor_height*1000
cam=np.array(s.camera.matrix_world);C=cam[:3,3];rot=cam[:3,:3]
for obj in s.objects:
    if obj.type!='MESH' or not obj.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    m=obj.data;key='mesh'+str(len(rows));v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(obj.matrix_world);world=v@M[:3,:3].T+M[:3,3]
    m.calc_loop_triangles();faces=np.array([p.vertices for p in m.loop_triangles],np.int32);q=(world-C)@rot
    uv=np.stack((354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]),axis=1)
    arrays[key+'_vertices']=world;arrays[key+'_faces']=faces
    rows.append({'key':key,'name':obj.name,'vertices':len(v),'triangles':len(faces),'boundsNative':[world.min(0).tolist(),world.max(0).tolist()],'boundsImage':[uv.min(0).tolist(),uv.max(0).tolist()],'matrixWorld':M.tolist(),'materials':[x.name for x in m.materials]})
np.savez_compressed(O/'source-rooftops-v45.npz',**arrays)
data={'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':rows,'camera':{'position':C.tolist(),'rotation':rot.tolist(),'focalPixels':f}}
(O/'source-rooftops-v45.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('ROOF_45_INSPECTED',len(rows),sum(x['triangles'] for x in rows),flush=True)
for x in rows:print(x['key'],x['name'],x['vertices'],x['materials'],flush=True)
