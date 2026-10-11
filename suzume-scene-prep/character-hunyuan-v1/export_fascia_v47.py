from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(__file__).parent;O=R/'poster-fascia-v47';native=O/'Suzume_dual_scene_fascia_v47.blend'
D=json.loads((O/'fascia-geometry-v47.json').read_text());check=json.loads((O/'verification-v47.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==check['nativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];out=[]
for q in D['members']:
    ob=s.objects[q['name']];m=ob.data;m.calc_loop_triangles();v=np.array([ob.matrix_world@p.co for p in m.vertices]);ix=np.array([t.vertices[:] for t in m.loop_triangles]);loops=np.array([t.loops[:] for t in m.loop_triangles]);norm=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',norm.ravel())
    p=(v[ix.ravel()][:,[0,2,1]]*[1,1,-1]).astype('f4');n=(norm[loops.ravel()][:,[0,2,1]]*[1,1,-1]).astype('f4')
    out.append({'name':q['name'],'positions':p.ravel().tolist(),'normals':n.ravel().tolist(),'materialIndices':[t.material_index for t in m.loop_triangles]})
spec={'revision':47,'nativeSha256':check['nativeSha256'],'materials':D['materials'],'members':out,'triangles':sum(len(q['positions'])//9 for q in out),'browserRuntimeVerified':False,'browserMaterialsApproximate':True}
(O/'browser-fascia-v47.json').write_text(json.dumps(spec,separators=(',',':')));print('FASCIA_47_EXPORTED',spec['triangles'])
