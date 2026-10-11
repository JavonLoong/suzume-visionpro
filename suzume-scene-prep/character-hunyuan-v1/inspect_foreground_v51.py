from pathlib import Path
import bpy,json,hashlib,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-foreground-v51';O.mkdir(exist_ok=True)
source=R/'poster-lower-facade-v50/Suzume_dual_scene_lower_facade_v50.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='ed93df6cd06f2844561a1df5933af030d7730a8593f144f021c4c4cceca7941f'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
rows=[];arrays={};cam=np.array(s.camera.matrix_world);C=cam[:3,3];rot=cam[:3,:3];f=s.camera.data.lens/s.camera.data.sensor_height*1000
for ob in s.objects:
    if ob.type!='MESH' or not ob.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    m=ob.data;key='mesh'+str(len(rows));v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],np.int32);arrays[key+'_vertices']=world;arrays[key+'_faces']=faces
    rows.append({'key':key,'name':ob.name,'vertices':len(v),'triangles':len(faces),'materials':[x.name for x in m.materials]})
np.savez_compressed(O/'source-foreground-v51.npz',**arrays)
data={'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':rows,'camera':{'position':C.tolist(),'rotation':rot.tolist(),'focalPixels':f}}
(O/'source-foreground-v51.json').write_text(json.dumps(data,indent=2))
ivy=s.objects['Individual three-dimensional ivy leaves.001'];m=ivy.data;attrs={};meta=[]
for a in m.attributes:
 if a.name=='position':continue
 if a.data_type=='FLOAT_VECTOR':arr=np.empty((len(a.data),3),'f4');a.data.foreach_get('vector',arr.ravel())
 elif a.data_type=='FLOAT_COLOR':arr=np.empty((len(a.data),4),'f4');a.data.foreach_get('color',arr.ravel())
 else:continue
 attrs[a.name]=arr;meta.append({'name':a.name,'type':a.data_type,'domain':a.domain})
attrs['points']=np.array([p.co[:] for p in m.vertices],dtype='f4');attrs['matrix']=np.array(ivy.matrix_world);attrs['world']=attrs['points']@attrs['matrix'][:3,:3].T+attrs['matrix'][:3,3];np.savez_compressed(O/'ivy-source-v51.npz',**attrs)
proto=s.objects['Individual three-dimensional ivy leaves prototype.001'];mat=proto.data.materials[0];materials=[]
for name in [mat.name,'Reference-calibrated upper facade pigments v48']:
 mat=bpy.data.materials[name];materials.append({'name':name,'nodes':[{'name':n.name,'type':n.bl_idname,'attribute':getattr(n,'attribute_name',None),'group':getattr(getattr(n,'node_tree',None),'name',None),'inputs':{i.name:str(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in mat.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in mat.node_tree.links]})
(O/'ivy-source-v51.json').write_text(json.dumps({'object':ivy.name,'count':len(m.vertices),'attributes':meta,'materials':materials},indent=2));print('FOREGROUND_51_SOURCE_EXPORTED',len(rows),len(m.vertices),flush=True)
