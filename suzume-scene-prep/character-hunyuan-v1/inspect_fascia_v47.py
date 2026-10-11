from pathlib import Path
import bpy,json,hashlib,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-fascia-v47';O.mkdir(exist_ok=True)
source=R/'poster-railings-v46/Suzume_dual_scene_railings_v46.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='f377b44edfb7287e25476dab31deca102a610521333d5d20e319d54c00521c2c'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
rows=[];arrays={};cam=np.array(s.camera.matrix_world);C=cam[:3,3];rot=cam[:3,:3];f=s.camera.data.lens/s.camera.data.sensor_height*1000
for ob in s.objects:
    if ob.type!='MESH' or not ob.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    m=ob.data;key='mesh'+str(len(rows));v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],np.int32);arrays[key+'_vertices']=world;arrays[key+'_faces']=faces
    rows.append({'key':key,'name':ob.name,'vertices':len(v),'triangles':len(faces),'materials':[x.name for x in m.materials]})
np.savez_compressed(O/'source-fascia-v47.npz',**arrays)
data={'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':rows,'camera':{'position':C.tolist(),'rotation':rot.tolist(),'focalPixels':f}}
(O/'source-fascia-v47.json').write_text(json.dumps(data,indent=2))
deps=bpy.context.evaluated_depsgraph_get();samples=[]
for u in [25,60,90,120,145,200,230]:
    for v in np.arange(546+u*.058,564+u*.058,1.5):
        ray=Vector(np.array([(u-354)/f,(500-v)/f,-1])@rot.T).normalized();hit,p,n,index,ob,M=s.ray_cast(deps,Vector(C),ray,distance=100)
        if not hit:continue
        mats=[x.name for x in ob.data.materials] if ob.type=='MESH' else []
        samples.append({'u':u,'v':float(v),'object':ob.name,'faceIndex':index,'point':list(p),'normal':list(n),'materials':mats})
(O/'fascia-ray-hits-v47.json').write_text(json.dumps(samples,indent=2));print('FASCIA_47_INSPECTED',len(rows),len(samples),flush=True)
for q in samples:
    if q['u'] in [90,200]:print(q['u'],round(q['v'],2),q['object'],q['faceIndex'],[round(v,3) for v in q['point']],flush=True)
