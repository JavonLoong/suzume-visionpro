from pathlib import Path
import bpy,json,hashlib,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-lower-facade-v50';O.mkdir(exist_ok=True)
source=R/'poster-arches-v49/Suzume_dual_scene_arches_v49.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='bbcfec64ae4a3614fbcd92d3ba0522942deb54a439a842201d7fbcadf3e248f5'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
rows=[];arrays={};cam=np.array(s.camera.matrix_world);C=cam[:3,3];rot=cam[:3,:3];f=s.camera.data.lens/s.camera.data.sensor_height*1000
for ob in s.objects:
    if ob.type!='MESH' or not ob.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    m=ob.data;key='mesh'+str(len(rows));v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],np.int32);arrays[key+'_vertices']=world;arrays[key+'_faces']=faces
    rows.append({'key':key,'name':ob.name,'vertices':len(v),'triangles':len(faces),'materials':[x.name for x in m.materials]})
np.savez_compressed(O/'source-lower-facade-v50.npz',**arrays)
data={'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':rows,'camera':{'position':C.tolist(),'rotation':rot.tolist(),'focalPixels':f}}
(O/'source-lower-facade-v50.json').write_text(json.dumps(data,indent=2))
deps=bpy.context.evaluated_depsgraph_get();samples=[]
for u in [10,25,50,80,100,115,140,175,220,270]:
    for v in np.arange(614,690,6):
        ray=Vector(np.array([(u-354)/f,(500-v)/f,-1])@rot.T).normalized();hit,p,n,index,ob,M=s.ray_cast(deps,Vector(C),ray,distance=100)
        if not hit:continue
        mats=[x.name for x in ob.data.materials] if ob.type=='MESH' else []
        samples.append({'u':u,'v':float(v),'object':ob.name,'faceIndex':index,'point':list(p),'normal':list(n),'materials':mats})
(O/'lower-ray-hits-v50.json').write_text(json.dumps(samples,indent=2));print('LOWER_FACADE_50_INSPECTED',len(rows),len(samples),flush=True)
s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=300/708;s.render.border_min_y=.295;s.render.border_max_y=.400;s.render.filepath=str(O/'lower-facade-before-v50.png');bpy.ops.render.render(write_still=True);print('LOWER_FACADE_50_BASELINE_RENDERED',flush=True)
