import bpy,json,numpy as np,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'analysis';A.mkdir(parents=True,exist_ok=True);F=A/'software_meshes';F.mkdir(exist_ok=True)
SOURCE=R.parent/'picounity/Assets/Models'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rows=[]
for group in ['DoorFrame','DoorLeaf']:
    before=set(bpy.data.objects);file=SOURCE/(group+'.fbx');bpy.ops.import_scene.fbx(filepath=str(file))
    objects=set(bpy.data.objects)-before
    for i,ob in enumerate(sorted(objects,key=lambda o:o.name)):
        if ob.type!='MESH':continue
        m=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();m.calc_loop_triangles()
        v=np.array([ob.matrix_world@p.co for p in m.vertices],dtype=np.float64);f=np.array([p.vertices for p in m.loop_triangles],dtype=np.int32)
        name=f'{group}_{i:02d}';np.savez_compressed(F/(name+'.npz'),vertices=v,faces=f)
        rows.append({'id':name,'group':group,'name':ob.name,'vertices':len(v),'faces':len(f),'bounds':np.array([v.min(0),v.max(0)]).tolist(),
                     'materials':[mat.name for mat in ob.data.materials if mat], 'images':[n.image.filepath for mat in ob.data.materials if mat and mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
        ob.name=name
    print('IMPORTED',group,flush=True)
(A/'software_source.json').write_text(json.dumps({'files':[{ 'path':str(SOURCE/(g+'.fbx')),'sha256':hashlib.sha256((SOURCE/(g+'.fbx')).read_bytes()).hexdigest()} for g in ['DoorFrame','DoorLeaf']],'meshes':rows},ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'软件原门_只读提取.blend'))
print('SOFTWARE_SOURCE_EXPORTED',len(rows),flush=True)
