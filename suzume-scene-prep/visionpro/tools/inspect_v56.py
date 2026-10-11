import bpy, json
from pathlib import Path
from mathutils import Vector

out = Path(__file__).resolve().parents[1] / 'validation'
out.mkdir(exist_ok=True)
scene = bpy.data.scenes['Night meadow through the door']
bpy.context.window.scene = scene
bpy.context.view_layer.update()
rows=[]
for ob in scene.objects:
    if ob.type != 'MESH': continue
    bounds=[ob.matrix_world @ Vector(v) for v in ob.bound_box]
    row={'name':ob.name,'vertices':len(ob.data.vertices),'bounds':[[min(v[i] for v in bounds) for i in range(3)],[max(v[i] for v in bounds) for i in range(3)]], 'materials':[]}
    for mat in ob.data.materials:
        if not mat: continue
        nodes=[]
        for n in mat.node_tree.nodes:
            d={'type':n.type,'name':n.name}
            if hasattr(n,'image') and n.image: d['image']={'name':n.image.name,'size':list(n.image.size),'path':n.image.filepath,'packed':bool(n.image.packed_file)}
            if n.type in ('BSDF_PRINCIPLED','EMISSION','ATTRIBUTE','VALTORGB'):
                d['inputs']={s.name:list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value for s in n.inputs if hasattr(s,'default_value')}
                d['links']=[(l.from_node.name,l.from_socket.name,l.to_socket.name) for l in mat.node_tree.links if l.to_node==n]
                if n.type=='ATTRIBUTE': d['attribute']=n.attribute_name
            nodes.append(d)
        row['materials'].append({'name':mat.name,'nodes':nodes})
    if ob.modifiers:
        row['modifiers']=[{'type':m.type,'nodes': [{'type':n.type,'object':n.inputs['Object'].default_value.name if n.type=='OBJECT_INFO' and n.inputs['Object'].default_value else None} for n in m.node_group.nodes] if m.type=='NODES' else []} for m in ob.modifiers]
        row['attributes']=[(a.name,a.data_type,a.domain) for a in ob.data.attributes]
    rows.append(row)
(out/'v56_source_inspection.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
for row in rows:
    if 'volume' not in row['name'] and 'portion' not in row['name'] and 'mist' not in row['name']:
        print(json.dumps(row,ensure_ascii=True),flush=True)
