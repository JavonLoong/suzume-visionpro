from pathlib import Path
import hashlib, json
import bpy
import numpy as np

R=Path(__file__).parent; O=R/'poster-right-bow-v56'; O.mkdir(exist_ok=True)
native=R/'poster-right-arches-v55/Suzume_dual_scene_right_arches_v55.blend'
prior=json.loads((R/'poster-right-arches-v55/release-v55.json').read_text(encoding='utf-8'))
digest=hashlib.sha256(native.read_bytes()).hexdigest(); assert digest==prior['nativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(native)); s=bpy.data.scenes['Official poster courtyard v38']; bpy.context.window.scene=s; s.frame_set(1); bpy.context.view_layer.update()
arrays={}; rows=[]
for ob in s.objects:
    if ob.type!='MESH' or not ob.name.startswith('Broken radial dome steelwork solid mesh'):continue
    m=ob.data; v=np.empty((len(m.vertices),3),'f4'); m.vertices.foreach_get('co',v.ravel()); M=np.array(ob.matrix_world); world=v@M[:3,:3].T+M[:3,3]; ix=np.empty(len(m.loops),np.int32); m.loops.foreach_get('vertex_index',ix); key='mesh'+str(len(rows)); arrays[key+'_vertices']=world; arrays[key+'_faces']=ix.reshape(-1,3)
    rows.append({'name':ob.name,'key':key,'vertices':len(v),'faces':len(ix)//3,'materials':[q.name for q in m.materials],'attributes':[{'name':a.name,'type':a.data_type,'domain':a.domain,'fields':list(a.data[0].bl_rna.properties.keys()) if len(a.data) else []} for a in m.attributes]})
support=s.objects['Poster right I-section post 2 v39']; m=support.data; v=np.array([support.matrix_world@q.co for q in m.vertices]); arrays['support_vertices']=v; arrays['support_faces']=np.array([q.vertices[:] for q in m.polygons]);
np.savez_compressed(O/'source-right-bow-v56.npz',**arrays)
report={'sourceNativeSha256':digest,'objects':rows,'support':support.name,'camera':{'matrixWorld':np.array(s.camera.matrix_world).tolist(),'lens':s.camera.data.lens}}
mat=bpy.data.materials['Reference-calibrated upper facade pigments v48']
report['paintGraph']={'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':{q.name:list(q.default_value) if hasattr(q.default_value,'__len__') and not isinstance(q.default_value,str) else q.default_value for q in n.inputs if hasattr(q,'default_value') and not q.is_linked and q.type in ['VALUE','RGBA','VECTOR']}} for n in mat.node_tree.nodes], 'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links]}
(O/'source-right-bow-v56.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(rows,indent=2))
